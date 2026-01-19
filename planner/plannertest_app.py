from datetime import date as date_cls
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from planner.models import Day, Quote, EveningReflection, TimeBlock


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="test@example.com",
    ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
)
class AuthFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
    def test_register_sends_confirmation_email(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "alice",
                "email": "alice@example.com",
                "password1": "ComplexPass123!",
                "password2": "ComplexPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "planner/auth/check_email.html")
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertEqual(email.to, ["alice@example.com"])
        self.assertIn("/activate/", email.body)

    def test_activate_account_marks_user_active(self):
        user = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="ComplexPass123!",
            is_active=False,
        )

        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        response = self.client.get(reverse("activate", args=[uidb64, token]))

        self.assertTemplateUsed(
            response, "planner/auth/email_confirm_success.html"
        )
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_login_logout_flow(self):
        user = User.objects.create_user(
            username="carol_test",
            email="carol@example.com",
            password="ComplexPass123!",
            is_active=True,
        )

        response = self.client.post(
            reverse("login"),
            {
                "email": "carol@example.com",
                "password": "ComplexPass123!",
            }
        )

        self.assertRedirects(response, reverse("today"))

        response = self.client.get(reverse("today"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("logout"))
        self.assertRedirects(response, reverse("home"))

        response = self.client.get(reverse("today"))
        self.assertRedirects(response, reverse("login") + "?next=/today/")


@override_settings(ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"])
class DayFlowTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="dana",
            email="dana@example.com",
            password="ComplexPass123!",
        )
        self.client.force_login(self.user)

        self.day = Day.objects.create(
            user=self.user,
            date=date_cls.today()
        )

    def test_day_page_loads(self):
        response = self.client.get(
            reverse(
                "day_detail",
                args=[
                    self.day.date.year,
                    self.day.date.month,
                    self.day.date.day,
                ],
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ziua mea")

    def test_update_day_notes(self):
        response = self.client.post(
            reverse("update_day_text"),
            {"day_id": self.day.id, "notes": "A meaningful note"},
        )

        self.assertEqual(response.status_code, 302)
        self.day.refresh_from_db()
        self.assertEqual(self.day.notes, "A meaningful note")

    def test_add_timeblock(self):
        response = self.client.post(
            reverse("add_timeblock"),
            {
                "day_id": self.day.id,
                "start_time": "09:00",
                "end_time": "10:00",
                "title": "Test task",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.day.time_blocks.count(), 1)

    def test_toggle_timeblock(self):
        block = TimeBlock.objects.create(
            day=self.day,
            start_time="09:00",
            end_time="10:00",
            title="Task",
        )

        response = self.client.get(
            reverse("toggle_timeblock", args=[block.id])
        )

        self.assertEqual(response.status_code, 302)
        block.refresh_from_db()
        self.assertTrue(block.completed)

    def test_close_day_creates_reflection_and_locks_day(self):
        response = self.client.post(
            reverse(
                "evening_reflection",
                args=[
                    self.day.date.year,
                    self.day.date.month,
                    self.day.date.day,
                ],
            ),
            {
                "drain": "Oboseală",
                "small_win": "Am rezistat",
            },
        )

        self.day.refresh_from_db()

        self.assertTrue(self.day.is_closed)
        self.assertIsNotNone(self.day.closed_at)
        self.assertTrue(
            EveningReflection.objects.filter(day=self.day).exists()
        )


class ClosingQuoteTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="eva",
            email="eva@example.com",
            password="ComplexPass123!",
        )
        self.client.force_login(self.user)

        self.quote1 = Quote.objects.create(
            text="Respiră. Ai făcut suficient.",
            active=True,
        )

        self.quote2 = Quote.objects.create(
            text="Nu totul trebuie rezolvat azi.",
            active=True,
        )

        self.day = Day.objects.create(
            user=self.user,
            date=date_cls.today(),
        )

    def test_closing_quote_is_assigned_once_and_persists(self):
        self.client.post(
            reverse(
                "evening_reflection",
                args=[
                    self.day.date.year,
                    self.day.date.month,
                    self.day.date.day,
                ],
            ),
            {
                "drain": "Greu",
                "small_win": "Am continuat",
            },
        )

        self.day.refresh_from_db()
        first_quote = self.day.closing_quote

        self.assertIsNotNone(first_quote)

        response = self.client.get(
            reverse(
                "day_detail",
                args=[
                    self.day.date.year,
                    self.day.date.month,
                    self.day.date.day,
                ],
            )
        )

        self.day.refresh_from_db()
        self.assertEqual(self.day.closing_quote, first_quote)
        self.assertContains(response, first_quote.text)


class ChartsTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="ana",
            email="ana@example.com",
            password="ComplexPass123!",
        )
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


