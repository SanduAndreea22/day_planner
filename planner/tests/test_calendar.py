import pytest
from django.urls import reverse
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_calendar_view(client, django_user_model):
    user = django_user_model.objects.create_user(username="user4", password="pass12345")
    client.login(username="user4", password="pass12345")
    url = reverse("calendar")
    response = client.get(url)
    assert response.status_code == 200
    assert "days" in response.context
