import pytest
from django.urls import reverse
from datetime import date, timedelta
from planner.models import Day, TimeBlock

@pytest.mark.django_db
def test_weekly_balance_score_view(client, django_user_model):
    user = django_user_model.objects.create_user(username="user15", password="pass12345")
    client.force_login(user)

    today = date.today()
    # creăm 3 zile cu stări și timeblocks
    for i in range(3):
        day = Day.objects.create(user=user, date=today - timedelta(days=i), mood="good")
        TimeBlock.objects.create(day=day, title=f"Task {i}", completed=True)

    url = reverse("weekly_balance_score")
    response = client.get(url)
    assert response.status_code == 200
    assert response.context["days_logged"] == 3
    assert response.context["completed_tasks"] == 3
