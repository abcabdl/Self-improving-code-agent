from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run_update(tmp_path: Path, memory: dict, summary: dict, policy: dict) -> dict:
    memory_path = tmp_path / "memory.json"
    summary_path = tmp_path / "r1" / "eval" / "summary.json"
    policy_path = tmp_path / "policy.json"
    output_path = tmp_path / "memory_r2.json"
    summary_path.parent.mkdir(parents=True)
    memory_path.write_text(json.dumps(memory), encoding="utf-8")
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    policy_path.write_text(json.dumps(policy), encoding="utf-8")

    subprocess.run(
        [
            sys.executable,
            "scripts/update_memory_q_values.py",
            "--memory",
            str(memory_path),
            "--summary",
            str(summary_path),
            "--policy",
            str(policy_path),
            "--output",
            str(output_path),
            "--alpha",
            "0.5",
        ],
        check=True,
    )
    return json.loads(output_path.read_text(encoding="utf-8"))


def test_policy_update_does_not_penalize_unattributed_p_failure(tmp_path: Path) -> None:
    memory = {
        "items": [
            {"instance_id": "mem_success", "q_value": 0.5},
            {"instance_id": "mem_failure_selected", "q_value": 0.5},
            {"instance_id": "mem_failure_unattributed_top", "q_value": 0.5},
            {"instance_id": "mem_l_empty", "q_value": 0.5},
        ]
    }
    summary = {
        "resolved_ids": ["target_success"],
        "unresolved_ids": ["target_failure_selected", "target_failure_unattributed"],
        "empty_patch_ids": ["target_l_empty"],
    }
    policy = {
        "call_log": [
            {
                "instance_id": "target_success",
                "route": "P",
                "large_model_called": True,
                "packet": {"selected_memory_ids": ["mem_1"]},
                "top_memories": [{"instance_id": "mem_success"}],
            },
            {
                "instance_id": "target_failure_selected",
                "route": "P",
                "large_model_called": True,
                "packet": {"selected_memory_ids": ["mem_1"]},
                "top_memories": [{"instance_id": "mem_failure_selected"}],
            },
            {
                "instance_id": "target_failure_unattributed",
                "route": "P",
                "large_model_called": True,
                "packet": {},
                "top_memories": [{"instance_id": "mem_failure_unattributed_top"}],
            },
            {
                "instance_id": "target_l_empty",
                "route": "L",
                "large_model_called": False,
                "packet": {},
                "top_memories": [{"instance_id": "mem_l_empty"}],
            },
        ]
    }

    output = run_update(tmp_path, memory, summary, policy)
    items = {row["instance_id"]: row for row in output["items"]}

    assert items["mem_success"]["q_value"] == 0.75
    assert items["mem_success"]["q_update_sources"] == ["packet_selected_success"]
    assert items["mem_failure_selected"]["q_value"] == 0.25
    assert items["mem_failure_selected"]["q_update_sources"] == ["p_route_failure"]
    assert items["mem_l_empty"]["q_value"] == 0.125
    assert items["mem_l_empty"]["q_update_sources"] == ["route_L_empty"]

    unattributed = items["mem_failure_unattributed_top"]
    assert unattributed["q_value"] == 0.5
    assert "q_update_sources" not in unattributed
    assert output["q_update_metadata"]["unattributed_events"][0]["source"] == "p_route_failure_unattributed"
    assert output["q_update_metadata"]["unattributed_events"][0]["top_memory_instance_ids"] == [
        "mem_failure_unattributed_top"
    ]

    assert items["mem_success"]["q_update_history"][0]["round"] == "r1"
