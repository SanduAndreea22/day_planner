import pytest
from django.urls import reverse
from datetime import date
from planner.models import Day, TimeBlock

@pytest.mark.django_db
def test_mood_chart_view(client, django_user_model):
    user = django_user_model.objects.create_user(username="user12", password="pass12345")
    client.force_login(user)
    Day.objects.create(user=user, date=date.today(), mood="good")

    url = reverse("mood_chart")
    response = client.get(url)
    assert response.status_code == 200
    assert "days" in response.context

@pytest.mark.django_db
def test_productivity_chart_view(client, django_user_model):
    user = django_user_model.objects.create_user(username="user13", password="pass12345")
    client.force_login(user)
    day = Day.objects.create(user=user, date=date.today())
    TimeBlock.objects.create(day=day, title="Task", completed=True)

    url = reverse("productivity_chart")
    response = client.get(url)
    assert response.status_code == 200
    data = response.context["data"]
    assert data[0]["completed"] == 1


