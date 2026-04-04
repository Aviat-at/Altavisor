from django.contrib import admin

from .models import (
    OrganizationPersonRelation,
    Person,
    PersonAddress,
    PersonAttachment,
    PersonCategory,
    PersonCategoryAssignment,
    PersonNote,
)


# ─── Inlines ───────────────────────────────────────────────────────────────────

class PersonCategoryAssignmentInline(admin.TabularInline):
    model = PersonCategoryAssignment
    extra = 0
    fields = ("category", "assigned_by", "is_active", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("category",)


class PersonAddressInline(admin.TabularInline):
    model = PersonAddress
    extra = 0
    fields = ("label", "line1", "city", "country", "is_default", "is_active")


class PersonNoteInline(admin.TabularInline):
    model = PersonNote
    extra = 0
    fields = ("body", "author", "created_at")
    readonly_fields = ("created_at",)

    def has_change_permission(self, request, obj=None):
        # Notes are immutable — no editing in admin either
        return False


class PersonAttachmentInline(admin.TabularInline):
    model = PersonAttachment
    extra = 0
    fields = ("label", "file", "uploaded_by", "created_at")
    readonly_fields = ("created_at",)


class OrganizationPersonRelationInline(admin.TabularInline):
    model = OrganizationPersonRelation
    extra = 0
    fields = (
        "organization_type", "organization_id", "role",
        "is_primary", "is_active", "started_on", "ended_on",
    )


# ─── ModelAdmin registrations ──────────────────────────────────────────────────

@admin.register(PersonCategory)
class PersonCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_system", "is_active", "created_at")
    list_filter = ("is_system", "is_active")
    search_fields = ("name", "slug")
    ordering = ("name",)
    readonly_fields = ("slug", "created_at", "updated_at")

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj and obj.is_system:
            # Prevent admin users from changing system category names too
            fields.extend(["name", "is_system"])
        return fields


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = (
        "full_name", "email", "phone", "is_active", "created_at"
    )
    list_filter = ("is_active", "gender")
    search_fields = ("first_name", "last_name", "email", "phone", "mobile")
    ordering = ("last_name", "first_name")
    readonly_fields = ("created_at", "updated_at", "created_by")

    fieldsets = (
        (None, {
            "fields": (
                "first_name", "last_name", "preferred_name",
                "email", "phone", "mobile",
            ),
        }),
        ("Personal Details", {
            "fields": ("date_of_birth", "gender"),
            "classes": ("collapse",),
        }),
        ("Status & Audit", {
            "fields": ("is_active", "created_by", "created_at", "updated_at"),
        }),
    )

    inlines = [
        PersonCategoryAssignmentInline,
        PersonAddressInline,
        OrganizationPersonRelationInline,
        PersonNoteInline,
        PersonAttachmentInline,
    ]

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = "Name"
    full_name.admin_order_field = "last_name"


@admin.register(PersonCategoryAssignment)
class PersonCategoryAssignmentAdmin(admin.ModelAdmin):
    list_display = ("person", "category", "is_active", "assigned_by", "created_at")
    list_filter = ("is_active", "category")
    search_fields = ("person__first_name", "person__last_name", "category__name")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PersonAddress)
class PersonAddressAdmin(admin.ModelAdmin):
    list_display = ("person", "label", "city", "country", "is_default", "is_active")
    list_filter = ("label", "is_default", "is_active")
    search_fields = ("person__first_name", "person__last_name", "city", "country")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PersonNote)
class PersonNoteAdmin(admin.ModelAdmin):
    list_display = ("person", "author", "created_at")
    search_fields = ("person__first_name", "person__last_name", "body")
    readonly_fields = ("created_at",)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # Preserve notes as immutable audit records
        return False


@admin.register(OrganizationPersonRelation)
class OrganizationPersonRelationAdmin(admin.ModelAdmin):
    list_display = (
        "person", "organization_type", "organization_id",
        "role", "is_primary", "is_active", "started_on", "ended_on",
    )
    list_filter = ("organization_type", "is_active", "is_primary")
    search_fields = (
        "person__first_name", "person__last_name",
        "organization_type", "role",
    )
    readonly_fields = ("created_at", "updated_at")
