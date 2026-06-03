from minisweagent.run.benchmarks.memory import format_memory_block, retrieve_memories


def test_hybrid_memory_filters_unrelated_high_q_global_memory():
    instance = {
        "instance_id": "django__target",
        "repo": "django/django",
        "problem_statement": "Fix form field validation for choices.",
        "hints_text": "",
    }
    memories = [
        {
            "instance_id": "django__same_high",
            "repo": "django/django",
            "tokens": ["form", "field", "validation"],
            "q_value": 0.5,
        },
        {
            "instance_id": "django__same_second",
            "repo": "django/django",
            "tokens": ["choices", "validation"],
            "q_value": 0.5,
        },
        {
            "instance_id": "global__high_q",
            "repo": "other/project",
            "tokens": ["unrelated"],
            "q_value": 0.95,
        },
        {
            "instance_id": "django__same_third",
            "repo": "django/django",
            "tokens": ["field"],
            "q_value": 0.5,
        },
    ]

    retrieved = retrieve_memories(
        instance,
        memories,
        k=3,
        strategy="hybrid",
        same_repo_k=2,
        global_k=1,
    )

    assert [item["instance_id"] for item in retrieved] == [
        "django__same_high",
        "django__same_second",
        "django__same_third",
    ]
    assert all(item["same_repo"] for item in retrieved)
    assert all(item["memory_confidence"] == "normal" for item in retrieved)


def test_hybrid_memory_keeps_similar_high_q_global_memory():
    instance = {
        "instance_id": "django__target",
        "repo": "django/django",
        "problem_statement": "Fix form field validation for choices.",
        "hints_text": "",
    }
    memories = [
        {
            "instance_id": "django__same_high",
            "repo": "django/django",
            "tokens": ["form", "field", "validation"],
            "q_value": 0.5,
        },
        {
            "instance_id": "django__same_second",
            "repo": "django/django",
            "tokens": ["choices", "validation"],
            "q_value": 0.5,
        },
        {
            "instance_id": "global__high_q",
            "repo": "other/project",
            "tokens": ["form", "field", "validation", "choices"],
            "q_value": 0.95,
        },
    ]

    retrieved = retrieve_memories(
        instance,
        memories,
        k=3,
        strategy="hybrid",
        same_repo_k=2,
        global_k=1,
    )

    assert [item["instance_id"] for item in retrieved] == [
        "django__same_high",
        "django__same_second",
        "global__high_q",
    ]
    assert retrieved[-1]["same_repo"] is False


def test_simple_gate_abstains_from_low_confidence_global_memory():
    instance = {
        "instance_id": "target__1",
        "repo": "repo/a",
        "problem_statement": "parser crash on edge token",
        "hints_text": "",
    }
    memories = [
        {
            "instance_id": "global__weak",
            "repo": "repo/b",
            "tokens": ["unrelated"],
            "q_value": 1.0,
        },
        {
            "instance_id": "global__low_q",
            "repo": "repo/b",
            "tokens": ["parser", "crash", "edge", "token"],
            "q_value": 0.1,
        },
    ]

    retrieved = retrieve_memories(
        instance,
        memories,
        k=2,
        strategy="score",
        gate_mode="simple",
        gate_min_similarity=0.18,
        gate_min_q=0.25,
    )

    assert retrieved == []


def test_simple_gate_keeps_same_repo_low_similarity_memory():
    instance = {
        "instance_id": "target__1",
        "repo": "repo/a",
        "problem_statement": "parser crash on edge token",
        "hints_text": "",
    }
    memories = [
        {
            "instance_id": "same__ok",
            "repo": "repo/a",
            "tokens": ["unrelated"],
            "q_value": 0.3,
        }
    ]

    retrieved = retrieve_memories(instance, memories, k=1, strategy="score", gate_mode="simple")

    assert [item["instance_id"] for item in retrieved] == ["same__ok"]
    assert retrieved[0]["memory_gate"] == "pass"


def test_low_confidence_hybrid_memory_is_downweighted_in_prompt():
    instance = {
        "instance_id": "sympy__target",
        "repo": "sympy/sympy",
        "problem_statement": "Fix polynomial expansion.",
        "hints_text": "",
    }
    memories = [
        {
            "instance_id": "sympy__weak",
            "repo": "sympy/sympy",
            "tokens": ["matrix"],
            "q_value": 0.5,
            "patch_summary": "A" * 800,
        },
        {
            "instance_id": "other__weak",
            "repo": "other/project",
            "tokens": ["parser"],
            "q_value": 0.5,
            "patch_summary": "B" * 800,
        },
    ]

    retrieved = retrieve_memories(
        instance,
        memories,
        k=2,
        strategy="hybrid",
        low_confidence_q=0.5,
        low_confidence_similarity=0.9,
    )
    block = format_memory_block(retrieved)

    assert all(item["memory_confidence"] == "low" for item in retrieved)
    assert "Confidence note" in block
    assert "A" * 500 not in block
