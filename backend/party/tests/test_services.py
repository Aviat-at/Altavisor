"""
test_services.py — service-layer unit tests for the party module.
"""
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from party.exceptions import (
    AddressNotFoundError,
    CategoryInactiveError,
    CategoryNotFoundError,
    CategorySystemProtectedError,
    DuplicateCategoryAssignmentError,
    PartyInactiveError,
    PartyNotFoundError,
    RelationshipConflictError,
    RelationshipNotFoundError,
)
from party.models import (
    Party,
    PartyAddress,
    PartyCategory,
    PartyCategoryAssignment,
    PartyNote,
    PartyRelationship,
)
from party.services import (
    assign_category_to_party,
    close_party_relationship,
    create_party,
    create_party_address,
    create_party_category,
    create_party_note,
    deactivate_party,
    deactivate_party_address,
    deactivate_party_category,
    link_parties,
    reactivate_party,
    remove_category_from_party,
    set_default_address,
    update_party_address,
    update_party_category,
    update_party_relationship,
)

User = get_user_model()


# ─── Helpers ───────────────────────────────────────────────────────────────────

def make_user(**kwargs) -> User:
    defaults = {"email": "user@test.com", "password": "testpass123"}
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def make_party(**kwargs) -> Party:
    defaults = {"party_type": Party.PartyType.PERSON, "is_active": True}
    defaults.update(kwargs)
    return Party.objects.create(**defaults)


def make_category(**kwargs) -> PartyCategory:
    defaults = {"name": "Customer", "slug": "customer"}
    defaults.update(kwargs)
    return PartyCategory.objects.create(**defaults)


# ─── create_party ─────────────────────────────────────────────────────────────

class CreatePartyTest(TestCase):
    def test_creates_person_party(self):
        party = create_party(party_type=Party.PartyType.PERSON)
        self.assertEqual(party.party_type, "person")
        self.assertTrue(party.is_active)

    def test_creates_company_party(self):
        party = create_party(party_type=Party.PartyType.ORGANIZATION)
        self.assertEqual(party.party_type, "organization")

    def test_inactive_party(self):
        party = create_party(party_type=Party.PartyType.PERSON, is_active=False)
        self.assertFalse(party.is_active)

    def test_sets_created_by(self):
        user = make_user()
        party = create_party(party_type=Party.PartyType.PERSON, created_by=user)
        self.assertEqual(party.created_by, user)

    def test_created_by_defaults_none(self):
        party = create_party(party_type=Party.PartyType.PERSON)
        self.assertIsNone(party.created_by)


# ─── deactivate_party ────────────────────────────────────────────────────────

class DeactivatePartyTest(TestCase):
    def test_sets_is_active_false(self):
        party = make_party()
        deactivate_party(party_id=party.id)
        party.refresh_from_db()
        self.assertFalse(party.is_active)

    def test_closes_active_relationships_as_member(self):
        party = make_party()
        org = make_party(party_type=Party.PartyType.ORGANIZATION)
        rel = PartyRelationship.objects.create(
            from_party=party, to_party=org, role="contact"
        )
        deactivate_party(party_id=party.id)
        rel.refresh_from_db()
        self.assertFalse(rel.is_active)
        self.assertEqual(rel.ended_on, timezone.now().date())

    def test_deactivates_category_assignments(self):
        party = make_party()
        cat = make_category()
        assignment = PartyCategoryAssignment.objects.create(party=party, category=cat)
        deactivate_party(party_id=party.id)
        assignment.refresh_from_db()
        self.assertFalse(assignment.is_active)

    def test_raises_if_already_inactive(self):
        party = make_party(is_active=False)
        with self.assertRaises(PartyInactiveError):
            deactivate_party(party_id=party.id)

    def test_raises_if_not_found(self):
        with self.assertRaises(PartyNotFoundError):
            deactivate_party(party_id=99999)


# ─── reactivate_party ────────────────────────────────────────────────────────

