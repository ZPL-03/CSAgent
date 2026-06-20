"""桌面端中英文语言资源。"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal

from core.paths import RUNTIME_DIR


LanguageCode = Literal["zh", "en"]
ThemeCode = Literal["auto", "dark", "light"]

DEFAULT_LANGUAGE: LanguageCode = "zh"
DEFAULT_THEME: ThemeCode = "dark"
LANGUAGE_OPTIONS: dict[str, str] = {
    "zh": "简体中文",
    "en": "English",
}
THEME_OPTIONS: dict[str, dict[str, str]] = {
    "zh": {
        "auto": "跟随系统",
        "dark": "深色工程",
        "light": "亮色工程",
    },
    "en": {
        "auto": "Auto",
        "dark": "Dark Engineering",
        "light": "Light Engineering",
    },
}

TEXT: dict[str, dict[str, str]] = {
    "zh": {
        "app.title": "CSAgent",
        "app.subtitle": "多智能体智能设计平台",
        "section.primary": "主流程",
        "section.utility": "辅助入口",
        "section.session": "当前会话",
        "section.manual": "人工操作",
        "section.runtime_log": "运行日志 · LOG",
        "section.agents": "智能体运行面板",
        "section.queue": "任务队列",
        "section.knowledge_status": "知识连接",
        "section.run_audit": "运行审计",
        "section.workbench": "工作流 · LangGraph DAG",
        "section.dialog": "对话 · 多智能体协作",
        "section.details": "实时结果 · LIVE",
        "section.language": "界面语言",
        "section.theme": "界面主题",
        "nav.workbench": "工作台",
        "nav.knowledge": "知识库",
        "nav.monitor": "监控",
        "nav.settings": "设置",
        "model.current": "领域主模型",
        "model.primary_active": "领域主模型 · {model}",
        "model.fallback_active": "回退模型 · {model}",
        "model.failed": "LLM 不可用",
        "model.primary_log": "模型状态：主模型 {model}（后端 {backend}，尝试 {attempts} 次）",
        "model.fallback_log": "模型状态：回退模型 {model}（后端 {backend}，尝试 {attempts} 次）",
        "model.failed_log": "模型状态：LLM 调用失败（尝试 {attempts} 次）",
        "status.waiting": "状态：等待输入设计需求",
        "status.busy": "状态：{status}",
        "status.ready_next": "等待下一步操作",
        "status.no_snapshot": "状态：没有可恢复的运行状态",
        "status.snapshot_failed": "状态：运行状态恢复失败：{error}",
        "status.snapshot_loaded": "状态：已恢复运行状态 {run_id}",
        "status.knowledge_refreshed": "状态：知识库视图已刷新",
        "input.placeholder": "例如：请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，极限压力不低于 35 MPa，生成 12 个候选，初筛保留 5 个候选",
        "chat.empty": "在下方输入设计需求，系统会实时显示任务解析、候选生成、代理初筛、有限元校核、知识回流和报告输出过程。",
        "chat.empty.title": "对话 · 等待设计任务",
        "chat.empty.user_prompt": "请为复合材料外压圆柱耐压壳设计方案，外压 30 MPa，极限压力不低于 35 MPa，生成 12 个候选，初筛保留 5 个候选",
        "chat.empty.agent_title": "ORCHESTRATOR",
        "chat.empty.agent_body": "收到任务后，系统会抽取用户已给事实，构建候选池和初筛目标，并在代理初筛、有限元校核、报告导出前请求人工确认。",
        "button.start": "发送",
        "button.confirm": "确认继续",
        "button.pause": "跳过/暂停",
        "button.example": "载入示例需求",
        "button.refresh_knowledge": "刷新知识库",
        "button.open_report": "打开最新报告",
        "button.export_data": "导出数据",
        "button.reset_view": "重置视角",
        "button.fit_view": "适配窗口",
        "button.show_fem_result": "显示有限元结果",
        "button.show_geometry": "显示几何模型",
        "button.no_fem_result": "暂无有限元结果",
        "button.view_trace": "查看执行轨迹 →",
        "button.refresh_runs": "刷新运行记录",
        "button.restore_run": "恢复运行状态",
        "tooltip.restore_run": "从本地运行库恢复上一次流程状态；只读取任务、候选、筛选结果、有限元结果、报告和待确认节点，不重新调用 LLM 或 ABAQUS。",
        "button.screen": "手动：代理初筛",
        "button.evaluate_selected": "手动：校核所选样本",
        "button.evaluate_all": "手动：校核当前候选",
        "button.report": "生成阶段报告",
        "button.report_dir": "报告保存目录",
        "button.reset": "重置会话",
        "tooltip.report_dir": "选择报告输出目录；未选择时写入项目 data/results。",
        "dialog.report_dir": "选择报告保存目录",
        "status.report_dir": "状态：报告保存目录已设置为 {path}",
        "report.kind.all": "全部报告",
        "report.kind.overall": "总体设计报告",
        "report.kind.fem": "FEM 校核报告",
        "report.kind.design_solution": "推荐设计方案",
        "metric.stage": "阶段：{value}",
        "metric.candidate_zero": "候选池：0",
        "metric.candidate": "候选池：{count} / 目标 {target}",
        "metric.pending_zero": "待校核：0",
        "metric.pending": "待校核：{count} / 初筛目标 {target}",
        "metric.pass": "通过：{count}",
        "agent.waiting": "等待",
        "agent.active": "运行中",
        "agent.done": "完成",
        "agent.failed": "失败",
        "agent.orchestrator": "任务编排 · 人工确认",
        "agent.candidate_gen": "候选生成 · 去重入池",
        "agent.screener": "代理初筛 · 排序",
        "agent.fem": "ABAQUS 校核",
        "agent.knowledge": "知识回流 · RAG/KG",
        "agent.report": "报告输出 · 解释",
        "queue.idle": "等待设计需求",
        "queue.progress": "流程进度：{percent}%",
        "queue.stage": "当前阶段：{stage}",
        "knowledge.status": "知识库：{status}；案例 {cases}；运行 {runs}",
        "audit.no_run": "未开始",
        "audit.none": "无",
        "audit.confirm_screen": "初筛确认",
        "audit.confirm_fem": "有限元校核确认",
        "audit.confirm_report": "报告导出确认",
        "audit.run": "运行：{run_id}",
        "audit.stage": "阶段：{stage}",
        "audit.confirmation": "确认：{confirmation}",
        "audit.artifacts": "产物：候选 {candidates} / 初筛 {screened} / FEM {results} / 知识 {knowledge}",
        "snapshot.none": "暂无可恢复运行",
        "user.continue": "继续",
        "user.pause": "跳过/暂停",
        "message.no_report": "当前还没有可打开的报告文件。",
        "message.open_report": "已尝试打开报告：{path}",
        "message.no_export_data": "当前会话还没有可导出的任务、候选、有限元或报告数据。",
        "message.export_data": "数据已导出：{json_path} / {csv_path}",
        "message.selected_done": "所选候选样本均已完成 ABAQUS 校核，无需重复提交。",
        "message.all_done": "当前候选样本都已完成 ABAQUS 校核，无需重复提交。",
        "task.initial.title": "任务概览",
        "task.initial.body": "输入自然语言需求后，系统会自动解析任务、生成候选，并在关键节点引导你确认是否继续。",
        "workflow.initial.title": "流程提示",
        "workflow.initial.body": "1. 输入一句自然语言需求，系统解析候选池总数和初筛保留数并生成初始候选<br>2. 确认代理初筛后，系统按 PBIPF 公式和面密度排序<br>3. 确认有限元校核后，系统执行 ABAQUS 两阶段校核并回流案例<br>4. 确认报告输出后，系统生成 Markdown/PDF 报告",
        "plot.offline_preview": "离线预览：当前未使用交互式 OpenGL 视图。",
        "plot.no_pyvista": "当前环境未安装 pyvistaqt，无法打开交互式三维视图。",
        "plot.opengl_failed": "当前环境无法初始化交互式 OpenGL 视图，已切换为离线预览。",
        "plot.no_candidate_geometry": "当前候选方案缺少几何参数，无法显示三维模型。",
        "plot.static_candidate_failed": "交互式 OpenGL 视图不可用，离线几何预览生成失败。",
        "plot.no_mode": "当前结果还没有可显示的模态云图数据。",
        "plot.static_mode_failed": "交互式 OpenGL 视图不可用，离线模态云图预览生成失败。",
        "plot.reference_hull": "参考耐压壳模型",
        "live_view.empty": "实时视口：生成候选后显示耐压壳几何；完成 ABAQUS 后显示一阶屈曲模态云图。",
        "render.candidate_fallback": "候选方案",
        "render.candidate_section": "{name} 几何剖面 | L={length:.1f} mm，R={radius:.1f} mm，t={thickness:.2f} mm",
        "render.material_layup": "材料：{material} | 铺层角：±{alpha:.1f}/±{beta:.1f}",
        "render.x_axis": "轴向长度 / mm",
        "render.y_axis": "径向尺寸 / mm",
        "render.thickness": "t={thickness:.2f} mm",
        "render.mode_title": "{name} 一阶屈曲模态云图",
        "render.mode_scalar": "归一化模态位移",
        "candidate.empty": "当前还没有候选方案。",
        "candidate.empty_body": "候选生成后显示统一候选池；未入选 Top-K 的方案置灰，但仍可人工送入 FEM。",
        "candidate.preview_empty": "选中候选方案后，这里会显示可旋转的三维几何视图。",
        "candidate.no_detail": "请选择候选方案查看详细信息。",
        "candidate.no_preview": "请选择候选方案查看三维几何视图。",
        "candidate.no_geometry": "暂无几何预览。",
        "candidate.headers": "样本|来源|极限|面密度|分数|FEM|状态|结论",
        "candidate.tab.detail": "设计详情",
        "candidate.tab.audit": "来源审计",
        "candidate.metric.total": "候选总数\n{count}",
        "candidate.metric.llm": "LLM\n{count}",
        "candidate.metric.case": "案例迁移\n{count}",
        "candidate.metric.doe": "DOE\n{count}",
        "candidate.metric.evaluated": "已校核\n{count}",
        "candidate.source.llm": "LLM 项目知识库/知识图谱增强",
        "candidate.source.case": "历史案例迁移",
        "candidate.source.doe": "DOE 参数采样",
        "candidate.source.unknown": "未知来源",
        "abaqus.preview_empty": "完成 ABAQUS 校核后，这里会显示可旋转的模态云图。",
        "abaqus.no_results": "暂无 ABAQUS 结果。",
        "abaqus.no_preview": "暂无结果预览。",
        "abaqus.select_result": "请选择结果查看详情。",
        "abaqus.select_preview": "请选择结果查看模态云图。",
        "abaqus.headers": "候选样本|正式编号|状态|极限压力|屈曲压力|面密度|结论|失效模式",
    },
    "en": {
        "app.title": "CSAgent",
        "app.subtitle": "Multi-Agent Intelligent Design Platform",
        "section.primary": "Primary Flow",
        "section.utility": "Utilities",
        "section.session": "Session",
        "section.manual": "Manual Actions",
        "section.runtime_log": "Runtime Log",
        "section.agents": "Agent Console",
        "section.queue": "Task Queue",
        "section.knowledge_status": "Knowledge Link",
        "section.run_audit": "Run Audit",
        "section.workbench": "Workflow · LangGraph DAG",
        "section.dialog": "Conversation · Multi-Agent Collaboration",
        "section.details": "Live Results",
        "section.language": "Language",
        "section.theme": "Theme",
        "nav.workbench": "Workbench",
        "nav.knowledge": "Knowledge",
        "nav.monitor": "Monitor",
        "nav.settings": "Settings",
        "model.current": "Domain Model",
        "model.primary_active": "Domain Model · {model}",
        "model.fallback_active": "Fallback Model · {model}",
        "model.failed": "LLM unavailable",
        "model.primary_log": "Model status: primary model {model} (backend {backend}, attempts {attempts})",
        "model.fallback_log": "Model status: fallback model {model} (backend {backend}, attempts {attempts})",
        "model.failed_log": "Model status: LLM call failed (attempts {attempts})",
        "status.waiting": "Status: waiting for design requirements",
        "status.busy": "Status: {status}",
        "status.ready_next": "waiting for the next action",
        "status.no_snapshot": "Status: no restorable run state is available",
        "status.snapshot_failed": "Status: failed to restore run state: {error}",
        "status.snapshot_loaded": "Status: restored run state {run_id}",
        "status.knowledge_refreshed": "Status: knowledge view refreshed",
        "input.placeholder": "Example: Design a composite external-pressure cylindrical pressure hull, external pressure 30 MPa, ultimate pressure at least 35 MPa, generate 12 candidates, keep 5 after screening",
        "chat.empty": "Enter a design request below. Task parsing, candidate generation, surrogate screening, FEM verification, knowledge persistence, and reporting will appear here in real time.",
        "chat.empty.title": "Conversation · Waiting for Design Task",
        "chat.empty.user_prompt": "Design a composite external-pressure cylindrical pressure hull, external pressure 30 MPa, ultimate pressure at least 35 MPa, generate 12 candidates, keep 5 after screening",
        "chat.empty.agent_title": "ORCHESTRATOR",
        "chat.empty.agent_body": "After receiving a task, the system extracts user facts, builds the candidate pool and screening target, then asks for human confirmation before screening, FEM verification, and report export.",
        "button.start": "Send",
        "button.confirm": "Confirm",
        "button.pause": "Skip / Pause",
        "button.example": "Load Example",
        "button.refresh_knowledge": "Refresh Knowledge",
        "button.open_report": "Open Latest Report",
        "button.export_data": "Export Data",
        "button.reset_view": "Reset View",
        "button.fit_view": "Fit View",
        "button.show_fem_result": "Show FEM Result",
        "button.show_geometry": "Show Geometry",
        "button.no_fem_result": "No FEM result yet",
        "button.view_trace": "View run trace →",
        "button.refresh_runs": "Refresh Runs",
        "button.restore_run": "Restore Run State",
        "tooltip.restore_run": "Restore the previous workflow state from the local runtime store without re-running LLM or ABAQUS.",
        "button.screen": "Manual: Screen",
        "button.evaluate_selected": "Manual: Verify Selected",
        "button.evaluate_all": "Manual: Verify Current",
        "button.report": "Generate Stage Report",
        "button.report_dir": "Report Save Folder",
        "button.reset": "Reset Session",
        "tooltip.report_dir": "Choose a report output folder. If unset, reports are written to project data/results.",
        "dialog.report_dir": "Choose Report Save Folder",
        "status.report_dir": "Status: report save folder set to {path}",
        "report.kind.all": "All Reports",
        "report.kind.overall": "Overall Design Report",
        "report.kind.fem": "FEM Verification Report",
        "report.kind.design_solution": "Recommended Design Solution",
        "metric.stage": "Stage: {value}",
        "metric.candidate_zero": "Candidate pool: 0",
        "metric.candidate": "Candidate pool: {count} / target {target}",
        "metric.pending_zero": "Pending FEM: 0",
        "metric.pending": "Pending FEM: {count} / screen target {target}",
        "metric.pass": "Passed: {count}",
        "agent.waiting": "Waiting",
        "agent.active": "Running",
        "agent.done": "Done",
        "agent.failed": "Failed",
        "agent.orchestrator": "Orchestration · HITL",
        "agent.candidate_gen": "Generation · dedup",
        "agent.screener": "Surrogate ranking",
        "agent.fem": "ABAQUS verification",
        "agent.knowledge": "Knowledge · RAG/KG",
        "agent.report": "Reports · rationale",
        "queue.idle": "Waiting for design requirements",
        "queue.progress": "Workflow progress: {percent}%",
        "queue.stage": "Current stage: {stage}",
        "knowledge.status": "Knowledge: {status}; cases {cases}; runs {runs}",
        "audit.no_run": "Not started",
        "audit.none": "None",
        "audit.confirm_screen": "Screening gate",
        "audit.confirm_fem": "FEM gate",
        "audit.confirm_report": "Report gate",
        "audit.run": "Run: {run_id}",
        "audit.stage": "Stage: {stage}",
        "audit.confirmation": "Gate: {confirmation}",
        "audit.artifacts": "Artifacts: candidates {candidates} / screened {screened} / FEM {results} / knowledge {knowledge}",
        "snapshot.none": "No restorable run",
        "user.continue": "Continue",
        "user.pause": "Skip / Pause",
        "message.no_report": "No report file is available yet.",
        "message.open_report": "Attempted to open report: {path}",
        "message.no_export_data": "The current session has no task, candidate, FEM, or report data to export.",
        "message.export_data": "Data exported: {json_path} / {csv_path}",
        "message.selected_done": "All selected candidates have already completed ABAQUS verification.",
        "message.all_done": "All current candidates have already completed ABAQUS verification.",
        "task.initial.title": "Task Overview",
        "task.initial.body": "After a natural-language request is entered, the system parses the task, generates candidates, and asks for confirmation at key gates.",
        "workflow.initial.title": "Workflow",
        "workflow.initial.body": "1. Enter one natural-language request; the system parses candidate count and screening count, then generates candidates<br>2. After screening confirmation, PBIPF and areal density rank the candidates<br>3. After FEM confirmation, ABAQUS runs two-stage verification and writes case memory<br>4. After report confirmation, Markdown/PDF reports are generated",
        "plot.offline_preview": "Offline preview: interactive OpenGL view is not active.",
        "plot.no_pyvista": "pyvistaqt is not available, so interactive 3D view cannot be opened.",
        "plot.opengl_failed": "Interactive OpenGL view cannot be initialized; offline preview is shown.",
        "plot.no_candidate_geometry": "This candidate lacks geometry parameters and cannot be rendered.",
        "plot.static_candidate_failed": "Interactive OpenGL is unavailable and the offline geometry preview could not be generated.",
        "plot.no_mode": "No mode-shape cloud-map data is available for this result yet.",
        "plot.static_mode_failed": "Interactive OpenGL is unavailable and the offline mode-shape preview could not be generated.",
        "plot.reference_hull": "Reference pressure hull",
        "live_view.empty": "Live viewport: candidate geometry is shown after generation; first buckling mode is shown after ABAQUS verification.",
        "render.candidate_fallback": "Candidate",
        "render.candidate_section": "{name} section | L={length:.1f} mm, R={radius:.1f} mm, t={thickness:.2f} mm",
        "render.material_layup": "Material: {material} | Layup angles: +/-{alpha:.1f}/+/-{beta:.1f}",
        "render.x_axis": "Axial length / mm",
        "render.y_axis": "Radial direction / mm",
        "render.thickness": "t={thickness:.2f} mm",
        "render.mode_title": "{name} first buckling mode",
        "render.mode_scalar": "Normalized mode displacement",
        "candidate.empty": "No candidates yet.",
        "candidate.empty_body": "After generation, the unified candidate pool appears here. Non-Top-K designs are dimmed but can still be sent to FEM manually.",
        "candidate.preview_empty": "Select a candidate to show the rotatable 3D geometry view.",
        "candidate.no_detail": "Select a candidate to view details.",
        "candidate.no_preview": "Select a candidate to view the 3D geometry.",
        "candidate.no_geometry": "No geometry preview is available.",
        "candidate.headers": "Sample|Source|Pult|Density|Score|FEM|Status|Verdict",
        "candidate.tab.detail": "Design Detail",
        "candidate.tab.audit": "Source Audit",
        "candidate.metric.total": "Total\n{count}",
        "candidate.metric.llm": "LLM\n{count}",
        "candidate.metric.case": "Case Transfer\n{count}",
        "candidate.metric.doe": "DOE\n{count}",
        "candidate.metric.evaluated": "Verified\n{count}",
        "candidate.source.llm": "LLM with project RAG/KG evidence",
        "candidate.source.case": "Historical case transfer",
        "candidate.source.doe": "DOE sampling",
        "candidate.source.unknown": "Unknown source",
        "abaqus.preview_empty": "After ABAQUS verification, the rotatable mode-shape cloud map is shown here.",
        "abaqus.no_results": "No ABAQUS results yet.",
        "abaqus.no_preview": "No result preview is available.",
        "abaqus.select_result": "Select a result to view details.",
        "abaqus.select_preview": "Select a result to view the mode-shape cloud map.",
        "abaqus.headers": "Candidate|Formal ID|Status|Ultimate pressure|Buckling pressure|Areal density|Verdict|Failure mode",
    },
}


class LocaleManager:
    """管理界面语言、主题和本地持久化设置。"""

    def __init__(self, settings_path: Path | None = None) -> None:
        env_path = os.getenv("CSDM_cph_UI_SETTINGS")
        self.settings_path = settings_path or (Path(env_path) if env_path else RUNTIME_DIR / "ui_settings.json")
        settings = self._load_settings()
        self.language: LanguageCode = self._normalize_language(settings.get("language"))
        self.theme: ThemeCode = self._normalize_theme(settings.get("theme"))

    def _load_settings(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _normalize_language(self, language: object) -> LanguageCode:
        value = str(language or DEFAULT_LANGUAGE)
        return value if value in LANGUAGE_OPTIONS else DEFAULT_LANGUAGE  # type: ignore[return-value]

    def _normalize_theme(self, theme: object) -> ThemeCode:
        value = str(theme or DEFAULT_THEME)
        return value if value in THEME_OPTIONS[DEFAULT_LANGUAGE] else DEFAULT_THEME  # type: ignore[return-value]

    def _save_settings(self) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(
            json.dumps({"language": self.language, "theme": self.theme}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def set_language(self, language: str) -> None:
        self.language = self._normalize_language(language)
        self._save_settings()

    def set_theme(self, theme: str) -> None:
        self.theme = self._normalize_theme(theme)
        self._save_settings()

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
