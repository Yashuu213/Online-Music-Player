from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, 
    QLabel, QSlider, QMessageBox, QTabWidget, QMenu, QInputDialog,
    QStackedWidget, QFrame, QSizePolicy, QScrollArea, QGraphicsDropShadowEffect
)
import sys
import os
import re
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QPixmap, QAction, QMovie, QColor
import requests
import random
from collections import Counter

from ui.styles import PREMIUM_PIKACHU_THEME
from ui.now_playing import NowPlayingWidget
from ui.custom_widgets import SongItemWidget, SongCardWidget, ArtistCardWidget
from ui.icons import get_icon, SVG_SEARCH, SVG_HOME, SVG_LIBRARY, SVG_CHEVRON_LEFT
from core.youtube_client import YouTubeClient
from core.audio_player import AudioPlayer
from core.storage import StorageManager

# --- Threads ---
class SearchThread(QThread):
    results_found = pyqtSignal(list, str) 
    error_occurred = pyqtSignal(str)

    def __init__(self, client, query, context="search", limit=15):
        super().__init__()
        self.client = client; self.query = query; self.context = context; self.limit = limit

    def run(self):
        try:
            results = self.client.search(self.query, limit=self.limit); self.results_found.emit(results, self.context)
        except Exception as e: self.error_occurred.emit(str(e))

class StreamUrlThread(QThread):
    url_found = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, client, video_url):
        super().__init__()
        self.client = client; self.video_url = video_url

    def run(self):
        try:
            url, title = self.client.get_stream_url(self.video_url)
            if url: self.url_found.emit(url, title)
            else: self.error_occurred.emit("Could not extract stream URL.")
        except Exception as e: self.error_occurred.emit(str(e))

class ThumbnailLoader(QThread):
    thumbnail_loaded = pyqtSignal(object, QPixmap, str) 

    def __init__(self, item_widget, url, video_id):
        super().__init__()
        self.item_widget = item_widget; self.url = url; self.video_id = video_id

    def run(self):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}; resp = requests.get(self.url, headers=headers, timeout=10)
            if resp.status_code == 200:
                pixmap = QPixmap(); [self.thumbnail_loaded.emit(self.item_widget, pixmap, self.video_id) for _ in [0] if pixmap.loadFromData(resp.content)]
        except Exception as e: print(f"DEBUG: Thumbnail load error: {e}")

