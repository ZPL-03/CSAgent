"""统一管理任务实例、候选方案与案例编号。"""

from __future__ import annotations

import hashlib
import json
import re
import uuid

from core.io_utils import read_json
from core.paths import CASE_LIBRARY_DIR, CASES_DIR, TASKS_DIR


TASK_PATTERN = re.compile(r"^TASK_(\d+)$")
CANDIDATE_PATTERN = re.compile(r"^C(\d+)$")
TEMP_CANDIDATE_PATTERN = re.compile(r"^TMP_(\d+)$")
CASE_PATTERN = re.compile(r"^CASE_(\d+)$")
REQUEST_PATTERN = re.compile(r"^REQ_[A-F0-9]{12}$")
TASK_FINGERPRINT_PATTERN = re.compile(r"^TFP_[A-F0-9]{16}$")


def _parse_index(value: str, pattern: re.Pattern[str]) -> int | None:
    match = pattern.match(value)
    if not match:
        return None
    return int(match.group(1))


def format_task_id(index: int) -> str:
    return f"TASK_{index}"


def format_candidate_id(index: int) -> str:
    return f"C{index}"


def new_request_id() -> str:
    return f"REQ_{uuid.uuid4().hex[:12].upper()}"


def format_task_fingerprint(digest: str) -> str:
    return f"TFP_{digest[:16].upper()}"


def task_index(task_id: str) -> int | None:
    return _parse_index(str(task_id), TASK_PATTERN)


def next_task_index() -> int:
    indices = []
    for path in TASKS_DIR.glob("TASK_*.json"):
        parsed = _parse_index(path.stem, TASK_PATTERN)
        if parsed is not None:
            indices.append(parsed)
    return max(indices, default=0) + 1


def next_task_id() -> str:
    return format_task_id(next_task_index())


def task_file_name(task_id: str) -> str:
    return f"{str(task_id).strip()}.json"


def task_display_label(task_id: str | None) -> str:
    return str(task_id or "").strip() or "-"


def task_file_name_for_payload(payload: dict) -> str:
    return task_file_name(str(payload.get("task_id") or "").strip())


def task_identity_payload(task_id: str) -> dict:
    return {"task_id": str(task_id).strip()}


def task_fingerprint_seed(task: dict) -> str:
    normalized = dict(task)
    normalized.pop("task_id", None)
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def task_fingerprint(task: dict) -> str:
    normalized = task_fingerprint_seed(task)
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()
    return format_task_fingerprint(digest)


def request_identity_payload(request_id: str | None, task_fp: str | None) -> dict:
    payload = {}
    if str(request_id or "").strip():
        payload["request_id"] = str(request_id).strip()
    if str(task_fp or "").strip():
        payload["task_fingerprint"] = str(task_fp).strip()
    return payload


def is_task_id(value: str | None) -> bool:
    return bool(TASK_PATTERN.match(str(value or "")))


def is_request_id(value: str | None) -> bool:
    return bool(REQUEST_PATTERN.match(str(value or "")))


def is_task_fingerprint(value: str | None) -> bool:
    return bool(TASK_FINGERPRINT_PATTERN.match(str(value or "")))


def request_file_stem(request_id: str) -> str:
    return str(request_id).strip()


def request_file_name(request_id: str) -> str:
    return f"{request_file_stem(request_id)}.json"


def request_display_label(request_id: str | None) -> str:
    text = str(request_id or "").strip()
    return text[:12] if text else "-"




def format_temp_candidate_id(index: int) -> str:
    return f"TMP_{index}"


def format_case_id(index: int) -> str:
    return f"CASE_{index}"


def candidate_index(candidate_id: str) -> int | None:
    return _parse_index(str(candidate_id), CANDIDATE_PATTERN)


def temp_candidate_index(candidate_id: str) -> int | None:
    return _parse_index(str(candidate_id), TEMP_CANDIDATE_PATTERN)


def case_id_for_candidate(candidate_id: str) -> str | None:
    index = candidate_index(candidate_id)
    if index is None:
        return None
    return format_case_id(index)


def _case_record_paths() -> list:
    paths = []
    seen = set()
    for folder in [CASES_DIR, CASE_LIBRARY_DIR]:
        for path in folder.glob("CASE_*.json"):
            if path.name in seen:
                continue
            seen.add(path.name)
            paths.append(path)
    return paths


def _max_candidate_index() -> int:
    indices = []
    for path in _case_record_paths():
        parsed_case = _parse_index(path.stem, CASE_PATTERN)
        if parsed_case is not None:
            indices.append(parsed_case)
        try:
            payload = read_json(path)
        except Exception:
            continue
        for value in [
            payload.get("design", {}).get("candidate_id"),
            payload.get("abaqus_results", {}).get("candidate_id"),
        ]:
            parsed = _parse_index(str(value), CANDIDATE_PATTERN)
            if parsed is not None:
                indices.append(parsed)
    return max(indices, default=0)


def _max_case_index() -> int:
    indices = []
    for path in _case_record_paths():
        parsed = _parse_index(path.stem, CASE_PATTERN)
        if parsed is not None:
            indices.append(parsed)
            continue
        try:
            case_id = str(read_json(path).get("case_id", ""))
        except Exception:
            continue
        parsed = _parse_index(case_id, CASE_PATTERN)
        if parsed is not None:
            indices.append(parsed)
    return max(indices, default=0)


def next_candidate_index() -> int:
    return _max_candidate_index() + 1


def next_case_id(candidate_id: str | None = None) -> str:
    preferred_index = candidate_index(candidate_id) if candidate_id else None
    if preferred_index is not None:
        case_id = format_case_id(preferred_index)
        for path in _case_record_paths():
            if path.stem == case_id:
                raise ValueError(f"案例编号 {case_id} 已存在，不能重复写入")
        # 正式案例编号与正式候选编号保持一一对应；并行求解时允许 C2 先于 C1 回写。
        # 后续新候选仍由现有最大编号顺延，不复用已占用编号。
        return case_id
    next_index = _max_case_index() + 1
    return format_case_id(next_index)
