"""
services.py — application / use-case layer for the people module.

All business logic, write workflows, and transactional operations live here.
Views call services; services call models and raise domain exceptions.
No ORM queries outside of services and selectors.

Shared sub-resource operations (addresses, notes, categories, relationships)
delegate to party.services — Party is the owner of those resources.
"""
import logging

from django.db import transaction

import party.services as party_services
from party.exceptions import (
    DuplicateCategoryAssignmentError,
    RelationshipConflictError,
    RelationshipNotFoundError,
)
from party.models import Party, PartyAddress, PartyCategoryAssignment, PartyRelationship

from .exceptions import (
    DuplicatePersonError,
    MergePersonError,
    PersonInactiveError,
    PersonNotFoundError,
)
from .models import Person

logger = logging.getLogger(__name__)


# ─── Internal Helpers ──────────────────────────────────────────────────────────

def _get_person(person_id: int) -> Person:
    try:
        return Person.objects.select_related("party").get(id=person_id)
    except Person.DoesNotExist:
        raise PersonNotFoundError(f"Person {person_id} not found.")


def _get_active_person(person_id: int) -> Person:
    person = _get_person(person_id)
    if not person.party.is_active:
        raise PersonInactiveError(
            f"Person {person_id} is inactive. Reactivate the person first."
        )
    return person


# ─── Duplicate Detection ───────────────────────────────────────────────────────

def detect_duplicate_persons(
    *,
    first_name: str,
    last_name: str,
    email: str = "",
    phone: str = "",
) -> list:
    """
    Return a list of existing active persons that are likely duplicates of
    the provided identity data.

    Each entry is a dict:
        {"person": <Person instance>, "reason": "<match_type>"}

    Match types (in descending confidence):
        "email_match"  — exact email match (high confidence)
        "name_match"   — same first + last name, case-insensitive (medium)
        "phone_match"  — same phone or mobile (medium)

    A candidate appearing via multiple signals is only included once,
    with the highest-confidence reason.

    Returns an empty list when first_name or last_name are blank, since
    partial data cannot reliably detect duplicates.
    """
    from django.db.models import Q

    if not first_name.strip() or not last_name.strip():
        return []

    candidates = []
    seen_ids: set = set()

    # High confidence: exact email match
    if email and email.strip():
        for p in Person.objects.select_related("party").filter(
            email__iexact=email.strip(), party__is_active=True
        ):
            if p.id not in seen_ids:
                candidates.append({"person": p, "reason": "email_match"})
                seen_ids.add(p.id)

    # Medium confidence: same full name (case-insensitive)
    for p in Person.objects.select_related("party").filter(
        first_name__iexact=first_name.strip(),
        last_name__iexact=last_name.strip(),
        party__is_active=True,
    ):
        if p.id not in seen_ids:
            candidates.append({"person": p, "reason": "name_match"})
            seen_ids.add(p.id)

    # Medium confidence: phone or mobile match
    if phone and phone.strip():
        for p in Person.objects.select_related("party").filter(
            Q(phone=phone.strip()) | Q(mobile=phone.strip()),
            party__is_active=True,
        ):
            if p.id not in seen_ids:
                candidates.append({"person": p, "reason": "phone_match"})
                seen_ids.add(p.id)

    return candidates


def _check_duplicates_or_raise(
    *,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    exclude_id: int = None,
) -> None:
    candidates = detect_duplicate_persons(
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
    )
    if exclude_id is not None:
        candidates = [c for c in candidates if c["person"].id != exclude_id]

    if candidates:
        names = ", ".join(c["person"].full_name for c in candidates)
        raise DuplicatePersonError(
            f"Potential duplicate persons found: {names}. "
            f"Set force=true to create anyway.",
            candidates=candidates,
        )


# ─── Person Use Cases ──────────────────────────────────────────────────────────

@transaction.atomic
def create_person(*, data: dict, created_by=None) -> Person:
    """
    Create a new Person record, atomically creating its Party first.

    Duplicate detection runs before creation. If likely duplicates exist,
    DuplicatePersonError is raised with the candidate list so the caller
    (view) can surface them to the user.

    Set data["force"] = True to bypass duplicate detection.
    """
    force = data.pop("force", False)

    if not force:
        _check_duplicates_or_raise(
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            email=data.get("email", "") or "",
            phone=data.get("phone", ""),
        )

    party = party_services.create_party(
        party_type=Party.PartyType.PERSON,
        created_by=created_by,
        is_active=True,
    )

    person = Person.objects.create(
        party=party,
        first_name=data["first_name"].strip(),
        last_name=data["last_name"].strip(),
        preferred_name=data.get("preferred_name", "").strip(),
        # Store None instead of empty string to preserve unique constraint
        email=data.get("email") or None,
        phone=data.get("phone", ""),
        mobile=data.get("mobile", ""),
        date_of_birth=data.get("date_of_birth"),
        gender=data.get("gender", ""),
    )

    logger.info(
        "Person created: id=%s name=%s by=%s",
        person.id,
        person.full_name,
        getattr(created_by, "email", created_by),
    )
    return person


