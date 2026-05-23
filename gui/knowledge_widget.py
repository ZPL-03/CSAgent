"""知识库展示组件。"""

from __future__ import annotations

import json

from PyQt6.QtWidgets import QTextBrowser

from core.case_memory import CaseMemoryIndex
from core.domain_knowledge import DomainKnowledgeBase
from core.paths import ABAQUS_RUNS_DIR, CASES_DIR, CASE_LIBRARY_DIR, MODELS_DIR


class KnowledgeWidget(QTextBrowser):
    """展示案例库、外部知识库/知识图谱和代理模型指标。"""

    def refresh(self) -> None:
        archive_cases = sorted(CASES_DIR.glob("CASE_*.json"))
        formal_cases = sorted(CASE_LIBRARY_DIR.glob("CASE_*.json"))
        metrics_path = MODELS_DIR / "surrogate_metrics.json"
        metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.exists() else {}
        knowledge_status = DomainKnowledgeBase().status()
        try:
            case_memory_count = CaseMemoryIndex().engine.count()
        except Exception:
            case_memory_count = 0

        odb_count = 0
        vis_count = 0
        for run_dir in ABAQUS_RUNS_DIR.glob("C*"):
            if (run_dir / f"{run_dir.name}.odb").exists():
                odb_count += 1
            if (run_dir / f"{run_dir.name}_mode1.json").exists():
                vis_count += 1

        lines = [
            "<h2>知识库状态</h2>",
            "<p><b>评估档案数：</b>"
            f"{len(archive_cases)}<br>"
            f"<b>正式案例库数：</b>{len(formal_cases)}<br>"
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
                    f"<b>当前模型：</b>{metrics.get('selected_model', '-')}<br>",
                    f"<b>训练样本数：</b>{metrics.get('training_size', '-')}<br>",
                    f"<b>RF MAPE：</b>{metrics.get('rf', {}).get('mape', '-')}<br>",
                    f"<b>RF RMSE：</b>{metrics.get('rf', {}).get('rmse', '-')}<br>",
                    f"<b>MLP MAPE：</b>{metrics.get('mlp', {}).get('mape', '-')}<br>",
                    f"<b>MLP RMSE：</b>{metrics.get('mlp', {}).get('rmse', '-')}</p>",
                ]
            )

        knowledge_ready = "可用" if knowledge_status.get("ready") else "未就绪"
        lines.extend(
            [
                "<h3>外部知识库/知识图谱状态</h3>",
                "<p>",
                f"<b>运行状态：</b>{knowledge_ready}<br>",
                f"<b>知识库文本块数：</b>{knowledge_status.get('rag_chunk_count', 0)}<br>",
                f"<b>知识图谱实体数：</b>{knowledge_status.get('kg_entity_count', 0)}<br>",
                f"<b>知识图谱关系数：</b>{knowledge_status.get('kg_relation_count', 0)}<br>",
                f"<b>源登记记录数：</b>{knowledge_status.get('source_registry_count', 0)}<br>",
                f"<b>结构化文档数：</b>{knowledge_status.get('structured_document_count', 0)}<br>",
                f"<b>Markdown 全文数：</b>{knowledge_status.get('markdown_document_count', 0)}<br>",
                f"<b>知识清单：</b>{knowledge_status.get('manifest_path') or '-'}<br>",
                f"<b>溯源资料目录：</b>{knowledge_status.get('provenance_dir') or '-'}<br>",
                f"<b>更新时间：</b>{knowledge_status.get('updated_at') or '-'}",
                "</p>",
            ]
        )

        lines.append("<h3>最新正式案例</h3>")
        if formal_cases:
            for path in formal_cases[-10:]:
                lines.append(f"<p>{path.stem}</p>")
        else:
            lines.append("<p>当前还没有“通过”并进入正式案例库的样本。</p>")

        self.setHtml("".join(lines))
