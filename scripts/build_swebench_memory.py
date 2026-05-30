"""Build a lightweight SWE-bench episodic memory file.

The memory stores successful reference repairs from a dataset split. At runtime
mini-swe-agent can retrieve similar memories and inject them as strategy hints.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

from datasets import load_dataset


DATASET_MAPPING = {
    "full": "princeton-nlp/SWE-Bench",
    "lite": "princeton-nlp/SWE-Bench_Lite",
    "verified": "princeton-nlp/SWE-Bench_Verified",
}


def touched_files(patch: str) -> list[str]:
    files: list[str] = []
    for line in (patch or "").splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                path = parts[2]
                if path.startswith("a/"):
                    path = path[2:]
                files.append(path)
    return sorted(dict.fromkeys(files))


def summarize_patch(patch: str, max_lines: int = 36) -> str:
    lines: list[str] = []
    current_file = ""
    for line in (patch or "").splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            current_file = parts[2][2:] if len(parts) >= 3 and parts[2].startswith("a/") else line
            lines.append(f"File: {current_file}")
        elif line.startswith("@@"):
            lines.append(line)
        elif line.startswith("+") and not line.startswith("+++"):
            stripped = line[1:].strip()
            if stripped and not stripped.startswith("#"):
                lines.append(f"Added: {stripped[:180]}")
        elif line.startswith("-") and not line.startswith("---"):
            stripped = line[1:].strip()
            if stripped and not stripped.startswith("#"):
                lines.append(f"Removed: {stripped[:180]}")
        if len(lines) >= max_lines:
            break
    return "\n".join(lines)


def tokenize(text: str) -> list[str]:
    stopwords = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "be",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "this",
        "to",
        "with",
    }
    return sorted(
        {
            tok.lower()
            for tok in re.findall(r"[A-Za-z_][A-Za-z0-9_]+|\d+", text or "")
            if tok.lower() not in stopwords and len(tok) > 1
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="lite", help="Dataset alias or Hugging Face dataset name")
    parser.add_argument("--split", default="test")
    parser.add_argument("--output", type=Path, default=Path("runs/memory/swebench_lite_test_memory.json"))
    parser.add_argument("--repos", default="", help="Optional comma-separated repo allowlist")
    parser.add_argument("--max-items", type=int, default=0)
    parser.add_argument("--max-per-repo", type=int, default=25)
    parser.add_argument("--scan-limit", type=int, default=0, help="Maximum streamed rows to scan before stopping")
    parser.add_argument("--streaming", action="store_true", help="Stream the dataset instead of downloading it first")
    parser.add_argument("--online", action="store_true", help="Allow Hugging Face network access")
    args = parser.parse_args()

    if not args.online:
        os.environ["HF_DATASETS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

    dataset_name = DATASET_MAPPING.get(args.dataset, args.dataset)
    ds = load_dataset(dataset_name, split=args.split, streaming=args.streaming)
    repos = {x.strip() for x in args.repos.split(",") if x.strip()}

    items = []
    per_repo: dict[str, int] = {}
    scanned = 0
    for row in ds:
        scanned += 1
        if repos and row.get("repo") not in repos:
            if args.scan_limit and scanned >= args.scan_limit:
                break
            continue
        repo_count = per_repo.get(row.get("repo", ""), 0)
        if args.max_per_repo and repo_count >= args.max_per_repo:
            if repos and all(per_repo.get(repo, 0) >= args.max_per_repo for repo in repos):
                break
            if args.scan_limit and scanned >= args.scan_limit:
                break
            continue
        patch = row.get("patch") or ""
        files = touched_files(patch)
        text = "\n".join(
            [
                row.get("repo", ""),
                row.get("problem_statement", ""),
                row.get("hints_text", ""),
                " ".join(files),
                summarize_patch(patch),
            ]
        )
        item = {
            "repo": row.get("repo", ""),
            "instance_id": row.get("instance_id", ""),
            "problem_statement": row.get("problem_statement", ""),
            "hints_text": row.get("hints_text", ""),
            "touched_files": files,
            "tests": list(row.get("FAIL_TO_PASS", []) or []),
            "patch_summary": summarize_patch(patch),
            "utility": 1.0,
            "q_value": 0.5,
            "tokens": tokenize(text),
        }
        items.append(item)
        per_repo[row.get("repo", "")] = repo_count + 1
        if args.max_items and len(items) >= args.max_items:
            break
        if args.scan_limit and scanned >= args.scan_limit:
            break

    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "dataset": dataset_name,
        "split": args.split,
        "items": items,
        "scanned": scanned,
        "per_repo": per_repo,
    }
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"Wrote {len(items)} memories to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
