from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from jarvis.core.assistant import Assistant
from jarvis.ui.main_window import JarvisWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS")
    app.setApplicationDisplayName("JARVIS — Personal AI Assistant")
    app.setOrganizationName("JARVIS")
    window = JarvisWindow(Assistant())
    window.run()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
