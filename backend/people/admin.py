from django.contrib import admin

from party.models import (
    PartyAddress,
    PartyAttachment,
    PartyCategoryAssignment,
    PartyNote,
    PartyRelationship,
)

from .models import Person


# ─── Inlines ───────────────────────────────────────────────────────────────────

class PartyCategoryAssignmentInline(admin.TabularInline):
    model = PartyCategoryAssignment
    extra = 0
    fields = ("category", "assigned_by", "is_active", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("category",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            party__person__isnull=False
        )


class PartyAddressInline(admin.TabularInline):
    model = PartyAddress
    extra = 0
    fields = ("label", "line1", "city", "country", "is_default", "is_active")


class PartyNoteInline(admin.TabularInline):
    model = PartyNote
    extra = 0
    fields = ("body", "author", "created_at")
    readonly_fields = ("created_at",)

    def has_change_permission(self, request, obj=None):
        return False


class PartyAttachmentInline(admin.TabularInline):
    model = PartyAttachment
    extra = 0
    fields = ("label", "file", "uploaded_by", "created_at")
    readonly_fields = ("created_at",)


class PartyRelationshipInline(admin.TabularInline):
    model = PartyRelationship
    fk_name = "from_party"
    extra = 0
    fields = ("to_party", "role", "is_primary", "is_active", "started_on", "ended_on")


# ─── ModelAdmin registrations ──────────────────────────────────────────────────

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "party_is_active", "created_at")
    list_filter = ("gender",)
    search_fields = ("first_name", "last_name", "email", "phone", "mobile")
    ordering = ("last_name", "first_name")
    readonly_fields = ("created_at", "updated_at", "party")

    fieldsets = (
        (None, {
            "fields": (
                "party",
                "first_name", "last_name", "preferred_name",
                "email", "phone", "mobile",
            ),
        }),
        ("Personal Details", {
            "fields": ("date_of_birth", "gender"),
            "classes": ("collapse",),
        }),
        ("Audit", {
            "fields": ("created_at", "updated_at"),
        }),
    )

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = "Name"
    full_name.admin_order_field = "last_name"

    def party_is_active(self, obj):
        return obj.party.is_active
    party_is_active.short_description = "Active"
    party_is_active.boolean = True
