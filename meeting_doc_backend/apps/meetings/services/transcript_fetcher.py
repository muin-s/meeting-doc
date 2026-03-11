from youtube_transcript_api import YouTubeTranscriptApi
import re

def extract_video_id(url):
    """
    Extracts the video ID from a YouTube URL.
    Handles various formats:
    - https://www.youtube.com/watch?v=dQw4w9WgXcQ
    - https://youtu.be/dQw4w9WgXcQ
    - https://youtube.com/v/dQw4w9WgXcQ
    - https://youtube.com/embed/dQw4w9WgXcQ
    """
    video_id_match = re.search(r'(?:v=|\/v\/|embed\/|youtu.be\/|\/shorts\/)([a-zA-Z0-9_-]{11})', url)
    if video_id_match:
        return video_id_match.group(1)
    return None

def fetch_youtube_transcript(url):
    """
    Fetches the transcript for a YouTube video and joins it into a single string.
    Returns a dictionary with the transcript text, video ID, and word count.
    """
    video_id = extract_video_id(url)
    if not video_id:
        return {"error": "Invalid YouTube URL"}

    try:
        ytt = YouTubeTranscriptApi()
        fetched = ytt.fetch(video_id)
        # Join all transcript parts into one big string
        transcript_text = " ".join([snippet.text for snippet in fetched])
        
        return {
            "transcript_text": transcript_text,
            "video_id": video_id,
            "word_count": len(transcript_text.split())
        }
    except Exception as e:
        return {"error": str(e)}

