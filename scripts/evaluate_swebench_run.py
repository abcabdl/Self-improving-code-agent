"""Evaluate a mini-SWE-agent SWE-bench run directory.

Usage:
    python scripts/evaluate_swebench_run.py runs/swebench-lite-dev-0-3-gpt5mini

The script expects ``preds.json`` in the run directory, writes ``preds.jsonl``,
detects instance ids automatically, and invokes the official SWE-bench harness.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def ensure_windows_resource_shim(repo_root: Path) -> None:
    """Let SWE-bench import its Unix-only resource dependency on Windows."""
    if platform.system() != "Windows":
        return
    shim = repo_root / "resource.py"
    if shim.exists():
        return
    shim.write_text(
        "\n".join(
            [
                "RLIMIT_AS = 9",
                "RLIMIT_CPU = 0",
                "RLIMIT_DATA = 2",
                "RLIMIT_FSIZE = 1",
                "RLIMIT_NOFILE = 7",
                "RLIMIT_STACK = 3",
                "RLIMIT_CORE = 4",
                "RLIM_INFINITY = -1",
                "",
                "def getrlimit(resource):",
                "    return (RLIM_INFINITY, RLIM_INFINITY)",
                "",
                "def setrlimit(resource, limits):",
                "    return None",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )


def patch_harness_newlines() -> None:
    """Patch installed SWE-bench harness for local Windows evaluation quirks."""
    if platform.system() != "Windows":
        return
    spec = importlib.util.find_spec("swebench")
    if spec is None or spec.origin is None:
        raise RuntimeError("swebench is not installed. Run: uv pip install swebench")
    harness = Path(spec.origin).parent / "harness" / "run_evaluation.py"
    text = harness.read_text(encoding="utf-8")
    patched = text.replace(
        'patch_file.write_text(pred[KEY_PREDICTION] or "")',
        'patch_file.write_text(pred[KEY_PREDICTION] or "", newline="\\n")',
    ).replace(
        "eval_file.write_text(test_spec.eval_script)",
        'eval_file.write_text(test_spec.eval_script, newline="\\n")',
    )
    marker = "def _codex_patch_eval_script(instance_id: str, eval_script: str) -> str:\n"
    if marker not in patched:
        helper = '''def _codex_patch_eval_script(instance_id: str, eval_script: str) -> str:
    """Apply local evaluation environment fixes without changing predictions."""
    if instance_id.startswith("pvlib__pvlib-python-"):
        install_cmd = "python -m pip install -e .[all]"
        fix_cmd = 'python -m pip install "numpy<2"'
        if install_cmd in eval_script and fix_cmd not in eval_script:
            eval_script = eval_script.replace(install_cmd, install_cmd + "\\n" + fix_cmd)
    if instance_id == "pyvista__pyvista-4315":
        install_cmd = "python -m pip install -e ."
        fix_cmd = "apt-get update && apt-get install -y libgl1 libglx-mesa0 libxrender1"
        if install_cmd in eval_script and fix_cmd not in eval_script:
            eval_script = eval_script.replace(install_cmd, fix_cmd + "\\n" + install_cmd)
    if instance_id.startswith("pydicom__pydicom-"):
        install_cmd = "python -m pip install -e ."
        fix_cmd = 'python -m pip install "pytest<8"'
        if install_cmd in eval_script and fix_cmd not in eval_script:
            eval_script = eval_script.replace(install_cmd, install_cmd + "\\n" + fix_cmd)
    return eval_script


'''
        patched = patched.replace("\nGIT_APPLY_CMDS = [", "\n" + helper + "GIT_APPLY_CMDS = [")
    elif 'instance_id.startswith("pydicom__pydicom-")' not in patched:
        patched = patched.replace(
            '    return eval_script\n\n\nGIT_APPLY_CMDS = [',
            '    if instance_id.startswith("pydicom__pydicom-"):\n'
            '        install_cmd = "python -m pip install -e ."\n'
            '        fix_cmd = \'python -m pip install "pytest<8"\'\n'
            '        if install_cmd in eval_script and fix_cmd not in eval_script:\n'
            '            eval_script = eval_script.replace(install_cmd, install_cmd + "\\\\n" + fix_cmd)\n'
            '    return eval_script\n\n\nGIT_APPLY_CMDS = [',
        )
    patched = patched.replace(
        'eval_file.write_text(test_spec.eval_script, newline="\\n")',
        'eval_file.write_text(_codex_patch_eval_script(instance_id, test_spec.eval_script), newline="\\n")',
    )
    if patched != text:
        harness.write_text(patched, encoding="utf-8", newline="\n")


def convert_predictions(run_dir: Path) -> tuple[Path, list[str]]:
    preds_json = run_dir / "preds.json"
    if not preds_json.exists():
        raise FileNotFoundError(f"Missing {preds_json}")
    data = json.loads(preds_json.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or not data:
        raise ValueError(f"{preds_json} does not contain any predictions")

    preds_jsonl = run_dir / "preds.jsonl"
    instance_ids: list[str] = []
    with preds_jsonl.open("w", encoding="utf-8", newline="\n") as f:
        for key, item in data.items():
            instance_id = item.get("instance_id") or key
            instance_ids.append(instance_id)
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    return preds_jsonl, instance_ids


def default_run_id(run_dir: Path, suffix: str) -> str:
    name = run_dir.name.replace("\\", "-").replace("/", "-")
    return f"{name}-{suffix}" if suffix else name


def copy_summary_to_report_dir(repo_root: Path, report_dir: Path, run_id: str) -> Path | None:
    """SWE-bench writes the run summary in cwd; mirror it into report_dir."""
    matches = sorted(repo_root.glob(f"*.{run_id}.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        return None
    source = matches[0]
    report_dir.mkdir(parents=True, exist_ok=True)
    destination = report_dir / source.name
    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="Run directory containing preds.json")
    parser.add_argument("--dataset-name", default="princeton-nlp/SWE-Bench_Lite")
    parser.add_argument("--split", default="dev")
    parser.add_argument("--run-id", default="", help="Defaults to the run directory name")
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--cache-level", default="instance", choices=["none", "base", "env", "instance"])
    parser.add_argument("--clean", default="False")
    parser.add_argument("--report-dir", default=".", help="Directory to write SWE-bench summary report")
    parser.add_argument("--online", action="store_true", help="Allow Hugging Face network access")
    parser.add_argument("--dry-run", action="store_true", help="Print the command without running it")
    args = parser.parse_args()

    repo_root = Path.cwd()
    run_dir = args.run_dir
    if not run_dir.is_absolute():
        run_dir = repo_root / run_dir
    run_dir = run_dir.resolve()

    ensure_windows_resource_shim(repo_root)
    patch_harness_newlines()
    preds_jsonl, instance_ids = convert_predictions(run_dir)

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    if not args.online:
        env["HF_DATASETS_OFFLINE"] = "1"
        env["HF_HUB_OFFLINE"] = "1"

    run_id = args.run_id or default_run_id(run_dir, "eval")
    cmd = [
        sys.executable,
        "-m",
        "swebench.harness.run_evaluation",
        "--dataset_name",
        args.dataset_name,
        "--split",
        args.split,
        "--predictions_path",
        str(preds_jsonl),
        "--instance_ids",
        *instance_ids,
        "--max_workers",
        str(args.max_workers),
        "--run_id",
        run_id,
        "--cache_level",
        args.cache_level,
        "--clean",
        args.clean,
        "--timeout",
        str(args.timeout),
        "--report_dir",
        args.report_dir,
    ]

    print(f"Run directory: {run_dir}")
    print(f"Predictions:   {preds_jsonl}")
    print(f"Instances:     {len(instance_ids)}")
    for instance_id in instance_ids:
        print(f"  - {instance_id}")
    print("Command:")
    print(" ".join(f'"{part}"' if " " in part else part for part in cmd))

    if args.dry_run:
        return 0
    result = subprocess.run(cmd, cwd=repo_root, env=env, check=False)
    report_dir = Path(args.report_dir)
    if not report_dir.is_absolute():
        report_dir = repo_root / report_dir
    copied = copy_summary_to_report_dir(repo_root, report_dir, run_id)
    if copied:
        print(f"Summary copied to: {copied}")
    else:
        print(f"Warning: no summary report matching *.{run_id}.json found in {repo_root}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
