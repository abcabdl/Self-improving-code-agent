from minisweagent.run.benchmarks.hybrid_gym_curriculum import (
    build_default_curriculum_records,
    build_challenge_curriculum_records,
    build_extended_transition_curriculum_records,
    build_generated_semantic_rule_curriculum_records,
    generated_semantic_rule_heldout_curriculum_tasks,
    build_heldout_curriculum_records,
    build_proxy_easy_curriculum_records,
    build_semantic_contrast_curriculum_records,
    build_semantic_guard_curriculum_records,
    build_semantic_rule_curriculum_records,
    build_semantic_variant_curriculum_records,
    build_string_none_guard_curriculum_records,
    build_transition_curriculum_records,
    curriculum_record_to_verl_record,
)


def test_default_curriculum_records_cover_locate_edit_test_and_memory():
    records = build_default_curriculum_records()

    skills = {record["skill"] for record in records}
    assert {"locate", "edit", "test"}.issubset(skills)
    assert all(record["memory_block"].startswith("<retrieved_repair_memories>") for record in records)
    assert all(record["assistant_message"]["extra"]["actions"] for record in records)
    assert any("exact source replacement" in record["observation_summary"] for record in records)


def test_curriculum_record_to_verl_preserves_training_metadata():
    record = build_default_curriculum_records()[0]

    verl = curriculum_record_to_verl_record(record)

    assert verl["data_source"].startswith("memory_agent_hybrid_gym_")
    assert verl["prompt"] == record["messages_before_action"]
    assert verl["response"] == record["assistant_message"]
    assert verl["reward_model"]["ground_truth"] == record["reward"]
    assert verl["extra_info"]["record_type"] == "hybrid_gym_curriculum"
    assert verl["extra_info"]["memory_ids"] == record["memory_ids"]


def test_curriculum_repeat_makes_instance_ids_unique():
    records = build_default_curriculum_records(repeat=2)

    instance_ids = [record["instance_id"] for record in records]
    assert len(instance_ids) == len(set(instance_ids))
    assert {record["repeat_index"] for record in records} == {0, 1}


def test_heldout_curriculum_uses_different_task_ids_and_same_skill_families():
    train_ids = {record["instance_id"] for record in build_default_curriculum_records()}
    heldout = build_heldout_curriculum_records()

    assert heldout
    assert train_ids.isdisjoint({record["instance_id"] for record in heldout})
    assert {"locate", "edit", "test"}.issubset({record["skill"] for record in heldout})


def test_challenge_curriculum_uses_challenge_tags_and_skills():
    records = build_challenge_curriculum_records()

    assert records
    assert all(record["instance_id"].startswith("challenge_") for record in records)
    assert {"locate", "edit", "test"}.issubset({record["skill"] for record in records})
    assert all("challenge" in record["tags"] for record in records)


def test_proxy_easy_curriculum_is_custom_self_suitable_and_balanced():
    records = build_proxy_easy_curriculum_records()

    assert len(records) >= 5
    assert {"locate", "edit", "test"}.issubset({record["skill"] for record in records})
    assert all(record["instance_id"].startswith("proxy_easy_") for record in records)
    assert all("proxy_easy" in record["tags"] for record in records)
    assert all("self_suitable" in record["tags"] for record in records)
    assert all(not record["repo"].startswith(("django", "pvlib", "sqlfluff", "pydicom")) for record in records)


def test_transition_curriculum_targets_empty_fence_and_pytest_regressions():
    records = build_transition_curriculum_records()

    assert records
    assert {"edit", "test"} == {record["skill"] for record in records}
    responses = [record["assistant_message"]["content"] for record in records]
    assert all("```mswea_bash_command" in response for response in responses)
    assert any("python -m pytest" in response for response in responses)
    assert any("empty_fence_repair" in record["tags"] for record in records)


def test_extended_transition_curriculum_is_train_only_and_balanced():
    records = build_extended_transition_curriculum_records()

    assert records
    assert {"locate", "edit", "test"}.issubset({record["skill"] for record in records})
    assert all(record["instance_id"].startswith("extended_") for record in records)
    assert all("extended_transition" in record["tags"] for record in records)
    assert any("stale_memory_recovery" in record["tags"] for record in records)
    assert any("truthiness_default" in record["tags"] for record in records)


def test_semantic_guard_curriculum_targets_strict_failures():
    records = build_semantic_guard_curriculum_records()

    assert records
    assert {"edit", "test"} == {record["skill"] for record in records}
    assert all(record["instance_id"].startswith("semantic_") for record in records)
    assert all("semantic_guard" in record["tags"] for record in records)
    responses = [record["assistant_message"]["content"] for record in records]
    assert any("is None else" in response for response in responses)
    assert any("python -m pytest" in response for response in responses)
    assert any("exact_test_target" in record["tags"] for record in records)


