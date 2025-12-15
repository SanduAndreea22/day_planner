import pytest
from django.urls import reverse
from django.contrib.auth.models import User

@pytest.mark.django_db
def test_weekly_balance_score(client, django_user_model):
    user = django_user_model.objects.create_user(username="user7", password="pass12345")
    client.login(username="user7", password="pass12345")
    url = reverse("weekly_score")
    response = client.get(url)
    assert response.status_code == 200
    assert "score" in response.context
