"""
test_selectors.py — selector (read layer) tests for the party module.
"""
from django.test import TestCase

from party.exceptions import PartyNotFoundError
from party.models import (
    Party,
    PartyAddress,
    PartyCategory,
    PartyNote,
    PartyRelationship,
)
from party.selectors import (
    get_party_addresses,
    get_party_by_id,
    get_party_categories,
    get_party_notes,
    get_party_relationships,
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


# ─── get_party_by_id ──────────────────────────────────────────────────────────

class GetPartyByIdTest(TestCase):
    def test_returns_party(self):
        party = make_party()
        result = get_party_by_id(party_id=party.id)
        self.assertEqual(result.id, party.id)

    def test_raises_if_not_found(self):
        with self.assertRaises(PartyNotFoundError):
            get_party_by_id(party_id=99999)

    def test_returns_inactive_party(self):
        party = make_party(is_active=False)
        result = get_party_by_id(party_id=party.id)
        self.assertFalse(result.is_active)


# ─── get_party_categories ────────────────────────────────────────────────────

class GetPartyCategoriesTest(TestCase):
    def test_returns_all_by_default(self):
        make_category(name="Cat1", slug="cat1")
        make_category(name="Cat2", slug="cat2")
        self.assertEqual(get_party_categories().count(), 2)

    def test_filter_active_only(self):
        make_category(name="Active", slug="active")
        make_category(name="Inactive", slug="inactive", is_active=False)
        self.assertEqual(get_party_categories(is_active=True).count(), 1)

    def test_filter_inactive_only(self):
        make_category(name="Active", slug="active")
        make_category(name="Inactive", slug="inactive", is_active=False)
        self.assertEqual(get_party_categories(is_active=False).count(), 1)

    def test_ordered_by_name(self):
        make_category(name="Zeta", slug="zeta")
        make_category(name="Alpha", slug="alpha")
        names = list(get_party_categories().values_list("name", flat=True))
        self.assertEqual(names, ["Alpha", "Zeta"])


# ─── get_party_addresses ─────────────────────────────────────────────────────

class GetPartyAddressesTest(TestCase):
    def setUp(self):
        self.party = make_party()

    def test_returns_active_by_default(self):
        PartyAddress.objects.create(
            party=self.party, line1="1 St", city="London", country="UK"
        )
        PartyAddress.objects.create(
            party=self.party,
            line1="2 St",
            city="Leeds",
            country="UK",
            is_active=False,
        )
        results = list(get_party_addresses(party_id=self.party.id))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].city, "London")

    def test_includes_inactive_when_none(self):
        PartyAddress.objects.create(
            party=self.party, line1="1 St", city="A", country="UK", is_active=False
        )
        results = list(get_party_addresses(party_id=self.party.id, is_active=None))
        self.assertEqual(len(results), 1)

    def test_default_address_ordered_first(self):
        PartyAddress.objects.create(
            party=self.party, line1="Non-default", city="A", country="UK", is_default=False
        )
        PartyAddress.objects.create(
            party=self.party, line1="Default", city="B", country="UK", is_default=True
        )
        results = list(get_party_addresses(party_id=self.party.id))
        self.assertTrue(results[0].is_default)


# ─── get_party_notes ─────────────────────────────────────────────────────────

class GetPartyNotesTest(TestCase):
    def test_returns_notes_newest_first(self):
        party = make_party()
        PartyNote.objects.create(party=party, body="First")
        PartyNote.objects.create(party=party, body="Second")
        results = list(get_party_notes(party_id=party.id))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].body, "Second")

    def test_returns_empty_for_no_notes(self):
        party = make_party()
        results = list(get_party_notes(party_id=party.id))
        self.assertEqual(results, [])


# ─── get_party_relationships ─────────────────────────────────────────────────

class GetPartyRelationshipsTest(TestCase):
    def setUp(self):
        self.person = make_party(party_type=Party.PartyType.PERSON)
        self.org1 = make_party(party_type=Party.PartyType.COMPANY)
        self.org2 = make_party(party_type=Party.PartyType.COMPANY)

    def test_filter_by_from_party(self):
        PartyRelationship.objects.create(
            from_party=self.person, to_party=self.org1, role="contact"
        )
        results = list(get_party_relationships(from_party_id=self.person.id))
        self.assertEqual(len(results), 1)

    def test_filter_by_to_party(self):
        PartyRelationship.objects.create(
            from_party=self.person, to_party=self.org1, role="contact"
        )
        results = list(get_party_relationships(to_party_id=self.org1.id))
        self.assertEqual(len(results), 1)

    def test_filter_active_only(self):
        PartyRelationship.objects.create(
            from_party=self.person, to_party=self.org1, role="active", is_active=True
        )
        PartyRelationship.objects.create(
            from_party=self.person, to_party=self.org2, role="inactive", is_active=False
        )
        results = list(
            get_party_relationships(from_party_id=self.person.id, is_active=True)
        )
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].is_active)

    def test_no_filters_returns_all(self):
        PartyRelationship.objects.create(
            from_party=self.person, to_party=self.org1, role="r1"
        )
        PartyRelationship.objects.create(
            from_party=self.person, to_party=self.org2, role="r2"
        )
        results = list(get_party_relationships())
        self.assertEqual(len(results), 2)
