from django.contrib import admin
from .models import Quote, Day, TimeBlock, UserProfile, EveningReflection, Feedback

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("short_text", "mood", "active")
    list_filter = ("active", "mood")
    search_fields = ("text",)

    def short_text(self, obj):
        return obj.text[:50]
    short_text.short_description = "Text"

@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "mood", "is_closed")
    list_filter = ("is_closed", "mood")
    date_hierarchy = "date"

@admin.register(TimeBlock)
class TimeBlockAdmin(admin.ModelAdmin):
    list_display = ("title", "day", "start_time", "end_time", "completed")

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "nickname", "pronoun")
    search_fields = ("user__email", "nickname")

@admin.register(EveningReflection)
class EveningReflectionAdmin(admin.ModelAdmin):
    list_display = ("day", "created_at")

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "message")


