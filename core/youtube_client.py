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
        Searches YouTube and prioritizes MUSICAL content.
        Uses flat extraction for maximum speed and applies soft heuristics for filtering.
        """
        cache_key = f"{query}_{limit}_{is_trending}"
        curr_time = time.time()

        if cache_key in self._cache:
            results, timestamp = self._cache[cache_key]
            if curr_time - timestamp < self._cache_expiry:
                print(f"DEBUG: Cache HIT for '{query}'")
                return results

        results = []
        # Soft Query Refinement
        refined_query = query
        music_keywords = ["song", "music", "audio", "video", "reels", "hits", "lyrics"]
        if not any(k in query.lower() for k in music_keywords) and not query.startswith(("http", "www")):
            refined_query = f"{query} song"
            
        opts = self.ydl_opts_base.copy()
        opts['extract_flat'] = True # FAST is priority for Home/Search results
        
        if is_trending:
            thirty_days_ago = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y%m%d')
            opts['daterange'] = yt_dlp.utils.DateRange(start=thirty_days_ago)

        try:
            print(f"DEBUG: Fetching FAST results for '{refined_query}'...")
            with yt_dlp.YoutubeDL(opts) as ydl:
                # Ask for significantly more results to ensure density (multiplier)
                search_n = limit + 20 if limit > 15 else limit + 5
                info = ydl.extract_info(f"ytsearch{search_n}:{refined_query}", download=False)
                
                if info and 'entries' in info:
                    for entry in info['entries']:
                        if not entry: continue
                        
                        title = entry.get('title', '').lower()
                        # Soft Guard 1: Basic Duration check (Relaxed for Home/Discovery)
                        duration = entry.get('duration')
                        is_home = limit > 15
                        if isinstance(duration, (int, float)) and duration > 0 and not is_home:
                            if duration < 20 or duration > 1800: continue
                        
                        # Soft Guard 2: Exclude obvious non-music keywords
                        exclude = ["full movie", "news", "interview", "documentary", "tutorial", "unboxing"]
                        if any(x in title for x in exclude): continue

                        results.append({
                            'id': entry.get('id'),
                            'title': entry.get('title', 'Unknown'),
                            'url': entry.get('url') if entry.get('url') else f"https://www.youtube.com/watch?v={entry.get('id')}",
                            'duration': entry.get('duration'),
                            'thumbnail': entry.get('thumbnail') or f"https://img.youtube.com/vi/{entry.get('id')}/mqdefault.jpg",
                            'is_artist': False,
                            'uploader': entry.get('uploader')
                        })
                        if len(results) >= limit: break
            
            if results:
                self._cache[cache_key] = (results, curr_time)
                if len(self._cache) > 100:
                    sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][1])
                    for k in sorted_keys[:20]: del self._cache[k]

        except Exception as e:
            print(f"Error searching: {e}")
            
        print(f"DEBUG: Returning {len(results)} search results.")
        return results

    def get_stream_url(self, video_url):
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts_stream) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return info.get('url'), info.get('title')
        except Exception as e:
            print(f"Error getting stream: {e}")
            return None, None
