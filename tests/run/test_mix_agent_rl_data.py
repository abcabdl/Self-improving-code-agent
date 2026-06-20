import json

from scripts.mix_agent_rl_data import _is_failed_informative, _parquet_safe, _sample


def test_failed_informative_requires_unresolved_action():
    assert _is_failed_informative(
        {
            "extra_info": {"resolved": False},
            "response": {"extra": {"actions": [{"command": "rg bug"}]}},
        }
    )
    assert not _is_failed_informative(
        {
            "extra_info": {"resolved": True},
            "response": {"extra": {"actions": [{"command": "rg bug"}]}},
        }
    )
    assert not _is_failed_informative({"extra_info": {"resolved": False}, "response": {"extra": {"actions": []}}})


def test_sample_uses_replacement_when_needed():
    import random

    records = [{"x": 1}]
    sampled = _sample(records, 3, random.Random(1))

    assert sampled == [{"x": 1}, {"x": 1}, {"x": 1}]


def test_parquet_safe_serializes_structured_reward_model():
    record = {
        "prompt": [{"role": "user", "content": "x"}],
        "response": {"role": "assistant", "content": "y"},
        "extra_info": {"skill": "edit"},
        "reward_model": {"style": "rule", "ground_truth": 1.0},
    }

    safe = _parquet_safe(record)

    assert json.loads(safe["reward_model"]) == {"style": "rule", "ground_truth": 1.0}
    assert json.loads(safe["extra_info"]) == {"skill": "edit"}
