import asyncio
import csv
import time
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QFrame, QSplitter, QStatusBar,
    QMessageBox, QApplication, QScrollArea, QSlider
)
from PySide6.QtCore import Qt, Slot, QTimer, QFileSystemWatcher
from core.bilibili_ws import BilibiliWSClient, BilibiliWSThread
from core.edge_tts import EdgeTTS
from core.sound_manager import SoundManager
from core.desktop_notifier import DesktopNotifier
from ui.pixel_widgets import PixelBadge, DanmakuCardWidget, PixelCard
from ui.settings_dialog import SettingsDialog
from core.theme import get_pixel_qss, MORANDI_APP_COLORS, load_morandi_colors

class MainWindow(QMainWindow):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.colors = load_morandi_colors()

        self.ws_client = None
        self.ws_thread = None

        self.sound_manager = SoundManager(self)
        self.tts_engine = EdgeTTS()
        self.desktop_notifier = DesktopNotifier(self.config_manager)

        self.tts_loop = None
        self.tts_queue = None

        # Analytics Data
        self.session_start_time = None
        self.danmaku_count = 0
        self.gift_count = 0
        self.battery_total = 0.0
        self.sc_total = 0.0
        self.guard_count = 0
        self.session_records = []

        self.setWindowTitle("Bilibili Pixel Danmaku (莫兰迪像素风弹幕助手)")
        self.resize(960, 660)

        self.init_ui()
        self.load_config_into_ui()

        # Timer for live duration counter
        self.live_timer = QTimer(self)
        self.live_timer.timeout.connect(self.update_live_timer)

        # Theme File Watcher
        self.theme_watcher = QFileSystemWatcher(self)
        if MORANDI_APP_COLORS.exists():
            self.theme_watcher.addPath(str(MORANDI_APP_COLORS))
        self.theme_watcher.fileChanged.connect(self.reload_theme)

        # Start TTS Async Task Queue Worker
        QTimer.singleShot(500, self.start_tts_queue_worker)

    @Slot()
    def reload_theme(self):
        try:
            self.colors = load_morandi_colors()
            qss = get_pixel_qss()
            QApplication.instance().setStyleSheet(qss)
            self.status_bar.showMessage("已自动同步全局 Morandi 壁纸主题配色")
            self.pop_label.setStyleSheet(f"color: {self.colors.get('accent_gold', '#c4ba97')}; font-weight: bold;")
            if self.ws_client and self.ws_client.is_running:
                self.status_badge.set_badge("[ 状态: 已连接 ]", bg_color=self.colors.get('accent_green', '#8ea382'), text_color=self.colors.get('bg_dark', '#1c1b18'))
            else:
                self.status_badge.set_badge("[ 状态: 已断开 ]", bg_color=self.colors.get('bg_card', '#2a2924'), text_color=self.colors.get('text_dim', '#949289'))
        except Exception as e:
            print(f"[Theme] Reload failed: {e}")

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Top Header Card (Controls + Metrics)
        top_card = PixelCard()
        top_layout = QVBoxLayout(top_card)
        top_layout.setContentsMargins(10, 8, 10, 8)
        top_layout.setSpacing(8)

        # Row 1: Connection & Main Controls
        r1_layout = QHBoxLayout()
        r1_layout.setSpacing(10)

        lbl_room = QLabel("直播间号:")
        lbl_room.setStyleSheet(f"font-weight: bold; color: {self.colors.get('primary', '#b8b39f')};")
        
        self.room_input = QLineEdit()
        self.room_input.setPlaceholderText("房间号, 如: 544853")
        self.room_input.setMaximumWidth(140)
        self.room_input.returnPressed.connect(self.toggle_connection)

        self.connect_btn = QPushButton("连接直播间")
        self.connect_btn.clicked.connect(self.toggle_connection)

        self.status_badge = PixelBadge("[ 状态: 已断开 ]", bg_color=self.colors.get('bg_card', '#2a2924'), text_color=self.colors.get('text_dim', '#949289'))
        self.pop_label = QLabel("人气: 0")
        self.pop_label.setStyleSheet(f"color: {self.colors.get('accent_gold', '#c4ba97')}; font-weight: bold;")

        btn_export = QPushButton("[ 导出记录 ]")
        btn_export.clicked.connect(self.export_session_data)

        btn_settings = QPushButton("[ 设置 ]")
        btn_settings.clicked.connect(self.open_settings)

        r1_layout.addWidget(lbl_room)
        r1_layout.addWidget(self.room_input)
        r1_layout.addWidget(self.connect_btn)
        r1_layout.addWidget(self.status_badge)
        r1_layout.addStretch()
        r1_layout.addWidget(self.pop_label)
        r1_layout.addWidget(btn_export)
        r1_layout.addWidget(btn_settings)
        top_layout.addLayout(r1_layout)

        # Row 2: Live Analytics HUD Bar
        r2_layout = QHBoxLayout()
        r2_layout.setSpacing(8)

        self.badge_duration = PixelBadge("[ 时长: 00:00:00 ]", bg_color=self.colors.get('bg_dark', '#1c1b18'), text_color=self.colors.get('text_dim', '#949289'))
        self.badge_dm_stat = PixelBadge("[ 弹幕: 0 条 ]", bg_color=self.colors.get('bg_dark', '#1c1b18'), text_color=self.colors.get('text', '#dedcd2'))
        self.badge_gift_stat = PixelBadge("[ 礼物: 0 (¥0.0) ]", bg_color=self.colors.get('bg_dark', '#1c1b18'), text_color=self.colors.get('accent_gold', '#c4ba97'))
        self.badge_sc_stat = PixelBadge("[ SC: ¥0.0 ]", bg_color=self.colors.get('bg_dark', '#1c1b18'), text_color=self.colors.get('accent_rose', '#c47079'))
        self.badge_guard_stat = PixelBadge("[ 舰队: 0 舰 ]", bg_color=self.colors.get('bg_dark', '#1c1b18'), text_color=self.colors.get('accent_purple', '#a292ad'))

        r2_layout.addWidget(self.badge_duration)
        r2_layout.addWidget(self.badge_dm_stat)
        r2_layout.addWidget(self.badge_gift_stat)
        r2_layout.addWidget(self.badge_sc_stat)
        r2_layout.addWidget(self.badge_guard_stat)
        r2_layout.addStretch()
        top_layout.addLayout(r2_layout)

        main_layout.addWidget(top_card)

        # Center Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        # Left: Danmaku Realtime Feed List
        left_panel = PixelCard()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(6)

        feed_title_box = QHBoxLayout()
        feed_title = QLabel("实时弹幕数据流")
        feed_title.setStyleSheet(f"font-weight: bold; color: {self.colors.get('primary', '#b8b39f')};")
        self.btn_clear = QPushButton("清屏")
        self.btn_clear.clicked.connect(self.clear_feed)
        feed_title_box.addWidget(feed_title)
        feed_title_box.addStretch()
        feed_title_box.addWidget(self.btn_clear)
        left_layout.addLayout(feed_title_box)

        self.danmaku_scroll = QScrollArea()
        self.danmaku_scroll.setWidgetResizable(True)
        self.danmaku_scroll.setStyleSheet("border: none; background: transparent;")
        
        self.danmaku_container = QWidget()
        self.danmaku_container.setStyleSheet("background: transparent;")
        self.danmaku_layout = QVBoxLayout(self.danmaku_container)
        self.danmaku_layout.setContentsMargins(0, 0, 0, 0)
        self.danmaku_layout.setSpacing(6)
        self.danmaku_layout.addStretch()
        self.danmaku_scroll.setWidget(self.danmaku_container)

        left_layout.addWidget(self.danmaku_scroll)
        splitter.addWidget(left_panel)

        # Right: Quick Controls & VIP Wall
        right_panel = PixelCard()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(8)

        right_title = QLabel("控制中心与贵宾区")
        right_title.setStyleSheet(f"font-weight: bold; color: {self.colors.get('primary', '#b8b39f')};")
        right_layout.addWidget(right_title)

        # Quick Toggle Switch Buttons
        btn_box = QHBoxLayout()
        btn_box.setSpacing(6)

        self.btn_toggle_tts = QPushButton("语音播报: 开")
        self.btn_toggle_tts.setCheckable(True)
        self.btn_toggle_tts.clicked.connect(self.toggle_tts)
        btn_box.addWidget(self.btn_toggle_tts)

        self.btn_toggle_sfx = QPushButton("复古音效: 开")
        self.btn_toggle_sfx.setCheckable(True)
        self.btn_toggle_sfx.clicked.connect(self.toggle_sfx)
        btn_box.addWidget(self.btn_toggle_sfx)

        right_layout.addLayout(btn_box)

        self.btn_toggle_notify = QPushButton("桌面通知: 开")
        self.btn_toggle_notify.setCheckable(True)
        self.btn_toggle_notify.clicked.connect(self.toggle_notify)
        right_layout.addWidget(self.btn_toggle_notify)

        # Master volume slider
        vol_box = QHBoxLayout()
        lbl_vol_icon = QLabel("音量:")
        lbl_vol_icon.setStyleSheet(f"color: {self.colors.get('text_dim', '#949289')};")
        self.slider_quick_vol = QSlider(Qt.Horizontal)
        self.slider_quick_vol.setRange(0, 100)
        self.slider_quick_vol.valueChanged.connect(self.on_quick_vol_changed)
        self.lbl_quick_vol = QLabel("80%")
        self.lbl_quick_vol.setFixedWidth(36)
        self.lbl_quick_vol.setStyleSheet(f"color: {self.colors.get('accent_gold', '#c4ba97')}; font-weight: bold;")
        vol_box.addWidget(lbl_vol_icon)
        vol_box.addWidget(self.slider_quick_vol)
        vol_box.addWidget(self.lbl_quick_vol)
        right_layout.addLayout(vol_box)

        # VIP Gift / Superchat feed
        lbl_vip = QLabel("高能榜与醒目留言:")
        lbl_vip.setStyleSheet(f"font-weight: bold; color: {self.colors.get('accent_gold', '#c4ba97')}; margin-top: 4px;")
        right_layout.addWidget(lbl_vip)

        self.vip_list = QListWidget()
        self.vip_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {self.colors.get('bg_dark', '#1c1b18')};
                border: 1px solid {self.colors.get('border', '#3d3c34')};
                padding: 2px;
            }}
            QListWidget::item {{
                padding: 4px;
                border-bottom: 1px solid {self.colors.get('border', '#3d3c34')};
            }}
        """)
        right_layout.addWidget(self.vip_list, 1)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter, 1)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 - 输入房间号后点击连接即可开启像素直播助手")

    def load_config_into_ui(self):
        room_id = self.config_manager.get("room_id", 544853)
        self.room_input.setText(str(room_id))

        tts_enabled = self.config_manager.get("tts.enabled", True)
        self.btn_toggle_tts.setChecked(tts_enabled)
        self.btn_toggle_tts.setText(f"语音播报: {'开' if tts_enabled else '关'}")

        sfx_enabled = self.config_manager.get("audio.sound_effects_enabled", True)
        self.btn_toggle_sfx.setChecked(sfx_enabled)
        self.btn_toggle_sfx.setText(f"复古音效: {'开' if sfx_enabled else '关'}")

        notify_enabled = self.config_manager.get("notification.enabled", True)
        self.btn_toggle_notify.setChecked(notify_enabled)
        self.btn_toggle_notify.setText(f"桌面通知: {'开' if notify_enabled else '关'}")

        master_vol = self.config_manager.get("audio.master_volume", 80)
        self.slider_quick_vol.setValue(master_vol)
        self.lbl_quick_vol.setText(f"{master_vol}%")
        self.sound_manager.set_master_volume(master_vol)

    def update_live_timer(self):
        if self.session_start_time:
            elapsed = int(time.time() - self.session_start_time)
            hrs = elapsed // 3600
            mins = (elapsed % 3600) // 60
            secs = elapsed % 60
            self.badge_duration.set_badge(f"[ 时长: {hrs:02d}:{mins:02d}:{secs:02d} ]")

    def on_quick_vol_changed(self, val):
        self.lbl_quick_vol.setText(f"{val}%")
        self.sound_manager.set_master_volume(val)
        self.config_manager.set("audio.master_volume", val)

    def toggle_connection(self):
        if self.ws_client and self.ws_client.is_running:
            self.ws_client.stop()
            self.live_timer.stop()
            self.connect_btn.setText("连接直播间")
            self.status_badge.set_badge("[ 状态: 已断开 ]", bg_color=self.colors.get('bg_card', '#2a2924'), text_color=self.colors.get('text_dim', '#949289'))
        else:
            room_str = self.room_input.text().strip()
            if not room_str.isdigit() or int(room_str) <= 0:
                QMessageBox.warning(self, "错误", "请输入有效的 Bilibili 直播间数字房间号")
                return

            room_id = int(room_str)
            self.config_manager.set("room_id", room_id)

            self.session_start_time = time.time()
            self.live_timer.start(1000)

            self.status_badge.set_badge("[ 状态: 连接中... ]", bg_color=self.colors.get('accent_gold', '#c4ba97'), text_color=self.colors.get('bg_dark', '#1c1b18'))
            self.connect_btn.setText("断开连接")

            cookie = self.config_manager.get("bilibili_cookie", "")
            self.ws_client = BilibiliWSClient(room_id, cookie=cookie)
            self.ws_client.connected_signal.connect(self.on_ws_connected)
            self.ws_client.disconnected_signal.connect(self.on_ws_disconnected)
            self.ws_client.danmaku_signal.connect(self.on_danmaku_received)
            self.ws_client.gift_signal.connect(self.on_gift_received)
            self.ws_client.superchat_signal.connect(self.on_superchat_received)
            self.ws_client.guard_signal.connect(self.on_guard_received)
            self.ws_client.interact_signal.connect(self.on_interact_received)
            self.ws_client.popularity_signal.connect(self.on_popularity_updated)

            self.ws_thread = BilibiliWSThread(self.ws_client)
            self.ws_thread.start()

    @Slot(str)
    def on_ws_connected(self, room_id):
        self.status_badge.set_badge("[ 状态: 已连接 ]", bg_color=self.colors.get('accent_green', '#8ea382'), text_color=self.colors.get('bg_dark', '#1c1b18'))
        cookie_tip = " (已登录认证)" if self.config_manager.get("bilibili_cookie", "") else " (游客模式)"
        self.status_bar.showMessage(f"成功连接至 Bilibili 直播间: {room_id}{cookie_tip}")

    @Slot(str)
    def on_ws_disconnected(self, reason):
        self.live_timer.stop()
        self.connect_btn.setText("连接直播间")
        self.status_badge.set_badge("[ 状态: 已断开 ]", bg_color=self.colors.get('accent_rose', '#c47079'), text_color=self.colors.get('bg_dark', '#1c1b18'))
        self.status_bar.showMessage(f"直播间连接断开: {reason}")

    @Slot(int)
    def on_popularity_updated(self, pop):
        self.pop_label.setText(f"人气: {pop}")

    def is_filtered(self, text):
        blocked_kw = self.config_manager.get("filter.blocked_keywords", [])
        for kw in blocked_kw:
            if kw and kw in text:
                return True
        return False

    @Slot(dict)
    def on_danmaku_received(self, data):
        data["type"] = "danmaku"
        if self.is_filtered(data.get("text", "")):
            return

        self.danmaku_count += 1
        self.badge_dm_stat.set_badge(f"[ 弹幕: {self.danmaku_count} 条 ]")
        self.session_records.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": "danmaku",
            "user": data.get("user", ""),
            "content": data.get("text", ""),
            "value": ""
        })

        self.append_feed_item(data)

        # Desktop notification with Avatar
        self.desktop_notifier.send_notification(
            f"{data.get('user', '观众')}",
            data.get("text", ""),
            avatar_url=data.get("avatar", ""),
            msg_type="danmaku"
        )

        # TTS speech
        if self.config_manager.get("tts.enabled", True) and self.config_manager.get("tts.read_danmaku", True):
            tmpl = self.config_manager.get("tts.danmaku_template", "{user}说：{msg}")
            speech_text = tmpl.format(user=data.get("user", ""), msg=data.get("text", ""))
            self.queue_tts(speech_text)

    @Slot(dict)
    def on_gift_received(self, data):
        data["type"] = "gift"
        self.gift_count += 1
        price = data.get("price", 0)
        self.battery_total += price
        self.badge_gift_stat.set_badge(f"[ 礼物: {self.gift_count} (¥{self.battery_total:.1f}) ]")

        self.session_records.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": "gift",
            "user": data.get("user", ""),
            "content": f"{data.get('gift_name')} x {data.get('num')}",
            "value": f"¥{price}"
        })

        self.append_feed_item(data)

        # Desktop notification with Avatar
        self.desktop_notifier.send_notification(
            f"收到礼物 - {data.get('user')}",
            f"送出 {data.get('gift_name')} x {data.get('num')}",
            avatar_url=data.get("avatar", ""),
            msg_type="gift"
        )

        if self.config_manager.get("audio.sound_effects_enabled", True):
            self.sound_manager.play_sfx("coin")

        if self.config_manager.get("tts.enabled", True) and self.config_manager.get("tts.read_gifts", True):
            tmpl = self.config_manager.get("tts.gift_template", "感谢 {user} 送出的 {gift_name} x {num}")
            speech_text = tmpl.format(user=data.get("user", ""), gift_name=data.get("gift_name", ""), num=data.get("num", 1))
            self.queue_tts(speech_text)

        item = QListWidgetItem(f"[ 礼物 ] {data.get('user')}: {data.get('gift_name')} x {data.get('num')}")
        item.setForeground(Qt.yellow)
        self.vip_list.insertItem(0, item)

    @Slot(dict)
    def on_superchat_received(self, data):
        data["type"] = "superchat"
        price = data.get("price", 0)
        self.sc_total += price
        self.badge_sc_stat.set_badge(f"[ SC: ¥{self.sc_total:.1f} ]")

        self.session_records.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": "superchat",
            "user": data.get("user", ""),
            "content": data.get("text", ""),
            "value": f"¥{price}"
        })

        self.append_feed_item(data)

        # Desktop notification with Avatar (high priority)
        self.desktop_notifier.send_notification(
            f"醒目留言 [¥{data.get('price')}] - {data.get('user')}",
            data.get("text", ""),
            avatar_url=data.get("avatar", ""),
            msg_type="superchat"
        )

        if self.config_manager.get("audio.sound_effects_enabled", True):
            self.sound_manager.play_sfx("alert")

        if self.config_manager.get("tts.enabled", True) and self.config_manager.get("tts.read_superchat", True):
            tmpl = self.config_manager.get("tts.sc_template", "感谢 {user} 的 {price} 元醒目留言：{msg}")
            speech_text = tmpl.format(user=data.get("user", ""), price=data.get("price", 0), msg=data.get("text", ""))
            self.queue_tts(speech_text)

        item = QListWidgetItem(f"[ SC ¥{data.get('price')} ] {data.get('user')}: {data.get('text')}")
        item.setForeground(Qt.red)
        self.vip_list.insertItem(0, item)

    @Slot(dict)
    def on_guard_received(self, data):
        data["type"] = "guard"
        self.guard_count += 1
        self.badge_guard_stat.set_badge(f"[ 舰队: {self.guard_count} 舰 ]")

        self.session_records.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "type": "guard",
            "user": data.get("user", ""),
            "content": f"开通 {data.get('gift_name')}",
            "value": ""
        })

        self.append_feed_item(data)

        # Desktop notification with Avatar
        self.desktop_notifier.send_notification(
            f"大航海开通 - {data.get('user')}",
            f"开通了 {data.get('gift_name')}",
            avatar_url=data.get("avatar", ""),
            msg_type="guard"
        )

        if self.config_manager.get("audio.sound_effects_enabled", True):
            self.sound_manager.play_sfx("levelup")

        item = QListWidgetItem(f"[ 舰长 ] {data.get('user')} 开通了 {data.get('gift_name')}")
        item.setForeground(Qt.cyan)
        self.vip_list.insertItem(0, item)

    @Slot(dict)
    def on_interact_received(self, data):
        data["type"] = "interact"
        self.append_feed_item(data)

    def append_feed_item(self, data):
        card = DanmakuCardWidget(data)
        count = self.danmaku_layout.count()
        self.danmaku_layout.insertWidget(count - 1, card)

        max_items = 40
        while self.danmaku_layout.count() > max_items + 1:
            item = self.danmaku_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

        QTimer.singleShot(50, lambda: self.danmaku_scroll.verticalScrollBar().setValue(
            self.danmaku_scroll.verticalScrollBar().maximum()
        ))

    def clear_feed(self):
        while self.danmaku_layout.count() > 1:
            item = self.danmaku_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self.vip_list.clear()

    def export_session_data(self):
        if not self.session_records:
            QMessageBox.information(self, "提示", "当前暂无弹幕记录可导出")
            return

        export_dir = Path.home() / "Downloads"
        export_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        room_id = self.config_manager.get("room_id", 0)
        export_file = export_dir / f"bilibili_live_{room_id}_{ts}.csv"

        try:
            with open(export_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["time", "type", "user", "content", "value"])
                writer.writeheader()
                writer.writerows(self.session_records)

            self.status_bar.showMessage(f"成功导出 {len(self.session_records)} 条记录至 {export_file}")
            QMessageBox.information(self, "导出成功", f"弹幕与礼物明细已保存至:\n{export_file}")
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"导出文件错误: {e}")

    def toggle_tts(self):
        enabled = self.btn_toggle_tts.isChecked()
        self.config_manager.set("tts.enabled", enabled)
        self.btn_toggle_tts.setText(f"语音播报: {'开' if enabled else '关'}")

    def toggle_sfx(self):
        enabled = self.btn_toggle_sfx.isChecked()
        self.config_manager.set("audio.sound_effects_enabled", enabled)
        self.btn_toggle_sfx.setText(f"复古音效: {'开' if enabled else '关'}")

    def toggle_notify(self):
        enabled = self.btn_toggle_notify.isChecked()
        self.config_manager.set("notification.enabled", enabled)
        self.btn_toggle_notify.setText(f"桌面通知: {'开' if enabled else '关'}")

    def open_settings(self):
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec():
            self.load_config_into_ui()

    def start_tts_queue_worker(self):
        import threading
        self.tts_queue = asyncio.Queue()

        def _worker_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.tts_loop = loop

            async def _process_queue():
                while True:
                    text = await self.tts_queue.get()
                    try:
                        voice = self.config_manager.get("tts.voice", "zh-CN-XiaoxiaoNeural")
                        audio_path = await self.tts_engine.generate_speech(text, voice=voice)
                        if audio_path:
                            self.sound_manager.play_tts_file(audio_path)
                            while self.sound_manager.is_playing:
                                await asyncio.sleep(0.1)
                    except Exception as e:
                        print(f"[TTS] Error: {e}")
                    finally:
                        self.tts_queue.task_done()

            loop.run_until_complete(_process_queue())

        threading.Thread(target=_worker_thread, daemon=True).start()

    def queue_tts(self, text):
        if self.tts_loop and self.tts_queue:
            self.tts_loop.call_soon_threadsafe(self.tts_queue.put_nowait, text)
