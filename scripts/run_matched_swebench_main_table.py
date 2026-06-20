#!/usr/bin/env python3
"""Run a matched SWE-Bench slice for the paper main table.

The experiment compares:

1. no memory with the large model,
2. simple/non-trained memory with the same large model,
3. a selective condition that first lets the small/local model self-handle all
   rows, delegates controller-failed rows to the large model, merges the
   predictions, and evaluates the merged run with the official harness.

The launcher is intentionally resumable: it skips completed prediction/eval
artifacts unless --redo-existing is set, and it writes a manifest plus a compact
main_table_summary.json/CSV for TeX-side reporting.
"""

from __future__ import annotations

import argparse
import base64
import csv
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
    "_test": "klieret/swe-bench-dummy-test-dataset",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def dataset_name(subset: str) -> str:
    return DATASET_MAPPING.get(subset, subset)


def select_instance_ids(subset: str, split: str, limit: int, filter_regex: str = "") -> list[str]:
    rows = list(load_dataset(dataset_name(subset), split=split))
    ids = [str(row["instance_id"]) for row in rows]
    if filter_regex:
        pattern = re.compile(filter_regex)
        ids = [instance_id for instance_id in ids if pattern.search(instance_id)]
    return ids[:limit] if limit else ids


def regex_for_ids(ids: list[str]) -> str:
    return "^(?:" + "|".join(re.escape(instance_id) for instance_id in ids) + ")$"


