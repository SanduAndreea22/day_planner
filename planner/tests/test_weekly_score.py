import pytest
from django.urls import reverse
from datetime import date, timedelta, time
from planner.models import Day, TimeBlock

@pytest.mark.django_db
def test_weekly_balance_score_view(client, django_user_model):
    user = django_user_model.objects.create_user(username="user15", password="pass12345")
    client.force_login(user)

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    for i in range(3):
        day = Day.objects.create(user=user, date=start_of_week + timedelta(days=i), mood="good")
        TimeBlock.objects.create(
            day=day,
            title=f"Task {i}",
            start_time=time(9+i, 0),
            end_time=time(10+i, 0),
            completed=True
        )

    url = reverse("weekly_score")
    response = client.get(url)

    assert response.status_code == 200
    assert response.context["days_logged"] == 3
    assert response.context["completed_tasks"] == 3
    assert response.context["mood_days"] == 3
    assert response.context["score"] > 0
    assert "message" in response.context

