import requests
from PIL import Image
from io import BytesIO

video_id = 'dQw4w9WgXcQ'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# Get full page and find sqp
r = requests.get(f'https://www.youtube.com/watch?v={video_id}', headers=headers)

# Find the sqp value - it appears after storyboard3_L
idx = r.text.find('storyboard3_L')
if idx > 0:
    chunk = r.text[idx:idx+500]
    print('Raw chunk:')
    print(chunk[:300])
else:
    print('storyboard3_L not found in page')
    print('Page length:', len(r.text))
