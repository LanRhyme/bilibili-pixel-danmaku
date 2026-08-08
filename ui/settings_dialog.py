from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QLineEdit, QCheckBox, QSlider, QComboBox, QPushButton,
    QFormLayout, QGroupBox, QSpinBox
)
from PySide6.QtCore import Qt
from ui.pixel_widgets import PixelCard
from core.theme import load_morandi_colors

class SettingsDialog(QDialog):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.colors = load_morandi_colors()
        self.setWindowTitle("系统设置 - Bilibili Pixel Danmaku")
        self.resize(560, 520)
        self.init_ui()
        self.load_values()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        # Tab 1: Cookie & Account
        tab_account = QWidget()
        layout_account = QFormLayout(tab_account)
        layout_account.setSpacing(10)

        lbl_cookie_tip = QLabel("填写 B 站 Cookie（包含 SESSDATA 与 bili_jct）可解除未登录连接限制，保障高频弹幕、SC、舰长 100% 零遗漏：")
        lbl_cookie_tip.setWordWrap(True)
        lbl_cookie_tip.setStyleSheet(f"color: {self.colors.get('accent_gold', '#bdb79a')}; font-size: 12px; margin-bottom: 6px;")
        layout_account.addRow(lbl_cookie_tip)

        self.edit_cookie = QLineEdit()
        self.edit_cookie.setPlaceholderText("例如: SESSDATA=xxxx; bili_jct=xxxx; buvid3=xxxx")
        layout_account.addRow("B站 Cookie:", self.edit_cookie)
        self.tabs.addTab(tab_account, "账号鉴权")

        # Tab 2: Desktop Notifications (桌面通知)
        tab_notify = QWidget()
        layout_notify = QFormLayout(tab_notify)
        layout_notify.setSpacing(10)

        self.cb_notify_enable = QCheckBox("启用 Linux 原生系统桌面通知 (notify-send)")
        self.cb_notify_dm = QCheckBox("通知普通弹幕")
        self.cb_notify_gift = QCheckBox("通知高能礼物")
        self.cb_notify_sc = QCheckBox("通知醒目留言 (SuperChat)")
        self.cb_notify_guard = QCheckBox("通知大航海 (舰长/提督/总督)")

        self.spin_notify_expire = QSpinBox()
        self.spin_notify_expire.setRange(1, 30)
        self.spin_notify_expire.setSuffix(" 秒")

        layout_notify.addRow(self.cb_notify_enable)
        layout_notify.addRow(self.cb_notify_dm)
        layout_notify.addRow(self.cb_notify_gift)
        layout_notify.addRow(self.cb_notify_sc)
        layout_notify.addRow(self.cb_notify_guard)
        layout_notify.addRow("通知停留时间:", self.spin_notify_expire)
        self.tabs.addTab(tab_notify, "桌面通知")

        # Tab 3: TTS
        tab_tts = QWidget()
        layout_tts = QFormLayout(tab_tts)

        self.cb_tts_enable = QCheckBox("启用 Edge-TTS 语音播报")
        self.cb_tts_danmaku = QCheckBox("播报普通弹幕")
        self.cb_tts_gifts = QCheckBox("播报礼物感谢")
        self.cb_tts_sc = QCheckBox("播报醒目留言 (SC)")

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

        layout_tts.addRow(self.cb_tts_enable)
        layout_tts.addRow(self.cb_tts_danmaku)
        layout_tts.addRow(self.cb_tts_gifts)
        layout_tts.addRow(self.cb_tts_sc)
        layout_tts.addRow("播报音色:", self.combo_voice)
        layout_tts.addRow("弹幕播报模板:", self.edit_dm_tmpl)
        layout_tts.addRow("礼物感谢模板:", self.edit_gift_tmpl)
        layout_tts.addRow("SC播报模板:", self.edit_sc_tmpl)
        self.tabs.addTab(tab_tts, "语音播报")

        # Tab 4: Audio
        tab_audio = QWidget()
        layout_audio = QFormLayout(tab_audio)
        self.cb_sfx_enable = QCheckBox("启用 8-Bit 复古音效 (送礼/升级/SC)")
        self.slider_vol = QSlider(Qt.Horizontal)
        self.slider_vol.setRange(0, 100)
        self.slider_vol.setValue(80)
        self.lbl_vol = QLabel("80%")
        self.slider_vol.valueChanged.connect(lambda v: self.lbl_vol.setText(f"{v}%"))

        vol_box = QHBoxLayout()
        vol_box.addWidget(self.slider_vol)
        vol_box.addWidget(self.lbl_vol)

        layout_audio.addRow(self.cb_sfx_enable)
        layout_audio.addRow("主音量:", vol_box)
        self.tabs.addTab(tab_audio, "音效音量")

        # Tab 5: Filter
        tab_filter = QWidget()
        layout_filter = QFormLayout(tab_filter)
        self.edit_blocked = QLineEdit()
        self.edit_blocked.setPlaceholderText("多个关键词用逗号隔开")
        layout_filter.addRow("屏蔽关键词列表:", self.edit_blocked)
        self.tabs.addTab(tab_filter, "弹幕过滤")

        main_layout.addWidget(self.tabs)

        btn_box = QHBoxLayout()
        self.btn_save = QPushButton("保存配置")
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

        self.accept()
