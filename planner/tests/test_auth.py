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


@pytest.mark.django_db
def test_register_lands_on_home(client):
    response = client.post(reverse("register"), {
        "email": "newbie@example.com",
        "password1": "ParolaTare123!",
        "password2": "ParolaTare123!",
    })
    assert response.status_code == 302
    assert response.url == reverse("home")


@pytest.mark.django_db
def test_login_lands_on_home(client):
    User.objects.create_user(username="user9", email="user9@example.com", password="ParolaTare123!")
    response = client.post(reverse("login"), {"email": "user9@example.com", "password": "ParolaTare123!"})
    assert response.status_code == 302
    assert response.url == reverse("home")
    assert client.get(reverse("today")).status_code == 302  # Today still reachable


@pytest.mark.django_db
def test_no_email_features_remain(client):
    """The app sends no email: no reset routes, no reminder endpoint, no forgot link."""
    for path in ("/password-reset/", "/password-reset/done/", "/reset/done/", "/tasks/send-evening-reminders/"):
        assert client.get(path).status_code == 404
    html = client.get(reverse("login")).content.decode()
    assert "password-reset" not in html


@pytest.mark.django_db
def test_profile_page_has_no_reminder_field(client, django_user_model):
    user = django_user_model.objects.create_user(username="np1", password="pass12345")
    client.force_login(user)
    html = client.get(reverse("profile")).content.decode()
    assert "evening_reminder_time" not in html
    assert "Evening reminder" not in html


@pytest.mark.django_db
def test_auth_error_messages_are_plain(client):
    User.objects.create_user(username="dup", email="dup@example.com", password="ParolaTare123!")
    r = client.post(reverse("register"), {"email": "dup@example.com", "password1": "ParolaTare123!", "password2": "ParolaTare123!"})
    assert "An account with this email already exists." in r.content.decode()
    r = client.post(reverse("register"), {"email": "new@example.com", "password1": "ParolaTare123!", "password2": "Different123!"})
    assert "The two passwords don’t match." in r.content.decode()
    r = client.post(reverse("login"), {"email": "dup@example.com", "password": "wrong"})
    html = r.content.decode()
    assert "Incorrect email or password." in html
    assert "💭" not in html and "🤍" not in html
