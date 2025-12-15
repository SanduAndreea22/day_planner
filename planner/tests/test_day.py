import pytest
from django.urls import reverse
from datetime import date
from planner.models import Day

@pytest.mark.django_db
def test_today_redirect(client, django_user_model):
    user = django_user_model.objects.create_user(username="user3", password="pass12345")
    client.force_login(user)
    url = reverse("today")
    response = client.get(url)
    assert response.status_code == 302

@pytest.mark.django_db
def test_day_detail_view(client, django_user_model):
    user = django_user_model.objects.create_user(username="user4", password="pass12345")
    client.force_login(user)
    today = date.today()
    url = reverse("day_detail", args=[today.year, today.month, today.day])
    response = client.get(url)
    assert response.status_code == 200
    assert Day.objects.filter(user=user, date=today).exists()

@pytest.mark.django_db
def test_set_day_color(client, django_user_model):
    user = django_user_model.objects.create_user(username="user5", password="pass12345")
    client.force_login(user)
    day = Day.objects.create(user=user, date=date.today())
    url = reverse("set_day_color")
    response = client.post(url, {"day_id": day.id, "color": "#ff0000"})
    day.refresh_from_db()
    assert day.color == "#ff0000"

@pytest.mark.django_db
def test_set_day_mood(client, django_user_model):
    user = django_user_model.objects.create_user(username="user6", password="pass12345")
    client.force_login(user)
    day = Day.objects.create(user=user, date=date.today())
    url = reverse("set_day_mood")
    response = client.post(url, {"day_id": day.id, "mood": "good"})
    day.refresh_from_db()
    assert day.mood == "good"

@pytest.mark.django_db
def test_update_day_text(client, django_user_model):
    user = django_user_model.objects.create_user(username="user7", password="pass12345")
    client.force_login(user)
    day = Day.objects.create(user=user, date=date.today())
    url = reverse("update_day_text")
    response = client.post(url, {"day_id": day.id, "notes": "Some notes"})
    day.refresh_from_db()
    assert day.notes == "Some notes"

