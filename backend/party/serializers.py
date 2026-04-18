"""
serializers.py — response representation layer for the party module.

Serializers format response shapes. They contain no business logic —
that lives in services.py.
"""
from rest_framework import serializers

from .models import (
    Party,
    PartyAddress,
    PartyCategory,
    PartyNote,
    PartyRelationship,
)


# ─── Party Serializer ──────────────────────────────────────────────────────────

class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = ["id", "party_type", "is_active", "created_at"]
        read_only_fields = fields


# ─── Category Serializer ───────────────────────────────────────────────────────

class PartyCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PartyCategory
        fields = ["id", "name", "slug", "description", "is_system", "is_active"]
        read_only_fields = fields


# ─── Address Serializer ────────────────────────────────────────────────────────

class PartyAddressSerializer(serializers.ModelSerializer):
    label_display = serializers.CharField(source="get_label_display", read_only=True)

    class Meta:
        model = PartyAddress
        fields = [
            "id", "party_id", "label", "label_display",
            "line1", "line2", "city", "state_province", "postal_code", "country",
            "is_default", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = fields


# ─── Note Serializer ───────────────────────────────────────────────────────────

class PartyNoteSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = PartyNote
        fields = ["id", "body", "author_name", "created_at"]
        read_only_fields = fields

    def get_author_name(self, obj) -> str | None:
        if obj.author:
            return obj.author.full_name or obj.author.email
        return None


# ─── Relationship Serializer ───────────────────────────────────────────────────

class PartyRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartyRelationship
        fields = [
            "id", "from_party_id", "to_party_id", "role",
            "is_primary", "is_active", "started_on", "ended_on",
        ]
        read_only_fields = fields
