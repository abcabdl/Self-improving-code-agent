#!/usr/bin/env python3
"""Export memory-augmented mini-SWE-agent trajectories for action-level RL."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from minisweagent.run.benchmarks.agent_rl import export_run_records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True, help="SWE-bench run directory containing trajectories")
    parser.add_argument("--summary", type=Path, required=True, help="SWE-bench evaluation summary JSON")
    parser.add_argument("--output", type=Path, default=Path("agent_rl_rollouts.jsonl"))
    parser.add_argument("--retrieval-log", type=Path, default=None, help="Optional retrieved_memories.jsonl")
    parser.add_argument("--run-id", default="")
    args = parser.parse_args()

    stats = export_run_records(
        run_dir=args.run_dir,
        summary_path=args.summary,
        output_path=args.output,
        retrieval_log=args.retrieval_log,
        run_id=args.run_id,
    )
    print(json.dumps({"output": str(args.output), **stats}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
