import csv
import hmac
import io
import zipfile
from collections import Counter
from datetime import date, datetime, timedelta
from calendar import monthrange
from random import choice
from types import SimpleNamespace
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import redirect, render, get_object_or_404
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Day, TimeBlock, Quote, EveningReflection, UserProfile, Feedback
from .forms import RegisterForm, EmailAuthenticationForm, TimeBlockForm, ProfileForm, FeedbackForm
from .decorators import ratelimit_post

HOME_PREVIEW_CARDS = [
    {"icon": "🌤", "title": "Today", "description": "Log a mood, a color, and a few gentle notes — whenever you feel like it."},
    {"icon": "📅", "title": "Calendar", "description": "See every day at a glance, colored by how it felt."},
    {"icon": "📈", "title": "Your Week", "description": "A gentle, non-judgmental summary of how balanced the week felt."},
]

MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}

def redirect_to_day(day):
    return redirect("day_detail", year=day.date.year, month=day.date.month, day=day.date.day)

def compute_streak(user):
    today = date.today()
    # A single query for a generous lookback window instead of one query per
    # day in the loop below — a year-plus streak used to mean hundreds of
    # individual round-trips to the database.
    cutoff = today - timedelta(days=400)
    days_by_date = {
        day.date: day
        for day in Day.objects.filter(user=user, date__gte=cutoff, date__lte=today)
    }

    streak = 0
    current = today
    while True:
        day = days_by_date.get(current)
        if day is None:
            break
        if not (day.mood or day.color or day.notes or day.is_closed):
            break
        streak += 1
        current -= timedelta(days=1)
    return streak

def _random_quote(queryset):
    # Picks a random id in Python instead of ORDER BY RANDOM(), which sorts
    # the whole matching set at the database for every call.
    quote_ids = list(queryset.values_list("id", flat=True))
    if not quote_ids:
        return None
    return Quote.objects.get(id=choice(quote_ids))


def assign_closing_quote(day_obj):
    if day_obj.closing_quote:
        return
    quotes = Quote.objects.filter(active=True)
    if day_obj.mood:
        mood_quotes = quotes.filter(mood=day_obj.mood)
        if mood_quotes.exists():
            quotes = mood_quotes
    day_obj.closing_quote = _random_quote(quotes)

def get_month_year(request):
    today = date.today()
    try:
        year = int(request.GET.get("year", today.year))
    except (TypeError, ValueError):
        year = today.year
    try:
        month = int(request.GET.get("month", today.month))
    except (TypeError, ValueError):
        month = today.month
    if not (1 <= month <= 12):
        month = today.month
    return year, month

def get_week_range(request):
    today = date.today()
    try:
        offset = int(request.GET.get("offset", 0))
    except (TypeError, ValueError):
        offset = 0
    start = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
    end = start + timedelta(days=6)

    return start, end, offset


@ratelimit_post('register', limit=5, period_seconds=3600)
def register_view(request):
    if request.user.is_authenticated:
        return redirect("today")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("today")

    return render(request, "planner/auth/register.html", {"form": form})

