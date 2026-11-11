import pytest
from datetime import date, timedelta
from django.urls import reverse
from planner.models import Day
from planner.views import MOOD_CHECKINS


@pytest.mark.django_db
def test_guest_home_renders_landing(client):
    response = client.get(reverse("home"))
    assert response.status_code == 200
    assert b"Create free account" in response.content


@pytest.mark.django_db
def test_member_home_shows_checkin_and_reflection(client, django_user_model):
    user = django_user_model.objects.create_user(username="u1", password="pass12345")
    client.force_login(user)
    response = client.get(reverse("home"))
    assert response.status_code == 200
    html = response.content.decode()
    assert "Welcome back to" in html
    assert "How are you feeling today?" in html
    assert "What is one thing you need more of today?" in html
    assert "You are allowed to take things one day at a time." in html
    assert reverse("set_day_mood") in html
    assert Day.objects.filter(user=user, date=date.today()).exists()


@pytest.mark.django_db
def test_every_checkin_maps_to_a_valid_mood(client, django_user_model):
    valid = dict(Day.MOOD_CHOICES)
    assert {m["value"] for m in MOOD_CHECKINS} <= set(valid)
    assert len(MOOD_CHECKINS) == 5


@pytest.mark.django_db
def test_checkin_posts_to_existing_mood_endpoint(client, django_user_model):
    user = django_user_model.objects.create_user(username="u2", password="pass12345")
    client.force_login(user)
    client.get(reverse("home"))
    day = Day.objects.get(user=user, date=date.today())
    response = client.post(reverse("set_day_mood"), {"day_id": day.id, "mood": "good"})
    assert response.status_code == 302
    day.refresh_from_db()
    assert day.mood == "good"
    assert b"is-selected" in client.get(reverse("home")).content


@pytest.mark.django_db
def test_progress_counts_only_own_recent_days(client, django_user_model):
    user = django_user_model.objects.create_user(username="u3", password="pass12345")
    other = django_user_model.objects.create_user(username="u4", password="pass12345")
    today = date.today()
    Day.objects.create(user=user, date=today - timedelta(days=1), mood="good", notes="a line")
    Day.objects.create(user=user, date=today - timedelta(days=2), mood="bad")
    Day.objects.create(user=other, date=today - timedelta(days=1), mood="good", notes="private")
    client.force_login(user)
    ctx = client.get(reverse("home")).context
    assert ctx["checkins_week"] == 2
    assert ctx["notes_days"] == 1
    assert ctx["mood_total"] == 2


@pytest.mark.django_db
def test_closed_day_has_no_mood_form(client, django_user_model):
    user = django_user_model.objects.create_user(username="u5", password="pass12345")
    Day.objects.create(user=user, date=date.today(), mood="good", is_closed=True)
    client.force_login(user)
    html = client.get(reverse("home")).content.decode()
    assert 'name="mood"' not in html


@pytest.mark.django_db
def test_home_shows_saved_quote_matching_mood(client, django_user_model):
    from planner.models import Quote
    Quote.objects.all().delete()
    Quote.objects.create(text="General kindness.", mood=None)
    Quote.objects.create(text="Hard days pass.", mood="very_bad")
    user = django_user_model.objects.create_user(username="q1", password="pass12345")
    client.force_login(user)
    assert "General kindness." in client.get(reverse("home")).content.decode()
    Day.objects.filter(user=user, date=date.today()).update(mood="very_bad")
    html = client.get(reverse("home")).content.decode()
    assert "Hard days pass." in html and "General kindness." not in html


@pytest.mark.django_db
def test_home_falls_back_without_quotes(client, django_user_model):
    from planner.models import Quote
    Quote.objects.all().delete()
    user = django_user_model.objects.create_user(username="q2", password="pass12345")
    client.force_login(user)
    assert client.get(reverse("home")).status_code == 200


@pytest.mark.django_db
def test_guest_landing_only_shows_general_quotes(client):
    from planner.models import Quote
    Quote.objects.all().delete()
    Quote.objects.create(text="General kindness.", mood=None)
    Quote.objects.create(text="Mood specific.", mood="good")
    for _ in range(5):
        html = client.get(reverse("home")).content.decode()
        assert "General kindness." in html and "Mood specific." not in html


@pytest.mark.django_db
def test_landing_shows_app_screenshot_and_trust_facts(client):
    html = client.get(reverse("home")).content.decode()
    assert "app-today.png" in html
    assert "No analytics or advertising trackers." in html
    assert reverse("privacy_policy") in html
