#!/usr/bin/env python3
"""Build and summarize the memory-covered matched SWE-Bench main table.

This script is intentionally narrow: it targets
``runs/matched-swebench-main-table-memory-covered-36`` and the final three-way
comparison used by the paper:

* A: no memory / no collaboration, all rows call the large model.
* B: strong non-trained memory, all rows call the large model.
* C: trained MemGate + packet selective, where P rows reuse B's large-model
  packet-call predictions and L rows make no large-model call.

Official resolved/empty/error counts come from SWE-bench harness summary JSONs
when available.  The script can also emit the merged C ``preds.json`` before
the harness is run.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def find_summary(eval_dir: Path, run_id: str) -> Path | None:
    matches = sorted(eval_dir.glob(f"*.{run_id}.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def summary_sets(path: Path | None) -> dict[str, set[str]]:
    if path is None or not path.exists():
        return {"resolved": set(), "empty": set(), "error": set(), "unresolved": set()}
    payload = read_json(path)
    return {
        "resolved": set(payload.get("resolved_ids", [])),
        "empty": set(payload.get("empty_patch_ids", [])),
        "error": set(payload.get("error_ids", [])),
        "unresolved": set(payload.get("unresolved_ids", [])),
    }


def trajectory_path(run_dir: Path, instance_id: str) -> Path:
    return run_dir / instance_id / f"{instance_id}.traj.json"


def usage_for_run(run_dir: Path, ids: list[str]) -> dict[str, Any]:
    api_calls = 0
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    cost = 0.0
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
        cost += float(stats.get("instance_cost", 0.0) or 0.0)
        for message in traj.get("messages", []):
            usage = (((message.get("extra") or {}).get("response") or {}).get("usage") or {})
            prompt_tokens += int(usage.get("prompt_tokens", 0) or 0)
            completion_tokens += int(usage.get("completion_tokens", 0) or 0)
            total_tokens += int(usage.get("total_tokens", 0) or 0)
    return {
        "rows_with_trajectory": rows_with_trajectory,
        "api_calls": api_calls,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "dollar_cost": round(cost, 6),
    }


def completed_pred_ids(run_dir: Path) -> set[str]:
    path = run_dir / "preds.json"
    if not path.exists():
        return set()
    payload = read_json(path)
    return set(payload) if isinstance(payload, dict) else set()


def empty_patch_prediction(instance_id: str) -> dict[str, Any]:
    return {
        "instance_id": instance_id,
        "model_name_or_path": "local-qwen3-8b-memory-polarproxy-v22+memgate_no_large_call",
        "model_patch": "",
    }


def build_selective_preds(
    *,
    ids: list[str],
    strong_run_dir: Path,
    policy_path: Path,
    output_dir: Path,
    require_complete_delegate: bool,
) -> dict[str, Any]:
    strong_preds = read_json(strong_run_dir / "preds.json")
    policy = read_json(policy_path)
    call_log = policy.get("call_log", [])
    route_by_id = {}
    for row in call_log:
        instance_id = str(row.get("instance_id"))
        route = str(row.get("route", "L"))
        fallback = str(row.get("fallback_route", route))
        route_by_id[instance_id] = "P" if route == "P" or fallback == "P" else "L"
    merged: dict[str, Any] = {}
    missing_delegate: list[str] = []
    large_ids: list[str] = []
    no_call_ids: list[str] = []
    for instance_id in ids:
        route = route_by_id.get(instance_id, "L")
        if route == "P":
            large_ids.append(instance_id)
            if instance_id not in strong_preds:
                missing_delegate.append(instance_id)
                merged[instance_id] = empty_patch_prediction(instance_id)
                continue
            row = dict(strong_preds[instance_id])
            row["model_name_or_path"] = str(row.get("model_name_or_path", "")) + "+memgate_packet_P"
            merged[instance_id] = row
        else:
            no_call_ids.append(instance_id)
            merged[instance_id] = empty_patch_prediction(instance_id)

    if missing_delegate and require_complete_delegate:
        raise SystemExit(
            "Missing strong-memory predictions for delegated rows: " + ", ".join(missing_delegate)
        )

    write_json(output_dir / "preds.json", merged)
    call_policy = {
        "artifact_type": "memory_covered_trained_memgate_packet_selective_merge",
        "source_policy": str(policy_path),
        "large_prediction_source": str(strong_run_dir),
        "rows": len(ids),
        "large_model_rows": len(large_ids),
        "no_call_rows": len(no_call_ids),
        "large_model_ids": large_ids,
        "no_call_ids": no_call_ids,
        "missing_delegate_predictions": missing_delegate,
        "call_log": [
            {
                "instance_id": instance_id,
                "route": route_by_id.get(instance_id, "L"),
                "readout_route": next(
                    (str(row.get("route", "L")) for row in call_log if str(row.get("instance_id")) == instance_id),
                    route_by_id.get(instance_id, "L"),
                ),
                "fallback_route": next(
                    (str(row.get("fallback_route", row.get("route", "L"))) for row in call_log if str(row.get("instance_id")) == instance_id),
                    route_by_id.get(instance_id, "L"),
                ),
                "large_model_called": route_by_id.get(instance_id, "L") == "P",
            }
            for instance_id in ids
        ],
    }
    write_json(output_dir / "call_policy_summary.json", call_policy)
    return call_policy


def route_error_metrics(
    *,
    ids: list[str],
    policy_path: Path,
    no_memory_summary: Path | None,
) -> dict[str, Any]:
    policy = read_json(policy_path)
    route_by_id = {str(row.get("instance_id")): str(row.get("route", "L")) for row in policy.get("call_log", [])}
    no_sets = summary_sets(no_memory_summary)
    delegate_gold = set(ids) & no_sets["resolved"]
    self_gold = set(ids) - delegate_gold
    false_delegate = [instance_id for instance_id in self_gold if route_by_id.get(instance_id, "L") == "P"]
    missed_delegate = [instance_id for instance_id in delegate_gold if route_by_id.get(instance_id, "L") != "P"]
    return {
        "self_handle_gold": len(self_gold),
        "delegate_gold": len(delegate_gold),
        "self_handle_false_delegate": len(false_delegate),
        "self_handle_false_delegate_rate": round(len(false_delegate) / max(1, len(self_gold)), 4),
        "delegate_missed": len(missed_delegate),
        "delegate_missed_rate": round(len(missed_delegate) / max(1, len(delegate_gold)), 4),
        "self_handle_false_delegate_ids": sorted(false_delegate),
        "delegate_missed_ids": sorted(missed_delegate),
    }


def condition_row(
    *,
    name: str,
    ids: list[str],
    summary_path: Path | None,
    usage_run_dir: Path | None,
    usage_ids: list[str] | None = None,
    large_model_rows: int | None = None,
    route_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sets = summary_sets(summary_path)
    usage_scope = usage_ids if usage_ids is not None else ids
    usage = usage_for_run(usage_run_dir, usage_scope) if usage_run_dir is not None else {
        "rows_with_trajectory": 0,
        "api_calls": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "dollar_cost": 0.0,
    }
    id_set = set(ids)
    row: dict[str, Any] = {
        "condition": name,
        "instances": len(ids),
        "resolved": len(sets["resolved"] & id_set),
        "resolved_rate": round(len(sets["resolved"] & id_set) / max(1, len(ids)), 4),
        "large_model_rows": int(large_model_rows if large_model_rows is not None else usage["rows_with_trajectory"]),
        "large_model_calls": int(usage["api_calls"]),
        "large_model_api_turns": int(usage["api_calls"]),
        "token_cost": int(usage["total_tokens"]),
        "prompt_tokens": int(usage["prompt_tokens"]),
        "completion_tokens": int(usage["completion_tokens"]),
        "dollar_cost": usage["dollar_cost"],
        "empty_patch": len(sets["empty"] & id_set),
        "empty_patch_rate": round(len(sets["empty"] & id_set) / max(1, len(ids)), 4),
        "harness_error": len(sets["error"] & id_set),
        "harness_error_rate": round(len(sets["error"] & id_set) / max(1, len(ids)), 4),
    }
    if route_metrics:
        for key, value in route_metrics.items():
            if not key.endswith("_ids"):
                row[key] = value
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("runs/matched-swebench-main-table-memory-covered-36"))
    parser.add_argument(
        "--policy-path",
        type=Path,
        default=None,
        help="MemGate policy summary. Defaults to memgate_readout_policy/call_policy_summary.json.",
    )
    parser.add_argument("--build-selective", action="store_true")
    parser.add_argument("--require-complete-delegate", action="store_true")
    parser.add_argument("--summarize", action="store_true")
    args = parser.parse_args()

    out_dir = args.out_dir
    ids = read_json(out_dir / "instances.json")["ids"]
    no_dir = out_dir / "no_memory_large"
    strong_dir = out_dir / "strong_memory_large"
    selective_dir = out_dir / "trained_memgate_packet_selective"
    c_policy = args.policy_path or out_dir / "memgate_readout_policy" / "call_policy_summary.json"

    if args.build_selective:
        call_policy = build_selective_preds(
            ids=ids,
            strong_run_dir=strong_dir,
            policy_path=c_policy,
            output_dir=selective_dir,
            require_complete_delegate=args.require_complete_delegate,
        )
        print(json.dumps(call_policy, ensure_ascii=False, indent=2, sort_keys=True))

    if not args.summarize:
        return 0

    eval_dir = out_dir / "eval"
    no_summary = find_summary(eval_dir, "memory-covered-no-memory-36")
    strong_summary = find_summary(eval_dir, "memory-covered-strong-memory-36")
    selective_summary = find_summary(eval_dir, "memory-covered-trained-memgate-selective-36")
    route_metrics = route_error_metrics(
        ids=ids,
        policy_path=selective_dir / "call_policy_summary.json",
        no_memory_summary=no_summary,
    )
    selective_policy = read_json(selective_dir / "call_policy_summary.json")
    selective_large_ids = selective_policy.get("large_model_ids", [])
    rows = [
        condition_row(
            name="no_memory_no_collaboration",
            ids=ids,
            summary_path=no_summary,
            usage_run_dir=no_dir,
        ),
        condition_row(
            name="strong_non_trained_memory",
            ids=ids,
            summary_path=strong_summary,
            usage_run_dir=strong_dir,
        ),
        condition_row(
            name="trained_memgate_packet_selective",
            ids=ids,
            summary_path=selective_summary,
            usage_run_dir=strong_dir,
            usage_ids=list(selective_large_ids),
            large_model_rows=len(selective_large_ids),
            route_metrics=route_metrics,
        ),
    ]
    payload = {
        "artifact_type": "memory_covered_matched_swebench_main_table_summary",
        "instances": len(ids),
        "completed_predictions": {
            "no_memory_large": len(completed_pred_ids(no_dir)),
            "strong_memory_large": len(completed_pred_ids(strong_dir)),
            "trained_memgate_packet_selective": len(completed_pred_ids(selective_dir)),
        },
        "summary_files": {
            "no_memory": str(no_summary) if no_summary else "",
            "strong_memory": str(strong_summary) if strong_summary else "",
            "trained_memgate_packet_selective": str(selective_summary) if selective_summary else "",
        },
        "route_metrics_detail": route_metrics,
        "rows": rows,
    }
    write_json(out_dir / "main_table_summary_memory_covered.json", payload)
    write_csv(out_dir / "main_table_summary_memory_covered.csv", rows)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
