import yt_dlp

class YouTubeClient:
    def __init__(self):
        self.ydl_opts_search = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': False, # Turn on logging
            'extract_flat': 'in_playlist',  # Better for search results
            'default_search': 'ytsearch10', 
            'ignoreerrors': True,
            'no_warnings': False,
        }
        
        self.ydl_opts_stream = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'key': 'FFmpegExtractAudio',
        }

    def search(self, query):
        """
        Searches YouTube for the query and returns a list of results.
        """
        results = []
        try:
            print(f"DEBUG: Searching for '{query}' using yt-dlp...")
            with yt_dlp.YoutubeDL(self.ydl_opts_search) as ydl:
                # Force ytsearch explicitly in the query if not already there, 
                # though default_search should handle it.
                info = ydl.extract_info(f"ytsearch10:{query}", download=False)
                
                print(f"DEBUG: Search finished. Info keys: {info.keys() if info else 'None'}")
                
                if info and 'entries' in info:
                    entries = list(info['entries']) # consume generator if it is one
                    print(f"DEBUG: Entries found: {len(entries)}")
                    
                    for entry in entries:
                        if not entry: continue
                        # print(f"DEBUG: Entry keys: {entry.keys()}")
                        
                        results.append({
                            'id': entry.get('id'),
                            'title': entry.get('title'),
                            'url': entry.get('url') if entry.get('url') else f"https://www.youtube.com/watch?v={entry.get('id')}",
                            'duration': entry.get('duration'),
                            'thumbnail': entry.get('thumbnail') or f"https://img.youtube.com/vi/{entry.get('id')}/mqdefault.jpg"
                        })
                else:
                    print("DEBUG: No 'entries' key in info.")
                    if info:
                        print(f"DEBUG: Info dump: {str(info)[:200]}...")

        except Exception as e:
            print(f"Error searching: {e}")
            import traceback
            traceback.print_exc()
            
        print(f"DEBUG: Returning {len(results)} results")
        return results

    def get_stream_url(self, video_url):
        """
        Getting the actual stream URL for a video.
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts_stream) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return info.get('url'), info.get('title')
        except Exception as e:
            print(f"Error getting stream: {e}")
            return None, None
