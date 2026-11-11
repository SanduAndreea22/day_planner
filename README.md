# Emotional Planner

A Django web app for organizing your day around **emotional wellbeing and gentle reflection**, not toxic productivity. Log how a day felt, close it with a small ritual, and see the pattern over time — without streak-shaming or guilt if you miss a day.

**Live demo:** https://day-planner-e2sv.onrender.com
*(hosted on Render's free tier — the first request after inactivity can take 30-50s to wake up)*

---

## What this project demonstrates

Underneath the calm interface is a production-shaped app: a test suite and migration check running in CI on every push, a collectstatic test that guards the deploy, and an error-monitoring hook ready to switch on with one environment variable.

- **No scores, no streaks.** The week and month pages only show what was recorded (days, moods, journal entries, finished time blocks), never a grade or a ranking.
- **Check-in without leaving the page.** The Home page saves a mood or a journal entry in place; the five emotions map onto the stored five-step mood scale, so calendar and charts keep working.
- **A no-account demo** (`/demo/`) that reads the saved quotes and stores nothing.

## Features

**Daily planning**
- Home: a daily check-in (five emotions), a reflection prompt, and a quiet look at recent days
- "My day": mood, day color, a journal entry, and time-blocked tasks for any day in range
- Evening reflection: a short close-of-day prompt (what drained you / one small thing that went well). Closing locks the day, and a closing quote matched to the mood is saved with it

**Looking back**
- Calendar (mood icon and day color per day) and a monthly overview with mood counts
- Mood chart and time-blocks chart (Chart.js, served locally), with the same data as a plain list underneath and a text fallback if the chart can't load
- "Your week": days logged, time blocks finished, moods logged
- Search past days by journal text (matches highlighted, paginated) or filter by mood

**Account & data**
- Email + password authentication, no email confirmation required (keeps it reliable on free hosting)
- Export all your data as CSV (days, time blocks, reflections)
- Delete your account and everything in it, permanently, with a password confirmation
- In-app feedback form

## Tech stack

- **Backend:** Django 5.2
- **Database:** PostgreSQL (production), SQLite (local dev)
- **Charts:** Chart.js 4 (vendored in `planner/static/planner/vendor/`, MIT license header kept)
- **Error monitoring:** Sentry — a no-op until `SENTRY_DSN` is set
- **Static files:** WhiteNoise
- **Testing/CI:** pytest (`requirements-dev.txt`), GitHub Actions runs `check`, `makemigrations --check` and the suite on Python 3.11 and 3.13
- **Hosting:** Render

## Architecture

Two apps: `core` (project settings) and `planner` (everything else — models, views, templates, tests). Key models:

| Model | Purpose |
|---|---|
| `Day` | One row per user per date (`unique_together`) — mood, color, notes, closed state |
| `TimeBlock` | Scheduled tasks within a day, with completion state |
| `EveningReflection` | The end-of-day ritual prompt, one-to-one with a closed `Day` |
| `UserProfile` | Nickname and a short bio (the table still has two unused reminder columns, see notes) |
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

## Dependencies

- `requirements.txt` — what runs in production (this is what the host and the Docker image install).
- `requirements-dev.txt` — adds the test tools (`pytest`, `pytest-django`, `coverage`) on top.

## Running locally

```bash
git clone https://github.com/SanduAndreea22/day_planner.git
cd day_planner
python -m venv venv
venv\Scripts\activate        # or: source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env         # fill in your own values
python manage.py migrate
python manage.py runserver
```

Sentry is optional for local dev and stays off without `SENTRY_DSN`. The app does not send any email.

Run the test suite with:

```bash
pytest
```

## 👩‍💻 Author

**Andreea Sandu**
LinkedIn: [linkedin.com/in/andreealuizasandu](https://linkedin.com/in/andreealuizasandu)

*Made with calm & a lot of debugging.*
