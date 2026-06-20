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


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return False


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _first_dict(*values: Any) -> dict[str, Any]:
    for value in values:
        parsed = _as_dict(value)
        if parsed:
            return parsed
    return {}


def memory_atom_direct_route(item: dict[str, Any]) -> str:
    """Return the conservative atom-direct route for a retrieved memory item.

    This is intentionally deterministic: runtime only treats a memory as
    packet-worthy when learned/offline evidence atoms say it supports the
    current task, all protective atoms are false, and there is concrete packet
    content to pass along.
    """

    atoms = _first_dict(
        item.get("evidence_atoms"),
        item.get("atom_summary"),
        item.get("memory_reliability_atoms"),
        item.get("route_atoms"),
    )
    if not atoms:
        return "SELF_HANDLE"

    current_task_support = _as_bool(atoms.get("current_task_support"))
    protective = any(
        _as_bool(atoms.get(key))
        for key in (
            "reverify_before_use",
            "recheck_needed",
            "auxiliary_only",
            "background_only",
            "insufficient_for_delegation",
            "not_enough_for_packet",
        )
    )
    packet_evidence = _as_dict(item.get("packet_evidence"))
    candidate_signal = _as_dict(item.get("packet_candidate_signal"))
    packet_paths = (
        item.get("touched_files")
        or item.get("candidate_paths")
        or packet_evidence.get("paths")
        or packet_evidence.get("current_files")
        or candidate_signal.get("candidate_paths")
        or []
    )
    packet_symbols = (
        item.get("touched_functions_classes")
        or item.get("candidate_symbols")
        or packet_evidence.get("symbols")
        or candidate_signal.get("candidate_symbols")
        or []
    )
    packet_tests = (
        item.get("tests")
        or item.get("test_nodes")
        or item.get("candidate_tests")
        or packet_evidence.get("test_nodes")
        or candidate_signal.get("candidate_tests")
        or []
    )
    has_packet_anchors = bool(packet_paths or packet_symbols or packet_tests)
    return "DELEGATE_PACKET" if current_task_support and not protective and has_packet_anchors else "SELF_HANDLE"


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
    gate_mode: str = "off",
    gate_min_similarity: float = 0.18,
    gate_min_q: float = 0.25,
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
    if gate_mode not in {"off", "simple", "atom_direct"}:
        raise ValueError(f"Unknown memory gate mode: {gate_mode}")

    def passes_gate(item: dict[str, Any]) -> bool:
        if gate_mode == "off":
            item["memory_gate"] = "off"
            return True
        if gate_mode == "atom_direct":
            route = memory_atom_direct_route(item)
            item["memory_gate"] = "pass" if route == "DELEGATE_PACKET" else "abstain"
            item["memory_route"] = route
            item["memory_gate_reason"] = (
                "atom_direct_packet_ready" if route == "DELEGATE_PACKET" else "atom_direct_self_handle_or_missing_packet"
            )
            return route == "DELEGATE_PACKET"
        q_value = float(item.get("q_value", 0.0))
        similarity = float(item.get("similarity_score", 0.0))
        same_repo = bool(item.get("same_repo", False))
        passed = q_value >= gate_min_q and (same_repo or similarity >= gate_min_similarity)
        item["memory_gate"] = "pass" if passed else "abstain"
        item["gate_min_similarity"] = round(gate_min_similarity, 4)
        item["gate_min_q"] = round(gate_min_q, 4)
        return passed

    if strategy == "score":
        selected = []
        for _, item in scored:
            if passes_gate(item):
                selected.append(item)
            if len(selected) >= k:
                break
        for item in selected:
            item["memory_strategy"] = strategy
            item["memory_confidence"] = "normal"
        return selected
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

    same_repo = [item for _, item in scored if item.get("same_repo") and passes_gate(item)]
    for item in same_repo[: max(0, same_repo_k)]:
        add_item(item)

    if global_k > 0:
        global_ranked = sorted(
            [
                item
                for _, item in scored
                if passes_gate(item)
                and (item.get("same_repo") or float(item.get("similarity_score", 0.0)) >= min_global_similarity)
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
            if not passes_gate(item):
                continue
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


def format_memory_block(memories: list[dict[str, Any]], *, stage_aware: bool = False) -> str:
    if not memories:
        return ""
    low_confidence = all(item.get("memory_confidence") == "low" for item in memories)
    chunks = [
        "<retrieved_repair_memories>",
        "The following are retrieved successful repair experiences from related SWE-bench tasks.",
        "Use them as strategic hints for locating files, designing tests, and avoiding common mistakes.",
        "Do not copy code blindly; verify against the current repository and issue.",
        (
            "Memory-use protocol: validate that remembered paths and symbols exist, map each useful memory to a "
            "current-repo invariant, inspect source/control flow before editing, then run a check that would fail if wrong."
        ),
        "If the current issue names a specific rule, class, function, or error, follow that current evidence before remembered filenames.",
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
        strategy_limit = 240 if low_confidence else 360
        chunks.extend(
            [
                (
                    f"<memory id=\"{idx}\" score=\"{item.get('retrieval_score', 0)}\" "
                    f"same_repo=\"{item.get('same_repo', False)}\" "
                    f"confidence=\"{item.get('memory_confidence', 'normal')}\" "
                    f"gate=\"{item.get('memory_gate', 'off')}\">"
                ),
                f"repo: {item.get('repo', 'unknown')}",
                f"instance_id: {item.get('instance_id', 'unknown')}",
                f"q_value: {item.get('q_value', 0)}",
            ]
        )
        if stage_aware:
            chunks.extend(
                [
                    (
                        f"localization_hint: remembered prior files: {files}. "
                        "Use them only after checking current issue names, symbols, and error text; "
                        "If any path is absent, migrate the hint by searching current repo symbols, issue terms, "
                        "and neighboring modules. Also migrate the hint if a remembered path points to a different rule."
                    ),
                    (
                        f"reproduction_hint: nearby tests or checks used before: {tests}. "
                        "Map these to the current checkout and run a behavior-sensitive check."
                    ),
                    (
                        f"patch_hypothesis_hint: {item.get('patch_summary', '').strip()[:strategy_limit]}. "
                        "Treat this as a hypothesis, not a patch recipe."
                    ),
                ]
            )
        else:
            chunks.extend(
                [
                    f"touched_files: {files}",
                    (
                        "path_migration_hint: verify remembered paths before using them; if they are absent, "
                        "map the memory to current-code symbols or nearby modules and continue from an existing "
                        "source file."
                    ),
                    f"relevant_tests: {tests}",
                    f"strategy: {item.get('patch_summary', '').strip()[:strategy_limit]}",
                ]
            )
        chunks.append("</memory>")
    chunks.append("</retrieved_repair_memories>")
    return "\n".join(chunks)
