import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_privacy_policy_renders(client):
    response = client.get(reverse("privacy_policy"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_terms_renders(client):
    response = client.get(reverse("terms"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_guide_renders(client):
    response = client.get(reverse("guide"))
    assert response.status_code == 200
