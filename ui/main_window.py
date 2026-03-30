from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, 
    QLabel, QSlider, QMessageBox, QTabWidget, QMenu, QInputDialog,
    QStackedWidget, QFrame, QSizePolicy, QScrollArea, QGraphicsDropShadowEffect, QApplication
)
import sys
import os
import re
import time
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QPixmap, QAction, QMovie, QColor
import requests
import random
import datetime
from collections import Counter

from ui.styles import PREMIUM_PIKACHU_THEME
from ui.now_playing import NowPlayingWidget
from ui.custom_widgets import SongItemWidget, SongCardWidget, ArtistCardWidget, PlaylistCardWidget
from ui.icons import get_icon, SVG_SEARCH, SVG_HOME, SVG_LIBRARY, SVG_CHEVRON_LEFT, SVG_TRENDING
from ui.modals import ModernInputDialog, ModernSelectionDialog
from core.youtube_client import YouTubeClient
from core.audio_player import AudioPlayer
from core.storage import StorageManager
from core.lyrics_engine import LyricsEngine

# --- Threads ---
class SearchThread(QThread):
    results_found = pyqtSignal(list, str) 
    error_occurred = pyqtSignal(str)
    def __init__(self, client, query, context="search", limit=15, is_trending=False):
        super().__init__(); self.client = client; self.query = query; self.context = context; self.limit = limit; self.is_trending = is_trending
    def run(self):
        try: results = self.client.search(self.query, limit=self.limit, is_trending=self.is_trending); self.results_found.emit(results, self.context)
        except Exception as e: self.error_occurred.emit(str(e))

class StreamUrlThread(QThread):
    url_found = pyqtSignal(str, str, str) # url, title, original_video_id
    error_occurred = pyqtSignal(str)
    def __init__(self, client, video_dict):
        super().__init__(); self.client = client; self.video = video_dict
    def run(self):
        try:
            url, title = self.client.get_stream_url(self.video['url'])
            if url: self.url_found.emit(url, title, self.video['id'])
            else: self.error_occurred.emit("Extraction failed.")
        except Exception as e: self.error_occurred.emit(str(e))

class ThumbnailLoader(QThread):
    thumbnail_loaded = pyqtSignal(object, QPixmap, str) 
    def __init__(self, item_widget, url, video_id):
        super().__init__(); self.item_widget = item_widget; self.url = url; self.video_id = video_id
    def run(self):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}; resp = requests.get(self.url, headers=headers, timeout=10)
            if resp.status_code == 200:
                pixmap = QPixmap()
                if pixmap.loadFromData(resp.content): self.thumbnail_loaded.emit(self.item_widget, pixmap, self.video_id)
        except: pass

class LyricsThread(QThread):
    lyrics_found = pyqtSignal(str)
    def __init__(self, engine, artist, song):
        super().__init__(); self.engine = engine; self.artist = artist; self.song = song
    def run(self):
        text = self.engine.fetch_lyrics(self.artist, self.song); self.lyrics_found.emit(text)