def test_semantic_contrast_curriculum_adds_diverse_strict_patterns():
    records = build_semantic_contrast_curriculum_records()

    assert records
    assert {"edit", "test"} == {record["skill"] for record in records}
    assert all(record["instance_id"].startswith("semantic_contrast_") for record in records)
    assert all("semantic_contrast" in record["tags"] for record in records)
    responses = [record["assistant_message"]["content"] for record in records]
    assert any("is not None else" in response for response in responses)
    assert any("is None else" in response for response in responses)
    assert any("dict(DEFAULT_HEADERS" in response for response in responses)
    assert sum("python -m pytest" in response for response in responses) >= 3


def test_semantic_variant_curriculum_covers_literal_defaults_and_exact_nodes():
    records = build_semantic_variant_curriculum_records()

    assert records
    assert {"edit", "test"} == {record["skill"] for record in records}
    assert all(record["instance_id"].startswith("semantic_variant_") for record in records)
    assert all("semantic_variant" in record["tags"] for record in records)
    responses = [record["assistant_message"]["content"] for record in records]
    assert any("value if value is not None else 10" in response for response in responses)
    assert any("count if count is not None else 3" in response for response in responses)
    assert any("'item' if prefix is None else prefix" in response for response in responses)
    assert any("dict(DEFAULT_OPTIONS" in response for response in responses)
    assert sum("python -m pytest" in response for response in responses) >= 4


def test_semantic_rule_curriculum_targets_v8_failures_without_heldout_names():
    records = build_semantic_rule_curriculum_records()

    assert records
    assert {"edit", "test"} == {record["skill"] for record in records}
    assert all(record["instance_id"].startswith("semantic_rule_") for record in records)
    assert all("semantic_rule" in record["tags"] for record in records)
    responses = [record["assistant_message"]["content"] for record in records]
    assert any("1 if value is None else value" in response for response in responses)
    assert any("limit if limit is not None else 5" in response for response in responses)
    assert any("dict(DEFAULT_OPTIONS if options is None else options)" in response for response in responses)
    assert sum("python -m pytest" in response for response in responses) >= 4
    joined = "\n".join(responses)
    assert "metricslib" not in joined
    assert "accumulators/test_weights" not in joined
    assert "decode/test_options" not in joined


def test_generated_semantic_rule_curriculum_expands_rule_families_without_probe_names():
    records = build_generated_semantic_rule_curriculum_records()

    assert records
    assert len(records) >= 32
    assert {"edit", "test"} == {record["skill"] for record in records}
    assert all(record["instance_id"].startswith("generated_semantic_") for record in records)
    assert all("generated_semantic_rule" in record["tags"] for record in records)
    responses = [record["assistant_message"]["content"] for record in records]
    assert sum("is not None else" in response for response in responses) >= 8
    assert sum("dict(" in response for response in responses) >= 4
    assert sum("python -m pytest" in response for response in responses) >= 16
    joined = "\n".join(responses)
    assert "metricslib" not in joined
    assert "test_accumulator.py" not in joined
    assert "decoder/test_options" not in joined


def test_generated_semantic_rule_heldout_uses_unseen_names():
    train_records = build_generated_semantic_rule_curriculum_records()
    heldout_tasks = generated_semantic_rule_heldout_curriculum_tasks()

    assert len(heldout_tasks) >= 20
    assert {"edit", "test"} == {task.skill for task in heldout_tasks}
    train_text = "\n".join(record["assistant_message"]["content"] for record in train_records)
    heldout_text = "\n".join(task.target_command for task in heldout_tasks)
    assert "windowopts" in heldout_text
    assert "toolbar_options" in heldout_text
    assert "windowopts" not in train_text
    assert "toolbar_options" not in train_text


def test_generated_semantic_rule_targets_quote_string_defaults_safely():
    records = build_generated_semantic_rule_curriculum_records()
    heldout_tasks = generated_semantic_rule_heldout_curriculum_tasks()

    commands = [record["assistant_message"]["extra"]["actions"][0]["command"] for record in records]
    commands.extend(task.target_command for task in heldout_tasks)

    assert any("def normalize_suffix" in command and 'old = "def ' in command for command in commands)
    assert any("def normalize_prefix" in command and 'old = "def ' in command for command in commands)
    assert all("old = 'def normalize_suffix" not in command for command in commands)
    assert all("old = 'def normalize_prefix" not in command for command in commands)


def test_string_none_guard_curriculum_removes_truthiness_else_branch():
    records = build_string_none_guard_curriculum_records()

    assert records
    assert {"edit", "test"} == {record["skill"] for record in records}
    assert all(record["instance_id"].startswith("string_none_guard_") for record in records)
    assert all("string_none_guard" in record["tags"] for record in records)

    commands = [record["assistant_message"]["extra"]["actions"][0]["command"] for record in records]
    joined = "\n".join(commands)
    assert "def normalize_code" in joined
    assert "return code if code is not None else 'NA'" in joined
    assert "else code or 'NA'" not in joined
    assert "return flag if flag is not None else True" in joined
    assert "return count if count is not None else 11" in joined
