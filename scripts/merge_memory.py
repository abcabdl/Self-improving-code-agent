"""Merge lightweight SWE-bench memory JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    items = []
    seen = set()
    for path in args.inputs:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        for item in data.get("items", data if isinstance(data, list) else []):
            key = (item.get("source", ""), item.get("repo", ""), item.get("instance_id", ""))
            if key in seen:
                continue
            seen.add(key)
            items.append(item)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"items": items}, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"Wrote {len(items)} merged memories to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
