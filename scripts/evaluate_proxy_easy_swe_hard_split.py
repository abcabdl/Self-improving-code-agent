#!/usr/bin/env python3
"""Evaluate a mixed proxy-easy + SWE-hard split without conflating metrics."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summary_sets(path: Path | None) -> dict[str, set[str]]:
    if path is None:
        return {"resolved": set(), "unresolved": set(), "empty": set(), "error": set()}
    payload = read_json(path)
    return {
        "resolved": {str(item) for item in payload.get("resolved_ids", [])},
        "unresolved": {str(item) for item in payload.get("unresolved_ids", [])},
        "empty": {str(item) for item in payload.get("empty_patch_ids", [])},
        "error": {str(item) for item in payload.get("error_ids", [])},
    }


def trajectory_path(run_dir: Path, instance_id: str) -> Path:
    return run_dir / instance_id / f"{instance_id}.traj.json"


def usage_by_instance(run_dir: Path | None) -> dict[str, dict[str, Any]]:
    if run_dir is None:
        return {}
    usage: dict[str, dict[str, Any]] = {}
    for path in run_dir.glob("*/*.traj.json"):
        instance_id = path.parent.name
        try:
            trajectory = read_json(path)
        except Exception:
            continue
        stats = ((trajectory.get("info") or {}).get("model_stats") or {})
        prompt_tokens = completion_tokens = total_tokens = 0
        for message in trajectory.get("messages", []):
            response = ((message.get("extra") or {}).get("response") or {})
            msg_usage = response.get("usage") or {}
            prompt_tokens += int(msg_usage.get("prompt_tokens", 0) or 0)
            completion_tokens += int(msg_usage.get("completion_tokens", 0) or 0)
            total_tokens += int(msg_usage.get("total_tokens", 0) or 0)
        usage[instance_id] = {
            "api_calls": int(stats.get("api_calls", 0) or 0),
            "dollar_cost": round(float(stats.get("instance_cost", 0.0) or 0.0), 6),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }
    return usage


def route_from_policy(row: dict[str, Any], *, assume_route: str) -> tuple[str, bool, int]:
    if row:
        route = str(row.get("route", row.get("fallback_route", ""))).upper()
        if route not in {"L", "P"}:
            route = "P" if bool(row.get("large_model_called")) else "L"
        large_called = bool(row.get("large_model_called", route == "P")) or route == "P"
        usage = row.get("usage") if isinstance(row.get("usage"), dict) else {}
        large_tokens = int(
            row.get("large_total_tokens")
            or row.get("total_tokens")
            or usage.get("total_tokens", 0)
            or 0
        )
        return route, large_called, large_tokens if large_called else 0
    if assume_route in {"L", "P"}:
        return assume_route, assume_route == "P", 0
    return "", False, 0


def proxy_pass(row: dict[str, Any], *, min_strict_score: float) -> bool:
    return (
        bool(row.get("has_action"))
        and bool(row.get("skill_match"))
        and bool(row.get("semantic_pass"))
        and float(row.get("strict_score", 0.0) or 0.0) >= min_strict_score
    )


def build_rows(
    *,
    mixed_rows: list[dict[str, Any]],
    proxy_results: list[dict[str, Any]],
    swe_sets: dict[str, set[str]],
    call_policy: dict[str, Any] | None,
    large_usage_by_id: dict[str, dict[str, Any]],
    assume_route: str,
    min_strict_score: float,
) -> list[dict[str, Any]]:
    proxy_by_id = {str(row.get("task_id")): row for row in proxy_results}
    policy_rows = {}
    if call_policy:
        policy_rows = {str(row.get("instance_id")): row for row in call_policy.get("call_log", [])}

    rows: list[dict[str, Any]] = []
    for item in mixed_rows:
        instance_id = str(item.get("id", ""))
        kind = str(item.get("kind", ""))
        route, large_called, large_tokens = route_from_policy(policy_rows.get(instance_id, {}), assume_route=assume_route)
        large_usage = large_usage_by_id.get(instance_id, {}) if large_called else {}
        if large_usage:
            large_tokens = int(large_usage.get("total_tokens", 0) or large_tokens)
        gold_route = "L" if kind == "proxy_easy" else "P" if kind == "swe_hard" else ""
        route_correct = bool(route and gold_route and route == gold_route)
        base = {
            "id": instance_id,
            "kind": kind,
            "gold_route": gold_route,
            "route": route,
            "route_correct": route_correct,
            "large_model_called": large_called,
            "large_api_calls": int(large_usage.get("api_calls", 0) or 0),
            "large_dollar_cost": float(large_usage.get("dollar_cost", 0.0) or 0.0),
            "large_prompt_tokens": int(large_usage.get("prompt_tokens", 0) or 0),
            "large_completion_tokens": int(large_usage.get("completion_tokens", 0) or 0),
            "large_total_tokens": large_tokens,
        }
        if kind == "proxy_easy":
            result = proxy_by_id.get(instance_id, {})
            usage = result.get("usage") if isinstance(result.get("usage"), dict) else {}
            passed = proxy_pass(result, min_strict_score=min_strict_score) if result else False
            rows.append(
                {
                    **base,
                    "metric": "proxy_easy_pass",
                    "passed": passed,
                    "strict_score": float(result.get("strict_score", 0.0) or 0.0),
                    "semantic_pass": bool(result.get("semantic_pass")),
                    "skill_match": bool(result.get("skill_match")),
                    "local_total_tokens": int(usage.get("total_tokens", 0) or 0),
                    "status": "passed" if passed else "failed",
                }
            )
            continue

        status = "missing_summary"
        passed = False
        if instance_id in swe_sets["resolved"]:
            status = "resolved"
            passed = True
        elif instance_id in swe_sets["empty"]:
            status = "empty"
        elif instance_id in swe_sets["error"]:
            status = "error"
        elif instance_id in swe_sets["unresolved"]:
            status = "unresolved"
        rows.append(
            {
                **base,
                "metric": "swe_hard_resolved",
                "passed": passed,
                "strict_score": "",
                "semantic_pass": "",
                "skill_match": "",
                "local_total_tokens": 0,
                "status": status,
            }
        )
    return rows


def rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def summarize(rows: list[dict[str, Any]], *, condition: str, split_manifest: dict[str, Any], min_strict_score: float) -> dict[str, Any]:
    proxy = [row for row in rows if row["kind"] == "proxy_easy"]
    hard = [row for row in rows if row["kind"] == "swe_hard"]
    routed = [row for row in rows if row.get("route")]
    route_counts = Counter(str(row.get("route") or "missing") for row in rows)
    hard_status = Counter(str(row.get("status")) for row in hard)
    proxy_passed = sum(bool(row["passed"]) for row in proxy)
    hard_resolved = sum(bool(row["passed"]) for row in hard)
    route_correct_and_passed = sum(bool(row["passed"]) and bool(row.get("route_correct")) for row in rows)
    large_rows = sum(bool(row["large_model_called"]) for row in rows)
    large_tokens = sum(int(row.get("large_total_tokens", 0) or 0) for row in rows)
    large_api_calls = sum(int(row.get("large_api_calls", 0) or 0) for row in rows)
    large_dollar_cost = round(sum(float(row.get("large_dollar_cost", 0.0) or 0.0) for row in rows), 6)
    local_tokens = sum(int(row.get("local_total_tokens", 0) or 0) for row in rows)
    return {
        "artifact_type": "proxy_easy_swe_hard_mixed_evaluation",
        "condition": condition,
        "split_artifact_type": split_manifest.get("artifact_type", ""),
        "counts": {
            "rows": len(rows),
            "proxy_easy": len(proxy),
            "swe_hard": len(hard),
            "routed_rows": len(routed),
        },
        "proxy_easy": {
            "passed": proxy_passed,
            "total": len(proxy),
            "pass_rate": rate(proxy_passed, len(proxy)),
            "mean_strict_score": round(
                sum(float(row.get("strict_score") or 0.0) for row in proxy) / max(1, len(proxy)),
                6,
            ),
            "local_total_tokens": local_tokens,
            "local_tokens_per_task": round(local_tokens / max(1, len(proxy)), 3),
            "min_strict_score": min_strict_score,
        },
        "swe_hard": {
            "resolved": hard_resolved,
            "total": len(hard),
            "resolved_rate": rate(hard_resolved, len(hard)),
            "status_counts": dict(sorted(hard_status.items())),
        },
        "route": {
            "route_counts": dict(sorted(route_counts.items())),
            "route_correct": sum(bool(row.get("route_correct")) for row in rows),
            "route_accuracy": rate(sum(bool(row.get("route_correct")) for row in rows), len(rows)),
            "proxy_easy_false_delegate": sum(row["kind"] == "proxy_easy" and row.get("route") == "P" for row in rows),
            "swe_hard_missed_delegate": sum(row["kind"] == "swe_hard" and row.get("route") == "L" for row in rows),
            "large_model_rows": large_rows,
            "large_model_row_rate": rate(large_rows, len(rows)),
            "large_api_calls": large_api_calls,
            "large_dollar_cost": large_dollar_cost,
            "large_total_tokens": large_tokens,
        },
        "mixed_units": {
            "proxy_pass_plus_swe_resolved": proxy_passed + hard_resolved,
            "route_correct_success": route_correct_and_passed,
            "route_correct_success_rate": rate(route_correct_and_passed, len(rows)),
            "total_rows": len(rows),
            "rate": rate(proxy_passed + hard_resolved, len(rows)),
            "note": "This is a routing/cost utility count; proxy_easy pass is not official SWE-Bench resolved.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split-dir", type=Path, required=True)
    parser.add_argument("--proxy-easy-results", type=Path, required=True)
    parser.add_argument("--swe-summary", type=Path)
    parser.add_argument("--call-policy", type=Path)
    parser.add_argument("--large-run-dir", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--condition", default="mixed_eval")
    parser.add_argument("--assume-route", choices=["L", "P", "none"], default="none")
    parser.add_argument("--min-strict-score", type=float, default=0.85)
    args = parser.parse_args()

    split_manifest = read_json(args.split_dir / "manifest.json")
    mixed_rows = read_json(args.split_dir / "mixed_rows.json")
    proxy_results = read_jsonl(args.proxy_easy_results)
    swe_sets = summary_sets(args.swe_summary)
    call_policy = read_json(args.call_policy) if args.call_policy else None
    large_usage = usage_by_instance(args.large_run_dir)
    rows = build_rows(
        mixed_rows=mixed_rows,
        proxy_results=proxy_results,
        swe_sets=swe_sets,
        call_policy=call_policy,
        large_usage_by_id=large_usage,
        assume_route=args.assume_route,
        min_strict_score=args.min_strict_score,
    )
    summary = summarize(
        rows,
        condition=args.condition,
        split_manifest=split_manifest,
        min_strict_score=args.min_strict_score,
    )
    args.out_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.out_dir / "summary.json", summary)
    write_json(args.out_dir / "rows.json", rows)
    write_csv(args.out_dir / "rows.csv", rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
