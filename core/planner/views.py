from datetime import date
from calendar import monthrange
from random import choice
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Day, TimeBlock, Quote, EveningReflection, UserProfile
from .forms import RegisterForm, EmailAuthenticationForm
from datetime import date, timedelta


def register_view(request):
    if request.user.is_authenticated:
        return redirect("today")

    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
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
        profile.nickname = request.POST.get("nickname", "")
        profile.bio = request.POST.get("bio", "")
        profile.save()
        saved = True

    return render(request, "planner/auth/profile.html", {
        "profile": profile,
        "saved": saved,
    })

def home_view(request):
    if request.user.is_authenticated:
        return redirect("today")

    quote = Quote.objects.filter(active=True).order_by("?").first()

    return render(request, "planner/home.html", {
        "quote": quote,
        "today": date.today(),
    })

@login_required
def today_view(request):
    today = date.today()
    return redirect(
        "day_detail",
        year=today.year,
        month=today.month,
        day=today.day
    )

from .models import EveningReflection

@login_required
def day_detail_view(request, year, month, day):
    selected_date = date(year, month, day)

    day_obj, _ = Day.objects.get_or_create(
        user=request.user,
        date=selected_date
    )

    message = None
    if selected_date < date.today():
        message = "Zi din trecut. Poți reflecta în ritmul tău 🤍"
    elif selected_date > date.today():
        message = "Zi din viitor. Nu trebuie încă să fie clară ✨"

    reflection = EveningReflection.objects.filter(day=day_obj).first()

    return render(request, "planner/day.html", {
        "day": day_obj,
        "time_blocks": day_obj.time_blocks.all(),
        "message": message,
        "quote": day_obj.closing_quote,  # ✅ CITAT
    })



@login_required
def set_day_color(request):
    if request.method != "POST":
        return redirect("today")

    day = get_object_or_404(
        Day,
        id=request.POST.get("day_id"),
        user=request.user
    )

    # 🔒 zi închisă → nu mai permitem modificări
    if day.is_closed:
        return redirect(
            "day_detail",
            year=day.date.year,
            month=day.date.month,
            day=day.date.day
        )

    color = request.POST.get("color")
    if color:
        day.color = color
        day.save(update_fields=["color"])

    return redirect(
        "day_detail",
        year=day.date.year,
        month=day.date.month,
        day=day.date.day
    )


@login_required
def set_day_mood(request):
    if request.method != "POST":
        return redirect("today")

    day = get_object_or_404(
        Day,
        id=request.POST.get("day_id"),
        user=request.user
    )

    # 🔒 zi închisă → nu mai permitem modificări
    if day.is_closed:
        return redirect(
            "day_detail",
            year=day.date.year,
            month=day.date.month,
            day=day.date.day
        )

    mood = request.POST.get("mood")
    if mood:
        day.mood = mood
        day.save(update_fields=["mood"])

    return redirect(
        "day_detail",
        year=day.date.year,
        month=day.date.month,
        day=day.date.day
    )


@login_required
def update_day_text(request):
    day = get_object_or_404(
        Day,
        id=request.POST.get("day_id"),
        user=request.user
    )

    day.notes = request.POST.get("notes", "")
    day.save(update_fields=["notes"])

    return redirect(
        "day_detail",
        year=day.date.year,
        month=day.date.month,
        day=day.date.day
    )

@login_required
def add_timeblock(request):
    day = get_object_or_404(
        Day,
        id=request.POST.get("day_id"),
        user=request.user
    )

    TimeBlock.objects.create(
        day=day,
        title=request.POST.get("title"),
        start_time=request.POST.get("start_time"),
        end_time=request.POST.get("end_time"),
    )

    return redirect(
        "day_detail",
        year=day.date.year,
        month=day.date.month,
        day=day.date.day
    )

@login_required
def toggle_timeblock(request, block_id):
    block = get_object_or_404(
        TimeBlock,
        id=block_id,
        day__user=request.user
    )

    block.completed = not block.completed
    block.save(update_fields=["completed"])

    day = block.day
    return redirect(
        "day_detail",
        year=day.date.year,
        month=day.date.month,
        day=day.date.day
    )

@login_required
def delete_timeblock(request, block_id):
    block = get_object_or_404(
        TimeBlock,
        id=block_id,
        day__user=request.user
    )

    day = block.day
    block.delete()

    return redirect(
        "day_detail",
        year=day.date.year,
        month=day.date.month,
        day=day.date.day
    )

@login_required
def evening_reflection_view(request, year, month, day):
    selected_date = date(year, month, day)

    day_obj = get_object_or_404(
        Day,
        user=request.user,
        date=selected_date
    )

    reflection, _ = EveningReflection.objects.get_or_create(day=day_obj)

    if request.method == "POST":
        # ✅ SALVEAZĂ STAREA ZILEI (NU SE PIERDE)
        day_obj.mood = request.POST.get("mood") or day_obj.mood
        day_obj.color = request.POST.get("color") or day_obj.color
        day_obj.notes = request.POST.get("notes", day_obj.notes)

        day_obj.save(update_fields=["mood", "color", "notes"])

        # ✅ REFLECȚIA DE SEARĂ
        reflection.drain = request.POST.get("drain", "")
        reflection.small_win = request.POST.get("small_win", "")
        reflection.save()

        # ✅ CITAT FINAL (în funcție de stare)
        if not day_obj.closing_quote:
            quotes = Quote.objects.filter(active=True)

            if day_obj.mood:
                mood_quotes = quotes.filter(mood=day_obj.mood)
                if mood_quotes.exists():
                    quotes = mood_quotes

            if quotes.exists():
                day_obj.closing_quote = choice(list(quotes))

        # ✅ ÎNCHIDE ZIUA
        day_obj.is_closed = True
        day_obj.closed_at = timezone.now()
        day_obj.save(update_fields=["is_closed", "closed_at", "closing_quote"])

        return redirect(
            "day_detail",
            year=year,
            month=month,
            day=day
        )

    return render(request, "planner/evening.html", {
        "day": day_obj,
        "reflection": reflection
    })


