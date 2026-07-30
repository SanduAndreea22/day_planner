import pytest
from datetime import date
from django.contrib.auth.models import User
from django.urls import reverse

from planner.models import Day


@pytest.mark.django_db
def test_delete_account_requires_login(client):
    url = reverse("delete_account")
    response = client.get(url)
    assert response.status_code == 302
    assert reverse("login") in response.url


@pytest.mark.django_db
def test_delete_account_view_renders(client):
    user = User.objects.create_user(
        username="user10",
        email="user10@example.com",
        password="OldPassword123!"
    )
    client.force_login(user)

    response = client.get(reverse("delete_account"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_delete_account_wrong_password_does_not_delete(client):
    user = User.objects.create_user(
        username="user11",
        email="user11@example.com",
        password="OldPassword123!"
    )
    client.force_login(user)

    response = client.post(reverse("delete_account"), {"password": "WrongPassword!"})
    assert response.status_code == 302
    assert response.url == reverse("delete_account")
    assert User.objects.filter(pk=user.pk).exists()


@pytest.mark.django_db
def test_delete_account_correct_password_deletes_everything(client):
    user = User.objects.create_user(
        username="user12",
        email="user12@example.com",
        password="OldPassword123!"
    )
    Day.objects.create(user=user, date=date.today(), mood="good")
    client.force_login(user)

    response = client.post(reverse("delete_account"), {"password": "OldPassword123!"})
    assert response.status_code == 302
    assert response.url == reverse("home")

    assert not User.objects.filter(pk=user.pk).exists()
    assert not Day.objects.filter(user_id=user.pk).exists()

    # the session should be logged out too
    response = client.get(reverse("today"))
    assert response.status_code == 302
    assert reverse("login") in response.url
