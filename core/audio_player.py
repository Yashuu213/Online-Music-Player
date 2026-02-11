import vlc
import sys
import time

class AudioPlayer:
    def __init__(self):
        # Force DirectX audio output to avoid MMDevice COM threading issues on Windows
        options = ["--aout=directx"]
        if sys.platform.startswith('linux'):
             options = [] # Default usually works on Linux
             
        self.instance = vlc.Instance(*options)
        self.player = self.instance.media_player_new()
        
    def play_url(self, url):
        """
        Plays the audio from the given URL.
        """
        try:
            media = self.instance.media_new(url)
            self.player.set_media(media)
            self.player.play()
            return True
        except Exception as e:
            print(f"Error playing: {e}")
            return False

    def pause(self):
        """
        Toggles pause/resume.
        """
        self.player.pause()

    def stop(self):
        """
        Stops playback.
        """
        self.player.stop()

    def set_volume(self, volume):
        """
        Sets volume (0-100).
        """
        self.player.audio_set_volume(volume)

    def get_time(self):
        """
        Returns current playback time in milliseconds.
        """
        return self.player.get_time()

    def set_time(self, position):
        """
        Sets playback time in milliseconds.
        """
        self.player.set_time(position)

    def get_length(self):
        """
        Returns total length of media in milliseconds.
        """
        return self.player.get_length()

    def is_playing(self):
        """
        Returns true if playing.
        """
        return self.player.is_playing()
