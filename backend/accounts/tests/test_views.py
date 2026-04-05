"""
test_views.py — HTTP / API layer tests for the accounts authentication endpoints.

Endpoints covered:
  POST   /api/auth/login/
  POST   /api/auth/refresh/
  POST   /api/auth/logout/
  GET    /api/auth/me/
  PATCH  /api/auth/me/
  POST   /api/auth/change-password/
  POST   /api/auth/register/
  GET    /api/auth/sso/
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# ─── Helpers ───────────────────────────────────────────────────────────────────

def make_user(**kwargs) -> User:
    defaults = {"email": "user@test.com", "password": "testpass123", "full_name": "Test User"}
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def make_admin(**kwargs) -> User:
    defaults = {
        "email": "admin@test.com",
        "password": "testpass123",
        "is_staff": True,
        "is_superuser": True,
    }
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


def get_tokens_for_user(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


# ─── Login ────────────────────────────────────────────────────────────────────

class LoginViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()

    def test_login_success_returns_200(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": "user@test.com", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_login_returns_access_and_refresh_tokens(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": "user@test.com", "password": "testpass123"},
            format="json",
        )
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_returns_user_data(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": "user@test.com", "password": "testpass123"},
            format="json",
        )
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["email"], "user@test.com")

    def test_login_updates_last_login(self):
        self.assertIsNone(self.user.last_login)
        self.client.post(
            "/api/auth/login/",
            {"email": "user@test.com", "password": "testpass123"},
            format="json",
        )
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)

    def test_login_wrong_password_returns_401(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": "user@test.com", "password": "wrongpassword"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_login_unknown_email_returns_401(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": "nobody@test.com", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_login_inactive_user_returns_401(self):
        self.user.is_active = False
        self.user.save()
        response = self.client.post(
            "/api/auth/login/",
            {"email": "user@test.com", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_login_email_is_case_insensitive(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": "USER@TEST.COM", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_login_missing_fields_returns_401(self):
        response = self.client.post("/api/auth/login/", {}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_login_response_has_detail_on_failure(self):
        response = self.client.post(
            "/api/auth/login/",
            {"email": "user@test.com", "password": "wrong"},
            format="json",
        )
        self.assertIn("detail", response.data)


# ─── Refresh ──────────────────────────────────────────────────────────────────

class RefreshViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.tokens = get_tokens_for_user(self.user)

    def test_refresh_returns_new_access_token(self):
        response = self.client.post(
            "/api/auth/refresh/",
            {"refresh": self.tokens["refresh"]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_refresh_without_token_returns_400(self):
        response = self.client.post("/api/auth/refresh/", {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_refresh_with_invalid_token_returns_401(self):
        response = self.client.post(
            "/api/auth/refresh/",
            {"refresh": "this.is.not.valid"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)


# ─── Logout ───────────────────────────────────────────────────────────────────

class LogoutViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.tokens = get_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.tokens['access']}")

    def test_logout_returns_200(self):
        response = self.client.post(
            "/api/auth/logout/",
            {"refresh": self.tokens["refresh"]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["detail"], "Logged out successfully.")

    def test_logout_without_refresh_token_still_returns_200(self):
        response = self.client.post("/api/auth/logout/", {}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_logout_requires_authentication(self):
        client = APIClient()
        response = client.post("/api/auth/logout/", {}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_logout_with_invalid_refresh_token_still_returns_200(self):
        # The view silently ignores token errors on logout
        response = self.client.post(
            "/api/auth/logout/",
            {"refresh": "invalid.token.here"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)


# ─── Me (GET + PATCH) ─────────────────────────────────────────────────────────

class MeViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user(full_name="Test User")
        self.client.force_authenticate(user=self.user)

    def test_get_me_returns_200(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 200)

    def test_get_me_returns_current_user_data(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.data["email"], "user@test.com")
        self.assertEqual(response.data["full_name"], "Test User")

    def test_get_me_includes_expected_fields(self):
        response = self.client.get("/api/auth/me/")
        for field in ("id", "email", "full_name", "role", "initials", "date_joined"):
            self.assertIn(field, response.data)

    def test_get_me_requires_authentication(self):
        client = APIClient()
        response = client.get("/api/auth/me/")
        self.assertEqual(response.status_code, 401)

    def test_patch_me_updates_full_name(self):
        response = self.client.patch(
            "/api/auth/me/",
            {"full_name": "Updated Name"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Updated Name")

    def test_patch_me_ignores_disallowed_fields(self):
        original_email = self.user.email
        self.client.patch(
            "/api/auth/me/",
            {"email": "hacker@test.com", "full_name": "Me"},
            format="json",
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, original_email)

    def test_patch_me_requires_authentication(self):
        client = APIClient()
        response = client.patch("/api/auth/me/", {"full_name": "x"}, format="json")
        self.assertEqual(response.status_code, 401)


# ─── Change Password ──────────────────────────────────────────────────────────

class ChangePasswordViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()
        self.client.force_authenticate(user=self.user)

    def test_change_password_success_returns_200(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "testpass123",
                "new_password": "NewSecure456!",
                "new_password_confirm": "NewSecure456!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("detail", response.data)

    def test_change_password_actually_changes_password(self):
        self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "testpass123",
                "new_password": "NewSecure456!",
                "new_password_confirm": "NewSecure456!",
            },
            format="json",
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewSecure456!"))

    def test_change_password_wrong_current_returns_400(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "wrongpassword",
                "new_password": "NewSecure456!",
                "new_password_confirm": "NewSecure456!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_change_password_mismatch_returns_400(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "testpass123",
                "new_password": "NewSecure456!",
                "new_password_confirm": "DifferentPass789!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_change_password_too_short_returns_400(self):
        response = self.client.post(
            "/api/auth/change-password/",
            {
                "current_password": "testpass123",
                "new_password": "short",
                "new_password_confirm": "short",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_change_password_requires_authentication(self):
        client = APIClient()
        response = client.post(
            "/api/auth/change-password/",
            {
                "current_password": "testpass123",
                "new_password": "NewSecure456!",
                "new_password_confirm": "NewSecure456!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_change_password_missing_fields_returns_400(self):
        response = self.client.post("/api/auth/change-password/", {}, format="json")
        self.assertEqual(response.status_code, 400)


# ─── Register ─────────────────────────────────────────────────────────────────

class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = make_admin()
        self.client.force_authenticate(user=self.admin)
        self.payload = {
            "email": "newuser@test.com",
            "full_name": "New User",
            "role": "viewer",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }

    def test_register_success_returns_201(self):
        response = self.client.post("/api/auth/register/", self.payload, format="json")
        self.assertEqual(response.status_code, 201)

    def test_register_creates_user(self):
        self.client.post("/api/auth/register/", self.payload, format="json")
        self.assertTrue(User.objects.filter(email="newuser@test.com").exists())

    def test_register_returns_user_data(self):
        response = self.client.post("/api/auth/register/", self.payload, format="json")
        self.assertEqual(response.data["email"], "newuser@test.com")
        self.assertEqual(response.data["full_name"], "New User")

    def test_register_password_not_in_response(self):
        response = self.client.post("/api/auth/register/", self.payload, format="json")
        self.assertNotIn("password", response.data)

    def test_register_duplicate_email_returns_400(self):
        make_user(email="newuser@test.com")
        response = self.client.post("/api/auth/register/", self.payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_register_password_mismatch_returns_400(self):
        payload = {**self.payload, "password_confirm": "DifferentPass456!"}
        response = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_register_short_password_returns_400(self):
        payload = {**self.payload, "password": "short", "password_confirm": "short"}
        response = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_register_requires_admin(self):
        regular_user = make_user(email="regular@test.com")
        client = APIClient()
        client.force_authenticate(user=regular_user)
        response = client.post("/api/auth/register/", self.payload, format="json")
        self.assertEqual(response.status_code, 403)

    def test_register_requires_authentication(self):
        client = APIClient()
        response = client.post("/api/auth/register/", self.payload, format="json")
        self.assertEqual(response.status_code, 401)

    def test_register_missing_email_returns_400(self):
        payload = {k: v for k, v in self.payload.items() if k != "email"}
        response = self.client.post("/api/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, 400)


# ─── SSO Placeholder ──────────────────────────────────────────────────────────

class SSOViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_sso_returns_501(self):
        response = self.client.get("/api/auth/sso/")
        self.assertEqual(response.status_code, 501)

    def test_sso_returns_not_configured_message(self):
        response = self.client.get("/api/auth/sso/")
        self.assertIn("detail", response.data)
        self.assertIn("SSO", response.data["detail"])

    def test_sso_accessible_without_authentication(self):
        response = self.client.get("/api/auth/sso/")
        # Should not return 401 — it's AllowAny
        self.assertNotEqual(response.status_code, 401)
