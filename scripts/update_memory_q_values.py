"""Update episodic-memory Q values from SWE-bench evaluation feedback."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def update_q(old_q: float, reward: float, alpha: float) -> float:
    return clamp01((1.0 - alpha) * old_q + alpha * reward)


def infer_round_label(summary_path: Path) -> str:
    for part in reversed(summary_path.parts):
        if re.fullmatch(r"r\d+", part):
            return part
    match = re.search(r"r(\d+)", summary_path.stem)
    if match:
        return f"r{match.group(1)}"
    return ""


def selected_memory_instance_ids(policy_row: dict[str, Any]) -> list[str]:
    top_memories = list(policy_row.get("top_memories", []) or [])
    top_by_index = {f"mem_{index}": top for index, top in enumerate(top_memories, 1)}
    top_by_id = {str(top.get("instance_id", "")): top for top in top_memories}

    selected: list[str] = []
    packet = policy_row.get("packet", {}) or {}
    for raw_id in packet.get("selected_memory_ids", []) or []:
        memory_key = str(raw_id)
        memory = top_by_index.get(memory_key) or top_by_id.get(memory_key)
        if memory:
            instance_id = str(memory.get("instance_id", ""))
            if instance_id:
                selected.append(instance_id)
    return selected


def top_memory_instance_ids(policy_row: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for memory in policy_row.get("top_memories", []) or []:
        instance_id = str(memory.get("instance_id", ""))
        if instance_id:
            ids.append(instance_id)
    return ids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--memory", type=Path, required=True, help="Input memory JSON")
    parser.add_argument("--summary", type=Path, required=True, help="Evaluation summary JSON")
    parser.add_argument("--output", type=Path, required=True, help="Updated memory JSON")
    parser.add_argument(
        "--policy",
        type=Path,
        default=None,
        help=(
            "Optional MemGate call_policy_summary.json. When provided, positive credit is "
            "assigned only to memories selected into packets for actual P-route calls; "
            "route=L empty patches strongly penalize top routed memories."
        ),
    )
    parser.add_argument(
        "--retrieval-log",
        type=Path,
        default=None,
        help="JSONL file recording which memories were retrieved for each evaluated instance",
    )
    parser.add_argument("--alpha", type=float, default=0.5, help="Q-learning step size")
    parser.add_argument("--success-reward", type=float, default=1.0)
    parser.add_argument("--failure-reward", type=float, default=0.0)
    parser.add_argument("--local-empty-reward", type=float, default=0.0)
    parser.add_argument("--round-label", default="", help="Optional label for q_update_history entries.")
    parser.add_argument(
        "--local-empty-alpha-multiplier",
        type=float,
        default=1.5,
        help="Extra penalty multiplier for route=L empty-patch memories when --policy is provided.",
    )
    args = parser.parse_args()

    payload = load_json(args.memory)
    items = payload.get("items", payload if isinstance(payload, list) else [])
    if not isinstance(items, list):
        raise ValueError(f"Memory file must contain a list or an object with an items list: {args.memory}")

    summary = load_json(args.summary)
    resolved = set(summary.get("resolved_ids", []))
    unresolved = set(summary.get("unresolved_ids", []))
    empty = set(summary.get("empty_patch_ids", []))
    rewards = {instance_id: args.success_reward for instance_id in resolved}
    rewards.update({instance_id: args.failure_reward for instance_id in unresolved})
    rewards.update({instance_id: args.failure_reward for instance_id in empty})

    updated = 0
    memory_feedback: dict[str, list[tuple[float, float, str]]] = defaultdict(list)
    unattributed_events: list[dict[str, Any]] = []
    if args.policy:
        policy = load_json(args.policy)
        policy_rows = {str(row.get("instance_id", "")): row for row in policy.get("call_log", [])}
        for target_id, reward in rewards.items():
            row = policy_rows.get(target_id, {})
            route = str(row.get("route", ""))
            large_called = bool(row.get("large_model_called", False))
            is_empty = target_id in empty

            if route == "L" and is_empty:
                penalty_alpha = clamp01(args.alpha * args.local_empty_alpha_multiplier)
                for memory_id in top_memory_instance_ids(row):
                    memory_feedback[memory_id].append((args.local_empty_reward, penalty_alpha, "route_L_empty"))
                continue

            if route == "P" and large_called:
                selected_ids = selected_memory_instance_ids(row)
                if reward >= args.success_reward:
                    for memory_id in selected_ids:
                        memory_feedback[memory_id].append((reward, args.alpha, "packet_selected_success"))
                else:
                    if not selected_ids:
                        unattributed_events.append(
                            {
                                "target_instance_id": target_id,
                                "route": route,
                                "source": "p_route_failure_unattributed",
                                "top_memory_instance_ids": top_memory_instance_ids(row),
                                "reward": reward,
                            }
                        )
                        continue
                    for memory_id in selected_ids:
                        memory_feedback[memory_id].append((reward, args.alpha, "p_route_failure"))
    elif args.retrieval_log:
        for line in args.retrieval_log.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            target_id = row.get("target_instance_id", "")
            memory_id = row.get("memory_instance_id", "")
            if target_id in rewards and memory_id:
                memory_feedback[memory_id].append((rewards[target_id], args.alpha, "retrieved"))
    else:
        for instance_id, reward in rewards.items():
            memory_feedback[instance_id].append((reward, args.alpha, "self"))

    round_label = args.round_label or infer_round_label(args.summary)
    for item in items:
        instance_id = item.get("instance_id", "")
        if not instance_id or instance_id not in memory_feedback:
            continue
        feedback = memory_feedback[instance_id]
        reward = sum(row[0] for row in feedback) / len(feedback)
        alpha = sum(row[1] for row in feedback) / len(feedback)
        old_q = float(item.get("q_value", float(item.get("utility", 1.0) or 0.0) / 2.0) or 0.0)
        item["q_value"] = round(update_q(old_q, reward, alpha), 4)
        item["last_reward"] = reward
        item["q_update_alpha"] = alpha
        item["q_update_count"] = len(feedback)
        item["q_update_sources"] = sorted({row[2] for row in feedback})
        history = list(item.get("q_update_history", []) or [])
        history.append(
            {
                "round": round_label,
                "old_q": round(old_q, 4),
                "new_q": item["q_value"],
                "reward": reward,
                "alpha": alpha,
                "count": len(feedback),
                "sources": item["q_update_sources"],
            }
        )
        item["q_update_history"] = history
        updated += 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, dict):
        payload["items"] = items
        if unattributed_events:
            metadata = dict(payload.get("q_update_metadata", {}) or {})
            events = list(metadata.get("unattributed_events", []) or [])
            events.extend(unattributed_events)
            metadata["unattributed_events"] = events
            payload["q_update_metadata"] = metadata
        out = payload
    else:
        out = items
    args.output.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"Updated {updated} memory Q values -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
