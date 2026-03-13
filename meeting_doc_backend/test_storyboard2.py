import requests
from PIL import Image
from io import BytesIO
import re

video_id = 'dQw4w9WgXcQ'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Get the sqp parameter from the page
r = requests.get(f'https://www.youtube.com/watch?v={video_id}', headers=headers)
match = re.search(r'https://i\.ytimg\.com/sb/' + video_id + r'/storyboard3_L\\\/\\\\.jpg\?sqp=([^|]+)\|', r.text)

if match:
    sqp = match.group(1)
    print('sqp found:', sqp[:50])
    
    # Try each level
    for level in [3, 2, 1, 0]:
        url = f'https://i.ytimg.com/sb/{video_id}/storyboard3_L{level}/M0.jpg?sqp={sqp}'
        resp = requests.get(url, headers=headers, timeout=10)
        print(f'Level {level}: {resp.status_code} - size: {len(resp.content)} bytes')
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            print(f'  Image size: {img.size}')
            break
else:
    print('sqp not found in page')
