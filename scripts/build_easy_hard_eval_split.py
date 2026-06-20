#!/usr/bin/env python3
"""Build an evidence-qualified easy/hard SWE-Bench evaluation split."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEV_PREFIXES = (
    "marshmallow-code__",
    "pvlib__",
    "pydicom__",
    "pylint-dev__",
    "pyvista__",
    "sqlfluff__",
)


@dataclass
class Evidence:
    file: str
    family: str
    split: str


@dataclass
class Row:
    id: str
    resolved: list[Evidence] = field(default_factory=list)
    submitted: list[Evidence] = field(default_factory=list)
    completed: list[Evidence] = field(default_factory=list)
    empty: list[Evidence] = field(default_factory=list)
    unresolved: list[Evidence] = field(default_factory=list)
    errors: list[Evidence] = field(default_factory=list)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def family_for_file(path: Path) -> str:
    name = path.name.lower()
    if "local-qwen" in name:
        return "local"
    if "gpt-5.4" in name or "gpt-5-mini" in name or "gpt5mini" in name:
        return "gpt"
    if "oracle" in name:
        return "oracle"
    return "other"


def split_for_file(path: Path, ids: list[str]) -> str:
    name = path.name.lower()
    if "dev" in name:
        return "dev"
    if "36" in name or "matched-main" in name or "memory-covered" in name:
        return "test36"
    if any(instance_id.startswith(DEV_PREFIXES) for instance_id in ids):
        return "dev"
    return "unknown"


def evidence_files(items: list[Evidence], limit: int = 5) -> str:
    return ";".join(item.file for item in items[:limit])


def count_family(items: list[Evidence], family: str) -> int:
    return sum(1 for item in items if item.family == family)


def count_family_split(items: list[Evidence], family: str, split: str) -> int:
    return sum(1 for item in items if item.family == family and item.split == split)


def row_split(row: Row) -> str:
    evidence = row.resolved + row.submitted
    if any(item.split == "dev" for item in evidence):
        return "dev"
    if any(item.split == "test36" for item in evidence):
        return "test36"
    return "unknown"


def collect_rows(root: Path) -> tuple[list[dict[str, Any]], list[Row]]:
    by_id: dict[str, Row] = {}
    summaries: list[dict[str, Any]] = []

    def ensure(instance_id: str) -> Row:
        row = by_id.get(instance_id)
        if row is None:
            row = Row(id=instance_id)
            by_id[instance_id] = row
        return row

    for path in sorted(root.glob("*.json")):
        try:
            payload = read_json(path)
        except Exception:
            continue
        if not isinstance(payload, dict) or not isinstance(payload.get("resolved_ids"), list):
            continue

        all_ids = list(payload.get("submitted_ids") or []) + list(payload.get("resolved_ids") or [])
        family = family_for_file(path)
        split = split_for_file(path, all_ids)
        summaries.append(
            {
                "file": path.name,
                "family": family,
                "split": split,
                "submitted": len(payload.get("submitted_ids") or []),
                "resolved": len(payload.get("resolved_ids") or []),
                "empty": len(payload.get("empty_patch_ids") or []),
            }
        )
        evidence = Evidence(path.name, family, split)
        for json_key, attr in [
            ("resolved_ids", "resolved"),
            ("submitted_ids", "submitted"),
            ("completed_ids", "completed"),
            ("empty_patch_ids", "empty"),
            ("unresolved_ids", "unresolved"),
            ("error_ids", "errors"),
        ]:
            for instance_id in payload.get(json_key) or []:
                getattr(ensure(str(instance_id)), attr).append(evidence)

    return summaries, list(by_id.values())


def flatten_rows(rows: list[Row], split: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        inferred_split = row_split(row)
        if split != "all" and inferred_split != split:
            continue
        local_resolved = [item for item in row.resolved if item.family == "local"]
        gpt_resolved = [item for item in row.resolved if item.family == "gpt"]
        local_submitted = [item for item in row.submitted if item.family == "local"]
        gpt_submitted = [item for item in row.submitted if item.family == "gpt"]
        local_empty = [item for item in row.empty if item.family == "local"]
        local_unresolved = [item for item in row.unresolved if item.family == "local"]
        gpt_empty = [item for item in row.empty if item.family == "gpt"]

        easy_candidate = inferred_split == split and bool(local_resolved)
        hard_candidate = (
            inferred_split == split
            and bool(gpt_resolved)
            and not local_resolved
            and (bool(local_submitted) or bool(local_empty) or bool(local_unresolved))
        )
        out.append(
            {
                "id": row.id,
                "split": inferred_split,
                "local_resolved_count": len(local_resolved),
                "gpt_resolved_count": len(gpt_resolved),
                "local_submitted_count": len(local_submitted),
                "gpt_submitted_count": len(gpt_submitted),
                "local_empty_count": len(local_empty),
                "local_unresolved_count": len(local_unresolved),
                "gpt_empty_count": len(gpt_empty),
                "local_resolved_dev_count": count_family_split(row.resolved, "local", "dev"),
                "gpt_resolved_dev_count": count_family_split(row.resolved, "gpt", "dev"),
                "easy_candidate": easy_candidate,
                "hard_candidate": hard_candidate,
                "easy_evidence_level": "historical_local_resolved_needs_fresh_current_verify"
                if easy_candidate
                else "",
                "hard_evidence_level": "gpt_resolved_and_historical_local_not_resolved"
                if hard_candidate
                else "",
                "requires_fresh_current_local_verify": easy_candidate,
                "local_resolved_files": evidence_files(local_resolved),
                "gpt_resolved_files": evidence_files(gpt_resolved),
                "local_empty_files": evidence_files(local_empty),
                "local_unresolved_files": evidence_files(local_unresolved),
            }
        )
    return out


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--split", choices=["dev", "test36", "all"], default="dev")
    parser.add_argument("--easy-count", type=int, default=5)
    parser.add_argument("--hard-count", type=int, default=10)
    args = parser.parse_args()

    summaries, source_rows = collect_rows(args.root)
    rows = flatten_rows(source_rows, args.split)
    easy_pool = sorted(
        [row for row in rows if row["easy_candidate"]],
        key=lambda row: (-int(row["local_resolved_count"]), -int(row["gpt_resolved_count"]), str(row["id"])),
    )
    hard_pool = sorted(
        [row for row in rows if row["hard_candidate"]],
        key=lambda row: (-int(row["gpt_resolved_count"]), -int(row["local_submitted_count"]), str(row["id"])),
    )

    selected_easy = easy_pool[: args.easy_count]
    selected_easy_ids = {row["id"] for row in selected_easy}
    selected_hard = [row for row in hard_pool if row["id"] not in selected_easy_ids][: args.hard_count]
    selected_ids = [row["id"] for row in selected_easy + selected_hard]

    manifest = {
        "artifact_type": "easy_hard_eval_split",
        "split": args.split,
        "requested": {"easy": args.easy_count, "hard": args.hard_count},
        "counts": {
            "summaries_scanned": len(summaries),
            "candidate_rows": len(rows),
            "easy_pool": len(easy_pool),
            "hard_pool": len(hard_pool),
            "selected_easy": len(selected_easy),
            "selected_hard": len(selected_hard),
            "selected_total": len(selected_ids),
        },
        "selected_easy_ids": [row["id"] for row in selected_easy],
        "selected_hard_ids": [row["id"] for row in selected_hard],
        "selected_ids": selected_ids,
        "selection_rules": [
            "easy: same split, resolved by at least one historical local-qwen summary.",
            "hard: same split, resolved by GPT summary, no local-qwen resolved evidence, and local-qwen has submitted/empty/unresolved evidence.",
            "Rows are ranked by evidence count, not by manual per-instance patch inspection.",
        ],
        "caveats": [
            "The easy rows are not yet strict fresh-current-local verified for local-qwen3-8b-memory-polarproxy-v22.",
            "Use fresh_verify_easy_instances.json before claiming self-suitable performance.",
            "This split is intended to replace the failed 36-row-derived mixed split, where strict fresh-local easy pool was zero.",
        ],
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "manifest.json", manifest)
    write_json(args.output_dir / "candidate_rows.json", rows)
    write_csv(args.output_dir / "candidate_rows.csv", rows)
    write_json(args.output_dir / "instances.json", {"ids": selected_ids})
    write_json(args.output_dir / "easy_instances.json", {"ids": [row["id"] for row in selected_easy]})
    write_json(args.output_dir / "hard_instances.json", {"ids": [row["id"] for row in selected_hard]})
    write_json(args.output_dir / "fresh_verify_easy_instances.json", {"ids": [row["id"] for row in selected_easy]})
    write_json(args.output_dir / "fresh_verify_hard_local_instances.json", {"ids": [row["id"] for row in selected_hard]})
    write_json(args.output_dir / "source_summaries.json", summaries)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
