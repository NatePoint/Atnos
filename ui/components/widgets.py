import os
from PySide6.QtCore import Qt, QPoint, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QIcon, QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QFrame, QComboBox, QListWidget, QListWidgetItem
)

ACCENT_COLOR = "#6366F1"
ACCENT_HOVER = "#4F46E5"
COLOR_BG_CARD = "#16161A"
COLOR_TEXT_MUTED = "#72727E"
COLOR_BORDER = "rgba(255, 255, 255, 0.07)"

QSS_SLIDER = f"""
QSlider::groove:horizontal {{
    height: 4px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    background: {ACCENT_COLOR};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: #FFFFFF;
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}}
"""


def draw_vector_icon(icon_type, color="#8E8E93", size=24):
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter()
    if painter.begin(pixmap):
        painter.setRenderHint(QPainter.Antialiasing)

        c = QColor(color)
        pen = QPen(c, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(QBrush(c))

        w, h = float(size), float(size)

        if icon_type == "play":
            path = QPainterPath()
            path.moveTo(w * 0.38, h * 0.28)
            path.lineTo(w * 0.72, h * 0.5)
            path.lineTo(w * 0.38, h * 0.72)
            path.closeSubpath()
            painter.drawPath(path)
        elif icon_type == "pause":
            painter.drawRoundedRect(QRectF(w * 0.32, h * 0.28, w * 0.12, h * 0.44), 1, 1)
            painter.drawRoundedRect(QRectF(w * 0.56, h * 0.28, w * 0.12, h * 0.44), 1, 1)
        elif icon_type == "next":
            path = QPainterPath()
            path.moveTo(w * 0.24, h * 0.28)
            path.lineTo(w * 0.56, h * 0.5)
            path.lineTo(w * 0.24, h * 0.72)
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawRoundedRect(QRectF(w * 0.64, h * 0.28, w * 0.08, h * 0.44), 1, 1)
        elif icon_type == "prev":
            painter.drawRoundedRect(QRectF(w * 0.28, h * 0.28, w * 0.08, h * 0.44), 1, 1)
            path = QPainterPath()
            path.moveTo(w * 0.76, h * 0.28)
            path.lineTo(w * 0.44, h * 0.5)
            path.lineTo(w * 0.76, h * 0.72)
            path.closeSubpath()
            painter.drawPath(path)
        elif icon_type == "volume":
            path = QPainterPath()
            path.moveTo(w * 0.2, h * 0.4)
            path.lineTo(w * 0.35, h * 0.4)
            path.lineTo(w * 0.55, h * 0.25)
            path.lineTo(w * 0.55, h * 0.75)
            path.lineTo(w * 0.35, h * 0.6)
            path.lineTo(w * 0.2, h * 0.6)
            path.closeSubpath()
            painter.drawPath(path)
            painter.setBrush(Qt.NoBrush)
            painter.drawArc(QRectF(w * 0.5, h * 0.3, w * 0.3, h * 0.4), -60 * 16, 120 * 16)

        painter.end()

    return QIcon(pixmap)


class GlassPanel(QFrame):
    def __init__(self, radius=14, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassPanel")
        self.setStyleSheet(f"""
            #GlassPanel {{
                background-color: {COLOR_BG_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: {radius}px;
            }}
        """)


class RedLineTitleBar(QWidget):
    settings_toggled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self._drag_pos = QPoint()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 15, 0)

        self.logo = QLabel("ATMOS")
        self.logo.setStyleSheet("font-size: 13px; font-weight: 800; letter-spacing: 2px; color: #FFFFFF;")
        
        layout.addWidget(self.logo)
        layout.addStretch()

        self.btn_settings = QPushButton("Настройки")
        self.btn_settings.setCursor(Qt.PointingHandCursor)
        self.btn_settings.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.05);
                color: #E1E1E6;
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                padding: 5px 14px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.1);
                border-color: {ACCENT_COLOR};
            }}
        """)
        self.btn_settings.clicked.connect(self.settings_toggled.emit)
        layout.addWidget(self.btn_settings)

        btn_min = QPushButton("—")
        btn_close = QPushButton("✕")
        for btn in (btn_min, btn_close):
            btn.setFixedSize(30, 30)
            btn.setCursor(Qt.PointingHandCursor)

        btn_min.setStyleSheet(f"QPushButton {{ background: transparent; color: {COLOR_TEXT_MUTED}; border: none; font-size: 13px; }} QPushButton:hover {{ color: #FFF; }}")
        btn_close.setStyleSheet(f"QPushButton {{ background: transparent; color: {COLOR_TEXT_MUTED}; border: none; font-size: 13px; }} QPushButton:hover {{ color: #FF453A; }}")

        btn_min.clicked.connect(self.window().showMinimized)
        btn_close.clicked.connect(self.window().close)

        layout.addWidget(btn_min)
        layout.addWidget(btn_close)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)


class CategoryTabBar(QWidget):
    tab_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)
        self.buttons = []

    def set_categories(self, categories: list, default_title="Все треки"):
        for btn in self.buttons:
            self.layout.removeWidget(btn)
            btn.deleteLater()
        self.buttons.clear()

        if not categories:
            categories = [default_title]

        for index, name in enumerate(categories):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda checked, idx=index, cat_name=name: self._on_click(idx, cat_name))
            self.layout.addWidget(btn)
            self.buttons.append(btn)

        self.set_active_tab(0)

    def _on_click(self, idx, cat_name):
        self.set_active_tab(idx)
        self.tab_changed.emit(cat_name)

    def set_active_tab(self, active_index):
        for idx, btn in enumerate(self.buttons):
            btn.setChecked(idx == active_index)
            if idx == active_index:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {ACCENT_COLOR};
                        color: #FFFFFF;
                        border: none;
                        border-radius: 16px;
                        font-weight: 600;
                        font-size: 11px;
                        padding: 0 18px;
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: rgba(255, 255, 255, 0.04);
                        color: {COLOR_TEXT_MUTED};
                        border: 1px solid {COLOR_BORDER};
                        border-radius: 16px;
                        font-weight: 500;
                        font-size: 11px;
                        padding: 0 18px;
                    }}
                    QPushButton:hover {{
                        background: rgba(255, 255, 255, 0.08);
                        color: #FFFFFF;
                    }}
                """)


