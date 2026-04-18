"""
services.py — application / use-case layer for the party module.

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
    MergePartyError,
    PartyInactiveError,
    PartyNotFoundError,
    RelationshipConflictError,
    RelationshipNotFoundError,
)
from .models import (
    Party,
    PartyAddress,
    PartyCategory,
    PartyCategoryAssignment,
    PartyNote,
    PartyRelationship,
)

logger = logging.getLogger(__name__)


# ─── Party Use Cases ───────────────────────────────────────────────────────────

@transaction.atomic
def create_party(*, party_type: str, created_by=None, is_active: bool = True) -> Party:
    """
    Create a new Party record.

    Typically called by a concrete entity service (e.g. create_person) as the
    first step before creating the entity's own row with a OneToOne link.
    """
    party = Party.objects.create(
        party_type=party_type,
        is_active=is_active,
        created_by=created_by,
    )

    logger.info(
        "Party created: id=%s type=%s by=%s",
        party.id,
        party_type,
        getattr(created_by, "email", created_by),
    )
    return party


@transaction.atomic
def deactivate_party(*, party_id: int) -> Party:
    """
    Soft-deactivate a Party and close all its active relationships and
    category assignments.
    """
    try:
        party = Party.objects.select_for_update().get(id=party_id)
    except Party.DoesNotExist:
        raise PartyNotFoundError(f"Party {party_id} not found.")

    if not party.is_active:
        raise PartyInactiveError(f"Party {party_id} is already inactive.")

    party.is_active = False
    party.save(update_fields=["is_active", "updated_at"])

    PartyRelationship.objects.filter(
        from_party=party, is_active=True
    ).update(is_active=False, ended_on=timezone.now().date())

    PartyRelationship.objects.filter(
        to_party=party, is_active=True
    ).update(is_active=False, ended_on=timezone.now().date())

    PartyCategoryAssignment.objects.filter(
        party=party, is_active=True
    ).update(is_active=False)

    logger.info("Party deactivated: id=%s", party_id)
    return party


# ─── Category Use Cases ────────────────────────────────────────────────────────

def create_party_category(
    *, name: str, description: str = "", is_system: bool = False
) -> PartyCategory:
    """
    Create a new PartyCategory.

    slug is auto-generated from name via django.utils.text.slugify.
    API-created categories always have is_system=False; pass is_system=True
    only from management commands or data migrations.
    """
    name = name.strip()
    slug = slugify(name)

    if PartyCategory.objects.filter(slug=slug).exists():
        raise ValueError(
            f"A category with slug '{slug}' already exists. "
            f"Choose a different name."
        )

    if PartyCategory.objects.filter(name__iexact=name).exists():
        raise ValueError(f"A category named '{name}' already exists.")

    category = PartyCategory.objects.create(
        name=name,
        slug=slug,
        description=description.strip() if description else "",
        is_system=is_system,
    )

    logger.info("PartyCategory created: id=%s slug=%s", category.id, category.slug)
    return category


def update_party_category(*, category_id: int, **fields) -> PartyCategory:
    """
    Update a PartyCategory.

    System categories may not have their name changed because application code
    may depend on their slug values. Their description field may be updated.
    """
    try:
        category = PartyCategory.objects.get(id=category_id)
    except PartyCategory.DoesNotExist:
        raise CategoryNotFoundError(f"Category {category_id} not found.")

    if category.is_system and "name" in fields:
        raise CategorySystemProtectedError(
            f"System-defined category '{category.name}' cannot be renamed. "
            f"Its slug is referenced by application code."
        )

    if "name" in fields:
        new_name = fields["name"].strip()
        new_slug = slugify(new_name)

        if (
            PartyCategory.objects.filter(slug=new_slug)
            .exclude(id=category_id)
            .exists()
        ):
            raise ValueError(f"A category with slug '{new_slug}' already exists.")

        category.name = new_name
        category.slug = new_slug

    if "description" in fields:
        category.description = fields["description"].strip() if fields["description"] else ""

    category.save()

    logger.info("PartyCategory updated: id=%s", category.id)
    return category


@transaction.atomic
def deactivate_party_category(*, category_id: int) -> PartyCategory:
    """
    Soft-deactivate a PartyCategory.

    Also deactivates all PartyCategoryAssignment rows referencing this
    category. System categories cannot be deactivated.
    This operation is idempotent — deactivating an already-inactive category
    returns it unchanged.
    """
    try:
        category = PartyCategory.objects.select_for_update().get(id=category_id)
    except PartyCategory.DoesNotExist:
        raise CategoryNotFoundError(f"Category {category_id} not found.")

    if category.is_system:
        raise CategorySystemProtectedError(
            f"System-defined category '{category.name}' cannot be deactivated."
        )

    if not category.is_active:
        return category  # idempotent

    category.is_active = False
    category.save(update_fields=["is_active", "updated_at"])

    deactivated_count = PartyCategoryAssignment.objects.filter(
        category=category, is_active=True
    ).update(is_active=False)

    logger.info(
        "PartyCategory deactivated: id=%s assignments_closed=%s",
        category.id,
        deactivated_count,
    )
    return category


# ─── Category Assignment Use Cases ────────────────────────────────────────────

@transaction.atomic
def assign_category_to_party(
    *, party_id: int, category_id: int, assigned_by=None
) -> PartyCategoryAssignment:
    """
    Assign a category to a party.

    If an active assignment already exists, DuplicateCategoryAssignmentError
    is raised. If the (party, category) row exists but is_active=False, it is
    reactivated rather than creating a duplicate DB row.
    """
    try:
        party = Party.objects.get(id=party_id, is_active=True)
    except Party.DoesNotExist:
        raise PartyNotFoundError(f"Active party {party_id} not found.")

    try:
        category = PartyCategory.objects.get(id=category_id)
    except PartyCategory.DoesNotExist:
        raise CategoryNotFoundError(f"Category {category_id} not found.")

    if not category.is_active:
        raise CategoryInactiveError(
            f"Category '{category.name}' is inactive and cannot be assigned."
        )

    assignment, created = PartyCategoryAssignment.objects.get_or_create(
        party=party,
        category=category,
        defaults={"assigned_by": assigned_by, "is_active": True},
    )

    if not created:
        if assignment.is_active:
            raise DuplicateCategoryAssignmentError(
                f"Party {party_id} already has an active assignment "
                f"for category '{category.name}'."
            )
        assignment.is_active = True
        assignment.assigned_by = assigned_by
        assignment.save(update_fields=["is_active", "assigned_by", "updated_at"])

    logger.info(
        "Category assigned: party=%s category=%s (created=%s) by=%s",
        party_id,
        category_id,
        created,
        getattr(assigned_by, "email", assigned_by),
    )
    return assignment


def remove_category_from_party(
    *, party_id: int, category_id: int
) -> None:
    """
    Remove (soft-deactivate) a category assignment from a party.

    Raises DuplicateCategoryAssignmentError if there is no active assignment
    to remove.
    """
    try:
        assignment = PartyCategoryAssignment.objects.get(
            party_id=party_id,
            category_id=category_id,
            is_active=True,
        )
    except PartyCategoryAssignment.DoesNotExist:
        raise DuplicateCategoryAssignmentError(
            f"No active category assignment found for "
            f"party={party_id}, category={category_id}."
        )

    assignment.is_active = False
    assignment.save(update_fields=["is_active", "updated_at"])

    logger.info("Category removed: party=%s category=%s", party_id, category_id)


# ─── Address Use Cases ─────────────────────────────────────────────────────────

@transaction.atomic
def create_party_address(
    *, party_id: int, label: str, line1: str, city: str, country: str, **kwargs
) -> PartyAddress:
    """
    Create a new address for a party.

    If is_default=True, any existing default address for this party is
    demoted so there is at most one default per party at any time.
    """
    try:
        party = Party.objects.get(id=party_id, is_active=True)
    except Party.DoesNotExist:
        raise PartyNotFoundError(f"Active party {party_id} not found.")

    is_default = kwargs.get("is_default", False)

    if is_default:
        PartyAddress.objects.filter(party=party, is_default=True).update(is_default=False)

    address = PartyAddress.objects.create(
        party=party,
        label=label,
        line1=line1,
        line2=kwargs.get("line2", ""),
        city=city,
        state_province=kwargs.get("state_province", ""),
        postal_code=kwargs.get("postal_code", ""),
        country=country,
        is_default=is_default,
    )

    return address


@transaction.atomic
def update_party_address(*, party_id: int, address_id: int, **fields) -> PartyAddress:
    """
    Update an existing active address.

    If is_default is being set to True, any other default address for
    this party is demoted first.
    """
    try:
        address = PartyAddress.objects.get(
            id=address_id,
            party_id=party_id,
            is_active=True,
        )
    except PartyAddress.DoesNotExist:
        raise AddressNotFoundError(
            f"Address {address_id} not found for party {party_id}."
        )

    if fields.get("is_default") and not address.is_default:
        PartyAddress.objects.filter(
            party_id=party_id, is_default=True
        ).exclude(id=address_id).update(is_default=False)

    updatable = [
        "label", "line1", "line2", "city",
        "state_province", "postal_code", "country", "is_default",
    ]
    for field in updatable:
        if field in fields:
            setattr(address, field, fields[field])

    address.save()
    return address


@transaction.atomic
def deactivate_party_address(*, party_id: int, address_id: int) -> PartyAddress:
    """Soft-deactivate an address. Idempotent — returns unchanged if already inactive."""
    try:
        address = PartyAddress.objects.get(id=address_id, party_id=party_id)
    except PartyAddress.DoesNotExist:
        raise AddressNotFoundError(
            f"Address {address_id} not found for party {party_id}."
        )

    if not address.is_active:
        return address  # idempotent

    address.is_active = False
    address.save(update_fields=["is_active", "updated_at"])
    return address


@transaction.atomic
def set_default_address(*, party_id: int, address_id: int) -> PartyAddress:
    """
    Make address_id the default for party_id, clearing any other default.

    Raises AddressNotFoundError if the address does not exist and is active
    for this party.
    """
    try:
        address = PartyAddress.objects.get(
            id=address_id, party_id=party_id, is_active=True
        )
    except PartyAddress.DoesNotExist:
        raise AddressNotFoundError(
            f"Address {address_id} not found for party {party_id}."
        )

    PartyAddress.objects.filter(
        party_id=party_id, is_default=True
    ).exclude(id=address_id).update(is_default=False)

    address.is_default = True
    address.save(update_fields=["is_default", "updated_at"])
    return address


# ─── Note Use Cases ────────────────────────────────────────────────────────────

def create_party_note(*, party_id: int, body: str, author=None) -> PartyNote:
    """
    Append an immutable note to a party.

    Notes cannot be edited or deleted after creation — they are audit records.
    """
    try:
        party = Party.objects.get(id=party_id, is_active=True)
    except Party.DoesNotExist:
        raise PartyNotFoundError(f"Active party {party_id} not found.")

    if not body or not body.strip():
        raise ValueError("Note body cannot be empty.")

    note = PartyNote.objects.create(
        party=party,
        body=body.strip(),
        author=author,
    )
    return note


# ─── Relationship Use Cases ────────────────────────────────────────────────────

@transaction.atomic
def link_parties(
    *,
    from_party_id: int,
    to_party_id: int,
    role: str,
    is_primary: bool = False,
    started_on=None,
) -> PartyRelationship:
    """
    Link two parties in a directed role relationship.

    Prevents creating a duplicate *active* relationship for the same
    (from_party, to_party, role) combination.
    """
    try:
        from_party = Party.objects.get(id=from_party_id, is_active=True)
    except Party.DoesNotExist:
        raise PartyNotFoundError(f"Active party {from_party_id} not found.")

    try:
        to_party = Party.objects.get(id=to_party_id, is_active=True)
    except Party.DoesNotExist:
        raise PartyNotFoundError(f"Active party {to_party_id} not found.")

    role = role.strip()

    active_exists = PartyRelationship.objects.filter(
        from_party=from_party,
        to_party=to_party,
        role=role,
        is_active=True,
    ).exists()

    if active_exists:
        raise RelationshipConflictError(
            f"An active relationship already exists for "
            f"from_party={from_party_id}, to_party={to_party_id}, "
            f"role='{role}'. Close the existing relationship before re-linking."
        )

    relationship = PartyRelationship.objects.create(
        from_party=from_party,
        to_party=to_party,
        role=role,
        is_primary=is_primary,
        started_on=started_on,
    )

    logger.info(
        "Party relationship created: id=%s from=%s to=%s role=%s",
        relationship.id,
        from_party_id,
        to_party_id,
        role,
    )
    return relationship


def update_party_relationship(*, relationship_id: int, **fields) -> PartyRelationship:
    """
    Update mutable fields on a party relationship.
    Only role, is_primary, and started_on may be changed.
    """
    try:
        relationship = PartyRelationship.objects.get(id=relationship_id)
    except PartyRelationship.DoesNotExist:
        raise RelationshipNotFoundError(
            f"Party relationship {relationship_id} not found."
        )

    for field in ["role", "is_primary", "started_on"]:
        if field in fields:
            setattr(relationship, field, fields[field])

    relationship.save()
    return relationship


def close_party_relationship(
    *, relationship_id: int, ended_on=None
) -> PartyRelationship:
    """
    Soft-close a party relationship.

    Sets is_active=False and ended_on to the provided date (or today).
    This operation is idempotent — closing an already-closed relationship
    returns it unchanged without raising.
    """
    try:
        relationship = PartyRelationship.objects.get(id=relationship_id)
    except PartyRelationship.DoesNotExist:
        raise RelationshipNotFoundError(
            f"Party relationship {relationship_id} not found."
        )

    if not relationship.is_active:
        return relationship  # idempotent

    relationship.is_active = False
    relationship.ended_on = ended_on or timezone.now().date()
    relationship.save(update_fields=["is_active", "ended_on", "updated_at"])

    logger.info("Party relationship closed: id=%s", relationship_id)
    return relationship


# ─── Merge Placeholder ────────────────────────────────────────────────────────

def merge_parties(*, source_id: int, target_id: int, merged_by=None) -> None:
    """
    Merge contract placeholder (HTTP 501).

    Full merge is intentionally not yet implemented because it requires:

      1. Knowing all cross-module FK dependencies (persons, companies,
         invoices, etc.) that reference the source party — none of those
         modules reference Party directly yet.
      2. A policy decision on which record's field values take precedence.
      3. Deduplication of category assignments and relationships on target
         after re-pointing.
      4. A permanent audit record linking source_id → target_id so that
         historic references can be resolved.

    Implementing a partial merge now would silently leave dangling references
    in future modules. This placeholder ensures the endpoint exists, returns
    a clear contract error, and documents what a real implementation needs.
    """
    raise MergePartyError(
        f"Party merge is not yet implemented. "
        f"Review source (source_id={source_id}) and target (target_id={target_id}) manually "
        f"and migrate references by hand until full merge support ships."
    )
