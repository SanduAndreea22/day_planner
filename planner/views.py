import csv
import io
import zipfile
from collections import Counter
from datetime import date, timedelta
from calendar import monthrange
from random import choice
from types import SimpleNamespace
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render, get_object_or_404
from django.http import Http404, HttpResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Day, TimeBlock, Quote, EveningReflection, UserProfile, Feedback
from .forms import RegisterForm, EmailAuthenticationForm, TimeBlockForm, ProfileForm, FeedbackForm
from .decorators import ratelimit_post

HOME_PREVIEW_CARDS = [
    {"icon": "🌤", "title": "Today", "description": "Pick a mood, write a journal entry, and plan the day in time blocks: slots like 09:00 – 10:00 · Study."},
    {"icon": "🌙", "title": "Evening reflection", "description": "Close the day with two optional questions: what drained you, and one small thing you appreciate. Closing locks the day, so it can't be edited afterward."},
    {"icon": "📅", "title": "Calendar", "description": "A month at a glance. Each day shows the mood you picked as an emoji, tinted with the day's color. Tap a day to open it."},
    {"icon": "📈", "title": "Your week", "description": "See which days you checked in and how many time blocks you finished. No ranking."},
]

# The home check-in offers five emotions, but the existing Day.mood field is a
# five-step scale (very_bad..very_good). Until a dedicated emotion field exists
# (see README / hand-off notes), each emotion is saved to the nearest existing
# step so the current charts, calendar and weekly view keep working unchanged.
MOOD_CHECKINS = [
    {"key": "happy", "label": "Happy", "value": "very_good"},
    {"key": "calm", "label": "Calm", "value": "good"},
    {"key": "tired", "label": "Tired", "value": "neutral"},
    {"key": "anxious", "label": "Anxious", "value": "bad"},
    {"key": "sad", "label": "Sad", "value": "very_bad"},
]

DAILY_MESSAGES = [
    "Small, honest moments are enough to begin with.",
    "Notice one thing that feels softer than yesterday.",
    "Rest is not the opposite of progress. It is part of it.",
    "Whatever you feel today is allowed to be here.",
    "Be as kind to yourself as you would be to a friend.",
    "A few quiet lines can change how a day is remembered.",
    "You don't need a perfect plan to take a gentle step.",
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
        return redirect("home")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("home")

    return render(request, "planner/auth/register.html", {"form": form})

@ratelimit_post('login', limit=10, period_seconds=300)
def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = EmailAuthenticationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("home")

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
            messages.success(request, "Thank you. Your feedback was sent.")
            return redirect("feedback")
    else:
        form = FeedbackForm()
    return render(request, "planner/feedback.html", {"form": form})

@login_required
@ratelimit_post('delete_account', limit=5, period_seconds=3600)
def delete_account_view(request):
    if request.method == "POST":
        password = request.POST.get("password", "")
        confirm_text = request.POST.get("confirm_text", "").strip().upper()
        if confirm_text != "DELETE":
            messages.error(request, "Type DELETE to confirm — your account was not deleted.")
            return redirect("delete_account")
        if request.user.check_password(password):
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, "Your account and all your data have been permanently deleted.")
            return redirect("home")
        messages.error(request, "Incorrect password — your account was not deleted.")
        return redirect("delete_account")
    return render(request, "planner/auth/delete_account.html")

def _daily_quote_text(day_obj, today):
    """A saved encouragement for today, stable across refreshes.

    Matches today's mood when one is set, otherwise uses the general quotes
    (no mood). Falls back to the built-in daily messages if none are saved.
    """
    quotes = Quote.objects.filter(active=True)
    if day_obj.mood:
        matched = quotes.filter(mood=day_obj.mood)
        if matched.exists():
            quotes = matched
    else:
        general = quotes.filter(mood__isnull=True) | quotes.filter(mood="")
        if general.exists():
            quotes = general
    ids = sorted(quotes.values_list("id", flat=True))
    if ids:
        return Quote.objects.get(id=ids[today.toordinal() % len(ids)]).text
    return DAILY_MESSAGES[today.toordinal() % len(DAILY_MESSAGES)]


