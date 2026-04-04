"""
test_selectors.py — selector (read layer) tests.

These tests verify that selectors return the correct querysets / dicts,
apply the right filters, and attach the expected prefetched data.
"""
from django.test import TestCase

from people.exceptions import CategoryNotFoundError, PersonNotFoundError
from people.models import (
    OrganizationPersonRelation,
    Person,
    PersonAddress,
    PersonCategory,
    PersonCategoryAssignment,
    PersonNote,
)
from people.selectors import (
    get_active_person_categories,
    get_category,
    get_person_addresses,
    get_person_categories,
    get_person_detail,
    get_person_notes,
    get_person_organizations,
    list_categories,
    list_persons,
    search_persons,
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


# ─── list_persons ──────────────────────────────────────────────────────────────

class ListPersonsTest(TestCase):
    def test_returns_active_persons_by_default(self):
        make_person()
        make_person(first_name="Inactive", last_name="Person", is_active=False)
        result = list_persons()
        self.assertEqual(result["count"], 1)

    def test_can_list_inactive_persons(self):
        make_person()
        make_person(first_name="Inactive", last_name="Person", is_active=False)
        result = list_persons(is_active=False)
        self.assertEqual(result["count"], 1)
        self.assertFalse(result["results"][0].is_active)

    def test_search_by_first_name(self):
        make_person(first_name="Alice", last_name="Smith")
        make_person(first_name="Bob", last_name="Jones", email="b@test.com")
        result = list_persons(search="alice")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0].first_name, "Alice")

    def test_search_by_last_name(self):
        make_person(first_name="Alice", last_name="Smith")
        make_person(first_name="Bob", last_name="Jones", email="b@test.com")
        result = list_persons(search="jones")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0].last_name, "Jones")

    def test_search_by_email(self):
        make_person(email="findme@example.com")
        make_person(first_name="Other", last_name="Person", email="other@example.com")
        result = list_persons(search="findme")
        self.assertEqual(result["count"], 1)

    def test_filter_by_category_id(self):
        p1 = make_person()
        make_person(first_name="Bob", last_name="Jones", email="bob@test.com")
        cat = make_category()
        PersonCategoryAssignment.objects.create(person=p1, category=cat)
        result = list_persons(category_id=cat.id)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0].id, p1.id)

    def test_pagination_count_is_total_not_page(self):
        for i in range(5):
            make_person(
                first_name=f"Person{i}", last_name="Test", email=f"p{i}@test.com"
            )
        result = list_persons(page=1, page_size=2)
        self.assertEqual(result["count"], 5)
        self.assertEqual(len(result["results"]), 2)
        self.assertTrue(result["has_next"])

    def test_last_page_has_next_false(self):
        for i in range(3):
            make_person(
                first_name=f"Person{i}", last_name="T", email=f"p{i}@test.com"
            )
        result = list_persons(page=2, page_size=2)
        self.assertEqual(len(result["results"]), 1)
        self.assertFalse(result["has_next"])

    def test_active_assignments_prefetched(self):
        person = make_person()
        cat = make_category()
        PersonCategoryAssignment.objects.create(person=person, category=cat)
        result = list_persons()
        p = result["results"][0]
        self.assertTrue(hasattr(p, "active_assignments"))
        self.assertEqual(len(p.active_assignments), 1)

    def test_inactive_assignments_not_in_active_assignments(self):
        person = make_person()
        cat = make_category()
        PersonCategoryAssignment.objects.create(
            person=person, category=cat, is_active=False
        )
        result = list_persons()
        p = result["results"][0]
        self.assertEqual(len(p.active_assignments), 0)


# ─── get_person_detail ─────────────────────────────────────────────────────────

