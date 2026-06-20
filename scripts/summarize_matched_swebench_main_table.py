#!/usr/bin/env python3
"""Summarize matched SWE-Bench main-table artifacts into JSON/CSV."""

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


def find_summary(eval_dir: Path, run_id: str) -> Path:
    matches = sorted(eval_dir.glob(f"*.{run_id}.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No summary matching *.{run_id}.json in {eval_dir}")
    return matches[0]


def trajectory_path(run_dir: Path, instance_id: str) -> Path:
    return run_dir / instance_id / f"{instance_id}.traj.json"


def merge_selective_preds(
    *,
    ids: list[str],
    self_run_dir: Path,
    delegate_run_dir: Path,
    delegate_ids: list[str],
    output_dir: Path,
) -> Path:
    self_preds = read_json(self_run_dir / "preds.json")
    delegate_preds = read_json(delegate_run_dir / "preds.json") if delegate_ids else {}
    delegate_set = set(delegate_ids)
    merged: dict[str, Any] = {}
    call_log: list[dict[str, Any]] = []
    for instance_id in ids:
        if instance_id in delegate_set:
            if instance_id not in delegate_preds:
                raise ValueError(f"Missing delegate prediction for {instance_id}")
            row = dict(delegate_preds[instance_id])
            row["model_name_or_path"] = str(row.get("model_name_or_path", "")) + "+selective_P_call"
            merged[instance_id] = row
            call_log.append({"instance_id": instance_id, "route": "P", "large_model_called": True})
        else:
            if instance_id not in self_preds:
                raise ValueError(f"Missing self prediction for {instance_id}")
            row = dict(self_preds[instance_id])
            row["model_name_or_path"] = str(row.get("model_name_or_path", "")) + "+selective_L_local"
            merged[instance_id] = row
            call_log.append({"instance_id": instance_id, "route": "L", "large_model_called": False})
    output_dir.mkdir(parents=True, exist_ok=True)
    preds_path = output_dir / "preds.json"
    write_json(preds_path, merged)
    write_json(
        output_dir / "call_policy_summary.json",
        {
            "artifact_type": "matched_swebench_selective_call_policy",
            "rows": len(ids),
            "large_model_calls": len(delegate_ids),
            "no_call_rows": len(ids) - len(delegate_ids),
            "call_log": call_log,
            "ready_for_harness_eval": True,
        },
    )
    return preds_path


def summary_sets(path: Path | None) -> dict[str, set[str]]:
    if path is None or not path.exists():
        return {"resolved": set(), "unresolved": set(), "empty": set(), "error": set()}
    payload = read_json(path)
    return {
        "resolved": set(payload.get("resolved_ids", [])),
        "unresolved": set(payload.get("unresolved_ids", [])),
        "empty": set(payload.get("empty_patch_ids", [])),
        "error": set(payload.get("error_ids", [])),
    }


def usage_for_run(run_dir: Path, ids: list[str]) -> dict[str, Any]:
    cost = 0.0
    api_calls = 0
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    trajectories = 0
    for instance_id in ids:
        path = trajectory_path(run_dir, instance_id)
        if not path.exists():
            continue
        trajectories += 1
        trajectory = read_json(path)
        stats = ((trajectory.get("info") or {}).get("model_stats") or {})
        cost += float(stats.get("instance_cost", 0.0) or 0.0)
        api_calls += int(stats.get("api_calls", 0) or 0)
        for message in trajectory.get("messages", []):
            response = ((message.get("extra") or {}).get("response") or {})
            usage = response.get("usage") or {}
            prompt_tokens += int(usage.get("prompt_tokens", 0) or 0)
            completion_tokens += int(usage.get("completion_tokens", 0) or 0)
            total_tokens += int(usage.get("total_tokens", 0) or 0)
    return {
        "trajectories": trajectories,
        "api_calls": api_calls,
        "cost": round(cost, 6),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def condition_row(
    *,
    name: str,
    ids: list[str],
    summary_path: Path | None,
    large_usage_run_dir: Path | None,
    large_model_calls_override: int | None = None,
    large_model_rows_override: int | None = None,
    route_errors: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sets = summary_sets(summary_path)
    usage = usage_for_run(large_usage_run_dir, ids) if large_usage_run_dir is not None else {
        "trajectories": 0,
        "api_calls": 0,
        "cost": 0.0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    large_calls = large_model_calls_override if large_model_calls_override is not None else usage["api_calls"]
    large_rows = large_model_rows_override if large_model_rows_override is not None else usage["trajectories"]
    total = len(ids)
    row = {
        "condition": name,
        "instances": total,
        "resolved": len(sets["resolved"] & set(ids)),
        "resolved_rate": round(len(sets["resolved"] & set(ids)) / total, 4) if total else 0.0,
        "large_model_rows": int(large_rows),
        "large_model_api_turns": int(large_calls),
        "large_model_calls": int(large_calls),
        "token_cost": usage["total_tokens"],
        "dollar_cost": usage["cost"],
        "empty_patch": len(sets["empty"] & set(ids)),
        "empty_patch_rate": round(len(sets["empty"] & set(ids)) / total, 4) if total else 0.0,
        "harness_error": len(sets["error"] & set(ids)),
        "harness_error_rate": round(len(sets["error"] & set(ids)) / total, 4) if total else 0.0,
        "prompt_tokens": usage["prompt_tokens"],
        "completion_tokens": usage["completion_tokens"],
    }
    if route_errors:
        row.update(route_errors)
    return row


def write_csv(rows: list[dict[str, Any]], output: Path) -> None:
    fieldnames = sorted({key for row in rows for key in row})
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def selective_route_errors(
    *,
    ids: list[str],
    call_policy_path: Path,
    self_summary: Path,
    large_reference_summary: Path,
) -> dict[str, Any]:
    policy = read_json(call_policy_path)
    route_by_id = {row["instance_id"]: row["route"] for row in policy.get("call_log", [])}
    self_sets = summary_sets(self_summary)
    large_sets = summary_sets(large_reference_summary)
    false_delegate = 0
    missed_delegate = 0
    self_gold = 0
    delegate_gold = 0
    for instance_id in ids:
        route = route_by_id.get(instance_id, "L")
        if instance_id in self_sets["resolved"]:
            gold = "SELF_HANDLE"
            self_gold += 1
        elif instance_id in large_sets["resolved"]:
            gold = "DELEGATE"
            delegate_gold += 1
        else:
            gold = "SELF_HANDLE"
            self_gold += 1
        if gold == "SELF_HANDLE" and route == "P":
            false_delegate += 1
        if gold == "DELEGATE" and route != "P":
            missed_delegate += 1
    return {
        "self_handle_gold": self_gold,
        "delegate_gold": delegate_gold,
        "self_handle_false_delegate": false_delegate,
        "self_handle_false_delegate_rate": round(false_delegate / self_gold, 4) if self_gold else 0.0,
        "delegate_missed": missed_delegate,
        "delegate_missed_rate": round(missed_delegate / delegate_gold, 4) if delegate_gold else 0.0,
    }


def selective_route_errors_large_reference(*, ids: list[str], call_policy_path: Path, large_reference_summary: Path) -> dict[str, Any]:
    policy = read_json(call_policy_path)
    route_by_id = {row["instance_id"]: row["route"] for row in policy.get("call_log", [])}
    large_sets = read_json(large_reference_summary)
    delegate_gold_ids = set(large_sets.get("resolved_ids", [])) & set(ids)
    false_delegate = 0
    missed_delegate = 0
    for instance_id in ids:
        route = route_by_id.get(instance_id, "L")
        gold = "DELEGATE" if instance_id in delegate_gold_ids else "SELF_HANDLE"
        if gold == "SELF_HANDLE" and route == "P":
            false_delegate += 1
        if gold == "DELEGATE" and route != "P":
            missed_delegate += 1
    self_gold = len(ids) - len(delegate_gold_ids)
    delegate_gold = len(delegate_gold_ids)
    return {
        "self_handle_gold": self_gold,
        "delegate_gold": delegate_gold,
        "self_handle_false_delegate": false_delegate,
        "self_handle_false_delegate_rate": round(false_delegate / self_gold, 4) if self_gold else 0.0,
        "delegate_missed": missed_delegate,
        "delegate_missed_rate": round(missed_delegate / delegate_gold, 4) if delegate_gold else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--delegate-limit", type=int, default=0, help="Use only the first N completed delegate predictions.")
    parser.add_argument(
        "--baseline-run-suffix",
        default="",
        help="Optional suffix between baseline run id and instance count, e.g. 'docker' for matched-main-no-memory-docker-36.",
    )
    parser.add_argument(
        "--route-gold",
        choices=["legacy", "large-reference"],
        default="legacy",
        help="Use legacy self/large attribution or mark only large-reference resolved rows as DELEGATE gold.",
    )
    parser.add_argument("--merge-only", action="store_true")
    args = parser.parse_args()

    out_dir = args.out_dir
    ids = read_json(out_dir / "instances.json")["ids"]
    delegate_ids = read_json(out_dir / "delegate_ids.json")["delegate_ids"]
    delegate_preds = read_json(out_dir / "selective_delegate_large" / "preds.json")
    completed_delegate_ids = [instance_id for instance_id in delegate_ids if instance_id in delegate_preds]
    if args.delegate_limit:
        completed_delegate_ids = completed_delegate_ids[: args.delegate_limit]

    suffix = f"delegate{len(completed_delegate_ids):02d}"
    merged_dir = out_dir / f"selective_merged_{suffix}"
    merge_selective_preds(
        ids=ids,
        self_run_dir=out_dir / "selective_self_local",
        delegate_run_dir=out_dir / "selective_delegate_large",
        delegate_ids=completed_delegate_ids,
        output_dir=merged_dir,
    )
    if args.merge_only:
        print(merged_dir)
        return 0

    eval_dir = out_dir / "eval"
    baseline_id_suffix = f"-{args.baseline_run_suffix}" if args.baseline_run_suffix else ""
    baseline_dir_suffix = f"_{args.baseline_run_suffix}" if args.baseline_run_suffix else ""
    output_suffix = f"{suffix}_{args.baseline_run_suffix}" if args.baseline_run_suffix else suffix
    no_summary = find_summary(eval_dir, f"matched-main-no-memory{baseline_id_suffix}-36")
    simple_summary = find_summary(eval_dir, f"matched-main-simple-memory{baseline_id_suffix}-36")
    selective_summary = find_summary(eval_dir, f"matched-main-selective-merged-{suffix}")
    self_summary = find_summary(eval_dir, "matched-main-selective-self-local-36")

    if args.route_gold == "large-reference":
        route_errors = selective_route_errors_large_reference(
            ids=ids,
            call_policy_path=merged_dir / "call_policy_summary.json",
            large_reference_summary=no_summary,
        )
    else:
        route_errors = selective_route_errors(
            ids=ids,
            call_policy_path=merged_dir / "call_policy_summary.json",
            self_summary=self_summary,
            large_reference_summary=no_summary,
        )
    rows = [
        condition_row(
            name="no_memory_no_collaboration",
            ids=ids,
            summary_path=no_summary,
            large_usage_run_dir=out_dir / f"no_memory_large{baseline_dir_suffix}",
        ),
        condition_row(
            name="simple_memory",
            ids=ids,
            summary_path=simple_summary,
            large_usage_run_dir=out_dir / f"simple_memory_large{baseline_dir_suffix}",
        ),
        condition_row(
            name=f"trained_memgate_packet_selective_{suffix}",
            ids=ids,
            summary_path=selective_summary,
            large_usage_run_dir=out_dir / "selective_delegate_large",
            large_model_rows_override=len(completed_delegate_ids),
            route_errors=route_errors,
        ),
    ]
    payload = {
        "artifact_type": "matched_swebench_main_table_summary",
        "instances": len(ids),
        "delegate_predictions_used": len(completed_delegate_ids),
        "delegate_ids_used": completed_delegate_ids,
        "baseline_run_suffix": args.baseline_run_suffix,
        "route_gold": args.route_gold,
        "rows": rows,
    }
    write_json(out_dir / f"main_table_summary_{output_suffix}.json", payload)
    write_csv(rows, out_dir / f"main_table_summary_{output_suffix}.csv")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