class FilterChipButton(QPushButton):
    def __init__(self, text, active=False):
        super().__init__(text); self.setCheckable(True); self.setChecked(active); self.setCursor(Qt.CursorShape.PointingHandCursor); self.setStyleSheet("QPushButton { background: rgba(255,255,255,0.05); color: #94A3B8; border: 1px solid rgba(255,255,255,0.1); border-radius: 15px; padding: 6px 15px; font-weight: 600; } QPushButton:hover { background: rgba(255,255,255,0.1); } QPushButton:checked { background: #FFD700; color: #000; }")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pikachu Music Player"); self.setGeometry(100, 100, 1200, 850); self.setStyleSheet(PREMIUM_PIKACHU_THEME)
        self.youtube_client = YouTubeClient(); self.audio_player = AudioPlayer(); self.storage = StorageManager(); self.lyrics_engine = LyricsEngine()
        self.current_video = None; self.next_queue = []; self.image_cache = {}; self.history_session = []; self.played_video_ids = set()
        self.was_playing = False; self.active_threads = [] ; self.last_refresh_times = {} 
        self.search_debounce = QTimer(); self.search_debounce.setSingleShot(True); self.search_debounce.setInterval(400); self.search_debounce.timeout.connect(self.start_search)
        self.init_ui(); self.load_history(); self.load_startup_content()
        self.timer = QTimer(); self.timer.setInterval(500); self.timer.timeout.connect(self.update_progress)

    def init_ui(self):
        self.central_container = QWidget(); self.setCentralWidget(self.central_container); main_layout = QHBoxLayout(self.central_container); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)
        self.sidebar = QFrame(); self.sidebar.setObjectName("Sidebar"); self.sidebar.setFixedWidth(240); sidebar_layout = QVBoxLayout(self.sidebar); sidebar_layout.setContentsMargins(20, 30, 20, 30); sidebar_layout.setSpacing(10)
        branding_layout = QHBoxLayout(); self.branding_gif = QLabel(); self.branding_gif.setFixedSize(50, 50); gif_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pii.gif")
        if os.path.exists(gif_path): self.movie = QMovie(gif_path); self.movie.setScaledSize(QSize(50, 50)); self.branding_gif.setMovie(self.movie); self.movie.start()
        else: self.branding_gif.setText("⚡"); self.branding_gif.setStyleSheet("font-size: 30px; color: #FFD700;")
        branding_layout.addWidget(self.branding_gif); b_l = QLabel("Pikachuu"); b_l.setStyleSheet("font-size: 24px; font-weight: 800; color: #FFD700;"); branding_layout.addWidget(b_l); sidebar_layout.addLayout(branding_layout); sidebar_layout.addSpacing(30)
        self.home_btn = self.create_sidebar_item("HOME", SVG_HOME, 0); sidebar_layout.addWidget(self.home_btn)
        self.search_btn = self.create_sidebar_item("SEARCH", SVG_SEARCH, 1); sidebar_layout.addWidget(self.search_btn)
        self.trending_btn = self.create_sidebar_item("TRENDING", SVG_TRENDING, 2); sidebar_layout.addWidget(self.trending_btn)
        self.library_btn = self.create_sidebar_item("LIBRARY", SVG_LIBRARY, 3); sidebar_layout.addWidget(self.library_btn)
        sidebar_layout.addStretch()
        self.mini_player = QFrame(); self.mini_player.setObjectName("GlassPanel"); self.mini_player.setFixedHeight(120); m_l = QVBoxLayout(self.mini_player); self.mini_thumb = QLabel(); self.mini_thumb.setFixedSize(40, 40); self.mini_thumb.setStyleSheet("background: #000; border-radius: 4px;"); m_l.addWidget(self.mini_thumb, alignment=Qt.AlignmentFlag.AlignCenter); self.mini_title = QLabel("Ready to play"); self.mini_title.setObjectName("MutedText"); self.mini_title.setAlignment(Qt.AlignmentFlag.AlignCenter); m_l.addWidget(self.mini_title); e_m = QPushButton("Expand Player"); e_m.setObjectName("SecondaryAction"); e_m.clicked.connect(self.switch_to_now_playing); m_l.addWidget(e_m); sidebar_layout.addWidget(self.mini_player); main_layout.addWidget(self.sidebar)
        self.content_stack = QStackedWidget()
        self.home_page = QWidget(); self.init_home_page(); self.content_stack.addWidget(self.home_page)
        self.search_page = QWidget(); self.init_search_page(); self.content_stack.addWidget(self.search_page)
        self.trending_page = QWidget(); self.init_trending_page(); self.content_stack.addWidget(self.trending_page)
        self.library_page = QWidget(); self.init_library_page(); self.content_stack.addWidget(self.library_page)
        self.now_playing_page = NowPlayingWidget(); self.content_stack.addWidget(self.now_playing_page)
        self.now_playing_page.back_clicked.connect(lambda: self.switch_page(0)); self.now_playing_page.next_song_requested.connect(self.play_video); self.now_playing_page.play_pause_clicked.connect(self.play_pause); self.now_playing_page.prev_clicked.connect(self.play_previous_song); self.now_playing_page.next_clicked.connect(self.play_next_in_queue); self.now_playing_page.seek_requested.connect(self.set_position)
        self.now_playing_page.skip_backward_clicked.connect(lambda: self.skip_time(-10000)); self.now_playing_page.skip_forward_clicked.connect(lambda: self.skip_time(10000))
        self.now_playing_page.add_to_playlist_clicked.connect(self.show_add_to_playlist_dialog)
        main_layout.addWidget(self.content_stack, stretch=1); self.switch_page(0)

    def create_sidebar_item(self, text, icon_svg, index): btn = QPushButton(f"  {text}"); btn.setObjectName("SidebarItem"); btn.setIcon(get_icon(icon_svg, "#94A3B8")); btn.setIconSize(QSize(20, 20)); btn.setCursor(Qt.CursorShape.PointingHandCursor); btn.clicked.connect(lambda: self.switch_page(index)); return btn

    def switch_page(self, i): 
        if i == 0: self.refresh_home_dashboard()
        if i == 1: self.refresh_search_recommendations()
        if i == 2: self.refresh_trending_page()
        if i == 3: self.load_library_playlists()
        self.content_stack.setCurrentIndex(i); self.home_btn.setProperty("active", i == 0); self.search_btn.setProperty("active", i == 1); self.trending_btn.setProperty("active", i == 2); self.library_btn.setProperty("active", i == 3)
        for b in [self.home_btn, self.search_btn, self.trending_btn, self.library_btn]: b.style().unpolish(b); b.style().polish(b)

    def switch_to_now_playing(self): self.content_stack.setCurrentIndex(4)

    def init_home_page(self):
        main_h_layout = QVBoxLayout(self.home_page); main_h_layout.setContentsMargins(0, 40, 0, 0); main_h_layout.setSpacing(15); self.pref_container = QWidget(); self.pref_layout = QHBoxLayout(self.pref_container); self.pref_layout.setContentsMargins(40, 0, 40, 0); self.pref_layout.setSpacing(10)
        langs = ["Hindi", "English", "Punjabi", "Haryanvi", "Bhojpuri", "Gujarati", "Reels Trending"]; user_langs = self.storage.get_preferences().get("languages", ["Hindi"])
        for lang in langs: chip = FilterChipButton(lang, active=(lang in user_langs)); chip.clicked.connect(self.on_lang_chip_clicked); self.pref_layout.addWidget(chip)
        self.pref_layout.addStretch(); main_h_layout.addWidget(self.pref_container)
        self.home_scroll = QScrollArea(); self.home_scroll.setWidgetResizable(True); self.home_scroll.setStyleSheet("background: transparent; border: none;"); self.home_scroll_container = QWidget(); self.home_rows_layout = QVBoxLayout(self.home_scroll_container); self.home_rows_layout.setContentsMargins(40, 20, 40, 20); self.home_rows_layout.setSpacing(40); self.home_scroll.setWidget(self.home_scroll_container); main_h_layout.addWidget(self.home_scroll)

    def init_trending_page(self):
        l = QVBoxLayout(self.trending_page); l.setContentsMargins(0, 40, 0, 0); l.setSpacing(30); h_t = QLabel("Trending Now India"); h_t.setObjectName("SectionHeader"); h_t.setStyleSheet("margin-left: 40px; font-size: 32px; color: #FFD700;"); l.addWidget(h_t)
        self.trend_scroll = QScrollArea(); self.trend_scroll.setWidgetResizable(True); self.trend_scroll.setStyleSheet("background: transparent; border: none;"); self.trend_container = QWidget(); self.trend_layout = QVBoxLayout(self.trend_container); self.trend_layout.setContentsMargins(40, 0, 40, 40); self.trend_layout.setSpacing(40); self.trend_scroll.setWidget(self.trend_container); l.addWidget(self.trend_scroll)

    def is_throttled(self, context, window=20):
        now = time.time(); last = self.last_refresh_times.get(context, 0)
        if now - last < window: return True
        self.last_refresh_times[context] = now; return False

    def on_lang_chip_clicked(self):
        selected = [w.text() for i in range(self.pref_layout.count()) for w in [self.pref_layout.itemAt(i).widget()] if isinstance(w, FilterChipButton) and w.isChecked()]; self.storage.update_languages(selected); [self.last_refresh_times.pop("home") if "home" in self.last_refresh_times else None]; self.refresh_home_dashboard()

    def refresh_trending_page(self):
        if self.is_throttled("trending", window=30): return
        self.clear_layout(self.trend_layout); month = datetime.datetime.now().strftime("%B %Y")
        reels_queries = ["trending instagram reels songs india hits this week", "viral reels music india mix", "latest instagram viral audio songs"]; movies_queries = [f"latest bollywood movie songs {month} released", "new indian cinema hits music official", "top bollywood soundtracks this month"]; yt_queries = [f"youtube music trending india chart {month}", "most viewed indian songs this week yt", "trending youtube music videos india"]; global_queries = [f"global viral chart 50 hits {month}", "billboard hot 100 trending worldwide", "global pop hits mix 2024"]; genre_trends = [("💎 Viral Indipop", "trending indipop songs india"), ("🔥 Punjabi Hits", "latest punjabi trending songs"), ("🌊 South Sensation", "trending telugu and tamil movie hits india")]
        rows = [("🔥 Viral on Instagram Reels", random.choice(reels_queries), "trend_reels", True), ("🎬 Latest Cinema Hits", random.choice(movies_queries), "trend_movies", True), ("📺 YouTube Music Trending", random.choice(yt_queries), "trend_yt", True), ("⚡ Global Viral 50", random.choice(global_queries), "trend_global", True)]
        g_t, g_q = random.choice(genre_trends); rows.append((g_t, g_q, "trend_genre", True)); random.shuffle(rows)
        for t, q, c, tr in rows: self.add_dynamic_row(t, q, c, self.trend_layout, tr)
        self.trend_layout.addStretch()

    def refresh_home_dashboard(self):
        if self.is_throttled("home", window=15): return
        self.clear_layout(self.home_rows_layout); hour = datetime.datetime.now().hour; greeting = "Good Morning ☀️" if 5 <= hour < 12 else "Good Afternoon 🌤️" if 12 <= hour < 17 else "Good Evening 🌙" if 17 <= hour < 22 else "Late Night Vibe 🌌"
        h_l = QLabel(greeting); h_l.setObjectName("SectionHeader"); h_l.setStyleSheet("font-size: 28px; color: #FFD700; border: none; padding: 0;"); self.home_rows_layout.addWidget(h_l)
        
        # Random seeds to break cache and ensure freshness
        seeds = ["", "trending", "hits", "mix", "new", "top", "viral", "2024"]
        s1 = random.choice(seeds); s2 = random.choice(seeds)
        
        bolly_pools = ["latest bollywood music releases", "trending hindi movie songs", "new bollywood hits mix", "viral indian film music 2024"]
        self.add_dynamic_row("Daily Dose of Bollywood 📺", f"{random.choice(bolly_pools)} {s1}", "home_ref", self.home_rows_layout, True)
        
        pref = self.storage.get_preferences(); user_langs = pref.get("languages", ["Hindi"]); random.shuffle(user_langs); searches = pref.get("last_searches", []); random.shuffle(searches); top_artists = self.get_top_artists_from_history(); random.shuffle(top_artists)
        
        if 5 <= hour < 12: self.add_dynamic_row("Morning Energy Boost ⚡", f"best motivational hits morning workout songs {s2}", "home_morning", self.home_rows_layout)
        elif 22 <= hour or hour < 5: self.add_dynamic_row("Midnight Lo-Fi & Sleep 😴", f"lofi chill relax sleep beats {s2}", "home_night", self.home_rows_layout)
        
        chill_pool = ["lofi aesthetic chill mix", "acoustic covers of popular songs", "soft piano music relax", "chill romantic songs bollywood"]; party_pool = ["high energy dance party hits 2024", "best club music remixes", "pump up gym beats workout", "new dj song remix hindi"]
        
        rows = [
            (f"Top {user_langs[0]} Hits 📈", f"new {user_langs[0]} songs trending this week {random.choice(seeds)}", f"home_lang_{user_langs[0].lower()}", True) if user_langs else None,
            (f"Inspired by: {searches[0]} 💿", f"{searches[0]} related best remixes and original full songs {random.choice(seeds)}", f"home_search_{searches[0].lower().replace(' ', '_')}", False) if searches else None,
            ("Chill & Vibes Only ☁️", f"{random.choice(chill_pool)} {random.choice(seeds)}", "home_lofi", False),
            ("Party Non-Stop 🕺", f"{random.choice(party_pool)} {random.choice(seeds)}", "home_party", True)
        ]
        rows = [r for r in rows if r]; random.shuffle(rows)
        for t, q, c, tr in rows: self.add_dynamic_row(t, q, c, self.home_rows_layout, tr)
        
        art_h = QLabel("Explore Your Favorite Artists 🎤"); art_h.setObjectName("SectionHeader"); self.home_rows_layout.addWidget(art_h)
        a_s = QScrollArea(); a_s.setFixedHeight(210); a_s.setWidgetResizable(True); a_s.setStyleSheet("background: transparent; border: none;"); a_c = QWidget(); a_l = QHBoxLayout(a_c); a_l.setContentsMargins(0,0,0,0); a_l.setSpacing(15); ads = [("Arijit Singh", "https://i.scdn.co/image/ab6761610000e5eb12810de09aef82b3c2069670"), ("Atif Aslam", "https://i.scdn.co/image/ab6761610000e5eb748805f42f53d71221fcc232"), ("Shreya Ghoshal", "https://i.scdn.co/image/ab6761610000e5eb7ed821e25e9acc8a2fb3a4d9"), ("Alka Yagnik", "https://i.scdn.co/image/ab6761610000e5eb46059c393bcaf146e4544760"), ("Honey Singh", "https://i.scdn.co/image/ab6761610000e5ebcc7517973d47ad8fcfcb7fb4"), ("Jubin Nautiyal", "https://i.scdn.co/image/ab6761610000e5eb4270d49489ef0cbcf3ca5932")]
        random.shuffle(ads); [ (a_l.addWidget(ArtistCardWidget(n)), self.active_threads.append(ThumbnailLoader(a_l.itemAt(a_l.count()-1).widget(), u, f"Artist_{n}")), self.active_threads[-1].thumbnail_loaded.connect(self.on_artist_image_loaded), self.active_threads[-1].start()) for n, u in ads[:6] ]; a_l.addStretch(); a_s.setWidget(a_c); self.home_rows_layout.addWidget(a_s)
        
        for art, _ in top_artists[:1]: self.add_dynamic_row(f"Magic from {art} ✨", f"{art} greatest hits mix {random.choice(seeds)}", f"home_{art.lower().replace(' ', '_')}", self.home_rows_layout)
        
        his_h = QLabel("Recently Played"); his_h.setObjectName("SectionHeader"); self.home_rows_layout.addWidget(his_h); self.his_scroll = self.create_row_scroll(); self.his_layout = self.his_scroll.widget().layout(); self.home_rows_layout.addWidget(self.his_scroll); self.load_history(); self.home_rows_layout.addStretch()

    def add_dynamic_row(self, title, query, context, layout, is_trending=False):
        h = QLabel(title); h.setObjectName("SectionHeader"); layout.addWidget(h); s = self.create_row_scroll(); s.setProperty("context", context); layout.addWidget(s); t = SearchThread(self.youtube_client, query, context=context, limit=12, is_trending=is_trending); t.results_found.connect(self.on_search_results); t.finished.connect(lambda: self.cleanup_thread(t)); self.active_threads.append(t); t.start()

    def cleanup_thread(self, t):
        # We stop removing them immediately to prevent QThread GC crashes on Windows
        pass 

    def start_search(self, q=None):
        if not q: q = self.search_input.text()
        if not q or len(q) < 3: (self.search_rec_scroll.show(), self.results_list.hide(), self.loading_label.hide(), self.results_list.clear()); return
        self.search_rec_scroll.hide(); self.results_list.show(); self.loading_label.show(); self.storage.add_search_term(q); self.loading_label.setText(f"Searching for '{q}'..."); self.search_thread = SearchThread(self.youtube_client, q, context="search", limit=25); self.search_thread.results_found.connect(self.on_search_results); self.search_thread.finished.connect(lambda: self.cleanup_thread(self.search_thread)); self.active_threads.append(self.search_thread); self.search_thread.start()

    def get_top_artists_from_history(self):
        hist = self.storage.get_history()
        if not hist: return []
        texts = [v.get('title', '') + " " + (v.get('uploader', '') or '') for v in hist]; top_names = ["Arijit Singh", "Atif Aslam", "Shreya Ghoshal", "Alka Yagnik", "Honey Singh", "Jubin Nautiyal", "Taylor Swift", "Darshan Raval", "Armaan Malik"]; counts = Counter()
        for t in texts: [counts.update({n: 1}) for n in top_names if n.lower() in t.lower()]; return counts.most_common(5)

    def on_artist_image_loaded(self, c, p, n): c.set_image(p) if not p.isNull() else None
    def create_row_scroll(self): s = QScrollArea(); s.setFixedHeight(240); s.setWidgetResizable(True); s.setStyleSheet("background: transparent; border: none;"); c = QWidget(); l = QHBoxLayout(c); l.setContentsMargins(0,0,0,0); l.setSpacing(15); s.setWidget(c); return s
    
    def init_search_page(self):
        l = QVBoxLayout(self.search_page); l.setContentsMargins(40, 40, 40, 20); l.setSpacing(20); s_b = QHBoxLayout(); self.search_input = QLineEdit(); self.search_input.setObjectName("SearchBar"); self.search_input.setPlaceholderText("Search for songs, artists, or genres..."); self.search_input.setFixedHeight(50); self.search_input.textChanged.connect(lambda: self.search_debounce.start()); s_c = QPushButton("Search"); s_c.setObjectName("PrimaryAction"); s_c.setFixedHeight(50); s_c.clicked.connect(self.start_search); s_b.addWidget(self.search_input, stretch=1); s_b.addWidget(s_c); l.addLayout(s_b)
        self.search_rec_scroll = QScrollArea(); self.search_rec_scroll.setWidgetResizable(True); self.search_rec_scroll.setStyleSheet("background: transparent; border: none;"); self.search_rec_container = QWidget(); self.search_rec_layout = QVBoxLayout(self.search_rec_container); self.search_rec_layout.setContentsMargins(0, 0, 0, 0); self.search_rec_layout.setSpacing(40); self.search_rec_scroll.setWidget(self.search_rec_container); l.addWidget(self.search_rec_scroll); self.results_list = QListWidget(); self.results_list.itemDoubleClicked.connect(self.on_item_double_clicked); self.results_list.hide(); l.addWidget(self.results_list); self.loading_label = QLabel(""); self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.loading_label.hide(); l.addWidget(self.loading_label)

    def refresh_search_recommendations(self):
        if self.is_throttled("search_rec"): return
        self.clear_layout(self.search_rec_layout); month = datetime.datetime.now().strftime("%B %Y"); trending_pool = [f"top songs india hits {month}", "viral global hits 50 music", "trending punjabi pop 2024"]; discover_pool = ["chill lofi aesthetic mix", "bollywood romantic unplugged", "high energy gym workout beats"]; pref = self.storage.get_preferences(); searches = pref.get("last_searches", []); hist_query = f"{random.choice(searches)} mix" if searches else "top billboard hits 2024"
        rows = [("📀 Trending Now", random.choice(trending_pool), "search_rec_trending", True), ("🎵 Pick of the Day", hist_query, "search_rec_history", False), ("✨ Discover New Vibes", random.choice(discover_pool), "search_rec_discover", False)]; random.shuffle(rows)
        for t, q, c, tr in rows: self.add_dynamic_row(t, q, c, self.search_rec_layout, tr)
        self.search_rec_layout.addStretch()

    def init_library_page(self):
        layout = QVBoxLayout(self.library_page); layout.setContentsMargins(40, 40, 40, 40); layout.setSpacing(20)
        # Header
        h_l = QHBoxLayout(); title = QLabel("My High-Class Collection 🏛️"); title.setObjectName("SectionHeader"); title.setStyleSheet("font-size: 32px;"); h_l.addWidget(title); h_l.addStretch()
        n_p = QPushButton("+ Create Playlist"); n_p.setObjectName("PrimaryAction"); n_p.setFixedWidth(180); n_p.clicked.connect(self.create_playlist); h_l.addWidget(n_p); layout.addLayout(h_l)
        # Stacked Grid/List
        self.lib_stack = QStackedWidget(); layout.addWidget(self.lib_stack)
        # Grid Mode (Playlists)
        self.lib_grid_scroll = QScrollArea(); self.lib_grid_scroll.setWidgetResizable(True); self.lib_grid_scroll.setStyleSheet("background: transparent; border: none;"); self.lib_grid_widget = QWidget(); self.lib_grid_layout = QHBoxLayout(self.lib_grid_widget); self.lib_grid_layout.setContentsMargins(0, 20, 0, 0); self.lib_grid_layout.setSpacing(25); self.lib_grid_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop); self.lib_grid_scroll.setWidget(self.lib_grid_widget); self.lib_stack.addWidget(self.lib_grid_scroll)
        # List Mode (Tracks)
        self.lib_list_widget = QWidget(); self.lib_list_layout = QVBoxLayout(self.lib_list_widget); self.lib_list_layout.setContentsMargins(0, 0, 0, 0)
        back_h = QHBoxLayout(); back_b = QPushButton(" ← Back to Collection"); back_b.setObjectName("SecondaryAction"); back_b.clicked.connect(lambda: self.lib_stack.setCurrentIndex(0)); back_h.addWidget(back_b); back_h.addStretch(); self.lib_list_layout.addLayout(back_h)
        self.playlist_title = QLabel("Playlist Name"); self.playlist_title.setStyleSheet("font-size: 24px; font-weight: 800; color: #FFD700; margin-top: 10px;"); self.lib_list_layout.addWidget(self.playlist_title)
        self.lib_tracks = QListWidget(); self.lib_tracks.itemDoubleClicked.connect(self.on_item_double_clicked); self.lib_list_layout.addWidget(self.lib_tracks); self.lib_stack.addWidget(self.lib_list_widget)

    def load_library_playlists(self):
        self.clear_layout(self.lib_grid_layout); playlists = self.storage.get_playlists()
        for name, tracks in playlists.items():
            card = PlaylistCardWidget(name, len(tracks)); card.clicked.connect(self.load_playlist_items_premium); self.lib_grid_layout.addWidget(card)
        self.lib_grid_layout.addStretch()

    def load_playlist_items_premium(self, name):
        self.playlist_title.setText(name); self.lib_tracks.clear(); tracks = self.storage.get_playlists().get(name, [])
        for v in tracks: self.add_to_list_widget(self.lib_tracks, v)
        self.lib_stack.setCurrentIndex(1)

    def on_search_results(self, results, context):
        if context == "search":
            self.results_list.clear()
            artists = [v for v in results if v.get('is_artist')]
            songs = [v for v in results if not v.get('is_artist')]
            if artists:
                h = QListWidgetItem(); h.setFlags(Qt.ItemFlag.NoItemFlags); self.results_list.addItem(h)
                l = QLabel("  TOP ARTISTS"); l.setObjectName("ResultHeader"); self.results_list.setItemWidget(h, l)
                for v in artists: self.add_to_list_widget(self.results_list, v)
            if songs:
                h = QListWidgetItem(); h.setFlags(Qt.ItemFlag.NoItemFlags); self.results_list.addItem(h)
                l = QLabel("  SONGS"); l.setObjectName("ResultHeader"); self.results_list.setItemWidget(h, l)
                for v in songs: self.add_to_list_widget(self.results_list, v)
        elif context == "recommendation":
            self.next_queue = [v for v in results if v['id'] not in self.played_video_ids and not v.get('is_artist')][:15]
            self.now_playing_page.up_next_list.clear()
            for v in self.next_queue: self.add_to_list_widget(self.now_playing_page.up_next_list, v)
        elif context.startswith("home_") or context.startswith("trend_") or context.startswith("search_rec_"):
            parent_layout = self.home_rows_layout if context.startswith("home_") else self.trend_layout if context.startswith("trend_") else self.search_rec_layout
            for i in range(parent_layout.count()):
                w = parent_layout.itemAt(i).widget()
                if isinstance(w, QScrollArea) and w.property("context") == context:
                    l = w.widget().layout(); self.clear_layout(l)
                    for v in results[:10]:
                        c = SongCardWidget(v); c.clicked.connect(self.play_video); l.addWidget(c)
                        if v.get('thumbnail'): 
                            lo = ThumbnailLoader(c, v['thumbnail'], v['id'])
                            lo.thumbnail_loaded.connect(self.on_card_thumb_loaded)
                            lo.finished.connect(lambda t_obj=lo: self.cleanup_thread(t_obj))
                            self.active_threads.append(lo)
                            lo.start()
                    l.addStretch(); break

    def on_card_thumb_loaded(self, card, pixmap, video_id): self.image_cache[video_id] = pixmap; card.set_thumbnail(pixmap)
    def clear_layout(self, layout):
        while layout.count(): item = layout.takeAt(0); item.widget().deleteLater() if item.widget() else None
    def add_to_list_widget(self, list_widget, video):
        item = QListWidgetItem(); item.setSizeHint(QSize(0, 72)); item.setData(Qt.ItemDataRole.UserRole, video); list_widget.addItem(item); widget = SongItemWidget(video); hasattr(widget, 'add_to_playlist_clicked') and widget.add_to_playlist_clicked.connect(self.show_add_to_playlist_dialog); list_widget.setItemWidget(item, widget)
        if video['id'] in self.image_cache: widget.set_thumbnail(self.image_cache[video['id']])
        elif video.get('thumbnail'): 
            lo = ThumbnailLoader(widget, video['thumbnail'], video['id'])
            lo.thumbnail_loaded.connect(lambda w, p, vid: self.cache_and_set(w, p, vid))
            lo.finished.connect(lambda t_obj=lo: self.cleanup_thread(t_obj))
            self.active_threads.append(lo)
            lo.start()
    def cache_and_set(self, w, p, v_id): self.image_cache[v_id] = p; w.set_thumbnail(p)
    def play_video(self, v):
        if not v: return
        self.current_video = v; self.storage.add_to_history(v); self.history_session.append(v); self.played_video_ids.add(v['id']); self.mini_title.setText(v['title']); pix = self.image_cache.get(v['id'])
        if pix: (self.mini_thumb.setPixmap(pix.scaled(40,40)), self.update_ambient_glow(pix))
        self.load_history(); self.fetch_recommendations(v); self.now_playing_page.update_info(v, pix); self.switch_to_now_playing()
        
        # Stream Extraction with Race Protection
        if hasattr(self, 'stream_thread') and self.stream_thread.isRunning():
            try: self.stream_thread.url_found.disconnect()
            except: pass
        self.stream_thread = StreamUrlThread(self.youtube_client, v); self.stream_thread.url_found.connect(self.on_stream_url_ready); self.stream_thread.finished.connect(lambda t_obj=self.stream_thread: self.cleanup_thread(t_obj)); self.active_threads.append(self.stream_thread); self.stream_thread.start()
        
        art = v.get('title', '').split(' - ')[0] if ' - ' in v.get('title', '') else v.get('uploader', 'Unknown'); song = v.get('title', '').split(' - ')[1] if ' - ' in v.get('title', '') else v.get('title', 'Unknown')
        ly_th = LyricsThread(self.lyrics_engine, art, song); ly_th.lyrics_found.connect(self.now_playing_page.update_lyrics); ly_th.finished.connect(lambda: self.cleanup_thread(ly_th)); self.active_threads.append(ly_th); ly_th.start()

    def on_stream_url_ready(self, url, title, video_id):
        # Only play if this is still the current video (Race protection)
        if self.current_video and self.current_video['id'] == video_id:
            if self.audio_player.play_url(url, crossfade=True): 
                self.now_playing_page.update_play_btn(True)
                self.timer.start()
    def update_progress(self):
        ms = self.audio_player.get_time(); self.now_playing_page.update_progress(ms)
        if self.was_playing and not self.audio_player.is_playing():
             l = self.audio_player.get_length(); [self.play_next_in_queue() for _ in [0] if l > 0 and (l - ms) < 2000]
        self.was_playing = self.audio_player.is_playing()
    def play_next_in_queue(self):
        if self.next_queue: self.play_video(self.next_queue.pop(0))
        elif self.current_video: self.fetch_recommendations(self.current_video) 
    def play_previous_song(self): [ (self.history_session.pop(), self.play_video(self.history_session.pop())) for _ in [0] if len(self.history_session) >= 2]
    def skip_time(self, ms_delta): curr = self.audio_player.get_time(); self.set_position(curr + ms_delta)
    def play_pause(self): (self.audio_player.pause(), self.now_playing_page.update_play_btn(False)) if self.audio_player.is_playing() else (self.audio_player.pause(), self.now_playing_page.update_play_btn(True))
    def set_position(self, p): self.audio_player.set_time(p)
    def load_history(self):
        if not hasattr(self, 'his_layout'): return
        self.clear_layout(self.his_layout); hist = self.storage.get_history()[:10]
        for v in hist:
            card = SongCardWidget(v); card.clicked.connect(self.play_video); self.his_layout.addWidget(card)
            if v['id'] in self.image_cache: card.set_thumbnail(self.image_cache[v['id']])
            elif v.get('thumbnail'): th = ThumbnailLoader(card, v['thumbnail'], v['id']); th.thumbnail_loaded.connect(self.on_card_thumb_loaded); th.finished.connect(lambda: self.cleanup_thread(th)); self.active_threads.append(th); th.start()
        self.his_layout.addStretch()
    def load_startup_content(self): self.refresh_home_dashboard(); self.refresh_search_recommendations()

    def create_playlist(self):
        dlg = ModernInputDialog("Create Playlist", "Give your collection a high-class name:", self)
        if dlg.exec():
            n = dlg.get_text()
            if n: self.storage.create_playlist(n); self.load_library_playlists()

    def show_add_to_playlist_dialog(self, v):
        pls = self.storage.get_playlists(); itms = list(pls.keys()) + ["+ New Playlist"]
        dlg = ModernSelectionDialog("Add to Playlist", f"Choose a collection for '{v.get('title', 'this track')[:30]}...':", itms, self)
        if dlg.exec():
            itm = dlg.get_selection()
            if itm == "+ New Playlist":
                ndlg = ModernInputDialog("New Playlist", "Name your new collection:", self)
                if ndlg.exec():
                    n = ndlg.get_text()
                    if n: self.storage.create_playlist(n); self.storage.add_to_playlist(n, v); self.load_library_playlists()
            else: self.storage.add_to_playlist(itm, v); self.load_library_playlists()

    def fetch_recommendations(self, v):
        t = v.get('title', ''); art = ""; [ (art := p[0].strip()) for s in [' - ', ' | ', ' – '] for p in [t.split(s)] if s in t and len(p) >= 2 ]
        t_c = re.sub(r'[^a-zA-Z0-9\s]', ' ', t); words = [w for w in t_c.split() if len(w) > 3][:2]; neg = " ".join([f"-{w}" for w in words])
        qs = [f'"{art}" hits {neg}', f'similar to {art} music', f'bollywood hits mix'] if art else [f'top trending songs {neg}']
        self.rec_thread = SearchThread(self.youtube_client, random.choice(qs), context="recommendation", limit=40); self.rec_thread.results_found.connect(self.on_search_results); self.rec_thread.start()
    def on_item_double_clicked(self, i): self.play_video(i.data(Qt.ItemDataRole.UserRole))

if __name__ == "__main__":
    app = QApplication(sys.argv); window = MainWindow(); window.show(); sys.exit(app.exec())
