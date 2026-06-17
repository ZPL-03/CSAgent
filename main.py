"""CSDM_cph 桌面程序入口。"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from core.paths import ensure_project_dirs
from gui.main_window import MainWindow
from gui.theme import install_application_font


def main() -> int:
    ensure_project_dirs()
    app = QApplication(sys.argv)
    install_application_font(app)
    window = MainWindow()
    window._ensure_window_within_work_area()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
