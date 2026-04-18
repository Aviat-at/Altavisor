from django.conf import settings
from django.db import models


# ─── Abstract Base ─────────────────────────────────────────────────────────────

class TimestampedModel(models.Model):
    """
    Abstract base that adds created_at / updated_at to every party model.
    Consistent with the audit-friendly field convention used in accounts.User
    (date_joined, last_login).
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ─── Party ─────────────────────────────────────────────────────────────────────

class Party(TimestampedModel):
    """
    Root identity record shared by all entity types (Person, Organization, etc.).

    party_type drives the OneToOne link to the concrete entity table.
    created_by is nullable so parties can be created programmatically without
    a user context (e.g. data imports, fixtures).
    """

    class PartyType(models.TextChoices):
        PERSON       = "person",       "Person"
        ORGANIZATION = "organization", "Organization"

    party_type = models.CharField(
        max_length=20,
        choices=PartyType.choices,
        db_index=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_parties",
    )

    class Meta:
        db_table = "party_parties"
        ordering = ["-created_at"]
        verbose_name = "Party"
        verbose_name_plural = "Parties"

    def __str__(self):
        return f"Party #{self.id} ({self.party_type})"


# ─── PartyCategory ─────────────────────────────────────────────────────────────

class PartyCategory(TimestampedModel):
    """
    Classification label applicable to any Party.

    Categories are classification-only. They must NOT store pricing, discount
    values, pricing profiles, or any product-domain data. That belongs to the
    product pricing domain.

    is_system=True marks categories that are seeded by the application and
    cannot be renamed, re-slugged, or deactivated via the API. The service
    layer enforces this; there is no DB constraint because the protection
    logic must also emit a useful error message.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(
        default=False,
        help_text="System categories are seeded by the app and cannot be modified via the API.",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "party_categories"
        ordering = ["name"]
        verbose_name = "Party Category"
        verbose_name_plural = "Party Categories"

    def __str__(self):
        return self.name


# ─── PartyCategoryAssignment ───────────────────────────────────────────────────

class PartyCategoryAssignment(TimestampedModel):
    """
    Explicit M2M through-model linking a Party to a PartyCategory.

    unique_together enforces that a (party, category) pair can only have
    one row. is_active allows soft-deactivation without losing history.
    The service layer additionally prevents creating a second active assignment
    for the same pair.
    """
    party = models.ForeignKey(
        Party,
        on_delete=models.CASCADE,
        related_name="category_assignments",
    )
    category = models.ForeignKey(
        PartyCategory,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="party_category_assignments_made",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "party_category_assignments"
        unique_together = [("party", "category")]
        ordering = ["category__name"]
        verbose_name = "Party Category Assignment"
        verbose_name_plural = "Party Category Assignments"

    def __str__(self):
        return f"{self.party} — {self.category}"


# ─── PartyAddress ──────────────────────────────────────────────────────────────

class PartyAddress(TimestampedModel):
    """
    A physical or postal address associated with a Party.

    A party may have multiple addresses with different labels.
    is_default=True indicates the primary address for a given party;
    the service layer ensures at most one default per party.
    is_active allows soft-deactivation without deleting historical addresses.
    """

    class Label(models.TextChoices):
        BILLING  = "billing",  "Billing"
        DELIVERY = "delivery", "Delivery"
        HOME     = "home",     "Home"
        WORK     = "work",     "Work"
        OTHER    = "other",    "Other"

    party = models.ForeignKey(
        Party,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    label = models.CharField(
        max_length=20,
        choices=Label.choices,
        default=Label.HOME,
    )
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "party_addresses"
        ordering = ["-is_default", "label"]
        indexes = [
            models.Index(fields=["party", "is_default"], name="party_address_default_idx"),
        ]
        verbose_name = "Party Address"
        verbose_name_plural = "Party Addresses"

    def __str__(self):
        return f"{self.party} — {self.get_label_display()}: {self.city}"


# ─── PartyNote ─────────────────────────────────────────────────────────────────

class PartyNote(models.Model):
    """
    Append-only freetext note attached to a Party.

    Notes are immutable audit records — there is no updated_at and no
    soft-delete. Once created, a note cannot be edited or removed.
    The author FK uses SET_NULL so notes are preserved if the author is deleted.
    """
    party = models.ForeignKey(
        Party,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    body = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="party_notes_authored",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "party_notes"
        ordering = ["-created_at"]
        verbose_name = "Party Note"
        verbose_name_plural = "Party Notes"

    def __str__(self):
        return f"Note on {self.party} at {self.created_at:%Y-%m-%d}"


# ─── PartyAttachment ───────────────────────────────────────────────────────────

class PartyAttachment(models.Model):
    """
    File attachment associated with a Party.

    Model is defined now to establish the DB schema.
    The file upload endpoint is deferred to phase 2 — MEDIA_ROOT and
    MEDIA_URL must be configured in settings.py before enabling uploads.
    """
    party = models.ForeignKey(
        Party,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    label = models.CharField(max_length=200)
    file = models.FileField(upload_to="parties/attachments/%Y/%m/")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="party_attachments_uploaded",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "party_attachments"
        ordering = ["-created_at"]
        verbose_name = "Party Attachment"
        verbose_name_plural = "Party Attachments"

    def __str__(self):
        return f"{self.label} — {self.party}"


# ─── PartyRelationship ─────────────────────────────────────────────────────────

class PartyRelationship(TimestampedModel):
    """
    Links two Party records in a directed role relationship.

    from_party is the member/child (e.g. a person), to_party is the
    organisation/parent (e.g. a company). role describes the nature of the
    link (e.g. "employee", "director", "contact").

    unique_together prevents duplicate rows for the same
    (from_party, to_party, role) combination. A previously closed relationship
    with the same combination cannot be re-opened without first deleting it —
    this is intentional; callers must close_party_relationship then
    link_parties again to model a re-hire.

    is_active + ended_on together model the temporal lifecycle of the link.
    """
    from_party = models.ForeignKey(
        Party,
        on_delete=models.CASCADE,
        related_name="relationships_as_member",
    )
    # to_party is nullable until the companies app ships and existing
    # OrganizationPersonRelation rows can be pointed at real Party records.
    to_party = models.ForeignKey(
        Party,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="relationships_as_org",
    )
    role = models.CharField(max_length=100)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    started_on = models.DateField(null=True, blank=True)
    ended_on = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "party_relationships"
        unique_together = [("from_party", "to_party", "role")]
        indexes = [
            models.Index(fields=["to_party", "is_active"], name="party_rel_to_active_idx"),
        ]
        ordering = ["-is_active", "-started_on", "-created_at"]
        verbose_name = "Party Relationship"
        verbose_name_plural = "Party Relationships"

    def __str__(self):
        return f"{self.from_party} → {self.to_party} ({self.role})"
