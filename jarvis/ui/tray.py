"""Optional native system tray integration, kept independent from the window."""
from __future__ import annotations

import importlib.util
import threading
from typing import Callable


class TrayController:
    def __init__(self, show: Callable[[], None], pause: Callable[[], None], exit_app: Callable[[], None]):
        self._show, self._pause, self._exit = show, pause, exit_app
        self._icon = None

    def start(self) -> bool:
        if self._icon is not None:
            return True
        if importlib.util.find_spec("pystray") is None or importlib.util.find_spec("PIL") is None:
            return False
        import pystray
        from PIL import Image, ImageDraw
        image = Image.new("RGB", (64, 64), "#07111f")
        draw = ImageDraw.Draw(image)
        draw.ellipse((8, 8, 56, 56), fill="#10d6d0", outline="#d9ffff", width=3)
        menu = pystray.Menu(
            pystray.MenuItem("Open JARVIS", lambda: self._show()),
            pystray.MenuItem("Pause assistant", lambda: self._pause()),
            pystray.MenuItem("Exit", lambda: self._exit()),
        )
        self._icon = pystray.Icon("jarvis", image, "JARVIS", menu)
        threading.Thread(target=self._icon.run, daemon=True).start()
        return True

    def stop(self) -> None:
        if self._icon:
            self._icon.stop()
