import hashlib
import urllib.request
import threading
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout
)
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
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
    def __init__(self, url="", username="用户", size=32, parent=None):
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
        painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                self.avatar_size - 2, self.avatar_size - 2,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            painter.drawPixmap(1, 1, scaled)
        else:
            # Morandi Initial Avatar Box
            bg_col = QColor(self.colors.get("primary", "#b8b39f"))
            painter.fillRect(1, 1, self.avatar_size - 2, self.avatar_size - 2, bg_col)
            painter.setPen(QColor(self.colors.get("bg_dark", "#1c1b18")))
            font = QFont("Noto Sans CJK SC", 10, QFont.Bold)
            painter.setFont(font)
            initial = (self.username[:1] if self.username else "U").upper()
            painter.drawText(0, 0, self.avatar_size, self.avatar_size, Qt.AlignCenter, initial)

        # 1px border
        painter.setPen(QColor(self.colors.get("border", "#3d3c34")))
        painter.drawRect(0, 0, self.avatar_size - 1, self.avatar_size - 1)
        painter.end()

        self.setPixmap(target)

class PixelCard(QFrame):
    def __init__(self, bg_color=None, border_color=None, parent=None):
        super().__init__(parent)
        self.setObjectName("card_frame")
        colors = load_morandi_colors()
        if bg_color is None: bg_color = colors.get("bg_panel", "#23221e")
        if border_color is None: border_color = colors.get("border", "#3d3c34")

        self.setStyleSheet(f"""
            QFrame#card_frame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 0px;
            }}
        """)

class PixelBadge(QLabel):
    def __init__(self, text="", bg_color=None, text_color=None, parent=None):
        super().__init__(text, parent)
        colors = load_morandi_colors()
        self.bg_color = bg_color if bg_color else colors.get("primary", "#b8b39f")
        self.text_color = text_color if text_color else colors.get("bg_dark", "#1c1b18")
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
                font-size: 10px;
                font-weight: bold;
                padding: 2px 6px;
                border: 1px solid {colors.get('border_dark', '#121210')};
                border-radius: 0px;
            }}
        """)

class DanmakuCardWidget(QFrame):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setObjectName("danmaku_item_card")
        self.data = data
        self.colors = load_morandi_colors()

        msg_type = self.data.get("type", "danmaku")
        if msg_type == "superchat":
            self.setStyleSheet(f"""
                QFrame#danmaku_item_card {{
                    background-color: {self.colors.get('bg_active', '#35342e')};
                    border: 1px solid {self.colors.get('accent_rose', '#ba6670')};
                }}
            """)
        elif msg_type == "gift":
            self.setStyleSheet(f"""
                QFrame#danmaku_item_card {{
                    background-color: {self.colors.get('bg_card', '#2a2924')};
                    border: 1px solid {self.colors.get('accent_gold', '#c4ba97')};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#danmaku_item_card {{
                    background-color: {self.colors.get('bg_card', '#2a2924')};
                    border: 1px solid {self.colors.get('border', '#3d3c34')};
                }}
            """)

        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(8)

        # Avatar
        avatar_url = self.data.get("avatar", "")
        username = self.data.get("user", "匿名用户")
        avatar_widget = AvatarWidget(url=avatar_url, username=username, size=32)
        main_layout.addWidget(avatar_widget, 0, Qt.AlignTop)

        # Right Column
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(2)

        # Header Row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(5)

        msg_type = self.data.get("type", "danmaku")

        guard_level = self.data.get("guard_level", 0)
        if guard_level > 0:
            guard_text = "总督" if guard_level == 1 else "提督" if guard_level == 2 else "舰长"
            guard_badge = PixelBadge(f"[ {guard_text} ]", bg_color=self.colors.get('accent_gold', '#c4ba97'), text_color=self.colors.get('bg_dark', '#1c1b18'))
            header_layout.addWidget(guard_badge)

        medal_name = self.data.get("medal_name", "")
        medal_level = self.data.get("medal_level", 0)
        if medal_name:
            medal_badge = PixelBadge(f"[ {medal_name} {medal_level} ]", bg_color=self.colors.get('accent_purple', '#a292ad'), text_color=self.colors.get('bg_dark', '#1c1b18'))
            header_layout.addWidget(medal_badge)

        if msg_type == "gift":
            tag_badge = PixelBadge("[ 礼物 ]", bg_color=self.colors.get('accent_gold', '#c4ba97'), text_color=self.colors.get('bg_dark', '#1c1b18'))
            header_layout.addWidget(tag_badge)
        elif msg_type == "superchat":
            price = self.data.get("price", 0)
            tag_badge = PixelBadge(f"[ SC ¥{price} ]", bg_color=self.colors.get('accent_rose', '#c47079'), text_color=self.colors.get('text', '#dedcd2'))
            header_layout.addWidget(tag_badge)

        user_label = QLabel(username)
        user_label.setStyleSheet(f"color: {self.colors.get('primary', '#b8b39f')}; font-weight: bold; font-size: 11px;")
        header_layout.addWidget(user_label)
        header_layout.addStretch()
        right_layout.addLayout(header_layout)

        # Content Row
        content_label = QLabel()
        content_label.setWordWrap(True)

        if msg_type in ("danmaku", "chat"):
            content_label.setText(self.data.get("text", ""))
            content_label.setStyleSheet(f"color: {self.colors.get('text', '#dedcd2')}; font-size: 12px;")
        elif msg_type == "gift":
            gift_name = self.data.get("gift_name", "礼物")
            num = self.data.get("num", 1)
            price = self.data.get("price", 0)
            content_label.setText(f"赠送 {gift_name} x {num} (电池 {price*10:.0f})")
            content_label.setStyleSheet(f"color: {self.colors.get('accent_gold', '#c4ba97')}; font-size: 12px; font-weight: bold;")
        elif msg_type == "superchat":
            text = self.data.get("text", "")
            content_label.setText(text)
            content_label.setStyleSheet(f"color: {self.colors.get('text', '#dedcd2')}; font-size: 12px; font-weight: bold;")
        elif msg_type in ("interact", "enter"):
            content_label.setText("进入直播间")
            content_label.setStyleSheet(f"color: {self.colors.get('text_dim', '#949289')}; font-size: 11px;")

        right_layout.addWidget(content_label)
        main_layout.addLayout(right_layout, 1)
