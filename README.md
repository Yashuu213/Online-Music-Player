# ⚡ Pikachu Music Player

<div align="center">

![Pikachu Music Player](https://img.shields.io/badge/Pikachu-Music%20Player-FFD700?style=for-the-badge&logo=spotify&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-GUI-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**A stunning, Pikachu-themed music player that streams YouTube audio with zero cost!**

*Experience music like never before with our electrifying interface* ⚡🎵

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Screenshots](#-screenshots) • [Build](#-building-executable)

</div>

---

## ✨ Features

### 🎨 **Modern Pikachu-Themed UI**
- **Electric Yellow & Blue Design** - Inspired by Pikachu's signature colors
- **Glassmorphism Effects** - Beautiful semi-transparent cards with blur
- **Spotify-Style Grid Layout** - Browse recommendations like a pro
- **Smooth Animations** - Hover effects and transitions throughout
- **Dark Theme** - Easy on the eyes for extended listening sessions

### 🎵 **Powerful Music Features**
- **🔍 YouTube Search** - Find any song instantly
- **🎧 High-Quality Streaming** - Direct audio streaming without video downloads
- **📊 Smart Dashboard** - View stats, recently played, and personalized recommendations
- **🎤 Popular Artists** - Quick access to your favorite artists
- **📜 History Tracking** - Never lose track of what you've listened to
- **🎵 Playlist Management** - Create and organize your music collections
- **⏭️ Queue System** - Build your perfect listening session
- **🎨 Album Art Display** - Beautiful rotating visualizer with album artwork

### 🎛️ **Advanced Playback Controls**
- **Play/Pause/Stop** - Full playback control
- **Previous/Next** - Navigate through your queue
- **Volume Control** - Adjust to your preference
- **Seek Bar** - Jump to any part of the song
- **Mini Player** - Always-visible bottom bar for quick controls
- **Now Playing View** - Full-screen immersive experience

### 💾 **Smart Data Management**
- **Auto-Save History** - Last 50 songs automatically tracked
- **Persistent Playlists** - Your collections saved locally
- **Thumbnail Caching** - Faster loading with cached images
- **JSON Storage** - Lightweight, human-readable data format

---

## 🚀 Installation

### Prerequisites
- **Python 3.8 or higher**
- **VLC Media Player** (required for audio playback)

### Step 1: Install VLC Media Player

#### Windows
Download and install from [videolan.org](https://www.videolan.org/vlc/download-windows.html)

#### Linux
```bash
sudo apt install vlc
```

#### macOS
```bash
brew install --cask vlc
```

### Step 2: Clone the Repository
```bash
git clone https://github.com/yourusername/pikachu-music-player.git
cd pikachu-music-player
```

### Step 3: Install Python Dependencies
```bash
pip install -r requirements.txt
```

**Dependencies:**
- `PyQt6` - Modern GUI framework
- `requests` - HTTP library for thumbnails
- `python-vlc` - VLC Python bindings
- `yt-dlp` - YouTube video/audio extraction

---

## 🎮 Usage

### Starting the Application
```bash
python main.py
```

### Quick Start Guide

1. **🏠 Dashboard**
   - View your listening statistics
   - Browse personalized recommendations (15 songs in grid layout)
   - Click any artist button to explore their music
   - See your recently played tracks

2. **🔍 Search**
   - Enter song name, artist, or keywords
   - Click Search or press Enter
   - Double-click any result to play instantly
   - Right-click to add to playlist

3. **📜 History**
   - View all previously played songs
   - Double-click to replay
   - Automatic tracking of last 50 songs

4. **🎵 Playlists**
   - Create custom playlists
   - Add songs from search or history
   - Click playlist cards to view contents
   - Manage your music collections

5. **🎶 Now Playing**
   - Full-screen music player
   - Rotating album art with electric glow
   - Yellow bar visualizer
   - Complete playback controls
   - Up Next queue display

---

## 📸 Screenshots

### Dashboard - Your Music Hub
![Dashboard](docs/dashboard.png)
*Beautiful Spotify-style grid with personalized recommendations and popular artists*

### Search - Find Any Song
![Search](docs/search.png)
*Instant YouTube search with modern card layout*

### Now Playing - Immersive Experience
![Now Playing](docs/now-playing.png)
*Full-screen player with rotating album art and Pikachu-themed visualizer*

### Playlists - Organize Your Music
![Playlists](docs/playlists.png)
*Grid view of your playlists with easy management*

---

## 🏗️ Project Structure

```
pikachu-music-player/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── data.json              # User data (history, playlists)
├── core/
│   ├── audio_player.py    # VLC audio playback engine
│   ├── youtube_client.py  # YouTube search & streaming
│   └── storage.py         # Data persistence manager
├── ui/
│   ├── main_window.py     # Main application window
│   ├── now_playing.py     # Now Playing widget
│   ├── custom_widgets.py  # Custom UI components
│   ├── styles.py          # Pikachu theme stylesheet
│   ├── icons.py           # SVG icon definitions
│   └── visualizer.py      # Audio visualizers
└── BUILD_EXE.md           # Executable build guide
```

---

## 🔧 Building Executable

Want to create a standalone `.exe` file? Check out our detailed guide:

📄 **[BUILD_EXE.md](BUILD_EXE.md)** - Complete instructions for creating Windows executables with PyInstaller

---

## 🎨 Design Philosophy

### Color Palette
- **Primary**: Electric Yellow (`#FFD700`, `#FFC107`) - Pikachu's signature color
- **Accent**: Electric Blue (`#00D4FF`, `#0099CC`) - Electric-type energy
- **Background**: Deep Navy (`#0A0E27`, `#1A1A2E`) - Dark, immersive
- **Text**: Light Gray (`#E0E0E0`) with yellow highlights

### UI/UX Principles
- **Glassmorphism**: Semi-transparent cards with subtle borders
- **Smooth Transitions**: 200-300ms hover effects
- **Grid Layouts**: Spotify-inspired browsing experience
- **Consistent Spacing**: 15-20px between elements
- **Rounded Corners**: 10-16px border radius throughout

---

## 🛠️ Technical Details

### Backend Architecture
- **Audio Engine**: VLC Media Player (python-vlc)
- **YouTube Integration**: yt-dlp for video/audio extraction
- **Data Storage**: JSON-based local storage
- **Threading**: QThread for non-blocking operations

### Frontend Framework
- **GUI**: PyQt6 with custom widgets
- **Styling**: CSS-like stylesheets with gradients
- **Icons**: SVG-based scalable icons
- **Animations**: Qt property animations

### Performance Optimizations
- **Thumbnail Caching**: Reduces network requests
- **Async Loading**: Background threads for search/thumbnails
- **Lazy Loading**: Load content as needed
- **Efficient Rendering**: Optimized widget updates

---

## 📋 Features Roadmap

### Current Version (v1.0)
- ✅ Modern Pikachu-themed UI
- ✅ YouTube search and streaming
- ✅ Playlist management
- ✅ History tracking
- ✅ Dashboard with recommendations
- ✅ Now Playing visualizer

### Planned Features (v2.0)
- 🔄 Lyrics display
- 🔄 Equalizer controls
- 🔄 Sleep timer
- 🔄 Keyboard shortcuts
- 🔄 Multiple theme options
- 🔄 Export/Import playlists
- 🔄 Cloud sync (optional)

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 style guide
- Add docstrings to functions
- Test on multiple platforms
- Update documentation

---

## 🐛 Troubleshooting

### Common Issues

**Q: App crashes on startup**
- Ensure VLC Media Player is installed
- Check Python version (3.8+)
- Verify all dependencies are installed

**Q: No sound during playback**
- Verify VLC is working independently
- Check system volume settings
- Ensure audio output device is connected

**Q: Search not working**
- Check internet connection
- Verify yt-dlp is up to date: `pip install --upgrade yt-dlp`

**Q: Thumbnails not loading**
- Check internet connection
- Clear cache by deleting `data.json` (backup first!)

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **VLC Media Player** - Powerful multimedia framework
- **yt-dlp** - YouTube video/audio extraction
- **PyQt6** - Modern Python GUI framework
- **Pikachu** - Inspiration for the electric theme ⚡

---

## 📞 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/pikachu-music-player/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/pikachu-music-player/discussions)

---

<div align="center">

**Made with ⚡ and 💛 by [Your Name]**

*If you like this project, please give it a ⭐!*

[![GitHub stars](https://img.shields.io/github/stars/yourusername/pikachu-music-player?style=social)](https://github.com/yourusername/pikachu-music-player/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/yourusername/pikachu-music-player?style=social)](https://github.com/yourusername/pikachu-music-player/network/members)

</div>
