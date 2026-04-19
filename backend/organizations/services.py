"""
services.py — application / use-case layer for the organizations module.

All business logic, write workflows, and transactional operations live here.
Views call services; services call models and raise domain exceptions.
No ORM queries outside of services and selectors.

Shared sub-resource operations (addresses, notes, categories) delegate to
party.services — Party is the owner of those resources.
"""
import logging

from django.db import transaction
from django.utils import timezone

import party.services as party_services
from party.exceptions import (
    DuplicateCategoryAssignmentError,
    AddressNotFoundError,
)
from party.models import Party, PartyAddress

from .exceptions import (
    MembershipConflictError,
    MembershipNotFoundError,
    MergeOrganizationError,
    OrganizationInactiveError,
    OrganizationNotFoundError,
)
from .models import Organization, OrganizationMembership

logger = logging.getLogger(__name__)


# ─── Internal Helpers ──────────────────────────────────────────────────────────

def _get_org(org_id: int) -> Organization:
    try:
        return Organization.objects.select_related("party").get(id=org_id)
    except Organization.DoesNotExist:
        raise OrganizationNotFoundError(f"Organization {org_id} not found.")


def _get_active_org(org_id: int) -> Organization:
    org = _get_org(org_id)
    if not org.party.is_active:
        raise OrganizationInactiveError(
            f"Organization {org_id} is inactive. Reactivate it first."
        )
    return org


# ─── Organization Use Cases ────────────────────────────────────────────────────

@transaction.atomic
def create_organization(*, data: dict, created_by=None) -> Organization:
    """
    Create a new Organization record, atomically creating its Party first.

    The Party is always created with party_type=ORGANIZATION. This invariant
    is enforced here — no caller should create an Organization party manually.
    """
    party = party_services.create_party(
        party_type=Party.PartyType.ORGANIZATION,
        created_by=created_by,
        is_active=True,
    )

    org = Organization.objects.create(
        party=party,
        legal_name=data["legal_name"].strip(),
        trading_name=data.get("trading_name", "").strip(),
        registration_number=data.get("registration_number", "").strip(),
        tax_id=data.get("tax_id", "").strip(),
        website=data.get("website", ""),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        industry=data.get("industry", "").strip(),
    )

    logger.info(
        "Organization created: id=%s legal_name=%s by=%s",
        org.id,
        org.legal_name,
        getattr(created_by, "email", created_by),
    )
    return org


@transaction.atomic
def update_organization(*, org_id: int, data: dict, updated_by=None) -> Organization:
    """Update mutable fields on an Organization record."""
    try:
        org = (
            Organization.objects.select_related("party")
            .select_for_update()
            .get(id=org_id)
        )
    except Organization.DoesNotExist:
        raise OrganizationNotFoundError(f"Organization {org_id} not found.")

    if not org.party.is_active:
        raise OrganizationInactiveError(
            f"Cannot update an inactive organization (id={org_id}). "
            f"Reactivate it first."
        )

    updatable_fields = [
        "legal_name", "trading_name", "registration_number",
        "tax_id", "website", "email", "phone", "industry",
    ]
    for field in updatable_fields:
        if field in data:
            value = data[field]
            if isinstance(value, str) and field in ("legal_name", "trading_name", "registration_number", "tax_id", "industry"):
                value = value.strip()
            setattr(org, field, value)

    org.save()

    logger.info(
        "Organization updated: id=%s by=%s",
        org.id,
        getattr(updated_by, "email", updated_by),
    )
    return org


@transaction.atomic
def deactivate_organization(*, org_id: int, deactivated_by=None) -> Organization:
    """
    Soft-deactivate an Organization via its Party.

    Delegates to party_services.deactivate_party() which also closes all
    active PartyRelationships and deactivates all active PartyCategoryAssignments.
    Also ends all active OrganizationMembership rows.
    """
    try:
        org = (
            Organization.objects.select_related("party")
            .select_for_update()
            .get(id=org_id)
        )
    except Organization.DoesNotExist:
        raise OrganizationNotFoundError(f"Organization {org_id} not found.")

    if not org.party.is_active:
        raise OrganizationInactiveError(f"Organization {org_id} is already inactive.")

    party_services.deactivate_party(party_id=org.party_id)

    OrganizationMembership.objects.filter(
        organization=org, is_active=True
    ).update(is_active=False, ended_on=timezone.now().date())

    logger.info(
        "Organization deactivated: id=%s by=%s",
        org.id,
        getattr(deactivated_by, "email", deactivated_by),
    )
    return org


@transaction.atomic
def reactivate_organization(*, org_id: int, reactivated_by=None) -> Organization:
    """Reactivate a previously deactivated Organization via its Party."""
    try:
        org = (
            Organization.objects.select_related("party")
            .select_for_update()
            .get(id=org_id)
        )
    except Organization.DoesNotExist:
        raise OrganizationNotFoundError(f"Organization {org_id} not found.")

    if org.party.is_active:
        raise OrganizationInactiveError(f"Organization {org_id} is already active.")

    party_services.reactivate_party(party_id=org.party_id)

    logger.info(
        "Organization reactivated: id=%s by=%s",
        org.id,
        getattr(reactivated_by, "email", reactivated_by),
    )
    return org


