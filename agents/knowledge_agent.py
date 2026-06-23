"""知识回流智能体。"""

from __future__ import annotations

from datetime import datetime
from typing import Dict

from agents.base import BaseAgent
from core.case_memory import CaseMemoryIndex
from core.config_loader import load_app_config
from core.id_utils import next_case_id
from core.io_utils import write_json
from core.paths import CASE_LIBRARY_DIR, CASES_DIR
from core.schema_validator import validate_or_raise
from core.surrogate_model import SurrogateModelManager
from core.task_contract import (
    normalize_boundary_conditions,
    normalize_load_conditions,
    task_payload_from_request,
)


class KnowledgeAgent(BaseAgent):
    agent_name = "KNOWLEDGE_AGENT"

    def __init__(self, progress_callback=None) -> None:
        super().__init__(progress_callback=progress_callback)
        self.case_memory = None
        self._case_memory_unavailable = False
        self.model_manager = SurrogateModelManager()
        self.config = load_app_config()
        self.min_case_records_for_retrain = int(self.config["pipeline"]["min_case_records_for_retrain"])

    def _sanitize_task(self, task: Dict) -> Dict:
        normalized = task_payload_from_request(task)
        return {
            "application": normalized.get("application"),
            "load_conditions": dict(normalized.get("load_conditions", {})),
            "boundary_conditions": dict(normalized.get("boundary_conditions", {})),
            "geometry_envelope": dict(normalized.get("geometry_envelope", {})),
            "material_system": dict(normalized.get("material_system", {})),
            "layup_constraints": dict(normalized.get("layup_constraints", {})),
            "candidate_generation_preferences": dict(normalized.get("candidate_generation_preferences", {})),
            "screening_preferences": dict(normalized.get("screening_preferences", {})),
            "hull_type": normalized.get("hull_type", "CYLINDRICAL"),
            "design_targets": dict(normalized.get("design_targets", {})),
        }

    def _sanitize_design(self, design: Dict) -> Dict:
        payload = {
            "candidate_id": design.get("candidate_id"),
            "display_name": design.get("display_name") or design.get("candidate_id"),
            "source": design.get("source"),
            "hull_type": design.get("hull_type", "CYLINDRICAL"),
            "geometry": dict(design.get("geometry", {})),
            "layup": dict(design.get("layup", {})),
            "material_system": dict(design.get("material_system", {})),
            "load_conditions": dict(normalize_load_conditions(design.get("load_conditions", {}))),
            "boundary_conditions": dict(normalize_boundary_conditions(design.get("boundary_conditions", {}))),
            "design_targets": dict(design.get("design_targets", {})),
            "rule_check": dict(design.get("rule_check", {})),
            "surrogate_ultimate_pressure_MPa": design.get("surrogate_ultimate_pressure_MPa"),
            "surrogate_PBIPF_MPa": design.get("surrogate_PBIPF_MPa"),
            "surrogate_uncertainty_MPa": design.get("surrogate_uncertainty_MPa"),
            "asme_linear_buckling_pressure_MPa": design.get("asme_linear_buckling_pressure_MPa"),
            "linear_buckling_source": design.get("linear_buckling_source"),
            "surrogate_weight": design.get("surrogate_weight"),
            "rationale": design.get("rationale", ""),
            "origin_summary": design.get("origin_summary", ""),
            "llm_output_excerpt": design.get("llm_output_excerpt"),
        }
        session_candidate_id = str(design.get("session_candidate_id") or "").strip()
        if session_candidate_id:
            payload["session_candidate_id"] = session_candidate_id
        return payload

    def _sanitize_abaqus_results(self, abaqus_results: Dict) -> Dict:
        keys = [
            "candidate_id",
            "session_candidate_id",
            "display_name",
            "status",
            "retry_count",
            "ultimate_pressure_MPa",
            "failure_pressure_MPa",
            "linear_buckling_pressure_MPa",
            "first_mode_eigenvalue",
            "postbuckling_pressure_MPa",
            "postbuckling_reference_pressure_MPa",
            "postbuckling_last_pressure_MPa",
            "riks_lpf_max",
            "riks_lpf_last",
            "riks_time_at_lpf_max",
            "riks_time_last",
            "imperfection_amplitude_mm",
            "ultimate_pressure_basis",
            "failure_mode",
            "max_displacement_mm",
            "weight_kg_per_m2",
            "verdict",
            "abaqus_odb",
            "linear_buckling_odb",
            "postbuckling_odb",
            "abaqus_inp",
            "postbuckling_inp",
            "visualization_json",
            "artifact_dir",
            "error_type",
            "error_log",
            "mode_eigenvalues",
            "load_summary",
            "boundary_summary",
            "diagnosis_summary",
            "analysis_type",
            "user_subroutine_used",
        ]
        return {key: abaqus_results.get(key) for key in keys}

    def _result_pressure(self, results: Dict) -> float | None:
        for key in ["ultimate_pressure_MPa", "failure_pressure_MPa", "linear_buckling_pressure_MPa"]:
            value = results.get(key)
            if value is not None:
                return float(value)
        return None

    def _build_record(self, task: Dict, design: Dict, abaqus_results: Dict) -> Dict:
        clean_task = self._sanitize_task(task)
        clean_design = self._sanitize_design(design)
        clean_results = self._sanitize_abaqus_results(abaqus_results)
        case_id = next_case_id(clean_design.get("candidate_id"))
        verdict = clean_results.get("verdict") or ("失败" if clean_results.get("status") != "success" else "未知")
        predicted = clean_design.get("surrogate_ultimate_pressure_MPa")
        actual = self._result_pressure(clean_results)
        record = {
            "case_id": case_id,
            "candidate_id": clean_design.get("candidate_id"),
            "display_name": clean_design.get("display_name") or clean_design.get("candidate_id"),
            "created_at": datetime.utcnow().isoformat(),
            "source": "abaqus_auto",
            "task": clean_task,
            "design": clean_design,
            "abaqus_results": clean_results,
            "verdict": verdict,
            "surrogate_pressure_error_pct": None
            if predicted is None or actual is None
            else round(abs(float(predicted) - actual) / max(actual, 1e-6) * 100.0, 3),
            "fem_agent_retry_count": int(clean_results.get("retry_count", 0) or 0),
        }
        task_id = str(task.get("task_id") or "").strip()
        if task_id:
            record["task_id"] = task_id
        session_candidate_id = str(clean_design.get("session_candidate_id") or clean_results.get("session_candidate_id") or "").strip()
        if session_candidate_id:
            record["session_candidate_id"] = session_candidate_id
        validate_or_raise("case_record.schema.json", record)
        return record

    def _should_store_record(self, abaqus_results: Dict) -> bool:
        return abaqus_results.get("status") == "success" and abaqus_results.get("verdict") == "通过"

    def _case_memory_index(self) -> CaseMemoryIndex | None:
        if getattr(self, "_case_memory_unavailable", False):
            return None
        if getattr(self, "case_memory", None) is not None:
            return self.case_memory
        try:
            self.case_memory = CaseMemoryIndex()
        except Exception as exc:
            self.case_memory = None
            self._case_memory_unavailable = True
            self.emit(f"案例向量记忆初始化失败，仅写入 JSON 案例：{exc}")
        return self.case_memory

    def _store_record(self, record: Dict) -> None:
        write_json(CASES_DIR / f"{record['case_id']}.json", record)
        case_memory = self._case_memory_index()
        if self._should_store_record(record.get("abaqus_results", {})):
            write_json(CASE_LIBRARY_DIR / f"{record['case_id']}.json", record)
            if case_memory is not None:
                try:
                    case_memory.upsert_cases([record], scope="formal")
                except Exception as exc:
                    self.case_memory = None
                    self._case_memory_unavailable = True
                    self.emit(f"案例向量记忆写入失败，JSON 案例已保存：{exc}")
        elif case_memory is not None:
            try:
                case_memory.upsert_cases([record], scope="archive")
            except Exception as exc:
                self.case_memory = None
                self._case_memory_unavailable = True
                self.emit(f"案例向量记忆写入失败，JSON 案例已保存：{exc}")

    def _maybe_retrain_surrogate(self) -> Dict | None:
        records = self.model_manager.load_training_records()
        record_count = len(records)
        if record_count < self.min_case_records_for_retrain:
            return None
        if record_count % self.min_case_records_for_retrain != 0:
            return None

        summary = self.model_manager.train_from_records(records)
        self.emit(
            "代理公式校准已更新："
            f"样本数={summary['training_size']} | "
            f"bias={summary['bias_MPa']:.4f} MPa | "
            f"scale={summary['scale']:.4f}"
        )
        return summary

    def run(self, input_data: Dict) -> Dict:
        task = input_data["task"]
        design = input_data["design"]
        abaqus_results = input_data["abaqus_results"]

        record = self._build_record(task, design, abaqus_results)
        self._store_record(record)
        if self._should_store_record(record["abaqus_results"]):
            self.emit(f"案例 {record['case_id']} 已进入正式案例库")
        else:
            self.emit(f"案例 {record['case_id']} 已归档到评估档案，未进入正式案例库")

        retrain_summary = self._maybe_retrain_surrogate()
        return {
            "status": "stored" if self._should_store_record(record["abaqus_results"]) else "archived_only",
            "case_id": record["case_id"],
            "retrained": retrain_summary is not None,
            "surrogate_summary": retrain_summary,
        }
