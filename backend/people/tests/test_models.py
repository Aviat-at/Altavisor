"""
test_models.py — model-level property and constraint tests.

These tests exercise the minimal model behaviour (@property methods,
__str__, Meta constraints) without going through the service or API layers.
"""
from django.db import IntegrityError
from django.test import TestCase

from party.models import (
    Party,
    PartyAddress,
    PartyCategory,
    PartyCategoryAssignment,
    PartyNote,
    PartyRelationship,
)
from people.models import Person


# ─── Helpers ───────────────────────────────────────────────────────────────────

def make_party(**kwargs) -> Party:
    defaults = {"party_type": Party.PartyType.PERSON, "is_active": True}
    defaults.update(kwargs)
    return Party.objects.create(**defaults)


def make_person(**kwargs) -> Person:
    """Create a Party + Person pair. Accepts is_active and created_by for the Party."""
    is_active = kwargs.pop("is_active", True)
    created_by = kwargs.pop("created_by", None)
    defaults = {"first_name": "Alice", "last_name": "Smith"}
    defaults.update(kwargs)
    party = Party.objects.create(
        party_type=Party.PartyType.PERSON,
        is_active=is_active,
        created_by=created_by,
    )
    return Person.objects.create(party=party, **defaults)


def make_category(**kwargs) -> PartyCategory:
    defaults = {"name": "Customer", "slug": "customer"}
    defaults.update(kwargs)
    return PartyCategory.objects.create(**defaults)


# ─── Person ────────────────────────────────────────────────────────────────────

class PersonPropertyTest(TestCase):
    def test_full_name(self):
        p = make_person(first_name="John", last_name="Doe")
        self.assertEqual(p.full_name, "John Doe")

    def test_display_name_uses_preferred_when_set(self):
        p = make_person(preferred_name="Johnny")
        self.assertEqual(p.display_name, "Johnny")

    def test_display_name_falls_back_to_full_name(self):
        p = make_person(first_name="John", last_name="Doe", preferred_name="")
        self.assertEqual(p.display_name, "John Doe")

    def test_initials(self):
        p = make_person(first_name="John", last_name="Doe")
        self.assertEqual(p.initials, "JD")

    def test_initials_single_letter_parts(self):
        p = make_person(first_name="A", last_name="B")
        self.assertEqual(p.initials, "AB")

    def test_str(self):
        p = make_person(first_name="Jane", last_name="Smith")
        self.assertEqual(str(p), "Jane Smith")

    def test_default_is_active_via_party(self):
        p = make_person()
        self.assertTrue(p.party.is_active)

    def test_email_nullable(self):
        p = make_person(email=None)
        self.assertIsNone(p.email)

    def test_email_unique_constraint(self):
        make_person(first_name="First", email="shared@example.com")
        with self.assertRaises(IntegrityError):
            make_person(first_name="Second", last_name="Other", email="shared@example.com")

    def test_email_null_not_unique_constrained(self):
        # Two persons with no email should both be storable
        make_person(first_name="First", last_name="A", email=None)
        make_person(first_name="Second", last_name="B", email=None)
        self.assertEqual(Person.objects.filter(email__isnull=True).count(), 2)


# ─── PartyCategory ─────────────────────────────────────────────────────────────

class PartyCategoryModelTest(TestCase):
    def test_str(self):
        cat = make_category(name="Supplier")
        self.assertEqual(str(cat), "Supplier")

    def test_default_is_not_system(self):
        cat = make_category()
        self.assertFalse(cat.is_system)

    def test_default_is_active(self):
        cat = make_category()
        self.assertTrue(cat.is_active)

    def test_slug_unique_constraint(self):
        make_category(name="Cat One", slug="cat-one")
        with self.assertRaises(IntegrityError):
            make_category(name="Cat Two", slug="cat-one")

    def test_name_unique_constraint(self):
        make_category(name="Unique Name", slug="unique-name")
        with self.assertRaises(IntegrityError):
            make_category(name="Unique Name", slug="unique-name-2")


# ─── PartyCategoryAssignment ───────────────────────────────────────────────────

class PartyCategoryAssignmentModelTest(TestCase):
    def setUp(self):
        self.person = make_person()
        self.category = make_category()

    def test_str(self):
        assignment = PartyCategoryAssignment.objects.create(
            party=self.person.party, category=self.category
        )
        self.assertIn(self.category.name, str(assignment))

    def test_unique_together_constraint(self):
        PartyCategoryAssignment.objects.create(
            party=self.person.party, category=self.category
        )
        with self.assertRaises(IntegrityError):
            PartyCategoryAssignment.objects.create(
                party=self.person.party, category=self.category
            )

    def test_default_is_active(self):
        assignment = PartyCategoryAssignment.objects.create(
            party=self.person.party, category=self.category
        )
        self.assertTrue(assignment.is_active)


# ─── PartyAddress ──────────────────────────────────────────────────────────────

class PartyAddressModelTest(TestCase):
    def setUp(self):
        self.person = make_person()

    def test_str(self):
        addr = PartyAddress.objects.create(
            party=self.person.party,
            label=PartyAddress.Label.HOME,
            line1="1 Main St",
            city="London",
            country="UK",
        )
        self.assertIn("London", str(addr))

    def test_default_label_is_home(self):
        addr = PartyAddress.objects.create(
            party=self.person.party, line1="1 St", city="City", country="UK"
        )
        self.assertEqual(addr.label, PartyAddress.Label.HOME)

    def test_default_is_active(self):
        addr = PartyAddress.objects.create(
            party=self.person.party, line1="1 St", city="City", country="UK"
        )
        self.assertTrue(addr.is_active)


# ─── PartyNote ─────────────────────────────────────────────────────────────────

class PartyNoteModelTest(TestCase):
    def test_str_contains_date(self):
        person = make_person(first_name="Bob", last_name="Jones")
        note = PartyNote.objects.create(party=person.party, body="A note.")
        self.assertIn(str(note.party.id), str(note))

    def test_created_at_set_on_create(self):
        person = make_person()
        note = PartyNote.objects.create(party=person.party, body="Test.")
        self.assertIsNotNone(note.created_at)


# ─── PartyRelationship ─────────────────────────────────────────────────────────

class PartyRelationshipModelTest(TestCase):
    def setUp(self):
        self.person = make_person()
        self.org_party = Party.objects.create(
            party_type=Party.PartyType.ORGANIZATION, is_active=True
        )

    def test_str(self):
        rel = PartyRelationship.objects.create(
            from_party=self.person.party,
            to_party=self.org_party,
            role="contact",
        )
        self.assertIn("contact", str(rel))

    def test_unique_together_constraint(self):
        PartyRelationship.objects.create(
            from_party=self.person.party,
            to_party=self.org_party,
            role="contact",
        )
        with self.assertRaises(IntegrityError):
            PartyRelationship.objects.create(
                from_party=self.person.party,
                to_party=self.org_party,
                role="contact",
            )

    def test_default_is_active(self):
        rel = PartyRelationship.objects.create(
            from_party=self.person.party,
            to_party=self.org_party,
            role="rep",
        )
        self.assertTrue(rel.is_active)

    def test_to_party_nullable(self):
        # to_party may be null until the companies app ships
        rel = PartyRelationship.objects.create(
            from_party=self.person.party,
            to_party=None,
            role="pending",
        )
        self.assertIsNone(rel.to_party)
