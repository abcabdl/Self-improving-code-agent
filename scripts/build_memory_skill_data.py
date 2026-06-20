#!/usr/bin/env python3
"""Build Hybrid-Gym-style locate/edit/test memory skill data from agent RL rollouts."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from minisweagent.run.benchmarks.memory_skills import (
    load_agent_rl_jsonl,
    records_to_skill_records,
    skill_record_to_verl_record,
)


def parquet_safe_record(record: dict) -> dict:
    """Store nested chat payloads as JSON so pyarrow never infers empty structs."""
    safe = dict(record)
    for key in ("prompt", "response"):
        if key in safe and not isinstance(safe[key], str):
            safe[key] = json.dumps(safe[key], ensure_ascii=False)
    return safe


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _write_parquet(path: Path, records: list[dict], *, val_ratio: float, seed: int) -> dict:
    import pandas as pd

    if not records:
        raise ValueError("No locate/edit/test skill records were extracted")
    path.mkdir(parents=True, exist_ok=True)
    records = list(records)
    random.Random(seed).shuffle(records)
    val_size = int(len(records) * val_ratio)
    if val_ratio > 0 and len(records) > 1:
        val_size = max(1, val_size)
    val_records = records[:val_size]
    train_records = records[val_size:]
    if not train_records and val_records:
        train_records, val_records = val_records, []

    train_records = [parquet_safe_record(record) for record in train_records]
    val_records = [parquet_safe_record(record) for record in val_records]
    train_path = path / "train.parquet"
    val_path = path / "val.parquet"
    pd.DataFrame(train_records).to_parquet(train_path, index=False)
    pd.DataFrame(val_records or train_records[:1]).to_parquet(val_path, index=False)

    by_skill: dict[str, int] = {}
    for record in records:
        skill = record.get("extra_info", {}).get("skill", "unknown")
        by_skill[skill] = by_skill.get(skill, 0) + 1
    stats = {
        "records": len(records),
        "train_records": len(train_records),
        "val_records": len(val_records or train_records[:1]),
        "by_skill": by_skill,
        "train_path": str(train_path),
        "val_path": str(val_path),
    }
    (path / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="agent_rl_rollouts.jsonl")
    parser.add_argument("--output", type=Path, required=True, help="Output JSONL path or Parquet directory")
    parser.add_argument("--format", choices=["jsonl", "parquet"], default="parquet")
    parser.add_argument("--val-ratio", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    raw_records = load_agent_rl_jsonl(args.input)
    skill_records = records_to_skill_records(raw_records)
    verl_records = [skill_record_to_verl_record(record) for record in skill_records]

    if args.format == "jsonl":
        _write_jsonl(args.output, verl_records)
        stats = {"output": str(args.output), "records": len(verl_records)}
    else:
        stats = _write_parquet(args.output, verl_records, val_ratio=args.val_ratio, seed=args.seed)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
