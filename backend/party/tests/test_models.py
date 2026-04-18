"""
test_models.py — model-level property and constraint tests for the party module.

These tests exercise minimal model behaviour (__str__, Meta constraints,
defaults) without going through the service or API layers.
"""
from django.db import IntegrityError
from django.test import TestCase

from party.models import (
    Party,
    PartyAddress,
    PartyAttachment,
    PartyCategory,
    PartyCategoryAssignment,
    PartyNote,
    PartyRelationship,
)


# ─── Helpers ───────────────────────────────────────────────────────────────────

def make_party(**kwargs) -> Party:
    defaults = {"party_type": Party.PartyType.PERSON, "is_active": True}
    defaults.update(kwargs)
    return Party.objects.create(**defaults)


def make_category(**kwargs) -> PartyCategory:
    defaults = {"name": "Customer", "slug": "customer"}
    defaults.update(kwargs)
    return PartyCategory.objects.create(**defaults)


# ─── Party ────────────────────────────────────────────────────────────────────

class PartyModelTest(TestCase):
    def test_str_contains_id_and_type(self):
        party = make_party(party_type=Party.PartyType.PERSON)
        s = str(party)
        self.assertIn("person", s)
        self.assertIn(str(party.id), s)

    def test_default_is_active_true(self):
        party = make_party()
        self.assertTrue(party.is_active)

    def test_created_by_nullable(self):
        party = make_party()
        self.assertIsNone(party.created_by)

    def test_party_type_choices(self):
        person = make_party(party_type=Party.PartyType.PERSON)
        company = make_party(party_type=Party.PartyType.ORGANIZATION)
        self.assertEqual(person.party_type, "person")
        self.assertEqual(company.party_type, "organization")


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
        self.party = make_party()
        self.category = make_category()

    def test_str(self):
        assignment = PartyCategoryAssignment.objects.create(
            party=self.party, category=self.category
        )
        self.assertIn(self.category.name, str(assignment))

    def test_unique_together_constraint(self):
        PartyCategoryAssignment.objects.create(
            party=self.party, category=self.category
        )
        with self.assertRaises(IntegrityError):
            PartyCategoryAssignment.objects.create(
                party=self.party, category=self.category
            )

    def test_default_is_active(self):
        assignment = PartyCategoryAssignment.objects.create(
            party=self.party, category=self.category
        )
        self.assertTrue(assignment.is_active)


# ─── PartyAddress ──────────────────────────────────────────────────────────────

class PartyAddressModelTest(TestCase):
    def setUp(self):
        self.party = make_party()

    def test_str(self):
        addr = PartyAddress.objects.create(
            party=self.party,
            label=PartyAddress.Label.HOME,
            line1="1 Main St",
            city="London",
            country="UK",
        )
        self.assertIn("London", str(addr))

    def test_default_label_is_home(self):
        addr = PartyAddress.objects.create(
            party=self.party, line1="1 St", city="City", country="UK"
        )
        self.assertEqual(addr.label, PartyAddress.Label.HOME)

    def test_default_is_active(self):
        addr = PartyAddress.objects.create(
            party=self.party, line1="1 St", city="City", country="UK"
        )
        self.assertTrue(addr.is_active)

    def test_default_is_not_default_address(self):
        addr = PartyAddress.objects.create(
            party=self.party, line1="1 St", city="City", country="UK"
        )
        self.assertFalse(addr.is_default)


# ─── PartyNote ─────────────────────────────────────────────────────────────────

class PartyNoteModelTest(TestCase):
    def test_str_contains_party_id(self):
        party = make_party()
        note = PartyNote.objects.create(party=party, body="A note.")
        self.assertIn(str(party.id), str(note))

    def test_created_at_set_on_create(self):
        party = make_party()
        note = PartyNote.objects.create(party=party, body="Test.")
        self.assertIsNotNone(note.created_at)

    def test_author_nullable(self):
        party = make_party()
        note = PartyNote.objects.create(party=party, body="Anonymous note.")
        self.assertIsNone(note.author)


# ─── PartyRelationship ─────────────────────────────────────────────────────────

class PartyRelationshipModelTest(TestCase):
    def setUp(self):
        self.from_party = make_party(party_type=Party.PartyType.PERSON)
        self.to_party = make_party(party_type=Party.PartyType.ORGANIZATION)

    def test_str(self):
        rel = PartyRelationship.objects.create(
            from_party=self.from_party,
            to_party=self.to_party,
            role="contact",
        )
        self.assertIn("contact", str(rel))

    def test_unique_together_constraint(self):
        PartyRelationship.objects.create(
            from_party=self.from_party,
            to_party=self.to_party,
            role="contact",
        )
        with self.assertRaises(IntegrityError):
            PartyRelationship.objects.create(
                from_party=self.from_party,
                to_party=self.to_party,
                role="contact",
            )

    def test_default_is_active(self):
        rel = PartyRelationship.objects.create(
            from_party=self.from_party,
            to_party=self.to_party,
            role="rep",
        )
        self.assertTrue(rel.is_active)

    def test_to_party_nullable(self):
        rel = PartyRelationship.objects.create(
            from_party=self.from_party,
            to_party=None,
            role="pending",
        )
        self.assertIsNone(rel.to_party)

    def test_null_to_party_not_unique_constrained(self):
        # Two NULL to_party rows with same role should both be storable (NULL != NULL)
        PartyRelationship.objects.create(
            from_party=self.from_party,
            to_party=None,
            role="pending",
        )
        rel2 = PartyRelationship.objects.create(
            from_party=self.from_party,
            to_party=None,
            role="pending",
        )
        self.assertIsNotNone(rel2.id)

    def test_default_is_not_primary(self):
        rel = PartyRelationship.objects.create(
            from_party=self.from_party,
            to_party=self.to_party,
            role="analyst",
        )
        self.assertFalse(rel.is_primary)
