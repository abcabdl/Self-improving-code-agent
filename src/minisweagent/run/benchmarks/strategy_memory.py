"""External strategy learning for SWE-bench agents without model updates."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ACTION_CATEGORIES = ("search", "inspect", "test", "edit", "submit", "other")
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

_WORKFLOW_STEP_TEXT = {
    "search": "Search for issue-specific symbols, call sites, and relevant files before editing.",
    "inspect": "Inspect the narrow code path and nearby tests to understand the existing contract.",
    "test": "Run a focused reproduction or targeted test to gather executable evidence.",
    "edit": "Apply the smallest source-code change consistent with the repository design.",
    "submit": "Inspect the final diff and submit only the intended source changes.",
    "other": "Use a supporting shell action only when it advances the current repair hypothesis.",
}

_REFLECTION_ADVICE = {
    "empty_patch": "Do not stop without a source patch. Re-check the issue, locate the implementation boundary, and make a minimal verified edit.",
    "no_targeted_test": "Run a focused reproduction or nearby regression test before submitting. A plausible patch without executable evidence is risky.",
    "no_edit": "Avoid spending the full budget only exploring. Convert the strongest evidence into a narrow source edit, then verify it.",
    "failed_commands": "Several shell actions failed. Check paths and command assumptions before continuing, and prefer smaller diagnostic commands.",
    "too_many_actions": "The trajectory wandered through many actions. Narrow the hypothesis earlier and use targeted search, inspection, and tests.",
    "generic_failure": "The previous repair attempt did not resolve the task. Prefer current repository evidence over analogy and verify the final behavior.",
}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def tokenize(text: str) -> list[str]:
    return sorted(
        {
            token.lower()
            for token in _TOKEN_RE.findall(text or "")
            if token.lower() not in _STOPWORDS and len(token) > 1
        }
    )


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def classify_command(command: str) -> str:
    """Map a shell command to a coarse tool-use action."""
    text = f" {command.lower()} "
    if "complete_task_and_submit_final_output" in text:
        return "submit"
    if re.search(r"(^|[;&|]\s*)(pytest|tox|nosetests|npm test|yarn test|pnpm test|cargo test|go test|make test)\b", text):
        return "test"
    if re.search(r"\bpython(?:3)?\s+-m\s+(pytest|unittest)\b|\bmanage\.py\s+test\b", text):
        return "test"
    if re.search(r"\b(sed\s+-i|perl\s+-pi|apply_patch|git\s+apply)\b", text):
        return "edit"
    if re.search(r"(?:^|\s)(?:cat|tee)\s+.*(?:>|>>)|(?:>|>>)\s*[^\s]+", text):
        return "edit"
    if re.search(r"\b(rg|grep|find|fd|locate)\b", text):
        return "search"
    if re.search(r"\b(cat|sed\s+-n|head|tail|nl|ls|pwd|tree|git\s+(status|diff|show))\b", text):
        return "inspect"
    if re.search(r"\bpython(?:3)?\b", text):
        return "test"
    return "other"


def extract_actions(trajectory: dict[str, Any]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    for message in trajectory.get("messages", []):
        for action in (message.get("extra") or {}).get("actions", []):
            command = str(action.get("command", "")).strip()
            if command:
                actions.append({"command": command, "category": classify_command(command)})
    return actions


def _compact_categories(actions: list[dict[str, str]]) -> list[str]:
    categories: list[str] = []
    counts: Counter[str] = Counter()
    for action in actions:
        category = action["category"]
        if (not categories or category != categories[-1]) and counts[category] < 2:
            categories.append(category)
            counts[category] += 1
        if len(categories) >= 10:
            break
    return categories


def workflow_from_trajectory(
    instance_id: str,
    repo: str,
    problem_statement: str,
    trajectory: dict[str, Any],
) -> dict[str, Any] | None:
    actions = extract_actions(trajectory)
    sequence = _compact_categories(actions)
    if not actions or "edit" not in sequence:
        return None
    signature = ">".join(sequence)
    digest = hashlib.sha1(f"{repo}:{signature}".encode("utf-8")).hexdigest()[:10]
    return {
        "workflow_id": f"workflow:{repo}:{digest}",
        "repo": repo,
        "tokens": tokenize(problem_statement),
        "action_sequence": sequence,
        "steps": [_WORKFLOW_STEP_TEXT[category] for category in sequence],
        "q_value": 0.75,
        "source_instance_ids": [instance_id],
        "success_count": 1,
        "failure_count": 0,
    }


def reflection_codes(trajectory: dict[str, Any], *, empty_patch: bool = False) -> list[str]:
    actions = extract_actions(trajectory)
    categories = [action["category"] for action in actions]
    failed_commands = sum(
        1
        for message in trajectory.get("messages", [])
        if message.get("role") in {"tool", "user"}
        and int((message.get("extra") or {}).get("returncode", 0) or 0) != 0
    )
    codes: list[str] = []
    if empty_patch:
        codes.append("empty_patch")
    if "test" not in categories:
        codes.append("no_targeted_test")
    if "edit" not in categories:
        codes.append("no_edit")
    if failed_commands >= 2:
        codes.append("failed_commands")
    if len(actions) >= 30:
        codes.append("too_many_actions")
    return codes or ["generic_failure"]


def reflections_from_trajectory(
    instance_id: str,
    repo: str,
    problem_statement: str,
    trajectory: dict[str, Any],
    *,
    empty_patch: bool = False,
) -> list[dict[str, Any]]:
    items = []
    for code in reflection_codes(trajectory, empty_patch=empty_patch):
        digest = hashlib.sha1(f"{repo}:{code}".encode("utf-8")).hexdigest()[:10]
        items.append(
            {
                "reflection_id": f"reflection:{repo}:{digest}",
                "repo": repo,
                "failure_code": code,
                "tokens": tokenize(problem_statement),
                "advice": _REFLECTION_ADVICE[code],
                "q_value": 0.5,
                "source_instance_ids": [instance_id],
                "use_count": 0,
            }
        )
    return items


def _new_bandit_actions() -> dict[str, dict[str, Any]]:
    return {category: {"q_value": 0.5, "update_count": 0} for category in ACTION_CATEGORIES}


def empty_strategy_memory() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "workflows": [],
        "reflections": [],
        "tool_bandit": {"global": _new_bandit_actions(), "repos": {}},
    }


def load_strategy_memory(strategy_file: str | Path) -> dict[str, Any]:
    path = Path(strategy_file)
    if not path.exists():
        raise FileNotFoundError(f"Strategy memory file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"Strategy memory must contain an object: {path}")
    payload.setdefault("schema_version", 1)
    payload.setdefault("workflows", [])
    payload.setdefault("reflections", [])
    bandit = payload.setdefault("tool_bandit", {})
    global_actions = bandit.setdefault("global", {})
    for category, defaults in _new_bandit_actions().items():
        global_actions.setdefault(category, defaults)
    bandit.setdefault("repos", {})
    return payload


def merge_strategy_items(existing: list[dict[str, Any]], additions: list[dict[str, Any]], *, id_key: str) -> int:
    by_id = {str(item.get(id_key, "")): item for item in existing}
    added = 0
    for item in additions:
        item_id = str(item[id_key])
        if item_id not in by_id:
            existing.append(item)
            by_id[item_id] = item
            added += 1
            continue
        current = by_id[item_id]
        sources = list(current.get("source_instance_ids", []))
        for source_id in item.get("source_instance_ids", []):
            if source_id not in sources:
                sources.append(source_id)
        current["source_instance_ids"] = sources
        if id_key == "workflow_id":
            current["success_count"] = int(current.get("success_count", 0)) + int(item.get("success_count", 0))
    return added


def _score_item(instance: dict[str, Any], item: dict[str, Any]) -> tuple[float, dict[str, Any]]:
    query_tokens = set(tokenize("\n".join([str(instance.get("problem_statement", "")), str(instance.get("hints_text", ""))])))
    similarity = _jaccard(query_tokens, set(item.get("tokens", [])))
    same_repo = item.get("repo", "") == instance.get("repo", "")
    q_value = _clamp01(float(item.get("q_value", 0.5) or 0.0))
    score = 0.55 * similarity + 0.25 * q_value + 0.2 * float(same_repo)
    enriched = dict(item)
    enriched["retrieval_score"] = round(score, 4)
    enriched["similarity_score"] = round(similarity, 4)
    enriched["same_repo"] = same_repo
    enriched["q_value"] = round(q_value, 4)
    return score, enriched


def retrieve_strategy_items(
    instance: dict[str, Any],
    items: list[dict[str, Any]],
    *,
    k: int,
    min_score: float = 0.3,
) -> list[dict[str, Any]]:
    if k <= 0:
        return []
    scored = [_score_item(instance, item) for item in items]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for score, item in scored[:k] if score >= min_score]


def tool_prior(strategy: dict[str, Any], repo: str) -> list[dict[str, Any]]:
    bandit = strategy.get("tool_bandit", {})
    global_actions = bandit.get("global", {})
    repo_actions = bandit.get("repos", {}).get(repo, {})
    priorities = []
    for category in ACTION_CATEGORIES:
        global_q = float(global_actions.get(category, {}).get("q_value", 0.5))
        repo_q = float(repo_actions.get(category, {}).get("q_value", global_q))
        priorities.append({"category": category, "q_value": round(0.4 * global_q + 0.6 * repo_q, 4)})
    priorities.sort(key=lambda item: item["q_value"], reverse=True)
    return priorities


def format_strategy_block(
    workflows: list[dict[str, Any]],
    reflections: list[dict[str, Any]],
    priorities: list[dict[str, Any]],
) -> str:
    if not workflows and not reflections and not priorities:
        return ""
    chunks = [
        "<learned_external_strategy>",
        "The following controller state was learned from previous repair trajectories and executable feedback.",
        "Use it as guidance, not as a rigid script. Current repository evidence and failing tests take priority.",
    ]
    if priorities:
        ordered = ", ".join(f"{item['category']}={item['q_value']}" for item in priorities)
        chunks.extend(
            [
                "<tool_use_bandit>",
                f"Historical action priorities: {ordered}",
                "Prefer high-value evidence gathering early, make a narrow edit once the hypothesis is clear, and verify before submission.",
                "</tool_use_bandit>",
            ]
        )
    for idx, workflow in enumerate(workflows, 1):
        chunks.append(
            f"<workflow id=\"{idx}\" workflow_id=\"{workflow.get('workflow_id', '')}\" "
            f"score=\"{workflow.get('retrieval_score', 0)}\" same_repo=\"{workflow.get('same_repo', False)}\">"
        )
        chunks.append("Suggested repair workflow:")
        for step_idx, step in enumerate(workflow.get("steps", []), 1):
            chunks.append(f"{step_idx}. {step}")
        chunks.append("</workflow>")
    for idx, reflection in enumerate(reflections, 1):
        chunks.extend(
            [
                f"<failure_reflection id=\"{idx}\" reflection_id=\"{reflection.get('reflection_id', '')}\" "
                f"score=\"{reflection.get('retrieval_score', 0)}\" same_repo=\"{reflection.get('same_repo', False)}\">",
                f"Avoid this previously observed failure mode: {reflection.get('advice', '')}",
                "</failure_reflection>",
            ]
        )
    chunks.append("</learned_external_strategy>")
    return "\n".join(chunks)


def trajectory_stats(trajectory: dict[str, Any]) -> dict[str, Any]:
    actions = extract_actions(trajectory)
    categories = [action["category"] for action in actions]
    return {
        "action_count": len(actions),
        "action_categories": categories,
        "category_counts": dict(Counter(categories)),
    }
