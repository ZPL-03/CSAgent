"""离线校验知识包并执行 CPU 领域检索，保存完整提示词证据和来源指纹。"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
QUERIES = [
    "对称且均衡的层合板，B 矩阵与 D16、D26 弯扭耦合分别有什么条件？",
    "ASME RD-1172 external pressure composite cylindrical shell buckling applicability boundary conditions",
    "复合材料外压圆柱壳初始几何缺陷比与缺陷幅值的定义及屈曲适用条件",
    "composite cylindrical shell buckling pressure ASME NASA ANSYS table t1 t2 material geometry",
    "T700 epoxy material properties elastic modulus strength units temperature conditions",
]


def fingerprint(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--query", action="append")
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args(argv)
    if args.threads < 1:
        parser.error("threads 必须为正整数")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=False)
    os.environ.update(CSDM_CPH_RUN_ROOT=str(output), CSDM_CPH_EMBEDDING_DEVICE="cpu",
                      CUDA_VISIBLE_DEVICES="-1", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                      OMP_NUM_THREADS=str(args.threads), MKL_NUM_THREADS=str(args.threads))
    sys.path.insert(0, str(ROOT))
    from core.builtin_knowledge import _encoder
    from core.domain_knowledge import DomainKnowledgeBase
    from core.io_utils import write_json
    from core.retrieval_evidence import binds_to_chunk, exclusion_reason, full_text, render_evidence
    from scripts.sync_builtin_knowledge import jsonl_rows, sha256, validate_bundle
    import torch

    torch.set_num_threads(args.threads)
    report = {"started_at": datetime.now(timezone.utc).isoformat(), "status": "running", "queries": []}
    try:
        knowledge = DomainKnowledgeBase()
        manifest = json.loads(knowledge.builtin_manifest_path.read_text(encoding="utf-8"))
        report["bundle_verification"] = validate_bundle(knowledge.builtin_dir)
        report["source_package_sha256"] = manifest["source_package_sha256"]
        report["assets"] = [{"path": entry["path"], "sha256": entry["sha256"], "bytes": entry["bytes"]} for entry in manifest["files"]]
        print(json.dumps({"stage": "bundle_verified", **report["bundle_verification"]}), flush=True)
        for query in args.query or QUERIES:
            result = knowledge.retrieve_by_query(query)
            snippets, audit = render_evidence(result["chunks"], result["relations"], knowledge.max_context_chars)
            if not result["chunks"] or not snippets:
                raise ValueError("查询没有完整可纳入的证据：" + query)
            if not any("BUILTIN_DENSE" in row["retrieval_sources"] for row in result["chunks"]):
                raise ValueError("查询未执行真实语义检索：" + query)
            report["queries"].append({**result, "prompt_evidence": snippets, "budget_audit": audit})
            print(json.dumps({"stage": "retrieved", "query": query, "chunks": len(result["chunks"]),
                              "relations": len(result["relations"]), "included": len(snippets),
                              "excluded": len(audit["excluded"]), "used_chars": audit["used_chars"]}, ensure_ascii=False), flush=True)

        # 对实际命中回查规范 JSONL，索引排序不能替代原文与来源身份的一致性检查。
        wanted = {row["chunk_id"] for result in report["queries"] for row in result["chunks"]}
        current = {row["chunk_id"]: row for row in jsonl_rows(knowledge.builtin_rag_chunks_path) if row["chunk_id"] in wanted}
        sources = {row["record_id"]: row for row in jsonl_rows(knowledge.builtin_dir / "provenance/source_metadata.compact.jsonl.gz")}
        checked_relations = []
        for result in report["queries"]:
            for row in result["chunks"]:
                canonical = current[row["chunk_id"]]
                if exclusion_reason(canonical) is not None or canonical["record_id"] not in sources:
                    raise ValueError("检索块不可用或来源记录缺失")
                keys = ("chunk_fingerprint", "record_id", "source_id", "applicability_context", "evidence_kind", "evidence_usage", "table_evidence")
                if any(row.get(key) != canonical.get(key) for key in keys) or full_text(row) != full_text(canonical):
                    raise ValueError("检索命中丢失或改变规范证据")
            for row in result["relations"]:
                if not binds_to_chunk(row, current[row["evidence_chunk_id"]]):
                    raise ValueError("KG 关系不绑定当前块")
                checked_relations.append({key: value for key, value in row.items() if key not in {"score", "retrieval_source"}})
            for snippet in result["prompt_evidence"]:
                packet = json.loads(snippet)
                canonical = current[packet["chunk_id"]]
                if packet["text"] != full_text(canonical) or packet["applicability_context"] != canonical.get("applicability_context"):
                    raise ValueError("提示词中的原文或条件不完整")
        engine = knowledge.vector.engine
        model_path = Path(engine._resolve_embedding_model_reference())
        _, model = _encoder(str(model_path), engine.embedding_device)
        devices = sorted({str(parameter.device) for parameter in model.parameters()})
        if devices != ["cpu"] or torch.cuda.is_initialized():
            raise ValueError("检索进程未保持 CPU 设备")
        report["encoder"] = {"model": engine.embedding_model_name, "devices": devices,
                             "cuda_initialized": torch.cuda.is_initialized(), "threads": torch.get_num_threads(),
                             "files": [{"path": str(path.relative_to(model_path)), "sha256": sha256(path)}
                                       for path in sorted(model_path.rglob("*")) if path.is_file()]}
        report["evidence_fingerprints"] = {
            "chunks": fingerprint(sorted((row["chunk_id"], row["chunk_fingerprint"], row["record_id"]) for row in current.values())),
            "sources": fingerprint([sources[key] for key in sorted({row["record_id"] for row in current.values()})]),
            "relations": fingerprint(sorted(checked_relations, key=lambda row: json.dumps(row, sort_keys=True))),
        }
        report["status"] = "passed"
    except Exception as exc:
        report.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    write_json(output / "retrieval_validation.json", report)
    print(json.dumps({"status": report["status"], "path": str(output / "retrieval_validation.json"),
                      "sha256": sha256(output / "retrieval_validation.json"), "error": report.get("error")}, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
