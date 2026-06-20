import json
import sys
from pathlib import Path

from scripts.build_proxy_easy_swe_hard_split import main


def test_build_proxy_easy_swe_hard_split_selects_passing_proxy_rows(tmp_path, monkeypatch):
    proxy_results = tmp_path / "proxy.jsonl"
    proxy_results.write_text(
        "\n".join(
            json.dumps(row)
            for row in [
                {
                    "task_id": "proxy_easy_pass_a",
                    "suite": "proxy_easy",
                    "expected_skill": "locate",
                    "strict_score": 0.92,
                    "has_action": True,
                    "skill_match": True,
                    "semantic_pass": True,
                    "usage": {"total_tokens": 111},
                },
                {
                    "task_id": "proxy_easy_low",
                    "suite": "proxy_easy",
                    "expected_skill": "edit",
                    "strict_score": 0.7,
                    "has_action": True,
                    "skill_match": True,
                    "semantic_pass": True,
                    "usage": {"total_tokens": 222},
                },
                {
                    "task_id": "proxy_easy_pass_b",
                    "suite": "proxy_easy",
                    "expected_skill": "test",
                    "strict_score": 1.0,
                    "has_action": True,
                    "skill_match": True,
                    "semantic_pass": True,
                    "usage": {"total_tokens": 123},
                },
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    hard_instances = tmp_path / "hard.json"
    hard_instances.write_text(json.dumps({"ids": ["hard_1", "hard_2", "hard_3"]}), encoding="utf-8")
    output_dir = tmp_path / "out"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_proxy_easy_swe_hard_split.py",
            "--proxy-easy-results",
            str(proxy_results),
            "--hard-instances",
            str(hard_instances),
            "--output-dir",
            str(output_dir),
            "--easy-count",
            "1",
            "--hard-count",
            "2",
            "--min-strict-score",
            "0.85",
        ],
    )

    assert main() == 0

    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    mixed_rows = json.loads((output_dir / "mixed_rows.json").read_text(encoding="utf-8"))
    assert manifest["selected_easy_ids"] == ["proxy_easy_pass_b"]
    assert manifest["selected_hard_ids"] == ["hard_1", "hard_2"]
    assert manifest["counts"]["proxy_easy_pass"] == 2
    assert [row["kind"] for row in mixed_rows] == ["proxy_easy", "swe_hard", "swe_hard"]
