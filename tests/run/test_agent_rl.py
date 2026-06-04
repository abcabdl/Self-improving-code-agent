import json

from minisweagent.run.benchmarks.agent_rl import (
    compute_agent_reward,
    export_run_records,
    find_trajectory,
    to_verl_record,
    trajectory_to_rl_records,
)
from scripts.run_agent_rl_rollouts import find_summary


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")


def _trajectory():
    return {
        "messages": [
            {"role": "system", "content": "You are mini-swe-agent."},
            {
                "role": "user",
                "content": (
                    "Fix the bug.\n"
                    "<retrieved_repair_memories>\n"
                    "- Prior fix: inspect parser tests.\n"
                    "</retrieved_repair_memories>"
                ),
            },
            {
                "role": "assistant",
                "content": "I will inspect the parser.",
                "extra": {"actions": [{"command": "rg parser", "tool_call_id": "call_1"}]},
            },
            {"role": "tool", "content": "parser.py:12:def parse(x): ..."},
            {"role": "assistant", "content": "No action this time.", "extra": {"actions": []}},
            {"role": "tool", "content": "No tool call."},
            {"role": "exit", "content": "done"},
        ]
    }


def test_reward_is_outcome_first_with_capped_generic_penalties():
    solved = compute_agent_reward(resolved=True, step_count=1000, invalid_action_count=1000)
    unsolved = compute_agent_reward(resolved=False, step_count=0, invalid_action_count=0)
    mildly_long = compute_agent_reward(resolved=True, step_count=10, invalid_action_count=1)

    assert solved == 0.9
    assert unsolved == 0.0
    assert solved > unsolved
    assert mildly_long == 0.99


def test_trajectory_to_rl_records_exports_one_record_per_assistant_step():
    records = trajectory_to_rl_records(
        trajectory=_trajectory(),
        instance_id="repo__1",
        repo="owner/repo",
        resolved=True,
        memory_usage=[{"memory_instance_id": "repo__memory", "rank": 1}],
        run_id="run-1",
    )

    assert len(records) == 2
    assert records[0]["memory_ids"] == ["repo__memory"]
    assert records[0]["memory_block"].startswith("<retrieved_repair_memories>")
    assert records[0]["assistant_action"]["command"] == "rg parser"
    assert records[0]["step_count"] == 2
    assert records[0]["invalid_action_count"] == 1
    assert records[1]["assistant_action"] is None
    assert "[tool] parser.py" in records[0]["observation_summary"]


def test_export_run_records_handles_missing_retrieval_log_and_unresolved_runs(tmp_path):
    run_dir = tmp_path / "run"
    instance_id = "repo__1"
    _write_json(run_dir / instance_id / f"{instance_id}.traj.json", _trajectory())
    summary = tmp_path / "summary.json"
    _write_json(summary, {"resolved_ids": [], "unresolved_ids": [instance_id], "empty_patch_ids": [], "error_ids": []})

    output = tmp_path / "rollouts.jsonl"
    stats = export_run_records(
        run_dir=run_dir,
        summary_path=summary,
        output_path=output,
        retrieval_log=tmp_path / "missing_retrieved_memories.jsonl",
        run_id="run-1",
    )

    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert stats == {"instances": 1, "records": 2, "missing_trajectories": 0}
    assert rows[0]["resolved"] is False
    assert rows[0]["memory_ids"] == []
    assert rows[0]["reward"] < 0.0


def test_export_run_records_counts_missing_trajectories(tmp_path):
    summary = tmp_path / "summary.json"
    _write_json(summary, {"resolved_ids": ["repo__missing"], "unresolved_ids": [], "empty_patch_ids": [], "error_ids": []})

    stats = export_run_records(run_dir=tmp_path / "run", summary_path=summary, output_path=tmp_path / "rollouts.jsonl")

    assert stats == {"instances": 1, "records": 0, "missing_trajectories": 1}


def test_export_run_records_reads_ranked_memory_usage(tmp_path):
    run_dir = tmp_path / "run"
    instance_id = "repo__1"
    _write_json(run_dir / instance_id / f"{instance_id}.traj.json", _trajectory())
    summary = tmp_path / "summary.json"
    _write_json(summary, {"resolved_ids": [instance_id], "unresolved_ids": [], "empty_patch_ids": [], "error_ids": []})
    retrieval_log = run_dir / "retrieved_memories.jsonl"
    _write_jsonl(
        retrieval_log,
        [
            {"target_instance_id": instance_id, "memory_instance_id": "memory_2", "rank": 2},
            {"target_instance_id": instance_id, "memory_instance_id": "memory_1", "rank": 1},
        ],
    )

    output = tmp_path / "rollouts.jsonl"
    export_run_records(run_dir=run_dir, summary_path=summary, output_path=output, retrieval_log=retrieval_log)

    first = json.loads(output.read_text(encoding="utf-8").splitlines()[0])
    assert first["memory_ids"] == ["memory_1", "memory_2"]


def test_to_verl_record_preserves_prompt_response_reward_and_metadata():
    record = trajectory_to_rl_records(
        trajectory=_trajectory(),
        instance_id="repo__1",
        repo="owner/repo",
        resolved=True,
        run_id="run-1",
    )[0]

    verl_record = to_verl_record(record)

    assert verl_record["data_source"] == "memory_augmented_mini_swe_agent"
    assert verl_record["prompt"] == record["messages_before_action"]
    assert verl_record["response"] == record["assistant_message"]
    assert verl_record["reward_model"] == {"style": "rule", "ground_truth": record["reward"]}
    assert verl_record["extra_info"]["instance_id"] == "repo__1"
    assert verl_record["extra_info"]["resolved"] is True


def test_find_trajectory_supports_nested_and_flat_layouts(tmp_path):
    nested = tmp_path / "repo__1" / "repo__1.traj.json"
    flat = tmp_path / "repo__2.traj.json"
    _write_json(nested, _trajectory())
    _write_json(flat, _trajectory())

    assert find_trajectory(tmp_path, "repo__1") == nested
    assert find_trajectory(tmp_path, "repo__2") == flat


def test_find_summary_falls_back_to_model_prefixed_evaluation_name(tmp_path):
    expected = tmp_path / "agent-rl-rollout_01.json"
    prefixed = tmp_path / "openai__gpt-5-mini.agent-rl-rollout_01.json"
    _write_json(prefixed, {"resolved_ids": []})

    assert find_summary(tmp_path, "agent-rl-rollout_01", expected) == prefixed
