import os
import hashlib
import urllib.request
import threading
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, Signal, QObject
from PySide6.QtGui import QPixmap, QPainter, QPainterPath, QColor, QFont
from core.theme import load_morandi_colors

AVATAR_CACHE_DIR = Path.home() / ".cache" / "bilibili-danmaku" / "avatars"
AVATAR_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_AVATAR_PIXMAP_CACHE = {}

class AvatarLoader(QObject):
    loaded_signal = Signal(str, QPixmap)

    def load_avatar(self, url, username):
        if not url:
            return
        if url in _AVATAR_PIXMAP_CACHE:
            return

        def _fetch():
            try:
                url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
                cached_file = AVATAR_CACHE_DIR / f"{url_hash}.jpg"

                if not cached_file.exists():
                    req = urllib.request.Request(
                        url,
                        headers={
                            "User-Agent": "Mozilla/5.0",
                            "Referer": "https://live.bilibili.com/"
                        }
                    )
                    with urllib.request.urlopen(req, timeout=4) as resp:
                        data = resp.read()
                        with open(cached_file, "wb") as f:
                            f.write(data)

                if cached_file.exists():
                    pix = QPixmap(str(cached_file))
                    if not pix.isNull():
                        _AVATAR_PIXMAP_CACHE[url] = pix
                        self.loaded_signal.emit(url, pix)
            except Exception:
                pass

        threading.Thread(target=_fetch, daemon=True).start()

_GLOBAL_AVATAR_LOADER = AvatarLoader()

class AvatarWidget(QLabel):
    def __init__(self, url="", username="用户", size=36, parent=None):
        super().__init__(parent)
        self.url = url
        self.username = username
        self.avatar_size = size
        self.setFixedSize(size, size)
        self.colors = load_morandi_colors()

        _GLOBAL_AVATAR_LOADER.loaded_signal.connect(self.on_avatar_loaded)
        self.update_avatar()
        if self.url and self.url not in _AVATAR_PIXMAP_CACHE:
            _GLOBAL_AVATAR_LOADER.load_avatar(self.url, self.username)

    def on_avatar_loaded(self, loaded_url, pixmap):
        if loaded_url == self.url:
            self.update_avatar()

    def update_avatar(self):
        pixmap = _AVATAR_PIXMAP_CACHE.get(self.url)
        target = QPixmap(self.avatar_size, self.avatar_size)
        target.fill(Qt.transparent)

        painter = QPainter(target)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        path = QPainterPath()
        path.addRoundedRect(0, 0, self.avatar_size, self.avatar_size, 6, 6)
        painter.setClipPath(path)

        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                self.avatar_size, self.avatar_size,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled)
        else:
            # Morandi Initial Avatar placeholder
            bg_col = QColor(self.colors.get("primary", "#afac9c"))
            painter.fillRect(0, 0, self.avatar_size, self.avatar_size, bg_col)
            painter.setPen(QColor(self.colors.get("bg_dark", "#1a1a18")))
            font = QFont("Noto Sans CJK SC", 12, QFont.Bold)
            painter.setFont(font)
            initial = (self.username[:1] if self.username else "B").upper()
            painter.drawText(0, 0, self.avatar_size, self.avatar_size, Qt.AlignCenter, initial)

        # Border
        painter.setClipping(False)
        painter.setPen(QColor(self.colors.get("border", "#64635f")))
        painter.drawRoundedRect(0, 0, self.avatar_size - 1, self.avatar_size - 1, 6, 6)
        painter.end()

        self.setPixmap(target)

class PixelCard(QFrame):
    def __init__(self, bg_color=None, border_color=None, parent=None):
        super().__init__(parent)
        self.setObjectName("card_frame")
        colors = load_morandi_colors()
        if bg_color is None: bg_color = colors.get("bg_panel", "#302f2c")
        if border_color is None: border_color = colors.get("border_dark", "#16161e")

        self.setStyleSheet(f"""
            QFrame#card_frame {{
                background-color: {bg_color};
                border-top: 2px solid {colors.get('border', '#64635f')};
                border-left: 2px solid {colors.get('border', '#64635f')};
                border-bottom: 2px solid {border_color};
                border-right: 2px solid {border_color};
                border-radius: 6px;
            }}
        """)

