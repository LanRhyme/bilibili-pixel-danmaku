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

    def set_avatar_size(self, size):
        if size == self.avatar_size:
            return
        self.avatar_size = size
        self.setFixedSize(size, size)
        self.update_avatar()

    def on_avatar_loaded(self, loaded_url, pixmap):
        if loaded_url == self.url:
            self.update_avatar()

    def update_avatar(self):
        pixmap = _AVATAR_PIXMAP_CACHE.get(self.url)
        target = QPixmap(self.avatar_size, self.avatar_size)
        target.fill(Qt.GlobalColor.transparent)

        painter = QPainter(target)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                self.avatar_size - 4, self.avatar_size - 4,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            painter.drawPixmap(2, 2, scaled)
        else:
            # Morandi Initial Avatar Box
            bg_col = QColor(self.colors.get("primary", "#afac9c"))
            painter.fillRect(2, 2, self.avatar_size - 4, self.avatar_size - 4, bg_col)
            painter.setPen(QColor(self.colors.get("bg_dark", "#1a1a18")))
            font = QFont("Noto Sans CJK SC", 10, QFont.Weight.Bold)
            painter.setFont(font)
            initial = (self.username[:1] if self.username else "U").upper()
            painter.drawText(0, 0, self.avatar_size, self.avatar_size, Qt.AlignmentFlag.AlignCenter, initial)

        # 2px pixel border
        pen = painter.pen()
        pen.setWidth(2)
        pen.setColor(QColor(self.colors.get("border", "#64635f")))
        painter.setPen(pen)
        painter.drawRect(1, 1, self.avatar_size - 3, self.avatar_size - 3)
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
    """像素徽章: 支持两种模式
    - 块状模式 (accent_color=None): 实色底 + 方括号文本, 终端状态灯风
    - HUD 色条模式 (accent_color=色): 暗底 + 左侧 3px 色条 + accent 色文字
    """
    def __init__(self, text="", bg_color=None, text_color=None, accent_color=None, parent=None):
        super().__init__(text, parent)
        colors = load_morandi_colors()
        self.accent_color = accent_color
        if accent_color is not None:
            self.bg_color = bg_color if bg_color else colors.get("bg_card", "#383732")
            self.text_color = text_color if text_color else accent_color
        else:
            self.bg_color = bg_color if bg_color else colors.get("primary", "#b8b39f")
            self.text_color = text_color if text_color else colors.get("bg_dark", "#1c1b18")
        self.update_style()

    def set_badge(self, text, bg_color=None, text_color=None, accent_color=None):
        self.setText(text)
        if bg_color is not None: self.bg_color = bg_color
        if text_color is not None: self.text_color = text_color
        if accent_color is not None: self.accent_color = accent_color
        self.update_style()

    def update_style(self):
        colors = load_morandi_colors()
        if self.accent_color is not None:
            self.setStyleSheet(f"""
                QLabel {{
                    background-color: {self.bg_color};
                    color: {self.text_color};
                    font-size: 10px;
                    font-weight: bold;
                    padding: 2px 8px;
                    border: 1px solid {colors.get('border', '#64635f')};
                    border-left: 3px solid {self.accent_color};
                    border-radius: 0px;
                }}
            """)
        else:
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
    def __init__(self, data, parent=None, font_size=12, avatar_size=32):
        super().__init__(parent)
        self.setObjectName("danmaku_item_card")
        self.data = data
        self.colors = load_morandi_colors()
        self.font_size = font_size
        self.avatar_size = avatar_size
        self.msg_type = self.data.get("type", "danmaku")

        msg_type = self.msg_type
        if msg_type == "superchat":
            accent = self.colors.get('accent_rose', '#c47079')
            self.setStyleSheet(f"""
                QFrame#danmaku_item_card {{
                    background-color: {self.colors.get('bg_active', '#403f39')};
                    border: 1px solid {self.colors.get('border', '#64635f')};
                    border-left: 3px solid {accent};
                }}
                QFrame#danmaku_item_card:hover {{
                    border-color: {accent};
                    border-left: 3px solid {accent};
                }}
            """)
        elif msg_type == "gift":
            accent = self.colors.get('accent_gold', '#bdb79a')
            self.setStyleSheet(f"""
                QFrame#danmaku_item_card {{
                    background-color: {self.colors.get('bg_card', '#383732')};
                    border: 1px solid {self.colors.get('border', '#64635f')};
                    border-left: 3px solid {accent};
                }}
                QFrame#danmaku_item_card:hover {{
                    background-color: {self.colors.get('bg_active', '#403f39')};
                    border-color: {accent};
                    border-left: 3px solid {accent};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#danmaku_item_card {{
                    background-color: {self.colors.get('bg_card', '#383732')};
                    border: 1px solid {self.colors.get('border', '#64635f')};
                }}
                QFrame#danmaku_item_card:hover {{
                    background-color: {self.colors.get('bg_active', '#403f39')};
                    border: 1px solid {self.colors.get('primary', '#afac9c')};
                }}
            """)

        self.init_ui()

    def set_scale(self, font_size=None, avatar_size=None):
        """动态调整字号与头像尺寸, 用于设置页保存后即时生效"""
        if font_size is not None and font_size != self.font_size:
            self.font_size = font_size
            self.user_label.setStyleSheet(
                f"color: {self.colors.get('primary', '#afac9c')}; font-weight: bold; font-size: {font_size + 1}px;"
            )
            self._apply_content_style(self.msg_type)
        if avatar_size is not None and avatar_size != self.avatar_size:
            self.avatar_size = avatar_size
            self.avatar_widget.set_avatar_size(avatar_size)

    def _apply_content_style(self, msg_type):
        fs = self.font_size
        if msg_type in ("danmaku", "chat"):
            self.content_label.setStyleSheet(f"color: {self.colors.get('text', '#f2f2f2')}; font-size: {fs}px;")
        elif msg_type == "gift":
            self.content_label.setStyleSheet(f"color: {self.colors.get('accent_gold', '#bdb79a')}; font-size: {fs}px; font-weight: bold;")
        elif msg_type == "superchat":
            self.content_label.setStyleSheet(f"color: {self.colors.get('text', '#f2f2f2')}; font-size: {fs}px; font-weight: bold;")
        elif msg_type in ("interact", "enter"):
            self.content_label.setStyleSheet(f"color: {self.colors.get('text_dim', '#dededd')}; font-size: {max(fs - 1, 9)}px;")

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(8)

        # Avatar
        avatar_url = self.data.get("avatar", "")
        username = self.data.get("user", "匿名用户")
        self.avatar_widget = AvatarWidget(url=avatar_url, username=username, size=self.avatar_size)
        main_layout.addWidget(self.avatar_widget, 0, Qt.AlignmentFlag.AlignTop)

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

        self.user_label = QLabel(username)
        self.user_label.setStyleSheet(f"color: {self.colors.get('primary', '#afac9c')}; font-weight: bold; font-size: {self.font_size + 1}px;")
        header_layout.addWidget(self.user_label)
        header_layout.addStretch()
        right_layout.addLayout(header_layout)

        # Content Row
        self.content_label = QLabel()
        self.content_label.setWordWrap(True)

        if msg_type in ("danmaku", "chat"):
            self.content_label.setText(self.data.get("text", ""))
        elif msg_type == "gift":
            gift_name = self.data.get("gift_name", "礼物")
            num = self.data.get("num", 1)
            price = self.data.get("price", 0)
            self.content_label.setText(f"赠送 {gift_name} x {num} (电池 {price*10:.0f})")
        elif msg_type == "superchat":
            self.content_label.setText(self.data.get("text", ""))
        elif msg_type in ("interact", "enter"):
            self.content_label.setText("进入直播间")

        self._apply_content_style(msg_type)
        right_layout.addWidget(self.content_label)
        main_layout.addLayout(right_layout, 1)
