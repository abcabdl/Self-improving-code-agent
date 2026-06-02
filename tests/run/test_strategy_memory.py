from minisweagent.run.benchmarks.strategy_memory import (
    classify_command,
    empty_strategy_memory,
    format_strategy_block,
    reflections_from_trajectory,
    retrieve_strategy_items,
    tool_prior,
    workflow_from_trajectory,
)


def _trajectory(*commands: str) -> dict:
    return {
        "messages": [
            {
                "role": "assistant",
                "extra": {"actions": [{"command": command}]},
            }
            for command in commands
        ]
    }


def test_classify_command_categories():
    assert classify_command("grep -R callback_args -n django") == "search"
    assert classify_command("sed -n '1,120p' django/urls/resolvers.py") == "inspect"
    assert classify_command("python -m pytest tests/urls_tests") == "test"
    assert classify_command("sed -i 's/old/new/' django/urls/resolvers.py") == "edit"
    assert classify_command("echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt") == "submit"


def test_build_and_retrieve_workflow():
    workflow = workflow_from_trajectory(
        "django__source",
        "django/django",
        "Optional URL params crash view callbacks.",
        _trajectory(
            "grep -R callback_args -n django",
            "sed -n '1,120p' django/urls/resolvers.py",
            "sed -i 's/old/new/' django/urls/resolvers.py",
            "python -m pytest tests/urls_tests",
        ),
    )
    assert workflow is not None
    retrieved = retrieve_strategy_items(
        {"repo": "django/django", "problem_statement": "URL callback args crash"},
        [workflow],
        k=1,
    )
    assert retrieved[0]["workflow_id"] == workflow["workflow_id"]
    assert retrieved[0]["same_repo"] is True


def test_failure_reflection_and_bandit_prompt():
    reflections = reflections_from_trajectory(
        "sympy__failed",
        "sympy/sympy",
        "Polynomial expansion fails.",
        _trajectory("grep -R expand -n sympy", "sed -n '1,80p' sympy/core.py"),
        empty_patch=True,
    )
    codes = {item["failure_code"] for item in reflections}
    assert {"empty_patch", "no_targeted_test", "no_edit"} <= codes

    strategy = empty_strategy_memory()
    strategy["tool_bandit"]["repos"]["sympy/sympy"] = {
        "search": {"q_value": 0.8, "update_count": 1},
        "inspect": {"q_value": 0.7, "update_count": 1},
    }
    priorities = tool_prior(strategy, "sympy/sympy")
    block = format_strategy_block([], reflections[:1], priorities)
    assert priorities[0]["category"] == "search"
    assert "<tool_use_bandit>" in block
    assert "<failure_reflection" in block
