"""Summarize continual SWE-bench batch experiments.

The report compares an updated-memory run against optional no-memory and
frozen-memory controls for each batch. It also extracts simple cost statistics
from trajectory files so the experiment can report accuracy-cost tradeoffs, not
only solved counts.
"""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import json
import re
from pathlib import Path
from typing import Any


TEST_RE = re.compile(r"\b(pytest|tox|nosetests|npm test|yarn test|pnpm test|cargo test|go test|make test)\b")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def resolve_path(path: str | Path, base: Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else base / value


def summary_sets(path: Path | None) -> dict[str, set[str]]:
    if path is None or not path.exists():
        return {"resolved": set(), "unresolved": set(), "empty": set(), "error": set()}
    payload = load_json(path)
    return {
        "resolved": set(payload.get("resolved_ids", [])),
        "unresolved": set(payload.get("unresolved_ids", [])),
        "empty": set(payload.get("empty_patch_ids", [])),
        "error": set(payload.get("error_ids", [])),
    }


def _trajectory_path(run_dir: Path, instance_id: str) -> Path:
    return run_dir / instance_id / f"{instance_id}.traj.json"


def _commands(trajectory: dict[str, Any]) -> list[str]:
    commands: list[str] = []
    for message in trajectory.get("messages", []):
        for action in (message.get("extra") or {}).get("actions", []):
            command = str(action.get("command", "")).strip()
            if command:
                commands.append(command)
    return commands


def run_cost(run_dir: Path, instance_ids: set[str]) -> dict[str, float]:
    total_cost = 0.0
    api_calls = 0
    tool_calls = 0
    test_runs = 0
    trajectories = 0
    for instance_id in sorted(instance_ids):
        path = _trajectory_path(run_dir, instance_id)
        if not path.exists():
            continue
        trajectory = load_json(path)
        stats = ((trajectory.get("info") or {}).get("model_stats") or {})
        total_cost += float(stats.get("instance_cost", 0.0) or 0.0)
        api_calls += int(stats.get("api_calls", 0) or 0)
        commands = _commands(trajectory)
        tool_calls += len(commands)
        test_runs += sum(1 for command in commands if TEST_RE.search(command.lower()))
        trajectories += 1
    return {
        "total_cost": round(total_cost, 6),
        "api_calls": api_calls,
        "tool_calls": tool_calls,
        "test_runs": test_runs,
        "trajectories": trajectories,
        "avg_tool_calls": round(tool_calls / trajectories, 3) if trajectories else 0.0,
        "avg_test_runs": round(test_runs / trajectories, 3) if trajectories else 0.0,
    }


def prefixed_cost(prefix: str, run_dir: Path, instance_ids: set[str]) -> dict[str, float]:
    return {f"{prefix}_{key}": value for key, value in run_cost(run_dir, instance_ids).items()}


def transfer_counts(updated: set[str], control: set[str], universe: set[str]) -> dict[str, int]:
    return {
        "positive_transfer": len((updated - control) & universe),
        "negative_transfer": len((control - updated) & universe),
        "shared_success": len((updated & control) & universe),
        "shared_failure": len(universe - (updated | control)),
    }


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = load_json(path)
    if "batches" not in manifest or not isinstance(manifest["batches"], list):
        raise ValueError(f"Manifest must contain a batches list: {path}")
    return manifest


def summarize(manifest_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    base = manifest_path.parent
    manifest = load_manifest(manifest_path)
    rows: list[dict[str, Any]] = []
    aggregate = Counter()
    for batch in manifest["batches"]:
        instance_ids = set(batch.get("instance_ids", []))
        updated_summary = resolve_path(batch["updated_summary"], base)
        updated_run = resolve_path(batch["updated_run_dir"], base)
        updated = summary_sets(updated_summary)

        no_memory = summary_sets(resolve_path(batch["no_memory_summary"], base) if batch.get("no_memory_summary") else None)
        frozen = summary_sets(resolve_path(batch["frozen_summary"], base) if batch.get("frozen_summary") else None)
        updated_cost = run_cost(updated_run, instance_ids)

        row: dict[str, Any] = {
            "batch": batch.get("name", f"batch_{len(rows) + 1}"),
            "instances": len(instance_ids),
            "updated_solved": len(updated["resolved"] & instance_ids),
            "updated_empty": len(updated["empty"] & instance_ids),
            "updated_errors": len(updated["error"] & instance_ids),
            **{f"updated_{key}": value for key, value in updated_cost.items()},
        }
        if batch.get("no_memory_summary"):
            row["no_memory_solved"] = len(no_memory["resolved"] & instance_ids)
            row.update({f"vs_no_memory_{k}": v for k, v in transfer_counts(updated["resolved"], no_memory["resolved"], instance_ids).items()})
            if batch.get("no_memory_run_dir"):
                row.update(prefixed_cost("no_memory", resolve_path(batch["no_memory_run_dir"], base), instance_ids))
        if batch.get("frozen_summary"):
            row["frozen_solved"] = len(frozen["resolved"] & instance_ids)
            row.update({f"vs_frozen_{k}": v for k, v in transfer_counts(updated["resolved"], frozen["resolved"], instance_ids).items()})
            if batch.get("frozen_run_dir"):
                row.update(prefixed_cost("frozen", resolve_path(batch["frozen_run_dir"], base), instance_ids))
        rows.append(row)
        for key, value in row.items():
            if isinstance(value, (int, float)) and key != "batch" and "_avg_" not in key:
                aggregate[key] += value

    totals = dict(aggregate)
    for prefix in ("updated", "no_memory", "frozen"):
        trajectories = float(totals.get(f"{prefix}_trajectories", 0) or 0)
        if trajectories:
            totals[f"{prefix}_avg_tool_calls"] = round(float(totals.get(f"{prefix}_tool_calls", 0)) / trajectories, 3)
            totals[f"{prefix}_avg_test_runs"] = round(float(totals.get(f"{prefix}_test_runs", 0)) / trajectories, 3)
    totals["batches"] = len(rows)
    return rows, totals


def write_outputs(rows: list[dict[str, Any]], totals: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {"rows": rows, "totals": totals}
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    csv_path = output.with_suffix(".csv")
    fieldnames = sorted({key for row in rows for key in row})
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote JSON report: {output}")
    print(f"Wrote CSV report:  {csv_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("continual_report.json"))
    args = parser.parse_args()

    rows, totals = summarize(args.manifest)
    write_outputs(rows, totals, args.output)
    for row in rows:
        print(
            f"{row['batch']}: updated={row['updated_solved']}/{row['instances']} "
            f"vs no-memory={row.get('no_memory_solved', 'n/a')} "
            f"vs frozen={row.get('frozen_solved', 'n/a')} "
            f"cost=${row['updated_total_cost']}"
        )
    print(f"Totals: {totals}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
