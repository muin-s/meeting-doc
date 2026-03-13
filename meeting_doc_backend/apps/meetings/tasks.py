from celery import shared_task
from apps.meetings.services.keyword_scanner import scan_for_key_timestamps
from apps.meetings.services.frame_grabber import grab_frames_at_timestamps
from apps.meetings.services.unified_processor import process_meeting
from apps.meetings.models import Meeting, ActionItem
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=2, soft_time_limit=120)
def process_meeting_task(
    self,
    transcript_text,
    transcript_timestamps,
    video_id,
    meeting_id=None
):
    try:
        logger.info(f"Processing meeting task for video_id: {video_id}")

        # Step 1: keyword scan
        key_timestamps = scan_for_key_timestamps(
            transcript_timestamps,
            max_frames=5,
            min_gap_seconds=30
        )
        timestamp_seconds_list = [
            t["timestamp_seconds"] for t in key_timestamps
        ]
        logger.info(f"Key timestamps: {timestamp_seconds_list}")

        # Step 2: grab frames
        frames = []
        if video_id and timestamp_seconds_list:
            frames = grab_frames_at_timestamps(
                video_id, timestamp_seconds_list
            )
            for i, frame in enumerate(frames):
                if i < len(key_timestamps):
                    frame["category"] = key_timestamps[i]["category"]
            logger.info(f"Frames grabbed: {len(frames)}")

        # Step 3: Gemini Vision
        result = process_meeting(transcript_text, frames, video_id)
        logger.info("Gemini processing complete")

        # Step 4: save to DB
        if meeting_id:
            try:
                meeting = Meeting.objects.get(id=meeting_id)
                meeting.summary = result.get("summary", "")
                meeting.key_decisions = result.get("key_decisions", [])
                meeting.participants_detected = result.get(
                    "participants_detected", []
                )
                meeting.visual_frames = result.get("visual_frames", [])
                meeting.is_processed = True
                meeting.save()

                # Also save action items
                ActionItem.objects.filter(meeting=meeting).delete()
                for item in result.get("action_items", []):
                    ActionItem.objects.create(
                        meeting=meeting,
                        description=item.get("description", ""),
                        assignee_name=item.get("assignee") or "",
                        priority=item.get("priority", "medium"),
                        due_date=item.get("due_date"),
                    )
                logger.info(f"Saved to DB: meeting {meeting_id}")
            except Meeting.DoesNotExist:
                logger.error(f"Meeting {meeting_id} not found")

        return result

    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        raise self.retry(exc=exc, countdown=5)
