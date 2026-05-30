"""Run multi-round MemRL-style SWE-bench self-improvement.

Each round runs mini-swe-agent with the current memory, evaluates the run, then
writes an updated memory file for the next round. The input memory is never
modified in place.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str], *, cwd: Path, env: dict[str, str], dry_run: bool = False) -> None:
    print("\n$ " + " ".join(f'"{part}"' if " " in part else part for part in cmd), flush=True)
    if dry_run:
        return
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def find_summary(repo_root: Path, out_dir: Path, run_id: str) -> Path | None:
    """Find the SWE-bench summary even if the harness wrote it in cwd."""
    candidates = list(out_dir.glob(f"*.{run_id}.json")) + list(repo_root.glob(f"*.{run_id}.json"))
    if not candidates:
        return None
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    source = candidates[0]
    destination = out_dir / source.name
    if source.resolve() != destination.resolve():
        out_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--out-dir", type=Path, default=Path("runs/memrl-rounds-gpt5mini"))
    parser.add_argument("--initial-memory", type=Path, default=Path("runs/memory/self_improve_memory.json"))
    parser.add_argument("--run-prefix", default="swebench-lite-dev-memrl")
    parser.add_argument("--model", default="openai/gpt-5-mini")
    parser.add_argument("--api-base", default="https://az.gptplus5.com/v1")
    parser.add_argument("--subset", default="lite")
    parser.add_argument("--split", default="dev")
    parser.add_argument("--config", default="swebench.yaml")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--memory-k", type=int, default=3)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--eval-timeout", type=int, default=1800)
    parser.add_argument("--eval-max-workers", type=int, default=1)
    parser.add_argument("--redo-existing", action="store_true")
    parser.add_argument("--resume", action="store_true", default=True, help="Skip rounds whose updated memory already exists")
    parser.add_argument("--no-resume", action="store_false", dest="resume", help="Do not skip completed rounds")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo_root = Path.cwd()
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")

    if not env.get("OPENAI_API_KEY") and not args.dry_run:
        raise RuntimeError("OPENAI_API_KEY is not set in this PowerShell session.")

    out_dir = args.out_dir
    if not out_dir.is_absolute():
        out_dir = repo_root / out_dir
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    current_memory = args.initial_memory
    for round_idx in range(1, args.rounds + 1):
        run_dir = out_dir / f"round_{round_idx}_run"
        run_id = f"{args.run_prefix}-r{round_idx}-gpt5mini-eval"
        summary_path = out_dir / f"openai__gpt-5-mini.{run_id}.json"
        next_memory = out_dir / f"memory_r{round_idx}.json"
        if args.resume and next_memory.exists():
            print(f"\nRound {round_idx} already has updated memory: {next_memory}")
            current_memory = next_memory
            continue

        run_cmd(
            [
                sys.executable,
                "-m",
                "minisweagent.run.benchmarks.swebench",
                "--subset",
                args.subset,
                "--split",
                args.split,
                "-o",
                str(run_dir),
                "-w",
                str(args.workers),
                "-m",
                args.model,
                "-c",
                args.config,
                "-c",
                f"model.model_kwargs.api_base={args.api_base}",
                "-c",
                "model.model_kwargs.drop_params=true",
                "-c",
                "model.cost_tracking=ignore_errors",
                "--memory-file",
                str(current_memory),
                "--memory-k",
                str(args.memory_k),
                *(["--redo-existing"] if args.redo_existing else []),
            ],
            cwd=repo_root,
            env=env,
            dry_run=args.dry_run,
        )

        run_cmd(
            [
                sys.executable,
                "scripts/evaluate_swebench_run.py",
                str(run_dir),
                "--run-id",
                run_id,
                "--timeout",
                str(args.eval_timeout),
                "--max-workers",
                str(args.eval_max_workers),
                "--report-dir",
                str(out_dir),
            ],
            cwd=repo_root,
            env=env,
            dry_run=args.dry_run,
        )

        if not args.dry_run:
            found_summary = find_summary(repo_root, out_dir, run_id)
            if found_summary is None:
                raise FileNotFoundError(f"Expected evaluation summary not found: {summary_path}")
            summary_path = found_summary

        run_cmd(
            [
                sys.executable,
                "scripts/update_memory_q_values.py",
                "--memory",
                str(current_memory),
                "--summary",
                str(summary_path),
                "--retrieval-log",
                str(run_dir / "retrieved_memories.jsonl"),
                "--output",
                str(next_memory),
                "--alpha",
                str(args.alpha),
            ],
            cwd=repo_root,
            env=env,
            dry_run=args.dry_run,
        )
        current_memory = next_memory

    print(f"\nDone. Final memory: {current_memory}")
    print(f"Output directory: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
