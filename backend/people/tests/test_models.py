"""
test_models.py — model-level property and constraint tests.

These tests exercise the minimal model behaviour (@property methods,
__str__, Meta constraints) without going through the service or API layers.
"""
from django.db import IntegrityError
from django.test import TestCase

from people.models import (
    OrganizationPersonRelation,
    Person,
    PersonAddress,
    PersonCategory,
    PersonCategoryAssignment,
    PersonNote,
)


# ─── Helpers ───────────────────────────────────────────────────────────────────

def make_person(**kwargs) -> Person:
    defaults = {"first_name": "Alice", "last_name": "Smith"}
    defaults.update(kwargs)
    return Person.objects.create(**defaults)


def make_category(**kwargs) -> PersonCategory:
    defaults = {"name": "Customer", "slug": "customer"}
    defaults.update(kwargs)
    return PersonCategory.objects.create(**defaults)


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

    def test_default_is_active(self):
        p = make_person()
        self.assertTrue(p.is_active)

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


# ─── PersonCategory ────────────────────────────────────────────────────────────

class PersonCategoryModelTest(TestCase):
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


# ─── PersonCategoryAssignment ──────────────────────────────────────────────────

class PersonCategoryAssignmentModelTest(TestCase):
    def setUp(self):
        self.person = make_person()
        self.category = make_category()

    def test_str(self):
        assignment = PersonCategoryAssignment.objects.create(
            person=self.person, category=self.category
        )
        self.assertIn(self.person.full_name, str(assignment))
        self.assertIn(self.category.name, str(assignment))

    def test_unique_together_constraint(self):
        PersonCategoryAssignment.objects.create(
            person=self.person, category=self.category
        )
        with self.assertRaises(IntegrityError):
            PersonCategoryAssignment.objects.create(
                person=self.person, category=self.category
            )

    def test_default_is_active(self):
        assignment = PersonCategoryAssignment.objects.create(
            person=self.person, category=self.category
        )
        self.assertTrue(assignment.is_active)


# ─── PersonAddress ─────────────────────────────────────────────────────────────

class PersonAddressModelTest(TestCase):
    def setUp(self):
        self.person = make_person()

    def test_str(self):
        addr = PersonAddress.objects.create(
            person=self.person,
            label=PersonAddress.Label.HOME,
            line1="1 Main St",
            city="London",
            country="UK",
        )
        self.assertIn("London", str(addr))

    def test_default_label_is_home(self):
        addr = PersonAddress.objects.create(
            person=self.person, line1="1 St", city="City", country="UK"
        )
        self.assertEqual(addr.label, PersonAddress.Label.HOME)

    def test_default_is_active(self):
        addr = PersonAddress.objects.create(
            person=self.person, line1="1 St", city="City", country="UK"
        )
        self.assertTrue(addr.is_active)


# ─── PersonNote ────────────────────────────────────────────────────────────────

class PersonNoteModelTest(TestCase):
    def test_str_contains_person_name(self):
        person = make_person(first_name="Bob", last_name="Jones")
        note = PersonNote.objects.create(person=person, body="A note.")
        self.assertIn("Bob Jones", str(note))

    def test_created_at_set_on_create(self):
        person = make_person()
        note = PersonNote.objects.create(person=person, body="Test.")
        self.assertIsNotNone(note.created_at)


# ─── OrganizationPersonRelation ────────────────────────────────────────────────

class OrgRelationModelTest(TestCase):
    def setUp(self):
        self.person = make_person()

    def test_str(self):
        rel = OrganizationPersonRelation.objects.create(
            person=self.person,
            organization_id=42,
            organization_type="customer",
            role="contact",
        )
        self.assertIn("customer#42", str(rel))
        self.assertIn("contact", str(rel))

    def test_unique_together_constraint(self):
        OrganizationPersonRelation.objects.create(
            person=self.person,
            organization_id=1,
            organization_type="customer",
            role="contact",
        )
        with self.assertRaises(IntegrityError):
            OrganizationPersonRelation.objects.create(
                person=self.person,
                organization_id=1,
                organization_type="customer",
                role="contact",
            )

    def test_default_is_active(self):
        rel = OrganizationPersonRelation.objects.create(
            person=self.person,
            organization_id=1,
            organization_type="supplier",
            role="rep",
        )
        self.assertTrue(rel.is_active)
