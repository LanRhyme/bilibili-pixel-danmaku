from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt
from core.theme import load_morandi_colors

class PixelCard(QFrame):
    def __init__(self, bg_color=None, border_color=None, parent=None):
        super().__init__(parent)
        self.setObjectName("card_frame")
        colors = load_morandi_colors()
        if bg_color is None: bg_color = colors.get("bg_panel", "#24283b")
        if border_color is None: border_color = colors.get("border_dark", "#16161e")

        self.setStyleSheet(f"""
            QFrame#card_frame {{
                background-color: {bg_color};
                border-top: 2px solid {colors.get('border', '#414868')};
                border-left: 2px solid {colors.get('border', '#414868')};
                border-bottom: 2px solid {border_color};
                border-right: 2px solid {border_color};
            }}
        """)

class PixelBadge(QLabel):
    def __init__(self, text="", bg_color=None, text_color=None, parent=None):
        super().__init__(text, parent)
        colors = load_morandi_colors()
        self.bg_color = bg_color if bg_color else colors.get("primary", "#7aa2f7")
        self.text_color = text_color if text_color else colors.get("bg_dark", "#1a1b26")
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
                padding: 2px 6px;
                border-top: 1px solid {colors.get('text', '#c0caf5')};
                border-left: 1px solid {colors.get('text', '#c0caf5')};
                border-bottom: 2px solid {colors.get('border_dark', '#16161e')};
                border-right: 2px solid {colors.get('border_dark', '#16161e')};
            }}
        """)

class DanmakuCardWidget(PixelCard):
    def __init__(self, data, parent=None):
        super().__init__(parent=parent)
        self.data = data
        self.init_ui()

    def init_ui(self):
        colors = load_morandi_colors()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        msg_type = self.data.get("type", "danmaku")

        guard_level = self.data.get("guard_level", 0)
        if guard_level > 0:
            guard_text = "总督" if guard_level == 1 else "提督" if guard_level == 2 else "舰长"
            guard_color = colors.get('accent_rose', '#ff757f') if guard_level == 1 else colors.get('accent_gold', '#ffc777') if guard_level == 2 else colors.get('accent_blue', '#7aa2f7')
            guard_badge = PixelBadge(guard_text, bg_color=guard_color, text_color=colors.get('bg_dark', '#101018'))
            layout.addWidget(guard_badge)

        medal_name = self.data.get("medal_name", "")
        medal_level = self.data.get("medal_level", 0)
        if medal_name:
            medal_badge = PixelBadge(f"{medal_name} {medal_level}", bg_color=colors.get('accent_purple', '#bb9af7'), text_color=colors.get('bg_dark', '#101018'))
            layout.addWidget(medal_badge)

        user_name = self.data.get("user", "匿名")
        user_label = QLabel(f"{user_name}:")
        user_label.setStyleSheet(f"font-weight: bold; color: {colors.get('accent_blue', '#7aa2f7')};")
        layout.addWidget(user_label)

        content_label = QLabel()
        content_label.setWordWrap(True)

        if msg_type in ("danmaku", "chat"):
            content_label.setText(self.data.get("text", ""))
            content_label.setStyleSheet(f"color: {colors.get('text', '#c0caf5')};")
        elif msg_type == "gift":
            gift_name = self.data.get("gift_name", "礼物")
            num = self.data.get("num", 1)
            price = self.data.get("price", 0)
            content_label.setText(f"送出 {gift_name} x {num} (电池 {price*10:.0f})")
            content_label.setStyleSheet(f"color: {colors.get('accent_gold', '#e0af68')}; font-weight: bold;")
        elif msg_type == "superchat":
            price = self.data.get("price", 0)
            text = self.data.get("text", "")
            content_label.setText(f"【醒目留言 ¥{price}】{text}")
            content_label.setStyleSheet(f"color: {colors.get('accent_rose', '#f7768e')}; font-weight: bold;")
        elif msg_type in ("interact", "enter"):
            content_label.setText("进入了直播间")
            content_label.setStyleSheet(f"color: {colors.get('text_dim', '#565f89')}; font-style: italic;")

        layout.addWidget(content_label, 1)
