import pytest
from django.urls import reverse
from datetime import date
from planner.models import Day

@pytest.mark.django_db
def test_monthly_overview_view(client, django_user_model):
    user = django_user_model.objects.create_user(username="user14", password="pass12345")
    client.force_login(user)

    today = date.today()
    Day.objects.create(user=user, date=today, mood="good")

    url = reverse("monthly_overview") + f"?year={today.year}&month={today.month}"
    response = client.get(url)
    assert response.status_code == 200
    assert "days" in response.context
    assert response.context["dominant_mood"] == "good"
