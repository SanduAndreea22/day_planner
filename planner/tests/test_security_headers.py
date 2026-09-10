import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_content_security_policy_header_present(client):
    response = client.get(reverse("home"))
    assert "Content-Security-Policy" in response
    csp = response["Content-Security-Policy"]
    assert "default-src 'self'" in csp
    assert "https://cdn.jsdelivr.net" in csp
    assert "https://fonts.googleapis.com" in csp
