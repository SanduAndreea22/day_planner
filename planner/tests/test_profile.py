import pytest
from django.urls import reverse

from planner.models import UserProfile


@pytest.mark.django_db
def test_profile_view_requires_login(client):
    response = client.get(reverse("profile"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_profile_view_get_creates_profile(client, django_user_model):
    user = django_user_model.objects.create_user(username="profileuser1", password="pass12345")
    client.force_login(user)

    response = client.get(reverse("profile"))

    assert response.status_code == 200
    assert UserProfile.objects.filter(user=user).exists()


@pytest.mark.django_db
def test_profile_view_post_updates_profile(client, django_user_model):
    user = django_user_model.objects.create_user(username="profileuser2", password="pass12345")
    client.force_login(user)

    response = client.post(reverse("profile"), {
        "nickname": "Andi",
        "bio": "Testing my profile",
        "evening_reminder_time": "20:30",
    })

    assert response.status_code == 200
    profile = UserProfile.objects.get(user=user)
    assert profile.nickname == "Andi"
    assert profile.bio == "Testing my profile"
    assert str(profile.evening_reminder_time) == "20:30:00"