class FilterChipButton(QPushButton):
    def __init__(self, text, active=False):
        super().__init__(text)
        self.setCheckable(True); self.setChecked(active); self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05); color: #94A3B8; border: 1px solid rgba(255, 255, 255, 0.1); 
                border-radius: 15px; padding: 6px 15px; font-weight: 600; font-size: 13px;
            }
            QPushButton:hover { background: rgba(255, 255, 255, 0.1); color: #FFFFFF; }
            QPushButton:checked { background: #FFD700; color: #000000; border: 1px solid #FFD700; }
        """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pikachu Music Player"); self.setGeometry(100, 100, 1200, 850); self.setStyleSheet(PREMIUM_PIKACHU_THEME)
        self.youtube_client = YouTubeClient(); self.audio_player = AudioPlayer(); self.storage = StorageManager()
        self.current_video = None; self.next_queue = []; self.image_cache = {}; self.history_session = []; self.played_video_ids = set()
        self.was_playing = False; self.active_threads = [] 
        self.search_debounce = QTimer(); self.search_debounce.setSingleShot(True); self.search_debounce.setInterval(400); self.search_debounce.timeout.connect(self.start_search)
        self.init_ui(); self.load_history(); self.load_playlists(); self.load_startup_content()
        self.timer = QTimer(); self.timer.setInterval(500); self.timer.timeout.connect(self.update_progress)

    def init_ui(self):
        self.central_container = QWidget(); self.setCentralWidget(self.central_container); main_layout = QHBoxLayout(self.central_container); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)
        self.sidebar = QFrame(); self.sidebar.setObjectName("Sidebar"); self.sidebar.setFixedWidth(240); sidebar_layout = QVBoxLayout(self.sidebar); sidebar_layout.setContentsMargins(20, 30, 20, 30); sidebar_layout.setSpacing(10)
        branding_layout = QHBoxLayout(); self.branding_gif = QLabel(); self.branding_gif.setFixedSize(50, 50)
        base_path = os.path.dirname(os.path.abspath(__file__)); gif_path = os.path.join(base_path, "..", "pii.gif")
        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path); self.movie.setScaledSize(QSize(50, 50)); self.branding_gif.setMovie(self.movie); self.movie.start()
        else:
            self.branding_gif.setText("⚡"); self.branding_gif.setStyleSheet("font-size: 30px; color: #FFD700;")
        branding_layout.addWidget(self.branding_gif); b_l = QLabel("Pikachuu"); b_l.setStyleSheet("font-size: 24px; font-weight: 800; color: #FFD700;"); branding_layout.addWidget(b_l); sidebar_layout.addLayout(branding_layout); sidebar_layout.addSpacing(30)
        self.home_btn = self.create_sidebar_item("HOME", SVG_HOME, 0); sidebar_layout.addWidget(self.home_btn); self.search_btn = self.create_sidebar_item("SEARCH", SVG_SEARCH, 1); sidebar_layout.addWidget(self.search_btn); self.library_btn = self.create_sidebar_item("LIBRARY", SVG_LIBRARY, 2); sidebar_layout.addWidget(self.library_btn); sidebar_layout.addStretch()
        self.mini_player = QFrame(); self.mini_player.setObjectName("GlassPanel"); self.mini_player.setFixedHeight(120); m_l = QVBoxLayout(self.mini_player); self.mini_thumb = QLabel(); self.mini_thumb.setFixedSize(40, 40); self.mini_thumb.setStyleSheet("background: #000; border-radius: 4px;"); m_l.addWidget(self.mini_thumb, alignment=Qt.AlignmentFlag.AlignCenter); self.mini_title = QLabel("Ready to play"); self.mini_title.setObjectName("MutedText"); self.mini_title.setAlignment(Qt.AlignmentFlag.AlignCenter); m_l.addWidget(self.mini_title); e_m = QPushButton("Expand Player"); e_m.setObjectName("SecondaryAction"); e_m.clicked.connect(self.switch_to_now_playing); m_l.addWidget(e_m); sidebar_layout.addWidget(self.mini_player); main_layout.addWidget(self.sidebar)
        self.content_stack = QStackedWidget(); self.home_page = QWidget(); self.init_home_page(); self.content_stack.addWidget(self.home_page); self.search_page = QWidget(); self.init_search_page(); self.content_stack.addWidget(self.search_page); self.library_page = QWidget(); self.init_library_page(); self.content_stack.addWidget(self.library_page); self.now_playing_page = NowPlayingWidget(); self.content_stack.addWidget(self.now_playing_page)
        self.now_playing_page.back_clicked.connect(lambda: self.switch_page(0)); self.now_playing_page.next_song_requested.connect(self.play_video); self.now_playing_page.play_pause_clicked.connect(self.play_pause); self.now_playing_page.prev_clicked.connect(self.play_previous_song); self.now_playing_page.next_clicked.connect(self.play_next_in_queue); self.now_playing_page.seek_requested.connect(self.set_position); main_layout.addWidget(self.content_stack, stretch=1); self.switch_page(0) 

    def create_sidebar_item(self, text, icon_svg, index):
        btn = QPushButton(f"  {text}"); btn.setObjectName("SidebarItem"); btn.setIcon(get_icon(icon_svg, "#94A3B8")); btn.setIconSize(QSize(20, 20)); btn.setCursor(Qt.CursorShape.PointingHandCursor); btn.clicked.connect(lambda: self.switch_page(index)); return btn

    def switch_page(self, i): 
        if i == 0: self.refresh_home_dashboard()
        self.content_stack.setCurrentIndex(i); self.home_btn.setProperty("active", i == 0); self.search_btn.setProperty("active", i == 1); self.library_btn.setProperty("active", i == 2); [ (b.style().unpolish(b), b.style().polish(b)) for b in [self.home_btn, self.search_btn, self.library_btn]]
    def switch_to_now_playing(self): self.content_stack.setCurrentIndex(3)

    def init_home_page(self):
        main_h_layout = QVBoxLayout(self.home_page); main_h_layout.setContentsMargins(0, 40, 0, 0); main_h_layout.setSpacing(15)
        self.pref_container = QWidget(); self.pref_layout = QHBoxLayout(self.pref_container); self.pref_layout.setContentsMargins(40, 0, 40, 0); self.pref_layout.setSpacing(10)
        langs = ["Hindi", "English", "Punjabi", "Haryanvi", "Bhojpuri", "Gujarati", "Tiktok Trending"]
        user_langs = self.storage.get_preferences().get("languages", ["Hindi"])
        for lang in langs:
            chip = FilterChipButton(lang, active=(lang in user_langs)); chip.clicked.connect(self.on_lang_chip_clicked); self.pref_layout.addWidget(chip)
        self.pref_layout.addStretch(); main_h_layout.addWidget(self.pref_container)
        self.home_scroll = QScrollArea(); self.home_scroll.setWidgetResizable(True); self.home_scroll.setStyleSheet("background: transparent; border: none;"); self.home_scroll_container = QWidget(); self.home_rows_layout = QVBoxLayout(self.home_scroll_container); self.home_rows_layout.setContentsMargins(40, 20, 40, 20); self.home_rows_layout.setSpacing(40)
        self.home_scroll.setWidget(self.home_scroll_container); main_h_layout.addWidget(self.home_scroll)

    def on_lang_chip_clicked(self):
        selected = []
        for i in range(self.pref_layout.count()):
            w = self.pref_layout.itemAt(i).widget()
            if isinstance(w, FilterChipButton) and w.isChecked():
                selected.append(w.text())
        self.storage.update_languages(selected); self.refresh_home_dashboard()

    def refresh_home_dashboard(self):
        self.clear_layout(self.home_rows_layout); art_h = QLabel("Popular Artists"); art_h.setObjectName("SectionHeader"); self.home_rows_layout.addWidget(art_h)
        a_s = QScrollArea(); a_s.setFixedHeight(210); a_s.setWidgetResizable(True); a_s.setStyleSheet("background: transparent; border: none;"); a_c = QWidget(); a_l = QHBoxLayout(a_c); a_l.setContentsMargins(0,0,0,0); a_l.setSpacing(15)
        ads = [("Arijit Singh", "https://i.scdn.co/image/ab6761610000e5eb12810de09aef82b3c2069670"), ("Atif Aslam", "https://i.scdn.co/image/ab6761610000e5eb748805f42f53d71221fcc232"), ("Shreya Ghoshal", "https://i.scdn.co/image/ab6761610000e5eb7ed821e25e9acc8a2fb3a4d9"), ("Alka Yagnik", "https://i.scdn.co/image/ab6761610000e5eb46059c393bcaf146e4544760"), ("Honey Singh", "https://i.scdn.co/image/ab6761610000e5ebcc7517973d47ad8fcfcb7fb4"), ("Jubin Nautiyal", "https://i.scdn.co/image/ab6761610000e5eb4270d49489ef0cbcf3ca5932")]
        for n, u in ads:
            c = ArtistCardWidget(n); c.clicked.connect(self.load_artist_songs); a_l.addWidget(c); loader = ThumbnailLoader(c, u, f"Artist_{n}"); loader.thumbnail_loaded.connect(self.on_artist_image_loaded); loader.finished.connect(lambda l=loader: self.active_threads.remove(l) if l in self.active_threads else None); self.active_threads.append(loader); loader.start()
        a_l.addStretch(); a_s.setWidget(a_c); self.home_rows_layout.addWidget(a_s)
        
        pref = self.storage.get_preferences(); user_langs = pref.get("languages", ["Hindi"]); searches = pref.get("last_searches", [])
        top_artists = self.get_top_artists_from_history()
        for art, _ in top_artists[:2]: self.add_dynamic_row(f"More from {art}", f"{art} best songs mix", f"home_{art.lower().replace(' ', '_')}")
        for term in searches[:2]: self.add_dynamic_row(f"Based on your search: {term}", f"{term} mix songs", f"home_search_{term.lower().replace(' ', '_')}")
        
        for lang in user_langs[:3]:
            self.add_dynamic_row(f"Top {lang} Hits", f"new {lang} songs 2024 trending", f"home_lang_{lang.lower()}")
            self.add_dynamic_row(f"Discover {lang} Folk & Pop", f"{lang} traditional and modern hits", f"home_folk_{lang.lower()}")
        
        self.add_dynamic_row("Daily Refresh", "latest bollywood music 2024", "home_ref")
        self.add_dynamic_row("Chill & Lo-Fi Lounge", "lofi hip hop music chill mix hindi", "home_lofi")
        self.add_dynamic_row("High Energy Floor Fillers", "latest party songs 2024 dance", "home_party")
        his_h = QLabel("Recently Played"); his_h.setObjectName("SectionHeader"); self.home_rows_layout.addWidget(his_h); self.his_scroll = self.create_row_scroll(); self.his_layout = self.his_scroll.widget().layout(); self.home_rows_layout.addWidget(self.his_scroll); self.load_history(); self.home_rows_layout.addStretch()

    def add_dynamic_row(self, title, query, context):
        h = QLabel(title); h.setObjectName("SectionHeader"); self.home_rows_layout.addWidget(h); s = self.create_row_scroll(); s.setProperty("context", context); self.home_rows_layout.addWidget(s)
        t = SearchThread(self.youtube_client, query, context=context, limit=12); t.results_found.connect(self.on_search_results); t.finished.connect(lambda t=t: self.active_threads.remove(t) if t in self.active_threads else None); self.active_threads.append(t); t.start()

    def start_search(self, q=None):
        if not q: q = self.search_input.text()
        if not q or len(q) < 3: return
        self.storage.add_search_term(q); self.loading_label.setText(f"Searching for '{q}'..."); self.search_thread = SearchThread(self.youtube_client, q, context="search", limit=25); self.search_thread.results_found.connect(self.on_search_results); self.search_thread.start()

    def get_top_artists_from_history(self):
        hist = self.storage.get_history()
        if not hist: return []
        texts = [v.get('title', '') + " " + (v.get('uploader', '') or '') for v in hist]
        top_names = ["Arijit Singh", "Atif Aslam", "Shreya Ghoshal", "Alka Yagnik", "Honey Singh", "Jubin Nautiyal", "Taylor Swift", "Darshan Raval", "Armaan Malik"]
        counts = Counter()
        for t in texts:
            for n in top_names:
                if n.lower() in t.lower(): counts[n] += 1
        return counts.most_common(3)

    def on_artist_image_loaded(self, c, p, n): c.set_image(p) if not p.isNull() else None
    def create_row_scroll(self): s = QScrollArea(); s.setFixedHeight(240); s.setWidgetResizable(True); s.setStyleSheet("background: transparent; border: none;"); c = QWidget(); l = QHBoxLayout(c); l.setContentsMargins(0,0,0,0); l.setSpacing(15); s.setWidget(c); return s
    def init_search_page(self):
        l = QVBoxLayout(self.search_page); l.setContentsMargins(40, 40, 40, 20); l.setSpacing(20); s_b = QHBoxLayout(); self.search_input = QLineEdit(); self.search_input.setObjectName("SearchBar"); self.search_input.setPlaceholderText("Search for songs, artists, or genres..."); self.search_input.setFixedHeight(50); self.search_input.textChanged.connect(lambda: self.search_debounce.start())
        s_c = QPushButton("Search"); s_c.setObjectName("PrimaryAction"); s_c.setFixedHeight(50); s_c.clicked.connect(self.start_search); s_b.addWidget(self.search_input, stretch=1); s_b.addWidget(s_c); l.addLayout(s_b); self.results_list = QListWidget(); self.results_list.itemDoubleClicked.connect(self.on_item_double_clicked); l.addWidget(self.results_list); self.loading_label = QLabel(""); self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter); l.addWidget(self.loading_label)
    def init_library_page(self):
        l = QHBoxLayout(self.library_page); l.setContentsMargins(0, 0, 0, 0); self.lib_list = QListWidget(); self.lib_list.setFixedWidth(200); self.lib_list.setObjectName("Sidebar"); self.lib_list.itemClicked.connect(self.load_playlist_items); l.addWidget(self.lib_list); r_c = QWidget(); r_l = QVBoxLayout(r_c); r_l.setContentsMargins(30,30,30,30); l_h = QLabel("Your Playlists"); l_h.setObjectName("SectionHeader"); r_l.addWidget(l_h); self.lib_tracks = QListWidget(); self.lib_tracks.itemDoubleClicked.connect(self.on_item_double_clicked); r_l.addWidget(self.lib_tracks); n_p = QPushButton("+ Create Playlist"); n_p.setObjectName("SecondaryAction"); n_p.clicked.connect(self.create_playlist); r_l.addWidget(n_p); l.addWidget(r_c)

    def load_artist_songs(self, n): self.switch_page(1); self.search_input.setText(n); self.start_search(n + " popular songs")
    def load_startup_content(self): self.refresh_home_dashboard()
    def on_search_results(self, results, context):
        self.loading_label.setText("")
        if context == "search":
            self.results_list.clear(); artists = [v for v in results if v.get('is_artist')]; songs = [v for v in results if not v.get('is_artist')]
            if artists: h = QListWidgetItem("TOP ARTISTS"); h.setObjectName("ResultHeader"); h.setFlags(Qt.ItemFlag.NoItemFlags); self.results_list.addItem(h); [self.add_to_list_widget(self.results_list, v) for v in artists]
            if songs: h = QListWidgetItem("SONGS"); h.setObjectName("ResultHeader"); h.setFlags(Qt.ItemFlag.NoItemFlags); self.results_list.addItem(h); [self.add_to_list_widget(self.results_list, v) for v in songs]
        elif context.startswith("home_"):
            for i in range(self.home_rows_layout.count()):
                w = self.home_rows_layout.itemAt(i).widget()
                if isinstance(w, QScrollArea) and w.property("context") == context:
                    l = w.widget().layout(); self.clear_layout(l)
                    for v in results[:10]:
                        c = SongCardWidget(v); c.clicked.connect(self.play_video); l.addWidget(c)
                        if v.get('thumbnail'): lo = ThumbnailLoader(c, v['thumbnail'], v['id']); lo.thumbnail_loaded.connect(self.on_card_thumb_loaded); lo.finished.connect(lambda l=lo: self.active_threads.remove(l) if l in self.active_threads else None); self.active_threads.append(lo); lo.start()
                    l.addStretch(); break

    def on_card_thumb_loaded(self, card, pixmap, video_id): self.image_cache[video_id] = pixmap; card.set_thumbnail(pixmap)
    def clear_layout(self, layout):
        while layout.count(): item = layout.takeAt(0); item.widget().deleteLater() if item.widget() else None
    def add_to_list_widget(self, list_widget, video):
        item = QListWidgetItem(); item.setSizeHint(QSize(0, 72)); item.setData(Qt.ItemDataRole.UserRole, video); list_widget.addItem(item); widget = SongItemWidget(video); widget.add_to_playlist_clicked.connect(self.show_add_to_playlist_dialog); list_widget.setItemWidget(item, widget)
        if video['id'] in self.image_cache: widget.set_thumbnail(self.image_cache[video['id']])
        elif video.get('thumbnail'):
            lo = ThumbnailLoader(widget, video['thumbnail'], video['id']); lo.thumbnail_loaded.connect(lambda w, p, vid: self.cache_and_set(w, p, vid)); lo.finished.connect(lambda l=lo: self.active_threads.remove(l) if l in self.active_threads else None); self.active_threads.append(lo); lo.start()
    def cache_and_set(self, w, p, v_id): self.image_cache[v_id] = p; w.set_thumbnail(p)
    def play_video(self, v):
        self.current_video = v; self.storage.add_to_history(v); self.history_session.append(v); self.played_video_ids.add(v['id']); self.mini_title.setText(v['title']); pix = self.image_cache.get(v['id'])
        if pix: (self.mini_thumb.setPixmap(pix.scaled(40,40)), self.update_ambient_glow(pix))
        self.load_history(); self.fetch_recommendations(v); self.stream_thread = StreamUrlThread(self.youtube_client, v['url']); self.stream_thread.url_found.connect(self.on_stream_url_ready); self.stream_thread.start(); self.now_playing_page.update_info(v, pix); self.switch_to_now_playing()
    def update_ambient_glow(self, p):
        if not p: return
        i = p.toImage().scaled(1, 1, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation); c = QColor(i.pixel(0, 0))
        if c.lightness() < 30: c = c.lighter(150)
        self.now_playing_page.set_ambient_color(c)
    def on_stream_url_ready(self, url, title): (self.now_playing_page.update_play_btn(True), self.timer.start()) if self.audio_player.play_url(url, crossfade=True) else None
    def update_progress(self):
        ms = self.audio_player.get_time(); self.now_playing_page.update_progress(ms)
        if self.was_playing and not self.audio_player.is_playing():
             l = self.audio_player.get_length(); [self.play_next_in_queue() for _ in [0] if l > 0 and (l - ms) < 2000]
        self.was_playing = self.audio_player.is_playing()
    def play_next_in_queue(self): [self.play_video(self.next_queue.pop(0)) for _ in [0] if self.next_queue]
    def play_previous_song(self): [ (self.history_session.pop(), self.play_video(self.history_session.pop())) for _ in [0] if len(self.history_session) >= 2]
    def play_pause(self): (self.audio_player.pause(), self.now_playing_page.update_play_btn(False)) if self.audio_player.is_playing() else (self.audio_player.pause(), self.now_playing_page.update_play_btn(True))
    def set_position(self, p): self.audio_player.set_time(p)
    def load_history(self):
        if not hasattr(self, 'his_layout'): return
        self.clear_layout(self.his_layout); hist = self.storage.get_history()[:10]
        for v in hist:
            card = SongCardWidget(v); card.clicked.connect(self.play_video); self.his_layout.addWidget(card)
            if v['id'] in self.image_cache: card.set_thumbnail(self.image_cache[v['id']])
            elif v.get('thumbnail'): th = ThumbnailLoader(card, v['thumbnail'], v['id']); th.thumbnail_loaded.connect(self.on_card_thumb_loaded); th.finished.connect(lambda l=th: self.active_threads.remove(l) if l in self.active_threads else None); self.active_threads.append(th); th.start()
        self.his_layout.addStretch()
    def load_playlists(self): [self.lib_list.addItem(n) for n in self.storage.get_playlists()]
    def load_playlist_items(self, itm): self.lib_tracks.clear(); [self.add_to_list_widget(self.lib_tracks, v) for v in self.storage.get_playlists().get(itm.text(), [])]
    def create_playlist(self): (n, ok) = QInputDialog.getText(self, "New Playlist", "Playlist Name:"); [(self.storage.create_playlist(n), self.load_playlists()) for _ in [0] if ok and n]
    def show_add_to_playlist_dialog(self, v):
        pls = self.storage.get_playlists(); itms = list(pls.keys()) + ["+ New Playlist"]; itm, ok = QInputDialog.getItem(self, "Add to Playlist", "Select Playlist:", itms, 0, False)
        if ok and itm:
            if itm == "+ New Playlist":
                n, ok2 = QInputDialog.getText(self, "New Playlist", "Name:"); [(self.storage.create_playlist(n), self.storage.add_to_playlist(n, v), self.load_playlists()) for _ in [0] if ok2 and n]
            else: self.storage.add_to_playlist(itm, v)
    def fetch_recommendations(self, v):
        t = v.get('title', ''); art = ""; song = ""; [ (art := p[0].strip(), song := p[1].strip()) for s in [' - ', ' | ', ' – ', ' : '] for p in [t.split(s)] if s in t and len(p) >= 2 ]
        qs = []
        if art: c_s = re.sub(r'[^a-zA-Z0-9\s]', '', song).split()[0] if song else ""; eq = f"-{c_s}" if c_s else ""; qs = [f'"{art}" popular music {eq}', f'"{art}" hits mix', f'songs by {art}', f'similar to {art} music']
        else: w = t.split(); qs = [f'{w[0]} related songs -{w[0]}'] if len(w) >= 2 else ['top bollywood music hits']
        final_query = random.choice(qs); self.rec_thread = SearchThread(self.youtube_client, final_query, context="recommendation", limit=40); self.rec_thread.results_found.connect(self.on_search_results); self.rec_thread.start()
    def on_item_double_clicked(self, i): self.play_video(i.data(Qt.ItemDataRole.UserRole))

if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv); window = MainWindow(); window.show(); sys.exit(app.exec())
