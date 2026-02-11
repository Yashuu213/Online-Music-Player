from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, 
    QLabel, QSlider, QMessageBox, QTabWidget, QMenu, QInputDialog,
    QStackedWidget, QFrame, QSizePolicy
)
import sys
import os

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QIcon, QPixmap, QAction
import requests
import random
from ui.styles import PREMIUM_THEME
from ui.now_playing import NowPlayingWidget
from ui.custom_widgets import SongItemWidget
from ui.icons import get_icon, SVG_SEARCH
from core.youtube_client import YouTubeClient
from core.audio_player import AudioPlayer
from core.storage import StorageManager

# --- Threads (Unchanged logic) ---
class SearchThread(QThread):
    results_found = pyqtSignal(list, str) 
    error_occurred = pyqtSignal(str)

    def __init__(self, client, query, context="search"):
        super().__init__()
        self.client = client
        self.query = query
        self.context = context

    def run(self):
        try:
            results = self.client.search(self.query)
            self.results_found.emit(results, self.context)
        except Exception as e:
            self.error_occurred.emit(str(e))

class StreamUrlThread(QThread):
    url_found = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, client, video_url):
        super().__init__()
        self.client = client
        self.video_url = video_url

    def run(self):
        try:
            url, title = self.client.get_stream_url(self.video_url)
            if url:
                self.url_found.emit(url, title)
            else:
                self.error_occurred.emit("Could not extract stream URL.")
        except Exception as e:
            self.error_occurred.emit(str(e))

