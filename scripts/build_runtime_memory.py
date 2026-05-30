"""Build runtime repair memories from resolved SWE-bench evaluation results."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

from datasets import load_dataset

from build_swebench_memory import summarize_patch, tokenize, touched_files


def load_summary(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--extra-summary", type=Path, action="append", default=[])
    parser.add_argument("--dataset", default="princeton-nlp/SWE-Bench_Lite")
    parser.add_argument("--split", default="dev")
    parser.add_argument("--output", type=Path, default=Path("runs/memory/runtime_resolved_memory.json"))
    args = parser.parse_args()

    os.environ["HF_DATASETS_OFFLINE"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"

    summaries = [load_summary(args.summary)] + [load_summary(p) for p in args.extra_summary]
    resolved_ids: set[str] = set()
    for summary in summaries:
        resolved_ids.update(summary.get("resolved_ids", []))

    preds = json.loads((args.run_dir / "preds.json").read_text(encoding="utf-8-sig"))
    ds = load_dataset(args.dataset, split=args.split)
    rows = {row["instance_id"]: row for row in ds}

    items = []
    for instance_id in sorted(resolved_ids):
        if instance_id not in rows or instance_id not in preds:
            continue
        row = rows[instance_id]
        patch = preds[instance_id].get("model_patch") or ""
        files = touched_files(patch)
        patch_summary = summarize_patch(patch)
        text = "\n".join(
            [
                row.get("repo", ""),
                row.get("problem_statement", ""),
                row.get("hints_text", ""),
                " ".join(files),
                patch_summary,
            ]
        )
        items.append(
            {
                "repo": row.get("repo", ""),
                "instance_id": instance_id,
                "problem_statement": row.get("problem_statement", ""),
                "hints_text": row.get("hints_text", ""),
                "touched_files": files,
                "tests": list(row.get("FAIL_TO_PASS", []) or []),
                "patch_summary": patch_summary,
                "utility": 2.0,
                "q_value": 1.0,
                "tokens": tokenize(text),
                "source": "runtime_resolved",
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps({"dataset": args.dataset, "split": args.split, "items": items}, indent=2, ensure_ascii=False),
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {len(items)} runtime memories to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
