import asyncio
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QFrame, QSplitter, QStatusBar,
    QMessageBox, QApplication, QScrollArea
)
from PySide6.QtCore import Qt, Slot, QTimer, QFileSystemWatcher
from core.bilibili_ws import BilibiliWSClient, BilibiliWSThread
from core.edge_tts import EdgeTTS
from core.sound_manager import SoundManager
from ui.pixel_widgets import PixelBadge, DanmakuCardWidget, PixelCard
from ui.overlay_window import DesktopOverlayWindow
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
        self.overlay_window = None

        self.tts_loop = None
        self.tts_queue = None

        self.setWindowTitle("Bilibili Pixel Danmaku (复古像素弹幕助手)")
        self.resize(860, 600)

        self.init_ui()
        self.init_overlay()
        self.load_config_into_ui()

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
            self.status_bar.showMessage("已自动同步应用 Morandi 主题色彩配置")
            self.pop_label.setStyleSheet(f"color: {self.colors.get('accent_gold', '#e0af68')}; font-weight: bold;")
            if self.ws_client and self.ws_client.is_running:
                self.status_badge.set_badge("已连接", bg_color=self.colors.get('accent_green', '#9ece6a'), text_color=self.colors.get('bg_dark', '#101018'))
            else:
                self.status_badge.set_badge("已断开", bg_color=self.colors.get('bg_card', '#414868'), text_color=self.colors.get('text', '#c0caf5'))
        except Exception as e:
            print(f"[Theme] Reload failed: {e}")

    def init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # Top Control Bar
        top_card = PixelCard()
        top_layout = QHBoxLayout(top_card)
        top_layout.setContentsMargins(10, 8, 10, 8)
        top_layout.setSpacing(10)

        lbl_room = QLabel("直播间号:")
        lbl_room.setStyleSheet(f"font-weight: bold; color: {self.colors.get('accent_blue', '#7aa2f7')};")
        self.room_input = QLineEdit()
        self.room_input.setPlaceholderText("例如: 544853")
        self.room_input.setMaximumWidth(160)

        self.connect_btn = QPushButton("连接直播间")
        self.connect_btn.clicked.connect(self.toggle_connection)

        self.status_badge = PixelBadge("已断开", bg_color=self.colors.get('bg_card', '#414868'), text_color=self.colors.get('text', '#c0caf5'))
        self.pop_label = QLabel("人气: 0")
        self.pop_label.setStyleSheet(f"color: {self.colors.get('accent_gold', '#e0af68')}; font-weight: bold;")

        top_layout.addWidget(lbl_room)
        top_layout.addWidget(self.room_input)
        top_layout.addWidget(self.connect_btn)
        top_layout.addWidget(self.status_badge)
        top_layout.addStretch()
        top_layout.addWidget(self.pop_label)

        btn_settings = QPushButton("⚙ 设置")
        btn_settings.clicked.connect(self.open_settings)
        top_layout.addWidget(btn_settings)

        main_layout.addWidget(top_card)

        # Center Splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left: Danmaku Realtime Feed List
        left_panel = PixelCard()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)

        feed_title_box = QHBoxLayout()
        feed_title = QLabel("实时弹幕数据流 (Realtime Stream)")
        feed_title.setStyleSheet(f"font-weight: bold; color: {self.colors.get('primary', '#7aa2f7')};")
        self.btn_clear = QPushButton("清屏")
        self.btn_clear.clicked.connect(self.clear_feed)
        feed_title_box.addWidget(feed_title)
        feed_title_box.addStretch()
        feed_title_box.addWidget(self.btn_clear)
        left_layout.addLayout(feed_title_box)

        self.danmaku_scroll = QScrollArea()
        self.danmaku_scroll.setWidgetResizable(True)
        self.danmaku_container = QWidget()
        self.danmaku_layout = QVBoxLayout(self.danmaku_container)
        self.danmaku_layout.setContentsMargins(4, 4, 4, 4)
        self.danmaku_layout.setSpacing(6)
        self.danmaku_layout.addStretch()
        self.danmaku_scroll.setWidget(self.danmaku_container)

        left_layout.addWidget(self.danmaku_scroll)
        splitter.addWidget(left_panel)

        # Right: Quick Controls & Gift Wall
        right_panel = PixelCard()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(8, 8, 8, 8)

        right_title = QLabel("控制中心与贵宾区")
        right_title.setStyleSheet(f"font-weight: bold; color: {self.colors.get('accent_purple', '#bb9af7')};")
        right_layout.addWidget(right_title)

        self.btn_toggle_tts = QPushButton("语音播报: 开")
        self.btn_toggle_tts.setCheckable(True)
        self.btn_toggle_tts.clicked.connect(self.toggle_tts)
        right_layout.addWidget(self.btn_toggle_tts)

        self.btn_toggle_sfx = QPushButton("复古音效: 开")
        self.btn_toggle_sfx.setCheckable(True)
        self.btn_toggle_sfx.clicked.connect(self.toggle_sfx)
        right_layout.addWidget(self.btn_toggle_sfx)

        self.btn_toggle_overlay = QPushButton("桌面悬浮窗: 关")
        self.btn_toggle_overlay.setCheckable(True)
        self.btn_toggle_overlay.clicked.connect(self.toggle_overlay)
        right_layout.addWidget(self.btn_toggle_overlay)

        # VIP Gift / Superchat feed
        lbl_vip = QLabel("高能榜与醒目留言 (SC/Gifts):")
        lbl_vip.setStyleSheet(f"font-weight: bold; color: {self.colors.get('accent_gold', '#e0af68')}; margin-top: 10px;")
        right_layout.addWidget(lbl_vip)

        self.vip_list = QListWidget()
        self.vip_list.setStyleSheet(f"background-color: {self.colors.get('bg_dark', '#1a1b26')}; border: 2px solid {self.colors.get('border_dark', '#16161e')};")
        right_layout.addWidget(self.vip_list, 1)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter, 1)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪 - 输入房间号后点击连接即可开启像素直播助手")

    def init_overlay(self):
        self.overlay_window = DesktopOverlayWindow(self.config_manager)

    def load_config_into_ui(self):
        room_id = self.config_manager.get("room_id", 544853)
        self.room_input.setText(str(room_id))

        tts_enabled = self.config_manager.get("tts.enabled", True)
        self.btn_toggle_tts.setChecked(tts_enabled)
        self.btn_toggle_tts.setText(f"语音播报: {'开' if tts_enabled else '关'}")

        sfx_enabled = self.config_manager.get("audio.sound_effects_enabled", True)
        self.btn_toggle_sfx.setChecked(sfx_enabled)
        self.btn_toggle_sfx.setText(f"复古音效: {'开' if sfx_enabled else '关'}")

        overlay_enabled = self.config_manager.get("overlay.enabled", False)
        self.btn_toggle_overlay.setChecked(overlay_enabled)
        self.btn_toggle_overlay.setText(f"桌面悬浮窗: {'开' if overlay_enabled else '关'}")

        master_vol = self.config_manager.get("audio.master_volume", 80)
        self.sound_manager.set_master_volume(master_vol)

    def toggle_connection(self):
        if self.ws_client and self.ws_client.is_running:
            self.ws_client.stop()
            self.connect_btn.setText("连接直播间")
            self.status_badge.set_badge("已断开", bg_color=self.colors.get('bg_card', '#414868'), text_color=self.colors.get('text', '#c0caf5'))
        else:
            room_str = self.room_input.text().strip()
            if not room_str.isdigit() or int(room_str) <= 0:
                QMessageBox.warning(self, "错误", "请输入有效的 Bilibili 直播间数字房间号！")
                return

            room_id = int(room_str)
            self.config_manager.set("room_id", room_id)

            self.status_badge.set_badge("正在连接...", bg_color=self.colors.get('accent_gold', '#e0af68'), text_color=self.colors.get('bg_dark', '#101018'))
            self.connect_btn.setText("断开连接")

            self.ws_client = BilibiliWSClient(room_id)
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
        self.status_badge.set_badge("已连接", bg_color=self.colors.get('accent_green', '#9ece6a'), text_color=self.colors.get('bg_dark', '#101018'))
        self.status_bar.showMessage(f"成功连接至 Bilibili 房间: {room_id}")

    @Slot(str)
    def on_ws_disconnected(self, reason):
        self.connect_btn.setText("连接直播间")
        self.status_badge.set_badge("已断开", bg_color=self.colors.get('accent_rose', '#f7768e'), text_color=self.colors.get('bg_dark', '#101018'))
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

        self.append_feed_item(data)

        if self.config_manager.get("tts.enabled", True) and self.config_manager.get("tts.read_danmaku", True):
            tmpl = self.config_manager.get("tts.danmaku_template", "{user}说：{msg}")
            speech_text = tmpl.format(user=data.get("user", ""), msg=data.get("text", ""))
            self.queue_tts(speech_text)

    @Slot(dict)
    def on_gift_received(self, data):
        data["type"] = "gift"
        self.append_feed_item(data)

        if self.config_manager.get("audio.sound_effects_enabled", True):
            self.sound_manager.play_sfx("coin")

        if self.config_manager.get("tts.enabled", True) and self.config_manager.get("tts.read_gifts", True):
            tmpl = self.config_manager.get("tts.gift_template", "感谢 {user} 送出的 {gift_name} x {num}")
            speech_text = tmpl.format(user=data.get("user", ""), gift_name=data.get("gift_name", ""), num=data.get("num", 1))
            self.queue_tts(speech_text)

        item = QListWidgetItem(f"🎁 {data.get('user')}: {data.get('gift_name')} x {data.get('num')}")
        item.setForeground(Qt.yellow)
        self.vip_list.insertItem(0, item)

    @Slot(dict)
    def on_superchat_received(self, data):
        data["type"] = "superchat"
        self.append_feed_item(data)

        if self.config_manager.get("audio.sound_effects_enabled", True):
            self.sound_manager.play_sfx("alert")

        if self.config_manager.get("tts.enabled", True) and self.config_manager.get("tts.read_superchat", True):
            tmpl = self.config_manager.get("tts.sc_template", "感谢 {user} 的 {price} 元醒目留言：{msg}")
            speech_text = tmpl.format(user=data.get("user", ""), price=data.get("price", 0), msg=data.get("text", ""))
            self.queue_tts(speech_text)

        item = QListWidgetItem(f"💰 [¥{data.get('price')}] {data.get('user')}: {data.get('text')}")
        item.setForeground(Qt.red)
        self.vip_list.insertItem(0, item)

    @Slot(dict)
    def on_guard_received(self, data):
        data["type"] = "guard"
        self.append_feed_item(data)

        if self.config_manager.get("audio.sound_effects_enabled", True):
            self.sound_manager.play_sfx("levelup")

        item = QListWidgetItem(f"⚓ {data.get('user')} 开通了 {data.get('gift_name')}")
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

        max_items = self.config_manager.get("overlay.max_danmaku", 30)
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

    def toggle_tts(self):
        enabled = self.btn_toggle_tts.isChecked()
        self.config_manager.set("tts.enabled", enabled)
        self.btn_toggle_tts.setText(f"语音播报: {'开' if enabled else '关'}")

    def toggle_sfx(self):
        enabled = self.btn_toggle_sfx.isChecked()
        self.config_manager.set("audio.sound_effects_enabled", enabled)
        self.btn_toggle_sfx.setText(f"复古音效: {'开' if enabled else '关'}")

    def toggle_overlay(self):
        enabled = self.btn_toggle_overlay.isChecked()
        self.config_manager.set("overlay.enabled", enabled)
        self.btn_toggle_overlay.setText(f"桌面悬浮窗: {'开' if enabled else '关'}")
        if enabled:
            self.overlay_window.show()
        else:
            self.overlay_window.hide()

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
