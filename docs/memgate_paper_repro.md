# MemGate Paper Reproduction Notes

This repository keeps the code path needed to reproduce the MemQ/MemGate paper
experiments without checking in large local artifacts.  Large outputs, training
data, trajectories, and checkpoints are intentionally excluded from Git.

## Main Code Paths

- `src/minisweagent/run/benchmarks/memory.py`: memory loading, retrieval, and
  atom-direct routing helpers.
- `src/minisweagent/agents/default.py`: guarded SWE-bench agent runtime used by
  the local/self-handle runs.
- `scripts/update_memory_q_values.py`: Q-value update utility.  With
  `--policy`, MemGate collaboration rounds credit only packet-selected memories
  used on `P` routes and apply a stronger penalty to `route=L` empty patches.
- `scripts/run_matched_swebench_main_table.py`: matched SWE-bench launcher for
  the main no-memory, strong-memory, and selective conditions.
- `scripts/summarize_memory_covered_main_table.py` and
  `scripts/summarize_matched_swebench_main_table.py`: summarize the table rows
  used in the paper.
- `scripts/build_memgate_retrieval_policy.py`,
  `scripts/run_unified_mixed_route_policy.py`, and
  `scripts/apply_hard_recall_protection_policy.py`: rebuild and post-process
  the unified MemGate routing policy.
- `scripts/build_proxy_easy_swe_hard_split.py` and
  `scripts/evaluate_proxy_easy_swe_hard_split.py`: construct and evaluate the
  mixed easy/hard split used for routing diagnostics.

## Artifact Policy

The following are local-only and should not be committed:

- `data/`
- `runs/`
- `logs/`
- root-level prediction JSON files
- model checkpoints and downloaded base models

For archival, store these separately as paper evidence/checkpoint bundles.
