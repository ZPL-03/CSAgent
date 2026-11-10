"""ABAQUS 求解智能体。"""

from __future__ import annotations

from pathlib import Path
from typing import Dict
from copy import deepcopy
import shutil
import hashlib

from jinja2 import Template

from abaqus.job_utils import compiler_environment, diagnose_failure, is_abaqus_available, read_tail_text, run_command, wait_for_result_file
from agents.base import BaseAgent
from core.config_loader import load_app_config
from core.fem_input_contract import attach_design_revision, design_revision_payload, validate_fem_input_or_raise
from core.io_utils import read_json, write_json
from core.paths import ABAQUS_RUNS_DIR, ABAQUS_TEMPLATE_DIR, IO_DIR, ROOT_DIR, to_project_relative_path
from core.pressure_hull_profile import expand_layup_for_fem
from core.schema_validator import validate_or_raise
from core.task_contract import describe_boundary_conditions, describe_load_conditions


class FEMAgent(BaseAgent):
    agent_name = "FEM_AGENT"
    artifact_path_keys = {
        "abaqus_odb",
        "linear_buckling_odb",
        "postbuckling_odb",
        "service_odb",
        "target_odb",
        "abaqus_inp",
        "postbuckling_inp",
        "service_inp",
        "target_inp",
        "visualization_json",
        "artifact_dir",
        "user_subroutine_path",
        "material_strength_include",
    }
    non_retryable_error_types = {
        "limit_point_not_confirmed",
        "progressive_damage_not_configured",
        "invalid_fem_input",
        "service_load_solver_failed",
        "target_load_solver_failed",
        "subroutine_compilation_failed",
        "capacity_solver_failed",
    }

    def __init__(self, progress_callback=None, config: Dict | None = None) -> None:
        super().__init__(progress_callback=progress_callback)
        self.config = config or load_app_config()
        self.abaqus_config = self.config["abaqus"]

    def _input_path(self, candidate_id: str) -> Path:
        return IO_DIR / f"input_{candidate_id}.json"

    def _result_path(self, candidate_id: str) -> Path:
        return IO_DIR / f"result_{candidate_id}.json"

    def _run_dir(self, candidate_id: str) -> Path:
        run_dir = ABAQUS_RUNS_DIR / candidate_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def _script_path(self, candidate_id: str) -> Path:
        return self._run_dir(candidate_id) / f"build_{candidate_id}.py"

    def _inp_path(self, candidate_id: str) -> Path:
        return self._run_dir(candidate_id) / f"{candidate_id}.inp"

    def _odb_path(self, candidate_id: str) -> Path:
        return self._run_dir(candidate_id) / f"{candidate_id}.odb"

    def _cleanup_run_artifacts(self, candidate_id: str, keep_logs: bool = True) -> None:
        run_dir = self._run_dir(candidate_id)
        removable = [".lck", ".023", ".com", ".jnl", ".prt", ".sim", ".env", ".odb_f"]
        if not keep_logs:
            removable.extend([".msg", ".dat", ".sta", ".log"])

        for root_name in [candidate_id, f"{candidate_id}_service", f"{candidate_id}_target", f"{candidate_id}_post"]:
            for suffix in removable:
                path = run_dir / f"{root_name}{suffix}"
                if path.exists():
                    path.unlink(missing_ok=True)

        for path in run_dir.glob("abaqus.rpy*"):
            path.unlink(missing_ok=True)
        for path in run_dir.glob("abaqus*.rec"):
            path.unlink(missing_ok=True)
        for path in run_dir.glob("candidate_retry_*.json"):
            path.unlink(missing_ok=True)

        script_path = self._script_path(candidate_id)
        if script_path.exists():
            script_path.unlink(missing_ok=True)

    def generate_script(self, candidate: Dict) -> Path:
        template_path = ABAQUS_TEMPLATE_DIR / "pressure_hull_analysis.py.j2"
        template = Template(template_path.read_text(encoding="utf-8"))
        run_dir = self._run_dir(candidate["candidate_id"])
        subroutine_path = ROOT_DIR / self.abaqus_config.get("user_subroutine", "")
        if candidate.get("analysis", {}).get("use_user_subroutine"):
            staged_subroutine = run_dir / subroutine_path.name
            shutil.copyfile(subroutine_path, staged_subroutine)
            subroutine_path = staged_subroutine
        script_content = template.render(
            project_root=str(ROOT_DIR),
            input_json=str(self._input_path(candidate["candidate_id"])),
            result_json=str(self._result_path(candidate["candidate_id"])),
            user_subroutine=str(subroutine_path),
        )
        script_path = self._script_path(candidate["candidate_id"])
        script_path.write_text(script_content, encoding="utf-8")
        if candidate.get("analysis", {}).get("use_user_subroutine"):
            material = candidate["material_system"]
            strengths = {"XC": material["Xc_MPa"], "XT": material["Xt_MPa"],
                         "YC": material["Yc_MPa"], "YT": material["Yt_MPa"], "S12": material["S_MPa"]}
            lines = ["      DOUBLE PRECISION XC,XT,YC,YT,S12"]
            lines.extend(f"      PARAMETER ({key}={float(value):.12E})".replace("E+", "D+").replace("E-", "D-")
                         for key, value in strengths.items())
            (run_dir / "pressure_hull_strength.inc").write_text(
                "\n".join(lines) + "\n", encoding="utf-8")
        return script_path

    def _diagnosis_summary(self, result: Dict) -> str:
        if result.get("status") == "success":
            verdict = result.get("verdict", "未判定")
            linear_pressure = result.get("linear_buckling_pressure_MPa")
            ultimate_pressure = result.get("ultimate_pressure_MPa")
            design_check_status = result.get("design_check_status")
            service_status = result.get("service_pressure_check_status")
            if design_check_status == "failed_at_service_pressure" or service_status == "failed":
                service_pressure = result.get("service_pressure_checked_MPa")
                service_index = result.get("service_hashin_index_max")
                failure_mode = result.get("service_hashin_failure_mode") or result.get("failure_mode")
                return (
                    f"精确服务压力校核已完成，服务压力 {service_pressure} MPa，"
                    f"线性屈曲压力 {linear_pressure} MPa，最大 Hashin 指数 {service_index}；"
                    f"控制模式为 {failure_mode}，设计判定为“{verdict}”，"
                    "容量分析因服务压力校核未通过而未运行。"
                )
            if design_check_status == "failed_at_design_target_pressure":
                target_pressure = result.get("target_pressure_checked_MPa")
                target_index = result.get("target_hashin_index_max")
                return (
                    f"精确目标压力校核已完成，目标压力 {target_pressure} MPa，"
                    f"线性屈曲压力 {linear_pressure} MPa，最大 Hashin 指数 {target_index}；"
                    f"控制模式为 {result.get('target_hashin_failure_mode') or result.get('failure_mode')}，"
                    f"设计判定为“{verdict}”，容量分析因目标压力校核未通过而未运行。"
                )
            if design_check_status == "passed_at_design_target_pressure":
                target_pressure = result.get("target_pressure_checked_MPa")
                target_index = result.get("target_hashin_index_max")
                capacity_status = result.get("capacity_assessment_status")
                return (
                    f"精确目标压力校核已完成，目标压力 {target_pressure} MPa，"
                    f"线性屈曲压力 {linear_pressure} MPa，最大 Hashin 指数 {target_index}；"
                    f"设计判定为“{verdict}”，容量分析状态为 {capacity_status}。"
                )
            basis = result.get("ultimate_pressure_basis") or "有限元校核"
            reference_pressure = result.get("postbuckling_reference_pressure_MPa")
            lpf = result.get("riks_lpf_max")
            if reference_pressure is not None and lpf is not None:
                return (
                    f"外压圆柱壳有限元校核已完成，线性屈曲压力 {linear_pressure} MPa；"
                    f"极限压力按“{basis}”计算，基准外压 {reference_pressure} MPa，"
                    f"最大 LPF={lpf}，得到极限压力 {ultimate_pressure} MPa，当前结论为“{verdict}”。"
                )
            return (
                f"外压圆柱壳有限元校核已完成，线性屈曲压力 {linear_pressure} MPa，"
                f"极限压力 {ultimate_pressure} MPa，当前结论为“{verdict}”。"
            )

        error_type = str(result.get("error_type") or "failed")
        mapping = {
            "mesh_error": "网格划分阶段出现异常，建议放宽网格尺寸后重试。",
            "geometry_issue": "几何装配阶段出现异常，建议检查半径、厚度和端部约束。",
            "convergence_fail": "非线性或特征值求解未稳定收敛，建议增大厚度、降低缺陷幅值或细化增量控制。",
            "pressure_negative": "求得负压力特征值，通常意味着载荷方向或边界设置需要复核。",
            "limit_point_not_confirmed": "Riks 作业未在成功状态下形成明确后峰下降，观测最大 LPF 不能作为极限压力。",
            "progressive_damage_not_configured": "当前运行未启用可执行的渐进损伤模型，不能给出材料极限强度结论。",
            "service_load_solver_failed": "服务压力精确加载作业未完成，不能给出服务工况结论。",
            "target_load_solver_failed": "设计目标压力精确加载作业未完成，不能给出目标工况结论。",
            "process_crash": "ABAQUS 进程异常退出，建议检查运行环境、日志和临时文件。",
            "abaqus_unavailable": "未找到 ABAQUS 命令，无法执行真实有限元求解。",
            "subroutine_compilation_failed": "用户子程序编译或链接失败，请检查该作业的 .log 和材料强度文件；不调整几何重试。",
            "capacity_solver_failed": "容量作业未生成可读结果，请检查该作业的 .log、.dat 和 .msg。",
        }
        return mapping.get(error_type, "求解未完成，建议检查日志后重试。")

    def _annotate_result(self, candidate: Dict, result: Dict) -> Dict:
        annotated = dict(result)
        for field in ("run_id", "task_id", "session_candidate_id"):
            if candidate.get(field):
                annotated[field] = candidate[field]
        if candidate.get("analysis", {}).get("use_user_subroutine"):
            source = self._run_dir(candidate["candidate_id"]) / Path(self.abaqus_config["user_subroutine"]).name
            include = source.parent / "pressure_hull_strength.inc"
            for path, key in ((source, "user_subroutine"), (include, "material_strength")):
                if path.is_file():
                    annotated[key + "_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            annotated["user_subroutine_path"] = str(source)
            annotated["material_strength_include"] = str(include)
            if annotated.get("user_subroutine_used"):
                annotated["progressive_damage_model"] = "irreversible_stress_triggered_field_degradation"
        for key in self.artifact_path_keys:
            if annotated.get(key):
                annotated[key] = to_project_relative_path(annotated[key])
        annotated["load_summary"] = describe_load_conditions(candidate.get("load_conditions", {}))
        annotated["boundary_summary"] = describe_boundary_conditions(candidate.get("boundary_conditions", {}))
        annotated["design_revision_id"] = candidate.get("design_revision_id")
        annotated["parent_design_revision_id"] = candidate.get("parent_design_revision_id")
        annotated["solved_design"] = {
            **deepcopy(design_revision_payload(candidate)),
            "design_revision_id": candidate.get("design_revision_id"),
            "parent_design_revision_id": candidate.get("parent_design_revision_id"),
        }
        annotated["diagnosis_summary"] = self._diagnosis_summary(annotated)
        return annotated

    def apply_adjustment(self, candidate: Dict, failure_type: str, attempt: int) -> Dict:
        adjusted = deepcopy(candidate)
        parent_revision_id = str(candidate.get("design_revision_id") or "")
        geometry = dict(adjusted["geometry"])
        adjustment: Dict[str, object] = {"attempt": attempt + 1, "failure_type": failure_type}

        if failure_type == "mesh_error":
            current_mesh_size = float(candidate.get("analysis", {}).get("mesh_size_mm", 0.0))
            adjusted.setdefault("analysis", {})
            adjusted["analysis"]["mesh_size_mm"] = round(max(current_mesh_size * 1.15, 6.0) if current_mesh_size else 8.0, 3)
            adjustment["strategy"] = "增大壳体网格尺寸以绕开局部畸变"
        elif failure_type == "geometry_issue":
            geometry["thickness_mm"] = round(min(max(geometry["thickness_mm"] + 0.5, 5.0), 20.0), 3)
            adjustment["strategy"] = "提高壁厚"
        elif failure_type == "convergence_fail":
            adjusted.setdefault("analysis", {})
            adjusted["analysis"]["buckling_modes"] = int(adjusted["analysis"].get("buckling_modes", 8)) + 4
            geometry["thickness_mm"] = round(min(geometry["thickness_mm"] + 0.8, 20.0), 3)
            adjustment["strategy"] = "增加特征值搜索规模并提高壁厚"
        elif failure_type == "pressure_negative":
            adjusted.setdefault("analysis", {})
            adjusted["analysis"]["buckling_modes"] = max(int(adjusted["analysis"].get("buckling_modes", 8)), 12) + 4
            adjustment["strategy"] = "增加屈曲模态搜索数量并复核压力方向"
        else:
            adjustment["strategy"] = "清理临时文件后重试"

        adjusted["geometry"] = geometry
        adjusted["layup"] = expand_layup_for_fem(adjusted.get("layup"), geometry)
        adjusted["last_adjustment"] = adjustment
        adjusted = attach_design_revision(adjusted, parent_revision_id=parent_revision_id)
        validate_fem_input_or_raise(adjusted)
        return adjusted

    def _empty_result_payload(self, candidate: Dict, status: str, error_type: str | None = None) -> Dict:
        candidate_id = candidate["candidate_id"]
        return {
            "candidate_id": candidate_id,
            "status": status,
            "retry_count": 0,
            "ultimate_pressure_MPa": None,
            "failure_pressure_MPa": None,
            "linear_buckling_pressure_MPa": None,
            "first_mode_eigenvalue": None,
            "failure_mode": None,
            "max_displacement_mm": None,
            "weight_kg_per_m2": None,
            "verdict": None,
            "abaqus_odb": None,
            "abaqus_inp": str(self._inp_path(candidate_id)) if self._inp_path(candidate_id).exists() else None,
            "visualization_json": None,
            "artifact_dir": str(self._run_dir(candidate_id)),
            "error_type": error_type,
            "error_log": None,
            "mode_eigenvalues": None,
        }

    def _run_real(self, candidate: Dict, result_path: Path) -> Dict:
        candidate_id = candidate["candidate_id"]
        run_dir = self._run_dir(candidate_id)
        self._cleanup_run_artifacts(candidate_id, keep_logs=False)
        script_path = self.generate_script(candidate)
        self.emit(f"{candidate_id} 耐压壳脚本已生成：{script_path.name}")

        command = [self.abaqus_config["command"], "cae", f"noGUI={script_path.name}"]
        return_code, stdout, stderr = run_command(
            command,
            workdir=run_dir,
            timeout=self.abaqus_config["job_timeout_seconds"],
            environment=compiler_environment() if candidate.get("analysis", {}).get("use_user_subroutine") else None,
        )
        self.emit(f"{candidate_id} ABAQUS 作业完成，返回码 {return_code}")

        if wait_for_result_file(
            result_path=result_path,
            timeout_seconds=self.abaqus_config["job_timeout_seconds"],
            poll_interval_seconds=self.abaqus_config["poll_interval_seconds"],
        ):
            result = self._annotate_result(candidate, read_json(result_path))
            write_json(result_path, result)
            self._cleanup_run_artifacts(candidate_id, keep_logs=True)
            return result

        diagnosis = diagnose_failure(
            msg_text=read_tail_text(run_dir / f"{candidate_id}.msg"),
            dat_text=read_tail_text(run_dir / f"{candidate_id}.dat"),
            return_code=return_code,
        )
        if diagnosis["error_type"] == "blf_negative":
            diagnosis["error_type"] = "pressure_negative"
        payload = self._empty_result_payload(candidate, "failed", diagnosis["error_type"])
        payload["error_log"] = {
            "stdout": stdout[-4000:],
            "stderr": stderr[-4000:],
            "reason": diagnosis["reason"],
        }
        return self._annotate_result(candidate, payload)

    def _abaqus_unavailable_result(self, candidate: Dict) -> Dict:
        candidate_id = candidate["candidate_id"]
        result = self._annotate_result(
            candidate,
            {
                **self._empty_result_payload(candidate, "max_retries_exceeded", "abaqus_unavailable"),
                "error_log": f"未找到 ABAQUS 命令：{self.abaqus_config['command']}",
            },
        )
        write_json(self._result_path(candidate_id), result)
        validate_or_raise("abaqus_result.schema.json", result)
        return result

    def run(self, candidate: Dict) -> Dict:
        validate_or_raise("candidate.schema.json", candidate)
        validate_fem_input_or_raise(candidate)
        retries = int(self.abaqus_config["max_retries"])
        current = deepcopy(candidate)
        current.setdefault("analysis", {})
        current["analysis"].setdefault("use_user_subroutine", bool(self.abaqus_config.get("use_user_subroutine", False)))
        current["analysis"]["solver_command"] = self.abaqus_config["command"]
        current = attach_design_revision(current)
        if current["analysis"]["use_user_subroutine"]:
            subroutine = self.abaqus_config.get("user_subroutine")
            if not subroutine or not (ROOT_DIR / subroutine).is_file():
                raise ValueError("已启用用户子程序，但 Fortran 文件不存在")
        candidate_id = current["candidate_id"]
        result_path = self._result_path(candidate_id)
        run_dir = self._run_dir(candidate_id)
        write_json(run_dir / "candidate_input.json", current)

        if not is_abaqus_available(self.abaqus_config["command"]):
            self.emit(f"{candidate_id} 未找到 ABAQUS 命令，真实有限元求解无法启动")
            return self._abaqus_unavailable_result(current)

        for attempt in range(retries):
            if result_path.exists():
                result_path.unlink()

            write_json(self._input_path(candidate_id), current)
            self.emit(f"{candidate_id} 第 {attempt + 1} 次真实 ABAQUS 求解")
            result = self._run_real(current, result_path)
            result["retry_count"] = attempt

            if result["status"] == "success":
                self._cleanup_run_artifacts(candidate_id, keep_logs=True)
                result = self._annotate_result(current, result)
                validate_or_raise("abaqus_result.schema.json", result)
                return result

            failure_type = result.get("error_type") or "failed"
            self.emit(f"{candidate_id} 失败类型：{failure_type}")
            if failure_type in self.non_retryable_error_types:
                final_result = self._annotate_result(current, dict(result))
                validate_or_raise("abaqus_result.schema.json", final_result)
                return final_result
            if attempt == retries - 1:
                final_result = self._annotate_result(current, dict(result))
                final_result["status"] = "max_retries_exceeded"
                validate_or_raise("abaqus_result.schema.json", final_result)
                return final_result

            current = self.apply_adjustment(current, failure_type, attempt)
            write_json(run_dir / f"candidate_retry_{attempt + 1}.json", current)
            strategy = current.get("last_adjustment", {}).get("strategy", "默认重试")
            self.emit(f"{candidate_id} 准备重试，调整策略：{strategy}")

        raise RuntimeError("FEM_AGENT 未按预期返回结果")
