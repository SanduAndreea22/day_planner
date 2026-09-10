import pytest
from django.urls import reverse
from datetime import date

from planner.models import Day, TimeBlock


@pytest.mark.django_db
def test_add_timeblock(client, django_user_model):
    user = django_user_model.objects.create_user(username="tbuser1", password="pass12345")
    client.force_login(user)
    day = Day.objects.create(user=user, date=date.today())

    response = client.post(reverse("add_timeblock"), {
        "day_id": day.id,
        "title": "Deep work",
        "start_time": "09:00",
        "end_time": "10:00",
    })

    assert response.status_code == 302
    assert TimeBlock.objects.filter(day=day, title="Deep work").exists()


@pytest.mark.django_db
def test_add_timeblock_rejects_overlap(client, django_user_model):
    user = django_user_model.objects.create_user(username="tbuser2", password="pass12345")
    client.force_login(user)
    day = Day.objects.create(user=user, date=date.today())
    TimeBlock.objects.create(day=day, title="Meeting", start_time="09:00", end_time="10:00")

    client.post(reverse("add_timeblock"), {
        "day_id": day.id,
        "title": "Call",
        "start_time": "09:30",
        "end_time": "11:00",
    })

    assert TimeBlock.objects.filter(day=day).count() == 1


@pytest.mark.django_db
def test_add_timeblock_rejects_invalid_time_range(client, django_user_model):
    user = django_user_model.objects.create_user(username="tbuser3", password="pass12345")
    client.force_login(user)
    day = Day.objects.create(user=user, date=date.today())

    client.post(reverse("add_timeblock"), {
        "day_id": day.id,
        "title": "Broken",
        "start_time": "10:00",
        "end_time": "09:00",
    })

    assert TimeBlock.objects.filter(day=day).count() == 0


@pytest.mark.django_db
def test_toggle_timeblock(client, django_user_model):
    user = django_user_model.objects.create_user(username="tbuser4", password="pass12345")
    client.force_login(user)
    day = Day.objects.create(user=user, date=date.today())
    block = TimeBlock.objects.create(day=day, title="Read", start_time="09:00", end_time="10:00")

    url = reverse("toggle_timeblock", args=[block.id])
    client.post(url)
    block.refresh_from_db()
    assert block.completed is True

    client.post(url)
    block.refresh_from_db()
    assert block.completed is False


@pytest.mark.django_db
def test_toggle_timeblock_requires_post(client, django_user_model):
    user = django_user_model.objects.create_user(username="tbuser5", password="pass12345")
    client.force_login(user)
    day = Day.objects.create(user=user, date=date.today())
    block = TimeBlock.objects.create(day=day, title="Read", start_time="09:00", end_time="10:00")

    response = client.get(reverse("toggle_timeblock", args=[block.id]))
    assert response.status_code == 405


@pytest.mark.django_db
def test_delete_timeblock(client, django_user_model):
    user = django_user_model.objects.create_user(username="tbuser6", password="pass12345")
    client.force_login(user)
    day = Day.objects.create(user=user, date=date.today())
    block = TimeBlock.objects.create(day=day, title="Read", start_time="09:00", end_time="10:00")

    client.post(reverse("delete_timeblock", args=[block.id]))

    assert not TimeBlock.objects.filter(id=block.id).exists()


@pytest.mark.django_db
def test_cannot_toggle_another_users_timeblock(client, django_user_model):
    owner = django_user_model.objects.create_user(username="tbuser7", password="pass12345")
    other = django_user_model.objects.create_user(username="tbuser8", password="pass12345")
    day = Day.objects.create(user=owner, date=date.today())
    block = TimeBlock.objects.create(day=day, title="Read", start_time="09:00", end_time="10:00")

    client.force_login(other)
    response = client.post(reverse("toggle_timeblock", args=[block.id]))

    assert response.status_code == 404
    block.refresh_from_db()
    assert block.completed is False
