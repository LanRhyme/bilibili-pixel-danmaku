import hashlib
import logging
import ssl
import sys
import threading
import urllib.request
from contextlib import suppress
from pathlib import Path

from core.notifier_linux import LinuxNotifier
from core.notifier_macos import MacOSNotifier

AVATAR_CACHE_DIR = Path.home() / ".cache" / "bilibili-danmaku" / "avatars"
AVATAR_CACHE_DIR.mkdir(parents=True, exist_ok=True)

try:
    import certifi

    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _SSL_CONTEXT = None


class DesktopNotifier:

    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self._backend: LinuxNotifier | MacOSNotifier | None = self._create_backend()

    @staticmethod
    def _create_backend():
        if sys.platform == "darwin":
            backend = MacOSNotifier()
        elif sys.platform.startswith("linux"):
            backend = LinuxNotifier()
        else:
            return None
        return backend if backend.is_available() else None

    def set_activation_callback(self, callback):
        if self._backend is not None:
            self._backend.set_activation_callback(callback)

    def send_notification(
        self, title, message, avatar_url="", msg_type="danmaku", expire_ms=4000
    ):
        if self._backend is None:
            return
        if not self._is_notify_enabled(msg_type):
            return

        urgency = "critical" if msg_type in ("superchat", "guard") else "normal"

        if avatar_url:
            local_file = self._avatar_cache_path(avatar_url)
            if local_file.exists():
                self._backend.send(
                    title, message, str(local_file), urgency, expire_ms, msg_type
                )
            else:
                # Async download and send
                def _fetch_and_send():
                    if self._backend is None:
                        return
                    path = None
                    try:
                        req = urllib.request.Request(
                            avatar_url,
                            headers={
                                "User-Agent": "Mozilla/5.0",
                                "Referer": "https://live.bilibili.com/",
                            },
                        )
                        if _SSL_CONTEXT is not None:
                            with urllib.request.urlopen(
                                req, timeout=3, context=_SSL_CONTEXT
                            ) as resp:
                                data = resp.read()
                        else:
                            with urllib.request.urlopen(req, timeout=3) as resp:
                                data = resp.read()
                        target = self._avatar_cache_path(avatar_url)
                        target.write_bytes(data)
                        path = str(target)
                    except Exception as e:
                        pass
                    self._backend.send(
                        title, message, path, urgency, expire_ms, msg_type
                    )

                threading.Thread(target=_fetch_and_send, daemon=True).start()
                return
        else:
            local_file = None

        self._backend.send(
            title,
            message,
            str(local_file) if local_file else None,
            urgency,
            expire_ms,
            msg_type,
        )

    def _is_notify_enabled(self, msg_type):
        if not self.config_manager:
            return True
        cm = self.config_manager
        with suppress(Exception):
            if not cm.get("notification.enabled", True):
                return False
            key = {
                "danmaku": "notification.danmaku",
                "chat": "notification.danmaku",
                "gift": "notification.gifts",
                "superchat": "notification.superchat",
                "guard": "notification.guard",
            }.get(msg_type)
            if key is not None and not cm.get(key, True):
                return False
        return True

    @staticmethod
    def _avatar_cache_path(avatar_url):
        url_hash = hashlib.sha256(avatar_url.encode("utf-8")).hexdigest()
        return AVATAR_CACHE_DIR / f"{url_hash}.jpg"
