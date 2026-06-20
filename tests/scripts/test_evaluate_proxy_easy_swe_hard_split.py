import json
import sys

from scripts.evaluate_proxy_easy_swe_hard_split import main


def test_evaluate_proxy_easy_swe_hard_split_keeps_metrics_separate(tmp_path, monkeypatch):
    split_dir = tmp_path / "split"
    split_dir.mkdir()
    (split_dir / "manifest.json").write_text(
        json.dumps({"artifact_type": "proxy_easy_swe_hard_mixed_split"}),
        encoding="utf-8",
    )
    (split_dir / "mixed_rows.json").write_text(
        json.dumps(
            [
                {"id": "proxy_easy_a", "kind": "proxy_easy"},
                {"id": "hard_a", "kind": "swe_hard"},
                {"id": "hard_b", "kind": "swe_hard"},
            ]
        ),
        encoding="utf-8",
    )
    proxy_results = tmp_path / "proxy.jsonl"
    proxy_results.write_text(
        json.dumps(
            {
                "task_id": "proxy_easy_a",
                "has_action": True,
                "skill_match": True,
                "semantic_pass": True,
                "strict_score": 0.9,
                "usage": {"total_tokens": 101},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    swe_summary = tmp_path / "swe.json"
    swe_summary.write_text(
        json.dumps({"resolved_ids": ["hard_a"], "unresolved_ids": ["hard_b"], "empty_patch_ids": [], "error_ids": []}),
        encoding="utf-8",
    )
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {
                "call_log": [
                    {"instance_id": "proxy_easy_a", "route": "L", "large_model_called": False},
                    {"instance_id": "hard_a", "route": "P", "large_model_called": True, "total_tokens": 1000},
                    {"instance_id": "hard_b", "route": "L", "large_model_called": False},
                ]
            }
        ),
        encoding="utf-8",
    )
    run_dir = tmp_path / "large"
    traj_dir = run_dir / "hard_a"
    traj_dir.mkdir(parents=True)
    (traj_dir / "hard_a.traj.json").write_text(
        json.dumps(
            {
                "info": {"model_stats": {"api_calls": 3, "instance_cost": 0.12}},
                "messages": [
                    {"extra": {"response": {"usage": {"prompt_tokens": 7, "completion_tokens": 5, "total_tokens": 12}}}},
                    {"extra": {"response": {"usage": {"prompt_tokens": 11, "completion_tokens": 13, "total_tokens": 24}}}},
                ],
            }
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "out"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "evaluate_proxy_easy_swe_hard_split.py",
            "--split-dir",
            str(split_dir),
            "--proxy-easy-results",
            str(proxy_results),
            "--swe-summary",
            str(swe_summary),
            "--call-policy",
            str(policy),
            "--large-run-dir",
            str(run_dir),
            "--out-dir",
            str(out_dir),
            "--condition",
            "unit",
        ],
    )

    assert main() == 0

    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["proxy_easy"]["passed"] == 1
    assert summary["swe_hard"]["resolved"] == 1
    assert summary["route"]["swe_hard_missed_delegate"] == 1
    assert summary["route"]["large_total_tokens"] == 36
    assert summary["route"]["large_api_calls"] == 3
    assert summary["route"]["large_dollar_cost"] == 0.12
    assert summary["mixed_units"]["proxy_pass_plus_swe_resolved"] == 2
    assert summary["mixed_units"]["route_correct_success"] == 2
