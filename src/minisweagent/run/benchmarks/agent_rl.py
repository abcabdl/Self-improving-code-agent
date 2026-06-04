"""Utilities for memory-augmented agent RL rollout export.

The first training stage keeps the existing mini-SWE-agent harness intact and
turns saved trajectories into action-level records. Rewards intentionally stay
minimal: verifier outcome dominates, with tiny generic penalties for long or
invalid trajectories.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

MEMORY_BLOCK_RE = re.compile(r"<retrieved_repair_memories>.*?</retrieved_repair_memories>", re.DOTALL)


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def load_summary(path: str | Path) -> dict[str, set[str]]:
    payload = load_json(path)
    return {
        "resolved": set(payload.get("resolved_ids", [])),
        "unresolved": set(payload.get("unresolved_ids", [])),
        "empty": set(payload.get("empty_patch_ids", [])),
        "error": set(payload.get("error_ids", [])),
    }


def compute_agent_reward(
    *,
    resolved: bool,
    step_count: int,
    invalid_action_count: int,
    step_penalty_cap: float = 0.05,
    invalid_penalty_cap: float = 0.05,
    step_budget: int = 100,
    invalid_budget: int = 10,
) -> float:
    """Compute a deliberately simple episode reward for agent RL.

    The reward is outcome-first. Penalties are small, capped, and generic; they
    discourage pathological rollouts without hand-designing SWE heuristics.
    """
    outcome = 1.0 if resolved else 0.0
    step_penalty = step_penalty_cap * min(1.0, max(0, step_count) / max(1, step_budget))
    invalid_penalty = invalid_penalty_cap * min(1.0, max(0, invalid_action_count) / max(1, invalid_budget))
    return round(outcome - step_penalty - invalid_penalty, 6)


def load_memory_usage(path: str | Path | None) -> dict[str, list[dict[str, Any]]]:
    if not path:
        return {}
    usage_path = Path(path)
    if not usage_path.exists():
        return {}
    usage: dict[str, list[dict[str, Any]]] = {}
    for line in usage_path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        usage.setdefault(item.get("target_instance_id", ""), []).append(item)
    for items in usage.values():
        items.sort(key=lambda item: int(item.get("rank", 0) or 0))
    return usage


def extract_memory_block(messages: list[dict[str, Any]]) -> str:
    for message in messages:
        if message.get("role") != "user":
            continue
        content = str(message.get("content") or "")
        match = MEMORY_BLOCK_RE.search(content)
        if match:
            return match.group(0)
    return ""


def summarize_observations(messages: list[dict[str, Any]], *, max_chars: int = 2000) -> str:
    parts: list[str] = []
    for message in messages:
        role = message.get("role", "")
        content = message.get("content", "")
        if isinstance(content, list):
            content = json.dumps(content, ensure_ascii=False)
        parts.append(f"[{role}] {str(content)}")
    text = "\n".join(parts).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars // 2] + "\n...[truncated]...\n" + text[-max_chars // 2 :]


def _assistant_step_indices(messages: list[dict[str, Any]]) -> list[int]:
    return [idx for idx, message in enumerate(messages) if message.get("role") == "assistant"]


def _following_observations(messages: list[dict[str, Any]], assistant_idx: int) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for message in messages[assistant_idx + 1 :]:
        if message.get("role") in {"assistant", "exit"}:
            break
        observations.append(message)
    return observations


def trajectory_action_stats(messages: list[dict[str, Any]]) -> dict[str, int]:
    assistant_indices = _assistant_step_indices(messages)
    invalid = 0
    for idx in assistant_indices:
        actions = messages[idx].get("extra", {}).get("actions", [])
        if not actions:
            invalid += 1
    return {"step_count": len(assistant_indices), "invalid_action_count": invalid}


def trajectory_to_rl_records(
    *,
    trajectory: dict[str, Any],
    instance_id: str,
    repo: str = "",
    resolved: bool,
    memory_usage: list[dict[str, Any]] | None = None,
    run_id: str = "",
) -> list[dict[str, Any]]:
    messages = list(trajectory.get("messages", []))
    stats = trajectory_action_stats(messages)
    reward = compute_agent_reward(resolved=resolved, **stats)
    memory_usage = memory_usage or []
    memory_ids = [item.get("memory_instance_id", "") for item in memory_usage if item.get("memory_instance_id")]
    memory_block = extract_memory_block(messages)
    records: list[dict[str, Any]] = []
    assistant_indices = _assistant_step_indices(messages)

    for step_idx, message_idx in enumerate(assistant_indices, 1):
        assistant_message = messages[message_idx]
        actions = assistant_message.get("extra", {}).get("actions", [])
        records.append(
            {
                "schema_version": 1,
                "run_id": run_id,
                "instance_id": instance_id,
                "repo": repo,
                "memory_ids": memory_ids,
                "memory_block": memory_block,
                "messages_before_action": messages[:message_idx],
                "assistant_action": actions[0] if actions else None,
                "assistant_message": assistant_message,
                "observation_summary": summarize_observations(_following_observations(messages, message_idx)),
                "resolved": resolved,
                "step_index": step_idx,
                "step_count": stats["step_count"],
                "invalid_action_count": stats["invalid_action_count"],
                "reward": reward,
            }
        )
    return records


def find_trajectory(run_dir: str | Path, instance_id: str) -> Path | None:
    run_path = Path(run_dir)
    candidates = [
        run_path / instance_id / f"{instance_id}.traj.json",
        run_path / f"{instance_id}.traj.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    matches = list(run_path.rglob(f"{instance_id}.traj.json"))
    return matches[0] if matches else None


def export_run_records(
    *,
    run_dir: str | Path,
    summary_path: str | Path,
    output_path: str | Path,
    retrieval_log: str | Path | None = None,
    run_id: str = "",
    repo_by_instance: dict[str, str] | None = None,
) -> dict[str, int]:
    summary = load_summary(summary_path)
    instance_ids = sorted(summary["resolved"] | summary["unresolved"] | summary["empty"] | summary["error"])
    usage = load_memory_usage(retrieval_log)
    repo_by_instance = repo_by_instance or {}
    total_records = 0
    missing_trajectories = 0
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8", newline="\n") as f:
        for instance_id in instance_ids:
            traj_path = find_trajectory(run_dir, instance_id)
            if traj_path is None:
                missing_trajectories += 1
                continue
            trajectory = load_json(traj_path)
            records = trajectory_to_rl_records(
                trajectory=trajectory,
                instance_id=instance_id,
                repo=repo_by_instance.get(instance_id, ""),
                resolved=instance_id in summary["resolved"],
                memory_usage=usage.get(instance_id, []),
                run_id=run_id,
            )
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            total_records += len(records)
    return {
        "instances": len(instance_ids),
        "records": total_records,
        "missing_trajectories": missing_trajectories,
    }


def to_verl_record(record: dict[str, Any]) -> dict[str, Any]:
    """Convert an exported agent-RL step into a generic verl/GRPO JSONL row."""
    return {
        "data_source": "memory_augmented_mini_swe_agent",
        "prompt": record.get("messages_before_action", []),
        "response": record.get("assistant_message", {}),
        "reward_model": {"style": "rule", "ground_truth": float(record.get("reward", 0.0))},
        "extra_info": {
            "instance_id": record.get("instance_id", ""),
            "repo": record.get("repo", ""),
            "run_id": record.get("run_id", ""),
            "resolved": bool(record.get("resolved", False)),
            "step_index": record.get("step_index", 0),
            "step_count": record.get("step_count", 0),
            "invalid_action_count": record.get("invalid_action_count", 0),
            "memory_ids": record.get("memory_ids", []),
        },
    }
