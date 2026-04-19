"""
serializers.py — API validation and representation layer for organizations.

Serializers validate request shapes and format response shapes.
They contain no business logic — that lives in services.py.
"""
from rest_framework import serializers

from party.models import PartyAddress, PartyAttachment, PartyCategory, PartyCategoryAssignment, PartyNote

from .models import Organization, OrganizationMembership


# ─── Category Serializers (re-use party shape) ────────────────────────────────

class OrgCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PartyCategory
        fields = [
            "id", "name", "slug", "description",
            "is_system", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = fields


class OrgCategoryAssignmentSerializer(serializers.ModelSerializer):
    category = OrgCategorySerializer(read_only=True)
    assigned_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PartyCategoryAssignment
        fields = ["id", "category", "assigned_by_name", "is_active", "created_at"]
        read_only_fields = fields

    def get_assigned_by_name(self, obj) -> str | None:
        if obj.assigned_by:
            return obj.assigned_by.full_name or obj.assigned_by.email
        return None


class CategoryAssignWriteSerializer(serializers.Serializer):
    category_id = serializers.IntegerField(min_value=1)


# ─── Address Serializers ───────────────────────────────────────────────────────

class OrgAddressSerializer(serializers.ModelSerializer):
    label_display = serializers.CharField(source="get_label_display", read_only=True)

    class Meta:
        model = PartyAddress
        fields = [
            "id", "label", "label_display",
            "line1", "line2", "city", "state_province", "postal_code", "country",
            "is_default", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "label_display", "created_at", "updated_at"]


class OrgAddressWriteSerializer(serializers.Serializer):
    label = serializers.ChoiceField(
        choices=PartyAddress.Label.choices,
        default=PartyAddress.Label.WORK,
        required=False,
    )
    line1 = serializers.CharField(max_length=200)
    line2 = serializers.CharField(max_length=200, allow_blank=True, default="", required=False)
    city = serializers.CharField(max_length=100)
    state_province = serializers.CharField(max_length=100, allow_blank=True, default="", required=False)
    postal_code = serializers.CharField(max_length=20, allow_blank=True, default="", required=False)
    country = serializers.CharField(max_length=100)
    is_default = serializers.BooleanField(default=False, required=False)


# ─── Note Serializers ──────────────────────────────────────────────────────────

class OrgNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = PartyNote
        fields = ["id", "body", "author_name", "created_at"]
        read_only_fields = fields

    def get_author_name(self, obj) -> str | None:
        if obj.author:
            return obj.author.full_name or obj.author.email
        return None


class OrgNoteWriteSerializer(serializers.Serializer):
    body = serializers.CharField(min_length=1)


# ─── Attachment Serializer ─────────────────────────────────────────────────────

class OrgAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PartyAttachment
        fields = ["id", "label", "file", "uploaded_by_name", "created_at"]
        read_only_fields = fields

    def get_uploaded_by_name(self, obj) -> str | None:
        if obj.uploaded_by:
            return obj.uploaded_by.full_name or obj.uploaded_by.email
        return None


# ─── Membership Serializers ────────────────────────────────────────────────────

class MembershipSerializer(serializers.ModelSerializer):
    person_name = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationMembership
        fields = [
            "id", "person_id", "person_name", "role",
            "is_primary", "is_active", "started_on", "ended_on",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_person_name(self, obj) -> str | None:
        if obj.person_id:
            return obj.person.full_name
        return None


class PersonMembershipSerializer(serializers.ModelSerializer):
    """Compact shape for embedding in PersonDetail — shows org side."""
    org_id = serializers.IntegerField(source="organization_id", read_only=True)
    org_name = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationMembership
        fields = [
            "id", "org_id", "org_name", "role",
            "is_primary", "is_active", "started_on", "ended_on",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_org_name(self, obj) -> str | None:
        return obj.organization.display_name if obj.organization_id else None


class MembershipWriteSerializer(serializers.Serializer):
    person_id = serializers.IntegerField(min_value=1)
    role = serializers.CharField(max_length=100)
    is_primary = serializers.BooleanField(default=False, required=False)
    started_on = serializers.DateField(required=False, allow_null=True)


class MembershipUpdateSerializer(serializers.Serializer):
    role = serializers.CharField(max_length=100, required=False)
    is_primary = serializers.BooleanField(required=False)
    started_on = serializers.DateField(required=False, allow_null=True)


# ─── Organization Serializers ──────────────────────────────────────────────────

class OrgListSerializer(serializers.ModelSerializer):
    """Compact shape for list/directory views."""
    is_active = serializers.BooleanField(source="party.is_active", read_only=True)
    display_name = serializers.CharField(read_only=True)
    primary_category = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id", "display_name", "legal_name", "trading_name",
            "email", "phone", "industry",
            "is_active", "primary_category", "created_at",
        ]
        read_only_fields = fields

    def get_primary_category(self, obj) -> str | None:
        assignments = getattr(obj.party, "active_assignments", None)
        if assignments:
            return assignments[0].category.name
        return None


class OrgDetailSerializer(serializers.ModelSerializer):
    """Full shape for detail/edit views."""
    is_active = serializers.BooleanField(source="party.is_active", read_only=True)
    display_name = serializers.CharField(read_only=True)
    created_by_name = serializers.SerializerMethodField()

    # Sub-resources via party
    addresses = OrgAddressSerializer(
        source="party.addresses", many=True, read_only=True
    )
    category_assignments = OrgCategoryAssignmentSerializer(
        source="party.active_assignments", many=True, read_only=True
    )
    notes = OrgNoteSerializer(
        source="party.notes", many=True, read_only=True
    )
    attachments = OrgAttachmentSerializer(
        source="party.attachments", many=True, read_only=True
    )

    # Memberships
    members = MembershipSerializer(
        source="memberships", many=True, read_only=True
    )

    class Meta:
        model = Organization
        fields = [
            "id", "display_name", "legal_name", "trading_name",
            "registration_number", "tax_id", "website",
            "email", "phone", "industry",
            "is_active", "created_by_name", "created_at", "updated_at",
            "addresses", "category_assignments", "notes", "attachments", "members",
        ]
        read_only_fields = fields

    def get_created_by_name(self, obj) -> str | None:
        created_by = obj.party.created_by
        if created_by:
            return created_by.full_name or created_by.email
        return None


class OrgWriteSerializer(serializers.Serializer):
    """Used for POST /organizations/ (create)."""
    legal_name = serializers.CharField(max_length=200)
    trading_name = serializers.CharField(max_length=200, allow_blank=True, default="", required=False)
    registration_number = serializers.CharField(max_length=100, allow_blank=True, default="", required=False)
    tax_id = serializers.CharField(max_length=100, allow_blank=True, default="", required=False)
    website = serializers.URLField(allow_blank=True, default="", required=False)
    email = serializers.EmailField(allow_blank=True, default="", required=False)
    phone = serializers.CharField(max_length=30, allow_blank=True, default="", required=False)
    industry = serializers.CharField(max_length=100, allow_blank=True, default="", required=False)


class OrgUpdateSerializer(serializers.Serializer):
    """Used for PATCH /organizations/<id>/ (partial update — all fields optional)."""
    legal_name = serializers.CharField(max_length=200, required=False)
    trading_name = serializers.CharField(max_length=200, allow_blank=True, required=False)
    registration_number = serializers.CharField(max_length=100, allow_blank=True, required=False)
    tax_id = serializers.CharField(max_length=100, allow_blank=True, required=False)
    website = serializers.URLField(allow_blank=True, required=False)
    email = serializers.EmailField(allow_blank=True, required=False)
    phone = serializers.CharField(max_length=30, allow_blank=True, required=False)
    industry = serializers.CharField(max_length=100, allow_blank=True, required=False)
