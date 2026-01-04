from django.urls import path
from .views import (
    # 🏠 Core
    home_view,
    today_view,
    day_detail_view,
    calendar_view,

    # ➕ TimeBlocks
    add_timeblock,
    toggle_timeblock,
    delete_timeblock,

    # 🎨 + 💭 Day State
    set_day_color,
    set_day_mood,
    update_day_text,

    # 🌙 Evening Reflection
    evening_reflection_view,

    # 📊 Analytics
    monthly_overview_view,
    weekly_balance_score_view,
    mood_chart_view,
    productivity_chart_view,

    # 🔐 Authentication
    register_view,
    login_view,
    logout_view,
    profile_view,
)

urlpatterns = [
    # =========================
    # 🏠 HOME
    # =========================
    path('', home_view, name='home'),

    # =========================
    # 📅 TODAY
    # =========================
    path('today/', today_view, name='today'),

    # =========================
    # 📆 SPECIFIC DAY
    # =========================
    path('day/<int:year>/<int:month>/<int:day>/', day_detail_view, name='day_detail'),

    # =========================
    # 🗓 CALENDAR
    # =========================
    path('calendar/', calendar_view, name='calendar'),
    path('calendar/<int:year>/<int:month>/', calendar_view, name='calendar_month'),

    # =========================
    # ⏰ TIMEBLOCKS
    # =========================
    path('add-timeblock/', add_timeblock, name='add_timeblock'),
    path('toggle-timeblock/<int:block_id>/', toggle_timeblock, name='toggle_timeblock'),
    path('delete-timeblock/<int:block_id>/', delete_timeblock, name='delete_timeblock'),

    # =========================
    # 🎨 + 💭 DAY STATE
    # =========================
    path('set-day-color/', set_day_color, name='set_day_color'),
    path('set-day-mood/', set_day_mood, name='set_day_mood'),
    path('update-day-text/', update_day_text, name='update_day_text'),

    # =========================
    # 🌙 EVENING REFLECTION
    # =========================
    path('evening-reflection/<int:year>/<int:month>/<int:day>/', evening_reflection_view, name='evening_reflection'),

    # =========================
    # 📊 ANALYTICS
    # =========================
    path('monthly-overview/', monthly_overview_view, name='monthly_overview'),
    path('weekly-score/', weekly_balance_score_view, name='weekly_score'),
    path('charts/mood/', mood_chart_view, name='mood_chart'),
    path('charts/productivity/', productivity_chart_view, name='productivity_chart'),

    # =========================
    # 🔐 AUTHENTICATION
    # =========================
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
]



