"""
selectors.py — read/query layer for the people module.

All ORM read logic lives here. Selectors return querysets or model instances;
they never write. Views call selectors directly for GET requests.
"""
from django.db.models import Prefetch

from .exceptions import CategoryNotFoundError, PersonNotFoundError
from .models import (
    OrganizationPersonRelation,
    Person,
    PersonAddress,
    PersonAttachment,
    PersonCategory,
    PersonCategoryAssignment,
    PersonNote,
)


# ─── Person Selectors ──────────────────────────────────────────────────────────

def list_persons(
    *,
    is_active: bool = True,
    search: str = "",
    category_id: int = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """
    Return a paginated dict of persons with optional filtering.

    Returns:
        {
            "results": list[Person],   # already evaluated
            "count":   int,            # total matching rows before pagination
            "page":    int,
            "page_size": int,
            "has_next": bool,
        }

    active_assignments is attached as a to_attr prefetch so that
    PersonListSerializer can read it without triggering extra queries.
    """
    from django.db.models import Q

    qs = Person.objects.select_related("created_by").prefetch_related(
        Prefetch(
            "category_assignments",
            queryset=PersonCategoryAssignment.objects.filter(
                is_active=True
            ).select_related("category"),
            to_attr="active_assignments",
        )
    )

    if is_active is not None:
        qs = qs.filter(is_active=is_active)

    if search:
        qs = qs.filter(
            Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(preferred_name__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
        )

    if category_id:
        qs = qs.filter(
            category_assignments__category_id=category_id,
            category_assignments__is_active=True,
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


def get_person_detail(*, person_id: int) -> Person:
    """
    Return a single Person with all related data prefetched in one query
    set.

    Raises PersonNotFoundError if the person does not exist (any active
    status).

    Prefetched relations available on the returned instance:
        .addresses          — active addresses only, default-first
        .active_assignments — active category assignments (to_attr)
        .org_relations      — all relations, active-first
        .notes              — all notes, newest-first
        .attachments        — all attachments, newest-first
    """
    try:
        return (
            Person.objects.select_related("created_by")
            .prefetch_related(
                Prefetch(
                    "addresses",
                    queryset=PersonAddress.objects.filter(
                        is_active=True
                    ).order_by("-is_default", "label"),
                ),
                Prefetch(
                    "category_assignments",
                    queryset=PersonCategoryAssignment.objects.filter(
                        is_active=True
                    ).select_related("category", "assigned_by"),
                    to_attr="active_assignments",
                ),
                Prefetch(
                    "org_relations",
                    queryset=OrganizationPersonRelation.objects.order_by(
                        "-is_active", "-started_on", "-created_at"
                    ),
                ),
                Prefetch(
                    "notes",
                    queryset=PersonNote.objects.select_related(
                        "author"
                    ).order_by("-created_at"),
                ),
                Prefetch(
                    "attachments",
                    queryset=PersonAttachment.objects.select_related(
                        "uploaded_by"
                    ).order_by("-created_at"),
                ),
            )
            .get(id=person_id)
        )
    except Person.DoesNotExist:
        raise PersonNotFoundError(f"Person {person_id} not found.")


def search_persons(*, q: str, active_only: bool = True):
    """
    Lightweight name/email search suitable for autocomplete or
    duplicate-check display.

    Returns a queryset — the caller decides slice size.
    """
    from django.db.models import Q

    qs = Person.objects.all()
    if active_only:
        qs = qs.filter(is_active=True)
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
        )
    return qs.order_by("last_name", "first_name")


# ─── Category Selectors ────────────────────────────────────────────────────────

def list_categories(
    *, is_active: bool = None, is_system: bool = None
):
    """
    Return a queryset of PersonCategory with optional filters.

    Passing None for a filter omits it (returns both active and inactive,
    or both system and custom).
    """
    qs = PersonCategory.objects.all()
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    if is_system is not None:
        qs = qs.filter(is_system=is_system)
    return qs.order_by("name")


def get_category(*, category_id: int) -> PersonCategory:
    """Return a single category or raise CategoryNotFoundError."""
    try:
        return PersonCategory.objects.get(id=category_id)
    except PersonCategory.DoesNotExist:
        raise CategoryNotFoundError(f"Category {category_id} not found.")


def get_person_categories(
    *, person_id: int, active_only: bool = True
):
    """
    Return category assignments for a person, with the category
    object pre-fetched via select_related.
    """
    qs = (
        PersonCategoryAssignment.objects.filter(person_id=person_id)
        .select_related("category", "assigned_by")
    )
    if active_only:
        qs = qs.filter(is_active=True)
    return qs.order_by("category__name")


def get_active_person_categories(*, person_id: int):
    """Convenience wrapper: active assignments only."""
    return get_person_categories(person_id=person_id, active_only=True)


# ─── Address Selectors ─────────────────────────────────────────────────────────

def get_person_addresses(*, person_id: int, active_only: bool = True):
    """Return addresses for a person. Defaults to active only."""
    qs = PersonAddress.objects.filter(person_id=person_id)
    if active_only:
        qs = qs.filter(is_active=True)
    return qs.order_by("-is_default", "label")


# ─── Note Selectors ────────────────────────────────────────────────────────────

def get_person_notes(*, person_id: int):
    """Return all notes for a person, newest first, with author."""
    return (
        PersonNote.objects.filter(person_id=person_id)
        .select_related("author")
        .order_by("-created_at")
    )


# ─── Attachment Selectors ──────────────────────────────────────────────────────

def get_person_attachments(*, person_id: int):
    """Return all attachments for a person, newest first."""
    return (
        PersonAttachment.objects.filter(person_id=person_id)
        .select_related("uploaded_by")
        .order_by("-created_at")
    )


# ─── Organization Relation Selectors ──────────────────────────────────────────

def get_person_organizations(
    *, person_id: int, active_only: bool = False
):
    """
    Return organization relations for a person.

    active_only=False (default) returns both active and closed relations
    so the full history is visible. Set active_only=True to filter to
    current links only.
    """
    qs = OrganizationPersonRelation.objects.filter(person_id=person_id)
    if active_only:
        qs = qs.filter(is_active=True)
    return qs.order_by("-is_active", "-started_on", "-created_at")