class ReactivatePartyTest(TestCase):
    def test_reactivates_party(self):
        party = make_party(is_active=False)
        reactivate_party(party_id=party.id)
        party.refresh_from_db()
        self.assertTrue(party.is_active)

    def test_raises_if_already_active(self):
        party = make_party(is_active=True)
        with self.assertRaises(PartyInactiveError):
            reactivate_party(party_id=party.id)

    def test_raises_if_not_found(self):
        with self.assertRaises(PartyNotFoundError):
            reactivate_party(party_id=99999)


# ─── create_party_category ───────────────────────────────────────────────────

class CreatePartyCategoryTest(TestCase):
    def test_creates_with_auto_slug(self):
        cat = create_party_category(name="Supplier Contact")
        self.assertEqual(cat.slug, "supplier-contact")

    def test_is_not_system_by_default(self):
        cat = create_party_category(name="Any Category")
        self.assertFalse(cat.is_system)

    def test_system_flag_can_be_set(self):
        cat = create_party_category(name="System Cat", is_system=True)
        self.assertTrue(cat.is_system)

    def test_raises_on_duplicate_slug(self):
        create_party_category(name="My Category")
        with self.assertRaises(ValueError):
            create_party_category(name="My Category")

    def test_raises_on_duplicate_name_different_case(self):
        create_party_category(name="Premium")
        with self.assertRaises(ValueError):
            create_party_category(name="premium")

    def test_description_stored(self):
        cat = create_party_category(name="VIP", description="Very important")
        self.assertEqual(cat.description, "Very important")

    def test_strips_whitespace_from_name(self):
        cat = create_party_category(name="  Trimmed  ")
        self.assertEqual(cat.name, "Trimmed")


# ─── update_party_category ───────────────────────────────────────────────────

class UpdatePartyCategoryTest(TestCase):
    def test_updates_name_and_regenerates_slug(self):
        cat = make_category(name="Old Name", slug="old-name")
        updated = update_party_category(category_id=cat.id, name="New Name")
        self.assertEqual(updated.name, "New Name")
        self.assertEqual(updated.slug, "new-name")

    def test_updates_description_on_system_category(self):
        cat = make_category(name="System", slug="system", is_system=True)
        updated = update_party_category(
            category_id=cat.id, description="Updated description"
        )
        self.assertEqual(updated.description, "Updated description")

    def test_raises_on_rename_system_category(self):
        cat = make_category(name="System Cat", slug="system-cat", is_system=True)
        with self.assertRaises(CategorySystemProtectedError):
            update_party_category(category_id=cat.id, name="Changed Name")

    def test_raises_if_not_found(self):
        with self.assertRaises(CategoryNotFoundError):
            update_party_category(category_id=99999, name="x")

    def test_raises_on_slug_collision(self):
        make_category(name="Existing", slug="existing")
        cat = make_category(name="Other", slug="other")
        with self.assertRaises(ValueError):
            update_party_category(category_id=cat.id, name="Existing")


# ─── deactivate_party_category ───────────────────────────────────────────────

class DeactivatePartyCategoryTest(TestCase):
    def test_deactivates_category(self):
        cat = make_category()
        deactivate_party_category(category_id=cat.id)
        cat.refresh_from_db()
        self.assertFalse(cat.is_active)

    def test_deactivates_active_assignments(self):
        party = make_party()
        cat = make_category()
        PartyCategoryAssignment.objects.create(party=party, category=cat)
        deactivate_party_category(category_id=cat.id)
        self.assertFalse(
            PartyCategoryAssignment.objects.filter(category=cat, is_active=True).exists()
        )

    def test_is_idempotent(self):
        cat = make_category()
        deactivate_party_category(category_id=cat.id)
        deactivate_party_category(category_id=cat.id)  # should not raise
        cat.refresh_from_db()
        self.assertFalse(cat.is_active)

    def test_raises_for_system_category(self):
        cat = make_category(name="System", slug="system", is_system=True)
        with self.assertRaises(CategorySystemProtectedError):
            deactivate_party_category(category_id=cat.id)

    def test_raises_if_not_found(self):
        with self.assertRaises(CategoryNotFoundError):
            deactivate_party_category(category_id=99999)


# ─── assign_category_to_party ────────────────────────────────────────────────

