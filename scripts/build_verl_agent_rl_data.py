#!/usr/bin/env python3
"""Convert exported agent-RL rollouts into verl-compatible JSONL or Parquet data."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from minisweagent.run.benchmarks.agent_rl import to_verl_record


def _load_records(path: Path, *, min_reward: float | None, include_failed: bool) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8-sig") as src:
        for line in src:
            if not line.strip():
                continue
            record = json.loads(line)
            reward = float(record.get("reward", 0.0))
            if min_reward is not None and reward < min_reward:
                continue
            if not include_failed and not bool(record.get("resolved", False)):
                continue
            records.append(to_verl_record(record))
    return records


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as dst:
        for record in records:
            dst.write(json.dumps(record, ensure_ascii=False) + "\n")


def _write_parquet_dir(path: Path, records: list[dict], *, val_ratio: float, seed: int) -> dict:
    import pandas as pd

    if not 0 <= val_ratio < 1:
        raise ValueError("--val-ratio must be in [0, 1)")
    if not records:
        raise ValueError("No records left after filtering")

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

    train_path = path / "train.parquet"
    val_path = path / "val.parquet"
    pd.DataFrame(train_records).to_parquet(train_path, index=False)
    pd.DataFrame(val_records or train_records[:1]).to_parquet(val_path, index=False)

    rewards = [float(record.get("reward_model", {}).get("ground_truth", 0.0)) for record in records]
    resolved = [bool(record.get("extra_info", {}).get("resolved", False)) for record in records]
    stats = {
        "records": len(records),
        "train_records": len(train_records),
        "val_records": len(val_records or train_records[:1]),
        "resolved_records": sum(resolved),
        "unresolved_records": len(resolved) - sum(resolved),
        "mean_reward": sum(rewards) / len(rewards) if rewards else 0.0,
        "train_path": str(train_path),
        "val_path": str(val_path),
    }
    (path / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="agent_rl_rollouts.jsonl")
    parser.add_argument("--output", type=Path, required=True, help="Output JSONL path or Parquet directory")
    parser.add_argument("--output-format", choices=["jsonl", "parquet"], default="jsonl")
    parser.add_argument("--min-reward", type=float, default=None, help="Optional filter for quick SFT/RL warm-start subsets")
    parser.add_argument("--val-ratio", type=float, default=0.05, help="Validation split ratio for Parquet output")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--include-failed", action="store_true", default=True, help="Keep unresolved records for RWR training")
    parser.add_argument("--only-success", dest="include_failed", action="store_false", help="Drop unresolved records for SFT warmup")
    args = parser.parse_args()

    records = _load_records(args.input, min_reward=args.min_reward, include_failed=args.include_failed)
    if args.output_format == "jsonl":
        _write_jsonl(args.output, records)
        stats = {"output": str(args.output), "records": len(records)}
    else:
        stats = _write_parquet_dir(args.output, records, val_ratio=args.val_ratio, seed=args.seed)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