@transaction.atomic
def update_person(*, person_id: int, data: dict, updated_by=None) -> Person:
    """
    Update mutable fields on a Person record.

    select_for_update() prevents a race condition where two concurrent
    updates both pass the duplicate check then both save.
    """
    try:
        person = (
            Person.objects.select_related("party")
            .select_for_update()
            .get(id=person_id)
        )
    except Person.DoesNotExist:
        raise PersonNotFoundError(f"Person {person_id} not found.")

    if not person.party.is_active:
        raise PersonInactiveError(
            f"Cannot update an inactive person (id={person_id}). "
            f"Reactivate the person first."
        )

    force = data.pop("force", False)

    if not force:
        _check_duplicates_or_raise(
            first_name=data.get("first_name", person.first_name),
            last_name=data.get("last_name", person.last_name),
            email=data.get("email", person.email or "") or "",
            phone=data.get("phone", person.phone),
            exclude_id=person_id,
        )

    updatable_fields = [
        "first_name", "last_name", "preferred_name",
        "phone", "mobile", "date_of_birth", "gender",
    ]
    for field in updatable_fields:
        if field in data:
            value = data[field]
            if isinstance(value, str):
                value = value.strip() if field in ("first_name", "last_name", "preferred_name") else value
            setattr(person, field, value)

    if "email" in data:
        person.email = data["email"] or None

    person.save()

    logger.info(
        "Person updated: id=%s by=%s",
        person.id,
        getattr(updated_by, "email", updated_by),
    )
    return person


@transaction.atomic
def deactivate_person(*, person_id: int, deactivated_by=None) -> Person:
    """
    Soft-deactivate a Person via its Party.

    Delegates to party_services.deactivate_party() which also closes all
    active PartyRelationships and deactivates all active PartyCategoryAssignments.
    """
    try:
        person = (
            Person.objects.select_related("party")
            .select_for_update()
            .get(id=person_id)
        )
    except Person.DoesNotExist:
        raise PersonNotFoundError(f"Person {person_id} not found.")

    if not person.party.is_active:
        raise PersonInactiveError(f"Person {person_id} is already inactive.")

    party_services.deactivate_party(party_id=person.party_id)

    logger.info(
        "Person deactivated: id=%s by=%s",
        person.id,
        getattr(deactivated_by, "email", deactivated_by),
    )
    return person


@transaction.atomic
def reactivate_person(*, person_id: int, reactivated_by=None) -> Person:
    """Reactivate a previously deactivated Person via its Party."""
    try:
        person = (
            Person.objects.select_related("party")
            .select_for_update()
            .get(id=person_id)
        )
    except Person.DoesNotExist:
        raise PersonNotFoundError(f"Person {person_id} not found.")

    if person.party.is_active:
        raise PersonInactiveError(f"Person {person_id} is already active.")

    party_services.reactivate_party(party_id=person.party_id)

    logger.info(
        "Person reactivated: id=%s by=%s",
        person.id,
        getattr(reactivated_by, "email", reactivated_by),
    )
    return person


def merge_persons(*, source_id: int, target_id: int, merged_by=None) -> None:
    """
    Merge contract placeholder.

    Full merge is intentionally not yet implemented because it requires:

      1. Knowing all cross-module FK dependencies (customers, suppliers,
         invoices, commissions, etc.) that reference the source person — none
         of those modules exist yet.
      2. A policy decision on which record's field values take precedence
         (source or target).
      3. Deduplication of category assignments and relationships on target
         after re-pointing.
      4. A permanent audit record linking source_id → target_id so that
         historic references can be resolved.

    Implementing a partial merge now would silently leave dangling references
    in future modules. This placeholder ensures the endpoint exists, returns
    a clear contract error, and documents what a real implementation needs.

    When implementing:
      @transaction.atomic
      1. Verify both persons exist and their parties are active.
      2. Re-point all downstream FKs (per-module migration list).
      3. Copy addresses / notes / categories not already on target.
      4. Create a MergeAuditRecord(source_id, target_id, merged_by, merged_at).
      5. Deactivate source party.
    """
    raise MergePersonError(
        f"Person merge is not yet implemented. "
        f"Review source (source_id={source_id}) and target (target_id={target_id}) manually "
        f"and migrate references by hand until full merge support ships."
    )


