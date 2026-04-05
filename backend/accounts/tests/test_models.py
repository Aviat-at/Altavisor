"""
test_models.py — Unit tests for the accounts User model and UserManager.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


# ─── UserManager ──────────────────────────────────────────────────────────────

class UserManagerTest(TestCase):
    def test_create_user_sets_email(self):
        user = User.objects.create_user(email="alice@example.com", password="pass1234!")
        self.assertEqual(user.email, "alice@example.com")

    def test_create_user_normalizes_email_domain(self):
        # Django's normalize_email lowercases only the domain part
        user = User.objects.create_user(email="alice@EXAMPLE.COM", password="pass1234!")
        self.assertEqual(user.email, "alice@example.com")

    def test_create_user_is_active_by_default(self):
        user = User.objects.create_user(email="bob@example.com", password="pass1234!")
        self.assertTrue(user.is_active)

    def test_create_user_is_not_staff_by_default(self):
        user = User.objects.create_user(email="carol@example.com", password="pass1234!")
        self.assertFalse(user.is_staff)

    def test_create_user_is_not_superuser_by_default(self):
        user = User.objects.create_user(email="dave@example.com", password="pass1234!")
        self.assertFalse(user.is_superuser)

    def test_create_user_password_is_hashed(self):
        user = User.objects.create_user(email="eve@example.com", password="plaintext")
        self.assertNotEqual(user.password, "plaintext")
        self.assertTrue(user.check_password("plaintext"))

    def test_create_user_without_email_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="pass1234!")

    def test_create_superuser_is_staff_and_superuser(self):
        admin = User.objects.create_superuser(email="admin@example.com", password="pass1234!")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_create_superuser_raises_if_is_staff_false(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="bad@example.com", password="pass1234!", is_staff=False
            )

    def test_create_superuser_raises_if_is_superuser_false(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email="bad2@example.com", password="pass1234!", is_superuser=False
            )


# ─── User model properties ────────────────────────────────────────────────────

class UserModelTest(TestCase):
    def test_str_returns_email(self):
        user = User.objects.create_user(email="frank@example.com", password="pass1234!")
        self.assertEqual(str(user), "frank@example.com")

    def test_initials_from_full_name(self):
        user = User.objects.create_user(
            email="grace@example.com", password="pass1234!", full_name="Grace Hopper"
        )
        self.assertEqual(user.initials, "GH")

    def test_initials_from_multi_word_name_uses_first_and_last(self):
        user = User.objects.create_user(
            email="henry@example.com", password="pass1234!", full_name="Henry Van Dyke"
        )
        self.assertEqual(user.initials, "HD")

    def test_initials_fallback_to_email_when_no_full_name(self):
        user = User.objects.create_user(email="ij@example.com", password="pass1234!")
        self.assertEqual(user.initials, "IJ")

    def test_initials_fallback_for_single_word_name(self):
        user = User.objects.create_user(
            email="kate@example.com", password="pass1234!", full_name="Kate"
        )
        self.assertEqual(user.initials, "KA")

    def test_default_role_is_viewer(self):
        user = User.objects.create_user(email="leo@example.com", password="pass1234!")
        self.assertEqual(user.role, User.Role.VIEWER)

    def test_email_is_unique(self):
        from django.db import IntegrityError
        User.objects.create_user(email="shared@example.com", password="pass1234!")
        with self.assertRaises(IntegrityError):
            User.objects.create_user(email="shared@example.com", password="other1234!")

    def test_date_joined_is_set_on_creation(self):
        user = User.objects.create_user(email="mia@example.com", password="pass1234!")
        self.assertIsNotNone(user.date_joined)
