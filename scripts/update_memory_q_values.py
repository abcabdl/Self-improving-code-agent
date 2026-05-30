"""Update episodic-memory Q values from SWE-bench evaluation feedback."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def update_q(old_q: float, reward: float, alpha: float) -> float:
    return clamp01((1.0 - alpha) * old_q + alpha * reward)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--memory", type=Path, required=True, help="Input memory JSON")
    parser.add_argument("--summary", type=Path, required=True, help="Evaluation summary JSON")
    parser.add_argument("--output", type=Path, required=True, help="Updated memory JSON")
    parser.add_argument(
        "--retrieval-log",
        type=Path,
        default=None,
        help="JSONL file recording which memories were retrieved for each evaluated instance",
    )
    parser.add_argument("--alpha", type=float, default=0.5, help="Q-learning step size")
    parser.add_argument("--success-reward", type=float, default=1.0)
    parser.add_argument("--failure-reward", type=float, default=0.0)
    args = parser.parse_args()

    payload = load_json(args.memory)
    items = payload.get("items", payload if isinstance(payload, list) else [])
    if not isinstance(items, list):
        raise ValueError(f"Memory file must contain a list or an object with an items list: {args.memory}")

    summary = load_json(args.summary)
    resolved = set(summary.get("resolved_ids", []))
    unresolved = set(summary.get("unresolved_ids", []))
    rewards = {instance_id: args.success_reward for instance_id in resolved}
    rewards.update({instance_id: args.failure_reward for instance_id in unresolved})

    updated = 0
    memory_rewards: dict[str, list[float]] = defaultdict(list)
    if args.retrieval_log:
        for line in args.retrieval_log.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            target_id = row.get("target_instance_id", "")
            memory_id = row.get("memory_instance_id", "")
            if target_id in rewards and memory_id:
                memory_rewards[memory_id].append(rewards[target_id])
    else:
        for instance_id, reward in rewards.items():
            memory_rewards[instance_id].append(reward)

    for item in items:
        instance_id = item.get("instance_id", "")
        if not instance_id or instance_id not in memory_rewards:
            continue
        reward = sum(memory_rewards[instance_id]) / len(memory_rewards[instance_id])
        old_q = float(item.get("q_value", float(item.get("utility", 1.0) or 0.0) / 2.0) or 0.0)
        item["q_value"] = round(update_q(old_q, reward, args.alpha), 4)
        item["last_reward"] = reward
        item["q_update_alpha"] = args.alpha
        item["q_update_count"] = len(memory_rewards[instance_id])
        updated += 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, dict):
        payload["items"] = items
        out = payload
    else:
        out = items
    args.output.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"Updated {updated} memory Q values -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
