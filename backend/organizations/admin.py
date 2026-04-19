from django.contrib import admin

from .models import Organization, OrganizationMembership


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ["legal_name", "trading_name", "email", "phone", "industry", "is_active", "created_at"]
    list_filter = ["party__is_active", "industry"]
    search_fields = ["legal_name", "trading_name", "email", "registration_number"]
    readonly_fields = ["created_at", "updated_at"]

    def is_active(self, obj):
        return obj.party.is_active
    is_active.boolean = True
    is_active.short_description = "Active"


@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ["person", "organization", "role", "is_primary", "is_active", "started_on", "ended_on"]
    list_filter = ["is_active", "is_primary", "organization"]
    search_fields = ["person__first_name", "person__last_name", "organization__legal_name", "role"]
    readonly_fields = ["created_at", "updated_at"]
