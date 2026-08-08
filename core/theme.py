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
    /* ============================================================
     * 莫兰迪复古像素风 2.0
     * 设计语言: 低饱和莫兰迪底色 + 直角硬边 + 双层边框层次
     *          主操作实色块 + 按压下沉动效 + HUD 色条统计
     * 所有颜色均来自 morandi_colors.json, 随壁纸动态同步
     * ============================================================ */

    /* ---- 全局基础 ---- */
    QMainWindow {{
        background-color: {c.get('bg_dark', '#1a1a18')};
        color: {c.get('text', '#f2f2f2')};
        font-family: "Noto Sans CJK SC", "Source Han Sans CN", "Microsoft YaHei", sans-serif;
        font-size: 12px;
    }}

    QDialog {{
        background-color: {c.get('bg_panel', '#302f2c')};
        color: {c.get('text', '#f2f2f2')};
        font-family: "Noto Sans CJK SC", "Source Han Sans CN", "Microsoft YaHei", sans-serif;
        font-size: 12px;
    }}

    QDialog QTabWidget::pane, QDialog QGroupBox {{
        background-color: {c.get('bg_panel', '#302f2c')};
    }}

    QWidget {{
        color: {c.get('text', '#f2f2f2')};
        font-size: 12px;
    }}

    QLabel {{
        background: transparent;
        color: {c.get('text', '#f2f2f2')};
        border: none;
        padding: 0px;
        margin: 0px;
    }}

    /* ---- 面板卡片: 顶部高光营造像素凸起感 ---- */
    QFrame#card_frame {{
        background-color: {c.get('bg_panel', '#302f2c')};
        border: 1px solid {c.get('border', '#64635f')};
        border-top: 1px solid {c.get('bg_active', '#403f39')};
        border-radius: 0px;
    }}

    /* ---- 弹幕卡片条目: 默认暗底, hover 提亮 ---- */
    QFrame#danmaku_item_card {{
        background-color: {c.get('bg_card', '#383732')};
        border: 1px solid {c.get('border', '#64635f')};
        border-radius: 0px;
    }}

    QFrame#danmaku_item_card:hover {{
        background-color: {c.get('bg_active', '#403f39')};
        border: 1px solid {c.get('primary', '#afac9c')};
    }}

    /* ---- 主操作按钮: 金色实色块 + 厚底边(按压下沉) ---- */
    QPushButton#connect_btn, QPushButton#save_btn {{
        background-color: {c.get('accent_gold', '#bdb79a')};
        color: {c.get('bg_dark', '#1a1a18')};
        border: 1px solid {c.get('border_dark', '#16161e')};
        border-bottom: 3px solid {c.get('border_dark', '#16161e')};
        padding: 6px 18px;
        font-weight: bold;
        font-size: 13px;
        border-radius: 0px;
    }}

    QPushButton#connect_btn:hover, QPushButton#save_btn:hover {{
        background-color: {c.get('primary_hover', '#c25f63')};
        color: {c.get('bg_dark', '#1a1a18')};
    }}

    QPushButton#connect_btn:pressed, QPushButton#save_btn:pressed {{
        border-bottom: 1px solid {c.get('border_dark', '#16161e')};
        padding-top: 8px;
        padding-bottom: 4px;
    }}

    /* ---- 次级按钮 ---- */
    QPushButton {{
        background-color: {c.get('bg_card', '#383732')};
        color: {c.get('text', '#f2f2f2')};
        border: 1px solid {c.get('border', '#64635f')};
        border-bottom: 2px solid {c.get('border_dark', '#16161e')};
        padding: 4px 12px;
        font-weight: bold;
        border-radius: 0px;
    }}

    QPushButton:hover {{
        background-color: {c.get('bg_active', '#403f39')};
        color: {c.get('primary', '#afac9c')};
        border-color: {c.get('primary', '#afac9c')};
    }}

    QPushButton:pressed {{
        border-bottom: 1px solid {c.get('border_dark', '#16161e')};
        padding-top: 5px;
        padding-bottom: 3px;
    }}

    QPushButton:checked {{
        background-color: {c.get('bg_dark', '#1a1a18')};
        color: {c.get('accent_gold', '#bdb79a')};
        border: 1px solid {c.get('accent_gold', '#bdb79a')};
        border-bottom: 2px solid {c.get('accent_gold', '#bdb79a')};
    }}

    /* ---- 输入框 / 数字框 / 下拉框: 聚焦金色下划线 ---- */
    QLineEdit, QSpinBox, QComboBox {{
        background-color: {c.get('bg_dark', '#1a1a18')};
        color: {c.get('text', '#f2f2f2')};
        border: 1px solid {c.get('border', '#64635f')};
        border-bottom: 2px solid {c.get('border', '#64635f')};
        padding: 4px 8px;
        border-radius: 0px;
        selection-background-color: {c.get('primary', '#afac9c')};
        selection-color: {c.get('bg_dark', '#1a1a18')};
    }}

    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
        border: 1px solid {c.get('primary', '#afac9c')};
        border-bottom: 2px solid {c.get('accent_gold', '#bdb79a')};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 22px;
        subcontrol-origin: padding;
        subcontrol-position: top right;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 3px solid {c.get('text_dim', '#dededd')};
        border-bottom: 3px solid {c.get('text_dim', '#dededd')};
        width: 5px;
        height: 5px;
        margin-right: 8px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {c.get('bg_panel', '#302f2c')};
        color: {c.get('text', '#f2f2f2')};
        border: 1px solid {c.get('border', '#64635f')};
        selection-background-color: {c.get('bg_active', '#403f39')};
        selection-color: {c.get('accent_gold', '#bdb79a')};
        outline: none;
    }}

    /* ---- 滚动区域: 容器透明, 仅外框 ---- */
    QScrollArea {{
        background-color: {c.get('bg_dark', '#1a1a18')};
        border: 1px solid {c.get('border', '#64635f')};
    }}

    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}

    /* ---- 列表控件 ---- */
    QListWidget {{
        background-color: {c.get('bg_dark', '#1a1a18')};
        border: 1px solid {c.get('border', '#64635f')};
        outline: none;
    }}

    QListWidget::item {{
        background-color: transparent;
        color: {c.get('text', '#f2f2f2')};
        padding: 5px 8px;
        border-bottom: 1px solid {c.get('bg_card', '#383732')};
    }}

    QListWidget::item:hover {{
        background-color: {c.get('bg_card', '#383732')};
    }}

    QListWidget::item:selected {{
        background-color: {c.get('bg_active', '#403f39')};
        color: {c.get('accent_gold', '#bdb79a')};
    }}

    /* ---- 分割线 ---- */
    QSplitter::handle {{
        background-color: {c.get('bg_dark', '#1a1a18')};
        width: 2px;
    }}

    QSplitter::handle:hover {{
        background-color: {c.get('accent_gold', '#bdb79a')};
    }}

    /* ---- 选项卡: 选中项金色顶条 ---- */
    QTabWidget::pane {{
        border: 1px solid {c.get('border', '#64635f')};
        background-color: {c.get('bg_panel', '#302f2c')};
    }}

    QTabBar::tab {{
        background-color: {c.get('bg_dark', '#1a1a18')};
        color: {c.get('text_dim', '#dededd')};
        border: 1px solid {c.get('border', '#64635f')};
        border-bottom: none;
        padding: 6px 18px;
        font-weight: bold;
    }}

    QTabBar::tab:hover {{
        background-color: {c.get('bg_card', '#383732')};
        color: {c.get('text', '#f2f2f2')};
    }}

    QTabBar::tab:selected {{
        background-color: {c.get('bg_panel', '#302f2c')};
        color: {c.get('accent_gold', '#bdb79a')};
        border-top: 2px solid {c.get('accent_gold', '#bdb79a')};
    }}

    /* ---- 滚动条: 细窄像素滑块 ---- */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 8px;
        margin: 1px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {c.get('border', '#64635f')};
        min-height: 24px;
        border: 1px solid {c.get('border_dark', '#16161e')};
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {c.get('accent_gold', '#bdb79a')};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background-color: transparent;
        height: 8px;
        margin: 1px;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {c.get('border', '#64635f')};
        min-width: 24px;
        border: 1px solid {c.get('border_dark', '#16161e')};
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {c.get('accent_gold', '#bdb79a')};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* ---- 滑块: 金色已填充段 ---- */
    QSlider::groove:horizontal {{
        height: 6px;
        background-color: {c.get('bg_dark', '#1a1a18')};
        border: 1px solid {c.get('border', '#64635f')};
    }}

    QSlider::sub-page:horizontal {{
        background-color: {c.get('accent_gold', '#bdb79a')};
        border: 1px solid {c.get('border', '#64635f')};
    }}

    QSlider::handle:horizontal {{
        background-color: {c.get('primary', '#afac9c')};
        border: 1px solid {c.get('border_dark', '#16161e')};
        width: 12px;
        margin: -5px 0;
    }}

    QSlider::handle:horizontal:hover {{
        background-color: {c.get('accent_gold', '#bdb79a')};
    }}

    /* ---- 复选框: 像素方块 ---- */
    QCheckBox {{
        color: {c.get('text', '#f2f2f2')};
        spacing: 7px;
        padding: 1px 0;
    }}

    QCheckBox::indicator {{
        width: 13px;
        height: 13px;
        border: 1px solid {c.get('border', '#64635f')};
        background-color: {c.get('bg_dark', '#1a1a18')};
    }}

    QCheckBox::indicator:hover {{
        border-color: {c.get('primary', '#afac9c')};
    }}

    QCheckBox::indicator:checked {{
        background-color: {c.get('accent_gold', '#bdb79a')};
        border: 1px solid {c.get('accent_gold', '#bdb79a')};
    }}

    /* ---- 分组框 ---- */
    QGroupBox {{
        border: 1px solid {c.get('border', '#64635f')};
        margin-top: 14px;
        padding: 10px 8px 6px 8px;
        font-weight: bold;
        color: {c.get('text', '#f2f2f2')};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 8px;
        padding: 0 5px;
        color: {c.get('primary', '#afac9c')};
        background-color: {c.get('bg_panel', '#302f2c')};
    }}

    /* ---- 状态栏 ---- */
    QStatusBar {{
        background-color: {c.get('bg_panel', '#302f2c')};
        color: {c.get('text_dim', '#dededd')};
        border-top: 1px solid {c.get('border', '#64635f')};
        font-size: 11px;
    }}

    QStatusBar::item {{
        border: none;
    }}

    QStatusBar QLabel {{
        color: {c.get('text_dim', '#dededd')};
        background: transparent;
    }}

    /* ---- 消息框 ---- */
    QMessageBox {{
        background-color: {c.get('bg_panel', '#302f2c')};
    }}
    """
