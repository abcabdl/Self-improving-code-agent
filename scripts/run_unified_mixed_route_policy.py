#!/usr/bin/env python3
"""Run one unified L/P route controller over proxy-easy and SWE-hard rows."""

from __future__ import annotations

import argparse
import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

from datasets import load_dataset
import requests

from minisweagent.run.benchmarks.hybrid_gym_curriculum import proxy_easy_curriculum_tasks
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def short_text(value: Any, limit: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text[:limit]


def compact_list(value: Any, *, limit: int = 4) -> list[str]:
    if isinstance(value, list):
        items = value
    elif isinstance(value, tuple):
        items = list(value)
    elif isinstance(value, str):
        try:
            parsed = json.loads(value)
        except Exception:
            parsed = None
        items = parsed if isinstance(parsed, list) else [value]
    else:
        items = []
    out: list[str] = []
    for item in items:
        text = short_text(item, 120)
        if text:
            out.append(text)
        if len(out) >= limit:
            break
    return out


def compact_memory(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "gate": item.get("memory_gate", item.get("gate", "")),
        "instance_id": item.get("instance_id", ""),
        "q_value": item.get("q_value", 0.0),
        "repo": item.get("repo", ""),
        "retrieval_score": item.get("retrieval_score", 0.0),
        "same_repo": bool(item.get("same_repo", False)),
        "semantic_score": item.get("semantic_score", 0.0),
        "similarity_score": item.get("similarity_score", 0.0),
    }


def proxy_task_by_id() -> dict[str, Any]:
    return {task.task_id: task for task in proxy_easy_curriculum_tasks()}


def dataset_rows_by_id(ids: list[str], *, split: str) -> dict[str, dict[str, Any]]:
    rows = list(load_dataset("princeton-nlp/SWE-Bench_Lite", split=split))
    wanted = set(ids)
    return {str(row["instance_id"]): dict(row) for row in rows if str(row["instance_id"]) in wanted}


def parse_json_response(text: str) -> tuple[dict[str, Any], str]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    candidates = [stripped]
    match = re.search(r"\{.*\}", stripped, flags=re.S)
    if match:
        candidates.insert(0, match.group(0))
    last_error = ""
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = str(exc)
            continue
        if isinstance(parsed, dict):
            return parsed, ""
    return {}, last_error or "no_json_object"


def normalize_route(payload: dict[str, Any], fallback: str = "L") -> str:
    raw = str(payload.get("route", payload.get("next_action", fallback))).strip().upper()
    if raw in {"P", "DELEGATE", "DELEGATE_PACKET", "PACKET"}:
        return "P"
    if raw in {"L", "SELF", "SELF_HANDLE", "LOCAL", "LOCAL_SELF_HANDLE"}:
        return "L"
    if bool(payload.get("delegate_needed", False)):
        return "P"
    return fallback


def packet_from_response(payload: dict[str, Any]) -> dict[str, Any]:
    packet = payload.get("delegate_packet", {})
    if not isinstance(packet, dict):
        packet = {}
    selected = payload.get("selected_memory_ids", [])
    if selected and not packet.get("selected_memory_ids"):
        packet["selected_memory_ids"] = selected
    if not packet.get("action_goal"):
        packet["action_goal"] = short_text(payload.get("reason", "delegate with selected memory evidence"), 180)
    packet.setdefault("path_hints", [])
    packet.setdefault("semantic_guards", ["verify_current_issue_first", "no_patch_copying"])
    packet.setdefault("uncertainty", short_text(payload.get("reason", ""), 180))
    return packet


def proxy_prompt_payload(instance_id: str, *, display_id: str | None = None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    task = proxy_task_by_id()[instance_id]
    memory = {
        "id": "mem_1",
        "repo": task.repo,
        "same_repo": True,
        "retrieval_score": 1.0,
        "similarity_score": 1.0,
        "q_value": 1.0,
        "remembered_issue": short_text(task.memory_hint, 900),
        "remembered_patch_summary": "",
        "remembered_tests": [],
    }
    payload = {
        "task_id": display_id or task.task_id,
        "repo": task.repo,
        "current_issue": short_text(task.problem_statement, 1800),
        "current_evidence": short_text(task.current_evidence, 1000),
        "candidate_next_step": short_text(task.expected_signal, 500),
        "memory_candidates": [memory],
    }
    return payload, [memory]


def hard_prompt_payload(
    instance: dict[str, Any],
    memories: list[dict[str, Any]],
    memory_items: dict[str, dict[str, Any]],
    *,
    display_id: str | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    compact: list[dict[str, Any]] = []
    for index, top in enumerate(memories, 1):
        remembered = memory_items.get(str(top.get("instance_id", "")), {})
        compact.append(
            {
                "id": f"mem_{index}",
                **compact_memory(top),
                "remembered_issue": short_text(remembered.get("problem_statement", ""), 280),
                "remembered_patch_summary": short_text(remembered.get("patch_summary", remembered.get("patch", "")), 280),
                "remembered_files": compact_list(remembered.get("touched_files", []), limit=4),
                "remembered_tests": compact_list(remembered.get("tests", []), limit=4),
            }
        )
    payload = {
        "task_id": display_id or instance.get("instance_id", ""),
        "repo": instance.get("repo", ""),
        "current_issue": short_text(instance.get("problem_statement", ""), 1800),
        "fail_to_pass": instance.get("FAIL_TO_PASS", ""),
        "memory_candidates": compact,
    }
    return payload, compact


def build_prompt(payload: dict[str, Any]) -> str:
    schema = {"route": "L or P", "selected_memory_ids": ["mem_1"], "reason": "short reason"}
    prompt_payload = {**payload, "output_schema": schema}
    return (
        "You are a small routing controller for a coding assistant.\n"
        "Decide whether this task should stay with the local small model (route L) or be delegated to a large model (route P).\n"
        "The task has no hidden label. Use only the visible issue, current evidence, and memory candidates.\n"
        "Choose L when the next step is simple, explicit, and locally executable from the evidence.\n"
        "Choose P when the task appears to require a full SWE repair, broad repository reasoning, or uncertain patch synthesis.\n"
        "If choosing P, select only memory ids that are actually useful. Do not repeat the input.\n"
        "Return strict compact JSON only, with keys: route, selected_memory_ids, reason.\n\n"
        f"{json.dumps(prompt_payload, ensure_ascii=False, indent=2, sort_keys=True)}\n"
    )


def call_chat(api_base: str, model: str, prompt: str, *, timeout: int, max_tokens: int) -> tuple[str, dict[str, Any]]:
    response = requests.post(
        api_base.rstrip("/") + "/chat/completions",
        headers={"Authorization": "Bearer EMPTY", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": max_tokens,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    text = str(((payload.get("choices") or [{}])[0].get("message") or {}).get("content", ""))
    return text, payload.get("usage", {})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--split-dir", type=Path, required=True)
    parser.add_argument("--memory-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--split", default="dev", choices=["dev", "test"])
    parser.add_argument("--api-base", default="http://127.0.0.1:18001/v1")
    parser.add_argument("--model", default="local-qwen3-8b-memory-polarproxy-v22")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--max-tokens", type=int, default=900)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    mixed_rows = read_json(args.split_dir / "mixed_rows.json")
    hard_ids = [str(row["id"]) for row in mixed_rows if row.get("kind") == "swe_hard"]
    hard_instances = dataset_rows_by_id(hard_ids, split=args.split)
    memory_payload = load_memory(args.memory_file)
    memory_items_payload = read_json(args.memory_file)
    raw_items = memory_items_payload.get("items", memory_items_payload) if isinstance(memory_items_payload, dict) else memory_items_payload
    memory_items = {str(item.get("instance_id")): item for item in raw_items if isinstance(item, dict)}

    args.output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = args.output_dir / "unified_route_readout.jsonl"
    existing = {str(row.get("instance_id")): row for row in read_jsonl(jsonl_path)} if args.resume else {}
    if jsonl_path.exists() and not args.resume:
        jsonl_path.unlink()

    call_log: list[dict[str, Any]] = []
    total_tokens = 0
    for index, mixed in enumerate(mixed_rows, 1):
        instance_id = str(mixed["id"])
        if instance_id in existing:
            row = dict(existing[instance_id])
            row["index"] = index
            call_log.append(row)
            total_tokens += int((row.get("usage") or {}).get("total_tokens", 0) or 0)
            continue

        display_id = f"task_{index:03d}"
        if mixed.get("kind") == "proxy_easy":
            payload, top_memories = proxy_prompt_payload(instance_id, display_id=display_id)
        else:
            instance = hard_instances[instance_id]
            retrieved = retrieve_memories(
                instance,
                memory_payload,
                k=3,
                strategy="hybrid",
                same_repo_k=2,
                global_k=1,
                min_global_similarity=0.18,
                gate_mode="simple",
                gate_min_similarity=0.18,
                gate_min_q=0.25,
            )
            payload, top_memories = hard_prompt_payload(instance, retrieved, memory_items, display_id=display_id)

        prompt = build_prompt(payload)
        raw_response = ""
        usage: dict[str, Any] = {}
        error = ""
        try:
            raw_response, usage = call_chat(
                args.api_base,
                args.model,
                prompt,
                timeout=args.timeout,
                max_tokens=args.max_tokens,
            )
            parsed, parse_error = parse_json_response(raw_response)
        except Exception as exc:  # noqa: BLE001 - policy artifact should preserve API failures.
            parsed = {}
            parse_error = str(exc)
            error = str(exc)
        route = normalize_route(parsed, fallback="L")
        total_tokens += int(usage.get("total_tokens", 0) or 0)
        row = {
            "index": index,
            "instance_id": instance_id,
            "route": route,
            "large_model_called": route == "P",
            "parse_error": parse_error,
            "error": error,
            "response": parsed,
            "raw_response": raw_response,
            "usage": usage,
            "top_memories": top_memories,
            "packet": packet_from_response(parsed) if route == "P" else {},
        }
        call_log.append(row)
        append_jsonl(jsonl_path, row)
        time.sleep(0.0)

    route_counts = Counter(row["route"] for row in call_log)
    payload = {
        "artifact_type": "unified_mixed_route_policy",
        "model": args.model,
        "api_base": args.api_base,
        "split_dir": str(args.split_dir),
        "rows": len(call_log),
        "large_model_rows": sum(row["route"] == "P" for row in call_log),
        "route_counts": dict(sorted(route_counts.items())),
        "fallback_rows": sum(bool(row.get("parse_error")) for row in call_log),
        "total_tokens": total_tokens,
        "decision_contract": "Prompt does not expose proxy_easy/swe_hard labels; labels are used only by downstream evaluation.",
        "call_log": [
            {
                "instance_id": row["instance_id"],
                "route": row["route"],
                "large_model_called": row["large_model_called"],
                "parse_error": row["parse_error"],
                "error": row["error"],
                "usage": row["usage"],
                "top_memories": row["top_memories"],
                "packet": row["packet"],
            }
            for row in call_log
        ],
    }
    write_json(args.output_dir / "call_policy_summary.json", payload)
    write_json(args.output_dir / "delegate_instances.json", {"ids": [row["instance_id"] for row in call_log if row["route"] == "P"]})
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