class ThumbnailLoader(QThread):
    thumbnail_loaded = pyqtSignal(object, QPixmap, str) # item, pixmap, video_id

    def __init__(self, item_widget, url, video_id):
        super().__init__()
        self.item_widget = item_widget
        self.url = url
        self.video_id = video_id

    def run(self):
        try:
            data = requests.get(self.url).content
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            self.thumbnail_loaded.emit(self.item_widget, pixmap, self.video_id)
        except:
            pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SteamTune - Premium")
        self.setGeometry(100, 100, 1000, 800)
        self.setStyleSheet(PREMIUM_THEME)

        self.youtube_client = YouTubeClient()
        self.audio_player = AudioPlayer()
        self.storage = StorageManager()
        
        self.current_video = None
        self.next_queue = []
        self.image_cache = {} # VideoID -> QPixmap
        self.next_queue = []
        self.image_cache = {} # VideoID -> QPixmap
        self.history_session = [] # Track session history for "Previous" button
        self.played_video_ids = set() # Track all played IDs to avoid repeats
        self.was_playing = False # For auto-play state tracking
        
        self.init_ui()
        self.load_history() 
        self.load_playlists()
        
        self.load_startup_content()
        
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_progress)

    def init_ui(self):
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # --- Page 0: Browser ---
        self.browser_page = QWidget()
        browser_layout = QVBoxLayout(self.browser_page)
        browser_layout.setContentsMargins(0,0,0,0)
        browser_layout.setSpacing(0)
        
        # --- Pikachuu Header ---
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet("background: transparent; border-bottom: 1px solid rgba(255,255,255,0.05);")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)
        
        brand_label = QLabel("Pikachuu")
        brand_label.setStyleSheet("font-size: 28px; font-weight: 800; color: #BB86FC; letter-spacing: 1px;")
        header_layout.addWidget(brand_label)
        
        header_layout.addStretch()
        
        # GIF Logic
        gif_label = QLabel()
        gif_label.setFixedSize(60, 60)
        
        # Determine path safely (Dev vs Frozen)
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            # Go up one level from ui/ to root
            base_path = os.path.join(base_path, "..") 
            
        gif_path = os.path.join(base_path, "pii.gif")
        
        if os.path.exists(gif_path):
            movie = QPixmap(gif_path) # Just static for now, or use QMovie if animated needed, 
                                      # but QPixmap is safer for basic display.
                                      # Actually user wanted GIF. 
            # Use QMovie for GIF
            from PyQt6.QtGui import QMovie
            self.pikachu_movie = QMovie(gif_path)
            self.pikachu_movie.setScaledSize(QSize(60, 60))
            gif_label.setMovie(self.pikachu_movie)
            self.pikachu_movie.start()
        else:
            gif_label.setText("⚡")
            gif_label.setStyleSheet("font-size: 30px; color: yellow;")
            
        header_layout.addWidget(gif_label)
        browser_layout.addWidget(header)
        
        # Tabs container with padding
        tabs_container = QWidget()
        tabs_layout = QVBoxLayout(tabs_container)
        tabs_layout.setContentsMargins(20, 20, 20, 0)
        
        self.tabs = QTabWidget()
        tabs_layout.addWidget(self.tabs)
        
        browser_layout.addWidget(tabs_container)
        
        self.search_tab = QWidget()
        self.init_search_tab()
        self.tabs.addTab(self.search_tab, "Search")
        
        self.history_tab = QWidget()
        self.init_history_tab()
        self.tabs.addTab(self.history_tab, "History")

        self.playlists_tab = QWidget()
        self.init_playlists_tab()
        self.tabs.addTab(self.playlists_tab, "Playlists")
        
        # Spacer to push mini player down if needed (not really needed with VBox)
        # browser_layout.addStretch() 
        
        self.init_mini_player(browser_layout)
        
        self.stack.addWidget(self.browser_page)
        
        # --- Page 1: Now Playing ---
        self.now_playing_page = NowPlayingWidget() 
        self.now_playing_page.back_clicked.connect(self.switch_to_browser)
        self.now_playing_page.next_song_requested.connect(self.play_video)
        self.now_playing_page.play_pause_clicked.connect(self.play_pause)
        self.now_playing_page.stop_clicked.connect(self.stop_music)
        self.now_playing_page.seek_requested.connect(self.set_position)
        
        # New Controls
        self.now_playing_page.next_clicked.connect(self.play_next_in_queue)
        self.now_playing_page.prev_clicked.connect(self.play_previous_song)
        
        self.stack.addWidget(self.now_playing_page)

    def switch_to_browser(self):
        self.stack.setCurrentIndex(0)

    def switch_to_now_playing(self):
        self.stack.setCurrentIndex(1)
        # Refresh visuals if needed
        if self.current_video:
             pixmap = self.image_cache.get(self.current_video['id'])
             self.now_playing_page.update_info(self.current_video, pixmap)
             self.now_playing_page.update_play_btn(self.audio_player.is_playing())

    def init_mini_player(self, parent_layout):
        self.mini_player_frame = QWidget()
        # Elevated Glass effect
        self.mini_player_frame.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2b2b2b, stop:1 #1a1a1a);
                border-top: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        self.mini_player_frame.setFixedHeight(80)
        
        layout = QHBoxLayout(self.mini_player_frame)
        layout.setContentsMargins(30, 10, 30, 10)
        layout.setSpacing(20)
        
        self.mini_info = QLabel("Ready to Play")
        self.mini_info.setStyleSheet("color: #E0E0E0; font-weight: 600; font-size: 15px;")
        layout.addWidget(self.mini_info)
        
        layout.addStretch()
        
        play_btn = QPushButton("Play / Pause") 
        play_btn.setFixedSize(120, 40)
        play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        play_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                font-weight: bold;
            }
            QPushButton:hover { background: rgba(255, 255, 255, 0.2); }
        """)
        play_btn.clicked.connect(self.play_pause)
        layout.addWidget(play_btn)
        
        expand_btn = QPushButton("Expand")
        expand_btn.setFixedSize(100, 40)
        expand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        expand_btn.clicked.connect(self.switch_to_now_playing)
        layout.addWidget(expand_btn)
        
        parent_layout.addWidget(self.mini_player_frame)

    # --- Tabs ---

    def init_search_tab(self):
        layout = QVBoxLayout(self.search_tab)
        layout.setContentsMargins(30, 20, 30, 0)
        layout.setSpacing(20)
        
        input_layout = QHBoxLayout()
        input_layout.setSpacing(15)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search songs, artists, or mix...")
        self.search_input.setFixedHeight(45)
        self.search_input.returnPressed.connect(self.start_search)
        
        search_btn = QPushButton()
        search_btn.setIcon(get_icon(SVG_SEARCH, "black"))
        search_btn.setIconSize(QSize(20, 20))
        search_btn.setFixedSize(45, 45)
        search_btn.setObjectName("primaryBtn")
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # Circular button override
        search_btn.setStyleSheet("""
            QPushButton#primaryBtn {
                border-radius: 22px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #BB86FC, stop:1 #985EFF);
            }
            QPushButton#primaryBtn:hover {
                margin-top: -2px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #C495FD, stop:1 #A673FF);
            }
        """)
        search_btn.clicked.connect(self.start_search)
        
        input_layout.addWidget(self.search_input)
        input_layout.addWidget(search_btn)
        layout.addLayout(input_layout)
        
        self.results_list = QListWidget()
        self.results_list.setCursor(Qt.CursorShape.PointingHandCursor)
        self.results_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.results_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_list.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(self.results_list)
        
        self.loading_label = QLabel("")
        self.loading_label.setStyleSheet("color: #888; font-style: italic;")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.loading_label)

    def init_history_tab(self):
        layout = QVBoxLayout(self.history_tab)
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.history_list)
        
        refresh_btn = QPushButton("Refresh History")
        refresh_btn.clicked.connect(self.load_history)
        layout.addWidget(refresh_btn)

    def init_playlists_tab(self):
        layout = QHBoxLayout(self.playlists_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Left Sidebar
        left_container = QWidget()
        left_container.setFixedWidth(260)
        left_container.setStyleSheet("""
            QWidget {
                background: rgba(0, 0, 0, 0.2);
                border-right: 1px solid rgba(255, 255, 255, 0.05);
            }
        """)
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(20, 25, 20, 20)
        left_layout.setSpacing(15)
        
        # Header
        lib_label = QLabel("YOUR LIBRARY")
        lib_label.setStyleSheet("color: #BB86FC; font-weight: 800; font-size: 13px; letter-spacing: 1.5px;")
        left_layout.addWidget(lib_label)
        
        # List of Playlists
        self.playlist_names = QListWidget()
        self.playlist_names.setCursor(Qt.CursorShape.PointingHandCursor)
        self.playlist_names.setStyleSheet("""
             QListWidget::item { 
                padding: 12px; 
                border-radius: 8px; 
                margin-bottom: 5px;
             }
             QListWidget::item:selected {
                background: rgba(187, 134, 252, 0.2);
                color: #FFF;
                font-weight: bold;
             }
        """)
        self.playlist_names.itemClicked.connect(self.load_playlist_items)
        left_layout.addWidget(self.playlist_names)
        
        # New Button
        new_btn = QPushButton("+ New Playlist")
        new_btn.setObjectName("primaryBtn")
        new_btn.setFixedHeight(45)
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.clicked.connect(self.create_playlist)
        left_layout.addWidget(new_btn)
        
        layout.addWidget(left_container)
        
        # Right Side - Tracks
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(30, 20, 30, 20)
        
        tracks_header = QLabel("Playlist Tracks")
        tracks_header.setStyleSheet("font-size: 24px; font-weight: 700; color: white; margin-bottom: 10px;")
        right_layout.addWidget(tracks_header)
        
        self.playlist_items = QListWidget()
        self.playlist_items.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.playlist_items.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlist_items.customContextMenuRequested.connect(self.show_context_menu)
        
        right_layout.addWidget(self.playlist_items)
        layout.addWidget(right_container)

    # --- Logic ---

    def load_startup_content(self):
        history = self.storage.get_history()
        
        # List of varied default queries to keep it fresh for new users/empty history
        default_queries = [
            "Trending Music 2024",
            "Global Top 50 Songs",
            "New Music Friday",
            "Viral Hits 2024",
            "Lo-fi Hip Hop Beats",
            "Best Pop Songs 2024",
            "Chill Hits Mix"
        ]
        
        start_query = random.choice(default_queries)

        if history:
            # Pick from a larger pool of history for variety, not just the last 5
            # Taking up to last 50 items to find a seed
            pool = history[:50] 
            if pool:
                seed = random.choice(pool)
                title = seed.get('title', '')
                
                # Create different types of mix queries based on the seed
                mix_types = [
                    f"{title} mix",
                    f"{title} radio",
                    f"{title} similar songs",
                ]
                
                # Attempt to extract artist for even more variety
                if "-" in title:
                    parts = title.split("-")
                    if len(parts) >= 2:
                        artist = parts[0].strip()
                        if artist:
                            mix_types.append(f"{artist} best songs")
                            mix_types.append(f"{artist} mix")

                start_query = random.choice(mix_types)
        
        self.loading_label.setText(f"Loading Mix for you: {start_query}...")
        self.search_thread = SearchThread(self.youtube_client, start_query, context="search")
        self.search_thread.results_found.connect(self.on_search_results)
        self.search_thread.start()

    def start_search(self):
        query = self.search_input.text()
        if not query: return
            
        self.loading_label.setText("Searching...")
        self.search_thread = SearchThread(self.youtube_client, query, context="search")
        self.search_thread.results_found.connect(self.on_search_results)
        self.search_thread.error_occurred.connect(self.on_error)
        self.search_thread.start()

    def on_search_results(self, results, context):
        if context == "search":
            target_list = self.results_list
            self.loading_label.setText("")
        elif context == "recommendation":
            target_list = self.now_playing_page.up_next_list
            
            # Helper function to normalize titles for comparison
            def normalize_title(title):
                if not title:
                    return ""
                normalized = title.lower()
                # Remove common patterns
                patterns = ['(official video)', '(official music video)', '(lyric video)', 
                           '(lyrics)', '[official video]', '[official music video]', 
                           '[lyric video]', '[lyrics]', '| official', '- official',
                           '(audio)', '[audio]', '(hd)', '[hd]', '(4k)', '[4k]']
                for pattern in patterns:
                    normalized = normalized.replace(pattern, '')
                return ' '.join(normalized.split()).strip()
            
            # Build set of seen titles
            seen_titles = set()
            if self.current_video:
                seen_titles.add(normalize_title(self.current_video.get('title', '')))
            
            
            # Add history titles
            history = self.storage.get_history()
            for h_video in history[:100]:
                seen_titles.add(normalize_title(h_video.get('title', '')))
            
            # Filter by ID, title, AND content type (exclude shorts and non-music)
            filtered = []
            for v in results:
                video_id = v.get('id')
                video_title = v.get('title', '')
                normalized = normalize_title(video_title)
                duration = v.get('duration', 0)
                
                # Skip if already played
                if video_id in self.played_video_ids:
                    continue
                if self.current_video and video_id == self.current_video.get('id'):
                    continue
                if normalized in seen_titles:
                    continue
                
                # FILTER OUT SHORTS (duration < 60 seconds)
                if duration and duration < 60:
                    print(f"DEBUG: Skipping short video: {video_title} ({duration}s)")
                    continue
                
                # FILTER OUT NON-MUSIC CONTENT (check title for non-music keywords)
                non_music_keywords = ['vlog', 'podcast', 'interview', 'reaction', 'review', 
                                     'tutorial', 'how to', 'comedy', 'funny', 'prank',
                                     'trailer', 'teaser', 'behind the scenes', 'making of']
                title_lower = video_title.lower()
                if any(keyword in title_lower for keyword in non_music_keywords):
                    print(f"DEBUG: Skipping non-music content: {video_title}")
                    continue
                
                filtered.append(v)
                seen_titles.add(normalized)
            
            random.shuffle(filtered)
            
            # Fallback if everything filtered
            if not filtered and results:
                temp_seen = set()
                for v in results:
                    norm = normalize_title(v.get('title', ''))
                    duration = v.get('duration', 0)
                    # At least filter shorts in fallback
                    if duration and duration < 60:
                        continue
                    if norm not in temp_seen:
                        filtered.append(v)
                        temp_seen.add(norm)
                        if len(filtered) >= 5:
                            break
                random.shuffle(filtered)

            self.next_queue = filtered
            print(f"DEBUG: Filtered from {len(results)} to {len(filtered)} music songs")
        else:
            return

        target_list.clear()
        for video in results:
            self.add_custom_item(target_list, video)

    def add_custom_item(self, list_widget, video):
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, 70)) 
        item.setData(Qt.ItemDataRole.UserRole, video) 
        list_widget.addItem(item)
        
        widget = SongItemWidget(video)
        widget.add_to_playlist_clicked.connect(self.show_add_to_playlist_dialog)
        
        list_widget.setItemWidget(item, widget)

        # Check cache first
        if video['id'] in self.image_cache:
            widget.set_thumbnail(self.image_cache[video['id']])
        elif video.get('thumbnail'):
            loader = ThumbnailLoader(widget, video['thumbnail'], video['id'])
            loader.thumbnail_loaded.connect(self.on_thumbnail_widget_loaded)
            loader.start()
            setattr(widget, 'loader', loader) 

    def on_thumbnail_widget_loaded(self, widget, pixmap, video_id):
        self.image_cache[video_id] = pixmap # Cache logic
        widget.set_thumbnail(pixmap)
        
        # Update Big Player Art if playing THIS song
        if self.current_video and video_id == self.current_video['id']:
            self.now_playing_page.update_info(self.current_video, pixmap)

    def show_add_to_playlist_dialog(self, video):
        playlists = self.storage.get_playlists()
        if not playlists:
             ans = QMessageBox.question(self, "No Playlists", "Create a new playlist?")
             if ans == QMessageBox.StandardButton.Yes:
                 self.create_playlist()
                 playlists = self.storage.get_playlists()
             else:
                 return

        items = list(playlists.keys()) + ["<New Playlist>"]
        item, ok = QInputDialog.getItem(self, "Add to Playlist", "Choose Playlist:", items, 0, False)
        if ok and item:
            if item == "<New Playlist>":
                self.create_and_add(video)
            else:
                self.storage.add_to_playlist(item, video)
                QMessageBox.information(self, "Success", f"Added to {item}")

    def on_item_double_clicked(self, item):
        video = item.data(Qt.ItemDataRole.UserRole)
        self.play_video(video)

    def play_video(self, video):
        self.current_video = video
        self.storage.add_to_history(video)
        self.history_session.append(video)
        self.played_video_ids.add(video['id'])
        
        self.mini_info.setText(f"Playing: {video['title']}")
        
        self.switch_to_now_playing() 
        # CACHE LOOKUP
        pixmap = self.image_cache.get(video['id'])
        self.now_playing_page.update_info(video, pixmap) # Pass None if not cached yet
        
        self.fetch_recommendations(video)

        self.stream_thread = StreamUrlThread(self.youtube_client, video['url'])
        self.stream_thread.url_found.connect(self.on_stream_url_ready)
        self.stream_thread.error_occurred.connect(self.on_error)
        self.stream_thread.start()

    def fetch_recommendations(self, video):
        title = video['title']
        
        # Extract artist name (handle multiple formats)
        artist = ""
        movie = ""
        
        # Common patterns: "Artist - Song", "Artist | Song", "Song | Artist"
        separators = [' - ', ' | ', ' ft. ', ' feat. ', ' x ', ' X ']
        for sep in separators:
            if sep in title:
                parts = title.split(sep)
                if len(parts) >= 2:
                    # Usually first part is artist
                    potential_artist = parts[0].strip()
                    # Filter out common non-artist words
                    if len(potential_artist) > 2 and not potential_artist.lower().startswith(('official', 'lyric', 'video')):
                        artist = potential_artist
                        break
        
        # Try to detect movie/album names (often in parentheses or brackets)
        import re
        movie_match = re.search(r'[\(\[]([^\)\]]+)[\)\]]', title)
        if movie_match:
            potential_movie = movie_match.group(1)
            # Check if it looks like a movie/album name (not "Official Video" etc)
            if not any(word in potential_movie.lower() for word in ['official', 'lyric', 'video', 'audio', 'hd', '4k']):
                movie = potential_movie
        
        # Build smart queries - MUSIC SPECIFIC
        queries = []
        
        if artist:
            # Artist-focused queries with music keywords
            queries.append(f'"{artist}" songs music')
            queries.append(f'"{artist}" latest songs')
            queries.append(f'"{artist}" hit songs')
            queries.append(f'"{artist}" audio songs')
        
        if movie:
            # Movie/Album-focused queries
            queries.append(f'"{movie}" songs')
            queries.append(f'"{movie}" music')
            queries.append(f'"{movie}" audio songs')
        
        # Genre-based fallback (extract from title)
        if any(word in title.lower() for word in ['hindi', 'bollywood', 'punjabi']):
            if 'hindi' in title.lower() or 'bollywood' in title.lower():
                queries.append('Bollywood songs 2024')
                queries.append('Hindi romantic songs')
            if 'punjabi' in title.lower():
                queries.append('Punjabi hit songs')
        
        # Title-based fallback with music keywords
        words = title.split()
        if len(words) >= 2:
            # Take first 2-3 meaningful words
            snippet_words = [w for w in words[:4] if len(w) > 2][:2]
            if snippet_words:
                snippet = " ".join(snippet_words)
                queries.append(f'"{snippet}" songs')
        
        # If still no queries, use generic music search
        if not queries:
            queries.append('Latest Hindi songs 2024')
            queries.append('Trending music 2024')
        
        # Pick a random query for variety
        query = random.choice(queries)
        
        print(f"DEBUG: Fetching recommendations for '{title}' using query: '{query}'")
        self.rec_thread = SearchThread(self.youtube_client, query, context="recommendation")
        self.rec_thread.results_found.connect(self.on_search_results)
        self.rec_thread.start()

    def on_stream_url_ready(self, url, title):
        success = self.audio_player.play_url(url)
        if success:
            self.now_playing_page.update_play_btn(True)
            self.timer.start()
        else:
            self.on_error("Failed to start playback.")

    def update_progress(self):
        length = self.audio_player.get_length()
        time = self.audio_player.get_time()
        is_playing = self.audio_player.is_playing()
        
        if length > 0:
            self.now_playing_page.progress_slider.setRange(0, length)
            self.now_playing_page.progress_slider.setValue(time)
            
        # Robust Auto-play:
        # If we were playing, and now we are not, and we are near the end (or length is valid),
        # then the song likely finished.
        if self.was_playing and not is_playing:
            # Check if we are really at the end? 
            # VLC usually stops at end. 
            # Just relying on transition is usually good enough for auto-play, 
            # provided the user didn't hit pause. 
            # But the user hitting pause sets is_playing=False. 
            # We must distinguishause. 
            # One way: check if time is close to length.
            if length > 0 and (length - time) < 2000: # Within 2 seconds of end
                 print("DEBUG: Auto-play triggered.")
                 QTimer.singleShot(100, self.play_next_in_queue) # Slight delay
        
        self.was_playing = is_playing

    def play_next_in_queue(self):
        if self.next_queue:
            next_video = self.next_queue.pop(0)
            self.play_video(next_video)
        else:
             # Logic to fetch more if queue is empty?
             # For now, try to fetch recommendations based on current video again if possible
             if self.current_video:
                 print("DEBUG: Queue empty, refetching recommendations...")
                 self.fetch_recommendations(self.current_video)
                 # We can't play immediately since fetch is async. 
                 # The fetch callback will populate queue. 
                 # We should ideally trigger play after fetch. 
                 # But simplistic: User will see music stop briefly.
                 pass
             else:
                 QMessageBox.information(self, "Info", "No more songs in queue.")

    def play_previous_song(self):
        # We need at least 2 items: current + previous
        if len(self.history_session) >= 2:
            self.history_session.pop() # Pop current
            prev_video = self.history_session.pop() # Pop previous to play it
            # (play_video will append it back)
            self.play_video(prev_video)
        else:
            # Maybe check persistent history?
            hist = self.storage.get_history()
            if len(hist) > 1:
                # Naive: just pick the 2nd most recent one
                self.play_video(hist[1])
            else:
                QMessageBox.information(self, "Info", "No previous song.")

    # --- Controls ---
    def play_pause(self):
        if self.audio_player.is_playing():
            self.audio_player.pause()
            self.now_playing_page.update_play_btn(False)
        else:
            self.audio_player.pause()
            self.now_playing_page.update_play_btn(True)

    def stop_music(self):
        self.audio_player.stop()
        self.now_playing_page.update_play_btn(False)
        self.timer.stop()
        
    def set_position(self, pos):
        self.audio_player.set_time(pos)

    # --- Storage Helpers ---
    def load_history(self):
        self.history_list.clear() 
        for video in self.storage.get_history():
            self.add_custom_item(self.history_list, video)

    def load_playlists(self):
        self.playlist_names.clear()
        for name in self.storage.get_playlists():
            self.playlist_names.addItem(name)
            
    def load_playlist_items(self, item):
        name = item.text()
        self.playlist_items.clear()
        self.playlist_items.setProperty("playlist_name", name)
        for video in self.storage.get_playlists().get(name, []):
             self.add_custom_item(self.playlist_items, video)
            
    def create_playlist(self):
        name, ok = QInputDialog.getText(self, "New Playlist", "Name:")
        if ok and name:
            self.storage.create_playlist(name)
            self.load_playlists()
            
    def create_and_add(self, video):
        name, ok = QInputDialog.getText(self, "New Playlist", "Name:")
        if ok and name:
            self.storage.create_playlist(name)
            self.storage.add_to_playlist(name, video)
            self.load_playlists()
            QMessageBox.information(self, "Success", f"Added to {name}")

    def show_context_menu(self, pos):
        sender = self.sender()
        item = sender.itemAt(pos)
        if not item: return
        video = item.data(Qt.ItemDataRole.UserRole)
        
        menu = QMenu()
        
        current_pl_name = sender.property("playlist_name")
        if current_pl_name:
            action = QAction("Remove from Playlist", self)
            action.triggered.connect(lambda: self.storage.remove_from_playlist(current_pl_name, video['id']) or self.load_playlist_items(self.playlist_names.currentItem()))
            menu.addAction(action)

        menu.exec(sender.mapToGlobal(pos))

    def on_error(self, message):
        self.loading_label.setText("")
        print(f"Error: {message}")
