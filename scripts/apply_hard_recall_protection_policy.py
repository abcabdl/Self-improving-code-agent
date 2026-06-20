#!/usr/bin/env python3
"""Promote strong hard-side retrieval clusters while protecting proxy-easy local rows."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def retrieval_by_id(retrieval_policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row.get("instance_id")): row for row in retrieval_policy.get("call_log", [])}


def strong_cluster(row: dict[str, Any], *, min_same_repo: int, min_similarity: float) -> bool:
    same_repo = int(row.get("same_repo_memories", 0) or 0)
    max_similarity = float(row.get("max_similarity", 0.0) or 0.0)
    return same_repo >= min_same_repo and max_similarity >= min_similarity


def promotion_packet(top_memories: list[dict[str, Any]]) -> dict[str, Any]:
    selected = [f"mem_{index}" for index, memory in enumerate(top_memories, 1) if memory.get("same_repo")]
    selected = selected[:3] or ["mem_1"]
    repos = sorted({str(memory.get("repo", "")) for memory in top_memories if memory.get("repo")})
    return {
        "action_goal": "delegate hard SWE repair because retrieved same-repo evidence forms a strong cluster",
        "path_hints": [],
        "selected_memory_ids": selected,
        "semantic_guards": ["verify_current_issue_first", "no_patch_copying", "use_memory_as_evidence_not_patch"],
        "uncertainty": "recall-protection promotion from MemGate L to P; memory cluster is evidence, not an oracle patch",
        "evidence_repos": repos,
    }


def apply_policy(
    *,
    base_policy: dict[str, Any],
    retrieval_policy: dict[str, Any],
    min_same_repo: int,
    min_similarity: float,
    mode: str,
) -> dict[str, Any]:
    retrieval = retrieval_by_id(retrieval_policy)
    call_log: list[dict[str, Any]] = []
    promoted_ids: list[str] = []
    protected_proxy_easy: list[str] = []
    for base_row in base_policy.get("call_log", []):
        row = dict(base_row)
        kind = str(row.get("kind", ""))
        instance_id = str(row.get("instance_id", ""))
        route = str(row.get("route", "")).upper()

        if kind == "proxy_easy":
            row["route"] = "L"
            row["large_model_called"] = False
            row["recall_protection"] = "proxy_easy_protected_local"
            protected_proxy_easy.append(instance_id)
            call_log.append(row)
            continue

        retrieval_row = retrieval.get(instance_id, {})
        if kind == "swe_hard" and route == "L" and strong_cluster(
            retrieval_row,
            min_same_repo=min_same_repo,
            min_similarity=min_similarity,
        ):
            top_memories = retrieval_row.get("top_memories") or row.get("top_memories") or []
            row["route"] = "P"
            row["large_model_called"] = True
            row["protected_promoted"] = True
            row["promotion_reason"] = "same_repo_cluster_recall_protection"
            row["promotion_thresholds"] = {
                "min_same_repo": min_same_repo,
                "min_similarity": min_similarity,
            }
            row["same_repo_memories"] = int(retrieval_row.get("same_repo_memories", 0) or 0)
            row["max_similarity"] = float(retrieval_row.get("max_similarity", 0.0) or 0.0)
            row["top_memories"] = top_memories
            row["packet"] = promotion_packet(top_memories)
            promoted_ids.append(instance_id)
        else:
            row["protected_promoted"] = False
        call_log.append(row)

    route_counts = Counter(str(row.get("route") or "missing") for row in call_log)
    kind_route_counts = Counter(f"{row.get('kind', '')}:{row.get('route', '')}" for row in call_log)
    return {
        "artifact_type": "hard_recall_protected_call_policy",
        "base_policy": base_policy.get("hard_policy", ""),
        "mode": mode,
        "rows": len(call_log),
        "large_model_rows": sum(bool(row.get("large_model_called")) for row in call_log),
        "route_counts": dict(sorted(route_counts.items())),
        "kind_route_counts": dict(sorted(kind_route_counts.items())),
        "promotion_thresholds": {
            "min_same_repo": min_same_repo,
            "min_similarity": min_similarity,
        },
        "promoted_ids": promoted_ids,
        "protected_proxy_easy_ids": protected_proxy_easy,
        "call_log": call_log,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-policy", type=Path, required=True)
    parser.add_argument("--retrieval-policy", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--min-same-repo", type=int, default=3)
    parser.add_argument("--min-similarity", type=float, default=0.28)
    parser.add_argument("--mode", default="proxy_easy_L_hard_same_repo_recall_protection")
    args = parser.parse_args()

    payload = apply_policy(
        base_policy=read_json(args.base_policy),
        retrieval_policy=read_json(args.retrieval_policy),
        min_same_repo=args.min_same_repo,
        min_similarity=args.min_similarity,
        mode=args.mode,
    )
    write_json(args.out, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
