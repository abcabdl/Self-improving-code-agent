#!/usr/bin/env python3
"""Mix agent action, memory skill, and failed-informative Parquet data."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import pandas as pd


def _load(path: Path) -> list[dict]:
    return pd.read_parquet(path).to_dict("records")


def _sample(records: list[dict], count: int, rng: random.Random) -> list[dict]:
    if count <= 0 or not records:
        return []
    if count <= len(records):
        return rng.sample(records, count)
    return [rng.choice(records) for _ in range(count)]


def _is_failed_informative(record: dict) -> bool:
    extra = record.get("extra_info", {}) or {}
    if bool(extra.get("resolved", False)):
        return False
    response = record.get("response", {}) or {}
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
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--agent-ratio", type=float, default=0.70)
    parser.add_argument("--skill-ratio", type=float, default=0.20)
    parser.add_argument("--failed-ratio", type=float, default=0.10)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    agent_train = _load(args.agent_train)
    agent_val = _load(args.agent_val)
    skills_train = _load(args.skills_train)
    skills_val = _load(args.skills_val)
    failed_train = [record for record in agent_train if _is_failed_informative(record)]
    failed_val = [record for record in agent_val if _is_failed_informative(record)]

    total = len(agent_train)
    agent_count = max(1, int(total * args.agent_ratio))
    skill_count = int(total * args.skill_ratio)
    failed_count = int(total * args.failed_ratio)
    train = [
        *_sample(agent_train, agent_count, rng),
        *_sample(skills_train, skill_count, rng),
        *_sample(failed_train, failed_count, rng),
    ]
    val = [*agent_val, *skills_val, *failed_val]
    rng.shuffle(train)
    rng.shuffle(val)

    args.output.mkdir(parents=True, exist_ok=True)
    train_path = args.output / "train.parquet"
    val_path = args.output / "val.parquet"
    pd.DataFrame(train).to_parquet(train_path, index=False)
    pd.DataFrame(val or train[:1]).to_parquet(val_path, index=False)

    stats = {
        "train_records": len(train),
        "val_records": len(val or train[:1]),
        "agent_sampled": agent_count,
        "skills_sampled": skill_count,
        "failed_sampled": failed_count,
        "failed_available": len(failed_train),
        "train_path": str(train_path),
        "val_path": str(val_path),
    }
    (args.output / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