def build_home_context(user, today):
    """Everything the signed-in home page shows, from existing Day data only.

    Deliberately no scores, streaks or targets: just a calm reflection of what
    the user has already recorded.
    """
    day_obj, _ = Day.objects.get_or_create(user=user, date=today)
    mood_labels = dict(Day.MOOD_CHOICES)
    recent = list(
        Day.objects.filter(user=user, date__gt=today - timedelta(days=30), date__lte=today)
    )
    by_date = {d.date: d for d in recent}

    week_start = today - timedelta(days=6)
    checkins_week = sum(1 for d in recent if d.mood and d.date >= week_start)
    notes_days = sum(1 for d in recent if d.notes.strip())

    # Last 14 days, oldest first, for the mood-pattern strip.
    strip = []
    for offset in range(13, -1, -1):
        d = today - timedelta(days=offset)
        entry = by_date.get(d)
        strip.append({
            "date": d,
            "mood": entry.mood if entry and entry.mood else "",
            "label": mood_labels.get(entry.mood, "") if entry and entry.mood else "",
            "is_today": d == today,
        })

    counts = Counter(d.mood for d in recent if d.mood)
    total = sum(counts.values())
    patterns = [
        {
            "value": value,
            "label": label,
            "count": counts.get(value, 0),
            "percent": round(counts.get(value, 0) * 100 / total) if total else 0,
        }
        for value, label in reversed(Day.MOOD_CHOICES)
    ]

    latest = sorted((d for d in recent if d.mood), key=lambda d: d.date, reverse=True)[:3]

    # "Welcome back" only makes sense once there is something to come back to.
    has_history = Day.objects.filter(user=user).exclude(
        (Q(mood__isnull=True) | Q(mood="")) & Q(notes="") & Q(is_closed=False)
    ).exists()

    return {
        "is_first_visit": not has_history,
        "day": day_obj,
        "today": today,
        "daily_message": _daily_quote_text(day_obj, today),
        "mood_checkins": MOOD_CHECKINS,
        "current_mood_label": mood_labels.get(day_obj.mood, ""),
        "current_checkin_label": {m["value"]: m["label"] for m in MOOD_CHECKINS}.get(day_obj.mood, ""),
        "checkins_week": checkins_week,
        "notes_days": notes_days,
        "mood_strip": strip,
        "mood_patterns": patterns,
        "mood_total": total,
        "latest_checkins": [
            {"date": d.date, "mood": d.mood, "label": mood_labels[d.mood]} for d in latest
        ],
        "nickname": getattr(getattr(user, "profile", None), "nickname", ""),
    }


def demo_view(request):
    """Try the daily check-in without an account.

    Read-only: it only reads the saved quotes. Nothing the visitor does on the
    page is sent to or stored on the server (all interaction is client-side).
    """
    active = Quote.objects.filter(active=True)
    general = list(active.filter(mood__isnull=True).values_list("text", flat=True)) or \
        list(active.filter(mood="").values_list("text", flat=True))
    quotes = {}
    for item in MOOD_CHECKINS:
        matched = list(active.filter(mood=item["value"]).values_list("text", flat=True))
        quotes[item["key"]] = matched or general or DAILY_MESSAGES
    return render(request, "planner/demo.html", {
        "mood_checkins": MOOD_CHECKINS,
        "demo_quotes": quotes,
    })


