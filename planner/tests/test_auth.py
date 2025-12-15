import pytest
from django.urls import reverse
from django.contrib.auth.models import User
from planner.models import UserProfile

@pytest.mark.django_db
def test_register_view(client):
    url = reverse("register")
    data = {
        "email": "test@example.com",
        "password1": "ParolaTare123!",
        "password2": "ParolaTare123!"
    }
    response = client.post(url, data)
    
    # Verificăm redirect după post
    assert response.status_code == 302
    
    # Verificăm că userul s-a creat
    user = User.objects.filter(email="test@example.com").first()
    assert user is not None
    assert user.username.startswith("user_")
    # Contul este inactiv până la confirmarea emailului
    assert user.is_active is False

@pytest.mark.django_db
def test_login_logout(client, django_user_model):
    # Creăm user activ pentru login
    user = django_user_model.objects.create_user(
        username="user1",
        email="user1@example.com",
        password="pass12345",
        is_active=True
    )

    login_url = reverse("login")
    logout_url = reverse("logout")

    # Login cu email
    response = client.post(login_url, {"email": "user1@example.com", "password": "pass12345"})
    assert response.status_code == 302  # redirect către 'today'

    # Logout
    response = client.get(logout_url)
    assert response.status_code == 302  # redirect către 'home'

@pytest.mark.django_db
def test_profile_view(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="user2",
        email="user2@example.com",
        password="pass12345",
        is_active=True
    )
    client.force_login(user)

    url = reverse("profile")
    response = client.get(url)
    assert response.status_code == 200
    assert "profile" in response.context

    # Test POST update
    response = client.post(url, {"nickname": "Andy", "bio": "Salut!"})
    assert response.status_code == 200
    profile = UserProfile.objects.get(user=user)
    assert profile.nickname == "Andy"
    assert profile.bio == "Salut!"
