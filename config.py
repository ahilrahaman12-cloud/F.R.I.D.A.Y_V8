"""Application configuration loaded from environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent
WORKSPACE_DIR = PROJECT_ROOT / "workspace"
VAULT_DIR = PROJECT_ROOT / "vault"
OBSIDIAN_VAULT_DIR = Path(
    os.getenv("OBSIDIAN_VAULT_PATH", r"D:\Obsedian\F.R.I.D.A.Y. Vault")
).expanduser()

load_dotenv(PROJECT_ROOT / ".env")

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
SCREEN_OBSERVER_INTERVAL_SECONDS = max(0.5, float(os.getenv("SCREEN_OBSERVER_INTERVAL_SECONDS", "2")))


def get_api_key() -> str:
    """Return the configured Gemini API key or raise a clear setup error."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set. Copy .env.example to .env and add your key.")
    return api_key
