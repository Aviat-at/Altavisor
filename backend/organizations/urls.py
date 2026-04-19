from django.urls import path

from . import views

urlpatterns = [
    # ── Organization list + create ─────────────────────────────────────────────
    path(
        "",
        views.orgs_list_create,
        name="orgs-list",
    ),

    # ── Organization detail + update ───────────────────────────────────────────
    path(
        "<int:org_id>/",
        views.org_detail_update,
        name="orgs-detail",
    ),
    path(
        "<int:org_id>/deactivate/",
        views.org_deactivate,
        name="orgs-deactivate",
    ),
    path(
        "<int:org_id>/reactivate/",
        views.org_reactivate,
        name="orgs-reactivate",
    ),

    # ── Members ────────────────────────────────────────────────────────────────
    path(
        "<int:org_id>/members/",
        views.org_members,
        name="orgs-members",
    ),
    path(
        "<int:org_id>/members/<int:membership_id>/",
        views.org_member_update,
        name="orgs-member-update",
    ),
    path(
        "<int:org_id>/members/<int:membership_id>/end/",
        views.org_member_end,
        name="orgs-member-end",
    ),

    # ── Categories ─────────────────────────────────────────────────────────────
    path(
        "<int:org_id>/categories/",
        views.org_categories,
        name="orgs-categories",
    ),
    path(
        "<int:org_id>/categories/<int:category_id>/",
        views.org_category_remove,
        name="orgs-category-remove",
    ),

    # ── Addresses ──────────────────────────────────────────────────────────────
    path(
        "<int:org_id>/addresses/",
        views.org_addresses,
        name="orgs-addresses",
    ),
    path(
        "<int:org_id>/addresses/<int:address_id>/",
        views.org_address_update,
        name="orgs-address-update",
    ),

    # ── Notes ──────────────────────────────────────────────────────────────────
    path(
        "<int:org_id>/notes/",
        views.org_notes,
        name="orgs-notes",
    ),
]
