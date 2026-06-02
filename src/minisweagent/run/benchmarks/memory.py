"""Lightweight episodic memory retrieval for SWE-bench runs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]+|\d+")
_STOPWORDS = {
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


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text or "") if t.lower() not in _STOPWORDS and len(t) > 1}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def load_memory(memory_file: str | Path) -> list[dict[str, Any]]:
    path = Path(memory_file)
    if not path.exists():
        raise FileNotFoundError(f"Memory file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, dict):
        items = data.get("items", [])
    else:
        items = data
    if not isinstance(items, list):
        raise ValueError(f"Memory file must contain a list or an object with an items list: {path}")
    for item in items:
        if "tokens" not in item:
            item["tokens"] = sorted(_tokens(_memory_text(item)))
        if "q_value" not in item:
            item["q_value"] = _q_from_legacy_utility(item.get("utility", 1.0))
    return items


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _q_from_legacy_utility(utility: Any) -> float:
    try:
        return _clamp01(float(utility or 0.0) / 2.0)
    except (TypeError, ValueError):
        return 0.5


def _memory_text(item: dict[str, Any]) -> str:
    parts = [
        item.get("repo", ""),
        item.get("problem_statement", ""),
        item.get("hints_text", ""),
        item.get("patch_summary", ""),
        " ".join(item.get("touched_files", []) or []),
    ]
    return "\n".join(str(p) for p in parts if p)


def retrieve_memories(
    instance: dict[str, Any],
    memories: list[dict[str, Any]],
    k: int = 3,
    *,
    exclude_instance_id: bool = True,
    strategy: str = "score",
    same_repo_k: int = 2,
    global_k: int = 1,
    min_global_similarity: float = 0.18,
    low_confidence_q: float = 0.5,
    low_confidence_similarity: float = 0.28,
) -> list[dict[str, Any]]:
    if not memories or k <= 0:
        return []
    query_tokens = _tokens(
        "\n".join(
            [
                str(instance.get("repo", "")),
                str(instance.get("problem_statement", "")),
                str(instance.get("hints_text", "")),
            ]
        )
    )
    repo = instance.get("repo", "")
    instance_id = instance.get("instance_id", "")
    scored: list[tuple[float, dict[str, Any]]] = []
    for item in memories:
        if exclude_instance_id and item.get("instance_id") == instance_id:
            continue
        item_tokens = set(item.get("tokens") or [])
        semantic = _jaccard(query_tokens, item_tokens)
        same_repo = 1.0 if item.get("repo") == repo else 0.0
        similarity = _clamp01(semantic + 0.15 * same_repo)
        q_value = _clamp01(float(item.get("q_value", _q_from_legacy_utility(item.get("utility", 1.0))) or 0.0))
        score = 0.7 * similarity + 0.3 * q_value
        if score > 0:
            enriched = dict(item)
            enriched["retrieval_score"] = round(score, 4)
            enriched["similarity_score"] = round(similarity, 4)
            enriched["semantic_score"] = round(semantic, 4)
            enriched["q_value"] = round(q_value, 4)
            enriched["same_repo"] = bool(same_repo)
            scored.append((score, enriched))
    scored.sort(key=lambda x: x[0], reverse=True)

    if strategy == "score":
        return [item for _, item in scored[:k]]
    if strategy != "hybrid":
        raise ValueError(f"Unknown memory retrieval strategy: {strategy}")

    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    def add_item(item: dict[str, Any]) -> None:
        memory_id = item.get("instance_id", "")
        if memory_id in selected_ids or len(selected) >= k:
            return
        selected.append(item)
        selected_ids.add(memory_id)

    same_repo = [item for _, item in scored if item.get("same_repo")]
    for item in same_repo[: max(0, same_repo_k)]:
        add_item(item)

    if global_k > 0:
        global_ranked = sorted(
            [
                item
                for _, item in scored
                if item.get("same_repo") or float(item.get("similarity_score", 0.0)) >= min_global_similarity
            ],
            key=lambda item: (
                float(item.get("q_value", 0.0)),
                float(item.get("similarity_score", 0.0)),
                float(item.get("retrieval_score", 0.0)),
            ),
            reverse=True,
        )
        for item in global_ranked:
            if len(selected) >= min(k, max(0, same_repo_k) + max(0, global_k)):
                break
            add_item(item)

        for _, item in scored:
            if not item.get("same_repo") and float(item.get("similarity_score", 0.0)) < min_global_similarity:
                continue
            if len(selected) >= k:
                break
            add_item(item)

    max_q = max((float(item.get("q_value", 0.0)) for item in selected), default=0.0)
    max_similarity = max((float(item.get("similarity_score", 0.0)) for item in selected), default=0.0)
    low_confidence = max_q <= low_confidence_q and max_similarity < low_confidence_similarity
    for item in selected:
        item["memory_strategy"] = strategy
        item["memory_confidence"] = "low" if low_confidence else "normal"
    return selected


def format_memory_block(memories: list[dict[str, Any]]) -> str:
    if not memories:
        return ""
    low_confidence = all(item.get("memory_confidence") == "low" for item in memories)
    chunks = [
        "<retrieved_repair_memories>",
        "The following are retrieved successful repair experiences from related SWE-bench tasks.",
        "Use them as strategic hints for locating files, designing tests, and avoiding common mistakes.",
        "Do not copy code blindly; verify against the current repository and issue.",
    ]
    if low_confidence:
        chunks.extend(
            [
                "Confidence note: these memories have weak retrieval confidence.",
                "Treat them as loose orientation only; prioritize the current failing tests, traceback, and codebase evidence.",
            ]
        )
    for idx, item in enumerate(memories, 1):
        files = ", ".join(item.get("touched_files", [])[:6]) or "unknown"
        tests = ", ".join(item.get("tests", [])[:4]) or "unknown"
        strategy_limit = 360 if low_confidence else 1200
        chunks.extend(
            [
                (
                    f"<memory id=\"{idx}\" score=\"{item.get('retrieval_score', 0)}\" "
                    f"same_repo=\"{item.get('same_repo', False)}\" "
                    f"confidence=\"{item.get('memory_confidence', 'normal')}\">"
                ),
                f"repo: {item.get('repo', 'unknown')}",
                f"instance_id: {item.get('instance_id', 'unknown')}",
                f"q_value: {item.get('q_value', 0)}",
                f"touched_files: {files}",
                f"relevant_tests: {tests}",
                f"strategy: {item.get('patch_summary', '').strip()[:strategy_limit]}",
                "</memory>",
            ]
        )
    chunks.append("</retrieved_repair_memories>")
    return "\n".join(chunks)
