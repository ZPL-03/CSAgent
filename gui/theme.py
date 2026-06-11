"""桌面端主题与字体工具。"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtWidgets import QApplication


_FONT_LOADED = False

FONT_FILES = [
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/NotoSansSC-VF.ttf"),
    Path("C:/Windows/Fonts/simhei.ttf"),
    Path("C:/Windows/Fonts/Deng.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
]

FONT_FAMILIES = [
    "Microsoft YaHei UI",
    "Microsoft YaHei",
    "Noto Sans SC",
    "SimHei",
    "DengXian",
    "Segoe UI",
    "Arial",
]


def install_application_font(app: QApplication | None = None) -> str:
    """加载中英文字体并返回实际选用的字体族。"""

    global _FONT_LOADED
    app = app or QApplication.instance()
    if app is None:
        return "Microsoft YaHei UI"

    if not _FONT_LOADED:
        for font_file in FONT_FILES:
            if font_file.exists():
                QFontDatabase.addApplicationFont(str(font_file))
        _FONT_LOADED = True

    families = set(QFontDatabase.families())
    family = next((item for item in FONT_FAMILIES if item in families), FONT_FAMILIES[-1])
    app.setFont(QFont(family, 10))
    return family


def application_stylesheet(font_family: str) -> str:
    """返回工程软件工作台主题样式。"""

    safe_font = font_family.replace('"', "")
    return f"""
    QMainWindow, QWidget {{
        background: #eef2f6;
        color: #172033;
        font-family: "{safe_font}";
        font-size: 14px;
    }}
    QFrame#topBar {{
        background: #101827;
        border: 0;
    }}
    QLabel#appTitle {{
        background: transparent;
        color: #f8fafc;
        font-size: 20px;
        font-weight: 700;
        letter-spacing: 0;
    }}
    QLabel#appSubtitle {{
        background: transparent;
        color: #cbd5e1;
        font-size: 12px;
    }}
    QLabel#sectionTitle {{
        color: #334155;
        font-size: 12px;
        font-weight: 700;
        padding: 8px 0 3px 0;
        letter-spacing: 0;
    }}
    QWidget#leftRail {{
        background: #f7f9fc;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
    }}
    QWidget#workbenchPane {{
        background: #ffffff;
        border: 1px solid #b7c2d0;
        border-radius: 4px;
    }}
    QLabel#statusLabel {{
        background: #e8eef7;
        border: 1px solid #bdc9da;
        border-left: 4px solid #2563eb;
        border-radius: 3px;
        padding: 9px 10px;
        color: #172033;
    }}
    QLabel[role="metricCard"] {{
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-left: 4px solid #2563eb;
        border-radius: 3px;
        padding: 10px 12px;
        font-weight: 600;
        color: #172033;
    }}
    QTextBrowser, QTableWidget, QLineEdit, QComboBox {{
        background: #ffffff;
        border: 1px solid #c4cfdd;
        border-radius: 3px;
        selection-background-color: #dbeafe;
        selection-color: #0f172a;
    }}
    QTextBrowser {{
        padding: 8px;
        line-height: 1.35;
    }}
    QLineEdit, QComboBox {{
        min-height: 36px;
        padding: 7px 10px;
        color: #172033;
    }}
    QTableWidget {{
        gridline-color: #e2e8f0;
        alternate-background-color: #f8fafc;
    }}
    QHeaderView::section {{
        background: #e8eef7;
        color: #172033;
        border: 0;
        border-right: 1px solid #c4cfdd;
        border-bottom: 1px solid #c4cfdd;
        padding: 7px 8px;
        font-weight: 700;
    }}
    QTabWidget::pane {{
        border: 1px solid #b7c2d0;
        border-radius: 3px;
        top: -1px;
        background: #ffffff;
    }}
    QTabBar::tab {{
        background: #e8eef7;
        color: #334155;
        border: 1px solid #b7c2d0;
        border-bottom: 0;
        padding: 8px 16px;
        margin-right: 2px;
        min-width: 76px;
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        background: #ffffff;
        color: #0f172a;
        border-top: 3px solid #2563eb;
    }}
    QPushButton {{
        min-height: 36px;
        border-radius: 3px;
        padding: 7px 12px;
        font-weight: 700;
        border: 1px solid #b7c2d0;
        background: #ffffff;
        color: #172033;
    }}
    QPushButton:hover {{
        background: #edf4ff;
        border-color: #93b4dd;
    }}
    QPushButton:disabled {{
        background: #f1f5f9;
        color: #94a3b8;
        border-color: #d7dee8;
    }}
    QPushButton[variant="primary"] {{
        background: #1d4ed8;
        border-color: #1d4ed8;
        color: #ffffff;
    }}
    QPushButton[variant="primary"]:hover {{
        background: #1e40af;
        border-color: #1e40af;
    }}
    QPushButton[variant="success"] {{
        background: #0f766e;
        border-color: #0f766e;
        color: #ffffff;
    }}
    QPushButton[variant="warning"] {{
        background: #fff7ed;
        border-color: #fdba74;
        color: #9a3412;
    }}
    QPushButton[variant="danger"] {{
        background: #fff1f2;
        border-color: #fda4af;
        color: #9f1239;
    }}
    QPushButton[variant="secondary"] {{
        background: #eef2ff;
        border-color: #c7d2fe;
        color: #3730a3;
    }}
    QLabel#plotHint {{
        background: #f8fafc;
        border: 1px solid #d6dee9;
        border-radius: 3px;
        padding: 6px 8px;
        color: #475569;
        font-size: 12px;
    }}
    """
