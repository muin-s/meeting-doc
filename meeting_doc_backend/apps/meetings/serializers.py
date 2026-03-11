from rest_framework import serializers
from apps.meetings.models import Meeting, Participant, Transcript, ActionItem


class ParticipantSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = Participant
        fields = [
            "id",
            "meeting",
            "name",
            "email",
            "initials",
            "avatar_url",
            "role",
            "role_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "initials"]


class TranscriptSerializer(serializers.ModelSerializer):
    speaker_name = serializers.CharField(
        source="speaker.name", read_only=True, default="Unknown"
    )
    speaker_initials = serializers.CharField(
        source="speaker.initials", read_only=True, default=""
    )

    class Meta:
        model = Transcript
        fields = [
            "id",
            "meeting",
            "speaker",
            "speaker_name",
            "speaker_initials",
            "timestamp",
            "text",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ActionItemSerializer(serializers.ModelSerializer):
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )
    assignee_name = serializers.CharField(
        source="assignee.name", read_only=True, default=None
    )
    assignee_initials = serializers.CharField(
        source="assignee.initials", read_only=True, default=""
    )
    assignee_avatar_url = serializers.CharField(
        source="assignee.avatar_url", read_only=True, default=""
    )

    class Meta:
        model = ActionItem
        fields = [
            "id",
            "meeting",
            "description",
            "notes",
            "priority",
            "priority_display",
            "status",
            "status_display",
            "assignee",
            "assignee_name",
            "assignee_initials",
            "assignee_avatar_url",
            "due_date",
            "timestamp_reference",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MeetingListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""

    participant_count = serializers.IntegerField(
        source="participants.count", read_only=True
    )
    action_item_count = serializers.IntegerField(
        source="action_items.count", read_only=True
    )

    class Meta:
        model = Meeting
        fields = [
            "id",
            "title",
            "description",
            "date",
            "duration_minutes",
            "thumbnail_url",
            "is_active",
            "participant_count",
            "action_item_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MeetingDetailSerializer(serializers.ModelSerializer):
    """Full serializer with nested participants, transcripts, and action items."""

    participants = ParticipantSerializer(many=True, read_only=True)
    transcripts = TranscriptSerializer(many=True, read_only=True)
    action_items = ActionItemSerializer(many=True, read_only=True)

    class Meta:
        model = Meeting
        fields = [
            "id",
            "title",
            "description",
            "date",
            "duration_minutes",
            "video_url",
            "thumbnail_url",
            "is_active",
            "participants",
            "transcripts",
            "action_items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
