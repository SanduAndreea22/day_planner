import pytest
from django.urls import reverse
from core.planner.models import Day, TimeBlock
from django.contrib.auth.models import User
from datetime import date


@pytest.mark.django_db
def test_day_detail_and_mood(client, django_user_model):
    user = django_user_model.objects.create_user(username="user2", password="pass12345")
    client.login(username="user2", password="pass12345")

    day = Day.objects.create(user=user, date=date.today())
    day_detail_url = reverse("day_detail", kwargs={"year": day.date.year, "month": day.date.month, "day": day.date.day})
    response = client.get(day_detail_url)
    assert response.status_code == 200
    assert "day" in response.context

    # set_day_mood
    set_mood_url = reverse("set_day_mood")
    response = client.post(set_mood_url, {"day_id": day.id, "mood": "good"})
    day.refresh_from_db()
    assert response.status_code == 302
    assert day.mood == "good"


@pytest.mark.django_db
def test_add_and_toggle_timeblock(client, django_user_model):
    user = django_user_model.objects.create_user(username="user3", password="pass12345")
    client.login(username="user3", password="pass12345")
    day = Day.objects.create(user=user, date=date.today())

    add_tb_url = reverse("add_timeblock")
    client.post(add_tb_url, {"day_id": day.id, "title": "Task", "start_time": "08:00", "end_time": "09:00"})
    assert day.time_blocks.count() == 1

    block = day.time_blocks.first()
    toggle_url = reverse("toggle_timeblock", kwargs={"block_id": block.id})
    client.get(toggle_url)
    block.refresh_from_db()
    assert block.completed is True
