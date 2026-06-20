#!/usr/bin/env python3
"""Mix agent action, memory skill, and failed-informative Parquet data."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import pandas as pd


def _load(path: Path) -> list[dict]:
    return pd.read_parquet(path).to_dict("records")


def _maybe_json_loads(value):
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith(("{", "[")):
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                return value
    return value


def _sample(records: list[dict], count: int, rng: random.Random) -> list[dict]:
    if count <= 0 or not records:
        return []
    if count <= len(records):
        return rng.sample(records, count)
    return [rng.choice(records) for _ in range(count)]


def _json_safe(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return _json_safe(value.tolist())
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(item) for item in value]
    return value


def _parquet_safe(record: dict) -> dict:
    safe = dict(record)
    for key in ("prompt", "response", "extra_info", "reward_model"):
        if key in safe and not isinstance(safe[key], str):
            safe[key] = json.dumps(_json_safe(safe[key]), ensure_ascii=False)
    return safe


def _record_source(record: dict) -> str:
    return str(record.get("data_source", "") or "")


def _sample_skills(
    records: list[dict],
    count: int,
    rng: random.Random,
    *,
    locate_ratio: float,
    edit_ratio: float,
    test_ratio: float,
    submit_ratio: float,
) -> tuple[list[dict], dict[str, int], dict[str, int]]:
    if count <= 0 or not records:
        return [], {"locate": 0, "edit": 0, "test": 0, "submit": 0, "other": 0}, {}

    buckets = {
        "locate": [record for record in records if _record_source(record).endswith("_locate")],
        "edit": [record for record in records if _record_source(record).endswith("_edit")],
        "test": [record for record in records if _record_source(record).endswith("_test")],
        "submit": [record for record in records if _record_source(record).endswith("_submit")],
    }
    known = set().union(*(set(map(id, bucket)) for bucket in buckets.values()))
    buckets["other"] = [record for record in records if id(record) not in known]

    ratios = {"locate": locate_ratio, "edit": edit_ratio, "test": test_ratio, "submit": submit_ratio}
    if sum(ratios.values()) <= 0:
        sampled = _sample(records, count, rng)
        return sampled, {"locate": 0, "edit": 0, "test": 0, "submit": 0, "other": len(sampled)}, {
            k: len(v) for k, v in buckets.items()
        }

    total_ratio = sum(max(0.0, ratio) for ratio in ratios.values())
    counts = {name: int(count * max(0.0, ratio) / total_ratio) for name, ratio in ratios.items()}
    while sum(counts.values()) < count:
        name = max(ratios, key=lambda key: (max(0.0, ratios[key]) / total_ratio * count) - counts[key])
        counts[name] += 1

    sampled: list[dict] = []
    sampled_counts: dict[str, int] = {}
    for name in ("locate", "edit", "test", "submit"):
        picked = _sample(buckets[name], counts[name], rng)
        sampled.extend(picked)
        sampled_counts[name] = len(picked)

    missing = count - len(sampled)
    if missing > 0:
        fallback = [record for name, bucket in buckets.items() for record in bucket if name != "other"] or records
        picked = _sample(fallback, missing, rng)
        sampled.extend(picked)
        sampled_counts["fallback"] = len(picked)
    sampled_counts["other"] = 0
    return sampled, sampled_counts, {k: len(v) for k, v in buckets.items()}


def _is_failed_informative(record: dict) -> bool:
    extra = _maybe_json_loads(record.get("extra_info", {})) or {}
    if bool(extra.get("resolved", False)):
        return False
    response = _maybe_json_loads(record.get("response", {})) or {}
    action = None
    if isinstance(response, dict):
        actions = response.get("extra", {}).get("actions", [])
        action = actions[0] if actions else None
    return action is not None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-train", type=Path, required=True)
    parser.add_argument("--agent-val", type=Path, required=True)
    parser.add_argument("--skills-train", type=Path, required=True)
    parser.add_argument("--skills-val", type=Path, required=True)
    parser.add_argument("--recovery-train", type=Path, default=None)
    parser.add_argument("--recovery-val", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--agent-ratio", type=float, default=0.70)
    parser.add_argument("--skill-ratio", type=float, default=0.20)
    parser.add_argument("--failed-ratio", type=float, default=0.10)
    parser.add_argument("--recovery-ratio", type=float, default=0.0)
    parser.add_argument("--skill-locate-ratio", type=float, default=0.0)
    parser.add_argument("--skill-edit-ratio", type=float, default=0.0)
    parser.add_argument("--skill-test-ratio", type=float, default=0.0)
    parser.add_argument("--skill-submit-ratio", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    agent_train = _load(args.agent_train)
    agent_val = _load(args.agent_val)
    skills_train = _load(args.skills_train)
    skills_val = _load(args.skills_val)
    recovery_train = _load(args.recovery_train) if args.recovery_train else []
    recovery_val = _load(args.recovery_val) if args.recovery_val else []
    failed_train = [record for record in agent_train if _is_failed_informative(record)]
    failed_val = [record for record in agent_val if _is_failed_informative(record)]

    total = len(agent_train)
    agent_count = max(1, int(total * args.agent_ratio))
    skill_count = int(total * args.skill_ratio)
    failed_count = int(total * args.failed_ratio)
    recovery_count = int(total * args.recovery_ratio)
    sampled_skills, sampled_skill_counts, available_skill_counts = _sample_skills(
        skills_train,
        skill_count,
        rng,
        locate_ratio=args.skill_locate_ratio,
        edit_ratio=args.skill_edit_ratio,
        test_ratio=args.skill_test_ratio,
        submit_ratio=args.skill_submit_ratio,
    )
    train = [
        *_sample(agent_train, agent_count, rng),
        *sampled_skills,
        *_sample(recovery_train, recovery_count, rng),
        *_sample(failed_train, failed_count, rng),
    ]
    val = [*agent_val, *skills_val, *recovery_val, *failed_val]
    rng.shuffle(train)
    rng.shuffle(val)

    args.output.mkdir(parents=True, exist_ok=True)
    train_path = args.output / "train.parquet"
    val_path = args.output / "val.parquet"
    pd.DataFrame([_parquet_safe(record) for record in train]).to_parquet(train_path, index=False)
    pd.DataFrame([_parquet_safe(record) for record in (val or train[:1])]).to_parquet(val_path, index=False)

    stats = {
        "train_records": len(train),
        "val_records": len(val or train[:1]),
        "agent_sampled": agent_count,
        "skills_sampled": skill_count,
        "skills_sampled_by_type": sampled_skill_counts,
        "skills_available_by_type": available_skill_counts,
        "failed_sampled": failed_count,
        "failed_available": len(failed_train),
        "recovery_sampled": recovery_count,
        "recovery_available": len(recovery_train),
        "train_path": str(train_path),
        "val_path": str(val_path),
    }
    (args.output / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
