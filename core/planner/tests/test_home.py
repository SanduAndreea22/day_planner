from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User


class HomeViewTests(TestCase):

    def test_home_page_loads_for_anonymous_user(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)

    def test_home_uses_correct_template(self):
        response = self.client.get(reverse("home"))
        self.assertTemplateUsed(response, "planner/home.html")

    def test_home_explains_app_purpose(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "organizarea zilelor")

    def test_home_has_cta_buttons(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Creează cont")
        self.assertContains(response, "Autentificare")

    def test_authenticated_user_is_redirected_to_today(self):
        user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

        response = self.client.get(reverse("home"))
        self.assertRedirects(response, reverse("today"))
