import json
import os

DATA_FILE = "data.json"

class StorageManager:
    def __init__(self):
        self.data = {
            "history": [],
            "playlists": {}
        }
        self.load_data()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    self.data = json.load(f)
            except:
                pass # Start fresh if corrupt

    def save_data(self):
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Error saving data: {e}")

    def add_to_history(self, video):
        # Avoid duplicates at the top
        history = self.data["history"]
        
        # Remove if exists already to move to top
        history = [v for v in history if v['id'] != video['id']]
        
        history.insert(0, video)
        
        # Limit history to 50 items
        if len(history) > 50:
            history.pop()
            
        self.data["history"] = history
        self.save_data()

    def get_history(self):
        return self.data["history"]

    def create_playlist(self, name):
        if name not in self.data["playlists"]:
            self.data["playlists"][name] = []
            self.save_data()
            return True
        return False

    def add_to_playlist(self, playlist_name, video):
        if playlist_name in self.data["playlists"]:
            # Check for duplicate
            playlist = self.data["playlists"][playlist_name]
            if not any(v['id'] == video['id'] for v in playlist):
                playlist.append(video)
                self.save_data()
                return True
        return False

    def get_playlists(self):
        return self.data["playlists"]

    def remove_from_playlist(self, playlist_name, video_id):
        if playlist_name in self.data["playlists"]:
            self.data["playlists"][playlist_name] = [
                v for v in self.data["playlists"][playlist_name] if v['id'] != video_id
            ]
            self.save_data()
