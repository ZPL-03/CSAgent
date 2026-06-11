"""桌面端中英文语言资源。"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

from core.paths import RUNTIME_DIR


LanguageCode = Literal["zh", "en"]

DEFAULT_LANGUAGE: LanguageCode = "zh"
LANGUAGE_OPTIONS: dict[str, str] = {
    "zh": "简体中文",
    "en": "English",
}

TEXT: dict[str, dict[str, str]] = {
    "zh": {
        "app.title": "CSDM_cph 耐压壳智能设计平台",
        "app.subtitle": "多智能体任务编排 / 候选生成 / 代理初筛 / ABAQUS 校核 / 案例回流 / 报告输出",
        "section.primary": "主流程",
        "section.utility": "辅助入口",
        "section.session": "当前会话",
        "section.manual": "人工操作",
        "section.language": "界面语言",
        "status.waiting": "状态：等待输入设计需求",
        "status.busy": "状态：{status}",
        "status.ready_next": "等待下一步操作",
        "status.no_snapshot": "状态：没有可载入的运行快照",
        "status.snapshot_failed": "状态：运行快照载入失败：{error}",
        "status.snapshot_loaded": "状态：已载入运行快照 {run_id}",
        "status.knowledge_refreshed": "状态：知识库视图已刷新",
        "input.placeholder": "例如：请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，极限压力不低于 35 MPa，生成 12 个候选，初筛保留 5 个候选",
        "button.start": "开始对话设计",
        "button.confirm": "确认继续",
        "button.pause": "跳过/暂停",
        "button.example": "载入示例需求",
        "button.refresh_knowledge": "刷新知识库",
        "button.open_report": "打开最新报告",
        "button.refresh_runs": "刷新运行记录",
        "button.restore_run": "载入运行快照",
        "button.screen": "手动：代理初筛",
        "button.evaluate_selected": "手动：校核所选样本",
        "button.evaluate_all": "手动：校核当前候选",
        "button.report": "手动：导出报告",
        "button.reset": "重置会话",
        "tab.task": "任务配置",
        "tab.workflow": "智能体流程",
        "tab.candidates": "候选方案",
        "tab.abaqus": "ABAQUS 结果",
        "tab.trace": "结果追踪",
        "tab.report": "报告预览",
        "tab.knowledge": "知识库",
        "tab.log": "日志",
        "metric.stage": "阶段：{value}",
        "metric.candidate_zero": "候选池：0",
        "metric.candidate": "候选池：{count} / 目标 {target}",
        "metric.pending_zero": "待校核：0",
        "metric.pending": "待校核：{count} / 初筛目标 {target}",
        "metric.pass": "通过：{count}",
        "snapshot.none": "暂无可恢复运行",
        "user.continue": "继续",
        "user.pause": "跳过/暂停",
        "message.no_report": "当前还没有可打开的报告文件。",
        "message.open_report": "已尝试打开报告：{path}",
        "message.selected_done": "所选候选样本均已完成 ABAQUS 校核，无需重复提交。",
        "message.all_done": "当前候选样本都已完成 ABAQUS 校核，无需重复提交。",
        "task.initial.title": "任务概览",
        "task.initial.body": "输入自然语言需求后，系统会自动解析任务、生成候选，并在关键节点引导你确认是否继续。",
        "workflow.initial.title": "流程提示",
        "workflow.initial.body": "1. 输入一句自然语言需求，系统解析候选池总数和初筛保留数并生成初始候选<br>2. 确认代理初筛后，系统按 PBIPF 公式和面密度排序<br>3. 确认有限元校核后，系统执行 ABAQUS 两阶段校核并回流案例<br>4. 确认报告输出后，系统生成 Markdown/PDF 报告",
        "plot.hint": "鼠标左键旋转，滚轮缩放，Shift+拖拽平移，双击重置视角。",
        "plot.no_pyvista": "当前环境未安装 pyvistaqt，无法提供交互式三维视图。",
        "plot.opengl_failed": "当前环境无法初始化交互式 OpenGL 视图，可在本地图形界面中重试。",
        "plot.no_candidate_geometry": "当前候选方案缺少几何参数，无法显示三维模型。",
        "plot.static_candidate_failed": "当前环境无法初始化交互式 OpenGL 视图，且静态几何图生成失败。",
        "plot.no_mode": "当前结果还没有可显示的模态云图数据。",
        "plot.static_mode_failed": "当前环境无法初始化交互式 OpenGL 视图，且静态模态云图生成失败。",
        "render.candidate_fallback": "候选方案",
        "render.candidate_section": "{name} 几何剖面 | L={length:.1f} mm，R={radius:.1f} mm，t={thickness:.2f} mm",
        "render.material_layup": "材料：{material} | 铺层角：±{alpha:.1f}/±{beta:.1f}",
        "render.x_axis": "轴向长度 / mm",
        "render.y_axis": "径向尺寸 / mm",
        "render.thickness": "t={thickness:.2f} mm",
        "render.mode_title": "{name} 一阶屈曲模态云图",
        "render.mode_scalar": "归一化模态位移",
        "candidate.empty": "当前还没有候选方案。",
        "candidate.preview_empty": "选中候选方案后，这里会显示可旋转的三维几何视图。",
        "candidate.no_detail": "请选择候选方案查看详细信息。",
        "candidate.no_preview": "请选择候选方案查看三维几何视图。",
        "candidate.no_geometry": "暂无几何预览。",
        "candidate.headers": "样本|来源|预测极限压力|预测面密度|排序分数|FEM极限压力|状态|结论",
        "abaqus.preview_empty": "完成 ABAQUS 校核后，这里会显示可旋转的模态云图。",
        "abaqus.no_results": "暂无 ABAQUS 结果。",
        "abaqus.no_preview": "暂无结果预览。",
        "abaqus.select_result": "请选择结果查看详情。",
        "abaqus.select_preview": "请选择结果查看模态云图。",
        "abaqus.headers": "候选样本|正式编号|状态|极限压力|屈曲压力|面密度|结论|失效模式",
    },
    "en": {
        "app.title": "CSDM_cph Pressure Hull Design Workbench",
        "app.subtitle": "Multi-agent orchestration / candidate generation / surrogate screening / ABAQUS verification / case memory / reports",
        "section.primary": "Primary Flow",
        "section.utility": "Utilities",
        "section.session": "Session",
        "section.manual": "Manual Actions",
        "section.language": "Language",
        "status.waiting": "Status: waiting for design requirements",
        "status.busy": "Status: {status}",
        "status.ready_next": "waiting for the next action",
        "status.no_snapshot": "Status: no run snapshot available",
        "status.snapshot_failed": "Status: failed to load run snapshot: {error}",
        "status.snapshot_loaded": "Status: loaded run snapshot {run_id}",
        "status.knowledge_refreshed": "Status: knowledge view refreshed",
        "input.placeholder": "Example: Design a composite external-pressure cylindrical pressure hull, external pressure 30 MPa, ultimate pressure at least 35 MPa, generate 12 candidates, keep 5 after screening",
        "button.start": "Start Design",
        "button.confirm": "Confirm",
        "button.pause": "Skip / Pause",
        "button.example": "Load Example",
        "button.refresh_knowledge": "Refresh Knowledge",
        "button.open_report": "Open Latest Report",
        "button.refresh_runs": "Refresh Runs",
        "button.restore_run": "Load Snapshot",
        "button.screen": "Manual: Screen",
        "button.evaluate_selected": "Manual: Verify Selected",
        "button.evaluate_all": "Manual: Verify Current",
        "button.report": "Manual: Export Report",
        "button.reset": "Reset Session",
        "tab.task": "Task",
        "tab.workflow": "Agents",
        "tab.candidates": "Candidates",
        "tab.abaqus": "ABAQUS",
        "tab.trace": "Trace",
        "tab.report": "Report",
        "tab.knowledge": "Knowledge",
        "tab.log": "Logs",
        "metric.stage": "Stage: {value}",
        "metric.candidate_zero": "Candidate pool: 0",
        "metric.candidate": "Candidate pool: {count} / target {target}",
        "metric.pending_zero": "Pending FEM: 0",
        "metric.pending": "Pending FEM: {count} / screen target {target}",
        "metric.pass": "Passed: {count}",
        "snapshot.none": "No restorable run",
        "user.continue": "Continue",
        "user.pause": "Skip / Pause",
        "message.no_report": "No report file is available yet.",
        "message.open_report": "Attempted to open report: {path}",
        "message.selected_done": "All selected candidates have already completed ABAQUS verification.",
        "message.all_done": "All current candidates have already completed ABAQUS verification.",
        "task.initial.title": "Task Overview",
        "task.initial.body": "After a natural-language request is entered, the system parses the task, generates candidates, and asks for confirmation at key gates.",
        "workflow.initial.title": "Workflow",
        "workflow.initial.body": "1. Enter one natural-language request; the system parses candidate count and screening count, then generates candidates<br>2. After screening confirmation, PBIPF and areal density rank the candidates<br>3. After FEM confirmation, ABAQUS runs two-stage verification and writes case memory<br>4. After report confirmation, Markdown/PDF reports are generated",
        "plot.hint": "Left-drag to rotate, wheel to zoom, Shift+drag to pan, double-click to reset view.",
        "plot.no_pyvista": "pyvistaqt is not available, so interactive 3D view cannot be provided.",
        "plot.opengl_failed": "Interactive OpenGL view cannot be initialized in the current environment.",
        "plot.no_candidate_geometry": "This candidate lacks geometry parameters and cannot be rendered.",
        "plot.static_candidate_failed": "Interactive OpenGL failed and the static geometry preview could not be generated.",
        "plot.no_mode": "No mode-shape cloud-map data is available for this result yet.",
        "plot.static_mode_failed": "Interactive OpenGL failed and the static mode-shape preview could not be generated.",
        "render.candidate_fallback": "Candidate",
        "render.candidate_section": "{name} section | L={length:.1f} mm, R={radius:.1f} mm, t={thickness:.2f} mm",
        "render.material_layup": "Material: {material} | Layup angles: +/-{alpha:.1f}/+/-{beta:.1f}",
        "render.x_axis": "Axial length / mm",
        "render.y_axis": "Radial direction / mm",
        "render.thickness": "t={thickness:.2f} mm",
        "render.mode_title": "{name} first buckling mode",
        "render.mode_scalar": "Normalized mode displacement",
        "candidate.empty": "No candidates yet.",
        "candidate.preview_empty": "Select a candidate to show the rotatable 3D geometry view.",
        "candidate.no_detail": "Select a candidate to view details.",
        "candidate.no_preview": "Select a candidate to view the 3D geometry.",
        "candidate.no_geometry": "No geometry preview is available.",
        "candidate.headers": "Sample|Source|Predicted ultimate pressure|Predicted areal density|Rank score|FEM ultimate pressure|Status|Verdict",
        "abaqus.preview_empty": "After ABAQUS verification, the rotatable mode-shape cloud map is shown here.",
        "abaqus.no_results": "No ABAQUS results yet.",
        "abaqus.no_preview": "No result preview is available.",
        "abaqus.select_result": "Select a result to view details.",
        "abaqus.select_preview": "Select a result to view the mode-shape cloud map.",
        "abaqus.headers": "Candidate|Formal ID|Status|Ultimate pressure|Buckling pressure|Areal density|Verdict|Failure mode",
    },
}


class LocaleManager:
    """管理界面语言和本地持久化设置。"""

    def __init__(self, settings_path: Path | None = None) -> None:
        env_path = os.getenv("CSDM_cph_UI_SETTINGS")
        self.settings_path = settings_path or (Path(env_path) if env_path else RUNTIME_DIR / "ui_settings.json")
        self.language: LanguageCode = self._load_language()

    def _load_language(self) -> LanguageCode:
        try:
            payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except Exception:
            return DEFAULT_LANGUAGE
        language = str(payload.get("language") or DEFAULT_LANGUAGE)
        return language if language in LANGUAGE_OPTIONS else DEFAULT_LANGUAGE  # type: ignore[return-value]

    def set_language(self, language: str) -> None:
        if language not in LANGUAGE_OPTIONS:
            language = DEFAULT_LANGUAGE
        self.language = language  # type: ignore[assignment]
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(
            json.dumps({"language": self.language}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def text(self, key: str, **kwargs: object) -> str:
        template = TEXT.get(self.language, {}).get(key) or TEXT[DEFAULT_LANGUAGE].get(key) or key
        try:
            return template.format(**kwargs)
        except Exception:
            return template


def text(key: str, language: str = DEFAULT_LANGUAGE, **kwargs: object) -> str:
    """按语言直接读取文本，供无状态渲染函数使用。"""

    lang = language if language in LANGUAGE_OPTIONS else DEFAULT_LANGUAGE
    template = TEXT.get(lang, {}).get(key) or TEXT[DEFAULT_LANGUAGE].get(key) or key
    try:
        return template.format(**kwargs)
    except Exception:
        return template
