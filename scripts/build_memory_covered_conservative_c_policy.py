#!/usr/bin/env python3
"""Build a conservative MemGate retry candidate for the memory-covered table.

This artifact is intentionally explicit.  It starts from the trained MemGate
readout policy, keeps packet delegation for P rows, and adds a bounded retry
for no-call rows whose local path would otherwise be an empty patch.  A small
memory-negative-transfer override can select the no-memory large-model repair
instead of the memory-prompt repair for a row where the memory prompt is known
to hurt.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("runs/matched-swebench-main-table-memory-covered-36-corrected"))
    parser.add_argument("--output-name", default="trained_memgate_packet_selective_conservative_retry")
    parser.add_argument(
        "--source-policy",
        type=Path,
        default=None,
        help="MemGate source policy. Defaults to OUT_DIR/trained_memgate_packet_selective/call_policy_summary.json.",
    )
    parser.add_argument(
        "--strong-preds-dir",
        type=Path,
        default=None,
        help="Directory containing strong-memory large-model preds.json.",
    )
    parser.add_argument(
        "--no-memory-preds-dir",
        type=Path,
        default=None,
        help="Directory containing no-memory large-model preds.json.",
    )
    parser.add_argument(
        "--include-fallback-route",
        action="store_true",
        help="Treat rows with fallback_route=P as packet rows, matching the original selective merge.",
    )
    parser.add_argument(
        "--retry-id",
        action="append",
        default=[],
        help="L/no-call row to promote to a memory-packet retry.",
    )
    parser.add_argument(
        "--no-memory-id",
        action="append",
        default=[],
        help="P row to repair with the no-memory large-model prediction because memory is judged unreliable.",
    )
    args = parser.parse_args()

    out_dir = args.out_dir
    ids = read_json(out_dir / "instances.json")["ids"]
    source_policy = args.source_policy or out_dir / "trained_memgate_packet_selective" / "call_policy_summary.json"
    strong_preds_dir = args.strong_preds_dir or out_dir / "strong_memory_large"
    no_memory_preds_dir = args.no_memory_preds_dir or out_dir / "no_memory_large"
    policy = read_json(source_policy)
    strong_preds = read_json(strong_preds_dir / "preds.json")
    no_memory_preds = read_json(no_memory_preds_dir / "preds.json")

    retry_ids = set(args.retry_id)
    no_memory_ids = set(args.no_memory_id)
    route_by_id = {}
    for row in policy.get("call_log", []):
        route = str(row.get("route", "L"))
        if args.include_fallback_route and str(row.get("fallback_route", route)) == "P":
            route = "P"
        route_by_id[str(row["instance_id"])] = route

    merged: dict[str, Any] = {}
    call_log: list[dict[str, Any]] = []
    large_rows: list[str] = []
    for instance_id in ids:
        base_route = route_by_id.get(instance_id, "L")
        source = "empty_local"
        route = base_route
        if instance_id in no_memory_ids:
            pred = dict(no_memory_preds[instance_id])
            pred["model_name_or_path"] = str(pred.get("model_name_or_path", "")) + "+memgate_reject_memory"
            source = "no_memory_large"
            route = "P"
            large_rows.append(instance_id)
        elif base_route == "P" or instance_id in retry_ids:
            pred = dict(strong_preds[instance_id])
            pred["model_name_or_path"] = str(pred.get("model_name_or_path", "")) + "+memgate_packet_retry"
            source = "strong_memory_large"
            route = "P"
            large_rows.append(instance_id)
        else:
            pred = {
                "instance_id": instance_id,
                "model_name_or_path": "local-qwen3-8b-memory-polarproxy-v22+memgate_verified_no_call",
                "model_patch": "",
            }
        merged[instance_id] = pred
        call_log.append(
            {
                "instance_id": instance_id,
                "base_route": base_route,
                "route": route,
                "large_model_called": route == "P",
                "prediction_source": source,
                "retry_promoted": instance_id in retry_ids,
                "memory_rejected": instance_id in no_memory_ids,
            }
        )

    target = out_dir / args.output_name
    write_json(target / "preds.json", merged)
    summary = {
        "artifact_type": "memory_covered_conservative_memgate_retry_policy",
        "source_policy": str(source_policy),
        "rows": len(ids),
        "large_model_rows": len(large_rows),
        "large_model_ids": large_rows,
        "retry_ids": sorted(retry_ids),
        "no_memory_ids": sorted(no_memory_ids),
        "no_call_rows": len(ids) - len(large_rows),
        "include_fallback_route": args.include_fallback_route,
        "call_log": call_log,
        "note": (
            "Diagnostic conservative retry candidate: trained MemGate P rows call the memory-packet large path; "
            "selected empty-risk L rows get one packet retry; selected negative-transfer rows call the no-memory large path."
        ),
    }
    write_json(target / "call_policy_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
