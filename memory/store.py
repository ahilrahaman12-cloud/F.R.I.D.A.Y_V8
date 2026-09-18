"""Obsidian-compatible Markdown memory store."""

from datetime import datetime
from pathlib import Path
import re
import threading

from config import OBSIDIAN_VAULT_DIR


class MemoryStore:
    """Loads user preferences and operating notes from local markdown files."""

    def __init__(self, vault_dir: Path | None = None) -> None:
        self.vault_dir = vault_dir or OBSIDIAN_VAULT_DIR
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.profile_file = self.vault_dir / "User_Profile.md"
        self.notes_file = self.vault_dir / "System_Lessons.md"
        self.activity_file = self.vault_dir / "Activity_Log.md"
        self._ensure_file(self.profile_file, "# User Profile\n")
        self._ensure_file(self.notes_file, "# Operating Notes\n")
        self._ensure_file(self.activity_file, "# F.R.I.D.A.Y. Activity Log\n")

    @staticmethod
    def _ensure_file(path: Path, heading: str) -> None:
        if not path.exists():
            path.write_text(heading, encoding="utf-8")

    def context(self, query: str = "") -> str:
        """Return core memory plus the notes most relevant to the current task."""
        sections = []
        with self._lock:
            for label, path in (("User preferences", self.profile_file), ("Operating notes", self.notes_file)):
                text = self._read(path)
                if text:
                    sections.append(f"## {label}\n{text[-6_000:]}")

            note_paths = [
                path for path in self.vault_dir.rglob("*.md")
                if path not in {self.profile_file, self.notes_file, self.activity_file}
            ]
            keywords = {word.lower() for word in re.findall(r"[A-Za-z0-9_]{3,}", query)}
            ranked_notes = []
            for path in note_paths:
                text = self._read(path)
                searchable = f"{path.name}\n{text}".lower()
                score = sum(keyword in searchable for keyword in keywords)
                if score:
                    ranked_notes.append((score, path, text))
            for _, path, text in sorted(ranked_notes, key=lambda item: (-item[0], item[1].name))[:4]:
                sections.append(f"## Linked note: {path.relative_to(self.vault_dir)}\n{text[:3_000]}")
        return "\n\n".join(sections) or "No saved memory is available."

    def append_preference(self, preference: str) -> None:
        """Persist one explicit user preference."""
        with self._lock, self.profile_file.open("a", encoding="utf-8") as profile:
            profile.write(f"\n- {preference.strip()}\n")

    def append_lesson(self, lesson: str) -> None:
        """Persist one concise operating correction."""
        with self._lock, self.notes_file.open("a", encoding="utf-8") as notes:
            notes.write(f"\n- {lesson.strip()}\n")

    def log_activity(self, event: str) -> None:
        """Append a timestamped activity entry visible in Obsidian."""
        timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
        with self._lock, self.activity_file.open("a", encoding="utf-8") as activity:
            activity.write(f"\n- [{timestamp}] {event.strip()}\n")

    @staticmethod
    def _read(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8").strip()
        except OSError:
            return ""
