import requests
import numpy as np
from PIL import Image
from io import BytesIO

def get_storyboard_info(video_id):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
            
        text = response.text
        idx = text.find('storyboard3_L')
        if idx == -1:
            return None
            
        chunk = text[idx:idx+800]
        # sqp is between sqp= and first |
        sqp_start = chunk.find('sqp=')
        if sqp_start == -1:
            return None
        sqp_start += 4
        sqp_end = chunk.find('|', sqp_start)
        if sqp_end == -1:
            return None
        sqp = chunk[sqp_start:sqp_end]
        
        parts = chunk.split('|')
        # Part 3 is Level 2 (index 2 in the sprite tokens after the first split, but index 3 in total split)
        # Based on user's test: Part 1: L0, Part 2: L1, Part 3: L2
        if len(parts) <= 3:
            return None
            
        part_l2 = parts[3]
        rs_token = part_l2.split('rs$')[1] if 'rs$' in part_l2 else ''
        
        return {
            "sqp": sqp,
            "rs_token": rs_token,
            "level": 2,
            "cols": 5,
            "rows": 5,
            "thumb_width": 160,
            "thumb_height": 90,
            "seconds_per_thumb": 5,
            "thumbs_per_sheet": 25
        }
    except Exception as e:
        print(f"Failed to get storyboard info: {e}")
        return None

def fetch_sprite_sheet(video_id, sheet_index, info):
    url = f"https://i.ytimg.com/sb/{video_id}/storyboard3_L{info['level']}/M{sheet_index}.jpg?sqp={info['sqp']}&rs={info['rs_token']}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        return Image.open(BytesIO(response.content))
    except Exception:
        return None

def slice_sprite_sheet(sprite_image, info):
    thumbnails = []
    width, height = sprite_image.size
    for row in range(info['rows']):
        for col in range(info['cols']):
            left = col * info['thumb_width']
            top = row * info['thumb_height']
            right = left + info['thumb_width']
            bottom = top + info['thumb_height']
            
            if right <= width and bottom <= height:
                thumb = sprite_image.crop((left, top, right, bottom))
                thumbnails.append(thumb)
    return thumbnails

def image_diff_score(img1, img2):
    try:
        # Resize to small gray for comparison speed
        i1 = img1.convert("L").resize((80, 45))
        i2 = img2.convert("L").resize((80, 45))
        a1 = np.array(i1).astype(float)
        a2 = np.array(i2).astype(float)
        diff = np.mean(np.abs(a1 - a2)) / 255.0
        return float(diff)
    except Exception:
        return 0.0

def detect_significant_frames(video_id, diff_threshold=0.15, min_gap_seconds=5):
    try:
        info = get_storyboard_info(video_id)
        if not info or not info['sqp']:
            return []
            
        all_thumbnails = []
        sheet_index = 0
        
        while len(all_thumbnails) < 108: # Standard total thumbnails
            sprite = fetch_sprite_sheet(video_id, sheet_index, info)
            if sprite is None:
                break
            thumbs = slice_sprite_sheet(sprite, info)
            all_thumbnails.extend(thumbs)
            sheet_index += 1
            if sheet_index > 10:
                break
                
        if len(all_thumbnails) < 2:
            return []
            
        significant = []
        last_flagged_seconds = -min_gap_seconds
        
        for i in range(1, len(all_thumbnails)):
            score = image_diff_score(all_thumbnails[i-1], all_thumbnails[i])
            current_seconds = i * info['seconds_per_thumb']
            gap = current_seconds - last_flagged_seconds
            
            if score > diff_threshold and gap >= min_gap_seconds:
                significant.append({
                    "thumbnail_index": i,
                    "estimated_timestamp_seconds": current_seconds,
                    "diff_score": round(score, 3),
                    "thumbnail": all_thumbnails[i]
                })
                last_flagged_seconds = current_seconds
                
        return significant
    except Exception as e:
        print(f"Storyboard detection failed: {e}")
        return []
