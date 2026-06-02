"""Build external workflow, reflection, and tool-bandit memory from evaluated trajectories."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from datasets import load_dataset

from minisweagent.run.benchmarks.strategy_memory import (
    ACTION_CATEGORIES,
    empty_strategy_memory,
    load_strategy_memory,
    merge_strategy_items,
    reflections_from_trajectory,
    trajectory_stats,
    workflow_from_trajectory,
)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def update_q(old_q: float, reward: float, alpha: float) -> float:
    return clamp01((1.0 - alpha) * old_q + alpha * reward)


def trajectory_path(run_dir: Path, instance_id: str) -> Path:
    return run_dir / instance_id / f"{instance_id}.traj.json"


def update_bandit_bucket(bucket: dict[str, dict[str, Any]], categories: list[str], reward: float, alpha: float) -> None:
    for category in sorted(set(categories)):
        state = bucket.setdefault(category, {"q_value": 0.5, "update_count": 0})
        state["q_value"] = round(update_q(float(state.get("q_value", 0.5)), reward, alpha), 4)
        state["update_count"] = int(state.get("update_count", 0)) + 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--dataset", default="princeton-nlp/SWE-Bench_Lite")
    parser.add_argument("--split", default="dev")
    parser.add_argument("--base-strategy", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--alpha", type=float, default=0.5)
    args = parser.parse_args()

    strategy = load_strategy_memory(args.base_strategy) if args.base_strategy else empty_strategy_memory()
    summary = load_json(args.summary)
    resolved = set(summary.get("resolved_ids", []))
    unresolved = set(summary.get("unresolved_ids", []))
    empty_patches = set(summary.get("empty_patch_ids", []))
    dataset = load_dataset(args.dataset, split=args.split)
    rows = {row["instance_id"]: row for row in dataset}

    workflows = []
    reflections = []
    processed = 0
    for instance_id in sorted(resolved | unresolved | empty_patches):
        path = trajectory_path(args.run_dir, instance_id)
        row = rows.get(instance_id)
        if not path.exists() or row is None:
            continue
        trajectory = load_json(path)
        repo = str(row.get("repo", ""))
        statement = str(row.get("problem_statement", ""))
        reward = 1.0 if instance_id in resolved else 0.0
        stats = trajectory_stats(trajectory)
        update_bandit_bucket(strategy["tool_bandit"]["global"], stats["action_categories"], reward, args.alpha)
        repo_bucket = strategy["tool_bandit"]["repos"].setdefault(repo, {})
        for category in ACTION_CATEGORIES:
            repo_bucket.setdefault(category, {"q_value": 0.5, "update_count": 0})
        update_bandit_bucket(repo_bucket, stats["action_categories"], reward, args.alpha)
        if instance_id in resolved:
            workflow = workflow_from_trajectory(instance_id, repo, statement, trajectory)
            if workflow:
                workflows.append(workflow)
        else:
            reflections.extend(
                reflections_from_trajectory(
                    instance_id,
                    repo,
                    statement,
                    trajectory,
                    empty_patch=instance_id in empty_patches,
                )
            )
        processed += 1

    added_workflows = merge_strategy_items(strategy["workflows"], workflows, id_key="workflow_id")
    added_reflections = merge_strategy_items(strategy["reflections"], reflections, id_key="reflection_id")
    strategy["last_build"] = {
        "run_dir": str(args.run_dir),
        "summary": str(args.summary),
        "processed_instances": processed,
        "added_workflows": added_workflows,
        "added_reflections": added_reflections,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(strategy, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(
        f"Built strategy memory from {processed} trajectories: "
        f"+{added_workflows} workflows, +{added_reflections} reflections -> {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