from datetime import date
from calendar import monthrange
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Day


@login_required
def calendar_view(request, year=None, month=None):
    today = date.today()

    # dacă nu primim lună → luna curentă
    if not year or not month:
        year = today.year
        month = today.month

    year = int(year)
    month = int(month)

    # limită minimă (noiembrie 2025)
    if year < 2025 or (year == 2025 and month < 11):
        year, month = 2025, 11

    days = []
    total_days = monthrange(year, month)[1]

    for d in range(1, total_days + 1):
        current = date(year, month, d)
        day_obj = Day.objects.filter(
            user=request.user,
            date=current
        ).first()

        days.append({
            "date": current,
            "day": day_obj,
            "is_today": current == today,
            "is_future": current > today,
        })

    # navigație
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    next_month = month + 1
    next_year = year
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


from datetime import date, timedelta
from calendar import month_name
from collections import Counter

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Day, TimeBlock


# ===================================================
# 🧠 HELPERS
# ===================================================

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


# ===================================================
# 💗 WEEKLY SCORE
# ===================================================

@login_required
def weekly_balance_score_view(request):
    start, end, offset = get_week_range(request)

    days = Day.objects.filter(
        user=request.user,
        date__range=[start, end]
    )

    days_logged = days.count()
    mood_days = sum(bool(d.mood) for d in days)
    completed_tasks = TimeBlock.objects.filter(
        day__in=days,
        completed=True
    ).count()

    score = min(
        days_logged * 10 +
        mood_days * 8 +
        completed_tasks * 2,
        100
    )

    if score < 30:
        message = "A fost greu. E suficient că ai fost aici."
        emoji = "🫶"
    elif score < 70:
        message = "Ai avut momente de echilibru. Este ok."
        emoji = "🌿"
    else:
        message = "Săptămână cu resurse bune."
        emoji = "💗"

    if days_logged == 0:
        suggestion = "Poate săptămâna viitoare începe cu o singură zi notată."
    elif days_logged < 3:
        suggestion = "Poate data viitoare adaugi un gând mic."
    else:
        suggestion = "Continuă în ritmul tău."

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


# ===================================================
# 📊 MONTHLY OVERVIEW
# ===================================================

@login_required
def monthly_overview_view(request):
    year, month = get_month_year(request)

    days = Day.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    ).order_by("date")

    moods = [d.mood for d in days if d.mood]
    counter = Counter(moods)
    dominant_mood = counter.most_common(1)[0][0] if counter else None

    interpretation_map = {
        "very_bad": ("🌧️", "Luna a fost solicitantă."),
        "bad": ("🌥️", "Au fost mai multe zile dificile."),
        "neutral": ("🌤️", "O lună stabilă, fără extreme."),
        "good": ("🌱", "Ai avut mai multe zile bune."),
        "very_good": ("🌸", "O lună cu resurse emoționale frumoase."),
        None: ("🌙", "Fiecare zi contează, chiar și cele nescrise."),
    }

    icon, interpretation = interpretation_map[dominant_mood]

    return render(request, "planner/monthly_overview.html", {
        "days": days,
        "year": year,
        "month": month,
        "month_name": month_name[month],
        "dominant_mood": dominant_mood,
        "icon": icon,
        "interpretation": interpretation,
    })


# ===================================================
# 📈 MOOD CHART
# ===================================================

@login_required
def mood_chart_view(request):
    year, month = get_month_year(request)

    days = Day.objects.filter(
        user=request.user,
        date__year=year,
        date__month=month
    ).order_by("date")

    moods = [d.mood for d in days if d.mood]
    most_common_mood = Counter(moods).most_common(1)[0][0] if moods else None

    return render(request, "planner/chart/mood.html", {
        "days": days,
        "year": year,
        "month": month,
        "month_name": month_name[month],
        "most_common_mood": most_common_mood,
    })


@login_required
def productivity_chart_view(request):
    # offset = 0 (săptămâna curentă)
    # offset = -1 (săptămâna trecută)
    # offset = +1 (săptămâna viitoare)
    offset = int(request.GET.get("offset", 0))

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    start = start_of_week + timedelta(weeks=offset)
    end = start + timedelta(days=6)

    days = Day.objects.filter(
        user=request.user,
        date__range=(start, end)
    ).order_by("date")

    data = []
    for d in days:
        data.append({
            "date": d.date.strftime("%d %b"),
            "completed": d.time_blocks.filter(completed=True).count(),
            "mood": d.mood or "none",
        })

    return render(request, "planner/chart/productivity.html", {
        "data": data,
        "start": start,
        "end": end,
        "offset": offset,
    })

from django.contrib.auth import get_user_model
from django.http import HttpResponse

def creeaza_superuser(request):
    User = get_user_model()
    if not User.objects.filter(username="admin").exists():
        User.objects.create_superuser(
            username="admin",
            email="admin@planner.com",
            password="ParolaTare123!!"
        )
        return HttpResponse("✅ Superuser creat cu succes.")
    else:
        return HttpResponse("⚠️ Superuserul există deja.")


