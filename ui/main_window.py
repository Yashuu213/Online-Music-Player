from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, 
    QLabel, QSlider, QMessageBox, QTabWidget, QMenu, QInputDialog,
    QStackedWidget, QFrame, QSizePolicy, QScrollArea
)
import sys
import os
import re
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QIcon, QPixmap, QAction, QMovie, QColor
import requests
import random

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
        self.client = client
        self.query = query
        self.context = context
        self.limit = limit

    def run(self):
        try:
            results = self.client.search(self.query, limit=self.limit)
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
    thumbnail_loaded = pyqtSignal(object, QPixmap, str) 

    def __init__(self, item_widget, url, video_id):
        super().__init__()
        self.item_widget = item_widget
        self.url = url
        self.video_id = video_id

    def run(self):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = requests.get(self.url, headers=headers, timeout=10)
            if resp.status_code == 200:
                pixmap = QPixmap(); [self.thumbnail_loaded.emit(self.item_widget, pixmap, self.video_id) for _ in [0] if pixmap.loadFromData(resp.content)]
        except Exception as e: print(f"DEBUG: Thumbnail load error: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pikachu Music Player")
        self.setGeometry(100, 100, 1200, 850)
        self.setStyleSheet(PREMIUM_PIKACHU_THEME)

        self.youtube_client = YouTubeClient()
        self.audio_player = AudioPlayer()
        self.storage = StorageManager()
        
        self.current_video = None
        self.next_queue = []
        self.image_cache = {} 
        self.history_session = [] 
        self.played_video_ids = set()
        self.was_playing = False
        self.active_threads = [] 
        
        # Debounce Timer for Smart Search
        self.search_debounce = QTimer()
        self.search_debounce.setSingleShot(True)
        self.search_debounce.setInterval(400) 
        self.search_debounce.timeout.connect(self.start_search)
        
        self.init_ui()
        self.load_history() 
        self.load_playlists()
        self.load_startup_content()
        
        self.timer = QTimer()
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.update_progress)

    def init_ui(self):
        self.central_container = QWidget(); self.setCentralWidget(self.central_container)
        main_layout = QHBoxLayout(self.central_container); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)
        
        self.sidebar = QFrame(); self.sidebar.setObjectName("Sidebar"); self.sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(self.sidebar); sidebar_layout.setContentsMargins(20, 30, 20, 30); sidebar_layout.setSpacing(10)
        
        branding_layout = QHBoxLayout(); self.branding_gif = QLabel(); self.branding_gif.setFixedSize(50, 50)
        base_path = os.path.dirname(os.path.abspath(__file__)); gif_path = os.path.join(base_path, "..", "pii.gif")
        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path); self.movie.setScaledSize(QSize(50, 50)); self.branding_gif.setMovie(self.movie); self.movie.start()
        else:
            self.branding_gif.setText("⚡"); self.branding_gif.setStyleSheet("font-size: 30px; color: #FFD700;")
            
        branding_layout.addWidget(self.branding_gif); b_l = QLabel("Pikachuu"); b_l.setStyleSheet("font-size: 24px; font-weight: 800; color: #FFD700;")
        branding_layout.addWidget(b_l); sidebar_layout.addLayout(branding_layout); sidebar_layout.addSpacing(30)
        
        self.home_btn = self.create_sidebar_item("HOME", SVG_HOME, 0); sidebar_layout.addWidget(self.home_btn)
        self.search_btn = self.create_sidebar_item("SEARCH", SVG_SEARCH, 1); sidebar_layout.addWidget(self.search_btn)
        self.library_btn = self.create_sidebar_item("LIBRARY", SVG_LIBRARY, 2); sidebar_layout.addWidget(self.library_btn)
        
        sidebar_layout.addStretch()
        self.mini_player = QFrame(); self.mini_player.setObjectName("GlassPanel"); self.mini_player.setFixedHeight(120); m_l = QVBoxLayout(self.mini_player)
        self.mini_thumb = QLabel(); self.mini_thumb.setFixedSize(40, 40); self.mini_thumb.setStyleSheet("background: #000; border-radius: 4px;"); m_l.addWidget(self.mini_thumb, alignment=Qt.AlignmentFlag.AlignCenter)
        self.mini_title = QLabel("Ready to play"); self.mini_title.setObjectName("MutedText"); self.mini_title.setAlignment(Qt.AlignmentFlag.AlignCenter); m_l.addWidget(self.mini_title)
        e_m = QPushButton("Expand Player"); e_m.setObjectName("SecondaryAction"); e_m.clicked.connect(self.switch_to_now_playing); m_l.addWidget(e_m); sidebar_layout.addWidget(self.mini_player); main_layout.addWidget(self.sidebar)
        
        self.content_stack = QStackedWidget(); self.home_page = QWidget(); self.init_home_page(); self.content_stack.addWidget(self.home_page)
        self.search_page = QWidget(); self.init_search_page(); self.content_stack.addWidget(self.search_page)
        self.library_page = QWidget(); self.init_library_page(); self.content_stack.addWidget(self.library_page)
        self.now_playing_page = NowPlayingWidget(); self.content_stack.addWidget(self.now_playing_page)
        self.now_playing_page.back_clicked.connect(lambda: self.switch_page(0))
        self.now_playing_page.next_song_requested.connect(self.play_video); self.now_playing_page.play_pause_clicked.connect(self.play_pause)
        self.now_playing_page.prev_clicked.connect(self.play_previous_song); self.now_playing_page.next_clicked.connect(self.play_next_in_queue)
        self.now_playing_page.seek_requested.connect(self.set_position); main_layout.addWidget(self.content_stack, stretch=1); self.switch_page(0) 

    def create_sidebar_item(self, text, icon_svg, index):
        btn = QPushButton(f"  {text}"); btn.setObjectName("SidebarItem"); btn.setIcon(get_icon(icon_svg, "#94A3B8")); btn.setIconSize(QSize(20, 20)); btn.setCursor(Qt.CursorShape.PointingHandCursor); btn.clicked.connect(lambda: self.switch_page(index)); return btn

    def switch_page(self, i): self.content_stack.setCurrentIndex(i); self.home_btn.setProperty("active", i == 0); self.search_btn.setProperty("active", i == 1); self.library_btn.setProperty("active", i == 2); [ (b.style().unpolish(b), b.style().polish(b)) for b in [self.home_btn, self.search_btn, self.library_btn]]
    def switch_to_now_playing(self): self.content_stack.setCurrentIndex(3)

    def init_home_page(self):
        main_h_layout = QVBoxLayout(self.home_page); main_h_layout.setContentsMargins(40, 40, 40, 40); main_h_layout.setSpacing(30); s = QScrollArea(); s.setWidgetResizable(True); s.setStyleSheet("background: transparent; border: none;"); s_c = QWidget(); s_l = QVBoxLayout(s_c); s_l.setSpacing(40)
        art_h = QLabel("Popular Artists"); art_h.setObjectName("SectionHeader"); s_l.addWidget(art_h); self.art_scroll = QScrollArea(); self.art_scroll.setFixedHeight(210); self.art_scroll.setWidgetResizable(True); self.art_scroll.setStyleSheet("background: transparent; border: none;")
        self.art_container = QWidget(); self.art_layout = QHBoxLayout(self.art_container); self.art_layout.setContentsMargins(0,0,0,0); self.art_layout.setSpacing(15)
        ads = [("Arijit Singh", "https://i.scdn.co/image/ab6761610000e5eb12810de09aef82b3c2069670"), ("Atif Aslam", "https://i.scdn.co/image/ab6761610000e5eb748805f42f53d71221fcc232"), ("Shreya Ghoshal", "https://i.scdn.co/image/ab6761610000e5eb7ed821e25e9acc8a2fb3a4d9"), ("Alka Yagnik", "https://i.scdn.co/image/ab6761610000e5eb46059c393bcaf146e4544760"), ("Honey Singh", "https://i.scdn.co/image/ab6761610000e5ebcc7517973d47ad8fcfcb7fb4"), ("Jubin Nautiyal", "https://i.scdn.co/image/ab6761610000e5eb4270d49489ef0cbcf3ca5932")]
        for name, img_url in ads:
            card = ArtistCardWidget(name); card.clicked.connect(self.load_artist_songs); self.art_layout.addWidget(card); loader = ThumbnailLoader(card, img_url, f"Artist_{name}"); loader.thumbnail_loaded.connect(self.on_artist_image_loaded); loader.finished.connect(lambda l=loader: self.active_threads.remove(l) if l in self.active_threads else None); self.active_threads.append(loader); loader.start()
        self.art_layout.addStretch(); self.art_scroll.setWidget(self.art_container); s_l.addWidget(self.art_scroll); rec_h = QLabel("Recommended for You"); rec_h.setObjectName("SectionHeader"); s_l.addWidget(rec_h); self.rec_scroll = self.create_row_scroll(); self.rec_layout = self.rec_scroll.widget().layout(); s_l.addWidget(self.rec_scroll)
        ari_h = QLabel("Best of Arijit Singh"); ari_h.setObjectName("SectionHeader"); s_l.addWidget(ari_h); self.ari_scroll = self.create_row_scroll(); self.ari_layout = self.ari_scroll.widget().layout(); s_l.addWidget(ari_h)
        atif_h = QLabel("Best of Atif Aslam"); atif_h.setObjectName("SectionHeader"); s_l.addWidget(atif_h); self.atif_scroll = self.create_row_scroll(); self.atif_layout = self.atif_scroll.widget().layout(); s_l.addWidget(atif_h)
        his_h = QLabel("Recently Played"); his_h.setObjectName("SectionHeader"); s_l.addWidget(his_h); self.his_scroll = self.create_row_scroll(); self.his_layout = self.his_scroll.widget().layout(); s_l.addWidget(self.his_scroll); s_l.addStretch(); s.setWidget(s_c); main_h_layout.addWidget(s)

    def on_artist_image_loaded(self, c, p, n): c.set_image(p) if not p.isNull() else None
    def create_row_scroll(self): s = QScrollArea(); s.setFixedHeight(240); s.setWidgetResizable(True); s.setStyleSheet("background: transparent; border: none;"); c = QWidget(); l = QHBoxLayout(c); l.setContentsMargins(0,0,0,0); l.setSpacing(15); s.setWidget(c); return s

    def init_search_page(self):
        l = QVBoxLayout(self.search_page); l.setContentsMargins(40, 40, 40, 20); l.setSpacing(20); s_b = QHBoxLayout()
        self.search_input = QLineEdit(); self.search_input.setObjectName("SearchBar"); self.search_input.setPlaceholderText("Search for songs, artists, or genres..."); self.search_input.setFixedHeight(50)
        self.search_input.textChanged.connect(lambda: self.search_debounce.start())
        s_c = QPushButton("Search"); s_c.setObjectName("PrimaryAction"); s_c.setFixedHeight(50); s_c.clicked.connect(self.start_search); s_b.addWidget(self.search_input, stretch=1); s_b.addWidget(s_c); l.addLayout(s_b)
        self.results_list = QListWidget(); self.results_list.itemDoubleClicked.connect(self.on_item_double_clicked); l.addWidget(self.results_list); self.loading_label = QLabel(""); self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter); l.addWidget(self.loading_label)
    def init_library_page(self):
        l = QHBoxLayout(self.library_page); l.setContentsMargins(0, 0, 0, 0); self.lib_list = QListWidget(); self.lib_list.setFixedWidth(200); self.lib_list.setObjectName("Sidebar"); self.lib_list.itemClicked.connect(self.load_playlist_items); l.addWidget(self.lib_list); r_c = QWidget(); r_l = QVBoxLayout(r_c); r_l.setContentsMargins(30,30,30,30)
        l_h = QLabel("Your Playlists"); l_h.setObjectName("SectionHeader"); r_l.addWidget(l_h); self.lib_tracks = QListWidget(); self.lib_tracks.itemDoubleClicked.connect(self.on_item_double_clicked); r_l.addWidget(self.lib_tracks); n_p = QPushButton("+ Create Playlist"); n_p.setObjectName("SecondaryAction"); n_p.clicked.connect(self.create_playlist); r_l.addWidget(n_p); l.addWidget(r_c)

    def start_search(self, q=None):
        if not q: q = self.search_input.text()
        if not q or len(q) < 3: return
        self.loading_label.setText(f"Searching for '{q}'..."); self.search_thread = SearchThread(self.youtube_client, q, context="search", limit=25); self.search_thread.results_found.connect(self.on_search_results); self.search_thread.start()

    def load_artist_songs(self, n): self.switch_page(1); self.search_input.setText(n); self.start_search(n + " popular songs")
    def load_startup_content(self):
        qs = [("Top Global Hits", "home_rec"), ("Arijit Singh Hits", "home_arijit"), ("Atif Aslam Popular Songs", "home_atif")]
        for q, c in qs:
            t = SearchThread(self.youtube_client, q, context=c, limit=20); t.results_found.connect(self.on_search_results); t.finished.connect(lambda t=t: self.active_threads.remove(t) if t in self.active_threads else None); self.active_threads.append(t); t.start()

    def on_search_results(self, results, context):
        self.loading_label.setText("")
        if context == "search":
            self.results_list.clear(); artists = [v for v in results if v.get('is_artist')]; songs = [v for v in results if not v.get('is_artist')]
            if artists:
                h = QListWidgetItem("TOP ARTISTS"); h.setObjectName("ResultHeader"); h.setFlags(Qt.ItemFlag.NoItemFlags); self.results_list.addItem(h); [self.add_to_list_widget(self.results_list, v) for v in artists]
            if songs:
                h = QListWidgetItem("SONGS"); h.setObjectName("ResultHeader"); h.setFlags(Qt.ItemFlag.NoItemFlags); self.results_list.addItem(h); [self.add_to_list_widget(self.results_list, v) for v in songs]
        elif context.startswith("home_"):
            if context == "home_rec": l = self.rec_layout
            elif context == "home_arijit": l = self.ari_layout
            elif context == "home_atif": l = self.atif_layout
            else: return
            self.clear_layout(l)
            for v in results[:10]:
                c = SongCardWidget(v); c.clicked.connect(self.play_video); l.addWidget(c)
                if v.get('thumbnail'):
                    loader = ThumbnailLoader(c, v['thumbnail'], v['id']); loader.thumbnail_loaded.connect(self.on_card_thumb_loaded); loader.finished.connect(lambda l=loader: self.active_threads.remove(l) if l in self.active_threads else None); self.active_threads.append(loader); loader.start()
            l.addStretch()
        elif context == "recommendation":
            import re
            def gcw(t): clean = re.sub(r'[\(\[].*?[\)\]]', '', t.lower()); return set(w for w in re.sub(r'[^a-zA-Z0-9\s]', ' ', clean).split() if len(w) > 2)
            def nt(t):
                if not t: return ""; n = re.sub(r'[\(\[].*?[\)\]]', '', t.lower())
                for x in ["remix", "lyrics", "audio", "official", "video", "karaoke", "instrumental", "unplugged", "cover", "full hd", "hd", "4k", "extra", "hits", "best"]: n = n.replace(x, "")
                return " ".join(re.sub(r'[^a-zA-Z0-9\s]', ' ', n).split())
            curr = self.current_video['title'] if self.current_video else ""; c_n = nt(curr); c_w = gcw(curr); filtered = []; seen = {c_n}
            for h in self.storage.get_history()[:30]: seen.add(nt(h.get('title', '')))
            random.shuffle(results)
            for v in results:
                v_n = nt(v['title']); overlap = len(c_w.intersection(gcw(v['title'])))
                if (v_n not in seen and overlap < 5 and v['id'] != (self.current_video['id'] if self.current_video else "")):
                    filtered.append(v); seen.add(v_n)
                if len(filtered) >= 20: break
            self.now_playing_page.up_next_list.clear(); self.next_queue = filtered; [self.add_to_list_widget(self.now_playing_page.up_next_list, v) for v in filtered]

    def on_card_thumb_loaded(self, card, pixmap, video_id): self.image_cache[video_id] = pixmap; card.set_thumbnail(pixmap)
    def clear_layout(self, layout):
        while layout.count(): child = layout.takeAt(0); child.widget().deleteLater() if child.widget() else None
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
        self.clear_layout(self.his_layout); hist = self.storage.get_history()[:10]
        for v in hist:
            card = SongCardWidget(v); card.clicked.connect(self.play_video); self.his_layout.addWidget(card)
            if v['id'] in self.image_cache: card.set_thumbnail(self.image_cache[v['id']])
            elif v.get('thumbnail'):
                th = ThumbnailLoader(card, v['thumbnail'], v['id']); th.thumbnail_loaded.connect(self.on_card_thumb_loaded); th.finished.connect(lambda l=th: self.active_threads.remove(l) if l in self.active_threads else None); self.active_threads.append(th); th.start()
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
    app = QApplication(sys.argv); window = MainWindow(); window.show(); sys.exit(app.exec())
