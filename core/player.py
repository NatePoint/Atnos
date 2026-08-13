import os
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


class PlayerCore(QObject):
    track_changed = Signal(dict)
    position_changed = Signal(int)
    duration_changed = Signal(int)
    playback_state_changed = Signal(bool)

    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self.playlist = []
        self.current_index = -1

        self.player.positionChanged.connect(self.position_changed.emit)
        self.player.durationChanged.connect(self.duration_changed.emit)
        self.player.playbackStateChanged.connect(self._on_state_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status)

    def set_playlist(self, files: list):
        self.playlist = files
        self.current_index = 0

    def play_track(self, index: int):
        if not self.playlist or index < 0 or index >= len(self.playlist):
            return

        self.current_index = index
        file_path = os.path.abspath(self.playlist[index])

        url = QUrl.fromLocalFile(file_path)
        self.player.setSource(url)

        track_info = self.parse_track_info(file_path)
        self.track_changed.emit(track_info)
        self.player.play()

    def play_index(self, index: int):
        self.play_track(index)

    def parse_track_info(self, file_path: str) -> dict:
        filename = os.path.basename(file_path)
        title, _ = os.path.splitext(filename)
        artist = "Неизвестный исполнитель"

        if " - " in title:
            parts = title.split(" - ", 1)
            artist, title = parts[0].strip(), parts[1].strip()
        elif "_" in title:
            title = title.replace("_", " ")

        return {"title": title, "artist": artist, "path": file_path}

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            if self.player.source().isEmpty() and self.playlist:
                self.play_track(0)
            else:
                self.player.play()

    def next_track(self):
        if not self.playlist:
            return
        next_idx = (self.current_index + 1) % len(self.playlist)
        self.play_track(next_idx)

    def prev_track(self):
        if not self.playlist:
            return
        prev_idx = (self.current_index - 1) % len(self.playlist)
        self.play_track(prev_idx)

    def set_volume(self, val: int):
        self.audio_output.setVolume(val / 100.0)

    def seek(self, pos_ms: int):
        self.player.setPosition(pos_ms)

    def _on_state_changed(self, state):
        is_playing = (state == QMediaPlayer.PlayingState)
        self.playback_state_changed.emit(is_playing)

    def _on_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.next_track()