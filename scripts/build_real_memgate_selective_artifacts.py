#!/usr/bin/env python3
"""Build artifacts for the real MemGate selective SWE-Bench condition.

This is the paper C condition:

* L rows use the small/local model's actual SWE-Bench patch trajectory.
* P rows use a large-model SWE-Bench run whose prompt is prefixed with the
  structured packet emitted by MemGate.

Unlike the accounting-only merge, this script never writes empty patches for L
rows.  It either merges real predictions or fails if a required prediction is
missing.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _clean_submitted_diff(text: str) -> str:
    if "<warning>" in text or "<output_head>" in text or "<output_tail>" in text:
        return ""
    marker = "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT"
    pos = text.find(marker)
    if pos < 0:
        return ""
    tail = text[pos + len(marker) :]
    diff_pos = tail.find("diff --git")
    if diff_pos < 0:
        return ""
    patch = tail[diff_pos:].strip()
    patch = re.split(r"\n</(?:output|content|tool)>", patch, maxsplit=1)[0].strip()
    if not all(token in patch for token in ("diff --git", "\n--- ", "\n+++ ", "\n@@")):
        return ""
    return patch + "\n"


def recover_submitted_patch(run_dir: Path, instance_id: str) -> str:
    traj_path = run_dir / instance_id / f"{instance_id}.traj.json"
    if not traj_path.exists():
        return ""
    try:
        trajectory = read_json(traj_path)
    except Exception:
        return ""
    candidates: list[str] = []
    for message in trajectory.get("messages", []):
        content = str(message.get("content", ""))
        patch = _clean_submitted_diff(content)
        if patch:
            candidates.append(patch)
    return candidates[-1] if candidates else ""


def route_for(row: dict[str, Any], *, use_fallback: bool) -> str:
    route = str(row.get("route", "L")).upper()
    fallback = str(row.get("fallback_route", route)).upper()
    if route == "P" or (use_fallback and fallback == "P"):
        return "P"
    return "L"


def packet_prefix(row: dict[str, Any]) -> str:
    packet = {
        "instance_id": row.get("instance_id", ""),
        "memgate_route": row.get("route", "L"),
        "fallback_route": row.get("fallback_route", row.get("route", "L")),
        "delegate_packet": row.get("packet", {}),
        "top_memories": row.get("top_memories", []),
        "controller_contract": [
            "Treat this packet as controller evidence, not as a patch.",
            "Verify current source and tests before editing.",
            "Use selected paths/tests as hints only when they match the current issue.",
            "Do not copy remembered code blindly.",
        ],
    }
    return (
        "<memgate_packet>\n"
        "A trained small memory controller selected DELEGATE_PACKET for this task.\n"
        "Use the structured packet below to focus localization, editing, testing, and verification.\n"
        f"{json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True)}\n"
        "</memgate_packet>"
    )


def build_policy_artifacts(
    *,
    instances_path: Path,
    policy_path: Path,
    output_dir: Path,
    use_fallback: bool,
) -> dict[str, Any]:
    ids = list(read_json(instances_path)["ids"])
    policy = read_json(policy_path)
    by_id = {str(row.get("instance_id")): row for row in policy.get("call_log", [])}

    call_log: list[dict[str, Any]] = []
    prefixes: dict[str, str] = {}
    delegate_ids: list[str] = []
    self_ids: list[str] = []
    for instance_id in ids:
        row = by_id.get(instance_id, {"instance_id": instance_id, "route": "L"})
        route = route_for(row, use_fallback=use_fallback)
        if route == "P":
            delegate_ids.append(instance_id)
            prefixes[instance_id] = packet_prefix(row)
        else:
            self_ids.append(instance_id)
        call_log.append(
            {
                "instance_id": instance_id,
                "route": route,
                "large_model_called": route == "P",
                "memgate_route": str(row.get("route", "L")),
                "fallback_route": str(row.get("fallback_route", row.get("route", "L"))),
                "packet": row.get("packet", {}),
                "top_memories": row.get("top_memories", []),
            }
        )

    summary = {
        "artifact_type": "real_memgate_packet_selective_policy",
        "source_policy": str(policy_path),
        "route_rule": "route_or_fallback_P" if use_fallback else "route_P_only",
        "rows": len(ids),
        "large_model_rows": len(delegate_ids),
        "no_call_rows": len(self_ids),
        "large_model_ids": delegate_ids,
        "self_local_ids": self_ids,
        "call_log": call_log,
    }
    write_json(output_dir / "delegate_instances.json", {"ids": delegate_ids})
    write_json(output_dir / "task_prefixes.json", prefixes)
    write_json(output_dir / "call_policy_summary.json", summary)
    return summary


def merge_predictions(
    *,
    instances_path: Path,
    policy_path: Path,
    self_run_dir: Path,
    delegate_run_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    ids = list(read_json(instances_path)["ids"])
    policy = read_json(policy_path)
    self_preds = read_json(self_run_dir / "preds.json")
    delegate_preds = read_json(delegate_run_dir / "preds.json")
    route_by_id = {str(row["instance_id"]): str(row["route"]) for row in policy.get("call_log", [])}

    merged: dict[str, Any] = {}
    missing: list[str] = []
    recovered: list[str] = []
    for instance_id in ids:
        route = route_by_id.get(instance_id, "L")
        source = delegate_preds if route == "P" else self_preds
        if instance_id not in source:
            missing.append(instance_id)
            continue
        row = dict(source[instance_id])
        if not str(row.get("model_patch", "")).strip():
            run_dir = delegate_run_dir if route == "P" else self_run_dir
            recovered_patch = recover_submitted_patch(run_dir, instance_id)
            if recovered_patch:
                row["model_patch"] = recovered_patch
                row["model_name_or_path"] = str(row.get("model_name_or_path", "")) + "+submitted_diff_recovered"
                recovered.append(instance_id)
        suffix = "+memgate_packet_P" if route == "P" else "+memgate_self_L"
        row["model_name_or_path"] = str(row.get("model_name_or_path", "")) + suffix
        merged[instance_id] = row
    if missing:
        raise SystemExit("Missing predictions for real C merge: " + ", ".join(missing))

    write_json(output_dir / "preds.json", merged)
    summary = {
        "artifact_type": "real_memgate_packet_selective_merge",
        "rows": len(ids),
        "self_run_dir": str(self_run_dir),
        "delegate_run_dir": str(delegate_run_dir),
        "merged_predictions": str(output_dir / "preds.json"),
        "submitted_diff_recovered_ids": recovered,
        "submitted_diff_recovered": len(recovered),
    }
    write_json(output_dir / "merge_summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances-json", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--self-run-dir", type=Path)
    parser.add_argument("--delegate-run-dir", type=Path)
    parser.add_argument("--use-fallback-route", action="store_true")
    parser.add_argument("--merge", action="store_true")
    args = parser.parse_args()

    summary = build_policy_artifacts(
        instances_path=args.instances_json,
        policy_path=args.policy,
        output_dir=args.output_dir,
        use_fallback=args.use_fallback_route,
    )
    if args.merge:
        if args.self_run_dir is None or args.delegate_run_dir is None:
            raise SystemExit("--merge requires --self-run-dir and --delegate-run-dir")
        summary = {
            **summary,
            "merge": merge_predictions(
                instances_path=args.instances_json,
                policy_path=args.output_dir / "call_policy_summary.json",
                self_run_dir=args.self_run_dir,
                delegate_run_dir=args.delegate_run_dir,
                output_dir=args.output_dir,
            ),
        }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
