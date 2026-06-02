"""Update external strategy Q-values from SWE-bench feedback and recorded strategy usage."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any

from minisweagent.run.benchmarks.strategy_memory import ACTION_CATEGORIES, load_strategy_memory, trajectory_stats


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def update_q(old_q: float, reward: float, alpha: float) -> float:
    return clamp01((1.0 - alpha) * old_q + alpha * reward)


def trajectory_path(run_dir: Path, instance_id: str) -> Path:
    return run_dir / instance_id / f"{instance_id}.traj.json"


def update_item_q(items: list[dict[str, Any]], rewards: dict[str, list[float]], *, id_key: str, alpha: float) -> int:
    updated = 0
    by_id = {str(item.get(id_key, "")): item for item in items}
    for item_id, values in rewards.items():
        item = by_id.get(item_id)
        if item is None or not values:
            continue
        reward = sum(values) / len(values)
        item["q_value"] = round(update_q(float(item.get("q_value", 0.5)), reward, alpha), 4)
        item["last_reward"] = reward
        item["q_update_count"] = int(item.get("q_update_count", 0)) + len(values)
        updated += 1
    return updated


def update_bandit_bucket(bucket: dict[str, dict[str, Any]], categories: list[str], reward: float, alpha: float) -> None:
    for category in sorted(set(categories)):
        state = bucket.setdefault(category, {"q_value": 0.5, "update_count": 0})
        state["q_value"] = round(update_q(float(state.get("q_value", 0.5)), reward, alpha), 4)
        state["update_count"] = int(state.get("update_count", 0)) + 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strategy", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--usage-log", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--alpha", type=float, default=0.5)
    args = parser.parse_args()

    strategy = load_strategy_memory(args.strategy)
    summary = load_json(args.summary)
    resolved = set(summary.get("resolved_ids", []))
    unresolved = set(summary.get("unresolved_ids", []))
    rewards = {instance_id: 1.0 for instance_id in resolved}
    rewards.update({instance_id: 0.0 for instance_id in unresolved})

    workflow_rewards: dict[str, list[float]] = defaultdict(list)
    reflection_rewards: dict[str, list[float]] = defaultdict(list)
    usage_rows = [
        json.loads(line)
        for line in args.usage_log.read_text(encoding="utf-8-sig").splitlines()
        if line.strip()
    ]
    for row in usage_rows:
        reward = rewards.get(str(row.get("target_instance_id", "")))
        if reward is None:
            continue
        for workflow_id in row.get("workflow_ids", []):
            workflow_rewards[str(workflow_id)].append(reward)
        for reflection_id in row.get("reflection_ids", []):
            # A reflection is useful when the task succeeds after receiving its warning.
            reflection_rewards[str(reflection_id)].append(reward)

    updated_workflows = update_item_q(strategy["workflows"], workflow_rewards, id_key="workflow_id", alpha=args.alpha)
    updated_reflections = update_item_q(strategy["reflections"], reflection_rewards, id_key="reflection_id", alpha=args.alpha)

    for instance_id, reward in rewards.items():
        path = trajectory_path(args.run_dir, instance_id)
        if not path.exists():
            continue
        trajectory = load_json(path)
        stats = trajectory_stats(trajectory)
        update_bandit_bucket(strategy["tool_bandit"]["global"], stats["action_categories"], reward, args.alpha)
        repo = next(
            (str(row.get("target_repo", "")) for row in usage_rows if row.get("target_instance_id") == instance_id),
            "",
        )
        repo_bucket = strategy["tool_bandit"]["repos"].setdefault(repo, {})
        for category in ACTION_CATEGORIES:
            repo_bucket.setdefault(category, {"q_value": 0.5, "update_count": 0})
        update_bandit_bucket(repo_bucket, stats["action_categories"], reward, args.alpha)

    strategy["last_update"] = {
        "summary": str(args.summary),
        "run_dir": str(args.run_dir),
        "usage_log": str(args.usage_log),
        "updated_workflows": updated_workflows,
        "updated_reflections": updated_reflections,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(strategy, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(
        f"Updated strategy memory: {updated_workflows} workflows, "
        f"{updated_reflections} reflections, tool bandit -> {args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
