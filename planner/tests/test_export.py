import io
import zipfile
from datetime import date, time

import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from planner.models import Day, TimeBlock, EveningReflection


@pytest.mark.django_db
def test_export_requires_login(client):
    response = client.get(reverse("export_data"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_export_contains_only_own_data(client):
    owner = User.objects.create_user(username="e1", email="e1@example.com", password="pass12345")
    other = User.objects.create_user(username="e2", email="e2@example.com", password="pass12345")
    client.force_login(owner)

    day = Day.objects.create(user=owner, date=date.today(), notes="my note")
    TimeBlock.objects.create(day=day, title="Focus", start_time=time(9, 0), end_time=time(10, 0))
    EveningReflection.objects.create(day=day, drain="tired", small_win="showed up")

    other_day = Day.objects.create(user=other, date=date.today(), notes="someone else's note")

    response = client.get(reverse("export_data"))
    assert response.status_code == 200
    assert response["Content-Type"] == "application/zip"

    zf = zipfile.ZipFile(io.BytesIO(response.content))
    names = zf.namelist()
    assert set(names) == {"days.csv", "time_blocks.csv", "reflections.csv"}

    days_csv = zf.read("days.csv").decode()
    assert "my note" in days_csv
    assert "someone else's note" not in days_csv

    blocks_csv = zf.read("time_blocks.csv").decode()
    assert "Focus" in blocks_csv

    reflections_csv = zf.read("reflections.csv").decode()
    assert "tired" in reflections_csv
    assert "showed up" in reflections_csv
