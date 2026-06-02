"""Run a continual SWE-bench experiment over unseen task batches.

Each batch can run three conditions:
1. no memory baseline,
2. frozen initial memory baseline,
3. updated memory, which is carried forward and updated after each batch.

The script writes a manifest consumed by ``scripts/report_continual_swe.py`` to
measure positive transfer, negative transfer, and cost.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any

from datasets import load_dataset


DATASET_MAPPING = {
    "full": "princeton-nlp/SWE-Bench",
    "lite": "princeton-nlp/SWE-Bench_Lite",
    "verified": "princeton-nlp/SWE-Bench_Verified",
}


def run_cmd(cmd: list[str], *, cwd: Path, env: dict[str, str], dry_run: bool = False) -> None:
    print("\n$ " + " ".join(f'"{part}"' if " " in part else part for part in cmd), flush=True)
    if dry_run:
        return
    subprocess.run(cmd, cwd=cwd, env=env, check=True)


def find_summary(repo_root: Path, out_dir: Path, run_id: str) -> Path | None:
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


def dataset_name(subset: str) -> str:
    return DATASET_MAPPING.get(subset, subset)


def load_instance_ids(subset: str, split: str, *, filter_prefix: str = "", limit: int = 0) -> list[str]:
    ids = sorted(str(row["instance_id"]) for row in load_dataset(dataset_name(subset), split=split))
    if filter_prefix:
        prefixes = tuple(part.strip() for part in filter_prefix.split(",") if part.strip())
        ids = [instance_id for instance_id in ids if instance_id.startswith(prefixes)]
    return ids[:limit] if limit else ids


def make_batches(ids: list[str], batch_size: int) -> list[list[str]]:
    if batch_size <= 0:
        raise ValueError("--batch-size must be positive")
    return [ids[i : i + batch_size] for i in range(0, len(ids), batch_size)]


def regex_for_batch(ids: list[str]) -> str:
    return "^(?:" + "|".join(re.escape(instance_id) for instance_id in ids) + ")$"


def run_swebench(
    *,
    repo_root: Path,
    env: dict[str, str],
    run_dir: Path,
    run_id: str,
    subset: str,
    split: str,
    instance_ids: list[str],
    model: str,
    api_base: str,
    config: str,
    workers: int,
    memory_file: Path | None,
    memory_k: int,
    memory_strategy: str,
    memory_same_repo_k: int,
    memory_global_k: int,
    memory_global_min_similarity: float,
    memory_low_confidence_q: float,
    memory_low_confidence_similarity: float,
    strategy_memory_file: Path | None,
    workflow_k: int,
    reflection_k: int,
    strategy_min_score: float,
    no_tool_bandit: bool,
    redo_existing: bool,
    dry_run: bool,
) -> None:
    cmd = [
        sys.executable,
        "-m",
        "minisweagent.run.benchmarks.swebench",
        "--subset",
        subset,
        "--split",
        split,
        "--filter",
        regex_for_batch(instance_ids),
        "-o",
        str(run_dir),
        "-w",
        str(workers),
        "-m",
        model,
        "-c",
        config,
        "-c",
        f"model.model_kwargs.api_base={api_base}",
        "-c",
        "model.model_kwargs.drop_params=true",
        "-c",
        "model.cost_tracking=ignore_errors",
        *(
            [
                "--memory-file",
                str(memory_file),
                "--memory-k",
                str(memory_k),
                "--memory-strategy",
                memory_strategy,
                "--memory-same-repo-k",
                str(memory_same_repo_k),
                "--memory-global-k",
                str(memory_global_k),
                "--memory-global-min-similarity",
                str(memory_global_min_similarity),
                "--memory-low-confidence-q",
                str(memory_low_confidence_q),
                "--memory-low-confidence-similarity",
                str(memory_low_confidence_similarity),
            ]
            if memory_file is not None and memory_k > 0
            else []
        ),
        *(
            [
                "--strategy-memory-file",
                str(strategy_memory_file),
                "--workflow-k",
                str(workflow_k),
                "--reflection-k",
                str(reflection_k),
                "--strategy-min-score",
                str(strategy_min_score),
                *(["--no-tool-bandit"] if no_tool_bandit else []),
            ]
            if strategy_memory_file is not None
            else []
        ),
        *(["--redo-existing"] if redo_existing else []),
    ]
    run_cmd(cmd, cwd=repo_root, env=env, dry_run=dry_run)


def evaluate_run(
    *,
    repo_root: Path,
    env: dict[str, str],
    run_dir: Path,
    out_dir: Path,
    run_id: str,
    dataset_name_value: str,
    split: str,
    eval_timeout: int,
    eval_max_workers: int,
    dry_run: bool,
) -> Path:
    run_cmd(
        [
            sys.executable,
            "scripts/evaluate_swebench_run.py",
            str(run_dir),
            "--dataset-name",
            dataset_name_value,
            "--split",
            split,
            "--run-id",
            run_id,
            "--timeout",
            str(eval_timeout),
            "--max-workers",
            str(eval_max_workers),
            "--report-dir",
            str(out_dir),
        ],
        cwd=repo_root,
        env=env,
        dry_run=dry_run,
    )
    if dry_run:
        return out_dir / f"openai__gpt-5-mini.{run_id}.json"
    found = find_summary(repo_root, out_dir, run_id)
    if found is None:
        raise FileNotFoundError(f"Expected evaluation summary for run_id={run_id} in {out_dir}")
    return found


def update_memory(
    *,
    repo_root: Path,
    env: dict[str, str],
    current_memory: Path,
    summary: Path,
    run_dir: Path,
    output: Path,
    alpha: float,
    dry_run: bool,
) -> None:
    run_cmd(
        [
            sys.executable,
            "scripts/update_memory_q_values.py",
            "--memory",
            str(current_memory),
            "--summary",
            str(summary),
            "--retrieval-log",
            str(run_dir / "retrieved_memories.jsonl"),
            "--output",
            str(output),
            "--alpha",
            str(alpha),
        ],
        cwd=repo_root,
        env=env,
        dry_run=dry_run,
    )


def update_strategy(
    *,
    repo_root: Path,
    env: dict[str, str],
    current_strategy: Path,
    summary: Path,
    run_dir: Path,
    output: Path,
    alpha: float,
    dry_run: bool,
) -> None:
    run_cmd(
        [
            sys.executable,
            "scripts/update_strategy_memory.py",
            "--strategy",
            str(current_strategy),
            "--summary",
            str(summary),
            "--run-dir",
            str(run_dir),
            "--usage-log",
            str(run_dir / "strategy_usage.jsonl"),
            "--output",
            str(output),
            "--alpha",
            str(alpha),
        ],
        cwd=repo_root,
        env=env,
        dry_run=dry_run,
    )


def rel(path: Path, base: Path) -> str:
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path.resolve())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("runs/continual-swe-gpt5mini"))
    parser.add_argument("--initial-memory", type=Path, default=Path("runs/memory/self_improve_memory.json"))
    parser.add_argument("--initial-strategy-memory", type=Path, default=None)
    parser.add_argument("--run-prefix", default="swebench-lite-dev-continual")
    parser.add_argument("--subset", default="lite")
    parser.add_argument("--split", default="dev")
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--filter-prefix", default="", help="Comma-separated instance-id prefixes, e.g. marshmallow-code__,pvlib__")
    parser.add_argument("--model", default="openai/gpt-5-mini")
    parser.add_argument("--api-base", default="https://az.gptplus5.com/v1")
    parser.add_argument("--config", default="swebench.yaml")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--memory-k", type=int, default=3)
    parser.add_argument("--memory-strategy", default="hybrid", choices=["score", "hybrid"])
    parser.add_argument("--memory-same-repo-k", type=int, default=2)
    parser.add_argument("--memory-global-k", type=int, default=0)
    parser.add_argument("--memory-global-min-similarity", type=float, default=0.18)
    parser.add_argument("--memory-low-confidence-q", type=float, default=0.5)
    parser.add_argument("--memory-low-confidence-similarity", type=float, default=0.28)
    parser.add_argument("--workflow-k", type=int, default=1)
    parser.add_argument("--reflection-k", type=int, default=2)
    parser.add_argument("--strategy-min-score", type=float, default=0.3)
    parser.add_argument("--no-tool-bandit", action="store_true")
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--eval-timeout", type=int, default=1800)
    parser.add_argument("--eval-max-workers", type=int, default=1)
    parser.add_argument("--skip-no-memory", action="store_true")
    parser.add_argument("--skip-frozen", action="store_true")
    parser.add_argument("--redo-existing", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo_root = Path.cwd()
    out_dir = args.out_dir if args.out_dir.is_absolute() else repo_root / args.out_dir
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    if not env.get("OPENAI_API_KEY") and not args.dry_run:
        raise RuntimeError("OPENAI_API_KEY is not set in this PowerShell session.")
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    instance_ids = load_instance_ids(args.subset, args.split, filter_prefix=args.filter_prefix, limit=args.limit)
    batches = make_batches(instance_ids, args.batch_size)
    if not batches:
        raise RuntimeError("No instances selected for continual experiment.")

    current_memory = args.initial_memory
    current_strategy = args.initial_strategy_memory
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "subset": args.subset,
        "dataset_name": dataset_name(args.subset),
        "split": args.split,
        "initial_memory": rel(args.initial_memory, out_dir),
        "initial_strategy_memory": rel(args.initial_strategy_memory, out_dir) if args.initial_strategy_memory else "",
        "batch_size": args.batch_size,
        "batches": [],
    }

    for idx, batch_ids in enumerate(batches, 1):
        name = f"batch_{idx:02d}"
        batch_dir = out_dir / name
        if not args.dry_run:
            batch_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n=== {name}: {len(batch_ids)} unseen instances ===")

        batch_record: dict[str, Any] = {"name": name, "instance_ids": batch_ids}

        if not args.skip_no_memory:
            run_dir = batch_dir / "no_memory_run"
            run_id = f"{args.run_prefix}-{name}-no-memory"
            run_swebench(
                repo_root=repo_root,
                env=env,
                run_dir=run_dir,
                run_id=run_id,
                subset=args.subset,
                split=args.split,
                instance_ids=batch_ids,
                model=args.model,
                api_base=args.api_base,
                config=args.config,
                workers=args.workers,
                memory_file=None,
                memory_k=0,
                memory_strategy=args.memory_strategy,
                memory_same_repo_k=args.memory_same_repo_k,
                memory_global_k=args.memory_global_k,
                memory_global_min_similarity=args.memory_global_min_similarity,
                memory_low_confidence_q=args.memory_low_confidence_q,
                memory_low_confidence_similarity=args.memory_low_confidence_similarity,
                strategy_memory_file=None,
                workflow_k=args.workflow_k,
                reflection_k=args.reflection_k,
                strategy_min_score=args.strategy_min_score,
                no_tool_bandit=args.no_tool_bandit,
                redo_existing=args.redo_existing,
                dry_run=args.dry_run,
            )
            summary = evaluate_run(
                repo_root=repo_root,
                env=env,
                run_dir=run_dir,
                out_dir=batch_dir,
                run_id=run_id,
                dataset_name_value=dataset_name(args.subset),
                split=args.split,
                eval_timeout=args.eval_timeout,
                eval_max_workers=args.eval_max_workers,
                dry_run=args.dry_run,
            )
            batch_record["no_memory_run_dir"] = rel(run_dir, out_dir)
            batch_record["no_memory_summary"] = rel(summary, out_dir)

        if not args.skip_frozen:
            run_dir = batch_dir / "frozen_memory_run"
            run_id = f"{args.run_prefix}-{name}-frozen"
            run_swebench(
                repo_root=repo_root,
                env=env,
                run_dir=run_dir,
                run_id=run_id,
                subset=args.subset,
                split=args.split,
                instance_ids=batch_ids,
                model=args.model,
                api_base=args.api_base,
                config=args.config,
                workers=args.workers,
                memory_file=args.initial_memory,
                memory_k=args.memory_k,
                memory_strategy=args.memory_strategy,
                memory_same_repo_k=args.memory_same_repo_k,
                memory_global_k=args.memory_global_k,
                memory_global_min_similarity=args.memory_global_min_similarity,
                memory_low_confidence_q=args.memory_low_confidence_q,
                memory_low_confidence_similarity=args.memory_low_confidence_similarity,
                strategy_memory_file=args.initial_strategy_memory,
                workflow_k=args.workflow_k,
                reflection_k=args.reflection_k,
                strategy_min_score=args.strategy_min_score,
                no_tool_bandit=args.no_tool_bandit,
                redo_existing=args.redo_existing,
                dry_run=args.dry_run,
            )
            summary = evaluate_run(
                repo_root=repo_root,
                env=env,
                run_dir=run_dir,
                out_dir=batch_dir,
                run_id=run_id,
                dataset_name_value=dataset_name(args.subset),
                split=args.split,
                eval_timeout=args.eval_timeout,
                eval_max_workers=args.eval_max_workers,
                dry_run=args.dry_run,
            )
            batch_record["frozen_run_dir"] = rel(run_dir, out_dir)
            batch_record["frozen_summary"] = rel(summary, out_dir)

        run_dir = batch_dir / "updated_memory_run"
        run_id = f"{args.run_prefix}-{name}-updated"
        run_swebench(
            repo_root=repo_root,
            env=env,
            run_dir=run_dir,
            run_id=run_id,
            subset=args.subset,
            split=args.split,
            instance_ids=batch_ids,
            model=args.model,
            api_base=args.api_base,
            config=args.config,
            workers=args.workers,
            memory_file=current_memory,
            memory_k=args.memory_k,
            memory_strategy=args.memory_strategy,
            memory_same_repo_k=args.memory_same_repo_k,
            memory_global_k=args.memory_global_k,
            memory_global_min_similarity=args.memory_global_min_similarity,
            memory_low_confidence_q=args.memory_low_confidence_q,
            memory_low_confidence_similarity=args.memory_low_confidence_similarity,
            strategy_memory_file=current_strategy,
            workflow_k=args.workflow_k,
            reflection_k=args.reflection_k,
            strategy_min_score=args.strategy_min_score,
            no_tool_bandit=args.no_tool_bandit,
            redo_existing=args.redo_existing,
            dry_run=args.dry_run,
        )
        summary = evaluate_run(
            repo_root=repo_root,
            env=env,
            run_dir=run_dir,
            out_dir=batch_dir,
            run_id=run_id,
            dataset_name_value=dataset_name(args.subset),
            split=args.split,
            eval_timeout=args.eval_timeout,
            eval_max_workers=args.eval_max_workers,
            dry_run=args.dry_run,
        )
        next_memory = batch_dir / "memory_after_batch.json"
        update_memory(
            repo_root=repo_root,
            env=env,
            current_memory=current_memory,
            summary=summary,
            run_dir=run_dir,
            output=next_memory,
            alpha=args.alpha,
            dry_run=args.dry_run,
        )
        batch_record["updated_run_dir"] = rel(run_dir, out_dir)
        batch_record["updated_summary"] = rel(summary, out_dir)
        batch_record["memory_before"] = rel(current_memory, out_dir)
        batch_record["memory_after"] = rel(next_memory, out_dir)
        current_memory = next_memory

        if current_strategy is not None:
            next_strategy = batch_dir / "strategy_after_batch.json"
            update_strategy(
                repo_root=repo_root,
                env=env,
                current_strategy=current_strategy,
                summary=summary,
                run_dir=run_dir,
                output=next_strategy,
                alpha=args.alpha,
                dry_run=args.dry_run,
            )
            batch_record["strategy_before"] = rel(current_strategy, out_dir)
            batch_record["strategy_after"] = rel(next_strategy, out_dir)
            current_strategy = next_strategy

        manifest["batches"].append(batch_record)
        manifest["final_memory"] = rel(current_memory, out_dir)
        manifest["final_strategy_memory"] = rel(current_strategy, out_dir) if current_strategy else ""
        manifest_path = out_dir / "manifest.json"
        if not args.dry_run:
            manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")

    manifest_path = out_dir / "manifest.json"
    if args.dry_run:
        print("\nDry run manifest preview:")
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
    else:
        print(f"\nWrote manifest: {manifest_path}")
        run_cmd(
            [sys.executable, "scripts/report_continual_swe.py", "--manifest", str(manifest_path), "--output", str(out_dir / "continual_report.json")],
            cwd=repo_root,
            env=env,
            dry_run=False,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
