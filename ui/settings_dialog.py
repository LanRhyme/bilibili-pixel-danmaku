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
        self.setWindowTitle("系统设置 - Pixel Danmaku")
        self.resize(500, 480)
        self.init_ui()
        self.load_values()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        # Tab 1: TTS
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

        # Tab 2: Audio
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

        # Tab 3: Overlay
        tab_overlay = QWidget()
        layout_overlay = QFormLayout(tab_overlay)
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(10, 100)
        self.lbl_opacity = QLabel("90%")
        self.slider_opacity.valueChanged.connect(lambda v: self.lbl_opacity.setText(f"{v}%"))

        op_box = QHBoxLayout()
        op_box.addWidget(self.slider_opacity)
        op_box.addWidget(self.lbl_opacity)

        self.spin_max_dm = QSpinBox()
        self.spin_max_dm.setRange(5, 100)

        layout_overlay.addRow("悬浮窗不透明度:", op_box)
        layout_overlay.addRow("最大弹幕保留行数:", self.spin_max_dm)
        self.tabs.addTab(tab_overlay, "悬浮窗")

        # Tab 4: Filter
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

        op = c.get("overlay.opacity", 90)
        self.slider_opacity.setValue(op)
        self.lbl_opacity.setText(f"{op}%")
        self.spin_max_dm.setValue(c.get("overlay.max_danmaku", 30))

        blocked = c.get("filter.blocked_keywords", [])
        self.edit_blocked.setText(", ".join(blocked))

    def save_and_close(self):
        c = self.config_manager
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

        c.set("overlay.opacity", self.slider_opacity.value())
        c.set("overlay.max_danmaku", self.spin_max_dm.value())

        kw_text = self.edit_blocked.text().strip()
        kws = [k.strip() for k in kw_text.split(",") if k.strip()]
        c.set("filter.blocked_keywords", kws)

        self.accept()
