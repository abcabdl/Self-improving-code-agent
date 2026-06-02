import json

from scripts.update_strategy_memory import main


def test_strategy_update_changes_workflow_reflection_and_bandit(monkeypatch, tmp_path):
    strategy = {
        "schema_version": 1,
        "workflows": [{"workflow_id": "workflow:one", "q_value": 0.5}],
        "reflections": [{"reflection_id": "reflection:one", "q_value": 0.5}],
        "tool_bandit": {
            "global": {},
            "repos": {},
        },
    }
    summary = {
        "resolved_ids": ["repo__task"],
        "unresolved_ids": [],
    }
    usage = {
        "target_instance_id": "repo__task",
        "target_repo": "repo/project",
        "workflow_ids": ["workflow:one"],
        "reflection_ids": ["reflection:one"],
        "tool_priorities": [],
    }
    trajectory = {
        "messages": [
            {"role": "assistant", "extra": {"actions": [{"command": "grep -R symbol -n src"}]}},
            {"role": "assistant", "extra": {"actions": [{"command": "python -m pytest tests/test_fix.py"}]}},
        ]
    }
    strategy_path = tmp_path / "strategy.json"
    summary_path = tmp_path / "summary.json"
    usage_path = tmp_path / "usage.jsonl"
    output_path = tmp_path / "updated.json"
    run_dir = tmp_path / "run"
    traj_path = run_dir / "repo__task" / "repo__task.traj.json"
    traj_path.parent.mkdir(parents=True)
    strategy_path.write_text(json.dumps(strategy), encoding="utf-8")
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    usage_path.write_text(json.dumps(usage) + "\n", encoding="utf-8")
    traj_path.write_text(json.dumps(trajectory), encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "update_strategy_memory.py",
            "--strategy",
            str(strategy_path),
            "--summary",
            str(summary_path),
            "--run-dir",
            str(run_dir),
            "--usage-log",
            str(usage_path),
            "--output",
            str(output_path),
        ],
    )
    assert main() == 0

    updated = json.loads(output_path.read_text(encoding="utf-8"))
    assert updated["workflows"][0]["q_value"] == 0.75
    assert updated["reflections"][0]["q_value"] == 0.75
    assert updated["tool_bandit"]["repos"]["repo/project"]["search"]["q_value"] == 0.75
    assert updated["tool_bandit"]["repos"]["repo/project"]["test"]["q_value"] == 0.75
