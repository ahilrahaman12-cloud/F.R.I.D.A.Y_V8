"""Desktop and web entry point for F.R.I.D.A.Y."""

import asyncio

from flask import Flask, jsonify, render_template, request

from core.brain import FridayBrain
from system.telemetry import get_system_state


def create_app(brain: FridayBrain | None = None) -> Flask:
    """Create the Flask application and allow dependency injection in tests."""
    app = Flask(__name__, template_folder="templates")
    assistant = brain

    def get_brain() -> FridayBrain:
        nonlocal assistant
        if assistant is None:
            assistant = FridayBrain()
        return assistant

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/chat")
    def chat():
        prompt = (request.get_json(silent=True) or {}).get("prompt", "").strip()
        if not prompt:
            return jsonify({"status": "ERROR", "response": "Prompt cannot be empty."}), 400
        return jsonify(asyncio.run(get_brain().think(prompt)))

    @app.post("/api/confirm")
    def confirm():
        approved = bool((request.get_json(silent=True) or {}).get("approve", False))
        return jsonify(asyncio.run(get_brain().resolve_confirmation(approved)))

    @app.get("/api/stats")
    def stats():
        return jsonify(get_system_state())

    return app


def run_desktop_app() -> None:
    """Start the Flask interface in a native desktop window."""
    import webview

    webview.create_window("F.R.I.D.A.Y. Assistant", create_app(), width=900, height=650, resizable=True)
    webview.start()


if __name__ == "__main__":
    run_desktop_app()
