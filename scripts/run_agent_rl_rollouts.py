#!/usr/bin/env python3
"""Collect grouped memory-augmented SWE-bench rollouts for GRPO-style training."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def run_cmd(cmd: list[str], *, cwd: Path, env: dict[str, str], dry_run: bool) -> None:
    print("\n$ " + " ".join(f'"{part}"' if " " in part else part for part in cmd), flush=True)
    if not dry_run:
        subprocess.run(cmd, cwd=cwd, env=env, check=True)


def find_summary(report_dir: Path, run_id: str, expected: Path) -> Path:
    if expected.exists():
        return expected

    candidates = sorted(
        report_dir.glob(f"*.{run_id}.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        candidates = sorted(
            report_dir.glob(f"*{run_id}*.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
    if not candidates:
        raise FileNotFoundError(f"Could not find evaluation summary for run_id={run_id!r} in {report_dir}")
    return candidates[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("runs/agent-rl-rollouts"))
    parser.add_argument("--initial-memory", type=Path, default=Path("runs/memory/self_improve_memory.json"))
    parser.add_argument("--subset", default="lite")
    parser.add_argument("--split", default="dev")
    parser.add_argument("--filter", default="", help="Regex filter for selected instances")
    parser.add_argument("--slice", default="", help="Slice passed through to swebench.py")
    parser.add_argument("--model", default="openai/local-7b")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000/v1")
    parser.add_argument("--config", default="swebench.yaml")
    parser.add_argument("--rollouts-per-instance", type=int, default=4)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--memory-k", type=int, default=3)
    parser.add_argument("--memory-strategy", default="hybrid", choices=["score", "hybrid"])
    parser.add_argument("--memory-stage-aware", action="store_true", default=True)
    parser.add_argument("--eval-timeout", type=int, default=1800)
    parser.add_argument("--eval-max-workers", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo_root = Path.cwd()
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": 1,
        "rollouts_per_instance": args.rollouts_per_instance,
        "memory_policy": "forced",
        "runs": [],
    }
    merged_rollouts = args.out_dir / "agent_rl_rollouts.jsonl"
    if merged_rollouts.exists() and not args.dry_run:
        merged_rollouts.unlink()

    for rollout_idx in range(args.rollouts_per_instance):
        rollout_name = f"rollout_{rollout_idx + 1:02d}"
        run_dir = args.out_dir / rollout_name / "run"
        run_id = f"agent-rl-{rollout_name}"
        swe_cmd = [
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
            str(args.initial_memory),
            "--memory-k",
            str(args.memory_k),
            "--memory-strategy",
            args.memory_strategy,
            "--memory-gate-mode",
            "off",
            *(["--memory-stage-aware"] if args.memory_stage_aware else []),
            *(["--filter", args.filter] if args.filter else []),
            *(["--slice", args.slice] if args.slice else []),
            "--redo-existing",
        ]
        run_cmd(swe_cmd, cwd=repo_root, env=env, dry_run=args.dry_run)

        expected_summary = args.out_dir / rollout_name / f"{run_id}.json"
        eval_cmd = [
            sys.executable,
            "scripts/evaluate_swebench_run.py",
            str(run_dir),
            "--dataset-name",
            "princeton-nlp/SWE-Bench_Lite" if args.subset == "lite" else args.subset,
            "--split",
            args.split,
            "--run-id",
            run_id,
            "--timeout",
            str(args.eval_timeout),
            "--max-workers",
            str(args.eval_max_workers),
            "--report-dir",
            str(expected_summary.parent),
        ]
        run_cmd(eval_cmd, cwd=repo_root, env=env, dry_run=args.dry_run)
        summary = expected_summary if args.dry_run else find_summary(expected_summary.parent, run_id, expected_summary)

        export_path = args.out_dir / rollout_name / "agent_rl_rollouts.jsonl"
        export_cmd = [
            sys.executable,
            "scripts/export_agent_rl_rollouts.py",
            "--run-dir",
            str(run_dir),
            "--summary",
            str(summary),
            "--retrieval-log",
            str(run_dir / "retrieved_memories.jsonl"),
            "--output",
            str(export_path),
            "--run-id",
            run_id,
        ]
        run_cmd(export_cmd, cwd=repo_root, env=env, dry_run=args.dry_run)

        if not args.dry_run and export_path.exists():
            with merged_rollouts.open("a", encoding="utf-8", newline="\n") as dst:
                dst.write(export_path.read_text(encoding="utf-8-sig"))
        manifest["runs"].append({"run_id": run_id, "run_dir": str(run_dir), "summary": str(summary), "export": str(export_path)})

    manifest["merged_rollouts"] = str(merged_rollouts)
    manifest_path = args.out_dir / "manifest.json"
    if args.dry_run:
        print(json.dumps(manifest, indent=2))
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")
        print(f"Wrote {manifest_path}")
        print(f"Wrote {merged_rollouts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