class GetPersonDetailTest(TestCase):
    def test_returns_person(self):
        person = make_person()
        detail = get_person_detail(person_id=person.id)
        self.assertEqual(detail.id, person.id)

    def test_raises_if_not_found(self):
        with self.assertRaises(PersonNotFoundError):
            get_person_detail(person_id=99999)

    def test_finds_inactive_person(self):
        person = make_person(is_active=False)
        detail = get_person_detail(person_id=person.id)
        self.assertFalse(detail.is_active)

    def test_addresses_prefetched(self):
        person = make_person()
        PersonAddress.objects.create(
            person=person, line1="1 St", city="London", country="UK"
        )
        detail = get_person_detail(person_id=person.id)
        # Should not cause additional queries
        self.assertEqual(detail.addresses.all().count(), 1)

    def test_active_assignments_prefetched_as_to_attr(self):
        person = make_person()
        cat = make_category()
        PersonCategoryAssignment.objects.create(person=person, category=cat)
        detail = get_person_detail(person_id=person.id)
        self.assertTrue(hasattr(detail, "active_assignments"))
        self.assertEqual(len(detail.active_assignments), 1)

    def test_only_active_addresses_in_prefetch(self):
        person = make_person()
        PersonAddress.objects.create(
            person=person, line1="Active", city="London", country="UK", is_active=True
        )
        PersonAddress.objects.create(
            person=person, line1="Inactive", city="Leeds", country="UK", is_active=False
        )
        detail = get_person_detail(person_id=person.id)
        self.assertEqual(detail.addresses.all().count(), 1)

    def test_notes_prefetched(self):
        person = make_person()
        PersonNote.objects.create(person=person, body="Note 1")
        PersonNote.objects.create(person=person, body="Note 2")
        detail = get_person_detail(person_id=person.id)
        self.assertEqual(detail.notes.all().count(), 2)


# ─── search_persons ────────────────────────────────────────────────────────────

class SearchPersonsTest(TestCase):
    def test_finds_by_first_name(self):
        make_person(first_name="Unique", last_name="Name")
        results = list(search_persons(q="Unique"))
        self.assertEqual(len(results), 1)

    def test_finds_by_email(self):
        make_person(email="findme@test.com")
        results = list(search_persons(q="findme"))
        self.assertEqual(len(results), 1)

    def test_excludes_inactive_by_default(self):
        make_person(first_name="Inactive", is_active=False)
        results = list(search_persons(q="Inactive"))
        self.assertEqual(len(results), 0)

    def test_includes_inactive_when_flag_set(self):
        make_person(first_name="Inactive", is_active=False)
        results = list(search_persons(q="Inactive", active_only=False))
        self.assertEqual(len(results), 1)

    def test_empty_query_returns_all_active(self):
        make_person()
        make_person(first_name="Second", last_name="Person", email="s@test.com")
        results = list(search_persons(q=""))
        self.assertEqual(len(results), 2)


# ─── list_categories ───────────────────────────────────────────────────────────

class ListCategoriesTest(TestCase):
    def test_returns_all_by_default(self):
        make_category(name="Cat1", slug="cat1")
        make_category(name="Cat2", slug="cat2")
        self.assertEqual(list_categories().count(), 2)

    def test_filter_active_only(self):
        make_category(name="Active", slug="active")
        make_category(name="Inactive", slug="inactive", is_active=False)
        self.assertEqual(list_categories(is_active=True).count(), 1)

    def test_filter_inactive_only(self):
        make_category(name="Active", slug="active")
        make_category(name="Inactive", slug="inactive", is_active=False)
        self.assertEqual(list_categories(is_active=False).count(), 1)

    def test_filter_system_only(self):
        make_category(name="System", slug="system", is_system=True)
        make_category(name="Custom", slug="custom", is_system=False)
        results = list(list_categories(is_system=True))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "System")

    def test_ordered_by_name(self):
        make_category(name="Zeta", slug="zeta")
        make_category(name="Alpha", slug="alpha")
        names = list(list_categories().values_list("name", flat=True))
        self.assertEqual(names, ["Alpha", "Zeta"])


# ─── get_category ──────────────────────────────────────────────────────────────

class GetCategoryTest(TestCase):
    def test_returns_category(self):
        cat = make_category()
        result = get_category(category_id=cat.id)
        self.assertEqual(result.id, cat.id)

    def test_raises_if_not_found(self):
        with self.assertRaises(CategoryNotFoundError):
            get_category(category_id=99999)


