import json
import logging
from google import genai
from django.conf import settings

logger = logging.getLogger(__name__)

def process_meeting(transcript_text, frames, video_id):
    """
    Unified processor that uses Gemini Vision to analyze transcript and visual frames.
    """
    if not settings.GEMINI_API_KEY:
        return {
            "error": "Gemini API key is not configured.",
            "summary": "Configuration error",
            "action_items": [],
            "key_decisions": [],
            "participants_detected": [],
            "visual_frames": []
        }

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        # Build contents list for Gemini Vision
        parts = []
        
        prompt = f"""You are an expert meeting analyst.
Analyze this meeting transcript and the visual frames captured
at key moments during the meeting.

Return ONLY valid JSON with exactly this structure:
{{
  "summary": "2-3 paragraph clean summary of the meeting",
  "action_items": [
    {{
      "description": "what needs to be done",
      "assignee": "person name or null",
      "priority": "high or medium or low",
      "due_date": "date string or null"
    }}
  ],
  "key_decisions": ["decision 1", "decision 2"],
  "participants_detected": ["name1", "name2"],
  "visual_frames": [
    {{
      "timestamp_seconds": 135,
      "label": "short label max 4 words",
      "category": "architecture or code or task_list or data or discussion",
      "description": "one sentence what is visible in this frame",
      "has_diagram": true or false,
      "has_code": true or false
    }}
  ]
}}

Return ONLY the JSON. No markdown. No explanation. No code blocks.

TRANSCRIPT:
{transcript_text}

The visual frames are attached as images in order of timestamp."""

        parts.append({"text": prompt})
        
        # Add frames that have data
        valid_frames = [f for f in frames if f.get("thumbnail_base64")]
        for frame in valid_frames:
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": frame["thumbnail_base64"]
                }
            })

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=parts
        )
        
        response_text = response.text.strip()
        
        # Clean up JSON if it contains markdown markers
        if response_text.startswith("```json"):
            response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        try:
            result = json.loads(response_text)
            
            # Merge frame metadata and add youtube URLs
            ai_visual_frames = result.get("visual_frames", [])
            for i, ai_frame in enumerate(ai_visual_frames):
                if i < len(valid_frames):
                    ai_frame["thumbnail_data_url"] = valid_frames[i]["thumbnail_data_url"]
                    ai_frame["youtube_url"] = f"https://www.youtube.com/watch?v={video_id}&t={valid_frames[i]['timestamp_seconds']}"
                else:
                    # Fallback if AI returned more frames than provided
                    ai_frame["thumbnail_data_url"] = None
                    ai_frame["youtube_url"] = f"https://www.youtube.com/watch?v={video_id}"
            
            # Ensure visual_frames is exactly as many as we sent (or at least capped)
            # Actually, let's keep what AI returned but ensure URLs are correct.
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI JSON response: {str(e)}")
            logger.debug(f"Raw response: {response_text}")
            raise Exception("Invalid JSON format from AI")

    except Exception as e:
        logger.error(f"Failed to process meeting with Gemini: {str(e)}")
        return {
            "error": f"Failed to parse AI response: {str(e)}",
            "summary": "Processing failed due to an error.",
            "action_items": [],
            "key_decisions": [],
            "participants_detected": [],
            "visual_frames": []
        }
