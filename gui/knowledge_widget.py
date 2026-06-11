"""知识库展示与证据检索组件。"""

from __future__ import annotations

import json
from html import escape
from typing import Any

from PyQt6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QTextBrowser, QVBoxLayout, QWidget

from core.case_memory import CaseMemoryIndex
from core.domain_knowledge import DomainKnowledgeBase
from core.paths import ABAQUS_RUNS_DIR, CASES_DIR, CASE_LIBRARY_DIR, MODELS_DIR


DEFAULT_EVIDENCE_QUERY = "复合材料外压圆柱耐压壳 外部静水压力 线性屈曲 极限压力 初始缺陷 制造质量控制"


class KnowledgeWidget(QWidget):
    """展示案例库、外部知识库/知识图谱、代理模型指标和检索证据。"""

    def __init__(self) -> None:
        super().__init__()
        self.knowledge_base = DomainKnowledgeBase()
        self._last_task: dict[str, Any] | None = None

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入工程检索词，例如：外压圆柱壳 屈曲 缺陷敏感性 制造质量控制")
        self.search_button = QPushButton("检索证据")
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)

        search_layout = QHBoxLayout()
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.search_button)

        layout = QVBoxLayout(self)
        layout.addLayout(search_layout)
        layout.addWidget(self.browser, 1)

        self.search_button.clicked.connect(self._search_from_input)
        self.search_input.returnPressed.connect(self._search_from_input)

    def refresh(self, task: dict[str, Any] | None = None, query_text: str | None = None) -> None:
        if task is not None:
            self._last_task = task

        archive_cases = sorted(CASES_DIR.glob("CASE_*.json"))
        formal_cases = sorted(CASE_LIBRARY_DIR.glob("CASE_*.json"))
        metrics = self._load_metrics()
        knowledge_status = self.knowledge_base.status()
        case_memory_count = self._case_memory_count()
        odb_count, vis_count = self._abaqus_archive_counts()
        evidence_payload = self._retrieve_evidence(task, query_text)

        lines = [
            self._status_html(
                archive_case_count=len(archive_cases),
                formal_case_count=len(formal_cases),
                case_memory_count=case_memory_count,
                odb_count=odb_count,
                vis_count=vis_count,
                metrics=metrics,
                knowledge_status=knowledge_status,
            ),
            self._evidence_html(evidence_payload),
            self._latest_cases_html(formal_cases),
        ]
        self.browser.setHtml("".join(lines))

    def toHtml(self) -> str:
        """兼容测试与外部调用读取当前 HTML。"""
        return self.browser.toHtml()

    def _search_from_input(self) -> None:
        query = self.search_input.text().strip()
        self.refresh(query_text=query or DEFAULT_EVIDENCE_QUERY)

    def _retrieve_evidence(self, task: dict[str, Any] | None, query_text: str | None) -> dict[str, Any]:
        if query_text is not None:
            query = query_text.strip() or DEFAULT_EVIDENCE_QUERY
            self.search_input.setText(query)
            return self.knowledge_base.retrieve_by_query(query, top_k=3, kg_top_k=5)

        active_task = task if task is not None else self._last_task
        if active_task:
            return self.knowledge_base.retrieve(active_task, top_k=3, kg_top_k=5)

        query = self.search_input.text().strip() or DEFAULT_EVIDENCE_QUERY
        self.search_input.setText(query)
        return self.knowledge_base.retrieve_by_query(query, top_k=3, kg_top_k=5)

    def _load_metrics(self) -> dict[str, Any]:
        metrics_path = MODELS_DIR / "surrogate_metrics.json"
        if not metrics_path.exists():
            return {}
        try:
            payload = json.loads(metrics_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
        return payload if isinstance(payload, dict) else {}

    def _case_memory_count(self) -> int:
        try:
            return int(CaseMemoryIndex().engine.count())
        except Exception:
            return 0

    def _abaqus_archive_counts(self) -> tuple[int, int]:
        odb_count = 0
        vis_count = 0
        for run_dir in ABAQUS_RUNS_DIR.glob("C*"):
            if (run_dir / f"{run_dir.name}.odb").exists():
                odb_count += 1
            if (run_dir / f"{run_dir.name}_mode1.json").exists():
                vis_count += 1
        return odb_count, vis_count

    def _status_html(
        self,
        *,
        archive_case_count: int,
        formal_case_count: int,
        case_memory_count: int,
        odb_count: int,
        vis_count: int,
        metrics: dict[str, Any],
        knowledge_status: dict[str, Any],
    ) -> str:
        knowledge_ready = "可用" if knowledge_status.get("ready") else "未就绪"
        lines = [
            "<h2>知识库状态</h2>",
            "<p><b>评估档案数：</b>"
            f"{archive_case_count}<br>"
            f"<b>正式案例库数：</b>{formal_case_count}<br>"
            f"<b>案例记忆向量块数：</b>{case_memory_count}<br>"
            f"<b>已归档 ODB 数：</b>{odb_count}<br>"
            f"<b>模态可视化数据数：</b>{vis_count}</p>",
            "<p>说明：候选方案只保存在当前会话中；完成 Abaqus 校核后会进入评估档案。"
            "只有校核结论为“通过”的样本才会进入正式案例库；案例记忆向量库用于相似案例召回和排序，"
            "不替代结构化迁移约束。</p>",
        ]

        if metrics:
            lines.extend(
                [
                    "<h3>代理模型指标</h3>",
                    "<p>",
                    f"<b>当前模型：</b>{escape(str(metrics.get('selected_model', '-')))}<br>",
                    f"<b>训练样本数：</b>{escape(str(metrics.get('training_size', '-')))}<br>",
                    f"<b>RF MAPE：</b>{escape(str(metrics.get('rf', {}).get('mape', '-')))}<br>",
                    f"<b>RF RMSE：</b>{escape(str(metrics.get('rf', {}).get('rmse', '-')))}<br>",
                    f"<b>MLP MAPE：</b>{escape(str(metrics.get('mlp', {}).get('mape', '-')))}<br>",
                    f"<b>MLP RMSE：</b>{escape(str(metrics.get('mlp', {}).get('rmse', '-')))}</p>",
                ]
            )

        lines.extend(
            [
                "<h3>外部知识库/知识图谱状态</h3>",
                "<p>",
                f"<b>运行状态：</b>{knowledge_ready}<br>",
                f"<b>知识库文本块数：</b>{knowledge_status.get('rag_chunk_count', 0)}<br>",
                f"<b>知识图谱实体数：</b>{knowledge_status.get('kg_entity_count', 0)}<br>",
                f"<b>知识图谱关系数：</b>{knowledge_status.get('kg_relation_count', 0)}<br>",
                f"<b>源登记记录数：</b>{knowledge_status.get('source_registry_count', 0)}<br>",
                f"<b>源元数据记录数：</b>{knowledge_status.get('source_metadata_count', 0)}<br>",
                f"<b>结构化文档数：</b>{knowledge_status.get('structured_document_count', 0)}<br>",
                f"<b>结构化文本块数：</b>{knowledge_status.get('structured_block_count', 0)}<br>",
                f"<b>表格记录数：</b>{knowledge_status.get('table_record_count', 0)}<br>",
                f"<b>图片记录数：</b>{knowledge_status.get('figure_record_count', 0)}<br>",
                f"<b>公式记录数：</b>{knowledge_status.get('formula_record_count', 0)}<br>",
                f"<b>Markdown 全文数：</b>{knowledge_status.get('markdown_document_count', 0)}<br>",
                f"<b>知识清单：</b>{escape(str(knowledge_status.get('manifest_path') or '-'))}<br>",
                f"<b>溯源资料目录：</b>{escape(str(knowledge_status.get('provenance_dir') or '-'))}<br>",
                f"<b>更新时间：</b>{escape(str(knowledge_status.get('updated_at') or '-'))}",
                "</p>",
            ]
        )
        return "".join(lines)

    def _evidence_html(self, payload: dict[str, Any]) -> str:
        query = str(payload.get("query") or "").strip()
        chunks = payload.get("chunks") if isinstance(payload.get("chunks"), list) else []
        relations = payload.get("relations") if isinstance(payload.get("relations"), list) else []

        lines = [
            "<h3>外部知识证据预览</h3>",
            "<p>证据预览用于审计候选生成 LLM 的工程上下文和人工核查来源，"
            "不作为确定性数值来源；代理公式、排序、有限元结果和案例入库由系统工程逻辑确定。</p>",
            f"<p><b>当前检索词：</b>{escape(query or '-')}</p>",
        ]

        lines.append("<h4>RAG 命中文本块</h4>")
        if chunks:
            for index, item in enumerate(chunks, start=1):
                title = item.get("document_title") or item.get("title") or item.get("record_id") or f"资料片段 {index}"
                page = self._page_text(item)
                score = item.get("score", "-")
                source_parts = [
                    f"记录：{item.get('record_id')}" if item.get("record_id") else "",
                    f"来源：{item.get('source_id')}" if item.get("source_id") else "",
                    f"页码：{page}" if page else "",
                    f"DOI：{item.get('doi')}" if item.get("doi") else "",
                    f"URL：{item.get('source_url')}" if item.get("source_url") else "",
                ]
                source_line = "；".join(escape(str(part)) for part in source_parts if part)
                text = escape(str(item.get("text") or ""))
                lines.append(
                    "<div style='margin-bottom:12px;'>"
                    f"<b>{index}. {escape(str(title))}</b><br>"
                    f"<span>得分：{escape(str(score))}</span><br>"
                    f"<span>{source_line}</span><br>"
                    f"<p>{text}</p>"
                    "</div>"
                )
        else:
            lines.append("<p>当前没有命中的 RAG 文本块。</p>")

        lines.append("<h4>知识图谱关系</h4>")
        if relations:
            for index, item in enumerate(relations, start=1):
                source = escape(str(item.get("source") or "-"))
                source_type = escape(str(item.get("source_type") or "-"))
                relation = escape(str(item.get("relation") or "-"))
                target = escape(str(item.get("target") or "-"))
                target_type = escape(str(item.get("target_type") or "-"))
                evidence = escape(str(item.get("evidence_document_title") or item.get("record_id") or ""))
                score = escape(str(item.get("score", "-")))
                lines.append(
                    "<p>"
                    f"<b>{index}. {source}({source_type}) -[{relation}]-&gt; {target}({target_type})</b><br>"
                    f"得分：{score}"
                    f"{'<br>依据：' + evidence if evidence else ''}"
                    "</p>"
                )
        else:
            lines.append("<p>当前没有命中的知识图谱关系。</p>")

        return "".join(lines)

    def _latest_cases_html(self, formal_cases: list[Any]) -> str:
        lines = ["<h3>最新正式案例</h3>"]
        if formal_cases:
            for path in formal_cases[-10:]:
                lines.append(f"<p>{escape(path.stem)}</p>")
        else:
            lines.append("<p>当前还没有“通过”并进入正式案例库的样本。</p>")
        return "".join(lines)

    def _page_text(self, item: dict[str, Any]) -> str:
        page_start = item.get("page_start")
        page_end = item.get("page_end")
        if page_start in (None, ""):
            return ""
        if page_end in (None, "", page_start):
            return str(page_start)
        return f"{page_start}-{page_end}"
