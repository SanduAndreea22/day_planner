import pytest
from django.urls import reverse
from datetime import date


@pytest.mark.django_db
def test_calendar_view(client, django_user_model):
    user = django_user_model.objects.create_user(username="user11", password="pass12345")
    client.force_login(user)

    url = reverse("calendar")
    response = client.get(url)
    assert response.status_code == 200

    today = date.today()
    days_in_month = response.context["days"]
    assert len(days_in_month) >= 28