class AssignCategoryToPartyTest(TestCase):
    def setUp(self):
        self.party = make_party()
        self.category = make_category()

    def test_creates_assignment(self):
        assignment = assign_category_to_party(
            party_id=self.party.id, category_id=self.category.id
        )
        self.assertTrue(assignment.is_active)
        self.assertEqual(assignment.party, self.party)

    def test_raises_on_duplicate_active_assignment(self):
        assign_category_to_party(party_id=self.party.id, category_id=self.category.id)
        with self.assertRaises(DuplicateCategoryAssignmentError):
            assign_category_to_party(party_id=self.party.id, category_id=self.category.id)

    def test_reactivates_inactive_assignment(self):
        a = assign_category_to_party(party_id=self.party.id, category_id=self.category.id)
        a.is_active = False
        a.save()
        reactivated = assign_category_to_party(
            party_id=self.party.id, category_id=self.category.id
        )
        self.assertTrue(reactivated.is_active)
        self.assertEqual(reactivated.id, a.id)

    def test_raises_if_party_not_found(self):
        with self.assertRaises(PartyNotFoundError):
            assign_category_to_party(party_id=99999, category_id=self.category.id)

    def test_raises_if_category_not_found(self):
        with self.assertRaises(CategoryNotFoundError):
            assign_category_to_party(party_id=self.party.id, category_id=99999)

    def test_raises_if_category_inactive(self):
        self.category.is_active = False
        self.category.save()
        with self.assertRaises(CategoryInactiveError):
            assign_category_to_party(party_id=self.party.id, category_id=self.category.id)

    def test_sets_assigned_by(self):
        user = make_user()
        assignment = assign_category_to_party(
            party_id=self.party.id, category_id=self.category.id, assigned_by=user
        )
        self.assertEqual(assignment.assigned_by, user)


# ─── remove_category_from_party ──────────────────────────────────────────────

class RemoveCategoryFromPartyTest(TestCase):
    def setUp(self):
        self.party = make_party()
        self.category = make_category()

    def test_deactivates_active_assignment(self):
        assign_category_to_party(party_id=self.party.id, category_id=self.category.id)
        remove_category_from_party(party_id=self.party.id, category_id=self.category.id)
        self.assertFalse(
            PartyCategoryAssignment.objects.filter(
                party=self.party, category=self.category, is_active=True
            ).exists()
        )

    def test_raises_if_no_active_assignment(self):
        with self.assertRaises(DuplicateCategoryAssignmentError):
            remove_category_from_party(party_id=self.party.id, category_id=self.category.id)


# ─── create_party_address ────────────────────────────────────────────────────

class CreatePartyAddressTest(TestCase):
    def setUp(self):
        self.party = make_party()

    def test_creates_address(self):
        addr = create_party_address(
            party_id=self.party.id,
            label=PartyAddress.Label.HOME,
            line1="1 Main St",
            city="London",
            country="UK",
        )
        self.assertEqual(addr.city, "London")
        self.assertEqual(addr.party, self.party)

    def test_new_default_demotes_existing(self):
        first = create_party_address(
            party_id=self.party.id,
            label=PartyAddress.Label.HOME,
            line1="1 St",
            city="London",
            country="UK",
            is_default=True,
        )
        create_party_address(
            party_id=self.party.id,
            label=PartyAddress.Label.WORK,
            line1="2 St",
            city="Manchester",
            country="UK",
            is_default=True,
        )
        first.refresh_from_db()
        self.assertFalse(first.is_default)

    def test_raises_if_party_not_found(self):
        with self.assertRaises(PartyNotFoundError):
            create_party_address(
                party_id=99999,
                label=PartyAddress.Label.HOME,
                line1="1 St",
                city="City",
                country="UK",
            )


# ─── update_party_address ────────────────────────────────────────────────────

