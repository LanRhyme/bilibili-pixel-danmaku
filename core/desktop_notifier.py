import os
import shutil
import hashlib
import urllib.request
import subprocess
import threading
from pathlib import Path

AVATAR_CACHE_DIR = Path.home() / ".cache" / "bilibili-danmaku" / "avatars"
AVATAR_CACHE_DIR.mkdir(parents=True, exist_ok=True)

class DesktopNotifier:
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.has_notify_send = shutil.which("notify-send") is not None

    def send_notification(self, title, message, avatar_url="", msg_type="danmaku", expire_ms=4000):
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
        if msg_type in ("superchat", "guard"):
            urgency = "critical"

        avatar_path = None
        if avatar_url:
            url_hash = hashlib.md5(avatar_url.encode('utf-8')).hexdigest()
            local_file = AVATAR_CACHE_DIR / f"{url_hash}.jpg"
            if local_file.exists():
                avatar_path = str(local_file)
            else:
                # Async download and send
                def _fetch_and_notify():
                    try:
                        req = urllib.request.Request(
                            avatar_url,
                            headers={
                                "User-Agent": "Mozilla/5.0",
                                "Referer": "https://live.bilibili.com/"
                            }
                        )
                        with urllib.request.urlopen(req, timeout=3) as resp:
                            data = resp.read()
                            with open(local_file, "wb") as f:
                                f.write(data)
                        self._exec_notify(title, message, str(local_file), urgency, expire_ms)
                    except Exception:
                        self._exec_notify(title, message, None, urgency, expire_ms)
                threading.Thread(target=_fetch_and_notify, daemon=True).start()
                return

        self._exec_notify(title, message, avatar_path, urgency, expire_ms)

    def _exec_notify(self, title, message, avatar_path, urgency, expire_ms):
        cmd = [
            "notify-send",
            "-a", "Bilibili 弹幕助手",
            "-u", urgency,
            "-t", str(expire_ms)
        ]
        if avatar_path and os.path.exists(avatar_path):
            cmd.extend(["-i", avatar_path])

        cmd.extend([title, message])

        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
