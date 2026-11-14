from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Dict, Iterable, List

from abaqus.cylindrical_geometry import positive_number, radius_reference, shell_radii
from core.case_memory import CaseMemoryIndex, is_transferable_case
from core.config_loader import fixed_imperfection_ratio, load_app_config
from core.fem_result_semantics import verified_capacity_pressure
from core.io_utils import read_json
from core.paths import CASE_LIBRARY_DIR, CASES_DIR
from core.task_contract import equivalent_in_plane_load, normalize_boundary_conditions, normalize_load_conditions


@dataclass
class RetrievedCase:
    record: Dict
    score: float
    match_level: int = 0
    vector_rank: int | None = None


class CaseRetriever:
    """结构化硬过滤 + 案例记忆向量排序的耐压壳历史案例检索器。"""

    def __init__(
        self,
        include_archive: bool = True,
        include_formal: bool = True,
        use_vector_index: bool | None = None,
    ) -> None:
        self.include_archive = include_archive
        self.include_formal = include_formal
        config = load_app_config()
        case_memory_config = dict(config.get("case_memory", {}))
        self.use_vector_index = (
            bool(case_memory_config.get("hybrid_retrieval", True))
            if use_vector_index is None
            else bool(use_vector_index)
        )
        self.vector_top_k_multiplier = int(case_memory_config.get("vector_top_k_multiplier", 4) or 4)
        self.vector_rank_weight = float(case_memory_config.get("vector_rank_weight", 0.1) or 0.1)
        self._case_memory: CaseMemoryIndex | None = None
        self._case_memory_failed = False

    @property
    def case_memory(self) -> CaseMemoryIndex | None:
        if not self.use_vector_index or self._case_memory_failed:
            return None
        if self._case_memory is not None:
            return self._case_memory
        try:
            self._case_memory = CaseMemoryIndex()
        except Exception:
            self._case_memory_failed = True
            return None
        return self._case_memory

    def _candidate_paths(self) -> List[Path]:
        paths = []
        if self.include_formal:
            paths.extend(sorted(CASE_LIBRARY_DIR.glob("CASE_*.json")))
        if self.include_archive:
            paths.extend(sorted(CASES_DIR.glob("CASE_*.json")))
        deduped = []
        seen = set()
        for path in paths:
            if path.name in seen:
                continue
            seen.add(path.name)
            deduped.append(path)
        return deduped

    def _case_scope(self, path: Path) -> str:
        return "formal" if path.parent == CASE_LIBRARY_DIR else "archive"

    def _load_record_items(self) -> Iterable[tuple[Dict, str]]:
        for path in self._candidate_paths():
            try:
                payload = read_json(path)
            except Exception:
                continue
            if isinstance(payload, dict):
                yield payload, self._case_scope(path)

    def _load_records(self) -> Iterable[Dict]:
        for payload, _scope in self._load_record_items():
            yield payload

    def _has_design(self, record: Dict) -> bool:
        design = record.get("design", {})
        return isinstance(design, dict) and bool(design)

    def _is_transferable(self, record: Dict) -> bool:
        return is_transferable_case(record)

    def _material_name(self, payload: Dict) -> str:
        material = payload.get("material_system", {})
        if not isinstance(material, dict):
            return ""
        return str(material.get("name") or "").strip().lower()

    def _geometry_center(self, task: Dict) -> Dict[str, float]:
        envelope = task.get("geometry_envelope", {})
        centers = {"imperfection_ratio": fixed_imperfection_ratio()}
        for key in ("length_mm", "radius_mm", "thickness_mm"):
            value = envelope.get(key)
            if value is None:
                continue
            if not isinstance(value, (list, tuple)) or len(value) != 2:
                raise ValueError(f"geometry_envelope.{key} 需要上下限")
            centers[key] = sum(positive_number(item, key) for item in value) / 2.0
        return centers

    def _hull_type(self, payload: Dict) -> str:
        return str(payload.get("hull_type") or "CYLINDRICAL")

    def _match_level(self, task: Dict, record: Dict) -> int:
        design = record.get("design", {})
        task_load = normalize_load_conditions(task.get("load_conditions", {}))
        task_boundary = normalize_boundary_conditions(task.get("boundary_conditions", {}))
        design_load = normalize_load_conditions(design.get("load_conditions", {}))
        design_boundary = normalize_boundary_conditions(design.get("boundary_conditions", {}))
        if self._hull_type(task) != self._hull_type(design):
            return -1

        task_material = self._material_name(task)
        design_material = self._material_name(design)
        same_load = task_load.get("type") == design_load.get("type")
        same_boundary = task_boundary.get("type") == design_boundary.get("type")
        same_material = not task_material or not design_material or task_material == design_material

        if same_load and same_boundary and same_material:
            return 3
        if same_load and same_boundary:
            return 2
        return -1

    def _score(self, task: Dict, record: Dict) -> float:
        design = record.get("design", {})
        geometry = design.get("geometry", {})
        design_targets = task.get("design_targets", {})
        geometry_center = self._geometry_center(task)
        load_gap = abs(
            equivalent_in_plane_load(task.get("load_conditions", {}))
            - equivalent_in_plane_load(design.get("load_conditions", {}))
        )
        geometry_gap = 0.0
        weights = {"length_mm": 0.02, "radius_mm": 0.08, "thickness_mm": 1.5, "imperfection_ratio": 1000.0}
        for key, center in geometry_center.items():
            if geometry.get(key) is None:
                return float("inf")
            if key == "imperfection_ratio":
                value = float(geometry[key])
                if isinstance(geometry[key], bool) or not math.isfinite(value) or value < 0:
                    raise ValueError("imperfection_ratio 必须为非负有限数值")
            else:
                value = positive_number(geometry[key], key)
            if key == "radius_mm" and radius_reference(geometry) != radius_reference(task):
                if geometry.get("thickness_mm") is None:
                    return float("inf")
                value = shell_radii(geometry)[radius_reference(task)]
            geometry_gap += abs(value - center) * weights[key]
        target = design_targets.get("ultimate_pressure_min_MPa")
        target_pressure = positive_number(target, "ultimate_pressure_min_MPa") if target is not None else None
        result_pressure = verified_capacity_pressure(record.get("abaqus_results", {}))
        pressure_gap = abs(result_pressure - target_pressure) if result_pressure is not None and target_pressure is not None else 0.0
        return load_gap + geometry_gap + pressure_gap * 2.0

    def _ranking_key(self, item: RetrievedCase) -> tuple:
        # 容量未知的案例仍可作为几何参考，但不与已有容量证据的案例比较压力距离。
        capacity_unknown = verified_capacity_pressure(item.record.get("abaqus_results", {})) is None
        return (-item.match_level, capacity_unknown, item.score,
                item.vector_rank if item.vector_rank is not None else float("inf"))

    def _vector_rank_map(self, task: Dict, top_k: int, transferable_only: bool = False) -> Dict[str, int]:
        memory = self.case_memory
        if memory is None:
            return {}
        where = {"transferable": "true"} if transferable_only else None
        query_k = max(top_k * max(self.vector_top_k_multiplier, 1), top_k)
        try:
            hits = memory.query(task, top_k=query_k, where=where)
        except Exception:
            self._case_memory_failed = True
            return {}
        rank_map: Dict[str, int] = {}
        for rank, hit in enumerate(hits):
            rank_map.setdefault(hit.case_id, rank)
        return rank_map

    def _combined_score(self, base_score: float, vector_rank: int | None, vector_size: int) -> float:
        if vector_rank is None:
            return base_score + max(vector_size, 1) * self.vector_rank_weight
        return base_score + vector_rank * self.vector_rank_weight

    def _basic_compatible(self, task: Dict, record: Dict) -> bool:
        design = record.get("design", {})
        if not self._has_design(record):
            return False
        if self._hull_type(task) != self._hull_type(design):
            return False
        task_material = self._material_name(task)
        design_material = self._material_name(design)
        return not task_material or not design_material or task_material == design_material

    def _relaxed_match_level(self, task: Dict, record: Dict) -> int:
        design = record.get("design", {})
        task_load = normalize_load_conditions(task.get("load_conditions", {}))
        task_boundary = normalize_boundary_conditions(task.get("boundary_conditions", {}))
        design_load = normalize_load_conditions(design.get("load_conditions", {}))
        design_boundary = normalize_boundary_conditions(design.get("boundary_conditions", {}))
        same_load = task_load.get("type") == design_load.get("type")
        same_boundary = task_boundary.get("type") == design_boundary.get("type")
        if same_load and same_boundary:
            return 2
        if same_load or same_boundary:
            return 1
        return 0

    def retrieve_similar_cases(self, task: Dict, top_k: int = 5) -> List[Dict]:
        records = list(self._load_records())
        vector_rank = self._vector_rank_map(task, top_k=top_k, transferable_only=False)
        vector_size = max(len(vector_rank), 1)
        records_by_case_id = {str(record.get("case_id")): record for record in records if record.get("case_id")}
        ranked: List[RetrievedCase] = []
        seen_case_ids: set[str] = set()

        for record in records:
            if not self._has_design(record):
                continue
            match_level = self._match_level(task, record)
            if match_level < 0:
                continue
            case_id = str(record.get("case_id") or "")
            seen_case_ids.add(case_id)
            rank = vector_rank.get(case_id)
            ranked.append(
                RetrievedCase(
                    record=record,
                    score=self._combined_score(self._score(task, record), rank, vector_size),
                    match_level=match_level,
                    vector_rank=rank,
                )
            )

        if not ranked and vector_rank:
            for case_id, rank in sorted(vector_rank.items(), key=lambda item: item[1]):
                record = records_by_case_id.get(case_id)
                if not record or case_id in seen_case_ids or not self._basic_compatible(task, record):
                    continue
                ranked.append(
                    RetrievedCase(
                        record=record,
                        score=self._combined_score(self._score(task, record), rank, vector_size),
                        match_level=self._relaxed_match_level(task, record),
                        vector_rank=rank,
                    )
                )
                if len(ranked) >= top_k:
                    break

        ranked.sort(key=self._ranking_key)
        return [item.record for item in ranked[:top_k]]

    def retrieve_transferable_cases(self, task: Dict, top_k: int = 5) -> List[Dict]:
        vector_rank = self._vector_rank_map(task, top_k=top_k, transferable_only=True)
        vector_size = max(len(vector_rank), 1)
        ranked: List[RetrievedCase] = []
        for record in self._load_records():
            if not self._is_transferable(record):
                continue
            match_level = self._match_level(task, record)
            if match_level < 3:
                continue
            case_id = str(record.get("case_id") or "")
            rank = vector_rank.get(case_id)
            ranked.append(
                RetrievedCase(
                    record=record,
                    score=self._combined_score(self._score(task, record), rank, vector_size),
                    match_level=match_level,
                    vector_rank=rank,
                )
            )
        ranked.sort(key=self._ranking_key)
        return [item.record for item in ranked[:top_k]]

    def transfer_candidates(self, task: Dict, top_k: int = 2) -> List[Dict]:
        transferred: List[Dict] = []
        for record in self.retrieve_transferable_cases(task, top_k=top_k):
            design = record.get("design", {})
            if isinstance(design, dict) and design:
                transferred.append(design)
        return transferred
