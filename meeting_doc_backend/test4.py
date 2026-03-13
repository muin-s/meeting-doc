import requests
from PIL import Image
from io import BytesIO

video_id = 'dQw4w9WgXcQ'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

r = requests.get(f'https://www.youtube.com/watch?v={video_id}', headers=headers)

idx = r.text.find('storyboard3_L')
chunk = r.text[idx:idx+500]

# Extract sqp - everything between sqp= and first |
sqp_start = chunk.find('sqp=') + 4
sqp_end = chunk.find('|', sqp_start)
sqp = chunk[sqp_start:sqp_end]
print('sqp:', sqp[:80])

# Extract per-level sqp tokens after the | separators
# Format is: width#height#count#cols#rows#duration#M#rs
parts = chunk.split('|')
print('Parts count:', len(parts))
for i, p in enumerate(parts[:8]):
    print(f'Part {i}:', p[:120])
