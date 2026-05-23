"""批量生成耐压壳初始样本并校准代理公式。"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agents.fem_agent import FEMAgent
from agents.knowledge_agent import KnowledgeAgent
from core.config_loader import load_material_db
from core.doe_sampler import DOESampler
from core.id_utils import next_candidate_index, next_task_id, task_file_name
from core.io_utils import write_json
from core.paths import ABAQUS_RUNS_DIR, CASES_DIR, CASE_LIBRARY_DIR, CHROMA_DIR, IO_DIR, MODELS_DIR, RESULTS_DIR, TASKS_DIR
from core.schema_validator import validate_or_raise
from core.surrogate_model import SurrogateModelManager
from core.task_contract import (
    boundary_condition_payload,
    build_task_request_record,
    load_condition_payload,
    normalize_task_payload,
    task_payload_from_request,
)


MODEL_FILES = [
    MODELS_DIR / "pressure_hull_surrogate_calibration.json",
]


def default_task(
    material_key: str,
    pressure_MPa: float,
    target_pressure_MPa: float | None = None,
    task_id: str | None = None,
) -> Dict:
    material = load_material_db()[material_key]
    target_pressure = float(target_pressure_MPa if target_pressure_MPa is not None else pressure_MPa)
    task_payload = normalize_task_payload(
        {
            "application": "复合材料外压圆柱耐压壳",
            "load_conditions": load_condition_payload("external_pressure", external_pressure_MPa=pressure_MPa),
            "boundary_conditions": boundary_condition_payload("END_CLAMPED"),
            "geometry_envelope": {
                "length_mm": [300, 800],
                "radius_mm": [80, 180],
                "thickness_mm": [5, 20],
                "alpha_deg": [10, 80],
                "beta_deg": [10, 80],
                "imperfection_ratio": [0.001, 0.01],
            },
            "material_system": {
                "name": material["display_name"],
                "density_kg_per_m3": material["density_kg_per_m3"],
                "E1_GPa": material["E1_GPa"],
                "E2_GPa": material["E2_GPa"],
                "G12_GPa": material["G12_GPa"],
                "nu12": material["nu12"],
                "Xt_MPa": material.get("Xt_MPa"),
                "Xc_MPa": material.get("Xc_MPa"),
                "Yt_MPa": material.get("Yt_MPa"),
                "Yc_MPa": material.get("Yc_MPa"),
                "S_MPa": material.get("S_MPa"),
                "material_key": material_key,
                "is_user_specified": True,
            },
            "layup_constraints": {
                "allowed_angles": [0, 45, -45, 90],
                "symmetric": True,
                "balanced": True,
                "min_ratio_per_angle": 0.05,
            },
            "hull_type": "CYLINDRICAL",
            "design_targets": {"ultimate_pressure_min_MPa": target_pressure, "primary_objective": "最小壳体质量"},
        }
    )
    validate_or_raise("task.schema.json", task_payload)
    if not task_id:
        return task_payload
    return build_task_request_record(
        task_payload,
        task_id=task_id,
        source="initial_case_build",
    )


def clear_dir(path: Path) -> None:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        return
    for child in path.iterdir():
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
        else:
            child.unlink(missing_ok=True)


def reset_dataset() -> None:
    for directory in [IO_DIR, RESULTS_DIR, CASES_DIR, ABAQUS_RUNS_DIR, CASE_LIBRARY_DIR, TASKS_DIR]:
        clear_dir(directory)
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR, ignore_errors=True)
    for model_path in MODEL_FILES:
        model_path.unlink(missing_ok=True)


def partition_count(total: int, buckets: int) -> List[int]:
    base = total // buckets
    remainder = total % buckets
    return [base + (1 if index < remainder else 0) for index in range(buckets)]


def build_candidates(task: Dict, count: int, start_index: int, strict_solver_window: bool) -> List[Dict]:
    sampler = DOESampler()
    return sampler.sample_candidates(
        task=task,
        n_samples=count,
        start_index=start_index,
        strict_solver_window=strict_solver_window,
        batch_multiplier=1,
    )


def solve_candidate(task: Dict, candidate: Dict) -> Tuple[Dict, Dict]:
    agent = FEMAgent()
    task_payload = task_payload_from_request(task)
    payload = dict(candidate)
    payload["design_targets"] = task_payload["design_targets"]
    payload["load_conditions"] = task_payload["load_conditions"]
    payload["boundary_conditions"] = task_payload["boundary_conditions"]
    payload["material_system"] = task_payload["material_system"]
    result = agent.run(payload)
    return payload, result


def run_task_batch(task: Dict, count: int, workers: int, strict_solver_window: bool) -> List[Dict]:
    if count <= 0:
        return []

    start_index = next_candidate_index()
    candidates = build_candidates(
        task=task,
        count=count,
        start_index=start_index,
        strict_solver_window=strict_solver_window,
    )

    knowledge_agent = KnowledgeAgent()
    records: List[Dict] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as executor:
        future_map = {
            executor.submit(solve_candidate, task, candidate): candidate["candidate_id"]
            for candidate in candidates
        }
        for future in as_completed(future_map):
            candidate, result = future.result()
            knowledge_agent.run({"task": task, "design": candidate, "abaqus_results": result})
            task_payload = task_payload_from_request(task)
            summary_record = {
                "candidate_id": candidate["candidate_id"],
                "material": task_payload["material_system"].get("name"),
                "status": result["status"],
                "ultimate_pressure_MPa": result.get("ultimate_pressure_MPa"),
                "linear_buckling_pressure_MPa": result.get("linear_buckling_pressure_MPa"),
                "verdict": result.get("verdict"),
                "retry_count": result.get("retry_count"),
                "artifact_dir": result.get("artifact_dir"),
            }
            task_id = str(task.get("task_id") or "").strip()
            if task_id:
                summary_record["task_id"] = task_id
            records.append(summary_record)
            print(json.dumps(records[-1], ensure_ascii=False))
    return records


def parse_pressures(text: str | None, task_count: int) -> List[float]:
    if text:
        return [float(item.strip()) for item in text.split(",") if item.strip()]
    base = [10.0, 20.0, 30.0, 40.0, 55.0, 70.0]
    if task_count <= len(base):
        return base[:task_count]
    extra = [base[-1] + 10.0 * index for index in range(task_count - len(base))]
    return base + extra


def task_specs(task_count: int, pressures: Sequence[float]) -> List[Tuple[str, float]]:
    material_keys = list(load_material_db().keys())
    specs: List[Tuple[str, float]] = []
    for index in range(task_count):
        material_key = material_keys[index % len(material_keys)]
        pressure_value = pressures[index % len(pressures)]
        specs.append((material_key, pressure_value))
    return specs


def train_surrogate() -> Dict | None:
    manager = SurrogateModelManager()
    records = manager.load_training_records()
    if len(records) < 3:
        print(json.dumps({"warning": "成功案例不足 3 条，跳过公式校准", "success_records": len(records)}, ensure_ascii=False, indent=2))
        return None
    summary = manager.train_from_records(records)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--task-count", type=int, default=3)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--full-range", action="store_true")
    parser.add_argument("--pressures", type=str, default="")
    parser.add_argument("--target-pressure", type=float, default=None)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--record-task", action="store_true", help="为批量建库写入 TASK_N 追溯记录")
    args = parser.parse_args()

    if args.reset:
        reset_dataset()

    pressures = parse_pressures(args.pressures or None, args.task_count)
    specs = task_specs(args.task_count, pressures)
    bucket_sizes = partition_count(args.count, len(specs))
    strict_solver_window = not args.full_range

    all_records: List[Dict] = []
    for (material_key, pressure), bucket_count in zip(specs, bucket_sizes):
        task_id = next_task_id() if args.record_task else None
        task = default_task(
            material_key=material_key,
            pressure_MPa=pressure,
            target_pressure_MPa=args.target_pressure,
            task_id=task_id,
        )
        if task_id:
            write_json(TASKS_DIR / task_file_name(task_id), task)
        task_records = run_task_batch(
            task=task,
            count=bucket_count,
            workers=args.workers,
            strict_solver_window=strict_solver_window,
        )
        all_records.extend(task_records)

    summary = train_surrogate()
    print(
        json.dumps(
            {
                "task_count": len(specs),
                "sample_count": len(all_records),
                "success_count": sum(1 for item in all_records if item["status"] == "success"),
                "pass_count": sum(1 for item in all_records if item.get("verdict") == "通过"),
                "materials": sorted({item["material"] for item in all_records}),
                "selected_model": summary.get("selected_model") if summary else None,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