class UpdatePartyAddressTest(TestCase):
    def setUp(self):
        self.party = make_party()
        self.addr = PartyAddress.objects.create(
            party=self.party, line1="1 St", city="London", country="UK"
        )

    def test_updates_city(self):
        updated = update_party_address(
            party_id=self.party.id, address_id=self.addr.id, city="Birmingham"
        )
        self.assertEqual(updated.city, "Birmingham")

    def test_setting_default_demotes_existing(self):
        default_addr = PartyAddress.objects.create(
            party=self.party, line1="D St", city="D", country="UK", is_default=True
        )
        update_party_address(
            party_id=self.party.id, address_id=self.addr.id, is_default=True
        )
        default_addr.refresh_from_db()
        self.assertFalse(default_addr.is_default)

    def test_raises_if_not_found(self):
        with self.assertRaises(AddressNotFoundError):
            update_party_address(
                party_id=self.party.id, address_id=99999, city="x"
            )


# ─── deactivate_party_address ────────────────────────────────────────────────

class DeactivatePartyAddressTest(TestCase):
    def setUp(self):
        self.party = make_party()
        self.addr = PartyAddress.objects.create(
            party=self.party, line1="1 St", city="London", country="UK"
        )

    def test_deactivates_address(self):
        deactivate_party_address(party_id=self.party.id, address_id=self.addr.id)
        self.addr.refresh_from_db()
        self.assertFalse(self.addr.is_active)

    def test_is_idempotent(self):
        deactivate_party_address(party_id=self.party.id, address_id=self.addr.id)
        deactivate_party_address(party_id=self.party.id, address_id=self.addr.id)
        self.addr.refresh_from_db()
        self.assertFalse(self.addr.is_active)

    def test_raises_if_not_found(self):
        with self.assertRaises(AddressNotFoundError):
            deactivate_party_address(party_id=self.party.id, address_id=99999)


# ─── set_default_address ─────────────────────────────────────────────────────

class SetDefaultAddressTest(TestCase):
    def test_sets_default_and_clears_existing(self):
        party = make_party()
        addr1 = PartyAddress.objects.create(
            party=party, line1="1 St", city="A", country="UK", is_default=True
        )
        addr2 = PartyAddress.objects.create(
            party=party, line1="2 St", city="B", country="UK"
        )
        set_default_address(party_id=party.id, address_id=addr2.id)
        addr1.refresh_from_db()
        addr2.refresh_from_db()
        self.assertFalse(addr1.is_default)
        self.assertTrue(addr2.is_default)

    def test_raises_if_not_found(self):
        party = make_party()
        with self.assertRaises(AddressNotFoundError):
            set_default_address(party_id=party.id, address_id=99999)


# ─── create_party_note ───────────────────────────────────────────────────────

class CreatePartyNoteTest(TestCase):
    def test_creates_note(self):
        party = make_party()
        note = create_party_note(party_id=party.id, body="Important note.")
        self.assertEqual(note.body, "Important note.")
        self.assertEqual(note.party, party)

    def test_strips_whitespace(self):
        party = make_party()
        note = create_party_note(party_id=party.id, body="  Padded.  ")
        self.assertEqual(note.body, "Padded.")

    def test_sets_author(self):
        party = make_party()
        user = make_user()
        note = create_party_note(party_id=party.id, body="Note.", author=user)
        self.assertEqual(note.author, user)

    def test_raises_on_empty_body(self):
        party = make_party()
        with self.assertRaises(ValueError):
            create_party_note(party_id=party.id, body="")

    def test_raises_if_party_not_found(self):
        with self.assertRaises(PartyNotFoundError):
            create_party_note(party_id=99999, body="Note.")

    def test_raises_if_party_inactive(self):
        party = make_party(is_active=False)
        with self.assertRaises(PartyNotFoundError):
            create_party_note(party_id=party.id, body="Note.")


# ─── link_parties ────────────────────────────────────────────────────────────

