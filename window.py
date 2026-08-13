import os
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve, QSettings
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QFileDialog

from core.player import PlayerCore
from core.visualizer import AudioCoreVisualizer
from ui.components.widgets import (
    RedLineTitleBar, CategoryTabBar, SettingsDrawer, ProPlayerBar,
    TrackListWidget, draw_vector_icon, COLOR_BORDER
)

TRANSLATIONS = {
    "Русский": {
        "settings": "Настройки",
        "lang": "Язык / Language",
        "theme": "Тема оформления",
        "anim": "Стиль визуализатора",
        "folder_header": "Основная папка с музыкой",
        "no_folder": "Папка не выбрана",
        "select_folder": "Выбрать папку",
        "default_tab": "Все треки",
        "no_track": "Трек не выбран",
        "no_folder_hint": "Укажите папку в Настройках",
        "dialog_title": "Выберите основную папку с музыкой",
        "track_list_title": "Список композиций",
    },
    "English": {
        "settings": "Settings",
        "lang": "Language / Язык",
        "theme": "Appearance Theme",
        "anim": "Visualizer Style",
        "folder_header": "Main Music Folder",
        "no_folder": "No folder selected",
        "select_folder": "Select Folder",
        "default_tab": "All Tracks",
        "no_track": "No track selected",
        "no_folder_hint": "Select folder in Settings",
        "dialog_title": "Select Main Music Folder",
        "track_list_title": "Tracks List",
    }
}

THEME_COLORS = {
    "Тёмный графит": {"bg": "#121215", "accent": "#6366F1"},
    "OLED Чёрный": {"bg": "#000000", "accent": "#3B82F6"},
    "Киберпанк Неон": {"bg": "#0B0E14", "accent": "#F43F5E"},
    "Фиолетовый закат": {"bg": "#130E1C", "accent": "#A855F7"},
    "Изумрудный ночной": {"bg": "#091410", "accent": "#10B981"},
    "Tokyo Night": {"bg": "#1A1B26", "accent": "#7AA2F7"},
}


