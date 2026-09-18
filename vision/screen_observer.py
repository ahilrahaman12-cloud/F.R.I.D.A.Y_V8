"""Background screen observer that keeps only the newest frame in memory."""

import threading
import time
from typing import Any

import pyautogui


class ScreenObserver:
    """Capture the desktop on an interval without writing frames to disk."""

    def __init__(self, interval_seconds: float) -> None:
        self.interval_seconds = interval_seconds
        self._lock = threading.Lock()
        self._latest_image: Any | None = None
        self._captured_at: float | None = None
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self.capture_once()
        self._thread = threading.Thread(target=self._run, name="friday-screen-observer", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def capture_once(self) -> None:
        try:
            image = pyautogui.screenshot()
        except Exception:
            return
        with self._lock:
            self._latest_image = image
            self._captured_at = time.time()

    def latest_image(self) -> Any | None:
        with self._lock:
            return self._latest_image.copy() if self._latest_image is not None else None

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "running": bool(self._thread and self._thread.is_alive()),
                "captured_at": self._captured_at,
                "interval_seconds": self.interval_seconds,
            }

    def _run(self) -> None:
        while not self._stop_event.wait(self.interval_seconds):
            self.capture_once()
