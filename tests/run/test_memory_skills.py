from minisweagent.run.benchmarks.memory_skills import classify_command, records_to_skill_records, skill_record_to_verl_record


def test_classify_command_extracts_locate_edit_and_test_skills():
    assert classify_command("rg 'class Parser' src") == "locate"
    assert classify_command("apply_patch <<'PATCH'\n*** Begin Patch\nPATCH") == "edit"
    assert classify_command("python -m pytest tests/test_parser.py") == "test"
    assert classify_command("echo hello") is None


def test_records_to_skill_records_preserves_action_context_and_rewards():
    records = [
        {
            "instance_id": "repo__1",
            "repo": "owner/repo",
            "messages_before_action": [{"role": "user", "content": "Fix bug"}],
            "assistant_message": {"role": "assistant", "content": "Search first"},
            "assistant_action": {"command": "rg parser src"},
            "observation_summary": "src/parser.py:def parse",
            "resolved": True,
            "reward": 0.9,
        },
        {
            "instance_id": "repo__1",
            "messages_before_action": [{"role": "user", "content": "Fix bug"}],
            "assistant_message": {"role": "assistant", "content": "Just talk"},
            "assistant_action": None,
            "resolved": False,
            "reward": -0.01,
        },
    ]

    skill_records = records_to_skill_records(records)
    verl_record = skill_record_to_verl_record(skill_records[0])

    assert len(skill_records) == 1
    assert skill_records[0]["skill"] == "locate"
    assert skill_records[0]["reward"] == 1.0
    assert verl_record["data_source"] == "memory_agent_skill_locate"
    assert verl_record["extra_info"]["skill"] == "locate"
