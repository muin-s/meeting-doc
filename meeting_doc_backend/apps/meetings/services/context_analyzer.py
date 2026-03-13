import json
import logging
from google import genai
from django.conf import settings

logger = logging.getLogger(__name__)

def analyze_key_moments(transcript_with_timestamps, visual_timestamps):
    """
    Cross reference visual timestamps with surrounding transcript text.
    Use Gemini to label the moments.
    """
    if not settings.GEMINI_API_KEY:
        return []

    moments_with_context = []
    
    for vt in visual_timestamps:
        ts = vt["estimated_timestamp_seconds"]
        
        # Get transcript text in a 10s window (5s before, 5s after)
        surrounding_text = []
        for entry in transcript_with_timestamps:
            start = entry.get("start", 0)
            if (ts - 5) <= start <= (ts + 5):
                surrounding_text.append(entry.get("text", ""))
        
        context_str = " ".join(surrounding_text)
        if not context_str:
            context_str = "[No speech detected]"
            
        moments_with_context.append({
            "timestamp_seconds": ts,
            "transcript_context": context_str
        })

    # Prepare Gemini Prompt
    prompt = f"""You are analyzing key moments in a meeting recording. 
For each visual moment below, I will give you the transcript 
text spoken around that time. Label each moment.

Return ONLY a JSON array with this exact structure:
[
  {{
    "timestamp_seconds": 135,
    "label": "short label max 4 words",
    "description": "one sentence description",
    "confidence": "high or medium or low"
  }}
]

Visual moments with surrounding transcript:
{json.dumps(moments_with_context, indent=2)}

Return ONLY the JSON array. No markdown. No explanation.
"""

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        response_text = response.text.strip()
        
        # Clean potential markdown
        if response_text.startswith("```json"):
            response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
        
        result = json.loads(response_text.strip())
        return result
    except Exception as e:
        logger.error(f"Failed to analyze key moments with Gemini: {str(e)}")
        # Fallback
        return [
            {
                "timestamp_seconds": m["timestamp_seconds"],
                "label": f"Key Moment {i+1}",
                "description": "Automatically detected visual transition.",
                "confidence": "low"
            }
            for i, m in enumerate(moments_with_context)
        ]