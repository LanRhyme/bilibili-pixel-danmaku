import json
from pathlib import Path

MORANDI_APP_COLORS = Path.home() / ".config" / "bilibili-pixel-danmaku" / "morandi_colors.json"

DEFAULT_PALETTE = {
    "bg_dark": "#1a1b26",
    "bg_panel": "#24283b",
    "bg_card": "#2f3549",
    "bg_active": "#3b4261",
    "border": "#414868",
    "border_dark": "#16161e",
    "text": "#c0caf5",
    "text_dim": "#7aa2f7",
    "subtext": "#a9b1d6",
    "primary": "#7aa2f7",
    "primary_hover": "#89ddff",
    "accent_gold": "#e0af68",
    "accent_rose": "#f7768e",
    "accent_green": "#9ece6a",
    "accent_cyan": "#7dcfff",
    "accent_purple": "#bb9af7",
    "shadow": "#101018"
}

def load_morandi_colors():
    if MORANDI_APP_COLORS.exists():
        try:
            with open(MORANDI_APP_COLORS, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_PALETTE, **data}
        except Exception:
            pass
    return DEFAULT_PALETTE

def get_pixel_qss():
    colors = load_morandi_colors()
    return f"""
    QMainWindow, QWidget {{
        background-color: {colors['bg_dark']};
        color: {colors['text']};
        font-family: "Noto Sans CJK SC", "Source Han Sans CN", "Microsoft YaHei", sans-serif;
        font-size: 13px;
    }}

    /* 像素面板卡片 */
    QFrame#panel_frame, QFrame#card_frame {{
        background-color: {colors['bg_panel']};
        border-top: 2px solid {colors['border']};
        border-left: 2px solid {colors['border']};
        border-bottom: 2px solid {colors['border_dark']};
        border-right: 2px solid {colors['border_dark']};
    }}

    /* 像素按钮 */
    QPushButton {{
        background-color: {colors['bg_card']};
        color: {colors['text']};
        border-top: 2px solid {colors['border']};
        border-left: 2px solid {colors['border']};
        border-bottom: 2px solid {colors['border_dark']};
        border-right: 2px solid {colors['border_dark']};
        padding: 6px 14px;
        font-weight: bold;
    }}

    QPushButton:hover {{
        background-color: {colors['primary']};
        color: {colors['bg_dark']};
        border-top: 2px solid {colors['text']};
        border-left: 2px solid {colors['text']};
        border-bottom: 2px solid {colors['border_dark']};
        border-right: 2px solid {colors['border_dark']};
    }}

    QPushButton:pressed, QPushButton:checked {{
        background-color: {colors['bg_active']};
        color: {colors['accent_green']};
        border-top: 2px solid {colors['border_dark']};
        border-left: 2px solid {colors['border_dark']};
        border-bottom: 2px solid {colors['border']};
        border-right: 2px solid {colors['border']};
        padding-top: 8px;
        padding-left: 16px;
        padding-bottom: 4px;
        padding-right: 12px;
    }}

    /* 输入框 */
    QLineEdit, QSpinBox {{
        background-color: {colors['bg_dark']};
        color: {colors['text']};
        border: 2px solid {colors['border_dark']};
        padding: 6px;
        selection-background-color: {colors['primary']};
        selection-color: {colors['bg_dark']};
    }}

    QLineEdit:focus, QSpinBox:focus {{
        border: 2px solid {colors['primary']};
        background-color: {colors['bg_panel']};
    }}

    /* 滚动区域 */
    QScrollArea {{
        border: 2px solid {colors['border_dark']};
        background-color: {colors['bg_dark']};
    }}

    QScrollBar:vertical {{
        background-color: {colors['bg_dark']};
        width: 10px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {colors['border']};
        min-height: 20px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {colors['primary']};
    }}

    QStatusBar {{
        background-color: {colors['bg_panel']};
        color: {colors['subtext']};
        border-top: 2px solid {colors['border_dark']};
    }}
    """