def merge_organizations(*, source_id: int, target_id: int, merged_by=None) -> None:
    """
    Merge contract placeholder (HTTP 501).

    Full merge requires cross-module FK resolution (invoices, contracts, etc.)
    that don't exist yet. See people.services.merge_persons for the documented
    implementation contract — same pattern applies here.
    """
    raise MergeOrganizationError(
        f"Organization merge is not yet implemented. "
        f"Review source (source_id={source_id}) and target (target_id={target_id}) manually."
    )


# ─── Membership Use Cases ──────────────────────────────────────────────────────

@transaction.atomic
def add_member(
    *,
    org_id: int,
    person_id: int,
    role: str,
    is_primary: bool = False,
    started_on=None,
    added_by=None,
) -> OrganizationMembership:
    """
    Add a Person as a member of an Organization in a given role.

    Raises MembershipConflictError if an active membership for the same
    (person, organization, role) combination already exists.

    The unique_together constraint prevents duplicate DB rows regardless of
    is_active; callers must end_membership then add_member again to model a
    re-hire with the same role.
    """
    from people.models import Person
    from people.exceptions import PersonNotFoundError, PersonInactiveError

    org = _get_active_org(org_id)

    try:
        person = Person.objects.select_related("party").get(id=person_id)
    except Person.DoesNotExist:
        raise PersonNotFoundError(f"Person {person_id} not found.")

    if not person.party.is_active:
        raise PersonInactiveError(
            f"Person {person_id} is inactive. Reactivate the person first."
        )

    role = role.strip()

    active_exists = OrganizationMembership.objects.filter(
        organization=org,
        person=person,
        role=role,
        is_active=True,
    ).exists()

    if active_exists:
        raise MembershipConflictError(
            f"Person {person_id} already has an active '{role}' membership "
            f"in organization {org_id}. End the existing membership first."
        )

    membership = OrganizationMembership.objects.create(
        organization=org,
        person=person,
        role=role,
        is_primary=is_primary,
        started_on=started_on,
    )

    logger.info(
        "Membership created: id=%s org=%s person=%s role=%s by=%s",
        membership.id,
        org_id,
        person_id,
        role,
        getattr(added_by, "email", added_by),
    )
    return membership


def update_membership(*, membership_id: int, data: dict, updated_by=None) -> OrganizationMembership:
    """Update mutable fields on a membership: role, is_primary, started_on."""
    try:
        membership = OrganizationMembership.objects.get(id=membership_id)
    except OrganizationMembership.DoesNotExist:
        raise MembershipNotFoundError(f"Membership {membership_id} not found.")

    for field in ["role", "is_primary", "started_on"]:
        if field in data:
            setattr(membership, field, data[field])

    membership.save()
    return membership


def end_membership(*, membership_id: int, ended_by=None) -> OrganizationMembership:
    """
    Soft-end an OrganizationMembership.

    Sets is_active=False and ended_on=today. Idempotent — ending an already
    inactive membership returns it unchanged without raising.
    """
    try:
        membership = OrganizationMembership.objects.get(id=membership_id)
    except OrganizationMembership.DoesNotExist:
        raise MembershipNotFoundError(f"Membership {membership_id} not found.")

    if not membership.is_active:
        return membership  # idempotent

    membership.is_active = False
    membership.ended_on = timezone.now().date()
    membership.save(update_fields=["is_active", "ended_on", "updated_at"])

    logger.info("Membership ended: id=%s by=%s", membership_id, getattr(ended_by, "email", ended_by))
    return membership


# ─── Category Use Cases (delegated) ───────────────────────────────────────────

def assign_category(*, org_id: int, category_id: int, assigned_by=None):
    """Assign a PartyCategory to the organization's Party."""
    org = _get_active_org(org_id)
    return party_services.assign_category_to_party(
        party_id=org.party_id,
        category_id=category_id,
        assigned_by=assigned_by,
    )


def remove_category(*, org_id: int, category_id: int, removed_by=None) -> None:
    """Remove (soft-deactivate) a category assignment from the organization's Party."""
    org = _get_org(org_id)
    party_services.remove_category_from_party(
        party_id=org.party_id,
        category_id=category_id,
    )


# ─── Address Use Cases (delegated) ────────────────────────────────────────────

@transaction.atomic
def create_address(*, org_id: int, data: dict, created_by=None):
    """Create a new PartyAddress for the organization's Party."""
    org = _get_active_org(org_id)
    return party_services.create_party_address(
        party_id=org.party_id,
        label=data.get("label", PartyAddress.Label.WORK),
        line1=data["line1"],
        city=data["city"],
        country=data["country"],
        line2=data.get("line2", ""),
        state_province=data.get("state_province", ""),
        postal_code=data.get("postal_code", ""),
        is_default=data.get("is_default", False),
    )


@transaction.atomic
def update_address(*, org_id: int, address_id: int, data: dict, updated_by=None):
    """Update an existing active address on the organization's Party."""
    org = _get_org(org_id)
    return party_services.update_party_address(
        party_id=org.party_id,
        address_id=address_id,
        **data,
    )


# ─── Note Use Cases (delegated) ───────────────────────────────────────────────

def create_note(*, org_id: int, body: str, author=None):
    """Append an immutable note to the organization's Party."""
    org = _get_active_org(org_id)
    return party_services.create_party_note(
        party_id=org.party_id,
        body=body,
        author=author,
    )
