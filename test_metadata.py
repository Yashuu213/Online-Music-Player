
import yt_dlp

def test_search(query, extract_flat=True):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'extract_flat': extract_flat,
        'ignoreerrors': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch5:{query}", download=False)
        if 'entries' in info:
            for i, entry in enumerate(info['entries']):
                if not entry: continue
                print(f"[{i+1}] Title: {entry.get('title')}")
                print(f"    Duration: {entry.get('duration')}")
                print(f"    Categories: {entry.get('categories')}")
                print(f"    Tags: {len(entry.get('tags', [])) if entry.get('tags') else 0}")
                print(f"    Type: {entry.get('_type')}")

print("--- Extract Flat: True ---")
test_search("Arijit Singh", extract_flat=True)
print("\n--- Extract Flat: False ---")
test_search("Arijit Singh", extract_flat=False)
