from django.urls import path
from .views import (
    home_view,
    today_view,
    day_detail_view,
    calendar_view,
    add_timeblock,
    toggle_timeblock,
    delete_timeblock,
    set_day_color,
    set_day_mood,
    update_day_text,
    evening_reflection_view,
    monthly_overview_view,
    weekly_balance_score_view,
    mood_chart_view,
    productivity_chart_view,
    register_view,
    login_view,
    logout_view,
    profile_view,
)

urlpatterns = [
    path('', home_view, name='home'),
    path('today/', today_view, name='today'),
    path('day/<int:year>/<int:month>/<int:day>/', day_detail_view, name='day_detail'),
    path('calendar/', calendar_view, name='calendar'),
    path('calendar/<int:year>/<int:month>/', calendar_view, name='calendar_month'),
    path('add-timeblock/', add_timeblock, name='add_timeblock'),
    path('toggle-timeblock/<int:block_id>/', toggle_timeblock, name='toggle_timeblock'),
    path('delete-timeblock/<int:block_id>/', delete_timeblock, name='delete_timeblock'),
    path('set-day-color/', set_day_color, name='set_day_color'),
    path('set-day-mood/', set_day_mood, name='set_day_mood'),
    path('update-day-text/', update_day_text, name='update_day_text'),
    path('evening-reflection/<int:year>/<int:month>/<int:day>/', evening_reflection_view, name='evening_reflection'),
    path('monthly-overview/', monthly_overview_view, name='monthly_overview'),
    path('weekly-score/', weekly_balance_score_view, name='weekly_score'),
    path('charts/mood/', mood_chart_view, name='mood_chart'),
    path('charts/productivity/', productivity_chart_view, name='productivity_chart'),
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
]



