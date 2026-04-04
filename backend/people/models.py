from django.conf import settings
from django.db import models


# ─── Abstract Base ─────────────────────────────────────────────────────────────

class TimestampedModel(models.Model):
    """
    Abstract base that adds created_at / updated_at to every people model.
    Consistent with the audit-friendly field convention used in accounts.User
    (date_joined, last_login).
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ─── PersonCategory ────────────────────────────────────────────────────────────

class PersonCategory(TimestampedModel):
    """
    Classification label for a Person.

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
        db_table = "people_person_categories"
        ordering = ["name"]
        verbose_name = "Person Category"
        verbose_name_plural = "Person Categories"

    def __str__(self):
        return self.name


# ─── Person ────────────────────────────────────────────────────────────────────

class Person(TimestampedModel):
    """
    Master human-identity record.

    A single Person is reusable across multiple business contexts: customer
    contact, supplier representative, commission holder, billing contact,
    delivery contact, etc. The context is determined by PersonCategoryAssignment
    and OrganizationPersonRelation, not by fields on this model.

    email is nullable because not all persons have or provide one.
    When provided it must be globally unique.
    """

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"
        PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    preferred_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    mobile = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_persons",
    )

    # M2M through model — accessed via person.category_assignments.all()
    categories = models.ManyToManyField(
        PersonCategory,
        through="PersonCategoryAssignment",
        related_name="persons",
    )

    class Meta:
        db_table = "people_persons"
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["last_name", "first_name"], name="person_name_idx"),
            models.Index(fields=["email"], name="person_email_idx"),
        ]
        verbose_name = "Person"
        verbose_name_plural = "People"

    def __str__(self):
        return self.full_name

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def display_name(self) -> str:
        """Preferred name if set, otherwise full name."""
        return self.preferred_name or self.full_name

    @property
    def initials(self) -> str:
        parts = [self.first_name, self.last_name]
        return "".join(p[0].upper() for p in parts if p)


# ─── PersonCategoryAssignment ──────────────────────────────────────────────────

class PersonCategoryAssignment(TimestampedModel):
    """
    Explicit M2M through-model linking a Person to a PersonCategory.

    unique_together enforces that a (person, category) pair can only have
    one row. is_active allows soft-deactivation without losing history.
    The service layer additionally prevents creating a second active assignment
    for the same pair.
    """
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="category_assignments",
    )
    category = models.ForeignKey(
        PersonCategory,
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="category_assignments_made",
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "people_category_assignments"
        unique_together = [("person", "category")]
        ordering = ["category__name"]
        verbose_name = "Person Category Assignment"
        verbose_name_plural = "Person Category Assignments"

    def __str__(self):
        return f"{self.person} — {self.category}"


# ─── PersonAddress ─────────────────────────────────────────────────────────────

class PersonAddress(TimestampedModel):
    """
    A physical or postal address associated with a Person.

    A person may have multiple addresses with different labels.
    is_default=True indicates the primary address for a given person;
    the service layer ensures at most one default per person.
    is_active allows soft-deactivation without deleting historical addresses.
    """

    class Label(models.TextChoices):
        BILLING = "billing", "Billing"
        DELIVERY = "delivery", "Delivery"
        HOME = "home", "Home"
        WORK = "work", "Work"
        OTHER = "other", "Other"

    person = models.ForeignKey(
        Person,
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
        db_table = "people_addresses"
        ordering = ["-is_default", "label"]
        indexes = [
            models.Index(fields=["person", "is_default"], name="address_default_idx"),
        ]
        verbose_name = "Person Address"
        verbose_name_plural = "Person Addresses"

    def __str__(self):
        return f"{self.person} — {self.get_label_display()}: {self.city}"


# ─── PersonNote ────────────────────────────────────────────────────────────────

class PersonNote(models.Model):
    """
    Append-only freetext note attached to a Person.

    Notes are immutable audit records — there is no updated_at and no
    soft-delete. Once created, a note cannot be edited or removed.
    The author FK uses SET_NULL so notes are preserved if the author is deleted.
    """
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    body = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="person_notes_authored",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "people_notes"
        ordering = ["-created_at"]
        verbose_name = "Person Note"
        verbose_name_plural = "Person Notes"

    def __str__(self):
        return f"Note on {self.person} at {self.created_at:%Y-%m-%d}"


# ─── PersonAttachment ──────────────────────────────────────────────────────────

class PersonAttachment(models.Model):
    """
    File attachment associated with a Person.

    Model is defined now to establish the DB schema.
    The file upload endpoint is deferred to phase 2 — MEDIA_ROOT and
    MEDIA_URL must be configured in settings.py before enabling uploads.
    """
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    label = models.CharField(max_length=200)
    file = models.FileField(upload_to="people/attachments/%Y/%m/")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="person_attachments_uploaded",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "people_attachments"
        ordering = ["-created_at"]
        verbose_name = "Person Attachment"
        verbose_name_plural = "Person Attachments"

    def __str__(self):
        return f"{self.label} — {self.person}"


# ─── OrganizationPersonRelation ────────────────────────────────────────────────

class OrganizationPersonRelation(TimestampedModel):
    """
    Links a Person to an external organization in a specific role.

    organization_id + organization_type are used instead of a ForeignKey or
    GenericForeignKey because:
      - No organizations app exists yet in this codebase.
      - GenericForeignKey prevents DB-level FK constraints and degrades
        query performance.
      - These two plain fields are easily migrated to a proper FK once
        an orgs app ships — it is a one-migration change.

    organization_type examples: "customer", "supplier", "partner"
    role examples: "contact", "representative", "billing", "delivery",
                   "commission_holder"

    unique_together prevents duplicate rows for the same combination.
    The service layer additionally prevents duplicate *active* relations.
    is_active + ended_on together model the temporal lifecycle of the link.
    """
    person = models.ForeignKey(
        Person,
        on_delete=models.CASCADE,
        related_name="org_relations",
    )
    organization_id = models.PositiveIntegerField(db_index=True)
    organization_type = models.CharField(max_length=50)
    role = models.CharField(max_length=100)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    started_on = models.DateField(null=True, blank=True)
    ended_on = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "people_org_relations"
        unique_together = [("person", "organization_id", "organization_type", "role")]
        indexes = [
            models.Index(
                fields=["organization_id", "organization_type"],
                name="org_relation_org_idx",
            ),
        ]
        ordering = ["-is_active", "-started_on", "-created_at"]
        verbose_name = "Organization-Person Relation"
        verbose_name_plural = "Organization-Person Relations"

    def __str__(self):
        return (
            f"{self.person} — {self.organization_type}#{self.organization_id}"
            f" ({self.role})"
        )
