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
from apps.meetings.tasks import process_meeting_task
from celery.result import AsyncResult
from django_ratelimit.decorators import ratelimit


def get_or_create_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


class MeetingViewSet(ModelViewSet):
    """
    API endpoint for meetings.
    - GET /api/meetings/         → list (lightweight)
    - GET /api/meetings/{id}/    → detail (with nested participants, transcripts, action items)
    - POST/PUT/PATCH/DELETE      → standard CRUD
    """

    ordering_fields = ["created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        session_key = get_or_create_session_key(self.request)
        return Meeting.objects.filter(session_key=session_key)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MeetingDetailSerializer
        return MeetingListSerializer

    @action(detail=False, methods=["post"], url_path="fetch-transcript", permission_classes=[AllowAny])
    def fetch_transcript(self, request):
        """POST /api/v1/meetings/fetch-transcript/ — fetch a transcript for a given YouTube URL."""
        session_key = get_or_create_session_key(request)
        youtube_url = request.data.get("youtube_url")
        if not youtube_url:
            return Response({"error": "youtube_url is required"}, status=400)

        # 1. Extract video_id from youtube_url
        import re
        video_id_match = re.search(r'(?:v=|\/|be\/)([a-zA-Z0-9_-]{11})', youtube_url)
        video_id = video_id_match.group(1) if video_id_match else None
        
        if not video_id:
            return Response({"error": "Invalid YouTube URL"}, status=400)

        # 2. Check if Meeting with this video_id exists AND is_processed=True
        meeting = Meeting.objects.filter(
            video_id=video_id,
            session_key=session_key,
            is_processed=True
        ).first()
        
        # 3. If YES: return cached result immediately
        existing = Meeting.objects.filter(
            video_id=video_id,
            session_key=session_key,
            is_processed=True
        ).first()
        
        if existing:
            action_items = ActionItem.objects.filter(meeting=existing)
            response_data = {
                "transcript_text": existing.transcript_text,
                "video_id": existing.video_id,
                "word_count": existing.word_count,
                "transcript_timestamps": [],
                "cached": True,
                "meeting_id": str(existing.id),
                "cached_result": {
                    "summary": existing.summary,
                    "action_items": [
                        {
                            "description": item.description,
                            "assignee": item.assignee_name,
                            "priority": item.priority,
                            "due_date": str(item.due_date) if item.due_date else None
                        }
                        for item in action_items
                    ],
                    "key_decisions": existing.key_decisions,
                    "participants_detected": existing.participants_detected,
                    "visual_frames": existing.visual_frames
                }
            }
            response = Response(response_data)
            response.set_cookie(
                'sessionid',
                request.session.session_key,
                max_age=60*60*24*30,
                httponly=True,
                samesite='Lax'
            )
            return response

        # 4. If NO: run normal transcript fetch
        result = fetch_youtube_transcript(youtube_url)
        if "error" in result:
            return Response({"error": result["error"]}, status=400)

        # Create or update Meeting record
        Meeting.objects.update_or_create(
            video_id=video_id,
            session_key=session_key,
            defaults={
                "youtube_url": youtube_url,
                "transcript_text": result.get("transcript_text", ""),
                "word_count": result.get("word_count", 0),
                "is_processed": False
            }
        )

        # 5. Return result with meeting_id
        meeting = Meeting.objects.get(video_id=video_id, session_key=session_key)
        request.session.save()
        result["cached"] = False
        result["meeting_id"] = str(meeting.id)
        
        response = Response(result)
        response.set_cookie(
            'sessionid',
            request.session.session_key,
            max_age=60*60*24*30,
            httponly=True,
            samesite='Lax'
        )
        return response

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
    @ratelimit(key='ip', rate='10/h', method='POST', block=True)
    def process_meeting_view(self, request):
        transcript_text = request.data.get("transcript_text", "")
        transcript_timestamps = request.data.get("transcript_timestamps", [])
        video_id = request.data.get("video_id", "")
        meeting_id = request.data.get("meeting_id", None)

        if not transcript_text or len(transcript_text.strip()) < 50:
            return Response({"error": "Transcript too short"}, status=400)

        # Get meeting instance if id provided, otherwise try to find it
        session_key = get_or_create_session_key(request)
        if not meeting_id:
            m = Meeting.objects.filter(video_id=video_id, session_key=session_key).first()
            if m:
                meeting_id = str(m.id)

        try:
            # Send to Celery background worker
            task = process_meeting_task.delay(
                transcript_text=transcript_text,
                transcript_timestamps=transcript_timestamps,
                video_id=video_id,
                meeting_id=meeting_id,
            )

            request.session.save()
            response = Response({
                "task_id": task.id,
                "status": "processing",
                "message": "Processing started in background"
            })
            response.set_cookie(
                'sessionid',
                request.session.session_key,
                max_age=60*60*24*30,
                httponly=True,
                samesite='Lax'
            )
            return response
        except Exception as e:
            # Redis not available fallback — run synchronously
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Celery failed, falling back to sync: {e}")
            
            # Re-collect logic for sync fallback (same as the task)
            key_timestamps = scan_for_key_timestamps(transcript_timestamps, max_frames=5, min_gap_seconds=30)
            timestamp_seconds_list = [t["timestamp_seconds"] for t in key_timestamps]
            frames = grab_frames_at_timestamps(video_id, timestamp_seconds_list) if (video_id and timestamp_seconds_list) else []
            for i, frame in enumerate(frames):
                if i < len(key_timestamps):
                    frame["category"] = key_timestamps[i]["category"]
            
            result = process_meeting(transcript_text, frames, video_id)
            
            # Save to DB manually
            if meeting_id:
                m = Meeting.objects.get(id=meeting_id)
                m.summary = result.get("summary", "")
                m.key_decisions = result.get("key_decisions", [])
                m.participants_detected = result.get("participants_detected", [])
                m.visual_frames = result.get("visual_frames", [])
                m.is_processed = True
                m.save()
            
            return Response(result)

    @action(
        detail=False,
        methods=["get"],
        url_path="task-status/(?P<task_id>[^/.]+)",
        permission_classes=[AllowAny]
    )
    def task_status(self, request, task_id=None):
        try:
            result = AsyncResult(task_id)
            state = result.state

            if state == "PENDING":
                return Response({"status": "pending"})
            elif state == "STARTED":
                return Response({"status": "processing"})
            elif state == "SUCCESS":
                return Response({
                    "status": "complete",
                    "result": result.get()
                })
            elif state == "FAILURE":
                return Response({
                    "status": "failed",
                    "error": str(result.info)
                }, status=500)
            else:
                return Response({"status": state.lower()})

        except Exception as e:
            return Response({
                "status": "error",
                "error": str(e)
            }, status=500)

    @action(detail=False, methods=["get"],
            url_path="history",
            permission_classes=[AllowAny])
    def history(self, request):
        """GET /api/v1/meetings/history/ — returns last 20 processed meetings."""
        session_key = get_or_create_session_key(request)
        queryset = Meeting.objects.filter(
            session_key=session_key, 
            is_processed=True
        ).order_by('-created_at')[:20]
        serializer = MeetingListSerializer(queryset, many=True)
        request.session.save()
        response = Response(serializer.data)
        response.set_cookie(
            'sessionid',
            request.session.session_key,
            max_age=60*60*24*30,
            httponly=True,
            samesite='Lax'
        )
        return response

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
