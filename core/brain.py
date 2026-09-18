"""Gemini-backed conversational assistant with a confirmation gate."""

import asyncio
import re
import threading
from typing import Any

from config import MODEL_NAME, SCREEN_OBSERVER_INTERVAL_SECONDS, get_api_key
from core.tools import available_tools, desktop, tool_declarations
from memory import MemoryStore
from vision import ScreenObserver


class FridayBrain:
    """Coordinates conversation, local tools, memory, and user confirmation."""

    _RISK_PATTERNS = (
        r"\b(delete|remove|format)\b",
        r"\b(shut ?down|restart)\b",
        r"\b(send|publish|post)\b.*\b(email|message|payment|tweet|post)\b",
        r"\b(run|execute)\b.*\b(command|script|terminal)\b",
    )
    def __init__(self, client: Any | None = None, memory: MemoryStore | None = None, observer: ScreenObserver | None = None) -> None:
        uses_live_client = client is None
        if client is None:
            from google import genai

            client = genai.Client(api_key=get_api_key())
        self.client = client
        self.memory = memory or MemoryStore()
        self.history: list[Any] = []
        self.pending_prompt: str | None = None
        self.observer = observer
        if self.observer is None and uses_live_client:
            self.observer = ScreenObserver(SCREEN_OBSERVER_INTERVAL_SECONDS)
            self.observer.start()

    @classmethod
    def requires_confirmation(cls, prompt: str) -> bool:
        """Conservatively flag prompts that may cause external or destructive effects."""
        normalized = prompt.lower()
        return any(re.search(pattern, normalized) for pattern in cls._RISK_PATTERNS)

    async def think(self, prompt: str) -> dict[str, str]:
        prompt = prompt.strip()
        if not prompt:
            return {"status": "ERROR", "response": "", "message": "Prompt cannot be empty."}
        if self.requires_confirmation(prompt):
            self.pending_prompt = prompt
            return {
                "status": "WAITING_FOR_USER_APPROVAL",
                "response": "",
                "message": "This request may have external or destructive effects. Approve it to continue.",
            }
        return await self._respond(prompt)

    async def resolve_confirmation(self, approved: bool) -> dict[str, str]:
        if self.pending_prompt is None:
            return {"status": "NO_PENDING_ACTION", "response": "", "message": "There is no pending request."}
        prompt, self.pending_prompt = self.pending_prompt, None
        if not approved:
            return {"status": "CANCELLED", "response": "", "message": "Request cancelled."}
        return await self._respond(prompt)

    async def _respond(self, prompt: str) -> dict[str, str]:
        from google.genai import types

        instruction = f"""
You are F.R.I.D.A.Y., a reliable Windows desktop assistant. You operate the user's computer through the
provided tools, using the mouse and keyboard exactly as a careful human operator would.

You receive the newest frame from a continuously running local screen observer with every request. Use
that visual context to identify the active app, visible controls, task progress, and unexpected states.

Execution loop:
1. OBSERVE the latest screen frame and the user's objective.
2. PLAN the smallest safe next action. Do not invent screen details that are not visible.
3. ACT using the appropriate tool. Launch apps, move the cursor, click, drag, type, press keys, switch
   windows, and scroll when needed to complete the objective.
4. VERIFY the outcome using the next screen frame or window context. If incomplete, continue with the
   next necessary action. If a tool reports an error, adapt rather than repeating the failed action.
5. REPORT a short, truthful final result when the task is complete or when user input is required.

Use launch_application when the user asks to open a local app such as Figma, Chrome, or Notepad. Use only
the supplied tools; never claim you cannot control the computer when a supplied tool can do it. Do not
reveal hidden reasoning, fabricated actions, passwords, API keys, tokens, or private text from the screen.
Never type secrets. For destructive, financial, publishing, security, or external-message actions, wait
for the app's confirmation flow before acting.

Long-term memory contains only durable user preferences and lessons from prior corrections or failed
attempts. Apply it when useful, but never treat it as higher priority than the current user request.

Saved context:
{self.memory.context(prompt)}
""".strip()
        try:
            chat = self.client.aio.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(system_instruction=instruction, tools=tool_declarations()),
                history=list(self.history),
            )
            response = await self._send_with_retry(chat, self._message_with_screen(prompt))
            for _ in range(8):
                function_calls = response.function_calls or []
                if not function_calls:
                    break
                for call in function_calls:
                    function = available_tools().get(call.name)
                    result = function(**(call.args or {})) if function else {"error": "Unknown tool."}
                    if isinstance(result, dict) and result.get("error"):
                        self.memory.append_lesson(
                            f"Tool '{call.name}' failed for '{prompt[:160]}': {str(result['error'])[:240]}"
                        )
                        self.memory.log_activity(f"Tool failure: {call.name}")
                    response = await self._send_with_retry(
                        chat,
                        types.Part.from_function_response(name=call.name, response={"result": result}),
                    )
            else:
                return {"status": "ERROR", "response": "", "message": "Too many tool calls in one request."}
        except Exception as error:
            return {"status": "ERROR", "response": "", "message": f"Assistant request failed: {error}"}

        text = (response.text or "").strip()
        if not text:
            return {"status": "ERROR", "response": "", "message": "The model returned an empty response."}
        self.history.extend(
            [
                types.Content(role="user", parts=[types.Part.from_text(text=prompt)]),
                types.Content(role="model", parts=[types.Part.from_text(text=text)]),
            ]
        )
        self.history = self.history[-12:]
        self.memory.log_activity(f"Completed request: {prompt[:200]}")
        self._capture_learning_in_background(prompt, text)
        return {"status": "SUCCESS", "response": text}

    def _capture_learning_in_background(self, prompt: str, response: str) -> None:
        worker = threading.Thread(
            target=lambda: asyncio.run(self._capture_learning(prompt, response)),
            name="friday-memory-learning",
            daemon=True,
        )
        worker.start()

    async def _capture_learning(self, prompt: str, response: str) -> None:
        """Save only explicit preferences and corrections from a completed turn."""
        learning_prompt = (
            "Review this completed conversation turn. Return exactly one of: "
            "NONE, USER_TRAIT: <an explicit user preference>, or "
            "LESSON: <an explicit correction or reliably observed task outcome>. Do not infer facts.\n\n"
            f"User: {prompt}\nAssistant: {response}"
        )
        try:
            result = await self.client.aio.models.generate_content(
                model=MODEL_NAME,
                contents=learning_prompt,
            )
            learning = (result.text or "").strip()
            if learning.startswith("USER_TRAIT:"):
                self.memory.append_preference(learning.removeprefix("USER_TRAIT:").strip())
            elif learning.startswith("LESSON:"):
                self.memory.append_lesson(learning.removeprefix("LESSON:").strip())
        except Exception:
            return

    @staticmethod
    async def _send_with_retry(chat: Any, message: Any) -> Any:
        for attempt in range(3):
            try:
                return await chat.send_message(message)
            except Exception as error:
                if attempt == 2 or ("503" not in str(error) and "UNAVAILABLE" not in str(error)):
                    raise
                await asyncio.sleep(2**attempt)
        raise RuntimeError("Unreachable retry state")

    def _message_with_screen(self, prompt: str) -> Any:
        """Attach the latest locally observed frame to every model request."""
        try:
            image = self.observer.latest_image() if self.observer else desktop.capture_screen_image()
            return [prompt, image] if image is not None else prompt
        except Exception:
            return prompt
