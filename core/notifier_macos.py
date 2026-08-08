import sys
import threading
import uuid
from contextlib import suppress

if sys.platform == "darwin":
    from Foundation import NSObject

    class _MacOSDelegate(NSObject):
        def userNotificationCenter_didReceiveNotificationResponse_withCompletionHandler_(
            self, center, response, done
        ):
            cb = self.notifier._activation_callback
            if cb is not None:
                import dispatch

                dispatch.dispatch_async(dispatch.dispatch_get_main_queue(), cb)
            done()

else:

    class _MacOSDelegate:
        pass


class MacOSNotifier:
    def __init__(self):
        self._available = sys.platform == "darwin"
        self._center = None
        self._delegate = None
        self._activation_callback = None
        self._lock = threading.Lock()

    def is_available(self):
        return self._available

    def set_activation_callback(self, callback):
        self._activation_callback = callback

    def send(
        self,
        title,
        message,
        avatar_path=None,
        urgency="normal",
        expire_ms=0,
        msg_type="danmaku",
    ):
        self._ensure_ready()
        import UserNotifications as UN

        content = UN.UNMutableNotificationContent.alloc().init()
        content.setTitle_(title)
        content.setBody_(message)
        content.setThreadIdentifier_(msg_type)

        if urgency == "critical":
            with suppress(Exception):
                content.interruptionLevel = 2

        if avatar_path:
            with suppress(Exception):
                from Foundation import NSURL

                url = NSURL.fileURLWithPath_(avatar_path)
                result = UN.UNNotificationAttachment.attachmentWithIdentifier_URL_options_error_(
                    f"att-{uuid.uuid4().hex}", url, None, None
                )
                att, err = result if isinstance(result, tuple) else (result, None)
                if att is not None:
                    content.setAttachments_([att])

        request = UN.UNNotificationRequest.requestWithIdentifier_content_trigger_(
            f"n-{uuid.uuid4().hex}",
            content,
            UN.UNTimeIntervalNotificationTrigger.triggerWithTimeInterval_repeats_(
                0.1, False
            ),
        )
        self._center.addNotificationRequest_withCompletionHandler_(
            request, lambda e: None
        )

    def _ensure_ready(self):
        if self._center is not None:
            return
        with self._lock:
            if self._center is not None:
                return
            import UserNotifications as UN

            delegate = _MacOSDelegate.alloc().init()
            delegate.notifier = self
            center = UN.UNUserNotificationCenter.currentNotificationCenter()
            center.setDelegate_(delegate)
            center.requestAuthorizationWithOptions_completionHandler_(
                UN.UNAuthorizationOptionAlert | UN.UNAuthorizationOptionSound,
                lambda granted, error: None,
            )
            self._center = center
            self._delegate = delegate
