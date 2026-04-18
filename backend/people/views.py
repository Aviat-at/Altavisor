"""
views.py — thin HTTP layer for the people module.

Every view follows the same contract:
  1. Receive request
  2. Validate input with a serializer
  3. Call a service (writes) or selector (reads)
  4. Return a Response

No ORM calls, no business logic, no domain decisions live here.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from . import selectors, services

# All exception names are importable from .exceptions — party-module exceptions
# are re-exported there under their original names so this import block is unchanged.
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
from .serializers import (
    CategoryAssignWriteSerializer,
    DuplicateCandidateSerializer,
    DuplicateCheckSerializer,
    OrganizationPersonRelationSerializer,
    OrganizationPersonRelationUpdateSerializer,
    OrganizationPersonRelationWriteSerializer,
    PersonAddressSerializer,
    PersonAddressWriteSerializer,
    PersonAttachmentSerializer,
    PersonCategoryAssignmentSerializer,
    PersonCategorySerializer,
    PersonCategoryWriteSerializer,
    PersonDetailSerializer,
    PersonListSerializer,
    PersonNoteSerializer,
    PersonNoteWriteSerializer,
    PersonUpdateSerializer,
    PersonWriteSerializer,
)


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _not_found(detail: str) -> Response:
    return Response({"detail": detail}, status=status.HTTP_404_NOT_FOUND)


def _conflict(detail: str, extra: dict = None) -> Response:
    body = {"detail": detail}
    if extra:
        body.update(extra)
    return Response(body, status=status.HTTP_409_CONFLICT)


# ─── Person Views ──────────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def persons_list_create(request):
    """
    GET  /api/people/persons/  — list persons (paginated, searchable, filterable)
    POST /api/people/persons/  — create a new person
    """
    if request.method == "GET":
        try:
            page = max(1, int(request.query_params.get("page", 1)))
            page_size = min(int(request.query_params.get("page_size", 50)), 200)
        except (ValueError, TypeError):
            return Response(
                {"detail": "page and page_size must be integers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        category_id = request.query_params.get("category_id")
        if category_id is not None:
            try:
                category_id = int(category_id)
            except ValueError:
                return Response(
                    {"detail": "category_id must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        is_active_param = request.query_params.get("is_active")
        is_active_filter = None if is_active_param is None else is_active_param.lower() == "true"
        result = selectors.list_persons(
            is_active=is_active_filter,
            search=request.query_params.get("search", "").strip(),
            category_id=category_id,
            page=page,
            page_size=page_size,
        )
        return Response({
            "results": PersonListSerializer(result["results"], many=True).data,
            "count": result["count"],
            "page": result["page"],
            "page_size": result["page_size"],
            "has_next": result["has_next"],
        })

    # POST
    serializer = PersonWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        person = services.create_person(
            data=dict(serializer.validated_data),
            created_by=request.user,
        )
    except DuplicatePersonError as exc:
        return _conflict(
            str(exc),
            extra={
                "code": "duplicate_detected",
                "candidates": DuplicateCandidateSerializer(
                    [c["person"] for c in exc.candidates], many=True
                ).data,
            },
        )

    detail = selectors.get_person_detail(person_id=person.id)
    return Response(PersonDetailSerializer(detail).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def person_detail_update(request, person_id):
    """
    GET   /api/people/persons/<id>/  — retrieve full person detail
    PATCH /api/people/persons/<id>/  — partially update person fields
    """
    if request.method == "GET":
        try:
            person = selectors.get_person_detail(person_id=person_id)
        except PersonNotFoundError:
            return _not_found(f"Person {person_id} not found.")
        return Response(PersonDetailSerializer(person).data)

    # PATCH
    serializer = PersonUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        person = services.update_person(
            person_id=person_id,
            data=dict(serializer.validated_data),
            updated_by=request.user,
        )
    except PersonNotFoundError:
        return _not_found(f"Person {person_id} not found.")
    except PersonInactiveError as exc:
        return _conflict(str(exc))
    except DuplicatePersonError as exc:
        return _conflict(
            str(exc),
            extra={
                "code": "duplicate_detected",
                "candidates": DuplicateCandidateSerializer(
                    [c["person"] for c in exc.candidates], many=True
                ).data,
            },
        )

    detail = selectors.get_person_detail(person_id=person.id)
    return Response(PersonDetailSerializer(detail).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def person_deactivate(request, person_id):
    """
    POST /api/people/persons/<id>/deactivate/
    Soft-deactivates the person and closes all active org relations and
    category assignments.
    """
    try:
        services.deactivate_person(
            person_id=person_id, deactivated_by=request.user
        )
    except PersonNotFoundError:
        return _not_found(f"Person {person_id} not found.")
    except PersonInactiveError as exc:
        return _conflict(str(exc))

    return Response({"detail": "Person deactivated successfully."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def person_reactivate(request, person_id):
    """
    POST /api/people/persons/<id>/reactivate/
    Reactivates a previously deactivated person.
    """
    try:
        services.reactivate_person(
            person_id=person_id, reactivated_by=request.user
        )
    except PersonNotFoundError:
        return _not_found(f"Person {person_id} not found.")
    except PersonInactiveError as exc:
        return _conflict(str(exc))

    return Response({"detail": "Person reactivated successfully."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def person_duplicate_check(request):
    """
    POST /api/people/persons/duplicate-check/
    Run duplicate detection without creating a record.
    Used by the frontend before showing the "create person" confirmation.
    """
    serializer = DuplicateCheckSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    d = serializer.validated_data
    candidates = services.detect_duplicate_persons(
        first_name=d["first_name"],
        last_name=d["last_name"],
        email=d.get("email", ""),
        phone=d.get("phone", ""),
    )

    return Response({
        "has_duplicates": bool(candidates),
        "candidates": [
            {
                **DuplicateCandidateSerializer(c["person"]).data,
                "reason": c["reason"],
            }
            for c in candidates
        ],
    })


@api_view(["POST"])
@permission_classes([IsAdminUser])
def person_merge(request, person_id):
    """
    POST /api/people/persons/<id>/merge/
    Merge placeholder — returns 501 until full implementation ships.
    Body: { "target_id": <int> }
    """
    target_id = request.data.get("target_id")
    if not target_id:
        return Response(
            {"detail": "target_id is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        services.merge_persons(
            source_id=person_id,
            target_id=int(target_id),
            merged_by=request.user,
        )
    except MergePersonError as exc:
        return Response(
            {"detail": str(exc), "code": "merge_not_implemented"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )

    return Response({"detail": "Merge completed."})


# ─── Category Views ────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def categories_list(request):
    """
    GET /api/people/categories/
    Optional query params: is_active, is_system
    """
    def _parse_bool(val):
        if val is None:
            return None
        return val.lower() == "true"

    categories = selectors.list_categories(
        is_active=_parse_bool(request.query_params.get("is_active")),
        is_system=_parse_bool(request.query_params.get("is_system")),
    )
    return Response(PersonCategorySerializer(categories, many=True).data)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def category_create(request):
    """POST /api/people/categories/"""
    serializer = PersonCategoryWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        category = services.create_category(
            data=dict(serializer.validated_data),
            created_by=request.user,
        )
    except ValueError as exc:
        return _conflict(str(exc))

    return Response(
        PersonCategorySerializer(category).data, status=status.HTTP_201_CREATED
    )


@api_view(["PATCH"])
@permission_classes([IsAdminUser])
def category_update(request, category_id):
    """PATCH /api/people/categories/<id>/"""
    serializer = PersonCategoryWriteSerializer(data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        category = services.update_category(
            category_id=category_id,
            data=dict(serializer.validated_data),
            updated_by=request.user,
        )
    except CategoryNotFoundError:
        return _not_found(f"Category {category_id} not found.")
    except (CategorySystemProtectedError, ValueError) as exc:
        return _conflict(str(exc))

    return Response(PersonCategorySerializer(category).data)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def category_deactivate(request, category_id):
    """POST /api/people/categories/<id>/deactivate/"""
    try:
        services.deactivate_category(
            category_id=category_id, deactivated_by=request.user
        )
    except CategoryNotFoundError:
        return _not_found(f"Category {category_id} not found.")
    except CategorySystemProtectedError as exc:
        return _conflict(str(exc))

    return Response({"detail": "Category deactivated."})


# ─── Person → Category Assignment Views ───────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def person_categories(request, person_id):
    """
    GET  /api/people/persons/<id>/categories/  — list category assignments
    POST /api/people/persons/<id>/categories/  — assign a category
    """
    if request.method == "GET":
        active_only = request.query_params.get("active_only", "true").lower() != "false"
        assignments = selectors.get_person_categories(
            person_id=person_id, active_only=active_only
        )
        return Response(PersonCategoryAssignmentSerializer(assignments, many=True).data)

    serializer = CategoryAssignWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        assignment = services.assign_category(
            person_id=person_id,
            category_id=serializer.validated_data["category_id"],
            assigned_by=request.user,
        )
    except PersonNotFoundError:
        return _not_found(f"Person {person_id} not found.")
    except (CategoryNotFoundError, CategoryInactiveError) as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
    except DuplicateCategoryAssignmentError as exc:
        return _conflict(str(exc))

    return Response(
        PersonCategoryAssignmentSerializer(assignment).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def person_category_remove(request, person_id, category_id):
    """DELETE /api/people/persons/<id>/categories/<cat_id>/"""
    try:
        services.remove_category(
            person_id=person_id,
            category_id=category_id,
            removed_by=request.user,
        )
    except DuplicateCategoryAssignmentError as exc:
        return _not_found(str(exc))

    return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Person → Address Views ────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def person_addresses(request, person_id):
    """
    GET  /api/people/persons/<id>/addresses/  — list addresses
    POST /api/people/persons/<id>/addresses/  — add an address
    """
    if request.method == "GET":
        active_only = request.query_params.get("active_only", "true").lower() != "false"
        addresses = selectors.get_person_addresses(
            person_id=person_id, active_only=active_only
        )
        return Response(PersonAddressSerializer(addresses, many=True).data)

    serializer = PersonAddressWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        address = services.create_address(
            person_id=person_id,
            data=dict(serializer.validated_data),
            created_by=request.user,
        )
    except PersonNotFoundError:
        return _not_found(f"Person {person_id} not found.")

    return Response(PersonAddressSerializer(address).data, status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def person_address_update(request, person_id, address_id):
    """PATCH /api/people/persons/<id>/addresses/<addr_id>/"""
    serializer = PersonAddressWriteSerializer(data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        address = services.update_address(
            person_id=person_id,
            address_id=address_id,
            data=dict(serializer.validated_data),
            updated_by=request.user,
        )
    except AddressNotFoundError as exc:
        return _not_found(str(exc))

    return Response(PersonAddressSerializer(address).data)


# ─── Person → Note Views ───────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def person_notes(request, person_id):
    """
    GET  /api/people/persons/<id>/notes/  — list notes (newest first)
    POST /api/people/persons/<id>/notes/  — add an immutable note
    """
    if request.method == "GET":
        notes = selectors.get_person_notes(person_id=person_id)
        return Response(PersonNoteSerializer(notes, many=True).data)

    serializer = PersonNoteWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        note = services.create_note(
            person_id=person_id,
            body=serializer.validated_data["body"],
            author=request.user,
        )
    except PersonNotFoundError:
        return _not_found(f"Person {person_id} not found.")
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(PersonNoteSerializer(note).data, status=status.HTTP_201_CREATED)


# ─── Person → Organization Relation Views ─────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def person_organizations(request, person_id):
    """
    GET  /api/people/persons/<id>/organizations/  — list org relations
    POST /api/people/persons/<id>/organizations/  — link to an organization
    """
    if request.method == "GET":
        active_only = request.query_params.get("active_only", "false").lower() == "true"
        relations = selectors.get_person_organizations(
            person_id=person_id, active_only=active_only
        )
        return Response(OrganizationPersonRelationSerializer(relations, many=True).data)

    serializer = OrganizationPersonRelationWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = dict(serializer.validated_data)
    data["person_id"] = person_id

    try:
        relation = services.link_person_to_organization(
            data=data, created_by=request.user
        )
    except PersonNotFoundError:
        return _not_found(f"Person {person_id} not found.")
    except OrganizationRelationConflictError as exc:
        return _conflict(str(exc))

    return Response(
        OrganizationPersonRelationSerializer(relation).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def person_organization_update(request, person_id, relation_id):
    """PATCH /api/people/persons/<id>/organizations/<rel_id>/"""
    serializer = OrganizationPersonRelationUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        relation = services.update_organization_relationship(
            relation_id=relation_id,
            data=dict(serializer.validated_data),
            updated_by=request.user,
        )
    except OrganizationRelationNotFoundError as exc:
        return _not_found(str(exc))

    return Response(OrganizationPersonRelationSerializer(relation).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def person_organization_close(request, person_id, relation_id):
    """POST /api/people/persons/<id>/organizations/<rel_id>/close/"""
    try:
        services.close_organization_relationship(
            relation_id=relation_id, closed_by=request.user
        )
    except OrganizationRelationNotFoundError as exc:
        return _not_found(str(exc))

    return Response({"detail": "Organization relation closed."})


# ─── Person → Attachment Views (Phase 2) ──────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def person_attachments(request, person_id):
    """
    GET /api/people/persons/<id>/attachments/

    File upload (POST) is deferred to phase 2.
    MEDIA_ROOT and MEDIA_URL must be configured in settings.py first.
    """
    attachments = selectors.get_person_attachments(person_id=person_id)
    return Response(PersonAttachmentSerializer(attachments, many=True).data)