def home_view(request):
    if request.user.is_authenticated:
        return render(request, "planner/home_member.html", build_home_context(request.user, date.today()))

    # A visitor has no mood yet, so only show the general (mood-less) quotes.
    general = Quote.objects.filter(active=True, mood__isnull=True) | Quote.objects.filter(active=True, mood="")
    quote = _random_quote(general) or _random_quote(Quote.objects.filter(active=True))
    return render(request, "planner/home.html", {
        "quote": quote,
        "today": date.today(),
        "preview_cards": HOME_PREVIEW_CARDS,
        "mood_checkins": MOOD_CHECKINS,
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
        message = "This day has passed. You can still add or review entries."
    elif selected_date > date.today():
        message = "This day hasn't happened yet. Plan it as loosely as you like."

    reflection = EveningReflection.objects.filter(day=day_obj).first()
    streak = compute_streak(request.user) if selected_date == date.today() else None

    return render(request, "planner/day.html", {
        "day": day_obj,
        "time_blocks": day_obj.time_blocks.all(),
        "message": message,
        "quote": day_obj.closing_quote,
        "reflection": reflection,
        "streak": streak,
        "is_today": selected_date == date.today(),
        "is_past": selected_date < date.today(),
        "nickname": getattr(getattr(request.user, "profile", None), "nickname", ""),
        "prev_date": selected_date - timedelta(days=1),
        "next_date": selected_date + timedelta(days=1),
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
        messages.error(request, "Please choose one of the listed day colors.")
        return redirect_to_day(day)
    if color:
        updated = Day.objects.filter(id=day.id, is_closed=False).update(color=color)
        if updated:
            messages.success(request, "Saved: day color")
    return redirect_to_day(day)


@login_required
def set_day_mood(request):
    if request.method != "POST":
        return redirect("today")
    day = get_object_or_404(Day, id=request.POST.get("day_id"), user=request.user)
    mood = request.POST.get("mood")
    if mood and mood not in dict(Day.MOOD_CHOICES):
        messages.error(request, "Please choose one of the listed moods.")
        return redirect_to_day(day)
    if mood:
        updated = Day.objects.filter(id=day.id, is_closed=False).update(mood=mood)
        if updated:
            messages.success(request, "Saved: mood")
    return redirect_to_day(day)


@login_required
def update_day_text(request):
    day = get_object_or_404(Day, id=request.POST.get("day_id"), user=request.user)
    if not day.is_closed:
        day.notes = request.POST.get("notes", "")
        day.save(update_fields=["notes"])
        messages.success(request, "Saved: journal entry")
    return redirect_to_day(day)


@login_required
def add_timeblock(request):
    day = get_object_or_404(Day, id=request.POST.get("day_id"), user=request.user)
    form = TimeBlockForm(request.POST)
    had_error = False
    if form.is_valid():
        start_time = form.cleaned_data["start_time"]
        end_time = form.cleaned_data["end_time"]
        overlaps = day.time_blocks.filter(
            start_time__lt=end_time, end_time__gt=start_time
        ).exists()
        if overlaps:
            messages.error(request, "That overlaps with a block you already have that day.")
            had_error = True
        else:
            block = form.save(commit=False)
            block.day = day
            block.save()
    else:
        had_error = True
        for error in form.non_field_errors():
            messages.error(request, error)
        for field, errors in form.errors.items():
            if field == "__all__":
                continue
            label = form[field].label
            for error in errors:
                text = str(error)
                text = text[0].lower() + text[1:] if text else text
                messages.error(request, f"{label}: {text}")
    response = redirect_to_day(day)
    if had_error:
        # Land on the form so the error shows right next to it, not off-screen at the top.
        response["Location"] += "#new-block"
    return response


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
        "month_name": MONTH_NAMES[month],
        "prev_month_name": MONTH_NAMES[prev_month],
        "next_month_name": MONTH_NAMES[next_month],
    })

@login_required
def weekly_balance_score_view(request):
    start, end, offset = get_week_range(request)
    days = list(Day.objects.filter(user=request.user, date__range=[start, end]))
    days_logged = len(days)
    mood_days = sum(bool(d.mood) for d in days)
    completed_tasks = TimeBlock.objects.filter(day__in=days, completed=True).count()

    score = min(days_logged * 10 + mood_days * 8 + completed_tasks * 2, 100)

    if days_logged == 0:
        message, suggestion = "Nothing recorded this week.", "You can start with a single day."
    elif days_logged < 3:
        message, suggestion = "A few days recorded this week.", "A mood or a journal entry on any day adds to this page."
    else:
        message, suggestion = "You checked in on several days this week.", ""

    return render(request, "planner/weekly_score.html", {
        "score": score,
        "message": message,
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

    mood_labels = dict(Day.MOOD_CHOICES)
    mood_count = len(moods)
    if mood_count == 0:
        interpretation = "No moods logged this month yet."
    elif mood_count < 3:
        interpretation = f"{mood_count} day{'s' if mood_count != 1 else ''} with a mood logged so far."
    else:
        interpretation = f"Most days with a mood were “{mood_labels[dominant_mood]}”."
    icon = ""

    return render(request, "planner/monthly_overview.html", {
        "days": days,
        "year": year,
        "month": month,
        "month_name": MONTH_NAMES[month],
        "dominant_mood": dominant_mood,
        "icon": icon,
        "interpretation": interpretation,
        "total_days": sum(1 for d in logged_days if d.mood or d.color or d.notes or d.is_closed),
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
        "mood_count": len(moods),
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
        ["date", "mood", "color", "notes", "is_closed", "closed_at"],
        (
            [d.date, d.mood, d.color, d.notes, d.is_closed, d.closed_at]
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
