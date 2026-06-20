#!/usr/bin/env python3
"""Rebuild MemGate's top-k memory policy from the current Q-valued memory file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from datasets import load_dataset

from minisweagent.run.benchmarks.memory import load_memory, retrieve_memories


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def dataset_rows_by_id(ids: list[str], *, split: str) -> dict[str, dict[str, Any]]:
    rows = list(load_dataset("princeton-nlp/SWE-Bench_Lite", split=split))
    wanted = set(ids)
    return {str(row["instance_id"]): dict(row) for row in rows if str(row["instance_id"]) in wanted}


def compact_memory(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "gate": item.get("memory_gate", item.get("gate", "")),
        "instance_id": item.get("instance_id", ""),
        "memory_confidence": item.get("memory_confidence", ""),
        "memory_route": item.get("memory_route", ""),
        "q_value": item.get("q_value", 0.0),
        "repo": item.get("repo", ""),
        "retrieval_score": item.get("retrieval_score", 0.0),
        "same_repo": bool(item.get("same_repo", False)),
        "semantic_score": item.get("semantic_score", 0.0),
        "similarity_score": item.get("similarity_score", 0.0),
    }


def fallback_route(top_memories: list[dict[str, Any]]) -> str:
    same_repo = sum(1 for item in top_memories if item.get("same_repo"))
    max_similarity = max((float(item.get("similarity_score", 0.0) or 0.0) for item in top_memories), default=0.0)
    return "P" if same_repo >= 2 and max_similarity >= 0.30 else "L"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances-json", type=Path, required=True)
    parser.add_argument("--split", default="test", choices=["dev", "test"])
    parser.add_argument("--memory-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--memory-k", type=int, default=3)
    parser.add_argument("--memory-strategy", choices=["score", "hybrid"], default="hybrid")
    parser.add_argument("--same-repo-k", type=int, default=2)
    parser.add_argument("--global-k", type=int, default=1)
    parser.add_argument("--min-global-similarity", type=float, default=0.18)
    parser.add_argument("--low-confidence-q", type=float, default=0.5)
    parser.add_argument("--low-confidence-similarity", type=float, default=0.28)
    parser.add_argument("--memory-gate-mode", choices=["off", "simple", "atom_direct"], default="simple")
    parser.add_argument("--gate-min-similarity", type=float, default=0.18)
    parser.add_argument("--gate-min-q", type=float, default=0.25)
    args = parser.parse_args()

    ids = [str(item) for item in read_json(args.instances_json)["ids"]]
    instances = dataset_rows_by_id(ids, split=args.split)
    memories = load_memory(args.memory_file)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    retrieval_log = args.output_dir / "retrieved_memories.jsonl"
    if retrieval_log.exists():
        retrieval_log.unlink()

    call_log: list[dict[str, Any]] = []
    for index, instance_id in enumerate(ids, 1):
        instance = instances[instance_id]
        retrieved = retrieve_memories(
            instance,
            memories,
            k=args.memory_k,
            strategy=args.memory_strategy,
            same_repo_k=args.same_repo_k,
            global_k=args.global_k,
            min_global_similarity=args.min_global_similarity,
            low_confidence_q=args.low_confidence_q,
            low_confidence_similarity=args.low_confidence_similarity,
            gate_mode=args.memory_gate_mode,
            gate_min_similarity=args.gate_min_similarity,
            gate_min_q=args.gate_min_q,
        )
        top_memories = [compact_memory(item) for item in retrieved]
        route = fallback_route(top_memories)
        for rank, memory in enumerate(top_memories, 1):
            append_jsonl(
                retrieval_log,
                {
                    "target_instance_id": instance_id,
                    "target_repo": instance.get("repo", ""),
                    "memory_instance_id": memory.get("instance_id", ""),
                    "memory_repo": memory.get("repo", ""),
                    "rank": rank,
                    "retrieval_score": memory.get("retrieval_score", 0.0),
                    "similarity_score": memory.get("similarity_score", 0.0),
                    "q_value": memory.get("q_value", 0.0),
                    "same_repo": memory.get("same_repo", False),
                },
            )
        call_log.append(
            {
                "fallback_route": route,
                "index": index,
                "instance_id": instance_id,
                "large_model_called": route == "P",
                "route": route,
                "same_repo_memories": sum(1 for item in top_memories if item.get("same_repo")),
                "max_similarity": max(
                    (float(item.get("similarity_score", 0.0) or 0.0) for item in top_memories),
                    default=0.0,
                ),
                "top_memories": top_memories,
            }
        )

    delegate_ids = [row["instance_id"] for row in call_log if row["route"] == "P"]
    summary = {
        "artifact_type": "memgate_retrieval_policy",
        "instances": len(ids),
        "split": args.split,
        "memory_file": str(args.memory_file),
        "memory_k": args.memory_k,
        "memory_strategy": args.memory_strategy,
        "memory_gate_mode": args.memory_gate_mode,
        "same_repo_k": args.same_repo_k,
        "global_k": args.global_k,
        "min_global_similarity": args.min_global_similarity,
        "gate_min_similarity": args.gate_min_similarity,
        "gate_min_q": args.gate_min_q,
        "large_model_calls": len(delegate_ids),
        "no_call_rows": len(ids) - len(delegate_ids),
        "delegate_ids": delegate_ids,
        "retrieval_log": str(retrieval_log),
        "call_log": call_log,
    }
    write_json(args.output_dir / "call_policy_summary.json", summary)
    write_json(args.output_dir / "delegate_instances.json", {"ids": delegate_ids})
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
