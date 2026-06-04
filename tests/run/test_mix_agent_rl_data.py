from scripts.mix_agent_rl_data import _is_failed_informative, _sample


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