@ratelimit_post('login', limit=10, period_seconds=300)
def login_view(request):
    if request.user.is_authenticated:
        return redirect("today")

    form = EmailAuthenticationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("today")

    return render(request, "planner/auth/login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("home")

@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    saved = False
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            saved = True
    else:
        form = ProfileForm(instance=profile)
    return render(request, "planner/auth/profile.html", {"profile": profile, "form": form, "saved": saved})

@login_required
def feedback_view(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            messages.success(request, "Thank you — your feedback was sent 🤍")
            return redirect("feedback")
    else:
        form = FeedbackForm()
    return render(request, "planner/feedback.html", {"form": form})

@login_required
@ratelimit_post('delete_account', limit=5, period_seconds=3600)
def delete_account_view(request):
    if request.method == "POST":
        password = request.POST.get("password", "")
        if request.user.check_password(password):
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, "Your account and all your data have been permanently deleted. Take care 🤍")
            return redirect("home")
        messages.error(request, "Incorrect password — your account was not deleted.")
        return redirect("delete_account")
    return render(request, "planner/auth/delete_account.html")

def home_view(request):
    if request.user.is_authenticated:
        return redirect("today")

    quote = _random_quote(Quote.objects.filter(active=True))
    return render(request, "planner/home.html", {
        "quote": quote,
        "today": date.today(),
        "preview_cards": HOME_PREVIEW_CARDS,
    })

@login_required
def today_view(request):
    today = date.today()
    return redirect("day_detail", year=today.year, month=today.month, day=today.day)

@login_required
def day_detail_view(request, year, month, day):
    try:
        selected_date = date(year, month, day)
    except ValueError:
        raise Http404("Invalid date")
    day_obj, _ = Day.objects.get_or_create(user=request.user, date=selected_date)

    message = None
    if selected_date < date.today():
        message = "Past day. You can reflect at your own pace 🤍"
    elif selected_date > date.today():
        message = "Future day. It doesn't need to be clear yet ✨"

    reflection = EveningReflection.objects.filter(day=day_obj).first()
    streak = compute_streak(request.user) if selected_date == date.today() else None

    return render(request, "planner/day.html", {
        "day": day_obj,
        "time_blocks": day_obj.time_blocks.all(),
        "message": message,
        "quote": day_obj.closing_quote,
        "reflection": reflection,
        "streak": streak,
    })

@login_required
def evening_reflection_view(request, year, month, day):
    try:
        selected_date = date(year, month, day)
    except ValueError:
        raise Http404("Invalid date")
    day_obj = get_object_or_404(Day, user=request.user, date=selected_date)
    if day_obj.is_closed:
        return redirect_to_day(day_obj)
    reflection, _ = EveningReflection.objects.get_or_create(day=day_obj)

    if request.method == "POST":
        mood = request.POST.get("mood")
        color = request.POST.get("color")
        day_obj.mood = mood[:20] if mood else day_obj.mood
        day_obj.color = color[:20] if color else day_obj.color
        day_obj.notes = request.POST.get("notes", day_obj.notes)
        day_obj.save(update_fields=["mood", "color", "notes"])

        reflection.drain = request.POST.get("drain", "")
        reflection.small_win = request.POST.get("small_win", "")
        reflection.save()

        assign_closing_quote(day_obj)

        day_obj.is_closed = True
        day_obj.closed_at = timezone.now()
        day_obj.save(update_fields=["is_closed", "closed_at", "closing_quote"])

        return redirect_to_day(day_obj)

    return render(request, "planner/evening.html", {"day": day_obj, "reflection": reflection})

@login_required
def set_day_color(request):
    if request.method != "POST":
        return redirect("today")
    day = get_object_or_404(Day, id=request.POST.get("day_id"), user=request.user)
    color = request.POST.get("color")
    if color and color not in dict(Day.COLOR_CHOICES):
        messages.error(request, "That's not a valid color option.")
        return redirect_to_day(day)
    if color:
        updated = Day.objects.filter(id=day.id, is_closed=False).update(color=color)
        if updated:
            messages.success(request, "Saved 🎨")
    return redirect_to_day(day)


@login_required
def set_day_mood(request):
    if request.method != "POST":
        return redirect("today")
    day = get_object_or_404(Day, id=request.POST.get("day_id"), user=request.user)
    mood = request.POST.get("mood")
    if mood and mood not in dict(Day.MOOD_CHOICES):
        messages.error(request, "That's not a valid mood option.")
        return redirect_to_day(day)
    if mood:
        updated = Day.objects.filter(id=day.id, is_closed=False).update(mood=mood)
        if updated:
            messages.success(request, "Saved 😌")
    return redirect_to_day(day)


@login_required
def update_day_text(request):
    day = get_object_or_404(Day, id=request.POST.get("day_id"), user=request.user)
    if not day.is_closed:
        day.notes = request.POST.get("notes", "")
        day.save(update_fields=["notes"])
    return redirect_to_day(day)


@login_required
def add_timeblock(request):
    day = get_object_or_404(Day, id=request.POST.get("day_id"), user=request.user)
    form = TimeBlockForm(request.POST)
    if form.is_valid():
        start_time = form.cleaned_data["start_time"]
        end_time = form.cleaned_data["end_time"]
        overlaps = day.time_blocks.filter(
            start_time__lt=end_time, end_time__gt=start_time
        ).exists()
        if overlaps:
            messages.error(request, "That overlaps with a block you already have that day.")
        else:
            block = form.save(commit=False)
            block.day = day
            block.save()
    else:
        for error in form.non_field_errors():
            messages.error(request, error)
        for field, errors in form.errors.items():
            if field == "__all__":
                continue
            label = form[field].label
            for error in errors:
                text = str(error)
                text = text[0].lower() + text[1:] if text else text
                messages.error(request, f"{label} — {text}")
    return redirect_to_day(day)


@login_required
@require_POST
def toggle_timeblock(request, block_id):
    block = get_object_or_404(TimeBlock, id=block_id, day__user=request.user)
    block.completed = not block.completed
    block.save(update_fields=["completed"])
    return redirect_to_day(block.day)


@login_required
@require_POST
def delete_timeblock(request, block_id):
    block = get_object_or_404(TimeBlock, id=block_id, day__user=request.user)
    day = block.day
    block.delete()
    return redirect_to_day(day)

@login_required
def calendar_view(request, year=None, month=None):
    today = date.today()
    year = year if year is not None else today.year
    month = month if month is not None else today.month

    if not (1 <= month <= 12) or not (1 <= year <= 9999):
        raise Http404("Invalid calendar month")

    if year < 2025 or (year == 2025 and month < 11):
        year, month = 2025, 11

    first_weekday, total_days = monthrange(year, month)
    start_day = (first_weekday + 1) % 7
    existing_days = {d.date: d for d in Day.objects.filter(user=request.user, date__year=year, date__month=month)}

    days = []
    for _ in range(start_day):
        days.append({
            "date": None,
            "day": None,
            "is_today": False,
            "is_future": False,
        })

    for day_num in range(1, total_days + 1):
        current = date(year, month, day_num)
        day_obj = existing_days.get(current)
        if not day_obj:
            day_obj = SimpleNamespace(mood=None, notes="", color=None)

        days.append({
            "date": current,
            "day": day_obj,
            "is_today": current == today,
            "is_future": current > today,
        })

    prev_month, prev_year = month - 1, year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    next_month, next_year = month + 1, year
    if next_month == 13:
        next_month = 1
        next_year += 1

    return render(request, "planner/calendar.html", {
        "year": year,
        "month": month,
        "days": days,
        "prev_month": prev_month,
        "prev_year": prev_year,
        "next_month": next_month,
        "next_year": next_year,
        "today": today,
    })

@login_required
def weekly_balance_score_view(request):
    start, end, offset = get_week_range(request)
    days = list(Day.objects.filter(user=request.user, date__range=[start, end]))
    days_logged = len(days)
    mood_days = sum(bool(d.mood) for d in days)
    completed_tasks = TimeBlock.objects.filter(day__in=days, completed=True).count()

    score = min(days_logged * 10 + mood_days * 8 + completed_tasks * 2, 100)

    if score < 30:
        message, emoji = "It was tough. It's enough that you were here.", "🫶"
    elif score < 70:
        message, emoji = "You had some balanced moments. It's okay.", "🌿"
    else:
        message, emoji = "A week with good resources.", "💗"

    if days_logged == 0:
        suggestion = "Maybe next week starts with just one logged day."
    elif days_logged < 3:
        suggestion = "Next time, add a small thought."
    else:
        suggestion = "Keep going at your own pace."

    return render(request, "planner/weekly_score.html", {
        "score": score,
        "message": message,
        "emoji": emoji,
        "suggestion": suggestion,
        "days_logged": days_logged,
        "completed_tasks": completed_tasks,
        "mood_days": mood_days,
        "start": start,
        "end": end,
        "offset": offset,
    })

@login_required
def monthly_overview_view(request):
    year, month = get_month_year(request)

    # Build the full month grid (leading blanks + every day, whether or not
    # it has a Day row), the same way calendar_view does — this used to only
    # loop over logged days, so any day without a row was simply missing
    # from the grid instead of showing as an empty cell in the right place.
    first_weekday, days_in_month = monthrange(year, month)
    start_offset = (first_weekday + 1) % 7
    logged_days = list(
        Day.objects.filter(user=request.user, date__year=year, date__month=month).order_by("date")
    )
    logged_by_date = {d.date: d for d in logged_days}

    days = [None] * start_offset
    for day_num in range(1, days_in_month + 1):
        current = date(year, month, day_num)
        days.append(logged_by_date.get(current) or SimpleNamespace(date=current, mood=None, color=None, notes=""))

    moods = [d.mood for d in logged_days if d.mood]
    dominant_mood = Counter(moods).most_common(1)[0][0] if moods else None

    interpretation_map = {
        "very_bad": ("🌧️", "The month was challenging."),
        "bad": ("🌥️", "There were several tough days."),
        "neutral": ("🌤️", "A stable month, no extremes."),
        "good": ("🌱", "You had several good days."),
        "very_good": ("🌸", "A month with nice emotional resources."),
        None: ("🌙", "Every day counts, even the unwritten ones."),
    }

    icon, interpretation = interpretation_map.get(dominant_mood, ("🌙", "Every day counts, even the unwritten ones."))

    return render(request, "planner/monthly_overview.html", {
        "days": days,
        "year": year,
        "month": month,
        "month_name": MONTH_NAMES[month],
        "dominant_mood": dominant_mood,
        "icon": icon,
        "interpretation": interpretation,
        "total_days": len(logged_days),
    })



@login_required
def mood_chart_view(request):
    year, month = get_month_year(request)
    days = Day.objects.filter(user=request.user, date__year=year, date__month=month).order_by("date")
    moods = [d.mood for d in days if d.mood]
    most_common_mood = Counter(moods).most_common(1)[0][0] if moods else None

    return render(request, "planner/chart/mood.html", {
        "days": days,
        "year": year,
        "month": month,
        "month_name": MONTH_NAMES[month],
        "most_common_mood": most_common_mood,
    })


@login_required
def productivity_chart_view(request):
    start, end, offset = get_week_range(request)

    days = Day.objects.filter(user=request.user, date__range=(start, end)).order_by("date")
    data = [{"date": d.date.strftime("%d %b"), "completed": d.time_blocks.filter(completed=True).count(), "mood": d.mood or "none"} for d in days]

    return render(request, "planner/chart/productivity.html", {"data": data, "start": start, "end": end, "offset": offset})


@login_required
def search_view(request):
    query = request.GET.get("q", "").strip()
    mood_filter = request.GET.get("mood", "")

    days = Day.objects.filter(user=request.user)
    if query:
        days = days.filter(notes__icontains=query)
    if mood_filter:
        days = days.filter(mood=mood_filter)
    days = days.order_by("-date")[:100]

    return render(request, "planner/search.html", {
        "days": days,
        "query": query,
        "mood_filter": mood_filter,
    })


def _rows_to_csv(header, rows):
    csv_file = io.StringIO()
    writer = csv.writer(csv_file)
    writer.writerow(header)
    writer.writerows(rows)
    return csv_file.getvalue()


@login_required
def export_data_view(request):
    user = request.user

    days_csv = _rows_to_csv(
        ["date", "mood", "color", "notes", "rest_day", "is_closed", "closed_at"],
        (
            [d.date, d.mood, d.color, d.notes, d.rest_day, d.is_closed, d.closed_at]
            for d in Day.objects.filter(user=user).order_by("date")
        ),
    )

    blocks_csv = _rows_to_csv(
        ["date", "title", "start_time", "end_time", "completed"],
        (
            [block.day.date, block.title, block.start_time, block.end_time, block.completed]
            for block in TimeBlock.objects.filter(day__user=user).select_related("day").order_by("day__date", "start_time")
        ),
    )

    reflections_csv = _rows_to_csv(
        ["date", "drain", "small_win"],
        (
            [r.day.date, r.drain, r.small_win]
            for r in EveningReflection.objects.filter(day__user=user).select_related("day").order_by("day__date")
        ),
    )

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("days.csv", days_csv)
        zf.writestr("time_blocks.csv", blocks_csv)
        zf.writestr("reflections.csv", reflections_csv)

    response = HttpResponse(buffer.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = 'attachment; filename="emotional_planner_export.zip"'
    return response


@csrf_exempt
@require_POST
def send_evening_reminders_view(request):
    expected = f"Bearer {settings.TASK_SECRET}"
    provided = request.META.get("HTTP_AUTHORIZATION", "")
    if not settings.TASK_SECRET or not hmac.compare_digest(provided, expected):
        return HttpResponseForbidden("Forbidden")

    window_end = timezone.localtime()
    window_start = window_end - timedelta(minutes=15)

    profiles = UserProfile.objects.exclude(evening_reminder_time__isnull=True).select_related("user")
    matching_profiles = []
    for profile in profiles:
        reminder_time = profile.evening_reminder_time
        # Combine against both the window's start and end date, since a
        # window spanning midnight (e.g. 23:45-00:00) would otherwise miss a
        # reminder time that falls on the earlier day. The start is
        # exclusive / end inclusive so consecutive 15-minute cron runs never
        # both match the same reminder time.
        reminder_candidates = {
            timezone.make_aware(datetime.combine(d, reminder_time), window_end.tzinfo)
            for d in (window_start.date(), window_end.date())
        }
        if any(window_start < candidate <= window_end for candidate in reminder_candidates):
            matching_profiles.append(profile)

    # One query for all matching users' today-Days instead of one per profile.
    closed_user_ids = set(
        Day.objects.filter(
            user_id__in=[p.user_id for p in matching_profiles],
            date=window_end.date(),
            is_closed=True,
        ).values_list("user_id", flat=True)
    )

    sent = 0
    for profile in matching_profiles:
        if profile.user_id in closed_user_ids:
            continue
        # Guards against two overlapping cron runs (a retried/delayed
        # GitHub Actions call landing next to a fresh one) both matching the
        # same window for the same profile and double-sending.
        if profile.last_evening_reminder_sent_at and profile.last_evening_reminder_sent_at > window_start:
            continue

        sent_count = send_mail(
            subject="🌙 A gentle nudge for your evening reflection",
            message=(
                "No pressure — whenever you're ready, your day is waiting for you.\n\n"
                + request.build_absolute_uri(reverse("today"))
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[profile.user.email],
            fail_silently=True,
        )
        if sent_count:
            sent += 1
            profile.last_evening_reminder_sent_at = window_end
            profile.save(update_fields=["last_evening_reminder_sent_at"])

    return HttpResponse(f"Sent {sent} reminder(s).")
