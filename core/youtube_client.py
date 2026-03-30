import yt_dlp

class YouTubeClient:
    def __init__(self):
        # Base options
        self.ydl_opts_base = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'extract_flat': True,
            'ignoreerrors': True,
            'no_warnings': True,
        }
        
        self.ydl_opts_stream = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'key': 'FFmpegExtractAudio',
        }

    def search(self, query, limit=15):
        """
        Searches YouTube and attempts to categorize results (Artists vs Songs).
        """
        results = []
        opts = self.ydl_opts_base.copy()
        
        try:
            print(f"DEBUG: Categorized search for '{query}' (Limit: {limit})...")
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Use ytsearchX for videos
                info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                
                if info and 'entries' in info:
                    for entry in info['entries']:
                        if not entry: continue
                        
                        is_artist = False
                        # Channel/Artist detection: Check for 'channel_url' or specific extractor keys
                        if entry.get('_type') == 'url' and 'channel' in entry.get('url', ''):
                            is_artist = True
                        elif entry.get('ie_key') == 'YoutubeChannel':
                             is_artist = True

                        results.append({
                            'id': entry.get('id'),
                            'title': entry.get('title', 'Unknown'),
                            'url': entry.get('url') if entry.get('url') else f"https://www.youtube.com/watch?v={entry.get('id')}",
                            'duration': entry.get('duration'),
                            'thumbnail': entry.get('thumbnail') or f"https://img.youtube.com/vi/{entry.get('id')}/mqdefault.jpg",
                            'is_artist': is_artist,
                            'uploader': entry.get('uploader')
                        })
        except Exception as e:
            print(f"Error searching: {e}")
            
        print(f"DEBUG: Returning {len(results)} results")
        return results

    def get_stream_url(self, video_url):
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts_stream) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return info.get('url'), info.get('title')
        except Exception as e:
            print(f"Error getting stream: {e}")
            return None, None
