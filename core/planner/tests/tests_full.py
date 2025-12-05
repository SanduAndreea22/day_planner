from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from planner.models import UserProfile, Day, TimeBlock


class DayPlannerFullTests(TestCase):
    def setUp(self):
        # Create test users
        self.user = User.objects.create_user(
            username="user_1",
            email="user1@test.com",
            password="StrongPass123!"
        )
        UserProfile.objects.create(user=self.user, nickname="Tester", bio="Bio test")

        self.other_user = User.objects.create_user(
            username="user_2",
            email="user2@test.com",
            password="StrongPass123!"
        )
        UserProfile.objects.create(user=self.other_user, nickname="Other", bio="Other bio")

    # -----------------------------
    # REGISTER
    # -----------------------------
    def test_register_success(self):
        response = self.client.post(reverse("register"), {
            "email": "newuser@test.com",
            "password1": "NewStrongPass123!",
            "password2": "NewStrongPass123!"
        })
        self.assertEqual(User.objects.filter(email="newuser@test.com").count(), 1)
        self.assertRedirects(response, reverse("today"))

    def test_register_password_mismatch(self):
        response = self.client.post(reverse("register"), {
            "email": "newuser2@test.com",
            "password1": "Password1!",
            "password2": "Password2!"
        })
        self.assertContains(response, "Parolele nu coincid")

    def test_register_duplicate_email(self):
        response = self.client.post(reverse("register"), {
            "email": "user1@test.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!"
        })
        self.assertContains(response, "Acest email este deja folosit")

    # -----------------------------
    # LOGIN / LOGOUT
    # -----------------------------
    def test_login_success(self):
        response = self.client.post(reverse("login"), {
            "email": "user1@test.com",
            "password": "StrongPass123!"
        })
        self.assertRedirects(response, reverse("today"))

    def test_login_wrong_password(self):
        response = self.client.post(reverse("login"), {
            "email": "user1@test.com",
            "password": "WrongPass!"
        })
        self.assertContains(response, "Email sau parolă incorectă")

    def test_login_nonexistent_user(self):
        response = self.client.post(reverse("login"), {
            "email": "nouser@test.com",
            "password": "Password123!"
        })
        self.assertContains(response, "Email sau parolă incorectă")

    def test_logout_redirect(self):
        self.client.login(username=self.user.username, password="StrongPass123!")
        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("home"))

    # -----------------------------
    # PROFILE
    # -----------------------------
    def test_profile_view_requires_login(self):
        response = self.client.get(reverse("profile"))
        self.assertRedirects(response, "/login/?next=/profile/")

    def test_profile_view_logged_in(self):
        self.client.login(username=self.user.username, password="StrongPass123!")
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.email)

    def test_profile_update_success(self):
        self.client.login(username=self.user.username, password="StrongPass123!")
        response = self.client.post(reverse("profile"), {"nickname": "Updated", "bio": "New bio"})
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.nickname, "Updated")
        self.assertEqual(profile.bio, "New bio")
        self.assertContains(response, "Profil actualizat")

    # -----------------------------
    # DAY & TIMEBLOCK
    # -----------------------------
    def test_create_day_and_timeblocks(self):
        self.client.login(username=self.user.username, password="StrongPass123!")
        day = Day.objects.create(user=self.user)
        tb1 = TimeBlock.objects.create(day=day, title="Task 1", start_hour=9, end_hour=10)
        tb2 = TimeBlock.objects.create(day=day, title="Task 2", start_hour=10, end_hour=11)
        self.assertEqual(day.timeblock_set.count(), 2)

    def test_timeblock_overlap(self):
        day = Day.objects.create(user=self.user)
        TimeBlock.objects.create(day=day, title="Task 1", start_hour=9, end_hour=11)
        tb2 = TimeBlock.objects.create(day=day, title="Task 2", start_hour=10, end_hour=12)
        self.assertEqual(day.timeblock_set.count(), 2)  # Currently no validation, just tests storage

    def test_delete_timeblock(self):
        day = Day.objects.create(user=self.user)
        tb = TimeBlock.objects.create(day=day, title="Task to delete", start_hour=9, end_hour=10)
        tb.delete()
        self.assertEqual(day.timeblock_set.count(), 0)

    # -----------------------------
    # REFLECTIONS
    # -----------------------------


    # -----------------------------
    # CALENDAR / VIEWS
    # -----------------------------
    def test_access_today_requires_login(self):
        response = self.client.get(reverse("today"))
        self.assertRedirects(response, "/login/?next=/today/")

    def test_access_calendar_requires_login(self):
        response = self.client.get(reverse("calendar"))
        self.assertRedirects(response, "/login/?next=/calendar/")

    def test_access_weekly_score_requires_login(self):
        response = self.client.get(reverse("weekly_score"))
        self.assertRedirects(response, "/login/?next=/weekly_score/")

    def test_access_monthly_overview_requires_login(self):
        response = self.client.get(reverse("monthly_overview"))
        self.assertRedirects(response, "/login/?next=/monthly_overview/")

    # -----------------------------
    # EDGE CASES
    # -----------------------------
    def test_register_short_password_fails(self):
        response = self.client.post(reverse("register"), {
            "email": "shortpass@test.com",
            "password1": "123",
            "password2": "123"
        })
        self.assertContains(response, "This password is too short")

    def test_register_weak_password_fails(self):
        response = self.client.post(reverse("register"), {
            "email": "weak@test.com",
            "password1": "password",
            "password2": "password"
        })
        self.assertContains(response, "This password is too common")

    def test_register_invalid_email_fails(self):
        response = self.client.post(reverse("register"), {
            "email": "not-an-email",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!"
        })
        self.assertContains(response, "Enter a valid email address")

    # -----------------------------
    # ACCESS CONTROL / OTHER USERS
    # -----------------------------
    def test_user_cannot_edit_others_profile(self):
        self.client.login(username=self.user.username, password="StrongPass123!")
        other_profile = UserProfile.objects.get(user=self.other_user)
        response = self.client.post(reverse("profile"), {"nickname": "Hacked", "bio": "Malicious"})
        self.assertNotEqual(other_profile.nickname, "Hacked")
        self.assertNotEqual(other_profile.bio, "Malicious")

    def test_user_cannot_access_others_day(self):
        day = Day.objects.create(user=self.other_user)
        self.client.login(username=self.user.username, password="StrongPass123!")
        response = self.client.get(reverse("today") + f"?day={day.id}")
        self.assertNotContains(response, self.other_user.email)

    # -----------------------------
    # ADDITIONAL CHECKS
    # -----------------------------
    def test_multiple_days_creation(self):
        for i in range(5):
            Day.objects.create(user=self.user)
        self.assertEqual(Day.objects.filter(user=self.user).count(), 5)

    def test_multiple_timeblocks_creation(self):
        day = Day.objects.create(user=self.user)
        for i in range(5):
            TimeBlock.objects.create(day=day, title=f"Task {i}", start_hour=i, end_hour=i + 1)
        self.assertEqual(day.timeblock_set.count(), 5)

    def test_profile_contains_nickname_and_bio(self):
        self.client.login(username=self.user.username, password="StrongPass123!")
        response = self.client.get(reverse("profile"))
        self.assertContains(response, "Tester")
        self.assertContains(response, "Bio test")




