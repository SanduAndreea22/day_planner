from django.db import migrations

GENERAL_QUOTES = [
    "You don't have to have it all figured out today.",
    "Small steps still count as moving forward.",
    "Rest is productive too.",
    "You're allowed to take today at your own pace.",
    "Showing up gently is still showing up.",
]

MOOD_QUOTES = {
    "very_bad": [
        "It's okay to not be okay. This day doesn't define you.",
        "You made it through today — that's enough.",
        "Hard days pass, even when they don't feel like it.",
        "Be as gentle with yourself as you would with someone you love.",
        "You don't need to fix everything tonight.",
    ],
    "bad": [
        "Some days are just harder. You're still doing your best.",
        "It's okay to feel off without knowing exactly why.",
        "Tomorrow can start softer than today did.",
        "You showed up, even on a tough day.",
        "Struggling doesn't mean you're failing.",
    ],
    "neutral": [
        "Not every day needs to be extraordinary.",
        "Quiet, ordinary days matter too.",
        "Steady is its own kind of progress.",
        "A calm day is still a good day.",
        "There's peace in an unremarkable day.",
    ],
    "good": [
        "Notice the good — it deserves your attention too.",
        "A good day is worth savoring, not rushing past.",
        "You're building something, one good day at a time.",
        "Let today's ease remind you what's possible.",
        "Enjoy this — you don't need a reason to.",
    ],
    "very_good": [
        "Let yourself feel proud of a day like this.",
        "Hold onto this feeling — you earned it.",
        "This is what taking care of yourself looks like.",
        "A day this good deserves to be remembered.",
        "Celebrate this, even quietly.",
    ],
}


def seed_quotes(apps, schema_editor):
    Quote = apps.get_model("planner", "Quote")

    for text in GENERAL_QUOTES:
        Quote.objects.get_or_create(text=text, mood=None, defaults={"active": True})

    for mood, quotes in MOOD_QUOTES.items():
        for text in quotes:
            Quote.objects.get_or_create(text=text, mood=mood, defaults={"active": True})


def remove_seeded_quotes(apps, schema_editor):
    Quote = apps.get_model("planner", "Quote")

    all_texts = list(GENERAL_QUOTES) + [text for quotes in MOOD_QUOTES.values() for text in quotes]
    Quote.objects.filter(text__in=all_texts).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("planner", "0015_feedback"),
    ]

    operations = [
        migrations.RunPython(seed_quotes, remove_seeded_quotes),
    ]
