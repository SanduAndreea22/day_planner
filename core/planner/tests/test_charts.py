from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class ChartsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="eva",
            email="eva@test.com",
            password="ComplexPass123!",
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_mood_chart_template_exists(self):
        response = self.client.get(reverse("mood_chart"))
        self.assertTemplateUsed(response, "planner/chart/mood.html")

    def test_productivity_chart_template_exists(self):
        response = self.client.get(reverse("productivity_chart"))
        self.assertTemplateUsed(response, "planner/chart/productivity.html")

    def test_monthly_overview_template_exists(self):
        response = self.client.get(reverse("monthly_overview"))
        self.assertTemplateUsed(response, "planner/monthly_overview.html")
