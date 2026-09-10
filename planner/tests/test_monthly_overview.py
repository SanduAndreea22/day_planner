import calendar

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


@pytest.mark.django_db
def test_monthly_overview_grid_covers_every_day_of_the_month(client, django_user_model):
    # Regression test: the grid used to only include days that already had a
    # Day row, so most of the month rendered as a blank/misaligned grid.
    user = django_user_model.objects.create_user(username="user15", password="pass12345")
    client.force_login(user)

    today = date.today()
    Day.objects.create(user=user, date=today, mood="good")

    url = reverse("monthly_overview") + f"?year={today.year}&month={today.month}"
    response = client.get(url)

    days_in_month = calendar.monthrange(today.year, today.month)[1]
    rendered_dates = [d.date for d in response.context["days"] if d is not None]

    assert len(rendered_dates) == days_in_month
    assert rendered_dates == sorted(rendered_dates)
    assert today in rendered_dates
    assert response.context["total_days"] == 1
