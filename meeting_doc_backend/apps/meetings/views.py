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
from apps.meetings.services.ai_processor import process_transcript
from apps.meetings.services.storyboard_analyzer import detect_significant_frames
from apps.meetings.services.context_analyzer import analyze_key_moments
from apps.meetings.services.frame_extractor import extract_hd_frame
from apps.meetings.services.keyword_scanner import scan_for_key_timestamps
from apps.meetings.services.frame_grabber import grab_frames_at_timestamps
from apps.meetings.services.unified_processor import process_meeting


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

    @action(detail=False, methods=["post"],
            url_path="process-transcript",
            permission_classes=[AllowAny])
    def process_transcript(self, request):
        transcript_text = request.data.get("transcript_text")
        if not transcript_text:
            return Response({"error": "transcript_text is required"}, status=400)
        if len(transcript_text.strip()) < 50:
            return Response({"error": "Transcript too short to process"}, status=400)

        result = process_transcript(transcript_text)

        if "error" in result and "action_items" not in result:
            return Response(result, status=500)

        return Response(result)

    @action(detail=False, methods=["post"],
            url_path="analyze-context",
            permission_classes=[AllowAny])
    def analyze_context(self, request):
        import os
        video_id = request.data.get("video_id")
        transcript_with_timestamps = request.data.get("transcript_timestamps", [])

        if not video_id:
            return Response({"error": "video_id is required"}, status=400)

        # Step 1+2: detect visual frame changes from storyboard
        visual_timestamps = detect_significant_frames(video_id)

        if not visual_timestamps:
            return Response({"error": "Could not analyze storyboard"}, status=400)

        # Create mapping of timestamp -> thumbnail for fallback
        thumbnail_map = { vt["estimated_timestamp_seconds"]: vt.get("thumbnail") for vt in visual_timestamps }

        # Step 3: cross reference with transcript via Gemini
        labeled_moments = analyze_key_moments(
            transcript_with_timestamps,
            visual_timestamps
        )

        # Step 4: fetch HD frame for each labeled moment
        # Store frames in media/frames/{video_id}/
        output_dir = os.path.join("media", "frames", video_id)
        os.makedirs(output_dir, exist_ok=True)

        results = []
        for moment in labeled_moments:
            ts = moment["timestamp_seconds"]
            fallback = thumbnail_map.get(ts)
            
            frame_path = extract_hd_frame(
                video_id,
                ts,
                output_dir,
                fallback_image=fallback
            )
            results.append({
                "timestamp_seconds": ts,
                "label": moment["label"],
                "description": moment["description"],
                "confidence": moment["confidence"],
                "frame_url": f"/media/frames/{video_id}/{os.path.basename(frame_path)}" if frame_path else None,
                "youtube_url": f"https://www.youtube.com/watch?v={video_id}&t={ts}"
            })

        return Response({"key_moments": results})

    @action(detail=False, methods=["post"],
            url_path="process-meeting",
            permission_classes=[AllowAny])
    def process_meeting_view(self, request):
        transcript_text = request.data.get("transcript_text", "")
        transcript_timestamps = request.data.get("transcript_timestamps", [])
        video_id = request.data.get("video_id", "")

        if not transcript_text:
            return Response({"error": "transcript_text is required"}, status=400)
        if len(transcript_text.strip()) < 50:
            return Response({"error": "Transcript too short"}, status=400)

        # Step 1: find semantic timestamps
        key_timestamps = scan_for_key_timestamps(
            transcript_timestamps,
            max_frames=5,
            min_gap_seconds=30
        )
        timestamp_seconds_list = [t["timestamp_seconds"] for t in key_timestamps]

        # Step 2: grab sprite thumbnails at those timestamps
        frames = []
        if video_id and timestamp_seconds_list:
            frames = grab_frames_at_timestamps(video_id, timestamp_seconds_list)

            # Merge category info into frames
            for i, frame in enumerate(frames):
                if i < len(key_timestamps):
                    frame["category"] = key_timestamps[i]["category"]
                    frame["matched_text"] = key_timestamps[i]["matched_text"]

        # Step 3: single Gemini Vision call
        result = process_meeting(transcript_text, frames, video_id)

        print(f"Key timestamps found: {timestamp_seconds_list}")
        print(f"Frames grabbed: {len(frames)}")
        print(f"Frames with thumbnails: {sum(1 for f in frames if f.get('thumbnail_base64'))}")

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
