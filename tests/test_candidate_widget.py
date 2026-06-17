import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from gui.candidate_widget import CandidateWidget


def _app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _candidate() -> dict:
    return {
        "candidate_id": "TMP_1",
        "display_name": "TMP_1",
        "source": "LLM",
        "hull_type": "CYLINDRICAL",
        "geometry": {
            "length_mm": 500.0,
            "radius_mm": 100.0,
            "thickness_mm": 10.0,
            "alpha_deg": 35.0,
            "beta_deg": 65.0,
            "imperfection_ratio": 0.005,
        },
        "layup": {
            "template_name": "PC1",
            "layup": "[90_4/(±35/±65)_8/90_4]",
            "skin_layup": "[90_4/(±35/±65)_8/90_4]",
            "ply_count": 40,
            "angles_deg": [90, 35, -35, 65, -65],
        },
        "material_system": {"name": "T700/Epoxy"},
        "load_conditions": {"type": "external_pressure", "external_pressure_MPa": 30.0},
        "boundary_conditions": {"type": "END_CLAMPED", "label": "两端固支"},
        "design_targets": {"ultimate_pressure_min_MPa": 35.0},
        "rule_check": {"is_valid": True, "errors": [], "suggestions": []},
        "rationale": "结构性能和制造风险均衡。",
        "generation_audit": {
            "source_targets": {"total": 4, "LLM": 2, "CASE_TRANSFER": 1, "DOE": 1},
            "raw_counts": {"LLM": 2, "CASE_TRANSFER": 1, "DOE": 2},
            "valid_counts": {"LLM": 1, "CASE_TRANSFER": 1, "DOE": 2},
            "invalid_counts": {"LLM": 1, "CASE_TRANSFER": 0, "DOE": 0},
            "added_counts": {"LLM": 1, "CASE_TRANSFER": 1, "DOE": 2},
            "duplicate_counts": {"LLM": 0, "CASE_TRANSFER": 0, "DOE": 1, "total": 1},
            "filter_reasons": {"LLM": ["TMP_2: radius_mm 超出范围"], "CASE_TRANSFER": [], "DOE": []},
            "doe_rounds": 2,
            "doe_fill_count": 2,
            "summary": "初始配额 LLM=2 / 案例迁移=1 / DOE=1；有效进入候选池 LLM=1，案例迁移=1，DOE补足=2；结构去重=1",
        },
    }


def test_candidate_widget_renders_generation_audit() -> None:
    app = _app()
    widget = CandidateWidget()
    selected: list[dict] = []
    try:
        widget.candidateSelected.connect(lambda candidate: selected.append(candidate))
        widget.update_candidates([_candidate()])
        html = widget.audit_browser.toHtml()

        assert "来源审计" in widget.summary_label.text()
        assert "候选来源与去重审计" in html
        assert "初始配额" in html
        assert "规则过滤原因" in html
        assert "radius_mm 超出范围" in html
        assert "DOE 补足" in html
        assert widget.total_metric.text().endswith("1")
        assert widget.llm_metric.text().endswith("1")
        assert widget.detail_tabs.count() == 2
        assert selected and selected[-1]["candidate_id"] == "TMP_1"
    finally:
        widget.close()
        app.processEvents()
