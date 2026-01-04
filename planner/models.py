from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


# ===================================================
# 👤 USER PROFILE
# ===================================================

class UserProfile(models.Model):
    PRONOUN_CHOICES = [
        ("she", "she / her"),
        ("he", "he / him"),
        ("they", "they"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    nickname = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True)

    pronoun = models.CharField(
        max_length=10,
        choices=PRONOUN_CHOICES,
        blank=True
    )

    evening_reminder_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Optional daily reminder time for evening reflection."
    )

    def __str__(self):
        return self.nickname or self.user.email


# ===================================================
# 💬 QUOTES (managed via Admin)
# ===================================================

class Quote(models.Model):
    text = models.TextField()

    # optional: associated with a mood
    mood = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    active = models.BooleanField(default=True)

    def __str__(self):
        return self.text[:60]


# ===================================================
# 📅 DAY
# ===================================================

class Day(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="days"
    )

    date = models.DateField()

    # 💭 Mood
    mood = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    # 🎨 Energy / Color
    color = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    # 📝 Notes / Thoughts
    notes = models.TextField(blank=True)

    # 🌱 Rest day
    rest_day = models.BooleanField(default=False)

    # 🌙 Day closed
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(blank=True, null=True)

    # 🌙 Closing quote (assigned when closing the day)
    closing_quote = models.ForeignKey(
        Quote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="days"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date"]
        unique_together = ("user", "date")  # ✅ VERY IMPORTANT

    def __str__(self):
        return f"{self.user.email} – {self.date}"


# ===================================================
# ⏰ TIME BLOCK (TASK)
# ===================================================

class TimeBlock(models.Model):
    day = models.ForeignKey(
        Day,
        on_delete=models.CASCADE,
        related_name="time_blocks"
    )

    title = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()

    completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_time"]

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError(
                "End time must be after start time."
            )

    def __str__(self):
        return f"{self.title} ({self.start_time}–{self.end_time})"


# ===================================================
# 🌙 EVENING REFLECTION
# ===================================================

class EveningReflection(models.Model):
    day = models.OneToOneField(
        Day,
        on_delete=models.CASCADE,
        related_name="evening_reflection"
    )

    drain = models.TextField(blank=True)
    small_win = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reflection – {self.day.user.email} – {self.day.date}"
