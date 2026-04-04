"""
serializers.py — API validation and representation layer.

Serializers validate request shapes and format response shapes.
They contain no business logic — that lives in services.py.
"""
from rest_framework import serializers

from .models import (
    OrganizationPersonRelation,
    Person,
    PersonAddress,
    PersonAttachment,
    PersonCategory,
    PersonCategoryAssignment,
    PersonNote,
)


# ─── Category Serializers ──────────────────────────────────────────────────────

class PersonCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonCategory
        fields = [
            "id", "name", "slug", "description",
            "is_system", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = fields


class PersonCategoryWriteSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(allow_blank=True, default="", required=False)


# ─── Address Serializers ───────────────────────────────────────────────────────

class PersonAddressSerializer(serializers.ModelSerializer):
    label_display = serializers.CharField(source="get_label_display", read_only=True)

    class Meta:
        model = PersonAddress
        fields = [
            "id", "label", "label_display",
            "line1", "line2", "city", "state_province", "postal_code", "country",
            "is_default", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "label_display", "created_at", "updated_at"]


class PersonAddressWriteSerializer(serializers.Serializer):
    label = serializers.ChoiceField(
        choices=PersonAddress.Label.choices,
        default=PersonAddress.Label.HOME,
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

class PersonNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = PersonNote
        fields = ["id", "body", "author_name", "created_at"]
        read_only_fields = fields

    def get_author_name(self, obj) -> str | None:
        if obj.author:
            return obj.author.full_name or obj.author.email
        return None


class PersonNoteWriteSerializer(serializers.Serializer):
    body = serializers.CharField(min_length=1)


# ─── Attachment Serializer ─────────────────────────────────────────────────────

class PersonAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PersonAttachment
        fields = ["id", "label", "file", "uploaded_by_name", "created_at"]
        read_only_fields = fields

    def get_uploaded_by_name(self, obj) -> str | None:
        if obj.uploaded_by:
            return obj.uploaded_by.full_name or obj.uploaded_by.email
        return None


# ─── Category Assignment Serializer ───────────────────────────────────────────

class PersonCategoryAssignmentSerializer(serializers.ModelSerializer):
    category = PersonCategorySerializer(read_only=True)
    assigned_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PersonCategoryAssignment
        fields = ["id", "category", "assigned_by_name", "is_active", "created_at"]
        read_only_fields = fields

    def get_assigned_by_name(self, obj) -> str | None:
        if obj.assigned_by:
            return obj.assigned_by.full_name or obj.assigned_by.email
        return None


class CategoryAssignWriteSerializer(serializers.Serializer):
    category_id = serializers.IntegerField(min_value=1)


# ─── Organization Relation Serializers ────────────────────────────────────────

class OrganizationPersonRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationPersonRelation
        fields = [
            "id", "person_id", "organization_id", "organization_type", "role",
            "is_primary", "is_active", "started_on", "ended_on",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "person_id", "created_at", "updated_at"]


class OrganizationPersonRelationWriteSerializer(serializers.Serializer):
    organization_id = serializers.IntegerField(min_value=1)
    organization_type = serializers.CharField(max_length=50)
    role = serializers.CharField(max_length=100)
    is_primary = serializers.BooleanField(default=False, required=False)
    started_on = serializers.DateField(required=False, allow_null=True)


class OrganizationPersonRelationUpdateSerializer(serializers.Serializer):
    role = serializers.CharField(max_length=100, required=False)
    is_primary = serializers.BooleanField(required=False)
    started_on = serializers.DateField(required=False, allow_null=True)


# ─── Person Serializers ────────────────────────────────────────────────────────

class PersonListSerializer(serializers.ModelSerializer):
    """
    Compact shape used in directory/list views.

    primary_category reads from the active_assignments to_attr that
    list_persons() prefetches — no extra query per row.
    """
    full_name = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    primary_category = serializers.SerializerMethodField()

    class Meta:
        model = Person
        fields = [
            "id", "full_name", "display_name",
            "email", "phone", "is_active",
            "primary_category", "created_at",
        ]
        read_only_fields = fields

    def get_primary_category(self, obj) -> str | None:
        assignments = getattr(obj, "active_assignments", None)
        if assignments:
            return assignments[0].category.name
        return None


class PersonDetailSerializer(serializers.ModelSerializer):
    """
    Full shape used in detail/edit views.

    Nested relations are read-only — mutations go through their own
    dedicated endpoints.
    """
    full_name = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    initials = serializers.CharField(read_only=True)
    gender_display = serializers.CharField(source="get_gender_display", read_only=True)
    created_by_name = serializers.SerializerMethodField()

    addresses = PersonAddressSerializer(many=True, read_only=True)
    category_assignments = PersonCategoryAssignmentSerializer(
        source="active_assignments", many=True, read_only=True
    )
    org_relations = OrganizationPersonRelationSerializer(many=True, read_only=True)
    notes = PersonNoteSerializer(many=True, read_only=True)
    attachments = PersonAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Person
        fields = [
            "id", "full_name", "display_name", "initials",
            "first_name", "last_name", "preferred_name",
            "email", "phone", "mobile",
            "date_of_birth", "gender", "gender_display",
            "is_active", "created_by_name", "created_at", "updated_at",
            "addresses", "category_assignments",
            "org_relations", "notes", "attachments",
        ]
        read_only_fields = fields

    def get_created_by_name(self, obj) -> str | None:
        if obj.created_by:
            return obj.created_by.full_name or obj.created_by.email
        return None


class PersonWriteSerializer(serializers.Serializer):
    """Used for POST /persons/ (create)."""
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    preferred_name = serializers.CharField(
        max_length=100, allow_blank=True, default="", required=False
    )
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    phone = serializers.CharField(max_length=30, allow_blank=True, default="", required=False)
    mobile = serializers.CharField(max_length=30, allow_blank=True, default="", required=False)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.ChoiceField(
        choices=[("", "")] + Person.Gender.choices,
        allow_blank=True,
        default="",
        required=False,
    )
    # force=True bypasses duplicate detection; set by the frontend after
    # the user reviews the candidates and confirms they want to proceed.
    force = serializers.BooleanField(default=False, required=False)


class PersonUpdateSerializer(serializers.Serializer):
    """Used for PATCH /persons/<id>/ (partial update — all fields optional)."""
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    preferred_name = serializers.CharField(
        max_length=100, allow_blank=True, required=False
    )
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    phone = serializers.CharField(max_length=30, allow_blank=True, required=False)
    mobile = serializers.CharField(max_length=30, allow_blank=True, required=False)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    gender = serializers.ChoiceField(
        choices=[("", "")] + Person.Gender.choices,
        allow_blank=True,
        required=False,
    )
    force = serializers.BooleanField(default=False, required=False)


# ─── Duplicate Check Serializers ──────────────────────────────────────────────

class DuplicateCheckSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=100)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    phone = serializers.CharField(
        max_length=30, required=False, allow_blank=True, default=""
    )


class DuplicateCandidateSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Person
        fields = ["id", "full_name", "email", "phone"]
        read_only_fields = fields
