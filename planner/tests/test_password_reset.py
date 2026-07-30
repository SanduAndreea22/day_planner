import re

import pytest
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse


@pytest.mark.django_db
def test_password_reset_view_renders(client):
    response = client.get(reverse("password_reset"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_password_reset_sends_email_and_updates_password(client):
    user = User.objects.create_user(
        username="user8",
        email="user8@example.com",
        password="OldPassword123!"
    )

    response = client.post(reverse("password_reset"), {"email": "user8@example.com"})
    assert response.status_code == 302
    assert response.url == reverse("password_reset_done")

    assert len(mail.outbox) == 1
    match = re.search(r"/reset/\S+", mail.outbox[0].body)
    assert match is not None
    reset_path = match.group(0)

    # first GET stores the real token in the session and redirects to the
    # same URL with the token replaced by "set-password"
    response = client.get(reset_path)
    assert response.status_code == 302
    confirm_path = response.url

    response = client.get(confirm_path)
    assert response.status_code == 200
    assert response.context["validlink"] is True

    response = client.post(confirm_path, {
        "new_password1": "NewPassword456!",
        "new_password2": "NewPassword456!",
    })
    assert response.status_code == 302
    assert response.url == reverse("password_reset_complete")

    user.refresh_from_db()
    assert user.check_password("NewPassword456!")


@pytest.mark.django_db
def test_password_reset_unknown_email_does_not_error_or_send_mail(client):
    response = client.post(reverse("password_reset"), {"email": "nobody@example.com"})
    assert response.status_code == 302
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_password_reset_confirm_rejects_invalid_token(client):
    user = User.objects.create_user(
        username="user9",
        email="user9@example.com",
        password="OldPassword123!"
    )
    from django.utils.http import urlsafe_base64_encode
    from django.utils.encoding import force_bytes

    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    bad_path = reverse("password_reset_confirm", kwargs={"uidb64": uidb64, "token": "bad-token"})

    response = client.get(bad_path)
    assert response.status_code == 200
    assert response.context["validlink"] is False