class LinkPartiesTest(TestCase):
    def setUp(self):
        self.from_party = make_party(party_type=Party.PartyType.PERSON)
        self.to_party = make_party(party_type=Party.PartyType.ORGANIZATION)

    def test_creates_relationship(self):
        rel = link_parties(
            from_party_id=self.from_party.id,
            to_party_id=self.to_party.id,
            role="contact",
        )
        self.assertTrue(rel.is_active)
        self.assertEqual(rel.from_party, self.from_party)
        self.assertEqual(rel.to_party, self.to_party)

    def test_raises_on_duplicate(self):
        link_parties(
            from_party_id=self.from_party.id,
            to_party_id=self.to_party.id,
            role="contact",
        )
        with self.assertRaises(RelationshipConflictError):
            link_parties(
                from_party_id=self.from_party.id,
                to_party_id=self.to_party.id,
                role="contact",
            )

    def test_different_role_allowed(self):
        link_parties(
            from_party_id=self.from_party.id,
            to_party_id=self.to_party.id,
            role="contact",
        )
        rel2 = link_parties(
            from_party_id=self.from_party.id,
            to_party_id=self.to_party.id,
            role="billing",
        )
        self.assertTrue(rel2.is_active)

    def test_null_to_party_skips_duplicate_check(self):
        link_parties(
            from_party_id=self.from_party.id,
            to_party_id=None,
            role="pending",
        )
        # Second with same role and null to_party should succeed
        rel2 = link_parties(
            from_party_id=self.from_party.id,
            to_party_id=None,
            role="pending",
        )
        self.assertIsNotNone(rel2.id)

    def test_stores_is_primary(self):
        rel = link_parties(
            from_party_id=self.from_party.id,
            to_party_id=self.to_party.id,
            role="manager",
            is_primary=True,
        )
        self.assertTrue(rel.is_primary)

    def test_stores_started_on(self):
        today = date.today()
        rel = link_parties(
            from_party_id=self.from_party.id,
            to_party_id=self.to_party.id,
            role="rep",
            started_on=today,
        )
        self.assertEqual(rel.started_on, today)

    def test_raises_if_from_party_not_found(self):
        with self.assertRaises(PartyNotFoundError):
            link_parties(from_party_id=99999, to_party_id=self.to_party.id, role="x")


# ─── update_party_relationship ───────────────────────────────────────────────

class UpdatePartyRelationshipTest(TestCase):
    def setUp(self):
        self.from_party = make_party()
        self.to_party = make_party(party_type=Party.PartyType.ORGANIZATION)
        self.rel = PartyRelationship.objects.create(
            from_party=self.from_party,
            to_party=self.to_party,
            role="contact",
        )

    def test_updates_role(self):
        updated = update_party_relationship(
            relationship_id=self.rel.id, role="billing"
        )
        self.assertEqual(updated.role, "billing")

    def test_updates_is_primary(self):
        updated = update_party_relationship(
            relationship_id=self.rel.id, is_primary=True
        )
        self.assertTrue(updated.is_primary)

    def test_raises_if_not_found(self):
        with self.assertRaises(RelationshipNotFoundError):
            update_party_relationship(relationship_id=99999, role="x")


# ─── close_party_relationship ────────────────────────────────────────────────

class ClosePartyRelationshipTest(TestCase):
    def setUp(self):
        self.from_party = make_party()
        self.to_party = make_party(party_type=Party.PartyType.ORGANIZATION)
        self.rel = PartyRelationship.objects.create(
            from_party=self.from_party,
            to_party=self.to_party,
            role="contact",
        )

    def test_closes_relationship(self):
        close_party_relationship(relationship_id=self.rel.id)
        self.rel.refresh_from_db()
        self.assertFalse(self.rel.is_active)

    def test_sets_ended_on(self):
        close_party_relationship(relationship_id=self.rel.id)
        self.rel.refresh_from_db()
        self.assertEqual(self.rel.ended_on, timezone.now().date())

    def test_custom_ended_on(self):
        custom_date = date(2025, 1, 1)
        close_party_relationship(relationship_id=self.rel.id, ended_on=custom_date)
        self.rel.refresh_from_db()
        self.assertEqual(self.rel.ended_on, custom_date)

    def test_is_idempotent(self):
        close_party_relationship(relationship_id=self.rel.id)
        close_party_relationship(relationship_id=self.rel.id)  # must not raise
        self.rel.refresh_from_db()
        self.assertFalse(self.rel.is_active)

    def test_raises_if_not_found(self):
        with self.assertRaises(RelationshipNotFoundError):
            close_party_relationship(relationship_id=99999)
