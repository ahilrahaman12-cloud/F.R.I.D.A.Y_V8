"""Concrete, user-directed Windows desktop operations."""

import os
import shutil
import time
from pathlib import Path
from typing import Any

import psutil
import pyautogui
import pygetwindow as window_api

from config import WORKSPACE_DIR


class DesktopController:
    """Performs one explicit desktop action at a time."""

    def __init__(self) -> None:
        pyautogui.PAUSE = 0.1

    @staticmethod
    def _result(message: str, **details: Any) -> dict[str, Any]:
        return {"status": "SUCCESS", "message": message, **details}

    def launch_application(self, app_name: str) -> dict[str, Any]:
        app_name = app_name.strip()
        if not app_name:
            return {"error": "Application name cannot be empty."}
        pyautogui.press("win")
        time.sleep(0.3)
        pyautogui.write(app_name, interval=0.02)
        pyautogui.press("enter")
        return self._result(f"Launching {app_name}.")

    def close_application(self, app_name: str) -> dict[str, Any]:
        target = app_name.strip().lower()
        if not target:
            return {"error": "Specify an application to close."}
        closed = []
        for process in psutil.process_iter(["pid", "name"]):
            try:
                process_name = (process.info["name"] or "").lower()
                if target in process_name:
                    process.terminate()
                    closed.append(process.info["name"])
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
        if not closed:
            return {"error": f"No running process matched '{app_name}'."}
        return self._result(f"Closing {app_name}.", processes=closed)

    def type_text(self, text: str) -> dict[str, Any]:
        if not text:
            return {"error": "Text cannot be empty."}
        pyautogui.write(text, interval=0.03)
        return self._result("Typed the requested text.")

    def press_key(self, key: str) -> dict[str, Any]:
        key = key.strip().lower()
        if key not in pyautogui.KEYBOARD_KEYS:
            return {"error": f"Unsupported keyboard key: {key}"}
        pyautogui.press(key)
        return self._result(f"Pressed {key}.")

    def hotkey(self, keys: list[str]) -> dict[str, Any]:
        normalized = [key.strip().lower() for key in keys]
        if not 2 <= len(normalized) <= 4 or any(key not in pyautogui.KEYBOARD_KEYS for key in normalized):
            return {"error": "Provide two to four valid keyboard keys."}
        pyautogui.hotkey(*normalized)
        return self._result("Executed keyboard shortcut.")

    def move_mouse(self, x: int, y: int) -> dict[str, Any]:
        current_x, current_y = pyautogui.position()
        distance = ((x - current_x) ** 2 + (y - current_y) ** 2) ** 0.5
        pyautogui.moveTo(x, y, duration=min(0.8, max(0.15, distance / 1_500)))
        return self._result("Moved the pointer.", x=x, y=y)

    def click(self, x: int, y: int, button: str = "left") -> dict[str, Any]:
        if button not in {"left", "right", "middle"}:
            return {"error": "Button must be left, right, or middle."}
        pyautogui.click(x=x, y=y, button=button)
        return self._result("Clicked the requested location.", x=x, y=y, button=button)

    def double_click(self, x: int, y: int) -> dict[str, Any]:
        pyautogui.doubleClick(x=x, y=y)
        return self._result("Double-clicked the requested location.", x=x, y=y)

    def right_click(self, x: int, y: int) -> dict[str, Any]:
        return self.click(x, y, button="right")

    def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> dict[str, Any]:
        self.move_mouse(start_x, start_y)
        pyautogui.dragTo(end_x, end_y, duration=0.5, button="left")
        return self._result("Dragged the pointer.")

    def switch_window(self, window_name: str) -> dict[str, Any]:
        target = window_name.strip().lower()
        try:
            for candidate in window_api.getAllWindows():
                if candidate.title and target in candidate.title.lower():
                    candidate.activate()
                    return self._result(f"Switched to {candidate.title}.")
        except Exception as error:
            return {"error": f"Could not switch windows: {error}"}
        return {"error": f"No window matched '{window_name}'."}

    def close_active_window(self) -> dict[str, Any]:
        pyautogui.hotkey("alt", "f4")
        return self._result("Closed the active window.")

    def minimize_all_windows(self) -> dict[str, Any]:
        pyautogui.hotkey("win", "d")
        return self._result("Minimized all windows.")

    def scroll(self, amount: int) -> dict[str, Any]:
        pyautogui.scroll(amount)
        return self._result("Scrolled the active window.", amount=amount)

    def screenshot(self) -> dict[str, Any]:
        screenshots = WORKSPACE_DIR / "screenshots"
        screenshots.mkdir(parents=True, exist_ok=True)
        image_path = screenshots / f"screen-{int(time.time())}.png"
        pyautogui.screenshot().save(image_path)
        return self._result("Captured a screenshot.", path=str(image_path.relative_to(WORKSPACE_DIR)))

    @staticmethod
    def capture_screen_image() -> Any:
        """Return a current screenshot for Gemini vision analysis."""
        return pyautogui.screenshot()

    def screen_context(self) -> dict[str, Any]:
        try:
            active = window_api.getActiveWindow()
            windows = [
                current.title.strip()
                for current in window_api.getAllWindows()
                if current.visible and current.title and current.title.strip()
            ]
            return self._result(
                "Read current screen context.",
                active_window=active.title.strip() if active and active.title else "Unknown",
                open_windows=windows,
            )
        except Exception as error:
            return {"error": f"Could not read window context: {error}"}

    @staticmethod
    def _desktop_item(name: str) -> Path:
        item = Path(name)
        if not name.strip() or item.name != name or item.is_absolute():
            raise ValueError("Use a single file or folder name, not a path.")
        return Path.home() / "Desktop" / item

    def create_desktop_folder(self, folder_name: str) -> dict[str, Any]:
        try:
            path = self._desktop_item(folder_name)
            path.mkdir(exist_ok=True)
            return self._result(f"Desktop folder '{folder_name}' is ready.")
        except (OSError, ValueError) as error:
            return {"error": str(error)}

    def create_desktop_file(self, filename: str, content: str = "") -> dict[str, Any]:
        try:
            path = self._desktop_item(filename)
            path.write_text(content, encoding="utf-8")
            return self._result(f"Desktop file '{filename}' was created.")
        except (OSError, ValueError) as error:
            return {"error": str(error)}

    def delete_desktop_item(self, item_name: str) -> dict[str, Any]:
        try:
            path = self._desktop_item(item_name)
            if not path.exists():
                return {"error": f"'{item_name}' was not found on the Desktop."}
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            return self._result(f"Deleted '{item_name}' from the Desktop.")
        except (OSError, ValueError) as error:
            return {"error": str(error)}