# ─── Category Use Cases ────────────────────────────────────────────────────────

def create_category(*, data: dict, created_by=None):
    """Create a new PartyCategory. Delegates to party_services."""
    return party_services.create_party_category(
        name=data["name"],
        description=data.get("description", ""),
        is_system=False,
    )


def update_category(*, category_id: int, data: dict, updated_by=None):
    """Update a PartyCategory. Delegates to party_services."""
    return party_services.update_party_category(category_id=category_id, **data)


@transaction.atomic
def deactivate_category(*, category_id: int, deactivated_by=None):
    """Soft-deactivate a PartyCategory. Delegates to party_services."""
    return party_services.deactivate_party_category(category_id=category_id)


# ─── Category Assignment Use Cases ────────────────────────────────────────────

@transaction.atomic
def assign_category(*, person_id: int, category_id: int, assigned_by=None):
    """Assign a PartyCategory to the person's Party."""
    person = _get_active_person(person_id)
    return party_services.assign_category_to_party(
        party_id=person.party_id,
        category_id=category_id,
        assigned_by=assigned_by,
    )


def remove_category(*, person_id: int, category_id: int, removed_by=None) -> None:
    """Remove (soft-deactivate) a category assignment from the person's Party."""
    person = _get_person(person_id)
    party_services.remove_category_from_party(
        party_id=person.party_id,
        category_id=category_id,
    )


# ─── Address Use Cases ─────────────────────────────────────────────────────────

@transaction.atomic
def create_address(*, person_id: int, data: dict, created_by=None):
    """Create a new PartyAddress for the person's Party."""
    person = _get_active_person(person_id)
    return party_services.create_party_address(
        party_id=person.party_id,
        label=data.get("label", PartyAddress.Label.HOME),
        line1=data["line1"],
        city=data["city"],
        country=data["country"],
        line2=data.get("line2", ""),
        state_province=data.get("state_province", ""),
        postal_code=data.get("postal_code", ""),
        is_default=data.get("is_default", False),
    )


@transaction.atomic
def update_address(*, person_id: int, address_id: int, data: dict, updated_by=None):
    """Update an existing active address on the person's Party."""
    person = _get_person(person_id)
    return party_services.update_party_address(
        party_id=person.party_id,
        address_id=address_id,
        **data,
    )


# ─── Note Use Cases ────────────────────────────────────────────────────────────

def create_note(*, person_id: int, body: str, author=None):
    """Append an immutable note to the person's Party."""
    person = _get_active_person(person_id)
    return party_services.create_party_note(
        party_id=person.party_id,
        body=body,
        author=author,
    )


# ─── Organization Relation Use Cases ──────────────────────────────────────────

@transaction.atomic
def link_person_to_organization(*, data: dict, created_by=None):
    """
    Link a person's Party to another Party in a specific role.

    data["to_party_id"] is optional until the companies app ships — pass
    it as None to create a pending relationship.

    Replaces the legacy link_person_to_organization(organization_id,
    organization_type) pattern with Party-to-Party semantics.
    """
    person_id = data["person_id"]
    person = _get_active_person(person_id)

    try:
        relation = party_services.link_parties(
            from_party_id=person.party_id,
            to_party_id=data.get("to_party_id"),
            role=data["role"].strip(),
            is_primary=data.get("is_primary", False),
            started_on=data.get("started_on"),
        )
    except RelationshipConflictError:
        raise

    logger.info(
        "Person org relation created: person=%s to_party=%s role=%s by=%s",
        person_id,
        data.get("to_party_id"),
        data["role"],
        getattr(created_by, "email", created_by),
    )
    return relation


def update_organization_relationship(*, relation_id: int, data: dict, updated_by=None):
    """Update mutable fields on a PartyRelationship."""
    try:
        return party_services.update_party_relationship(
            relationship_id=relation_id, **data
        )
    except Exception:
        raise RelationshipNotFoundError(
            f"Organization relation {relation_id} not found."
        ) from None


def close_organization_relationship(*, relation_id: int, closed_by=None):
    """Soft-close a PartyRelationship."""
    return party_services.close_party_relationship(relationship_id=relation_id)
