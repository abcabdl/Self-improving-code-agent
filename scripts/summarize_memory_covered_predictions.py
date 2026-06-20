#!/usr/bin/env python3
"""Summarize matched memory-covered predictions before SWE-bench harness eval."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


BASE = Path("runs/matched-swebench-main-table-memory-covered-36")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def trajectory_path(run_dir: Path, instance_id: str) -> Path:
    return run_dir / instance_id / f"{instance_id}.traj.json"


def usage_for_run(run_dir: Path, ids: list[str]) -> dict[str, Any]:
    api_calls = prompt_tokens = completion_tokens = total_tokens = 0
    dollar_cost = 0.0
    rows_with_trajectory = 0
    for instance_id in ids:
        path = trajectory_path(run_dir, instance_id)
        if not path.exists():
            continue
        rows_with_trajectory += 1
        try:
            traj = read_json(path)
        except Exception:
            continue
        stats = ((traj.get("info") or {}).get("model_stats") or {})
        api_calls += int(stats.get("api_calls", 0) or 0)
        dollar_cost += float(stats.get("instance_cost", 0.0) or 0.0)
        for message in traj.get("messages", []):
            usage = (((message.get("extra") or {}).get("response") or {}).get("usage") or {})
            prompt_tokens += int(usage.get("prompt_tokens", 0) or 0)
            completion_tokens += int(usage.get("completion_tokens", 0) or 0)
            total_tokens += int(usage.get("total_tokens", 0) or 0)
    return {
        "rows_with_trajectory": rows_with_trajectory,
        "large_model_calls": api_calls,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "token_cost": total_tokens,
        "dollar_cost": round(dollar_cost, 6),
    }


def empty_count(preds: dict[str, Any], ids: list[str]) -> int:
    return sum(1 for instance_id in ids if not ((preds.get(instance_id) or {}).get("model_patch") or "").strip())


def main() -> int:
    ids = read_json(BASE / "instances.json")["ids"]
    no_preds = read_json(BASE / "no_memory_large" / "preds.json")
    strong_preds = read_json(BASE / "strong_memory_large" / "preds.json")
    selective_preds = read_json(BASE / "trained_memgate_packet_selective" / "preds.json")
    selective_policy = read_json(BASE / "trained_memgate_packet_selective" / "call_policy_summary.json")
    large_ids = selective_policy["large_model_ids"]

    no_usage = usage_for_run(BASE / "no_memory_large", ids)
    strong_usage = usage_for_run(BASE / "strong_memory_large", ids)
    selective_usage = usage_for_run(BASE / "strong_memory_large", large_ids)

    rows = [
        {
            "condition": "no_memory_no_collaboration",
            "instances": len(ids),
            "completed_predictions": len(no_preds),
            "resolved": "",
            "resolved_rate": "",
            "large_model_rows": no_usage["rows_with_trajectory"],
            **no_usage,
            "empty_patch": empty_count(no_preds, ids),
            "empty_patch_rate": round(empty_count(no_preds, ids) / len(ids), 4),
            "harness_error": "",
            "harness_error_rate": "",
            "note": "13 rows are explicit empty placeholders after provider returned insufficient balance; 4 rows backfilled from prior identical no-memory gpt-5.4-mini run.",
        },
        {
            "condition": "strong_non_trained_memory",
            "instances": len(ids),
            "completed_predictions": len(strong_preds),
            "resolved": "",
            "resolved_rate": "",
            "large_model_rows": strong_usage["rows_with_trajectory"],
            **strong_usage,
            "empty_patch": empty_count(strong_preds, ids),
            "empty_patch_rate": round(empty_count(strong_preds, ids) / len(ids), 4),
            "harness_error": "",
            "harness_error_rate": "",
            "note": "Official harness pending; local Docker hit pagefile pressure.",
        },
        {
            "condition": "trained_memgate_packet_selective",
            "instances": len(ids),
            "completed_predictions": len(selective_preds),
            "resolved": "",
            "resolved_rate": "",
            "large_model_rows": len(large_ids),
            **selective_usage,
            "empty_patch": empty_count(selective_preds, ids),
            "empty_patch_rate": round(empty_count(selective_preds, ids) / len(ids), 4),
            "harness_error": "",
            "harness_error_rate": "",
            "self_handle_false_delegate_rate": "",
            "delegate_missed_rate": "",
            "note": "Selective policy uses MemGate readout P or calibrated high-confidence fallback P.",
        },
    ]

    out_json = BASE / "main_table_prediction_summary_provisional.json"
    out_csv = BASE / "main_table_prediction_summary_provisional.csv"
    write_json(
        out_json,
        {
            "artifact_type": "prediction_level_provisional_summary",
            "warning": "Resolved/harness metrics are intentionally blank because official SWE-bench harness could not finish on local Docker due pagefile pressure.",
            "rows": rows,
            "policy": {
                "large_model_rows": len(large_ids),
                "no_call_rows": len(selective_policy["no_call_ids"]),
                "source_policy": selective_policy["source_policy"],
            },
        },
    )
    fieldnames = sorted({key for row in rows for key in row})
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(out_json)
    print(out_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
