from datetime import date, timedelta

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
