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
    
    # Use assignee_name from model, or fallback to assignee.name if linked
    display_assignee = serializers.SerializerMethodField()

    class Meta:
        model = ActionItem
        fields = [
            "id",
            "meeting",
            "description",
            "assignee_name",
            "notes",
            "priority",
            "priority_display",
            "status",
            "status_display",
            "assignee",
            "display_assignee",
            "due_date",
            "timestamp_reference",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_display_assignee(self, obj):
        if obj.assignee:
            return obj.assignee.name
        return obj.assignee_name or "Unassigned"


class MeetingSerializer(serializers.ModelSerializer):
    """Full serializer including analysis fields."""
    class Meta:
        model = Meeting
        fields = [
            "id", "video_id", "title", "youtube_url", "transcript_text",
            "summary", "key_decisions", "participants_detected", "visual_frames",
            "word_count", "is_processed", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MeetingListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    class Meta:
        model = Meeting
        fields = [
            "id", "video_id", "title", "youtube_url", "summary",
            "is_processed", "word_count", "created_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class MeetingDetailSerializer(serializers.ModelSerializer):
    """Full detail with related objects."""
    participants = ParticipantSerializer(many=True, read_only=True)
    transcripts = TranscriptSerializer(many=True, read_only=True)
    action_items = ActionItemSerializer(many=True, read_only=True)

    class Meta:
        model = Meeting
        fields = [
            "id", "video_id", "title", "youtube_url", "transcript_text",
            "summary", "key_decisions", "participants_detected", "visual_frames",
            "word_count", "is_processed", "participants", "transcripts", 
            "action_items", "created_at", "updated_at"
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
