from django.db import models
from apps.core.models import UUIDModel


class Meeting(UUIDModel):
    """
    Represents a recorded meeting session.
    Maps to the frontend's meeting header: title, date, duration, presenter, video.
    """

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, default="")
    date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(
        help_text="Duration of the meeting in minutes"
    )
    video_url = models.URLField(blank=True, default="")
    thumbnail_url = models.URLField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Meeting"
        verbose_name_plural = "Meetings"
        ordering = ["-date"]

    def __str__(self):
        return self.title


class Participant(UUIDModel):
    """
    Represents a participant in a meeting.
    Maps to the frontend's avatars, speaker names, roles.
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
        help_text="Display initials, e.g. 'SJ' for Sarah Jenkins",
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
        # Auto-generate initials from name if not provided
        if not self.initials and self.name:
            parts = self.name.strip().split()
            self.initials = "".join(p[0].upper() for p in parts[:2])
        super().save(*args, **kwargs)


class Transcript(UUIDModel):
    """
    Represents a single transcript entry (one speaker turn) within a meeting.
    Maps to the frontend's Raw Transcript tab: speaker, timestamp, text.
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
        help_text="Timestamp in the video, e.g. '12:04'",
    )
    text = models.TextField()
    order = models.PositiveIntegerField(
        default=0,
        help_text="Order of this entry in the transcript",
    )

    class Meta:
        verbose_name = "Transcript Entry"
        verbose_name_plural = "Transcript Entries"
        ordering = ["order", "timestamp"]

    def __str__(self):
        speaker_name = self.speaker.name if self.speaker else "Unknown"
        return f"[{self.timestamp}] {speaker_name}: {self.text[:50]}"


class ActionItem(UUIDModel):
    """
    Represents an action item extracted from a meeting.
    Maps to the frontend's Action Items tab: description, priority, status, assignee.
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
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Additional context, e.g. 'Mentioned at 14:20 during infrastructure discussion'",
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
    due_date = models.DateField(null=True, blank=True)
    timestamp_reference = models.CharField(
        max_length=10,
        blank=True,
        default="",
        help_text="Timestamp in the video where this action item was mentioned",
    )

    class Meta:
        verbose_name = "Action Item"
        verbose_name_plural = "Action Items"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.description[:60]}"
