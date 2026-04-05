"""
test_services.py — service-layer unit tests.

These tests exercise business logic directly, without going through the
HTTP layer, to keep them fast and focused on domain correctness.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from people.exceptions import (
    AddressNotFoundError,
    CategoryInactiveError,
    CategoryNotFoundError,
    CategorySystemProtectedError,
    DuplicateCategoryAssignmentError,
    DuplicatePersonError,
    MergePersonError,
    OrganizationRelationConflictError,
    OrganizationRelationNotFoundError,
    PersonInactiveError,
    PersonNotFoundError,
)
from people.models import (
    OrganizationPersonRelation,
    Person,
    PersonAddress,
    PersonCategory,
    PersonCategoryAssignment,
    PersonNote,
)
from people.services import (
    assign_category,
    close_organization_relationship,
    create_address,
    create_category,
    create_note,
    create_person,
    deactivate_category,
    deactivate_person,
    detect_duplicate_persons,
    link_person_to_organization,
    merge_persons,
    remove_category,
    update_address,
    update_category,
    update_organization_relationship,
    update_person,
)

User = get_user_model()


# ─── Helpers ───────────────────────────────────────────────────────────────────

def make_user(**kwargs) -> User:
    defaults = {"email": "user@test.com", "password": "testpass123"}
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def make_person(**kwargs) -> Person:
    defaults = {"first_name": "Alice", "last_name": "Smith"}
    defaults.update(kwargs)
    return Person.objects.create(**defaults)


def make_category(**kwargs) -> PersonCategory:
    defaults = {"name": "Customer", "slug": "customer"}
    defaults.update(kwargs)
    return PersonCategory.objects.create(**defaults)


# ─── detect_duplicate_persons ─────────────────────────────────────────────────

class DetectDuplicatePersonsTest(TestCase):
    def test_returns_empty_for_no_existing_persons(self):
        result = detect_duplicate_persons(
            first_name="New", last_name="Person"
        )
        self.assertEqual(result, [])

    def test_detects_email_match(self):
        make_person(first_name="Existing", email="match@example.com")
        result = detect_duplicate_persons(
            first_name="Different", last_name="Name", email="match@example.com"
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["reason"], "email_match")

    def test_detects_name_match(self):
        make_person(first_name="Alice", last_name="Smith")
        result = detect_duplicate_persons(first_name="Alice", last_name="Smith")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["reason"], "name_match")

    def test_name_match_is_case_insensitive(self):
        make_person(first_name="Alice", last_name="Smith")
        result = detect_duplicate_persons(first_name="alice", last_name="SMITH")
        self.assertEqual(len(result), 1)

    def test_detects_phone_match(self):
        make_person(first_name="Bob", last_name="Jones", phone="01234567890")
        result = detect_duplicate_persons(
            first_name="Different", last_name="Name", phone="01234567890"
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["reason"], "phone_match")

    def test_same_person_via_multiple_signals_not_duplicated(self):
        make_person(
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            phone="01234567890",
        )
        result = detect_duplicate_persons(
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            phone="01234567890",
        )
        self.assertEqual(len(result), 1)

    def test_ignores_inactive_persons(self):
        make_person(first_name="Alice", last_name="Smith", is_active=False)
        result = detect_duplicate_persons(first_name="Alice", last_name="Smith")
        self.assertEqual(result, [])

    def test_returns_empty_when_name_missing(self):
        result = detect_duplicate_persons(first_name="", last_name="")
        self.assertEqual(result, [])


# ─── create_person ─────────────────────────────────────────────────────────────

class CreatePersonTest(TestCase):
    def test_creates_successfully(self):
        person = create_person(data={"first_name": "Alice", "last_name": "Smith"})
        self.assertEqual(person.full_name, "Alice Smith")
        self.assertTrue(person.is_active)

    def test_sets_created_by(self):
        user = make_user()
        person = create_person(
            data={"first_name": "Bob", "last_name": "Jones", "force": True},
            created_by=user,
        )
        self.assertEqual(person.created_by, user)

    def test_email_stored_as_none_when_blank(self):
        person = create_person(
            data={"first_name": "Test", "last_name": "User", "email": ""}
        )
        self.assertIsNone(person.email)

    def test_raises_on_name_duplicate(self):
        make_person(first_name="Alice", last_name="Smith")
        with self.assertRaises(DuplicatePersonError) as ctx:
            create_person(data={"first_name": "Alice", "last_name": "Smith"})
        self.assertEqual(len(ctx.exception.candidates), 1)

    def test_raises_on_email_duplicate(self):
        make_person(first_name="Alice", last_name="Smith", email="alice@example.com")
        with self.assertRaises(DuplicatePersonError):
            create_person(
                data={
                    "first_name": "Other",
                    "last_name": "Person",
                    "email": "alice@example.com",
                }
            )

    def test_force_bypasses_duplicate_check(self):
        make_person(first_name="Alice", last_name="Smith")
        person = create_person(
            data={"first_name": "Alice", "last_name": "Smith", "force": True}
        )
        self.assertEqual(person.full_name, "Alice Smith")

    def test_force_consumed_and_not_stored(self):
        # 'force' is a transient flag, not a model field
        person = create_person(
            data={"first_name": "Test", "last_name": "User", "force": True}
        )
        self.assertFalse(hasattr(person, "force"))


# ─── update_person ─────────────────────────────────────────────────────────────

class UpdatePersonTest(TestCase):
    def setUp(self):
        self.person = make_person(first_name="Alice", last_name="Smith")

    def test_updates_first_name(self):
        updated = update_person(
            person_id=self.person.id, data={"first_name": "Alicia", "force": True}
        )
        self.assertEqual(updated.first_name, "Alicia")

    def test_updates_email_to_none_when_blank(self):
        self.person.email = "old@example.com"
        self.person.save()
        updated = update_person(
            person_id=self.person.id, data={"email": "", "force": True}
        )
        self.assertIsNone(updated.email)

    def test_raises_if_person_not_found(self):
        with self.assertRaises(PersonNotFoundError):
            update_person(person_id=99999, data={"first_name": "x", "force": True})

    def test_raises_if_person_inactive(self):
        self.person.is_active = False
        self.person.save()
        with self.assertRaises(PersonInactiveError):
            update_person(
                person_id=self.person.id, data={"first_name": "x", "force": True}
            )

    def test_duplicate_check_excludes_self(self):
        # Updating a person with its own name/email should not raise
        self.person.email = "alice@example.com"
        self.person.save()
        updated = update_person(
            person_id=self.person.id,
            data={"first_name": "Alice", "last_name": "Smith", "email": "alice@example.com"},
        )
        self.assertEqual(updated.first_name, "Alice")

    def test_raises_on_duplicate_with_other_person(self):
        make_person(
            first_name="Bob", last_name="Jones", email="bob@example.com"
        )
        with self.assertRaises(DuplicatePersonError):
            update_person(
                person_id=self.person.id,
                data={"email": "bob@example.com"},
            )


# ─── deactivate_person ─────────────────────────────────────────────────────────

class DeactivatePersonTest(TestCase):
    def setUp(self):
        self.person = make_person()

    def test_sets_is_active_false(self):
        deactivate_person(person_id=self.person.id)
        self.person.refresh_from_db()
        self.assertFalse(self.person.is_active)

    def test_closes_active_org_relations(self):
        OrganizationPersonRelation.objects.create(
            person=self.person,
            organization_id=1,
            organization_type="customer",
            role="contact",
        )
        deactivate_person(person_id=self.person.id)
        self.assertFalse(
            OrganizationPersonRelation.objects.filter(
                person=self.person, is_active=True
            ).exists()
        )

    def test_closed_org_relation_gets_ended_on(self):
        OrganizationPersonRelation.objects.create(
            person=self.person,
            organization_id=1,
            organization_type="customer",
            role="contact",
        )
        deactivate_person(person_id=self.person.id)
        rel = OrganizationPersonRelation.objects.get(person=self.person)
        self.assertIsNotNone(rel.ended_on)
        self.assertEqual(rel.ended_on, timezone.now().date())

    def test_deactivates_active_category_assignments(self):
        cat = make_category()
        PersonCategoryAssignment.objects.create(person=self.person, category=cat)
        deactivate_person(person_id=self.person.id)
        self.assertFalse(
            PersonCategoryAssignment.objects.filter(
                person=self.person, is_active=True
            ).exists()
        )

    def test_raises_if_not_found(self):
        with self.assertRaises(PersonNotFoundError):
            deactivate_person(person_id=99999)

    def test_raises_if_already_inactive(self):
        self.person.is_active = False
        self.person.save()
        with self.assertRaises(PersonInactiveError):
            deactivate_person(person_id=self.person.id)

    def test_does_not_affect_already_closed_org_relations(self):
        rel = OrganizationPersonRelation.objects.create(
            person=self.person,
            organization_id=1,
            organization_type="customer",
            role="contact",
            is_active=False,
            ended_on=timezone.now().date(),
        )
        deactivate_person(person_id=self.person.id)
        rel.refresh_from_db()
        # Should be unchanged
        self.assertFalse(rel.is_active)


# ─── merge_persons ─────────────────────────────────────────────────────────────

class MergePersonPlaceholderTest(TestCase):
    def test_raises_merge_not_implemented(self):
        with self.assertRaises(MergePersonError) as ctx:
            merge_persons(source_id=1, target_id=2)
        self.assertIn("not yet implemented", str(ctx.exception))
        self.assertIn("source_id=1", str(ctx.exception))
        self.assertIn("target_id=2", str(ctx.exception))


# ─── create_category ───────────────────────────────────────────────────────────

class CreateCategoryTest(TestCase):
    def test_creates_with_auto_slug(self):
        cat = create_category(data={"name": "Supplier Contact"})
        self.assertEqual(cat.slug, "supplier-contact")

    def test_is_not_system(self):
        cat = create_category(data={"name": "Any Category"})
        self.assertFalse(cat.is_system)

    def test_raises_on_duplicate_slug(self):
        create_category(data={"name": "My Category"})
        with self.assertRaises(ValueError):
            create_category(data={"name": "My Category"})

    def test_raises_on_duplicate_name_different_case(self):
        create_category(data={"name": "Premium"})
        with self.assertRaises(ValueError):
            create_category(data={"name": "premium"})

    def test_description_stored(self):
        cat = create_category(data={"name": "VIP", "description": "Very important"})
        self.assertEqual(cat.description, "Very important")


# ─── update_category ───────────────────────────────────────────────────────────

class UpdateCategoryTest(TestCase):
    def test_updates_name_and_regenerates_slug(self):
        cat = make_category(name="Old Name", slug="old-name")
        updated = update_category(category_id=cat.id, data={"name": "New Name"})
        self.assertEqual(updated.name, "New Name")
        self.assertEqual(updated.slug, "new-name")

    def test_updates_description_on_system_category(self):
        cat = make_category(name="System", slug="system", is_system=True)
        updated = update_category(
            category_id=cat.id, data={"description": "Updated description"}
        )
        self.assertEqual(updated.description, "Updated description")

    def test_raises_on_rename_system_category(self):
        cat = make_category(name="System Cat", slug="system-cat", is_system=True)
        with self.assertRaises(CategorySystemProtectedError):
            update_category(category_id=cat.id, data={"name": "Changed Name"})

    def test_raises_if_not_found(self):
        with self.assertRaises(CategoryNotFoundError):
            update_category(category_id=99999, data={"name": "x"})

    def test_raises_on_slug_collision(self):
        make_category(name="Existing", slug="existing")
        cat = make_category(name="Other", slug="other")
        with self.assertRaises(ValueError):
            update_category(category_id=cat.id, data={"name": "Existing"})


# ─── deactivate_category ───────────────────────────────────────────────────────

class DeactivateCategoryTest(TestCase):
    def test_deactivates_category(self):
        cat = make_category()
        deactivate_category(category_id=cat.id)
        cat.refresh_from_db()
        self.assertFalse(cat.is_active)

    def test_deactivates_active_assignments(self):
        person = make_person()
        cat = make_category()
        PersonCategoryAssignment.objects.create(person=person, category=cat)
        deactivate_category(category_id=cat.id)
        self.assertFalse(
            PersonCategoryAssignment.objects.filter(
                category=cat, is_active=True
            ).exists()
        )

    def test_is_idempotent(self):
        cat = make_category()
        deactivate_category(category_id=cat.id)
        deactivate_category(category_id=cat.id)  # should not raise
        cat.refresh_from_db()
        self.assertFalse(cat.is_active)

    def test_raises_for_system_category(self):
        cat = make_category(name="System", slug="system", is_system=True)
        with self.assertRaises(CategorySystemProtectedError):
            deactivate_category(category_id=cat.id)

    def test_raises_if_not_found(self):
        with self.assertRaises(CategoryNotFoundError):
            deactivate_category(category_id=99999)


# ─── assign_category ───────────────────────────────────────────────────────────

class AssignCategoryTest(TestCase):
    def setUp(self):
        self.person = make_person()
        self.category = make_category()

    def test_creates_assignment(self):
        assignment = assign_category(
            person_id=self.person.id, category_id=self.category.id
        )
        self.assertTrue(assignment.is_active)
        self.assertEqual(assignment.person, self.person)
        self.assertEqual(assignment.category, self.category)

    def test_raises_on_duplicate_active_assignment(self):
        assign_category(person_id=self.person.id, category_id=self.category.id)
        with self.assertRaises(DuplicateCategoryAssignmentError):
            assign_category(person_id=self.person.id, category_id=self.category.id)

    def test_reactivates_previously_removed_assignment(self):
        assignment = assign_category(
            person_id=self.person.id, category_id=self.category.id
        )
        assignment.is_active = False
        assignment.save()

        reactivated = assign_category(
            person_id=self.person.id, category_id=self.category.id
        )
        self.assertTrue(reactivated.is_active)
        # Should be same DB row, not a new one
        self.assertEqual(reactivated.id, assignment.id)

    def test_raises_if_person_not_found(self):
        with self.assertRaises(PersonNotFoundError):
            assign_category(person_id=99999, category_id=self.category.id)

    def test_raises_if_person_inactive(self):
        self.person.is_active = False
        self.person.save()
        with self.assertRaises(PersonNotFoundError):
            assign_category(person_id=self.person.id, category_id=self.category.id)

    def test_raises_if_category_not_found(self):
        with self.assertRaises(CategoryNotFoundError):
            assign_category(person_id=self.person.id, category_id=99999)

    def test_raises_if_category_inactive(self):
        self.category.is_active = False
        self.category.save()
        with self.assertRaises(CategoryInactiveError):
            assign_category(person_id=self.person.id, category_id=self.category.id)

    def test_sets_assigned_by(self):
        user = make_user()
        assignment = assign_category(
            person_id=self.person.id,
            category_id=self.category.id,
            assigned_by=user,
        )
        self.assertEqual(assignment.assigned_by, user)


# ─── remove_category ───────────────────────────────────────────────────────────

class RemoveCategoryTest(TestCase):
    def setUp(self):
        self.person = make_person()
        self.category = make_category()

    def test_deactivates_assignment(self):
        assign_category(person_id=self.person.id, category_id=self.category.id)
        remove_category(person_id=self.person.id, category_id=self.category.id)
        self.assertFalse(
            PersonCategoryAssignment.objects.filter(
                person=self.person,
                category=self.category,
                is_active=True,
            ).exists()
        )

    def test_raises_if_no_active_assignment(self):
        with self.assertRaises(DuplicateCategoryAssignmentError):
            remove_category(person_id=self.person.id, category_id=self.category.id)


# ─── create_address ────────────────────────────────────────────────────────────

class CreateAddressTest(TestCase):
    def setUp(self):
        self.person = make_person()

    def test_creates_address(self):
        addr = create_address(
            person_id=self.person.id,
            data={"line1": "1 Main St", "city": "London", "country": "UK"},
        )
        self.assertEqual(addr.city, "London")
        self.assertEqual(addr.person, self.person)

    def test_new_default_demotes_existing_default(self):
        first = create_address(
            person_id=self.person.id,
            data={"line1": "1 St", "city": "London", "country": "UK", "is_default": True},
        )
        self.assertTrue(first.is_default)

        create_address(
            person_id=self.person.id,
            data={"line1": "2 St", "city": "Manchester", "country": "UK", "is_default": True},
        )
        first.refresh_from_db()
        self.assertFalse(first.is_default)

    def test_raises_if_person_not_found(self):
        with self.assertRaises(PersonNotFoundError):
            create_address(
                person_id=99999,
                data={"line1": "1 St", "city": "City", "country": "UK"},
            )


# ─── update_address ────────────────────────────────────────────────────────────

class UpdateAddressTest(TestCase):
    def setUp(self):
        self.person = make_person()
        self.address = PersonAddress.objects.create(
            person=self.person, line1="1 St", city="London", country="UK"
        )

    def test_updates_city(self):
        updated = update_address(
            person_id=self.person.id,
            address_id=self.address.id,
            data={"city": "Birmingham"},
        )
        self.assertEqual(updated.city, "Birmingham")

    def test_setting_default_demotes_existing(self):
        existing_default = PersonAddress.objects.create(
            person=self.person,
            line1="Default St",
            city="City",
            country="UK",
            is_default=True,
        )
        update_address(
            person_id=self.person.id,
            address_id=self.address.id,
            data={"is_default": True},
        )
        existing_default.refresh_from_db()
        self.assertFalse(existing_default.is_default)

    def test_raises_if_not_found(self):
        with self.assertRaises(AddressNotFoundError):
            update_address(
                person_id=self.person.id,
                address_id=99999,
                data={"city": "x"},
            )


# ─── create_note ───────────────────────────────────────────────────────────────

class CreateNoteTest(TestCase):
    def setUp(self):
        self.person = make_person()

    def test_creates_note(self):
        note = create_note(person_id=self.person.id, body="Important note.")
        self.assertEqual(note.body, "Important note.")
        self.assertEqual(note.person, self.person)

    def test_strips_whitespace(self):
        note = create_note(person_id=self.person.id, body="  Note with spaces.  ")
        self.assertEqual(note.body, "Note with spaces.")

    def test_sets_author(self):
        user = make_user()
        note = create_note(person_id=self.person.id, body="Note.", author=user)
        self.assertEqual(note.author, user)

    def test_raises_on_empty_body(self):
        with self.assertRaises(ValueError):
            create_note(person_id=self.person.id, body="")

    def test_raises_on_whitespace_only_body(self):
        with self.assertRaises(ValueError):
            create_note(person_id=self.person.id, body="   ")

    def test_raises_if_person_not_found(self):
        with self.assertRaises(PersonNotFoundError):
            create_note(person_id=99999, body="Note.")


# ─── link_person_to_organization ──────────────────────────────────────────────

class LinkPersonToOrganizationTest(TestCase):
    def setUp(self):
        self.person = make_person()
        self.org_data = {
            "person_id": None,  # set per-test
            "organization_id": 1,
            "organization_type": "customer",
            "role": "contact",
        }

    def _link(self, **overrides):
        data = {**self.org_data, "person_id": self.person.id}
        data.update(overrides)
        return link_person_to_organization(data=data)

    def test_creates_relation(self):
        rel = self._link()
        self.assertTrue(rel.is_active)
        self.assertEqual(rel.person, self.person)

    def test_raises_on_duplicate_active_relation(self):
        self._link()
        with self.assertRaises(OrganizationRelationConflictError):
            self._link()

    def test_different_role_is_allowed(self):
        self._link(role="contact")
        rel2 = self._link(role="billing")
        self.assertTrue(rel2.is_active)

    def test_different_org_type_is_allowed(self):
        self._link(organization_type="customer")
        rel2 = self._link(organization_type="supplier")
        self.assertTrue(rel2.is_active)

    def test_raises_if_person_not_found(self):
        with self.assertRaises(PersonNotFoundError):
            link_person_to_organization(
                data={**self.org_data, "person_id": 99999}
            )


# ─── close_organization_relationship ──────────────────────────────────────────

class CloseOrganizationRelationshipTest(TestCase):
    def setUp(self):
        self.person = make_person()
        self.rel = OrganizationPersonRelation.objects.create(
            person=self.person,
            organization_id=1,
            organization_type="customer",
            role="contact",
        )

    def test_closes_relation(self):
        close_organization_relationship(relation_id=self.rel.id)
        self.rel.refresh_from_db()
        self.assertFalse(self.rel.is_active)

    def test_sets_ended_on_to_today(self):
        close_organization_relationship(relation_id=self.rel.id)
        self.rel.refresh_from_db()
        self.assertEqual(self.rel.ended_on, timezone.now().date())

    def test_is_idempotent(self):
        close_organization_relationship(relation_id=self.rel.id)
        close_organization_relationship(relation_id=self.rel.id)  # must not raise
        self.rel.refresh_from_db()
        self.assertFalse(self.rel.is_active)

    def test_raises_if_not_found(self):
        with self.assertRaises(OrganizationRelationNotFoundError):
            close_organization_relationship(relation_id=99999)


# ─── update_organization_relationship ─────────────────────────────────────────

class UpdateOrganizationRelationshipTest(TestCase):
    def setUp(self):
        self.person = make_person()
        self.rel = OrganizationPersonRelation.objects.create(
            person=self.person,
            organization_id=1,
            organization_type="customer",
            role="contact",
        )

    def test_updates_role(self):
        updated = update_organization_relationship(
            relation_id=self.rel.id, data={"role": "billing"}
        )
        self.assertEqual(updated.role, "billing")

    def test_updates_is_primary(self):
        updated = update_organization_relationship(
            relation_id=self.rel.id, data={"is_primary": True}
        )
        self.assertTrue(updated.is_primary)

    def test_raises_if_not_found(self):
        with self.assertRaises(OrganizationRelationNotFoundError):
            update_organization_relationship(relation_id=99999, data={"role": "x"})


# ─── Additional edge-case coverage ────────────────────────────────────────────

class DetectDuplicatePersonsMobileTest(TestCase):
    """Mobile phone field is a separate column from phone."""

    def test_detects_mobile_match(self):
        make_person(first_name="Carol", last_name="Lee", mobile="07700900123")
        result = detect_duplicate_persons(
            first_name="Different", last_name="Person", phone="07700900123"
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["reason"], "phone_match")

    def test_detects_phone_field_match_via_phone_param(self):
        # phone stored in phone column is matched when same value is passed as phone param
        make_person(first_name="Dan", last_name="Brown", phone="01111222233")
        result = detect_duplicate_persons(
            first_name="Different", last_name="Name", phone="01111222233"
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["reason"], "phone_match")

    def test_returns_empty_for_blank_phone_and_no_other_match(self):
        make_person(first_name="Dan", last_name="Brown", phone="01234567890")
        result = detect_duplicate_persons(
            first_name="Different", last_name="Name", phone=""
        )
        self.assertEqual(result, [])


class CreatePersonEdgeCaseTest(TestCase):
    def test_strips_whitespace_from_first_and_last_name(self):
        person = create_person(
            data={"first_name": "  Alice  ", "last_name": "  Smith  "}
        )
        self.assertEqual(person.first_name, "Alice")
        self.assertEqual(person.last_name, "Smith")

    def test_stores_optional_fields(self):
        person = create_person(
            data={
                "first_name": "Bob",
                "last_name": "Jones",
                "phone": "01234567890",
                "mobile": "07700900000",
                "gender": "male",
                "preferred_name": "Bobby",
            }
        )
        self.assertEqual(person.phone, "01234567890")
        self.assertEqual(person.mobile, "07700900000")
        self.assertEqual(person.gender, "male")
        self.assertEqual(person.preferred_name, "Bobby")


class UpdatePersonEdgeCaseTest(TestCase):
    def setUp(self):
        self.person = make_person(
            first_name="Alice",
            last_name="Smith",
            phone="01111111111",
        )

    def test_updates_phone(self):
        updated = update_person(
            person_id=self.person.id, data={"phone": "02222222222", "force": True}
        )
        self.assertEqual(updated.phone, "02222222222")

    def test_updates_gender(self):
        updated = update_person(
            person_id=self.person.id, data={"gender": "female", "force": True}
        )
        self.assertEqual(updated.gender, "female")

    def test_partial_update_preserves_untouched_fields(self):
        original_last = self.person.last_name
        update_person(
            person_id=self.person.id, data={"first_name": "Alicia", "force": True}
        )
        self.person.refresh_from_db()
        self.assertEqual(self.person.last_name, original_last)


class CreateAddressEdgeCaseTest(TestCase):
    def test_raises_if_person_inactive(self):
        person = make_person(is_active=False)
        with self.assertRaises(PersonNotFoundError):
            create_address(
                person_id=person.id,
                data={"line1": "1 St", "city": "London", "country": "UK"},
            )

    def test_default_label_is_home(self):
        person = make_person()
        addr = create_address(
            person_id=person.id,
            data={"line1": "1 St", "city": "London", "country": "UK"},
        )
        from people.models import PersonAddress
        self.assertEqual(addr.label, PersonAddress.Label.HOME)

    def test_non_default_address_does_not_affect_existing_default(self):
        person = make_person()
        first = create_address(
            person_id=person.id,
            data={"line1": "1 St", "city": "London", "country": "UK", "is_default": True},
        )
        create_address(
            person_id=person.id,
            data={"line1": "2 St", "city": "Birmingham", "country": "UK", "is_default": False},
        )
        first.refresh_from_db()
        self.assertTrue(first.is_default)


class UpdateAddressEdgeCaseTest(TestCase):
    def setUp(self):
        self.person = make_person()
        from people.models import PersonAddress
        self.addr = PersonAddress.objects.create(
            person=self.person, line1="1 St", city="London", country="UK", is_default=True
        )

    def test_setting_already_default_does_not_raise(self):
        # Updating is_default=True on an address already default is a no-op demotion
        from people.models import PersonAddress
        updated = update_address(
            person_id=self.person.id,
            address_id=self.addr.id,
            data={"is_default": True},
        )
        self.assertTrue(updated.is_default)

    def test_raises_if_address_belongs_to_different_person(self):
        other_person = make_person(first_name="Other", last_name="Person", email="o@test.com")
        with self.assertRaises(AddressNotFoundError):
            update_address(
                person_id=other_person.id,
                address_id=self.addr.id,
                data={"city": "Manchester"},
            )


class CreateNoteEdgeCaseTest(TestCase):
    def test_raises_if_person_inactive(self):
        person = make_person(is_active=False)
        with self.assertRaises(PersonNotFoundError):
            create_note(person_id=person.id, body="Some note.")


class LinkOrganizationEdgeCaseTest(TestCase):
    def test_raises_if_person_inactive(self):
        person = make_person(is_active=False)
        with self.assertRaises(PersonNotFoundError):
            link_person_to_organization(
                data={
                    "person_id": person.id,
                    "organization_id": 1,
                    "organization_type": "customer",
                    "role": "contact",
                }
            )

    def test_stores_started_on(self):
        from datetime import date
        person = make_person()
        today = date.today()
        rel = link_person_to_organization(
            data={
                "person_id": person.id,
                "organization_id": 5,
                "organization_type": "supplier",
                "role": "rep",
                "started_on": today,
            }
        )
        self.assertEqual(rel.started_on, today)

    def test_stores_is_primary(self):
        person = make_person()
        rel = link_person_to_organization(
            data={
                "person_id": person.id,
                "organization_id": 7,
                "organization_type": "partner",
                "role": "manager",
                "is_primary": True,
            }
        )
        self.assertTrue(rel.is_primary)


class AssignCategoryEdgeCaseTest(TestCase):
    def test_reactivated_assignment_updates_assigned_by(self):
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        person = make_person()
        category = make_category()
        first_user = UserModel.objects.create_user(email="first@test.com", password="pass1234!")
        second_user = UserModel.objects.create_user(email="second@test.com", password="pass1234!")

        assignment = assign_category(
            person_id=person.id, category_id=category.id, assigned_by=first_user
        )
        assignment.is_active = False
        assignment.save()

        reactivated = assign_category(
            person_id=person.id, category_id=category.id, assigned_by=second_user
        )
        self.assertEqual(reactivated.assigned_by, second_user)
