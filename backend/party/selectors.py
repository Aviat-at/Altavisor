"""
selectors.py — read/query layer for the party module.

All ORM read logic lives here. Selectors return querysets or model instances;
they never write. Views call selectors directly for GET requests.
"""
from .exceptions import PartyNotFoundError
from .models import (
    Party,
    PartyAddress,
    PartyCategory,
    PartyNote,
    PartyRelationship,
)


# ─── Party Selectors ───────────────────────────────────────────────────────────

def get_party_by_id(*, party_id: int) -> Party:
    """Return a single Party or raise PartyNotFoundError."""
    try:
        return Party.objects.get(id=party_id)
    except Party.DoesNotExist:
        raise PartyNotFoundError(f"Party {party_id} not found.")


# ─── Category Selectors ────────────────────────────────────────────────────────

def get_party_categories(*, is_active=None):
    """
    Return a queryset of PartyCategory with optional is_active filter.

    Passing None omits the filter (returns both active and inactive).
    """
    qs = PartyCategory.objects.all()
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs.order_by("name")


# ─── Address Selectors ─────────────────────────────────────────────────────────

def get_party_addresses(*, party_id: int, is_active=True):
    """Return addresses for a party. Defaults to active only."""
    qs = PartyAddress.objects.filter(party_id=party_id)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    return qs.order_by("-is_default", "label")


# ─── Note Selectors ────────────────────────────────────────────────────────────

def get_party_notes(*, party_id: int):
    """Return all notes for a party, newest first, with author."""
    return (
        PartyNote.objects.filter(party_id=party_id)
        .select_related("author")
        .order_by("-created_at")
    )


# ─── Relationship Selectors ────────────────────────────────────────────────────

def get_party_relationships(
    *, from_party_id: int = None, to_party_id: int = None, is_active=None
):
    """
    Return party relationships with optional filters.

    Passing None for a filter omits it.
    At least one of from_party_id or to_party_id should typically be provided.
    """
    qs = PartyRelationship.objects.select_related("from_party", "to_party")

    if from_party_id is not None:
        qs = qs.filter(from_party_id=from_party_id)

    if to_party_id is not None:
        qs = qs.filter(to_party_id=to_party_id)

    if is_active is not None:
        qs = qs.filter(is_active=is_active)

    return qs.order_by("-is_active", "-started_on", "-created_at")
