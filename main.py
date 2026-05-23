"""CSDM_cph 桌面程序入口。"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from core.paths import ensure_project_dirs
from gui.main_window import MainWindow


def main() -> int:
    ensure_project_dirs()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
