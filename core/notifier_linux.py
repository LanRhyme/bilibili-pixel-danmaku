import contextlib
import os
import shutil
import subprocess

APP_NAME = "Bilibili 弹幕助手"


class LinuxNotifier:
    def __init__(self):
        self._available = shutil.which("notify-send") is not None

    def is_available(self):
        return self._available

    def set_activation_callback(self, callback):
        pass

    def send(
        self,
        title,
        message,
        avatar_path=None,
        urgency="normal",
        expire_ms=4000,
        msg_type="danmaku",
    ):
        cmd = [
            "notify-send",
            "-a",
            APP_NAME,
            "-u",
            urgency,
            "-t",
            str(expire_ms),
        ]
        if avatar_path and os.path.exists(avatar_path):
            cmd.extend(["-i", avatar_path])
        cmd.extend([title, message])
        with contextlib.suppress(Exception):
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
