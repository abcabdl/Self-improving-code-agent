#!/usr/bin/env python3
"""Run one SWE-Bench condition instance-by-instance with a wall-clock timeout.

This wrapper is for long matched-slice experiments where an unstable provider
or Docker startup can hang a whole batch. It keeps the normal mini-SWE-agent
runner unchanged, but launches one instance at a time and skips completed
predictions on resume.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def regex_for_id(instance_id: str) -> str:
    return "^" + re.escape(instance_id) + "$"


def completed_ids(run_dir: Path) -> set[str]:
    preds_path = run_dir / "preds.json"
    if not preds_path.exists():
        return set()
    try:
        preds = read_json(preds_path)
    except Exception:
        return set()
    return set(preds) if isinstance(preds, dict) else set()


def write_empty_prediction(run_dir: Path, instance_id: str, model_name: str, reason: str) -> None:
    preds_path = run_dir / "preds.json"
    try:
        preds = read_json(preds_path) if preds_path.exists() else {}
    except Exception:
        preds = {}
    if not isinstance(preds, dict):
        preds = {}
    preds[instance_id] = {
        "instance_id": instance_id,
        "model_name_or_path": f"{model_name}+empty_on_{reason}",
        "model_patch": "",
    }
    preds_path.write_text(json.dumps(preds, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def cleanup_minisweagent_containers() -> None:
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except FileNotFoundError:
        return
    names = [line.strip() for line in result.stdout.splitlines() if line.strip().startswith("minisweagent-")]
    if names:
        subprocess.run(["docker", "rm", "-f", *names], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances-json", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--subset", default="lite")
    parser.add_argument("--split", default="test")
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-class", default="")
    parser.add_argument("--api-base", required=True)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--api-key-b64-env", default="")
    parser.add_argument("--config", default="swebench_backticks.yaml")
    parser.add_argument("--step-limit", type=int, default=24)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--docker-pull-timeout", type=int, default=300)
    parser.add_argument("--memory-file", type=Path, default=None)
    parser.add_argument("--memory-k", type=int, default=3)
    parser.add_argument("--memory-strategy", default="hybrid")
    parser.add_argument("--memory-same-repo-k", type=int, default=2)
    parser.add_argument("--memory-global-k", type=int, default=1)
    parser.add_argument("--memory-gate-mode", default="off")
    parser.add_argument("--memory-stage-aware", action="store_true")
    parser.add_argument("--task-prefix-file", type=Path, default=None)
    parser.add_argument("--strategy-memory-file", type=Path, default=None)
    parser.add_argument("--workflow-k", type=int, default=1)
    parser.add_argument("--reflection-k", type=int, default=2)
    parser.add_argument("--redo-existing", action="store_true")
    parser.add_argument("--cleanup-containers-on-timeout", action="store_true")
    parser.add_argument("--write-empty-on-failure", action="store_true")
    args = parser.parse_args()

    payload = read_json(args.instances_json)
    ids = list(payload.get("ids", []))
    if not ids:
        raise SystemExit(f"No ids in {args.instances_json}")

    args.run_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("MSWEA_SILENT_STARTUP", "1")
    if args.api_key is not None:
        env["OPENAI_API_KEY"] = args.api_key
    elif args.api_key_b64_env:
        value = env.get(args.api_key_b64_env, "")
        if not value:
            raise SystemExit(f"Missing base64 API key env var: {args.api_key_b64_env}")
        env["OPENAI_API_KEY"] = base64.b64decode(value).decode("utf-8")

    skipped = completed_ids(args.run_dir) if not args.redo_existing else set()
    log_path = args.run_dir / "per_instance_launcher.log"
    with log_path.open("a", encoding="utf-8", newline="\n") as log:
        for index, instance_id in enumerate(ids, 1):
            if instance_id in skipped:
                print(f"[{index}/{len(ids)}] skip completed {instance_id}", flush=True)
                continue
            cmd = [
                sys.executable,
                "-m",
                "minisweagent.run.benchmarks.swebench",
                "--subset",
                args.subset,
                "--split",
                args.split,
                "--filter",
                regex_for_id(instance_id),
                "-o",
                str(args.run_dir),
                "-w",
                "1",
                "-m",
                args.model,
            ]
            if args.model_class:
                cmd.extend(["--model-class", args.model_class])
            cmd.extend(
                [
                "-c",
                args.config,
                "-c",
                f"model.model_kwargs.api_base={args.api_base}",
                "-c",
                "model.model_kwargs.drop_params=true",
                "-c",
                "model.cost_tracking=ignore_errors",
                "-c",
                f"agent.step_limit={args.step_limit}",
                "-c",
                f"environment.pull_timeout={args.docker_pull_timeout}",
                ]
            )
            if args.memory_file is not None:
                cmd.extend(
                    [
                        "--memory-file",
                        str(args.memory_file),
                        "--memory-k",
                        str(args.memory_k),
                        "--memory-strategy",
                        args.memory_strategy,
                        "--memory-same-repo-k",
                        str(args.memory_same_repo_k),
                        "--memory-global-k",
                        str(args.memory_global_k),
                        "--memory-gate-mode",
                        args.memory_gate_mode,
                    ]
                )
                if args.memory_stage_aware:
                    cmd.append("--memory-stage-aware")
            if args.task_prefix_file is not None:
                cmd.extend(["--task-prefix-file", str(args.task_prefix_file)])
            if args.strategy_memory_file is not None:
                cmd.extend(
                    [
                        "--strategy-memory-file",
                        str(args.strategy_memory_file),
                        "--workflow-k",
                        str(args.workflow_k),
                        "--reflection-k",
                        str(args.reflection_k),
                    ]
                )
            if args.redo_existing:
                cmd.append("--redo-existing")

            print(f"[{index}/{len(ids)}] run {instance_id}", flush=True)
            log.write("\n$ " + " ".join(cmd) + "\n")
            log.flush()
            try:
                result = subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=args.timeout)
            except subprocess.TimeoutExpired:
                log.write(f"\nTIMEOUT after {args.timeout}s: {instance_id}\n")
                log.flush()
                if args.cleanup_containers_on_timeout:
                    cleanup_minisweagent_containers()
                if args.write_empty_on_failure:
                    write_empty_prediction(args.run_dir, instance_id, args.model, "timeout")
                continue
            if result.returncode != 0:
                log.write(f"\nFAILED exit={result.returncode}: {instance_id}\n")
                log.flush()
                if args.write_empty_on_failure:
                    write_empty_prediction(args.run_dir, instance_id, args.model, f"exit_{result.returncode}")
            if args.cleanup_containers_on_timeout:
                cleanup_minisweagent_containers()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