class SettingsDrawer(GlassPanel):
    folder_selected = Signal()
    theme_changed = Signal(str)
    lang_changed = Signal(str)
    anim_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(radius=18, parent=parent)
        self.setObjectName("SettingsDrawer")
        self.setStyleSheet(f"""
            #SettingsDrawer {{
                background-color: #121215;
                border: 1px solid {COLOR_BORDER};
                border-radius: 18px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.lbl_title = QLabel("Настройки")
        self.lbl_title.setStyleSheet("color: #FFFFFF; font-size: 15px; font-weight: 700;")
        layout.addWidget(self.lbl_title)

        self.lbl_lang = QLabel("Язык / Language", styleSheet=f"color: {COLOR_TEXT_MUTED}; font-size: 11px; margin-top: 4px;")
        layout.addWidget(self.lbl_lang)
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Русский", "English"])
        self.lang_combo.setStyleSheet(self._combo_qss())
        self.lang_combo.currentTextChanged.connect(self.lang_changed.emit)
        layout.addWidget(self.lang_combo)

        self.lbl_theme = QLabel("Тема оформления", styleSheet=f"color: {COLOR_TEXT_MUTED}; font-size: 11px; margin-top: 4px;")
        layout.addWidget(self.lbl_theme)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Тёмный графит", "OLED Чёрный", "Киберпанк Неон", "Фиолетовый закат", "Изумрудный ночной", "Tokyo Night"])
        self.theme_combo.setStyleSheet(self._combo_qss())
        self.theme_combo.currentTextChanged.connect(self.theme_changed.emit)
        layout.addWidget(self.theme_combo)

        self.lbl_anim = QLabel("Стиль визуализатора", styleSheet=f"color: {COLOR_TEXT_MUTED}; font-size: 11px; margin-top: 4px;")
        layout.addWidget(self.lbl_anim)
        self.anim_combo = QComboBox()
        self.anim_combo.addItems(["Импульсный круг", "Вращающиеся орбиты", "Волновой спектр"])
        self.anim_combo.setStyleSheet(self._combo_qss())
        self.anim_combo.currentTextChanged.connect(self.anim_changed.emit)
        layout.addWidget(self.anim_combo)

        self.lbl_folder_header = QLabel("Основная папка с музыкой", styleSheet=f"color: {COLOR_TEXT_MUTED}; font-size: 11px; margin-top: 4px;")
        layout.addWidget(self.lbl_folder_header)
        
        self.lbl_folder_path = QLabel("Папка не выбрана")
        self.lbl_folder_path.setWordWrap(True)
        self.lbl_folder_path.setStyleSheet(f"color: #D1D1D6; font-size: 10px; background: rgba(0,0,0,0.3); padding: 8px; border-radius: 8px; border: 1px solid {COLOR_BORDER};")
        layout.addWidget(self.lbl_folder_path)

        self.btn_folder = QPushButton("Выбрать папку")
        self.btn_folder.setCursor(Qt.PointingHandCursor)
        self.btn_folder.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT_COLOR};
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 9px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {ACCENT_HOVER};
            }}
        """)
        self.btn_folder.clicked.connect(self.folder_selected.emit)
        layout.addWidget(self.btn_folder)

        layout.addStretch()

    def _combo_qss(self):
        return f"""
            QComboBox {{
                background: #1A1A1E;
                color: #FFF;
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 11px;
            }}
            QComboBox QAbstractItemView {{
                background: #1A1A1E;
                color: #FFF;
                selection-background-color: {ACCENT_COLOR};
            }}
        """

    def set_current_folder_text(self, path: str, no_folder_text="Папка не выбрана"):
        if path:
            folder_name = os.path.basename(os.path.normpath(path)) or path
            self.lbl_folder_path.setText(f"{folder_name}\n({path})")
        else:
            self.lbl_folder_path.setText(no_folder_text)


