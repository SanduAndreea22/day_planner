import pytest
from django.urls import reverse
from datetime import date, timedelta, time
from planner.models import Day, TimeBlock

@pytest.mark.django_db
def test_weekly_balance_score_view(client, django_user_model):
    # Creăm user
    user = django_user_model.objects.create_user(username="user15", password="pass12345")
    client.force_login(user)

    today = date.today()

    # Creăm 3 zile cu stări și timeblocks
    for i in range(3):
        day = Day.objects.create(user=user, date=today - timedelta(days=i), mood="good")
        TimeBlock.objects.create(
            day=day,
            title=f"Task {i}",
            start_time=time(9+i, 0),  # start_time obligatoriu
            end_time=time(10+i, 0),   # end_time obligatoriu
            completed=True
        )

    # Folosim numele corect din urls.py: "weekly_score"
    url = reverse("weekly_score")
    response = client.get(url)

    # Verificăm statusul și datele din context
    assert response.status_code == 200
    assert response.context["days_logged"] == 3
    assert response.context["completed_tasks"] == 3

