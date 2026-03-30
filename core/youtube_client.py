import yt_dlp
import datetime
import time

class YDLLogger:
    def debug(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): print(f"YT Error: {msg}")

class YouTubeClient:
    def __init__(self):
        # Base options optimized for speed
        self.ydl_opts_base = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'extract_flat': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'logger': YDLLogger(),
        }
        
        self.ydl_opts_stream = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
            'nocheckcertificate': True,
            'extract_flat': False,
            'logger': YDLLogger(),
        }

        # Memory Cache: { "query_str": (results, timestamp) }
        self._cache = {}
        self._cache_expiry = 600 # 10 minutes

    def search(self, query, limit=15, is_trending=False):
        """
        Searches YouTube and attempts to categorize results (Artists vs Songs).
        If is_trending is True, it filters for results from the last 30 days.
        Uses in-memory caching to prevent redundant network hits.
        """
        # Create a unique cache key based on query, limit, and trending status
        cache_key = f"{query}_{limit}_{is_trending}"
        curr_time = time.time()

        if cache_key in self._cache:
            results, timestamp = self._cache[cache_key]
            if curr_time - timestamp < self._cache_expiry:
                print(f"DEBUG: Cache HIT for '{query}'")
                return results

        results = []
        opts = self.ydl_opts_base.copy()
        
        if is_trending:
            # Only results from the last 30 days
            thirty_days_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y%m%d')
            opts['daterange'] = yt_dlp.utils.DateRange(start=thirty_days_ago)

        try:
            print(f"DEBUG: Fetching NEW results for '{query}'...")
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                
                if info and 'entries' in info:
                    for entry in info['entries']:
                        if not entry: continue
                        
                        is_artist = False
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
            
            # Store in cache
            if results:
                self._cache[cache_key] = (results, curr_time)
                # Cleanup cache if it grows too large
                if len(self._cache) > 100:
                    sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][1])
                    for k in sorted_keys[:20]: del self._cache[k]

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
