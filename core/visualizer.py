import math
from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QRadialGradient
from PySide6.QtWidgets import QWidget


class AudioCoreVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(320, 320)
        self.is_playing = False
        self.mode = "Импульсный круг"
        self.angle = 0.0
        self.pulse_phase = 0.0
        self.accent_color = QColor("#6366F1")

        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self._update_animation)
        self.timer.start()

    def set_mode(self, mode_name: str):
        self.mode = mode_name
        self.update()

    def set_accent_color(self, hex_color: str):
        self.accent_color = QColor(hex_color)
        self.update()

    def _update_animation(self):
        if self.is_playing:
            self.angle = (self.angle + 2.0) % 360
            self.pulse_phase += 0.06
        else:
            self.pulse_phase += 0.02
        self.update()

    def paintEvent(self, event):
        painter = QPainter()
        if not painter.begin(self):
            return

        painter.setRenderHint(QPainter.Antialiasing)

        cx = self.width() / 2.0
        cy = self.height() / 2.0
        base_radius = 85.0

        glow_pulse = math.sin(self.pulse_phase * 2) * (15.0 if self.is_playing else 5.0)
        glow_radius = base_radius + 45.0 + glow_pulse
        
        glow_grad = QRadialGradient(cx, cy, glow_radius)
        c_glow = QColor(self.accent_color)
        c_glow.setAlpha(60 if self.is_playing else 25)
        glow_grad.setColorAt(0.2, c_glow)
        c_glow_zero = QColor(self.accent_color)
        c_glow_zero.setAlpha(0)
        glow_grad.setColorAt(1.0, c_glow_zero)

        painter.setPen(Qt.NoPen)
        painter.setBrush(glow_grad)
        painter.drawEllipse(QRectF(cx - glow_radius, cy - glow_radius, glow_radius * 2, glow_radius * 2))

        mode_lower = self.mode.lower()
        if "орбиты" in mode_lower or "orbits" in mode_lower:
            self._draw_orbits(painter, cx, cy, base_radius)
        elif "спектр" in mode_lower or "spectrum" in mode_lower:
            self._draw_waves(painter, cx, cy, base_radius)
        else:
            self._draw_pulse_dots(painter, cx, cy, base_radius)

        inner_grad = QRadialGradient(cx, cy, base_radius)
        inner_grad.setColorAt(0, QColor("#1A1A22"))
        inner_grad.setColorAt(1, QColor("#0D0D12"))

        painter.setPen(Qt.NoPen)
        painter.setBrush(inner_grad)
        painter.drawEllipse(QRectF(cx - base_radius, cy - base_radius, base_radius * 2, base_radius * 2))

        border_pen = QPen(self.accent_color, 2.5)
        painter.setPen(border_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(cx - base_radius, cy - base_radius, base_radius * 2, base_radius * 2))

        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Segoe UI", 15, QFont.Bold))
        painter.drawText(self.rect(), Qt.AlignCenter, "ATMOS\nmusic")

        painter.end()

    def _draw_pulse_dots(self, painter, cx, cy, r):
        num_dots = 40
        for i in range(num_dots):
            ang = math.radians(i * (360.0 / num_dots) + self.angle)
            
            if self.is_playing:
                wave = math.sin(self.pulse_phase * 3 + i * 0.4)
                amp = 12.0 + wave * 10.0
            else:
                wave = math.sin(self.pulse_phase + i * 0.2)
                amp = 4.0 + wave * 2.0

            dot_r = r + 14.0 + amp
            x = cx + dot_r * math.cos(ang)
            y = cy + dot_r * math.sin(ang)

            col = QColor(self.accent_color)
            col.setAlpha(min(255, max(40, int(120 + amp * 8))))

            dot_size = 4.5 + (amp * 0.25)
            painter.setPen(Qt.NoPen)
            painter.setBrush(col)
            painter.drawEllipse(QRectF(x - dot_size / 2.0, y - dot_size / 2.0, dot_size, dot_size))

    def _draw_orbits(self, painter, cx, cy, r):
        painter.setBrush(Qt.NoBrush)

        c1 = QColor(self.accent_color)
        c1.setAlpha(220 if self.is_playing else 100)
        pen1 = QPen(c1, 2, Qt.DashLine)
        painter.setPen(pen1)
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.angle * 1.5)
        painter.drawEllipse(QRectF(-r - 16, -r - 16, (r + 16) * 2, (r + 16) * 2))
        painter.restore()

        c2 = QColor("#FFFFFF")
        c2.setAlpha(160 if self.is_playing else 70)
        pen2 = QPen(c2, 1.5, Qt.DotLine)
        painter.setPen(pen2)
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(-self.angle * 2.0)
        painter.drawEllipse(QRectF(-r - 28, -r - 28, (r + 28) * 2, (r + 28) * 2))
        painter.restore()

    def _draw_waves(self, painter, cx, cy, r):
        num_bars = 48
        for i in range(num_bars):
            ang = math.radians(i * (360.0 / num_bars) + self.angle * 0.5)
            
            if self.is_playing:
                length = 6.0 + (math.sin(self.pulse_phase * 4 + i * 0.3) + 1.0) * 10.0
            else:
                length = 2.0 + (math.sin(self.pulse_phase + i * 0.2) + 1.0) * 2.0

            x1 = cx + (r + 6.0) * math.cos(ang)
            y1 = cy + (r + 6.0) * math.sin(ang)
            x2 = cx + (r + 6.0 + length) * math.cos(ang)
            y2 = cy + (r + 6.0 + length) * math.sin(ang)

            col = QColor(self.accent_color)
            col.setAlpha(min(255, int(100 + length * 10)))
            pen = QPen(col, 2.5, Qt.SolidLine, Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(x1, y1, x2, y2)