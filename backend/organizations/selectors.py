"""
selectors.py — read/query layer for the organizations module.

All ORM read logic lives here. Selectors return querysets or model instances;
they never write. Views call selectors directly for GET requests.

Sub-resources (addresses, notes, categories) live on Party;
selectors traverse organization → party → sub-resource.
"""
from django.db.models import Prefetch

from party.models import (
    PartyAddress,
    PartyAttachment,
    PartyCategoryAssignment,
    PartyNote,
)

from .exceptions import OrganizationNotFoundError, MembershipNotFoundError
from .models import Organization, OrganizationMembership


# ─── Organization Selectors ────────────────────────────────────────────────────

def list_organizations(
    *,
    is_active: bool = True,
    search: str = "",
    category_id: int = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """
    Return a paginated dict of organizations with optional filtering.

    Returns:
        {
            "results": list[Organization],
            "count":   int,
            "page":    int,
            "page_size": int,
            "has_next": bool,
        }
    """
    from django.db.models import Q

    qs = Organization.objects.select_related("party", "party__created_by").prefetch_related(
        Prefetch(
            "party__category_assignments",
            queryset=PartyCategoryAssignment.objects.filter(
                is_active=True
            ).select_related("category"),
            to_attr="active_assignments",
        )
    )

    if is_active is not None:
        qs = qs.filter(party__is_active=is_active)

    if search:
        qs = qs.filter(
            Q(legal_name__icontains=search)
            | Q(trading_name__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
            | Q(industry__icontains=search)
        )

    if category_id:
        qs = qs.filter(
            party__category_assignments__category_id=category_id,
            party__category_assignments__is_active=True,
        ).distinct()

    total = qs.count()
    offset = (page - 1) * page_size
    results = list(qs[offset: offset + page_size])

    return {
        "results": results,
        "count": total,
        "page": page,
        "page_size": page_size,
        "has_next": (offset + page_size) < total,
    }


def get_organization_detail(*, org_id: int) -> Organization:
    """
    Return a single Organization with all related data prefetched.

    Raises OrganizationNotFoundError if the organization does not exist.

    Prefetched relations available on the returned instance:
        .party.addresses          — active addresses only, default-first
        .party.active_assignments — active category assignments (to_attr)
        .party.notes              — all notes, newest-first
        .party.attachments        — all attachments, newest-first
        .memberships              — all memberships with person prefetched
    """
    try:
        return (
            Organization.objects.select_related("party", "party__created_by")
            .prefetch_related(
                Prefetch(
                    "party__addresses",
                    queryset=PartyAddress.objects.filter(
                        is_active=True
                    ).order_by("-is_default", "label"),
                ),
                Prefetch(
                    "party__category_assignments",
                    queryset=PartyCategoryAssignment.objects.filter(
                        is_active=True
                    ).select_related("category", "assigned_by"),
                    to_attr="active_assignments",
                ),
                Prefetch(
                    "party__notes",
                    queryset=PartyNote.objects.select_related(
                        "author"
                    ).order_by("-created_at"),
                ),
                Prefetch(
                    "party__attachments",
                    queryset=PartyAttachment.objects.select_related(
                        "uploaded_by"
                    ).order_by("-created_at"),
                ),
                Prefetch(
                    "memberships",
                    queryset=OrganizationMembership.objects.select_related(
                        "person"
                    ).order_by("-is_active", "-started_on", "-created_at"),
                ),
            )
            .get(id=org_id)
        )
    except Organization.DoesNotExist:
        raise OrganizationNotFoundError(f"Organization {org_id} not found.")


# ─── Membership Selectors ──────────────────────────────────────────────────────

def list_memberships(*, org_id: int, is_active: bool = None):
    """Return memberships for an organization, with person prefetched."""
    try:
        org = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        raise OrganizationNotFoundError(f"Organization {org_id} not found.")

    qs = OrganizationMembership.objects.filter(
        organization=org
    ).select_related("person", "person__party")

    if is_active is not None:
        qs = qs.filter(is_active=is_active)

    return qs.order_by("-is_active", "-started_on", "-created_at")


def get_person_memberships(*, person_id: int, is_active: bool = None):
    """
    Return OrganizationMembership rows for a person, with org prefetched.

    Used by people.selectors to embed memberships in PersonDetail.
    """
    from people.models import Person
    from people.exceptions import PersonNotFoundError

    try:
        person = Person.objects.get(id=person_id)
    except Person.DoesNotExist:
        raise PersonNotFoundError(f"Person {person_id} not found.")

    qs = OrganizationMembership.objects.filter(
        person=person
    ).select_related("organization", "organization__party")

    if is_active is not None:
        qs = qs.filter(is_active=is_active)

    return qs.order_by("-is_active", "-started_on", "-created_at")


def get_membership(*, membership_id: int) -> OrganizationMembership:
    """Return a single membership or raise MembershipNotFoundError."""
    try:
        return OrganizationMembership.objects.select_related(
            "person", "organization"
        ).get(id=membership_id)
    except OrganizationMembership.DoesNotExist:
        raise MembershipNotFoundError(f"Membership {membership_id} not found.")


# ─── Address Selectors ─────────────────────────────────────────────────────────

def get_org_addresses(*, org_id: int, active_only: bool = True):
    """Return addresses for an organization. Defaults to active only."""
    try:
        org = Organization.objects.select_related("party").get(id=org_id)
    except Organization.DoesNotExist:
        raise OrganizationNotFoundError(f"Organization {org_id} not found.")

    qs = PartyAddress.objects.filter(party_id=org.party_id)
    if active_only:
        qs = qs.filter(is_active=True)
    return qs.order_by("-is_default", "label")


# ─── Note Selectors ────────────────────────────────────────────────────────────

def get_org_notes(*, org_id: int):
    """Return all notes for an organization, newest first, with author."""
    try:
        org = Organization.objects.select_related("party").get(id=org_id)
    except Organization.DoesNotExist:
        raise OrganizationNotFoundError(f"Organization {org_id} not found.")

    return (
        PartyNote.objects.filter(party_id=org.party_id)
        .select_related("author")
        .order_by("-created_at")
    )


# ─── Category Selectors ────────────────────────────────────────────────────────

def get_org_categories(*, org_id: int, active_only: bool = True):
    """Return category assignments for an organization."""
    try:
        org = Organization.objects.select_related("party").get(id=org_id)
    except Organization.DoesNotExist:
        raise OrganizationNotFoundError(f"Organization {org_id} not found.")

    qs = (
        PartyCategoryAssignment.objects.filter(party_id=org.party_id)
        .select_related("category", "assigned_by")
    )
    if active_only:
        qs = qs.filter(is_active=True)
    return qs.order_by("category__name")
