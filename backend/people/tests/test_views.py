"""
test_views.py — HTTP / API layer tests.

These tests verify that views correctly delegate to services and selectors,
return the right status codes, and respond with the expected response shapes.
Business logic correctness is tested in test_services.py.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from people.models import (
    OrganizationPersonRelation,
    Person,
    PersonAddress,
    PersonCategory,
    PersonCategoryAssignment,
    PersonNote,
)

User = get_user_model()


# ─── Helpers ───────────────────────────────────────────────────────────────────

def make_admin(**kwargs) -> User:
    defaults = {
        "email": "admin@test.com",
        "password": "testpass123",
        "is_staff": True,
        "is_superuser": True,
    }
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


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


# ─── Person List + Create ──────────────────────────────────────────────────────

class PersonListCreateViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)

    def test_list_returns_200_empty(self):
        response = self.client.get("/api/people/persons/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 0)
        self.assertEqual(response.data["results"], [])

    def test_list_returns_paginated_persons(self):
        make_person()
        response = self.client.get("/api/people/persons/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertIn("full_name", response.data["results"][0])

    def test_list_search_param(self):
        make_person(first_name="Alice", last_name="Smith")
        make_person(first_name="Bob", last_name="Jones", email="b@test.com")
        response = self.client.get("/api/people/persons/?search=alice")
        self.assertEqual(response.data["count"], 1)

    def test_list_excludes_inactive_by_default(self):
        make_person(is_active=False)
        response = self.client.get("/api/people/persons/")
        self.assertEqual(response.data["count"], 0)

    def test_list_includes_inactive_when_param(self):
        make_person(is_active=False)
        response = self.client.get("/api/people/persons/?is_active=false")
        self.assertEqual(response.data["count"], 1)

    def test_create_returns_201(self):
        response = self.client.post(
            "/api/people/persons/",
            {"first_name": "John", "last_name": "Doe", "force": True},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["first_name"], "John")

    def test_create_returns_detail_shape(self):
        response = self.client.post(
            "/api/people/persons/",
            {"first_name": "John", "last_name": "Doe", "force": True},
            format="json",
        )
        self.assertIn("addresses", response.data)
        self.assertIn("category_assignments", response.data)
        self.assertIn("org_relations", response.data)

    def test_create_duplicate_returns_409(self):
        make_person(first_name="John", last_name="Doe")
        response = self.client.post(
            "/api/people/persons/",
            {"first_name": "John", "last_name": "Doe"},
            format="json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "duplicate_detected")
        self.assertIn("candidates", response.data)

    def test_create_with_force_bypasses_duplicate(self):
        make_person(first_name="John", last_name="Doe")
        response = self.client.post(
            "/api/people/persons/",
            {"first_name": "John", "last_name": "Doe", "force": True},
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_create_missing_required_fields_returns_400(self):
        response = self.client.post(
            "/api/people/persons/", {"first_name": "Only"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_requires_authentication(self):
        client = APIClient()
        response = client.get("/api/people/persons/")
        self.assertEqual(response.status_code, 401)

    def test_invalid_page_size_returns_400(self):
        response = self.client.get("/api/people/persons/?page_size=notanumber")
        self.assertEqual(response.status_code, 400)


# ─── Person Detail + Update ────────────────────────────────────────────────────

class PersonDetailUpdateViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)
        self.person = make_person()

    def test_get_returns_200(self):
        response = self.client.get(f"/api/people/persons/{self.person.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], self.person.id)

    def test_get_not_found_returns_404(self):
        response = self.client.get("/api/people/persons/99999/")
        self.assertEqual(response.status_code, 404)

    def test_patch_returns_200(self):
        response = self.client.patch(
            f"/api/people/persons/{self.person.id}/",
            {"preferred_name": "Ali", "force": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["preferred_name"], "Ali")

    def test_patch_inactive_person_returns_409(self):
        self.person.is_active = False
        self.person.save()
        response = self.client.patch(
            f"/api/people/persons/{self.person.id}/",
            {"first_name": "x", "force": True},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_patch_duplicate_detected_returns_409(self):
        make_person(
            first_name="Bob",
            last_name="Jones",
            email="bob@example.com",
        )
        response = self.client.patch(
            f"/api/people/persons/{self.person.id}/",
            {"email": "bob@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "duplicate_detected")


# ─── Person Deactivate ─────────────────────────────────────────────────────────

class PersonDeactivateViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)
        self.person = make_person()

    def test_deactivate_returns_200(self):
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/deactivate/"
        )
        self.assertEqual(response.status_code, 200)
        self.person.refresh_from_db()
        self.assertFalse(self.person.is_active)

    def test_deactivate_not_found_returns_404(self):
        response = self.client.post("/api/people/persons/99999/deactivate/")
        self.assertEqual(response.status_code, 404)

    def test_deactivate_already_inactive_returns_409(self):
        self.person.is_active = False
        self.person.save()
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/deactivate/"
        )
        self.assertEqual(response.status_code, 409)


# ─── Duplicate Check ───────────────────────────────────────────────────────────

class DuplicateCheckViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)

    def test_no_duplicates_returns_false(self):
        response = self.client.post(
            "/api/people/persons/duplicate-check/",
            {"first_name": "Unique", "last_name": "Person"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["has_duplicates"])
        self.assertEqual(response.data["candidates"], [])

    def test_with_name_duplicate_returns_true(self):
        make_person(first_name="John", last_name="Smith")
        response = self.client.post(
            "/api/people/persons/duplicate-check/",
            {"first_name": "John", "last_name": "Smith"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["has_duplicates"])
        self.assertEqual(len(response.data["candidates"]), 1)
        self.assertEqual(response.data["candidates"][0]["reason"], "name_match")

    def test_missing_required_fields_returns_400(self):
        response = self.client.post(
            "/api/people/persons/duplicate-check/",
            {"first_name": "Only"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


# ─── Merge (placeholder) ───────────────────────────────────────────────────────

class MergePersonViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        self.person = make_person()

    def test_merge_returns_501(self):
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/merge/",
            {"target_id": 2},
            format="json",
        )
        self.assertEqual(response.status_code, 501)
        self.assertEqual(response.data["code"], "merge_not_implemented")

    def test_merge_missing_target_returns_400(self):
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/merge/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_merge_requires_admin(self):
        user = make_user(email="regular@test.com")
        self.client.force_authenticate(user=user)
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/merge/",
            {"target_id": 2},
            format="json",
        )
        self.assertEqual(response.status_code, 403)


# ─── Category Views ────────────────────────────────────────────────────────────

class CategoryViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.user = make_user(email="regular@test.com")

    def test_list_categories_authenticated(self):
        self.client.force_authenticate(user=self.user)
        make_category()
        response = self.client.get("/api/people/categories/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_list_categories_unauthenticated_returns_401(self):
        response = self.client.get("/api/people/categories/")
        self.assertEqual(response.status_code, 401)

    def test_list_filter_active(self):
        self.client.force_authenticate(user=self.user)
        make_category(name="Active", slug="active")
        make_category(name="Inactive", slug="inactive", is_active=False)
        response = self.client.get("/api/people/categories/?is_active=true")
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Active")

    def test_create_category_admin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(
            "/api/people/categories/create/",
            {"name": "New Category"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["name"], "New Category")
        self.assertEqual(response.data["slug"], "new-category")
        self.assertFalse(response.data["is_system"])

    def test_create_category_non_admin_returns_403(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/people/categories/create/",
            {"name": "New"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_create_duplicate_category_returns_409(self):
        self.client.force_authenticate(user=self.admin)
        self.client.post(
            "/api/people/categories/create/", {"name": "Dup"}, format="json"
        )
        response = self.client.post(
            "/api/people/categories/create/", {"name": "Dup"}, format="json"
        )
        self.assertEqual(response.status_code, 409)

    def test_update_category_admin(self):
        self.client.force_authenticate(user=self.admin)
        cat = make_category()
        response = self.client.patch(
            f"/api/people/categories/{cat.id}/",
            {"description": "Updated desc"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["description"], "Updated desc")

    def test_update_system_category_name_returns_409(self):
        self.client.force_authenticate(user=self.admin)
        cat = make_category(name="System Cat", slug="system-cat", is_system=True)
        response = self.client.patch(
            f"/api/people/categories/{cat.id}/",
            {"name": "Changed"},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_deactivate_category_admin(self):
        self.client.force_authenticate(user=self.admin)
        cat = make_category()
        response = self.client.post(f"/api/people/categories/{cat.id}/deactivate/")
        self.assertEqual(response.status_code, 200)
        cat.refresh_from_db()
        self.assertFalse(cat.is_active)

    def test_deactivate_system_category_returns_409(self):
        self.client.force_authenticate(user=self.admin)
        cat = make_category(name="Sys", slug="sys", is_system=True)
        response = self.client.post(f"/api/people/categories/{cat.id}/deactivate/")
        self.assertEqual(response.status_code, 409)

    def test_deactivate_category_not_found_returns_404(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post("/api/people/categories/99999/deactivate/")
        self.assertEqual(response.status_code, 404)


# ─── Person → Category Assignment Views ───────────────────────────────────────

class PersonCategoryAssignmentViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)
        self.person = make_person()
        self.category = make_category()

    def test_list_assignments_returns_200(self):
        response = self.client.get(
            f"/api/people/persons/{self.person.id}/categories/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_assign_category_returns_201(self):
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/categories/",
            {"category_id": self.category.id},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["is_active"])

    def test_duplicate_assign_returns_409(self):
        self.client.post(
            f"/api/people/persons/{self.person.id}/categories/",
            {"category_id": self.category.id},
            format="json",
        )
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/categories/",
            {"category_id": self.category.id},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_assign_inactive_category_returns_404(self):
        self.category.is_active = False
        self.category.save()
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/categories/",
            {"category_id": self.category.id},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_remove_category_returns_204(self):
        PersonCategoryAssignment.objects.create(
            person=self.person, category=self.category
        )
        response = self.client.delete(
            f"/api/people/persons/{self.person.id}/categories/{self.category.id}/"
        )
        self.assertEqual(response.status_code, 204)

    def test_remove_non_existent_assignment_returns_404(self):
        response = self.client.delete(
            f"/api/people/persons/{self.person.id}/categories/{self.category.id}/"
        )
        self.assertEqual(response.status_code, 404)


# ─── Person → Address Views ────────────────────────────────────────────────────

class PersonAddressViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)
        self.person = make_person()

    def test_list_addresses_returns_200(self):
        response = self.client.get(
            f"/api/people/persons/{self.person.id}/addresses/"
        )
        self.assertEqual(response.status_code, 200)

    def test_create_address_returns_201(self):
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/addresses/",
            {"line1": "1 Main St", "city": "London", "country": "UK"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["city"], "London")

    def test_create_address_person_not_found_returns_404(self):
        response = self.client.post(
            "/api/people/persons/99999/addresses/",
            {"line1": "1 St", "city": "City", "country": "UK"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_create_address_missing_required_returns_400(self):
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/addresses/",
            {"line1": "1 St"},  # missing city and country
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_update_address_returns_200(self):
        address = PersonAddress.objects.create(
            person=self.person, line1="1 St", city="London", country="UK"
        )
        response = self.client.patch(
            f"/api/people/persons/{self.person.id}/addresses/{address.id}/",
            {"city": "Manchester"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["city"], "Manchester")

    def test_update_address_not_found_returns_404(self):
        response = self.client.patch(
            f"/api/people/persons/{self.person.id}/addresses/99999/",
            {"city": "x"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)


# ─── Person → Note Views ───────────────────────────────────────────────────────

class PersonNoteViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)
        self.person = make_person()

    def test_list_notes_returns_200(self):
        response = self.client.get(f"/api/people/persons/{self.person.id}/notes/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_create_note_returns_201(self):
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/notes/",
            {"body": "A test note."},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["body"], "A test note.")

    def test_create_note_sets_author_to_request_user(self):
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/notes/",
            {"body": "Authored note."},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["author_name"], self.user.email)

    def test_create_note_empty_body_returns_400(self):
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/notes/",
            {"body": ""},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_create_note_person_not_found_returns_404(self):
        response = self.client.post(
            "/api/people/persons/99999/notes/",
            {"body": "Note."},
            format="json",
        )
        self.assertEqual(response.status_code, 404)


# ─── Person → Organization Relation Views ─────────────────────────────────────

class PersonOrgRelationViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)
        self.person = make_person()
        self.org_payload = {
            "organization_id": 1,
            "organization_type": "customer",
            "role": "contact",
        }

    def test_list_org_relations_returns_200(self):
        response = self.client.get(
            f"/api/people/persons/{self.person.id}/organizations/"
        )
        self.assertEqual(response.status_code, 200)

    def test_link_org_returns_201(self):
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/organizations/",
            self.org_payload,
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["is_active"])

    def test_duplicate_link_returns_409(self):
        self.client.post(
            f"/api/people/persons/{self.person.id}/organizations/",
            self.org_payload,
            format="json",
        )
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/organizations/",
            self.org_payload,
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_link_person_not_found_returns_404(self):
        response = self.client.post(
            "/api/people/persons/99999/organizations/",
            self.org_payload,
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_update_org_relation_returns_200(self):
        rel = OrganizationPersonRelation.objects.create(
            person=self.person,
            organization_id=1,
            organization_type="customer",
            role="contact",
        )
        response = self.client.patch(
            f"/api/people/persons/{self.person.id}/organizations/{rel.id}/",
            {"role": "billing"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role"], "billing")

    def test_update_org_relation_not_found_returns_404(self):
        response = self.client.patch(
            f"/api/people/persons/{self.person.id}/organizations/99999/",
            {"role": "x"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_close_org_relation_returns_200(self):
        rel = OrganizationPersonRelation.objects.create(
            person=self.person,
            organization_id=1,
            organization_type="customer",
            role="contact",
        )
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/organizations/{rel.id}/close/"
        )
        self.assertEqual(response.status_code, 200)
        rel.refresh_from_db()
        self.assertFalse(rel.is_active)

    def test_close_org_relation_not_found_returns_404(self):
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/organizations/99999/close/"
        )
        self.assertEqual(response.status_code, 404)

    def test_list_active_only_param(self):
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
        response = self.client.get(
            f"/api/people/persons/{self.person.id}/organizations/?active_only=true"
        )
        self.assertEqual(len(response.data), 1)
        self.assertTrue(response.data[0]["is_active"])


# ─── Person → Attachments ─────────────────────────────────────────────────────

class PersonAttachmentsViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)
        self.person = make_person()

    def test_list_attachments_returns_200(self):
        response = self.client.get(
            f"/api/people/persons/{self.person.id}/attachments/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])


# ─── Authentication guards on sub-resource endpoints ──────────────────────────

class SubResourceAuthTest(TestCase):
    """Verify that sub-resource endpoints all require authentication."""

    def setUp(self):
        self.client = APIClient()
        # Create a real person so the person_id exists (returns 401 not 404)
        from django.contrib.auth import get_user_model
        UserModel = get_user_model()
        admin = UserModel.objects.create_user(
            email="setup@test.com", password="pass1234!", is_staff=True, is_superuser=True
        )
        auth_client = APIClient()
        auth_client.force_authenticate(user=admin)
        r = auth_client.post(
            "/api/people/persons/",
            {"first_name": "Auth", "last_name": "Test", "force": True},
            format="json",
        )
        self.person_id = r.data["id"]

    def _assert_requires_auth(self, method, url, data=None):
        fn = getattr(self.client, method)
        kwargs = {"format": "json"} if data is not None else {}
        if data is not None:
            response = fn(url, data, **kwargs)
        else:
            response = fn(url)
        self.assertEqual(
            response.status_code, 401,
            f"Expected 401 for {method.upper()} {url}, got {response.status_code}",
        )

    def test_addresses_list_requires_auth(self):
        self._assert_requires_auth("get", f"/api/people/persons/{self.person_id}/addresses/")

    def test_addresses_create_requires_auth(self):
        self._assert_requires_auth(
            "post",
            f"/api/people/persons/{self.person_id}/addresses/",
            {"line1": "1 St", "city": "London", "country": "UK"},
        )

    def test_notes_list_requires_auth(self):
        self._assert_requires_auth("get", f"/api/people/persons/{self.person_id}/notes/")

    def test_notes_create_requires_auth(self):
        self._assert_requires_auth(
            "post",
            f"/api/people/persons/{self.person_id}/notes/",
            {"body": "Note."},
        )

    def test_categories_list_requires_auth(self):
        self._assert_requires_auth("get", f"/api/people/persons/{self.person_id}/categories/")

    def test_organizations_list_requires_auth(self):
        self._assert_requires_auth("get", f"/api/people/persons/{self.person_id}/organizations/")

    def test_person_detail_requires_auth(self):
        self._assert_requires_auth("get", f"/api/people/persons/{self.person_id}/")

    def test_deactivate_requires_auth(self):
        self._assert_requires_auth("post", f"/api/people/persons/{self.person_id}/deactivate/")


# ─── Person list — category filter ────────────────────────────────────────────

class PersonListCategoryFilterTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)

    def test_filter_by_category_id(self):
        cat = make_category(name="VIP", slug="vip")
        person_vip = make_person(first_name="VIP", last_name="Person", email="vip@test.com")
        make_person(first_name="Regular", last_name="Person", email="reg@test.com")
        PersonCategoryAssignment.objects.create(person=person_vip, category=cat)
        response = self.client.get(f"/api/people/persons/?category_id={cat.id}")
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], person_vip.id)

    def test_filter_by_nonexistent_category_id_returns_empty(self):
        make_person()
        response = self.client.get("/api/people/persons/?category_id=99999")
        self.assertEqual(response.data["count"], 0)


# ─── Person note — inactive person ────────────────────────────────────────────

class PersonNoteInactivePersonTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)
        self.person = make_person(is_active=False)

    def test_create_note_for_inactive_person_returns_404(self):
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/notes/",
            {"body": "Note for inactive."},
            format="json",
        )
        self.assertEqual(response.status_code, 404)


# ─── Address for inactive person ──────────────────────────────────────────────

class AddressInactivePersonTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)
        self.person = make_person(is_active=False)

    def test_create_address_for_inactive_person_returns_404(self):
        response = self.client.post(
            f"/api/people/persons/{self.person.id}/addresses/",
            {"line1": "1 St", "city": "London", "country": "UK"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
