import csv
import hmac
import io
import zipfile
from collections import Counter
from datetime import date, timedelta
from calendar import monthrange
from random import choice
from types import SimpleNamespace
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import redirect, render, get_object_or_404
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Day, TimeBlock, Quote, EveningReflection, UserProfile
from .forms import RegisterForm, EmailAuthenticationForm, TimeBlockForm, ProfileForm

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

def assign_closing_quote(day_obj):
    if day_obj.closing_quote:
        return
    quotes = Quote.objects.filter(active=True)
    if day_obj.mood:
        mood_quotes = quotes.filter(mood=day_obj.mood)
        if mood_quotes.exists():
            quotes = mood_quotes
    if quotes.exists():
        day_obj.closing_quote = choice(list(quotes))

def get_month_year(request):
    today = date.today()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))
    return year, month

def get_week_range(request):
    today = date.today()
    offset = int(request.GET.get("offset", 0))
    start = today - timedelta(days=today.weekday()) + timedelta(weeks=offset)
    end = start + timedelta(days=6)

    return start, end, offset


def register_view(request):
    if request.user.is_authenticated:
        return redirect("today")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.is_active = True
        user.save()
        login(request, user)
        return redirect("today")

    return render(request, "planner/auth/register.html", {"form": form})

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

    quote = Quote.objects.filter(active=True).order_by("?").first()
    return render(request, "planner/home.html", {"quote": quote, "today": date.today()})

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

    return render(request, "planner/day.html", {
        "day": day_obj,
        "time_blocks": day_obj.time_blocks.all(),
        "message": message,
        "quote": day_obj.closing_quote,
        "reflection": reflection,
    })

@login_required
def evening_reflection_view(request, year, month, day):
    try:
        selected_date = date(year, month, day)
    except ValueError:
        raise Http404("Invalid date")
    day_obj = get_object_or_404(Day, user=request.user, date=selected_date)
    reflection, _ = EveningReflection.objects.get_or_create(day=day_obj)

    if request.method == "POST":
        day_obj.mood = request.POST.get("mood") or day_obj.mood
        day_obj.color = request.POST.get("color") or day_obj.color
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
    if not day.is_closed:
        color = request.POST.get("color")
        if color:
            day.color = color
            day.save(update_fields=["color"])
    return redirect_to_day(day)


@login_required
def set_day_mood(request):
    if request.method != "POST":
        return redirect("today")
    day = get_object_or_404(Day, id=request.POST.get("day_id"), user=request.user)
    if not day.is_closed:
        mood = request.POST.get("mood")
        if mood:
            day.mood = mood
            day.save(update_fields=["mood"])
    return redirect_to_day(day)


@login_required
def update_day_text(request):
    day = get_object_or_404(Day, id=request.POST.get("day_id"), user=request.user)
    day.notes = request.POST.get("notes", "")
    day.save(update_fields=["notes"])
    return redirect_to_day(day)


@login_required
def add_timeblock(request):
    day = get_object_or_404(Day, id=request.POST.get("day_id"), user=request.user)
    form = TimeBlockForm(request.POST)
    if form.is_valid():
        block = form.save(commit=False)
        block.day = day
        block.save()
    else:
        for error in form.non_field_errors():
            messages.error(request, error)
        for field, errors in form.errors.items():
            if field == "__all__":
                continue
            for error in errors:
                messages.error(request, f"{field}: {error}")
    return redirect_to_day(day)


@login_required
def toggle_timeblock(request, block_id):
    block = get_object_or_404(TimeBlock, id=block_id, day__user=request.user)
    block.completed = not block.completed
    block.save(update_fields=["completed"])
    return redirect_to_day(block.day)


@login_required
def delete_timeblock(request, block_id):
    block = get_object_or_404(TimeBlock, id=block_id, day__user=request.user)
    day = block.day
    block.delete()
    return redirect_to_day(day)

@login_required
def calendar_view(request, year=None, month=None):
    today = date.today()
    year = int(year or today.year)
    month = int(month or today.month)

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
    days = Day.objects.filter(user=request.user, date__range=[start, end])
    days_logged = days.count()
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
    days = Day.objects.filter(user=request.user, date__year=year, date__month=month).order_by("date")
    moods = [d.mood for d in days if d.mood]
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
        "total_days": days.count(),
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
    offset = int(request.GET.get("offset", 0))
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    start = start_of_week + timedelta(weeks=offset)
    end = start + timedelta(days=6)

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


@login_required
def export_data_view(request):
    user = request.user

    days_csv = io.StringIO()
    writer = csv.writer(days_csv)
    writer.writerow(["date", "mood", "color", "notes", "rest_day", "is_closed", "closed_at"])
    for d in Day.objects.filter(user=user).order_by("date"):
        writer.writerow([d.date, d.mood, d.color, d.notes, d.rest_day, d.is_closed, d.closed_at])

    blocks_csv = io.StringIO()
    writer = csv.writer(blocks_csv)
    writer.writerow(["date", "title", "start_time", "end_time", "completed"])
    for block in TimeBlock.objects.filter(day__user=user).select_related("day").order_by("day__date", "start_time"):
        writer.writerow([block.day.date, block.title, block.start_time, block.end_time, block.completed])

    reflections_csv = io.StringIO()
    writer = csv.writer(reflections_csv)
    writer.writerow(["date", "drain", "small_win"])
    for r in EveningReflection.objects.filter(day__user=user).select_related("day").order_by("day__date"):
        writer.writerow([r.day.date, r.drain, r.small_win])

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("days.csv", days_csv.getvalue())
        zf.writestr("time_blocks.csv", blocks_csv.getvalue())
        zf.writestr("reflections.csv", reflections_csv.getvalue())

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

    now_local = timezone.localtime()
    window_start = (now_local - timedelta(minutes=15)).time()
    window_end = now_local.time()
    today = timezone.localdate()

    sent = 0
    profiles = UserProfile.objects.exclude(evening_reminder_time__isnull=True).select_related("user")
    for profile in profiles:
        reminder_time = profile.evening_reminder_time
        if not (window_start <= reminder_time <= window_end):
            continue

        day = Day.objects.filter(user=profile.user, date=today).first()
        if day and day.is_closed:
            continue

        send_mail(
            subject="🌙 A gentle nudge for your evening reflection",
            message=(
                "No pressure — whenever you're ready, your day is waiting for you.\n\n"
                + request.build_absolute_uri(reverse("today"))
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[profile.user.email],
            fail_silently=True,
        )
        sent += 1

    return HttpResponse(f"Sent {sent} reminder(s).")


def create_superuser(request):
    User = get_user_model()
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(username="admin", email="admin@planner.com", password="StrongPassword123!!")
        return HttpResponse("✅ Superuser created successfully.")
    else:
        return HttpResponse("⚠️ Superuser already exists.")
