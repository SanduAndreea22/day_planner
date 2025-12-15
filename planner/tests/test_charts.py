import pytest
from django.urls import reverse
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_mood_chart(client, django_user_model):
    user = django_user_model.objects.create_user(username="user5", password="pass12345")
    client.login(username="user5", password="pass12345")
    url = reverse("mood_chart")
    response = client.get(url)
    assert response.status_code == 200
    assert "days" in response.context

@pytest.mark.django_db
def test_productivity_chart(client, django_user_model):
    user = django_user_model.objects.create_user(username="user6", password="pass12345")
    client.login(username="user6", password="pass12345")
    url = reverse("productivity_chart")
    response = client.get(url)
    assert response.status_code == 200
    assert "data" in response.context

