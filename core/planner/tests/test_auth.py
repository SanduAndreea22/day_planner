from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from planner.models import UserProfile

class AuthTests(TestCase):

    # ================================
    # REGISTER
    # ================================

    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("register"),
            {
                "email": "user@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(User.objects.count(), 1)
        self.assertRedirects(response, reverse("today"))

    def test_register_duplicate_email_fails(self):
        User.objects.create_user(
            username="existing_user",
            email="dup@example.com",
            password="StrongPass123!",
        )

        response = self.client.post(
            reverse("register"),
            {
                "email": "dup@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(User.objects.count(), 1)
        self.assertContains(response, "Acest email este deja folosit")

    # ================================
    # LOGIN
    # ================================

    def test_login_with_correct_email_and_password(self):
        user = User.objects.create_user(
            username="login_user",
            email="login@example.com",
            password="StrongPass123!",
        )

        response = self.client.post(
            reverse("login"),
            {
                "email": "login@example.com",
                "password": "StrongPass123!",
            },
        )

        self.assertRedirects(response, reverse("today"))

    def test_login_with_wrong_password_fails(self):
        User.objects.create_user(
            username="wrong_pass",
            email="wrong@example.com",
            password="StrongPass123!",
        )

        response = self.client.post(
            reverse("login"),
            {
                "email": "wrong@example.com",
                "password": "BadPassword",
            },
        )

        self.assertContains(response, "Email sau parolă incorectă")

    def test_login_with_unknown_email_fails(self):
        response = self.client.post(
            reverse("login"),
            {
                "email": "unknown@example.com",
                "password": "StrongPass123!",
            },
        )

        self.assertContains(response, "Email sau parolă incorectă")

    # ================================
    # LOGOUT
    # ================================

    def test_logout_redirects_to_home(self):
        user = User.objects.create_user(
            username="logoutuser",
            email="logout@example.com",
            password="StrongPass123!",
        )

        self.client.login(username=user.username, password="StrongPass123!")

        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("home"))

    # ================================
    # PROFILE
    # ================================

    def test_profile_page_requires_login(self):
        response = self.client.get(reverse("profile"))
        self.assertRedirects(response, "/login/?next=/profile/")

    def test_profile_update(self):
        user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="StrongPass123!",
        )

        self.client.login(username=user.username, password="StrongPass123!")

        response = self.client.post(
            reverse("profile"),
            {
                "nickname": "Andi",
                "bio": "Mă simt bine azi",
            },
        )

        profile = UserProfile.objects.get(user=user)

        self.assertEqual(profile.nickname, "Andi")
        self.assertEqual(profile.bio, "Mă simt bine azi")
        self.assertContains(response, "Profil actualizat")
