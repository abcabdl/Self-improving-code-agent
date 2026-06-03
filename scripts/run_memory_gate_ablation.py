"""Run forced-vs-gated memory continual SWE-bench ablations."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys


def run_cmd(cmd: list[str], *, cwd: Path, env: dict[str, str], dry_run: bool) -> None:
    print("\n$ " + " ".join(f'"{part}"' if " " in part else part for part in cmd), flush=True)
    if not dry_run:
        subprocess.run(cmd, cwd=cwd, env=env, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-root", type=Path, default=Path("runs/memory-gate-ablation"))
    parser.add_argument("--initial-memory", type=Path, default=Path("runs/memory/self_improve_memory.json"))
    parser.add_argument("--initial-strategy-memory", type=Path, default=None)
    parser.add_argument("--policies", default="forced,gated", help="Comma-separated policies: forced,gated")
    parser.add_argument("--subset", default="lite")
    parser.add_argument("--split", default="dev")
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--model", default="openai/gpt-5-mini")
    parser.add_argument("--api-base", default="https://az.gptplus5.com/v1")
    parser.add_argument("--config", default="swebench.yaml")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--memory-k", type=int, default=2)
    parser.add_argument("--memory-strategy", default="hybrid", choices=["score", "hybrid"])
    parser.add_argument("--memory-same-repo-k", type=int, default=2)
    parser.add_argument("--memory-global-k", type=int, default=1)
    parser.add_argument("--memory-gate-min-similarity", type=float, default=0.18)
    parser.add_argument("--memory-gate-min-q", type=float, default=0.25)
    parser.add_argument("--memory-stage-aware", action="store_true")
    parser.add_argument("--workflow-k", type=int, default=1)
    parser.add_argument("--reflection-k", type=int, default=1)
    parser.add_argument("--strategy-min-score", type=float, default=0.45)
    parser.add_argument("--no-tool-bandit", dest="no_tool_bandit", action="store_true", default=True)
    parser.add_argument("--tool-bandit", dest="no_tool_bandit", action="store_false")
    parser.add_argument("--redo-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo_root = Path.cwd()
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")

    for policy in [p.strip() for p in args.policies.split(",") if p.strip()]:
        if policy not in {"forced", "gated"}:
            raise ValueError(f"Unknown policy: {policy}")
        out_dir = args.out_root / policy
        cmd = [
            sys.executable,
            "scripts/run_continual_swe_batches.py",
            "--out-dir",
            str(out_dir),
            "--initial-memory",
            str(args.initial_memory),
            "--run-prefix",
            f"swebench-{args.subset}-{args.split}-memory-{policy}",
            "--subset",
            args.subset,
            "--split",
            args.split,
            "--batch-size",
            str(args.batch_size),
            "--limit",
            str(args.limit),
            "--model",
            args.model,
            "--api-base",
            args.api_base,
            "--config",
            args.config,
            "--workers",
            str(args.workers),
            "--memory-k",
            str(args.memory_k),
            "--memory-strategy",
            args.memory_strategy,
            "--memory-same-repo-k",
            str(args.memory_same_repo_k),
            "--memory-global-k",
            str(args.memory_global_k),
            "--memory-policy",
            policy,
            "--memory-gate-min-similarity",
            str(args.memory_gate_min_similarity),
            "--memory-gate-min-q",
            str(args.memory_gate_min_q),
            "--workflow-k",
            str(args.workflow_k),
            "--reflection-k",
            str(args.reflection_k),
            "--strategy-min-score",
            str(args.strategy_min_score),
            *(["--initial-strategy-memory", str(args.initial_strategy_memory)] if args.initial_strategy_memory else []),
            *(["--memory-stage-aware"] if args.memory_stage_aware else []),
            *(["--no-tool-bandit"] if args.no_tool_bandit else []),
            *(["--redo-existing"] if args.redo_existing else []),
            *(["--dry-run"] if args.dry_run else []),
        ]
        run_cmd(cmd, cwd=repo_root, env=env, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
