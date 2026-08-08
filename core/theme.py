import json
from pathlib import Path

MORANDI_APP_COLORS = Path.home() / ".config" / "bilibili-pixel-danmaku" / "morandi_colors.json"

DEFAULT_PALETTE = {
    "bg_dark": "#1a1a18",
    "bg_panel": "#242320",
    "bg_card": "#2e2d29",
    "bg_active": "#3a3833",
    "border": "#4e4c44",
    "border_dark": "#121210",
    "text": "#e8e6df",
    "text_dim": "#99978f",
    "subtext": "#b0ada3",
    "primary": "#b8b39f",
    "primary_hover": "#c9c4b1",
    "accent_gold": "#c2b88f",
    "accent_rose": "#ba6670",
    "accent_green": "#8a997d",
    "accent_cyan": "#879c9e",
    "accent_purple": "#9e8ea8",
    "accent_blue": "#8a9ba8",
    "shadow": "#0d0d0c"
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
        font-family: "Noto Sans CJK SC", "Source Han Sans CN", "Microsoft YaHei", monospace;
        font-size: 12px;
    }}

    /* 像素面板卡片 */
    QFrame#card_frame {{
        background-color: {colors['bg_panel']};
        border-top: 1px solid {colors['border']};
        border-left: 1px solid {colors['border']};
        border-bottom: 2px solid {colors['border_dark']};
        border-right: 2px solid {colors['border_dark']};
        border-radius: 0px;
    }}

    /* 像素按钮 */
    QPushButton {{
        background-color: {colors['bg_card']};
        color: {colors['text']};
        border-top: 1px solid {colors['border']};
        border-left: 1px solid {colors['border']};
        border-bottom: 2px solid {colors['border_dark']};
        border-right: 2px solid {colors['border_dark']};
        padding: 5px 12px;
        font-weight: bold;
        border-radius: 0px;
    }}

    QPushButton:hover {{
        background-color: {colors['bg_active']};
        color: {colors['primary_hover']};
        border-top: 1px solid {colors['primary']};
        border-left: 1px solid {colors['primary']};
    }}

    QPushButton:pressed, QPushButton:checked {{
        background-color: {colors['bg_dark']};
        color: {colors['accent_gold']};
        border-top: 2px solid {colors['border_dark']};
        border-left: 2px solid {colors['border_dark']};
        border-bottom: 1px solid {colors['border']};
        border-right: 1px solid {colors['border']};
        padding-top: 6px;
        padding-left: 13px;
        padding-bottom: 4px;
        padding-right: 11px;
    }}

    /* 输入框 */
    QLineEdit, QSpinBox {{
        background-color: {colors['bg_dark']};
        color: {colors['text']};
        border-top: 2px solid {colors['border_dark']};
        border-left: 2px solid {colors['border_dark']};
        border-bottom: 1px solid {colors['border']};
        border-right: 1px solid {colors['border']};
        padding: 5px 8px;
        border-radius: 0px;
        selection-background-color: {colors['primary']};
        selection-color: {colors['bg_dark']};
    }}

    QLineEdit:focus, QSpinBox:focus {{
        border: 1px solid {colors['primary']};
        background-color: {colors['bg_panel']};
    }}

    /* 选项卡设置 */
    QTabWidget::pane {{
        border: 1px solid {colors['border']};
        background-color: {colors['bg_panel']};
    }}

    QTabBar::tab {{
        background-color: {colors['bg_dark']};
        color: {colors['text_dim']};
        border: 1px solid {colors['border_dark']};
        padding: 6px 14px;
        font-weight: bold;
    }}

    QTabBar::tab:selected {{
        background-color: {colors['bg_panel']};
        color: {colors['text']};
        border-top: 2px solid {colors['primary']};
        border-bottom: 1px solid {colors['bg_panel']};
    }}

    /* 滚动条 */
    QScrollArea {{
        border: 1px solid {colors['border_dark']};
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
        border-radius: 0px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {colors['primary']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* 滑块控件 */
    QSlider::groove:horizontal {{
        height: 6px;
        background-color: {colors['bg_dark']};
        border: 1px solid {colors['border_dark']};
    }}

    QSlider::handle:horizontal {{
        background-color: {colors['primary']};
        border: 1px solid {colors['border_dark']};
        width: 12px;
        margin: -4px 0;
    }}

    QSlider::handle:horizontal:hover {{
        background-color: {colors['primary_hover']};
    }}

    QStatusBar {{
        background-color: {colors['bg_panel']};
        color: {colors['text_dim']};
        border-top: 1px solid {colors['border_dark']};
        font-size: 11px;
    }}
    """
