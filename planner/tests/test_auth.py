import pytest
from django.urls import reverse
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_register_view(client):
    url = reverse("register")
    data = {
        "email": "test@example.com",
        "password1": "ParolaTare123!",
        "password2": "ParolaTare123!"
    }
    response = client.post(url, data)

    assert response.status_code == 302

    user = User.objects.filter(email="test@example.com").first()
    assert user is not None
    assert user.username.startswith("user_")
    assert user.is_active is True

@pytest.mark.django_db
def test_login_logout(client):
    # Creăm user
    user = User.objects.create_user(
        username="user1",
        email="user1@example.com",
        password="ParolaTare123!"
    )

    login_url = reverse("login")
    logout_url = reverse("logout")

    response = client.post(login_url, {"email": "user1@example.com", "password": "ParolaTare123!"})
    assert response.status_code == 302

    response = client.get(logout_url)
    assert response.status_code == 302

@pytest.mark.django_db
def test_profile_view(client):
    user = User.objects.create_user(
        username="user2",
        email="user2@example.com",
        password="ParolaTare123!"
    )
    client.force_login(user)

    url = reverse("profile")
    response = client.get(url)
    assert response.status_code == 200
    assert b"profile" in response.content
