import json
import logging
import base64
from google import genai
from django.conf import settings

logger = logging.getLogger(__name__)

def process_meeting(transcript_text, frames, video_id):
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        prompt = f"""You are an expert meeting analyst.
Analyze this meeting transcript and the visual frames captured at key moments.

Return ONLY valid JSON with exactly this structure:
{{
  "summary": "2-3 paragraph clean summary",
  "action_items": [
    {{
      "description": "what needs to be done",
      "assignee": "person name or null",
      "priority": "high or medium or low",
      "due_date": null
    }}
  ],
  "key_decisions": ["decision 1"],
  "participants_detected": ["name1"],
  "visual_frames": [
    {{
      "timestamp_seconds": 0,
      "label": "max 4 words",
      "category": "architecture or code or task_list or data or discussion",
      "description": "one sentence description",
      "has_diagram": false,
      "has_code": false
    }}
  ]
}}

Return ONLY the JSON. No markdown. No explanation.

TRANSCRIPT:
{transcript_text}"""

        parts = [{"text": prompt}]

        for frame in frames:
            if frame.get("thumbnail_base64"):
                parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": frame["thumbnail_base64"]
                    }
                })

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[{"role": "user", "parts": parts}]
        )
        
        result_text = response.text.strip()
        # Strip markdown if present
        if result_text.startswith("```"):
            # Find the first and last triple backticks
            start_index = result_text.find("```")
            end_index = result_text.rfind("```")
            if start_index != -1 and end_index != -1 and start_index != end_index:
                content = result_text[start_index+3:end_index].strip()
                if content.startswith("json"):
                    result_text = content[4:].strip()
                else:
                    result_text = content
        
        result = json.loads(result_text)
        
        # Merge thumbnail data back into visual_frames
        for i, vf in enumerate(result.get("visual_frames", [])):
            if i < len(frames):
                vf["thumbnail_data_url"] = frames[i].get("thumbnail_data_url")
                vf["youtube_url"] = f"https://www.youtube.com/watch?v={video_id}&t={vf.get('timestamp_seconds', 0)}"
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}")
        return _empty_result()
    except Exception as e:
        logger.error(f"Failed to process meeting with Gemini: {e}")
        return _empty_result()

def _empty_result():
    return {
        "summary": "Processing failed due to an error.",
        "action_items": [],
        "key_decisions": [],
        "participants_detected": [],
        "visual_frames": []
    }
