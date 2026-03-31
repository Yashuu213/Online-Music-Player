
import yt_dlp
import datetime

def debug_search(query, limit=5):
    refined_query = f"{query} official song audio"
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'extract_flat': False, # What I changed to
        'ignoreerrors': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch{limit + 10}:{refined_query}", download=False)
        if 'entries' in info:
            for i, entry in enumerate(info['entries']):
                if not entry:
                    print(f"[{i+1}] NULL Entry")
                    continue
                categories = [c.lower() for c in entry.get('categories', [])]
                duration = entry.get('duration', 0)
                print(f"[{i+1}] Title: {entry.get('title')}")
                print(f"    Categories: {categories}")
                print(f"    Duration: {duration}")
                
                # Check my guards
                is_music = 'music' in categories
                is_duration = 30 < duration < 1200
                print(f"    Pass Guard Music: {is_music}")
                print(f"    Pass Guard Dur: {is_duration}")
                print("-" * 20)

debug_search("latest bollywood music releases")
