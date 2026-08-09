from datetime import date, datetime, timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from planner.models import Day, UserProfile

URL_NAME = "send_evening_reminders"


@pytest.mark.django_db
def test_reminder_endpoint_rejects_missing_token(client):
    response = client.post(reverse(URL_NAME))
    assert response.status_code == 403


@pytest.mark.django_db
@override_settings(TASK_SECRET="test-secret")
def test_reminder_endpoint_rejects_wrong_token(client):
    response = client.post(reverse(URL_NAME), HTTP_AUTHORIZATION="Bearer nope")
    assert response.status_code == 403


@pytest.mark.django_db
@override_settings(TASK_SECRET="test-secret")
def test_reminder_sent_when_time_matches_and_day_open(client):
    user = User.objects.create_user(username="r1", email="r1@example.com", password="pass12345")
    now = timezone.localtime()
    UserProfile.objects.create(user=user, evening_reminder_time=now.time())
    Day.objects.create(user=user, date=timezone.localdate(), is_closed=False)

    response = client.post(reverse(URL_NAME), HTTP_AUTHORIZATION="Bearer test-secret")
    assert response.status_code == 200
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["r1@example.com"]


@pytest.mark.django_db
@override_settings(TASK_SECRET="test-secret")
def test_reminder_not_sent_when_day_already_closed(client):
    user = User.objects.create_user(username="r2", email="r2@example.com", password="pass12345")
    now = timezone.localtime()
    UserProfile.objects.create(user=user, evening_reminder_time=now.time())
    Day.objects.create(user=user, date=timezone.localdate(), is_closed=True)

    response = client.post(reverse(URL_NAME), HTTP_AUTHORIZATION="Bearer test-secret")
    assert response.status_code == 200
    assert len(mail.outbox) == 0


@pytest.mark.django_db
@override_settings(TASK_SECRET="test-secret")
def test_reminder_not_sent_when_time_does_not_match(client):
    user = User.objects.create_user(username="r3", email="r3@example.com", password="pass12345")
    now = timezone.localtime()
    far_off_time = (now + timedelta(hours=5)).time()
    UserProfile.objects.create(user=user, evening_reminder_time=far_off_time)
    Day.objects.create(user=user, date=timezone.localdate(), is_closed=False)

    response = client.post(reverse(URL_NAME), HTTP_AUTHORIZATION="Bearer test-secret")
    assert response.status_code == 200
    assert len(mail.outbox) == 0


@pytest.mark.django_db
@override_settings(TASK_SECRET="test-secret")
def test_reminder_sent_when_window_spans_midnight(client):
    user = User.objects.create_user(username="r4", email="r4@example.com", password="pass12345")
    UserProfile.objects.create(user=user, evening_reminder_time=datetime.strptime("23:55", "%H:%M").time())

    now = timezone.localtime()
    fake_now = timezone.make_aware(datetime.combine(now.date(), datetime.strptime("00:05", "%H:%M").time()), now.tzinfo)
    Day.objects.create(user=user, date=fake_now.date(), is_closed=False)

    with patch("planner.views.timezone.localtime", return_value=fake_now):
        response = client.post(reverse(URL_NAME), HTTP_AUTHORIZATION="Bearer test-secret")

    assert response.status_code == 200
    assert len(mail.outbox) == 1


@pytest.mark.django_db
@override_settings(TASK_SECRET="test-secret")
def test_reminder_not_sent_twice_across_adjacent_windows(client):
    user = User.objects.create_user(username="r5", email="r5@example.com", password="pass12345")
    reminder_time = datetime.strptime("20:00", "%H:%M").time()
    UserProfile.objects.create(user=user, evening_reminder_time=reminder_time)

    now = timezone.localtime()
    first_run = timezone.make_aware(datetime.combine(now.date(), reminder_time), now.tzinfo)
    second_run = first_run + timedelta(minutes=15)
    Day.objects.create(user=user, date=first_run.date(), is_closed=False)

    with patch("planner.views.timezone.localtime", return_value=first_run):
        client.post(reverse(URL_NAME), HTTP_AUTHORIZATION="Bearer test-secret")
    with patch("planner.views.timezone.localtime", return_value=second_run):
        client.post(reverse(URL_NAME), HTTP_AUTHORIZATION="Bearer test-secret")

    assert len(mail.outbox) == 1
