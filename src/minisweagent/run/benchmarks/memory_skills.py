"""Hybrid-Gym-style auxiliary skill extraction for memory-agent training."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from minisweagent.run.benchmarks.agent_rl import compute_agent_reward, extract_memory_block, summarize_observations, to_verl_record

LOCATE_RE = re.compile(r"\b(rg|grep|find|ls|sed|cat|head|tail|python\s+-c|python3\s+-c)\b", re.IGNORECASE)
EDIT_RE = re.compile(r"\b(apply_patch|git\s+apply|python\s+- <<|python3\s+- <<|perl\s+-pi|sed\s+-i)\b|>\s*\w|diff --git", re.IGNORECASE)
TEST_RE = re.compile(r"\b(pytest|tox|unittest|nosetests|python\s+-m\s+pytest|python3\s+-m\s+pytest|npm\s+test|cargo\s+test)\b", re.IGNORECASE)


def classify_command(command: str) -> str | None:
    """Classify a shell command into locate/edit/test skill buckets."""
    command = command.strip()
    if not command:
        return None
    if TEST_RE.search(command):
        return "test"
    if EDIT_RE.search(command):
        return "edit"
    if LOCATE_RE.search(command):
        return "locate"
    return None


def _assistant_step_indices(messages: list[dict[str, Any]]) -> list[int]:
    return [idx for idx, message in enumerate(messages) if message.get("role") == "assistant"]


def _following_observations(messages: list[dict[str, Any]], assistant_idx: int) -> list[dict[str, Any]]:
    observations = []
    for message in messages[assistant_idx + 1 :]:
        if message.get("role") in {"assistant", "exit"}:
            break
        observations.append(message)
    return observations


def _skill_reward(*, resolved: bool, skill: str, command: str, observations: list[dict[str, Any]]) -> float:
    reward = 1.0 if resolved else 0.25
    text = "\n".join(str(item.get("content", "")) for item in observations).lower()
    command_l = command.lower()
    if skill == "locate" and (".py" in text or "def " in text or "class " in text):
        reward += 0.1
    elif skill == "edit" and ("apply_patch" in command_l or "diff --git" in command_l or "write_text" in command_l):
        reward += 0.1
    elif skill == "test" and ("<returncode>0</returncode>" in text or "passed" in text):
        reward += 0.1
    return round(min(1.0, reward), 6)


def trajectory_to_memory_skill_records(
    *,
    trajectory: dict[str, Any],
    instance_id: str,
    repo: str = "",
    resolved: bool,
    run_id: str = "",
) -> list[dict[str, Any]]:
    """Extract locate/edit/test records from a saved mini-SWE-agent trajectory."""
    messages = list(trajectory.get("messages", []))
    memory_block = extract_memory_block(messages)
    records = []
    for step_idx, message_idx in enumerate(_assistant_step_indices(messages), 1):
        assistant_message = messages[message_idx]
        actions = assistant_message.get("extra", {}).get("actions", [])
        if not actions:
            continue
        action = actions[0]
        command = str(action.get("command", "")) if isinstance(action, dict) else str(action)
        skill = classify_command(command)
        if skill is None:
            continue
        observations = _following_observations(messages, message_idx)
        reward = _skill_reward(resolved=resolved, skill=skill, command=command, observations=observations)
        records.append(
            {
                "schema_version": 1,
                "record_type": "memory_skill",
                "skill": skill,
                "run_id": run_id,
                "instance_id": instance_id,
                "repo": repo,
                "memory_block": memory_block,
                "messages_before_action": messages[:message_idx],
                "assistant_action": action,
                "assistant_message": assistant_message,
                "observation_summary": summarize_observations(observations),
                "resolved": resolved,
                "step_index": step_idx,
                "step_count": len(_assistant_step_indices(messages)),
                "invalid_action_count": 0,
                "reward": reward,
            }
        )
    return records


def skill_record_to_verl_record(record: dict[str, Any]) -> dict[str, Any]:
    verl_record = to_verl_record(record)
    verl_record["data_source"] = f"memory_agent_skill_{record.get('skill', 'unknown')}"
    verl_record["extra_info"]["record_type"] = "memory_skill"
    verl_record["extra_info"]["skill"] = record.get("skill", "")
    verl_record["extra_info"]["observation_summary"] = record.get("observation_summary", "")
    return verl_record


def load_agent_rl_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records = []
    with Path(path).open("r", encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records


def records_to_skill_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert existing action-level records into skill records without reloading trajectories."""
    skill_records = []
    for record in records:
        action = record.get("assistant_action")
        command = str(action.get("command", "")) if isinstance(action, dict) else str(action or "")
        skill = classify_command(command)
        if skill is None:
            continue
        skill_record = dict(record)
        skill_record["record_type"] = "memory_skill"
        skill_record["skill"] = skill
        skill_record["reward"] = _skill_reward(
            resolved=bool(record.get("resolved", False)),
            skill=skill,
            command=command,
            observations=[{"role": "tool", "content": record.get("observation_summary", "")}],
        )
        skill_records.append(skill_record)
    return skill_records
