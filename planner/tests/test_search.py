import pytest
from datetime import date, timedelta
from django.contrib.auth.models import User
from django.urls import reverse

from planner.models import Day


@pytest.mark.django_db
def test_search_requires_login(client):
    response = client.get(reverse("search"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_search_by_text(client):
    user = User.objects.create_user(username="s1", email="s1@example.com", password="pass12345")
    client.force_login(user)

    Day.objects.create(user=user, date=date.today(), notes="A very calm morning walk")
    Day.objects.create(user=user, date=date.today() - timedelta(days=1), notes="Stressful meeting")

    response = client.get(reverse("search"), {"q": "calm"})
    assert response.status_code == 200
    assert len(response.context["days"]) == 1
    assert "calm" in response.context["days"][0].notes


@pytest.mark.django_db
def test_search_by_mood(client):
    user = User.objects.create_user(username="s2", email="s2@example.com", password="pass12345")
    client.force_login(user)

    Day.objects.create(user=user, date=date.today(), mood="good", notes="")
    Day.objects.create(user=user, date=date.today() - timedelta(days=1), mood="bad", notes="")

    response = client.get(reverse("search"), {"mood": "good"})
    assert response.status_code == 200
    assert len(response.context["days"]) == 1
    assert response.context["days"][0].mood == "good"


@pytest.mark.django_db
def test_search_only_returns_own_days(client):
    owner = User.objects.create_user(username="s3", email="s3@example.com", password="pass12345")
    other = User.objects.create_user(username="s4", email="s4@example.com", password="pass12345")
    client.force_login(owner)

    Day.objects.create(user=other, date=date.today(), notes="secret entry")

    response = client.get(reverse("search"), {"q": "secret"})
    assert response.status_code == 200
    assert len(response.context["days"]) == 0
