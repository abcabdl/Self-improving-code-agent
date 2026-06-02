import json

from scripts.report_continual_swe import summarize


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_continual_report_transfer_and_cost(tmp_path):
    run_dir = tmp_path / "batch_01" / "updated_memory_run"
    no_memory_run_dir = tmp_path / "batch_01" / "no_memory_run"
    frozen_run_dir = tmp_path / "batch_01" / "frozen_memory_run"
    instance_ids = ["repo__a", "repo__b", "repo__c"]

    _write_json(
        tmp_path / "batch_01" / "updated.json",
        {"resolved_ids": ["repo__a", "repo__b"], "unresolved_ids": ["repo__c"], "empty_patch_ids": [], "error_ids": []},
    )
    _write_json(
        tmp_path / "batch_01" / "no_memory.json",
        {"resolved_ids": ["repo__a"], "unresolved_ids": ["repo__b", "repo__c"], "empty_patch_ids": [], "error_ids": []},
    )
    _write_json(
        tmp_path / "batch_01" / "frozen.json",
        {"resolved_ids": ["repo__b", "repo__c"], "unresolved_ids": ["repo__a"], "empty_patch_ids": [], "error_ids": []},
    )

    _write_json(
        run_dir / "repo__a" / "repo__a.traj.json",
        {
            "messages": [{"extra": {"actions": [{"command": "pytest tests/test_a.py"}, {"command": "sed -n '1,20p' a.py"}]}}],
            "info": {"model_stats": {"instance_cost": 0.25, "api_calls": 3}},
        },
    )
    _write_json(
        run_dir / "repo__b" / "repo__b.traj.json",
        {
            "messages": [{"extra": {"actions": [{"command": "rg parser"}, {"command": "python -m pytest tests/test_b.py"}]}}],
            "info": {"model_stats": {"instance_cost": 0.50, "api_calls": 4}},
        },
    )
    _write_json(
        no_memory_run_dir / "repo__a" / "repo__a.traj.json",
        {
            "messages": [{"extra": {"actions": [{"command": "rg bug"}]}}],
            "info": {"model_stats": {"instance_cost": 0.10, "api_calls": 1}},
        },
    )
    _write_json(
        frozen_run_dir / "repo__b" / "repo__b.traj.json",
        {
            "messages": [{"extra": {"actions": [{"command": "pytest"}]}}],
            "info": {"model_stats": {"instance_cost": 0.20, "api_calls": 2}},
        },
    )

    manifest = tmp_path / "manifest.json"
    _write_json(
        manifest,
        {
            "batches": [
                {
                    "name": "batch_01",
                    "instance_ids": instance_ids,
                    "updated_run_dir": "batch_01/updated_memory_run",
                    "updated_summary": "batch_01/updated.json",
                    "no_memory_run_dir": "batch_01/no_memory_run",
                    "no_memory_summary": "batch_01/no_memory.json",
                    "frozen_run_dir": "batch_01/frozen_memory_run",
                    "frozen_summary": "batch_01/frozen.json",
                }
            ]
        },
    )

    rows, totals = summarize(manifest)
    row = rows[0]

    assert row["updated_solved"] == 2
    assert row["vs_no_memory_positive_transfer"] == 1
    assert row["vs_no_memory_negative_transfer"] == 0
    assert row["vs_frozen_positive_transfer"] == 1
    assert row["vs_frozen_negative_transfer"] == 1
    assert row["updated_total_cost"] == 0.75
    assert row["updated_api_calls"] == 7
    assert row["updated_tool_calls"] == 4
    assert row["updated_test_runs"] == 2
    assert row["no_memory_total_cost"] == 0.10
    assert row["frozen_total_cost"] == 0.20
    assert totals["updated_solved"] == 2
    assert totals["updated_avg_tool_calls"] == 2.0
    assert totals["no_memory_avg_tool_calls"] == 1.0
