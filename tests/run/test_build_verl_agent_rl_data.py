import json

import pandas as pd

from scripts.build_verl_agent_rl_data import _load_records, _write_parquet_dir


def _write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")


def _record(instance_id, reward, resolved):
    return {
        "instance_id": instance_id,
        "repo": "owner/repo",
        "messages_before_action": [{"role": "user", "content": "Fix it"}],
        "assistant_message": {"role": "assistant", "content": "THOUGHT\n", "extra": {"actions": [{"command": "rg bug"}]}},
        "resolved": resolved,
        "reward": reward,
        "step_index": 1,
        "step_count": 1,
        "invalid_action_count": 0,
    }


def test_load_records_keeps_failed_by_default_and_can_filter_success(tmp_path):
    input_path = tmp_path / "rollouts.jsonl"
    _write_jsonl(input_path, [_record("a", 0.9, True), _record("b", -0.01, False)])

    all_records = _load_records(input_path, min_reward=None, include_failed=True)
    success_records = _load_records(input_path, min_reward=None, include_failed=False)

    assert len(all_records) == 2
    assert len(success_records) == 1
    assert all_records[0]["reward_model"]["ground_truth"] == 0.9


def test_write_parquet_dir_creates_train_val_and_stats(tmp_path):
    records = [
        {
            "data_source": "memory_augmented_mini_swe_agent",
            "prompt": [{"role": "user", "content": "Fix it"}],
            "response": {"role": "assistant", "content": "Use rg"},
            "reward_model": {"style": "rule", "ground_truth": 1.0},
            "extra_info": {"resolved": True},
        },
        {
            "data_source": "memory_augmented_mini_swe_agent",
            "prompt": [{"role": "user", "content": "Fix it"}],
            "response": {"role": "assistant", "content": "Use pytest"},
            "reward_model": {"style": "rule", "ground_truth": 0.0},
            "extra_info": {"resolved": False},
        },
    ]

    stats = _write_parquet_dir(tmp_path / "verl", records, val_ratio=0.5, seed=1)

    assert stats["train_records"] == 1
    assert stats["val_records"] == 1
    assert (tmp_path / "verl" / "stats.json").exists()
    assert len(pd.read_parquet(tmp_path / "verl" / "train.parquet")) == 1
    assert len(pd.read_parquet(tmp_path / "verl" / "val.parquet")) == 1
