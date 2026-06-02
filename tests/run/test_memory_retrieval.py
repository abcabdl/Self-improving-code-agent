from minisweagent.run.benchmarks.memory import retrieve_memories


def test_hybrid_global_zero_keeps_only_same_repo_memories():
    instance = {
        "instance_id": "target__1",
        "repo": "repo/a",
        "problem_statement": "parser crash on edge token",
        "hints_text": "",
    }
    memories = [
        {
            "instance_id": "repo__same",
            "repo": "repo/a",
            "tokens": ["parser", "edge"],
            "q_value": 0.4,
        },
        {
            "instance_id": "repo__other_high_q",
            "repo": "repo/b",
            "tokens": ["parser", "edge", "token"],
            "q_value": 1.0,
        },
    ]

    retrieved = retrieve_memories(
        instance,
        memories,
        k=3,
        strategy="hybrid",
        same_repo_k=3,
        global_k=0,
    )

    assert [item["instance_id"] for item in retrieved] == ["repo__same"]
