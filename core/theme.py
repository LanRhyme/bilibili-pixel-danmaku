import json
from pathlib import Path

MORANDI_APP_COLORS = Path.home() / ".config" / "bilibili-pixel-danmaku" / "morandi_colors.json"

DEFAULT_PALETTE = {
    "bg_dark": "#1c1b18",
    "bg_panel": "#23221e",
    "bg_card": "#2a2924",
    "bg_active": "#35342e",
    "border": "#3d3c34",
    "border_dark": "#121210",
    "text": "#dedcd2",
    "text_dim": "#949289",
    "subtext": "#adaa9e",
    "primary": "#b8b39f",
    "primary_hover": "#c9c4b1",
    "accent_gold": "#c4ba97",
    "accent_rose": "#c47079",
    "accent_green": "#8ea382",
    "accent_cyan": "#8fa4b3",
    "accent_purple": "#a292ad",
    "accent_blue": "#8fa4b3"
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
    c = load_morandi_colors()
    return f"""
    /* 全局主窗口与基础控件 */
    QMainWindow {{
        background-color: {c['bg_dark']};
        color: {c['text']};
        font-family: "Noto Sans CJK SC", "Source Han Sans CN", "Microsoft YaHei", sans-serif;
        font-size: 12px;
    }}

    /* 所有文本标签默认透明，彻底消除背景色块补丁感 */
    QLabel {{
        background: transparent;
        color: {c['text']};
        border: none;
        padding: 0px;
        margin: 0px;
    }}

    /* 面板外框 */
    QFrame#card_frame {{
        background-color: {c['bg_panel']};
        border: 1px solid {c['border']};
        border-radius: 0px;
    }}

    /* 弹幕卡片条目 */
    QFrame#danmaku_item_card {{
        background-color: {c['bg_card']};
        border: 1px solid {c['border']};
        border-radius: 0px;
    }}

    /* 按钮 */
    QPushButton {{
        background-color: {c['bg_card']};
        color: {c['text']};
        border: 1px solid {c['border']};
        padding: 5px 12px;
        font-weight: bold;
        border-radius: 0px;
    }}

    QPushButton:hover {{
        background-color: {c['bg_active']};
        color: {c['primary_hover']};
        border: 1px solid {c['primary']};
    }}

    QPushButton:pressed, QPushButton:checked {{
        background-color: {c['bg_dark']};
        color: {c['accent_gold']};
        border: 1px solid {c['accent_gold']};
    }}

    /* 输入框与数字框 */
    QLineEdit, QSpinBox {{
        background-color: {c['bg_dark']};
        color: {c['text']};
        border: 1px solid {c['border']};
        padding: 4px 8px;
        border-radius: 0px;
        selection-background-color: {c['primary']};
        selection-color: {c['bg_dark']};
    }}

    QLineEdit:focus, QSpinBox:focus {{
        border: 1px solid {c['primary']};
    }}

    /* 滚动区域与容器完全透明无色差 */
    QScrollArea {{
        background-color: {c['bg_dark']};
        border: 1px solid {c['border']};
    }}

    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}

    /* 列表控件与项目 */
    QListWidget {{
        background-color: {c['bg_panel']};
        border: 1px solid {c['border']};
        outline: none;
    }}

    QListWidget::item {{
        background-color: transparent;
        color: {c['text']};
        padding: 4px 6px;
        border-bottom: 1px solid {c['bg_card']};
    }}

    QListWidget::item:hover {{
        background-color: {c['bg_card']};
    }}

    QListWidget::item:selected {{
        background-color: {c['bg_active']};
        color: {c['accent_gold']};
    }}

    /* 分割线 */
    QSplitter::handle {{
        background-color: {c['bg_dark']};
    }}

    /* 选项卡设置 */
    QTabWidget::pane {{
        border: 1px solid {c['border']};
        background-color: {c['bg_panel']};
    }}

    QTabBar::tab {{
        background-color: {c['bg_dark']};
        color: {c['text_dim']};
        border: 1px solid {c['border']};
        padding: 6px 14px;
        font-weight: bold;
    }}

    QTabBar::tab:selected {{
        background-color: {c['bg_panel']};
        color: {c['text']};
        border-bottom: 1px solid {c['bg_panel']};
    }}

    /* 滚动条 */
    QScrollBar:vertical {{
        background-color: {c['bg_dark']};
        width: 8px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {c['border']};
        min-height: 20px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {c['primary']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* 滑块控件 */
    QSlider::groove:horizontal {{
        height: 4px;
        background-color: {c['bg_dark']};
        border: 1px solid {c['border']};
    }}

    QSlider::handle:horizontal {{
        background-color: {c['primary']};
        border: 1px solid {c['border_dark']};
        width: 10px;
        margin: -4px 0;
    }}

    QSlider::handle:horizontal:hover {{
        background-color: {c['accent_gold']};
    }}

    QStatusBar {{
        background-color: {c['bg_panel']};
        color: {c['text_dim']};
        border-top: 1px solid {c['border']};
        font-size: 11px;
    }}
    """
