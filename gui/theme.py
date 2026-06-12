"""桌面端主题与字体工具。"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QFont, QFontDatabase, QPalette
from PyQt6.QtWidgets import QApplication


_FONT_LOADED = False

FONT_FILES = [
    Path("C:/Windows/Fonts/segoeui.ttf"),
    Path("C:/Windows/Fonts/segoeuib.ttf"),
    Path("C:/Windows/Fonts/CascadiaCode.ttf"),
    Path("C:/Windows/Fonts/CascadiaMono.ttf"),
    Path("C:/Windows/Fonts/NotoSansSC-VF.ttf"),
    Path("C:/Windows/Fonts/msyh.ttc"),
    Path("C:/Windows/Fonts/msyhl.ttc"),
    Path("C:/Windows/Fonts/simhei.ttf"),
    Path("C:/Windows/Fonts/Deng.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
]

FONT_FAMILIES = [
    "Segoe UI Variable Text",
    "Segoe UI",
    "HarmonyOS Sans SC",
    "Microsoft YaHei UI",
    "Microsoft YaHei",
    "Noto Sans SC",
    "Microsoft YaHei UI Light",
    "SimHei",
    "DengXian",
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
    font = QFont(family)
    font.setPointSizeF(10.2)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferQuality)
    app.setFont(font)
    return family


def resolve_theme(theme: str, app: QApplication | None = None) -> str:
    """解析自动主题并返回实际使用的主题名。"""

    if theme in {"dark", "light"}:
        return theme
    app = app or QApplication.instance()
    if app is None:
        return "dark"
    window_color = app.palette().color(QPalette.ColorRole.Window)
    return "dark" if window_color.lightness() < 128 else "light"


def _theme_palette(theme: str) -> dict[str, str]:
    if theme == "light":
        return {
            "app_bg": "#eef3f8",
            "text": "#172033",
            "top_bg": "#ffffff",
            "title": "#172033",
            "subtitle": "#64748b",
            "nav": "#475569",
            "nav_hover": "#172033",
            "section": "#334155",
            "agent_bg": "#e8eef6",
            "agent_border": "#c3cedd",
            "center_bg": "#f8fbff",
            "result_bg": "#f4f7fb",
            "surface": "#ffffff",
            "surface_alt": "#f8fafc",
            "border": "#c3cedd",
            "border_soft": "#d3dce8",
            "muted": "#475569",
            "status_bg": "#e8eef7",
            "metric_bg": "#ffffff",
            "field_bg": "#ffffff",
            "field_text": "#172033",
            "table_head": "#e8eef7",
            "tab_bg": "#e8eef7",
            "tab_selected": "#ffffff",
            "button_bg": "#ffffff",
            "button_hover": "#edf4ff",
            "button_disabled": "#f1f5f9",
            "disabled_text": "#94a3b8",
            "primary": "#1d4ed8",
            "primary_hover": "#1e40af",
            "success": "#0f766e",
            "warning_bg": "#fff7ed",
            "warning_border": "#fdba74",
            "warning_text": "#9a3412",
            "danger_bg": "#fff1f2",
            "danger_border": "#fda4af",
            "danger_text": "#9f1239",
            "secondary_bg": "#eef2ff",
            "secondary_border": "#c7d2fe",
            "secondary_text": "#3730a3",
            "accent": "#2563eb",
            "accent_soft": "#dbeafe",
            "agent_card": "#ffffff",
            "agent_card_active": "#eaf2ff",
            "agent_card_done": "#ecfdf5",
            "agent_text": "#172033",
            "agent_done_text": "#065f46",
            "agent_wait": "#64748b",
            "agent_active": "#2563eb",
            "agent_done": "#0f766e",
            "progress_bg": "#dbe4ef",
            "progress_chunk": "#2563eb",
            "log_bg": "#ffffff",
            "log_text": "#334155",
            "plot_bg": "#f8fbff",
        }
    return {
        "app_bg": "#080d15",
        "text": "#dbe4ef",
        "top_bg": "#121922",
        "title": "#f8fafc",
        "subtitle": "#94a3b8",
        "nav": "#cbd5e1",
        "nav_hover": "#ffffff",
        "section": "#a9b6c8",
        "agent_bg": "#101821",
        "agent_border": "#253246",
        "center_bg": "#0c121b",
        "result_bg": "#101821",
        "surface": "#182233",
        "surface_alt": "#111a28",
        "border": "#2c3a4f",
        "border_soft": "#334155",
        "muted": "#94a3b8",
        "status_bg": "#0e2238",
        "metric_bg": "#111c2e",
        "field_bg": "#111827",
        "field_text": "#e5edf7",
        "table_head": "#182337",
        "tab_bg": "#111a2b",
        "tab_selected": "#182337",
        "button_bg": "#111827",
        "button_hover": "#1f2d44",
        "button_disabled": "#111827",
        "disabled_text": "#64748b",
        "primary": "#2563eb",
        "primary_hover": "#1d4ed8",
        "success": "#0f766e",
        "warning_bg": "#3f2a16",
        "warning_border": "#b45309",
        "warning_text": "#fed7aa",
        "danger_bg": "#3c1822",
        "danger_border": "#be123c",
        "danger_text": "#fecdd3",
        "secondary_bg": "#19264a",
        "secondary_border": "#334a8f",
        "secondary_text": "#c7d2fe",
        "accent": "#38bdf8",
        "accent_soft": "#1e3a5f",
        "agent_card": "#1a2434",
        "agent_card_active": "#1c2638",
        "agent_card_done": "#122720",
        "agent_text": "#dbe4ef",
        "agent_done_text": "#ecfdf5",
        "agent_wait": "#64748b",
        "agent_active": "#38bdf8",
        "agent_done": "#14b8a6",
        "progress_bg": "#08111f",
        "progress_chunk": "#38bdf8",
        "log_bg": "#111a28",
        "log_text": "#a7b3c6",
        "plot_bg": "#101821",
    }


def application_stylesheet(font_family: str, theme: str = "dark") -> str:
    """返回工程软件工作台主题样式。"""

    safe_font = font_family.replace('"', "")
    font_stack = (
        f'"{safe_font}", "Segoe UI Variable Text", "Segoe UI", '
        '"Microsoft YaHei UI", "Microsoft YaHei", "Noto Sans SC", "Arial"'
    )
    color = _theme_palette(resolve_theme(theme))
    return f"""
    QMainWindow, QWidget {{
        background: {color["app_bg"]};
        color: {color["text"]};
        font-family: {font_stack};
        font-size: 13px;
    }}
    QFrame#topBar {{
        background: {color["top_bg"]};
        border: 0;
        border-bottom: 1px solid {color["border"]};
    }}
    QLabel#appTitle {{
        background: transparent;
        color: {color["title"]};
        font-size: 19px;
        font-weight: 700;
        letter-spacing: 0;
    }}
    QLabel#appSubtitle {{
        background: transparent;
        color: {color["subtitle"]};
        font-size: 12px;
    }}
    QLabel#navChip {{
        background: transparent;
        color: {color["nav"]};
        border-bottom: 2px solid transparent;
        padding: 5px 8px;
        font-size: 12px;
        font-weight: 600;
    }}
    QLabel#navChip:hover {{
        color: {color["nav_hover"]};
        border-bottom-color: {color["accent"]};
    }}
    QPushButton#navButton {{
        background: transparent;
        border: 0;
        border-bottom: 3px solid transparent;
        border-radius: 0;
        padding: 11px 14px 9px 14px;
        min-height: 28px;
        color: {color["nav"]};
        font-size: 12px;
        font-weight: 600;
    }}
    QPushButton#navButton:hover {{
        background: transparent;
        color: {color["nav_hover"]};
        border-bottom-color: {color["accent"]};
    }}
    QPushButton#navButton:checked {{
        background: transparent;
        color: {color["nav_hover"]};
        border-bottom-color: {color["accent"]};
    }}
    QLabel#logoBadge {{
        background: transparent;
        border: 0;
    }}
    QLabel#logoBadge[mode="text"] {{
        background: {color["primary"]};
        color: #ffffff;
        border-radius: 8px;
        font-size: 13px;
        font-weight: 800;
    }}
    QLabel#logoBadge[mode="image"] {{
        background: transparent;
        border-radius: 8px;
    }}
    QLabel#modelChip {{
        background: {color["button_bg"]};
        border: 1px solid {color["border_soft"]};
        border-radius: 15px;
        color: {color["subtitle"]};
        padding: 6px 18px;
        font-size: 12px;
        min-width: 118px;
    }}
    QLabel#sectionTitle {{
        background: transparent;
        color: {color["section"]};
        font-size: 12px;
        font-weight: 700;
        padding: 8px 0 3px 0;
        letter-spacing: 0;
    }}
    QWidget#agentRail {{
        background: {color["agent_bg"]};
        border: 1px solid {color["agent_border"]};
        border-radius: 0;
    }}
    QWidget#centerWorkbench {{
        background: {color["center_bg"]};
        border: 0;
        border-radius: 0;
    }}
    QWidget#conversationPanel {{
        background: {color["center_bg"]};
        border: 1px solid {color["border"]};
        border-radius: 12px;
    }}
    QWidget#resultRail {{
        background: {color["result_bg"]};
        border: 1px solid {color["border"]};
        border-radius: 0;
    }}
    QWidget#agentRail QLabel#sectionTitle {{
        color: {color["agent_text"]};
    }}
    QFrame#agentStatusCard {{
        background: {color["agent_card"]};
        border: 1px solid {color["agent_border"]};
        border-radius: 10px;
        color: {color["agent_text"]};
    }}
    QFrame#agentStatusCard[state="active"] {{
        background: {color["agent_card_active"]};
        border-color: {color["border_soft"]};
    }}
    QFrame#agentStatusCard[state="done"] {{
        background: {color["agent_card_done"]};
        border-color: {color["agent_done"]};
    }}
    QFrame#agentStatusCard[state="failed"] {{
        background: {color["danger_bg"]};
        border-color: {color["danger_border"]};
    }}
    QWidget#agentRail QLabel#agentCard {{
        background: {color["agent_card"]};
        border: 1px solid {color["agent_border"]};
        border-left: 0;
        border-radius: 10px;
        padding: 12px 12px;
        color: {color["agent_text"]};
        line-height: 1.35;
    }}
    QWidget#agentRail QLabel#agentCard[state="active"] {{
        background: {color["agent_card_active"]};
        border-color: {color["border_soft"]};
        color: {color["title"]};
    }}
    QWidget#agentRail QLabel#agentCard[state="done"] {{
        background: {color["agent_card_done"]};
        border-color: {color["agent_done"]};
        color: {color["agent_done_text"]};
    }}
    QWidget#agentRail QLabel#agentCard[state="failed"] {{
        background: {color["danger_bg"]};
        border-color: {color["danger_border"]};
        color: {color["danger_text"]};
    }}
    QWidget#agentRail QLabel#statusLabel {{
        background: {color["button_bg"]};
        border: 1px solid {color["agent_border"]};
        border-left: 4px solid {color["agent_active"]};
        color: {color["agent_text"]};
    }}
    QWidget#centerWorkbench QTextBrowser {{
        background: transparent;
    }}
    QLabel#chatStatus {{
        background: transparent;
        border: 0;
        color: {color["muted"]};
        padding: 2px 0;
        font-size: 12px;
    }}
    QLabel#statusLabel {{
        background: {color["status_bg"]};
        border: 1px solid {color["border_soft"]};
        border-left: 0;
        border-radius: 8px;
        padding: 9px 10px;
        color: {color["text"]};
    }}
    QLabel[role="metricCard"] {{
        background: {color["metric_bg"]};
        border: 1px solid {color["border_soft"]};
        border-left: 0;
        border-radius: 8px;
        padding: 13px 14px;
        font-weight: 600;
        color: {color["text"]};
    }}
    QProgressBar {{
        background: {color["progress_bg"]};
        border: 1px solid {color["agent_border"]};
        border-radius: 3px;
        height: 8px;
    }}
    QProgressBar::chunk {{
        background: {color["progress_chunk"]};
        border-radius: 3px;
    }}
    QTextBrowser, QTextEdit, QTableWidget, QLineEdit, QComboBox {{
        background: {color["field_bg"]};
        border: 1px solid {color["border_soft"]};
        border-radius: 8px;
        selection-background-color: {color["accent_soft"]};
        selection-color: {color["field_text"]};
        color: {color["field_text"]};
    }}
    QTextBrowser, QTextEdit {{
        padding: 8px;
        line-height: 1.35;
    }}
    QTextEdit#runtimeLog {{
         font-family: "Cascadia Mono", "Cascadia Code", "Consolas", {font_stack};
        font-size: 12px;
        color: {color["log_text"]};
        background: {color["log_bg"]};
        border: 1px solid {color["border_soft"]};
        border-radius: 10px;
        padding: 12px;
    }}
    QLineEdit, QComboBox {{
        min-height: 38px;
        padding: 8px 12px;
        color: {color["field_text"]};
    }}
    QTableWidget {{
        gridline-color: {color["border_soft"]};
        alternate-background-color: {color["surface_alt"]};
    }}
    QHeaderView::section {{
        background: {color["table_head"]};
        color: {color["text"]};
        border: 0;
        border-right: 1px solid {color["border_soft"]};
        border-bottom: 1px solid {color["border_soft"]};
        padding: 7px 8px;
        font-weight: 700;
    }}
    QTabWidget::pane {{
        border: 1px solid {color["border"]};
        border-radius: 3px;
        top: -1px;
        background: {color["surface"]};
    }}
    QTabBar::tab {{
        background: {color["tab_bg"]};
        color: {color["muted"]};
        border: 1px solid {color["border"]};
        border-bottom: 0;
        padding: 7px 9px;
        margin-right: 2px;
        min-width: 56px;
        font-weight: 600;
    }}
    QTabBar::tab:selected {{
        background: {color["tab_selected"]};
        color: {color["text"]};
        border-top: 3px solid {color["accent"]};
    }}
    QPushButton {{
        min-height: 38px;
        border-radius: 8px;
        padding: 8px 14px;
        font-weight: 600;
        border: 1px solid {color["border"]};
        background: {color["button_bg"]};
        color: {color["text"]};
    }}
    QPushButton:hover {{
        background: {color["button_hover"]};
        border-color: {color["accent"]};
    }}
    QPushButton:disabled {{
        background: {color["button_disabled"]};
        color: {color["disabled_text"]};
        border-color: {color["border_soft"]};
    }}
    QPushButton[variant="primary"] {{
        background: {color["primary"]};
        border-color: {color["primary"]};
        color: #ffffff;
        min-height: 42px;
    }}
    QPushButton[variant="primary"]:hover {{
        background: {color["primary_hover"]};
        border-color: {color["primary_hover"]};
    }}
    QPushButton[variant="success"] {{
        background: {color["success"]};
        border-color: {color["success"]};
        color: #ffffff;
    }}
    QPushButton[variant="warning"] {{
        background: {color["warning_bg"]};
        border-color: {color["warning_border"]};
        color: {color["warning_text"]};
    }}
    QPushButton[variant="danger"] {{
        background: {color["danger_bg"]};
        border-color: {color["danger_border"]};
        color: {color["danger_text"]};
    }}
    QPushButton[variant="secondary"] {{
        background: {color["secondary_bg"]};
        border-color: {color["secondary_border"]};
        color: {color["secondary_text"]};
    }}
    QPushButton[variant="icon"] {{
        background: {color["button_bg"]};
        border-color: {color["border_soft"]};
        color: {color["text"]};
        min-width: 30px;
        max-width: 30px;
        min-height: 28px;
        max-height: 28px;
        border-radius: 8px;
        padding: 0;
        font-size: 14px;
        font-weight: 700;
    }}
    QPushButton[variant="icon"]:hover {{
        background: {color["button_hover"]};
        border-color: {color["accent"]};
        color: {color["accent"]};
    }}
    QPushButton[variant="link"] {{
        background: transparent;
        border: 0;
        color: {color["accent"]};
        min-height: 24px;
        padding: 2px 4px;
        font-weight: 600;
    }}
    QPushButton[variant="link"]:hover {{
        background: transparent;
        border: 0;
        color: {color["nav_hover"]};
    }}
    QLabel#settingsCard, QWidget#settingsCard {{
        background: {color["surface_alt"]};
        border: 1px solid {color["border_soft"]};
        border-radius: 12px;
        padding: 12px 16px;
        color: {color["text"]};
    }}
    QWidget#settingsCard QLabel {{
        background: transparent;
    }}
    QLabel#configTitle {{
        background: transparent;
        color: {color["title"]};
        font-size: 17px;
        font-weight: 800;
        padding: 0;
    }}
    QLabel#configSubtitle {{
        background: transparent;
        color: {color["muted"]};
        font-size: 12px;
        line-height: 1.35;
        padding: 0;
    }}
    QFrame#configCard {{
        background: {color["surface_alt"]};
        border: 1px solid {color["border_soft"]};
        border-radius: 10px;
    }}
    QLabel#configCardTitle {{
        background: transparent;
        color: {color["title"]};
        font-size: 13px;
        font-weight: 800;
        padding: 0 0 2px 0;
    }}
    QLabel#configKey {{
        background: transparent;
        color: {color["muted"]};
        font-size: 11px;
        font-weight: 600;
        padding: 0;
    }}
    QLabel#configValue {{
        background: transparent;
        color: {color["text"]};
        font-size: 12px;
        font-weight: 600;
        padding: 0;
    }}
    QSplitter::handle {{
        background: {color["border"]};
    }}
    QLabel#plotHint {{
        background: transparent;
        border: 0;
        border-radius: 0;
        padding: 2px 0;
        color: {color["muted"]};
        font-size: 12px;
    }}
    QLabel#plotCanvas {{
        background: {color["plot_bg"]};
        border: 1px solid {color["border"]};
        border-radius: 10px;
        padding: 0;
    }}
    QLabel#plotEmpty {{
        background: {color["surface_alt"]};
        border: 1px solid {color["border_soft"]};
        border-radius: 10px;
        padding: 18px;
        color: {color["muted"]};
        line-height: 1.4;
    }}
    QSplitter::handle {{
        background: {color["app_bg"]};
    }}
    """
