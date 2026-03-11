from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.meetings.models import Meeting, Participant, Transcript, ActionItem
from apps.meetings.serializers import (
    MeetingListSerializer,
    MeetingDetailSerializer,
    ParticipantSerializer,
    TranscriptSerializer,
    ActionItemSerializer,
)
from apps.meetings.services.transcript_fetcher import fetch_youtube_transcript


class MeetingViewSet(ModelViewSet):
    """
    API endpoint for meetings.
    - GET /api/meetings/         → list (lightweight)
    - GET /api/meetings/{id}/    → detail (with nested participants, transcripts, action items)
    - POST/PUT/PATCH/DELETE      → standard CRUD
    """

    queryset = Meeting.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ["title", "description"]
    ordering_fields = ["date", "created_at", "duration_minutes"]
    ordering = ["-date"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MeetingDetailSerializer
        return MeetingListSerializer

    @action(detail=False, methods=["post"], url_path="fetch-transcript", permission_classes=[AllowAny])
    def fetch_transcript(self, request):
        """POST /api/v1/meetings/fetch-transcript/ — fetch a transcript for a given YouTube URL."""
        youtube_url = request.data.get("youtube_url")
        if not youtube_url:
            return Response({"error": "youtube_url is required"}, status=400)

        result = fetch_youtube_transcript(youtube_url)
        if "error" in result:
            return Response({"error": result["error"]}, status=400)

        return Response(result)

    @action(detail=True, methods=["get"], url_path="transcripts")
    def transcripts(self, request, pk=None):
        """GET /api/meetings/{id}/transcripts/ — all transcript entries for this meeting."""
        meeting = self.get_object()
        transcripts = meeting.transcripts.select_related("speaker").all()
        serializer = TranscriptSerializer(transcripts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="action-items")
    def action_items(self, request, pk=None):
        """GET /api/meetings/{id}/action-items/ — all action items for this meeting."""
        meeting = self.get_object()
        items = meeting.action_items.select_related("assignee").all()
        serializer = ActionItemSerializer(items, many=True)
        return Response(serializer.data)


class ParticipantViewSet(ModelViewSet):
    """
    API endpoint for participants.
    Supports filtering by meeting.
    """

    queryset = Participant.objects.select_related("meeting").all()
    serializer_class = ParticipantSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ["meeting", "role"]
    search_fields = ["name", "email"]


class TranscriptViewSet(ModelViewSet):
    """
    API endpoint for transcript entries.
    Supports filtering by meeting and speaker.
    """

    queryset = Transcript.objects.select_related("meeting", "speaker").all()
    serializer_class = TranscriptSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["meeting", "speaker"]
    search_fields = ["text"]
    ordering_fields = ["order", "timestamp"]
    ordering = ["order"]


class ActionItemViewSet(ModelViewSet):
    """
    API endpoint for action items.
    Supports filtering by meeting, priority, status, and assignee.
    """

    queryset = ActionItem.objects.select_related("meeting", "assignee").all()
    serializer_class = ActionItemSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["meeting", "priority", "status", "assignee"]
    search_fields = ["description", "notes"]
    ordering_fields = ["created_at", "priority", "due_date"]
    ordering = ["-created_at"]
