import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from planner.models import Feedback


@pytest.mark.django_db
def test_feedback_requires_login(client):
    response = client.get(reverse("feedback"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_feedback_form_renders(client):
    user = User.objects.create_user(username="f1", email="f1@example.com", password="pass12345")
    client.force_login(user)

    response = client.get(reverse("feedback"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_feedback_submission_saves_and_redirects(client):
    user = User.objects.create_user(username="f2", email="f2@example.com", password="pass12345")
    client.force_login(user)

    response = client.post(reverse("feedback"), {"message": "Really like the calendar view!"})
    assert response.status_code == 302

    entry = Feedback.objects.get()
    assert entry.user == user
    assert entry.message == "Really like the calendar view!"


@pytest.mark.django_db
def test_feedback_rejects_empty_message(client):
    user = User.objects.create_user(username="f3", email="f3@example.com", password="pass12345")
    client.force_login(user)

    response = client.post(reverse("feedback"), {"message": ""})
    assert response.status_code == 200
    assert Feedback.objects.count() == 0
