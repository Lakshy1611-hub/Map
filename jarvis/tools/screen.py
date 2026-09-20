from __future__ import annotations

import base64
import json
import os
import re
from datetime import datetime
from pathlib import Path

from jarvis.config import Settings
from jarvis.core.models import ToolResult


def _capture(directory: str = "screenshots") -> tuple[Path | None, str | None]:
    try:
        import pyautogui
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        path = target / f"jarvis-{datetime.now():%Y%m%d-%H%M%S}.png"
        pyautogui.screenshot(str(path))
        return path, None
    except Exception as exc:
        return None, str(exc)


def take_screenshot(directory: str = "screenshots") -> ToolResult:
    """Capture the full desktop to a timestamped PNG."""
    path, error = _capture(directory)
    if error:
        return ToolResult(False, f"Screenshot failed: {error}")
    return ToolResult(True, f"Screenshot saved to {path}.", {"path": str(path)})


def _vision_answer(question: str, image_path: Path) -> str:
    settings = Settings()
    if not settings.api_key:
        return "Screen captured. Add a Gemini API key to enable visual analysis."
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=settings.api_key)
        image_bytes = image_path.read_bytes()
        response = client.models.generate_content(
            model=settings.model,
            contents=[
                question or "Describe what is visible on my Windows screen and tell me the next useful action.",
                types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            ],
        )
        return (getattr(response, "text", "") or "").strip() or "I could not read the screen clearly."
    except Exception as exc:
        return f"Screen analysis is unavailable right now: {exc}"


def inspect_screen(question: str = "") -> ToolResult:
    """Capture the desktop and analyze the visible UI with the configured Gemini vision model."""
    path, error = _capture()
    if error:
        return ToolResult(False, f"Screen capture failed: {error}")
    answer = _vision_answer(question, path)
    return ToolResult(True, answer, {"path": str(path)})


def visual_click(target: str) -> ToolResult:
    """Find a described UI target on screen with vision and click its center."""
    path, error = _capture()
    if error:
        return ToolResult(False, f"Screen capture failed: {error}")
    settings = Settings()
    if not settings.api_key:
        return ToolResult(False, "A Gemini API key is required for visual clicking.")
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=settings.api_key)
        prompt = (
            "Find the center coordinates of the requested UI element on this screenshot. "
            "Return ONLY JSON: {\"x\": integer, \"y\": integer, \"confidence\": number}. "
            f"Requested target: {target}"
        )
        response = client.models.generate_content(
            model=settings.model,
            contents=[prompt, types.Part.from_bytes(data=path.read_bytes(), mime_type="image/png")],
        )
        raw = (getattr(response, "text", "") or "").strip()
        match = re.search(r"\{.*\}", raw, flags=re.S)
        if not match:
            return ToolResult(False, "Vision did not return usable coordinates.")
        point = json.loads(match.group(0))
        x, y = int(point["x"]), int(point["y"])
        confidence = float(point.get("confidence", 0))
        if confidence < 0.55 or x < 0 or y < 0:
            return ToolResult(False, "Vision was not confident enough to click that target safely.")
        import pyautogui
        pyautogui.click(x, y)
        return ToolResult(True, f"Clicked the {target} at {x}, {y}.", {"x": x, "y": y, "confidence": confidence})
    except Exception as exc:
        return ToolResult(False, f"Visual click failed: {exc}")