def run_cmd(cmd: list[str], *, cwd: Path, env: dict[str, str], log_path: Path, dry_run: bool = False) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    printable = " ".join(f'"{part}"' if " " in part else part for part in cmd)
    with log_path.open("a", encoding="utf-8", newline="\n") as log:
        log.write(f"\n$ {printable}\n")
        log.flush()
        print(f"$ {printable}", flush=True)
        if dry_run:
            return
        result = subprocess.run(cmd, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {result.returncode}: {printable}. See {log_path}")


def run_swebench(
    *,
    repo_root: Path,
    env: dict[str, str],
    run_dir: Path,
    ids: list[str],
    subset: str,
    split: str,
    model: str,
    api_base: str,
    api_key_value: str | None,
    config: str,
    workers: int,
    step_limit: int,
    memory_file: Path | None = None,
    memory_gate_mode: str = "off",
    memory_strategy: str = "hybrid",
    memory_k: int = 3,
    memory_stage_aware: bool = True,
    strategy_memory_file: Path | None = None,
    workflow_k: int = 1,
    reflection_k: int = 2,
    redo_existing: bool = False,
    dry_run: bool = False,
) -> None:
    if not redo_existing and (run_dir / "preds.json").exists():
        preds = read_json(run_dir / "preds.json")
        if isinstance(preds, dict) and all(instance_id in preds for instance_id in ids):
            print(f"Skipping completed predictions: {run_dir}")
            return

    cmd = [
        sys.executable,
        "-m",
        "minisweagent.run.benchmarks.swebench",
        "--subset",
        subset,
        "--split",
        split,
        "--filter",
        regex_for_ids(ids),
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
        "-c",
        f"agent.step_limit={step_limit}",
    ]
    if api_key_value is not None:
        cmd.extend(["-c", f"model.model_kwargs.api_key={api_key_value}"])
    if memory_file is not None:
        cmd.extend(
            [
                "--memory-file",
                str(memory_file),
                "--memory-k",
                str(memory_k),
                "--memory-strategy",
                memory_strategy,
                "--memory-gate-mode",
                memory_gate_mode,
            ]
        )
        if memory_stage_aware:
            cmd.append("--memory-stage-aware")
    if strategy_memory_file is not None:
        cmd.extend(
            [
                "--strategy-memory-file",
                str(strategy_memory_file),
                "--workflow-k",
                str(workflow_k),
                "--reflection-k",
                str(reflection_k),
            ]
        )
    if redo_existing:
        cmd.append("--redo-existing")
    run_cmd(cmd, cwd=repo_root, env=env, log_path=run_dir / "launcher.log", dry_run=dry_run)


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


def evaluate(
    *,
    repo_root: Path,
    env: dict[str, str],
    run_dir: Path,
    out_dir: Path,
    run_id: str,
    subset: str,
    split: str,
    max_workers: int,
    timeout: int,
    redo_existing: bool,
    dry_run: bool,
) -> Path:
    existing = find_summary(repo_root, out_dir, run_id)
    if existing is not None and not redo_existing:
        print(f"Skipping completed eval: {existing}")
        return existing
    run_cmd(
        [
            sys.executable,
            "scripts/evaluate_swebench_run.py",
            str(run_dir),
            "--dataset-name",
            dataset_name(subset),
            "--split",
            split,
            "--run-id",
            run_id,
            "--timeout",
            str(timeout),
            "--max-workers",
            str(max_workers),
            "--report-dir",
            str(out_dir),
        ],
        cwd=repo_root,
        env=env,
        log_path=out_dir / f"{run_id}.eval.log",
        dry_run=dry_run,
    )
    if dry_run:
        return out_dir / f"dry-run.{run_id}.json"
    found = find_summary(repo_root, out_dir, run_id)
    if found is None:
        raise FileNotFoundError(f"Expected evaluation summary for run_id={run_id} in {out_dir}")
    return found


def trajectory_path(run_dir: Path, instance_id: str) -> Path:
    return run_dir / instance_id / f"{instance_id}.traj.json"


def patch_is_empty(patch: str) -> bool:
    text = str(patch or "").strip()
    if not text:
        return True
    return "diff --git" not in text and "--- " not in text and "+++ " not in text


def choose_delegate_ids(self_run_dir: Path, ids: list[str], *, max_delegate: int) -> list[str]:
    preds_path = self_run_dir / "preds.json"
    preds = read_json(preds_path) if preds_path.exists() else {}
    delegates: list[str] = []
    for instance_id in ids:
        pred = preds.get(instance_id, {}) if isinstance(preds, dict) else {}
        patch = str(pred.get("model_patch", ""))
        should_delegate = patch_is_empty(patch)
        traj = trajectory_path(self_run_dir, instance_id)
        if traj.exists():
            try:
                info = (read_json(traj).get("info") or {})
                status = str(info.get("exit_status", ""))
                if status and status not in {"submitted", "completed"}:
                    should_delegate = True
            except Exception:
                should_delegate = True
        if should_delegate:
            delegates.append(instance_id)
    if max_delegate > 0:
        delegates = delegates[:max_delegate]
    return delegates


def merge_selective_preds(
    *,
    ids: list[str],
    self_run_dir: Path,
    delegate_run_dir: Path,
    delegate_ids: list[str],
    output_dir: Path,
) -> Path:
    self_preds = read_json(self_run_dir / "preds.json")
    delegate_preds = read_json(delegate_run_dir / "preds.json") if delegate_ids else {}
    delegate_set = set(delegate_ids)
    merged: dict[str, Any] = {}
    call_log: list[dict[str, Any]] = []
    for instance_id in ids:
        if instance_id in delegate_set:
            if instance_id not in delegate_preds:
                raise ValueError(f"Missing delegate prediction for {instance_id}")
            row = dict(delegate_preds[instance_id])
            row["model_name_or_path"] = str(row.get("model_name_or_path", "")) + "+selective_P_call"
            merged[instance_id] = row
            call_log.append({"instance_id": instance_id, "route": "P", "large_model_called": True})
        else:
            if instance_id not in self_preds:
                raise ValueError(f"Missing self prediction for {instance_id}")
            row = dict(self_preds[instance_id])
            row["model_name_or_path"] = str(row.get("model_name_or_path", "")) + "+selective_L_local"
            merged[instance_id] = row
            call_log.append({"instance_id": instance_id, "route": "L", "large_model_called": False})
    output_dir.mkdir(parents=True, exist_ok=True)
    preds_path = output_dir / "preds.json"
    write_json(preds_path, merged)
    write_json(
        output_dir / "call_policy_summary.json",
        {
            "artifact_type": "matched_swebench_selective_call_policy",
            "rows": len(ids),
            "large_model_calls": len(delegate_ids),
            "no_call_rows": len(ids) - len(delegate_ids),
            "call_log": call_log,
            "ready_for_harness_eval": True,
        },
    )
    return preds_path


def summary_sets(path: Path | None) -> dict[str, set[str]]:
    if path is None or not path.exists():
        return {"resolved": set(), "unresolved": set(), "empty": set(), "error": set()}
    payload = read_json(path)
    return {
        "resolved": set(payload.get("resolved_ids", [])),
        "unresolved": set(payload.get("unresolved_ids", [])),
        "empty": set(payload.get("empty_patch_ids", [])),
        "error": set(payload.get("error_ids", [])),
    }


def usage_for_run(run_dir: Path, ids: list[str]) -> dict[str, Any]:
    cost = 0.0
    api_calls = 0
    prompt_tokens = 0
    completion_tokens = 0
    total_tokens = 0
    trajectories = 0
    for instance_id in ids:
        path = trajectory_path(run_dir, instance_id)
        if not path.exists():
            continue
        trajectories += 1
        trajectory = read_json(path)
        stats = ((trajectory.get("info") or {}).get("model_stats") or {})
        cost += float(stats.get("instance_cost", 0.0) or 0.0)
        api_calls += int(stats.get("api_calls", 0) or 0)
        for message in trajectory.get("messages", []):
            response = ((message.get("extra") or {}).get("response") or {})
            usage = response.get("usage") or {}
            prompt_tokens += int(usage.get("prompt_tokens", 0) or 0)
            completion_tokens += int(usage.get("completion_tokens", 0) or 0)
            total_tokens += int(usage.get("total_tokens", 0) or 0)
    return {
        "trajectories": trajectories,
        "api_calls": api_calls,
        "cost": round(cost, 6),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def condition_row(
    *,
    name: str,
    ids: list[str],
    summary_path: Path | None,
    large_usage_run_dir: Path | None,
    large_model_calls_override: int | None = None,
    route_errors: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sets = summary_sets(summary_path)
    usage = usage_for_run(large_usage_run_dir, ids) if large_usage_run_dir is not None else {
        "trajectories": 0,
        "api_calls": 0,
        "cost": 0.0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }
    large_calls = large_model_calls_override if large_model_calls_override is not None else usage["api_calls"]
    total = len(ids)
    row = {
        "condition": name,
        "instances": total,
        "resolved": len(sets["resolved"] & set(ids)),
        "resolved_rate": round(len(sets["resolved"] & set(ids)) / total, 4) if total else 0.0,
        "large_model_calls": int(large_calls),
        "token_cost": usage["total_tokens"],
        "dollar_cost": usage["cost"],
        "empty_patch": len(sets["empty"] & set(ids)),
        "empty_patch_rate": round(len(sets["empty"] & set(ids)) / total, 4) if total else 0.0,
        "harness_error": len(sets["error"] & set(ids)),
        "harness_error_rate": round(len(sets["error"] & set(ids)) / total, 4) if total else 0.0,
        "prompt_tokens": usage["prompt_tokens"],
        "completion_tokens": usage["completion_tokens"],
    }
    if route_errors:
        row.update(route_errors)
    return row


def selective_route_errors(
    *,
    ids: list[str],
    call_policy_path: Path,
    self_summary: Path,
    large_reference_summary: Path,
) -> dict[str, Any]:
    policy = read_json(call_policy_path)
    route_by_id = {row["instance_id"]: row["route"] for row in policy.get("call_log", [])}
    self_sets = summary_sets(self_summary)
    large_sets = summary_sets(large_reference_summary)
    false_delegate = 0
    missed_delegate = 0
    self_gold = 0
    delegate_gold = 0
    for instance_id in ids:
        route = route_by_id.get(instance_id, "L")
        if instance_id in self_sets["resolved"]:
            gold = "SELF_HANDLE"
            self_gold += 1
        elif instance_id in large_sets["resolved"]:
            gold = "DELEGATE"
            delegate_gold += 1
        else:
            gold = "SELF_HANDLE"
            self_gold += 1
        if gold == "SELF_HANDLE" and route == "P":
            false_delegate += 1
        if gold == "DELEGATE" and route != "P":
            missed_delegate += 1
    return {
        "self_handle_gold": self_gold,
        "delegate_gold": delegate_gold,
        "self_handle_false_delegate": false_delegate,
        "self_handle_false_delegate_rate": round(false_delegate / self_gold, 4) if self_gold else 0.0,
        "delegate_missed": missed_delegate,
        "delegate_missed_rate": round(missed_delegate / delegate_gold, 4) if delegate_gold else 0.0,
    }


def write_csv(rows: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path("runs/matched-swebench-main-table-50"))
    parser.add_argument("--subset", default="lite")
    parser.add_argument("--split", default="test")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--filter-regex", default="")
    parser.add_argument("--large-model", default="openai/gpt-5.4-mini")
    parser.add_argument("--large-api-base", default=os.getenv("OPENAI_BASE_URL", "https://zz1cc.cc.cd/v1"))
    parser.add_argument("--large-api-key-b64-env", default="MINI_SWE_LARGE_API_KEY_B64")
    parser.add_argument("--self-model", default="openai/local-qwen3-8b-memory-polarproxy-v22")
    parser.add_argument("--self-api-base", default="http://127.0.0.1:18001/v1")
    parser.add_argument("--memory-file", type=Path, default=Path("runs/memory/self_improve_memory.json"))
    parser.add_argument("--strong-memory-file", type=Path, default=None)
    parser.add_argument("--strategy-memory-file", type=Path, default=None)
    parser.add_argument("--config", default="swebench_backticks.yaml")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--eval-workers", type=int, default=1)
    parser.add_argument("--step-limit", type=int, default=24)
    parser.add_argument("--eval-timeout", type=int, default=1800)
    parser.add_argument("--max-delegate", type=int, default=20)
    parser.add_argument("--redo-existing", action="store_true")
    parser.add_argument("--skip-eval", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    repo_root = Path.cwd()
    out_dir = args.out_dir if args.out_dir.is_absolute() else repo_root / args.out_dir
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("MSWEA_SILENT_STARTUP", "1")

    api_key_b64 = env.get(args.large_api_key_b64_env, "")
    if api_key_b64:
        env["OPENAI_API_KEY"] = base64.b64decode(api_key_b64).decode("utf-8")
    elif not env.get("OPENAI_API_KEY") and not args.dry_run:
        raise RuntimeError(f"Set {args.large_api_key_b64_env} or OPENAI_API_KEY before launching.")

    ids = select_instance_ids(args.subset, args.split, args.limit, args.filter_regex)
    if not ids:
        raise RuntimeError("No instances selected.")
    write_json(out_dir / "instances.json", {"dataset": dataset_name(args.subset), "split": args.split, "ids": ids})

    manifest: dict[str, Any] = {
        "artifact_type": "matched_swebench_main_table_manifest",
        "dataset": dataset_name(args.subset),
        "subset": args.subset,
        "split": args.split,
        "instances": ids,
        "large_model": args.large_model,
        "self_model": args.self_model,
        "memory_file": str(args.memory_file),
        "conditions": {},
    }

    no_dir = out_dir / "no_memory_large"
    run_swebench(
        repo_root=repo_root,
        env=env,
        run_dir=no_dir,
        ids=ids,
        subset=args.subset,
        split=args.split,
        model=args.large_model,
        api_base=args.large_api_base,
        api_key_value=None,
        config=args.config,
        workers=args.workers,
        step_limit=args.step_limit,
        redo_existing=args.redo_existing,
        dry_run=args.dry_run,
    )
    no_summary = None
    if not args.skip_eval:
        no_summary = evaluate(
            repo_root=repo_root,
            env=env,
            run_dir=no_dir,
            out_dir=out_dir / "eval",
            run_id="matched-main-no-memory",
            subset=args.subset,
            split=args.split,
            max_workers=args.eval_workers,
            timeout=args.eval_timeout,
            redo_existing=args.redo_existing,
            dry_run=args.dry_run,
        )
    manifest["conditions"]["no_memory"] = {"run_dir": str(no_dir), "summary": str(no_summary) if no_summary else ""}
    write_json(out_dir / "manifest.json", manifest)

    strong_memory_file = args.strong_memory_file or args.memory_file
    simple_dir = out_dir / ("strong_memory_large" if args.strong_memory_file or args.strategy_memory_file else "simple_memory_large")
    run_swebench(
        repo_root=repo_root,
        env=env,
        run_dir=simple_dir,
        ids=ids,
        subset=args.subset,
        split=args.split,
        model=args.large_model,
        api_base=args.large_api_base,
        api_key_value=None,
        config=args.config,
        workers=args.workers,
        step_limit=args.step_limit,
        memory_file=strong_memory_file,
        memory_gate_mode="simple",
        strategy_memory_file=args.strategy_memory_file,
        redo_existing=args.redo_existing,
        dry_run=args.dry_run,
    )
    simple_summary = None
    if not args.skip_eval:
        simple_summary = evaluate(
            repo_root=repo_root,
            env=env,
            run_dir=simple_dir,
            out_dir=out_dir / "eval",
            run_id="matched-main-simple-memory",
            subset=args.subset,
            split=args.split,
            max_workers=args.eval_workers,
            timeout=args.eval_timeout,
            redo_existing=args.redo_existing,
            dry_run=args.dry_run,
        )
    manifest["conditions"]["simple_memory"] = {
        "run_dir": str(simple_dir),
        "summary": str(simple_summary) if simple_summary else "",
        "memory_file": str(strong_memory_file),
        "strategy_memory_file": str(args.strategy_memory_file) if args.strategy_memory_file else "",
    }
    write_json(out_dir / "manifest.json", manifest)

    self_dir = out_dir / "selective_self_local"
    run_swebench(
        repo_root=repo_root,
        env=env,
        run_dir=self_dir,
        ids=ids,
        subset=args.subset,
        split=args.split,
        model=args.self_model,
        api_base=args.self_api_base,
        api_key_value="EMPTY",
        config=args.config,
        workers=args.workers,
        step_limit=args.step_limit,
        memory_file=args.memory_file,
        memory_gate_mode="simple",
        redo_existing=args.redo_existing,
        dry_run=args.dry_run,
    )
    self_summary = None
    if not args.skip_eval:
        self_summary = evaluate(
            repo_root=repo_root,
            env=env,
            run_dir=self_dir,
            out_dir=out_dir / "eval",
            run_id="matched-main-selective-self-local",
            subset=args.subset,
            split=args.split,
            max_workers=args.eval_workers,
            timeout=args.eval_timeout,
            redo_existing=args.redo_existing,
            dry_run=args.dry_run,
        )

    delegate_ids = choose_delegate_ids(self_dir, ids, max_delegate=args.max_delegate) if not args.dry_run else ids[: min(args.max_delegate, len(ids))]
    write_json(out_dir / "delegate_ids.json", {"delegate_ids": delegate_ids, "policy": "controller_failed_or_empty_patch"})

    delegate_dir = out_dir / "selective_delegate_large"
    if delegate_ids:
        run_swebench(
            repo_root=repo_root,
            env=env,
            run_dir=delegate_dir,
            ids=delegate_ids,
            subset=args.subset,
            split=args.split,
            model=args.large_model,
            api_base=args.large_api_base,
            api_key_value=None,
            config=args.config,
            workers=args.workers,
            step_limit=args.step_limit,
            memory_file=args.memory_file,
            memory_gate_mode="simple",
            redo_existing=args.redo_existing,
            dry_run=args.dry_run,
        )

    merged_dir = out_dir / "selective_merged"
    if not args.dry_run:
        merge_selective_preds(ids=ids, self_run_dir=self_dir, delegate_run_dir=delegate_dir, delegate_ids=delegate_ids, output_dir=merged_dir)
    selective_summary = None
    if not args.skip_eval:
        selective_summary = evaluate(
            repo_root=repo_root,
            env=env,
            run_dir=merged_dir,
            out_dir=out_dir / "eval",
            run_id="matched-main-selective-merged",
            subset=args.subset,
            split=args.split,
            max_workers=args.eval_workers,
            timeout=args.eval_timeout,
            redo_existing=args.redo_existing,
            dry_run=args.dry_run,
        )

    manifest["conditions"]["selective"] = {
        "self_run_dir": str(self_dir),
        "self_summary": str(self_summary) if self_summary else "",
        "delegate_run_dir": str(delegate_dir),
        "delegate_ids": delegate_ids,
        "merged_run_dir": str(merged_dir),
        "summary": str(selective_summary) if selective_summary else "",
    }
    write_json(out_dir / "manifest.json", manifest)

    if not args.skip_eval and not args.dry_run:
        route_errors = selective_route_errors(
            ids=ids,
            call_policy_path=merged_dir / "call_policy_summary.json",
            self_summary=self_summary,
            large_reference_summary=no_summary,
        )
        rows = [
            condition_row(name="no_memory_no_collaboration", ids=ids, summary_path=no_summary, large_usage_run_dir=no_dir),
            condition_row(name="simple_memory", ids=ids, summary_path=simple_summary, large_usage_run_dir=simple_dir),
            condition_row(
                name="trained_memgate_packet_selective",
                ids=ids,
                summary_path=selective_summary,
                large_usage_run_dir=delegate_dir if delegate_ids else None,
                large_model_calls_override=len(delegate_ids),
                route_errors=route_errors,
            ),
        ]
        summary = {"artifact_type": "matched_swebench_main_table_summary", "rows": rows, "manifest": str(out_dir / "manifest.json")}
        write_json(out_dir / "main_table_summary.json", summary)
        write_csv(rows, out_dir / "main_table_summary.csv")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"Wrote manifest: {out_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
