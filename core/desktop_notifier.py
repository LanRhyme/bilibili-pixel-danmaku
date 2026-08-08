import shutil
import subprocess
from pathlib import Path

class DesktopNotifier:
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.has_notify_send = shutil.which("notify-send") is not None

    def send_notification(self, title, message, msg_type="danmaku", expire_ms=4000):
        if not self.has_notify_send:
            return

        if self.config_manager:
            if not self.config_manager.get("notification.enabled", True):
                return
            if msg_type in ("danmaku", "chat") and not self.config_manager.get("notification.danmaku", True):
                return
            if msg_type == "gift" and not self.config_manager.get("notification.gifts", True):
                return
            if msg_type == "superchat" and not self.config_manager.get("notification.superchat", True):
                return
            if msg_type == "guard" and not self.config_manager.get("notification.guard", True):
                return

        urgency = "normal"
        if msg_type == "superchat":
            urgency = "critical"
        elif msg_type == "guard":
            urgency = "critical"

        cmd = [
            "notify-send",
            "-a", "Bilibili 弹幕助手",
            "-u", urgency,
            "-t", str(expire_ms),
            title,
            message
        ]

        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
