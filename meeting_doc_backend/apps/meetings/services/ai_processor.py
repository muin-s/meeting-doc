import json
import logging
from google import genai
from django.conf import settings

logger = logging.getLogger(__name__)

def process_transcript(transcript_text):
    if not settings.GEMINI_API_KEY:
        return {
            "error": "Gemini API key is not configured.",
            "raw": ""
        }
        
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        prompt = f"""You are an expert meeting analyst. Analyze the following meeting transcript
and return a JSON response with exactly this structure:
{{
  "summary": "2-3 paragraph clean summary of the entire meeting",
  "action_items": [
    {{
      "description": "what needs to be done",
      "assignee": "person's name or null if unknown",
      "priority": "high or medium or low",
      "due_date": "mentioned date or null"
    }}
  ],
  "key_decisions": ["decision 1", "decision 2"],
  "participants_detected": ["name1", "name2"]
}}

Return ONLY the JSON. No markdown, no explanation, no code blocks.
Just raw JSON.

TRANSCRIPT:
{transcript_text}
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        response_text = response.text.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
                
        response_text = response_text.strip()
        
        result = json.loads(response_text)
        return result
    except Exception as e:
        logger.error(f"Failed to process transcript with Gemini: {str(e)}")
        raw_text = response.text if 'response' in locals() and hasattr(response, 'text') else ""
        return {
            "error": f"Failed to parse AI response: {str(e)}",
            "raw": raw_text
        }