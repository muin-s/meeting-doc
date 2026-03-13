
import base64
from io import BytesIO
from apps.meetings.services.storyboard_analyzer import get_storyboard_info, fetch_sprite_sheet, slice_sprite_sheet

def grab_frames_at_timestamps(video_id, timestamps_seconds):
    """
    Grabs sprite thumbnails at specific timestamps and converts them to base64.
    """
    frames = []
    
    try:
        info = get_storyboard_info(video_id)
        if not info:
            # Return list of failed frames if info fetch fails
            return [
                {
                    "timestamp_seconds": t,
                    "thumbnail_base64": None,
                    "thumbnail_data_url": None
                }
                for t in timestamps_seconds
            ]
            
        # Cache for sprite sheets to avoid redundant network calls
        sprite_cache = {}

        for timestamp in timestamps_seconds:
            try:
                # thumb_index = timestamp // 5 (based on seconds_per_thumb=5)
                thumb_index = timestamp // info.get('seconds_per_thumb', 5)
                # sheet_index = thumb_index // 25 (based on thumbs_per_sheet=25)
                sheet_index = thumb_index // info.get('thumbs_per_sheet', 25)
                position_in_sheet = thumb_index % info.get('thumbs_per_sheet', 25)

                if sheet_index not in sprite_cache:
                    sprite_cache[sheet_index] = fetch_sprite_sheet(video_id, sheet_index, info)
                
                sprite_image = sprite_cache[sheet_index]
                if sprite_image is None:
                    frames.append({
                        "timestamp_seconds": timestamp,
                        "thumbnail_base64": None,
                        "thumbnail_data_url": None
                    })
                    continue

                thumbnails = slice_sprite_sheet(sprite_image, info)
                if position_in_sheet >= len(thumbnails):
                    frames.append({
                        "timestamp_seconds": timestamp,
                        "thumbnail_base64": None,
                        "thumbnail_data_url": None
                    })
                    continue

                img = thumbnails[position_in_sheet]
                
                # Convert PIL image to base64
                buffered = BytesIO()
                img.save(buffered, format="JPEG", quality=85)
                b64 = base64.b64encode(buffered.getvalue()).decode()

                frames.append({
                    "timestamp_seconds": timestamp,
                    "thumbnail_base64": b64,
                    "thumbnail_data_url": f"data:image/jpeg;base64,{b64}"
                })
                
            except Exception:
                frames.append({
                    "timestamp_seconds": timestamp,
                    "thumbnail_base64": None,
                    "thumbnail_data_url": None
                })
                
    except Exception:
        # Final fallback
        return [
            {
                "timestamp_seconds": t,
                "thumbnail_base64": None,
                "thumbnail_data_url": None
            }
            for t in timestamps_seconds
        ]

    return frames
