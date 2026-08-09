from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
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
    feedback_view,
    delete_account_view,
    search_view,
    export_data_view,
    send_evening_reminders_view,
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
    path('feedback/', feedback_view, name='feedback'),
    path('delete-account/', delete_account_view, name='delete_account'),
    path('search/', search_view, name='search'),
    path('export-data/', export_data_view, name='export_data'),
    path('tasks/send-evening-reminders/', send_evening_reminders_view, name='send_evening_reminders'),

    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='planner/auth/password_reset.html',
        email_template_name='planner/email/password_reset_email.txt',
        html_email_template_name='planner/email/password_reset_email.html',
        subject_template_name='planner/email/password_reset_subject.txt',
        success_url=reverse_lazy('password_reset_done'),
    ), name='password_reset'),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='planner/auth/password_reset_done.html',
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='planner/auth/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete'),
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='planner/auth/password_reset_complete.html',
    ), name='password_reset_complete'),

    path('how-it-works/', TemplateView.as_view(
        template_name='planner/guide.html',
    ), name='guide'),

    path('privacy-policy/', TemplateView.as_view(
        template_name='planner/legal/privacy_policy.html',
    ), name='privacy_policy'),

    path('terms/', TemplateView.as_view(
        template_name='planner/legal/terms.html',
    ), name='terms'),
]



