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


# ─── Person ────────────────────────────────────────────────────────────────────

class Person(TimestampedModel):
    """
    Human-specific identity data, extending Party via a OneToOne link.

    party.Party holds is_active, created_by, and all shared sub-resources
    (addresses, notes, attachments, categories, relationships). Person holds
    the human-specific fields only.

    A Person must never exist without a Party — services.create_person()
    creates both atomically.
    """

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"
        PREFER_NOT_TO_SAY = "prefer_not_to_say", "Prefer not to say"

    party = models.OneToOneField(
        "party.Party",
        on_delete=models.CASCADE,
        related_name="person",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    preferred_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    mobile = models.CharField(max_length=30, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=Gender.choices, blank=True)

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
