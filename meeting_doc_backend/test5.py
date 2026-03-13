import requests
from PIL import Image
from io import BytesIO

video_id = 'dQw4w9WgXcQ'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

r = requests.get(f'https://www.youtube.com/watch?v={video_id}', headers=headers)
idx = r.text.find('storyboard3_L')
chunk = r.text[idx:idx+600]
parts = chunk.split('|')

sqp_start = chunk.find('sqp=') + 4
sqp_end = chunk.find('|', sqp_start)
sqp = chunk[sqp_start:sqp_end]

# Level 2 = 160x90, 5x5 grid - best balance of quality vs size
# Part 3 = Level 2, rs token is after rs$
level = 2
part = parts[3]
rs_token = part.split('rs$')[1] if 'rs$' in part else ''
print('rs token:', rs_token)

url = f'https://i.ytimg.com/sb/{video_id}/storyboard3_L{level}/M0.jpg?sqp={sqp}&rs={rs_token}'
print('URL:', url[:100])

resp = requests.get(url, headers=headers, timeout=10)
print('Status:', resp.status_code)
print('Size:', len(resp.content), 'bytes')

if resp.status_code == 200:
    img = Image.open(BytesIO(resp.content))
    print('Image dimensions:', img.size)
    img.save('test_sprite.jpg')
    print('Saved as test_sprite.jpg')
