"""Small Hybrid-Gym-style curriculum tasks for memory-agent training.

These records keep the difficulty below full SWE-bench while preserving the
important loop: use a retrieved memory, locate current code, make a minimal
source edit, and verify the behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


ACTION_FENCE = "mswea_bash_command"


@dataclass(frozen=True)
class CurriculumTask:
    task_id: str
    skill: str
    repo: str
    problem_statement: str
    memory_hint: str
    target_command: str
    expected_signal: str
    current_evidence: str = ""
    reward: float = 1.0
    tags: tuple[str, ...] = field(default_factory=tuple)


def format_action(command: str, thought: str = "I will take the next focused step from the memory hint.") -> dict[str, Any]:
    """Return a textbased mini-swe-agent assistant response for one command."""
    return {
        "role": "assistant",
        "content": f"THOUGHT: {thought}\n\n```{ACTION_FENCE}\n{command.strip()}\n```",
        "extra": {"actions": [{"command": command.strip()}]},
    }


def memory_block(task: CurriculumTask) -> str:
    return (
        "<retrieved_repair_memories>\n"
        f"- memory_id: {task.task_id}-memory\n"
        f"- repo: {task.repo}\n"
        f"- useful_prior: {task.memory_hint}\n"
        "</retrieved_repair_memories>"
    )


def task_prompt(task: CurriculumTask) -> list[dict[str, str]]:
    """Build a one-step prompt that exercises one local-codebase skill."""
    content = (
        "<curriculum_task>\n"
        f"id: {task.task_id}\n"
        f"skill: {task.skill}\n"
        f"repo: {task.repo}\n"
        f"problem: {task.problem_statement}\n"
        f"{memory_block(task)}\n"
        "<rules>\n"
        "- Emit exactly one bash command in a mswea_bash_command fence.\n"
        "- Prefer current source evidence over stale paths in memory.\n"
        "- Do not submit a final answer in this curriculum step.\n"
        "</rules>\n"
        "</curriculum_task>"
    )
    if task.current_evidence:
        content += f"\n<current_evidence>\n{task.current_evidence}\n</current_evidence>"
    return [{"role": "user", "content": content}]


def task_to_record(task: CurriculumTask, *, run_id: str = "hybrid-gym-mini-curriculum") -> dict[str, Any]:
    """Convert a curriculum task into the existing agent-RL step schema."""
    response = format_action(task.target_command)
    return {
        "schema_version": 1,
        "record_type": "hybrid_gym_curriculum",
        "skill": task.skill,
        "run_id": run_id,
        "instance_id": task.task_id,
        "repo": task.repo,
        "memory_ids": [f"{task.task_id}-memory"],
        "memory_block": memory_block(task),
        "messages_before_action": task_prompt(task),
        "assistant_action": response["extra"]["actions"][0],
        "assistant_message": response,
        "observation_summary": task.expected_signal,
        "resolved": True,
        "step_index": 1,
        "step_count": 1,
        "invalid_action_count": 0,
        "reward": round(float(task.reward), 6),
        "tags": list(task.tags),
    }


def curriculum_record_to_verl_record(record: dict[str, Any]) -> dict[str, Any]:
    """Convert a curriculum record into a verl-compatible row."""
    return {
        "data_source": f"memory_agent_hybrid_gym_{record.get('skill', 'unknown')}",
        "prompt": record.get("messages_before_action", []),
        "response": record.get("assistant_message", {}),
        "reward_model": {"style": "rule", "ground_truth": float(record.get("reward", 0.0))},
        "extra_info": {
            "record_type": "hybrid_gym_curriculum",
            "skill": record.get("skill", ""),
            "instance_id": record.get("instance_id", ""),
            "repo": record.get("repo", ""),
            "run_id": record.get("run_id", ""),
            "memory_ids": record.get("memory_ids", []),
            "expected_signal": record.get("observation_summary", ""),
            "tags": record.get("tags", []),
        },
    }


def default_curriculum_tasks() -> list[CurriculumTask]:
    """Return a conservative starter course for locate/edit/test memory use."""
    return [
        CurriculumTask(
            task_id="mini_locate_memory_symbol",
            skill="locate",
            repo="toy/parserlib",
            problem_statement="A parser option is ignored when normalize_mode is called with aliases.",
            memory_hint="The prior fix started by searching for normalize_mode in parser/options.py.",
            target_command='rg -n "normalize_mode|ModeAlias" src tests',
            expected_signal="A good locate step returns the current file and symbol before editing.",
            tags=("locate", "memory_to_current_source"),
        ),
        CurriculumTask(
            task_id="mini_edit_exact_replacement",
            skill="edit",
            repo="toy/parserlib",
            problem_statement="The current source still returns the raw alias instead of canonicalizing it.",
            memory_hint="After locating the current helper, replace the raw return with ALIASES.get(value, value).",
            current_evidence=(
                "src/parserlib/options.py:17:def normalize_mode(value):\n"
                "src/parserlib/options.py:18:    return value"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/parserlib/options.py')\n"
                "text = path.read_text()\n"
                "old = 'def normalize_mode(value):\\n    return value\\n'\n"
                "new = 'def normalize_mode(value):\\n    return ALIASES.get(value, value)\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit step performs one exact source replacement in the located file.",
            tags=("edit", "exact_replacement", "no_noop"),
        ),
        CurriculumTask(
            task_id="mini_test_focused_behavior",
            skill="test",
            repo="toy/parserlib",
            problem_statement="Verify that alias canonicalization now works without running the entire suite.",
            memory_hint=(
                "The prior successful check used the exact narrow parser option test: "
                "tests/test_options.py::test_normalize_mode_alias. Copy this node exactly."
            ),
            target_command="PYTHONPATH=src:. python -m pytest tests/test_options.py::test_normalize_mode_alias -q",
            expected_signal="A good test step runs a focused verification for the edited behavior.",
            tags=("test", "focused_verification"),
        ),
        CurriculumTask(
            task_id="mini_recover_stale_memory_path",
            skill="locate",
            repo="toy/apilib",
            problem_statement="The public client still drops timeout when retrying requests.",
            memory_hint="A stale memory mentions old_client.py, but the project was reorganized after that fix.",
            current_evidence="find . -name '*client*.py' would reveal src/apilib/http/client.py.",
            target_command='rg -n "timeout|retry|Client" src/apilib tests',
            expected_signal="A good recovery step searches current source instead of trusting the stale path.",
            tags=("locate", "stale_memory_recovery"),
        ),
    ]


def heldout_curriculum_tasks() -> list[CurriculumTask]:
    """Return held-out mini tasks with the same skills but different repos/symbols."""
    return [
        CurriculumTask(
            task_id="heldout_locate_cache_key",
            skill="locate",
            repo="toy/cachelib",
            problem_statement="Cache entries with tuple keys miss because the key normalization helper changed names.",
            memory_hint="A previous fix searched for normalize_cache_key near cache/store.py before editing.",
            target_command='rg -n "normalize_cache_key|CacheKey|make_key" src tests',
            expected_signal="A good locate step searches current source for the renamed cache-key helper.",
            tags=("heldout", "locate", "memory_to_current_source"),
        ),
        CurriculumTask(
            task_id="heldout_edit_exact_default",
            skill="edit",
            repo="toy/metricslib",
            problem_statement=(
                "The current source still treats a missing sample weight as zero instead of one, "
                "but an explicit sample weight of 0 must remain valid."
            ),
            memory_hint=(
                "After reading the current accumulator helper, replace the zero default with a unit default "
                "only in the None branch. Do not use `value or 1`, because explicit zero weights must be preserved."
            ),
            current_evidence=(
                "src/metricslib/accumulator.py:41:def sample_weight(value):\n"
                "src/metricslib/accumulator.py:42:    return value or 0"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/metricslib/accumulator.py')\n"
                "text = path.read_text()\n"
                "old = 'def sample_weight(value):\\n    return value or 0\\n'\n"
                "new = 'def sample_weight(value):\\n    return value if value is not None else 1\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit step performs one exact source replacement using the observed current helper.",
            tags=("heldout", "edit", "exact_replacement"),
        ),
        CurriculumTask(
            task_id="heldout_test_narrow_import",
            skill="test",
            repo="toy/metricslib",
            problem_statement="Verify the missing-weight default with a narrow test before broader checks.",
            memory_hint=(
                "The prior successful verification used this exact node: "
                "tests/test_accumulator.py::test_missing_sample_weight_defaults_to_one. Copy it exactly."
            ),
            target_command="PYTHONPATH=src:. python -m pytest tests/test_accumulator.py::test_missing_sample_weight_defaults_to_one -q",
            expected_signal="A good test step runs the focused behavior test for the current bug.",
            tags=("heldout", "test", "focused_verification"),
        ),
        CurriculumTask(
            task_id="heldout_recover_stale_module",
            skill="locate",
            repo="toy/templatelib",
            problem_statement="The renderer still fails to escape braces inside nested template expressions.",
            memory_hint="A stale memory mentions template_old.py, but the renderer was moved after that fix.",
            current_evidence="find . -name '*render*.py' would reveal src/templatelib/render/engine.py.",
            target_command='rg -n "escape|brace|render|Template" src/templatelib tests',
            expected_signal="A good recovery step searches current renderer source instead of using template_old.py.",
            tags=("heldout", "locate", "stale_memory_recovery"),
        ),
    ]


def proxy_easy_curriculum_tasks() -> list[CurriculumTask]:
    """Return custom easy/self-suitable tasks for dynamic-call evaluation.

    These tasks are intentionally simpler than SWE-Bench repairs.  They measure
    whether the local model can choose a low-cost next command from explicit
    current evidence and a short memory hint.
    """
    return [
        CurriculumTask(
            task_id="proxy_easy_locate_timeout_config",
            skill="locate",
            repo="toy/netcfg",
            problem_statement="The timeout parser ignores the named timeout config helper after a module rename.",
            memory_hint="A previous fix began by searching for parse_timeout and TimeoutConfig in source and tests.",
            target_command='rg -n "parse_timeout|TimeoutConfig|timeout" src/netcfg tests',
            expected_signal="A good easy self-handle step locates the current timeout helper before editing.",
            tags=("proxy_easy", "locate", "self_suitable"),
        ),
        CurriculumTask(
            task_id="proxy_easy_edit_none_timeout",
            skill="edit",
            repo="toy/netcfg",
            problem_statement="The current helper treats an explicit timeout of 0 as missing.",
            memory_hint="Use the observed current helper and replace the truthiness fallback with an explicit None check.",
            current_evidence=(
                "src/netcfg/timeout.py:12:def normalize_timeout(value):\n"
                "src/netcfg/timeout.py:13:    return value or 30"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/netcfg/timeout.py')\n"
                "text = path.read_text()\n"
                "old = 'def normalize_timeout(value):\\n    return value or 30\\n'\n"
                "new = 'def normalize_timeout(value):\\n    return value if value is not None else 30\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good easy self-handle edit preserves explicit zero with an is-not-None guard.",
            tags=("proxy_easy", "edit", "self_suitable", "truthiness_default"),
        ),
        CurriculumTask(
            task_id="proxy_easy_test_timeout_node",
            skill="test",
            repo="toy/netcfg",
            problem_statement="Verify that explicit zero timeout is preserved with a focused regression test.",
            memory_hint=(
                "The prior successful check used this exact node: "
                "tests/test_timeout.py::test_zero_timeout_is_not_defaulted. Copy it exactly."
            ),
            target_command="PYTHONPATH=src:. python -m pytest tests/test_timeout.py::test_zero_timeout_is_not_defaulted -q",
            expected_signal="A good easy self-handle test runs the narrow timeout regression only.",
            tags=("proxy_easy", "test", "self_suitable", "focused_verification"),
        ),
        CurriculumTask(
            task_id="proxy_easy_edit_alias_return",
            skill="edit",
            repo="toy/colorcfg",
            problem_statement="The color mode helper still returns raw aliases instead of canonical names.",
            memory_hint="After reading the current helper, replace the raw return with COLOR_ALIASES.get(value, value).",
            current_evidence=(
                "src/colorcfg/modes.py:21:def normalize_color_mode(value):\n"
                "src/colorcfg/modes.py:22:    return value"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/colorcfg/modes.py')\n"
                "text = path.read_text()\n"
                "old = 'def normalize_color_mode(value):\\n    return value\\n'\n"
                "new = 'def normalize_color_mode(value):\\n    return COLOR_ALIASES.get(value, value)\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good easy self-handle edit performs one exact alias canonicalization replacement.",
            tags=("proxy_easy", "edit", "self_suitable", "exact_replacement"),
        ),
        CurriculumTask(
            task_id="proxy_easy_locate_stale_renderer_path",
            skill="locate",
            repo="toy/weblib",
            problem_statement="HTML escaping still fails after the renderer module was reorganized.",
            memory_hint="A stale memory mentions html_renderer_old.py, but the current code moved under src/weblib/render.",
            current_evidence="find . -name '*render*.py' would reveal src/weblib/render/html.py.",
            target_command='rg -n "escape_html|safe_html|Renderer|render" src/weblib tests',
            expected_signal="A good easy self-handle step searches current renderer code instead of the stale file.",
            tags=("proxy_easy", "locate", "self_suitable", "stale_memory_recovery"),
        ),
    ]


def challenge_curriculum_tasks() -> list[CurriculumTask]:
    """Return harder held-out tasks that require sharper current-source anchoring."""
    return [
        CurriculumTask(
            task_id="challenge_locate_async_retry",
            skill="locate",
            repo="toy/asynclib",
            problem_statement="Async retries ignore cancellation because the current retry helper was renamed.",
            memory_hint="A prior repair began by searching the active async retry helper, not the old retry.py path.",
            current_evidence="Project layout includes src/asynclib/retrying/ and tests/async_retry/.",
            target_command='rg -n "cancel|CancelledError|retry|RetryPolicy" src/asynclib tests/async_retry',
            expected_signal="A good locate step searches the active async retry package and tests.",
            tags=("challenge", "locate", "renamed_helper"),
        ),
        CurriculumTask(
            task_id="challenge_edit_guarded_replace",
            skill="edit",
            repo="toy/jsonlib",
            problem_statement="The decoder still mutates shared default options when caller options are omitted.",
            memory_hint="The earlier fix changed the current decode_options helper to copy DEFAULT_OPTIONS before mutation.",
            current_evidence=(
                "src/jsonlib/decoder.py:88:def decode_options(options=None):\n"
                "src/jsonlib/decoder.py:89:    opts = options or DEFAULT_OPTIONS\n"
                "src/jsonlib/decoder.py:90:    opts['strict'] = bool(opts.get('strict', True))"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/jsonlib/decoder.py')\n"
                "text = path.read_text()\n"
                "old = '    opts = options or DEFAULT_OPTIONS\\n'\n"
                "new = '    opts = dict(DEFAULT_OPTIONS if options is None else options)\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit step copies the default options with a one-line exact replacement.",
            tags=("challenge", "edit", "shared_mutable_default"),
        ),
        CurriculumTask(
            task_id="challenge_test_targeted_env",
            skill="test",
            repo="toy/jsonlib",
            problem_statement="Verify that decode_options no longer mutates DEFAULT_OPTIONS.",
            memory_hint=(
                "The prior successful check used PYTHONPATH=src:. with this exact decoder regression node: "
                "tests/decoder/test_options.py::test_decode_options_does_not_mutate_defaults. Copy it exactly."
            ),
            target_command="PYTHONPATH=src:. python -m pytest tests/decoder/test_options.py::test_decode_options_does_not_mutate_defaults -q",
            expected_signal="A good test step runs the narrow decoder regression test with local source import path.",
            tags=("challenge", "test", "local_import_path"),
        ),
        CurriculumTask(
            task_id="challenge_recover_deleted_file",
            skill="locate",
            repo="toy/urilib",
            problem_statement="URL joining drops query strings when the base URL ends with a slash.",
            memory_hint="A stale memory says url_helpers_old.py, but that file was deleted after the routing rewrite.",
            current_evidence="find . -name '*url*.py' would reveal src/urilib/parse/join.py and tests/test_join.py.",
            target_command='rg -n "join_url|query|base_url|urljoin|slash" src/urilib tests',
            expected_signal="A good recovery step searches current URI join code instead of the deleted helper.",
            tags=("challenge", "locate", "deleted_stale_file"),
        ),
    ]


def build_default_curriculum_records(*, repeat: int = 1, run_id: str = "hybrid-gym-mini-curriculum") -> list[dict[str, Any]]:
    if repeat < 1:
        raise ValueError("repeat must be >= 1")
    records: list[dict[str, Any]] = []
    for repeat_idx in range(repeat):
        for task in default_curriculum_tasks():
            record = task_to_record(task, run_id=run_id)
            if repeat > 1:
                record["instance_id"] = f"{task.task_id}_r{repeat_idx + 1:02d}"
                record["repeat_index"] = repeat_idx
            records.append(record)
    return records


def build_heldout_curriculum_records(*, run_id: str = "hybrid-gym-mini-heldout") -> list[dict[str, Any]]:
    return [task_to_record(task, run_id=run_id) for task in heldout_curriculum_tasks()]


def build_proxy_easy_curriculum_records(*, run_id: str = "hybrid-gym-proxy-easy") -> list[dict[str, Any]]:
    return [task_to_record(task, run_id=run_id) for task in proxy_easy_curriculum_tasks()]


def build_challenge_curriculum_records(*, run_id: str = "hybrid-gym-mini-challenge") -> list[dict[str, Any]]:
    return [task_to_record(task, run_id=run_id) for task in challenge_curriculum_tasks()]


def transition_curriculum_tasks() -> list[CurriculumTask]:
    """Return extra train-only variants for terse edit/test transition control."""
    return [
        CurriculumTask(
            task_id="transition_edit_copy_default_map",
            skill="edit",
            repo="toy/configlib",
            problem_statement="The loader still mutates the shared default mapping when caller overrides are absent.",
            memory_hint="Once the current helper line is observed, make the replacement immediately instead of diffing again.",
            current_evidence=(
                "src/configlib/loader.py:52:def load_options(options=None):\n"
                "src/configlib/loader.py:53:    opts = options or DEFAULT_OPTIONS\n"
                "src/configlib/loader.py:54:    opts['enabled'] = bool(opts.get('enabled', True))"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/configlib/loader.py')\n"
                "text = path.read_text()\n"
                "old = '    opts = options or DEFAULT_OPTIONS\\n'\n"
                "new = '    opts = dict(DEFAULT_OPTIONS if options is None else options)\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit step emits a complete command inside the action fence, with no empty fence.",
            tags=("transition", "edit", "shared_mutable_default", "empty_fence_repair"),
        ),
        CurriculumTask(
            task_id="transition_test_pytest_path",
            skill="test",
            repo="toy/configlib",
            problem_statement="Verify the default-options mutation regression with the narrow Python test.",
            memory_hint="The project is Python; use PYTHONPATH=src:. and pytest, not another language test runner.",
            target_command=(
                "PYTHONPATH=src:. python -m pytest "
                "tests/loader/test_options.py::test_load_options_does_not_mutate_defaults -q"
            ),
            expected_signal="A good test step runs the focused pytest regression with local source imports.",
            tags=("transition", "test", "pytest_runner", "focused_verification"),
        ),
        CurriculumTask(
            task_id="transition_edit_none_default_limit",
            skill="edit",
            repo="toy/ratelib",
            problem_statement="The limiter still treats an explicit zero limit as missing and falls back to the default.",
            memory_hint="The current source line is already observed; replace the truthiness check with an is-None check.",
            current_evidence=(
                "src/ratelib/limits.py:31:def normalize_limit(limit):\n"
                "src/ratelib/limits.py:32:    return limit or DEFAULT_LIMIT"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/ratelib/limits.py')\n"
                "text = path.read_text()\n"
                "old = 'def normalize_limit(limit):\\n    return limit or DEFAULT_LIMIT\\n'\n"
                "new = 'def normalize_limit(limit):\\n    return DEFAULT_LIMIT if limit is None else limit\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit step commits the exact observed-line replacement instead of searching again.",
            tags=("transition", "edit", "observed_evidence_to_edit", "truthiness_default"),
        ),
        CurriculumTask(
            task_id="transition_edit_copy_header_list",
            skill="edit",
            repo="toy/csvlib",
            problem_statement="The parser mutates the shared default header list across calls.",
            memory_hint="The earlier repair copied defaults before appending; do the same in the observed current helper.",
            current_evidence=(
                "src/csvlib/parser.py:64:def parse_headers(headers=None):\n"
                "src/csvlib/parser.py:65:    result = headers or DEFAULT_HEADERS\n"
                "src/csvlib/parser.py:66:    result.append('row_id')"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/csvlib/parser.py')\n"
                "text = path.read_text()\n"
                "old = '    result = headers or DEFAULT_HEADERS\\n'\n"
                "new = '    result = list(DEFAULT_HEADERS if headers is None else headers)\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit step copies the shared default list with one exact source replacement.",
            tags=("transition", "edit", "observed_evidence_to_edit", "mutable_default"),
        ),
        CurriculumTask(
            task_id="transition_edit_preserve_empty_string",
            skill="edit",
            repo="toy/authlib",
            problem_statement="The auth helper replaces an explicitly empty realm with the default realm.",
            memory_hint="Once the current return line is observed, preserve empty strings by checking for None.",
            current_evidence=(
                "src/authlib/challenge.py:23:def normalize_realm(realm):\n"
                "src/authlib/challenge.py:24:    return realm or DEFAULT_REALM"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/authlib/challenge.py')\n"
                "text = path.read_text()\n"
                "old = 'def normalize_realm(realm):\\n    return realm or DEFAULT_REALM\\n'\n"
                "new = 'def normalize_realm(realm):\\n    return DEFAULT_REALM if realm is None else realm\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit step uses current evidence to make the exact None-check replacement.",
            tags=("transition", "edit", "observed_evidence_to_edit", "truthiness_default"),
        ),
    ]


def build_transition_curriculum_records(*, repeat: int = 1, run_id: str = "hybrid-gym-mini-transition") -> list[dict[str, Any]]:
    if repeat < 1:
        raise ValueError("repeat must be >= 1")
    records: list[dict[str, Any]] = []
    for repeat_idx in range(repeat):
        for task in transition_curriculum_tasks():
            record = task_to_record(task, run_id=run_id)
            if repeat > 1:
                record["instance_id"] = f"{task.task_id}_r{repeat_idx + 1:02d}"
                record["repeat_index"] = repeat_idx
            records.append(record)
    return records


def extended_transition_curriculum_tasks() -> list[CurriculumTask]:
    """Return train-only variants for memory-conditioned next-action control."""
    return [
        CurriculumTask(
            task_id="extended_locate_stale_symbol_renamed",
            skill="locate",
            repo="toy/schedulerlib",
            problem_statement="Scheduled jobs still run twice when the dedupe helper was renamed after the old fix.",
            memory_hint="A stale memory mentions dedupe_old.py; first search the current scheduler code and tests.",
            current_evidence="Project layout includes src/schedulerlib/jobs/ and tests/jobs/.",
            target_command='rg -n "dedupe|duplicate|job_id|schedule" src/schedulerlib tests/jobs',
            expected_signal="A good locate step anchors on current source symbols before trusting the stale memory path.",
            tags=("extended_transition", "locate", "stale_memory_recovery", "renamed_symbol"),
        ),
        CurriculumTask(
            task_id="extended_locate_import_moved_helper",
            skill="locate",
            repo="toy/tablelib",
            problem_statement="CSV table parsing still drops quoted separators after the tokenizer moved packages.",
            memory_hint="The prior repair searched tokenizer symbols instead of opening the obsolete csv_parser.py file.",
            current_evidence="find . -name '*token*.py' would reveal src/tablelib/parse/tokenizer.py.",
            target_command='rg -n "tokenize|separator|quote|csv" src/tablelib tests',
            expected_signal="A good locate step searches the active tokenizer package and related tests.",
            tags=("extended_transition", "locate", "moved_helper", "memory_to_current_source"),
        ),
        CurriculumTask(
            task_id="extended_edit_copy_nested_default",
            skill="edit",
            repo="toy/requestlib",
            problem_statement="The request builder mutates nested default headers when caller headers are omitted.",
            memory_hint="Once the current helper line is observed, copy the default mapping before mutation.",
            current_evidence=(
                "src/requestlib/builder.py:72:def normalize_headers(headers=None):\n"
                "src/requestlib/builder.py:73:    out = headers or DEFAULT_HEADERS\n"
                "src/requestlib/builder.py:74:    out['accept'] = out.get('accept', '*/*')"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/requestlib/builder.py')\n"
                "text = path.read_text()\n"
                "old = '    out = headers or DEFAULT_HEADERS\\n'\n"
                "new = '    out = dict(DEFAULT_HEADERS if headers is None else headers)\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit step commits the exact observed replacement without emitting an empty fence.",
            tags=("extended_transition", "edit", "mutable_default", "observed_evidence_to_edit"),
        ),
        CurriculumTask(
            task_id="extended_edit_preserve_zero_timeout",
            skill="edit",
            repo="toy/httplib",
            problem_statement="The HTTP client treats an explicit zero timeout as missing and restores the default.",
            memory_hint="The current evidence is enough; replace the truthiness default with an is-None check.",
            current_evidence=(
                "src/httplib/client.py:39:def normalize_timeout(timeout):\n"
                "src/httplib/client.py:40:    return timeout or DEFAULT_TIMEOUT"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/httplib/client.py')\n"
                "text = path.read_text()\n"
                "old = 'def normalize_timeout(timeout):\\n    return timeout or DEFAULT_TIMEOUT\\n'\n"
                "new = 'def normalize_timeout(timeout):\\n    return DEFAULT_TIMEOUT if timeout is None else timeout\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit step preserves explicit zero values with a minimal source replacement.",
            tags=("extended_transition", "edit", "truthiness_default", "observed_evidence_to_edit"),
        ),
        CurriculumTask(
            task_id="extended_edit_preserve_empty_collection",
            skill="edit",
            repo="toy/filterlib",
            problem_statement="The filter helper replaces an explicitly empty allowlist with the default allowlist.",
            memory_hint="The observed helper line should be edited directly; do not rerun broad search first.",
            current_evidence=(
                "src/filterlib/rules.py:18:def normalize_allowlist(values):\n"
                "src/filterlib/rules.py:19:    return values or DEFAULT_ALLOWLIST"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/filterlib/rules.py')\n"
                "text = path.read_text()\n"
                "old = 'def normalize_allowlist(values):\\n    return values or DEFAULT_ALLOWLIST\\n'\n"
                "new = 'def normalize_allowlist(values):\\n    return DEFAULT_ALLOWLIST if values is None else values\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit step uses current evidence to preserve explicit empty collections.",
            tags=("extended_transition", "edit", "truthiness_default", "observed_evidence_to_edit"),
        ),
        CurriculumTask(
            task_id="extended_test_python_narrow_env",
            skill="test",
            repo="toy/requestlib",
            problem_statement="Verify the nested default-header regression with one focused Python test.",
            memory_hint="The prior successful check used pytest with PYTHONPATH=src:.; do not use a Go or JS runner.",
            target_command=(
                "PYTHONPATH=src:. python -m pytest "
                "tests/builder/test_headers.py::test_normalize_headers_does_not_mutate_defaults -q"
            ),
            expected_signal="A good test step runs the narrow pytest target with local source imports.",
            tags=("extended_transition", "test", "pytest_runner", "focused_verification"),
        ),
        CurriculumTask(
            task_id="extended_test_current_package_path",
            skill="test",
            repo="toy/schedulerlib",
            problem_statement="Verify duplicate scheduled jobs are suppressed with the current package layout.",
            memory_hint="The active regression test lives under tests/jobs, not the stale tests/test_old_scheduler.py path.",
            target_command="PYTHONPATH=src:. python -m pytest tests/jobs/test_dedupe.py::test_duplicate_job_id_runs_once -q",
            expected_signal="A good test step uses the current focused test path rather than a stale memory path.",
            tags=("extended_transition", "test", "stale_memory_recovery", "focused_verification"),
        ),
    ]


def build_extended_transition_curriculum_records(
    *, repeat: int = 1, run_id: str = "hybrid-gym-mini-extended-transition"
) -> list[dict[str, Any]]:
    if repeat < 1:
        raise ValueError("repeat must be >= 1")
    records: list[dict[str, Any]] = []
    for repeat_idx in range(repeat):
        for task in extended_transition_curriculum_tasks():
            record = task_to_record(task, run_id=run_id)
            if repeat > 1:
                record["instance_id"] = f"{task.task_id}_r{repeat_idx + 1:02d}"
                record["repeat_index"] = repeat_idx
            records.append(record)
    return records


def semantic_guard_curriculum_tasks() -> list[CurriculumTask]:
    """Return train-only guard tasks for exact semantic edits and test targets."""
    return [
        CurriculumTask(
            task_id="semantic_edit_none_weight_guard",
            skill="edit",
            repo="toy/scoringlib",
            problem_statement="The scorer must preserve explicit zero weights instead of replacing them with defaults.",
            memory_hint="A similar repair failed when it used value or 1; use an explicit None check in the observed helper.",
            current_evidence=(
                "src/scoringlib/weights.py:27:def normalize_weight(weight):\n"
                "src/scoringlib/weights.py:28:    return weight or DEFAULT_WEIGHT"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/scoringlib/weights.py')\n"
                "text = path.read_text()\n"
                "old = 'def normalize_weight(weight):\\n    return weight or DEFAULT_WEIGHT\\n'\n"
                "new = 'def normalize_weight(weight):\\n    return DEFAULT_WEIGHT if weight is None else weight\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit step uses an explicit None check and preserves explicit zero values.",
            tags=("semantic_guard", "edit", "none_check", "truthiness_default_repair"),
        ),
        CurriculumTask(
            task_id="semantic_edit_none_sample_guard",
            skill="edit",
            repo="toy/statlib",
            problem_statement="The sampler must preserve an explicit empty sample list instead of falling back to defaults.",
            memory_hint="The exact replacement should check for None; using samples or DEFAULT_SAMPLES is semantically wrong.",
            current_evidence=(
                "src/statlib/samples.py:33:def normalize_samples(samples):\n"
                "src/statlib/samples.py:34:    return samples or DEFAULT_SAMPLES"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/statlib/samples.py')\n"
                "text = path.read_text()\n"
                "old = 'def normalize_samples(samples):\\n    return samples or DEFAULT_SAMPLES\\n'\n"
                "new = 'def normalize_samples(samples):\\n    return DEFAULT_SAMPLES if samples is None else samples\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit step does not use a truthiness default when explicit empty values are meaningful.",
            tags=("semantic_guard", "edit", "none_check", "truthiness_default_repair"),
        ),
        CurriculumTask(
            task_id="semantic_edit_none_options_guard",
            skill="edit",
            repo="toy/formatlib",
            problem_statement="The formatter mutates default options and also treats an empty options dict as missing.",
            memory_hint="Copy the default options only when options is None; preserve explicit empty dictionaries.",
            current_evidence=(
                "src/formatlib/options.py:45:def normalize_options(options=None):\n"
                "src/formatlib/options.py:46:    opts = options or DEFAULT_OPTIONS\n"
                "src/formatlib/options.py:47:    opts['compact'] = bool(opts.get('compact', False))"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/formatlib/options.py')\n"
                "text = path.read_text()\n"
                "old = '    opts = options or DEFAULT_OPTIONS\\n'\n"
                "new = '    opts = dict(DEFAULT_OPTIONS if options is None else options)\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit step both copies defaults and uses options is None rather than truthiness.",
            tags=("semantic_guard", "edit", "none_check", "mutable_default"),
        ),
        CurriculumTask(
            task_id="semantic_test_exact_accumulator_path",
            skill="test",
            repo="toy/scoringlib",
            problem_statement="Verify the explicit-zero weight regression with the current focused Python test.",
            memory_hint="Do not invent a nearby test path; use the exact current test node from the repair memory.",
            target_command=(
                "PYTHONPATH=src:. python -m pytest "
                "tests/weights/test_normalize.py::test_explicit_zero_weight_is_preserved -q"
            ),
            expected_signal="A good test step uses the exact focused pytest node, not a plausible renamed path.",
            tags=("semantic_guard", "test", "exact_test_target", "focused_verification"),
        ),
        CurriculumTask(
            task_id="semantic_test_exact_decoder_path",
            skill="test",
            repo="toy/formatlib",
            problem_statement="Verify the options normalizer does not mutate defaults.",
            memory_hint="The exact regression lives in tests/options/test_normalize.py; avoid approximate package paths.",
            target_command=(
                "PYTHONPATH=src:. python -m pytest "
                "tests/options/test_normalize.py::test_normalize_options_does_not_mutate_defaults -q"
            ),
            expected_signal="A good test step preserves the exact focused test path and test name.",
            tags=("semantic_guard", "test", "exact_test_target", "focused_verification"),
        ),
    ]


def semantic_contrast_curriculum_tasks() -> list[CurriculumTask]:
    """Return train-only contrast tasks for strict semantic action choices."""
    return [
        CurriculumTask(
            task_id="semantic_contrast_edit_timeout_none",
            skill="edit",
            repo="toy/netlib",
            problem_statement="The request helper must preserve an explicit timeout of 0 instead of using the default.",
            memory_hint=(
                "A previous repair regressed because it used timeout or DEFAULT_TIMEOUT; the observed helper needs "
                "an explicit None check."
            ),
            current_evidence=(
                "src/netlib/options.py:21:def normalize_timeout(timeout):\n"
                "src/netlib/options.py:22:    return timeout or DEFAULT_TIMEOUT"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/netlib/options.py')\n"
                "text = path.read_text()\n"
                "old = 'def normalize_timeout(timeout):\\n    return timeout or DEFAULT_TIMEOUT\\n'\n"
                "new = 'def normalize_timeout(timeout):\\n    return timeout if timeout is not None else DEFAULT_TIMEOUT\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit preserves explicit zero by using timeout is not None.",
            tags=("semantic_contrast", "edit", "none_check", "truthiness_default_repair"),
        ),
        CurriculumTask(
            task_id="semantic_contrast_edit_empty_patterns",
            skill="edit",
            repo="toy/searchlib",
            problem_statement="The filter helper must preserve an explicit empty pattern list.",
            memory_hint="Do not collapse empty lists with patterns or DEFAULT_PATTERNS; only None means missing.",
            current_evidence=(
                "src/searchlib/filters.py:38:def normalize_patterns(patterns):\n"
                "src/searchlib/filters.py:39:    return patterns or DEFAULT_PATTERNS"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/searchlib/filters.py')\n"
                "text = path.read_text()\n"
                "old = 'def normalize_patterns(patterns):\\n    return patterns or DEFAULT_PATTERNS\\n'\n"
                "new = 'def normalize_patterns(patterns):\\n    return DEFAULT_PATTERNS if patterns is None else patterns\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit keeps explicit empty lists distinct from missing values.",
            tags=("semantic_contrast", "edit", "none_check", "truthiness_default_repair"),
        ),
        CurriculumTask(
            task_id="semantic_contrast_edit_mutable_headers",
            skill="edit",
            repo="toy/httplib",
            problem_statement="The header normalizer mutates shared defaults and treats an empty header dict as missing.",
            memory_hint="Copy defaults only when headers is None; preserve explicit empty dictionaries.",
            current_evidence=(
                "src/httplib/headers.py:52:def normalize_headers(headers=None):\n"
                "src/httplib/headers.py:53:    result = headers or DEFAULT_HEADERS\n"
                "src/httplib/headers.py:54:    result['agent'] = result.get('agent', 'mini')"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/httplib/headers.py')\n"
                "text = path.read_text()\n"
                "old = '    result = headers or DEFAULT_HEADERS\\n'\n"
                "new = '    result = dict(DEFAULT_HEADERS if headers is None else headers)\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit avoids both truthiness defaults and shared mutable defaults.",
            tags=("semantic_contrast", "edit", "none_check", "mutable_default"),
        ),
        CurriculumTask(
            task_id="semantic_contrast_test_exact_timeout_node",
            skill="test",
            repo="toy/netlib",
            problem_statement="Verify explicit timeout zero is preserved with the current focused test.",
            memory_hint=(
                "Use the exact pytest node from current evidence; nearby files like tests/test_options.py are stale."
            ),
            target_command=(
                "PYTHONPATH=src:. python -m pytest "
                "tests/request/test_timeout_options.py::test_explicit_zero_timeout_is_preserved -q"
            ),
            expected_signal="A good test step copies the exact focused pytest target.",
            tags=("semantic_contrast", "test", "exact_test_target", "focused_verification"),
        ),
        CurriculumTask(
            task_id="semantic_contrast_test_exact_headers_node",
            skill="test",
            repo="toy/httplib",
            problem_statement="Verify default headers are not mutated by normalization.",
            memory_hint="The exact regression node is under tests/headers; avoid plausible options-path aliases.",
            target_command=(
                "PYTHONPATH=src:. python -m pytest "
                "tests/headers/test_normalize_headers.py::test_default_headers_are_not_mutated -q"
            ),
            expected_signal="A good test step preserves the exact test file and node name.",
            tags=("semantic_contrast", "test", "exact_test_target", "focused_verification"),
        ),
        CurriculumTask(
            task_id="semantic_contrast_test_exact_patterns_node",
            skill="test",
            repo="toy/searchlib",
            problem_statement="Verify an explicit empty pattern list does not fall back to defaults.",
            memory_hint="Copy the current focused node exactly; do not shorten it to the package-level test file.",
            target_command=(
                "PYTHONPATH=src:. python -m pytest "
                "tests/filters/test_patterns.py::test_empty_patterns_are_preserved -q"
            ),
            expected_signal="A good test step uses the exact focused regression node.",
            tags=("semantic_contrast", "test", "exact_test_target", "focused_verification"),
        ),
    ]


def semantic_variant_curriculum_tasks() -> list[CurriculumTask]:
    """Return broader train-only variants for literal defaults and exact tests."""
    return [
        CurriculumTask(
            task_id="semantic_variant_edit_literal_limit",
            skill="edit",
            repo="toy/ratelib",
            problem_statement="The limiter must preserve an explicit zero limit instead of using the fallback limit.",
            memory_hint="The failed pattern is changing one truthiness fallback into another; use an explicit None guard.",
            current_evidence=(
                "src/ratelib/limits.py:19:def normalize_limit(value):\n"
                "src/ratelib/limits.py:20:    return value or 0"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/ratelib/limits.py')\n"
                "text = path.read_text()\n"
                "old = 'def normalize_limit(value):\\n    return value or 0\\n'\n"
                "new = 'def normalize_limit(value):\\n    return value if value is not None else 10\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit uses the literal fallback only in the None branch.",
            tags=("semantic_variant", "edit", "none_check", "literal_default"),
        ),
        CurriculumTask(
            task_id="semantic_variant_edit_literal_retry",
            skill="edit",
            repo="toy/retrylib",
            problem_statement="The retry helper must preserve an explicit retry count of zero.",
            memory_hint="Do not write count or 3; the replacement must use count is not None.",
            current_evidence=(
                "src/retrylib/config.py:12:def retry_count(count):\n"
                "src/retrylib/config.py:13:    return count or 1"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/retrylib/config.py')\n"
                "text = path.read_text()\n"
                "old = 'def retry_count(count):\\n    return count or 1\\n'\n"
                "new = 'def retry_count(count):\\n    return count if count is not None else 3\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit preserves explicit zero retry counts.",
            tags=("semantic_variant", "edit", "none_check", "literal_default"),
        ),
        CurriculumTask(
            task_id="semantic_variant_edit_prefix_branch",
            skill="edit",
            repo="toy/pathlibx",
            problem_statement="The path helper must preserve an explicit empty prefix.",
            memory_hint="The branch can put the default first, but only when prefix is None.",
            current_evidence=(
                "src/pathlibx/names.py:28:def normalize_prefix(prefix):\n"
                "src/pathlibx/names.py:29:    return prefix or 'item'"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/pathlibx/names.py')\n"
                "text = path.read_text()\n"
                "old = \"def normalize_prefix(prefix):\\n    return prefix or 'item'\\n\"\n"
                "new = \"def normalize_prefix(prefix):\\n    return 'item' if prefix is None else prefix\\n\"\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit preserves explicit empty strings while keeping the default for None.",
            tags=("semantic_variant", "edit", "none_check", "literal_default"),
        ),
        CurriculumTask(
            task_id="semantic_variant_edit_mutable_accumulator",
            skill="edit",
            repo="toy/eventlib",
            problem_statement="The event accumulator mutates shared default options and treats an empty dict as missing.",
            memory_hint="Copy defaults only for None; an empty dict is explicit current evidence.",
            current_evidence=(
                "src/eventlib/options.py:44:def normalize_options(options=None):\n"
                "src/eventlib/options.py:45:    opts = options or DEFAULT_OPTIONS\n"
                "src/eventlib/options.py:46:    opts['mode'] = opts.get('mode', 'safe')"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/eventlib/options.py')\n"
                "text = path.read_text()\n"
                "old = '    opts = options or DEFAULT_OPTIONS\\n'\n"
                "new = '    opts = dict(DEFAULT_OPTIONS if options is None else options)\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit handles both the None guard and mutable default copy.",
            tags=("semantic_variant", "edit", "none_check", "mutable_default"),
        ),
        CurriculumTask(
            task_id="semantic_variant_test_exact_metric_node",
            skill="test",
            repo="toy/ratelib",
            problem_statement="Verify the literal limit fallback with the focused test node.",
            memory_hint="Copy the exact pytest target; do not substitute a nearby test_metrics path.",
            target_command=(
                "PYTHONPATH=src:. python -m pytest "
                "tests/rates/test_limits.py::test_zero_limit_is_preserved -q"
            ),
            expected_signal="A good test step preserves the exact focused pytest node.",
            tags=("semantic_variant", "test", "exact_test_target", "focused_verification"),
        ),
        CurriculumTask(
            task_id="semantic_variant_test_exact_accumulator_node",
            skill="test",
            repo="toy/eventlib",
            problem_statement="Verify option normalization does not mutate default options.",
            memory_hint="The exact node is under tests/events; avoid similar accumulator or options names.",
            target_command=(
                "PYTHONPATH=src:. python -m pytest "
                "tests/events/test_options.py::test_normalize_options_does_not_mutate_defaults -q"
            ),
            expected_signal="A good test step uses the exact current test file and test function.",
            tags=("semantic_variant", "test", "exact_test_target", "focused_verification"),
        ),
        CurriculumTask(
            task_id="semantic_variant_test_exact_retry_node",
            skill="test",
            repo="toy/retrylib",
            problem_statement="Verify an explicit retry count of zero is preserved.",
            memory_hint="Use the exact node from memory, including the retry_count function name.",
            target_command=(
                "PYTHONPATH=src:. python -m pytest "
                "tests/config/test_retry_count.py::test_zero_retry_count_is_not_defaulted -q"
            ),
            expected_signal="A good test step copies the exact pytest node.",
            tags=("semantic_variant", "test", "exact_test_target", "focused_verification"),
        ),
        CurriculumTask(
            task_id="semantic_variant_test_exact_prefix_node",
            skill="test",
            repo="toy/pathlibx",
            problem_statement="Verify an explicit empty prefix does not fall back to the default.",
            memory_hint="Do not shorten to tests/test_names.py; run the exact focused regression node.",
            target_command=(
                "PYTHONPATH=src:. python -m pytest "
                "tests/names/test_prefix.py::test_empty_prefix_is_preserved -q"
            ),
            expected_signal="A good test step uses the exact focused regression node.",
            tags=("semantic_variant", "test", "exact_test_target", "focused_verification"),
        ),
    ]


def semantic_rule_curriculum_tasks() -> list[CurriculumTask]:
    """Return train-only rule tasks for semantic guards and exact test copying.

    These tasks intentionally avoid the held-out/challenge package and test
    names while targeting the v8 failure family: replacing one truthiness
    fallback with another, and inventing a plausible pytest node instead of
    copying the exact focused target.
    """
    return [
        CurriculumTask(
            task_id="semantic_rule_edit_value_or_zero",
            skill="edit",
            repo="toy/scoreboard",
            problem_statement="The point normalizer must preserve explicit zero points while using 1 only for missing values.",
            memory_hint=(
                "A bad repair changed one truthiness fallback into another, such as value or 1. "
                "The rule is: keep explicit zero, and put the fallback only in the None branch."
            ),
            current_evidence=(
                "src/scoreboard/points.py:17:def normalize_points(value):\n"
                "src/scoreboard/points.py:18:    return value or 0"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/scoreboard/points.py')\n"
                "text = path.read_text()\n"
                "old = 'def normalize_points(value):\\n    return value or 0\\n'\n"
                "new = 'def normalize_points(value):\\n    return 1 if value is None else value\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit never uses value or 1 when explicit zero must be preserved.",
            tags=("semantic_rule", "edit", "none_check", "truthiness_default_repair", "anti_or_fallback"),
        ),
        CurriculumTask(
            task_id="semantic_rule_edit_limit_literal",
            skill="edit",
            repo="toy/windowlib",
            problem_statement="The window limit helper must preserve a zero limit while falling back to 5 only when missing.",
            memory_hint="Do not output limit or 5. Use an explicit is-None branch that preserves zero.",
            current_evidence=(
                "src/windowlib/limits.py:24:def normalize_limit(limit):\n"
                "src/windowlib/limits.py:25:    return limit or 0"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/windowlib/limits.py')\n"
                "text = path.read_text()\n"
                "old = 'def normalize_limit(limit):\\n    return limit or 0\\n'\n"
                "new = 'def normalize_limit(limit):\\n    return limit if limit is not None else 5\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit changes truthiness fallback into an explicit None guard.",
            tags=("semantic_rule", "edit", "none_check", "truthiness_default_repair", "anti_or_fallback"),
        ),
        CurriculumTask(
            task_id="semantic_rule_edit_empty_label",
            skill="edit",
            repo="toy/labellib",
            problem_statement="The label helper must preserve an explicit empty label instead of replacing it with the default.",
            memory_hint="An empty string is explicit. Only None should become the default label.",
            current_evidence=(
                "src/labellib/names.py:31:def normalize_label(label):\n"
                "src/labellib/names.py:32:    return label or 'untitled'"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/labellib/names.py')\n"
                "text = path.read_text()\n"
                "old = \"def normalize_label(label):\\n    return label or 'untitled'\\n\"\n"
                "new = \"def normalize_label(label):\\n    return 'untitled' if label is None else label\\n\"\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit preserves explicit empty strings with an is-None default branch.",
            tags=("semantic_rule", "edit", "none_check", "truthiness_default_repair", "anti_or_fallback"),
        ),
        CurriculumTask(
            task_id="semantic_rule_edit_empty_mapping",
            skill="edit",
            repo="toy/tablelib",
            problem_statement="The table options helper must preserve an empty mapping and avoid mutating shared defaults.",
            memory_hint="Copy defaults only when options is None; an empty dict is a real user choice.",
            current_evidence=(
                "src/tablelib/options.py:39:def normalize_options(options=None):\n"
                "src/tablelib/options.py:40:    opts = options or DEFAULT_OPTIONS\n"
                "src/tablelib/options.py:41:    opts['border'] = opts.get('border', False)"
            ),
            target_command=(
                "python - <<'PY'\n"
                "from pathlib import Path\n"
                "path = Path('src/tablelib/options.py')\n"
                "text = path.read_text()\n"
                "old = '    opts = options or DEFAULT_OPTIONS\\n'\n"
                "new = '    opts = dict(DEFAULT_OPTIONS if options is None else options)\\n'\n"
                "assert old in text\n"
                "path.write_text(text.replace(old, new, 1))\n"
                "PY"
            ),
            expected_signal="A good edit combines an explicit None guard with a defensive default copy.",
            tags=("semantic_rule", "edit", "none_check", "mutable_default", "anti_or_fallback"),
        ),
        CurriculumTask(
            task_id="semantic_rule_test_copy_exact_points",
            skill="test",
            repo="toy/scoreboard",
            problem_statement="Verify zero points are preserved with the exact current regression test.",
            memory_hint=(
                "The exact pytest target is part of the memory. Do not rename points to weights, "
                "do not invent test_missing_points, and do not shorten the node."
            ),
            target_command=(
                "PYTHONPATH=src:. python -m pytest "
                "tests/points/test_normalize_points.py::test_explicit_zero_points_are_preserved -q"
            ),
            expected_signal="A good test step copies the focused pytest file and function exactly.",
            tags=("semantic_rule", "test", "exact_test_target", "focused_verification", "copy_exact_node"),
        ),
        CurriculumTask(
            task_id="semantic_rule_test_copy_exact_window",
            skill="test",
            repo="toy/windowlib",
            problem_statement="Verify zero window limits are preserved.",
            memory_hint="Run the exact node under tests/windows; plausible tests/limits aliases are stale.",
            target_command=(
                "PYTHONPATH=src:. python -m pytest "
                "tests/windows/test_limits.py::test_zero_window_limit_is_preserved -q"
            ),
            expected_signal="A good test step does not approximate the pytest node.",
            tags=("semantic_rule", "test", "exact_test_target", "focused_verification", "copy_exact_node"),
        ),
        CurriculumTask(
            task_id="semantic_rule_test_copy_exact_label",
            skill="test",
            repo="toy/labellib",
            problem_statement="Verify an explicit empty label is preserved.",
            memory_hint="Keep the test path and function text exactly as provided.",
            target_command=(
                "PYTHONPATH=src:. python -m pytest "
                "tests/labels/test_names.py::test_empty_label_is_not_defaulted -q"
            ),
            expected_signal="A good test step preserves the exact focused regression node.",
            tags=("semantic_rule", "test", "exact_test_target", "focused_verification", "copy_exact_node"),
        ),
        CurriculumTask(
            task_id="semantic_rule_test_copy_exact_table",
            skill="test",
            repo="toy/tablelib",
            problem_statement="Verify table options do not mutate shared defaults.",
            memory_hint="Use the exact tests/table_options node rather than a nearby options test.",
            target_command=(
                "PYTHONPATH=src:. python -m pytest "
                "tests/table_options/test_normalize.py::test_default_options_are_not_mutated -q"
            ),
            expected_signal="A good test step copies the exact current pytest node.",
            tags=("semantic_rule", "test", "exact_test_target", "focused_verification", "copy_exact_node"),
        ),
    ]


def generated_semantic_rule_curriculum_tasks() -> list[CurriculumTask]:
    """Return deterministic, train-only semantic-rule variants.

    v9 showed that a few hand-written rule examples still overfit: the model
    learned the train set but preserved neither the None-branch rule nor exact
    pytest-node copying on heldout names. These variants expand the same rule
    families with many unrelated names while avoiding heldout/challenge package
    and test paths.
    """
    edit_specs = [
        ("quota", "quota", "0", "3", "explicit zero quota", "src/quotalib/rules.py", "normalize_quota"),
        ("depth", "depth", "0", "2", "explicit zero depth", "src/treeopts/depth.py", "normalize_depth"),
        ("delay", "delay", "0", "10", "explicit zero delay", "src/timerules/delay.py", "normalize_delay"),
        ("tries", "tries", "0", "4", "explicit zero retry count", "src/retryopts/tries.py", "normalize_tries"),
        ("priority", "priority", "0", "5", "explicit zero priority", "src/queueopts/priority.py", "normalize_priority"),
        ("offset", "offset", "0", "12", "explicit zero offset", "src/pageopts/offset.py", "normalize_offset"),
        ("budget", "budget", "0", "100", "explicit zero budget", "src/budgetopts/limits.py", "normalize_budget"),
        ("rank", "rank", "0", "9", "explicit zero rank", "src/rankopts/order.py", "normalize_rank"),
        ("suffix", "suffix", "''", "'default'", "explicit empty suffix", "src/nameopts/suffix.py", "normalize_suffix"),
        ("title", "title", "''", "'untitled'", "explicit empty title", "src/titleopts/text.py", "normalize_title"),
        ("token", "token", "''", "'anon'", "explicit empty token", "src/authopts/token.py", "normalize_token"),
        ("marker", "marker", "''", "'MISSING'", "explicit empty marker", "src/markopts/marker.py", "normalize_marker"),
    ]
    tasks: list[CurriculumTask] = []
    for idx, (task_name, var, old_default, new_default, explicit_case, path, func) in enumerate(edit_specs, start=1):
        line_no = 20 + idx
        old_source = f"def {func}({var}):\n    return {var} or {old_default}\n"
        new_source = f"def {func}({var}):\n    return {var} if {var} is not None else {new_default}\n"
        tasks.append(
            CurriculumTask(
                task_id=f"generated_semantic_edit_{task_name}",
                skill="edit",
                repo=f"toy/{task_name}lib",
                problem_statement=(
                    f"The helper must preserve {explicit_case}; only a missing None value should use the default."
                ),
                memory_hint=(
                    f"Do not repair `{var} or {new_default}`. The current line is a truthiness fallback, "
                    "so rewrite it as an explicit None branch that preserves falsy user values."
                ),
                current_evidence=(
                    f"{path}:{line_no}:def {func}({var}):\n"
                    f"{path}:{line_no + 1}:    return {var} or {old_default}"
                ),
                target_command=(
                    "python - <<'PY'\n"
                    "from pathlib import Path\n"
                    f"path = Path('{path}')\n"
                    "text = path.read_text()\n"
                    f"old = {old_source!r}\n"
                    f"new = {new_source!r}\n"
                    "assert old in text\n"
                    "path.write_text(text.replace(old, new, 1))\n"
                    "PY"
                ),
                expected_signal="A good edit converts truthiness fallback into an explicit None branch.",
                tags=("generated_semantic_rule", "edit", "none_check", "anti_or_fallback"),
            )
        )

    mapping_specs = [
        ("palette", "settings", "DEFAULT_PALETTE", "src/paletteopts/settings.py", "normalize_palette"),
        ("button", "options", "DEFAULT_BUTTON_OPTIONS", "src/buttonopts/options.py", "normalize_button_options"),
        ("column", "config", "DEFAULT_COLUMNS", "src/columnopts/config.py", "normalize_columns"),
        ("view", "params", "DEFAULT_VIEW_PARAMS", "src/viewopts/params.py", "normalize_view_params"),
    ]
    for idx, (task_name, var, default_name, path, func) in enumerate(mapping_specs, start=1):
        line_no = 60 + idx
        tasks.append(
            CurriculumTask(
                task_id=f"generated_semantic_edit_mapping_{task_name}",
                skill="edit",
                repo=f"toy/{task_name}lib",
                problem_statement=(
                    "The helper must preserve an explicit empty mapping and must not mutate shared defaults."
                ),
                memory_hint=(
                    f"`{var} or {default_name}` is wrong because an empty dict is explicit. "
                    "Copy the selected mapping after checking whether the argument is None."
                ),
                current_evidence=(
                    f"{path}:{line_no}:def {func}({var}=None):\n"
                    f"{path}:{line_no + 1}:    opts = {var} or {default_name}\n"
                    f"{path}:{line_no + 2}:    opts['enabled'] = opts.get('enabled', True)"
                ),
                target_command=(
                    "python - <<'PY'\n"
                    "from pathlib import Path\n"
                    f"path = Path('{path}')\n"
                    "text = path.read_text()\n"
                    f"old = '    opts = {var} or {default_name}\\n'\n"
                    f"new = '    opts = dict({default_name} if {var} is None else {var})\\n'\n"
                    "assert old in text\n"
                    "path.write_text(text.replace(old, new, 1))\n"
                    "PY"
                ),
                expected_signal="A good edit preserves explicit empty mappings and defensively copies defaults.",
                tags=("generated_semantic_rule", "edit", "none_check", "mutable_default", "anti_or_fallback"),
            )
        )

    test_specs = [
        ("quota", "tests/quotas/test_rules.py::test_zero_quota_is_preserved"),
        ("depth", "tests/tree_depth/test_options.py::test_zero_depth_is_not_defaulted"),
        ("delay", "tests/delays/test_normalize.py::test_zero_delay_is_valid"),
        ("tries", "tests/retry_counts/test_tries.py::test_zero_tries_is_preserved"),
        ("priority", "tests/priorities/test_order.py::test_zero_priority_is_not_defaulted"),
        ("offset", "tests/pagination/test_offsets.py::test_zero_offset_is_respected"),
        ("budget", "tests/budgets/test_limits.py::test_zero_budget_is_preserved"),
        ("rank", "tests/ranking/test_rank.py::test_zero_rank_is_valid"),
        ("suffix", "tests/naming/test_suffix.py::test_empty_suffix_is_preserved"),
        ("title", "tests/titles/test_text.py::test_empty_title_is_not_defaulted"),
        ("token", "tests/auth_tokens/test_token.py::test_empty_token_is_preserved"),
        ("marker", "tests/markers/test_marker.py::test_empty_marker_is_valid"),
        ("palette", "tests/palette_options/test_settings.py::test_empty_palette_settings_are_preserved"),
        ("button", "tests/button_options/test_options.py::test_default_button_options_are_not_mutated"),
        ("column", "tests/column_config/test_columns.py::test_empty_column_config_is_preserved"),
        ("view", "tests/view_params/test_params.py::test_default_view_params_are_not_mutated"),
    ]
    for task_name, node in test_specs:
        tasks.append(
            CurriculumTask(
                task_id=f"generated_semantic_test_{task_name}",
                skill="test",
                repo=f"toy/{task_name}lib",
                problem_statement="Run the exact focused regression test; nearby file names are stale distractors.",
                memory_hint=(
                    f"Exact pytest node to copy: {node}. Do not rename directories, do not substitute a similar "
                    "function name, and keep PYTHONPATH=src:."
                ),
                target_command=f"PYTHONPATH=src:. python -m pytest {node} -q",
                expected_signal="A good test step copies the exact focused pytest node from memory.",
                tags=("generated_semantic_rule", "test", "exact_test_target", "focused_verification", "copy_exact_node"),
            )
        )
    return tasks


def string_none_guard_curriculum_tasks() -> list[CurriculumTask]:
    """Return targeted repairs for string/falsey defaults.

    v11 fixed the quote-safe replacement template but still sometimes keeps a
    truthiness fallback in the non-None branch, e.g. ``code if code is not None
    else code or 'NA'``. These tasks train the general rule: after detecting
    None explicitly, preserve the user-supplied value unchanged.
    """
    specs = [
        ("code", "code", "''", "'NA'", "src/codeopts/code.py", "normalize_code"),
        ("slug", "slug", "''", "'missing'", "src/slugopts/slug.py", "normalize_slug"),
        ("alias", "alias", "''", "'anonymous'", "src/aliasopts/name.py", "normalize_alias"),
        ("caption", "caption", "''", "'untitled'", "src/captionopts/text.py", "normalize_caption"),
        ("flag", "flag", "False", "True", "src/flagopts/flag.py", "normalize_flag"),
        ("count", "count", "0", "11", "src/countopts/count.py", "normalize_count"),
    ]
    tasks: list[CurriculumTask] = []
    for idx, (task_name, var, old_default, new_default, path, func) in enumerate(specs, start=1):
        line_no = 90 + idx
        old_source = f"def {func}({var}):\n    return {var} or {old_default}\n"
        new_source = f"def {func}({var}):\n    return {var} if {var} is not None else {new_default}\n"
        wrong_source = f"return {var} if {var} is not None else {var} or {new_default}"
        tasks.append(
            CurriculumTask(
                task_id=f"string_none_guard_edit_{task_name}",
                skill="edit",
                repo=f"toy/{task_name}guard",
                problem_statement=(
                    f"Repair {func} so only None uses {new_default}; explicit falsy values must be returned unchanged."
                ),
                memory_hint=(
                    f"The current `{var} or {old_default}` fallback conflates None with explicit falsy input. "
                    f"Do not produce `{wrong_source}`; after the None check, return `{var}` unchanged."
                ),
                current_evidence=(
                    f"{path}:{line_no}:def {func}({var}):\n"
                    f"{path}:{line_no + 1}:    return {var} or {old_default}"
                ),
                target_command=(
                    "python - <<'PY'\n"
                    "from pathlib import Path\n"
                    f"path = Path('{path}')\n"
                    "text = path.read_text()\n"
                    f"old = {old_source!r}\n"
                    f"new = {new_source!r}\n"
                    "assert old in text\n"
                    "path.write_text(text.replace(old, new, 1))\n"
                    "PY"
                ),
                expected_signal="A good edit removes the truthiness fallback from the non-None branch.",
                tags=("string_none_guard", "edit", "none_check", "anti_or_fallback", "preserve_falsy"),
            )
        )

    test_specs = [
        ("code", "tests/codes/test_code.py::test_empty_code_is_valid"),
        ("slug", "tests/slugs/test_slug.py::test_empty_slug_is_preserved"),
        ("alias", "tests/aliases/test_name.py::test_empty_alias_is_preserved"),
        ("caption", "tests/captions/test_text.py::test_empty_caption_is_preserved"),
        ("flag", "tests/flags/test_flag.py::test_false_flag_is_preserved"),
        ("count", "tests/counts/test_count.py::test_zero_count_is_preserved"),
    ]
    for task_name, node in test_specs:
        tasks.append(
            CurriculumTask(
                task_id=f"string_none_guard_test_{task_name}",
                skill="test",
                repo=f"toy/{task_name}guard",
                problem_statement="Run the exact focused regression test for the falsy-value preservation repair.",
                memory_hint=(
                    f"Exact pytest node to copy: {node}. Keep PYTHONPATH=src:. and do not substitute nearby names."
                ),
                target_command=f"PYTHONPATH=src:. python -m pytest {node} -q",
                expected_signal="A good test step copies the exact focused falsy-value regression node.",
                tags=("string_none_guard", "test", "exact_test_target", "focused_verification", "preserve_falsy"),
            )
        )
    return tasks


def generated_semantic_rule_heldout_curriculum_tasks() -> list[CurriculumTask]:
    """Return generated semantic-rule evaluation tasks with unseen names.

    This suite is intentionally larger than the four hand-written heldout tasks
    and uses names absent from the v10 train generator. It tests whether the
    model learned the rule family rather than the generated identifiers.
    """
    edit_specs = [
        ("window", "window", "0", "8", "explicit zero window", "src/windowopts/range.py", "normalize_window"),
        ("span", "span", "0", "6", "explicit zero span", "src/spanopts/span.py", "normalize_span"),
        ("level", "level", "0", "7", "explicit zero level", "src/levelopts/level.py", "normalize_level"),
        ("floor", "floor", "0", "1", "explicit zero floor", "src/flooropts/floor.py", "normalize_floor"),
        ("seed", "seed", "0", "42", "explicit zero seed", "src/seedopts/random.py", "normalize_seed"),
        ("prefix", "prefix", "''", "'item'", "explicit empty prefix", "src/prefixopts/name.py", "normalize_prefix"),
        ("label", "label", "''", "'unknown'", "explicit empty label", "src/labelopts/text.py", "normalize_label"),
        ("code", "code", "''", "'NA'", "explicit empty code", "src/codeopts/code.py", "normalize_code"),
    ]
    tasks: list[CurriculumTask] = []
    for idx, (task_name, var, old_default, new_default, explicit_case, path, func) in enumerate(edit_specs, start=1):
        line_no = 30 + idx
        old_source = f"def {func}({var}):\n    return {var} or {old_default}\n"
        new_source = f"def {func}({var}):\n    return {var} if {var} is not None else {new_default}\n"
        tasks.append(
            CurriculumTask(
                task_id=f"generated_heldout_semantic_edit_{task_name}",
                skill="edit",
                repo=f"toy/{task_name}lib",
                problem_statement=(
                    f"The helper must preserve {explicit_case}; only None should trigger the default {new_default}."
                ),
                memory_hint=(
                    f"The observed `{var} or {old_default}` line is a truthiness fallback. "
                    f"Use an explicit None branch so falsy user values stay valid and None maps to {new_default}."
                ),
                current_evidence=(
                    f"{path}:{line_no}:def {func}({var}):\n"
                    f"{path}:{line_no + 1}:    return {var} or {old_default}"
                ),
                target_command=(
                    "python - <<'PY'\n"
                    "from pathlib import Path\n"
                    f"path = Path('{path}')\n"
                    "text = path.read_text()\n"
                    f"old = {old_source!r}\n"
                    f"new = {new_source!r}\n"
                    "assert old in text\n"
                    "path.write_text(text.replace(old, new, 1))\n"
                    "PY"
                ),
                expected_signal="A good edit converts truthiness fallback into an explicit None branch.",
                tags=("generated_semantic_rule_heldout", "edit", "none_check", "anti_or_fallback"),
            )
        )

    mapping_specs = [
        ("toolbar", "settings", "DEFAULT_TOOLBAR", "src/toolbaropts/settings.py", "normalize_toolbar"),
        ("layout", "options", "DEFAULT_LAYOUT", "src/layoutopts/options.py", "normalize_layout"),
        ("chart", "config", "DEFAULT_CHART", "src/chartopts/config.py", "normalize_chart"),
        ("export", "params", "DEFAULT_EXPORT", "src/exportopts/params.py", "normalize_export"),
    ]
    for idx, (task_name, var, default_name, path, func) in enumerate(mapping_specs, start=1):
        line_no = 70 + idx
        tasks.append(
            CurriculumTask(
                task_id=f"generated_heldout_semantic_edit_mapping_{task_name}",
                skill="edit",
                repo=f"toy/{task_name}lib",
                problem_statement="The helper must preserve an explicit empty mapping and avoid mutating defaults.",
                memory_hint=(
                    f"`{var} or {default_name}` is wrong for empty dicts. "
                    "Check None explicitly and copy the selected mapping before mutation."
                ),
                current_evidence=(
                    f"{path}:{line_no}:def {func}({var}=None):\n"
                    f"{path}:{line_no + 1}:    opts = {var} or {default_name}\n"
                    f"{path}:{line_no + 2}:    opts['enabled'] = opts.get('enabled', True)"
                ),
                target_command=(
                    "python - <<'PY'\n"
                    "from pathlib import Path\n"
                    f"path = Path('{path}')\n"
                    "text = path.read_text()\n"
                    f"old = '    opts = {var} or {default_name}\\n'\n"
                    f"new = '    opts = dict({default_name} if {var} is None else {var})\\n'\n"
                    "assert old in text\n"
                    "path.write_text(text.replace(old, new, 1))\n"
                    "PY"
                ),
                expected_signal="A good edit preserves explicit empty mappings and copies defaults.",
                tags=("generated_semantic_rule_heldout", "edit", "none_check", "mutable_default", "anti_or_fallback"),
            )
        )

    test_specs = [
        ("window", "tests/windows/test_range.py::test_zero_window_is_preserved"),
        ("span", "tests/spans/test_span.py::test_zero_span_is_not_defaulted"),
        ("level", "tests/levels/test_level.py::test_zero_level_is_valid"),
        ("floor", "tests/floors/test_floor.py::test_zero_floor_is_respected"),
        ("seed", "tests/seeds/test_random.py::test_zero_seed_is_preserved"),
        ("prefix", "tests/prefixes/test_name.py::test_empty_prefix_is_preserved"),
        ("label", "tests/labels/test_text.py::test_empty_label_is_not_defaulted"),
        ("code", "tests/codes/test_code.py::test_empty_code_is_valid"),
        ("toolbar", "tests/toolbar_options/test_settings.py::test_empty_toolbar_settings_are_preserved"),
        ("layout", "tests/layout_options/test_options.py::test_default_layout_options_are_not_mutated"),
        ("chart", "tests/chart_config/test_config.py::test_empty_chart_config_is_preserved"),
        ("export", "tests/export_params/test_params.py::test_default_export_params_are_not_mutated"),
    ]
    for task_name, node in test_specs:
        tasks.append(
            CurriculumTask(
                task_id=f"generated_heldout_semantic_test_{task_name}",
                skill="test",
                repo=f"toy/{task_name}lib",
                problem_statement="Run the exact focused regression test; nearby remembered names are distractors.",
                memory_hint=(
                    f"Exact pytest node to copy: {node}. Keep the directory, function name, and PYTHONPATH exactly."
                ),
                target_command=f"PYTHONPATH=src:. python -m pytest {node} -q",
                expected_signal="A good test step copies the exact focused pytest node from memory.",
                tags=(
                    "generated_semantic_rule_heldout",
                    "test",
                    "exact_test_target",
                    "focused_verification",
                    "copy_exact_node",
                ),
            )
        )
    return tasks


def generated_semantic_rule_wide_heldout_curriculum_tasks() -> list[CurriculumTask]:
    """Return a wider unseen-name semantic-rule evaluation suite.

    This is evaluation-only. It expands the generated held-out audit with new
    package names, defaults, and pytest nodes so that a model that passes the
    24-task suite still has to show rule transfer instead of memorizing names.
    """
    edit_specs = [
        ("radius", "radius", "0", "15", "explicit zero radius", "src/radiusopts/shape.py", "normalize_radius"),
        ("margin", "margin", "0", "4", "explicit zero margin", "src/marginopts/box.py", "normalize_margin"),
        ("scale", "scale", "0", "1", "explicit zero scale", "src/scaleopts/value.py", "normalize_scale"),
        ("indent", "indent", "0", "2", "explicit zero indent", "src/indentopts/text.py", "normalize_indent"),
        ("page", "page", "0", "1", "explicit zero page", "src/pageindex/page.py", "normalize_page"),
        ("threshold", "threshold", "0", "9", "explicit zero threshold", "src/thresholdopts/limit.py", "normalize_threshold"),
        ("name", "name", "''", "'guest'", "explicit empty name", "src/nameguard/name.py", "normalize_name"),
        ("tag", "tag", "''", "'default'", "explicit empty tag", "src/tagguard/tag.py", "normalize_tag"),
        ("note", "note", "''", "'none'", "explicit empty note", "src/noteguard/note.py", "normalize_note"),
        ("path", "path", "''", "'root'", "explicit empty path", "src/pathguard/path.py", "normalize_path"),
        ("enabled", "enabled", "False", "True", "explicit false enabled flag", "src/enabledguard/flag.py", "normalize_enabled"),
        ("visible", "visible", "False", "True", "explicit false visible flag", "src/visibleguard/flag.py", "normalize_visible"),
    ]
    tasks: list[CurriculumTask] = []
    for idx, (task_name, var, old_default, new_default, explicit_case, path, func) in enumerate(edit_specs, start=1):
        line_no = 120 + idx
        old_source = f"def {func}({var}):\n    return {var} or {old_default}\n"
        new_source = f"def {func}({var}):\n    return {var} if {var} is not None else {new_default}\n"
        tasks.append(
            CurriculumTask(
                task_id=f"generated_wide_heldout_semantic_edit_{task_name}",
                skill="edit",
                repo=f"toy/{task_name}wide",
                problem_statement=(
                    f"The helper must preserve {explicit_case}; only None should trigger the default {new_default}."
                ),
                memory_hint=(
                    f"The observed `{var} or {old_default}` fallback is semantically wrong. "
                    f"Use an explicit None guard and return `{var}` unchanged for non-None falsy values."
                ),
                current_evidence=(
                    f"{path}:{line_no}:def {func}({var}):\n"
                    f"{path}:{line_no + 1}:    return {var} or {old_default}"
                ),
                target_command=(
                    "python - <<'PY'\n"
                    "from pathlib import Path\n"
                    f"path = Path('{path}')\n"
                    "text = path.read_text()\n"
                    f"old = {old_source!r}\n"
                    f"new = {new_source!r}\n"
                    "assert old in text\n"
                    "path.write_text(text.replace(old, new, 1))\n"
                    "PY"
                ),
                expected_signal="A good edit converts the truthiness fallback into an explicit None branch.",
                tags=("generated_semantic_rule_wide_heldout", "edit", "none_check", "anti_or_fallback"),
            )
        )

    mapping_specs = [
        ("badge", "settings", "DEFAULT_BADGE", "src/badgeopts/settings.py", "normalize_badge"),
        ("panel", "options", "DEFAULT_PANEL", "src/panelopts/options.py", "normalize_panel"),
        ("widget", "config", "DEFAULT_WIDGET", "src/widgetopts/config.py", "normalize_widget"),
        ("report", "params", "DEFAULT_REPORT", "src/reportopts/params.py", "normalize_report"),
        ("filter", "rules", "DEFAULT_FILTER_RULES", "src/filteropts/rules.py", "normalize_filter"),
        ("exporter", "settings", "DEFAULT_EXPORTER", "src/exporteropts/settings.py", "normalize_exporter"),
    ]
    for idx, (task_name, var, default_name, path, func) in enumerate(mapping_specs, start=1):
        line_no = 150 + idx
        tasks.append(
            CurriculumTask(
                task_id=f"generated_wide_heldout_semantic_edit_mapping_{task_name}",
                skill="edit",
                repo=f"toy/{task_name}wide",
                problem_statement="The helper must preserve an explicit empty mapping and avoid mutating defaults.",
                memory_hint=(
                    f"`{var} or {default_name}` treats empty dicts as missing. "
                    "Check None explicitly and copy the selected mapping before mutation."
                ),
                current_evidence=(
                    f"{path}:{line_no}:def {func}({var}=None):\n"
                    f"{path}:{line_no + 1}:    opts = {var} or {default_name}\n"
                    f"{path}:{line_no + 2}:    opts['enabled'] = opts.get('enabled', True)"
                ),
                target_command=(
                    "python - <<'PY'\n"
                    "from pathlib import Path\n"
                    f"path = Path('{path}')\n"
                    "text = path.read_text()\n"
                    f"old = '    opts = {var} or {default_name}\\n'\n"
                    f"new = '    opts = dict({default_name} if {var} is None else {var})\\n'\n"
                    "assert old in text\n"
                    "path.write_text(text.replace(old, new, 1))\n"
                    "PY"
                ),
                expected_signal="A good edit preserves explicit empty mappings and copies defaults.",
                tags=("generated_semantic_rule_wide_heldout", "edit", "none_check", "mutable_default"),
            )
        )

    test_specs = [
        ("radius", "tests/radius/test_shape.py::test_zero_radius_is_preserved"),
        ("margin", "tests/margins/test_box.py::test_zero_margin_is_not_defaulted"),
        ("scale", "tests/scales/test_value.py::test_zero_scale_is_valid"),
        ("indent", "tests/indents/test_text.py::test_zero_indent_is_respected"),
        ("page", "tests/page_index/test_page.py::test_zero_page_is_preserved"),
        ("threshold", "tests/thresholds/test_limit.py::test_zero_threshold_is_valid"),
        ("name", "tests/names/test_name.py::test_empty_name_is_preserved"),
        ("tag", "tests/tags/test_tag.py::test_empty_tag_is_preserved"),
        ("note", "tests/notes/test_note.py::test_empty_note_is_not_defaulted"),
        ("path", "tests/paths/test_path.py::test_empty_path_is_preserved"),
        ("enabled", "tests/enabled/test_flag.py::test_false_enabled_is_preserved"),
        ("visible", "tests/visible/test_flag.py::test_false_visible_is_preserved"),
        ("badge", "tests/badge_options/test_settings.py::test_empty_badge_settings_are_preserved"),
        ("panel", "tests/panel_options/test_options.py::test_default_panel_options_are_not_mutated"),
        ("widget", "tests/widget_config/test_config.py::test_empty_widget_config_is_preserved"),
        ("report", "tests/report_params/test_params.py::test_default_report_params_are_not_mutated"),
        ("filter", "tests/filter_rules/test_rules.py::test_empty_filter_rules_are_preserved"),
        ("exporter", "tests/exporter_settings/test_settings.py::test_default_exporter_settings_are_not_mutated"),
    ]
    for task_name, node in test_specs:
        tasks.append(
            CurriculumTask(
                task_id=f"generated_wide_heldout_semantic_test_{task_name}",
                skill="test",
                repo=f"toy/{task_name}wide",
                problem_statement="Run the exact focused regression test; nearby remembered names are distractors.",
                memory_hint=(
                    f"Exact pytest node to copy: {node}. Keep the directory, function name, and PYTHONPATH exactly."
                ),
                target_command=f"PYTHONPATH=src:. python -m pytest {node} -q",
                expected_signal="A good test step copies the exact focused pytest node from memory.",
                tags=(
                    "generated_semantic_rule_wide_heldout",
                    "test",
                    "exact_test_target",
                    "focused_verification",
                    "copy_exact_node",
                ),
            )
        )
    return tasks


def build_semantic_guard_curriculum_records(
    *, repeat: int = 1, run_id: str = "hybrid-gym-mini-semantic-guard"
) -> list[dict[str, Any]]:
    if repeat < 1:
        raise ValueError("repeat must be >= 1")
    records: list[dict[str, Any]] = []
    for repeat_idx in range(repeat):
        for task in semantic_guard_curriculum_tasks():
            record = task_to_record(task, run_id=run_id)
            if repeat > 1:
                record["instance_id"] = f"{task.task_id}_r{repeat_idx + 1:02d}"
                record["repeat_index"] = repeat_idx
            records.append(record)
    return records


def build_semantic_variant_curriculum_records(
    *, repeat: int = 1, run_id: str = "hybrid-gym-mini-semantic-variant"
) -> list[dict[str, Any]]:
    if repeat < 1:
        raise ValueError("repeat must be >= 1")
    records: list[dict[str, Any]] = []
    for repeat_idx in range(repeat):
        for task in semantic_variant_curriculum_tasks():
            record = task_to_record(task, run_id=run_id)
            if repeat > 1:
                record["instance_id"] = f"{task.task_id}_r{repeat_idx + 1:02d}"
                record["repeat_index"] = repeat_idx
            records.append(record)
    return records


def build_semantic_rule_curriculum_records(
    *, repeat: int = 1, run_id: str = "hybrid-gym-mini-semantic-rule"
) -> list[dict[str, Any]]:
    if repeat < 1:
        raise ValueError("repeat must be >= 1")
    records: list[dict[str, Any]] = []
    for repeat_idx in range(repeat):
        for task in semantic_rule_curriculum_tasks():
            record = task_to_record(task, run_id=run_id)
            if repeat > 1:
                record["instance_id"] = f"{task.task_id}_r{repeat_idx + 1:02d}"
                record["repeat_index"] = repeat_idx
            records.append(record)
    return records


def build_generated_semantic_rule_curriculum_records(
    *, repeat: int = 1, run_id: str = "hybrid-gym-mini-generated-semantic-rule"
) -> list[dict[str, Any]]:
    if repeat < 1:
        raise ValueError("repeat must be >= 1")
    records: list[dict[str, Any]] = []
    for repeat_idx in range(repeat):
        for task in generated_semantic_rule_curriculum_tasks():
            record = task_to_record(task, run_id=run_id)
            if repeat > 1:
                record["instance_id"] = f"{task.task_id}_r{repeat_idx + 1:02d}"
                record["repeat_index"] = repeat_idx
            records.append(record)
    return records


def build_string_none_guard_curriculum_records(
    *, repeat: int = 1, run_id: str = "hybrid-gym-mini-string-none-guard"
) -> list[dict[str, Any]]:
    if repeat < 1:
        raise ValueError("repeat must be >= 1")
    records: list[dict[str, Any]] = []
    for repeat_idx in range(repeat):
        for task in string_none_guard_curriculum_tasks():
            record = task_to_record(task, run_id=run_id)
            if repeat > 1:
                record["instance_id"] = f"{task.task_id}_r{repeat_idx + 1:02d}"
                record["repeat_index"] = repeat_idx
            records.append(record)
    return records


def build_semantic_contrast_curriculum_records(
    *, repeat: int = 1, run_id: str = "hybrid-gym-mini-semantic-contrast"
) -> list[dict[str, Any]]:
    if repeat < 1:
        raise ValueError("repeat must be >= 1")
    records: list[dict[str, Any]] = []
    for repeat_idx in range(repeat):
        for task in semantic_contrast_curriculum_tasks():
            record = task_to_record(task, run_id=run_id)
            if repeat > 1:
                record["instance_id"] = f"{task.task_id}_r{repeat_idx + 1:02d}"
                record["repeat_index"] = repeat_idx
            records.append(record)
    return records
