import pytest
from django.urls import reverse
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_monthly_overview(client, django_user_model):
    user = django_user_model.objects.create_user(username="user8", password="pass12345")
    client.login(username="user8", password="pass12345")
    url = reverse("monthly_overview")
    response = client.get(url)
    assert response.status_code == 200
    assert "days" in response.context
