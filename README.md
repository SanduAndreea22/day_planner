# 🌸 Emotional Planner

A Django web app for organizing your day around **emotional wellbeing and gentle reflection**, not toxic productivity. Log how a day felt, close it with a small ritual, and see the pattern over time — without streak-shaming or guilt if you miss a day.

**Live demo:** https://day-planner-e2sv.onrender.com
*(hosted on Render's free tier — the first request after inactivity can take 30-50s to wake up)*

---

## What this project demonstrates

Underneath the calm interface is a fully production-shaped app: password reset with real email delivery, scheduled background jobs on a free host with no built-in scheduler, a 43-test suite running in CI on every push, and an error-monitoring hook ready to switch on with one environment variable.

- **Evening reminder emails without a task queue.** Render's free tier has no Celery/cron worker, so a GitHub Actions workflow (`.github/workflows/evening-reminders.yml`) pings a protected endpoint every 15 minutes, which sends a reminder email (via Brevo) to any user whose `evening_reminder_time` has just passed and who hasn't closed their day yet — a real scheduled job built entirely out of free infrastructure.
- **Streak logic that respects the app's own philosophy.** `compute_streak()` counts consecutive days *only* where the user actually engaged (mood, color, notes, or a closed day) — not just days the row exists — and it's shown gently ("🌿 X days in a row you've written something"), only once it reaches 2+ days, never as a guilt trip if it breaks.
- **A weekly balance score that's additive, not punitive**: `min(days_logged*10 + mood_days*8 + completed_tasks*2, 100)`, capped at 100 and framed on-screen as *"This score doesn't define you. It's just a gentle reflection."*

## Features

**Daily planning**
- "Today" view: log a mood, a color, free-text notes, and time-blocked tasks for the day
- Evening reflection ritual: a short close-of-day prompt (what drained you / one small win), with a gentle animated transition when you close the day, and a rotating closing quote matched to your mood
- Optional daily evening reminder email, sent by a scheduled job (see above) — never required, easy to turn off

**Looking back**
- Calendar and monthly overview of logged days
- Mood chart and productivity chart (Chart.js), colored by the day's mood — with the same data available as a plain list underneath, for accessibility
- Weekly balance score with an animated count-up on load
- Gentle streak indicator, shown only on "Today" and only when it means something
- Search past days by note content or filter by mood

**Account & data**
- Email + password authentication, no email confirmation required (keeps it reliable on free hosting)
- Password reset via real email (rate-limited)
- Export all your data as CSV (days, time blocks, reflections)
- Delete your account and everything in it, permanently, with a password confirmation
- In-app feedback form

## Tech stack

- **Backend:** Django 5.2
- **Database:** PostgreSQL (production), SQLite (local dev)
- **Charts:** Chart.js
- **Email:** Brevo (Sendinblue) API, console backend for local dev
- **Error monitoring:** Sentry — a no-op until `SENTRY_DSN` is set
- **Scheduled jobs:** GitHub Actions cron (`workflow_dispatch` + `schedule`), no external task queue
- **Static files:** WhiteNoise
- **Testing/CI:** pytest + `manage.py test` (43 tests), GitHub Actions runs the suite on every push
- **Hosting:** Render

## Architecture

Two apps: `core` (project settings) and `planner` (everything else — models, views, templates, tests). Key models:

| Model | Purpose |
|---|---|
| `Day` | One row per user per date (`unique_together`) — mood, color, notes, rest-day flag, closed state |
| `TimeBlock` | Scheduled tasks within a day, with completion state |
| `EveningReflection` | The end-of-day ritual prompt, one-to-one with a closed `Day` |
| `UserProfile` | Nickname, pronouns, optional evening reminder time |
| `Quote` | Mood-tagged quotes shown when a day is closed |
| `Feedback` | In-app feedback messages |

## Before migrating in production

The migration history includes several destructive changes (field renames,
`RemoveField`, a `delete_habit`) from early iteration on the schema — normal
during development, but a reminder that any future `RemoveField`/`RunPython`
migration should be backed up for first. Before running `python manage.py
migrate` against the production database (Neon Postgres, via `DATABASE_URL`):

1. Take a backup — either a Neon branch/snapshot of the database (fast,
   built into the Neon dashboard) or `pg_dump "$DATABASE_URL" > backup.sql`.
2. Run the migration against a copy first if it's destructive (drops or
   renames a column with existing data), not directly on production.
3. Keep the backup until you've confirmed the app works correctly after the
   migration.

## Running locally

```bash
git clone https://github.com/SanduAndreea22/day_planner.git
cd day_planner
python -m venv venv
venv\Scripts\activate        # or: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # fill in your own values
python manage.py migrate
python manage.py runserver
```

Email, Sentry, and the evening-reminder task secret are all optional for local dev — without them, email just prints to the console and Sentry stays off.

Run the test suite with:

```bash
python manage.py test
```

## 👩‍💻 Author

**Andreea Sandu**
LinkedIn: [linkedin.com/in/andreealuizasandu](https://linkedin.com/in/andreealuizasandu)

✨ *Made with calm & a lot of debugging.* ✨
