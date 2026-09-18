"""Safe local tools exposed to the language model."""

import platform
import sys
from pathlib import Path
from typing import Any

from computer import DesktopController
from config import WORKSPACE_DIR


desktop = DesktopController()


def _workspace_path(requested_path: str) -> Path:
    """Resolve a path and prevent tools from escaping the assistant workspace."""
    workspace = WORKSPACE_DIR.resolve()
    candidate = (workspace / requested_path).resolve()
    if candidate != workspace and workspace not in candidate.parents:
        raise ValueError("Paths must stay inside the F.R.I.D.A.Y. workspace.")
    return candidate


def get_system_info() -> dict[str, str]:
    """Return basic operating system details."""
    return {
        "operating_system": f"{platform.system()} {platform.release()}",
        "python_version": sys.version.split()[0],
        "architecture": platform.machine(),
    }


def list_workspace_files(directory_path: str = ".") -> dict[str, Any]:
    """List a directory inside the dedicated assistant workspace."""
    try:
        directory = _workspace_path(directory_path)
        if not directory.is_dir():
            return {"error": f"Directory does not exist: {directory_path}"}
        return {
            "path": str(directory.relative_to(WORKSPACE_DIR.resolve())) or ".",
            "items": sorted(item.name for item in directory.iterdir()),
        }
    except (OSError, ValueError) as error:
        return {"error": str(error)}


def write_workspace_file(file_path: str, content: str) -> dict[str, Any]:
    """Create or replace a UTF-8 text file inside the assistant workspace."""
    try:
        target = _workspace_path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"status": "SUCCESS", "path": str(target.relative_to(WORKSPACE_DIR.resolve()))}
    except (OSError, ValueError) as error:
        return {"error": str(error)}


def launch_application(app_name: str) -> dict[str, Any]:
    """Launch an installed Windows application using Start search."""
    return desktop.launch_application(app_name)


def close_application(app_name: str) -> dict[str, Any]:
    """Close a named running application."""
    return desktop.close_application(app_name)


def type_text(text: str) -> dict[str, Any]:
    """Type text into the active application."""
    return desktop.type_text(text)


def press_key(key: str) -> dict[str, Any]:
    """Press one keyboard key in the active application."""
    return desktop.press_key(key)


def execute_shortcut(keys: list[str]) -> dict[str, Any]:
    """Press a keyboard shortcut in the active application."""
    return desktop.hotkey(keys)


def move_mouse(x: int, y: int) -> dict[str, Any]:
    """Move the mouse pointer to screen coordinates."""
    return desktop.move_mouse(x, y)


def click(x: int, y: int, button: str = "left") -> dict[str, Any]:
    """Click a screen coordinate."""
    return desktop.click(x, y, button)


def double_click(x: int, y: int) -> dict[str, Any]:
    """Double-click a screen coordinate."""
    return desktop.double_click(x, y)


def right_click(x: int, y: int) -> dict[str, Any]:
    """Right-click a screen coordinate."""
    return desktop.right_click(x, y)


def drag(start_x: int, start_y: int, end_x: int, end_y: int) -> dict[str, Any]:
    """Drag from one screen coordinate to another."""
    return desktop.drag(start_x, start_y, end_x, end_y)


def switch_window(window_name: str) -> dict[str, Any]:
    """Bring a named application window to the foreground."""
    return desktop.switch_window(window_name)


def close_active_window() -> dict[str, Any]:
    """Close the current foreground window."""
    return desktop.close_active_window()


def minimize_all_windows() -> dict[str, Any]:
    """Minimize all visible Windows applications."""
    return desktop.minimize_all_windows()


def scroll(amount: int) -> dict[str, Any]:
    """Scroll the active window."""
    return desktop.scroll(amount)


def take_screenshot() -> dict[str, Any]:
    """Save a screenshot in the assistant workspace."""
    return desktop.screenshot()


def get_screen_context() -> dict[str, Any]:
    """Get the active window and visible application titles."""
    return desktop.screen_context()


def create_desktop_folder(folder_name: str) -> dict[str, Any]:
    """Create a Desktop folder."""
    return desktop.create_desktop_folder(folder_name)


def create_desktop_file(filename: str, content: str = "") -> dict[str, Any]:
    """Create a UTF-8 text file on the Desktop."""
    return desktop.create_desktop_file(filename, content)


def delete_desktop_item(item_name: str) -> dict[str, Any]:
    """Permanently delete one directly named Desktop file or folder."""
    return desktop.delete_desktop_item(item_name)


def available_tools() -> dict[str, Any]:
    """Return the function map used when fulfilling model tool calls."""
    return {
        "get_system_info": get_system_info,
        "list_workspace_files": list_workspace_files,
        "write_workspace_file": write_workspace_file,
        "launch_application": launch_application,
        "close_application": close_application,
        "type_text": type_text,
        "press_key": press_key,
        "execute_shortcut": execute_shortcut,
        "move_mouse": move_mouse,
        "click": click,
        "double_click": double_click,
        "right_click": right_click,
        "drag": drag,
        "switch_window": switch_window,
        "close_active_window": close_active_window,
        "minimize_all_windows": minimize_all_windows,
        "scroll": scroll,
        "take_screenshot": take_screenshot,
        "get_screen_context": get_screen_context,
        "create_desktop_folder": create_desktop_folder,
        "create_desktop_file": create_desktop_file,
        "delete_desktop_item": delete_desktop_item,
    }