def format_time(ms: int) -> str:
    seconds = max(0, ms // 1000)
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"


class MinimalBgFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MinimalBgFrame")
        self.set_theme("Тёмный графит")

    def set_theme(self, theme_name: str):
        theme = THEME_COLORS.get(theme_name, THEME_COLORS["Тёмный графит"])
        self.setStyleSheet(f"""
            #MinimalBgFrame {{
                background-color: {theme['bg']};
                border: 1px solid {COLOR_BORDER};
                border-radius: 20px;
            }}
        """)


class RedLineMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings_store = QSettings("RedLine", "AtmosPlayer")
        self.player = PlayerCore()
        self.playlists = {}
        self.current_category = "Все треки"
        self.current_lang = self.settings_store.value("lang", "Русский")

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(1060, 680)

        self.bg_frame = MinimalBgFrame(self)

        main_layout = QVBoxLayout(self.bg_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.title_bar = RedLineTitleBar(self)
        self.title_bar.settings_toggled.connect(self.toggle_settings)
        main_layout.addWidget(self.title_bar)

        self.workspace = QWidget()
        ws_layout = QVBoxLayout(self.workspace)
        ws_layout.setContentsMargins(25, 0, 25, 20)

        self.tab_bar = CategoryTabBar()
        self.tab_bar.tab_changed.connect(self._on_category_changed)
        ws_layout.addWidget(self.tab_bar, alignment=Qt.AlignCenter)

        center_area = QHBoxLayout()
        center_area.setSpacing(20)

        self.track_list = TrackListWidget()
        self.track_list.setFixedWidth(340)
        self.track_list.track_selected.connect(self._on_track_list_item_clicked)
        center_area.addWidget(self.track_list)

        visualizer_container = QWidget()
        vis_layout = QVBoxLayout(visualizer_container)
        vis_layout.setContentsMargins(0, 0, 0, 0)

        self.visualizer = AudioCoreVisualizer()
        vis_layout.addStretch()
        vis_layout.addWidget(self.visualizer, alignment=Qt.AlignCenter)
        vis_layout.addStretch()

        center_area.addWidget(visualizer_container, stretch=1)
        ws_layout.addLayout(center_area, stretch=1)

        self.player_bar = ProPlayerBar()
        ws_layout.addWidget(self.player_bar)

        main_layout.addWidget(self.workspace)

        self.settings_drawer = SettingsDrawer(self.bg_frame)
        self.drawer_width = 310
        self.settings_drawer.hide()
        self.settings_drawer.folder_selected.connect(self.select_music_folder)
        self.settings_drawer.theme_changed.connect(self.apply_theme)
        self.settings_drawer.lang_changed.connect(self.change_language)
        self.settings_drawer.anim_changed.connect(self.apply_anim_style)

        self.anim = QPropertyAnimation(self.settings_drawer, b"geometry")
        self.anim.setDuration(280)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.finished.connect(self._on_anim_finished)

        self.setCentralWidget(self.bg_frame)
        self._bind_signals()
        self._load_saved_settings()

    def _bind_signals(self):
        self.player_bar.btn_play.clicked.connect(self.player.toggle_play)
        self.player_bar.btn_next.clicked.connect(self.player.next_track)
        self.player_bar.btn_prev.clicked.connect(self.player.prev_track)

        self.player_bar.vol_slider.valueChanged.connect(self.player.set_volume)
        self.player_bar.timeline_slider.sliderMoved.connect(self.player.seek)

        self.player.track_changed.connect(self._on_track_changed)
        self.player.position_changed.connect(self._on_position_changed)
        self.player.duration_changed.connect(self._on_duration_changed)
        self.player.playback_state_changed.connect(self._on_state_changed)

    def _load_saved_settings(self):
        saved_lang = self.settings_store.value("lang", "Русский")
        self.settings_drawer.lang_combo.setCurrentText(saved_lang)
        self.change_language(saved_lang)

        saved_theme = self.settings_store.value("theme", "Тёмный графит")
        self.settings_drawer.theme_combo.setCurrentText(saved_theme)
        self.apply_theme(saved_theme)

        saved_anim = self.settings_store.value("anim_style", "Импульсный круг")
        self.settings_drawer.anim_combo.setCurrentText(saved_anim)
        self.apply_anim_style(saved_anim)

        saved_folder = self.settings_store.value("music_folder", "")
        if saved_folder and os.path.exists(saved_folder):
            t = TRANSLATIONS[self.current_lang]
            self.settings_drawer.set_current_folder_text(saved_folder, t["no_folder"])
            self._scan_and_load_structure(saved_folder)

    def change_language(self, lang_name: str):
        self.current_lang = lang_name if lang_name in TRANSLATIONS else "Русский"
        self.settings_store.setValue("lang", self.current_lang)
        t = TRANSLATIONS[self.current_lang]

        self.title_bar.btn_settings.setText(t["settings"])
        self.settings_drawer.lbl_title.setText(t["settings"])
        self.settings_drawer.lbl_lang.setText(t["lang"])
        self.settings_drawer.lbl_theme.setText(t["theme"])
        self.settings_drawer.lbl_anim.setText(t["anim"])
        self.settings_drawer.lbl_folder_header.setText(t["folder_header"])
        self.settings_drawer.btn_folder.setText(t["select_folder"])
        self.track_list.lbl_header.setText(t["track_list_title"])

        saved_folder = self.settings_store.value("music_folder", "")
        self.settings_drawer.set_current_folder_text(saved_folder, t["no_folder"])

        if not self.player.playlist:
            self.player_bar.lbl_title.setText(t["no_track"])
            self.player_bar.lbl_artist.setText(t["no_folder_hint"])

        if self.playlists:
            categories = list(self.playlists.keys())
            self.tab_bar.set_categories(categories, default_title=t["default_tab"])
        else:
            self.tab_bar.set_categories([t["default_tab"]], default_title=t["default_tab"])

    def apply_theme(self, theme_name: str):
        self.settings_store.setValue("theme", theme_name)
        self.bg_frame.set_theme(theme_name)
        theme_cfg = THEME_COLORS.get(theme_name, THEME_COLORS["Тёмный графит"])
        self.visualizer.set_accent_color(theme_cfg["accent"])

    def apply_anim_style(self, anim_name: str):
        self.settings_store.setValue("anim_style", anim_name)
        self.visualizer.set_mode(anim_name)

    def select_music_folder(self):
        t = TRANSLATIONS[self.current_lang]
        folder = QFileDialog.getExistingDirectory(self, t["dialog_title"])
        if folder:
            self.settings_store.setValue("music_folder", folder)
            self.settings_drawer.set_current_folder_text(folder, t["no_folder"])
            self._scan_and_load_structure(folder)

    def _scan_and_load_structure(self, base_folder: str):
        valid_exts = ('.mp3', '.flac', '.wav', '.ogg', '.m4a', '.aac', '.wma', '.opus')
        t = TRANSLATIONS[self.current_lang]
        default_name = t["default_tab"]

        self.playlists = {default_name: []}
        base_folder = os.path.abspath(os.path.normpath(base_folder))

        try:
            for root, _, files in os.walk(base_folder):
                for f in files:
                    if f.lower().endswith(valid_exts):
                        full_path = os.path.join(root, f)
                        self.playlists[default_name].append(full_path)

                        rel_dir = os.path.relpath(root, base_folder)
                        if rel_dir != ".":
                            sub_name = os.path.basename(root)
                            if sub_name not in self.playlists:
                                self.playlists[sub_name] = []
                            self.playlists[sub_name].append(full_path)

        except Exception as e:
            print(f"Ошибка сканирования: {e}")

        categories = list(self.playlists.keys())
        self.tab_bar.set_categories(categories, default_title=default_name)
        self._on_category_changed(default_name)

    def _on_category_changed(self, category_name: str):
        self.current_category = category_name
        tracks = self.playlists.get(category_name, [])
        self.track_list.set_tracks(tracks)

        if tracks:
            self.player.set_playlist(tracks)
            first_info = self.player.parse_track_info(tracks[0])
            self._on_track_changed(first_info)

    def _on_track_list_item_clicked(self, index: int):
        self.player.play_index(index)

    def _on_track_changed(self, track: dict):
        t = TRANSLATIONS[self.current_lang]
        self.player_bar.lbl_title.setText(track.get("title", t["no_track"]))
        self.player_bar.lbl_artist.setText(track.get("artist", "—"))
        if self.player.current_index >= 0:
            self.track_list.set_active_index(self.player.current_index)

    def _on_position_changed(self, position_ms: int):
        if not self.player_bar.timeline_slider.isSliderDown():
            self.player_bar.timeline_slider.setValue(position_ms)
        self.player_bar.lbl_current_time.setText(format_time(position_ms))

    def _on_duration_changed(self, duration_ms: int):
        self.player_bar.timeline_slider.setRange(0, duration_ms)
        self.player_bar.lbl_total_time.setText(format_time(duration_ms))

    def _on_state_changed(self, is_playing: bool):
        self.visualizer.is_playing = is_playing
        icon_name = "pause" if is_playing else "play"
        self.player_bar.btn_play.setIcon(draw_vector_icon(icon_name, color="#FFFFFF", size=18))

    def _on_anim_finished(self):
        if self.anim.direction() == QPropertyAnimation.Backward:
            self.settings_drawer.hide()

    def toggle_settings(self):
        h = self.bg_frame.height() - 60
        start_x = self.width() - 10
        end_x = self.width() - self.drawer_width - 15

        if self.settings_drawer.isVisible():
            self.anim.setDirection(QPropertyAnimation.Backward)
            self.anim.setStartValue(QRect(start_x, 50, self.drawer_width, h))
            self.anim.setEndValue(QRect(end_x, 50, self.drawer_width, h))
            self.anim.start()
        else:
            self.settings_drawer.setGeometry(start_x, 50, self.drawer_width, h)
            self.settings_drawer.show()
            self.settings_drawer.raise_()
            self.anim.setDirection(QPropertyAnimation.Forward)
            self.anim.setStartValue(QRect(start_x, 50, self.drawer_width, h))
            self.anim.setEndValue(QRect(end_x, 50, self.drawer_width, h))
            self.anim.start()