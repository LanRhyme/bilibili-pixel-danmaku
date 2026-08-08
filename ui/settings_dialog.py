import sys

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QCheckBox, QSlider, QComboBox, QPushButton,
    QFormLayout, QGroupBox, QSpinBox, QFrame
)
from PySide6.QtCore import Qt
from core.theme import load_morandi_colors

class SettingsDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.colors = load_morandi_colors()
        self.setWindowTitle("系统设置 · Pixel Danmaku")
        self.resize(580, 560)
        self.init_ui()
        self.load_values()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)
        self.tabs = QTabWidget()

        # Tab 1: Cookie & Account
        tab_account = QWidget()
        layout_account = QVBoxLayout(tab_account)
        layout_account.setContentsMargins(12, 12, 12, 12)
        layout_account.setSpacing(10)

        grp_cookie = QGroupBox("B 站账号鉴权")
        gl_cookie = QVBoxLayout(grp_cookie)
        gl_cookie.setSpacing(8)
        lbl_cookie_tip = QLabel("填写 B 站 Cookie（包含 SESSDATA 与 bili_jct）可解除未登录连接限制，保障高频弹幕、SC、舰长 100% 零遗漏")
        lbl_cookie_tip.setWordWrap(True)
        lbl_cookie_tip.setStyleSheet(f"color: {self.colors.get('accent_gold', '#bdb79a')}; font-size: 12px;")
        gl_cookie.addWidget(lbl_cookie_tip)
        self.edit_cookie = QLineEdit()
        self.edit_cookie.setPlaceholderText("例如: SESSDATA=xxxx; bili_jct=xxxx; buvid3=xxxx")
        gl_cookie.addWidget(self.edit_cookie)
        layout_account.addWidget(grp_cookie)
        layout_account.addStretch()
        self.tabs.addTab(tab_account, "账号鉴权")

        # Tab 2: Desktop Notifications
        tab_notify = QWidget()
        layout_notify = QVBoxLayout(tab_notify)
        layout_notify.setContentsMargins(12, 12, 12, 12)
        layout_notify.setSpacing(10)

        grp_notify = QGroupBox("通知内容")
        gl_notify = QVBoxLayout(grp_notify)
        gl_notify.setSpacing(8)
        self.cb_notify_enable = QCheckBox("启用系统桌面通知")
        self.cb_notify_dm = QCheckBox("通知普通弹幕")
        self.cb_notify_gift = QCheckBox("通知高能礼物")
        self.cb_notify_sc = QCheckBox("通知醒目留言 (SuperChat)")
        self.cb_notify_guard = QCheckBox("通知大航海 (舰长/提督/总督)")
        gl_notify.addWidget(self.cb_notify_enable)
        gl_notify.addWidget(self.cb_notify_dm)
        gl_notify.addWidget(self.cb_notify_gift)
        gl_notify.addWidget(self.cb_notify_sc)
        gl_notify.addWidget(self.cb_notify_guard)

        self.spin_notify_expire = QSpinBox()
        self.spin_notify_expire.setRange(1, 30)
        self.spin_notify_expire.setSuffix(" 秒")
        form_expire = QFormLayout()
        form_expire.addRow("通知停留时间:", self.spin_notify_expire)
        gl_notify.addLayout(form_expire)

        if sys.platform == "darwin":
            self.spin_notify_expire.setEnabled(False)
            lbl_expire_hint = QLabel(
                "此选项仅 Linux 生效"
            )
            lbl_expire_hint.setStyleSheet(
                f"color: {self.colors.get('text_dim', '#dededd')}; font-size: 12px;"
            )
            lbl_expire_hint.setWordWrap(True)
            gl_notify.addWidget(lbl_expire_hint)

        layout_notify.addWidget(grp_notify)
        layout_notify.addStretch()
        self.tabs.addTab(tab_notify, "桌面通知")

        # Tab 3: TTS
        tab_tts = QWidget()
        layout_tts = QVBoxLayout(tab_tts)
        layout_tts.setContentsMargins(12, 12, 12, 12)
        layout_tts.setSpacing(10)

        grp_tts_sw = QGroupBox("播报内容")
        gl_sw = QVBoxLayout(grp_tts_sw)
        gl_sw.setSpacing(8)
        self.cb_tts_enable = QCheckBox("启用 Edge-TTS 语音播报")
        self.cb_tts_danmaku = QCheckBox("播报普通弹幕")
        self.cb_tts_gifts = QCheckBox("播报礼物感谢")
        self.cb_tts_sc = QCheckBox("播报醒目留言 (SC)")
        gl_sw.addWidget(self.cb_tts_enable)
        gl_sw.addWidget(self.cb_tts_danmaku)
        gl_sw.addWidget(self.cb_tts_gifts)
        gl_sw.addWidget(self.cb_tts_sc)

        grp_tts_cfg = QGroupBox("播报配置")
        gl_cfg = QFormLayout(grp_tts_cfg)
        gl_cfg.setSpacing(8)
        self.combo_voice = QComboBox()
        voices = [
            ("晓晓 (女声，自然)", "zh-CN-XiaoxiaoNeural"),
            ("云希 (男声，沉稳)", "zh-CN-YunxiNeural"),
            ("云扬 (男声，专业)", "zh-CN-YunyangNeural"),
            ("晓依 (女声，甜美)", "zh-CN-XiaoyiNeural"),
            ("辽宁东北话 (晓北)", "zh-CN-liaoning-XiaobeiNeural"),
            ("陕西陕西方言 (晓妮)", "zh-CN-shaanxi-XiaoniNeural")
        ]
        for name, code in voices:
            self.combo_voice.addItem(name, code)

        self.edit_dm_tmpl = QLineEdit()
        self.edit_gift_tmpl = QLineEdit()
        self.edit_sc_tmpl = QLineEdit()

        gl_cfg.addRow("播报音色:", self.combo_voice)
        gl_cfg.addRow("弹幕播报模板:", self.edit_dm_tmpl)
        gl_cfg.addRow("礼物感谢模板:", self.edit_gift_tmpl)
        gl_cfg.addRow("SC播报模板:", self.edit_sc_tmpl)

        layout_tts.addWidget(grp_tts_sw)
        layout_tts.addWidget(grp_tts_cfg)
        layout_tts.addStretch()
        self.tabs.addTab(tab_tts, "语音播报")

        # Tab 4: Audio
        tab_audio = QWidget()
        layout_audio = QVBoxLayout(tab_audio)
        layout_audio.setContentsMargins(12, 12, 12, 12)
        layout_audio.setSpacing(10)

        grp_audio = QGroupBox("音效与音量")
        gl_audio = QVBoxLayout(grp_audio)
        gl_audio.setSpacing(10)
        self.cb_sfx_enable = QCheckBox("启用 8-Bit 复古音效 (送礼/升级/SC)")
        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(80)
        self.lbl_vol = QLabel("80%")
        self.lbl_vol.setStyleSheet(f"color: {self.colors.get('accent_gold', '#bdb79a')}; font-weight: bold;")
        self.slider_vol.valueChanged.connect(lambda v: self.lbl_vol.setText(f"{v}%"))

        vol_box = QHBoxLayout()
        vol_box.addWidget(self.slider_vol)
        vol_box.addWidget(self.lbl_vol)

        gl_audio.addWidget(self.cb_sfx_enable)
        gl_audio.addWidget(QLabel("主音量:"))
        gl_audio.addLayout(vol_box)
        layout_audio.addWidget(grp_audio)
        layout_audio.addStretch()
        self.tabs.addTab(tab_audio, "音效音量")

        # Tab 5: Filter
        tab_filter = QWidget()
        layout_filter = QVBoxLayout(tab_filter)
        layout_filter.setContentsMargins(12, 12, 12, 12)
        layout_filter.setSpacing(10)

        grp_filter = QGroupBox("屏蔽规则")
        gl_filter = QVBoxLayout(grp_filter)
        gl_filter.setSpacing(8)
        lbl_filter_tip = QLabel("命中关键词的弹幕将不会显示、播报与通知")
        lbl_filter_tip.setStyleSheet(f"color: {self.colors.get('text_dim', '#dededd')}; font-size: 12px;")
        self.edit_blocked = QLineEdit()
        self.edit_blocked.setPlaceholderText("多个关键词用逗号隔开")
        gl_filter.addWidget(lbl_filter_tip)
        gl_filter.addWidget(self.edit_blocked)
        layout_filter.addWidget(grp_filter)
        layout_filter.addStretch()
        self.tabs.addTab(tab_filter, "弹幕过滤")

        # Tab 6: UI Display Scale (界面显示)
        tab_ui = QWidget()
        layout_ui = QVBoxLayout(tab_ui)
        layout_ui.setContentsMargins(12, 12, 12, 12)
        layout_ui.setSpacing(10)

        grp_ui_dm = QGroupBox("弹幕面板")
        gl_ui_dm = QVBoxLayout(grp_ui_dm)
        gl_ui_dm.setSpacing(10)
        gl_ui_dm.addWidget(QLabel("弹幕内容字号:"))
        self.slider_dm_font = QSlider(Qt.Orientation.Horizontal)
        self.slider_dm_font.setRange(10, 24)
        self.slider_dm_font.setValue(12)
        self.lbl_dm_font = QLabel("12px")
        self.lbl_dm_font.setStyleSheet(f"color: {self.colors.get('accent_gold', '#bdb79a')}; font-weight: bold;")
        row_dm_font = QHBoxLayout()
        row_dm_font.addWidget(self.slider_dm_font)
        row_dm_font.addWidget(self.lbl_dm_font)
        gl_ui_dm.addLayout(row_dm_font)

        gl_ui_dm.addWidget(QLabel("头像大小:"))
        self.slider_avatar = QSlider(Qt.Orientation.Horizontal)
        self.slider_avatar.setRange(24, 64)
        self.slider_avatar.setValue(32)
        self.lbl_avatar = QLabel("32px")
        self.lbl_avatar.setStyleSheet(f"color: {self.colors.get('accent_gold', '#bdb79a')}; font-weight: bold;")
        row_avatar = QHBoxLayout()
        row_avatar.addWidget(self.slider_avatar)
        row_avatar.addWidget(self.lbl_avatar)
        gl_ui_dm.addLayout(row_avatar)
        layout_ui.addWidget(grp_ui_dm)

        grp_ui_vip = QGroupBox("高能榜与醒目留言面板")
        gl_ui_vip = QVBoxLayout(grp_ui_vip)
        gl_ui_vip.setSpacing(10)
        gl_ui_vip.addWidget(QLabel("列表字号:"))
        self.slider_vip_font = QSlider(Qt.Orientation.Horizontal)
        self.slider_vip_font.setRange(10, 24)
        self.slider_vip_font.setValue(12)
        self.lbl_vip_font = QLabel("12px")
        self.lbl_vip_font.setStyleSheet(f"color: {self.colors.get('accent_gold', '#bdb79a')}; font-weight: bold;")
        row_vip_font = QHBoxLayout()
        row_vip_font.addWidget(self.slider_vip_font)
        row_vip_font.addWidget(self.lbl_vip_font)
        gl_ui_vip.addLayout(row_vip_font)
        layout_ui.addWidget(grp_ui_vip)
        layout_ui.addStretch()

        self.slider_dm_font.valueChanged.connect(lambda v: self.lbl_dm_font.setText(f"{v}px"))
        self.slider_avatar.valueChanged.connect(lambda v: self.lbl_avatar.setText(f"{v}px"))
        self.slider_vip_font.valueChanged.connect(lambda v: self.lbl_vip_font.setText(f"{v}px"))
        self.tabs.addTab(tab_ui, "界面显示")

        main_layout.addWidget(self.tabs)

        # Bottom button bar with separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {self.colors.get('border', '#64635f')}; max-height: 1px; border: none;")
        main_layout.addWidget(sep)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(8)
        self.btn_save = QPushButton("保存配置")
        self.btn_save.setObjectName("save_btn")
        self.btn_cancel = QPushButton("取消")
        self.btn_save.clicked.connect(self.save_and_close)
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addStretch()
        btn_box.addWidget(self.btn_save)
        btn_box.addWidget(self.btn_cancel)
        main_layout.addLayout(btn_box)

    def load_values(self):
        c = self.config_manager
        self.edit_cookie.setText(c.get("bilibili_cookie", ""))

        self.cb_notify_enable.setChecked(c.get("notification.enabled", True))
        self.cb_notify_dm.setChecked(c.get("notification.danmaku", False))
        self.cb_notify_gift.setChecked(c.get("notification.gifts", True))
        self.cb_notify_sc.setChecked(c.get("notification.superchat", True))
        self.cb_notify_guard.setChecked(c.get("notification.guard", True))
        self.spin_notify_expire.setValue(c.get("notification.expire_ms", 4000) // 1000)

        self.cb_tts_enable.setChecked(c.get("tts.enabled", True))
        self.cb_tts_danmaku.setChecked(c.get("tts.read_danmaku", True))
        self.cb_tts_gifts.setChecked(c.get("tts.read_gifts", True))
        self.cb_tts_sc.setChecked(c.get("tts.read_superchat", True))

        voice_code = c.get("tts.voice", "zh-CN-XiaoxiaoNeural")
        idx = self.combo_voice.findData(voice_code)
        if idx >= 0: self.combo_voice.setCurrentIndex(idx)

        self.edit_dm_tmpl.setText(c.get("tts.danmaku_template", "{user}说：{msg}"))
        self.edit_gift_tmpl.setText(c.get("tts.gift_template", "感谢 {user} 送出的 {gift_name} x {num}"))
        self.edit_sc_tmpl.setText(c.get("tts.sc_template", "感谢 {user} 的 {price} 元醒目留言：{msg}"))

        self.cb_sfx_enable.setChecked(c.get("audio.sound_effects_enabled", True))
        vol = c.get("audio.master_volume", 80)
        self.slider_vol.setValue(vol)
        self.lbl_vol.setText(f"{vol}%")

        blocked = c.get("filter.blocked_keywords", [])
        self.edit_blocked.setText(", ".join(blocked))

        dm_font = c.get("ui.danmaku_font_size", 12)
        self.slider_dm_font.setValue(dm_font)
        self.lbl_dm_font.setText(f"{dm_font}px")
        avatar = c.get("ui.avatar_size", 32)
        self.slider_avatar.setValue(avatar)
        self.lbl_avatar.setText(f"{avatar}px")
        vip_font = c.get("ui.vip_font_size", 12)
        self.slider_vip_font.setValue(vip_font)
        self.lbl_vip_font.setText(f"{vip_font}px")

    def save_and_close(self):
        c = self.config_manager
        c.set("bilibili_cookie", self.edit_cookie.text().strip())

        c.set("notification.enabled", self.cb_notify_enable.isChecked())
        c.set("notification.danmaku", self.cb_notify_dm.isChecked())
        c.set("notification.gifts", self.cb_notify_gift.isChecked())
        c.set("notification.superchat", self.cb_notify_sc.isChecked())
        c.set("notification.guard", self.cb_notify_guard.isChecked())
        c.set("notification.expire_ms", self.spin_notify_expire.value() * 1000)

        c.set("tts.enabled", self.cb_tts_enable.isChecked())
        c.set("tts.read_danmaku", self.cb_tts_danmaku.isChecked())
        c.set("tts.read_gifts", self.cb_tts_gifts.isChecked())
        c.set("tts.read_superchat", self.cb_tts_sc.isChecked())
        c.set("tts.voice", self.combo_voice.currentData())
        c.set("tts.danmaku_template", self.edit_dm_tmpl.text())
        c.set("tts.gift_template", self.edit_gift_tmpl.text())
        c.set("tts.sc_template", self.edit_sc_tmpl.text())

        c.set("audio.sound_effects_enabled", self.cb_sfx_enable.isChecked())
        c.set("audio.master_volume", self.slider_vol.value())

        kw_text = self.edit_blocked.text().strip()
        kws = [k.strip() for k in kw_text.split(",") if k.strip()]
        c.set("filter.blocked_keywords", kws)

        c.set("ui.danmaku_font_size", self.slider_dm_font.value())
        c.set("ui.avatar_size", self.slider_avatar.value())
        c.set("ui.vip_font_size", self.slider_vip_font.value())

        self.accept()
