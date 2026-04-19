from django.conf import settings
from django.db import models


# ─── Abstract Base ─────────────────────────────────────────────────────────────

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ─── Organization ──────────────────────────────────────────────────────────────

class Organization(TimestampedModel):
    """
    Organization-specific identity data, extending Party via a OneToOne link.

    party.Party holds is_active, created_by, and all shared sub-resources
    (addresses, notes, attachments, categories, relationships). Organization
    holds the org-specific fields only.

    An Organization must never exist without a Party — services.create_organization()
    creates both atomically. The service enforces party_type = ORGANIZATION.
    """

    party = models.OneToOneField(
        "party.Party",
        on_delete=models.CASCADE,
        related_name="organization",
    )
    legal_name = models.CharField(max_length=200)
    trading_name = models.CharField(max_length=200, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    tax_id = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    industry = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "org_organizations"
        ordering = ["legal_name"]
        indexes = [
            models.Index(fields=["legal_name"], name="org_legal_name_idx"),
        ]
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

    def __str__(self):
        return self.display_name

    @property
    def display_name(self) -> str:
        return self.trading_name or self.legal_name


# ─── OrganizationMembership ────────────────────────────────────────────────────

class OrganizationMembership(TimestampedModel):
    """
    Explicit M2M through model linking a Person to an Organization in a role.

    This is the canonical way to express people-to-organization relationships.
    Do not use PartyRelationship for this purpose — that model is reserved for
    generic cross-party links (person-to-person, org-to-org, etc.).

    unique_together on (person, organization, role) prevents duplicate rows.
    A previously ended membership with the same combination cannot be re-opened
    without first deleting it — callers must end_membership then add_member
    again to model a re-hire.

    is_active + ended_on together model the temporal lifecycle of the link.
    is_primary marks the person's main/primary organization.
    """

    person = models.ForeignKey(
        "people.Person",
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role = models.CharField(max_length=100)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    started_on = models.DateField(null=True, blank=True)
    ended_on = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "org_memberships"
        unique_together = [("person", "organization", "role")]
        ordering = ["-is_active", "-started_on", "-created_at"]
        indexes = [
            models.Index(fields=["organization", "is_active"], name="membership_org_active_idx"),
            models.Index(fields=["person", "is_active"], name="membership_person_active_idx"),
        ]
        verbose_name = "Organization Membership"
        verbose_name_plural = "Organization Memberships"

    def __str__(self):
        return f"{self.person} → {self.organization} ({self.role})"
