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

    # A GET (e.g. an <img> on another site) must not log anyone out.
    response = client.get(logout_url)
    assert response.status_code == 302
    assert "_auth_user_id" in client.session

    response = client.post(logout_url)
    assert response.status_code == 302
    assert "_auth_user_id" not in client.session

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


@pytest.mark.django_db
def test_login_locks_after_repeated_failures_per_account(client):
    from django.core.cache import cache
    cache.clear()
    User.objects.create_user(username="lk", email="lk@example.com", password="ParolaTare123!")
    for i in range(10):
        # a different forged IP each time must not reset the per-account counter
        client.post(reverse("login"), {"email": "lk@example.com", "password": "bad"}, HTTP_X_FORWARDED_FOR=f"10.0.0.{i}")
    r = client.post(reverse("login"), {"email": "lk@example.com", "password": "ParolaTare123!"}, HTTP_X_FORWARDED_FOR="10.9.9.9", follow=True)
    assert "Too many failed attempts" in r.content.decode()
    cache.clear()


@pytest.mark.django_db
def test_logout_post_requires_csrf_token(django_user_model):
    from django.test import Client
    user = django_user_model.objects.create_user(username="csrf1", password="pass12345")
    strict = Client(enforce_csrf_checks=True)
    strict.force_login(user)
    assert strict.post(reverse("logout")).status_code == 403
    assert "_auth_user_id" in strict.session


@pytest.mark.django_db
def test_signed_in_pages_are_not_stored_by_browsers(client, django_user_model):
    user = django_user_model.objects.create_user(username="nc1", password="pass12345")
    assert "no-store" not in client.get(reverse("home")).get("Cache-Control", "")   # public landing
    client.force_login(user)
    cc = client.get(reverse("search"))["Cache-Control"]
    assert "no-store" in cc and "private" in cc


@pytest.mark.django_db
def test_register_rejects_password_similar_to_email(client):
    r = client.post(reverse("register"), {
        "email": "andreeasandu@example.com",
        "password1": "andreeasandu",
        "password2": "andreeasandu",
    })
    assert r.status_code == 200                      # re-rendered with errors, not redirected
    assert not User.objects.filter(email="andreeasandu@example.com").exists()
    assert "too similar" in r.content.decode()


@pytest.mark.django_db
def test_register_shows_every_password_problem(client):
    r = client.post(reverse("register"), {"email": "x1@example.com", "password1": "123", "password2": "123"})
    html = r.content.decode()
    assert "too short" in html and "entirely numeric" in html


@pytest.mark.django_db
def test_password_length_is_capped(client):
    r = client.post(reverse("register"), {"email": "long@example.com", "password1": "A1!" * 500, "password2": "A1!" * 500})
    assert r.status_code == 200
    assert not User.objects.filter(email="long@example.com").exists()
