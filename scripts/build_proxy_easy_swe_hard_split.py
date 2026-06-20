#!/usr/bin/env python3
"""Build a mixed split with custom proxy-easy rows and SWE hard rows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def passed_proxy_easy(row: dict[str, Any], *, min_strict_score: float) -> bool:
    return (
        str(row.get("suite", "")) == "proxy_easy"
        and bool(row.get("has_action"))
        and bool(row.get("skill_match"))
        and bool(row.get("semantic_pass"))
        and float(row.get("strict_score", 0.0)) >= min_strict_score
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proxy-easy-results", type=Path, required=True)
    parser.add_argument("--hard-instances", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--easy-count", type=int, default=5)
    parser.add_argument("--hard-count", type=int, default=10)
    parser.add_argument("--min-strict-score", type=float, default=0.85)
    args = parser.parse_args()

    proxy_rows = read_jsonl(args.proxy_easy_results)
    hard_ids = [str(item) for item in read_json(args.hard_instances).get("ids", [])]

    pass_rows = [row for row in proxy_rows if passed_proxy_easy(row, min_strict_score=args.min_strict_score)]
    pass_rows.sort(key=lambda row: (-float(row.get("strict_score", 0.0)), str(row.get("task_id", ""))))
    selected_easy = pass_rows[: args.easy_count]
    selected_hard = hard_ids[: args.hard_count]

    easy_ids = [str(row.get("task_id", "")) for row in selected_easy]
    mixed_rows = [
        {
            "id": row["task_id"],
            "kind": "proxy_easy",
            "suite": "proxy_easy",
            "expected_skill": row.get("expected_skill", ""),
            "strict_score": row.get("strict_score", 0.0),
            "total_tokens": (row.get("usage") or {}).get("total_tokens", 0),
            "source": str(args.proxy_easy_results),
        }
        for row in selected_easy
    ]
    mixed_rows.extend(
        {
            "id": instance_id,
            "kind": "swe_hard",
            "suite": "swebench_lite_dev",
            "source": str(args.hard_instances),
        }
        for instance_id in selected_hard
    )

    summary = {
        "artifact_type": "proxy_easy_swe_hard_mixed_split",
        "proxy_easy_results": str(args.proxy_easy_results),
        "hard_instances": str(args.hard_instances),
        "requested": {"easy": args.easy_count, "hard": args.hard_count},
        "selected_easy_ids": easy_ids,
        "selected_hard_ids": selected_hard,
        "selected_ids": easy_ids + selected_hard,
        "counts": {
            "proxy_easy_rows": len(proxy_rows),
            "proxy_easy_pass": len(pass_rows),
            "hard_pool": len(hard_ids),
            "selected_easy": len(selected_easy),
            "selected_hard": len(selected_hard),
            "selected_total": len(mixed_rows),
        },
        "acceptance": {
            "min_strict_score": args.min_strict_score,
            "requires_action": True,
            "requires_skill_match": True,
            "requires_semantic_pass": True,
        },
        "caveats": [
            "Easy rows are custom proxy self-handle tasks, not SWE-Bench repairs.",
            "Do not compare easy resolved counts with official SWE-Bench resolved counts as the same metric.",
            "Use this split to evaluate route/token behavior: local Qwen should handle proxy_easy cheaply, while swe_hard rows test delegation.",
        ],
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "manifest.json", summary)
    write_json(args.output_dir / "mixed_rows.json", mixed_rows)
    write_json(args.output_dir / "proxy_easy_instances.json", {"ids": easy_ids})
    write_json(args.output_dir / "swe_hard_instances.json", {"ids": selected_hard})
    write_json(args.output_dir / "instances.json", {"ids": easy_ids + selected_hard})
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
