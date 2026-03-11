from django.contrib import admin
from apps.meetings.models import Meeting, Participant, Transcript, ActionItem


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 0


class TranscriptInline(admin.TabularInline):
    model = Transcript
    extra = 0
    fields = ["speaker", "timestamp", "text", "order"]


class ActionItemInline(admin.TabularInline):
    model = ActionItem
    extra = 0
    fields = ["description", "priority", "status", "assignee", "due_date"]


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ["title", "date", "duration_minutes", "is_active", "created_at"]
    list_filter = ["is_active", "date"]
    search_fields = ["title", "description"]
    inlines = [ParticipantInline, TranscriptInline, ActionItemInline]


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "role", "meeting", "initials"]
    list_filter = ["role"]
    search_fields = ["name", "email"]


@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    list_display = ["meeting", "speaker", "timestamp", "order"]
    list_filter = ["meeting"]
    search_fields = ["text"]


@admin.register(ActionItem)
class ActionItemAdmin(admin.ModelAdmin):
    list_display = ["description", "priority", "status", "assignee", "meeting", "due_date"]
    list_filter = ["priority", "status"]
    search_fields = ["description", "notes"]
