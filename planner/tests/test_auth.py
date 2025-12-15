import pytest
from django.urls import reverse
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_register_view(client):
    url = reverse("register")
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password1": "ParolaTare123!",
        "password2": "ParolaTare123!"
    }
    response = client.post(url, data)
    assert response.status_code == 302
    assert User.objects.filter(username="testuser").exists()

@pytest.mark.django_db
def test_login_logout(client, django_user_model):
    user = django_user_model.objects.create_user(username="user1", password="pass12345")
    login_url = reverse("login")
    logout_url = reverse("logout")

    # login
    response = client.post(login_url, {"username": "user1", "password": "pass12345"})
    assert response.status_code == 302

    # logout
    response = client.get(logout_url)
    assert response.status_code == 302