class PixelBadge(QLabel):
    def __init__(self, text="", bg_color=None, text_color=None, parent=None):
        super().__init__(text, parent)
        colors = load_morandi_colors()
        self.bg_color = bg_color if bg_color else colors.get("primary", "#afac9c")
        self.text_color = text_color if text_color else colors.get("bg_dark", "#1a1a18")
        self.update_style()

    def set_badge(self, text, bg_color=None, text_color=None):
        self.setText(text)
        if bg_color: self.bg_color = bg_color
        if text_color: self.text_color = text_color
        self.update_style()

    def update_style(self):
        colors = load_morandi_colors()
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {self.bg_color};
                color: {self.text_color};
                font-size: 11px;
                font-weight: bold;
                padding: 2px 8px;
                border-radius: 4px;
                border-top: 1px solid rgba(255, 255, 255, 0.2);
                border-bottom: 2px solid {colors.get('border_dark', '#16161e')};
            }}
        """)

class DanmakuCardWidget(PixelCard):
    def __init__(self, data, parent=None):
        colors = load_morandi_colors()
        msg_type = data.get("type", "danmaku")
        card_bg = colors.get("bg_panel", "#302f2c")

        if msg_type == "superchat":
            card_bg = colors.get("bg_active", "#403f39")
        elif msg_type == "gift":
            card_bg = colors.get("bg_card", "#383732")

        super().__init__(bg_color=card_bg, parent=parent)
        self.data = data
        self.init_ui()

    def init_ui(self):
        colors = load_morandi_colors()
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(10)

        # 1. Avatar (Left)
        avatar_url = self.data.get("avatar", "")
        username = self.data.get("user", "匿名用户")
        avatar_widget = AvatarWidget(url=avatar_url, username=username, size=38)
        main_layout.addWidget(avatar_widget, 0, Qt.AlignTop)

        # 2. Content (Right)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        # Header Row: Badges + Username
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        guard_level = self.data.get("guard_level", 0)
        if guard_level > 0:
            guard_text = "总督" if guard_level == 1 else "提督" if guard_level == 2 else "舰长"
            guard_color = colors.get('accent_rose', '#b24355') if guard_level == 1 else colors.get('accent_gold', '#bdb79a') if guard_level == 2 else colors.get('primary', '#afac9c')
            guard_badge = PixelBadge(guard_text, bg_color=guard_color, text_color=colors.get('bg_dark', '#1a1a18'))
            header_layout.addWidget(guard_badge)

        medal_name = self.data.get("medal_name", "")
        medal_level = self.data.get("medal_level", 0)
        if medal_name:
            medal_badge = PixelBadge(f"{medal_name} {medal_level}", bg_color=colors.get('accent_purple', '#a899b9'), text_color=colors.get('bg_dark', '#1a1a18'))
            header_layout.addWidget(medal_badge)

        user_label = QLabel(username)
        user_label.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {colors.get('primary', '#afac9c')};")
        header_layout.addWidget(user_label)
        header_layout.addStretch()
        right_layout.addLayout(header_layout)

        # Body Row: Message
        msg_type = self.data.get("type", "danmaku")
        content_label = QLabel()
        content_label.setWordWrap(True)

        if msg_type in ("danmaku", "chat"):
            content_label.setText(self.data.get("text", ""))
            content_label.setStyleSheet(f"font-size: 13px; color: {colors.get('text', '#f2f2f2')}; line-height: 1.4;")
        elif msg_type == "gift":
            gift_name = self.data.get("gift_name", "礼物")
            num = self.data.get("num", 1)
            price = self.data.get("price", 0)
            content_label.setText(f"🎁 赠送了 {gift_name} x {num} (电池 {price*10:.0f})")
            content_label.setStyleSheet(f"font-size: 13px; color: {colors.get('accent_gold', '#bdb79a')}; font-weight: bold;")
        elif msg_type == "superchat":
            price = self.data.get("price", 0)
            text = self.data.get("text", "")
            content_label.setText(f"💰 醒目留言 [¥{price}]：\n{text}")
            content_label.setStyleSheet(f"font-size: 13px; color: {colors.get('accent_rose', '#b24355')}; font-weight: bold; background: rgba(178, 67, 85, 0.15); padding: 4px; border-radius: 4px;")
        elif msg_type in ("interact", "enter"):
            content_label.setText("✨ 进入了直播间")
            content_label.setStyleSheet(f"font-size: 12px; color: {colors.get('text_dim', '#dededd')}; font-style: italic;")

        right_layout.addWidget(content_label)
        main_layout.addLayout(right_layout, 1)