class TrackListWidget(GlassPanel):
    track_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(radius=18, parent=parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.lbl_header = QLabel("Список композиций")
        self.lbl_header.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 700;")
        layout.addWidget(self.lbl_header)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background: transparent;
                border: none;
                color: #E1E1E6;
                font-size: 11px;
            }}
            QListWidget::item {{
                padding: 8px 10px;
                border-radius: 8px;
                margin-bottom: 2px;
            }}
            QListWidget::item:hover {{
                background: rgba(255, 255, 255, 0.05);
            }}
            QListWidget::item:selected {{
                background: {ACCENT_COLOR};
                color: #FFFFFF;
                font-weight: 600;
            }}
        """)
        self.list_widget.itemClicked.connect(
            lambda item: self.track_selected.emit(self.list_widget.row(item))
        )
        layout.addWidget(self.list_widget)

    def set_tracks(self, track_paths: list):
        self.list_widget.clear()
        for path in track_paths:
            filename = os.path.basename(path)
            title, _ = os.path.splitext(filename)
            item = QListWidgetItem(title)
            item.setToolTip(path)
            self.list_widget.addItem(item)

    def set_active_index(self, index: int):
        if 0 <= index < self.list_widget.count():
            self.list_widget.setCurrentRow(index)


class ProPlayerBar(GlassPanel):
    def __init__(self, parent=None):
        super().__init__(radius=18, parent=parent)
        self.setFixedHeight(85)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 10, 20, 10)

        timeline_layout = QHBoxLayout()
        timeline_layout.setSpacing(10)

        self.lbl_current_time = QLabel("00:00")
        self.lbl_current_time.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; font-weight: 500;")

        self.timeline_slider = QSlider(Qt.Horizontal)
        self.timeline_slider.setStyleSheet(QSS_SLIDER)
        self.timeline_slider.setRange(0, 1000)

        self.lbl_total_time = QLabel("00:00")
        self.lbl_total_time.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px; font-weight: 500;")

        timeline_layout.addWidget(self.lbl_current_time)
        timeline_layout.addWidget(self.timeline_slider)
        timeline_layout.addWidget(self.lbl_total_time)

        main_layout.addLayout(timeline_layout)

        controls_layout = QHBoxLayout()

        track_info = QHBoxLayout()
        track_cover = GlassPanel(radius=8)
        track_cover.setFixedSize(36, 36)

        meta_layout = QVBoxLayout()
        meta_layout.setSpacing(2)
        self.lbl_title = QLabel("Трек не выбран")
        self.lbl_title.setStyleSheet("color: #FFFFFF; font-weight: 600; font-size: 11px;")
        self.lbl_artist = QLabel("Укажите папку в Настройках")
        self.lbl_artist.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")
        meta_layout.addWidget(self.lbl_title)
        meta_layout.addWidget(self.lbl_artist)

        track_info.addWidget(track_cover)
        track_info.addLayout(meta_layout)

        controls_layout.addLayout(track_info)
        controls_layout.addStretch()

        transport = QHBoxLayout()
        transport.setSpacing(14)

        self.btn_prev = QPushButton()
        self.btn_play = QPushButton()
        self.btn_next = QPushButton()

        self.btn_prev.setIcon(draw_vector_icon("prev", color="#FFFFFF", size=16))
        self.btn_next.setIcon(draw_vector_icon("next", color="#FFFFFF", size=16))

        for b in (self.btn_prev, self.btn_next):
            b.setFixedSize(34, 34)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("QPushButton { background: transparent; border: none; border-radius: 17px; } QPushButton:hover { background: rgba(255, 255, 255, 0.08); }")

        self.btn_play.setFixedSize(40, 40)
        self.btn_play.setCursor(Qt.PointingHandCursor)
        self.btn_play.setIcon(draw_vector_icon("play", color="#FFFFFF", size=18))
        self.btn_play.setStyleSheet(f"QPushButton {{ background: {ACCENT_COLOR}; border: none; border-radius: 20px; }} QPushButton:hover {{ background: {ACCENT_HOVER}; }}")

        transport.addWidget(self.btn_prev)
        transport.addWidget(self.btn_play)
        transport.addWidget(self.btn_next)

        controls_layout.addLayout(transport)
        controls_layout.addStretch()

        vol_layout = QHBoxLayout()
        vol_icon = QLabel()
        vol_icon.setPixmap(draw_vector_icon("volume", color=COLOR_TEXT_MUTED, size=16).pixmap(16, 16))

        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setStyleSheet(QSS_SLIDER)
        self.vol_slider.setFixedWidth(80)
        self.vol_slider.setValue(80)

        vol_layout.addWidget(vol_icon)
        vol_layout.addWidget(self.vol_slider)

        controls_layout.addLayout(vol_layout)
        main_layout.addLayout(controls_layout)