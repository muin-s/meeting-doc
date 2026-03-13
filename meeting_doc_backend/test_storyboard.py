import requests
import re

video_id = 'dQw4w9WgXcQ'
url = f'https://www.youtube.com/watch?v={video_id}'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

r = requests.get(url, headers=headers)
print('Page status:', r.status_code)

matches = re.findall(r'https://i\.ytimg\.com/sb/[^\\\\"]+', r.text)
for m in matches[:10]:
    print('Found:', m)

matches2 = re.findall(r'storyboard3[^\\\\"]{0,100}', r.text)
for m in matches2[:5]:
    print('Storyboard ref:', m[:100])
