"""
views.py — thin HTTP layer for the organizations module.

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

from party.exceptions import (
    AddressNotFoundError,
    CategoryInactiveError,
    CategoryNotFoundError,
    DuplicateCategoryAssignmentError,
)

from . import selectors, services
from .exceptions import (
    MembershipConflictError,
    MembershipNotFoundError,
    MergeOrganizationError,
    OrganizationInactiveError,
    OrganizationNotFoundError,
)
from .serializers import (
    CategoryAssignWriteSerializer,
    MembershipSerializer,
    MembershipUpdateSerializer,
    MembershipWriteSerializer,
    OrgAddressSerializer,
    OrgAddressWriteSerializer,
    OrgCategoryAssignmentSerializer,
    OrgDetailSerializer,
    OrgListSerializer,
    OrgNoteSerializer,
    OrgNoteWriteSerializer,
    OrgUpdateSerializer,
    OrgWriteSerializer,
)


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _not_found(detail: str) -> Response:
    return Response({"detail": detail}, status=status.HTTP_404_NOT_FOUND)


def _conflict(detail: str, extra: dict = None) -> Response:
    body = {"detail": detail}
    if extra:
        body.update(extra)
    return Response(body, status=status.HTTP_409_CONFLICT)


# ─── Organization Views ────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def orgs_list_create(request):
    """
    GET  /api/organizations/  — list organizations (paginated, searchable, filterable)
    POST /api/organizations/  — create a new organization
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
        is_active_filter = True if is_active_param is None else is_active_param.lower() == "true"

        result = selectors.list_organizations(
            is_active=is_active_filter,
            search=request.query_params.get("search", "").strip(),
            category_id=category_id,
            page=page,
            page_size=page_size,
        )
        return Response({
            "results": OrgListSerializer(result["results"], many=True).data,
            "count": result["count"],
            "page": result["page"],
            "page_size": result["page_size"],
            "has_next": result["has_next"],
        })

    # POST
    serializer = OrgWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    org = services.create_organization(
        data=dict(serializer.validated_data),
        created_by=request.user,
    )

    detail = selectors.get_organization_detail(org_id=org.id)
    return Response(OrgDetailSerializer(detail).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def org_detail_update(request, org_id):
    """
    GET   /api/organizations/<id>/  — retrieve full organization detail
    PATCH /api/organizations/<id>/  — partially update organization fields
    """
    if request.method == "GET":
        try:
            org = selectors.get_organization_detail(org_id=org_id)
        except OrganizationNotFoundError:
            return _not_found(f"Organization {org_id} not found.")
        return Response(OrgDetailSerializer(org).data)

    # PATCH
    serializer = OrgUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        org = services.update_organization(
            org_id=org_id,
            data=dict(serializer.validated_data),
            updated_by=request.user,
        )
    except OrganizationNotFoundError:
        return _not_found(f"Organization {org_id} not found.")
    except OrganizationInactiveError as exc:
        return _conflict(str(exc))

    detail = selectors.get_organization_detail(org_id=org.id)
    return Response(OrgDetailSerializer(detail).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def org_deactivate(request, org_id):
    """POST /api/organizations/<id>/deactivate/"""
    try:
        services.deactivate_organization(
            org_id=org_id, deactivated_by=request.user
        )
    except OrganizationNotFoundError:
        return _not_found(f"Organization {org_id} not found.")
    except OrganizationInactiveError as exc:
        return _conflict(str(exc))

    return Response({"detail": "Organization deactivated successfully."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def org_reactivate(request, org_id):
    """POST /api/organizations/<id>/reactivate/"""
    try:
        services.reactivate_organization(
            org_id=org_id, reactivated_by=request.user
        )
    except OrganizationNotFoundError:
        return _not_found(f"Organization {org_id} not found.")
    except OrganizationInactiveError as exc:
        return _conflict(str(exc))

    return Response({"detail": "Organization reactivated successfully."})


# ─── Membership Views ──────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def org_members(request, org_id):
    """
    GET  /api/organizations/<id>/members/  — list members
    POST /api/organizations/<id>/members/  — add a member
    """
    if request.method == "GET":
        is_active_param = request.query_params.get("is_active")
        is_active = None if is_active_param is None else is_active_param.lower() == "true"
        try:
            memberships = selectors.list_memberships(org_id=org_id, is_active=is_active)
        except OrganizationNotFoundError:
            return _not_found(f"Organization {org_id} not found.")
        return Response(MembershipSerializer(memberships, many=True).data)

    # POST
    serializer = MembershipWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    d = serializer.validated_data
    try:
        membership = services.add_member(
            org_id=org_id,
            person_id=d["person_id"],
            role=d["role"],
            is_primary=d.get("is_primary", False),
            started_on=d.get("started_on"),
            added_by=request.user,
        )
    except OrganizationNotFoundError:
        return _not_found(f"Organization {org_id} not found.")
    except OrganizationInactiveError as exc:
        return _conflict(str(exc))
    except Exception as exc:
        # Catches PersonNotFoundError, PersonInactiveError, MembershipConflictError
        exc_name = type(exc).__name__
        if "NotFound" in exc_name:
            return _not_found(str(exc))
        return _conflict(str(exc))

    return Response(MembershipSerializer(membership).data, status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def org_member_update(request, org_id, membership_id):
    """PATCH /api/organizations/<id>/members/<m_id>/"""
    serializer = MembershipUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        membership = services.update_membership(
            membership_id=membership_id,
            data=dict(serializer.validated_data),
            updated_by=request.user,
        )
    except MembershipNotFoundError:
        return _not_found(f"Membership {membership_id} not found.")

    return Response(MembershipSerializer(membership).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def org_member_end(request, org_id, membership_id):
    """POST /api/organizations/<id>/members/<m_id>/end/"""
    try:
        services.end_membership(membership_id=membership_id, ended_by=request.user)
    except MembershipNotFoundError:
        return _not_found(f"Membership {membership_id} not found.")

    return Response({"detail": "Membership ended."})


# ─── Organization → Category Assignment Views ──────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def org_categories(request, org_id):
    """
    GET  /api/organizations/<id>/categories/  — list category assignments
    POST /api/organizations/<id>/categories/  — assign a category
    """
    if request.method == "GET":
        active_only = request.query_params.get("active_only", "true").lower() != "false"
        try:
            assignments = selectors.get_org_categories(org_id=org_id, active_only=active_only)
        except OrganizationNotFoundError:
            return _not_found(f"Organization {org_id} not found.")
        return Response(OrgCategoryAssignmentSerializer(assignments, many=True).data)

    serializer = CategoryAssignWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        assignment = services.assign_category(
            org_id=org_id,
            category_id=serializer.validated_data["category_id"],
            assigned_by=request.user,
        )
    except OrganizationNotFoundError:
        return _not_found(f"Organization {org_id} not found.")
    except (CategoryNotFoundError, CategoryInactiveError) as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
    except DuplicateCategoryAssignmentError as exc:
        return _conflict(str(exc))

    return Response(
        OrgCategoryAssignmentSerializer(assignment).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def org_category_remove(request, org_id, category_id):
    """DELETE /api/organizations/<id>/categories/<cat_id>/"""
    try:
        services.remove_category(
            org_id=org_id,
            category_id=category_id,
            removed_by=request.user,
        )
    except DuplicateCategoryAssignmentError as exc:
        return _not_found(str(exc))

    return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Organization → Address Views ─────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def org_addresses(request, org_id):
    """
    GET  /api/organizations/<id>/addresses/  — list addresses
    POST /api/organizations/<id>/addresses/  — add an address
    """
    if request.method == "GET":
        active_only = request.query_params.get("active_only", "true").lower() != "false"
        try:
            addresses = selectors.get_org_addresses(org_id=org_id, active_only=active_only)
        except OrganizationNotFoundError:
            return _not_found(f"Organization {org_id} not found.")
        return Response(OrgAddressSerializer(addresses, many=True).data)

    serializer = OrgAddressWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        address = services.create_address(
            org_id=org_id,
            data=dict(serializer.validated_data),
            created_by=request.user,
        )
    except (OrganizationNotFoundError, OrganizationInactiveError):
        return _not_found(f"Organization {org_id} not found.")

    return Response(OrgAddressSerializer(address).data, status=status.HTTP_201_CREATED)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def org_address_update(request, org_id, address_id):
    """PATCH /api/organizations/<id>/addresses/<addr_id>/"""
    serializer = OrgAddressWriteSerializer(data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        address = services.update_address(
            org_id=org_id,
            address_id=address_id,
            data=dict(serializer.validated_data),
            updated_by=request.user,
        )
    except AddressNotFoundError as exc:
        return _not_found(str(exc))

    return Response(OrgAddressSerializer(address).data)


# ─── Organization → Note Views ─────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def org_notes(request, org_id):
    """
    GET  /api/organizations/<id>/notes/  — list notes (newest first)
    POST /api/organizations/<id>/notes/  — add an immutable note
    """
    if request.method == "GET":
        try:
            notes = selectors.get_org_notes(org_id=org_id)
        except OrganizationNotFoundError:
            return _not_found(f"Organization {org_id} not found.")
        return Response(OrgNoteSerializer(notes, many=True).data)

    serializer = OrgNoteWriteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        note = services.create_note(
            org_id=org_id,
            body=serializer.validated_data["body"],
            author=request.user,
        )
    except (OrganizationNotFoundError, OrganizationInactiveError):
        return _not_found(f"Organization {org_id} not found.")
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(OrgNoteSerializer(note).data, status=status.HTTP_201_CREATED)
