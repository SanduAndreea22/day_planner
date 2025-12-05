from datetime import date
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from planner.models import Day


class DayViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dana",
            email="dana@test.com",
            password="ComplexPass123!",
        )
        self.client = Client()
        self.client.force_login(self.user)

        self.day = Day.objects.create(
            user=self.user,
            date=date.today()
        )

    def test_update_day_notes(self):
        response = self.client.post(
            reverse("update_day_text"),
            {"day_id": self.day.id, "notes": "Un gând important"},
        )

        self.assertEqual(response.status_code, 302)
        self.day.refresh_from_db()
        self.assertEqual(self.day.notes, "Un gând important")

    def test_day_is_closed_redirect(self):
        self.day.is_closed = True
        self.day.save()

        response = self.client.get(
            reverse(
                "day_detail",
                args=[self.day.date.year, self.day.date.month, self.day.date.day],
            )
        )

        self.assertEqual(response.status_code, 200)
