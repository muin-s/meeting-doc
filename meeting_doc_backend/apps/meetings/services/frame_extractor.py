import subprocess
import os
import shutil
from PIL import Image

def format_time(seconds):
    """Convert integer seconds to HH:MM:SS string"""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def extract_hd_frame(video_id, timestamp_seconds, output_dir, fallback_image=None):
    """
    Use yt-dlp to download a 2s section and ffmpeg to extract middle frame.
    Gracefully fall back to fallback_image if tools fail.
    """
    final_image_path = os.path.join(output_dir, f"{video_id}_{timestamp_seconds}.jpg")
    
    # If already exists, return
    if os.path.exists(final_image_path):
        return final_image_path

    start_time = max(0, timestamp_seconds - 1)
    end_time = timestamp_seconds + 1
    
    # YouTube URL
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # File naming
    video_filename = f"{video_id}_{timestamp_seconds}_temp.mp4"
    temp_video_path = os.path.join(output_dir, video_filename)
    
    # Check for yt-dlp and ffmpeg
    yt_dlp_path = shutil.which("yt-dlp")
    ffmpeg_path = shutil.which("ffmpeg")
    
    if not yt_dlp_path or not ffmpeg_path:
        if fallback_image:
            fallback_image.save(final_image_path, "JPEG")
            return final_image_path
        return None

    try:
        # Step 1: Download section using yt-dlp
        section = f"*{format_time(start_time)}-{format_time(end_time)}"
        
        cmd_dlp = [
            "yt-dlp",
            # We use --download-sections to avoid full download
            "--download-sections", section,
            "-f", "bestvideo[height<=720]",
            "-o", temp_video_path,
            url
        ]
        
        # Increased timeout as downloads can take time
        subprocess.run(cmd_dlp, check=True, timeout=90, capture_output=True)
        
        # Step 2: Extract frame using ffmpeg
        if os.path.exists(temp_video_path):
            cmd_ffmpeg = [
                "ffmpeg", "-y",
                "-i", temp_video_path,
                "-vf", "select=eq(n\,15)", # Attempt to get middle frame
                "-vframes", "1",
                final_image_path
            ]
            subprocess.run(cmd_ffmpeg, check=True, timeout=20, capture_output=True)
            
            # Clean up temp video
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
    
    except Exception as e:
        print(f"Frame extraction failed for {video_id} at {timestamp_seconds}: {str(e)}")
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
            
    # Final check: if yt-dlp/ffmpeg failed to create image, use fallback
    if not os.path.exists(final_image_path) and fallback_image:
        try:
            fallback_image.save(final_image_path, "JPEG")
            return final_image_path
        except Exception as e:
            print(f"Failed to save fallback image: {e}")
            
    return final_image_path if os.path.exists(final_image_path) else None
