"""CS_LLM FEM-ready 候选响应的机器导入合同。"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

from core.fem_input_contract import validate_fem_input
from core.io_utils import read_json, write_json
from core.id_utils import next_task_id
from core.paths import IO_DIR
from core.task_contract import build_task_request_record


FEM_READY_GENERATION_MODE = "fem_ready_cylindrical_shell"
FEM_READY_CONTRACT_VERSION = "1"
FEM_READY_SCHEMA_VERSION = "2"
FEM_SOURCE_TABLE_SHA256 = "04ba2a97d0979d270a21dff8b470fc6052ef5418208224cc3dcac3cd8e316c97"


class FEMCandidateTransferError(ValueError):
    """表示外部候选响应不满足当前 CSDM_cph 输入合同。"""


def _fingerprint(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate_screening_classification(candidate: Dict[str, Any], index: int) -> None:
    """复核历史筛选角色，禁止把来源参考值写成当前 Abaqus 结论。"""
    screening = candidate.get("screening")
    provenance = candidate.get("provenance")
    targets = candidate.get("design_targets")
    if not isinstance(screening, dict) or not isinstance(provenance, dict) or not isinstance(targets, dict):
        raise FEMCandidateTransferError(f"FEM-ready 候选 {index} 缺少筛选分类。")
    if screening.get("current_abaqus_status") != "not_run" or screening.get("current_design_verdict") != "pending":
        raise FEMCandidateTransferError(f"FEM-ready 候选 {index} 冒充当前有限元结果。")
    historical = provenance.get("historical_fem_reference")
    if not isinstance(historical, dict) or historical.get("status") != "screening_reference_only_not_current_run":
        raise FEMCandidateTransferError(f"FEM-ready 候选 {index} 历史结果边界无效。")
    try:
        source_meets = float(historical["ultimate_pressure_MPa"]) >= float(targets["ultimate_pressure_min_MPa"])
    except (KeyError, TypeError, ValueError) as exc:
        raise FEMCandidateTransferError(f"FEM-ready 候选 {index} 历史筛选数值无效。") from exc
    geometry_match = provenance.get("geometry_match")
    expected_role = (
        "historically_screened_baseline"
        if geometry_match == "exact" and source_meets
        else "exact_geometry_exploration"
        if geometry_match == "exact"
        else "nearest_neighbor_transfer_exploration"
        if geometry_match == "nearest_neighbor_transfer"
        else ""
    )
    expected_comparison = (
        "at_or_above_target_for_same_geometry"
        if expected_role == "historically_screened_baseline"
        else "below_target_for_same_geometry"
        if expected_role == "exact_geometry_exploration"
        else "not_applicable_after_geometry_transfer"
        if expected_role == "nearest_neighbor_transfer_exploration"
        else ""
    )
    if not expected_role or screening.get("candidate_role") != expected_role:
        raise FEMCandidateTransferError(f"FEM-ready 候选 {index} 候选角色与来源不一致。")
    if screening.get("historical_reference_comparison") != expected_comparison:
        raise FEMCandidateTransferError(f"FEM-ready 候选 {index} 历史比较标签与来源不一致。")


def validate_fem_ready_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """验证设计服务响应并返回可进入有限元队列的候选副本。"""
    if not isinstance(response, dict):
        raise FEMCandidateTransferError("FEM-ready 响应必须是 JSON 对象。")
    if response.get("status") != "passed":
        raise FEMCandidateTransferError("FEM-ready 响应状态不是 passed。")
    if response.get("generation_mode") != FEM_READY_GENERATION_MODE:
        raise FEMCandidateTransferError("FEM-ready generation_mode 无效。")
    if str(response.get("contract_version")) != FEM_READY_CONTRACT_VERSION:
        raise FEMCandidateTransferError("FEM-ready contract_version 无效。")

    result = response.get("result")
    if not isinstance(result, dict):
        raise FEMCandidateTransferError("FEM-ready 响应缺少 result。")
    if str(result.get("schema_version")) != FEM_READY_SCHEMA_VERSION:
        raise FEMCandidateTransferError("FEM-ready schema_version 无效。")
    if str(result.get("contract_version")) != FEM_READY_CONTRACT_VERSION:
        raise FEMCandidateTransferError("FEM-ready result.contract_version 无效。")
    if result.get("generation_mode") != FEM_READY_GENERATION_MODE:
        raise FEMCandidateTransferError("FEM-ready result.generation_mode 无效。")

    source_table = result.get("source_table")
    if not isinstance(source_table, dict) or source_table.get("sha256") != FEM_SOURCE_TABLE_SHA256:
        raise FEMCandidateTransferError("FEM-ready 正式有限元表格指纹无效。")
    candidates = result.get("candidates")
    candidate_count = result.get("candidate_count")
    if not isinstance(candidates, list) or isinstance(candidate_count, bool) or candidate_count != len(candidates):
        raise FEMCandidateTransferError("FEM-ready 候选数量字段不一致。")
    if not candidates:
        raise FEMCandidateTransferError("FEM-ready 候选列表为空。")

    revisions: set[str] = set()
    normalized: List[Dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, dict):
            raise FEMCandidateTransferError(f"FEM-ready 候选 {index} 不是对象。")
        if candidate.get("candidate_id") != f"TMP_{index}":
            raise FEMCandidateTransferError(f"FEM-ready 候选 {index} 编号不连续。")
        provenance = candidate.get("provenance")
        if not isinstance(provenance, dict) or provenance.get("source_sha256") != FEM_SOURCE_TABLE_SHA256:
            raise FEMCandidateTransferError(f"FEM-ready 候选 {index} 来源指纹无效。")
        _validate_screening_classification(candidate, index)
        issues = validate_fem_input(candidate)
        if issues:
            raise FEMCandidateTransferError(
                f"FEM-ready 候选 {index} 输入不完整或不一致：" + ", ".join(issues)
            )
        revision = str(candidate.get("design_revision_id") or "")
        if revision in revisions:
            raise FEMCandidateTransferError("FEM-ready 响应包含重复 design_revision_id。")
        revisions.add(revision)
        normalized.append(deepcopy(candidate))

    expected_fingerprint = _fingerprint(
        {
            "request": result.get("request"),
            "source_table": source_table,
            "candidates": candidates,
        }
    )
    if result.get("design_fingerprint") != expected_fingerprint:
        raise FEMCandidateTransferError("FEM-ready design_fingerprint 与候选内容不一致。")
    return normalized


def import_fem_ready_response(path: Path, output_path: Path | None = None) -> Dict[str, Any]:
    """从 UTF-8 JSON 文件导入并保存已验证的机器候选包。"""
    response = read_json(path)
    candidates = validate_fem_ready_response(response)
    result = response["result"]
    target = output_path or IO_DIR / f"imported_fem_{result['design_fingerprint']}.json"
    payload = {
        "status": "validated",
        "generation_mode": FEM_READY_GENERATION_MODE,
        "contract_version": FEM_READY_CONTRACT_VERSION,
        "source_table": deepcopy(result["source_table"]),
        "request": deepcopy(result["request"]),
        "candidate_count": len(candidates),
        "design_fingerprint": result["design_fingerprint"],
        "candidates": candidates,
    }
    write_json(target, payload)
    return {"path": str(target), "payload": payload}


def build_fem_ready_task_record(payload: Dict[str, Any]) -> Dict[str, Any]:
    """把已验证的设计请求转换为 CSDM_cph 任务记录，不从自然语言反解析字段。"""
    request = payload.get("request")
    candidates = payload.get("candidates")
    if not isinstance(request, dict) or not isinstance(candidates, list) or not candidates:
        raise FEMCandidateTransferError("FEM-ready 候选包缺少 request 或 candidates。")
    geometry = request.get("geometry") or {}
    length = geometry.get("length_mm")
    radius = geometry.get("radius_mm")
    angles = sorted(
        {
            abs(float(angle))
            for candidate in candidates
            for angle in (candidate.get("layup") or {}).get("angles_deg", [])
        }
    )
    task_payload = {
        "application": str(request.get("structure_form") or "复合材料外压圆柱耐压壳"),
        "hull_type": "CYLINDRICAL",
        "load_conditions": deepcopy(request.get("load_conditions") or {}),
        "boundary_conditions": deepcopy(request.get("boundary_conditions") or {}),
        "geometry_envelope": {
            "length_mm": [length, length],
            "radius_mm": [radius, radius],
        },
        "candidate_generation_preferences": {
            "total_candidates": len(candidates),
        },
        "screening_preferences": {
            "top_k_candidates": min(len(candidates), 30),
        },
        "layup_constraints": {
            "allowed_angles_deg": angles,
            "symmetric": all(bool((candidate.get("layup") or {}).get("symmetric")) for candidate in candidates),
            "balanced": all(bool((candidate.get("layup") or {}).get("balanced")) for candidate in candidates),
        },
        "design_targets": deepcopy(request.get("design_targets") or {}),
        "user_input_facts": {
            "fixed_geometry": {"length_mm": length, "radius_mm": radius},
            "load_conditions": deepcopy(request.get("load_conditions") or {}),
            "boundary_conditions": deepcopy(request.get("boundary_conditions") or {}),
            "design_targets": deepcopy(request.get("design_targets") or {}),
        },
    }
    return build_task_request_record(
        task_payload,
        task_id=next_task_id(),
        source="csllm_fem_ready",
    )
