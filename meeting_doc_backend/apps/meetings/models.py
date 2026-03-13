from django.db import models
from apps.core.models import UUIDModel, TimeStampedModel


class Meeting(UUIDModel, TimeStampedModel):
    video_id = models.CharField(max_length=30, db_index=True)
    session_key = models.CharField(
        max_length=40,
        db_index=True,
        default="",
        blank=True
    )
    title = models.CharField(max_length=500, blank=True)
    youtube_url = models.URLField(blank=True)
    transcript_text = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    key_decisions = models.JSONField(default=list)
    participants_detected = models.JSONField(default=list)
    visual_frames = models.JSONField(default=list)
    word_count = models.IntegerField(default=0)
    is_processed = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ["video_id", "session_key"]
        ordering = ["-created_at"]
        verbose_name = "Meeting"
        verbose_name_plural = "Meetings"

    def __str__(self):
        return self.title or self.video_id


class Participant(UUIDModel, TimeStampedModel):
    """
    Represents a participant in a meeting.
    """

    class Role(models.TextChoices):
        ORGANIZER = "organizer", "Organizer"
        PRESENTER = "presenter", "Presenter"
        ATTENDEE = "attendee", "Attendee"

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="participants",
    )
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, default="")
    initials = models.CharField(
        max_length=5,
        blank=True,
        default="",
    )
    avatar_url = models.URLField(blank=True, default="")
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ATTENDEE,
    )

    class Meta:
        verbose_name = "Participant"
        verbose_name_plural = "Participants"
        ordering = ["name"]
        unique_together = [("meeting", "email")]

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        if not self.initials and self.name:
            parts = self.name.strip().split()
            self.initials = "".join(p[0].upper() for p in parts[:2])
        super().save(*args, **kwargs)


class Transcript(UUIDModel, TimeStampedModel):
    """
    Represents a single transcript entry within a meeting.
    """

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="transcripts",
    )
    speaker = models.ForeignKey(
        Participant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transcript_entries",
    )
    timestamp = models.CharField(
        max_length=10,
    )
    text = models.TextField()
    order = models.PositiveIntegerField(
        default=0,
    )

    class Meta:
        verbose_name = "Transcript Entry"
        verbose_name_plural = "Transcript Entries"
        ordering = ["order", "timestamp"]

    def __str__(self):
        speaker_name = self.speaker.name if self.speaker else "Unknown"
        return f"[{self.timestamp}] {speaker_name}: {self.text[:50]}"


class ActionItem(UUIDModel, TimeStampedModel):
    """
    Represents an action item extracted from a meeting.
    """

    class Priority(models.TextChoices):
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        DONE = "done", "Done"

    meeting = models.ForeignKey(
        Meeting,
        on_delete=models.CASCADE,
        related_name="action_items",
    )
    description = models.TextField()
    assignee_name = models.CharField(max_length=255, blank=True, default="")
    notes = models.TextField(
        blank=True,
        default="",
    )
    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING,
    )
    assignee = models.ForeignKey(
        Participant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_action_items",
    )
    due_date = models.CharField(max_length=100, null=True, blank=True)
    timestamp_reference = models.CharField(
        max_length=10,
        blank=True,
        default="",
    )

    class Meta:
        verbose_name = "Action Item"
        verbose_name_plural = "Action Items"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.description[:60]}"
