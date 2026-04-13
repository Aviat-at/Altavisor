from django.urls import path

from . import views

urlpatterns = [
    # ── Person list + create ───────────────────────────────────────────────────
    path(
        "persons/",
        views.persons_list_create,
        name="people-persons-list",
    ),

    # ── Person standalone actions (before <person_id>/ to avoid slug conflicts)
    path(
        "persons/duplicate-check/",
        views.person_duplicate_check,
        name="people-duplicate-check",
    ),

    # ── Person detail + update ─────────────────────────────────────────────────
    path(
        "persons/<int:person_id>/",
        views.person_detail_update,
        name="people-person-detail",
    ),
    path(
        "persons/<int:person_id>/deactivate/",
        views.person_deactivate,
        name="people-person-deactivate",
    ),
    path(
        "persons/<int:person_id>/reactivate/",
        views.person_reactivate,
        name="people-person-reactivate",
    ),
    path(
        "persons/<int:person_id>/merge/",
        views.person_merge,
        name="people-person-merge",
    ),

    # ── Person → Categories ────────────────────────────────────────────────────
    path(
        "persons/<int:person_id>/categories/",
        views.person_categories,
        name="people-person-categories",
    ),
    path(
        "persons/<int:person_id>/categories/<int:category_id>/",
        views.person_category_remove,
        name="people-person-category-remove",
    ),

    # ── Person → Addresses ─────────────────────────────────────────────────────
    path(
        "persons/<int:person_id>/addresses/",
        views.person_addresses,
        name="people-person-addresses",
    ),
    path(
        "persons/<int:person_id>/addresses/<int:address_id>/",
        views.person_address_update,
        name="people-person-address-update",
    ),

    # ── Person → Notes ─────────────────────────────────────────────────────────
    path(
        "persons/<int:person_id>/notes/",
        views.person_notes,
        name="people-person-notes",
    ),

    # ── Person → Organizations ─────────────────────────────────────────────────
    path(
        "persons/<int:person_id>/organizations/",
        views.person_organizations,
        name="people-person-organizations",
    ),
    path(
        "persons/<int:person_id>/organizations/<int:relation_id>/",
        views.person_organization_update,
        name="people-person-organization-update",
    ),
    path(
        "persons/<int:person_id>/organizations/<int:relation_id>/close/",
        views.person_organization_close,
        name="people-person-organization-close",
    ),

    # ── Person → Attachments ───────────────────────────────────────────────────
    path(
        "persons/<int:person_id>/attachments/",
        views.person_attachments,
        name="people-person-attachments",
    ),

    # ── Categories (standalone management) ────────────────────────────────────
    path(
        "categories/",
        views.categories_list,
        name="people-categories-list",
    ),
    path(
        "categories/create/",
        views.category_create,
        name="people-category-create",
    ),
    path(
        "categories/<int:category_id>/",
        views.category_update,
        name="people-category-update",
    ),
    path(
        "categories/<int:category_id>/deactivate/",
        views.category_deactivate,
        name="people-category-deactivate",
    ),
]
