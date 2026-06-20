from scripts.apply_hard_recall_protection_policy import apply_policy


def test_apply_hard_recall_protection_preserves_easy_and_promotes_strong_hard():
    base_policy = {
        "call_log": [
            {"instance_id": "easy_a", "kind": "proxy_easy", "route": "P", "large_model_called": True},
            {"instance_id": "hard_strong", "kind": "swe_hard", "route": "L", "large_model_called": False},
            {"instance_id": "hard_weak", "kind": "swe_hard", "route": "L", "large_model_called": False},
            {"instance_id": "hard_already_p", "kind": "swe_hard", "route": "P", "large_model_called": True},
        ]
    }
    retrieval_policy = {
        "call_log": [
            {
                "instance_id": "hard_strong",
                "same_repo_memories": 3,
                "max_similarity": 0.281,
                "top_memories": [
                    {"same_repo": True, "repo": "org/repo", "instance_id": "m1"},
                    {"same_repo": True, "repo": "org/repo", "instance_id": "m2"},
                    {"same_repo": True, "repo": "org/repo", "instance_id": "m3"},
                ],
            },
            {
                "instance_id": "hard_weak",
                "same_repo_memories": 1,
                "max_similarity": 0.45,
                "top_memories": [{"same_repo": True, "repo": "org/other", "instance_id": "m4"}],
            },
        ]
    }

    result = apply_policy(
        base_policy=base_policy,
        retrieval_policy=retrieval_policy,
        min_same_repo=3,
        min_similarity=0.28,
        mode="unit",
    )

    rows = {row["instance_id"]: row for row in result["call_log"]}
    assert rows["easy_a"]["route"] == "L"
    assert rows["easy_a"]["large_model_called"] is False
    assert rows["hard_strong"]["route"] == "P"
    assert rows["hard_strong"]["protected_promoted"] is True
    assert rows["hard_strong"]["packet"]["selected_memory_ids"] == ["mem_1", "mem_2", "mem_3"]
    assert rows["hard_weak"]["route"] == "L"
    assert rows["hard_weak"]["protected_promoted"] is False
    assert rows["hard_already_p"]["route"] == "P"
    assert result["promoted_ids"] == ["hard_strong"]
    assert result["kind_route_counts"] == {"proxy_easy:L": 1, "swe_hard:L": 1, "swe_hard:P": 2}