# ─── get_person_categories ─────────────────────────────────────────────────────

class GetPersonCategoriesTest(TestCase):
    def setUp(self):
        self.person = make_person()
        self.cat = make_category()

    def test_returns_active_assignments(self):
        PersonCategoryAssignment.objects.create(
            person=self.person, category=self.cat
        )
        results = list(get_person_categories(person_id=self.person.id))
        self.assertEqual(len(results), 1)

    def test_filters_inactive_by_default(self):
        PersonCategoryAssignment.objects.create(
            person=self.person, category=self.cat, is_active=False
        )
        results = list(get_person_categories(person_id=self.person.id))
        self.assertEqual(len(results), 0)

    def test_includes_inactive_when_flag_false(self):
        PersonCategoryAssignment.objects.create(
            person=self.person, category=self.cat, is_active=False
        )
        results = list(
            get_person_categories(person_id=self.person.id, active_only=False)
        )
        self.assertEqual(len(results), 1)

    def test_get_active_person_categories_wrapper(self):
        PersonCategoryAssignment.objects.create(
            person=self.person, category=self.cat
        )
        results = list(get_active_person_categories(person_id=self.person.id))
        self.assertEqual(len(results), 1)


# ─── get_person_addresses ──────────────────────────────────────────────────────

class GetPersonAddressesTest(TestCase):
    def setUp(self):
        self.person = make_person()

    def test_returns_active_addresses_by_default(self):
        PersonAddress.objects.create(
            person=self.person, line1="1 St", city="London", country="UK"
        )
        PersonAddress.objects.create(
            person=self.person,
            line1="2 St",
            city="Leeds",
            country="UK",
            is_active=False,
        )
        results = list(get_person_addresses(person_id=self.person.id))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].city, "London")

    def test_includes_inactive_when_flag_false(self):
        PersonAddress.objects.create(
            person=self.person,
            line1="1 St",
            city="City",
            country="UK",
            is_active=False,
        )
        results = list(
            get_person_addresses(person_id=self.person.id, active_only=False)
        )
        self.assertEqual(len(results), 1)

    def test_default_address_ordered_first(self):
        PersonAddress.objects.create(
            person=self.person, line1="Non-default", city="A", country="UK", is_default=False
        )
        PersonAddress.objects.create(
            person=self.person, line1="Default", city="B", country="UK", is_default=True
        )
        results = list(get_person_addresses(person_id=self.person.id))
        self.assertTrue(results[0].is_default)


# ─── get_person_notes ──────────────────────────────────────────────────────────

class GetPersonNotesTest(TestCase):
    def test_returns_notes_newest_first(self):
        person = make_person()
        PersonNote.objects.create(person=person, body="First")
        PersonNote.objects.create(person=person, body="Second")
        results = list(get_person_notes(person_id=person.id))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].body, "Second")

    def test_returns_empty_for_person_with_no_notes(self):
        person = make_person()
        results = list(get_person_notes(person_id=person.id))
        self.assertEqual(results, [])


# ─── get_person_organizations ──────────────────────────────────────────────────

class GetPersonOrganizationsTest(TestCase):
    def setUp(self):
        self.person = make_person()

    def test_returns_all_by_default(self):
        OrganizationPersonRelation.objects.create(
            person=self.person,
            organization_id=1,
            organization_type="customer",
            role="contact",
            is_active=True,
        )
        OrganizationPersonRelation.objects.create(
            person=self.person,
            organization_id=2,
            organization_type="supplier",
            role="rep",
            is_active=False,
        )
        results = list(get_person_organizations(person_id=self.person.id))
        self.assertEqual(len(results), 2)

    def test_active_only_flag(self):
        OrganizationPersonRelation.objects.create(
            person=self.person,
            organization_id=1,
            organization_type="customer",
            role="contact",
            is_active=True,
        )
        OrganizationPersonRelation.objects.create(
            person=self.person,
            organization_id=2,
            organization_type="supplier",
            role="rep",
            is_active=False,
        )
        results = list(
            get_person_organizations(person_id=self.person.id, active_only=True)
        )
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].is_active)