def tool_declarations() -> list[Any]:
    """Build Gemini declarations lazily so local tests need no SDK import."""
    from google.genai import types

    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="get_system_info",
                    description="Get basic operating system and Python details.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={}),
                ),
                types.FunctionDeclaration(
                    name="launch_application",
                    description="Launch an installed Windows application, such as Figma, Chrome, or Notepad.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={"app_name": types.Schema(type=types.Type.STRING)}, required=["app_name"]),
                ),
                types.FunctionDeclaration(
                    name="close_application",
                    description="Close a named running Windows application.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={"app_name": types.Schema(type=types.Type.STRING)}, required=["app_name"]),
                ),
                types.FunctionDeclaration(
                    name="type_text",
                    description="Type user-requested text in the currently active application.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={"text": types.Schema(type=types.Type.STRING)}, required=["text"]),
                ),
                types.FunctionDeclaration(
                    name="press_key",
                    description="Press one keyboard key in the active application.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={"key": types.Schema(type=types.Type.STRING)}, required=["key"]),
                ),
                types.FunctionDeclaration(
                    name="execute_shortcut",
                    description="Press a user-requested keyboard shortcut, such as ctrl+s or alt+tab.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={"keys": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING))}, required=["keys"]),
                ),
                types.FunctionDeclaration(
                    name="move_mouse",
                    description="Move the pointer to a screen coordinate.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={"x": types.Schema(type=types.Type.INTEGER), "y": types.Schema(type=types.Type.INTEGER)}, required=["x", "y"]),
                ),
                types.FunctionDeclaration(
                    name="click",
                    description="Click a screen coordinate.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={"x": types.Schema(type=types.Type.INTEGER), "y": types.Schema(type=types.Type.INTEGER), "button": types.Schema(type=types.Type.STRING)}, required=["x", "y"]),
                ),
                types.FunctionDeclaration(
                    name="double_click",
                    description="Double-click a screen coordinate.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={"x": types.Schema(type=types.Type.INTEGER), "y": types.Schema(type=types.Type.INTEGER)}, required=["x", "y"]),
                ),
                types.FunctionDeclaration(
                    name="right_click",
                    description="Right-click a screen coordinate.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={"x": types.Schema(type=types.Type.INTEGER), "y": types.Schema(type=types.Type.INTEGER)}, required=["x", "y"]),
                ),
                types.FunctionDeclaration(
                    name="drag",
                    description="Drag from one screen coordinate to another.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={"start_x": types.Schema(type=types.Type.INTEGER), "start_y": types.Schema(type=types.Type.INTEGER), "end_x": types.Schema(type=types.Type.INTEGER), "end_y": types.Schema(type=types.Type.INTEGER)}, required=["start_x", "start_y", "end_x", "end_y"]),
                ),
                types.FunctionDeclaration(
                    name="switch_window",
                    description="Bring a named application window to the foreground.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={"window_name": types.Schema(type=types.Type.STRING)}, required=["window_name"]),
                ),
                types.FunctionDeclaration(
                    name="close_active_window",
                    description="Close the current foreground window when the user asks.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={}),
                ),
                types.FunctionDeclaration(
                    name="minimize_all_windows",
                    description="Minimize all open Windows applications when the user asks.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={}),
                ),
                types.FunctionDeclaration(
                    name="scroll",
                    description="Scroll the active window; positive is up and negative is down.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={"amount": types.Schema(type=types.Type.INTEGER)}, required=["amount"]),
                ),
                types.FunctionDeclaration(
                    name="take_screenshot",
                    description="Capture the current screen into the assistant workspace.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={}),
                ),
                types.FunctionDeclaration(
                    name="get_screen_context",
                    description="Read the active window title and visible Windows application titles.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={}),
                ),
                types.FunctionDeclaration(
                    name="create_desktop_folder",
                    description="Create a directly named folder on the Windows Desktop.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={"folder_name": types.Schema(type=types.Type.STRING)}, required=["folder_name"]),
                ),
                types.FunctionDeclaration(
                    name="create_desktop_file",
                    description="Create a text file on the Windows Desktop.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={"filename": types.Schema(type=types.Type.STRING), "content": types.Schema(type=types.Type.STRING)}, required=["filename"]),
                ),
                types.FunctionDeclaration(
                    name="delete_desktop_item",
                    description="Permanently delete one directly named Desktop file or folder. Only use after user confirmation.",
                    parameters=types.Schema(type=types.Type.OBJECT, properties={"item_name": types.Schema(type=types.Type.STRING)}, required=["item_name"]),
                ),
                types.FunctionDeclaration(
                    name="list_workspace_files",
                    description="List files in F.R.I.D.A.Y.'s dedicated workspace.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={"directory_path": types.Schema(type=types.Type.STRING)},
                    ),
                ),
                types.FunctionDeclaration(
                    name="write_workspace_file",
                    description="Write a text file inside F.R.I.D.A.Y.'s dedicated workspace.",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "file_path": types.Schema(type=types.Type.STRING),
                            "content": types.Schema(type=types.Type.STRING),
                        },
                        required=["file_path", "content"],
                    ),
                ),
            ]
        )
    ]
