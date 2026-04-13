"""
services.py — application / use-case layer for the people module.

All business logic, write workflows, and transactional operations live here.
Views call services; services call models and raise domain exceptions.
No ORM queries outside of services and selectors.
"""
import logging

from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from .exceptions import (
    AddressNotFoundError,
    CategoryInactiveError,
    CategoryNotFoundError,
    CategorySystemProtectedError,
    DuplicateCategoryAssignmentError,
    DuplicatePersonError,
    MergePersonError,
    OrganizationRelationConflictError,
    OrganizationRelationNotFoundError,
    PersonInactiveError,
    PersonNotFoundError,
)
from .models import (
    OrganizationPersonRelation,
    Person,
    PersonAddress,
    PersonCategory,
    PersonCategoryAssignment,
    PersonNote,
)

logger = logging.getLogger(__name__)


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
        for p in Person.objects.filter(email__iexact=email.strip(), is_active=True):
            if p.id not in seen_ids:
                candidates.append({"person": p, "reason": "email_match"})
                seen_ids.add(p.id)

    # Medium confidence: same full name (case-insensitive)
    for p in Person.objects.filter(
        first_name__iexact=first_name.strip(),
        last_name__iexact=last_name.strip(),
        is_active=True,
    ):
        if p.id not in seen_ids:
            candidates.append({"person": p, "reason": "name_match"})
            seen_ids.add(p.id)

    # Medium confidence: phone or mobile match
    if phone and phone.strip():
        for p in Person.objects.filter(
            Q(phone=phone.strip()) | Q(mobile=phone.strip()),
            is_active=True,
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
    """
    Internal helper. Runs duplicate detection and raises DuplicatePersonError
    with the candidate list if any duplicates are found.

    exclude_id is used during updates to exclude the person being edited.
    """
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
    Create a new Person record.

    Duplicate detection runs before creation. If likely duplicates exist,
    DuplicatePersonError is raised with the candidate list so the caller
    (view) can surface them to the user.

    Set data["force"] = True to bypass duplicate detection and create anyway.
    This is the correct pattern for cases where the user has reviewed the
    candidates and confirmed the new record is intentional.
    """
    force = data.pop("force", False)

    if not force:
        _check_duplicates_or_raise(
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            email=data.get("email", "") or "",
            phone=data.get("phone", ""),
        )

    person = Person.objects.create(
        first_name=data["first_name"].strip(),
        last_name=data["last_name"].strip(),
        preferred_name=data.get("preferred_name", "").strip(),
        # Store None instead of empty string to preserve unique constraint
        email=data.get("email") or None,
        phone=data.get("phone", ""),
        mobile=data.get("mobile", ""),
        date_of_birth=data.get("date_of_birth"),
        gender=data.get("gender", ""),
        created_by=created_by,
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

    Re-runs duplicate detection with the post-update values, excluding
    the record being edited so it does not flag itself.
    """
    try:
        person = Person.objects.select_for_update().get(id=person_id)
    except Person.DoesNotExist:
        raise PersonNotFoundError(f"Person {person_id} not found.")

    if not person.is_active:
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

    # Email is nullable unique — handle separately to avoid storing ""
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
    Soft-deactivate a Person.

    Also closes all active OrganizationPersonRelations and deactivates all
    active PersonCategoryAssignments for this person so the person's data
    remains internally consistent after deactivation.
    """
    try:
        person = Person.objects.select_for_update().get(id=person_id)
    except Person.DoesNotExist:
        raise PersonNotFoundError(f"Person {person_id} not found.")

    if not person.is_active:
        raise PersonInactiveError(f"Person {person_id} is already inactive.")

    person.is_active = False
    person.save(update_fields=["is_active", "updated_at"])

    # Close all active org relations
    OrganizationPersonRelation.objects.filter(
        person=person, is_active=True
    ).update(is_active=False, ended_on=timezone.now().date())

    # Deactivate all active category assignments
    PersonCategoryAssignment.objects.filter(
        person=person, is_active=True
    ).update(is_active=False)

    logger.info(
        "Person deactivated: id=%s by=%s",
        person.id,
        getattr(deactivated_by, "email", deactivated_by),
    )
    return person


@transaction.atomic
def reactivate_person(*, person_id: int, reactivated_by=None) -> Person:
    """
    Reactivate a previously deactivated Person.
    """
    try:
        person = Person.objects.select_for_update().get(id=person_id)
    except Person.DoesNotExist:
        raise PersonNotFoundError(f"Person {person_id} not found.")

    if person.is_active:
        raise PersonInactiveError(f"Person {person_id} is already active.")

    person.is_active = True
    person.save(update_fields=["is_active", "updated_at"])

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
      3. Deduplication of category assignments and org relations on target
         after re-pointing.
      4. A permanent audit record linking source_id → target_id so that
         historic references can be resolved.

    Implementing a partial merge now would silently leave dangling references
    in future modules. This placeholder ensures the endpoint exists, returns
    a clear contract error, and documents what a real implementation needs.

    When implementing:
      @transaction.atomic
      1. Verify both persons exist and are active.
      2. Re-point all downstream FKs (per-module migration list).
      3. Copy addresses / notes / categories not already on target.
      4. Create a MergeAuditRecord(source_id, target_id, merged_by, merged_at).
      5. Deactivate source person.
    """
    raise MergePersonError(
        f"Person merge is not yet implemented. "
        f"Review source (source_id={source_id}) and target (target_id={target_id}) manually "
        f"and migrate references by hand until full merge support ships."
    )


# ─── Category Use Cases ────────────────────────────────────────────────────────

def create_category(*, data: dict, created_by=None) -> PersonCategory:
    """
    Create a new PersonCategory.

    slug is auto-generated from name via django.utils.text.slugify so the
    caller never needs to supply it. Uniqueness is validated before creation.

    API-created categories always have is_system=False.
    System categories are seeded via management commands or data migrations.
    """
    name = data["name"].strip()
    slug = slugify(name)

    if PersonCategory.objects.filter(slug=slug).exists():
        raise ValueError(
            f"A category with slug '{slug}' already exists. "
            f"Choose a different name."
        )

    if PersonCategory.objects.filter(name__iexact=name).exists():
        raise ValueError(
            f"A category named '{name}' already exists."
        )

    category = PersonCategory.objects.create(
        name=name,
        slug=slug,
        description=data.get("description", "").strip(),
        is_system=False,
    )

    logger.info(
        "PersonCategory created: id=%s slug=%s by=%s",
        category.id,
        category.slug,
        getattr(created_by, "email", created_by),
    )
    return category


def update_category(
    *, category_id: int, data: dict, updated_by=None
) -> PersonCategory:
    """
    Update a PersonCategory.

    System categories may not have their name or slug changed because
    application code may depend on their slug values. Their description
    field may be updated.
    """
    try:
        category = PersonCategory.objects.get(id=category_id)
    except PersonCategory.DoesNotExist:
        raise CategoryNotFoundError(f"Category {category_id} not found.")

    if category.is_system and "name" in data:
        raise CategorySystemProtectedError(
            f"System-defined category '{category.name}' cannot be renamed. "
            f"Its slug is referenced by application code."
        )

    if "name" in data:
        new_name = data["name"].strip()
        new_slug = slugify(new_name)

        if (
            PersonCategory.objects.filter(slug=new_slug)
            .exclude(id=category_id)
            .exists()
        ):
            raise ValueError(
                f"A category with slug '{new_slug}' already exists."
            )

        category.name = new_name
        category.slug = new_slug

    if "description" in data:
        category.description = data["description"].strip() if data["description"] else ""

    category.save()

    logger.info(
        "PersonCategory updated: id=%s by=%s",
        category.id,
        getattr(updated_by, "email", updated_by),
    )
    return category


@transaction.atomic
def deactivate_category(
    *, category_id: int, deactivated_by=None
) -> PersonCategory:
    """
    Soft-deactivate a PersonCategory.

    Also deactivates all PersonCategoryAssignment rows referencing this
    category so that persons no longer appear as having this category
    assigned after it is removed from active use.

    System categories cannot be deactivated.
    This operation is idempotent — deactivating an already-inactive category
    returns it unchanged.
    """
    try:
        category = PersonCategory.objects.select_for_update().get(id=category_id)
    except PersonCategory.DoesNotExist:
        raise CategoryNotFoundError(f"Category {category_id} not found.")

    if category.is_system:
        raise CategorySystemProtectedError(
            f"System-defined category '{category.name}' cannot be deactivated."
        )

    if not category.is_active:
        return category  # idempotent

    category.is_active = False
    category.save(update_fields=["is_active", "updated_at"])

    deactivated_count = PersonCategoryAssignment.objects.filter(
        category=category, is_active=True
    ).update(is_active=False)

    logger.info(
        "PersonCategory deactivated: id=%s assignments_closed=%s by=%s",
        category.id,
        deactivated_count,
        getattr(deactivated_by, "email", deactivated_by),
    )
    return category


# ─── Category Assignment Use Cases ────────────────────────────────────────────

@transaction.atomic
def assign_category(
    *, person_id: int, category_id: int, assigned_by=None
) -> PersonCategoryAssignment:
    """
    Assign a category to a person.

    If an active assignment already exists, DuplicateCategoryAssignmentError
    is raised so the caller can surface a clear message.

    If the (person, category) row exists but is_active=False (was previously
    removed), it is reactivated rather than creating a duplicate DB row —
    the unique_together constraint requires this.
    """
    try:
        person = Person.objects.get(id=person_id, is_active=True)
    except Person.DoesNotExist:
        raise PersonNotFoundError(
            f"Active person {person_id} not found."
        )

    try:
        category = PersonCategory.objects.get(id=category_id)
    except PersonCategory.DoesNotExist:
        raise CategoryNotFoundError(f"Category {category_id} not found.")

    if not category.is_active:
        raise CategoryInactiveError(
            f"Category '{category.name}' is inactive and cannot be assigned."
        )

    assignment, created = PersonCategoryAssignment.objects.get_or_create(
        person=person,
        category=category,
        defaults={"assigned_by": assigned_by, "is_active": True},
    )

    if not created:
        if assignment.is_active:
            raise DuplicateCategoryAssignmentError(
                f"Person {person_id} already has an active assignment "
                f"for category '{category.name}'."
            )
        # Reactivate a previously removed assignment
        assignment.is_active = True
        assignment.assigned_by = assigned_by
        assignment.save(update_fields=["is_active", "assigned_by", "updated_at"])

    logger.info(
        "Category assigned: person=%s category=%s (created=%s) by=%s",
        person_id,
        category_id,
        created,
        getattr(assigned_by, "email", assigned_by),
    )
    return assignment


def remove_category(
    *, person_id: int, category_id: int, removed_by=None
) -> None:
    """
    Remove (soft-deactivate) a category assignment from a person.

    Raises DuplicateCategoryAssignmentError if there is no active assignment
    to remove (re-using the exception for "assignment state mismatch").
    """
    try:
        assignment = PersonCategoryAssignment.objects.get(
            person_id=person_id,
            category_id=category_id,
            is_active=True,
        )
    except PersonCategoryAssignment.DoesNotExist:
        raise DuplicateCategoryAssignmentError(
            f"No active category assignment found for "
            f"person={person_id}, category={category_id}."
        )

    assignment.is_active = False
    assignment.save(update_fields=["is_active", "updated_at"])

    logger.info(
        "Category removed: person=%s category=%s by=%s",
        person_id,
        category_id,
        getattr(removed_by, "email", removed_by),
    )


# ─── Address Use Cases ─────────────────────────────────────────────────────────

@transaction.atomic
def create_address(*, person_id: int, data: dict, created_by=None) -> PersonAddress:
    """
    Create a new address for a person.

    If is_default=True, any existing default address for this person is
    demoted so there is at most one default per person at any time.
    """
    try:
        person = Person.objects.get(id=person_id, is_active=True)
    except Person.DoesNotExist:
        raise PersonNotFoundError(f"Active person {person_id} not found.")

    if data.get("is_default"):
        PersonAddress.objects.filter(
            person=person, is_default=True
        ).update(is_default=False)

    address = PersonAddress.objects.create(
        person=person,
        label=data.get("label", PersonAddress.Label.HOME),
        line1=data["line1"],
        line2=data.get("line2", ""),
        city=data["city"],
        state_province=data.get("state_province", ""),
        postal_code=data.get("postal_code", ""),
        country=data["country"],
        is_default=data.get("is_default", False),
    )

    return address


@transaction.atomic
def update_address(
    *, person_id: int, address_id: int, data: dict, updated_by=None
) -> PersonAddress:
    """
    Update an existing active address.

    If is_default is being set to True, any other default address for
    this person is demoted first.
    """
    try:
        address = PersonAddress.objects.get(
            id=address_id,
            person_id=person_id,
            is_active=True,
        )
    except PersonAddress.DoesNotExist:
        raise AddressNotFoundError(
            f"Address {address_id} not found for person {person_id}."
        )

    if data.get("is_default") and not address.is_default:
        PersonAddress.objects.filter(
            person_id=person_id, is_default=True
        ).exclude(id=address_id).update(is_default=False)

    updatable = [
        "label", "line1", "line2", "city",
        "state_province", "postal_code", "country", "is_default",
    ]
    for field in updatable:
        if field in data:
            setattr(address, field, data[field])

    address.save()
    return address


# ─── Note Use Cases ────────────────────────────────────────────────────────────

def create_note(*, person_id: int, body: str, author=None) -> PersonNote:
    """
    Append an immutable note to a person.

    Notes cannot be edited or deleted after creation — they are audit records.
    """
    try:
        person = Person.objects.get(id=person_id, is_active=True)
    except Person.DoesNotExist:
        raise PersonNotFoundError(f"Active person {person_id} not found.")

    if not body or not body.strip():
        raise ValueError("Note body cannot be empty.")

    note = PersonNote.objects.create(
        person=person,
        body=body.strip(),
        author=author,
    )
    return note


# ─── Organization Relation Use Cases ──────────────────────────────────────────

@transaction.atomic
def link_person_to_organization(
    *, data: dict, created_by=None
) -> OrganizationPersonRelation:
    """
    Link a person to an organization in a specific role.

    Prevents creating a duplicate *active* relation for the same
    (person, organization_id, organization_type, role) combination.

    A previously closed relation for the same combination is a different
    temporal record and does not block creating a new active one — the
    unique_together constraint is on the four columns, so a second row
    with the same combination would still violate it. The service raises
    OrganizationRelationConflictError only when is_active=True already exists,
    so callers must close the existing relation before re-linking.
    """
    person_id = data["person_id"]
    organization_id = data["organization_id"]
    organization_type = data["organization_type"].strip()
    role = data["role"].strip()

    try:
        person = Person.objects.get(id=person_id, is_active=True)
    except Person.DoesNotExist:
        raise PersonNotFoundError(f"Active person {person_id} not found.")

    active_exists = OrganizationPersonRelation.objects.filter(
        person=person,
        organization_id=organization_id,
        organization_type=organization_type,
        role=role,
        is_active=True,
    ).exists()

    if active_exists:
        raise OrganizationRelationConflictError(
            f"An active relation already exists for "
            f"person={person_id}, {organization_type}#{organization_id}, "
            f"role='{role}'. Close the existing relation before re-linking."
        )

    relation = OrganizationPersonRelation.objects.create(
        person=person,
        organization_id=organization_id,
        organization_type=organization_type,
        role=role,
        is_primary=data.get("is_primary", False),
        started_on=data.get("started_on"),
    )

    logger.info(
        "Org relation created: person=%s %s#%s role=%s by=%s",
        person_id,
        organization_type,
        organization_id,
        role,
        getattr(created_by, "email", created_by),
    )
    return relation


def update_organization_relationship(
    *, relation_id: int, data: dict, updated_by=None
) -> OrganizationPersonRelation:
    """
    Update mutable fields on an organization-person relation.
    Only role, is_primary, and started_on may be changed.
    """
    try:
        relation = OrganizationPersonRelation.objects.get(id=relation_id)
    except OrganizationPersonRelation.DoesNotExist:
        raise OrganizationRelationNotFoundError(
            f"Organization relation {relation_id} not found."
        )

    for field in ["role", "is_primary", "started_on"]:
        if field in data:
            setattr(relation, field, data[field])

    relation.save()
    return relation


def close_organization_relationship(
    *, relation_id: int, closed_by=None
) -> OrganizationPersonRelation:
    """
    Soft-close an organization-person relation.

    Sets is_active=False and ended_on=today.
    This operation is idempotent — closing an already-closed relation
    returns it unchanged without raising.
    """
    try:
        relation = OrganizationPersonRelation.objects.get(id=relation_id)
    except OrganizationPersonRelation.DoesNotExist:
        raise OrganizationRelationNotFoundError(
            f"Organization relation {relation_id} not found."
        )

    if not relation.is_active:
        return relation  # idempotent

    relation.is_active = False
    relation.ended_on = timezone.now().date()
    relation.save(update_fields=["is_active", "ended_on", "updated_at"])

    logger.info(
        "Org relation closed: id=%s by=%s",
        relation_id,
        getattr(closed_by, "email", closed_by),
    )
    return relation
