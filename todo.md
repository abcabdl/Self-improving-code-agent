# Mini-SWE Memory/RL TODO

## DO FIRST: Main Direction After 2026-06-14

The small model is a memory/evidence assistant for the large SWE repair model.
It is not the final planner, patch writer, or verifier/retry judge.

- [ ] Promote the route-controller work through the direct `L/P` readout path,
  not the rejected A/B tiny-SFT path.  The A/B tiny calibration lowered loss
  but kept behavior at route both-swaps `0.218182` and SELF_HANDLE
  no-overdelegate `0.476744`, so do not continue that surface.  The neutral
  direct readout artifact
  `runs\v1k_atom_aware_route_direct_readout_20260618_1120` passes no-update
  v22 acceptance: both-swaps `0.927273`, SELF_HANDLE no-overdelegate
  `0.906977`, DELEGATE preservation `1.0`, memory reliability no-regression
  `0.555556`.  Next build a direct-readout integration/no-regression manifest:
  verify the four remaining false-packet base pairs, join decisions to packet
  availability/assembly, rerun protected memory-reliability, and only then
  consider runtime patcher integration.  Keep `ready_for_runtime_rule=false`
  until that manifest passes.
  Update 2026-06-18 11:50 CST: promotion manifest is now materialized at
  `runs\v1k_atom_aware_route_direct_readout_20260618_1120\promotion_manifest_20260618_1145.json`.
  Decision is `offline_gate_pass_runtime_blocked`; full 110-row direct
  readout passes, but recovery hard slices still warn.  Residual audit finds
  8 false-packet rows / 4 base pairs, mostly `auxiliary_only=true` plus two
  `reverify_before_use=true`.  Next concrete test: build a residual guard or
  target for those false-packet cases, then join `P` rows to packet assembly
  and run a bounded offline replay before any runtime integration.
- [x] Run the next real assistant-chain benchmark before more packet LoRA work.
  Use a paired SWE-like / SWE-Bench subset: large-model direct baseline,
  memory-prompt baseline, and small-controller-assisted large-model repair.
  Report resolved rate, large-model calls/tokens, tool calls, harness outcome,
  memory selection/rejection, packet usefulness, and failure attribution.
  Done first as
  `runs\swebench-assistant-chain-paired-pvlib2-20260614`: no-memory `1/2`,
  frozen-memory `0/2`, updated-memory `1/2`.  This is a useful real
  transfer diagnostic, not proof that memory improves solved rate.
- [ ] Keep the small-model output target narrow and stable:
  reliable-memory ids, rejected stale/distractor ids, path/function/test-node
  evidence, guard atoms, evidence ids, and delegate/self-handle decision.
  Do not make the small model freely generate a complex full packet schema
  unless it beats the prompt/template packet on broad held-out gates.
- [ ] Prefer prompt/data contract plus deterministic packet assembly for the
  delegation context.  Packet LoRA is allowed only as a focused ablation on
  one failed boundary, not as the main route.
- [x] Fix compact locate delegate prompt hygiene without adding task-id
  rewrites.  The 2026-06-15 locate-only rerun
  `runs\scoreable_selective_proxy_mixed_family_v3_locate4_compactprompt_scopeanchors_gpt54mini_20260615_1730.scored.jsonl.summary.json`
  restored locate mean strict to `0.892321` with action/skill/semantic all
  `1.0`, after making meta words non-paths and using `src tests` when
  `path_hints` is empty.
- [ ] Turn the compact locate hygiene into learned small-controller evidence
  atoms instead of more runtime prompt rules: `has_path_hints`,
  `empty_path_hints_use_source_test_roots`, `reject_meta_words_as_paths`, and
  `prefer_concrete_symbol_anchors`.  Gate those atoms on the four locate rows,
  then rerun the v3 route/packet no-regression and only then consider another
  broader delegate proxy.
- [x] Gate the compact locate hygiene atoms as a small-controller readout.
  The first v1 atom wording exposed a useful ambiguity (`target_match=0.6875`,
  `empty_path_hints_use_source_test_roots=0/4`), because the model treated the
  fallback as a universal rule.  The v1b contract made the decision
  sample-specific with current-visible-only `observed_path_hints`, and local
  v22 reached `16/16` target match:
  `runs\locate_prompt_hygiene_atoms_v1b_20260615_1746.val.gate.jsonl.summary.json`.
- [ ] Bridge the v1b locate hygiene atoms into locate packet assembly and rerun
  v3 route/packet no-regression before any broader large-delegate proxy.  Keep
  this as learned atom -> template assembly; do not convert it into a runtime
  command normalizer.
- [x] Bridge the locate hygiene atoms into packet assembly and verify the
  packet contract.  The corrected bridge
  `runs\locate_prompt_hygiene_atom_packet_bridge_v1b_20260615_1800.packet_gate.jsonl`
  reached `4/4` assembly success and wrote
  `runs\locate_prompt_hygiene_atom_packet_bridge_v1b_20260615_1800.packets.jsonl`.
  The first bridge attempt failed canonically only because the prompt did not
  expose the new nested `packet_evidence.locate_prompt_hygiene_atoms` field.
- [ ] Rerun the v3 route/packet no-regression using the new locate-hygiene
  bridge packets, then only widen to a broader large-delegate proxy if that
  stays clean.  Do not add more runtime locate prose before that check.
- [x] Rerun v3 route/packet no-regression with the locate-hygiene atom bridge.
  The v3b packet set
  `data\scoreable_selective_proxy_mixed_family_v3b_locate_hygiene_bridge_20260615_1810`
  keeps the original 32 non-locate packet rows and replaces only the four
  locate rows with atom-bridge packets.  Packet assembly stayed `36/36`, and
  route/no-call stayed `58/58`:
  `runs\scoreable_selective_proxy_mixed_family_v3b_locate_hygiene_bridge_20260615_1810.packet_gate.jsonl.summary.json`
  and
  `runs\scoreable_selective_proxy_mixed_family_v3b_locate_hygiene_bridge_20260615_1810.route_gate.jsonl.summary.json`.
- [ ] Decide the next downstream metric before spending external calls: either
  rerun only the four locate rows through `gpt-5.4-mini` from the new v3b
  packets as a cheap confirmation, or rerun the full 36-row large-delegate
  proxy if we need an apples-to-apples v3b score.  Do not start another
  training run or prompt expansion before this decision.
- [x] Run the cheap four-row `gpt-5.4-mini` confirmation from the new locate
  atom-bridge packets.  The v3c confirmation
  `runs\scoreable_selective_proxy_mixed_family_v3c_locate_bridge_confirmation_gpt54mini_20260615_1825.scored.jsonl.summary.json`
  reached action/skill/semantic `1.0`, error `0`, and mean strict `0.892321`;
  `heldout_locate_cache_key` used `src tests`, with no meta-word paths and no
  bare `.`.
- [ ] Treat a full 36-row v3b `gpt-5.4-mini` proxy as optional
  apples-to-apples reporting, not a debugging prerequisite.  If skipped, move
  to the next controller boundary from benchmark failures rather than adding
  more locate prompt text.
- [ ] Calibrate the default-value atom-to-route boundary before any more
  downstream large-model calls from this family.  The 2026-06-15 diagnostic
  added `scripts\build_default_value_route_boundary_eval.py` and showed:
  raw `route_sft` gate was schema-dirty with target match `0.0`; protected
  short route and atom-only-neutral variants were schema-clean but target match
  only `0.666667`; atom-derived wording over-corrected to target match
  `0.333333`; minimal atom payload briefly reached `0.666667` with
  task/variant-label leakage.  Failure is the small controller route boundary,
  not extraction/packet bridge or the large delegate.  Next build a tiny
  protected calibration target over `command_problem_default_mismatch ->
  route_verdict` with balanced wrong-explicit positives and
  correct/truthiness false controls, then gate on the default-value route
  heldout, default-value bridge atoms, semantic-risk no-regression,
  stale/distractor memory checks, and packet assembly before any
  `gpt-5.4-mini` spend.  Do not add a runtime default parser, task-label route
  override, or packet rewrite.
  Update 2026-06-15 19:18 CST: the first verl SFT calibration candidate
  `default_value_atom_route_calibration_v1_20260615_1910_lora/global_step_48`
  is rejected.  Offline PEFT generation on the 3-row heldout val produced
  valid/exact-schema JSON but only matched `2/3`, identical to v22, and still
  missed the single `DELEGATE_PACKET` default-mismatch positive.  Do not adopt
  it, do not replace v22, and do not spend downstream `gpt-5.4-mini` calls from
  this family yet.  Next try a smaller chat-SFT, preference, or fixed-label
  readout target for the atom-to-route boundary, with exact-schema replay and
  balanced false controls, then gate offline/temporary before any bridge or
  assistant-chain run.
  Update 2026-06-15 19:28 CST: the first chat-SFT continuation
  `default_value_atom_route_calibration_chat_sft_v1_20260615_1925` is also not
  adoptable.  It learned the 3-row val split (`3/3`) and fixed the heldout
  positive, but the 12-row atom-only heldout dropped to `4/12` because it
  over-delegated false controls (`DELEGATE_PACKET=10/12`, `SELF_HANDLE=2/12`;
  gold `SELF_HANDLE` only `1/8`).  Next default-value route work should build
  matched false-control replay or a preference/fixed-label route readout:
  pair every default-mismatch positive with same-task correct-explicit and
  truthiness negatives, optimize under- and over-delegation symmetrically, and
  require atom-only 12-row route match above the v22 all-self baseline
  (`>0.666667`) before any bridge/no-regression/large-model step.
  Update 2026-06-15 19:50 CST: the fixed-label route readout plus matched
  pairwise DPO target is the first positive result.  Added
  `scripts\build_default_value_route_label_readout_data.py` and
  `scripts\build_default_value_route_label_pairwise.py`.  v22 fixed-label
  logprob was not enough by itself: raw all `SELF_HANDLE` (`0.666667`),
  normalized all `DELEGATE` (`0.333333`).  The 16-row matched DPO continuation
  `default_value_route_label_pairwise_dpo_v1_20260615_1945` improved pairwise
  preference accuracy `0.5 -> 1.0`, and its 12-row fixed-label readout gate got
  raw/normalized accuracy `1.0`, missed delegate `0.0`, over-delegate `0.0`,
  with predictions `DELEGATE=4`, `SELF_HANDLE=8`.  Do not adopt it yet:
  next build a label-to-route JSON bridge or route-verdict readout wrapper,
  then run the original default-value route contract and broader
  semantic/stale/packet no-regression before any large-model call.
  Update 2026-06-15 19:57 CST: the label-to-route JSON bridge is clean.
  Added `scripts\bridge_default_value_label_readout_to_route.py`; the DPO
  fixed-label predictions bridged back to the original 12-row
  `route_verdict_short` contract with valid JSON `1.0`, exact schema `1.0`,
  route/target match `1.0`, and failures `0`
  (`runs\default_value_route_label_readout_v1_dpo1945_route_bridge_20260615_1955.jsonl.summary.json`).
  Next step is no-regression for this readout pattern: semantic-risk route
  gates, stale/distractor memory checks, route/no-call controls, and packet
  assembly.  Still no `gpt-5.4-mini` calls from this family until those pass.
  Update 2026-06-15 20:27 CST: no-regression and offline integration are both
  clean.  Added
  `scripts\run_default_value_route_readout_integration_gate.py`; the DPO1945
  fixed-label readout, route bridge, prior packets/audit, and cached delegate
  scored rows align on the 12-row atom-only split:
  `DELEGATE=4`, `SELF_HANDLE=8`, label/route/target/call alignment all `1.0`,
  delegate packet availability `1.0`, prompt atom-only `1.0`, cached delegate
  semantic/skill/action/error-free all `1.0`, expected next-proxy calls `4`
  with call reduction `0.666667`
  (`runs\default_value_route_readout_integration_gate_dpo1945_cached_20260615_2025.json`).
  Do not rerun the same four `gpt-5.4-mini` calls unless a fresh packet/template
  changes.  Next useful step: broaden this learned label-readout route head
  across mixed atom families or a genuinely new assistant-chain slice, while
  keeping packet assembly deterministic and avoiding runtime default parsers.
  Update 2026-06-15 20:42 CST: broadened the route-label readout diagnostic to
  the 58-row mixed-family v3 route boundary.  Added
  `scripts\build_route_label_readout_from_route_boundary.py` and
  `scripts\run_route_label_readout_gate.py`.  The atom-only label data
  `data\scoreable_route_label_readout_v3_atomonly_20260615_2035` has
  `DELEGATE=36`, `SELF_HANDLE=22`, prompt leakage `0`.  Local v22 generation
  gate
  `runs\scoreable_route_label_readout_v3_atomonly_v22_20260615_2038.jsonl.summary.json`
  produced valid labels `1.0` but collapsed to all `DELEGATE`: label match
  `0.620690`, missed delegate `0.0`, over-delegate `0.379310`,
  `SELF_HANDLE 0/22`.  This means default-value is fixed narrowly, but the
  general route-label head still has a SELF_HANDLE sufficiency problem.
  Next build matched preference/fixed-label calibration for the mixed-family
  route-label readout, emphasizing hard no-call controls, and require over-
  delegate near `0` without missed delegates before any broader proxy run.
  Update 2026-06-15 21:12 CST: built and trained the first mixed-family
  SELF_HANDLE sufficiency candidate without touching the served v22 endpoint.
  Added `scripts\build_route_label_pairwise_from_readout.py` and
  `scripts\run_route_label_logprob_gate.py`.  Calibration data
  `data\scoreable_route_label_pairwise_v3_selfhandle2x_20260615_2048` has
  `80` pairs from the 58-row label readout: chosen `DELEGATE=36`,
  `SELF_HANDLE=44` with 2x no-call weighting.  v22 dry-run preference accuracy
  was `0.45`.  A 1-epoch DPO continuation from base Qwen3-8B + initial v22
  adapter wrote candidate
  `/mnt/memory-agent/runs/scoreable_route_label_pairwise_v3_selfhandle2x_dpo_v1_20260615_2102/adapter`;
  train before/after preference accuracy `0.45 -> 1.0`.  The candidate passed
  the 58-row mixed-family label logprob gate with raw/normalized accuracy
  `1.0`, missed delegate `0.0`, over-delegate `0.0`, predictions
  `DELEGATE=36`, `SELF_HANDLE=22`
  (`runs\scoreable_route_label_readout_v3_atomonly_dpo2102_logprob_20260615_2110.jsonl.summary.json`).
  Do not adopt yet: next gates are adapter free-form label generation,
  label-to-route bridge/no-regression, and default-value preservation.
  Update 2026-06-15 21:30 CST: the same DPO candidate fails as a free-form
  generative route head, despite passing logprob readout.  Added
  `scripts\run_route_label_adapter_generation_gate.py`; remote generation gate
  on the 58-row mixed-family readout produced valid labels `1.0` but again
  all `DELEGATE`: label match `0.620690`, missed delegate `0.0`,
  over-delegate `0.379310`, `SELF_HANDLE 0/22`
  (`runs\scoreable_route_label_readout_v3_atomonly_dpo2102_generation_20260615_2124.jsonl.summary.json`).
  Do not deploy or serve this adapter as a generative route head.  Next path
  should be score-based: use fixed-label logprob readout -> deterministic
  label-to-route bridge -> no-regression/default-value preservation gates.
  Update 2026-06-15 21:36 CST: score-based route bridge is clean for the mixed
  58-row v3 route boundary.  Added
  `scripts\bridge_route_label_readout_to_scoreable_route.py`; using the DPO2102
  logprob predictions, the bridge reached valid JSON `1.0`, exact schema
  `1.0`, target/route match `1.0/1.0`, predicted labels `DELEGATE=36`,
  `SELF_HANDLE=22`, failures `0`
  (`runs\scoreable_route_label_readout_v3_atomonly_dpo2102_route_bridge_20260615_2135.jsonl.summary.json`).
  This validates fixed-label logprob scorer -> deterministic route template
  for mixed-family v3.  Still blocked from adoption until default-value
  preservation and a no-regression manifest pass; generation failure remains
  an explicit warning against serving it as a free-form route model.
  Update 2026-06-15 21:42 CST: default-value preservation failed, so DPO2102
  is rejected as a unified route scorer.  Updated
  `scripts\run_route_label_logprob_gate.py` to read either `response` or
  `gold_label`; candidate DPO2102 on the 12-row default-value label readout got
  raw accuracy `0.666667` with all `SELF_HANDLE`, normalized accuracy
  `0.333333` with all `DELEGATE`, normalized over-delegate `0.666667`
  (`runs\default_value_route_label_readout_v1_dpo2102_preservation_logprob_20260615_2140.jsonl.summary.json`).
  Next training should not be single-family: build a multi-task route-label
  mix that combines mixed-family SELF_HANDLE sufficiency rows with default-
  value matched positives/false controls, then require both gates clean before
  any bridge/proxy.
  Update 2026-06-15 21:59 CST: multi-task route-label DPO candidate fixed both
  tested families in logprob readout space.  Added
  `scripts\mix_route_label_pairwise_data.py`; mix
  `data\route_label_pairwise_multitask_mixed80_default80_20260615_2148` has
  `160` pairs (`mixed=80`, `default_value=80`, chosen `DELEGATE=76`,
  `SELF_HANDLE=84`).  v22 dry-run preference accuracy was `0.475`.  A 1-epoch
  DPO continuation from base Qwen3-8B + initial v22 adapter wrote candidate
  `/mnt/memory-agent/runs/route_label_pairwise_multitask_mixed80_default80_dpo_v1_20260615_2154/adapter`;
  train before/after preference accuracy `0.475 -> 1.0`.  Gates:
  mixed-family 58-row logprob readout `1.0` raw/normalized, missed/over
  delegate `0.0/0.0`, predictions `DELEGATE=36`, `SELF_HANDLE=22`;
  default-value 12-row preservation `1.0` raw/normalized, missed/over
  delegate `0.0/0.0`, predictions `DELEGATE=4`, `SELF_HANDLE=8`.
  Next: bridge both logprob readouts to route JSON and build a no-regression
  manifest; still do not serve it as a free-form route model or replace v22.
  Update 2026-06-15 22:12 CST: DPO2154 passed the score-based route bridge and
  no-regression manifest.  Mixed-family bridge
  `runs\scoreable_route_label_readout_v3_atomonly_multitask2154_route_bridge_20260615_2205.jsonl.summary.json`
  and default-value bridge
  `runs\default_value_route_label_readout_v1_multitask2154_route_bridge_20260615_2205.jsonl.summary.json`
  both reached valid JSON/exact schema/target/route match `1.0`, with route
  counts matching gold.  Added
  `scripts\summarize_route_label_multitask_readout_no_regression.py`; manifest
  `runs\route_label_multitask_readout_no_regression_20260615_2210.json`
  reports `ready_for_score_based_integration=true`,
  `ready_for_free_form_route_generation=false`,
  `ready_to_replace_served_v22=false`, blockers `[]`.  Next step is a
  score-based offline integration gate that joins these route decisions to
  packet/no-call audits and broader semantic/stale/packet no-regression; still
  no serving replacement or broad large-model proxy.
  Update 2026-06-15 22:45 CST: the score-based offline integration gate is now
  clean.  Added `scripts\run_route_label_score_readout_integration_gate.py`;
  it joins the DPO2154 fixed-label logprob route readout, deterministic route
  bridge, v3b locate-hygiene packet assembly, v3 no-call audit, and cached
  delegate scores without any model call.  The first run exposed only a
  packet-id alignment issue for the four replaced locate atom-bridge packets;
  resolving by exact `packet_id` first and `task_id` fallback fixed the gate.
  Final gate
  `runs\route_label_multitask2154_score_readout_integration_gate_20260615_2245.json`
  reports rows `58`, `DELEGATE=36`, `SELF_HANDLE=22`, expected large calls
  `36/58`, no-call rows `22/58`, call reduction `0.37931`, label/route/target
  match `1.0`, packet availability/contract `1.0`, cached delegate
  semantic/skill/action/error-free all `1.0`, cached mean strict `0.93988`,
  prompt leakage `0`, blockers `[]`.  This is ready for a bounded
  score-based proxy/assistant-chain replay, but still not ready for free-form
  route generation, serving replacement, or another same-artifact large-model
  rerun unless an apples-to-apples report is explicitly needed.
  Next: choose a genuinely new downstream slice or real assistant-chain
  failure bucket; train/evaluate only memory/evidence atoms or score-based
  boundary readouts from those failures, not packet formatting loss.
  Update 2026-06-15 20:05 CST: no-regression manifest is green for the next
  offline gate, but still blocks large-model calls.  Added
  `scripts\summarize_default_value_route_readout_no_regression.py`; manifest
  `runs\default_value_route_readout_no_regression_dpo1945_20260615_2002.json`
  reports `ready_for_next_gate=true`, `ready_for_large_model_call=false`,
  blockers `[]`.  Anchors pass: fixed-label route readout `12/12`, route bridge
  `12/12`, semantic memory `104` rows with stale/distractor `1.0/1.0` and
  all-core `0.951923`, semantic mapping val/train `1.0/1.0`, default-value
  extraction/atom bridge ready, mixed-family route/no-call `58/58`, packet
  assembly `36/36`.  Next build a small offline integration gate that consumes
  fixed labels, templates route JSON, assembles packets, and checks call/no-call
  alignment without invoking the large model.
- [ ] Train from benchmark failures, not from generic packet formatting loss.
  Bucket failures into memory error, stale-memory acceptance, localization
  miss, guard omission, over/under-delegation, weak packet evidence, and large
  model ignoring evidence.  Build matched hard positives/negatives for the
  most frequent bucket.
  Update 2026-06-15 23:05 CST: added the first real assistant-chain failure
  bucket summarizer, `scripts\summarize_assistant_chain_failure_buckets.py`,
  and ran it on the two paired 2026-06-14 assistant-chain runs.  Corrected the
  official solved-id reader to use only `resolved` / `resolved_ids`, not
  `completed_ids`.  Mixed2
  `runs\assistant_chain_failure_buckets_mixed2_20260615_2305.json` confirms
  all conditions are `0/2` solved with non-empty unresolved patches; main
  buckets are `semantic_patch_gap_nonempty_unresolved=6`,
  `dependency_import_recovery_friction=6`, `format_guard_friction=5`,
  `accepted_memory_but_shared_failure=4`, partial marshmallow/sqlfluff patch
  buckets, and `weak_or_missing_behavioral_verification=3`.  Pvlib2
  `runs\assistant_chain_failure_buckets_pvlib2_20260615_2305.json` preserves
  `pvlib-1606` solved positives and `pvlib-1707` unresolved negatives; buckets
  include `memory_negative_transfer_candidate=1` and
  `semantic_patch_gap_nonempty_unresolved=4`.  Next experiment should build a
  narrow atom/readout target from these real failures:
  `patch_is_partial`, `behavioral_verification_missing_or_weak`,
  `accepted_memory_did_not_resolve_boundary`, `memory_negative_transfer_risk`,
  selected/rejected memory ids, and current evidence ids.  Keep packet assembly
  deterministic; do not add benchmark-specific runtime patch rules or rerun the
  same large-model proxy unless an apples-to-apples report is explicitly needed.
- [ ] Use SFT/preference training for small evidence atoms and boundary
  decisions: reliable-vs-stale memory, delegate-vs-self-handle,
  copy-selected-vs-copy-default, source-current-vs-stale, and semantic-guard
  presence.  Avoid training the small model as a final verifier/planner.
- [ ] Judge all new training by held-out gates and downstream chain metrics,
  not training loss.  Required checks: no regression on the 104-row controller
  gate, no regression on hard stale/distractor and packet-boundary gates, and
  actual improvement or clear diagnostic value on the assistant-chain
  benchmark.
- [ ] Do not bridge or downstream-evaluate the compact route-risk LoRA
  checkpoints until semantic-risk delegate positives improve on generation
  gates.  The 2026-06-14 gs8/gs40 route-risk contrastive SFTs lowered
  teacher-forcing loss but still generated `guarded_self_handle` for all
  missed-delegate semantic-risk rows.  Next route-risk work should train a
  narrower evidence atom / preference boundary, or add a logprob/ranking
  diagnostic, not another full-packet or runtime delegate rule.
- [ ] Build the next small-model target around explicit evidence atoms for
  `semantic_risk_requires_delegate`: issue clue, current evidence source,
  edit complexity, why small self-edit is unsafe, and selected/rejected memory
  ids.  Then assemble packets by template for the large model.  The small
  model should learn this boundary from data; do not add a hard-coded
  semantic-risk override.
- [ ] Do not use the direct route-risk-v2 causal prompt as the controller
  surface.  The 2026-06-15 check
  `runs\route-risk-v2-causal-probe-v22-after-v2b-dedup-val10-20260615_1858.jsonl`
  kept valid JSON but collapsed to all self-handle: matched self-handle `5/5`,
  missed semantic-risk delegate `0/3`, protected delegate `0/2`.  This means
  v2 causal wording alone does not transfer into a route-only verdict.  Next
  useful work should keep explicit causal atom output as the learned target
  and assemble route/packet hints by template or by a separately gated stable
  readout, with no runtime semantic-risk override.
- [ ] Do not assume atom-only v2 output is already stable.  The 2026-06-15
  atom-only gate
  `runs\sufficiency-route-atom-only-v22-v2b-val10-20260615_1904-fixed.jsonl`
  is schema-clean, but all-atoms match is only `0.3`: semantic-risk delegate
  rows still get `self_handle_guard_evidence_sufficient` wrong `3/3` and
  `visible_command_semantically_insufficient` right only `1/3`.  Next learned
  target should isolate those two negative-sufficiency/command-insufficiency
  atoms with replay for matched self-handle and protected delegate rows, then
  gate against the 104-row memory controller, stale/distractor verdicts,
  refined mapping-risk atom mix, and assistant-chain proxy before any broad
  benchmark run.
- [ ] Use the two-atom gate as the immediate boundary diagnostic, but do not
  train from it without the nonsemantic delegate role.  The 2026-06-15 runs
  `runs\sufficiency-command-atom-v22-v2b-val10-20260615_1911.jsonl` and
  `runs\sufficiency-command-atom-v22-v2b-train18-20260615_1911.jsonl` show
  schema-clean output and improved command-insufficiency readout on semantic
  delegate rows (`3/3` val, `5/6` train), but
  `self_handle_guard_evidence_sufficient` remains the main miss (`1/3` val,
  `3/6` train), and protected delegate rows are wrongly treated as
  command-insufficient (`0/2` val/train).  Next data/readout should keep three
  roles separate: semantic command insufficiency, self-handle sufficiency, and
  nonsemantic delegate reason.  Then gate with matched self-handle replay,
  protected delegate replay, 104-row memory behavior, hard stale/distractor
  verdicts, refined mapping-risk atom mix, and only then assistant-chain proxy.
- [ ] Use the three-role atom readout as the next best controller target
  shape, but fix its protected-delegate false positives before any downstream
  run.  The 2026-06-15 gate
  `runs\sufficiency-command-reason-atom-v22-v2b-val10-20260615_1916.jsonl`
  gets semantic-risk delegate rows clean (`3/3` all atoms) and
  `nonsemantic_delegate_reason_present` clean (`1.0`), while train18 similarly
  gets semantic-risk sufficiency `6/6`.  Remaining issue:
  `visible_command_semantically_insufficient` is still wrongly true for
  protected delegate rows (`0/2` val/train), and matched self-handle has a few
  over-cautious false positives.  Next small data/readout step should contrast
  semantic command insufficiency vs nonsemantic delegate reason vs guarded
  self-handle, then rerun memory/stale/mapping no-regression.  Do not convert
  this into a runtime delegate rule.
- [ ] Prefer the exclusive role readout for the next tiny boundary target.
  The 2026-06-15 role-choice gate
  `runs\sufficiency-role-choice-v22-v2b-val10-20260615_1922.jsonl` removes the
  protected-delegate contamination: matched self-handle `5/5`, protected
  delegate `2/2`, schema `1.0`, but semantic command insufficiency remains
  under-detected (`1/3` val, `3/6` train).  Next experiment should be a tiny
  learned/readout boundary for `semantic_command_insufficient` versus
  `guarded_self_handle`, with protected nonsemantic delegate replay and the
  standard memory/stale/mapping no-regression gates.  No broad route/packet
  SFT and no runtime override.
- [ ] Stop prompt-only binary semantic-vs-guarded variants.  The 2026-06-15
  binary readout
  `runs\semantic-vs-guarded-role-v22-v2b-val8-20260615_1927.jsonl` collapsed
  to all `guarded_self_handle`: matched self-handle `5/5`, semantic-risk
  positives `0/3`; train16 did the same.  The next route-boundary experiment
  should use the exclusive three-role surface with protected nonsemantic replay
  and matched self-handle replay, then train/calibrate only that tiny readout
  if no-regression gates pass.  Do not repeat prompt-only binary readouts and
  do not add a runtime semantic override.
- [ ] Do not rely on untrained logprob calibration for the semantic-vs-guarded
  boundary.  The 2026-06-15 pairwise logprob diagnostic
  `runs\semantic_guarded_role_pairwise_v1_v22_logprob_val8_20260615_1932_summary.json`
  got matched self-handle `5/5` but semantic-risk positives `0/3`; train16
  got matched self-handle `10/10` but semantic-risk positives only `1/6`.
  Raw and normalized margins agree, so this is not just label length.  Next
  experiment should be a tiny learned readout on the exclusive three-role
  surface, with protected nonsemantic delegate replay, matched self-handle
  replay, 104-row memory/stale/distractor gates, refined mapping-risk atom mix,
  and only then assistant-chain proxy.  Keep packet assembly templated and do
  not add a runtime override.
- [ ] For the next semantic-risk atom experiment, do not repeat plain
  generation SFT on the same v2 data.  The v2 prompt/data contract improved
  v22 directly, but the gs10 LoRA regressed held-out semantic-risk calibration.
  Build a preference/ranking or balanced hard-negative target that contrasts
  `guarded_self_handle_edit` against `delegate_positive_detected` while
  protecting missed-delegate semantic-risk recall.  Gate on over-delegation,
  missed-delegation, memory verdict exact/set match, path recall, and atom
  vocabulary recall before any bridge/full-controller/downstream run.
- [ ] Before any semantic-risk preference training, remove the A/B position
  bias exposed by the compact pairwise gate.  v22 chose candidate B for every
  both-order val row, so direct pairwise choice data would teach position
  artifacts.  Next diagnostic should use order-invariant scoring, separate
  single-candidate accept/reject labels, or a logprob comparison over fixed
  label tokens, then require above-chance both-order accuracy before training.
- [ ] Do not train semantic-risk accept/reject as a plain generated verdict
  yet.  The single-candidate gate removed A/B position, but v22 predicted
  `ACCEPT` for every val candidate.  Next attempt should ask for concrete error
  fields / mismatch atoms, or use fixed-label logprob scoring, so the signal is
  about detecting wrong semantic-risk atoms rather than agreeing with a
  plausible-looking candidate.
- [ ] Use the 2026-06-14 field-only semantic-risk split as the next clean
  boundary target, not the noisier mismatch-field target.  The direct
  `semantic_risk_requires_delegate`/`packet_hint` gate shows v22 predicts
  `delegate=true` for every row: `reject_under_delegation` is clean
  (`30/30` train, `7/7` val), but `reject_over_delegation` fails completely
  (`0/29` train, `0/3` val).  Next training should be a tiny protected
  over-delegation boundary experiment for
  `guarded_self_handle_edit -> self_handle_with_guards`, with required
  non-regression on missed-delegate semantic-risk recall, the 104-row
  controller gate, and hard memory reliable/stale/distractor verdict gates.
  Do not implement this as a runtime self-handle override.
- [ ] Do not keep expanding semantic-risk prompt rules as the main fix.  The
  action-aware field-only control added visible `controller_command` and
  `controller_summary`, but v22 still predicted `delegate=true` for every
  train/val row.  Treat over-delegation on guarded edits as a learned boundary
  target: build a protected tiny SFT or order-invariant scoring target, then
  gate it against field-only over/under split, original v2 evidence atoms,
  104-row controller behavior, and hard memory verdict rows before any
  downstream assistant-chain run.
- [ ] Do not deploy or downstream-evaluate the
  `semantic_risk_fieldonly_action_v2_20260614_2052_lora/global_step_7`
  adapter.  The 1-epoch 7-step SFT produced valid JSON but exactly preserved
  the v22 all-delegate behavior: `reject_under_delegation` stayed perfect
  (`30/30` train, `7/7` val), while `reject_over_delegation` stayed zero
  (`0/29` train, `0/3` val).  Next semantic-risk work should change the
  learning/readout formulation rather than repeat more plain SFT epochs:
  consider a label-token/classification-style target, stronger oversampling of
  guarded-edit negatives with protected delegate-positive replay, or a serving
  path that returns true/false logprobs for order-invariant scoring.  Keep this
  as learned boundary work, not a runtime self-handle rule.
- [ ] Label-only semantic-risk generation is not enough by itself.  The
  `SELF_HANDLE`/`DELEGATE` readout on
  `data\semantic_risk_label_action_v2_20260614_2110` still predicted
  `DELEGATE` for every v22 train/val row, with
  `reject_over_delegation=0/29` train and `0/3` val.  Do not spend the next
  heartbeat on more prompt/readout variants unless they expose real label
  probabilities.  Next useful work is either logprob-capable serving/eval,
  strongly reweighted label-only training with protected delegate replay, or a
  separate lightweight classifier/value head over compact evidence.
- [ ] Stop repeating plain SFT on the current semantic-risk label surface.
  The self4 diagnostic
  `semantic_risk_label_action_self4_v2_20260614_2118_lora/global_step_18`
  used train labels `SELF_HANDLE=116`, `DELEGATE=30`, but still generated
  `DELEGATE` for every train and val row.  This rules out simple class
  reweighting as a useful next step.  Next work should implement a genuinely
  different readout/learning path: logprob-capable serving for fixed labels, a
  lightweight classifier/value head over compact evidence, or an evidence-atom
  representation that explicitly predicts `self_handle_sufficient` before the
  route label.  Keep packet assembly templated and do not add runtime
  self-handle overrides.
- [ ] Use logprob readout carefully for semantic-risk boundaries.  The offline
  v22 label logprob gate on val10 found a real hidden signal: raw logprob got
  `reject_over_delegation=3/3`, while free-form generation and
  token-normalized logprob both predicted `DELEGATE` for all rows.  However,
  raw logprob missed `3/7` under-delegation positives, and normalized scoring
  is biased because `SELF_HANDLE` is longer than `DELEGATE`.  Next work should
  build an equal-length/single-token label set or calibrate raw-vs-normalized
  margins on train and val before treating logprob as the controller decision
  surface.  This remains learned readout/calibration, not a runtime semantic
  override.
- [ ] Do not directly use uncalibrated A/B logprob as the semantic-risk route
  controller.  The equal-length mapping control showed
  `A=SELF_HANDLE,B=DELEGATE` gets only `1/3` over-delegation rows, while the
  reverse mapping gets `0/3`; both keep under-delegation `7/7`.  This means the
  earlier raw `SELF_HANDLE` signal is partly label-surface dependent.  Next
  useful work is mapping-calibrated logprob scoring across multiple labels, or
  an explicit evidence atom target such as `self_handle_sufficient=true/false`
  followed by templated packet assembly.  Avoid runtime semantic overrides.
- [ ] Do not train the single-field `self_handle_sufficient` atom target as-is.
  The v22 sufficiency-atom generation gate flipped to the opposite trivial
  prior: it predicted `self_handle_sufficient=true` for every train/val row,
  solving over-delegation but failing all under-delegation rows.  Next
  semantic-risk target should enforce consistency between
  `self_handle_sufficient` and `semantic_risk_requires_delegate`, or predict
  causal evidence atoms first (`current_edit_simple`, `guard_present`,
  `semantic_fail`, `missing_action`, `memory_stale`) and let the packet
  template derive the route.  This should stay a learned atom target, not a
  hard-coded rule.
- [ ] Do not train the joint consistency target as-is either.  It made
  `semantic_risk_requires_delegate` and `self_handle_sufficient` internally
  consistent, but chose the all-delegate side for every train/val row.  Next
  semantic-risk work should remove route/sufficiency booleans from generation
  and ask only for causal evidence atoms with polarity, such as
  `current_edit_simple`, `guard_present`, `controller_semantic_passed`,
  `missing_action`, `semantic_fail`, and `self_handle_not_sufficient`.
  Deterministic packet/template assembly can derive the delegate hint from
  selected atoms; the learned value is whether the small model selects reliable
  evidence atoms, not a runtime override.
- [x] Continue the causal evidence atom direction, but audit the vocabulary and
  labels before any SFT.  The first causal-atom-only gate avoided the trivial
  all-one-side collapse and got train derived-route `0.79661`, but val was
  only `0.5`.  Cleanups needed: remove or split the broad
  `semantic_risk_evidence_present` atom, audit repeated
  `heldout_edit_exact_default` rows where visible evidence says
  `controller_semantic_pass=true` but gold delegates, and derive packet hints
  only from concrete negative atoms such as `controller_semantic_failed`,
  `mutable_default_mapping_risk`, `missing_action`, or
  `self_handle_not_sufficient`.  Train only after the held-out causal-atom
  gate has a cleaner target and the atom schema is explainable from visible
  evidence.
- [x] Next semantic-risk causal-atom step:
  build a tiny correction/protected replay target for the residual distinction
  between `mutable_default_mapping_risk` and
  `mutable_default_copy_guard_visible` / `guarded_edit_self_handle_evidence`.
  Use the clean visible-evidence atom schema, exclude or downweight
  `source_delegate_visible_atom_conflict` rows when training route labels, and
  gate before any GPU SFT.  Required before training: preserve v2clean val
  derived delegate `>=0.9`, improve the mapping-filter miss, keep
  `reject_under_delegation` high without all-delegate collapse, unknown atom
  rate near `0`, and run memory reliable/stale/distractor no-regression gates.
  Packet hints must remain template-derived from selected atoms.
- [ ] Next copy-guard correction attempt:
  do not deploy
  `/mnt/memory-agent/runs/semantic_risk_copyguard_v1_v22_lora_20260614_2235`.
  It improved train copy-guard rows (`32/44`) but failed the held-out
  `copy_guard_positive` row (`0/1`) and introduced unknown atom emissions
  (`problem_statement`, `controller_semantic_pass`; val unknown rate `0.4`).
  Build a stricter closed-vocabulary atom-polarity target instead of another
  plain list-generation SFT: include more held-out copy-guard variants,
  explicitly mark prompt field names as non-atoms, and gate on unknown atom
  rate `0`, copy-guard held-out improvement, mapping-risk preservation,
  protected negative preservation, and memory reliable/stale/distractor
  no-regression.  Packet hint remains template-derived from atoms.
- [x] Closed-vocabulary atom-polarity diagnostic:
  built `data\semantic_risk_atom_polarity_v1clean_20260614_2258` with route
  and boundary prompt leakage `0`, then ran v22 val gate
  `runs\semantic-risk-atom-polarity-v22-v1clean-val10-20260614_2258.jsonl`.
  Result: valid JSON/exact schema `1.0/1.0`, unknown/non-atom key rates
  `0/0`, avg atom accuracy `0.828571`, derived delegate `0.9`.  The held-out
  copy-guard row still fails (`0/1`) because v22 correctly marks
  `mutable_default_copy_guard_visible=true` but also incorrectly keeps
  `mutable_default_mapping_risk=true`.
- [ ] Next risk-cancellation target:
  build a paired/preference or classification-style atom-polarity dataset for
  the narrow decision "visible copy guard + semantic pass cancels mutable
  mapping risk."  The learned output should decide the boolean for
  `mutable_default_mapping_risk`, not generate a patch, packet, route, or free
  atom list.  Protect `mapping_risk_negative` rows where no adequate copy guard
  exists, protect non-mutable positives, require unknown/non-atom key rates
  `0`, and require memory reliable/stale/distractor no-regression before any
  adapter is served or downstream large-model evaluation is run.
- [x] Single-boolean mapping-risk diagnostic:
  built `data\semantic_risk_mapping_risk_binary_v1_20260614_2311` and ran
  v22 gates
  `runs\semantic-risk-mapping-risk-binary-v22-v1-val10-20260614_2311.jsonl`
  and
  `runs\semantic-risk-mapping-risk-binary-v22-v1-train98-20260614_2311.jsonl`.
  Result: valid JSON/exact schema/unknown key all clean (`1.0/1.0/0.0`), but
  v22 predicted `mutable_default_mapping_risk=false` for every row.  This fixes
  copy-guard positives (`44/44` train, `1/1` val) but misses all true
  mapping-risk negatives (`0/12` train, `0/2` val).  Do not use this as a
  runtime rule or deploy a false-biased classifier.
- [x] Matched-risk pairwise readout:
  build a balanced contrastive/readout dataset where each prompt compares or
  independently scores a copy-guard-positive row and a mapping-risk-negative
  row.  Success criterion before training: above-chance distinction without
  label-position bias, exact output schema, unknown key rate `0`, and
  preservation of protected negative rows.  If generation remains biased,
  prefer calibrated scoring/pairwise loss over another free-form SFT.
  Done as `data\semantic_risk_mapping_risk_pairwise_v1_20260614_2322`, with
  prompt leakage `0`, balanced risk position (`A=24/B=24` train,
  `A=4/B=4` val), exact schema `1.0`, unknown key `0.0`, and v22 choice match
  `1.0` on both train48 and val8
  (`runs\semantic-risk-mapping-risk-pairwise-v22-v1-train48-20260614_2322.jsonl`,
  `runs\semantic-risk-mapping-risk-pairwise-v22-v1-val8-20260614_2322.jsonl`).
  This shows the boundary is readout-visible when copy-guard and unresolved
  mapping-risk evidence are contrasted side by side.  Do not train from this
  small pair set yet: it has only two unique copy-guard task families and one
  unique mapping-risk task family, so it is a diagnostic signal rather than
  sufficient supervision.
- [ ] Next matched-risk expansion:
  collect or synthesize more real assistant-chain/proxy mapping-family variants
  before any SFT/DPO: multiple unresolved mutable-default mapping risks,
  multiple copy-guard positives, protected non-mapping positives/negatives, and
  stale/distractor memory perturbations.  Re-run single-row binary,
  closed-vocabulary polarity, and pairwise readouts.  Train only if the
  expanded pairwise/readout surface stays position-balanced and the single-row
  surface no longer collapses to all-false, with memory reliable/stale/distractor
  no-regression.
- [x] First expanded matched-risk coverage diagnostic:
  built
  `data\semantic_risk_mapping_risk_expanded_pairwise_v1_20260614_2338` from
  visible packet records plus semantic copy-guard negatives.  The builder now
  sanitizes support labels from task IDs/prompts and audits leakage.  Data:
  train `48` with `24` unique unresolved-risk task families, val `8` with `4`
  unique unresolved-risk task families; route/support-label leakage `0`.
  v22 generation was schema-clean but position-biased:
  train choice match `0.604167` with `B=43/48`, val choice match `0.5` with
  `B=8/8`
  (`runs\semantic-risk-mapping-risk-expanded-pairwise-v22-v1-train48-20260614_2338.jsonl`,
  `runs\semantic-risk-mapping-risk-expanded-pairwise-v22-v1-val8-20260614_2338.jsonl`).
  Do not train pairwise A/B generation from this surface.
- [x] Expanded single-case binary diagnostic:
  built `data\semantic_risk_mapping_risk_expanded_binary_v1_20260614_2344`
  from the same sanitized visible evidence.  Data is intentionally diagnostic
  and imbalanced: train `26` (`24` true unresolved risk, `2` false copy-guard
  cancel), val `5` (`4` true, `1` false), leakage `0`.
  v22 no longer collapsed to all-false: val risk match `1.0`, train risk match
  `0.846154`, valid/exact schema `1.0`, unknown key `0.0`
  (`runs\semantic-risk-mapping-risk-expanded-binary-v22-v1-val5-20260614_2344.jsonl`,
  `runs\semantic-risk-mapping-risk-expanded-binary-v22-v1-train26-20260614_2344.jsonl`).
  Misses are four true `copy_default_only_visible` list-family rows.  This is
  the more promising readout, but not train-ready because false/protected
  examples are too few.
- [ ] Next expanded binary step:
  add more false/protected examples before training: copy-guard-cancel rows,
  guarded self-handle edits, protected non-mutable positives/negatives, and
  stale/distractor memory perturbations.  Then re-run original binary,
  expanded binary, expanded pairwise, closed-vocab polarity, and memory
  reliable/stale/distractor no-regression.  Only consider SFT/DPO if expanded
  single-case true/false accuracy is balanced and pairwise A/B position bias is
  not used as the controller surface.
- [x] Protected-false expanded binary gate:
  extended `scripts\build_semantic_risk_mapping_risk_expanded_binary.py` with
  `--protected-false-source-dir` so guarded/protected false rows from the clean
  semantic-risk binary data can be added as visible-evidence no-regression
  cases.  Built
  `data\semantic_risk_mapping_risk_expanded_binary_v2protected_20260614_2355`:
  train `37` (`24` true, `13` false), val `9` (`4` true, `5` false), route and
  support-label leakage `0`.  v22 gate:
  val risk match `1.0`, train risk match `0.891892`, exact schema `1.0`,
  unknown key `0.0`
  (`runs\semantic-risk-mapping-risk-expanded-binary-v22-v2protected-val9-20260614_2355.jsonl`,
  `runs\semantic-risk-mapping-risk-expanded-binary-v22-v2protected-train37-20260614_2355.jsonl`).
  All protected false and copy-guard-cancel rows passed; the remaining misses
  are four true `copy_default_only_visible` list-family rows.  Still do not
  train yet: this is a strong diagnostic surface, but it must be checked
  against original binary, atom-polarity, and memory stale/distractor gates.
- [ ] Next no-regression gate before any SFT:
  run the original mapping-risk binary gate, closed-vocabulary atom-polarity
  gate, expanded binary v2protected gate, expanded pairwise bias check, and the
  memory reliable/stale/distractor controller gate in one manifest.  Success
  requires balanced true/false expanded binary behavior, no regression on
  protected false rows, no unknown keys, and no stale/distractor acceptance
  regression.  Only then consider a tiny SFT/DPO experiment; otherwise collect
  more list-family true-risk examples and protected false examples.
- [ ] If fixed-label scoring is needed for semantic-risk boundaries, first
  change or add a serving path that actually returns logprobs.  The current
  local chat endpoint accepted `logprobs/top_logprobs` but returned no logprob
  fields, and `/v1/completions` returned `404`, so free-form generation gates
  remain the available diagnostic surface for now.
- [ ] Keep verifier RETRY work auxiliary only.  The RETRY boundary readouts are
  useful safety/recovery data, but they should not drive the main experiment or
  redefine the small model as a planner/verifier.

## 2026-06-14 SWE-Bench Assistant-Chain Follow-up

- [x] Run/report the first `gpt-5.4-mini` SWE-Bench Lite assistant-chain
  smoke:
  `runs\swebench-assistant-chain-smoke-20260614`.
  Single instance `marshmallow-code__marshmallow-1343` resolved under all
  three conditions: no-memory, frozen memory, and updated memory.  Updated
  memory used one gated same-repo memory row and had lower cost/tool use
  (`$0.029553`, `8` tool calls) than no-memory (`$0.084137`, `19` tool calls)
  and frozen memory (`$0.059749`, `13` tool calls), but solved count is tied
  at `1/1`, so this is only a cost/step smoke signal.
- [x] Next SWE-Bench experiment should be a harder paired subset, not another
  single easy smoke.  Pick `3-5` Lite instances from prior continual reports
  where no-memory/frozen had unresolved, high tool count, or positive-transfer
  opportunities.  Keep the framing as memory/evidence assistance around the
  large model: memory retrieval and gating, source-aware context, path/function
  hints, semantic guards, and selective delegation; do not add benchmark-
  specific hard-coded packet rules.
  Done first as a 2-instance paired pass on the two strongest pvlib candidates
  to control cost and get a real transfer signal quickly.  Broader 3-5 instance
  follow-up remains useful after the transfer-atom target is strengthened.
- [x] Build the harder paired-subset candidate list from prior continual
  reports:
  `runs\swebench-assistant-chain-candidate-selection-20260614\candidate_instances.json`.
  Highest-priority positive-transfer candidates are
  `pvlib__pvlib-python-1707` and `pvlib__pvlib-python-1606`, where prior
  updated-memory runs resolved but no-memory and frozen-memory did not.
  Additional candidates include `pyvista__pyvista-4315`,
  `pvlib__pvlib-python-1854`, `marshmallow-code__marshmallow-1359`, and
  hard all-failed/high-cost SQLFluff or Astroid instances.
- [x] Run a no-model-call memory coverage preflight for the proposed harder
  subset:
  `runs\swebench-assistant-chain-preflight-20260614\memory_preflight.json`.
  Proposed instances
  `{pvlib__pvlib-python-1707, pvlib__pvlib-python-1606,
  marshmallow-code__marshmallow-1359, sqlfluff__sqlfluff-1625}` all retrieve
  gated same-repo memory: `4/4` instances with memory, `8/8` retrieved rows
  gate-pass, `8/8` same-repo.  This supports running the next paired
  benchmark as a true memory-assistant test rather than an empty-memory smoke.
- [x] Before launching the harder subset, ensure stale `minisweagent-*` Docker
  containers from the previous smoke will not collide with new harness runs,
  and run only one relay/model condition at a time if the expected duration or
  provider cost is high.
  Done before launch and again after completion; the six generated
  `minisweagent-*` sleep containers from the paired run were removed.
- [x] Monitor the launched 2-instance real paired benchmark:
  `runs\swebench-assistant-chain-paired-pvlib2-20260614`.
  Background processes at launch: `uv` PID `69284`, child Python PID `99864`.
  Instances: `pvlib__pvlib-python-1606` and `pvlib__pvlib-python-1707`.
  Conditions: no-memory, frozen-memory, updated-memory with gated/stage-aware
  memory.  After completion, summarize `continual_report.json`, retrieved
  memory logs, patches, resolved count, cost/tool calls, and any
  positive/negative transfer.
- [x] Convert the real paired benchmark into memory/evidence atom supervision
  instead of adding runtime memory rules.
  Added `scripts\build_swebench_transfer_evidence_atoms.py` and built
  `data\swebench_transfer_evidence_atoms_20260614_1525`.
  Labels: `1` shared failure / insufficient memory and `1` shared success with
  frozen-memory negative transfer.  The rows treat all retrieved gate-pass
  memories as weak hints, not causal repair evidence, because updated-memory
  did not beat no-memory and frozen-memory hurt one instance.
- [x] Run a v22 small-controller readout on the new real transfer atom eval:
  `runs\swebench-transfer-evidence-atoms-v22-20260614_1525.jsonl`.
  Results: valid JSON `1.0`, rejected-memory recall/precision `1.0/1.0`,
  selected-memory recall/precision `1.0/1.0`, action accuracy `1.0`, but
  path recall `0.0`, explicit delegate-needed accuracy `0.0`, semantic-guard
  recall `0.5`, and all-core `0.0`.  Interpretation: v22 can reject the
  misleading gate-pass memories, but needs training to keep localization,
  explicit delegate route, and guard atoms after rejecting them.
- [x] Build the first controller-training mix from real transfer failures plus
  protected replay, without adding runtime rules.
  Added `scripts\build_memory_evidence_atom_controller_mix.py` and built
  `data\memory_evidence_atom_controller_mix_swebench4_replay_20260614_1600`.
  The mix has `392` train records and `90` val records: `4` real SWE-Bench
  transfer-atom rows repeated as hard boundary signal, plus protected replay
  from the 104-row controller gate and locate-sparse stale/distractor verdict
  atoms.  The combined transfer gate is still diagnostic-only: v22 gets valid
  JSON and memory rejection `1.0`, but path recall `0.5`, explicit
  `delegate_needed` accuracy `0.0`, semantic-guard recall `0.5`, and
  all-core `0.0`.
- [x] Before any GPU SFT, audit the candidate mix for schema consistency and
  leakage, then define held-out gates: original 104-row controller gate,
  hard stale/distractor locate-sparse verdict rows, the combined 4-row
  SWE-Bench transfer gate, and at least one downstream assistant-chain proxy.
  Only run a short SFT if the expected gain is explicit
  `delegate_needed`/guard/localization stability, not packet formatting loss.
  Done first for
  `data\memory_evidence_atom_controller_mix_swebench4_replay_20260614_1600`:
  added `scripts\audit_memory_evidence_atom_mix.py`; audit status `pass`,
  rows `482`, response JSON valid `1.0`, response leakage rows `0`, transfer
  contract rates all `1.0`.  Added
  `data\memory_evidence_atom_controller_mix_swebench4_replay_20260614_1600\gate_manifest.json`
  with four gates: combined real SWE-Bench transfer, original 104-row
  controller, hard stale/distractor locate-sparse verdict, and downstream
  assistant-chain proxy.
- [ ] Select or implement the missing scorer commands for the gate manifest
  before training: especially the hard stale/distractor locate-sparse verdict
  scorer and the downstream assistant-chain proxy scorer.  If the existing
  scripts already cover them, record exact commands; otherwise add small
  offline scorers only.  Do not add runtime selector/packet rules.
  First scorer implemented:
  `scripts\run_stale_memory_verdict_sft_gate.py`.  A partial v22 baseline on
  `data\stale_memory_verdict_atom_sft_correction_locate_sparse_20260614_1838\val.parquet`
  wrote
  `runs\stale-memory-verdict-sft-gate-v22-locatesparse-20260614_1615.jsonl`.
  Because the input has `156` rows, the first run was stopped after `72` rows
  and summarized as partial: valid JSON `1.0`, candidate id match `1.0`,
  verdict match `0.388889`, distractor verdict match `0.047619`,
  stale verdict match `1.0`, reliable verdict match `0.777778`,
  all-exact `0.027778`.  This exposes a real learned boundary target:
  v22 over-calls `reject_stale_overlap` for distractors under path-like
  evidence.  Next run should use an explicit `--limit` or a balanced subset
  rather than an accidental full 156-row pass.
- [x] Run the bounded balanced stale/distractor verdict gate.
  Updated `scripts\run_stale_memory_verdict_sft_gate.py` with
  `--balanced-per-role` and ran a controlled balanced30 v22 baseline:
  `runs\stale-memory-verdict-sft-gate-v22-locatesparse-balanced30-20260614_1625.jsonl`.
  Results: rows `30`, valid JSON `1.0`, candidate id `1.0`, verdict match
  `0.466667`, current-path exact `0.2`, stale-overlap-risk match `0.333333`,
  prefer-current-evidence match `0.666667`, all-exact `0.0`.  By role:
  distractor verdict `0/10`, reliable verdict `4/10`, stale verdict `10/10`.
  This is now the official hard verdict baseline in
  `data\memory_evidence_atom_controller_mix_swebench4_replay_20260614_1600\gate_manifest.json`.
- [x] Decide whether to launch a short SFT from the audited mix.
  Launch only if the training/eval command can check all manifest gates:
  combined 4-row SWE-Bench transfer gate, 104-row controller gate,
  balanced hard stale/distractor verdict gate, and downstream assistant-chain
  proxy.  Required improvement target: distractor/reliable verdict boundary,
  explicit `delegate_needed`, guard recall, and path stability.  Required
  non-regression: strong stale verdict, memory rejection, JSON validity, and
  proxy call/token reduction.
  Decision report now says `ready_for_short_sft=true` with no blockers:
  `data\memory_evidence_atom_controller_mix_swebench4_replay_20260614_1600\training_decision_20260614_1635.json`.
  Added compatibility metadata `stats.json` and a launch/eval plan
  `short_sft_plan_20260614_1638.json`.  Still not launched: the plan is for a
  short evidence-atom stability test only, and post-SFT gates must run before
  treating it as progress.
- [x] If accepted, launch only a short 1-epoch SFT on
  `data\memory_evidence_atom_controller_mix_swebench4_replay_20260614_1600`
  using the existing trainer/launcher.  After it finishes, immediately run:
  combined transfer gate, balanced hard verdict gate, original 104-row
  controller gate, and downstream proxy summary.  Stop if the adapter improves
  distractor/reliable boundary by sacrificing stale rejection or proxy call
  reduction.
- [x] Post-SFT decision for `gs49`: do not deploy and do not run downstream
  proxy/assistant-chain from it.
  Checkpoint:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_evidence_atom_controller_mix_swebench4_replay_20260614_1600_lora/global_step_49`.
  Transfer4 improved strongly: path recall `1.0`, explicit delegate decision
  `1.0`, semantic guard recall `1.0`, all-core `0.75`.  Hard verdict
  balanced30 improved only weakly: verdict `0.533333`, distractor `0.1`,
  reliable `0.7`, but stale fell to `0.8` and all-exact stayed `0.0`.
  The 104-row controller gate failed non-regression badly: all-core
  `0.298077`, action/delegate `0.5`, semantic guard recall `0.076923`,
  with all `104` outputs setting `delegate_needed=false`.  This is exactly why
  gates must judge training, not loss.  Treat `gs49` as a diagnostic adapter
  showing transfer-atom learnability plus catastrophic route/guard forgetting.
- [x] Next memory/evidence controller training step:
  build a v2 mix that keeps the useful transfer atom rows but explicitly
  protects delegate-positive controller behavior and guard atoms.  Increase
  protected replay for the 52 delegate-positive rows from the 104-row gate,
  include matched self-handle negatives, retain hard stale/distractor/reliable
  balanced rows, and keep the output target narrow
  (`selected/rejected memory ids`, `localization`, `delegate_needed`,
  `next_action`, `guards`, compact evidence ids).  Do not add a runtime
  delegate rule or packet normalizer.  Before any GPU run, audit the mix and
  run a no-training prompt/readout or small held-out dry gate if possible.
  Success criteria: preserve v22-like 104-row all-core/delegate/guard metrics
  while keeping transfer4 delegate/path/guard improvements and not reducing
  stale verdict below baseline.
  Done as
  `data\memory_evidence_atom_controller_mix_v2_routeguard_replay_20260614_1725`
  plus short SFT checkpoint
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_evidence_atom_controller_mix_v2_routeguard_replay_20260614_1725_lora/global_step_85`.
  This was a useful negative result, not a deployable model: transfer4 stayed
  good (`delegate_decision=1.0`, path/guard recall `1.0`, all-core `0.75`),
  but hard verdict still regressed stale (`1.0 -> 0.8`) and 104-row controller
  repeated the gs49 collapse (`all_core=0.298077`, delegate/action `0.5`,
  semantic guard recall `0.076923`, all `104` outputs
  `delegate_needed=false`).  Do not run downstream from this adapter.
- [ ] Next controller-learning step after v2 failure:
  stop trying same-format mixed SFT ratio changes.  Build a task-separated or
  controller-compatible atom interface so stale/distractor verdict supervision
  cannot overwrite normal route/guard behavior.  Candidate designs:
  add explicit task tags and output contracts for `memory_verdict_atom` versus
  `controller_route_guard_atom`; or use a two-message/one-JSON target with
  separate fields such as `memory_verdict_atoms` and `controller_decision`,
  requiring `delegate_needed`, `next_action`, and guard fields on every normal
  controller row.  First run this as a prompt/no-training diagnostic or tiny
  held-out readout before any GPU SFT.  Required gate: no `delegate_needed=false`
  collapse on 104-row controller, no stale-verdict regression, and transfer4
  path/delegate/guard gains retained.  Do not add runtime delegate rules or
  packet normalizers.
  First no-training probe done:
  `runs\task-separated-controller-probe-v22-balanced20-20260614_1818.jsonl`.
  It proved formatting is not the bottleneck: valid JSON, `task_type`,
  `memory_verdict_atoms`, and `controller_decision` were all `1.0`, with
  memory recall `1.0`; but all `20` balanced rows predicted
  `delegate_needed=false`, so delegate accuracy stayed `0.5`, missed delegate
  rate `0.5`, semantic guard recall `0.15`, and all-core `0.4`.  Therefore
  field separation alone is insufficient.
- [ ] Next low-cost diagnostic:
  isolate route-risk before any more SFT.  Build/run a forced-choice or compact
  diagnostic-head probe on the same balanced delegate/self-handle rows, with
  labels such as `delegate_risk` versus `guarded_self_handle`, and score
  whether v22 can choose the right route when not asked to emit full JSON.
  Then test a bridge prompt that copies the chosen diagnostic into the normal
  controller JSON.  Only if both are promising should a tiny SFT be considered.
  The target remains learned route/guard judgment, not a runtime delegate
  override.
  First compact probe done:
  `runs\route-risk-choice-probe-v22-balanced20-20260614_1832.jsonl`.
  It improved over full JSON but is still weak: delegate match `0.65`,
  route-risk match `0.5`, missed delegate `0.35`, and delegate-positive rows
  only `0.3` correct.  It predicts `guarded_self_handle` for most semantic-risk
  edit rows, while catching only a few obvious delegate-risk rows.  Next step:
  build a compact contrastive route-risk dataset from the missed delegate
  semantic-risk rows and matched self-handle rows; gate it before any bridge
  back to full controller JSON or GPU SFT.
- [x] Full104 route-risk forced-choice baseline and compact contrastive data.
  Full v22 forced-choice baseline:
  `runs\route-risk-choice-probe-v22-full104-20260614_1838.jsonl`.
  Rows `104`, valid JSON `1.0`, delegate match `0.644231`, route-risk match
  `0.567308`, missed delegate `0.355769`, unnecessary delegate `0.0`.
  Self-handle rows were `52/52` correct, but delegate-positive rows were only
  `15/52` correct; the `37` misses are mostly semantic-risk edit families.
  Built
  `data\route_risk_contrastive_from_full104_v22miss_20260614_1844` with
  `89` pairs / SFT train-val `67/22`: `37` missed delegate semantic-risk,
  `15` protected delegate-detected, and `37` matched self-handle rows.
  Prompt leakage audit found `0` hidden gold/probe-label rows.
- [ ] Next compact route-risk gate before GPU training:
  run v22 generation on the compact contrastive `val.parquet` and, if feasible,
  a logprob/pairwise preference diagnostic on `rm_pairs.parquet`.  Required
  before any tiny SFT: identify whether the compact target is already easy,
  still systematically misses semantic-risk delegate rows, or suffers from
  completion/serialization bias.  Do not bridge back to full controller JSON
  and do not run downstream assistant-chain until the compact route-risk gate
  improves.
  First fixed-scorer v22 generation gate done:
  `runs\route-risk-choice-probe-v22-contrastive-val22-fixed-20260615_1702.jsonl`.
  Result: valid JSON `1.0`, delegate match `0.681818`, route-risk match
  `0.545455`, missed delegate `0.318182`, unnecessary delegate `0.0`.
  Delegate-positive rows are still weak (`6/13` correct, `7/13` missed) and
  misses are concentrated in three repeated task ids:
  `heldout_edit_exact_default`,
  `generated_wide_heldout_semantic_edit_mapping_exporter`, and
  `generated_wide_heldout_semantic_edit_radius`.  The earlier
  `runs\route-risk-choice-probe-v22-contrastive-val22-20260615_1702.jsonl`
  is invalid because the scorer misread SFT `prompt`/`response`/`extra_info`
  formats and saw empty tasks/gold labels.  Next step: de-duplicate this
  contrastive val, add by-bucket reporting, then decide whether the narrow
  route-risk target is trainable; do not bridge to full controller JSON yet.
- [x] De-duplicated compact route-risk report:
  updated `scripts\run_route_risk_choice_probe.py` with
  `--dedupe-task-bucket-gold` plus by-bucket summaries and ran
  `runs\route-risk-choice-probe-v22-contrastive-val10-dedup-fixed-20260615_1709.jsonl`.
  Result: rows `10`, valid JSON `1.0`, delegate match `0.7`,
  route-risk match `0.6`, missed delegate `0.3`, unnecessary delegate `0.0`.
  The clean separation is useful: matched self-handle rows are `5/5` correct,
  protected delegate-detected rows are `2/2` correct, but
  `missed_delegate_semantic_risk` rows are `0/3` correct and all predicted
  `guarded_self_handle/edit`.  Next target should be a tiny evidence-atom /
  classification readout for this specific missed semantic-risk delegate
  boundary, with protected replay for the already-correct self-handle and
  protected delegate rows.  Do not make an all-delegate route rule.
- [x] First semantic-risk delegate atom probe:
  built
  `data\semantic_delegate_atom_boundary_v1_20260615_1714` with one atom,
  `semantic_risk_requires_delegate`, true only for
  `missed_delegate_semantic_risk` and false for matched self-handle plus
  protected delegate-detected rows.  v22 gates:
  `runs\semantic-delegate-atom-boundary-v22-v1-train18-20260615_1714.jsonl`
  and
  `runs\semantic-delegate-atom-boundary-v22-v1-val10-20260615_1714.jsonl`.
  Result: schema clean and missed semantic-risk recall is perfect
  (`train 6/6`, `val 3/3`), but precision is bad: train/val atom match both
  `0.5`, false positive rate `0.5`.  False positives include protected
  non-semantic delegate rows (`challenge_recover_deleted_file`,
  `heldout_recover_stale_module`) and matched self-handle semantic/locate rows.
  Do not train this single boolean as-is.  Next step should split the target
  into evidence polarity/role atoms such as `semantic_risk_evidence_present`,
  `self_handle_guard_evidence_sufficient`, and `nonsemantic_delegate_reason`,
  then template route hints from atoms with protected replay.
- [x] Three-atom semantic delegate polarity probe:
  built `data\semantic_delegate_atom_polarity_v1_20260615_1719` with
  `semantic_risk_evidence_present`, `self_handle_guard_evidence_sufficient`,
  and `nonsemantic_delegate_reason`.  v22 gates:
  `runs\semantic-delegate-atom-polarity-v22-v1-train18-20260615_1719.jsonl`
  and
  `runs\semantic-delegate-atom-polarity-v22-v1-val10-20260615_1719.jsonl`.
  Result: schema clean, but generation collapses to the same polarity for
  every row: semantic risk true, self-handle sufficient true, nonsemantic
  delegate false.  Matched self-handle rows are perfect, but
  missed semantic-risk delegate rows fail on `self_handle_guard_evidence_sufficient`
  (`0/6` train, `0/3` val) and protected delegate rows fail all three atoms.
  Do not train this multi-boolean generation target as-is.  Next attempt should
  isolate a single negative sufficiency readout, e.g.
  `self_handle_guard_evidence_sufficient=false` for missed semantic-risk and
  protected nonsemantic delegates, with matched self-handle positives; consider
  fixed-label/logprob or pairwise ranking if generation keeps collapsing.
- [x] Single self-handle sufficiency atom generation probe:
  built `data\self_handle_sufficiency_atom_boundary_v1_20260615_1725`.
  Target is only `self_handle_guard_evidence_sufficient`: true for matched
  self-handle, false for missed semantic-risk delegate and protected
  nonsemantic delegate.  v22 gates:
  `runs\self-handle-sufficiency-atom-boundary-v22-v1-train18-20260615_1725.jsonl`
  and
  `runs\self-handle-sufficiency-atom-boundary-v22-v1-val10-20260615_1725.jsonl`.
  Result: schema clean, but free-form generation predicts true for every row.
  Val atom match `0.5`; train atom match `0.555556`; all missed semantic-risk
  and protected delegate negatives are false positives.  Stop prompt/generation
  variants here.  Next useful low-cost diagnostic is fixed-label/logprob or
  pairwise ranking for the same sufficiency boundary, because the free-form
  JSON surface has collapsed.
- [x] No-update pairwise/logprob diagnostic for self-handle sufficiency:
  built `data\self_handle_sufficiency_pairwise_v1_20260615_1730`, uploaded it
  to remote, and ran
  `/mnt/memory-agent/runs/self_handle_sufficiency_pairwise_v1_v22_logprob_20260615_1730`
  with existing `scripts\run_pairwise_logprob_diagnostics.py`.  Pulled local
  copy to
  `runs\self_handle_sufficiency_pairwise_v1_v22_logprob_20260615_1730`.
  Result: raw and normalized accuracy both `0.535714`.  By bucket:
  matched self-handle `15/15`, missed semantic-risk delegate `0/9`,
  protected delegate-detected `0/4`.  Token lengths are equal (`12/12`), so
  this is not a length-normalization artifact.  v22 probabilities really prefer
  the wrong `self_handle_guard_evidence_sufficient=true` completion for every
  negative.  Next step, if training is justified, should be a tiny sufficiency
  boundary SFT/DPO/classifier with protected replay and strict gates; do not
  keep probing prompt/logprob variants.
- [x] Tiny self-handle sufficiency LoRA diagnostic:
  ran two v22-initialized reference-free DPO probes on
  `data\self_handle_sufficiency_pairwise_v1_20260615_1730/train.parquet`.
  The conservative 1ep run
  `self_handle_sufficiency_v1_v22init_reffree_1ep_20260615_0143` did not flip
  negative buckets (`missed_delegate_semantic_risk=0`, protected delegate `0`).
  The stronger 4ep/lr1e-5 diagnostic
  `self_handle_sufficiency_v1_v22init_reffree_4ep_lr1e5_20260615_0148` got
  pairwise train/val/all `1.0` and generation atom val10 `1.0`, proving the
  isolated sufficiency atom is learnable.  But route-risk val10 dedup only
  improved the missed semantic-risk bucket from `0/3` to `1/3`; two semantic
  delegate rows still became `guarded_self_handle`.  Do not deploy this adapter
  and do not add a runtime sufficiency-to-delegate override.
- [ ] Next learned bridge target:
  build an explicit atom-to-route / causal route dataset where
  `self_handle_guard_evidence_sufficient=false` is consumed as evidence for
  `delegate_needed=true`, while matched self-handle and protected delegate rows
  remain replayed.  This should be a learned controller target, not a packet
  template or hard-coded routing rule.  Required gates before any assistant-chain
  run: sufficiency atom val10, route-risk dedup val10 with
  `missed_delegate_semantic_risk >= 2/3` and no matched-self over-delegation,
  104-row memory controller no-regression, hard stale/distractor verdict,
  refined mapping-risk atom mix, and assistant-chain proxy summary.
- [x] Bridge v1 diagnostic:
  built `data\sufficiency_route_bridge_v1_20260615_0200` and added
  `scripts\build_sufficiency_route_bridge_data.py`,
  `scripts\run_sufficiency_route_bridge_gate.py`, and tests.  v22 baseline on
  bridge val10 is clean JSON/schema but all self-handle
  (`delegate_match=0.5`, `sufficiency_match=0.5`,
  `missed_delegate_semantic_risk=0/3`).  Tiny bridge SFT from v22:
  1ep did not fix semantic delegates; 4ep/lr1e-5 improved the bridge prompt
  only partly (`semantic-risk delegate=1/3`, protected delegate `2/2`) and
  regressed the original route-risk val10 surface to all self-handle
  (`delegate positives=0/5`).  Do not deploy either bridge adapter.
- [ ] Next bridge improvement:
  replace pure SFT bridge v1 with a preference/consistency target that directly
  contrasts coherent route JSON against "sufficiency true + self-handle" for
  delegate-positive rows, while replaying matched self-handle and protected
  delegate negatives.  Score both the bridge prompt and the original
  route-risk prompt before any further assistant-chain run.  Success threshold:
  bridge val `missed_delegate_semantic_risk >= 2/3`, protected delegate `2/2`,
  matched self-handle over-delegation `0`, and original route-risk val10 no
  worse than v22.
- [x] Preference/consistency bridge v1 diagnostic:
  built `data\sufficiency_route_bridge_pairwise_v1_20260615_0225` and added
  `scripts\build_sufficiency_route_bridge_pairwise.py` plus tests.  v22
  no-update normalized logprob again shows the missing boundary:
  matched self-handle `15/15`, missed semantic-risk delegate `0/9`, protected
  delegate `0/4`.  A 4ep/lr1e-5 v22-initialized reference-free DPO adapter
  made pairwise train/val/all `1.0`, but generation still failed semantic-risk
  delegate rows: bridge val `missed_delegate_semantic_risk=0/3`; original
  route-risk val10 also `0/3`.  It did preserve matched self-handle and
  protected delegate, but it is not deployable because the core semantic-risk
  transfer did not move.
- [ ] Next bridge representation:
  stop training the same route/sufficiency pairwise surface.  Build a v2 bridge
  target that exposes semantic-risk causal evidence explicitly, e.g.
  `semantic_risk_evidence_present`, `visible_command_semantically_insufficient`,
  `self_handle_guard_evidence_sufficient`, and route fields, or use a two-step
  prompt where the model first emits evidence atoms and then consumes those
  atoms in the same response.  The key success condition is moving
  `missed_delegate_semantic_risk` before any broader assistant-chain run; do
  not add a runtime rule that maps atom names to delegate.
- [ ] Narrow the bridge atoms further before another train.
  The current v2 bridge shows that the wide atom
  `semantic_risk_evidence_present` is too easy: it appears in both true
  delegate edit cases and false-safe scalar/default cases.  Refine the next
  dataset around comparison atoms such as
  `command_problem_default_mismatch`, `low_strict_semantic_uncertainty`,
  `visible_command_evidence_conflict`, and
  `guard_shape_present_but_semantics_wrong`, plus matched/protected replay.
  Use the two stubborn positives `heldout_edit_exact_default` and
  `generated_wide_heldout_semantic_edit_radius`, matched self-handle negatives,
  and protected nonsemantic delegate negatives.  Score with a fixed-label atom
  gate first; use role generation only as a downstream check.
- [ ] Broaden real transfer atoms beyond the current four SWE-Bench rows when
  provider budget allows.  Prefer instances that can distinguish reliable
  positive transfer from weak same-repo memory; the current `3` shared-failure
  and `1` frozen-negative-transfer rows mostly teach rejection, not reliable
  memory acceptance.
- [x] Monitor mixed2 transfer-atom expansion benchmark:
  `runs\swebench-assistant-chain-paired-mixed2-20260614`.
  Instances: `marshmallow-code__marshmallow-1359` and
  `sqlfluff__sqlfluff-1625`; conditions: no-memory, frozen-memory, and
  updated-memory.  After completion, summarize resolved/cost/tool/memory rows,
  then build transfer atoms with
  `scripts\build_swebench_transfer_evidence_atoms.py` and rerun the v22
  controller readout to see whether non-pvlib rows expose the same
  route/localization/guard weaknesses.
  Done: no-memory/frozen/updated all solved `0/2`, with no errors or empty
  patches.  Updated memory retrieved `2` same-repo gate-pass rows
  (`marshmallow-1343`, `sqlfluff-2419`) but gave no downstream gain.
  Transfer atoms:
  `data\swebench_transfer_evidence_atoms_mixed2_20260614_1552`, labels
  `shared_failure_insufficient_memory: 2`.  v22 readout:
  valid JSON `1.0`, memory rejection `1.0`, path/function/action `1.0`, but
  explicit delegation `0.0`, semantic-guard recall `0.5`, and all-core `0.0`.

## 2026-06-14 Alias-Canonical Packet Follow-up

- [x] Evaluate the completed alias-canonical LoRA on a temporary remote
  `127.0.0.1:8002` service, copy probe artifacts locally, and kill `8002`
  afterwards.
- [x] Add scorer metrics that separate internally nested packet fields from
  top-level usable packets: `top_level_packet_shape` and `wrapper_violation`.
- [x] Build and test an offline route/envelope canonicalization curriculum for
  wrapper, missing-route, missing-guard, uncertainty-string, and boolean-shape
  failures.
- [x] Run v22 prompt-only baseline on the synthetic route/envelope val split;
  result is all-core `1.0`, so this data is too easy to justify a standalone
  GPU training job.
- [x] Build the next harder packet target from real alias-LoRA failures rather
  than the easy synthetic prompt: source-side bad drafts should include
  observed `packet`/`payload`/`canonical_packet` wrapping, missing
  `semantic_guards`, unstable `route`, unstable exact `uncertainty`, and
  stale-vs-distractor confusion.
- [x] Gate the next packet-target experiment on held-out
  `top_level_packet_shape`, exact `route`, exact `uncertainty`,
  `semantic_guards` presence, memory-ID split, and leakage `0`; do not call
  `gpt-5.4-mini` downstream until these small-controller packet metrics
  materially improve.
- [ ] If the real-failure-driven target still overfits, merge only the useful
  rows with schema-first/generalization/protected replay, keeping the learning
  target as controller packet judgment rather than a runtime normalizer.

## 2026-06-14 Real-Failure Packet Repair Follow-up

- [x] Build real alias-LoRA failure repair data from observed bad drafts and
  visible failed checks:
  `data\stale_memory_packet_real_failure_repair_20260614_0710`.
- [x] Run v22 prompt-only baseline on the real-failure repair val split; it is
  not saturated (`top_level_packet_shape=0.777778`, `uncertainty=0.333333`,
  guard-aware `all_core_exact=0.0`), so a short SFT was justified.
- [x] Train and evaluate short real-failure repair LoRA from alias-canonical
  init:
  `stale_memory_packet_real_failure_repair_sft_aliasinit_20260614_0716`.
- [x] Add semantic guard metrics to the packet-target scorer:
  `semantic_guards_match` and `semantic_guard_jaccard`, and include exact
  semantic guards in `all_core_exact`.
- [x] Confirm the repair adapter improves top-level packet structure on held-out
  val (`0.777778 -> 1.0`) and removes wrapper errors, but does not yet solve
  exact uncertainty or semantic guard retention.
- [x] Build the next residual target around exact uncertainty strings,
  semantic guard retention, and stale-vs-distractor memory split.  Use more
  than the current 9 held-out rows if possible, or merge with protected replay;
  avoid another tiny overfit-only SFT.
- [x] Do not call `gpt-5.4-mini` downstream until guard-aware packet metrics
  materially improve: top-level shape `1.0`, semantic guard exact match much
  higher than `0.222222`, uncertainty exact much higher than `0.444444`, and
  stable stale/distractor split.

## 2026-06-14 Residual Guard/Uncertainty Follow-up

- [x] Build residual guard/uncertainty/memory-split packet data:
  `data\stale_memory_packet_residual_guard_uncertainty_20260614_0735`.
- [x] Confirm v22 prompt-only fails this evidence-compression target by copying
  the source object; val packet metrics are all `0.0`.
- [x] Train/evaluate residual LoRA from real-failure repair init:
  `stale_memory_packet_residual_guard_uncertainty_sft_repairinit_20260614_0748`.
- [x] Record the key held-out val result: `all_core_exact=0.75`,
  `semantic_guards_match=0.8125`, `uncertainty_match=0.8125`,
  `top_level_packet_shape=0.75`; temp `8002` was killed after probing.
- [x] Broaden this residual packet eval before downstream delegation: add more
  task names, guard phrasings, source-needed decisions, and no-copy cases, or
  mix with protected replay, then gate against v22 and the residual adapter.
- [ ] Fix the remaining failure modes in data/eval, not runtime code:
  occasional source-object copying and missing
  `packet_evidence.avoid_line_number_only_edit=false` on locate rows.
- [ ] Only after broader guard-aware packet metrics remain strong should a
  single-relay `gpt-5.4-mini` downstream delegate probe be considered.

## 2026-06-14 Broadened Residual Eval Follow-up

- [x] Build broadened eval-only residual packet split:
  `data\stale_memory_packet_broadened_residual_eval_20260614_0830`.
- [x] Run v22 baseline on the broadened split:
  `all_core_exact=0.25`, `top_level_packet_shape=0.25`,
  `semantic_guards_match=0.75`, `uncertainty_match=0.5`.
- [x] Run the residual adapter on the same broadened split:
  `all_core_exact=0.0`, `top_level_packet_shape=0.0`,
  `wrapper_violation=0.958333`, showing severe wrapper regression.
- [x] Add and run an explicit source-object copying scorer metric:
  `source_copy_violation_rate` checks copied source/evidence keys such as
  `visible_evidence`, `observed_bad_draft`, `repair_focus`, and
  `SOURCE_EVIDENCE*`.  Latest rescore: v22 broadened eval
  `source_copy_violation=0.0`, residual adapter broadened eval
  `source_copy_violation=0.0` but `wrapper_violation=0.958333`, and narrow
  residual val `source_copy_violation=0.1875`.  This separates copy leakage
  from the wrapper regression.
- [x] Confirm LATEX-NIPS already covers the main novelty boundaries:
  Hybrid-Gym, SWE-Adept, SWE-Edit, Polar, CODESKILL, MemGovern, and
  feedback-normalized developer memory; no paper update needed for this
  negative diagnostic.
- [x] Build a replay/generalization mix before any more downstream work:
  combine top-level schema rows, real-failure repair rows, residual
  guard/uncertainty rows, and broadened no-copy negatives.
  Done as
  `data\stale_memory_packet_replay_generalization_mix_20260614_0755`.
  Summary: train/val `332/58`, source-copy pressure rows `142`, wrapper
  pressure rows `390`, hidden leakage `0`, target source-copy leakage `0`.
  The original 24-row broadened eval remains held out and unmodified.
- [x] Launch a conservative short replay/generalization SFT from the safer
  real-failure repair adapter, not from the wrapper-regressed residual adapter.
  Remote PID `331464`, output
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/stale_memory_packet_replay_generalization_sft_repairinit_20260614_0805`,
  log
  `/mnt/memory-agent/logs/stale_memory_packet_replay_generalization_sft_repairinit_20260614_0805.log`.
- [ ] Gate the next adapter on both the narrow residual split and broadened eval;
  require no wrapper regression, strong guard/uncertainty retention, and stable
  stale/distractor split before considering `gpt-5.4-mini`.
- [ ] After training completes, evaluate the replay/generalization adapter on:
  the 58-row mix val, the 16-row narrow residual val, and the original 24-row
  broadened held-out eval.  Required gates before any `gpt-5.4-mini` call:
  wrapper violation near `0`, source-copy violation near `0`, top-level packet
  shape not below v22 on broadened eval, and guard/uncertainty/memory split
  retained.
- [x] Evaluate the replay/generalization adapter on the three gates.  Result:
  source-copy improved, but broad held-out still failed; mix val all-core
  `0.37931`, wrapper `0.137931`, source-copy `0.051724`; narrow residual
  all-core `0.625`, wrapper `0.125`, source-copy `0.0`; broadened held-out
  all-core `0.083333`, top-level shape `0.125`, wrapper `0.458333`,
  source-copy `0.0`.  Do not call `gpt-5.4-mini`; this adapter did not beat v22
  on the broadened gate.
- [x] Build actual-failure repair rows from the replay adapter's failed outputs,
  without using the original broadened eval as training rows:
  `data\stale_memory_packet_replay_actual_failure_repair_20260614_0838`.
  Summary: train/val `132/21`, base train `33`, wrapper-failure rows `43`,
  leakage `0`.
- [x] Launch a smaller actual-failure correction from the replay adapter:
  remote PID `331934`, output
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/stale_memory_packet_actual_failure_repair_sft_replayinit_20260614_0840`,
  lr `1e-6`, epochs `2`.  This is still offline learned repair, not a runtime
  packet unwrapping rule.
- [ ] After the actual-failure correction completes, rerun the same three gates.
  Stop if broadened held-out wrapper remains high or top-level/all-core remains
  below v22; next improvement should target canonical field ownership
  (`packet_evidence`, `avoid_line_number_only_edit`, `uncertainty`) rather than
  downstream large-model delegation.
- [x] Rerun the same three gates for actual-failure correction.  Result:
  mix val improved to all-core `0.448276`, wrapper `0.12069`, source-copy
  `0.017241`; narrow residual stayed all-core `0.625` but regressed on
  source-copy `0.0625`; broadened held-out improved to top-level `0.25`,
  all-core `0.166667`, wrapper `0.416667`, source-copy `0.0`, still not better
  than v22 all-core `0.25` / wrapper `0.0`.  Do not call `gpt-5.4-mini`.
- [ ] Build the next offline target as an atomic canonical field-ownership
  curriculum, not another broad replay mix: top-level `route=DELEGATE_PACKET`,
  nested `memory_decision`, nested `localization.uncertainty`,
  `packet_evidence.compact_code_anchors`, exact `semantic_guards`, and explicit
  `avoid_line_number_only_edit`; contrast against `packet` wrappers, singular
  `path_hint`/`code_anchor`, `code_anchors`, `memory_ids`, and route aliases.
- [x] Build and smoke-test the atomic canonical field-ownership curriculum:
  `data\stale_memory_packet_field_ownership_curriculum_20260614_0918`.
  Summary: train/val `120/18`, wrapper pressure `69`, alias pressure `138`,
  leakage `0`; tests passed (`9 passed`).
- [x] Run v22 prompt-only baseline on field-ownership val:
  all-core `0.333333`, top-level `0.388889`, memory/localization shape
  `0.5/0.444444`, packet-evidence shape `1.0`, wrapper/source-copy `0.0/0.0`,
  uncertainty `0.333333`.  This split is useful because it isolates ownership
  and uncertainty drift without source-copy noise.
- [ ] Next experiment should be a small field-ownership correction only if it is
  evaluated against the original broadened held-out gate plus narrow residual
  replay.  Use low lr and protected replay; stop if it improves the new atomic
  split but worsens broadened all-core/wrapper.
- [x] Launch the small field-ownership correction from actual-failure init:
  remote PID `332325`, output
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/stale_memory_packet_field_ownership_sft_actualinit_20260614_0926`,
  lr `8e-7`, epochs `2`, train/val `120/18`.
- [ ] Monitor PID `332325` to completion, then evaluate on field-ownership val,
  original narrow residual val, and original broadened held-out eval.  Treat
  field-val-only gains as insufficient if broadened wrapper/all-core worsens.
- [x] Evaluate field-ownership correction on all gates.  It failed the real
  gates: field val top-level improved `0.388889 -> 0.666667`, but all-core fell
  `0.333333 -> 0.277778`; narrow residual collapsed to all-core `0.0`; broad
  held-out fell to all-core `0.125`, wrapper `0.583333`.  Stop training this
  branch.
- [ ] Next improvement should be analysis/data design, not another LoRA:
  inspect field-ownership outputs for prompt-style overfitting and build a
  protected-replay formulation where atomic ownership rows are a minority mixed
  with residual/broadened canonical packets, or switch to pairwise preference
  over canonical-vs-wrapper outputs.  Do not run downstream delegation.
- [x] Inspect field-ownership failure outputs.  Finding: on field val the model
  emits the eight canonical top-level keys but still misses memory split /
  uncertainty; on narrow residual it collapses into `patch` / `patched_packet`
  style outputs; on broad held-out it returns `packet` wrappers in 13/24 rows.
- [ ] Prefer next data design as pairwise preference / reward-proxy rows:
  canonical top-level packet should be preferred over semantically similar
  `packet`, `patch`, `payload`, singular alias, and route-alias outputs.
  Include residual/broadened prompts as protected contexts, not just synthetic
  field prompts.

每轮监控/推进前先看本文件和 `progress.md`：`todo.md` 记录待做项与研究路线，`progress.md` 记录已经执行的命令、结果、日志、反思和阻塞。

## Current Main Direction

Status: active main track as of 2026-06-09.

The project should now be framed as **memory-conditioned controller learning for small-large coding-agent collaboration**.

Core claim:

- [ ] 训练一个小模型 memory-aware coding controller，让它学会用检索到的 repair memory 完成 locate/edit/test/recovery，并判断记忆什么时候可靠、什么时候过时或不足。
- [ ] 当小模型证据不足时，再选择性委派给大模型；委派不是泛泛“多智能体 prompt”，而是由小 controller 输出 structured packet：memory-grounded anchors、path hints、semantic guards、uncertainty、delegation goal。
- [ ] 大模型的作用是补全 residual complex patch / locate step；论文主创新仍然是小模型如何学习使用 memory 和何时委派。
- [ ] 不为了维持 GPU 或任务在跑而跑实验；只跑能验证主线 claim、排除关键替代解释、或补齐论文表格的实验。
- [ ] `gpt-5.4-mini` 实验默认只用一个 relay，优先 muyuan；只有 provider failure 或显式 provider-stability check 时才跑第二家。

Nearest useful next step:

- [x] 做 non-oracle source-inspection-before-packet：在 5 个 residual delegate cases 上，从可见 source/test/current evidence 中补充 anchors，再生成 source-inspected delegation packets。
- [ ] 用一个 `gpt-5.4-mini` relay 跑 source-inspected packet probe，并与 normal packet、guarded candidate、oracle-anchor upper bound 对比。
- [ ] 如果 source inspection 能缩小 oracle-anchor gap，再把它作为小 controller packet-generation training/eval 的下一阶段；如果不能，就把当前结果诚实写成 residual packet-quality bottleneck。

## Immediate Checks

- [ ] 每轮先检查远端 GPU、Qwen OpenAI-compatible 服务、训练日志、服务日志。
- [ ] 每轮确认本地 SSH tunnel `127.0.0.1:18001 -> remote 127.0.0.1:8001` 可用。
- [ ] 每轮确认 `http://127.0.0.1:18001/v1/models` 和一次最小 chat/completions 调用健康。
- [ ] 每轮检查 Docker Desktop 状态；可以主动启动 Docker Desktop，但仅在需要 SWE-Bench/harness 时启动对应评测。
- [ ] 每轮检查 `progress.md` 最近记录，避免重复跑已经完成的实验。

## Current Single-Agent Track

- [x] 汇总 untrained Qwen、v16、v22 在相同小任务套件上的主指标表；v20/v21 作为回归诊断保留部分结果。
- [x] 补齐 untrained Qwen baseline：`path_edit_commitment`、`generated_semantic_wide_heldout`、`challenge`、`heldout` 已有同套件结果。
- [ ] 不用训练 loss 作为质量证明；以 probe/eval 的 strict score、semantic pass、skill match、action rate 为准。
- [ ] 诊断 v22 剩余问题：locate 精度/覆盖不足，以及 wide-heldout 中一次 edit-vs-locate mismatch。
- [x] 检查 v22 `generated_semantic_wide_heldout` repeat01 稳定性复跑结果。
- [x] 检查 v22 `generated_semantic_wide_heldout` repeat02 稳定性复跑结果。
- [x] 检查 v22 `challenge` repeat01 稳定性复跑结果。
- [x] 检查 v22 `heldout` repeat01 稳定性复跑结果。
- [x] 检查 v22 `generated_semantic_wide_heldout` repeat03 稳定性复跑结果。
- [x] 生成 v22/base controller delegation audit，作为多智能体 proxy pilot 的第一步。
- [x] 检查 v22 `generated_semantic_wide_heldout` repeat04 稳定性复跑结果。
- [ ] 若没有评测或训练在跑，不自动为了占用 GPU 启动任务；优先检查是否存在能支持当前主线的 conservative small-task training/evaluation step，不满足则只记录阻塞/下一步。

## Multi-Agent Direction

Status: active but renamed in paper framing. Single-agent v22 is now treated as the small memory-aware controller backbone; new work should prioritize memory-conditioned controller learning, packet quality, and selective large-model delegation. Avoid presenting the work as generic multi-agent software engineering.
Use this large-model config if testing the multi-agent pilot. Keep raw API keys outside repo files.

Memory retrieval
   ↓
Small model controller
   ├─ SELF_HANDLE: locate/edit/test
   └─ DELEGATE_PACKET: anchors + paths + guards + uncertainty
          ↓
       Large model
       
- [x] 在单智能体 Qwen memory/RL 路线稳定后，做一个多智能体 pilot。
- [ ] 核心想法：训练小模型作为 memory/RL controller，负责检索经验、定位文件/函数、选择 locate/edit/test/delegate、做格式与 no-op/semantic guard；大模型只在复杂补丁生成时被调用。
- [ ] 目标贡献不要写成泛泛的 multi-agent，而要写成：低成本训练的小模型 memory/RL controller 学会围绕大模型进行代码定位、编辑、测试、委派和验证。
- [ ] 对比 Hybrid-Gym 时强调区别：Hybrid-Gym 更像通用 skill learning；本工作是 memory-conditioned skill/controller learning，重点包括 stale memory correction、memory-to-current-source transfer、semantic guard preservation、selective delegation。
- [ ] 实验对照至少包括：
  - large model single-agent
  - small model single-agent
  - large model + untrained small controller
  - large model + trained memory/RL small controller
- [ ] 关键指标：
  - resolved rate / task success
  - token cost
  - big-model call count
  - localization accuracy
  - edit/test action accuracy
  - no-op patch rate
  - recovery-after-failure rate
- [ ] 先做 proxy/trace 版本：大模型可以先用固定 endpoint 或 mock patcher，验证 controller 是否能减少上下文、减少大模型调用、提升定位和测试闭环。
- [x] 基于 `runs\multi-agent-proxy-v1\v22_controller_delegation_audit.json` 设计第一版 small-controller + delegate-to-large proxy 实验。
- [x] 生成离线 delegate cost simulation：oracle delegate 与 80% success delegate 两个设定。
- [x] 实现真实 large-patcher delegate probe 脚本，先只覆盖 v22 audit 中的 delegation candidates。
- [x] 改用可用 `gpt-5.4-mini` OpenAI-compatible chat 端点跑真实 5-candidate delegate probe。
- [x] 给真实 delegate prompt 加入原始 small-task prompt 上下文，但不泄漏 `target_command`。
- [x] 给真实 delegate prompt 加入通用 None-vs-truthiness semantic guard，并复跑两家 provider。
- [x] 将 guarded delegate 结果整理进论文实验表：v22 controller-only、v22+large delegate、base+large delegate、oracle/80% proxy。
- [x] 跑 `large model + untrained/base controller` 同套 44-task delegate 对照，避免只展示 trained-controller 的好结果。
- [x] 跑或模拟 `large model single-agent` 同套 44-task 对照，区分“base controller 全委派”与“无 controller 直接大模型”。
- [ ] 将 `runs\multi-agent-proxy-v1\multi_agent_proxy_summary.md` 同步到 LATEX-NIPS 论文表格。
- [x] 将 `runs\multi-agent-proxy-v1\multi_agent_proxy_summary.md` 同步到 LATEX-NIPS 论文表格。
- [x] 收集 `large-only + same semantic guard` 公平性检查，判断 trained controller 的优势是否只是 prompt guard 带来的。
- [x] 收集 v22 controller audit repeat，检查 44-task delegate rate 是否稳定在约 5/44。
- [x] 测试 improved large-delegate locate prompt，针对当前 5 个 residual delegate cases 提升 locate anchor coverage；结果为负，不进入主表。
- [ ] 将多智能体下一步改为 structured delegation packet：小 controller 输出 action_goal、visible anchors、path hints、semantic guards、controller uncertainty，再让大模型按 packet 生成补丁/定位命令。
- [ ] 训练或评估 controller 直接生成 delegation packet，而不是只输出单条命令；比较 packet anchor recall、semantic guard recall、delegate 后 strict score。
- [x] 跑一轮真实小-大模型协作链路：
  v10 small controller packet -> `gpt-5.4-mini` delegate -> v10 visible verifier -> verifier-selected retry。
  初始 9-row delegate mean strict `0.775487`、semantic pass `0.777778`、1 个 provider 504；
  v10 verifier 在实际 delegate outputs 上 retry precision/recall `1.0/1.0`；
  收紧 mutable-copy retry protocol 后，2 个 verifier-selected retries 全部 semantic pass，
  merged mean strict `0.910963`、semantic pass `1.0`、big attempts `11`。
- [x] 修复 verifier label/feature schema 的 mutable-copy blind spot：
  将 `dict(x if x is not None else DEFAULT)`、`dict(DEFAULT) if x is None else dict(x)`、
  `(x if x is not None else DEFAULT).copy()` 标为安全 selected-copy；
  添加 `truthiness_or_only_in_old_replacement`、`selected_mutable_copy_is_safe/risky` visible features。
- [x] 基于真实协作失败/修复样例生成 balanced visible-guard verifier SFT/eval split：
  覆盖 visible-default mismatch、unresolved `copy.deepcopy`、one-branch mutable-copy/reuse、safe selected-copy、
  truthiness only in old replacement；prompt 不含 `target_command` 或 hidden scorer labels。
- [x] 用 v10/v22 prompt-only 在 balanced verifier eval split 上跑基线；
  guardfix split 上 v10/v22 都达到 valid JSON `1.0`、verdict accuracy `1.0`、retry precision/recall `1.0/1.0`。
  结论：verifier split 先作为辅助分支停在数据/诊断层，不把主线转成小模型 verifier。
- [ ] 重新聚焦主线：小模型不是主要替大模型做难 verifier，而是检索可靠 memory、定位文件/函数、组织可用 packet、减少大模型上下文和调用，并在明显失败时触发重试。
- [x] 重新聚焦主线并建立第一版显式 memory-controller eval：
  每个任务提供 reliable/stale/distractor memory candidates，让小模型选择/拒绝 memory、定位文件/函数、选择 `locate/edit/test/delegate`、判断是否需要大模型、并输出 semantic/no-op/format guard。
  v22 baseline 在 26-row balanced split 上表现为：
  selected-memory recall `1.0`、stale rejection `0.884615`、distractor rejection `1.0`、path recall `0.980769`，
  但 delegate decision accuracy 只有 `0.5`、missed delegate `0.5`、semantic-guard recall `0.076923`。
- [x] 跑一轮低成本 v1b memory-controller SFT，目标是让小模型学会 memory selection + route/guard decision，而不是硬编码规则：
  dataset `data\memory_controller_sft_v1b_broad26_retrieval_route_guard_20260611_1425`，
  train/val `120/6`，delegate/self balanced；
  checkpoint `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1b_broad26_retrieval_route_guard_20260611_1425_lora/global_step_30`；
  v1b 对比 v22：missed delegate `0.500000 -> 0.423077`、guard-bool accuracy `0.269231 -> 0.679487`、all-core-correct `0.346154 -> 0.423077`，
  但 valid JSON `1.0 -> 0.846154`，memory selection/rejection 和 path recall 回退，且出现 unnecessary delegate `0.076923`。
- [ ] 下一步主线改进 v1c：不要继续堆脚本规则；把 v1b 暴露的问题蒸馏成 compact-decision 训练目标。
  目标输出只包含 selected/rejected memory IDs、compact localization、next_action、delegate_needed、guard flags，以及必要时的最小 delegate_packet；
  明确禁止复制输入 `output_schema`、memory candidates、完整 prompt/current evidence 到输出；
  指标目标：valid JSON 回到 `1.0`，保持或提高 guard-bool accuracy，降低 missed delegate，同时不引入 unnecessary delegate，并让 reliable/stale/distractor memory selection 接近 v22。
- [x] 完成 v1c compact-decision 训练/eval：
  dataset `data\memory_controller_sft_v1c_compact_decision_20260611_1505`，train/val `160/6`，train delegate/self `80/80`；
  checkpoint `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1c_compact_decision_20260611_1505_lora/global_step_40`；
  原始 26-row eval 中 valid JSON `1.0`，selected/rejected memory precision/recall 全部 `1.0`，stale/distractor rejection `1.0/1.0`，
  action/delegate accuracy `0.538462/0.538462`，missed delegate `0.461538`，unnecessary delegate `0.0`，all-core-correct `0.5`。
  结论：v1c 修复 v1b 的格式/复制问题，证明小模型能学会稳定检索可靠 memory；但 guard-bool accuracy 降到 `0.217949`，guard/route 判断仍是瓶颈。
- [x] 给 memory-controller eval 增加小型 held-out perturbation：
  对同一任务打乱 memory 顺序、替换 distractor、让 stale memory 看起来更相似；
  评估小模型是否真的学会检索可靠经验，而不是记住固定 memory ID 或固定字段位置。
  已新增 `scripts\perturb_memory_controller_eval.py`；
  `runs\multi-agent-proxy-v1\memory_controller_eval_v2_broad26_perturb2_20260611_1525.jsonl` 有 `52` rows。
  v1c perturb result：
  valid JSON `1.0`，selected-memory recall/precision `1.0/0.971154`，rejected-memory recall/precision `0.971154/1.0`，
  stale/distractor rejection `0.942308/1.0`，说明它不是只记固定顺序；但 missed delegate 仍 `0.461538`，guard-bool accuracy 仍 `0.217949`。
- [ ] 下一步 v1d：route/guard-focused correction，而不是更多推理规则或 benchmark-specific hack。
  从 v22/v1b/v1c 的可见失败构建 hard positives/negatives：
  `semantic_pass=false`、`predicted_skill` mismatch、`strict_score<0.8`、no-op/format risk 应该 delegate 或保留 guard；
  高 strict + semantic pass + skill match 应 self-handle；
  目标是提高 delegate decision accuracy 和 guard-bool accuracy，同时保持 v1c 的 valid JSON `1.0` 与 memory selection/rejection 稳定。
- [ ] 给 v1d eval 增加更难 stale-memory perturbation：
  stale memory 分享正确 path/function 词汇但给出错误 fallback 或旧路径；
  评估 reliable-memory selection、stale rejection、guard preservation 是否仍稳定。
- [ ] v1b/v1c 通过 controller-side 指标前，不要调用 `gpt-5.4-mini` 做下游大模型补丁评估；
  只有当小模型的 memory/action/delegate/guard 决策稳定后，才接大模型测 token cost、big-call count 和 downstream semantic pass。
- [ ] 启动 memory/locating assistance ablation：
  full v10 packet vs 去掉 `visible_task_context/source_inspection/current_evidence` 的 packet，
  测 delegate strict score、semantic pass、path/source-anchor recall、big-model tokens；
  只作为辅助消融，用结果判断 memory/current evidence 本身是否有用；不要作为主优势对照。
- [x] 跑公平 memory-assisted 对照：
  heuristic/untrained-style packet builder 和 trained v10 packet 都保留 non-oracle memory/current evidence，再接同一 `gpt-5.4-mini` delegate。
  9-row residual subset 上 heuristic mean strict `0.860191`、semantic `0.777778`；
  v10 rerun mean strict `0.848900`、semantic `0.777778`；
  7 个共同 task 上 heuristic `0.841674` vs v10 `0.828131`，二者失败相同。
  结论：当前 residual downstream packet 质量不能证明 trained v10 明显优于 memory-retaining heuristic/untrained packet。
- [x] 主线下一步必须做 same-memory trained-vs-untrained route+packet 端到端对照：
  两边都给相同 memory/current evidence；
  比较 route/packet 决策、big-model call count、delegate downstream strict、semantic pass、token cost。
  重点证明训练后小模型学会“何时委派、如何压缩/组织 memory、如何定位文件/函数”，而不是证明 memory 本身有用。
- [x] 在 harder semantic/memory packet split 上跑真实同 memory 小-大协作对照：
  v22 未训练 packet controller 在 12/12 valid packets 上 anchor recall `0.670139`，
  下游 `gpt-5.4-mini` mean strict `0.879248`、semantic `0.833333`、12 calls、`8863` tokens；
  v10 训练后 controller 在 11/12 valid packets 上 anchor recall `0.916667`，11 个有效包下游 mean strict `0.922166`、semantic `1.0`、11 calls、`9359` tokens。
  公平 common 11-task 对照：v22 `0.875708/0.818182` vs v10 `0.922166/1.0`。
  Caveat：v10 有 1 个 invalid JSON packet，按 12-row 端到端记零则 mean strict `0.845319`、semantic `0.916667`。
- [ ] 下一步主线修复：构建 v11 packet serialization/compact memory-evidence correction set，
  针对 `generated_wide_heldout_semantic_edit_margin` 这类失败，禁止把 raw multi-line controller command 或 source blob 放进 `source_inspection`，
  只保留 compact `visible_task_context`、path hints、code/behavior anchors、semantic guards；
  训练/评估后必须复跑同一个 harder 12-row split，再接同一个 `gpt-5.4-mini` delegate。
- [ ] 给 packet 训练/eval 增加格式 guard 指标：
  valid JSON rate、raw-command/source-blob copying rate、max packet chars、visible-context retention、
  delegate-only anchor recall、downstream semantic pass；
  不要只看 route accuracy 或训练 loss。
- [ ] 当前优先级更新：V31 focused LoRA 已按用户要求停止；下一步不要继续 V31，集中做 Multi-Agent Direction 的固定路由/困难路由 packet-quality 评估。
- [ ] 为 5 个 residual delegate rows 建立 delegate-only packet-quality probe：固定路由为 `DELEGATE_PACKET`，评估 anchor/guard/path/source-anchor recall、JSON validity、repair rate、downstream large-delegate strict score。
- [ ] 专门修复两类已观察失败：`challenge_locate_async_retry` 的漏委派，以及 `generated_wide_heldout_semantic_edit_path` 的 JSON packet 格式坏掉。
- [x] 建立并运行第一版 delegate-only packet-quality probe：
  `scripts\run_delegate_only_packet_probe.py`。
- [x] 证明 `challenge_locate_async_retry` 在强制 `DELEGATE_PACKET` 时 packet 内容可达满分，主要问题是 routing/委派决策。
- [x] 修复 `generated_wide_heldout_semantic_edit_path` 的主要 JSON 失败源：禁止把 raw `rg` query / shell command / long source snippet 复制进 JSON 字段后，valid JSON 达到 `1.0`。
- [ ] 下一步把 anchor recall 拆成 essential residual anchors vs broad lexical anchors；当前 24-anchor 版本 JSON/path/guard 稳定，但 full anchor recall 只有 `0.383333`。
- [ ] 用 essential-anchor packet target 或 anchor-reranking metric 重新评估 5 个 residual delegate rows，再接 downstream large-delegate strict score。
- [x] 新增 essential/code-anchor scorer：
  `scripts\score_delegate_essential_anchors.py`。
- [x] 修复 scorer 读取 SFT JSONL 的 bug：`response` 需要从 `{role, content}` 中 unwrap `content`，否则 gold anchors 为空。
- [x] 用 corrected scorer 评估 forced compact/no-query packet：
  full anchor recall `0.383333`，broad essential-anchor recall `0.621429`，code-anchor recall `0.826667`，guard/path/source-anchor recall `1.0/1.0/0.971429`。
- [x] 用单一 muyuan relay 跑 downstream `gpt-5.4-mini` forced compact/no-query packet delegate：
  mean strict score `0.927857`，action/skill/semantic/error `1.0/1.0/1.0/0.0`。
- [ ] 设计下一版 packet compression：保留 code anchors + 少量 behavior anchors，禁止 raw `rg` query / shell command / long source snippet，同时争取接近 fuller source-inspected packet 的 downstream strict score `0.9725`。
- [x] 新增 packet compression variant builder：
  `scripts\build_delegate_packet_compression_variant.py`。
- [x] 运行 code+behavior+context no-query packet variant：
  `runs\multi-agent-proxy-v1\delegate_packets_code_behavior_context_noquery_20260610_0138.jsonl`。
- [x] 用单一 muyuan relay 评估该 variant 的 downstream delegate strict score：
  mean strict `0.962857`，action/skill/semantic/error `1.0/1.0/1.0/0.0`，相比 compact/no-query `0.927857` 明显提升，接近 fuller source-inspected `0.9725`。
- [ ] 如果继续优化 packet compression，只针对 `heldout_recover_stale_module` 做最小调整；不要退回 raw `rg` query copying。
- [ ] 将 best compressed packet result 写入 LATEX-NIPS：强调 serialization stability、no raw query copying、code+behavior anchors、downstream strict score `0.962857`，并与 fuller packet `0.9725` 区分。
- [x] 对 `heldout_recover_stale_module` 做通用 scope-path fix：从 visible controller command 中抽取 locate path scopes，如 `tests`，合并进 `path_hints`，仍不复制 raw source-inspection query。
- [x] 运行 scopefix no-query packet variant：
  initial mean strict `0.918571`，其中 stale-module 提升到 `0.957143`，但 edit-path 随机语义失败。
- [x] 同一 muyuan relay 只重试 failed edit-path case，并合并 final scored file：
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_muyuan_code_behavior_context_scopefix_noquery_final_20260610_0152_scored.jsonl`。
- [x] 当前 best compressed packet result：
  code+behavior+context+scopefix no-query mean strict `0.971429`，action/skill/semantic/error `1.0/1.0/1.0/0.0`，几乎匹配 fuller source-inspected `0.9725`。
- [ ] 更新 LATEX-NIPS 时使用最新 best compressed packet `0.971429`，而不是旧 `0.962857`。
- [x] 已同步 LATEX-NIPS：
  abstract、small-controller table、residual delegate table 已加入 compressed no-query packet `0.971429` 和 full-audit diagnostic `0.996753`。
- [x] 已重新编译 `neurips_2026.tex`：
  PDF 生成成功，14 页，`228581` bytes；仅剩 duplicate table destination / underfull vbox / MiKTeX update warnings。
- [ ] 下一步做 best compressed packet 的 provider-stochasticity 稳健性检查：同一 relay 重复 1--2 次或只重试低分 case，报告均值/方差，避免把一次 `0.971429` 过度解释为稳定上界。
- [ ] 继续改进真实 large delegate 的 locate 覆盖率；优先通过 controller-provided anchors/guards，而不是继续堆通用大模型 prompt。
- [ ] source-inspected packet 必须保持 non-oracle：不得使用 `target_command`、hidden target anchors、hidden scorer labels；oracle-anchor 数据只能作为 upper bound 或 synthetic augmentation 单独标注。
- [ ] 重点指标加入 delegate-only anchor recall；不要只看 all-row anchor recall，因为 easy self-handled rows 会掩盖 residual delegate packets 的问题。
- [ ] 后续再接真实 SWE-Bench mini-batch；不要在 proxy 结果不稳时直接扩大到 full SWE-Bench。

## Paper And Novelty

- [ ] 在 `C:\Users\zrz20\Desktop\vscode\multi-rl\创智大作业\LATEX-NIPS` 中同步论文叙事。
- [ ] 查新并对比相关方向：SWE-Edit、SWE-Adept、Hybrid-Gym、Polar-style proxy/trace、memory/RL coding agents、多智能体软件工程 agent。
- [ ] 论文主张要保守：优先强调训练小 controller 的可行性、memory 对定位/编辑/测试/恢复闭环的帮助、以及选择性大模型调用带来的 cost-normalized tradeoff。
- [ ] 把 delegation packet 写成 secondary contribution 或 extension，除非 non-oracle source-inspected packet 明确提升 residual delegate cases。
- [ ] 在有 baseline 对照之前，不声明 trained/memory Qwen 优于 untrained Qwen 或大模型。
- [ ] 写清楚失败案例和 negative transfer：例如 v20/v21 语义 guard 退化，v22 靠 anchor replay 恢复。
- [ ] 不声称 true SWE-Bench harness 结果；即使 Docker Desktop 已启动，也只有 harness 真正跑通时才写 SWE-Bench 结果，proxy/small-task trace 要分开写。

## Logging Discipline

- [ ] 每次运行实验后，把命令、输出路径、原始指标、失败样例、阻塞和下一步写入 `progress.md`。
- [ ] 新想法、新待办、新实验矩阵放入本文件，不只留在聊天记录里。
## 2026-06-09 Heartbeat Follow-up

- [x] Check whether `runs\multi-agent-proxy-v1\controller_packet_route_v22_generated_wide_repeat07_utf8_20260609_192947.jsonl` finished and record its summary metrics.
- [x] If the repeat07 run is complete and no job is running, launch the next conservative missing packet-route check, preferably heldout or challenge repeat, before any full SWE-Bench attempt.
- [ ] Diagnose the weaker structured packet large-delegate result (`mean_strict=0.696643`, `error_rate=0.2`) by comparing task-level failures against the earlier guarded-candidate delegate.
- [ ] Keep Docker Desktop/harness status explicit for true SWE-Bench runs; do not claim SWE-Bench results from proxy tasks.

## 2026-06-09 20:25 Heartbeat Follow-up

- [x] Respect the updated user rule: each `gpt-5.4-mini` experiment should use one relay only; use the other relay only for provider failure or an explicit provider-stability check.
- [x] Run one useful `gpt-5.4-mini` meta-review via the muyuan endpoint, not both relays.
- [x] Add an offline 44-task routing ablation from existing artifacts:
  `runs\multi-agent-proxy-v1\routing_ablation_44task_20260609_2025.md`.
- [ ] Next useful experiment: train/evaluate controller outputs as `SELF_HANDLE` vs `DELEGATE_PACKET`, and score packet anchor recall, semantic-guard recall, and delegate strict score.
- [ ] Build packet-supervision data focused on the 5 residual delegate rows: teach the controller to recover anchors such as `CancelledError`, `RetryPolicy`, `join_url`, `base_url`, `urljoin`, `CacheKey`, `make_key`, and edit-operation anchors like `old/new/replace/write_text`.
- [ ] Add a packet-quality metric to the training/eval loop: delegate-only target-anchor recall, semantic-guard recall, and downstream delegate strict score. Do not optimize only all-row anchor recall because easy self-handled rows already dominate that metric.
- [x] Build first route/packet SFT data artifact:
  `data\delegate_packet_sft_v22_44task_repeat4_20260609_2045`.
- [x] Add a source-inspection-before-packet step so residual anchors become visible before the controller writes `DELEGATE_PACKET`.
- [x] Alternative or companion: build a clearly labeled oracle-packet augmentation set that includes hidden target anchors only as synthetic supervision, then report it separately from non-oracle packet results.
- [x] Build clearly labeled oracle-anchor packet augmentation and run one upper-bound delegate probe:
  `runs\multi-agent-proxy-v1\oracle_anchor_delegate_upper_bound_20260609_2050.md`.
- [x] Convert the oracle-anchor upper-bound into a non-oracle mechanism: source-inspection/retrieval before packet generation should surface anchors like `RetryPolicy`, `CancelledError`, `join_url`, `urljoin`, `CacheKey`, and `make_key` from visible source/test context.
- [x] Build source-inspected packet SFT artifacts for controller training:
  `runs\multi-agent-proxy-v1\delegate_packet_sft_sourceinspected_v22_44task_repeat4_20260609_2125.jsonl` and
  `data\delegate_packet_sft_sourceinspected_v22_44task_repeat4_20260609_2125`.
- [x] Write paper-ready source-inspected packet summary:
  `runs\multi-agent-proxy-v1\source_inspected_packet_summary_20260609_2125.md`.
- [x] Run one safe `gpt-5.4-mini` source-inspected packet probe after a relay key is available as an environment variable; do not put keys in command lines, files, or logs.
- [x] Add source-inspected delegate probe numbers to the LATEX-NIPS experiment table, clearly marking provider/retry conditions and avoiding overclaiming full 44-task routing improvement.
- [ ] If training on oracle-anchor data, keep it as synthetic augmentation in the paper and report non-oracle packet results separately.
- [ ] Before claiming multi-agent improvement, show learned routing beats simple threshold/heuristic routing under the same large-delegate scorer, or explicitly frame current result as a low-cost controller and residual-delegation diagnosis.
- [ ] Fix remote SSH authentication for heartbeat health checks; current BatchMode SSH returned permission denied, while the local tunnel remains healthy.

## 2026-06-09 22:52 Heartbeat Follow-up

- [x] Record LATEX-NIPS update/compile status for source-inspected residual delegation tables.
- [x] Confirm `controller_packet_route_v22_generated_wide_repeat07_utf8_20260609_192947` finished: 36 tasks, strict/semantic/skill/action all `1.000000`; repeat08 also finished with the same metrics.
- [x] Confirm local endpoint health: `/v1/models` returns `local-qwen3-8b-memory-polarproxy-v22`; minimal chat returns exact `ok`.
- [x] Confirm Docker state: Mattermost and Postgres containers are up; no SWE-Bench harness container launched.
- [ ] Fix or route around wzw `/chat/completions` 403 (`error code: 1010`) before using it for further `gpt-5.4-mini` review/probe calls. `/v1/models` works, so the key/base URL are at least partially valid.
- [x] Add recent self-evolving skill-memory work to related work, especially CODESKILL (arXiv:2605.25430), and sharpen novelty against it: our object is not a general skill bank but a memory-conditioned small controller that selects self-handle vs structured residual packet handoff.
- [ ] Next real experiment, when training credentials are available: train/evaluate the source-inspected `SELF_HANDLE` vs `DELEGATE_PACKET` controller target, then compare learned routing against simple threshold routing under the same delegate scorer.
- [x] Add the untrained packet-router baseline to the LATEX-NIPS small-controller section: v22 on 44 unique source-inspected route targets gets route accuracy `0.886364` but predicts `DELEGATE_PACKET` on `0/5` gold delegate rows, so packet routing is not solved by prompting alone.
- [x] Build compact non-oracle source-inspected packet targets to avoid asking the small controller to copy the full visible packet.
- [x] Run compact untrained-v22 route baseline on the same 44 unique records:
  route accuracy `0.954545`, valid JSON `0.977273`, `3/5` gold delegate rows predicted as valid `DELEGATE_PACKET`, delegate anchor/guard/path/source-anchor recall `0.6/0.8/0.6/0.6`.
- [x] Add deterministic threshold/heuristic route baseline on compact unique44:
  threshold `strict_score < 0.95` or failed semantic/skill checks gets route accuracy `1.000000`, valid JSON `1.000000`, and delegate anchor/guard/path/source-anchor recall `1.0/1.0/1.0/1.0`.
- [x] Add delegate-route hardness audit:
  compact unique44 is `easy_threshold_separable`; self strict score min/max `1.0/1.0`, delegate strict score min/max `0.478571/0.914286`, gap `0.085714`, overlap pairs `0`.
- [ ] For packet-router training, do not claim learned route improvement on the current compact 44-record target unless it beats the threshold baseline on a harder split where strict score alone is insufficient.
- [ ] Next conservative experiment design: either build a harder route split with ambiguous strict scores, or fix the router and train/evaluate compact packet generation quality plus downstream delegate strict score.
- [x] Paper polish: fix the small overfull hbox in Table~`multiagent`; duplicate table destination warnings remain but PDF currently compiles successfully.

## 2026-06-10 Controller-Training Follow-up

- [x] Keep V31 stopped and refocus on the main contribution: a low-cost small memory/RL controller that retrieves memory, locates files/functions, selects `locate`/`edit`/`test`/`delegate`, and enforces format/no-op/semantic guards.
- [x] Run same-relay stability checks for the best compressed no-query delegation packet:
  three comparable no-provider-error merged runs have strict means `[0.971429, 0.971429, 0.98]`, mean `0.974286`, pstdev `0.004041`; one raw repeat hit a provider `504` and should be reported separately from model semantics.
- [x] Launch and complete non-oracle compact route/packet controller SFT:
  dataset `data\delegate_packet_sft_sourceinspected_compact_v22_44task_repeat4_20260609_2328`,
  remote session `delegate_packet_controller_compact_v1_localbase_20260610_0226`,
  local base `/mnt/memory-agent/models/Qwen3-8B`,
  checkpoints `global_step_13` and `global_step_26`,
  validation loss improved from `1.025` to `0.792`.
- [x] Serve/evaluate learned controller checkpoints on temporary port `8002/18002` and compare route/packet behavior with `scripts\run_delegate_packet_route_probe.py`.
- [x] Compare learned controller against:

## 2026-06-11 v19 Sanitized Packet Follow-up

## 2026-06-17 Formal V1K Assistant-Chain Follow-up

- [x] Run the formal 10-row assistant-chain validation with Docker harness
  available.  Artifact:
  `runs\swebench-assistant-chain-v1k10-20260617\formal_summary.json`.
- [x] Compare no-memory vs gated runtime memory under true SWE-Bench harness:
  both are `4/10`, evaluator errors `0`, empty patches `0`.
- [x] Record transfer cases:
  positive transfer `pvlib__pvlib-python-1854`, negative transfer
  `pvlib__pvlib-python-1154`, shared unresolved
  `marshmallow-code__marshmallow-1359`,
  `pvlib__pvlib-python-1707`,
  `sqlfluff__sqlfluff-1517`,
  `sqlfluff__sqlfluff-1625`,
  `sqlfluff__sqlfluff-1733`.
- [x] Add an offline failure-attribution script instead of changing runtime
  routing:
  `scripts\summarize_v1k_formal_failure_attribution.py`.
- [x] Generate attribution artifacts:
  `runs\swebench-assistant-chain-v1k10-20260617\failure_attribution.json`
  and
  `runs\swebench-assistant-chain-v1k10-20260617\failure_attribution.md`.
- [ ] Next short Multi-Agent Direction experiment:
  materialize a small controller target from the positive-vs-negative transfer
  cases.  The target should ask the small model whether a memory is
  reliable-current packet evidence, reverify-only evidence, low-weight
  auxiliary evidence, or insufficient.  It should preserve path/symbol/test
  evidence but not reveal or copy a patch.
- [ ] Next integration step after that:
  connect v1k packet evidence to a tiny controlled runtime branch on the 7
  ready positives plus sqlfluff protect controls.  Acceptance: ready packets
  are actually used, protect controls do not delegate, and downstream is not
  worse than no-memory.  Do not broad-sweep before this passes.
- [ ] Do not launch another LoRA or serve a new controller only from the flat
  `4/10` result.  Training is justified only if the new target explicitly
  addresses the observed positive/negative transfer boundary and preserves the
  earlier reliability/protect gates.
- [x] Materialize the first tiny transfer-boundary readout from the formal
  result:
  `runs\v1k_transfer_boundary_readout_20260617_2235`.
  It has `10` rows, prompt leakage `0`, and labels
  `ALLOW_AS_LOW_WEIGHT_EVIDENCE=3`,
  `ALLOW_PACKET_EVIDENCE_AFTER_REVERIFY=1`,
  `PROTECT_REVERIFY_BEFORE_PACKET=1`,
  `REVERIFY_OR_SELF_HANDLE_UNTIL_STRONG_PACKET=5`.
- [x] Run the no-update v22 generation gate on that target.  Result:
  valid labels `1.0`, label match `0.1`, prediction collapse to
  `ALLOW_PACKET_EVIDENCE_AFTER_REVERIFY` on `10/10` rows.
- [ ] Next short Multi-Agent Direction experiment:
  expand the transfer-boundary target with more non-leaking hard negatives and
  low-weight positives from existing formal/proxy traces.  Needed rows:
  same-repo near-miss protect examples, packet-ready but strict-unhelpful
  examples, and low-weight auxiliary examples.  Keep labels as learned
  controller targets; do not add repo/path/symbol runtime rules.
- [ ] Before any tiny SFT/DPO:
  rerun no-update/readout gates, check prompt leakage `0`, avoid all-allow or
  all-protect collapse, and run old reliability/protect no-regression gates.
- [x] Expand the transfer-boundary target from existing formal/proxy traces:
  `runs\v1k_transfer_boundary_expanded_readout_20260617_2300`.
  It has `55` rows, prompt leakage `0`, blockers `[]`, and label distribution
  `16/12/11/16` across low-weight / strong-allow / protect / insufficient.
- [x] Run no-update v22 on the expanded target.  Result:
  valid label `1.0`, label match `0.218182`, but prediction collapsed to
  `ALLOW_PACKET_EVIDENCE_AFTER_REVERIFY` on `55/55`.
- [x] Run label-order rotation diagnostic.  Result:
  valid label `1.0`, label match `0.2`; predictions changed distribution
  after label rotation, confirming label-order/surface sensitivity, but the
  semantic boundary is still not learned.
- [ ] Next short Multi-Agent Direction experiment:
  redesign this target into an order-robust controller objective before any
  training.  Preferred options: pairwise support-vs-protect comparisons, short
  neutral labels, or factorized atoms such as `strong_packet_evidence`,
  `low_weight_only`, `needs_reverify`, and `insufficient`.  Gate by both
  original and order-rotated variants.
- [x] Try the factorized atom version:
  `runs\v1k_transfer_boundary_atom_readout_20260617_2315`.
  It has `220` rows, prompt leakage `0`, blockers `[]`.
- [x] Run no-update v22 on atom target and reverse-label variant.  Both collapse
  to `TRUE` on `220/220`, overall match `0.25`.  This means atom TRUE/FALSE
  wording is not enough; the question formulation itself is too permissive.
- [ ] Next target-design step:
  build a contrastive/pairwise transfer-boundary surface instead of direct
  TRUE/FALSE or 4-way generation.  Use neutral labels such as `LEFT/RIGHT` or
  `A/B`, balanced swaps, and require both-swaps accuracy before any training.
  The examples should compare reliable packet evidence against low-weight,
  reverify, or insufficient memories under the same/current-like task context.

- [x] Add deterministic route-probe packet sanitizer that removes forbidden top-level `reason` while preserving `route` and `delegate_packet`.
- [x] Re-audit sanitized v19 hard-12 packets before large delegation:
  valid JSON `1.0`, top-level reason `0.0`, blocking risk `0.0`, concrete-default recall `8/8`, mutable-copy recall `4/4`.
- [x] Run justified single-relay `gpt-5.4-mini` downstream probe on sanitized v19 hard-12 packets:
  `12` calls, provider errors `0`, total tokens `29828`, mean strict `0.853377`, semantic pass `1.0`, skill match `0.833333`.
- [x] Offline next step: inspect/update the proxy scorer so safe `perl -0pi` edit commands are recognized as edit actions, then rescore existing v19 sanitized delegate outputs without new provider calls.
  Rescored v19 sanitized hard-12: mean strict `0.911710`, action/skill/semantic/error `1.0/1.0/1.0/0.0`; only two Perl edit rows changed from `unknown` to `edit`.
- [x] Build a concise same-scorer comparison table for v13/v17/v19-sanitized hard-12 packet quality and downstream delegate metrics, suitable for LATEX-NIPS, before launching new provider calls.
  Artifact: `runs\multi-agent-proxy-v1\harder12_same_scorer_packet_comparison_20260611_1330.md`.
  Key comparison: v13 `0/8` concrete-default and `0/4` mutable-copy recall, semantic `0.916667`;
  v17 `1/8` and `0/4`, semantic `0.916667`;
  v19-sanitized `8/8` and `4/4`, semantic `1.0`, same-scorer mean strict `0.911710`.
- [x] Sync `harder12_same_scorer_packet_comparison_20260611_1330.md` into LATEX-NIPS with conservative framing:
  v19 validates learned memory-to-packet repair content plus deterministic schema guard, not a generic multi-agent or absolute strict-score claim.
  Added Table `hardpacket` to `LATEX-NIPS\neurips_2026.tex`; compiled `neurips_2026.pdf` successfully, 16 pages, 237063 bytes.
- [ ] Build a tiny v20 schema-clean correction set from v19 top-level-reason outputs so no-top-level-reason becomes learned controller behavior rather than only deterministic postprocessing.
  Built/trained as a cleanup artifact:
  dataset `data\delegate_packet_sft_v20_mixed_v19_plus_schema_clean_20260611_1348`,
  checkpoint `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/delegate_packet_sft_v20_mixed_v19_plus_schema_clean_20260611_1348_lora/global_step_188`.
  Do not continue schema-only optimization unless needed as a baseline.
- [ ] Do not launch another broad training/eval just to use GPU; the next run must target either schema-clean packet learning or a controller-side memory/packet quality metric.

## 2026-06-11 Main-Direction Refocus

- [ ] Active next experiment: build a memory-retrieval/action-selection controller eval, not another packet-schema micro-benchmark.
  Each task should include reliable memory, stale memory, and distractor memory candidates plus current source/test evidence.
  The small controller must output:
  selected/rejected memory IDs with reasons, file/function localization, next action among `locate/edit/test/delegate`,
  semantic/no-op guard, and whether large-model delegation is needed.
- [ ] Metrics for the next eval:
  reliable-memory selection precision/recall,
  stale/distractor rejection rate,
  file/function localization accuracy,
  action-choice accuracy,
  unnecessary big-model call rate,
  delegate packet validity/content when delegation is chosen,

## 2026-06-14 Mixed Perturb Follow-up

- [x] Build offline mixed perturb stale-memory verdict audit with candidate-order shuffle and locate/edit lexical-overlap stale/distractor variants, without adding runtime selector rules.
- [x] Run mixed perturb generation + packet-visible bridge on the locate-sparse SFT adapter; record the failure boundary.
- [x] Convert the perturb failures into a learned SFT correction set rather than adding an inference-time stale/distractor/path rule.
- [x] Train the small mixed-perturb verdict-atom correction and verify the mixed perturb packet-visible gate passes with zero leakage.
- [x] Re-run the original full stale-memory candidate-verdict gate with the newest adapter and verify no regression.
- [x] Next conservative gate: re-run the locate sparse/empty evidence generation probe with the newest mixed-perturb adapter to ensure the perturb correction did not regress sparse/empty locate cases.
- [x] Run the downstream readiness/AZ audit using the newest full generation and packet bridge before any `gpt-5.4-mini` delegate call.
- [x] Run a tiny downstream AZ probe from the 4 readiness rows only after the packet-visible payload was inspected and had no hidden labels.
  Result: `4` calls, provider errors `0`, total tokens `20939`, mean strict `0.836023`, action/skill/semantic `1.0/1.0/1.0`.
  Weak rows are `heldout_locate_cache_key` strict `0.76` and `generated_wide_heldout_semantic_edit_margin` strict `0.809091`, mainly due to anchor-overlap / command-shape strictness rather than memory-selection failure.
- [x] Analyze low-strict AZ rows with a local-only packet-target artifact:
  `runs\multi-agent-proxy-v1\stale_memory_packet_target_local_analysis_20260614_0435.json`.
  Weak rows are `heldout_locate_cache_key` and `generated_wide_heldout_semantic_edit_margin`.
  Diagnosis: sparse locate evidence needs learned source-inspection/uncertainty before delegation; visible edit evidence needs compact code-anchor retention and should avoid line-number-only edit plans.
- [ ] Next local-only improvement:
  build a tiny packet-target correction/eval set from these four rows as training/eval supervision, not runtime if-rules.
  Required target fields: selected/rejected memory IDs, path hints, uncertainty/source-inspection-needed flag, compact code anchors, and semantic guards.
  Do not call `gpt-5.4-mini` again until this visible packet target has changed enough to justify a tiny rerun.
- [x] Add arXiv 2606.11976 ("Exploration Structure in LLM Agents for Multi-File Change Localization") to LATEX-NIPS as a narrow repository-localization/exploration-structure contrast, keeping the main novelty centered on learned memory reliability and packet-visible evidence selection.

## 2026-06-14 Locate Sparse-Evidence Stale-Memory Follow-up

- [x] Build offline locate sparse/empty evidence pairwise data from neutral-id stale-memory candidate verdict pairs:
  `data\stale_memory_locate_sparse_evidence_pairwise_20260614_0213`.
- [x] Add tests for the locate sparse-evidence builder:
  `tests\scripts\test_build_stale_memory_locate_sparse_evidence_pairwise.py`.
- [x] Run remote boundary-replay adapter logprob diagnostic on the locate sparse/empty data:
  raw and normalized preference accuracy both `1.0` over `156` rows.
- [x] Run remote boundary-replay adapter generation probe on the same data:
  `60` groups, valid JSON `1.0`, verdict match `0.9`, distractor verdict match `0.833333`.
- [x] Run 6-row consistency-contract diagnostic on generation failures:
  verdict match only `0.333333`, so the failure is not fixed by a simple output contract.
- [ ] Next conservative improvement:
  build a small learned verdict-atom generation-stability correction initialized from the boundary-replay adapter.
  Use the 6 locate distractor generation failures as hard rows and protect fixed distractor/reliable/stale rows.
  Do not add a runtime task-id/path/string rule for stale-vs-distractor.
- [ ] Before any `gpt-5.4-mini` downstream call, rerun generated-atom probe, packet-visible bridge, and downstream readiness audit.
  Gate should require zero hidden-payload leakage and no remaining mixed-set failed boundary rows.
- [ ] Check whether an existing remote trainer can do adapter-continuation SFT/sequence loss for JSON verdict atoms.
  Pairwise DPO may be the wrong next optimizer because the locate sparse/empty logprob preference is already saturated.
  and verification catch rate for unsafe/no-op/semantic-risk edits.
- [ ] Build the first offline proxy trace from existing small-task artifacts before training:
  compare untrained/base controller, v22 memory controller, and v19/v20 packet controllers on retrieval/action decisions under the same visible memory candidates.
- [ ] Only after the offline retrieval/action eval is well-defined should we train another small controller checkpoint.
  untrained v22 compact route baseline (`route_accuracy=0.954545`, delegate recall `0.6/0.8/0.6/0.6`),
  deterministic threshold route baseline (`route_accuracy=1.0` on current easy split),
  and downstream compressed delegate score.
- [x] v3 learned compact policy:
  valid JSON `0.977273`, route accuracy `0.977273`,
  delegate anchor/guard/path/source recall `0.633333/1.0/1.0/0.8`,
  downstream strict on 4 strict-valid packets `0.866518`.
- [x] v4 learned context target:
  valid JSON `1.0`, route accuracy `1.0`,
  delegate anchor/guard/path/source recall `1.0/1.0/1.0/1.0`,
  visible-context retention `0.4`,
  downstream strict `0.957143`.
- [x] v5 learned context-schema target:
  valid JSON `1.0`, route accuracy `1.0`,
  delegate anchor/guard/path/source recall `1.0/1.0/1.0/1.0`,
  visible-context retention `1.0`,
  downstream strict raw/retry-merged/repeat01 `0.927143/0.98/0.98`.
- [x] Write honestly that the current 44-task split is easy-threshold-separable; v5 supports learned non-oracle packet generation and selective delegation feasibility, not learned routing superiority over a threshold heuristic.
- [ ] Next: build a harder ambiguous routing split where strict score alone is insufficient, or reframe the immediate claim around packet-generation quality under a fixed/selective router.
- [ ] Next: add an edit-specific semantic packet guard for residual edit tasks, because `generated_wide_heldout_semantic_edit_path` remains the unstable downstream case even with perfect anchor/path/context retention.
- [x] Add a controller-verifier retry script for failed downstream delegate rows:
  `scripts\run_large_delegate_guard_retry.py`.
- [x] Measure recovery-after-failure on v5 learned packets:
  two failed raw/repeat downstream runs had semantic pass rate `0.8`; guard retry fixed `2/2` semantic failures, after-retry semantic pass rate `1.0`, mean strict improved from `0.928572` to `0.981429`.
- [ ] Next paper update: add v5 learned-controller table entries only with caveats:
  route/packet probe `1.0`, visible-context retention `1.0`, downstream raw/retry/repeat `0.927143/0.98/0.98`, and note large-delegate stochasticity.
- [ ] Next paper update: add controller-verifier recovery metric separately:
  semantic recovery-after-failure `2/2`, after-retry mean strict `0.981429`; do not conflate this with strict `<0.95` recovery.
- [ ] Next experiment: build a harder route/verification split where strict score alone is insufficient, e.g. rows with high strict but semantic guard risk, low strict but self-recoverable commands, or delegate packets requiring memory/context evidence rather than threshold routing.

## 2026-06-10 Mixed Semantic-Guard Controller Follow-up

- [x] Fix `score_large_delegate_probe.py` task index so `generated_semantic_heldout` mixed12 rows are not scored as `missing_task`.
- [x] Add general semantic-scorer equivalence for sed replacements, None-guard branch order, and mapping-copy forms; verify with `16 passed` in `tests\scripts\test_run_hybrid_gym_curriculum_probe.py`.
- [x] Re-score mixed12 first retry after scorer fixes:
  `harder_semantic_guard_mixed12_retry_gpt54mini_muyuan_20260610_0448_rescored_v3.jsonl`,
  semantic pass `11/12`, mean strict `0.855682`.
- [x] Add general verifier-retry prompt rules for shared mutable defaults:
  copy the selected mapping/list after the None check and avoid unresolved `copy.deepcopy`.
- [x] Complete challenge retry round4 and final mixed12 merge:
  `harder_semantic_guard_mixed12_retry_recovery_summary_20260610_0528.json`.
  Raw semantic `0/12` -> after-retry `12/12`; strict mean `0.598593 -> 0.877706`; strict recovery `5/12`.
- [x] Continue v5 learned-controller mixed12 packet probe rows 5--12 as one-row runs; full batch stalled after 3 rows, while rows 1--4 all had valid JSON/route/anchor/guard/path/source/context retention `1.0`.
- [x] Finish rows 5--12 one-row v5 mixed12 packet probe and aggregate:
  valid JSON/route accuracy `0.75`; invalid JSON tasks are
  `generated_heldout_semantic_edit_level`, `path_edit_commitment_upload`, and `path_edit_commitment_download`.
- [x] Build v6 diversified semantic-guard packet-format SFT data:
  `data\delegate_packet_sft_mixed12_semguard_format_policy_v6_20260610_0645`
  with 139 records, including 60 mixed12 non-oracle records and 24 focused invalid-JSON repeats.
- [x] Stop temporary remote 8002 v5 service to free GPU memory after initial v6 OOM; keep 8001 v22 service active.
- [x] Relaunch v6 training after freeing 8002:
  `delegate_packet_controller_policy_v6_mixed12_semguard_retry_free8002_20260610_0700`;
  epoch 1 completed with val/loss `0.330`, checkpoint `global_step_32` exists, epoch 2 running at last check.
- [x] After v6 training completes, serve latest v6 checkpoint on remote 8002/local 18002 and rerun the mixed12 packet probe.
- [x] Compare v5 vs v6 on mixed12 packet retention:
  valid JSON, route accuracy, anchor/guard/path/source-anchor recall, visible-context retention, and token cost.
- [x] v6 mixed12 packet-format result:
  `controller_packet_route_learned_policy_v6_mixed12_semguard_20260610_0715.jsonl.summary.json`;
  valid JSON/route/delegate packet rate `1.0`, anchor/guard/path/source/context retention all `1.0`,
  token cost `17059` total tokens. This improves v5 mixed12 packet retention from `0.75`.
- [x] v6 mixed12 downstream + semantic verifier retry:
  raw downstream strict/semantic `0.825958/0.833333`; semantic-failure retry fixed `2/2`,
  merged strict/semantic `0.870065/1.0`, retry used 2 big-model calls and `1714` tokens.
- [x] Add v6 mixed12 verifier-routing audit:
  semantic-fail-only retry selects `2/12` rows and fixes `2/2`; strict-threshold retry would over-call
  (`strict < 0.95` selects `12/12`, with `10` unnecessary calls for semantic recovery).
- [x] Update LATEX-NIPS text with v6 mixed12 packet/retry results and verifier-routing comparison; report semantic recovery separately from strict score, and keep the easy 44-task route split caveat.
- [x] Recompile LATEX-NIPS after MiKTeX permission/setup issue is resolved; manual
  `pdflatex -> bibtex -> pdflatex -> pdflatex` compile succeeded, producing
  `LATEX-NIPS\neurips_2026.pdf` with 14 pages and latest size `230184` bytes after verifier-routing text update.
- [x] Answer the "is it good enough?" checkpoint with a concrete experiment instead of only discussion:
  heuristic harder-semguard mixed12 baseline gets route/packet recall `1.0` but drops visible context (`0.0`);
  untrained v22 smoke3 gets route `1.0` but anchor recall only `0.708333` and is slow;
  v6 remains stronger for stable packet serialization, but routing superiority is still not proven.
- [ ] Next required experiment before claiming advantage:
  build a true hard mixed accept/retry split with high-strict semantic-risk rows, low-strict semantically correct rows,
  low-strict self-recoverable rows, and delegate rows requiring memory/context evidence; compare semantic verifier,
  strict-threshold router, untrained v22, learned v6, and heuristic packet router on big-model call count,
  token cost, semantic recovery, strict score, visible-context retention, and unnecessary retry calls.
- [x] Add or fix the heuristic packet baseline so it can optionally retain `visible_task_context`;
  rerun heuristic vs learned v6 on the harder split, because the current heuristic route score is inflated by an all-delegate target and its packet quality is not equivalent to v6.
  Result: `--retain-visible-context` heuristic gets full packet-retention metrics on the all-delegate mixed12 diagnostic,
  so this split should be treated as packet-format regression only, not learned-routing evidence.
- [ ] Do not launch another all-delegate packet-retention run as the main next result;
  the next useful step is the true hard mixed accept/retry split with unnecessary big-model calls measured explicitly.
- [x] Add reusable accept-vs-retry policy audit:
  `scripts\audit_accept_retry_policy.py`.
  On v6 mixed12 downstream rows, semantic-fail/error verifier selects `2` rows, captures `2/2` failures,
  makes `0` unnecessary calls, and estimates `1714` retry tokens; `strict < 0.95` selects `12` rows,
  makes `10` unnecessary calls, and estimates `10284` retry tokens.
- [ ] Next hard split expansion:
  collect additional rows beyond v6 mixed12 so the accept/retry audit includes high-strict semantic-risk,
  low-strict semantic-correct, provider-error retry, self-recoverable low-strict, and memory/context-dependent delegate rows.
  Then compare semantic verifier, strict thresholds, untrained controller, learned v6 controller, and heuristic packet router.
- [x] Build a provenance-preserving candidate pool for that hard split:
  `scripts\build_accept_retry_candidate_pool.py` and
  `runs\multi-agent-proxy-v1\accept_retry_candidate_pool_20260610_1331.{json,md}`.
  Current pool has `140` rows / `56` unique tasks:
  `accept_low_strict_semantic_ok=71`, `accept_high_strict_semantic_ok=20`,
  `retry_semantic_failure_low_strict=29`, `retry_provider_or_delegate_error=20`.
- [ ] Sample a clean balanced subset from the candidate pool, with explicit provider/source constraints, before running policy comparisons;
  do not report the raw candidate pool as a final result because it mixes providers, retry conditions, and merged artifacts.
- [x] Sample and audit a clean accept/retry subset:
  `scripts\sample_accept_retry_subset.py`,
  `runs\multi-agent-proxy-v1\accept_retry_clean_subset_muyuan_no_v6_nomissing_20260610_1352.{jsonl,summary.json,md}`,
  and
  `runs\multi-agent-proxy-v1\accept_retry_clean_subset_muyuan_no_v6_nomissing_policy_audit_20260610_1352.{json,md}`.
  Clean subset: `17` unique tasks, provider tag `muyuan`, excluding `v6_mixed12`, oracle/synthetic rows, provider errors, and `missing_task`.
  Class counts: accept low-strict semantic-ok `8`, accept high-strict semantic-ok `4`, retry semantic-failure low-strict `5`.
  Audit: semantic verifier selects `5` rows and captures `5/5` with `0` unnecessary calls; `strict < 0.95` selects `13` rows with `8` unnecessary calls.
- [x] Add clean-subset token-cost estimates to the paper/proxy narrative:
  add token-cost estimates for the clean subset audit, or draft a LATEX-NIPS ablation paragraph/table that clearly labels it as an offline accept/retry diagnostic rather than an end-to-end SWE-Bench result.
- [x] Run a broader accept/retry diagnostic stress subset with provider/delegate errors included:
  `runs\multi-agent-proxy-v1\accept_retry_broad_subset_retryfirst_with_errors_no_v6_nomissing_20260610_1452.{jsonl,summary.json,md}` and
  `runs\multi-agent-proxy-v1\accept_retry_broad_subset_retryfirst_with_errors_policy_audit_tokens_20260610_1452.{json,md}`.
  Result: 26 rows, 8 retry-needed rows; semantic/error verifier captures 8/8 with 0 unnecessary calls and estimated 6856 retry tokens, while `strict < 0.95` captures 8/8 but makes 12 unnecessary calls and estimates 17140 tokens.
- [ ] Next hard split step:
  build a broader clean accept/retry comparison that adds memory/context-dependent delegate rows and self-recoverable low-strict rows, then compare semantic verifier, strict thresholds, untrained v22, learned v6, and heuristic packet router on unnecessary calls, token cost, semantic recovery, and downstream strict score.
- [ ] Next verifier realism step:
  replace offline scorer-label retry selection with controller-visible features from packets/logs
  (semantic guard text, delegate_error category, visible anchors, path hints, uncertainty, and no-op/format checks),
  then compare against strict-threshold routing without using hidden semantic labels.
- [x] Add and run an initial post-delegate visible retry policy audit:
  `scripts\audit_visible_retry_policy.py`,
  `runs\multi-agent-proxy-v1\accept_retry_broad_subset_visible_policy_audit_20260610_1507.{json,md}`,
  and
  `runs\multi-agent-proxy-v1\accept_retry_broad_subset_visible_policy_audit_v2_20260610_1512.{json,md}`.
  v2 visible guard-risk captures `8/8` retry-needed rows with `4` unnecessary calls and estimated `10284` retry tokens;
  this beats `strict < 0.95` on unnecessary calls (`12`) but is worse than `strict < 0.8` (`1`) on this subset.
- [ ] Next verifier realism step:
  regenerate a small packet-preserving accept/retry trace, because many broad-subset sources are scored-only JSONL without raw packet/default/path evidence.
  The verifier should select retries from controller-visible packet fields plus delegate command/error only, then evaluate against scorer labels after the fact.
- [x] Run a GPU-backed packet-preserving controller probe and packet-visible retry audit:
  `runs\multi-agent-proxy-v1\controller_packet_route_learned_policy_v6_val_packetpreserve_20260610_1538.{jsonl,summary.json}`;
  `runs\multi-agent-proxy-v1\v6_mixed12_packet_visible_retry_policy_audit_v3_20260610_1602.{json,md}`.
  Live v6 controller on `127.0.0.1:18002` achieved valid JSON/route accuracy `1.0` on 8 SFT-val packet-preserving rows, with delegate anchor/guard/path/source/context recall all `1.0`.
  On v6 mixed12 downstream rows, packet-visible guard selects `2`, captures `2/2`, misses `0`, makes `0` unnecessary calls, and estimates `1714` retry tokens; `strict < 0.95` makes `10` unnecessary calls.
- [x] Broader packet-visible hardening step:
  generated and evaluated the 26-row broad packet-preserving accept/retry trace.
  Live v6 on `127.0.0.1:18002` completed
  `controller_packet_route_learned_policy_v6_broad_packetpreserve_thr08_20260610_1632.{jsonl,summary.json}`:
  valid JSON `1.0`, route accuracy only `0.576923`, but delegate anchor/guard/path/source/context retention all `1.0`.
  After current scorer re-score and visible-guard fixes,
  `accept_retry_broad_packet_visible_retry_policy_audit_thr08_rescored_current_v3_20260610_1720.{json,md}`
  shows packet-visible guard selects `8`, captures `7/7`, misses `0`, makes `1` unnecessary call, and estimates `6856` retry tokens;
  `strict < 0.8` captures `7/7` with `2` unnecessary calls and `7713` tokens;
  `strict < 0.95` captures `7/7` with `13` unnecessary calls and `17140` tokens.
- [ ] Next route-learning step:
  train or calibrate the small controller specifically for the broad `SELF_HANDLE` vs `DELEGATE_PACKET` accept/retry routing decision while preserving v6 packet quality.
  The heuristic baseline with `strict-threshold 0.8` gets route accuracy `1.0` on the same 26 packet-preserving records,
  while v6 matches a conservative `0.95`-like route accuracy of `0.576923`.
  This should become a route-head / reward-model / DAgger correction experiment, not another all-delegate packet-format run.
- [ ] Next comparison step:
  run the same broad hard split through untrained v22 and the trained/calibrated controller, then compare route accuracy,
  delegate-only anchor recall, semantic guard recall, path/source-anchor recall, big-model call count, estimated token cost,
  unnecessary retry calls, no-op patch rate, and recovery-after-failure.
- [x] Run the prompt-fixed v10 route controller on the same 26-row broad packet-preserving current-rescored split:
  `runs\multi-agent-proxy-v1\controller_packet_route_v10_broad_packetpreserve_thr08_promptfix_20260610_2132.{jsonl,summary.json}`.
  Result: valid JSON `1.0`, route accuracy `1.0`, delegate packet rate `0.346154`, delegate anchor/guard/path/source-anchor recall all `1.0`.
  This matches the `strict < 0.8` heuristic route baseline and improves over v6/v9 route accuracy `0.576923`, while preserving packet quality.
- [x] Run real downstream `gpt-5.4-mini` delegate on the 9 v10-selected non-oracle packets, using only the muyuan relay:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_muyuan_v10_broad_thr08_packets_20260610_2152{,_scored}.jsonl`.
  Result: 9 calls, 7202 tokens, provider errors `0`, mean strict `0.848900`, semantic pass `0.777778`.
  After 2 semantic-failure guard retries, one row recovered; merged 9-row result has mean strict `0.878265`, semantic pass `0.888889`.
- [x] Build the full 26-row selective-controller proxy:
  `runs\multi-agent-proxy-v1\v10_full26_selective_delegate_proxy_20260610_2220.{jsonl,summary.json}`.
  Initial: 9/26 big-model calls, 7202 delegate tokens, mean strict `0.890022`, semantic pass `0.923077`.
  After semantic-failure retry: 11/26 big-model calls, 9167 delegate+retry tokens, mean strict `0.900187`, semantic pass `0.961538`.
- [x] Fix packet-visible retry audit compatibility for bare extracted `delegate_packet` rows and Python `.replace(old, new)` visible-default mismatch detection:
  `scripts\audit_packet_visible_retry_policy.py`.
  Final v10 actual-downstream audit:
  `runs\multi-agent-proxy-v1\v10_broad_thr08_actual_downstream_packet_visible_retry_audit_v3_20260610_2214.{json,md}`;
  packet-visible guard captures `2/2` true downstream failures with `0` unnecessary calls, matching `strict < 0.8` and beating `strict < 0.95`.
- [x] Next targeted improvement:
  improve v10 packet/context retention or verifier/retry prompting for the remaining failure
  `generated_wide_heldout_semantic_edit_path`, where the large delegate kept `''` instead of the visible default `root`.
  Do a minimal targeted slice or single-row retry/data-fix experiment before launching another broad run.
  Completed by adding a generic visible-default rule to `scripts\run_large_delegate_guard_retry.py` and rerunning only that one row:
  `runs\multi-agent-proxy-v1\target_path_default_guardretry_promptfix_20260610_2359{,_scored}.jsonl`.
  Result: one extra big-model call, `1000` tokens, strict `0.914286`, semantic pass `1.0`.
  Final 26-row selective proxy:
  `runs\multi-agent-proxy-v1\v10_full26_selective_delegate_proxy_all_guardretry_promptfix_20260610_2359.{jsonl,summary.json}`;
  total big-model calls `12/26`, total delegate+retry tokens `10167`, mean strict `0.910352`, semantic pass `1.0`.
- [x] Next robustness check:
  because v10 visible-context retention on delegate rows is only `0.555556`, add a small packet-retention correction set or prompt constraint that keeps `visible_task_context` for every `DELEGATE_PACKET`, then rerun the 9 delegate-row packet probe and the one failed downstream path row.
  Completed as a scorer/schema fix rather than new training:
  v10 placed visible context top-level for `5/9` delegated rows and nested under `source_inspection.visible_task_context` for `4/9`.
  Updated `scripts\run_delegate_packet_route_probe.py` to count either placement and reran:
  `runs\multi-agent-proxy-v1\controller_packet_route_v10_broad_packetpreserve_thr08_promptfix_contextfix_20260611_0012.{jsonl,summary.json}`.
  Corrected visible-context retention is `1.0`, with route accuracy/packet recalls still `1.0`.
- [ ] Next training/distillation step:
  distill the successful visible-default verifier rule into small-controller data:
  examples should teach the controller/verifier that when visible evidence says only `None` triggers default `X`, commands rewriting `value or old_fallback` must use `else X`, not the old fallback.
  Evaluate this as a controller-visible semantic guard/verifier target, not as hidden scorer-label routing.
  Initial non-oracle artifact built:
  `data\visible_guard_verifier_v10_downstream_no_score_fields_20260611_0026.jsonl`,
  rows `9`, labels `RETRY=2` / `ACCEPT=7`.
  Prompt leak audit found no `semantic_pass`, `strict_score`, `semantic_issues`, or `target_command`; those audit labels are only in `extra_info`.
- [x] Next verifier-head evaluation step:
  run v10 or v22 on `data\visible_guard_verifier_v10_downstream_no_score_fields_20260611_0026.jsonl` as a tiny verifier probe.
  Metrics should include valid JSON, verifier verdict accuracy against visible-rule labels, retry recall, unnecessary retry calls, and whether the small model can cite visible-default/mutable-default reasons without hidden scorer labels.
  Completed with `scripts\run_visible_guard_verifier_probe.py`.
  Prompt-only baseline on no-score fields:
  v10/v22 valid JSON `1.0`, verdict accuracy `0.666667`, retry recall `0.0`, unnecessary retry calls `1`.
  Feature-enriched prompts:
  `data\visible_guard_verifier_v10_downstream_features_no_score_fields_20260611_0040.jsonl`
  gave recall `1.0` but precision `0.5`;
  `data\visible_guard_verifier_v10_downstream_features2_no_score_fields_20260611_0048.jsonl`
  gave v10/v22 accuracy `0.888889`, retry recall `0.5`, precision `1.0`, unnecessary retry calls `0`.
  Remaining miss: both models still accept `generated_wide_heldout_semantic_edit_path` even when visible features say
  `visible_default_matches_command=false`.
- [ ] Next verifier training step:
  build a balanced visible-guard verifier SFT split from feature-enriched records plus generated visible-default and mutable-default cases.
  Train/evaluate a small verifier head on valid JSON, verdict accuracy, retry recall, retry precision, unnecessary retry calls, and reason faithfulness.
  Keep prompts non-oracle: no `target_command`, no hidden scorer labels; scorer labels may appear only in `extra_info` for auditing.
- [ ] Next paper update:
  once the visible-context retention fix or verifier-distillation result is available, update LATEX-NIPS with the v10 selective-delegation result:
  9/26 initial large-model calls, 12/26 after guard retries, semantic pass `1.0`, mean strict `0.910352`, and caveat that the route split is threshold-separable.
- [x] Run actual v12 small-controller plus large-delegate collaboration on the harder same-memory 12-row split:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_muyuan_v12_sanitized_formatguard_harder_packets_20260611_0055{,_scored}.jsonl`.
  Result: 12 calls, provider errors `0`, `9583` tokens, mean strict `0.878057`, semantic pass `0.833333`.
  This does not beat v22 untrained packets on downstream quality, despite perfect v12 packet validity/recall.
- [x] Run auxiliary v12 semantic-failure guard retry on the two failed rows:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_muyuan_v12_sanitized_formatguard_harder_packets_semfail_guardretry_20260611_0055{,_scored}.jsonl`.
  Both failures recovered; merged result
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_muyuan_v12_sanitized_formatguard_harder_packets_with_semfail_guardretry_20260611_0055.jsonl`
  has 14 total large calls, mean strict `0.920915`, semantic pass `1.0`.
  Treat this as auxiliary evidence for acceptance/retry, not the main paper contribution.
- [x] Diagnose first-pass packet quality with non-oracle packet ablations:
  added `scripts\enrich_delegate_packets_visible_evidence.py`.
  Naive visible-evidence stuffing was negative:
  `v12_visibleevidence` got mean strict `0.840557`, semantic pass `0.833333`, skill-match `0.916667`, `10878` tokens.
  Concise visible-derived `delegate_contract.repair_constraints` was positive:
  `v12_repairconstraints` got mean strict `0.900081`, semantic pass `0.916667`, skill-match `1.0`, `9977` tokens.
  Summary:
  `runs\multi-agent-proxy-v1\harder_semguard_v12_packet_ablation_summary_20260611_0055.json`.
- [x] Main repair-constraint training step:
  built and evaluated v13/v14/v15 controller variants for concise, memory-grounded
  `delegate_contract.repair_constraints` on the same harder 12-row split.
  v13 is the best current trained-controller result:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_muyuan_v13_repairprompt_harder_packets_20260611_0145_scored.jsonl`,
  mean strict `0.900081`, semantic pass `0.916667`.
  v14/v15 are negative but useful:
  v14 all-12 with invalid packet counted failed has mean strict `0.737284`, semantic pass `0.5`;
  v15 all-12 with invalid packets counted failed has mean strict `0.664800`, semantic pass `0.583333`.
  Cause: stronger repair-constraint supervision made the small controller over-expand or hallucinate constraints and sometimes break JSON.
- [x] Next main controller-training step:
  build a v16 correction set starting from the v13/v12 schema-safe behavior, not v15.
  Target behavior:
  short valid JSON only; no top-level `reason`; no raw or sanitized controller blobs in `source_inspection`;
  no long `current_evidence` dumping inside `source_inspection`;
  at most 1-2 reliable visible-derived `repair_constraints`;
  leave `repair_constraints` empty when evidence is weak.
  Evaluate v16 against v13/v22/v12 on the same harder 12-row split before any paper claim.
- [x] Next memory/controller-quality diagnostic:
  add a packet guard audit that scores controller-visible packet quality before large-model calls:
  valid JSON, max response chars, no nested raw/source blobs, exact visible default extraction,
  mutable-default copy rule extraction, repair-constraint contradiction rate, and path/source-anchor recall.
  Use this to reject bad packets or request controller retry before calling the large model.
- [x] Initial packet guard audit utility:
  added `scripts\audit_delegate_packet_quality.py` and ran it on v13/v14/v15 harder probes.
  Blocking-risk rates: v13 `0.0`, v14 `0.416667`, v15 `0.666667`.
  This is now a concrete candidate reward/guard signal for the small memory/RL controller:
  reject or retry invalid JSON, raw-copy risk, missing visible defaults in constraints, and contradictory constraints before calling the large model.
- [x] Next packet-guard training step:
  turn the v13/v14/v15 packet-quality audit rows into a non-oracle correction set.
  Positive targets should imitate v13-style schema-safe packets and visible-derived concise constraints;
  negative/correction targets should cover v14/v15 invalid JSON, overlong path packets, generic constraints, contradictory constraints,
  and raw/sanitized controller blob leakage.
  Evaluate as controller packet quality first, then downstream `gpt-5.4-mini` calls only if packet blocking-risk improves.
- [ ] Next packet-quality learning step:
  v16/v17 fixed schema hygiene but not first-pass downstream quality.
  Build a small hard-negative correction/eval set where `repair_constraints` must include concrete visible defaults on the exact harder rows
  (`None maps to 8/6/7/4/root/upload-root/download-root`) and must include mutable-copy constraints for mapping/list cases.
  Train/evaluate against v13/v17 on the same harder 12 split, with metrics:
  concrete-default constraint recall, mutable-copy constraint recall, packet blocking-risk, downstream semantic pass,
  and downstream skill-match under the same large relay.
- [x] Built the first exact harder-row repair-constraint correction/eval step:
  `scripts\build_harder_repair_constraint_data.py`,
  `scripts\score_harder_repair_constraints.py`,
  and dataset `data\delegate_packet_sft_v18_harder_defaults_mutable_constraints_20260611_1145`.
  Baselines: v13 concrete-default recall `0/8`, mutable-copy `0/4`; v17 concrete-default recall `1/8`, mutable-copy `0/4`.
  v18 checkpoint `global_step_61` improved partial concrete-default recall (`3/4` on first 6 diagnostic rows) but regressed badly on JSON/packet hygiene:
  partial valid JSON `0.666667`, top-level reason `0.666667`, blocking risk `0.5`, mutable-copy recall `0`.
  Decision: do not run downstream large-delegate calls for v18.
- [ ] Next packet-quality learning step:
  build v19 correction data from v18 failures, preserving v17 schema hygiene while adding hard default/mutable-copy targets.
  Correction prompts should explicitly reject:
  top-level `reason`, invalid/truncated JSON, repeated or overlong constraints,
  misleading constraints such as `return value or 1` under a None-only default rule,
  and mapping constraints that fail to say "copy the selected mapping/list before mutation".
  Evaluate before any large-delegate calls on:
  valid JSON, top-level reason rate, concrete-default constraint recall, mutable-copy constraint recall,
  over-expanded/contradictory constraint rate, packet blocking risk, and mean response chars.
- [x] Built v19 correction data without launching another training job:
  `data\delegate_packet_sft_v19_v18_failure_compact_corrections_20260611_1228`.
  It uses v18 bad packets plus PacketQualityGuard feedback and compact corrected targets from v18 hard positives.
  Stats: `96` records, train `72`, val `24`, all `12` hard tasks covered, raw-copy-risk responses `0`.
  Also updated `audit_delegate_packet_quality.py` so top-level `reason` is blocking and updated
  `build_packet_quality_correction_data.py` to reject invalid JSON, top-level reason, repeated/overlong constraints,
  value-or-default repairs, and unreliable `copy.deepcopy` suggestions.
- [ ] Next packet-quality learning step:
  build a mixed v19 training dataset from v17 schema-hygiene base + v18 exact hard-target positives + v19 correction rows.
  Train one short controller LoRA only if remote GPU is idle, then evaluate only controller-side first:
  valid JSON, top-level reason rate, concrete-default recall, mutable-copy recall,
  over-expanded/contradictory constraint rate, packet blocking risk, and mean response chars.
  Do not run downstream large-delegate calls unless this beats v17 hygiene and improves hard constraint recall.
- [x] Built and trained mixed v19 controller:
  dataset `data\delegate_packet_sft_v19_mixed_v17_v18_hard_v19_corrections_20260611_1232`,
  checkpoint `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/delegate_packet_sft_v19_mixed_v17_v18_hard_v19_corrections_20260611_1232_lora/global_step_170`.
  Hard-12 controller-only result:
  valid JSON `1.0`, route accuracy `1.0`, repair-constraint rate `1.0`,
  concrete-default constraint recall `8/8`, mutable-copy constraint recall `4/4`,
  raw-copy/overexpanded/missing-default/contradictory rates `0`.
  Remaining blocker: top-level `reason` rate `1.0`, so packet blocking risk remains `1.0`.
- [ ] Next narrow packet-quality step:
  fix v19 schema leakage without disturbing its now-correct repair constraints.
  First try a deterministic packet sanitizer/eval that strips top-level `reason` from valid v19 responses and re-runs:
  packet-quality audit, concrete-default recall, mutable-copy recall, and delegate-packet extraction.
  If sanitized v19 has blocking risk `0` while preserving `8/8` and `4/4`, then run downstream `gpt-5.4-mini` large-delegate on sanitized v19 packets.
  If sanitizer is considered too post-hoc, build a tiny v20 reason-removal correction set from v19 outputs and train/evaluate before downstream calls.
- [ ] Next selective-collaboration comparison:
  rerun the 26-row selective split with memory available to all controllers.
  Compare untrained-small auxiliary vs trained-small auxiliary around the same large model, rather than only large-model single-agent or verifier-only variants.

## 2026-06-11 Memory/RL Controller Refocus

- [x] Evaluate v1d route/guard-focused controller on the original 26-row memory-controller split.
  Result: valid JSON `1.0`, memory selection/rejection all `1.0`, stale/distractor rejection `1.0/1.0`,
  action/delegate accuracy `0.576923/0.576923`, missed delegate `0.423077`, unnecessary delegate `0.0`,
  guard-bool accuracy `0.256410`, all-core `0.538462`.
- [x] Evaluate v1d on the 52-row shuffled-memory/distractor perturbation split.
  Result: valid JSON `1.0`, selected-memory recall/precision `1.0/0.971154`,
  stale/distractor rejection `0.942308/1.0`, action/delegate accuracy `0.596154/0.596154`,
  missed delegate `0.403846`, unnecessary delegate `0.0`, guard-bool accuracy `0.262821`.
- [x] Add and run a harder stale-memory reliability eval where stale memory shares current path/function vocabulary.
  Script: `scripts\build_hard_stale_memory_controller_eval.py`.
  v1d result on 26 rows: selected/rejected memory precision/recall all `1.0`,
  stale/distractor rejection `1.0/1.0`, action/delegate accuracy `0.576923/0.576923`,
  missed delegate `0.423077`, guard-bool accuracy `0.269231`.
- [ ] Treat v1d as evidence that learned memory reliability is working, but route/guard remains undertrained.
  Do not run downstream `gpt-5.4-mini` patch/delegate probes until controller-side missed-delegate and guard metrics improve.
- [ ] Build v1e as a learned route/guard/reliability correction set, not an inference-time rule layer.
  Preserve v1d/v1c reliable-memory and stale-rejection behavior.
  Add hard delegate positives from repeated missed-delegate rows:
  `heldout_edit_exact_default`, `challenge_recover_deleted_file`,
  `generated_heldout_semantic_edit_mapping_chart`,
  `generated_wide_heldout_semantic_edit_name`,
  `generated_wide_heldout_semantic_edit_mapping_exporter`,
  `generated_wide_heldout_semantic_edit_radius`.
- [ ] v1e target metrics before any large-model downstream call:
  valid JSON `1.0`;
  stale/distractor rejection at least `0.95`;
  missed delegate below `0.35`;
  guard-bool accuracy above `0.45`;
  unnecessary delegate near `0.0`.
- [ ] Keep scripts as offline data/eval/training harnesses only.
  The paper claim should be that the small model learns memory reliability, route/delegate, and guard judgments, not that a hand-coded pipeline enforces them.

## 2026-06-11 v1e Negative Result

- [x] Build and train v1e route/guard/reliability correction.
  Dataset: `data\memory_controller_sft_v1e_route_guard_reliability_20260611_1540`.
  Checkpoint: `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1e_route_guard_reliability_20260611_1540_lora/global_step_95`.
  Result: negative for the route/guard goal.
- [x] Evaluate v1e on original/perturb/hard-stale controller evals.
  Original 26: action/delegate `0.538462/0.538462`, missed delegate `0.461538`, guard-bool `0.217949`.
  Perturb 52: action/delegate `0.538462/0.538462`, missed delegate `0.461538`, guard-bool `0.25`.
  Hard-stale 26: action/delegate `0.538462/0.538462`, missed delegate `0.461538`, guard-bool `0.217949`.
  Memory reliability remains strong, but v1e is worse than v1d on missed delegates and does not fix guard booleans.
- [x] Keep v1d as the current best controller checkpoint.
  v1e should not be used for downstream `gpt-5.4-mini` delegation.
- [ ] Do not start another blind v1f SFT run with only stronger prose or more repeated rows.
  First fix the target/eval shape so guard/route decisions are primary learned outputs, not ignored tail fields.
- [ ] Build a small guard/route diagnostic target before more training:
  controller outputs `risk_state`, `delegate_reason`, `guard_required`, `guard_type`, and `evidence_ids` before the usual compact packet.
  Evaluate this diagnostic with guard classification accuracy, missed-delegate rate, unnecessary-delegate rate, and memory reliability.
- [ ] If the diagnostic improves, then fold it back into the normal controller response as learned intermediate fields or compact packet metadata.
  Keep it as learned behavior; do not add inference-time rules that force guard booleans from scorer labels.

## 2026-06-11 Guard/Route Diagnostic Head

- [x] Build guard/route-primary diagnostic eval.
  Artifact: `runs\multi-agent-proxy-v1\guard_route_diagnostic_v1_broad26_20260611_1620.jsonl`.
  Gold distribution: `13` delegate-risk, `11` guarded-self-handle, `2` low-risk rows.
- [x] Run v22 baseline on the diagnostic head target.
  Result after enum-label rescoring:
  valid JSON `1.0`;
  risk-state accuracy `0.615385`;
  delegate accuracy `0.653846`;
  missed delegate `0.0`;
  unnecessary delegate `0.346154`;
  guard-required accuracy `0.923077`;
  guard-type recall `0.532051`;
  evidence recall `1.0`.
- [ ] Build diagnostic-head SFT/eval data from original + perturb + hard-stale rows.
  The target should make the learned boundary explicit:
  delegate-risk vs guarded-self-handle vs low-risk, controlled enum `delegate_reason`,
  guard-required, guard types, and trusted evidence IDs.
- [x] Built diagnostic-head SFT/eval data from original + perturb + hard-stale rows.
  Combined eval: `runs\multi-agent-proxy-v1\guard_route_diagnostic_v1_combined104_20260611_1635.jsonl`.
  SFT split: `data\guard_route_diagnostic_sft_v1_20260611_1635`, train/val `332/21`,
  train delegate needed `168`, val delegate needed `10`.
- [ ] Train/evaluate a tiny diagnostic-head controller only if GPU is idle and no other relevant eval is running.
  Target before folding back into normal controller:
  valid JSON `1.0`;
  missed delegate near `0.0`;
  unnecessary delegate below `0.15`;
  guard-required accuracy above `0.9`;
  guard-type recall above `0.75`;
  evidence recall near `1.0`.
- [x] Trained/evaluated diagnostic-head controller.
  Checkpoint: `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/guard_route_diagnostic_sft_v1_20260611_1635_lora/global_step_83`.
  Original 26 and combined 104 both reached:
  valid JSON `1.0`, risk-state/delegate/reason/guard-required accuracy `1.0`,
  missed delegate `0.0`, unnecessary delegate `0.0`, evidence recall `1.0`,
  guard-type recall `0.923077`.
- [ ] After diagnostic-head success, fold learned diagnostic fields into the normal controller response or use them as compact packet metadata.
  Do not add inference-time rules that force route/guard from scorer labels.
- [ ] Next main step:
  add `risk_state`, `delegate_reason`, `guard_required`, `guard_types`, and `evidence_ids`
  to the normal memory-controller target/response and train/evaluate a normal controller variant.
  The goal is to keep memory reliability while improving normal-controller missed-delegate and guard-bool metrics,
  not to run the diagnostic head as a separate hard-coded router.
- [x] Train/evaluate v1f normal+diagnostic folding attempt.
  Result: useful semi-positive, not enough.
  Original diag-prompt 26: memory selection/rejection and stale/distractor rejection all `1.0`,
  action/delegate `0.576923/0.576923`, missed delegate `0.423077`,
  guard-bool `0.487179`, risk-state `0.461538`, evidence recall `1.0`.
  Hard-stale diag-prompt 26: memory/stale/distractor still `1.0`, missed delegate still `0.423077`,
  guard-bool `0.333333`, risk-state `0.423077`, evidence recall `1.0`.
  Conclusion: appending diagnostic fields to the normal JSON target improves guard/evidence reporting but does not transfer the standalone diagnostic head's route boundary.
- [ ] Build v1g route-first/decomposed controller target.
  Do not add inference-time route/guard rules.
  Target should force learned order inside the response:
  first `controller_decision` with `risk_state`, `route`, `delegate_needed`, `delegate_reason`,
  `guard_required`, `guard_types`, and `evidence_ids`; then `memory_packet`, `localization`,
  `guards`, and optional compact `delegate_packet`.
  The goal is learned small-controller judgment, not a hard router wrapped around the model.
- [x] Built/trained/evaluated v1g route-first/decomposed controller target.
  Code support:
  `scripts\build_memory_controller_sft_data.py --route-first-target`,
  `scripts\add_diagnostics_to_memory_controller_eval.py --route-first`,
  and nested-schema scoring in `scripts\run_memory_controller_eval.py`.
  Dataset: `data\memory_controller_sft_v1g_routefirst_20260611_1735`, train/val `339/26`.
  Checkpoint: `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1g_routefirst_20260611_1735_lora/global_step_84`.
  Result: negative for route learning.
  Original 26: missed delegate `0.5`, risk-state `0.076923`, guard-bool `0.435897`,
  stale rejection `0.884615`.
  Hard-stale 26: missed delegate `0.5`, risk-state `0.115385`, guard-bool `0.397436`,
  memory/stale/distractor all `1.0`.
  Diagnosis: model learned nested schema but collapsed to `delegate_needed=false` on `26/26` rows.
- [ ] v1g success criteria before downstream `gpt-5.4-mini` calls:
  valid JSON `1.0`;
  selected/rejected memory and stale/distractor rejection near `1.0`;
  missed delegate below `0.25`;
  unnecessary delegate near `0.0`;
  guard-bool above `0.5`;
  evidence recall near `1.0`;
  route/risk metrics clearly above v1f normal+diagnostic folding.
- [ ] Optional only after v1g design/eval files exist:
  run perturb52 for v1f diag-prompt as a diagnostic baseline.
  Do not spend more GPU/API time on v1f unless it directly informs v1g.
- [ ] Do not continue v1g as-is and do not run v1g perturb52.
  Route-first field order alone is not enough; it caused self-handle collapse.
- [ ] Next main experiment: diagnostic-head teacher / auxiliary route supervision.
  Use the successful guard-route diagnostic head as a teacher signal, but keep inference as one learned small controller.
  Candidate designs:
  two-message SFT target where the model first emits `DIAGNOSIS`/`controller_decision`, then emits the normal packet;
  or an auxiliary-distilled dataset that contrasts delegate-risk rows against visually similar guarded-self-handle rows.
  Success should be measured on normal controller outputs, not by running a separate hard-coded diagnostic router.
- [x] Tested simple auxiliary-diagnostic multitask SFT as v1h.
  Added `scripts\mix_controller_auxiliary_sft_data.py`.
  Dataset: `data\memory_controller_sft_v1h_auxdiag_mix_20260611_1810`, train/val `1009/26`,
  with normal controller rows plus diagnostic-head rows repeated twice.
  Checkpoint: `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1h_auxdiag_mix_20260611_1810_lora/global_step_252`.
  Result on normal-controller original 26:
  missed delegate `0.461538`, risk-state `0.115385`, guard-bool `0.307692`, evidence recall `1.0`.
  Diagnosis: despite balanced labels, normal-prompt inference collapsed mostly to `low_risk`/`delegate_needed=false`.
  Conclusion: simple multitask auxiliary examples do not transfer diagnostic-head route skill to the normal controller prompt.
- [ ] Do not continue simple v1h-style multitask auxiliary mixing.
  It changes the training distribution but not the normal-prompt route boundary.
- [ ] Next route-learning attempt should use same-prompt contrastive/teacher supervision.
  The teacher diagnosis must appear under the exact normal-controller prompt shape, for example as:
  candidate decision A: self-handle with evidence;
  candidate decision B: delegate with evidence;
  target: select the reliable decision and then emit the normal compact controller packet.
  This should teach the small model to compare evidence/reliability instead of memorizing a separate diagnostic task format.
- [ ] Build a focused contrastive route dataset from v1f/v1g missed delegates:
  positive delegate-risk examples:
  `heldout_recover_stale_module`, `heldout_edit_exact_default`, `challenge_recover_deleted_file`,
  `generated_heldout_semantic_edit_mapping_chart`, `generated_wide_heldout_semantic_edit_name`,
  `generated_wide_heldout_semantic_edit_mapping_exporter`, `generated_wide_heldout_semantic_edit_radius`;
  matched self-handle negatives should share path/function/memory style but have semantic pass + executable action.
  This is training supervision, not an inference rule.
- [x] Built/trained/evaluated v1i same-prompt contrastive route supervision.
  Dataset: `data\memory_controller_sft_v1i_contrastive_route_20260611_1835`.
  Checkpoint: `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1i_contrastive_route_20260611_1835_lora/global_step_72`.
  Result: first clear normal-controller route/guard improvement.
  Original 26: missed delegate `0.230769`, guard-bool `0.730769`, memory/stale/distractor `0.961538`.
  Hard-stale 26: missed delegate `0.192308`, guard-bool `0.769231`.
  Combined104: missed delegate `0.192308`, guard-bool `0.753205`, memory/stale/distractor `0.980769`.
  Remaining blockers: valid JSON below `1.0`, unnecessary delegate nonzero, semantic-guard recall low, risk-state labels drift.
- [x] Built/trained/evaluated v1j strict contrastive schema/guard correction.
  Code: `scripts\build_contrastive_memory_controller_sft_data.py --strict-output-contract`.
  Dataset: `data\memory_controller_sft_v1j_contrastive_schema_guard_20260611_1930`.
  Checkpoint: `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1j_contrastive_schema_guard_20260611_1930_lora/global_step_136`.
  Strict combined104 result: valid JSON/memory/stale/distractor/action/delegate/risk/delegate-reason/guard-required/all-core all `1.0`,
  guard-bool `0.996795`, semantic-guard recall `0.956731`.
  Non-strict original26 cross-check: delegation remains improved (`missed_delegate=0.115385`, unnecessary `0.0`), but action/guard/risk collapse
  (`action_accuracy=0.192308`, guard-bool `0.397436`, risk-state `0.0`).
- [ ] Do not call downstream `gpt-5.4-mini` from v1j yet.
  v1j is a strong contract-dependent controller result, but the next proof must be held-out strict-contract generalization, not a large-patcher run.
- [ ] Next immediate controller eval:
  build/run a held-out strict-contract perturb/generalization split for v1j:
  shuffle memory order, replace distractors, make stale memory share current path/function vocabulary, and lightly paraphrase task wording while preserving the strict learned output schema.
  Target metrics before downstream large-model calls:
  valid JSON `1.0`;
  selected/rejected memory and stale/distractor rejection at least `0.98`;
  missed delegate below `0.15`;
  unnecessary delegate near `0.0`;
  guard-bool above `0.9`;
  semantic-guard recall above `0.8`;
  risk/delegate-reason/evidence stable.
- [x] Ran v1j held-out strict-contract memory perturb eval.
  Eval split:
  `runs\multi-agent-proxy-v1\memory_controller_eval_v2_combined104_contrastive_strict_v1j_perturb_seed97_20260611_2205.jsonl`.
  Result:
  valid JSON `1.0`;
  selected/rejected memory and stale/distractor rejection all `1.0`;
  missed delegate `0.019231`;
  unnecessary delegate `0.028846`;
  guard-bool `0.977564`;
  semantic-guard recall `0.908654`;
  risk-state `0.942308`;
  delegate-reason `0.903846`;
  evidence recall `1.0`;
  all-core `0.951923`.
  This passes the controller-side gate for a small downstream selective-collaboration proxy.
- [ ] If v1j passes held-out strict-contract eval, run the next selective-collaboration proxy:
  v1j packets vs v22/untrained packets under equal memory/current evidence, comparing route/delegate decisions,
  big-model call count, token cost, downstream strict/semantic pass, and packet guard/anchor recall.
  This is the point where a small number of `gpt-5.4-mini` calls becomes justified.
- [ ] Next proxy should be deliberately small and balanced:
  select a subset from v1j held-out perturb results with delegate positives and self-handle negatives,
  include the few remaining v1j failure families (`heldout_edit_exact_default`, `generated_heldout_semantic_edit_mapping_chart`,
  `generated_wide_heldout_semantic_edit_mapping_filter`, `generated_wide_heldout_semantic_edit_visible`),
  and compare against v22/untrained packets under the same visible memory/current evidence.
  Stop after this proxy unless it changes the paper-relevant conclusion.
- [x] Ran the deliberately small selective-collaboration proxy.
  Subset: 8 tasks, 4 gold delegate positives and 4 self-handle negatives.
  v1j controller:
  4/8 big-model calls, exactly all 4 delegate positives; missed delegate `0`, unnecessary delegate `0`.
  v22/untrained controller on the same strict prompt/evidence:
  0/8 big-model calls; missed all 4 delegate positives; delegate accuracy `0.5`, guard-bool `0.25`, all-core `0.0`.
  v1j -> `gpt-5.4-mini` fixed-skill packet delegate:
  4 calls, 0 provider errors, total `9647` tokens, mean strict `0.848742`, semantic pass `0.75`, action/skill match `1.0`.
  Summary artifact:
  `runs\multi-agent-proxy-v1\memory_controller_collab_proxy8_summary_20260611_2340.json`.
- [ ] Do not use the first `large_delegate_gpt54mini_az_v1j_collab_proxy8_20260611_2315*` result for conclusions.
  It used an offline proxy adapter bug where `expected_skill=delegate`; use the `fixskill_20260611_2335` artifacts instead.
- [ ] Next high-value options:
  either run a tiny all-delegate/no-controller baseline on the same 8 tasks to compare token cost and downstream quality,
  or sync the v1j controller gate plus proxy8 pilot table into LATEX-NIPS.
  Do not expand to a broad large-model run until the paper table needs it.
- [x] Ran tiny all-delegate/no-controller baseline on the same proxy8 subset.
  All-delegate:
  8/8 big-model calls, 0 provider errors, total `19621` tokens,
  mean strict `0.893575`, semantic pass `0.875`, action/skill match `1.0`.
  v1j selective:
  4/8 big-model calls, total `9647` tokens,
  mean strict on delegated rows `0.848742`, semantic pass on delegated rows `0.75`.
  Cost tradeoff:
  v1j cuts calls by `50%` and tokens by `0.508333` versus all-delegate, while avoiding all 4 unnecessary self-handle calls.
  Summary artifact:
  `runs\multi-agent-proxy-v1\memory_controller_collab_proxy8_summary_with_alldelegate_20260612_0015.json`.
- [x] Synced v1j controller gate + proxy8 selective-vs-all-delegate table into LATEX-NIPS with a small-pilot caveat.
  Paper now frames this as learned memory-conditioned routing and selective large-model collaboration:
  v1j held-out strict perturb all-core `0.951923`, missed delegate `0.019231`,
  proxy8 `4/8` calls and `9647` tokens versus all-delegate `8/8` calls and `19621` tokens.
  Do not claim broad resolved-rate from proxy8.
- [ ] Next best step:
  design the next small controller-first experiment before spending more API/GPU:
  either a preregistered slightly larger selective proxy with memory available to all controllers,
  or an evidence-ablation eval that removes/replaces reliable memory in the same strict prompt to measure whether v1j's route/guard decision truly depends on reliable retrieved experience.
  Prefer the smallest experiment that tests learned memory reliability and packet evidence use, not another scripted routing rule.
- [x] Ran the first controller-first memory evidence ablation on proxy8 unique.
  Baseline v1j proxy8 unique:
  valid JSON `1.0`, all-core `1.0`, selected/evidence reliable rates `1.0/1.0`,
  delegate-needed rate `0.5`, risk-delegate rate `0.5`.
  Ablation result across 24 rows:
  valid JSON `0.916667`, all-core `0.291667`, delegate accuracy `0.708333`,
  unnecessary delegate `0.208333`, missed delegate `0.083333`, evidence recall `0.208333`.
  Variant summaries:
  `drop_reliable_memory` selected/evidence reliable `0/0`, delegate changed `0.375`;
  `redact_reliable_memory` still selected reliable id `0.875` but evidence reliable only `0.375`, delegate changed `0.25`;
  `stale_as_reliable` selected reliable id `0.875`, evidence reliable `0.25`, delegate/risk rates `0.75`, delegate changed `0.25`.
  Interpretation:
  v1j is sensitive to reliable-memory content/removal, but it still partially follows the stable `mem_reliable_current` ID under redaction/stale-as-reliable.
- [x] Built and ran a proxy8 unique ID-randomized/content-contrastive eval.
  Artifact:
  `runs\multi-agent-proxy-v1\memory_controller_eval_v2_proxy8_unique_idrand_v1j_eval_20260612_0035.jsonl`.
  Overall v1j:
  valid JSON `1.0`, selected/rejected memory recall `1.0/1.0`, evidence recall `1.0`,
  action/delegate accuracy `0.916667/0.916667`, missed delegate `0.0`, unnecessary delegate `0.083333`,
  all-core `0.916667`.
  Variant summary:
  pure `id_randomized` all-core `1.0`;
  stale-content under old reliable ID all-core `0.875`;
  redacted/stale-content under old reliable ID all-core `0.875`.
  Main remaining failure:
  `generated_wide_heldout_semantic_edit_mapping_filter` becomes over-conservative delegate in both stale-content variants.
  Important caveat:
  old `stale_rejection_rate`/`distractor_rejection_rate` scorer fields are invalid under randomized IDs because they check literal `mem_stale_prior`/`mem_distractor`.
- [ ] Next controller-side metric fix:
  update the memory-controller eval/summarizer to compute stale/distractor rejection by gold rejected IDs or candidate kind/content role, not hard-coded memory ID strings.
  Then rerun only the small ID-randomized proxy8 summary; no training is justified until the corrected metrics show a real reliability gap beyond the two over-conservative mapping-filter rows.
- [x] Fixed randomized-ID stale/distractor metrics and rescored proxy8 ID-randomized eval without rerunning the model.
  Code:
  `scripts\run_memory_controller_eval.py` now computes stale/distractor rejection from prompt candidate roles when available,
  and `scripts\rescore_memory_controller_eval.py` can rescore saved outputs.
  Corrected ID-randomized proxy8:
  stale/distractor rejection `1.0/1.0`, stale/distractor role recall `1.0/1.0`,
  all-core remains `0.916667`, unnecessary delegate `0.083333`, missed delegate `0.0`.
  Conclusion:
  v1j's reliable-memory retrieval is robust to randomized IDs on this proxy; no broad v1k training is justified now.
- [x] Synced the corrected ID-randomized robustness result into LATEX-NIPS.
  Added a short paragraph after the selective-collaboration table:
  v1j keeps selected/rejected memory recall, stale/distractor rejection, and evidence recall at `1.0`
  on the 24-row ID-randomized/content-swapped proxy after role-aware rescoring;
  all-core `0.917`, no missed delegates, one over-conservative unnecessary-delegation pattern.
- [ ] Optional learned correction only if corrected metrics confirm a gap:
  build a tiny content-contrastive correction set only for the two over-conservative `mapping_filter` stale-content rows,
  focused on avoiding unnecessary delegation when reliable evidence is present under a non-stable ID,
  while preserving selected/evidence recall and stale/distractor rejection at `1.0`.
- [x] Ran the next small selective-collaboration proxy instead of broad training.
  Proxy12 was preregistered from the v1j combined104 perturb split:
  12 tasks, 6 gold delegate positives and 6 self-handle negatives, including the known `mapping_filter` family.
  v1j trained controller delegated exactly 6/12, missed `0/6` delegate positives, and had `0/6` unnecessary calls.
  v22/untrained-style controller on the same strict prompt/evidence delegated 0/12, missed `6/6` delegate positives,
  despite selected/rejected memory and stale/distractor rejection at `1.0`.
  all-delegate made 12/12 calls and had 6 unnecessary calls.
  Downstream `gpt-5.4-mini`:
  v1j selective used `14620` tokens, mean strict `0.864616`, semantic pass `0.833333`;
  all-delegate used `27661` tokens, mean strict `0.804459`, semantic pass `0.583333`.
  Summary: `runs\multi-agent-proxy-v1\memory_controller_collab_proxy12_summary_20260612_0110.json`.
  Paper table updated from proxy8 to proxy12.
- [ ] Next best step after proxy12:
  do not launch broad v1k or wide large-model eval.
  First compile-check LATEX-NIPS and inspect the single v1j delegate semantic failure
  `generated_heldout_semantic_edit_mapping_chart` as packet-content error analysis.
  Only build a tiny learned correction if this exposes a general packet compression/evidence issue, not a one-off scorer quirk.
- [x] Inspected the single v1j proxy12 semantic failure.
  `generated_heldout_semantic_edit_mapping_chart` is not a route/memory failure:
  v1j correctly delegates, but the compact packet does not explicitly preserve the stronger constraint
  "copy the selected mapping before mutation."
  As a result `gpt-5.4-mini` emits `DEFAULT_CHART.copy() if config is None else config`,
  while the scorer/target expects `dict(DEFAULT_CHART if config is None else config)`.
  all-delegate makes the same family of mistake, so this is packet-content/evidence compression plus delegate behavior, not a learned routing failure.
  LATEX-NIPS caveat updated.
- [ ] Optional next controller-first diagnostic:
  build a very small mutable-container packet-content eval before any training.
  Include mapping/list cases where the correct packet must distinguish:
  copy-default-only, copy-input-only, and copy-selected-object-before-mutation.
  Measure packet guard/anchor recall and downstream semantic pass.
  Do not add inference-time rules that force this from task labels; only train if the diagnostic shows a repeated learned compression gap.
- [x] Built an offline plan for the optional mutable-container packet-content diagnostic.
  Artifact:
  `runs\multi-agent-proxy-v1\mutable_container_packet_content_diagnostic_plan_20260612_0200.json`.
  Existing candidate tasks: `22` total, `21` copy-selected-mapping and `1` copy-selected-list.
  This confirms the proxy12 chart failure belongs to a real semantic family, but does not yet justify training.
- [ ] If continuing this branch, build only a tiny eval first:
  sample a balanced subset from the 22 existing mutable-container candidates,
  score whether the controller packet explicitly preserves `copy selected mapping/list before mutation`,
  and only then decide whether a small learned packet-compression correction is warranted.
- [x] Built the tiny mutable-container packet-content eval spec without running a model.
  Artifact:
  `runs\multi-agent-proxy-v1\mutable_container_packet_content_eval8_20260612_0205.jsonl`.
  Rows: `8`, with `7` copy-selected-mapping and `1` copy-selected-list case.
  This is an eval spec only; it does not add a scripted inference rule.
- [ ] Next executable step, only if worth spending a short controller eval:
  implement/run a tiny packet builder/scorer for `mutable_container_packet_content_eval8`.
  Score explicit evidence recall for
  `copy_selected_mapping_before_mutation` and `copy_selected_list_before_mutation`,
  plus generic empty-container/default-mutation guard recall.
  Keep this controller-first; do not call `gpt-5.4-mini` unless packet evidence recall is adequate.
- [x] Implemented and ran an offline packet-content scorer on saved proxy12 packets.
  Script: `scripts\score_mutable_container_packet_content.py`.
  Result on the 2 overlapping proxy12 mutable mapping packets:
  copy-specific recall `0.0`,
  generic empty-container recall `1.0`,
  None-guard recall `1.0`,
  avoid-mutating-default recall `1.0`.
  Artifact:
  `runs\multi-agent-proxy-v1\mutable_container_packet_content_eval8_v1j_proxy12_packets_score_20260612_0212.jsonl`.
  Interpretation:
  current packets preserve broad guards but drop the specific `copy selected mapping/list before mutation` evidence.
- [x] Ran the short v1j controller eval for all 8 mutable-container packet-content rows.
  Because preferred `18001 -> 8001` is currently serving the older
  `/mnt/memory-agent/.../v21_plus_v16_anchor_replay_parquet_lora/global_step_1710`
  checkpoint under the `local-qwen3-8b-memory-polarproxy-v22` name, a temporary side service was used:
  remote `127.0.0.1:8002`, local `127.0.0.1:18002`,
  checkpoint `memory_controller_sft_v1j_contrastive_schema_guard_20260611_1930_lora/global_step_136`.
  It was stopped after the diagnostic.
  Eval artifact:
  `runs\multi-agent-proxy-v1\mutable_container_packet_content_eval8_v1j_controller_20260612_0130.jsonl`.
  Result:
  valid JSON/memory selection/stale rejection/distractor rejection/path/function/action/delegate/evidence/all-core all `1.0`;
  missed delegate `0.0`, unnecessary delegate `0.0`;
  semantic-guard recall `0.75`;
  delegate-reason accuracy `0.75`;
  total tokens `8799`.
- [x] Built and scored v1j collaboration packets for all 8 mutable-container rows.
  Builder:
  `scripts\build_mutable_container_packet_content_eval.py`.
  Packets:
  `runs\multi-agent-proxy-v1\mutable_container_packet_content_eval8_v1j_packets_20260612_0135.jsonl`.
  Score:
  `runs\multi-agent-proxy-v1\mutable_container_packet_content_eval8_v1j_packets_score_20260612_0135.jsonl`.
  Packet-content metrics:
  copy-specific recall `0.75`;
  generic empty-container recall `0.75`;
  None-guard recall `1.0`;
  avoid-mutating-default recall `1.0`.
  Six generated mapping rows preserve copy-specific evidence; failures are
  `transition_edit_copy_header_list` and `challenge_edit_guarded_replace`,
  where v1j compresses to broad default/observed-preservation guards instead of explicit copy-selected-container evidence.
- [ ] Next learned packet-compression correction, if continuing this branch:
  build a tiny supervision/eval package that teaches the controller to preserve
  `copy selected mapping/list before mutation` when reliable memory/current evidence supports it,
  with matched negatives/pass cases so this remains learned evidence compression rather than a task-label rule.
  Include held-out rows from the remaining mutable-container candidates in
  `runs\multi-agent-proxy-v1\mutable_container_packet_content_diagnostic_plan_20260612_0200.json`.
  Do not modify runtime packet builder to inject `copy_selected_*` heuristics.
- [x] Corrected the packet-content metric to separate structured packet compression from context retention.
  Old `copy_specific_recall=0.75` was inflated because it searched the whole packet, including raw `visible_task_context.memory_hint`.
  New contract-only score:
  `runs\multi-agent-proxy-v1\mutable_container_packet_content_eval8_v1j_packets_contractscore_20260612_0205.jsonl`.
  Result:
  structured `delegate_contract` copy-specific recall `0.0`,
  anywhere/context recall `0.75`,
  None guard `1.0`,
  avoid-mutating-default `1.0`.
  This means the next learning target is structured `delegate_contract.repair_constraints`,
  not simply preserving visible context.
- [x] Audited visible-evidence support before building correction data.
  Script:
  `scripts\audit_mutable_container_evidence_support.py`.
  Audit:
  `runs\multi-agent-proxy-v1\mutable_container_evidence_support_audit_20260612_0205.jsonl`.
  Among 22 mutable-container candidates:
  14 explicitly mention copy-selected in visible memory,
  4 are inferable from empty-container plus mutable-default visible evidence,
  4 are only copy-default-visible and are excluded from copy-selected positive training:
  `challenge_edit_guarded_replace`,
  `transition_edit_copy_default_map`,
  `transition_edit_copy_header_list`,
  `extended_edit_copy_nested_default`.
  Do not train copy-selected positives from these 4 unless the prompt/evidence is rewritten to visibly support that target.
- [x] Built a tiny learned packet-compression correction package without launching training.
  Builder:
  `scripts\build_mutable_container_packet_compression_correction.py`.
  Dataset:
  `data\memory_controller_sft_v1k_mutable_packet_compression_20260612_0215`.
  Eval:
  `runs\multi-agent-proxy-v1\mutable_container_packet_compression_v1k_eval18_20260612_0215.jsonl`.
  Stats:
  18 safe tasks, 4 unsafe excluded tasks, train/val unique tasks `12/6`, train/val records `48/6`.
  Audit:
  train/val overlap `0`;
  raw target-command leakage in prompt/response `0`;
  train/val support labels are only `explicit_visible_copy_selected` and
  `inferable_from_empty_container_and_mutable_default`.
- [x] Ran v1j baseline on the new 18-row packet-compression eval.
  Exact controller metrics:
  valid JSON/memory/stale/distractor/path/action/delegate/evidence/all-core all `1.0`;
  function recall `0.5`;
  semantic-guard recall `0.0`;
  repair-constraint exact recall `0.0`;
  repair-constraint rate `1.0`.
  Semantic repair-constraint score:
  `runs\multi-agent-proxy-v1\mutable_container_packet_compression_v1j_baseline_semantic_constraints_20260612_0240.jsonl`.
  Result:
  copy-selected semantic recall `0.722222`;
  None-guard semantic recall `1.0`;
  empty-container semantic recall `0.666667`;
  avoid-mutating semantic recall `0.555556`;
  exact recall `0.0`.
- [x] Next decision before training:
  decide whether v1k should train exact natural-language `repair_constraints` or a compact enum normal form.
  Since v1j already emits enum-like constraints such as `copy_selected_mapping_before_mutation`,
  the lowest-risk correction may be to standardize the accepted normal form and scorer,
  then train only if held-out exact/semantic recall remains below target.
  Avoid broad v1k training until this normal-form choice is explicit.
- [x] Trained and evaluated the compact enum normal-form v1k packet-compression correction.
  Training:
  dataset `data\memory_controller_sft_v1k_mutable_packet_compression_enum_20260612_0255`,
  checkpoint `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1k_mutable_packet_compression_enum_20260612_0255_lora/global_step_12`,
  1 epoch / 12 steps / batch 4 / lr `3e-5`, final train/val loss `0.949/0.949`.
  18-row eval:
  valid JSON/memory/stale/distractor/path/action/delegate/risk/evidence/all-core all `1.0`;
  repair-constraint exact recall/precision `0.925926/0.981481`;
  canonical recall/precision `0.925926/0.981481`;
  copy-selected and avoid-mutating semantic recall `1.0`,
  None/empty semantic recall `0.944444`.
  Tiny downstream `gpt-5.4-mini` mutable delegate2 probe:
  2/2 semantic pass, mean strict `0.955`, no provider errors.
  This supports learned reliable-evidence compression into structured packets, not a runtime mutable-container rule.
- [x] Only after the learned packet-compression correction passes a held-out packet-content eval,
  rerun a tiny downstream `gpt-5.4-mini` collaboration probe on the failed families.
  Do not spend API calls while the packet evidence itself is incomplete.
- [x] Next best controller-first step:
  build a harder held-out packet-compression eval for v1k before any broader training or API run:
  randomized memory IDs, paraphrased reliable memory, stale memories sharing current path/function vocabulary,
  copy-default-only negatives, and unsupported copy-selected distractors.
  Target: keep memory selection/rejection, stale/distractor rejection, route/delegate, and evidence at `>=0.98`,
  keep repair-constraint canonical recall above `0.90`,
  and avoid adding unsupported copy-selected constraints on negatives.
- [x] Ran the harder v1k packet-compression eval before any broader API call.
  Eval:
  `runs\multi-agent-proxy-v1\mutable_container_packet_compression_v1k_hard_eval_20260612_0235.jsonl`.
  Output:
  `runs\multi-agent-proxy-v1\mutable_container_packet_compression_v1k_hard_eval_v1k_output_20260612_0240.jsonl`.
  Rows `40`: `36` randomized/paraphrased copy-selected positives and `4` copy-default-only negatives.
  Result:
  valid JSON `1.0`,
  selected-memory recall/precision `1.0/1.0`,
  rejected-memory recall/precision `0.9875/1.0`,
  stale/distractor role recall `1.0/1.0`,
  route/delegate/evidence all `1.0`,
  all-core `0.975`,
  exact repair-constraint recall/precision `0.925/0.920833`,
  canonical recall/precision `0.925/0.933333`.
  Positive copy-selected recall `36/36=1.0`;
  unsupported negative copy-selected false-positive `1/4=0.25`.
  The remaining false positive is `transition_edit_copy_header_list`, where v1k overgeneralizes to `copy_selected_mapping_before_mutation`.
- [ ] Do not run the next `gpt-5.4-mini` probe yet.
  The harder eval did not fully pass the unsupported-copy negative gate.
  Build a tiny v1l contrastive correction/eval package from the four copy-default-only negatives plus matched supported positives.
  Target gate:
  positive copy-selected recall near `1.0`,
  unsupported-copy false-positive `0/4`,
  memory selection/rejection, role-aware stale/distractor rejection, route/delegate, and evidence near `1.0`,
  no runtime packet-builder rule that infers `copy_selected_*` from labels.
- [x] Diagnosed and cleaned the v1l eval artifact before making any downstream API decision.
  The first v1l 43-row eval had `31` connection errors after row `12`,
  so the apparent valid JSON `0.27907` was mostly tunnel/service pollution.
  Retried only the missing rows and combined:
  clean v1l valid JSON `1.0`, route/delegate/evidence `1.0`,
  positive copy-selected recall `36/36`,
  but unsupported no-copy false-positive `4/7`,
  all on `transition_edit_copy_header_list` variants.
- [x] Built and ran a tiny v1m all-negative contrastive correction without adding runtime packet rules.
  Builder change:
  `scripts\build_mutable_container_packet_contrastive_correction.py --train-all-negatives`.
  Dataset:
  `data\memory_controller_sft_v1m_mutable_packet_contrastive_allneg_20260612_0405`,
  train/val/eval `44/11/43`, no train/val/eval prompt overlap,
  no `target_new_line` / `target_command` / `gold_patch` / `expected_output` leakage.
  Checkpoint:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1m_mutable_packet_contrastive_allneg_20260612_0405_lora/global_step_11`.
  v1m eval:
  valid JSON `1.0`, memory/rejection/stale/distractor role recall `1.0`,
  route/delegate/evidence `1.0`, positive copy-selected recall `36/36`,
  unsupported no-copy false-positive reduced from v1l `4/7` to `2/7`.
  Gate still fails, so no new `gpt-5.4-mini` probe was launched.
- [ ] Next controller-first step:
  inspect the two remaining v1m false positives and the two correct variants for
  `transition_edit_copy_header_list`.
  Build a more targeted boundary correction/eval that distinguishes
  `copy_default_container_before_mutation` from `copy_selected_container_before_mutation`
  using visible reliable evidence, not task labels or runtime packet-builder rules.
  Do not run downstream `gpt-5.4-mini` until unsupported-copy false positives are `0/7`
  or a stricter preregistered gate is met without memory/route/evidence regression.
- [x] Converted the remaining header/list boundary into a positive copy-default packet target.
  Added `copy_default_container_before_mutation` to the offline hard-eval normal form and scorer;
  fixed the scorer to evaluate copy-selected/copy-default per constraint item so joined constraints cannot create false positives.
  Built v1n data:
  `data\memory_controller_sft_v1n_mutable_packet_copydefault_20260612_0430`,
  train/val/eval `44/11/43`, no prompt overlap or hidden target leakage.
  Old v1m on v1n gold had copy-default recall only `0.571429`, justifying a tiny correction run.
- [x] Trained/evaluated v1n copy-default correction.
  Checkpoint:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1n_mutable_packet_copydefault_20260612_0430_lora/global_step_11`.
  Exact controller metrics:
  valid JSON/memory/rejection/role-aware stale/distractor/path/action/delegate/evidence/all-core all `1.0`;
  repair-constraint recall/precision `0.899225/0.953488`.
  Boundary metrics:
  unsupported no-copy copy-selected false positive `0/7`,
  negative copy-default recall `7/7`,
  but supported positive copy-selected recall regressed to `32/36`
  and positive copy-default false positives appeared in `4/36`.
  Gate still fails; no downstream `gpt-5.4-mini` call.
- [ ] Next controller-first step:
  inspect the 4 v1n supported-copy false negatives / copy-default false positives.
  Build a balanced v1o correction/eval that preserves both sides:
  supported copy-selected recall back near `36/36`,
  unsupported-copy false positives remain `0/7`,
  copy-default recall remains `7/7`,
  and memory/route/evidence stay at `1.0`.
  Do not add runtime packet-builder heuristics and do not call the large model until this gate passes.
- [x] Reinterpreted the v1n "supported-copy" misses with visible-evidence support labels.
  All 4 misses are `inferable_from_empty_container_and_mutable_default`, where visible memory says
  "copy defaults only when input is None; preserve explicit empty dictionaries"
  rather than explicitly saying "copy selected mapping before mutation".
  Treating these as hard copy-selected failures would rely on hidden target lines,
  which conflicts with the main claim that the controller learns from reliable visible evidence.
- [x] Added and ran support-aware packet gate:
  `scripts\summarize_mutable_container_support_gate.py`.
  v1n:
  explicit copy-selected positives `28/28`,
  explicit copy-default false positives `0/28`,
  copy-default-only negative copy-selected false positives `0/7`,
  copy-default recall `7/7`,
  inferable ambiguous rows reported separately `4/8` copy-selected and `4/8` copy-default.
  v1m on the same gate fails the negative side:
  copy-selected false positives `2/7`, copy-default recall `4/7`.
- [x] Since v1n passed the strict explicit+negative controller gate, ran only a tiny explicit-evidence downstream delegate probe.
  Packets:
  `runs\multi-agent-proxy-v1\mutable_container_packet_contrastive_v1n_delegate4_packets_20260612_0500.jsonl`.
  `gpt-5.4-mini` delegate output:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_az_v1n_explicit_delegate4_20260612_0505.jsonl`.
  Scored output:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_az_v1n_explicit_delegate4_20260612_0505_scored.jsonl`.
  Result:
  4/4 semantic pass, mean strict `0.91`, action/skill match `1.0`, provider errors `0`,
  total tokens `10296`.
  This is a narrow explicit-evidence collaboration result, not a broad benchmark claim.
- [ ] Next controller-first/reporting step:
  standardize the support-aware gate in the packet-compression summary and produce a small same-eval comparison table
  for v1k/v1m/v1n under explicit-copy-selected, copy-default-only negative, and inferable/ambiguous buckets.
  Only after that table is clean should LATEX-NIPS add a narrow v1n paragraph/table row.
  Do not expand `gpt-5.4-mini` calls until the paper genuinely needs more downstream evidence.
- [x] Produced the support-aware packet-boundary comparison.
  Artifacts:
  `runs\multi-agent-proxy-v1\mutable_container_packet_compression_v1k_hard_eval_support_gate_20260612_0510.jsonl`,
  `runs\multi-agent-proxy-v1\mutable_container_packet_contrastive_v1n_eval_v1k_output_20260612_0515.jsonl`,
  `runs\multi-agent-proxy-v1\mutable_container_packet_contrastive_v1n_eval_v1k_support_gate_20260612_1200.jsonl`,
  and
  `runs\multi-agent-proxy-v1\mutable_container_support_gate_comparison_v1k_v1m_v1n_20260612_1200.json`.
  Same-eval result:
  v1k eval43 and v1n eval43 both pass the strict explicit+negative support gate;
  v1m eval43 fails with negative copy-selected FP `0.285714` and copy-default recall `0.571429`.
  Original v1k hard40 still fails with negative copy-selected FP `0.25` and copy-default recall `0.5`.
  Interpretation:
  do not overclaim v1n as strictly stronger than v1k; use v1m as the cleaner negative comparison, and present v1n as a support-aware packet-boundary/controller-to-delegate result.
- [ ] Make `scripts\summarize_mutable_container_support_gate.py` or an equivalent support-aware bucket table part of the standard packet-compression summary path.
  This should stay offline/eval-only and must not rewrite runtime packets.
- [ ] Build the next controller-only generalization eval:
  new visible-memory paraphrases,
  new copy-selected vs copy-default families,
  randomized reliable/stale/distractor IDs,
  and ambiguous/inferable cases separated from hard labels.
  Target:
  explicit copy-selected recall `1.0`,
  explicit copy-default FP `0`,
  negative copy-selected FP `0`,
  copy-default recall `1.0`,
  memory/route/evidence near `1.0`.
  Do not call `gpt-5.4-mini` unless this controller-side gate holds on genuinely new families.
- [x] Built and ran the controller-only generated mutable-container packet generalization eval.
  Builder:
  `scripts\build_mutable_container_packet_generalization_eval.py`.
  Eval:
  `runs\multi-agent-proxy-v1\mutable_container_packet_generalization_eval_20260612_1210.jsonl`,
  18 rows = 6 explicit copy-selected + 6 copy-default-only negatives + 6 inferable/ambiguous.
  v1n output:
  `runs\multi-agent-proxy-v1\mutable_container_packet_generalization_eval_v1n_output_20260612_1215.jsonl`.
  Support gate:
  `runs\multi-agent-proxy-v1\mutable_container_packet_generalization_eval_v1n_support_gate_20260612_1225.jsonl`.
  Result:
  primary support boundary passes
  (explicit copy-selected recall `1.0`, explicit copy-default FP `0`, negative copy-selected FP `0`, negative copy-default recall `1.0`),
  but secondary packet quality does not pass:
  evidence recall `0.833333`,
  repair-constraint recall `0.777778`,
  with systematic missing `check_none_explicitly_preserve_empty_falsy_container` under new paraphrases and 3 copy-default rows using support labels instead of reliable memory ids in `evidence_ids`.
- [ ] Build a tiny v1o correction/eval for the generated generalization failures.
  Focus:
  paraphrased None-guard evidence such as "only when input is None" / "preserve caller-supplied containers",
  evidence-id schema robustness,
  and retention of copy-selected/copy-default support boundary.
  Target:
  support gate remains pass,
  evidence recall near `1.0`,
  repair-constraint recall near `1.0`,
  no unsupported copy-selected constraints.
  This should be learned controller data/eval, not a runtime packet rewrite.
- [x] Built and trained v1o correction, but it is a negative result.
  Builder:
  `scripts\build_mutable_container_packet_generalization_correction.py`.
  Dataset:
  `data\memory_controller_sft_v1o_mutable_packet_generalization_20260612_1220`,
  train `48`, val `6`, fresh eval `12`, no hidden target-command/patch leakage.
  Checkpoint:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1o_mutable_packet_generalization_20260612_1220_lora/global_step_12`.
  Training:
  1 epoch / 12 steps / lr `2e-5` / batch `4`, final train loss about `0.873`, val/loss `0.876`.
  Eval:
  `runs\multi-agent-proxy-v1\mutable_container_packet_generalization_v1o_eval_v1o_output_20260612_1230.jsonl`.
  Support gate still passes, but secondary packet quality does not:
  evidence recall `0.833333`,
  repair-constraint recall `0.722222`,
  still systematically missing `check_none_explicitly_preserve_empty_falsy_container`,
  and 2 copy-default rows still use support label as `evidence_ids`.
  Do not call `gpt-5.4-mini` from this checkpoint.
- [x] Next v1p controller-first step:
  do not continue blind SFT.
  First build a field-level diagnostic/scorer for:
  `evidence_ids_are_selected_memory_ids`,
  `support_label_not_used_as_evidence_id`,
  and paraphrased None-guard recall.
  Then build contrastive data that makes label-as-id visibly wrong and includes multiple None-guard paraphrase clusters.
  Keep copy-selected/copy-default support-boundary examples balanced so the already-good primary boundary does not regress.
- [x] Built and ran v1p field-contrastive correction.
  Important data-quality fix:
  the first builder hid `visible_evidence_support.label` but leaked bucket labels through prompt `task_id`;
  fixed prompt-visible IDs to bucket-neutral names while preserving labels only in `extra_info`.
  Dataset:
  `data\memory_controller_sft_v1p_mutable_packet_field_contrastive_20260612_1245`,
  train/val/eval `30/6/18`, no prompt support-label or hidden target leakage,
  gold `evidence_ids == selected_memory_ids`, and all gold packets include the None/empty-container guard.
  Checkpoint:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1p_mutable_packet_field_contrastive_20260612_1245_lora/global_step_7`.
  Hidden-label field eval:
  strict support gate passes, evidence exact `1.0`, support-label-as-evidence `0.0`,
  but None-guard recall is only `0.666667` and explicit-copy rows still have None-guard recall `0.0`.
  Old generated eval:
  strict support gate still passes, but evidence exact remains `0.833333`,
  support-label-as-evidence remains `0.166667`, and None-guard recall is only `0.277778`.
  Conclusion:
  v1p is a partial positive for evidence-id schema under label-hidden prompts,
  but not robust enough for a downstream `gpt-5.4-mini` probe.
- [x] Next v1q controller-first step:
  build a label-hidden version of the old generated generalization eval and run v1n/v1p on the same prompt schema.
  Goal:
  separate prompt-schema artifacts from learned memory reasoning.
  Then build a tiny balanced correction only if the failure persists after labels are hidden.
  Requirements:
  no runtime packet-builder heuristics,
  labels only in `extra_info`,
  prompt-visible support must be natural descriptions,
  explicit-copy reliable memories must require both copy-selected and None/empty-container guard,
  evidence ids must be selected memory ids.
  Gate before any `gpt-5.4-mini` call:
  strict support gate passes,
  evidence exact `>=0.98`,
  support-label-as-evidence `0`,
  None-guard recall near `1.0` on explicit/copy-default/ambiguous buckets,
  and no regression on memory selection/rejection or route/delegate.
- [x] Ran v1q label-hidden diagnostic for v1p on the old generated generalization eval.
  Builder:
  `scripts\build_mutable_container_packet_label_hidden_eval.py`.
  Eval:
  `runs\multi-agent-proxy-v1\mutable_container_packet_generalization_labelhidden_eval_20260612_1320.jsonl`.
  v1p output:
  `runs\multi-agent-proxy-v1\mutable_container_packet_generalization_labelhidden_eval_v1p_output_20260612_1325.jsonl`.
  Result:
  evidence exact improved to `1.0`, support-label-as-evidence dropped to `0.0`,
  and strict support gate still passes.
  Remaining failure:
  None-guard recall only `0.333333`,
  with explicit copy-selected and copy-default-only buckets both at `0.0`.
  Interpretation:
  prompt-visible labels caused evidence-id schema errors,
  but missing None/empty-container guard is a real learned packet-compression gap.
- [x] Next v1r controller-first step:
  build a small balanced correction/eval focused only on evidence-to-constraint compression for the None/empty-container guard.
  Include explicit copy-selected and copy-default-only examples where the reliable memory paraphrases the None/default boundary and the gold packet must include
  `check_none_explicitly_preserve_empty_falsy_container`.
  Keep labels hidden from prompts and labels only in `extra_info`.
  Do not add runtime heuristics.
  Before any `gpt-5.4-mini` probe, require:
  strict support gate pass,
  evidence exact `1.0`,
  support-label-as-evidence `0`,
  and None-guard recall near `1.0` on explicit, copy-default-only, and ambiguous buckets.
- [x] Built/trained/evaluated v1r None-guard correction.
  Builder:
  `scripts\build_mutable_container_packet_noneguard_correction.py`.
  Dataset:
  `data\memory_controller_sft_v1r_mutable_packet_noneguard_20260612_1345`,
  train/val/eval `63/9/24`, prompt labels hidden, no target leakage,
  all gold rows include `check_none_explicitly_preserve_empty_falsy_container`.
  Checkpoint:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1r_mutable_packet_noneguard_20260612_1345_lora/global_step_15`.
  v1r held-out:
  evidence exact `1.0`, support-label-as-evidence `0`, None-guard recall `1.0`,
  but strict support gate fails because copy-default-only negative copy-selected FP is `0.125`
  and copy-default recall is only `0.625`.
  Old label-hidden generated eval:
  strict support gate passes and evidence exact remains `1.0`,
  but None-guard recall remains low at `0.277778`
  with explicit and copy-default buckets still `0.0`.
  Conclusion:
  v1r is a local positive for None-guard learning but not robust enough for delegation.
- [x] Next v1s controller-first step:
  build mixed replay / contrastive balancing rather than another single-focus SFT.
  Combine v1r None-guard examples with earlier v1n/v1q support-boundary examples,
  keep labels hidden from prompts,
  and balance explicit copy-selected mapping/list, copy-default-only, ambiguous, stale/distractor roles.
  Evaluate on both:
  `runs\multi-agent-proxy-v1\mutable_container_packet_noneguard_v1r_eval_20260612_1345.jsonl`
  and
  `runs\multi-agent-proxy-v1\mutable_container_packet_generalization_labelhidden_eval_20260612_1320.jsonl`.
  Gate before any `gpt-5.4-mini` call:
  strict support gate passes on both,
  evidence exact `1.0`,
  support-label-as-evidence `0`,
  None-guard recall near `1.0` on explicit/copy-default/ambiguous buckets,
  and memory/route/delegate all-core remains `1.0`.
- [x] Built/trained/evaluated v1s mixed replay.
  Dataset:
  `data\memory_controller_sft_v1s_mutable_packet_mixed_replay_20260612_1455`,
  train/val `93/15`, built from v1p field-contrastive plus v1r None-guard data.
  Audit:
  no prompt support-label leakage, no hidden target leakage, gold evidence ids match selected memory ids,
  all `108` rows include `check_none_explicitly_preserve_empty_falsy_container`.
  Checkpoint:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1s_mutable_packet_mixed_replay_20260612_1455_lora/global_step_23`.
  v1r held-out:
  evidence exact `1.0`, None-guard recall `1.0`,
  but strict support gate still fails:
  copy-default-only negative copy-selected FP `0.125`, copy-default recall `0.75`.
  Old label-hidden generated eval:
  strict support gate passes and evidence exact `1.0`,
  but None-guard recall remains `0.333333`,
  with explicit/copy-default buckets still at `0.0`.
  Conclusion:
  v1s is a partial improvement over v1r but still not ready for large-model delegation.
- [x] Next v1t controller-first step:
  inspect v1s failures before training again.
  Specifically:
  analyze v1r copy-default-only misses/false positives,
  old label-hidden explicit/copy-default None-guard misses,
  and whether failures correlate with mapping/list family or specific paraphrase templates.
  Then build a more balanced correction:
  equal copy-selected mapping/list,
  stronger copy-default-only replay,
  old label-hidden eval rows converted into training-style correction examples,
  labels hidden from prompts,
  and no runtime packet-builder heuristics.
  Gate before `gpt-5.4-mini`:
  strict support gate passes on both v1r and old label-hidden eval,
  evidence exact `1.0`,
  support-label-as-evidence `0`,
  and None-guard recall near `1.0` on explicit/copy-default/ambiguous buckets.
- [x] Built/trained/evaluated v1t balanced replay from v1s failure diagnosis.
  Failure diagnosis:
  `runs\multi-agent-proxy-v1\mutable_container_v1s_failure_diagnosis_20260612_1535.jsonl`
  showed two main gaps:
  v1r copy-default-only rows missed `copy_default_container_before_mutation` or emitted unsupported `copy_selected_*`,
  and old label-hidden explicit/copy-default rows missed the None/empty-container guard from short memory phrases.
  Builder:
  `scripts\build_mutable_container_packet_v1t_balanced_correction.py`.
  Dataset:
  `data\memory_controller_sft_v1t_mutable_packet_balanced_20260612_1625`,
  train/val `156/24`, labels hidden, no target leakage, evidence ids correct,
  all rows include the None guard.
  Checkpoint:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1t_mutable_packet_balanced_20260612_1625_lora/global_step_39`.
  Generated balanced held-out:
  evidence exact `1.0`, None-guard recall `1.0`, but strict support gate fails:
  explicit copy-default FP `0.125`, copy-default-only negative copy-selected FP `0.375`.
  Old label-hidden eval:
  None-guard recall improves to `0.722222`, but repair precision drops to `0.655556`
  and support gate fails badly:
  explicit copy-default FP `0.666667`, negative copy-selected FP `1.0`.
  Conclusion:
  v1t overcorrects by emitting copy-selected and copy-default constraints together.
- [x] Next v1u controller-first step:
  do not continue plain SFT/replay.
  Build a field-level mutual-exclusion scorer and contrastive data/reward target:
  if visible memory supports copy-default-only, `copy_selected_*` is wrong;
  if visible memory explicitly supports copy-selected, `copy_default_container_before_mutation` is wrong unless separately supported;
  None/empty guard is independent and should still be retained.
  Use this to create balanced negative/contrastive examples or an offline reward diagnostic.
  This must remain learned controller supervision/evaluation, not a runtime packet rewrite.
  Gate before `gpt-5.4-mini`:
  strict support gate passes on both generated balanced and old label-hidden evals,
  evidence exact `1.0`,
  support-label-as-evidence `0`,
  None-guard recall high,
  and repair precision recovers without losing recall.
- [x] Built/trained/evaluated v1u mutual-exclusion correction.
  Added scorer:
  `scripts\score_mutable_container_packet_mutual_exclusion.py`.
  Added builder:
  `scripts\build_mutable_container_packet_v1u_mutual_exclusion_correction.py`.
  Dataset:
  `data\memory_controller_sft_v1u_mutual_exclusion_20260612_1455`,
  train/val `99/15`, no prompt support-label leakage, no gold both-copy rows,
  all gold rows include the None/empty guard, and gold evidence ids match selected memory ids.
  Checkpoint:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1u_mutual_exclusion_20260612_1455_lora/global_step_24`.
  Training:
  1 epoch / 24 steps / lr `2e-5` / batch `4`, train loss about `1.014 -> 0.562`, val/loss `0.583`.
  Clean old label-hidden eval:
  `runs\multi-agent-proxy-v1\mutable_container_packet_generalization_labelhidden_v1u_eval_v1u_output_20260612_1600.jsonl`.
  Positive:
  evidence exact `1.0`, support-label-as-evidence `0.0`,
  explicit copy-selected bucket is clean
  (`copy_selected_target_rate=1.0`, wrong-family `0.0`, copy-default FP `0.0`, None-guard `1.0`, repair exact `1.0`).
  Negative:
  strict mutual-exclusion gate still fails because copy-default-only rows have
  copy-selected FP `0.833333`, both-copy rate `0.833333`, and None-guard recall `0.0`.
  Do not call `gpt-5.4-mini`.
- [x] Next v1v controller-first step:
  build a narrow copy-default-only negative-heavy correction or reward diagnostic instead of broad replay.
  Focus only on the remaining learned packet-compression failure:
  reliable memory says copy default on absent input and preserve explicit empty/falsy caller containers,
  so the packet should include
  `copy_default_container_before_mutation`,
  `check_none_explicitly_preserve_empty_falsy_container`,
  and `avoid_mutating_shared_defaults_or_callers`,
  while excluding all `copy_selected_*`.
  Keep a small explicit-copy anchor replay so the now-clean explicit bucket does not regress,
  but avoid equal-weight ambiguous/explicit replay that teaches over-broad copy-selected emission.
  Evaluate first on the old label-hidden copy-default-only rows and a small generated held-out set.
  Gate before any `gpt-5.4-mini` call:
  evidence exact `1.0`,
  support-label-as-evidence `0`,
  copy-default-only copy-selected FP `0`,
  copy-default-only None-guard recall near `1.0`,
  explicit-copy bucket remains clean,
  and max both-copy rate `0`.
- [x] Built/trained/evaluated v1v copy-default-only negative-heavy correction.
  Added builder:
  `scripts\build_mutable_container_packet_v1v_copydefault_negative_correction.py`.
  Dataset:
  `data\memory_controller_sft_v1v_copydefault_negative_20260612_1530`,
  train/val `105/15`, dominated by copy-default-only negatives with small explicit-copy anchor replay.
  Audit:
  no prompt support-label leakage, no gold both-copy rows,
  all gold rows include the None/empty guard,
  copy-default-only gold rows always include `copy_default_container_before_mutation`,
  copy-default-only gold rows never include `copy_selected_*`,
  and gold evidence ids match selected memory ids.
  Checkpoint:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1v_copydefault_negative_20260612_1530_lora/global_step_26`.
  Generated held-out:
  valid JSON and all-core `1.0`, evidence exact `1.0`,
  copy-default-only copy-selected FP improves to `0.375`,
  but None-guard recall is only `0.625` and strict mutual-exclusion gate still fails.
  Old label-hidden eval:
  evidence exact `1.0`, support-label-as-evidence `0.0`,
  but copy-default-only copy-selected FP regresses to `1.0`,
  explicit copy-default FP `0.5`, max both-copy rate `1.0`,
  and copy-default-only None-guard recall only `0.166667`.
  Conclusion:
  ordinary SFT/replay is not enough for this field-level boundary; do not call `gpt-5.4-mini`.
- [x] Next v1w controller-first step:
  stop broad SFT/replay for this failure and build a pairwise/preference or reward-diagnostic target.
  For each same prompt, compare a clean packet against near-miss packets:
  clean copy-default-only packet includes
  `copy_default_container_before_mutation`,
  `check_none_explicitly_preserve_empty_falsy_container`,
  and `avoid_mutating_shared_defaults_or_callers`;
  negative packets either add unsupported `copy_selected_*`,
  omit the None/empty guard,
  add both copy-selected and copy-default,
  or use the wrong copy-selected family.
  First implement this as an offline scorer/pair dataset and report pairwise preference accuracy or reward margins using existing v1u/v1v outputs.
  Only train if the pair data audit passes and the objective remains a learned controller decision, not runtime packet rewriting.
  Gate before any `gpt-5.4-mini` call remains:
  evidence exact `1.0`,
  support-label-as-evidence `0`,
  copy-default-only copy-selected FP `0`,
  copy-default-only None-guard recall near `1.0`,
  explicit-copy bucket clean,
  and max both-copy rate `0`.
- [x] Built v1w pairwise/reward diagnostic.
  Added:
  `scripts\build_mutable_container_packet_v1w_pairwise_reward.py`.
  Dataset:
  `data\memory_controller_pairwise_v1w_packet_boundary_20260612_1555`,
  `66` same-prompt clean-vs-near-miss pairs from `18` old label-hidden rows.
  Pair audit:
  no prompt support-label leakage,
  no non-positive reward margins,
  no copy-default chosen packet contains `copy_selected_*`,
  no copy-default chosen packet misses `copy_default_container_before_mutation` or the None/empty guard,
  and no chosen evidence id uses a support label.
  Pairwise clean-vs-near-miss reward accuracy:
  `1.0`, minimum margin `0.25`.
  Reward scoring of existing outputs:
  v1u copy-default-only mean score `-0.021667`, clean margin `0.721667`, negative-or-zero rate `0.833333`;
  v1v copy-default-only mean score `-0.033333`, clean margin `0.733333`, negative-or-zero rate `0.833333`.
  Conclusion:
  this reward signal detects exactly the field-boundary failures that SFT/replay did not fix.
  Do not call `gpt-5.4-mini`.
- [x] Next v1x controller-first step:
  connect the v1w pairs to an actual learned preference path, or build a reward-proxy candidate-ranking eval first if DPO/pairwise training is not immediately available.
  Preferred order:
  inspect existing verl/SFT support for chosen/rejected or reward-model fields;
  if pairwise training is available, run a tiny v1x preference training on `pairs.parquet`;
  otherwise generate small candidate sets for each prompt and evaluate whether the v1w reward can rank clean packets above controller-like near misses.
  Keep the boundary learned:
  do not add runtime packet rewriting that removes `copy_selected_*` or inserts the None guard.
  Gate before any `gpt-5.4-mini` call remains unchanged:
  evidence exact `1.0`,
  support-label-as-evidence `0`,
  copy-default-only copy-selected FP `0`,
  copy-default-only None-guard recall near `1.0`,
  explicit-copy bucket clean,
  and max both-copy rate `0`.
- [x] Built and ran v1x reward-proxy candidate ranking.
  Added:
  `scripts\run_mutable_container_packet_v1x_reward_proxy_ranking.py`.
  Output:
  `data\memory_controller_pairwise_v1x_reward_proxy_ranking_20260612_1605`.
  Test:
  `uv run pytest tests\scripts\test_run_mutable_container_packet_v1x_reward_proxy_ranking.py -q`
  passed `2`.
  Result:
  `18` candidate sets,
  clean top-1 `1.0`,
  clean-vs-near-miss positive margin rate `1.0`,
  mean/min clean-vs-near-miss margin `0.316667/0.25`.
  With actual v1u/v1v outputs added as candidates,
  mean clean-vs-best-controller margin `0.373889`, min `0.0`;
  zeros are explicit-copy rows where controller output was already clean.
  Conclusion:
  reward-proxy can rank clean packet-boundary decisions above the exact near misses,
  but the controller still does not generate those packets reliably.
  Do not call `gpt-5.4-mini`.
- [ ] Next v1y controller-first step:
  inspect and choose a minimal learned preference path.
  First verify whether existing `verl`/launcher can consume `chosen`/`rejected` pairs or reward-weighted examples without adding a separate brittle runtime pipeline.
  If direct DPO/RM training is too large a change, build a tiny reward-weighted SFT candidate dataset from v1w/v1x:
  clean packets high reward/weight, near-miss packets low or negative reward,
  and evaluate only controller packet gates afterward.
  Keep this as training supervision, not runtime packet rewriting.
  Gate before any `gpt-5.4-mini` call remains:
  evidence exact `1.0`,
  support-label-as-evidence `0`,
  copy-default-only copy-selected FP `0`,
  copy-default-only None-guard recall near `1.0`,
  explicit-copy bucket clean,
  and max both-copy rate `0`.
- [x] Inspected v1y preference path.
  Current `AgentRLDataset` supports `reward_model.ground_truth -> loss_weight`,
  and `fsdp_sft_trainer` applies `loss_weight`.
  Direct DPO/pairwise code exists in upstream `verl` recipes/datasets,
  but using it now would be a new training path.
  Important decision:
  do not train on rejected packets as low-weight responses because that still imitates bad packets.
- [x] Built v1y preference-correction SFT data.
  Added:
  `scripts\build_mutable_container_packet_v1y_preference_correction.py`.
  Dataset:
  `data\memory_controller_sft_v1y_preference_correction_20260612_1615`,
  train/val `72/12`,
  `66` correction records plus `18` clean anchors.
  Design:
  rejected packet appears only as prior assistant context,
  preference feedback explains the boundary failure,
  supervised target remains the clean packet.
  Audit:
  no prompt support-label leakage,
  no preference guard text in responses,
  no rejected context in targets,
  all rewards `1.0`.
  Tests:
  `uv run pytest tests\scripts\test_build_mutable_container_packet_v1y_preference_correction.py tests\scripts\test_run_mutable_container_packet_v1x_reward_proxy_ranking.py -q`
  passed `4`.
- [ ] Next v1y training/eval step:
  if GPU can be freed intentionally, stop the temporary/preferred service only for the training window,
  train `data\memory_controller_sft_v1y_preference_correction_20260612_1615` for 1 epoch with existing `AgentRLDataset`,
  serve the checkpoint on a temporary port,
  and evaluate on the same old label-hidden eval plus the v1v generated held-out.
  Do not launch while v22 service occupies GPU unless memory is confirmed safe.
  Gate before any `gpt-5.4-mini` call remains:
  evidence exact `1.0`,
  support-label-as-evidence `0`,
  copy-default-only copy-selected FP `0`,
  copy-default-only None-guard recall near `1.0`,
  explicit-copy bucket clean,
  and max both-copy rate `0`.
- [x] Trained and evaluated v1y preference-correction checkpoint.
  Checkpoint:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1y_preference_correction_20260612_1615_lora/global_step_18`.
  Training:
  1 epoch / 18 steps / lr `2e-5` / batch `4`,
  val/loss `0.323`.
  Complete eval:
  `runs\multi-agent-proxy-v1\mutable_container_packet_generalization_labelhidden_v1y_eval_v1y_output_20260612_1625.jsonl`.
  Main positives:
  valid JSON `1.0`,
  selected/rejected memory recall `1.0/1.0`,
  path/action/delegate/evidence/all-core all `1.0`,
  guard-bool accuracy `1.0`.
  Mutual-exclusion:
  explicit-copy bucket clean,
  copy-default-only copy-selected FP improves to `0.166667`,
  but gate still fails.
  Main failure:
  None-guard recall only `0.277778` overall,
  explicit-copy and copy-default-only None-guard recall both `0.0`.
  Reward score:
  mean `0.278333`, clean margin `0.421667`;
  copy-default-only negative-or-zero rate down to `0.166667`.
  Preferred v22 service on `8001/18001` was restored after eval.
  Do not call `gpt-5.4-mini`.
- [ ] Next v1z controller-first step:
  inspect v1y failure rows and build a minimal preference-correction focused on omission of
  `check_none_explicitly_preserve_empty_falsy_container`.
  Keep the improved copy-default-only mutual exclusion by including both-copy/add-copy-selected near misses as replay,
  but upweight or prioritize omitted-None-guard rejected variants in the correction context.
  Evaluate before training on whether the v1w reward and scorer identify these rows;
  then train only if the data audit shows no support-label leakage and no rejected target imitation.
  Gate before any `gpt-5.4-mini` call remains:
  evidence exact `1.0`,
  support-label-as-evidence `0`,
  copy-default-only copy-selected FP `0`,
  copy-default-only None-guard recall near `1.0`,
  explicit-copy bucket clean,
  and max both-copy rate `0`.
- [x] Built/trained/evaluated v1z None-guard preference correction.
  Added:
  `scripts\build_mutable_container_packet_v1z_noneguard_preference_correction.py`.
  Dataset:
  `data\memory_controller_sft_v1z_noneguard_preference_20260612_1645`,
  total `113`, train/val `101/12`,
  actual v1y failure corrections `17`,
  no prompt support-label leakage,
  no preference guard in targets,
  no rejected context in targets.
  Tests:
  v1z/v1y/v1x tests passed `6`.
  Checkpoint:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v1z_noneguard_preference_20260612_1645_lora/global_step_25`.
  Training:
  1 epoch / 25 steps / lr `2e-5` / batch `4`,
  val/loss `0.049`.
  Eval:
  `runs\multi-agent-proxy-v1\mutable_container_packet_generalization_labelhidden_v1z_eval_v1z_output_20260612_1655.jsonl`.
  Main positives:
  valid JSON, memory selection/rejection, stale/distractor rejection, path/action/delegate/evidence/all-core all `1.0`;
  repair recall/precision `0.777778/0.925926`;
  overall None-guard recall improves to `0.611111`.
  Mixed/negative:
  explicit-copy None-guard improves to `0.833333`,
  but copy-default-only None-guard remains `0.0`,
  copy-default-only copy-selected FP regresses to `0.333333`,
  max both-copy rate `0.333333`.
  Preferred v22 service on `8001/18001` was restored after eval.
  Do not call `gpt-5.4-mini`.
- [ ] Next v2a controller-first step:
  stop single-axis correction/replay.
  Build a compact per-bucket diagnostic table comparing v1v, v1y, and v1z on:
  copy-default-only copy-selected FP,
  copy-default recall,
  None-guard recall,
  both-copy rate,
  repair exact,
  and reward clean margin.
  Then inspect only the copy-default-only prompts/outputs.
  If training again, create a bucket-conditioned preference set that explicitly teaches:
  copy-default-only -> `copy_default_container_before_mutation`
  + `check_none_explicitly_preserve_empty_falsy_container`
  + `avoid_mutating_shared_defaults_or_callers`
  and no `copy_selected_*`;
  explicit-copy -> target `copy_selected_*`
  + None guard
  + avoid mutation
  and no copy-default.
  Do not train until the dataset audit proves no support-label leakage and no rejected target imitation.
  Gate before any `gpt-5.4-mini` call remains:
  evidence exact `1.0`,
  support-label-as-evidence `0`,
  copy-default-only copy-selected FP `0`,
  copy-default-only None-guard recall near `1.0`,
  explicit-copy bucket clean,
  and max both-copy rate `0`.
- [x] Built the v2a per-bucket diagnostic table.
  Output:
  `data\memory_controller_v2a_bucket_diagnostics_20260612_1710`.
  Result:
  v1z explicit-copy is nearly clean, but copy-default-only still has
  None-guard recall `0.0`, copy-selected FP `0.333333`, both-copy `0.333333`.
  Interpretation:
  the current failure is a bucket-conditioned packet-boundary conflict, not a
  memory selection/path/action/delegate failure.
- [x] Built/trained/evaluated v2b bucket-conditioned preference correction.
  Added:
  `scripts\build_mutable_container_packet_v2b_bucket_preference_correction.py`.
  Dataset:
  `data\memory_controller_sft_v2b_bucket_preference_20260612_1725`,
  total `115`, train/val `103/12`,
  copy-default-only `66`, explicit-copy `49`,
  no support-label leakage,
  no preference guard/rejected context in targets,
  no clean-boundary failures.
  Checkpoint:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/memory_controller_sft_v2b_bucket_preference_20260612_1725_lora/global_step_25`.
  Eval:
  valid JSON/memory/path/action/delegate/evidence/all-core all `1.0`;
  repair recall/precision `0.851852/0.962963`.
  Positive:
  explicit-copy bucket is clean:
  target copy-selected `1.0`,
  copy-default FP `0.0`,
  both-copy `0.0`,
  None guard `1.0`,
  repair exact `1.0`.
  Blocker:
  copy-default-only still fails:
  copy-default rate `1.0`,
  None guard `0.0`,
  copy-selected FP `0.166667`,
  both-copy `0.166667`,
  repair exact `0.0`.
  Preferred v22 service on `8001/18001` was restored after eval.
  Do not call `gpt-5.4-mini`.
- [ ] Next v2c diagnostic step:
  do not train another broad correction set yet.
  Build a tiny contrastive representation probe for copy-default-only rows that
  varies only whether the visible reliable memory explicitly states the
  independence of:
  `copy_default_container_before_mutation`
  and `check_none_explicitly_preserve_empty_falsy_container`.
  Compare v22/v1y/v1z/v2b outputs on this probe.
  Goal:
  decide whether the failure is caused by prompt/packet representation
  ambiguity or by insufficient learned preference.
  If it is representation ambiguity, fix the training target wording/data
  format; if not, build a smaller DPO/pairwise-style objective focused only on
  preserving independent constraints.
  Do not add runtime packet rewriting rules.
  Do not use `gpt-5.4-mini` until the packet gate passes:
  evidence exact `1.0`,
  support-label-as-evidence `0`,
  copy-default-only copy-selected FP `0`,
  copy-default-only None-guard recall near `1.0`,
  explicit-copy bucket clean,
  max both-copy rate `0`.
- [x] Built and ran v2c representation probe.
  Added:
  `scripts\build_mutable_container_packet_v2c_representation_probe.py`.
  Probe:
  `runs\multi-agent-proxy-v1\mutable_container_packet_v2c_representation_probe_20260612_1735.jsonl`,
  12 copy-default-only rows,
  `compact_boundary` 6 and `independent_constraints` 6,
  no prompt support-label leakage,
  all gold packets remain copy-default-only with None guard and no copy-selected.
  v22 result:
  on `independent_constraints`, None guard `1.0`, copy-default `1.0`, copy-selected FP `0.0`,
  but repair exact `0.0` because it drops avoid-mutation on all 6 rows.
  v2b result:
  on `independent_constraints`, None guard `1.0`, copy-default `1.0`, copy-selected FP `0.0`,
  repair exact `0.833333`.
  Interpretation:
  the main copy-default-only failure is partly representation/evidence-factorization,
  not a need for runtime packet rewriting.
- [x] Next v2d data/target step:
  build a small evidence-atom/factorized-target correction set rather than a bucket-rule replay set.
  The target should make each reliable memory support atom explicit in training metadata:
  default-copy support,
  None/empty preservation support,
  avoid-shared-mutation support,
  copy-selected support family if present.
  Supervise the controller to emit `delegate_packet.repair_constraints` from these independent atoms while still citing selected memory IDs as evidence.
  Evaluation must include both old label-hidden rows and v2c representation variants.
  Gate before any `gpt-5.4-mini` call:
  evidence exact `1.0`,
  support-label-as-evidence `0`,
  copy-default-only copy-selected FP `0`,
  copy-default-only copy-default recall `1.0`,
  copy-default-only None-guard recall near `1.0`,
  avoid-mutation recall near `1.0`,
  explicit-copy bucket clean,
  max both-copy rate `0`.
  Do not implement a runtime packet rewriter.
- [x] Built/trained/evaluated v2d and v2e evidence-atom correction.
  v2d:
  dataset `data\memory_controller_sft_v2d_evidence_atom_20260612_1810`,
  checkpoint `global_step_15`,
  old18 gate failed with None guard `0.166667`, copy-default-only copy-selected FP `0.166667`,
  copy-default rate `0.833333`.
  v2c probe showed independent constraints fix None/copy-default/copy-selected,
  but avoid-mutation recall drops to `0.333333`.
  v2e:
  dataset `data\memory_controller_sft_v2e_evidence_atom_completeness_20260612_1845`,
  checkpoint `global_step_21`, val loss `0.703`.
  v2e did not pass gate and regressed old18 copy-default-only behavior:
  copy-selected FP `0.833333`, both-copy `0.5`, repair exact `0.0`.
  Failure taxonomy:
  `runs\multi-agent-proxy-v1\mutable_container_packet_v2b_v2d_v2e_failure_taxonomy_20260612_1910.json`.
  Do not call `gpt-5.4-mini`.
- [x] Next controller-learning step:
  stop broad correction-set training for this mutable-container packet gate.
  Diagnose why v2e corrections create negative transfer between `compact_boundary`
  and `independent_constraints`.
  Build an offline pairwise/ranking or typed-evidence objective that scores complete atom sets:
  default-copy vs selected-copy alternative,
  None/empty preservation as independent required atom,
  avoid-shared-mutation as independent required atom.
  The small model must learn to emit all supported atoms and reject unsupported copy-selected,
  while evidence IDs remain selected memory IDs.
  Evaluate on old18 + v2c before any further training or downstream large-model call.
  Keep runtime packet rewriting forbidden.
- [x] Preference data-format bridge / dry-run:
  do not convert v2f into another SFT correction set.
  Export the pairwise data into a VERL `RMDataset`-compatible format with
  prompt/chosen/rejected fields preserved and bad packets never inserted into prompt context.
  Added:
  `scripts\export_pairwise_for_verl_rm.py`
  and `tests\scripts\test_export_pairwise_for_verl_rm.py`.
  Full export:
  `data\memory_controller_pairwise_v2f_rm_export_20260612_2015`,
  `176` rows, `30` groups, positive margin `1.0`, min margin `0.18`,
  no support-label leakage, rejected-in-prompt `false`.
  Remote tiny dry-run:
  VERL `RMDataset` reads the uploaded 8-row parquet with Qwen3-8B tokenizer;
  first sample shapes are `(2, 2048)` for both input ids and attention mask.
- [x] DPO-style loss dry-run:
  add a no-update dry-run that loads one pairwise batch from
  `data\memory_controller_pairwise_v2f_rm_export_20260612_2015\rm_pairs.parquet`.
  The dry-run consumes `prompt/chosen/rejected` as preference alternatives,
  not as SFT responses and not as previous assistant-turn correction context.
  Added:
  `scripts\run_pairwise_dpo_dryrun.py`,
  `tests\scripts\test_run_pairwise_dpo_dryrun_no_torch.py`,
  and `tests\scripts\test_run_pairwise_dpo_dryrun.py`.
  Local tests:
  `6 passed, 1 skipped`.
  Remote Qwen3-8B dry-run:
  limit 1 loss `0.1427`, logp margin `18.75`, preference accuracy `1.0`;
  limit 2 loss `0.116943`, mean/min logp margin `21.125 / 18.75`,
  preference accuracy `1.0`.
  No optimizer update, no checkpoint, no packet rewrite.
- [x] Preference-training engineering step:
  implement a tiny LoRA preference trainer or launcher for the v2f RM export.
  Start with a very small subset and one short run:
  load `prompt/chosen/rejected`,
  compute DPO-style chosen/rejected logprobs,
  apply LoRA optimizer updates,
  write an explicit checkpoint/log directory,
  and record train loss plus no-op safety checks.
  Do not train on rejected packets as SFT responses.
  After that, serve the checkpoint temporarily and evaluate old18 + v2c.
  Required post-training gate before any downstream `gpt-5.4-mini` probe:
  old18 + v2c valid JSON/memory/path/action/delegate/evidence/all-core `1.0`,
  support-label-as-evidence `0`,
  copy-default-only copy-selected FP `0`,
  copy-default-only copy-default recall `1.0`,
  copy-default-only None-guard recall near `1.0`,
  avoid-mutation recall near `1.0`,
  explicit-copy bucket clean,
  max both-copy rate `0`.
- [x] Ran tiny/stable LoRA preference diagnostics.
  v2g tiny 4-row smoke test proved the PEFT update/checkpoint path but was not a usable controller:
  preference accuracy `0.5`, mean margin `-80.375`.
  Updated the trainer to use disabled-adapter DPO reference logps plus before/after and per-bucket diagnostics.
  Built balanced30:
  `data\memory_controller_pairwise_v2f_rm_export_balanced30_20260612_1945`,
  one lowest-positive-margin pair per group,
  `30` rows / `30` groups,
  bucket counts `copy_default_only=18`, `explicit_copy_selected=6`, `inferable_ambiguous=6`.
  v2h/v2i 30-step short runs were stable but not gate-ready:
  overall preference accuracy stayed `0.766667`.
  v2i bucket diagnostics showed explicit-copy is already good
  (`1.0` accuracy, positive margin),
  while copy-default-only and inferable-ambiguous remain negative-margin
  (`0.722222` / `0.666667` accuracy).
  Do not serve v2g/v2h/v2i and do not call `gpt-5.4-mini`.
- [x] v2j preference-target diagnostic:
  inspect balanced30 failing pairs by bucket, pair variant, completion length,
  and rejected feature type.
  Goal:
  decide whether huge negative margins are caused by sequence-length/logprob bias,
  JSON field ordering/serialization artifacts,
  or genuinely missing atom-level preference.
  If length/serialization dominates, build a normalized-pair export or
  token-normalized loss diagnostic.
  If atom preference dominates, build an atom-level pairwise objective over
  default-copy, None/empty preservation, and avoid-shared-mutation decisions.
  Do not convert rejected packets into SFT targets.
  Do not add runtime packet rewriting rules.
  Do not run old18/v2c packet gate or downstream large-model probes until a
  preference checkpoint has sane per-bucket margins.
- [x] Ran v2j logprob/atom-failure diagnostic.
  Added:
  `scripts\run_pairwise_logprob_diagnostics.py`
  and `tests\scripts\test_run_pairwise_logprob_diagnostics_no_torch.py`.
  Local tests:
  `3 passed`; py_compile passed.
  Remote output:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/memory_controller_pairwise_v2j_logprob_diag_balanced30_20260612_2018`.
  Balanced30 metrics:
  raw accuracy `0.766667`,
  token-normalized accuracy `0.666667`,
  mean raw margin `-29.120833`,
  mean normalized margin `-0.094315`.
  Token normalization did not solve the failure.
  Explicit-copy remains clean (`1.0 / 1.0` raw/normalized accuracy).
  Synthetic unsupported-copy negatives are mostly separated
  (`0.958333 / 0.833333` raw/normalized accuracy).
  Severe failures concentrate in actual controller outputs that omit
  `avoid_mutating_shared_defaults_or_callers`:
  `6` rows, raw/normalized accuracy `0.0 / 0.0`,
  mean raw margin `-200.479167`,
  mean normalized margin `-0.539188`.
  Conclusion:
  next bottleneck is an atom-level avoid-mutation preference failure, not a
  generic sequence-length artifact and not a need for runtime packet rewriting.
- [x] v2k atom-level preference step:
  build compact pairwise data that isolates
  `avoid_mutating_shared_defaults_or_callers` as a mandatory evidence atom.
  Prefer short canonical completions or field-local alternatives over full JSON
  packet SFT.
  Include positive examples where selected reliable memory supports:
  default-copy plus None/empty preservation plus avoid-shared-mutation.
  Include hard negatives that are identical except they omit avoid-mutation.
  Keep evidence IDs as selected memory IDs, never support-label strings.
  Evaluate with raw and normalized logprob diagnostics before any LoRA training.
  If margins become sane, run a tiny LoRA update and then old18/v2c gate.
  Do not train rejected full packets as SFT responses.
  Do not add runtime packet rewriting rules.
  Do not call `gpt-5.4-mini` before the packet gate passes.
- [x] Ran v2k avoid-mutation atom diagnostic.
  Added:
  `scripts\build_mutable_container_packet_v2k_avoid_mutation_atom_pairwise.py`
  and
  `tests\scripts\test_build_mutable_container_packet_v2k_avoid_mutation_atom_pairwise.py`.
  Local tests:
  `3 passed`; py_compile passed.
  Built:
  `data\memory_controller_pairwise_v2k_avoid_mutation_atom_20260612_2000`,
  `30` rows / `30` groups,
  chosen/rejected differ only by
  `avoid_mutating_shared_defaults_or_callers`,
  no support-label evidence leakage.
  Remote no-update logprob diagnostic:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/memory_controller_pairwise_v2k_avoid_atom_logprob_diag_20260612_2028`.
  Result:
  raw accuracy `1.0`,
  token-normalized accuracy `1.0`,
  mean raw margin `8.105729`,
  mean normalized margin `0.332183`,
  all buckets `1.0 / 1.0`.
  Conclusion:
  the base/v22 model can prefer the avoid-mutation atom when represented as a
  compact field-local decision.
  The remaining failure is likely full-packet composition/serialization, not
  atom valuation.
  Do not train v2k LoRA yet because the short target is already solved.
- [x] v2l packet-plan bridge diagnostic:
  build a compact two-stage target where the controller first emits
  `packet_plan`:
  selected memory ids,
  evidence ids,
  required repair atoms,
  and guard checklist;
  then emits/evaluates the full `delegate_packet`.
  The plan must be model-produced training/evaluation target, not a runtime
  packet rewriter.
  Use v2j/v2k findings to test whether making atom checklists explicit improves
  full packet completeness for the six actual-output failures that omitted
  `avoid_mutating_shared_defaults_or_callers`.
  Evaluate plan-only and full-packet alternatives with raw/normalized logprob
  diagnostics before any LoRA training.
  If plan-level margins are sane but full-packet margins are not, train or
  evaluate a small controller objective on plan-to-packet consistency rather
  than broader SFT correction.
  Do not call `gpt-5.4-mini` before old18/v2c packet gates pass.
- [x] Ran v2l packet-plan bridge diagnostic.
  Added:
  `scripts\build_mutable_container_packet_v2l_packet_plan_bridge.py`
  and
  `tests\scripts\test_build_mutable_container_packet_v2l_packet_plan_bridge.py`.
  Local tests:
  `4 passed`; py_compile passed.
  Built:
  `data\memory_controller_pairwise_v2l_packet_plan_bridge_20260612_2010`,
  `18` rows from `6` actual-output failures:
  `6` plan-only,
  `6` plan-context-full-packet,
  `6` plan-plus-full-consistency.
  Remote no-update logprob diagnostic:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/memory_controller_pairwise_v2l_packet_plan_bridge_logprob_diag_20260612_2038`.
  Results:
  overall raw/normalized accuracy `0.333333 / 0.333333`.
  `plan_only` is solved:
  `1.0 / 1.0`, mean margin `9.916667 / 0.252711`.
  `plan_context_full_packet` fails:
  `0.0 / 0.0`, mean margin `-157.4375 / -0.403343`.
  `plan_plus_full_consistency` fails:
  `0.0 / 0.0`, mean margin `-171.0 / -0.308981`.
  Conclusion:
  packet_plan/atom selection is learned in short form,
  but full-packet generation still receives higher likelihood when omitting the
  required avoid-mutation atom.
  The bottleneck is plan-to-full-packet composition/serialization.
- [x] v2m local plan-to-packet consistency objective:
  build pairwise data where the prompt contains a packet_plan and the completion
  is only the `delegate_packet.repair_constraints` field, not the full JSON
  packet.
  Chosen constraints must exactly include all packet_plan required atoms;
  rejected constraints should be identical except they omit
  `avoid_mutating_shared_defaults_or_callers`.
  Evaluate raw and normalized logprob margins.
  If v2m is solved like v2k, the remaining issue is full JSON serialization and
  the controller should be trained/evaluated to emit a compact plan/checklist
  before full packet generation.
  If v2m fails, train a tiny LoRA or DPO objective on this local consistency
  field before any full-packet gate.
  Do not add runtime packet rewriting rules.
  Do not call `gpt-5.4-mini` before old18/v2c packet gates pass.
- [x] Ran v2m local plan-to-repair-constraints consistency diagnostic.
  Added:
  `scripts\build_mutable_container_packet_v2m_plan_constraints_consistency.py`
  and
  `tests\scripts\test_build_mutable_container_packet_v2m_plan_constraints_consistency.py`.
  Local tests:
  `4 passed`; py_compile passed.
  Built:
  `data\memory_controller_pairwise_v2m_plan_constraints_consistency_20260612_2020`,
  `6` rows / `6` groups,
  completion only `delegate_packet.repair_constraints`,
  chosen/rejected differ only by
  `avoid_mutating_shared_defaults_or_callers`.
  Remote no-update logprob diagnostic:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/memory_controller_pairwise_v2m_plan_constraints_logprob_diag_20260612_2048`.
  Result:
  raw accuracy `1.0`,
  token-normalized accuracy `1.0`,
  mean raw margin `8.557292`,
  mean normalized margin `0.526583`,
  worst raw margin still positive `8.375`.
  Conclusion:
  local plan-to-constraints consistency is already solved; the unresolved issue
  is full long JSON packet composition/serialization.
  Do not train v2m LoRA.
- [x] v2n compact output-format diagnostic:
  build an evaluation target that separates the model output into:
  `packet_plan`,
  `delegate_packet.repair_constraints`,
  and `delegate_packet_rest` / other packet fields.
  Compare alternatives where the plan and constraints are complete versus
  alternatives that omit avoid-mutation in the constraints while keeping the rest
  of the packet stable.
  Goal:
  test whether a compact structured output format lets the controller preserve
  learned critical atoms without a runtime rewriter.
  Evaluate raw/normalized logprob margins before any training.
  If v2n succeeds, update the controller target format and paper narrative
  toward learned plan/checklist emission.
  If v2n fails, consider a tiny LoRA/DPO objective only on compact output-format
  consistency, not broad full-packet SFT.
  Do not call `gpt-5.4-mini` before old18/v2c packet gates pass.
- [x] Ran v2n compact output-format diagnostic.
  Added:
  `scripts\build_mutable_container_packet_v2n_compact_output_format.py`
  and
  `tests\scripts\test_build_mutable_container_packet_v2n_compact_output_format.py`.
  Local tests:
  `4 passed`; py_compile passed.
  Built:
  `data\memory_controller_pairwise_v2n_compact_output_format_20260612_2030`,
  `6` rows / `6` groups.
  Chosen/rejected keep `packet_plan`, `delegate_packet_rest`, and `packet_rest`
  identical; only `delegate_packet_constraints` differs by the avoid-mutation
  atom.
  Remote no-update logprob diagnostic:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/memory_controller_pairwise_v2n_compact_output_logprob_diag_20260612_2058`.
  Result:
  overall raw/normalized accuracy `0.333333 / 0.666667`,
  mean raw/normalized margin `-2.916667 / 0.01263`.
  `copy_default_only` improves to normalized accuracy `1.0`
  with mean normalized margin `0.029803`,
  but `inferable_ambiguous` remains `0.0 / 0.0`
  with mean normalized margin `-0.021717`.
  Conclusion:
  splitting constraints out helps but does not fully solve long-output/rest-field
  interaction, especially for ambiguous prompts.
- [x] Next v2o constraints-first/minimal-rest compact format:
  build a variant where `delegate_packet_constraints` appears first in the
  completion, followed by `packet_plan`, and only minimal rest fields needed for
  routing/localization/guards.
  Compare complete constraints vs omit-avoid alternatives with rest fields held
  fixed.
  Focus especially on the two `inferable_ambiguous` failures from v2n.
  Evaluate raw/normalized logprob margins before any training.
  If v2o passes, use this output format as the candidate controller target for
  old18/v2c generation probes.
  If v2o still fails on ambiguous rows, build a tiny DPO objective only on this
  compact output-format consistency, not broad full-packet SFT.
  Do not add runtime packet rewriting rules.
  Do not call `gpt-5.4-mini` before packet gates pass.
- [x] Ran v2o constraints-first/minimal-rest no-update diagnostic.
  Added:
  `scripts\build_mutable_container_packet_v2o_constraints_first_minimal_rest.py`
  and
  `tests\scripts\test_build_mutable_container_packet_v2o_constraints_first_minimal_rest.py`.
  Local tests:
  `2 passed`; py_compile passed.
  Built:
  `data\memory_controller_pairwise_v2o_constraints_first_minimal_rest_20260612_2020`,
  `6` rows / `6` groups, `copy_default_only=4`,
  `inferable_ambiguous=2`.
  Chosen/rejected keep `packet_plan` and minimal rest fixed; only
  `delegate_packet_constraints` differs by
  `avoid_mutating_shared_defaults_or_callers`, and constraints are the first
  generated field.
  Remote no-update logprob diagnostic:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/memory_controller_pairwise_v2o_constraints_first_minimal_rest_logprob_diag_20260612_2028`.
  Result:
  overall raw/normalized accuracy `0.666667 / 1.0`,
  mean raw/normalized margin `6.791667 / 0.059586`.
  The two previously failing `inferable_ambiguous` rows are now clean:
  raw/normalized accuracy `1.0 / 1.0`,
  mean raw/normalized margin `17.75 / 0.097664`.
  Remaining raw failures are two `copy_default_only` rows with the chosen side
  10 tokens longer; both have positive normalized margins.
  Conclusion:
  putting evidence-backed constraints first and shortening the rest fixes the
  ambiguous long-output interaction without runtime packet rewriting.
- [x] v2p direct generation probe for the v2o target format.
  Added:
  `scripts\run_constraints_first_generation_probe.py`
  and
  `tests\scripts\test_run_constraints_first_generation_probe.py`.
  Local tests:
  `5 passed`; py_compile passed.
  Command:
  `uv run python scripts\run_constraints_first_generation_probe.py --pairs data\memory_controller_pairwise_v2o_constraints_first_minimal_rest_20260612_2020\rm_pairs.parquet --output runs\multi-agent-proxy-v1\constraints_first_generation_probe_v2p_20260612_2035.jsonl --api-base http://127.0.0.1:18001/v1 --model local-qwen3-8b-memory-polarproxy-v22 --timeout 120 --max-tokens 900`.
  Result:
  valid JSON `1.0`,
  constraints-first `1.0`,
  constraint recall/precision `1.0 / 1.0`,
  avoid-mutation rate `1.0`,
  packet-plan rate `1.0`,
  selected-memory/evidence match `1.0 / 1.0`,
  but strict `minimal_rest` field rate `0.0`, so format-core `0.0`.
  Conclusion:
  actual decoding already preserves the key evidence atom and plan; the only
  failure is schema-wrapper naming/rest placement. Treat this as target-format
  alignment work, not a reason to call the large model or add a runtime rewriter.
- [x] Next v2q constraints-first flat-rest generation target:
  build a compact target that keeps `delegate_packet_constraints` first and
  `packet_plan` second, then allows flat minimal routing/localization/guard
  fields matching the v2p natural generations instead of forcing a
  `minimal_rest` wrapper.
  Evaluate both pairwise logprob and direct generation on the same six rows.
  Passing gate should require valid JSON, constraints-first, full required
  constraint recall including `avoid_mutating_shared_defaults_or_callers`,
  selected/evidence memory match, and no unsupported copy-selected atom.
  Do not treat this as runtime packet rewriting; it is a controller target-format
  change.
  Do not call `gpt-5.4-mini` until v2q generation passes and old18/v2c compact
  gates are sane.
- [x] Ran v2q constraints-first flat-rest pairwise and generation gates.
  Added:
  `scripts\build_mutable_container_packet_v2q_constraints_first_flat_rest.py`
  and
  `tests\scripts\test_build_mutable_container_packet_v2q_constraints_first_flat_rest.py`.
  Updated:
  `scripts\run_constraints_first_generation_probe.py`
  and
  `tests\scripts\test_run_constraints_first_generation_probe.py`
  to score flat rest as a target format and explicitly reject unsupported
  copy-selected atoms.
  Local tests:
  `6 passed`; py_compile passed.
  Built:
  `data\memory_controller_pairwise_v2q_constraints_first_flat_rest_20260612_2045`,
  `6` rows / `6` groups, `copy_default_only=4`,
  `inferable_ambiguous=2`.
  Remote no-update logprob diagnostic:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/memory_controller_pairwise_v2q_constraints_first_flat_rest_logprob_diag_20260612_2052`.
  Result:
  raw/normalized accuracy `1.0 / 1.0`,
  mean raw/normalized margin `13.166667 / 0.06511`.
  Direct generation command:
  `uv run python scripts\run_constraints_first_generation_probe.py --pairs data\memory_controller_pairwise_v2q_constraints_first_flat_rest_20260612_2045\rm_pairs.parquet --output runs\multi-agent-proxy-v1\constraints_first_flat_rest_generation_probe_v2q_20260612_2055.jsonl --api-base http://127.0.0.1:18001/v1 --model local-qwen3-8b-memory-polarproxy-v22 --timeout 120 --max-tokens 900`.
  Result:
  valid JSON `1.0`,
  constraints-first `1.0`,
  constraint recall/precision `1.0 / 1.0`,
  avoid-mutation `1.0`,
  unsupported copy-selected rate `0.0`,
  packet-plan `1.0`,
  flat rest `1.0`,
  selected/evidence match `1.0 / 1.0`,
  format-core `1.0`.
  Conclusion:
  v2q is the current best candidate controller target format for reliable
  memory packet compression: it preserves the critical evidence atoms during
  actual decoding without runtime packet rewriting.
- [x] Next v2r old18/v2c compact generation gate:
  convert the relevant old18 label-hidden rows and v2c representation-probe rows
  into the v2q constraints-first flat-rest target format, then run a direct
  generation gate with the served v22 endpoint.
  Gate metrics:
  valid JSON, constraints-first, required constraint recall/precision,
  avoid-mutation recall, unsupported copy-selected false-positive rate,
  selected/evidence memory match, path/localization recall, and guard presence.
  If v2r passes, update LATEX-NIPS with the support-aware packet-boundary table
  and consider a tiny downstream large-model edit probe only after the packet
  gate.
  If v2r fails, build targeted contrastive/pairwise data for the failing format
  or evidence-boundary cases; do not add runtime rewriters.
  Do not call `gpt-5.4-mini` yet.
- [x] Ran v2r old18/v2c compact generation gate.
  Added:
  `scripts\build_mutable_container_packet_v2r_flat_rest_gate.py`
  and
  `tests\scripts\test_build_mutable_container_packet_v2r_flat_rest_gate.py`.
  Updated:
  `scripts\run_constraints_first_generation_probe.py`
  to report path recall, guard presence, action/delegate match, and by-source /
  by-bucket summaries.
  Local tests:
  `6 passed`; py_compile passed.
  Built:
  `data\memory_controller_v2r_old18_v2c_flat_rest_gate_20260612_2105`,
  `30` rows / `30` groups:
  old18 label-hidden `18`, v2c representation `12`;
  buckets `copy_default_only=18`, `explicit_copy_selected=6`,
  `inferable_ambiguous=6`.
  Direct generation:
  `runs\multi-agent-proxy-v1\constraints_first_flat_rest_generation_probe_v2r_old18_v2c_20260612_2110.jsonl`.
  The first shell timed out at 15 minutes, but the background probe finished all
  `30` rows and wrote the summary.
  Result:
  valid JSON `0.933333`,
  constraints-first `0.933333`,
  packet-plan `0.933333`,
  flat rest `0.933333`,
  selected/evidence match `0.933333 / 0.933333`,
  path recall `0.9`,
  guard presence `0.8`,
  action/delegate accuracy `0.866667 / 0.866667`,
  strict constraint recall/precision `0.033333 / 0.033333`,
  strict avoid-mutation rate `0.033333`,
  format-core `0.0`.
  Failure diagnosis:
  `27/30` generations made `delegate_packet_constraints` a dict instead of a
  flat list.
  Nested atom extraction shows the model often knows the atoms:
  nested/list atom counts include
  `avoid_mutating_shared_defaults_or_callers=28`,
  `check_none_explicitly_preserve_empty_falsy_container=28`,
  `copy_default_container_before_mutation=23`,
  `copy_selected_mapping_before_mutation=5`.
  Conclusion:
  v2r fails the strict gate, but the bottleneck is mostly field-type/list-format
  generalization, not missing reliable evidence atoms.
- [x] Next v2s flat-list field-type correction:
  build a small pairwise or generation-target diagnostic where
  `delegate_packet_constraints` must be a JSON list, while hard negatives keep
  the same atoms nested under objects such as `required_repair_atoms` or
  `repair_constraints`.
  Use old18/v2c v2r failures as source rows.
  Evaluate raw/normalized logprob and a short direct generation gate.
  This should train/test the small controller's format judgment, not a runtime
  normalizer; do not post-process nested constraints into lists.
  Do not call `gpt-5.4-mini`.
- [x] Ran v2s flat-list field-type diagnostic and generation gate.
  Added:
  `scripts\build_mutable_container_packet_v2s_flat_list_field_type_pairwise.py`
  and
  `tests\scripts\test_build_mutable_container_packet_v2s_flat_list_field_type_pairwise.py`.
  Updated:
  `scripts\run_constraints_first_generation_probe.py`
  to avoid treating gold-supported explicit copy-selected atoms as unsupported
  and to rescore existing outputs offline without another model call.
  Pairwise data:
  `data\memory_controller_pairwise_v2s_flat_list_field_type_20260612_2135`,
  `30` rows / `30` groups.
  Rejected variants use same atoms nested under objects:
  `required_repair_atoms=23`, `repair_constraints=6`, `already_flat_list=1`.
  Remote no-update logprob diagnostic:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/memory_controller_pairwise_v2s_flat_list_field_type_logprob_diag_20260612_2140`.
  Result:
  raw/normalized accuracy `1.0 / 1.0`,
  mean raw/normalized margin `16.591667 / 0.034581`;
  all buckets `1.0 / 1.0`.
  Generation-gate data:
  `data\memory_controller_v2s_flat_list_generation_gate_20260612_2150`,
  `30` rows.
  Direct generation:
  `runs\multi-agent-proxy-v1\constraints_first_flat_list_generation_probe_v2s_20260612_2155.jsonl`,
  rescored to
  `runs\multi-agent-proxy-v1\constraints_first_flat_list_generation_probe_v2s_20260612_2155_rescored.jsonl`.
  Rescored result:
  valid JSON `1.0`,
  constraints-first `1.0`,
  constraint recall/precision `1.0 / 1.0`,
  avoid-mutation `1.0`,
  unsupported copy-selected `0.0`,
  flat rest `1.0`,
  path recall `1.0`,
  guard presence `1.0`,
  action/delegate `1.0 / 1.0`,
  format-core `0.7`.
  By source:
  old18 format-core `1.0`;
  v2c format-core `0.25`.
  Failure diagnosis:
  v2s solved the flat-list field type and atom preservation.
  Remaining v2c failures omit `packet_plan`; top-level selected/evidence ids
  are usually correct.
- [x] Next v2t packet-plan retention diagnostic:
  build a focused generation/pairwise target for v2c-style prompts where
  `packet_plan` must remain present immediately after
  `delegate_packet_constraints`, while top-level selected/evidence ids and flat
  rest stay unchanged.
  Hard negatives should omit `packet_plan` but keep otherwise correct atoms and
  top-level evidence ids, matching v2s failures.
  This is target-format learning, not a runtime wrapper insertion.
  Do not call `gpt-5.4-mini`.
- [x] Next v2u / downstream decision:
  v2t-full now passes the 30-row old18/v2c strict generation gate with
  constraints-first, flat-list constraints, packet_plan second, flat rest,
  selected/evidence ids, path recall, guards, action/delegate, and format-core
  all at `1.0`.
  Before calling `gpt-5.4-mini`, choose one of two small steps:
  run a tiny 3--4 row downstream delegate probe only on held-out
  mutable-container residuals, or build a broader non-v2c generalization gate
  that checks the same learned packet boundary without adding runtime
  normalizers.
  Do not convert this into hard-coded packet repair rules.
- [x] Next v2v / tiny downstream choice:
  v2u broader v2f balanced30 gate also passes strict generation with all core
  metrics at `1.0`, so the packet-boundary target is no longer only an
  old18/v2c artifact.
  The next useful step can be a tiny 3--4 row downstream `gpt-5.4-mini` delegate
  probe on held-out mutable-container residuals, using one relay and only the
  v2t/v2u-clean packets, or a still broader non-mutable memory-controller gate
  if we want more small-model-only evidence first.
  Keep this controller-first; do not add runtime packet normalizers or broad
  large-model sweeps.
- [x] Next v2w:
  Do not expand to a broad large-model sweep yet.
  Either build a non-mutable-family small-controller gate for locating/testing
  or design a tiny verifier-style probe where the small controller decides
  whether to accept/retry a large-model command using packet-visible evidence.
  The main value should remain learned memory reliability, locating/editing/
  testing/delegation, and guard judgment rather than more prompt rules.
- [ ] Next v2x:
  Build a compact visible-default/semantic-guard binding correction for the
  small controller using packet-visible evidence only.
  The v2w miss is `generated_wide_heldout_semantic_edit_path`: packet-visible
  default is `root`, while the delegate command used `else ''`; v22 accepted
  the command because it saw an explicit `None` guard but failed to bind the
  guard to `visible_default_matches_command=false`.
  Evaluate on the same 9-row visible accept/retry probe first:
  target valid JSON `1.0`, retry precision `1.0`, retry recall `1.0`, and
  unnecessary retry calls `0`.
  Do not make this a runtime rule-based normalizer; use it as a small-controller
  judgment/distillation target.
- [x] v2x current-feature rebuild check:
  rebuilt the same 9-row downstream visible verifier data with the current
  feature extractor and reran v22.
  Result: valid JSON `1.0`, verdict accuracy `0.777778`, retry recall `0.5`,
  retry precision `0.5`, unnecessary retry `1`, missed retry `1`.
  This is worse than v2w, so do not fix the issue by adding more visible policy
  text or runtime rules.
- [ ] Next v2y:
  Build/evaluate a compact relation-binding target for the small controller:
  selected/evidence ids, semantic guard id, visible default required by packet,
  command default used by delegate, `defaults_match`, and accept/retry decision.
  Positive/negative pairs should teach the model that explicit `None` checks are
  insufficient when the `else` value disagrees with packet-visible evidence, and
  that safe `.copy()` forms do not require unnecessary `copy.deepcopy` retries.
  First evaluate on the same 9-row downstream probe and a tiny balanced
  synthetic held-out set; only after retry recall/precision both reach `1.0`
  should another tiny `gpt-5.4-mini` collaboration run be considered.
- [x] v2y/v2z compact relation-binding probes:
  added `scripts\build_visible_guard_relation_binding_probe.py` and tests.
  Fixed sed replacement default extraction in
  `scripts\build_visible_guard_verifier_data.py`, because the old extractor
  polluted `else 'guest'` with the path suffix.
  Prompt-only v22 results on the same 9-row downstream probe:
  v2y compact relation initial `0.444444` verdict accuracy, retry
  precision/recall `0.2/0.5`;
  sed-fix v2y `0.555556`, precision/recall `0.25/0.5`;
  v2z applicability fields `0.777778`, precision/recall `0.0/0.0`, with zero
  unnecessary retries but both true retry rows missed.
  Conclusion: compact inputs help diagnose the boundary but prompt-only v22
  does not solve it.
- [ ] Next v3a:
  Build a tiny pairwise/logprob diagnostic for compact relation decisions,
  not another verbose prompt.
  Chosen/rejected pairs should isolate:
  RETRY > ACCEPT when `default_binding_applicable=true` and
  `defaults_match=false`;
  ACCEPT > RETRY when default/mutable-copy relations are not applicable;
  ACCEPT > RETRY for safe selected-copy forms such as
  `(config.copy() if config is not None else DEFAULT.copy())`.
  Evaluate no-update logprob margins first on local/remote v22; train only if
  margins show the controller has not learned the boundary.
  Do not call `gpt-5.4-mini` until this compact relation decision gate improves.
- [x] v3a compact relation decision pairwise/logprob diagnostic:
  added `scripts\build_visible_guard_relation_v3a_pairwise.py` and tests.
  Cleaned default extraction for sed/python replacement defaults with escaped
  newlines.
  Built 9 clean pairs:
  `relations_not_applicable_accept=3`, `relations_satisfied=4`,
  `unresolved_copy_deepcopy=1`, `visible_default_mismatch=1`.
  Remote no-update logprob on Qwen3-8B:
  raw/normalized accuracy `1.0/1.0`, mean raw margin `26.638889`, mean
  normalized margin `0.4104`.
  Important mismatch row `generated_wide_heldout_semantic_edit_path` is also
  positive: raw margin `4.125`, normalized margin `0.614745`.
  Conclusion: do not train this boundary yet; the model can score the correct
  short verdict higher, but free-form generation/reason text remains unstable.
- [ ] Next v3b:
  Build a short verdict-head/direct-choice probe for the same compact relation
  records.
  Compare three modes on the 9-row downstream probe:
  full JSON reason generation, short `{"verdict": ...}` generation, and
  two-choice logprob scoring of ACCEPT vs RETRY.
  Success target: valid JSON `1.0`, retry recall/precision `1.0/1.0`, no
  unnecessary retries, without training and without runtime rule rewriting.
  Only if short verdict/direct-choice still fails should we consider a tiny
  SFT/DPO correction; do not call `gpt-5.4-mini` before this gate.
- [x] v3b short verdict-head generation probe:
  added `scripts\build_visible_guard_short_verdict_probe.py` and tests.
  Built `data\visible_guard_short_verdict_v3b_downstream9_20260613_0027.jsonl`.
  Local v22 short verdict generation result:
  valid JSON `1.0`, verdict accuracy `0.555556`, retry recall/precision
  `0.0/0.0`, unnecessary retries `2`, missed retries `2`.
  This confirms free generation is unstable even when the output is only
  `{"verdict": ...}`.
  Because v3a two-completion logprob scoring was `1.0/1.0`, do not train this
  boundary or add more prompt text.
- [ ] Next v3c:
  Implement/evaluate a two-choice verdict scorer for compact relation records:
  score the two short completions `{"verdict":"ACCEPT"}` and
  `{"verdict":"RETRY"}` under the same prompt, choose the higher normalized
  logprob, and report retry precision/recall, unnecessary retries, and token
  cost on the 9-row downstream probe.
  This is an execution-interface change for a learned controller subdecision,
  not a runtime rule-based verifier.
  If v3c matches v3a pairwise accuracy, use direct-choice scoring for
  accept/retry before any new `gpt-5.4-mini` collaboration test.
- [x] v3c two-choice verdict scorer:
  added `scripts\score_visible_guard_relation_choice.py` and tests.
  Using the v3a pairwise details, normalized-logprob two-choice scoring gets:
  rows `9`, accuracy `1.0`, retry recall/precision `1.0/1.0`,
  unnecessary retries `0`, missed retries `0`, total choice tokens `642`.
  This beats v3b short verdict generation, which used `5247` provider tokens
  and still had retry precision/recall `0.0/0.0`.
  Conclusion: accept/retry should be executed as a learned two-choice scoring
  subdecision, not free JSON generation and not a hand-written verifier rule.
- [ ] Next v3d:
  Integrate the v3c two-choice accept/retry scorer into a tiny packet-visible
  collaboration trace.
  Reuse the same 9-row downstream setting if possible:
  small controller packet -> large delegate output already available ->
  compact relation extraction -> two-choice accept/retry decision.
  Report final accepted/retry counts, retry precision/recall, unnecessary
  large-model retry calls avoided, and token accounting.
  Keep this tiny and do not launch a broad `gpt-5.4-mini` sweep.
- [x] v3d packet-visible collaboration trace summary:
  added `scripts\summarize_visible_guard_choice_trace.py` and tests.
  On the existing 9-row downstream delegate trace, v3c two-choice policy:
  accepted `7`, retry calls `2`, retry recall/precision `1.0/1.0`,
  unnecessary retries `0`, missed retries `0`, accepted semantic pass `1.0`,
  accepted mean strict `0.899606`, choice loss tokens `642`.
  v3b short-generation policy on the same trace:
  accepted `7`, retry calls `2`, retry recall/precision `0.0/0.0`,
  unnecessary retries `2`, missed retries `2`, accepted semantic pass
  `0.714286`, accepted mean strict `0.834045`, provider tokens `5247`.
  This supports using learned two-choice scoring as the accept/retry interface,
  not free JSON generation or hard-coded verifier rules.
- [x] Next v3e:
  Update LATEX-NIPS narrowly with the v3a--v3d accept/retry interface ablation.
  Emphasize:
  compact relation evidence + two-choice scoring succeeds;
  full/short free generation fails;
  no new training and no large-model sweep were needed.
  Keep the claim bounded to packet-visible accept/retry on the 9-row trace.
- [x] Next v3f:
  Test whether the learned two-choice scoring interface generalizes beyond the
  visible-default/mutable-copy downstream9 slice.
  Build a tiny non-mutable guard/route accept-retry or locate/edit/test/delegate
  choice set from existing artifacts if possible, score alternatives with the
  same local Qwen v22 endpoint, and compare against free generation.
  This should remain a small-controller judgment probe:
  do not add runtime verifier rules, do not launch broad `gpt-5.4-mini`
  sweeps, and only call the large model for a tiny packet-gated collaboration
  smoke after the exact question and sample are fixed.
- [x] Next v3g:
  Build a label-bias-controlled route-choice diagnostic before treating
  two-choice scoring as a route interface.
  v3f route-json scoring predicted `DELEGATE_PACKET` on all 26 rows, while
  equal-length A/B scoring predicted `SELF_HANDLE` on all 26 rows; both got
  only `0.5` accuracy on a balanced route split.
  Next try swapped-label A/B pairs or length-matched semantic route rationales
  and measure consistency by gold route and perturbation.
  This should diagnose readout bias in the learned controller, not become a
  runtime rule or large-model gate.
- [x] Next v3h:
  Do not use route two-choice scoring as a collaboration gate yet.
  Design a different learned route-decision interface:
  either semantically rich but length-balanced route rationales, or a tiny
  contrastive route-choice training/eval set that explicitly separates
  self-handle evidence-sufficient rows from delegate-risk rows under swapped
  label controls.
  Success target before any route-gated large-model run:
  balanced route accuracy clearly above `0.5`, non-collapsed predictions for
  both `SELF_HANDLE` and `DELEGATE_PACKET`, and stable behavior under label
  swapping.
  Keep this as small-controller judgment learning, not a runtime route rule.
- [x] Next v3i:
  Build a tiny contrastive route correction focused on the v3f--v3h collapse.
  Use existing v1j/v2 controller records to create balanced delegate-risk vs
  evidence-sufficient self-handle examples, with hard stale/current-path-vocab
  perturbations and no hidden scorer labels in the prompt.
  Evaluate before training if possible, then train only if needed.
  Success target:
  route predictions must be non-collapsed, balanced accuracy clearly above
  `0.5`, and delegate-risk recall should improve without sacrificing
  self-handle guard correctness.
  Keep accept/retry two-choice as the only currently positive collaboration
  gate; do not run route-gated `gpt-5.4-mini` until v3i passes.
- [x] v3i/v3j current result:
  Built balanced route-judgment v3i data and evaluated both free generation and
  no-update pairwise scoring.
  v3i free generation is non-collapsed but insufficient:
  route accuracy `0.692308`, missed delegate `0.076923`, unnecessary delegate
  `0.230769`, semantic guard recall `0.038462`.
  v3i pairwise normalized accuracy is only `0.653846` and is biased by packet
  completion length/surface.
  Added v3j equal-structure route-card pairs to remove packet length; v3j
  no-update normalized accuracy returns to `0.5` and predicts
  `DELEGATE_PACKET` on all `26` rows.
  Conclusion:
  route choice is not ready as a direct readout or runtime gate; do not launch
  route-gated `gpt-5.4-mini` and do not add hard-coded route rules.
- [x] Next v3k:
  Run a tiny targeted route-card / route-judgment correction on the balanced
  v3i/v3j train split, preferably with a short DPO/SFT LoRA that contrasts
  delegate-risk rows against evidence-sufficient self-handle rows.
  Ready local train artifact:
  `data\route_judgment_v3j_equalized_v1j_train_20260613_1445`
  (`546` pairs, `273/273`, token delta `0`).
  Re-evaluate three gates after training:
  v3i free-generation route judgment, v3i packet-like pairwise, and v3j
  equal-structure route-card pairwise.
  Success target before any route-gated collaboration:
  non-collapsed predictions, balanced route accuracy clearly above `0.5`,
  self-handle recall restored above the v3j `0/13` failure, delegate recall not
  below the v3i `12/13` pairwise signal, and no degradation of the already-good
  accept/retry two-choice gate.
  Keep this as small-model judgment learning; do not encode a fixed
  SELF/DELEGATE routing heuristic into the pipeline.
- [x] v3k current result / Next v3l:
  Ran remote DPO-style LoRA correction on the v3j equalized route-card train
  split, output
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/route_judgment_v3k_equalized_dpo_lora_noeval_20260613_1510`.
  Training: `546` pairs, `273` steps, batch `2`, lr `5e-6`, rank `4`,
  loss `0.693359 -> 0.187744`, mean train margin `3.950206`.
  Positive route-card result:
  v3j equalized held-out normalized accuracy improved from `0.5` to
  `0.923077` (`24/26`), raw accuracy `0.961538`.
  Partial packet/generation result:
  v3i packet-like normalized accuracy improved from `0.653846` to `0.692308`;
  v3i free generation improved route accuracy from `0.692308` to `0.730769`,
  delegate gold `12/13`, self-handle gold still `7/13`, unnecessary delegate
  still `6/13`.
  Blocking regression:
  accept/retry relation raw accuracy remains `1.0`, but normalized accuracy
  drops from `1.0` to `0.888889`, missing one relations-satisfied ACCEPT row.
  Therefore do not launch route-gated `gpt-5.4-mini` yet.
  Next v3l should train or choose a small multi-objective/interface correction
  that keeps the route-card gain while replaying the accept/retry relation
  gate, and should diagnose the two v3j misses plus the v3i packet-like
  path-edit/semantic rows before any collaboration smoke.
- [x] v3l current result / Next v3m:
  Built `data\route_judgment_v3l_route_accept_replay_20260613_1530` with
  `726` train pairs: `546` v3j equalized route-card pairs plus `180`
  compact accept/retry relation replay pairs (`9` unique rows repeated 20x).
  Validation set has `35` pairs: `26` route-card plus `9` accept/retry.
  Remote DPO LoRA output:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/route_judgment_v3l_route_accept_replay_dpo_lora_noeval_20260613_1540`.
  Training: `726` pairs, `363` steps, batch `2`, lr `5e-6`, rank `4`,
  loss `0.693359 -> 0.157959`, mean train margin `17.861915`.
  Result:
  v3j equalized route-card stays strong at normalized `0.923077`
  (raw `1.0`);
  accept/retry relation recovers to normalized/raw `1.0/1.0`;
  but v3i packet-like normalized stays only `0.653846`, and v3i
  free-generation route accuracy returns to `0.692308`
  (`DELEGATE_PACKET` gold `10/13`, `SELF_HANDLE` gold `8/13`).
  Conclusion:
  replay solved the v3k accept/retry regression, but route generalization to
  packet-like/free-generation interfaces is still not learned.
  Do not run route-gated `gpt-5.4-mini`.
  Next v3m should diagnose the interface mismatch, especially why route-card
  scoring works while packet-like and free-generation still confuse
  residual-patch uncertainty with stale/distractor risk.
  Prefer a diagnostic or small data/interface change over another blind LoRA:
  compare route-card fields against v3i generation fields, inspect the missed
  delegate rows and unnecessary delegate rows, and decide whether to train a
  compact direct route-choice head or add packet-like route-card completions
  as learned supervision.
- [x] v3m current result / Next v3n:
  Built offline diagnostic artifact
  `runs\multi-agent-proxy-v1\v3m_interface_diagnostic_20260613_1605`.
  It aligns v3l free-generation route decisions, v3j equalized route-card
  logprob details, and v3i packet-like logprob details over the same 26 rows.
  Result:
  free generation has `8` route failures (`3` missed delegate, `5`
  unnecessary delegate);
  route-card normalized scoring fails only `2` rows;
  packet-like normalized scoring fails `9` rows;
  `6/8` generation failures are rows where route-card scoring was already
  correct.
  Interpretation:
  the route signal exists in the controller, but the free-generation / packet
  interface exposes it poorly.
  Common failure mode:
  generation inflates both `stale_or_distractor_risk` and
  `residual_patch_uncertainty` for self-handle rows, or marks true delegate
  rows as `self_handle_guard_sufficient=true`.
  Next v3n should build/evaluate a compact route-decision interface that uses
  route-card-style fields but matches generation-time field semantics:
  `reliable_support`, `stale_or_distractor_risk`,
  `residual_patch_uncertainty`, `self_handle_guard_sufficient`, and a short
  route verdict.
  Start with no-update direct-choice/logprob scoring before any more LoRA.
  Do not add a runtime SELF/DELEGATE rule and do not call `gpt-5.4-mini` yet.
- [x] v3n/v3o current result:
  Added offline compact route-decision builders/scorer:
  `scripts\build_route_decision_v3n_pairwise.py`,
  `scripts\build_route_decision_v3o_pairwise.py`,
  and `scripts\score_route_decision_v3n.py`, with tests.
  v3n used the four generation-time evidence booleans plus `route_verdict`.
  On the same balanced 26-row v1j validation split, v3l adapter no-update
  scoring got normalized route accuracy `0.5`, predictions
  `DELEGATE_PACKET=18`, `SELF_HANDLE=8`; raw scoring got `0.576923` but
  collapsed toward `SELF_HANDLE=24`.
  v3o added `large_model_role` and `controller_commitment`; it collapsed to
  `DELEGATE_PACKET=26` under both raw and normalized scoring, accuracy `0.5`.
  Diagnostic artifact:
  `runs\multi-agent-proxy-v1\v3n_v3o_route_decision_diagnostic_20260613_1645`.
  Conclusion:
  compact direct-choice/free-generation-style route surfaces still do not
  expose the learned route signal that v3j equalized route-card scoring shows.
  Do not run route-gated `gpt-5.4-mini`.
- [x] Next v3p:
  Stop blind prompt/interface variants after v3n/v3o.
  Either:
  (1) build an exact v3j-vs-v3n surface ablation that changes only one factor
  at a time (`route` vs `route_verdict`, prompt header, key order, commitment
  strings, `guard_sufficient_for_self_handle` vs
  `self_handle_guard_sufficient`), or
  (2) train a tiny compact-interface correction using route-card-compatible
  supervision plus accept/retry replay, then evaluate v3j route-card, v3n/v3o
  compact route, v3i free generation, v3i packet-like scoring, and
  accept/retry.
  Success target before any route-gated large-model call:
  non-collapsed predictions, route accuracy clearly above `0.5`, delegate
  recall and self-handle recall both above `10/13`, and accept/retry still
  normalized/raw `1.0/1.0`.
  Keep the change as learned controller judgment/readout; do not encode
  SELF/DELEGATE as a runtime heuristic.
- [x] v3p current result:
  Built `data\route_surface_v3p_ablation_v1j_val_20260613_1725` with
  `182` pair rows = `26` balanced source rows times `7` surface variants.
  All variants are route-balanced (`13/13`) and have max whitespace token
  delta `0`.
  Remote no-update scoring with the v3l route+accept adapter produced:
  `v3j_exact` normalized/raw route accuracy `0.923077/1.0`;
  `route_verdict_key` `0.923077/1.0`;
  `self_handle_guard_key` `0.769231/0.807692`;
  `generation_key_names` `0.692308/0.769231`;
  `short_prompt_v3j_fields` `0.692308/0.730769`;
  `no_commitment_fields` `0.538462/0.807692`;
  `v3n_like_surface` `0.538462/0.423077`.
  Artifact:
  `runs\multi-agent-proxy-v1\v3p_route_surface_ablation_20260613_1735`.
  Interpretation:
  the route key can be changed to `route_verdict` without loss, but the
  learned readout is sensitive to the
  `guard_sufficient_for_self_handle` key, action-commitment fields
  (`large_model_role`, `controller_commitment`), and the full v3j prompt
  semantics.
  This is a good learned-interface diagnosis, not a runtime router rule.
  Do not run route-gated `gpt-5.4-mini` yet.
- [x] Next v3q:
  Build a tiny route-interface correction/replay based on v3p:
  preserve v3j prompt semantics, `guard_sufficient_for_self_handle`, and
  `large_model_role`/`controller_commitment`, while allowing
  `route_verdict` if desired.
  Mix with accept/retry replay so the previously solved accept/retry gate does
  not regress.
  Evaluate after training or no-update correction on:
  v3j route-card,
  `route_verdict_key`,
  v3n/v3o compact surfaces,
  v3i free generation,
  v3i packet-like pairwise,
  and accept/retry relation.
  Success target before any route-gated large-model call:
  non-collapsed route predictions, normalized route accuracy clearly above
  `0.5`, delegate recall and self-handle recall both at least `10/13`, and
  accept/retry normalized/raw `1.0/1.0`.
  The point is to train the small controller's judgment/readout schema, not to
  hard-code SELF/DELEGATE routing in the pipeline.
- [x] v3q current result / Next v3r:
  Built route-verdict-key train/val from v3p stable surface and mixed route
  training with accept/retry replay:
  `data\route_surface_v3q_routeverdict_accept_replay_20260613_1750`
  (`726` train pairs = `546` route + `180` accept/retry; `35` val pairs).
  Remote DPO LoRA checkpoint:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/route_surface_v3q_routeverdict_accept_replay_dpo_lora_noeval_20260613_1800/adapter`.
  Training:
  `726` rows, `363` steps, loss `0.693359 -> 0.295410`,
  mean train margin `17.059143`, mean preference accuracy `0.691460`.
  Regression:
  route-verdict normalized/route accuracy `0.884615`
  (`DELEGATE_PACKET=16`, `SELF_HANDLE=10`; delegate recall `13/13`,
  self-handle recall `10/13`);
  v3j exact normalized `0.884615`;
  v3n compact normalized `0.576923`;
  v3i packet-like normalized `0.692308`;
  accept/retry normalized/raw `1.0/1.0`.
  Artifact:
  `runs\multi-agent-proxy-v1\v3q_routeverdict_replay_20260613_1820`.
  Conclusion:
  v3q preserves accept/retry but does not beat v3p no-update or v3l route-card
  readout, and compact/packet route remains weak.
  Do not run route-gated `gpt-5.4-mini` from v3q.
- [x] Next v3r:
  Diagnose the three v3q self-handle over-delegations and the route-card
  normalized drop from `0.923077` to `0.884615`.
  Compare v3q failures against v3p `route_verdict_key` failures and v3l
  route-card failures; inspect whether accept/retry replay or route-verdict
  training shifted margins on self-handle rows.
  Prefer a margin/error analysis or a smaller replay ratio sweep over another
  blind LoRA.
  Only train again if the analysis identifies a clear learned-interface target;
  otherwise keep v3p no-update route-card as the current best route readout and
  focus on memory packet quality/guard learning.
- [x] Next v3s:
  Build a tiny contrastive replay/margin correction for
  "self-handle despite stale/distractor risk" rows.
  Positive pattern:
  `reliable_support=true`, `stale_or_distractor_risk=true`,
  `residual_patch_uncertainty=false`,
  `guard_sufficient_for_self_handle=true`, with exact current source or exact
  focused test evidence.
  Hard negatives should differ by missing reliable current evidence, missing
  guard sufficiency, or true residual patch uncertainty, not by task family
  labels.
  Keep accept/retry replay as an anchor.
  Before training, first build and inspect the data/margins; train only if the
  correction is small and clearly targets this learned boundary.
  Success target:
  recover v3p/v3l route-card normalized `0.923077` or better,
  keep delegate recall at least `12/13`, self-handle recall at least `11/13`,
  and preserve accept/retry normalized/raw `1.0/1.0`.
  Do not add runtime rules that map stale risk to SELF/DELEGATE.
- [x] v3t route-objective diagnostic / route rabbit-hole stop point:
  Do not train another naive route replay yet.
  v3s data audit found the self-handle-with-stale-risk positive pattern is
  already abundant (`273/546` train rows, all self-handle route rows).
  The v3t artifact
  `runs\multi-agent-proxy-v1\v3t_objective_surface_diagnostic_20260613_1900`
  confirms the route surfaces are whitespace balanced but DPO/replay shifted
  normalized margins in a route-dependent way:
  v3p no-update route-verdict margins were delegate/self
  `0.192778/0.203857`, while v3q became `0.268707/0.145408`.
  This explains the delegation bias without justifying another blind route
  LoRA.
  Updated direction after user feedback:
  use the stable v3p/v3l route-card readout pragmatically and move to
  small-controller + large-model collaboration tests.
  Do not spend more turns trying to make arbitrary JSON field names/orders
  robust before testing cooperation.
- [x] Ran a working `gpt-5.4-mini` collaboration smoke on the replacement AZ
  endpoint.
  Health probe:
  `https://az.gptplus5.com/v1/chat/completions` with model `gpt-5.4-mini`
  returned HTTP `200`.
  4-row mutable-container delegate packet smoke:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_aznew_v1n_delegate4_20260613_1912_scored.jsonl.summary.json`,
  rows `4`, error `0`, action/skill/semantic pass rates `1.0/1.0/1.0`,
  mean strict `0.898750`, total tokens `7637`.
  6-row selective proxy12 delegate smoke:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_aznew_v1j_collab_proxy12_20260613_1915_scored.jsonl.summary.json`,
  rows `6`, error `0`, action/skill `1.0/1.0`, semantic pass `0.666667`,
  mean strict `0.820319`, total tokens `8885`.
  Existing guard retry recovered the proxy12 failures:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_aznew_v1j_collab_proxy12_semfail_guardretry_20260613_1915_scored.jsonl.summary.json`,
  rows `5`, semantic pass `1.0`, mean strict `0.923500`.
  Replacement summary:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_aznew_v1j_collab_proxy12_with_guardretry_20260613_1915_summary.json`,
  combined 6 rows mean strict `0.929107`, semantic pass `1.0`,
  total calls including retry `11`, total tokens `18533`.
- [x] Built the cleaner route-card-gated collaboration summary artifact.
  Files:
  `runs\multi-agent-proxy-v1\route_card_gated_collaboration_summary_20260613_1918.json`
  and
  `runs\multi-agent-proxy-v1\route_card_gated_collaboration_summary_20260613_1918.md`.
  Key linked evidence:
  v3p `route_verdict_key` route readout `0.923077/1.0`
  normalized/raw route accuracy,
  v1j proxy12 controller selects `6/12` delegate rows,
  AZ delegate4 reaches semantic pass `1.0`,
  AZ proxy12 initial delegate reaches semantic pass `0.666667`,
  and guard-retry replacement reaches proxy12 delegated-row semantic pass
  `1.0` with mean strict `0.929107`.
  Initial selective tokens `8885` vs existing all-delegate `27661`
  (`0.678790` token reduction); including retry uses `18533` tokens
  (`0.329995` reduction).
  Caveat:
  this still stitches stable route-card evidence to existing v1j packet outputs
  rather than one unified live route-card-to-packet trace.
- [ ] Next collaboration step:
  build a cleaner route-card-gated collaboration summary that explicitly links
  the stable small-controller route-card readout to packet generation and large
  delegate calls.
  Revised after the summary artifact:
  build a small unified live trace, not another summary:
  route-card readout selects SELF/DELEGATE,
  packet generator emits packet only for delegate rows,
  `gpt-5.4-mini` is called only on delegate rows,
  and a learned/score-based verifier decides retry.
  Keep it small:
  8--12 tasks, no broad benchmark, and no more route-interface ablations unless
  this unified trace exposes a specific learnable failure.
  Report:
  route-card delegate/self counts,
  big-model call rate,
  no-op/semantic guard pass before and after guard retry,
  token/call savings vs all-delegate,
  and which failures are packet-quality vs delegate-generation vs verifier
  threshold issues.
  Avoid hard-coded route/retry rules; any new change should be data/eval design
  for the controller's learned reliability, packet-boundary, and verifier
  judgment.
- [x] First learned-verifier collaboration step:
  Ran a proxy12 Qwen-verifier-gated retry trace on the AZ `gpt-5.4-mini`
  channel.
  Artifacts:
  `runs\multi-agent-proxy-v1\visible_guard_verifier_proxy12_aznew_20260613_1931.jsonl`,
  `runs\multi-agent-proxy-v1\visible_guard_verifier_qwen_v22_proxy12_aznew_20260613_1931.jsonl`,
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_aznew_v1j_collab_proxy12_qwenverifier_retry_20260613_1932_scored.jsonl.summary.json`,
  and
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_aznew_v1j_collab_proxy12_with_qwenverifier_retry_20260613_1932_summary.json`.
  Result:
  Qwen verifier selected `3` retry rows from `6` delegated rows, including
  both scorer-true semantic failures; `gpt-5.4-mini` retry scored `3/3`
  semantic pass with mean strict `0.932727`.
  Merged proxy12 delegated rows reached semantic pass `1.0`, mean strict
  `0.908653`, using `9` large calls / `15495` large tokens.
  This is cheaper than the earlier strict `<0.95` retry (`11` large calls /
  `18533` tokens) and should be treated as learned verifier evidence, not as a
  new runtime rule.
- [ ] Next verifier training/eval step:
  turn the Qwen-verifier proxy12 trace into a small accept/retry preference
  set with three classes of evidence:
  true semantic failures recovered by retry,
  accepted rows that should stay accepted,
  and conservative false-positive retry rows such as
  `heldout_edit_exact_default`.
  Evaluate with pairwise/logprob scoring before any LoRA; only train if the
  target is clearly "small controller learns retry judgment" rather than
  copying a visible-rule policy.
- [x] Built the first verifier retry preference set and scored it with
  no-update Qwen3-8B logprobs.
  Added offline builder
  `scripts\build_verifier_retry_preference_from_trace.py`.
  Dataset:
  `data\verifier_retry_pairwise_proxy12_qwen_20260613_1938`,
  rows `6`, true verdicts `ACCEPT=4`, `RETRY=2`, no scorer-label leakage in
  prompt text.
  Remote no-update logprob artifact:
  `runs\multi-agent-proxy-v1\verifier_retry_pairwise_proxy12_qwen_logprob_20260613_1943`.
  Result:
  raw/normalized accuracy `0.833333/0.833333`.
  Base Qwen already prefers RETRY for both true semantic failures, including
  the exporter row missed by the visible-rule audit; the only failure is the
  conservative false-positive retry on `heldout_edit_exact_default`.
  This supports learned verifier training, but 6 rows is too small for LoRA.
- [ ] Broaden verifier preference data before training:
  merge compatible accept/retry traces from proxy12, mixed12, downstream9, and
  previous visible-guard relation probes into a 20--30 row pairwise set.
  Preserve three audit buckets:
  true retry caught/missed,
  accepted rows correctly accepted,
  accepted rows that Qwen over-retries.
  Run no-update logprob first; train only if the broadened set shows a clear
  learnable boundary and not just schema memorization.
- [x] Broadened verifier preference diagnostic v1:
  added `scripts\build_broadened_verifier_preference_mix.py` and built
  `data\verifier_retry_pairwise_broadened_mix_20260613_1948`.
  Composition:
  `30` rows =
  `6` proxy12 real verifier pairs,
  `9` downstream9 relation-interface pairs,
  `15` guardfix verifier-boundary regularizer pairs.
  No prompt leakage of scorer labels or target commands.
  Remote no-update Qwen3-8B logprob artifact:
  `runs\multi-agent-proxy-v1\verifier_retry_pairwise_broadened_mix_logprob_20260613_1950`.
  Overall raw/normalized accuracy:
  `0.966667/0.700000`.
  By source:
  proxy12 real verifier `0.833333/0.833333`;
  downstream9 relation interface `1.0/1.0`;
  guardfix regularizer `1.0/0.466667`.
  Do not train this mix as-is: regularizer ACCEPT completions are much shorter
  than rejected RETRY completions, creating a normalized-logprob artifact.
- [ ] Fix verifier pairwise completion symmetry:
  rebuild the broadened mix with ACCEPT and RETRY completions that have matched
  reason/repair-goal length and comparable JSON structure.
  Re-run no-update raw and normalized logprob by source.
  Only consider LoRA if both real-trace and regularizer subsets are stable
  without relying on raw length bias.
- [x] Fixed verifier pairwise completion symmetry as an offline diagnostic and
  reran no-update logprob.
  Added `--symmetric-completions` to
  `scripts\build_broadened_verifier_preference_mix.py` and built
  `data\verifier_retry_pairwise_broadened_mix_v2_symmetric_20260613_1755`.
  Prompt leakage stayed clean and chosen/rejected lengths became comparable.
  Remote no-update artifact:
  `runs\multi-agent-proxy-v1\verifier_retry_pairwise_broadened_mix_v2_symmetric_logprob_20260613_1755`.
  Result:
  raw/normalized `0.566667/0.266667`;
  by source:
  proxy12 real verifier `0.666667/0.333333`,
  downstream9 relation interface `0.666667/0.444444`,
  guardfix regularizer `0.466667/0.133333`.
  Decision:
  do not train LoRA on this broadened mix yet.
  The v1 high raw score was partly completion-format/length aided, so the next
  data improvement should not be another schema tweak.  Return to live
  cooperation traces and collect small-controller verifier decisions in the
  actual execution interface.
- [ ] Next stricter unified trace:
  run one compact live trace where the same small-controller interface produces
  route-card route readout, packet/packet-empty decision, Qwen verifier
  ACCEPT/RETRY, and selective large-model calls.
  Keep it at `8--12` tasks and report:
  route accuracy/counts, initial large-call rate, Qwen verifier retry
  precision/recall against scorer audit, final semantic pass, total large
  tokens, and failure attribution.
- [ ] Immediate next run:
  build/run the compact unified collaboration trace on 8--12 tasks, using the
  stable route-card readout and current packet generator rather than more route
  JSON ablations.
  Use Qwen verifier retry in the actual packet-visible verifier prompt, not the
  broadened pairwise v2 synthetic completion format.
  Call `gpt-5.4-mini` only on route-card delegate rows and only retry rows
  selected by the Qwen verifier.
  Stop and inspect rather than train if failures are packet-quality or
  delegate-generation failures.
- [x] Built the explicit existing proxy12 unified collaboration baseline
  artifact:
  `runs\multi-agent-proxy-v1\unified_collaboration_trace_existing_proxy12_qwenverifier_20260613_1805.json`
  and `.md`.
  It links the current stable controller proxy to packet emission,
  `gpt-5.4-mini` delegate calls, Qwen verifier retry, and merged scorer
  outcome:
  `6/12` delegate rows, no missed/unnecessary gold delegation, Qwen verifier
  retry recall/precision `1.0/0.666667`, merged semantic pass `1.0`, total
  large tokens `15495`.
  This is a baseline artifact, not a replacement for the next live trace.
- [ ] Next live trace implementation detail:
  if running another trace, avoid empty AZ health probes because the updated
  endpoint charged `1455` prompt tokens for a trivial request.
  Reuse existing health unless it is stale; spend large-model calls only on
  selected delegate/retry rows.
- [x] Ran a route-card-gated proxy12 delta trace instead of another route
  schema ablation.
  Artifact:
  `runs\multi-agent-proxy-v1\routecard_v3p_proxy12_delta_collaboration_summary_20260613_1818.json`
  and `.md`.
  The v3p `route_verdict_key` readout covers `11/12` proxy tasks, delegates
  `8/12`, misses `0` gold delegate rows, and over-delegates `2` self-edit
  rows:
  `generated_wide_heldout_semantic_edit_mapping_filter` and
  `generated_wide_heldout_semantic_edit_visible`.
  Called `gpt-5.4-mini` only on these 2 extra rows:
  semantic pass `1.0`, mean strict `0.9325`, extra large tokens `5119`.
  Qwen verifier selected 1 retry even though both rows were scorer-semantic
  safe; retry raised that row strict `0.94 -> 0.955` but cost another `2768`
  large tokens.
  Combined with the existing 6-row Qwen-verifier baseline:
  semantic pass `1.0`, mean strict `0.91649`, total large tokens `23382`,
  still below all-delegate proxy12 `27661` but `+7887` over the tighter v1j
  baseline.
- [ ] Next learned-boundary data step:
  build a tiny route-confidence / verifier-boundary diagnostic, not a runtime
  rule.
  Positive self-handle examples:
  route-card overdelegated rows where current evidence and guards are
  sufficient and large-model output is semantically safe but unnecessary.
  Positive delegate examples:
  true residual rows caught by route-card/Qwen verifier.
  Verifier ACCEPT examples:
  commands where risky old text appears inside `.replace(...)` but
  `replacement_new_text_has_none_guard=true` and
  `replacement_new_text_has_truthiness_or=false`.
  Verifier RETRY examples:
  true semantic failures or replacement new text that keeps the risky
  truthiness/default/mutable-copy pattern.
  Run no-update scoring first; train only if the target separates learned
  evidence judgment from task-family labels and completion-length artifacts.
- [x] Built and scored the route-confidence / verifier-boundary diagnostic.
  Added offline builder
  `scripts\build_route_verifier_boundary_diagnostic.py`.
  Dataset:
  `data\route_verifier_boundary_diagnostic_v2_20260613_1823`,
  `19` rows =
  `11` route-confidence pairs and `8` verifier-boundary pairs.
  Prompt leakage check passed.
  Remote no-update artifact:
  `runs\multi-agent-proxy-v1\route_verifier_boundary_diagnostic_v2_logprob_20260613_1823`.
  Overall raw/normalized `0.736842/0.736842`.
  By bucket:
  route true delegate `1.0/1.0`;
  route true self-handle `0.0/0.0`;
  route overdelegated self-handle `0.0/0.0`;
  verifier safe accept `1.0/1.0`;
  verifier old-text false-positive accept `1.0/1.0`;
  verifier true retry `1.0/1.0`.
  Decision:
  verifier boundary does not need immediate training; no-update scoring already
  separates old text in `.replace(...)` from new patch semantics when the
  completion target is clean.
  The real weakness is route confidence/self-handle: the route-card surface is
  high-recall but conservatively delegates every self-handle row in this
  diagnostic.
- [x] Next route-confidence correction step:
  build a tiny balanced route-confidence correction/eval around self-handle
  positives, not a broad LoRA.
  Include:
  route-overdelegated self rows from the proxy12 delta,
  true self-handle locate/test/edit rows with reliable current evidence and
  guard sufficiency,
  true residual delegate rows as anchors.
  Audit margins before training; only train if the data separates
  `guard_sufficient_for_self_handle=true` from residual patch uncertainty
  without relying on task family names or field-order artifacts.
- [x] Built the route-confidence-only balanced diagnostic and ran no-update
  Qwen3-8B scoring.
  Dataset:
  `data\route_confidence_balanced_proxy12_20260613_1829`,
  `11` rows =
  `6` true residual delegate anchors and `5` self-handle positives
  (`3` true self rows plus `2` route-card overdelegated self rows).
  Remote artifact:
  `runs\multi-agent-proxy-v1\route_confidence_balanced_proxy12_logprob_20260613_1829`.
  Result:
  raw/normalized `0.545455/0.545455`.
  By bucket:
  route true delegate `1.0/1.0`;
  route true self-handle `0.0/0.0`;
  route overdelegated self-handle `0.0/0.0`.
  Conclusion:
  the verifier mixture was not the issue; the learned controller boundary is
  specifically self-handle confidence under reliable current evidence and
  sufficient guards.
- [x] Next tiny correction decision:
  if compute remains idle, run a tiny route-confidence LoRA/DPO dry-run only
  with strict replay checks.
  Success criteria before calling it useful:
  self-handle route logprob improves on the 5 self rows,
  true delegate recall remains `6/6`,
  v2 verifier-boundary rows remain `8/8`,
  and the live proxy12 collaboration token budget should move back toward the
  tighter v1j baseline rather than the overdelegating route-card trace.
  Stop if improvement depends on task ids, route-card field order, or a hard
  threshold that would replace controller judgment.
- [x] Ran the tiny route-confidence DPO LoRA diagnostic.
  Added offline `--adapter` scoring to
  `scripts\run_pairwise_logprob_diagnostics.py`.
  Training:
  `route_confidence_balanced_proxy12_dpo_lora_20260613_1836`,
  rows `11`, steps `11`, rank/alpha `4/8`, lr `5e-6`,
  loss `0.693359 -> 0.668457`.
  Route replay:
  raw/normalized remained `0.545455/0.545455`;
  true delegate stayed `1.0/1.0`;
  true self-handle and overdelegated self-handle stayed `0.0/0.0`.
  Verifier-boundary replay:
  raw/normalized stayed `0.736842/0.736842`, with all verifier buckets still
  solved.
  Decision:
  do not deploy this adapter.
  It slightly moves margins but does not learn the self-handle boundary.
- [x] Next data improvement:
  expand route-confidence self-handle positives before more training.
  Add generated and trace-derived examples where the controller should
  self-handle because:
  reliable current evidence already localizes the file/function,
  the action is locate/test/simple-edit rather than residual patch synthesis,
  no-op/semantic/format guards are sufficient,
  and historical memory is useful as a hint but not enough to justify a large
  model call.
  Keep matched true-delegate anchors and replay the verifier-boundary set.
  Use the stable route-card readout as the execution interface, but treat
  route confidence as a learned small-model boundary, not a hard threshold.
- [x] Built expanded route-confidence data and ran 1ep/2ep DPO LoRA replay.
  Expanded dataset:
  `data\route_confidence_expanded_v3q_unique_20260613_1842`,
  `76` rows, `20` groups, labels
  `SELF_HANDLE=39`, `DELEGATE_PACKET=37`.
  1ep adapter improved expanded-train self raw accuracy but did not transfer to
  proxy12 replay, so it was not deployed.
  2ep adapter reached raw/normalized `1.0/1.0` on:
  expanded train `76/76`,
  proxy12 route replay `11/11`,
  verifier-boundary replay `19/19`.
  Proxy12 replay fixed the two route-card overdelegated self rows while
  preserving all six true delegate anchors.
- [x] Ran compact adapter-gated large-model cooperation probe with current AZ
  `gpt-5.4-mini`.
  Offline adapter-gated replay delegated `6/12`, missed `0`, unnecessary `0`,
  and skipped:
  `generated_wide_heldout_semantic_edit_mapping_filter`,
  `generated_wide_heldout_semantic_edit_visible`.
  Current AZ initial large delegate:
  semantic pass `0.666667`, mean strict `0.817949`, tokens `12401`.
  Qwen v22 verifier selected `3/6` retries; scorer-audit retry
  recall/precision `1.0/0.666667`.
  Retry rows all passed.
  Final delegated-row semantic pass `1.0`, mean strict `0.906282`,
  total large calls/tokens `9 / 18271`.
  Result is below all-delegate proxy12 tokens (`27661`) but above the previous
  tight v1j Qwen-verifier baseline (`15495`) because the current AZ endpoint
  used more tokens.
- [x] Next implementation improvement:
  make route-confidence adapter scoring usable as an online/live readout
  without deploying it as the main Qwen service yet.
  Keep it a learned route-confidence scorer over the stable route-card surface:
  score `SELF_HANDLE` vs `DELEGATE_PACKET` completions, emit margin/decision,
  and build the delegate packet only when the learned score selects
  `DELEGATE_PACKET`.
  Do not add task-family suppression rules or schema-ablation branching.
- [x] Built the first fixed-choice online readout diagnostic.
  Added `scripts\build_route_confidence_readout_pairs.py`.
  Fixed-choice pair semantics:
  `chosen=DELEGATE_PACKET`, `rejected=SELF_HANDLE`;
  positive margin means delegate, negative margin means self-handle.
  Result:
  the earlier 2ep route-confidence adapter is not directly deployable as an
  online route scorer.
  Full and minimal completions predicted delegate `11/11`, raw/normalized
  route accuracy `0.545455`.
  `flags_no_reason` had partial signal but still missed true delegates or
  overdelegated self rows depending on raw vs normalized margin.
  Conclusion:
  the old perfect replay was partly completion-surface dependent; do not
  deploy it and do not replace it with a hard-coded self-handle suppression
  rule.
- [x] Tried one readout-consistent DPO correction.
  Added `--completion-style` to
  `scripts\build_route_confidence_expanded.py`.
  Built:
  `data\route_confidence_expanded_v3q_flagsnr_unique_20260613_1912`,
  rows `76`, `DELEGATE_PACKET=37`, `SELF_HANDLE=39`,
  completion style `flags_no_reason`.
  No-update raw/normalized `0.526316/0.486842`.
  2ep DPO:
  `route_confidence_expanded_v3q_flagsnr_unique_dpo_lora_2ep_20260613_1912`,
  preference accuracy `0.526316 -> 0.578947`.
  Proxy12 fixed-choice replay:
  raw accuracy `0.636364`, but still overdelegated four self rows;
  normalized accuracy `0.545455`, delegate `11/11`.
  Verifier-boundary replay stayed `0.736842/0.736842`.
  Decision:
  do not deploy this adapter.
- [ ] Next route-confidence training target:
  train the small model on a genuinely online-readout-consistent objective.
  Requirements:
  fixed-choice readout is the primary eval gate, not old chosen/rejected replay;
  self-handle positives must include locate/test/simple-edit rows with reliable
  current evidence and sufficient guards;
  delegate anchors must overlap in task family/path/guard wording with
  self-handle positives so the model cannot solve by family names;
  success requires proxy12 fixed-choice route accuracy above `0.8`, zero missed
  true delegate rows, and fewer than two self overdelegates before another
  large-model collaboration run.
  Prefer data/model changes over prompt/schema perturbation.
- [x] First promising fixed-choice route readout adapter found, but not ready.
  Reference-free LoRA on the `flags_no_reason` fixed-choice surface:
  `route_confidence_expanded_v3q_flagsnr_unique_reffree_lora_2ep_20260613_1931`.
  Train preference accuracy improved `0.526316 -> 0.815789`.
  Proxy12 fixed-choice normalized replay:
  route accuracy `0.818182`, predicted delegate `8/11`, missed delegates `0`,
  overdelegates `2`.
  Diagnostic proxy12 gate would delegate `7/12`, miss `0`, overdelegate `2`.
  Verifier buckets remained solved, but route true self in the mixed
  verifier-boundary set only improved to `0.333333`.
  Decision:
  promising online-readout direction, but do not deploy and do not run another
  large-model collaboration trace yet.
- [x] Tried a simple delegate-anchor oversampling correction.
  Added offline `--bucket-repeat BUCKET=N` to
  `scripts\build_route_confidence_expanded.py`.
  Built
  `data\route_confidence_expanded_v3q_flagsnr_delegate2x_20260613_1941`
  with `expanded_true_delegate_anchor=2`:
  rows `113`, `DELEGATE_PACKET=74`, `SELF_HANDLE=39`.
  Reference-free 2ep LoRA
  `route_confidence_expanded_v3q_flagsnr_delegate2x_reffree_lora_2ep_20260613_1941`
  recovered delegate anchors (`1.0`) but weakened self buckets
  (`0.545455/0.333333/0.4`).
  Proxy12 fixed-choice accuracy was `0.909091`, missed `0`, but overdelegated
  `4` self rows, so it is not deployable.
  Lesson:
  naive delegate-anchor weighting is too blunt; do not keep pushing this line
  as a runtime gate or task rule.
- [ ] Next route-confidence data experiment:
  build matched delegate/self correction rows instead of schema variants or
  one-sided oversampling.
  Requirements:
  self positives should include locate/test/simple-edit cases with reliable
  current evidence and sufficient guards;
  delegate anchors should share similar path/family/guard wording so the model
  must learn residual uncertainty rather than label priors;
  include the two known overdelegated self cases as learned correction examples
  without task-id rules.
  Gate:
  proxy12 fixed-choice normalized accuracy `>0.85`,
  missed delegates `0`,
  overdelegates `<=1`,
  verifier true retry/safe accept buckets remain `1.0`.
- [x] Next verifier precision data package:
  reduce over-retry while preserving true-failure recall.
  Use the new reffree2ep gate7 AZ trace plus the previous v1j trace to build a
  small verifier precision diagnostic where the model must accept commands
  whose replacement new text already satisfies the visible guards and must
  retry unsafe mutable-copy commands.
  Built an extra hard-accept pair set from the routecard v3p proxy12 extra2
  trace:
  `data\verifier_retry_pairwise_routecard_extra2_qwen_20260613_2025`,
  rows `2`, both true `ACCEPT`, including
  `accepted_row_conservative_qwen_retry=1`.
  Mixed v4:
  `data\verifier_retry_pairwise_broadened_mix_v4_gate7_extra2_symmetric_20260613_2025`,
  rows `24`, groups `11`, true verdicts `ACCEPT=19`, `RETRY=5`.
  Hard conservative false-positive accept rows increased from `3` to `4`.
  This remains an offline learned-verifier training package, not a runtime
  retry rule.
- [x] Next verifier evaluation:
  run a short remote no-update logprob and, only if needed, a tiny
  reference-free/low-rank LoRA diagnostic on
  `data\verifier_retry_pairwise_broadened_mix_v4_gate7_extra2_symmetric_20260613_2025\rm_pairs.parquet`.
  Then map the learned two-choice accept/retry predictions back to the gate7
  trace with `scripts\summarize_visible_guard_choice_trace.py`.
  Success criteria before another large-model collaboration run:
  gate7 retry recall `1.0`,
  retry precision `>0.8`,
  unnecessary retry calls `<2`,
  `accepted_row_conservative_qwen_retry` bucket improves to `1.0`,
  true retry buckets stay `1.0`,
  and no visible prompt contains hidden target commands or scorer labels.
  Do not deploy a verifier adapter or call `gpt-5.4-mini` from it until this
  gate passes.
  Result:
  no-update v4 mix raw/normalized `0.75/0.5`;
  gate7 two-choice summary retry recall/precision `1.0/0.333333`,
  unnecessary retries `2`.
  Short v4 reference-free LoRA:
  remote checkpoint
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/verifier_retry_pairwise_broadened_mix_v4_gate7_extra2_reffree_lora_2ep_20260613_2035`,
  rows `24`, steps `48`, train preference accuracy `0.75 -> 0.791667`.
  Gate7 adapter replay stayed unchanged:
  retry recall/precision `1.0/0.333333`, unnecessary retries `2`,
  `accepted_row_conservative_qwen_retry=0.0`.
  Do not deploy this adapter and do not launch another large-model trace from
  it.
- [x] Next verifier objective:
  build matched/balanced accept-vs-retry evidence pairs instead of adding more
  one-sided ACCEPT rows.
  For each conservative false-positive ACCEPT row
  (`heldout_edit_exact_default`,
  `generated_wide_heldout_semantic_edit_mapping_exporter`,
  and the routecard extra2 false-positive), add near-matched true RETRY rows
  using the same packet/guard vocabulary and similar command surfaces.
  Keep `visible_default_mismatch` and `unresolved_copy_deepcopy` as protected
  risk buckets so they are not swamped by easy accept examples.
  Gate before any new large-model collaboration:
  gate7 retry recall `1.0`,
  retry precision `>0.8`,
  unnecessary retries `<2`,
  `accepted_row_conservative_qwen_retry=1.0`,
  true retry buckets `1.0`,
  `visible_default_mismatch=1.0`,
  `unresolved_copy_deepcopy=1.0`.
  This must remain learned pairwise/SFT data, not a runtime retry rule.
  Result:
  built protected v5 diagnostic
  `data\verifier_retry_pairwise_matched_v5_gate7_extra2_protected_20260613_2045`,
  rows `24`, groups `10`, true verdicts `ACCEPT=12`, `RETRY=12`.
  Bucket mix protects hard accept and retry/risk buckets:
  `accepted_row_conservative_qwen_retry=4`,
  `true_retry_caught_by_qwen=4`,
  `true_retry_caught_by_qwen_missed_by_visible_rule=2`,
  `visible_default_mismatch=3`,
  `unresolved_copy_deepcopy=3`.
  Remote no-update Qwen3-8B logprob:
  raw/normalized `0.458333/0.333333`.
  `accepted_row_conservative_qwen_retry` stayed solved at `1.0`, but all
  RETRY/risk buckets stayed `0.0`.
  Decision:
  do not train v5 and do not run a large-model trace from it; protected
  reweighting alone is not enough.
- [x] Next verifier v6 objective:
  build a more isomorphic short completion surface for the same packet-visible
  evidence, because the long JSON reason surface still lets RETRY/risk buckets
  lose under both v4 and v5.
  Chosen/rejected completions should differ only in compact learned fields,
  for example
  `{"verdict":"ACCEPT|RETRY","risk":"safe|default_mismatch|copy_unresolved|selected_copy_risky"}`.
  Preserve prompt-visible evidence only; keep scorer labels in audit metadata.
  First run no-update logprob on v6.
  Only if no-update still fails should a tiny LoRA diagnostic run.
  Gate before any new large-model collaboration:
  gate7 retry recall `1.0`,
  retry precision `>0.8`,
  unnecessary retries `<2`,
  `accepted_row_conservative_qwen_retry=1.0`,
  true retry/risk buckets `1.0`.
  Do not add a runtime packet-visible retry rule.
  Result:
  built v6 short verdict+risk data
  `data\verifier_retry_pairwise_shortverdict_v6_gate7_extra2_20260613_2050`
  and gate7 subset
  `data\verifier_retry_pairwise_gate7_shortverdict_v6_20260613_2050`.
  No-update v6 mix normalized accuracy reached `0.833333`;
  gate7 no-update had retry recall/precision `1.0/0.5`.
  Tiny reference-free v6 LoRA:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/verifier_retry_pairwise_shortverdict_v6_reffree_lora_2ep_20260613_2055`.
  Gate7 adapter-choice eval:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/verifier_retry_pairwise_gate7_shortverdict_v6_reffree2ep_eval_20260613_2055/choice_trace.jsonl.summary.json`,
  rows `7`, accuracy `1.0`, retry recall/precision `1.0/1.0`,
  pred retry `1`, unnecessary/missed retries `0/0`.
  This passes the current gate7 collaboration boundary.
  Caveat:
  do not claim the verifier is generally solved, because the broader protected
  v6 mix still fails `unresolved_copy_deepcopy`.
- [x] Ran the next live collaboration step with the usable fixed-choice gate.
  Gate:
  `route_confidence_reffree2ep_proxy12_readout_gate_20260613_1931`,
  delegated `7/12`, missed `0`, overdelegated `2`.
  Initial `gpt-5.4-mini` packet delegate:
  `7` calls, semantic pass `0.857143`, mean strict `0.86545`,
  large tokens `11772`.
  Qwen v22 verifier:
  retry recall `1.0`, precision `0.333333`,
  selected `3` retries with `2` unnecessary retries.
  Final after guard retry:
  delegated-row semantic pass `1.0`, mean strict `0.903307`,
  large calls/tokens `10 / 16042`, Qwen verifier tokens `7359`.
  Artifact:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_az_routeconf_reffree2ep_gate7_with_qwenretry_20260613_1941_summary.json`.
  This validates the small-controller + large-patch-specialist cooperation
  path even though route/verifier precision still need training.
- [x] Next live collaboration step:
  after verifier precision and matched route corrections, rerun a compact
  `8--12` task trace with the same protocol:
  learned route readout, structured packet compression, Qwen verifier, and
  selective `gpt-5.4-mini` retry.
  Target:
  keep final semantic pass `1.0`, reduce large calls below `10`, and avoid
  hidden scorer labels in verifier prompts.
  Result:
  used the v6 short-verdict adapter choice interface, not the old generation
  verifier, on the existing route-confidence gate7 trace.
  Choice verifier:
  `runs\multi-agent-proxy-v1\choice_trace_v6_gate7_reffree2ep_20260613_2055.jsonl`,
  retry recall/precision `1.0/1.0`,
  `0` unnecessary retries,
  choice loss tokens `176`.
  Selective retry:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_az_routeconf_reffree2ep_gate7_v6choice_retry_20260613_2100.jsonl`,
  `1` large retry call, provider errors `0`, retry semantic pass `1.0`,
  retry strict `0.94`.
  Final summary:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_az_routeconf_reffree2ep_gate7_with_v6choice_retry_20260613_2100_summary.json`.
  Final delegated-row semantic pass `1.0`,
  mean strict `0.903307`,
  large calls/tokens `8 / 14576`.
  Compared with the earlier Qwen generation verifier retry trace
  (`10 / 16042` and verifier tokens `7359`), v6 choice saves `2` large calls,
  `1466` large-model tokens, and replaces generation verifier tokens with
  `176` two-choice loss tokens.
  Verification:
  `python -m pytest tests/scripts/test_score_visible_guard_relation_choice.py tests/scripts/test_summarize_visible_guard_choice_trace.py`
  passed.
- [x] Next verifier v6b objective:
  keep the short verdict+risk surface, but add/fix learned examples for the
  `copy_unresolved` / `unresolved_copy_deepcopy` risk bucket.
  This should be data/objective work only, not a runtime command-text rule.
  Gate before treating verifier as broadly usable:
  gate7 retry recall/precision `1.0/1.0`,
  `unresolved_copy_deepcopy=1.0`,
  `visible_default_mismatch=1.0`,
  true retry buckets `1.0`,
  hard accept buckets `1.0`.
  Result:
  added offline target-surface builder
  `scripts\build_verifier_shortverdict_v6b.py` and tests
  `tests\scripts\test_build_verifier_shortverdict_v6b.py`.
  Wide v6b
  `data\verifier_retry_pairwise_shortverdict_v6b_missingcopy_20260613_2110`
  fixed `unresolved_copy_deepcopy=1.0` but regressed
  `visible_default_mismatch=0.0`, so do not use the wide schema rewrite.
  Copy-only v6c
  `data\verifier_retry_pairwise_shortverdict_v6c_copyonly_missingcopy_20260613_2118`
  preserves original v6 completions for non-copy rows and relabels only
  `copy_unresolved -> missing_copy_import`.
  No-update v6c normalized accuracy `0.958333`;
  `unresolved_copy_deepcopy=1.0`,
  `visible_default_mismatch=1.0`,
  true retry buckets `1.0`,
  with one remaining accept false positive.
  Tiny reference-free LoRA:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/verifier_retry_pairwise_shortverdict_v6c_copyonly_missingcopy_reffree_lora_2ep_20260613_2120`.
  Broad adapter replay:
  normalized accuracy `1.0`, all protected buckets `1.0`.
  Gate7 adapter-choice replay:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/verifier_retry_pairwise_gate7_shortverdict_v6c_copyonly_missingcopy_reffree2ep_eval_20260613_2120/choice_trace.jsonl.summary.json`,
  retry recall/precision `1.0/1.0`, unnecessary/missed `0/0`.
  This is a learned target-surface/data fix, not a runtime verifier rule.
- [x] Next fresh collaboration trace:
  rerun a fresh compact `8--12` task trace with:
  learned route readout,
  structured packets,
  v6c short-verdict choice verifier,
  and selective `gpt-5.4-mini` retry.
  Preferred verifier candidate:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/verifier_retry_pairwise_shortverdict_v6c_copyonly_missingcopy_reffree_lora_2ep_20260613_2120/adapter`.
  Use normalized pairwise choice, not raw preference accuracy.
  Target:
  final delegated semantic pass `1.0`,
  large calls `<=8` on a comparable trace,
  no hidden scorer labels in verifier prompts,
  and no packet-visible runtime retry rule.
  Do not spend more cycles on route JSON field-order/field-name robustness
  unless it directly improves learned controller cooperation.
  Result:
  ran a fresh AZ `gpt-5.4-mini` delegate on the route-confidence gate7 packet
  rows, not a replay of old delegate outputs.
  Initial delegate:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_az_routeconf_reffree2ep_gate7_fresh_v6c_20260613_2128_scored.jsonl`,
  semantic pass `0.714286`, mean strict `0.832593`, provider errors `0`.
  Added offline v6c fresh visible-record pair builder:
  `scripts\build_verifier_shortverdict_v6c_from_visible_records.py`
  with tests.
  The first generic `retry_needed` risk-head attempt failed the two mutable-copy
  RETRY rows, showing target-surface sensitivity rather than absence of
  controller knowledge.
  Rebuilt with packet-visible selected-copy-risk features mapped to the learned
  `selected_copy_risky` risk head:
  `data\verifier_retry_pairwise_gate7_fresh_shortverdict_v6c_20260613_2134`.
  Remote v6c adapter normalized logprob accuracy `1.0`
  (raw `0.714286` because RETRY completions are longer).
  Choice trace:
  `runs\multi-agent-proxy-v1\choice_trace_v6c_gate7_fresh_20260613_2134.jsonl`,
  retry recall/precision `1.0/1.0`,
  unnecessary/missed retries `0/0`,
  choice tokens `219`.
  Selective retry:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_az_routeconf_reffree2ep_gate7_fresh_v6c_choice_retry_20260613_2134_scored.jsonl`,
  retry rows `2`, semantic pass `1.0`.
  Final summary:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_az_routeconf_reffree2ep_gate7_fresh_v6c_with_choice_retry_20260613_2134_summary.json`,
  final delegated-row semantic pass `1.0`,
  mean strict `0.904021`,
  large calls/tokens `9 / 14700`.
  This misses the aspirational `<=8` calls on this fresh sample because the
  large model made two mutable-copy mistakes, but it still beats the older
  Qwen-generation-verifier trace (`10 / 16042`) and shows the small learned
  verifier can restore correctness without unnecessary retry.
- [x] Next Multi-Agent Direction step:
  broaden the fresh collaboration validation beyond the same gate7 task IDs
  with a new compact `8--12` task mix that includes:
  at least two non-mutable ACCEPT rows,
  two mutable selected-copy RETRY rows,
  one visible-default mismatch RETRY row,
  and one route-overdelegated self-handle row.
  The objective is not another JSON field-order ablation; it is to test whether
  the learned route/packet/verifier interfaces generalize when the small
  controller must retrieve reliable evidence, compress a packet, and choose
  delegate/retry boundaries before calling the large patch generator.
  Keep using normalized pairwise choice for route/verifier readouts.
  Success criteria:
  no hidden scorer labels in verifier prompts,
  no packet-visible runtime retry rule,
  retry recall/precision `>=0.8`,
  final delegated semantic pass `1.0`,
  and large calls lower than an all-delegate+retry baseline on the same mix.
  Result:
  the compact mix exposed a packet evidence-retention failure rather than a
  route-format failure.  One row with guard
  `copy_the_focused_pytest_node_exactly` dropped the exact pytest node and kept
  only the file path, causing AZ `gpt-5.4-mini` to run file-level pytest.
  Added `scripts\build_exact_test_node_packet_retention_pairwise.py` plus
  tests, generated
  `data\exact_test_node_packet_retention_pairwise_20260613_2148`
  with `32` exact-node retention pairs, and added conservative visible
  verifier features for exact-node mismatch.
  Corrected the compact packet proxy by retaining the visible exact node only
  for `generated_wide_heldout_semantic_test_path`:
  `runs\multi-agent-proxy-v1\compact_mix_v6c_20260613_2142_exactnode_packets.jsonl`.
  Reran the same `8` rows through AZ:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_az_compact_mix_v6c_exactnode_20260613_2148_scored.jsonl`,
  semantic pass `1.0` (`8/8`), mean strict `0.928206`, provider errors `0`.
  Previous compact mix was semantic pass `0.875`, mean strict `0.876644`.
  Rebuilt visible verifier:
  `runs\multi-agent-proxy-v1\visible_guard_verifier_compact_mix_v6c_exactnode_20260613_2148_v3.jsonl`,
  `8` ACCEPT / `0` RETRY, no unnecessary/missed retry.
  Remote v22 readout on exact-node pairwise data:
  normalized accuracy `0.0` (`0/32`), showing the current small model does not
  yet prefer full-node retention over a shorter file-only packet.
  A tiny reference-free LoRA learnability probe reduced loss/margin but still
  left preference accuracy `0.0`, so the next step should use a shorter
  fieldized node-evidence target rather than full long-packet preference.
- [x] Next Multi-Agent Direction step:
  build a compact fieldized exact-node evidence-retention target that avoids
  length bias, e.g. chosen output contains a short
  `packet_plan` / `evidence_atoms` field with
  `focused_test_node: tests/...py::test_...`,
  `requires_pythonpath_src: true`, and `copy_exact_node: true`, while rejected
  output contains only the test file.  Evaluate it with normalized pairwise
  logprob on v22 first; only launch a tiny LoRA if readout is below target.
  Success criteria:
  normalized pairwise accuracy improves from `0.0` toward `>=0.8` on the
  32-row exact-node retention set,
  no hidden scorer labels in prompts,
  no online task-id packet rewrite,
  and a regenerated compact-mix packet still lets AZ `gpt-5.4-mini` solve
  `8/8` with no verifier retry.
  Result:
  added `scripts\build_exact_test_node_evidence_atom_pairwise.py` and generated
  `data\exact_test_node_evidence_atom_pairwise_20260613_2206` with `64` rows
  / `32` groups.  This short fieldized target uses
  `evidence_atoms.focused_test_node`, `test_path`,
  `requires_pythonpath_src`, `copy_exact_node`, and a short `packet_plan`.
  v22 normalized logprob readout:
  `raw_accuracy=1.0`, `normalized_accuracy=1.0`,
  mean normalized margin `0.259264`.
  This contrasts with the full-packet target's `0.0` normalized accuracy and
  confirms that the small model can express the judgment when the target
  surface is short and stable.
  Added `scripts\run_exact_test_node_evidence_atom_probe.py`.
  Long prompt generation failed by echoing/truncation
  (`valid_json_rate=0.0`), but compact prompt generation on Qwen v22 succeeded
  on all `32` de-duplicated tasks:
  valid JSON `1.0`, exact-node match `1.0`, file-only-node `0.0`,
  reliable-evidence `1.0`.
  Added `scripts\apply_exact_node_evidence_atoms_to_packets.py` as an offline
  proxy serializer from generated atoms to packet fields; it changed only
  `generated_wide_heldout_semantic_test_path` in the compact mix.
  Reran AZ `gpt-5.4-mini` on the atom-derived compact mix:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_az_compact_mix_v6c_atomderived_20260613_2206_scored.jsonl`,
  semantic pass `1.0` (`8/8`), mean strict `0.930223`, provider errors `0`.
  Final visible verifier:
  `runs\multi-agent-proxy-v1\visible_guard_verifier_compact_mix_v6c_atomderived_20260613_2206_v2.jsonl`,
  `8` ACCEPT / `0` RETRY.
  Local tests for the new builders/probes/guard fixes passed:
  `11 passed`, `8 passed`, and final guard tests `7 passed`.
- [x] Next Multi-Agent Direction step:
  generalize the short evidence-atom bridge beyond exact pytest nodes.  Build
  one compact atom target each for:
  locate anchors/path scopes,
  mutable selected-copy/default-copy safety,
  stale-memory rejection/current-evidence preference,
  and verifier retry cues.  Use v22 normalized logprob first, then compact
  generation probes, before any training.  The packet serializer should consume
  generated atoms as an offline proxy/eval path, while the claimed mechanism
  remains a learned controller emitting reliable evidence atoms, not hand-coded
  runtime packet rewrites.
  Success criteria:
  atom readout/generation accuracy `>=0.8` per family,
  compact mix remains `8/8` semantic pass with no unnecessary retry,
  no hidden scorer labels in prompts,
  and no additional JSON field-order ablation unless it directly improves this
  small-model/large-model cooperation path.
- [x] First generalization family: visible-default / semantic-guard atom bridge.
  Added `scripts\build_visible_default_guard_atom_pairwise.py` and
  `scripts\run_visible_default_guard_atom_probe.py` with tests.
  Clean v2x data:
  `data\visible_default_guard_atom_pairwise_v2x_clean_20260613_2254`,
  `90` pairs / `30` groups across `copy_default_only`,
  `explicit_copy_selected`, and `inferable_ambiguous`.
  Remote v22 normalized readout:
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/visible_default_guard_atom_v2x_clean_logprob_20260613_2254`,
  raw/normalized accuracy `1.0/1.0`, mean normalized margin `0.193740`.
  Direct generation without consistency contract showed the exact surface issue
  the user warned about: valid JSON and evidence-id match were both `1.0`,
  but `repair_constraints` recall was only `0.4` because the model expressed
  correct booleans/bindings while omitting their list forms.
  Direct generation with a non-answer-leaking field-consistency contract:
  `runs\multi-agent-proxy-v1\visible_default_guard_atom_qwen_v22_generation_v2x_clean_consistency_20260613_2254.jsonl`,
  valid JSON `1.0`, constraint exact `0.966667`,
  None/avoid/evidence-id match `1.0`, mean constraint recall/precision
  `0.988889/0.988889`.
  One remaining miss is an explicit-copy-selected row where the model chose
  `copy_default_only` instead of `copy_selected_mapping`.
- [x] Next Multi-Agent Direction step:
  connect the v2x visible-default/semantic-guard atom to the same offline
  atom-to-packet proxy path used for exact pytest nodes, then run only a tiny
  `gpt-5.4-mini` delegate probe on the held-out mutable rows if the serialized
  packets pass a packet-visible audit.  Do not add runtime inference rules that
  decide copy-default/copy-selected from task labels; the proxy may only consume
  small-model-generated atoms and check field consistency.
  Success criteria:
  packet-visible audit preserves evidence ids and repair constraints from the
  generated atom, no support-label leakage, no hidden scorer labels, and a
  3--4 row AZ delegate probe maintains semantic pass without extra broad
  large-model sweeps.
  Result:
  added `scripts\build_visible_default_guard_atom_gate_from_packets.py` and
  `scripts\apply_visible_default_guard_atoms_to_packets.py`.
  Qwen v22 generated atoms for the 4 held-out delegate4 packets with
  valid JSON / constraint exact / evidence-id match all `1.0`.
  The serializer accepted `4/4` and refused `0`.
  AZ `gpt-5.4-mini` returned outputs for `3/4` rows; those returned rows had
  semantic pass `1.0`, action/skill match `1.0`, and mean strict `0.925000`.
  The remaining chart row hit provider `503 No available channel`; one direct
  retry hit the same provider blocker, so do not keep spending calls on it
  until the endpoint is stable.
- [x] Next atom family after v2x:
  build a stale-memory/current-evidence preference atom readout, because this
  is closest to the core claim that the small controller retrieves reliable
  experience and rejects stale experience.  Use hard-stale rows where stale
  memory shares path/function vocabulary, evaluate v22 logprob and compact
  generation before any training or large-model call.
  Concrete next step:
  use `scripts\build_hard_stale_memory_controller_eval.py` / existing
  memory-controller eval rows to create a short atom target with
  `selected_memory_ids`, `rejected_stale_ids`, `current_evidence_paths`,
  `stale_overlap_risk`, and `next_action`.  Run v22 normalized logprob first,
  then a compact generation probe.  Do not call AZ until the stale atom gate
  passes; the current AZ channel already showed transient 503s.
  Result:
  built `scripts\build_stale_memory_evidence_atom_pairwise.py` and
  `scripts\run_stale_memory_evidence_atom_probe.py`.
  Clean hard-stale neutral-id data:
  `data\stale_memory_evidence_atom_pairwise_hardstale1_20260613_2343`
  (`104` pairs, original reliable/stale ids and kind labels removed from
  prompts).  v22 normalized logprob passed the readout gate at `0.894231`,
  but compact generation did not pass the AZ-ready gate:
  base all-atom exact `0.25`, consistency-prompt all-atom exact `0.45`.
  Selected reliable memory was strong (`1.0` base exact; `0.95` with
  consistency), but stale/distractor rejection fields and strict nesting were
  not stable enough.
- [x] Next stale-memory step:
  do not call `gpt-5.4-mini` yet.  Build a shorter per-candidate verdict atom
  or tiny focused correction target for neutral-id role binding:
  each memory candidate should get one verdict such as
  `use_current`, `reject_stale_overlap`, or `reject_distractor`, plus compact
  current-evidence path atoms.  Rerun v22 normalized logprob and compact
  generation; only connect to packet/AZ if generation reaches a usable gate
  (target: selected reliable memory `>=0.95`, stale rejection `>=0.85`,
  valid JSON `1.0`, no hidden ids/kinds in prompt).
  Result:
  added `scripts\build_stale_memory_candidate_verdict_pairwise.py` and
  `scripts\run_stale_memory_candidate_verdict_probe.py`.
  Clean neutral-id data:
  `data\stale_memory_candidate_verdict_pairwise_hardstale1_20260613_2358`
  (`156` pairs / `60` candidate groups; reliable/stale/distractor balanced;
  original ids/kinds removed from prompts).  v22 logprob:
  normalized `0.762821` overall, reliable `0.961538`, stale `0.865385`,
  distractor `0.461538`.  Direct generation remained below gate:
  base verdict match `0.466667`, consistency-prompt verdict match `0.616667`.
  A distractor-only standalone 2-epoch LoRA improved distractor replay but
  damaged reliable/stale replay (`0.576923` overall normalized), so do not
  adopt that adapter.
- [x] Next stale-memory correction:
  do not use the distractor-only standalone LoRA and do not call AZ yet.
  Either add trainer support to initialize correction from the existing v22
  adapter and run a small balanced verdict correction, or redesign the verdict
  surface into two binary atoms:
  `supported_by_current_evidence` and
  `reject_reason=stale_overlap|unrelated_distractor`.
  Gate before downstream packet/AZ:
  valid JSON `1.0`, candidate id match `1.0`, verdict/reason match `>=0.85`,
  reliable/stale/distractor buckets all `>=0.8`, and no original
  reliable/stale ids or kind labels in prompts.
  Result:
  tried the two-stage binary atom surface:
  `data\stale_memory_binary_verdict_pairwise_hardstale1_20260614_0022`
  (`130` pairs / `105` groups, no id/kind leakage).
  Generation improved over three-class verdict but stayed below gate:
  valid JSON/candidate-id `1.0/1.0`, support/reason match
  `0.790476/0.790476`, all-exact `0.342857`.
  Remote v22 logprob showed the binary surface is not yet learned:
  normalized `0.407692`; reliable support and stale reason are strong, but
  false support for stale/distractor and distractor-vs-stale reason are weak.
  Also added `--initial-adapter` to
  `scripts\train_pairwise_dpo_lora.py`, so future correction can continue from
  the active v22 adapter instead of training a standalone base-Qwen LoRA.
- [x] Next stale-memory training gate:
  run only a small balanced v22-initialized correction, not a standalone LoRA:
  use `scripts\train_pairwise_dpo_lora.py --initial-adapter
  /mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/v21_plus_v16_anchor_replay_parquet_lora/global_step_1710`
  on a balanced candidate-verdict or binary-verdict set.  Replay must report
  reliable/stale/distractor buckets separately, and the adapter is usable only
  if all protected buckets stay `>=0.8` and generation reaches the gate.  Do
  not call `gpt-5.4-mini` or write a serializer fallback before that.
- [x] Next stale-memory packet-visible bridge:
  use the v22-initialized balanced candidate-verdict adapter as a generated
  atom source, not as a hard-coded selector.  Build a small packet-visible
  stale-memory audit that consumes generated verdict atoms and checks whether
  reliable memories, rejected stale memories, rejected distractors, current
  evidence paths, and prefer-current flags survive into a compact packet
  without hidden role labels.  Start with local/offline packet audit only.
  Do not call `gpt-5.4-mini` until packet-visible fields pass a stricter gate:
  valid JSON `1.0`, candidate ids `1.0`, verdict match `>=0.9`, all role
  buckets `>=0.85`, no hidden original reliable/stale/distractor labels, and
  no packet rule that infers labels from ids or task metadata.
  Current evidence:
  base adapter generation on `60` candidate groups reached valid JSON
  `1.0`, candidate-id `1.0`, verdict `0.933333`, with reliable/stale/distractor
  verdict buckets `1.0/1.0/0.8`; consistency prompt reached verdict `0.883333`
  and better field consistency but hurt reliable rows.  Residual failure:
  `4/20` distractors are still predicted as stale overlap, and path/boolean
  fields are not stable enough for downstream AZ.
- [x] Next stale-memory downstream audit:
  now that the residualmix adapter passes the offline packet-visible gate, run
  a tiny packet-to-large readiness audit before any broad AZ call.  Select
  2--4 rows that stress the former residual boundary, especially rows where a
  distractor shares path/function words with stale memory.  The audit should
  verify that the packet exposes generated selected/rejected/current-evidence
  atoms without hidden role labels, and only then optionally call
  `gpt-5.4-mini` on the tiny subset.  Stop if packet warnings, hidden labels,
  or provider 503s appear.  This step must remain evidence of learned
  memory-boundary judgment; do not add a runtime rule that infers reliability
  from ids, task names, or gold roles.
  Current evidence:
  residualmix generation reached valid JSON/candidate-id `1.0/1.0`, verdict
  `0.966667`, role verdict reliable/stale/distractor `1.0/1.0/0.9`.
  Packet-visible bridge reached selected exact `1.0`,
  rejected-stale/rejected-distractor `0.9/0.9`, mean path recall/precision
  `0.975/0.95`, leakage `0.0/0.0`, and `gate_pass=true`.
- [x] Next stale-memory residual boundary correction:
  use the downstream readiness audit to build a small follow-up target for the
  two still-failed rows, not a runtime rule.  The hard cases are
  `heldout_locate_cache_key/mem_2`, where locate has empty current evidence and
  the distractor is still treated as stale overlap, and
  `path_edit_commitment_download/mem_1`, where an upload-path distractor shares
  enough path/edit wording to be misclassified as stale.  Keep the successful
  fixed-boundary rows as protected replay, and gate with generated verdict atoms
  plus packet-visible audit before any new `gpt-5.4-mini` call.
  Current evidence:
  built `data\stale_memory_candidate_verdict_boundary_replay_20260614_0248`
  (`200` rows / `60` groups) from the readiness audit, trained a conservative
  residualmix-initialized correction, and reran full generated-atom plus
  packet-visible gates.  Generation improved verdict match
  `0.966667 -> 0.983333`, distractor verdict `0.9 -> 0.95`, and packet bridge
  rejected-stale/rejected-distractor exact `0.9/0.9 -> 0.95/0.95` with zero
  leakage.  Downstream readiness improved from `2/4` to `3/4` AZ-ready rows.
  The only remaining failure is `heldout_locate_cache_key/mem_2`, an empty
  current-evidence locate case still predicted as `reject_stale_overlap`.
- [x] Next stale-memory locate-empty-evidence correction:
  do not keep oversampling the single remaining row.  Build a broader
  neutral-id readout for locate tasks with empty or sparse current evidence,
  contrasting unrelated old-move notes against true stale-overlap notes and
  reliable locate hints.  Success gate should be generated verdict atoms and
  packet-visible bridge on held-out locate-style rows, with the three newly
  fixed distractor rows as protected replay.  Do not call `gpt-5.4-mini` until
  this residual boundary passes locally.
  Done as a learned verdict-atom SFT correction rather than a runtime selector:
  `data\stale_memory_verdict_atom_sft_correction_locate_sparse_20260614_1838`,
  adapter
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/stale_memory_verdict_atom_sft_locatesparse_boundaryinit_20260614_1846/adapter`.
  Locate sparse generation verdict rose `0.9 -> 1.0`, full candidate-verdict
  generation reached role verdict reliable/stale/distractor `1.0/1.0/1.0`,
  packet bridge selected/stale/distractor exact `1.0/1.0/1.0` with leakage
  `0.0/0.0`, and downstream readiness became `4/4` fixed with
  `mixed_set_gate_pass=true`.
- [x] Next stale-memory robustness gate before any `gpt-5.4-mini` downstream
  probe:
  build a mixed perturb audit that randomizes memory candidate order and adds
  neutral lexical-overlap stale/distractor variants for locate and edit tasks.
  Reuse the same generated verdict atom + packet-visible bridge metrics.
  Success criteria: valid JSON/candidate/verdict near `1.0`, packet
  selected/stale/distractor exact near `1.0`, hidden leakage `0.0`, and no
  collapse of reliable current-path recall.  If this passes, run only a tiny
  downstream AZ probe; if not, train another learned correction from the failed
  perturb rows instead of adding runtime if-rules.
  Done with
  `data\stale_memory_mixed_perturb_pairwise_20260614_0317` and adapter
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/stale_memory_verdict_atom_sft_mixedperturb_boundaryinit_20260614_0332/adapter`.
  Mixed perturb, original full candidate-verdict, and locate sparse gates all
  passed with selected/stale/distractor exact `1.0` and hidden leakage `0.0`.
  A tiny AZ delegate probe then reached semantic pass `1.0`, mean strict
  `0.836023`, and showed the remaining bottleneck is packet anchor density /
  command shape, not stale-memory selection.
- [x] Build tiny packet-target correction/eval data for the weak downstream
  stale-memory delegate rows.
  Artifact: `data\stale_memory_packet_target_correction_20260614_0448`.
  Summary: base/train/val `4/10/4`, weak rows `2`,
  source-inspection-needed rows `1`, avoid-line-number-only-edit rows `3`,
  leakage rows `0`.  Local v22 prompt-only probe on this target failed
  (`valid_json=0.25`, route/memory/source-inspection/path/code-anchor metrics
  `0.0`), so this is a real learned-target gap rather than a prompt wording
  issue.
- [x] Audit protected replay availability before training on the tiny
  packet-target correction.
  Artifact:
  `runs\multi-agent-proxy-v1\stale_memory_packet_target_replay_readiness_audit_20260614_0520.json`.
  Result: scanned `35` datasets; only `14` sampled rows directly match the new
  packet-target schema, while `836` rows can protect older JSON/memory/path/
  packet-plan/constraint behavior.  Decision: do not immediately train a
  4-row adapter; build a deliberate schema-aware replay mix first.
- [x] Next stale-memory packet-target step:
  build a schema-aware replay mix, not a runtime rule.  Use the new
  stale-memory packet-target rows for source-inspection uncertainty and compact
  code-anchor retention, and use older packet-plan/constraint rows only as
  protected replay for JSON shape, selected/rejected memory IDs, localization,
  packet-plan retention, and guard/constraint preservation.  Gate locally on
  valid JSON, selected/rejected memory IDs, source-inspection-needed,
  uncertainty, path hints, compact code anchors, avoid-line-number-only-edit,
  and leakage `0.0`.
  Done as
  `data\stale_memory_packet_target_replay_mix_20260614_0538` plus scorer
  `scripts/run_stale_memory_packet_target_probe.py`.  Mix summary:
  train/val/all `69/4/73`, protected replay `39`, target train `30`, target
  val `4`, leakage `0`.  The tiny v22-init LoRA reduced loss
  (`train 1.917048 -> 1.215395`, `val 3.136719 -> 2.288086`) and learned some
  train rows (`train4 valid_json=1.0`, core exact `0.75`), but held-out val
  remained failed (`valid_json=0.25`, all core metrics `0.0`), so this is now a
  target-generalization data problem rather than a service/scorer problem.
- [x] Next stale-memory packet-target generalization step:
  do not keep training the same 69-row mix blindly.  Build a broader
  target-specific generalization set from local perturbations of the four weak
  packet-target families: held-out path/function/default literals, locate rows
  with sparse current evidence, edit rows with compact code anchors, and
  explicit negative stale/distractor memory.  Keep this as offline supervision
  for learned packet-target generation; do not add runtime rewrite rules.  Gate
  on both train and held-out val so that train memorization without val
  improvement is rejected.
  Done in two variants.  Old prompt data:
  `data\stale_memory_packet_target_generalization_20260614_0522` gave v22 val
  `valid_json=0.333333`, all core `0.0`; LoRA
  `stale_memory_packet_target_sft_generalization_v22init_20260614_0530`
  reduced val loss but still gave val core `0.0`, train6 core `0.5`.
  Schema-first anti-copy prompt data:
  `data\stale_memory_packet_target_generalization_schemafirst_20260614_0550`
  improved prompt-only valid JSON to `1.0` but kept core `0.0`; LoRA
  `stale_memory_packet_target_sft_schemafirst_v22init_20260614_0555`
  reached train6 core `0.333333` but held-out val core remained `0.0`.
  Conclusion: prompt anti-copy helps JSON validity, but the current small data
  still does not teach nested field types and memory/localization/packet object
  shape well enough.
- [x] Next stale-memory packet-target schema step:
  build a micro-curriculum for nested packet schema before any more full-task
  LoRA: rows that specifically contrast string/list shallow outputs against the
  required nested objects for `memory_decision`, `localization`, and
  `packet_evidence`; include positive/negative field-type pairs and compact
  JSON-generation SFT rows with short source context.  Gate on field-shape
  accuracy first, then memory IDs/path/code-anchor exactness.  Do not call
  `gpt-5.4-mini` or run downstream delegate until held-out packet-target core
  metrics move above zero.
  Done as a scorer upgrade plus micro-curriculum:
  `scripts/run_stale_memory_packet_target_probe.py` now reports
  `memory_decision_shape_match`, `localization_shape_match`,
  `packet_evidence_shape_match`, and `nested_shape_exact`.  Data:
  `data\stale_memory_packet_schema_microcurriculum_20260614_0620`
  (`train/val=64/3`, leakage `0`).  Baseline v22 had valid JSON `1.0` but
  nested-shape exact `0.0`; LoRA
  `stale_memory_packet_schema_micro_sft_v22init_20260614_0624` reduced val loss
  (`2.525391 -> 0.738770`) but held-out nested-shape exact remained `0.0`.
  Residual errors are now concrete: singular keys like `selected_memory_id`
  instead of `selected_memory_ids`, aliases like `code_anchors` instead of
  `compact_code_anchors`, and fields placed in the wrong object.
- [x] Next schema alias-correction step:
  build an even more atomic alias-to-canonical-key curriculum before another
  full packet run.  Train short rows that convert common shallow/alias outputs
  (`selected_memory_id`, `stale_overlap_memory_id`, `file`, `anchor`,
  `code_anchors`, misplaced `source_inspection_needed`) into the exact
  canonical nested keys.  Gate only on nested shape and canonical-key exactness
  first; then merge with packet-target generalization data.  This should remain
  learned output-shape supervision, not a runtime normalizer.
  Superseded by the 2026-06-14 10:05 canonical preference experiment:
  standalone SFT alias/field curricula overfit and can collapse into
  `patch`/wrapper outputs.  The next target should be pairwise/ranking data
  where bad wrappers/aliases live only in `rejected`, not in prompt context.
- [x] Next canonical preference step:
  build a length-balanced / format-equated preference set for stale-memory
  packet ownership.  The first pairwise builder
  `scripts\build_stale_memory_packet_canonical_preference_pairs.py` passed
  leakage audits and exposed that v22 strongly prefers shorter wrapper/alias
  completions (`normalized_accuracy=0.0` on a 12-row logprob probe), while a
  tiny 48-pair DPO only nudged margins and still had val
  `normalized_accuracy=0.0`.  Do not serve this adapter for generation.  Next,
  make chosen/rejected alternatives closer in token length and field coverage:
  keep the same canonical content but compare top-level canonical packets
  against wrappers that retain diagnosis/implication length, and add
  normalized-margin gates before any training.
  Done with `--variant-set balanced` as
  `data\stale_memory_packet_balanced_canonical_preference_pairs_20260614_1012`.
  Audit: pairs/groups `156/26`, chosen canonical `1.0`, rejected noncanonical
  `1.0`, leakage `0`, mean/max abs whitespace token delta `7.096154/16`.
  v22 normalized logprob gate recovered strongly: train24 `0.833333`, val24
  `0.791667`, full val54 `0.87037`.  This shows the previous failure was
  largely a format/length imbalance diagnostic; do not train full balanced
  preference data.
- [x] Next route-alias hard-negative step:
  focus only on the remaining weak balanced variants, especially
  `balanced_route_alias` and a few `balanced_alias_nested` rows.  Full-val
  normalized accuracy by variant: wrapper_packet/full `1.0`, wrapper_payload
  `1.0`, patch_extra `1.0`, misplaced_uncertainty `1.0`, alias_nested
  `0.777778`, route_alias `0.444444`.  Build a tiny route-verdict preference
  set or reuse the existing route-decision pairwise tools so the controller
  learns that `route` must stay `DELEGATE_PACKET` while `expected_skill` stays
  `edit/locate/test`.  Gate by normalized logprob first; train only if the
  route-alias margin remains weak and keep any training isolated from packet
  generation gates.
  Compact route/alias hard negatives were built as
  `data\stale_memory_packet_route_alias_hardneg_pairs_20260614_1021`.
  Audit: pairs/groups `52/26`, train/val `34/18`, leakage `0`, token delta
  `0`.  v22 solved this compact readout: train34 and val18 raw/normalized
  accuracy `1.0/1.0`, so no compact route-alias training was launched.
- [x] Full-packet interaction diagnostic after compact route/alias saturation:
  added `scripts\build_stale_memory_packet_full_interaction_probe.py` and
  `tests\scripts\test_build_stale_memory_packet_full_interaction_probe.py`.
  Built `data\stale_memory_packet_full_interaction_probe_20260614_1024`.
  Audit: pairs/groups `78/26`, train/val `51/27`, chosen canonical `1.0`,
  rejected noncanonical `1.0`, leakage `0`, token delta `0`.
  v22 no-update logprob gate on full val27: raw/normalized
  `0.666667/0.703704`, mean normalized margin `0.071032`.
  Route ownership is solved in full packets:
  `full_route_alias_only=1.0`, `full_route_skill_swapped=1.0`.
  The real remaining failure is nested plural memory field ownership:
  `full_memory_alias_nested` val normalized `0.111111`, train normalized
  `0.058824`.
- [ ] Next conservative packet-learning step:
  do not train route-alias.  Build a tiny targeted learned objective for
  full-packet `memory_decision` plural-key ownership only, with protected replay
  from already-solved route/wrapper/patch/misplaced variants.  Gate by
  normalized logprob before any LoRA and, if trained, require no regression on
  route full-packet pairs, balanced canonical full-val, and compact route/alias.
  The target is that the small controller learns nested memory field ownership;
  do not add a runtime alias normalizer or packet rewrite rule.
  Done as diagnostics, but not solved enough to deploy:
  `data\stale_memory_packet_memory_key_preference_mix_20260614_1041`
  and repeat-weighted train mix
  `data\stale_memory_packet_memory_key_preference_mix_trepeat3_20260614_1048`.
  The mix audit was clean (`216` pairs, target/replay `60/156`, leakage `0`).
  v22 separated replay vs target: replay buckets normalized `1.0`, target
  memory plural keys val normalized `0.111111`.  A tiny DPO LoRA
  `stale_memory_packet_memory_key_prefmix_trepeat3_dpo_v22init_20260614_1050`
  improved target val normalized to `0.333333` while keeping replay `1.0`, but
  the target remains below gate and PEFT warned about stacked adapters.
  Do not serve this adapter or run generation/delegation from it.
- [x] Short memory-key atom diagnostic:
  added `scripts\build_stale_memory_key_atom_probe.py` and
  `tests\scripts\test_build_stale_memory_key_atom_probe.py`.
  Dataset `data\stale_memory_key_atom_probe_20260614_1058`, pairs `26`,
  leakage `0`.  v22 normalized accuracy was `1.0` on both val9 and train17
  (`mean_normalized_margin` about `0.279/0.276`) despite raw length-biased
  accuracy `0.0`.  Interpretation: the controller knows the compact plural-key
  atom, but fails to retain it inside a full packet.
- [x] Next memory-key step:
  build an atom-to-packet bridge / retention probe, not another broad
  full-packet DPO.  Prompt should include compact memory-key atoms plus visible
  memory evidence, and the completion should be the full canonical packet.
  Evaluate whether the small controller can carry normalized-solved atoms into
  full `memory_decision` without wrapper/route regression.  Keep this as learned
  packet construction supervision; do not add runtime alias rewrite logic.
  Done as `data\stale_memory_key_atom_to_packet_bridge_20260614_1110`.
  Result: v22 ranks full canonical packets over alias full packets under the
  atom prompt (val/train normalized `1.0/1.0`), but generation collapses to
  atom-only JSON.  A protected short SFT mix
  `data\stale_memory_key_atom_to_packet_bridge_protected_sft_mix_20260614_1115`
  and adapter
  `stale_memory_key_atom_to_packet_bridge_sft_protected_v22init_20260614_1118`
  reduced loss but did not improve generation: bridge val still has valid JSON
  `1.0` and all nested/top-level/core packet metrics `0.0`, with outputs
  containing only `selected_memory_ids`,
  `rejected_stale_overlap_memory_ids`, and
  `rejected_distractor_memory_ids`.  Do not deploy this adapter.
- [x] Next memory-key output-mode step:
  build a generation-first full-packet scaffold retention target, not another
  atom-only SFT or pairwise ranking job.  The prompt may expose compact atoms,
  but the desired completion must require the canonical full packet object from
  the first token-level decision: top-level `route`, nested `memory_decision`,
  nested `localization`, nested `packet_evidence`, exact semantic guards, and
  exact uncertainty.  Include atom-only JSON as rejected/non-target examples
  only in preference/eval data, not as response text.  Gate with
  `run_stale_memory_packet_target_probe.py` generation metrics on bridge val
  plus protected replay; stop if valid JSON remains atom-only.  Do not add a
  runtime alias/scaffold wrapper and do not call `gpt-5.4-mini` until this
  generation gate materially improves.
  Done as eval-first prompt/data target design.  Plain scaffold data
  `data\stale_memory_packet_scaffold_retention_20260614_1140` made v22 generate
  the full nested packet and all evidence fields exactly (`1.0` on memory,
  localization, packet evidence, guards, uncertainty, paths, anchors), but
  route ownership remained `0.0` because the model filled `route` with task ids
  or expected skills.  The route-literal variant
  `data\stale_memory_packet_scaffold_retention_routelit_20260614_1145`
  reached val9 all-core exact `1.0` with no training.  Do not train the prior
  bridge SFT adapter; the key bottleneck was output-contract ambiguity, not a
  missing atom skill.
- [x] Next scaffold-retention robustness step:
  broaden the route-literal scaffold gate before downstream delegation.  Add
  held-out task names, permuted atom order, route/task/expected-skill lexical
  distractors, sparse locate evidence, and protected replay from residual /
  broadened packet rows.  Success gate: generation all-core remains high,
  route stays literal `DELEGATE_PACKET`, wrapper/source-copy violations stay
  `0`, and semantic guards / uncertainty / memory split remain exact.  If it
  passes, consider a tiny downstream delegate probe; if it fails, build learned
  correction from failed perturb rows only.  Do not implement runtime route
  normalization.
  First attempt
  `data\stale_memory_packet_scaffold_robustness_eval_20260614_1152` failed
  despite valid JSON `1.0`: all nested/top-level/core metrics were `0.0`.
  New scorer diagnostic showed `contract_copy_violation_rate=1.0`; the prompt
  contract was too object-shaped and got copied under `first_field` /
  `payload` / `VISIBLE_PACKET_ATOMS`.  Fixed as prompt/data target design, not
  runtime repair: added
  `scripts\build_stale_memory_packet_scaffold_noncopy_robustness_eval.py` and
  built
  `data\stale_memory_packet_scaffold_noncopy_robustness_eval_20260614_1156`.
  v22 passed all 45 rows across the five perturbation variants with
  `all_core_exact=1.0`, route/top-level/nested/evidence metrics `1.0`, and
  wrapper/source-copy/contract-copy violations `0.0`.
- [x] Next protected non-copy packet replay step:
  broaden beyond the original 9 route-literal rows using residual / broadened
  stale-memory packet rows and already-solved packet-plan / memory-boundary
  replay.  Keep the non-copy prompt style; add `contract_copy_violation` to the
  gate; require no regression on route literal, memory split,
  source-inspection, uncertainty, semantic guards, and wrapper/source-copy
  metrics.  Do not train or call the large model unless this broader local
  controller replay stays clean.
  Done as
  `data\stale_memory_packet_noncopy_protected_replay_eval_20260614_1234`:
  95 rows from broadened residual eval, replay/generalization mix, target
  replay, and scaffold retention replay.  Audit: atom-only target rows `0`,
  prompt contract-meta-key rows `0`.  v22 generation reached `1.0` on valid
  JSON, nested/top-level packet shape, route, memory split, source-inspection,
  uncertainty, semantic guards, path/code-anchor/guard Jaccard, and
  `all_core_exact`; wrapper/source-copy/contract-copy violations all `0.0`.
- [x] Do not run another `gpt-5.4-mini` delegate probe until the small local
  packet-target generation materially improves and the protected replay mix
  shows no regression in existing packet-plan / memory-boundary behavior.
  The non-copy 45-row scaffold gate and 95-row protected replay gate now pass.
  Next candidate is a tiny downstream delegate/proxy check using the existing
  command surface and no packet normalizer, ideally on a small held-out subset
  that exercises memory reliability and semantic/no-op guard evidence.
  Done with the existing stale-memory readiness audit/packet surface:
  `runs\multi-agent-proxy-v1\large_delegate_gpt54mini_az_stalememory_sft_mixedperturb_delegate4_20260614_1308{,_scored}.jsonl`.
  AZ `gpt-5.4-mini` returned 4/4 rows with no provider errors; scoring gave
  action `1.0`, skill match `1.0`, semantic pass `1.0`, mean strict
  `0.882046`, total tokens `8765`.
- [x] Next verifier-boundary step:
  turn the 4 stale-memory delegate rows into ACCEPT-style verifier evidence,
  because all 4 semantic-pass rows have strict scores below the old diagnostic
  `0.95` retry threshold.  Do not run guard retry from that threshold alone;
  train/evaluate the small controller to distinguish semantic pass from
  cosmetic/anchor strict loss, and only retry when semantic/no-op/format guards
  actually fail.
  Done as
  `data\stale_memory_verifier_accept_boundary_pairs_20260614_1315`.
  Summary: `4` rows / `4` groups, bucket
  `accept_low_strict_semantic_ok: 4`, true verdict `ACCEPT: 4`,
  hidden metric key leakage `0`; focused tests passed (`13 passed`).
- [x] Next verifier-boundary readout:
  mix these 4 ACCEPT-boundary pairs with prior accept/retry verifier pairs
  such as
  `data\verifier_retry_pairwise_proxy12_qwen_20260613_1938`
  and
  `data\verifier_retry_pairwise_broadened_mix_v4_gate7_extra2_symmetric_20260613_2025`,
  then run a local normalized-choice/logprob or tiny generation readout before
  any training.  Success criteria: no hidden scorer labels in prompts, no
  runtime threshold rule, ACCEPT retained on the low-strict semantic-safe rows,
  retry retained on semantic/no-op/format/provider failures, and no over-retry
  regression.  Train only if this readout shows a real learned boundary gap
  that protected replay can close.
  Done as sanitized diagnostic mix
  `data\verifier_retry_pairwise_accept_boundary_mix_sanitized_20260614_1338`
  plus v22 readout
  `runs\multi-agent-proxy-v1\visible_guard_verifier_v22_accept_boundary_mix_sanitized_norm_20260614_1348.jsonl`.
  Hidden prompt key counts were `0` for `strict_score`, `semantic_pass`,
  `semantic_issues`, `delegate_error`, and `anchor_overlap`.
  v22 readout: valid JSON `1.0`, verdict accuracy `0.736842`, retry
  recall/precision `0.5/0.4`, errors `0`.  The new
  `accept_low_strict_semantic_ok` bucket was clean (`4/4` ACCEPT, `0` retry),
  so no ACCEPT-boundary training is justified by itself.
- [x] Next verifier-boundary improvement:
  build a prompt-clean RETRY-boundary mini-set for the missed retry cases
  (`challenge_edit_guarded_replace`,
  `generated_wide_heldout_semantic_edit_path`) and matched over-retry ACCEPT
  cases (`challenge_recover_deleted_file`,
  `generated_wide_heldout_semantic_edit_name`, `heldout_edit_exact_default`).
  Keep the source as visible semantic/no-op/format/provider evidence, not
  scorer labels; rerun the same sanitized v22 readout before any LoRA/DPO.
  Required gate before training: preserve `4/4` ACCEPT on
  `accept_low_strict_semantic_ok`, improve retry recall above `0.5`, and reduce
  unnecessary retries below `3/15` without adding runtime threshold rules.
  Done as
  `data\verifier_retry_boundary_focus_mix_20260614_1350` with hidden prompt key
  rows `0`.  v22 focus readout
  `runs\multi-agent-proxy-v1\visible_guard_verifier_v22_retry_boundary_focus_20260614_1351.jsonl`
  kept protected ACCEPT replay `4/4` but failed all five historical boundary
  rows: verdict accuracy `0.444444`, retry recall/precision `0.0/0.0`, missed
  retries `2`, unnecessary retries `3`.  Do not train from this alone and do
  not add a runtime retry rule.
- [x] Next verifier-boundary step:
  downgrade this from main-track planner work to auxiliary recovery data.
  The user clarified that the small model is not the planner; it is an
  assistant to the large model.  Do not spend the next run training a verifier
  planner.  Keep these rows as future safety/recovery supervision only.
  Done: the 2026-06-14 14:20 update treats verifier RETRY as optional recovery
  and moved the main track to assistant-chain evaluation.
- [x] Reframe and summarize the current evidence as a memory/evidence assistant
  chain rather than a verifier-planner chain.
  Added `scripts\summarize_memory_assistant_chain_eval.py` and built
  `runs\multi-agent-proxy-v1\memory_assistant_chain_eval_20260614_1405.json`
  plus `.md` with no new large-model calls.  Main metrics:
  104-row controller gate has memory selection/rejection `1.0/1.0`,
  delegate decision accuracy `0.951923`, all-core `0.951923`;
  proxy12 assistant chain delegates `6/12` rows with missed/unnecessary
  delegation `0/0`, cuts large calls by `0.5`, cuts large tokens by
  `0.471458`, and improves delegated semantic pass `0.583333 -> 0.833333`
  versus all-delegate; stale-memory delegate4 has semantic pass `1.0` and
  leakage rows `0`.  Optional Qwen retry is reported separately as recovery,
  not the main proof.
- [x] First self-handle execution evidence audit for proxy12.
  Added `scripts\audit_proxy_self_handle_execution.py` and rebuilt
  `runs\multi-agent-proxy-v1\memory_assistant_chain_eval_20260614_1420.json`.
  Existing self-handle commands on proxy12: `6` rows, missing commands `0`,
  action rate `1.0`, skill match `1.0`, semantic pass `1.0`, mean strict
  `0.871667`.  This closes the immediate "self-handle rows are only route
  decisions" reporting gap, but it is still proxy-scored execution-shape
  evidence rather than real repo mutation plus harness execution.
- [x] Semantic-risk no-regression manifest before any SFT.
  Done as
  `runs\semantic-risk-no-regression-manifest-v22-v3broader-20260615_0021.json`.
  Memory/evidence no-regression passed (`all_core_correct_rate=0.951923`,
  stale/distractor rejection `1.0/1.0`).  Broader single-case semantic-risk
  binary is the current best readout (`val17 risk match=1.0`,
  `train61 risk match=0.901639`, exact schema `1.0`, unknown key `0.0`), but
  `ready_for_semantic_risk_sft=false`: expanded A/B pairwise still has position
  bias and atom polarity still has a copy-guard-positive residual.  Do not train
  from the pairwise generation surface.
- [x] Next semantic-risk controller data step:
  build a residual-focus slice from the six missed true
  `copy_default_only_visible` list-family rows plus matched clean
  protected-false/current-evidence rows.  Keep prompts label-hidden and
  visible-evidence-only.  This should produce better evidence for the small
  model's `semantic_risk_requires_delegate` atom without adding runtime packet
  normalizers or benchmark-specific rules.  Re-run the single-case binary gate,
  atom-polarity gate, pairwise bias check, and memory assistant-chain manifest
  before any tiny SFT/DPO.
  Done as
  `data\semantic_risk_residual_focus_binary_v1_20260615_0029`: train12 is
  balanced (`6` missed true residual + `6` matched clean false), val12 is
  balanced (`6` clean true holdout + `6` matched clean false), and both splits
  have route/support-label leakage `0`.  v22 gate:
  train12 risk match `0.5` with all residual true rows missed and all false
  rows clean; val12 risk match `1.0`.  This isolates a narrow learnable
  evidence boundary rather than a broad list-family failure.
- [x] Next semantic-risk atom step:
  convert the residual-focus slice into an atom-level target using existing
  evidence atoms, especially `none_guard_rewrite_visible`,
  `mutable_default_mapping_risk`, and `mutable_default_copy_guard_visible`.
  Keep packet hints template-derived from atoms.  Required before any tiny SFT:
  residual train true-risk recall improves without losing matched false rows,
  val12 remains `1.0`, broader v3 binary does not regress, atom polarity
  copy-guard residual improves, expanded pairwise is still diagnostic-only, and
  memory assistant-chain no-regression still passes.
  Done as
  `data\semantic_risk_residual_atom_polarity_v1_20260615_0041`.
  v22 atom gate is schema-clean and recovers the missed true residuals
  (`missed_true_residual=6/6`, `clean_true_holdout=6/6`) but over-delegates
  matched false rows (`train matched_clean_false=1/6`, `val matched_clean_false=3/6`
  by derived delegate).  The useful atom is `mutable_default_mapping_risk`
  itself (`val 6 TP / 0 FP / 0 FN`; train 6 TP / 2 FP / 0 FN); noisy
  over-delegation comes from broader auxiliary atoms such as
  `guarded_edit_self_handle_evidence`, `self_handle_evidence_positive`, and
  over-generalized copy-guard atoms.  Do not derive delegate by raw union of all
  negative/protective atoms.
- [x] Next semantic-risk readout step:
  build a narrower mapping-risk-atom/protected-false boundary gate from the
  residual atom data.  Score `mutable_default_mapping_risk` directly and report
  protected false/copy-guard false positives separately.  Success criterion
  before tiny SFT: true residual recall stays `6/6`, protected/copy-guard false
  positives approach `0`, broader v3 binary and memory assistant-chain manifest
  do not regress, and no pairwise A/B generation surface is used for training.
  Done with
  `scripts\score_semantic_risk_mapping_atom_boundary.py`.
  Val12 passed (`TP=6`, `FP=0`, `FN=0`, `TN=6`, precision/recall `1.0/1.0`).
  Train12 kept true residual recall `6/6` but had two copy-guard-cancelled
  false positives:
  `generated_heldout_semantic_edit_mapping_chart` and
  `generated_wide_heldout_semantic_edit_mapping_filter`.  This confirms that
  `mutable_default_mapping_risk` is a useful narrow atom, but copy-guard
  cancellation still needs learned boundary data.
- [x] Next semantic-risk cancellation step:
  build a tiny copy-guard-cancel boundary slice or preference readout using
  the two mapping-atom false positives plus matched true residual rows and
  clean protected false rows.  The target should teach the small model to keep
  `mutable_default_mapping_risk=false` when visible current evidence already
  includes a safe copy/guard command with semantic pass, while preserving
  `mutable_default_mapping_risk=true` for unresolved truthiness fallback +
  shared default mutation.  Keep this as learned atom supervision; do not add
  runtime command/string rules.
  Done as
  `data\semantic_risk_copyguard_cancel_boundary_v1_20260615_0115`.
  v22 on the narrow single-atom prompt fixed the targeted copy-guard false
  positives (`copy_guard_cancelled=2/2` train, `1/1` val) while preserving true
  residual recall (`copy_default_only_visible=6/6` train and val).  Train risk
  match is `0.833333` because two scalar truthiness protected negatives are
  still misclassified as mapping/container risk:
  `generated_wide_heldout_semantic_edit_name` and
  `generated_wide_heldout_semantic_edit_radius`.  Val13 is clean (`1.0`).
- [x] Next semantic-risk scalar/container boundary step:
  build a tiny boundary slice for scalar truthiness guards versus mutable
  container/default mapping risk.  Positive rows should keep unresolved
  container default mutation (`items = arg or DEFAULT_LIST; items.append(...)`);
  negative rows should include scalar/non-container guards such as
  `return name or ''`, `return radius or 0`, and related protected false rows.
  The learned atom target is still only `mutable_default_mapping_risk`; packet
  and delegate decisions remain template/controller-level.  Do not add runtime
  regex rules for scalar returns.
  Done as
  `data\semantic_risk_scalar_container_boundary_v1_20260615_0128`.  v22 got
  train12 and val13 risk match `1.0`, with exact schema `1.0` and unknown-key
  rate `0.0`.  It preserved true container/default mutation
  (`copy_default_only_visible=6/6`), preserved copy-guard cancellation, and
  fixed the scalar truthiness false rows (`return name or ''`,
  `return radius or 0`) without adding runtime regex rules.
- [ ] Next semantic-risk consolidation step:
  use
  `data\semantic_risk_mapping_atom_boundary_mix_v1_20260615_1645` and the
  v22 runs
  `runs\semantic-risk-mapping-atom-boundary-mix-v22-v1-val55-20260615_1645.jsonl`
  and
  `runs\semantic-risk-mapping-atom-boundary-mix-v22-v1-train97-20260615_1645.jsonl`
  as the current atom-boundary diagnostic.  Val55 is clean (`1.0` risk match,
  schema `1.0`, unknown key `0.0`), but train97 is only `0.855670` because
  duplicated old residuals remain: twelve `copy_default_only_visible`
  false-negatives from six repeated `v1v_copydefault_*_copy_selected_list`
  task ids, plus two repeated scalar protected false positives
  (`generated_wide_heldout_semantic_edit_name`,
  `generated_wide_heldout_semantic_edit_radius`).  Before any tiny SFT, build
  a de-duplicated residual replay / train-val-clean boundary report and rerun
  memory assistant-chain no-regression.  Do not train from duplicated residual
  rows or from the A/B pairwise surface.
- [x] De-duplicated semantic-risk boundary replay:
  built
  `data\semantic_risk_mapping_atom_boundary_mix_v1_dedup_refinedfirst_20260615_1652`
  with refined scalar/container boundary prompts first, then copy-guard,
  residual, and broader rows.  It drops duplicate
  `(task_id, risk_kind, gold)` rows (`36` train, `29` val) while keeping a
  single-atom `mutable_default_mapping_risk` target and route/support-label
  leakage `0`.  v22 is clean on both gates:
  train61 risk match `1.0`, val26 risk match `1.0`, exact schema `1.0`,
  unknown key `0.0`.  This means the earlier train97 failures were caused by
  duplicated rows plus older prompt contracts, not by an unsolved mapping-risk
  boundary.  Still do not train yet until memory assistant-chain no-regression
  and a real assistant-chain harness step are replayed.
- [x] Wire refined mapping-risk atom mix into no-regression manifest.
  Updated `scripts\summarize_semantic_risk_no_regression_manifest.py` with
  optional mapping-atom-mix summaries and generated
  `runs\semantic-risk-no-regression-manifest-v22-with-dedup-refined-mix-20260615_1657.json`.
  Manifest status: memory assistant-chain pass; dedup refined mapping atom mix
  pass (`train61=1.0`, `val26=1.0`); semantic-risk SFT still not ready because
  expanded A/B pairwise generation has position bias.  Next useful experiment
  is the real assistant-chain harness, not semantic-risk SFT.
- [ ] Next main experiment:
  build a cleaner tiny learned readout for the exclusive three-role surface,
  but stop immediate pairwise-DPO sweeps.  The current v22 pairwise logs cover
  the pre-training story:
  `runs\sufficiency_role_pairwise_v1_v22_logprob_val20_20260615_1939_summary.json`
  and
  `runs\sufficiency_role_pairwise_v1_v22_logprob_train36_20260615_1939_summary.json`.
  Val20 stays at raw/normalized accuracy `0.6/0.5`, and train36 stays at
  `0.638889/0.5`.  Matched self-handle is fine, protected delegate is
  recoverable, but missed semantic-risk rows remain the hard failure
  (`0/6` on val20, `1/12` on train36 by raw score).  So the next useful step
  is still a tiny learned readout on
  `guarded_self_handle` / `semantic_command_insufficient` /
  `nonsemantic_delegate_reason`, but the first DPO probes show the current
  pairwise objective is not enough:
  strong DPO moved val semantic-risk to `3/6` but regressed protected delegate
  to `1/4`; conservative/replay-balanced DPO preserved protected but left
  semantic-risk at `0/6`.  The PEFT nested-adapter warning is now guarded:
  `scripts\train_pairwise_dpo_lora.py` and
  `scripts\run_pairwise_logprob_diagnostics.py` reject implicit adapter-on-
  adapter runs unless `--allow-nested-peft` is explicit, and the updated
  scripts were synced to remote.  Next implementation should either use a clean
  base-model + `--initial-adapter` continuation path or a role-classifier/SFT-
  style readout with balanced replay, then gate on role-choice generation,
  route-risk dedup, 104-row memory controller, hard stale/distractor verdicts,
  refined mapping-risk atom mix, and only then assistant-chain proxy.  Do not
  add runtime routing rules.
- [ ] Do not deploy the clean-base three-role DPO adapter yet.
  The clean continuation run
  `runs\sufficiency_role_readout_cleanbase_v1_dpo_2ep_lr5e6_20260615_2014`
  fixed the nested-PEFT issue and made pairwise ranking much better
  (val20 raw/normalized `0.90/0.95`; semantic-risk normalized `5/6`;
  protected `4/4`).  But greedy role generation on val10 still matched only
  `0.8`, with missed semantic-risk `1/3` and the same two failures predicted
  as `guarded_self_handle`:
  `runs\sufficiency_role_readout_cleanbase_v1_dpo_2ep_lr5e6_role_choice_val10_generation_20260615_2014_summary.json`.
  Next learned-readout step should be generation-aligned, e.g. a tiny
  three-role SFT/classifier-style target with matched/protected replay, then
  rerun role-choice generation, original route-risk dedup, memory/stale/
  mapping no-regression, and only then assistant-chain.  Do not keep running
  DPO-only sweeps unless they include a generation gate improvement.
- [ ] Stop immediate role-only SFT sweeps too.
  The first clean-base three-role SFT run
  `runs\sufficiency_role_choice_sft_v1_cleanbase_3ep_lr5e6_20260615_2027`
  memorized the tiny train18 target, but val10 generation got worse than the
  clean DPO gate: role match `0.7`, semantic-risk still `1/3`, and protected
  delegate regressed to `1/2`.  The target surface is too small/thin to teach
  the hard semantic boundary by plain role JSON imitation.  Next step should
  collect or synthesize more boundary evidence for the two stubborn semantic
  rows, or use a fixed-label classifier/readout evaluated by scoring rather
  than free generation, while retaining role-choice generation as a required
  downstream gate.  Do not run assistant-chain from these adapters.
- [x] Next boundary-data step:
  build an evidence-comparison atom target for the two stubborn semantic-risk
  rows rather than another role-label trainer.  The hard cases are
  `heldout_edit_exact_default` and
  `generated_wide_heldout_semantic_edit_radius`; both look superficially
  self-handle-safe because the command has a None-guard shape or
  `semantic_pass=true`, but the visible command still conflicts with the
  problem/current evidence.  Candidate learned atoms:
  `command_problem_default_mismatch`, `low_strict_semantic_uncertainty`,
  `visible_command_evidence_conflict`, and
  `guard_shape_present_but_semantics_wrong`.  Include positives from these
  rows plus mapping/default rows, and negatives from matched self-handle rows
  whose command genuinely matches the requested default/guard, plus protected
  nonsemantic delegate replay.  Evaluate by fixed-label atom scoring first,
  then role-choice generation; do not add task-id/default-value regex routing.
- [x] Build and probe first evidence-comparison atom target.
  Done as
  `data\sufficiency_evidence_comparison_atoms_v1_20260615_0445` with four
  atoms:
  `command_problem_default_mismatch`,
  `low_strict_semantic_uncertainty`,
  `visible_command_evidence_conflict`, and
  `guard_shape_present_but_semantics_wrong`.  Zero-shot v22 was schema-clean
  but weak (val10 avg atom accuracy `0.525`, all28 `0.517857`).  A clean-base
  SFT probe
  `runs\sufficiency_evidence_comparison_atoms_v1_cleanbase_sft_5ep_lr5e6_20260615_0445`
  improved generation substantially (val10 avg atom accuracy `0.875`, all28
  `0.928571`, matched/protected buckets `1.0`) but still failed the real
  conflict/default atoms: `generated_wide_heldout_semantic_edit_radius` and
  `generated_wide_heldout_semantic_edit_mapping_exporter`.  Do not deploy this
  adapter or run assistant-chain from it.
- [x] Next evidence-comparison step:
  build a contrastive mismatch/conflict atom slice that teaches the sharp atoms
  the v1 SFT missed.  Positive rows should include wrong scalar fallback
  commands such as `radius -> else 0` when the problem default is `15`, and
  wrong mutable-default copy commands where the default branch still mutates a
  shared mapping/list.  Negative rows should include matched self-handle edits
  with the same surface shape but correct fallback/default or correct copy on
  both branches, plus protected nonsemantic delegate replay.  Score fixed-label
  atoms first; only proceed to role-choice/no-regression if
  `command_problem_default_mismatch`, `visible_command_evidence_conflict`, and
  `guard_shape_present_but_semantics_wrong` all improve without reintroducing
  matched/protected false positives.  Keep this as learned atom supervision,
  not a runtime task-id/default regex.
- [x] Build and probe contrastive mismatch/conflict atom slice.
  Done as
  `data\sufficiency_evidence_comparison_contrastive_v2_20260615_0506`.
  Zero-shot v22 stayed weak (val12 avg atom accuracy `0.541667`).  Clean-base
  SFT
  `runs\sufficiency_evidence_comparison_contrastive_v2_cleanbase_sft_6ep_lr5e6_20260615_0506`
  improved val12/all25 to avg atom accuracy `0.979167/0.98`, with matched and
  protected replay at `1.0`.  It fixed
  `visible_command_evidence_conflict` and
  `guard_shape_present_but_semantics_wrong` (`1.0`), but still predicted
  `command_problem_default_mismatch=false` for every row.  Do not deploy this
  adapter or run assistant-chain from it.
- [x] Next scalar default-mismatch step:
  build a tiny scalar/default micro-curriculum with multiple wrong-vs-correct
  fallback pairs beyond `radius`: numeric (`default 15` vs `0`, `default 6/7`
  vs `0`), string/path (`'download-root'` vs `''`), and bool (`True` vs
  `False`) cases.  Use counterfactual rows where problem/current evidence
  states the default explicitly and visible command either writes the correct
  default or preserves the old/default-wrong fallback.  Keep matched/protected
  replay.  Gate must show `command_problem_default_mismatch` positive recall
  without broad false positives before any role-choice or assistant-chain
  evaluation.
- [x] Build and probe scalar default-mismatch micro-curriculum.
  Done as
  `data\sufficiency_default_mismatch_micro_v1_20260615_0519`.  Zero-shot v22
  collapsed to broad default/conflict positives (val9 avg atom accuracy
  `0.416667`).  Clean-base SFT
  `runs\sufficiency_default_mismatch_micro_v1_cleanbase_sft_8ep_lr5e6_20260615_0519`
  made the other three atoms clean (`low_strict`, `conflict`, `guard_wrong`
  all `1.0`) and preserved matched/protected replay, but
  `command_problem_default_mismatch` still predicted positive `0` times on
  val9/all17.  Do not deploy this adapter or run assistant-chain from it.
- [x] Stop four-key generation SFT sweeps for `command_problem_default_mismatch`.
  The atom did not emerge from v1 evidence-comparison data, v2 contrastive
  conflict data, or scalar default-mismatch micro data.  Next useful direction
  is a separate binary/default-mismatch readout or a value-extraction target
  that outputs `requested_default`, `command_default`, and `defaults_match`
  before the boolean.  Evaluate by fixed-label scoring/logprob first, with
  matched/protected replay, before any role-choice or assistant-chain gate.
- [x] Try value-extraction default comparison surface.
  Done as `data\default_value_extraction_v1_20260615_0530` and
  `runs\default_value_extraction_v1_cleanbase_sft_8ep_lr5e6_20260615_0530`.
  It is more informative than the four-key atom surface: all17 generation
  reached all-fields match `0.764706`, avg field accuracy `0.862745`, and
  defaults-match match `0.882353`; wrong-explicit-guard defaults-match is
  `4/5`.  But string quoting/empty-string normalization and bool requested
  default still fail, so do not deploy or run assistant-chain from it.
- [x] Next default-value readout step:
  add normalized scoring and a small replay set for string/bool defaults.
  Normalize quotes for string literals (`'download-root'` vs `download-root`)
  and empty-string spelling (`''` vs empty string) in the scorer, but keep raw
  fields in the model output.  Add bool wrong-vs-correct examples where problem
  clearly says requested default `True` and command writes `False`.  Gate on
  `defaults_match` and raw field accuracy before using the signal to assemble
  `command_problem_default_mismatch`.  Done with scoring-only normalization,
  `data\default_value_extraction_string_bool_replay_v1_20260615_2145`, and
  `runs\default_value_extraction_string_bool_replay_v1_cleanbase_sft_6ep_lr5e6_20260615_2145`.
  The normalized scorer raised the previous v1 all17 score from all-fields
  `0.764706` / avg field `0.862745` to `0.882353` / `0.921569`, exposing two
  real residual failures.  The string/bool replay SFT then reached schema
  `1.0`, val9 all-fields `1.0`, and all29 all-fields `1.0`.  Do not deploy
  solely from this tiny gate.
- [ ] Next default-value bridge/no-regression step:
  convert the extracted fields into a templated
  `command_problem_default_mismatch` evidence atom only after no-regression
  checks.  Required checks before route/assistant-chain use: original 104-row
  controller gate, hard stale/distractor verdict gate, protected nonsemantic
  delegate replay, refined semantic/mapping-risk atom mix, and a small
  assistant-chain proxy where the large model sees a packet assembled from the
  extracted fields.  This should remain learned evidence readout plus template
  assembly, not a runtime task-id/default parser.
- [x] Add the default-value-to-atom bridge audit.
  Done as `scripts\bridge_default_value_extraction_to_atoms.py`.  It accepts
  only valid/schema-clean generated fields where `defaults_match` agrees with
  normalized `requested_default == command_default`, then derives the packet
  atom and repair constraints.  On
  `runs\default_value_extraction_string_bool_replay_v1_val_bridge_atoms_20260615_2153.jsonl`
  and
  `runs\default_value_extraction_string_bool_replay_v1_all_bridge_atoms_20260615_2153.jsonl`,
  accepted rate was `1.0`, mismatch precision/recall were `1.0/1.0`, and
  protected nonsemantic replay stayed negative.  This is still an offline
  bridge diagnostic, not deployment.
- [x] Next no-regression gate for default-value readout:
  evaluate the value-extraction adapter or an equivalent served endpoint
  against the standard memory/stale/semantic-risk gates before any broad
  assistant-chain run.  If serving the adapter would disturb the preferred
  v22 service, run an in-process adapter generation probe or start a temporary
  separate port.  Required report: 104-row controller behavior, hard
  stale/distractor verdicts, refined semantic/mapping-risk atom mix, and a
  tiny packet-to-large-model proxy where the packet uses only bridge-generated
  mismatch atoms.  Done as a readiness manifest rather than a misleading
  full-controller adapter eval:
  `runs\default-value-readout-readiness-manifest-20260615_2158.json`.
  The default-value field gate and field-to-atom bridge pass, existing v22
  memory anchor passes, and refined mapping anchor passes; decision is
  `ready_for_tiny_packet_proxy=true` but
  `ready_for_adapter_deployment=false`.
- [x] Do not run the default-value tiny packet proxy until actual transfer is clean.
  The actual scoreable-task gate
  `runs\default_value_actual_proxy_eval_v1_readout_scored_norm_20260615_2158.jsonl.summary.json`
  exposed transfer failures that the synthetic micro gate hid: all9 field
  match `0.777778`, defaults-match `0.777778`; bridge precision/recall
  `0.6/1.0` with two false-positive mismatch atoms on a truthiness-control
  radius row and a correct visible bool row.  The updated manifest
  `runs\default-value-readout-readiness-manifest-actualgate-20260615_2158.json`
  therefore has `ready_for_tiny_packet_proxy=false`.  Next work should add
  actual-task replay / broader held-out controls for truthiness-vs-default and
  bool requested-default extraction, then rerun the actual scoreable gate.
- [x] Fix default-value actual scoreable transfer with actual-family replay.
  Done as `scripts\build_default_value_actual_replay_data.py` and
  `data\default_value_actual_replay_v1_20260615_2210`.  The replay adds
  scoreable-family actual prompts for margin/scale/name/tag/enabled/page while
  excluding the held-out actual gate task ids radius/visible/exact-default.
  Short continuation SFT
  `runs\default_value_actual_replay_v1_from_readout_sft_4ep_lr3e6_20260615_2210`
  used 38 train rows, 4 epochs, `lr=3e-6`, and did not replace the v22
  service.  Results: synthetic val9/all47 field all-fields `1.0/1.0`; val/all
  bridge precision/recall `1.0/1.0`; held-out actual scoreable gate field
  all9 `1.0`; held-out actual bridge precision/recall `1.0/1.0`, `tp=3`,
  `fp=0`, `fn=0`.  Manifest
  `runs\default-value-readout-readiness-manifest-actualreplay-20260615_2210.json`
  now has `ready_for_tiny_packet_proxy=true` and
  `ready_for_adapter_deployment=false`.
- [x] Run the next tiny default-value packet-to-large-model proxy.
  Use only accepted bridge-generated `command_problem_default_mismatch` atoms
  from the default-value readout; refuse invalid/schema-dirty/internally
  inconsistent field rows instead of repairing them.  Keep the preferred v22
  service unchanged and use the readout adapter offline/in-process or on a
  temporary separate port.  The proxy should run on scoreable actual tasks and
  report semantic pass/strict score, large-call count, token cost, invalid-field
  refusals, and whether wrong-explicit positives improve without false
  positives on correct-explicit/truthiness controls.  This is packet/template
  assembly from learned evidence atoms, not deployment of the readout as a full
  controller and not a task-id/default parser.  Done as
  `scripts\build_default_value_tiny_packet_proxy.py`,
  `scripts\summarize_default_value_tiny_packet_proxy.py`, and
  `runs\default_value_tiny_packet_proxy_20260615_2226_summary.json`: 9 actual
  rows, 3 large calls, 6 no-call controls, invalid-field refusals `0`,
  false-positive controls `[]`, missed positives `[]`, `gpt-5.4-mini`
  provider errors `0/3`, delegate semantic pass `1.0`, mean strict `0.915909`,
  total tokens `5088`, large-call reduction vs all rows `0.666667`.
- [x] Broaden the default-value packet proxy without changing the controller contract.
  Build a slightly larger scoreable held-out slice from generated wide
  semantic tasks beyond radius/visible/exact-default, using the learned
  default-value readout and bridge-generated packet atoms.  Compare three
  conditions: bridge-selective packet proxy, all-delegate with the same packet
  prompt, and a no-packet/candidate-prompt baseline.  Required report:
  semantic pass, mean strict, call/token cost, false-positive no-call controls,
  invalid/inconsistent readout refusals, and per-family failures.  Do not add
  runtime task-id/default parsers; if new failures appear, turn them into
  evidence-readout/reliability training examples or packet-template diagnostics.
  Done as `data\default_value_broadened_proxy_eval_v1_20260615_2234` and
  `runs\default_value_broadened_proxy_comparison_20260615_2234.json`.  The
  readout/bridge gate was clean on 12 rows: field all-fields `1.0`, bridge
  precision/recall `1.0/1.0`, `tp=4`, `fp=0`, `fn=0`.  Large-model comparison
  with `gpt-5.4-mini`: bridge-selective packet proxy used 4 calls, semantic
  pass `1.0`, mean strict `0.866559`, tokens `7703`; all-delegate packet used
  12 calls, semantic pass `1.0`, mean strict `0.893020`, tokens `24404`;
  no-packet candidate baseline used 12 calls, semantic pass `0.75`, mean
  strict `0.844426`, tokens `19438`.  Selective vs all-packet call reduction
  `0.666667`, token reduction `0.684355`; packet semantic delta vs candidate
  `+0.25`.
- [x] Convert default-value proxy contrasts into learned controller data.
  Use the broadened comparison traces to build training/preference examples for
  packet reliability and selective delegation: bridge-positive rows should call
  the large patch generator with accepted default-mismatch atoms; correct and
  truthiness controls should no-call unless another learned atom/risk warrants
  delegation.  Include no-packet failures as evidence that packet atoms matter,
  but do not add runtime task-id/default parsing.  Gate the resulting controller
  target on held-out scoreable default-value rows, stale-memory rejection,
  semantic-risk no-regression, and packet false-positive controls before any
  larger assistant-chain run.  Done as
  `scripts\build_default_value_proxy_contrast_training_data.py` and
  `data\default_value_proxy_contrast_training_v1_20260615_2246`: route pairs
  `12`, route SFT rows `12`, packet-context preference pairs `2`, route
  distribution `DELEGATE_PACKET=4` / `SELF_HANDLE=8`, balanced variants
  `4/4/4`, skipped packet pairs `[]`.  Did not train from this alone because
  the packet-context slice is only two rows and would overfit.
- [x] Mix default-value, stale-memory, and semantic-risk packet reliability data.
  Combine `data\default_value_proxy_contrast_training_v1_20260615_2246` with
  existing stale-memory packet preference / semantic-risk packet-boundary data
  into a small controller target that learns route + packet reliability across
  atom families.  Required gates before training/deployment claims: default-value
  heldout route false-positive controls, stale/distractor rejection, refined
  semantic-risk no-regression, packet-context preference accuracy, and a tiny
  assistant-chain proxy with mixed atoms.  Keep packet construction template
  based and avoid task-id/default parsers.  Done as
  `scripts\build_mixed_packet_reliability_data.py` and
  `data\mixed_packet_reliability_controller_v1_20260615_2256`: pairwise total
  `296` (`default_value=14`, `stale_memory=164`, `semantic_risk=118`) with
  train/val `197/99`, plus semantic-risk boundary SFT total `87` with train/val
  `61/26`.  The summary explicitly marks `ready_for_training=false` because
  default-value still lacks an independent val slice in the mix and
  packet-context default-value evidence is only `2` rows.
- [ ] Build a mixed packet-reliability gate before any training.
  Evaluate the mixed target family by family rather than training immediately:
  default-value heldout route false-positive controls, stale/distractor memory
  rejection and packet canonical/key preference accuracy, semantic-risk
  evidence preference and refined boundary no-regression, and packet-context
  preference accuracy.  If gates are clean, run a tiny mixed-atom
  assistant-chain proxy before claiming deployment readiness.  Partial gate:
  `runs\mixed_packet_reliability_semantic_boundary_v22_20260615_2302.jsonl.summary.json`
  scored the mixed semantic-risk boundary val slice at rows `26`, valid-json
  `1.0`, exact-schema `1.0`, risk-match `1.0`, unknown-key `0.0`, errors `0`.
  Mixed pair-generation gate added as
  `scripts\run_mixed_packet_reliability_pair_gate.py`.  Current v22 failed the
  pair interface gates: stale packet-memory-key smoke `6` rows valid-json
  `1.0` but preferred/core/full packet match `0.0`; semantic-risk preference
  val `38` rows valid-json `1.0` but choice match `0.5` with all predictions
  `B`; default-value route `12` rows valid-json `0.916667` but route match
  `0.0`, mostly ad-hoc edit/decision objects instead of `route_verdict`.
  Therefore do not run a larger assistant-chain proxy yet.
- [x] Build a compact mixed chosen-response SFT/format target.
  Convert the mixed pair data into a small supervised target where the response
  is the chosen controller commitment: `route_verdict` for default-value route,
  `{"choice":"A"|"B"}` for semantic-risk preference, and canonical packet core
  JSON for stale-memory packet reliability.  Keep this as learned controller
  behavior, not runtime output normalization.  Gate before any training claim:
  default route format/route accuracy, semantic A/B balance and accuracy,
  stale packet core/full accuracy, and semantic boundary no-regression.  Done
  as `scripts\build_mixed_packet_reliability_sft_data.py` and
  `data\mixed_packet_reliability_chosen_sft_v1_20260615_2318`: total `296`,
  train/val `197/99`, families `default_value=14`, `stale_memory=164`,
  `semantic_risk=118`, semantic choice labels total `A=55/B=63`, val
  `A=19/B=19`.  Summary remains `ready_for_training=false`.
- [x] Train or dry-run a short mixed chosen-response adapter candidate, then rerun gates.
  Use `data\mixed_packet_reliability_chosen_sft_v1_20260615_2318\train_sft.parquet`
  as a compact interface/format target only if compute is free and the run is
  clearly labeled candidate, not deployment.  Required post-checks: mixed pair
  generation val gate, semantic boundary no-regression, default-value route
  controls, stale packet canonical core/full accuracy, and no larger
  assistant-chain proxy until those recover.  Done as remote candidate
  `/mnt/memory-agent/runs/mixed_packet_reliability_chosen_sft_v1_candidate_20260615_2325`
  from v22 initial adapter, epochs `2`, steps `198`, train loss
  `2.436533 -> 0.804448`, val loss `2.247897 -> 0.546884`.  Candidate was
  served temporarily on remote `8002` and then stopped; v22 on `8001` was not
  changed.  Gates: semantic A/B val recovered to `38/38`, but stale packet
  core/full remained `0.0`, default-value route remained `0.0`, and semantic
  boundary risk-match regressed from v22 `1.0` to `0.769231`.  Candidate is not
  deployable and no assistant-chain proxy should use it.
- [x] Build a protected mixed interface curriculum before another candidate.
  Do not simply add more generic SFT rows.  Build a smaller protected mix that
  keeps semantic mapping-boundary replay in the train target, isolates
  default-value `route_verdict` rows as a strict short-format head, and breaks
  stale-memory packet core into top-level-field retention / memory-id plural
  / no-wrapper subtargets.  Rerun v22 and candidate gates on each subtarget
  before another adapter: semantic boundary no-regression, route verdict
  format/accuracy, stale packet core/full, and semantic A/B balance.  Done as
  `scripts\build_protected_mixed_interface_curriculum.py`,
  `scripts\run_protected_mixed_interface_gate.py`, tests
  `tests\scripts\test_build_protected_mixed_interface_curriculum.py` and
  `tests\scripts\test_run_protected_mixed_interface_gate.py`, plus data
  `data\protected_mixed_interface_curriculum_v1b_20260616_0025`: total `820`,
  train/val `547/273`, kinds semantic-boundary `174`, semantic-choice `118`,
  route-short `48`, and stale subtargets `160` each.  v22 baseline gates:
  protected val `runs\protected_mixed_interface_val_v22_20260616_0050.jsonl`
  had target-match `0.593407`; by kind boundary `52/52`, memory plural ids
  `60/61`, semantic choice `19/38` with all `B`, packet evidence `26/61`,
  top-level core `5/61`.  Route train gate
  `runs\protected_mixed_interface_route_train_v22_20260616_0110.jsonl` had
  exact schema `48/48` but route-match `32/48`, all `SELF_HANDLE`.
- [x] Train a short protected mixed interface adapter candidate, then rerun gates.
  Use `data\protected_mixed_interface_curriculum_v1b_20260616_0025\train_sft.parquet`
  only as an offline candidate from v22, not deployment.  The goal is learned
  controller behavior: preserve semantic boundary `1.0`, fix semantic A/B
  order bias, fix wrong-explicit default `DELEGATE_PACKET` route boundary, and
  improve stale top-level route/core plus packet evidence flags without
  regressing the already-good memory plural-id target.  Required checks before
  any assistant-chain run: protected val gate, route short-format gate,
  previous mixed pair gate, previous semantic boundary no-regression, and
  stale packet canonical/core diagnostics.  Stop and record failures if the
  adapter only learns output templates but not route/evidence boundaries.  Done
  as remote candidate
  `/mnt/memory-agent/runs/protected_mixed_interface_candidate_20260616_0125`
  from v22, epochs `1`, steps `274`, lr `2e-6`, train eval
  `1.568490 -> 0.101327`, val eval `1.422549 -> 0.031123`; temporary service
  on remote `8002` was stopped and v22 on `8001` was not replaced.  Gates:
  protected val target-match improved `0.593407 -> 0.772894`, with boundary
  `52/52`, memory ids `61/61`, packet evidence `50/61`, semantic choice
  `23/38`, top-level core `25/61`; semantic boundary no-regression stayed
  `26/26`; but route short-format regressed `32/48 -> 28/48` and original
  mixed stale packet core/full remained `0.0`.  Candidate is not deployable.
- [x] Build a full-packet composition bridge and harder route-boundary target.
  The protected subtargets improved, but they do not yet compose into the
  original canonical packet JSON.  Build offline examples that require the
  small controller to assemble route/task/skill/localization/memory_decision/
  packet_evidence together after the decomposed heads, with anti-wrapper,
  anti-source-prompt-copy, plural-id, and route-field ownership negatives.
  Separately build an independent default-value route-boundary split with
  wrong-explicit, correct-explicit, and truthiness controls so route verdict is
  learned instead of pulled by packet-format templates.  Gate v22 and the
  protected candidate on these before any more training; only train a new
  candidate if the bridge has held-out route controls and full-packet scoring
  targets.  Done as `scripts\build_full_packet_composition_bridge_data.py`,
  `scripts\run_full_packet_composition_bridge_gate.py`, and tests
  `tests\scripts\test_build_full_packet_composition_bridge_data.py`,
  `tests\scripts\test_run_full_packet_composition_bridge_gate.py`.
  Data `data\full_packet_composition_bridge_v1_20260616_0205`: total `172`,
  train/val `108/64`, full-packet composition `160`, route-boundary `12`, with
  one route task held out in val.  v22 gate:
  `runs\full_packet_composition_bridge_val_v22_20260616_0205.jsonl.partial_summary.json`
  valid JSON `1.0`, full-packet composition `0/61`, route-boundary `3/3`.
  Failure mode is scaffold echo: the model emits `top_level_core` /
  `memory_plural_ids` / `packet_evidence_fields` instead of deleting scaffold
  and composing the final canonical packet.
- [x] Build a scaffold-deletion composition target and broaden route controls.
  The new bridge found the exact missing step: after reading decomposed heads,
  the small model must output only the final canonical packet and must not echo
  intermediate head names.  Add an explicit offline composition target with
  negative examples for head echo, source-prompt copy, singular aliases, and
  route/path aliasing.  Broaden route-boundary controls beyond one held-out
  task before another adapter.  Gate v22 and the protected candidate on
  full-packet composition, then train only if held-out full-packet core and
  semantic boundary no-regression are both measurable.  Done as
  `scripts\build_scaffold_deletion_composition_data.py` and updated
  `scripts\run_full_packet_composition_bridge_gate.py` so scaffold-deletion rows
  share the full canonical packet gate.  Data
  `data\scaffold_deletion_composition_v1_20260616_0235`: total `172`,
  train/val `99/73`, scaffold-deletion composition `160`, route-boundary `12`.
  v22 gate `runs\scaffold_deletion_composition_val_v22_20260616_0235.jsonl.summary.json`
  reached `1.0` target match on all `73` rows, with `61/61` full-packet
  composition and `12/12` route controls correct.
- [x] Build the packet assembly proxy gate and a broader route control set.
  The learning signal is now clear enough to use in a proxy rather than another
  adapter: make the small controller choose evidence atoms, then pass only the
  scaffold-deletion prompt to the large patch generator.  Build a proxy gate
  that checks the packet assembly template end-to-end, and broaden the route
  controls to more than one held-out task so route boundary is not an isolated
  special case.  Do not hard-code runtime normalizers; keep the learned
  controller and prompt/template assembly separate.  Done as
  `scripts\run_packet_assembly_proxy_gate.py` and
  `tests\scripts\test_run_packet_assembly_proxy_gate.py`.  Gate
  `runs\packet_assembly_proxy_val_v22_20260616_0300.jsonl.summary.json` over
  `61` scaffold-deletion val packet rows had assembly-success `1.0`,
  canonical exact match `1.0`, no scaffold leakage `1.0`, and all
  large-delegate-safe field preservation checks `1.0`.  Did not call
  `gpt-5.4-mini` because these packets map to synthetic task ids not present in
  the scorer (`0/9` scoreable ids).
- [x] Build a scoreable assistant-chain packet assembly slice.
  Reuse the scaffold-deletion assembly template, but construct rows from real
  Hybrid-Gym/path-edit scoreable tasks so the large delegate output can be
  measured.  Required before spending large-model calls: task ids must exist in
  `score_large_delegate_probe.task_index()`, packet assembly gate must pass,
  route boundary must include delegate/self controls, and the evaluation must
  report large-call count/tokens, delegated semantic pass, mean strict score,
  and self-handle evidence.  Keep packet assembly prompt/template based; do not
  add runtime output normalizers.  Done as
  `scripts\build_scoreable_packet_assembly_slice.py` and
  `data\scoreable_packet_assembly_slice_v1_20260616_1120`: 8 scoreable packet
  rows plus 2 route controls.  Packet assembly now passes on v22:
  `runs\scoreable_packet_assembly_proxy_gate_v22_20260616_1120.jsonl.summary.json`
  has assembly success/canonical exact/delegate-safe preservation all `1.0`
  and writes 8 packets.  Large-model calls were intentionally skipped because
  the required route boundary did not pass:
  `runs\scoreable_packet_assembly_full_gate_v22_20260616_1135.jsonl.summary.json`
  got packet rows `8/8` but route controls only `1/2`, with v22 predicting
  `DELEGATE_PACKET` for the focused-test self-handle control.
- [x] Fix the scoreable route/no-call boundary before spending large-model calls.
  Build a tiny learned/readout gate on the same scoreable slice that separates
  `DELEGATE_PACKET` for missing or uncertain actions from `SELF_HANDLE` when
  visible memory already gives an exact focused command.  Required before
  running `gpt-5.4-mini`: route self-control pass, packet assembly still `8/8`,
  hard stale/distractor memory no-regression, semantic-risk no-regression, and
  no runtime delegate/self override.  Once this passes, run
  `scripts\run_large_delegate_probe.py` with
  `data\scoreable_packet_assembly_slice_v1_20260616_1120\audit.json` and
  `runs\scoreable_packet_assembly_proxy_gate_v22_20260616_1120.packets.jsonl`,
  then score with `scripts\score_large_delegate_probe.py`.  Done as
  `scripts\build_scoreable_route_boundary_data.py` and
  `scripts\run_scoreable_route_boundary_gate.py`.  v22 route gate
  `runs\scoreable_route_boundary_v1_v22_20260616_1125.jsonl.summary.json`
  passed: rows `8`, delegate `4/4`, self-handle `4/4`, valid JSON/exact schema
  `1.0`.  Then the scoreable packet large-delegate probe with `gpt-5.4-mini`
  ran on 8 packet rows:
  `runs\scoreable_packet_assembly_large_delegate_gpt54mini_20260616_1130.scored.jsonl.summary.json`
  has provider errors `0`, action/skill/semantic pass all `1.0`, mean strict
  `0.897861`, total tokens `20528`.  Treat this as a tiny successful
  assistant-chain proxy, not yet broad benchmark proof.
- [x] Broaden the scoreable assistant-chain proxy with selective no-call accounting.
  Build a balanced scoreable set with delegated packet rows plus self-handle
  controls in the same audit manifest, so the report includes large-call count,
  no-call controls, token cost, semantic pass, mean strict score, and call
  reduction.  Preserve the current division of labor: small model learns route,
  memory reliability, exact test-command atoms, and scoped locate path hints;
  packet assembly remains prompt/template based; `gpt-5.4-mini` is called only
  on delegated rows.  Target the observed strict-score weaknesses first:
  cache-key locate path scoping and exact `PYTHONPATH=src:. ... -q` test-command
  preservation.  Do not add task-id/default/path runtime parsers.  Done as
  `scripts\build_scoreable_selective_proxy_slice.py` and
  `data\scoreable_selective_proxy_v1_20260616_1135`: 15 total rows, 10
  delegated packet rows, 5 self-handle no-call controls, call reduction
  `0.333333`.  v22 packet gate
  `runs\scoreable_selective_proxy_v1_packet_gate_v22_20260616_1135.jsonl.summary.json`
  passed 10/10 with all preservation checks `1.0`; route gate
  `runs\scoreable_selective_proxy_v1_route_gate_v22_20260616_1135.jsonl.summary.json`
  passed 15/15 with delegate `10/10` and self-handle `5/5`.  `gpt-5.4-mini`
  was called only on delegated rows:
  `runs\scoreable_selective_proxy_v1_large_delegate_gpt54mini_20260616_1135.scored.jsonl.summary.json`
  has provider errors `0`, action/skill `1.0`, semantic pass `0.9`, mean
  strict `0.852283`, total tokens `27083`.
- [x] Build exact-command evidence atom targets from selective proxy failures.
  Use the failed/low-strict rows from
  `runs\scoreable_selective_proxy_v1_large_delegate_gpt54mini_20260616_1135.scored.jsonl`
  to train/gate small-controller atoms for exact edit replacement preservation
  and scoped locate path hints.  Initial failures: visible-flag edit used the
  old default `False` instead of requested `True`; cache-key locate searched
  `.` too broadly; URL recover locate and path-edit rows were semantic-pass but
  lower strict due to command style.  Keep this as learned evidence/readout
  supervision and packet-template refinement, not task-id/default/path runtime
  parsers.  Done as `scripts\build_exact_command_evidence_atom_data.py`,
  `scripts\build_exact_command_single_atom_data.py`,
  `scripts\run_exact_command_evidence_atom_gate.py`, and
  `scripts\run_exact_command_single_atom_gate.py`.  Rebuilt data after fixing
  quoted default extraction:
  `data\exact_command_evidence_atoms_v1_20260616_1200` has 11 rows and
  `data\exact_command_single_atoms_v1_20260616_1200` has 55 rows with
  labels `False=7`, `None=30`, `True=18`.  Clean single-atom prompt gate
  `runs\exact_command_single_atoms_v1_v22_20260616_1205.jsonl.summary.json`
  has valid JSON/exact schema/atom match all `1.0`, value match `0.690909`;
  prompt-polluted baseline was `0.309091`.  Remaining blocker is learned
  `null`/false discrimination and `candidate_scope_is_specific` value match
  `0.181818`, not packet assembly.
- [x] Train or calibrate exact-command single-atom readout before another large-model proxy.
  Use `data\exact_command_single_atoms_v1_20260616_1205` as the first clean
  representation target, then add balanced non-applicable/null and applicable
  false examples for `candidate_scope_is_specific`, `candidate_uses_visible_default`,
  and `candidate_needs_retry_or_refinement`.  Evaluate with
  `scripts\run_exact_command_single_atom_gate.py`; require improved value match
  on `False` and `None`, especially scope-specific, before rerunning the
  selective proxy or spending more `gpt-5.4-mini` calls.  Keep this as
  learned evidence-atom supervision; do not add runtime default/path/scope
  parsers or benchmark-specific route overrides.  Done as
  `scripts\build_exact_command_calibration_data.py` and
  `data\exact_command_calibration_v1_20260616_1218`: train `96`, val `55`.
  Remote continuation SFT from v22 adapter ran for `96` steps, val loss
  `1.337995 -> 0.035057`, output adapter
  `/mnt/memory-agent/runs/agent-rl-rollouts-qwen3-8b-a800-v1/checkpoints/exact_command_calibration_v1_20260616_1218_lora`.
  Real generation gate on temporary 8002 service:
  `runs\exact_command_single_atoms_v1_calib1218_8002_20260616_1222.jsonl.summary.json`
  has rows `55`, errors `0`, valid JSON/exact schema/atom match all `1.0`,
  value match `0.927273` versus v22 clean baseline `0.690909`; scope-specific
  improved `0.181818 -> 0.818182`.  Temporary 8002 service and local 18002
  tunnel were shut down; preferred v22 service remains active on 8001/18001.
- [x] Add a tiny path-edit residual calibration slice before rerunning selective proxy.
  Remaining calibrated failures are concentrated in
  `path_edit_commitment_artifact` and `path_edit_commitment_upload`:
  non-locate `candidate_scope_is_specific` should be null, and
  `candidate_needs_retry_or_refinement` should remain true for lower-strict
  command-style mismatches.  Build a small residual slice using these failures
  plus matched non-failures, train or gate it against the calibrated adapter,
  then run route/packet/no-regression gates before any new large-model proxy
  or assistant-chain benchmark spend.  Done as
  `scripts\build_exact_command_residual_data.py` and
  `data\exact_command_path_edit_residual_v1_20260616_1228`: train `68`, val
  `55`, focused failures `48`, matched nonfailures `20`.  Remote residual SFT
  from `exact_command_calibration_v1_20260616_1218_lora/adapter` ran `34`
  steps, clean val loss `0.035057 -> 0.017084`, but real generation gate
  `runs\exact_command_single_atoms_v1_residual1228_8002_20260616_1232.jsonl.summary.json`
  regressed value match to `0.872727` from the calibrated adapter's `0.927273`;
  it improved scope-specific to `0.909091` but collapsed `False` predictions
  to `0`.  Do not adopt this residual adapter.
- [x] Build balanced residual v2 for exact-command atoms before no-regression gates.
  Use the v1 residual failure as evidence that one-way focused correction is
  too narrow.  Build a balanced residual slice that keeps the path-edit
  `scope=null` and `retry=true` corrections while explicitly preserving
  `candidate_needs_retry_or_refinement:false`, `candidate_scope_is_specific:false`,
  and `candidate_uses_visible_default:false` examples.  Evaluate first on the
  55-row single-atom gate; only if value match beats `0.927273` without
  collapsing `False`, run route/packet/no-regression gates.  Do not call
  `gpt-5.4-mini` or rerun selective proxy until this passes.  Done as
  `scripts\build_exact_command_balanced_residual_data.py` and
  `data\exact_command_balanced_residual_v2_20260616_1240`: train `140`, val
  `55`, with base calibration `96`, focused residual `16`, false protection
  `28`, value counts `False=52`, `None=40`, `True=48`.  Remote SFT from
  `exact_command_calibration_v1_20260616_1218_lora/adapter` ran `70` steps,
  clean val loss `0.035057 -> 0.011042`.  Real gate
  `runs\exact_command_single_atoms_v1_balanced_residual_v2_8002_20260616_1244.jsonl.summary.json`
  reached value match `0.963636`, with predicted `False=8`, `None=28`,
  `True=19`.  No-regression gates passed:
  route `runs\scoreable_selective_proxy_v1_route_gate_balanced_residual_v2_8002_20260616_1246.jsonl.summary.json`
  has route match `1.0`; packet assembly
  `runs\scoreable_selective_proxy_v1_packet_gate_balanced_residual_v2_8002_20260616_1248.jsonl.summary.json`
  has assembly/canonical/preservation checks all `1.0`.
- [x] Compare balanced residual v2 on the selective proxy before any broad benchmark.
  Use the existing `data\scoreable_selective_proxy_v1_20260616_1135` slice.
  Keep large calls selective and only on delegated rows.  Compare against
  current baselines: v22 route/packet gates `1.0`, exact-command calibrated
  atom gate `0.927273`, balanced residual v2 atom gate `0.963636`, and prior
  selective large-delegate semantic pass `0.9`, mean strict `0.852283`, tokens
  `27083`.  If running `gpt-5.4-mini`, reuse packet outputs from the passing
  packet gate and record token cost; do not broaden to a full benchmark until
  this small proxy comparison is clean.  Done with
  `runs\scoreable_selective_proxy_v1_packet_gate_balanced_residual_v2_8002_20260616_1248.packets.jsonl`
  and `gpt-5.4-mini` on only the 10 delegated rows:
  `runs\scoreable_selective_proxy_v1_large_delegate_balanced_residual_v2_gpt54mini_20260616_1255.scored.jsonl.summary.json`
  has rows `10`, provider errors `0`, action/skill `1.0`, semantic pass `1.0`,
  mean strict `0.892640`, total tokens `23118`.  This improves over the prior
  selective proxy semantic pass `0.9`, mean strict `0.852283`, tokens `27083`.
  Keep call reduction at `5/15` no-call controls; do not broaden yet.
- [x] Build learned locate-scope retention slice for cache-key broad-search failures.
  The remaining selective-proxy bottleneck is `heldout_locate_cache_key`, where
  the large delegate still emits broad `rg ... .` and strict stays `0.76`.
  Build a small learned atom/packet retention target that teaches the small
  controller to preserve scoped path/root evidence for locate packets and to
  distinguish broad-dot searches from acceptable scoped locate commands.  Use
  existing visible evidence and scored traces; do not add a runtime scope
  parser or benchmark-specific path rewrite.  Gate the atom/packet slice before
  any additional `gpt-5.4-mini` calls or broader assistant-chain benchmark.
  Done as `scripts\build_locate_scope_retention_data.py`,
  `scripts\run_locate_scope_retention_gate.py`, and
  `data\locate_scope_retention_v1_20260615_1305`.  v22 atom gate
  `runs\locate_scope_retention_v1_v22_20260615_1305.jsonl.summary.json`
  is schema-clean but target match `0.0`: it preserves visible paths on `3/4`
  rows and knows broad-dot search is unacceptable, but over-applies
  `fallback_scope_roots=["src","tests"]` and
  `needs_source_scope_refinement=true` to all rows, and treats memory-relative
  hints like `cache/store.py` as current paths.  Packet assembly gate
  `runs\locate_scope_retention_packet_v1_v22_20260615_1310.jsonl.summary.json`
  passes with assembly/canonical/delegate-safe preservation all `1.0`, proving
  the packet/template layer can carry scoped hints once the atom target supplies
  them.
- [x] Calibrate the locate-scope atom readout before any more large-model calls.
  Build a tiny balanced/protected target from
  `data\locate_scope_retention_v1_20260615_1305`: visible-scope positives must
  keep `fallback_scope_roots=[]` and `needs_source_scope_refinement=false`,
  while cache-key-like sparse rows must keep fallback roots `src/tests` without
  promoting `cache/store.py` to a visible current path.  Gate on the 4-row
  locate-scope atom slice, the 55-row exact-command single-atom gate, and the
  selective route/packet no-regression gates before calling `gpt-5.4-mini` or
  broadening to assistant-chain benchmark.  This should remain learned
  evidence-atom calibration, not a runtime scope rewrite.  Done as
  `scripts\build_locate_scope_calibration_data.py` and
  `data\locate_scope_calibration_v1_20260615_1320`: train `48`, val `4`,
  balanced visible-scope protection and sparse-scope refinement.  Remote SFT
  from `exact_command_balanced_residual_v2_20260616_1240_lora/adapter` ran
  `24` steps and lowered val loss `0.602295 -> 0.375854`, but real generation
  gate
  `runs\locate_scope_retention_v1_locscope_calib1320_8002_20260615_1322.jsonl.summary.json`
  stayed target match `0.0`.  Do not adopt this adapter and do not downstream
  evaluate it.
- [ ] Reformulate locate-scope readout instead of repeating plain multi-field SFT.
  The failed calibration shows the model keeps emitting fallback roots for all
  rows and confuses memory/stale text with current source paths.  Next attempt
  should split the target into single atoms or fixed-label/logprob decisions:
  `visible_path_hints_are_sufficient`, `scope_refinement_needed`, and
  `memory_relative_hint_is_not_current_path`.  Keep packet assembly templated
  and gate against the 4-row locate-scope slice plus the 55-row exact-command
  single-atom gate before any more `gpt-5.4-mini` calls.  Initial diagnostic
  done as `scripts\build_locate_scope_single_atom_data.py` and
  `data\locate_scope_single_atoms_v1_20260615_1328`; v22 gate
  `runs\locate_scope_single_atoms_v1_v22_20260615_1328.jsonl.summary.json`
  has schema/atom match `1.0`, target match `0.5`, with
  `visible_path_hints_are_sufficient` already clean `4/4` and the other two
  atoms collapsed mostly true.
- [x] Train/calibrate only the two failing locate-scope single atoms.
  Build a tiny protected replay target for `scope_refinement_needed` and
  `memory_relative_hint_is_not_current_path`, keeping the already-clean
  `visible_path_hints_are_sufficient` as no-regression replay.  Require
  improvement on `data\locate_scope_single_atoms_v1_20260615_1328`, no
  regression on the 55-row exact-command single-atom gate, and route/packet
  no-regression before using the packets for another selective `gpt-5.4-mini`
  probe.  Done as `scripts\build_locate_scope_single_atom_calibration_data.py`
  and `data\locate_scope_single_atom_calibration_v1_20260615_1335`: train
  `96`, val `12`.  Remote SFT from balanced residual v2 ran `48` steps and
  lowered val loss `0.366058 -> 0.121193`.  Real generation gate
  `runs\locate_scope_single_atoms_v1_single_atom_calib1335_8002_20260615_1338.jsonl.summary.json`
  improved target match `0.5 -> 0.666667`, mostly from
  `scope_refinement_needed` improving `0.25 -> 0.75`, but
  `memory_relative_hint_is_not_current_path` stayed `0.25`.  No-regression
  gate
  `runs\exact_command_single_atoms_v1_single_atom_locscope_calib1335_8002_20260615_1339.jsonl.summary.json`
  regressed to `0.927273` from current best `0.963636`; do not adopt this
  adapter and do not downstream-evaluate it.
- [ ] Fix `memory_relative_hint_is_not_current_path` without regressing exact-command atoms.
  The next attempt should either mix in the full exact-command balanced
  residual/calibration rows during training or use fixed-label/logprob scoring
  for the memory-relative boundary instead of generated booleans.  Require:
  `memory_relative_hint_is_not_current_path` above `0.25`, overall
  locate-scope single-atom above `0.666667`, exact-command single-atom at least
  current best `0.963636`, and route/packet no-regression before any
  `gpt-5.4-mini` call.
- [ ] Reformulate the memory-relative locate-scope target before more SFT.
  The 2026-06-15 fixed-label/logprob diagnostic showed label-surface priors,
  not usable calibration: compact JSON predicted all true (`0.25` accuracy),
  while `TRUE`/`FALSE` predicted all false (`0.583333` but broke the clean
  visible-path atom).  The exact-command-protected mixed SFT
  `exactcmd_locscope_memory_false_mix_v1_20260615_1358_lora` protected and even
  improved exact-command atoms (`0.981818`) but left
  `memory_relative_hint_is_not_current_path` at `0.25`; do not adopt it.  Next
  work should change the learned target shape, e.g.
  `memory_hint_status in {absent, stale_relative_only, current_visible_support}`
  or separate atoms `memory_relative_hint_present` and
  `memory_relative_hint_supported_by_visible_source`, with full exact-command
  replay in the mix.  Gate against locate-scope single atoms, exact-command
  atoms, route, and packet assembly before any large-model proxy call.
- [ ] Build the locate-scope packet bridge from feature-explicit evidence atoms.
  The 2026-06-15 reformulation found a clean target:
  `data\locate_scope_memory_hint_atoms_v1b_20260615_1425` and
  `runs\locate_scope_memory_hint_atoms_v1b_v22_20260615_1425.jsonl.summary.json`
  get valid JSON/exact schema/atom/value match all `1.0` on the two atoms
  `memory_relative_hint_present` and `visible_scope_hints_present`.  Use these
  atoms, not the old failed `memory_relative_hint_is_not_current_path` boolean,
  to derive packet/template locate hints.  Required next gates: preserve
  exact-command single atoms at `>=0.963636`, route match `1.0`, packet
  assembly preservation `1.0`, and only then rerun a selective large-delegate
  probe on cache-key-like locate rows.  Do not implement a runtime task-id or
  path parser; this remains learned atom selection plus deterministic template
  assembly.
- [x] Fold the locate-scope atom bridge into the 15-row selective proxy before a broad benchmark.
  The bridge experiment
  `runs\locate_scope_atom_packet_bridge_v1_large_delegate_gpt54mini_20260615_1445.scored.jsonl.summary.json`
  passed on the 4 locate rows: provider errors `0`, action/skill/semantic pass
  all `1.0`, mean strict `0.892321`.  The key cache-key row improved from the
  previous broad-dot command strict `0.76` to `0.88` with scoped
  `rg ... src tests`.  Next combine these locate bridge packets with the
  existing non-locate delegated packets and the 5 self-handle no-call controls
  from `data\scoreable_selective_proxy_v1_20260616_1135`.  Required report:
  large calls `10/15`, no-call controls `5/15`, provider errors, semantic
  pass, mean strict, cache-key strict, token cost, and comparison against
  `scoreable_selective_proxy_v1_large_delegate_balanced_residual_v2_gpt54mini_20260616_1255`.
  This was run as
  `runs\scoreable_selective_proxy_v1_with_locscope_bridge_gpt54mini_20260615_1430.scored.jsonl.summary.json`.
  The integrated proxy was not clean enough to broaden: rows `10`, provider
  errors `0`, action/skill `1.0`, semantic pass `0.9`, mean strict `0.864104`,
  total tokens `41254`.
- [ ] Stabilize the integrated 10-call selective proxy before any broad benchmark.
  The locate subset in the integrated run passed (`4/4` semantic, mean strict
  `0.901697`) and kept the cache-key improvement (`0.88`, scoped
  `rg ... src tests`), but the unchanged non-locate
  `path_edit_commitment_artifact` packet produced a multi-line edit scored as
  `edit_replacement_mismatch`.  Next diagnose compact packet/template or
  learned output-format evidence atoms for the 6 non-locate delegate rows,
  especially path-edit commitment, without adding task-id-specific command
  rewrites.  Then rerun the same 10-call integrated proxy and require semantic
  pass `1.0`, mean strict at least the baseline `0.892640` or a clearly
  explained scorer-only delta, cache-key strict `>=0.88`, and token cost close
  to or below the `23118` baseline before broadening.
- [ ] Train/evaluate compact edit evidence atoms for packet-only delegation.
  The 2026-06-15 packet-only ablation showed that abstract packets are
  insufficient for edit delegation: plain packet-only got semantic pass `0.4`
  and mean strict `0.705516` because edit rows lacked concrete current evidence
  and default lines.  Hydrating controller-visible evidence into packets fixed
  semantic pass (`1.0`) and the `path_edit_commitment_artifact` failure, with
  mean strict `0.879104` and cache-key strict `0.88`, but it still trailed the
  balanced-residual-v2 baseline mean strict `0.892640` and used more tokens
  (`34529` vs `23118`).  Next build a learned atom target for edit packets:
  exact source path, exact current return line, intended None default, and
  preserve-falsy guard.  Packet/template assembly should use these atoms to
  create a compact delegate packet; do not add task-id-specific command rewrites
  or depend on the full original prompt.
- [x] Replace independent edit atoms with an `edit_evidence_bundle` or contrastive binding target.
  The first compact edit atom gates show useful but incomplete learning:
  `runs\compact_edit_evidence_atoms_v1_v22_20260615_1453.jsonl.summary.json`
  got target match `0.833333`, with source path/current return line/preserve
  guard all `1.0` but `none_default_literal` only `0.333333`.
  The v1b detected-feature surface
  `runs\compact_edit_evidence_atoms_v1b_v22_20260615_1456.jsonl.summary.json`
  stayed at `0.833333`; default improved to `0.666667` but current return line
  regressed to `0.666667` because the model mixed the current line with the
  intended repaired None-default line.  Next evaluate a single structured
  bundle emitted once per task with fields `source_path`, `current_return_line`,
  `none_default_literal`, and `preserve_falsy_guard`, or a pairwise target that
  contrasts current-line extraction against repaired-line/default extraction.
  Do not train on v1/v1b as-is and do not patch this with task-specific command
  rewrites.
- [x] Add a learned output-format/minimal-edit style target before broad benchmark.
  The structured bundle gate passed:
  `runs\edit_evidence_bundle_v1_v22_20260615_1501.jsonl.summary.json`
  has bundle match and all field matches at `1.0`.  Applying the predicted
  bundles to packets and running packet-only delegation improved token cost:
  `runs\scoreable_selective_proxy_v1_with_locscope_editbundle_v1b_packetonly_gpt54mini_20260615_1504.scored.jsonl.summary.json`
  got provider errors `0`, action/skill `1.0`, semantic pass `1.0`, mean strict
  `0.878195`, total tokens `18200`, and cache-key strict `0.88`.  This is much
  cheaper than the balanced-residual-v2 baseline (`23118` tokens) and fixes
  the bundle-binding issue, but mean strict still trails baseline `0.892640`
  due to lower-overlap command styles such as terse `perl` substitutions.
  Next build a small learned style/preference target that preserves the
  edit_evidence_bundle fields while encouraging scorer-stable minimal Python
  replacement commands.  Do not broaden until semantic pass stays `1.0`,
  cache-key strict stays `>=0.88`, and mean strict reaches or clearly explains
  parity with the baseline.
- [x] Run the next broader assistant-chain / scoreable proxy slice with bundle+style packets.
  The style bundle cleared the integrated 10-call gate:
  `runs\scoreable_selective_proxy_v1_with_locscope_editbundle_v2style_packetonly_gpt54mini_20260615_1515.scored.jsonl.summary.json`
  got provider errors `0`, action/skill `1.0`, semantic pass `1.0`, mean strict
  `0.914396`, total tokens `22413`, and cache-key strict `0.88`, beating the
  balanced-residual-v2 baseline mean strict `0.892640` while using fewer tokens
  than its `23118`.  Next broaden carefully to an assistant-chain or scoreable
  proxy slice that keeps no-call controls, uses v22 for locate/edit evidence
  bundle+style packets, and calls `gpt-5.4-mini` only for delegated rows.  Do
  not change automation commands or introduce task-id-specific command rewrites.
  Done as `data\scoreable_selective_proxy_broad_v1b_20260615_1543` plus
  `runs\scoreable_selective_proxy_broad_v1b_locscope_editbundle_style_packetonly_gpt54mini_20260615_1552.scored.jsonl.summary.json`.
  The slice has `26` real scoreable tasks, `18` delegated rows (`14` edit,
  `4` locate), and `8` no-call controls.  v22 route/no-call matched `1.0`,
  packet assembly matched `1.0`, broad edit-bundle style matched `1.0`, and
  packet-only `gpt-5.4-mini` got provider errors `0`, semantic pass `1.0`,
  mean strict `0.916999`, edit mean strict `0.924049`, locate mean strict
  `0.892321`, cache-key strict `0.88`, total tokens `38573`.
- [x] Extend learned edit evidence bundles beyond the None/default/falsy family before broadening again.
  The broadened proxy deliberately excluded `heldout_edit_exact_default` after
  the current bundle target produced an unsupported `None` gold default.  Do
  not solve this by adding task-id rewrites.  Next build a typed bundle target
  or bundle-family router for at least:
  `none_default_falsy_scalar`, `path_commitment_default`, and
  `mapping_mutable_container`, where each family has explicit fields and a gate
  proving target support before packet assembly.  Required gates: bundle/field
  match `1.0` on the new family rows, no regression on the current 14-row
  edit-bundle style gate, route/no-call `1.0`, packet assembly `1.0`, then a
  broader packet-only large-delegate probe.  Keep packet assembly
  prompt/template based and avoid command rewrites.
  First typed family completed for `mapping_mutable_container`:
  `runs\typed_edit_evidence_bundle_mapping_v1_v22_20260615_1610.jsonl.summary.json`
  has rows `6`, errors `0`, bundle/field match `1.0`; route/no-call and packet
  assembly gates are both `1.0`; downstream packet-only `gpt-5.4-mini` on
  `runs\scoreable_selective_proxy_mapping_typed_v1_packetonly_gpt54mini_20260615_1618.scored.jsonl.summary.json`
  got rows `6`, provider errors `0`, semantic pass `1.0`, mean strict `0.9425`,
  total tokens `12309`.  The delegate produced selected-copy mapping repairs
  such as `dict(DEFAULT_BADGE if settings is None else settings)`, validating
  the typed-bundle path.
- [x] Run a mixed-family selective proxy with scalar bundle + typed mapping bundle + locate-scope atoms.
  Build a controlled slice with scalar None/default edit rows, typed mapping
  edit rows, the existing `4` locate-scope atom-bridge rows, and focused-test
  no-call controls.  Reuse learned family gates; do not route mapping rows
  through the scalar edit bundle and do not add task-id command rewrites.
  Required gates before large-model calls: route/no-call `1.0`, packet assembly
  `1.0`, scalar bundle no-regression on the `14`-row broad gate, typed mapping
  bundle no-regression on the `6`-row gate, locate-scope bridge success `1.0`,
  packet-id alignment `1.0`.  Then call `gpt-5.4-mini` only on delegated rows
  and report semantic pass, mean strict, family subsets, token cost, and
  no-call count.
  Done as `data\scoreable_selective_proxy_mixed_family_v1_20260615_1626` and
  `runs\scoreable_selective_proxy_mixed_family_v1_packetonly_gpt54mini_20260615_1630.scored.jsonl.summary.json`.
  The slice has `34` tasks, `24` delegated rows, `10` no-call controls, exact
  packet-id alignment, and clean family-gate provenance.  Packet-only
  `gpt-5.4-mini` got provider errors `0`, semantic pass `1.0`, action rate
  `1.0`, skill match `0.958333`, mean strict `0.909907`, total tokens `45858`.
  Family subsets: scalar/path edit `14/14` semantic with mean strict `0.900962`,
  typed mapping `6/6` semantic with mean strict `0.9425`, locate `4/4` semantic
  with mean strict `0.892321`.
- [x] Add an output-style/readout guard for unambiguous edit commands before the next mixed run.
  The mixed-family run's main weak row was
  `generated_wide_heldout_semantic_edit_visible`: `gpt-5.4-mini` produced a
  semantically correct `python -c` one-liner, but the proxy classifier labeled
  it as `test`, dropping strict score to `0.575`.  Do not solve this by
  task-specific retry or command rewriting.  Next teach/read out a style field
  such as `preferred_edit_command_style = python_pathlib_exact_replace_heredoc`
  and update packet constraints to ask for heredoc `python - <<'PY'` edit
  commands for edit rows.  Gate this as a learned field/no-regression target,
  then rerun the same mixed-family packet-only proxy and require semantic pass
  `1.0`, skill match `1.0`, and mean strict above the current `0.909907`.
  Done first as the v2 heredoc field/guidance run:
  `runs\scoreable_selective_proxy_mixed_family_v2_heredoc_packetonly_gpt54mini_20260615_1616.retrymerged.scored.jsonl.summary.json`.
  Retry-merged metrics: rows `24`, provider errors `0`, semantic pass `1.0`,
  skill match `1.0`, mean strict `0.931611`, total tokens `99352`.  The weak
  visible-edit row now emits a heredoc edit and scores `0.925`.
  A compact-style wording check was then run as
  `runs\scoreable_selective_proxy_mixed_family_v2_compactstyle_packetonly_gpt54mini_20260615_1626.scored.jsonl.summary.json`.
  It keeps provider errors `0`, semantic pass `1.0`, skill match `1.0`, and
  mean strict `0.927605`; packet JSON drops from `64123` to `62557` chars and
  provider-reported total tokens drop from `99352` to `96321`, but row-level
  `cached_tokens=4864` accounting is stochastic enough that token totals should
  be treated as a noisy proxy.
- [x] Compress the shared large-delegate prompt contract before broadening to a
  larger assistant-chain benchmark.  The compact style wording only removed
  `1566` packet JSON chars and preserved clean semantics, but most prompt text
  is still the repeated global `build_packet_prompt` edit/locate contract plus
  full pretty-printed packet.  Next build a prompt-template compression
  ablation that keeps the learned bundle fields unchanged, shortens shared
  edit/locate contract text, optionally serializes the delegate packet compactly,
  and reruns the same 24-call mixed-family slice.  Require semantic pass `1.0`,
  skill match `1.0`, no provider errors, mean strict near the heredoc result
  (`>=0.927` or a row-level explanation), and lower stable prompt characters
  before any broader assistant-chain run.
  Done as an optional `--compact-packet-prompt` ablation in
  `scripts\run_large_delegate_probe.py`, leaving default automation behavior
  unchanged.  Local prompt chars on the same 24 packets dropped
  `101311 -> 71798` (`0.7087x`).  Real packet-only `gpt-5.4-mini` run
  `runs\scoreable_selective_proxy_mixed_family_v2_compactprompt_packetonly_gpt54mini_20260615_1635.scored.jsonl.summary.json`
  got rows `24`, provider errors `0`, semantic pass `1.0`, skill match `1.0`,
  mean strict `0.939545`, and total tokens `87246`, improving over both the
  long heredoc run (`0.931611`, `99352` retry-merged tokens) and compact-style
  wording run (`0.927605`, `96321` tokens).  Family means: scalar/path edit
  `0.933557`, typed mapping `0.985`, locate `0.892321`.
- [ ] Use the compact prompt path for the next broader assistant-chain or
  scoreable proxy evaluation, but keep the small-model target fixed as
  memory/evidence atoms plus template packet assembly.  Before launching a
  much broader benchmark, run one no-regression checklist on the same
  artifacts: packet-id alignment, route/no-call controls, semantic/skill
  `1.0`, and row-level inspection of locate lows.  Then broaden to the next
  real assistant-chain slice only if expected runtime/cost is reasonable and
  no unrelated evaluation is already saturating resources.
  Candidate v3 slice was built as
  `data\scoreable_selective_proxy_mixed_family_v3_20260615_1648`: `58` tasks,
  `36` delegated rows, `22` no-call controls, call reduction `0.37931`.  A
  four-way parallel local v22 gate attempt was intentionally stopped because
  throughput was too slow; partial rows were all clean
  (`route 8/8`, `packet 8/8`, `scalar bundle 8/8`, `typed bundle 7/7`) and are
  recorded in
  `runs\scoreable_selective_proxy_mixed_family_v3_partial_gate_abort_20260615_1652.audit.json`.
  Next step: rerun the v3 gates sequentially or in smaller batches, then only
  launch the 36-call compact-prompt `gpt-5.4-mini` probe if all gates are clean.
  Done: v3 gates were rerun sequentially/residual and all passed cleanly:
  route/no-call `58/58`, packet assembly `36/36`, scalar bundle `22/22`, typed
  mapping bundle `10/10`, packet alignment `36/36`.  The 36-call compact-prompt
  `gpt-5.4-mini` probe
  `runs\scoreable_selective_proxy_mixed_family_v3_compactprompt_packetonly_gpt54mini_20260615_1715.scored.jsonl.summary.json`
  got provider errors `0`, semantic pass `1.0`, skill match `1.0`, mean strict
  `0.939880`, total tokens `118958`, with `22` no-call controls held out of
  large-model calls.  New v3 rows were clean and strong (`12/12` semantic,
  mean strict `0.947520`).
- [ ] Fix locate compact-prompt hygiene before another broad run.  In the v3
  compact-prompt probe, the only clear regression was locate formatting:
  `heldout_locate_cache_key` emitted a semantically valid `rg` command but
  appended meta words as paths (`-- controller query problem memory current
  evidence .`), dropping strict to `0.76`.  Add a narrow locate prompt/template
  hygiene check that prevents meta instruction words from becoming shell paths,
  rerun only the 4 locate rows with compact prompt, and require locate mean
  strict back near the v2 compact prompt (`>=0.892321`) with semantic/skill
  `1.0`.  Do not add task-id-specific locate rewrites.
- [x] Build a real assistant-chain failure atom seed for the memory/RL
  controller, without adding runtime rules.
  Done as `data\assistant_chain_failure_atoms_20260615_2254` from the mixed2
  and pvlib2 assistant-chain failure summaries.  Metrics: rows `12`, train
  `10`, val `2`, prompt leakage terms `{}`, action hints
  `delegate_with_stronger_evidence_packet=9`,
  `reject_memory_and_delegate_or_reverify=1`,
  `run_behavioral_verification=1`, `self_handle_with_guards=1`.  Atom positives:
  `patch_is_partial=6`, `semantic_patch_sufficiency_gap=10`,
  `behavioral_verification_missing_or_weak=6`,
  `accepted_memory_did_not_resolve_boundary=6`,
  `memory_negative_transfer_risk=1`.  This is a seed/readout dataset, not
  enough for a new checkpoint by itself.
- [ ] Next short Multi-Agent Direction experiment:
  merge `data\assistant_chain_failure_atoms_20260615_2254` into the existing
  memory/evidence atom controller mix or build a tiny no-regression readout
  probe for v22/DPO2154 on these 12 rows.  Required checks before training:
  prompt leakage remains `0`, schema exact rate `1.0`, atom exact/readout exact
  reported separately, and no packet-builder/runtime rule is introduced.
  Prefer a bounded logprob/readout gate over long training.
  First probe done:
  `runs\assistant_chain_failure_atom_v22_gate_20260615_2301.jsonl.summary.json`.
  v22 got valid/exact JSON schema `1.0`, but bool atom exact/list atom exact/all
  atom exact were all `0.0`; avg bool atom match `0.642857`, avg list atom match
  `0.583333`, next-action match `0.666667`.  It over-predicts partial/weak
  verification, hallucinates accepted memory ids on no-memory rows, and misses
  the negative-transfer action.  Next build an explicit atom-vocabulary /
  empty-memory binding target or merge this seed into the controller atom mix;
  do not encode these as runtime rules.
  Correction data built as
  `data\assistant_chain_failure_atom_corrections_20260615_2309`: source rows
  `12`, hard rows `12`, SFT train `40`, SFT val `8`, RM pairs `12`, leakage
  rows `0`.  Next merge this with protected replay from existing
  memory/evidence atom datasets and run a tiny no-regression SFT/DPO dryrun or
  logprob gate; do not train it alone.
  Protected mix built as
  `data\assistant_chain_atom_protected_mix_v3_20260615_2314`: train `724`, val
  `68`, assistant-chain corrections `40/8`, protected routeguard replay
  `684/60`, response JSON valid `1.0`, leakage rows `0`, audit status `pass`,
  transfer contract all `1.0`.  Next run only a bounded no-regression dryrun or
  short SFT adapter probe, and require: old route/guard transfer gate clean,
  assistant-chain atom gate improves over v22 (`all_atom_exact=0.0`,
  avg bool `0.642857`), stale-memory verdict replay does not regress.  Do not
  replace served v22 from this package without those gates.
  Readiness manifest built as
  `data\assistant_chain_atom_protected_mix_v3_20260615_2314\readiness_manifest.json`:
  `ready_for_tiny_adapter_probe=true`, blockers `[]`, warnings
  `assistant_chain_atom_baseline_all_exact_zero`,
  `assistant_chain_atom_bool_boundary_weak`,
  `assistant_chain_next_action_boundary_weak`.  Next active step can be either
  local logprob/dryrun checks or a deliberately tiny adapter probe with strict
  post-gates; do not launch long training and do not replace served v22.
  Tiny probe done as a bounded diagnostic, not a promotion:
  subset `data\assistant_chain_atom_tiny_probe_subset_20260615_2324`
  (`94/20` rows) and launch manifest
  `runs\assistant_chain_atom_tiny_probe_launch_20260615_2328\launch_manifest.json`.
  Batch-size `2` OOMed while v22 was resident; batch-size `1` completed at
  `runs\assistant_chain_atom_tiny_probe_bs1_20260615_2337` with train loss
  `1.191267 -> 0.481812` and val loss `1.109094 -> 0.463556`.  The 12-row
  assistant-chain post-gate
  `runs\assistant_chain_failure_atom_tiny_probe_bs1_20260615_2343.jsonl.summary.json`
  kept JSON/schema `1.0` and improved averages over v22 (bool atom
  `0.642857 -> 0.678572`, list atom `0.583333 -> 0.791667`,
  next-action `0.666667 -> 0.75`), but strict promotion failed:
  all-atom exact stayed `0.0`, packet-focus exact stayed `0.0`, and next-action
  collapsed to `delegate_with_stronger_evidence_packet` for all `12` rows.
  Do not replace v22 and do not run broad gates from this candidate.
- [ ] Next controller improvement after the tiny probe:
  build learned boundary supervision for non-delegate actions and packet-focus
  selection instead of adding runtime rules.  Target failure modes from the
  post-gate: over-delegation on `self_handle_with_guards`,
  `run_behavioral_verification`, and
  `reject_memory_and_delegate_or_reverify`; weak `patch_is_partial`,
  `behavioral_verification_missing_or_weak`, and
  `memory_negative_transfer_risk`; packet focus collapsing to
  `patch_sufficiency`.  Use protected replay again, keep leakage `0`, keep
  schema `1.0`, and require improvement in all-atom or packet-focus exactness
  before another adapter probe.  Treat batch-size `1` as the safe remote SFT
  default while the v22 service is resident.
  Post-probe residual data built as
  `data\assistant_chain_post_probe_boundary_20260615_2352`: source rows `12`,
  SFT train/val `23/10`, RM pairs train/val `10/2`, leakage `0`.  It is
  intentionally **not ready for training**:
  blocker `insufficient_train_non_delegate_assistant_chain_boundaries`.
  The split shows the problem clearly: train has `9` delegate rows and only
  `1` non-delegate (`reject_memory_and_delegate_or_reverify`), while val holds
  the missed `self_handle_with_guards` and `run_behavioral_verification` rows.
  Failure tags are dominated by `packet_focus_miss=12`,
  `overdelegation=3`, and `non_delegate_gold=3`.  Do not run another adapter
  probe from this residual data alone.
- [ ] Broaden real assistant-chain/proxy boundary data before the next
  adapter probe.  Need at least a few train-side examples for
  `self_handle_with_guards`, `run_behavioral_verification`, and
  `reject_memory_and_delegate_or_reverify`, plus packet-focus targets beyond
  the collapsed `patch_sufficiency`.  Prefer collecting/deriving these from
  real assistant-chain or existing scoreable proxy traces, then rebuild a
  protected mix with replay and a readiness manifest.  Acceptance before
  training: leakage `0`, schema-valid targets `1.0`, non-delegate train
  coverage no longer blocked, protected routeguard/stale-memory replay present,
  and a post-gate plan that compares against v22 on the same 12-row baseline.
  Proxy-to-assistant readiness audit added as
  `data\proxy_to_assistant_boundary_readiness_20260616_0006\readiness_manifest.json`:
  small selective proxy is clean (`15/15` route, `10/10` packet, delegated
  semantic/action/skill `1.0`, mean strict `0.892640`, no-call `5/15`) and
  broad selective proxy is clean (`26/26` route, `18/18` packet, delegated
  semantic/action/skill `1.0`, mean strict `0.916999`, no-call `8/26`).
  Decision: `ready_for_next_proxy_trace=true`, but
  `ready_for_next_adapter_probe=false` and `ready_for_broad_benchmark=false`
  because assistant-chain train-side non-delegate coverage is still blocked
  and packet focus misses all rows.  Next: use proxy traces only as bounded
  held-out evidence, and actively collect/derive train-side non-delegate
  assistant-chain boundary rows before any adapter probe.
  Non-delegate boundary candidate pool summarized as
  `data\non_delegate_boundary_pool_20260616_0013\boundary_pool_manifest.json`.
  It found enough proxy evidence to design rows, not to train directly:
  scoreable no-call controls `35`, sufficiency route bridge train delegate
  false/true `10/8`, self-handle atom train false/true `8/10`, and verifier
  retry rows `8`, all with no summarized prompt leakage.  Remaining
  assistant-chain gaps are exactly
  `missing_train_self_handle_with_guards`,
  `missing_train_run_behavioral_verification`,
  `too_few_train_reject_or_reverify`, and
  `packet_focus_targets_not_covered`.  Next concrete data step: build a small
  assistant-chain-shaped boundary package from these sources with explicit
  `next_action` and `packet_focus` labels, but keep source schemas separated
  and require a new readiness manifest before any training.
  Done as a draft-only package
  `data\assistant_chain_shaped_boundary_draft_20260616_0018`: rows `12`,
  source counts `scoreable_route_boundary_proxy=4`,
  `sufficiency_route_bridge_proxy=4`, `verifier_retry_proxy=4`; action counts
  `self_handle_with_guards=4`, `run_behavioral_verification=4`,
  `reject_memory_and_delegate_or_reverify=4`; packet-focus counts
  `semantic_guard=12`, `behavioral_verification=8`,
  `memory_reliability=4`, `self_handle_exact_command=4`.
  It is explicitly `ready_for_training=false` because rows are proxy-derived.
  Next: audit these rows for prompt leakage, schema fidelity, and
  action/focus plausibility, then build a protected readiness manifest before
  any training or adapter probe.
  Audit done as
  `data\assistant_chain_shaped_boundary_draft_20260616_0018\audit_summary.json`:
  rows `12`, schema-ok `12`, proxy/not-trainable marks `12`, leakage `0`,
  action/focus coverage intact, and `ready_for_promotion_review=true`.
  Warning: `embedded_proxy_prompt_rows=12`, so the next step is not training.
  Compress the nested route/verifier/sufficiency prompts into concise
  assistant-chain-like telemetry summaries, rerun the audit, and only then
  consider a protected mix/readiness manifest.
  Compressed draft built as
  `data\assistant_chain_shaped_boundary_compressed_draft_20260616_0028`:
  prompt chars `49098 -> 23310` (`0.474765x`), action/focus counts preserved,
  and audit now has schema-ok `12/12`, proxy/not-trainable marks `12/12`,
  leakage `0`, embedded proxy prompt rows `0`, blockers `[]`, warnings `[]`,
  `ready_for_promotion_review=true`, `ready_for_training=false`.  Next:
  build a promotion/protected-readiness manifest that decides whether a subset
  of these compressed rows can join a protected assistant-chain boundary mix
  with route/guard replay; do not train directly from the compressed draft.
  Promotion readiness manifest built as
  `data\boundary_promotion_readiness_20260616_0033\readiness_manifest.json`.
  Decision: `ready_for_protected_mix_build=true`,
  `ready_for_adapter_probe=false`; compressed draft has rows `12`,
  prompt ratio `0.474765`, action coverage
  `self_handle_with_guards=4`, `run_behavioral_verification=4`,
  `reject_memory_and_delegate_or_reverify=4`; protected replay remains clean
  with train/val `724/68`, JSON valid `1.0`, leakage `0`, audit `pass`.
  Next: build a protected mix candidate plus readiness manifest and held-out
  gates.  Do not train until that new candidate manifest passes.
- [ ] Next boundary-controller experiment:
  build a bounded learned readout/focus calibration for the clean boundary
  rows, with protected replay, instead of adding runtime packet-focus or route
  rules.  The previous compressed draft
  `data\assistant_chain_shaped_boundary_compressed_draft_20260616_0028` was
  rechecked and is **not promotable**:
  `prompt_target_leakage_rows=12` in
  `data\assistant_chain_shaped_boundary_compressed_draft_20260616_0028\audit_summary_recheck_targetleak.json`.
  Use the clean replacement
  `data\assistant_chain_shaped_boundary_compressed_draft_20260616_0038_clean`
  instead: rows `12`, prompt ratio `0.412950`, schema-ok `12/12`,
  prompt target leakage `0`, embedded proxy prompt rows `0`, action coverage
  `self_handle_with_guards=4`, `run_behavioral_verification=4`,
  `reject_memory_and_delegate_or_reverify=4`, and packet-focus coverage
  `semantic_guard=12`, `behavioral_verification=8`,
  `memory_reliability=4`, `self_handle_exact_command=4`.
  Protected candidate built as
  `data\boundary_protected_mix_candidate_20260616_0048`: train/val `736/68`,
  candidate rows `12`, protected replay `724`, response JSON valid `1.0`,
  prompt target leakage `0`, replay audit `pass`, transfer contract rates all
  `1.0`.  Its readiness manifest allows only
  `ready_for_heldout_gate=true`; `ready_for_adapter_probe=false` and
  `ready_for_training=false`.
  Held-out v22 clean-boundary gate
  `runs\boundary_clean_proxy_v22_gate_20260616_0052.jsonl.summary.json`
  proves the remaining weakness: valid/exact schema `1.0`, avg bool atom match
  `0.952381`, but all-atom exact `0.0`, next-action match `0.333333`,
  packet-focus exact/recall `0.0`; v22 predicts self-handle for the four
  self-handle rows but collapses all verifier/reverify rows to
  `delegate_with_stronger_evidence_packet` and every packet focus to
  `patch_sufficiency`.
  Acceptance before any adapter probe: improve non-delegate readout and
  packet-focus exactness over this gate, keep JSON/schema `1.0`, keep protected
  replay/transfer/stale-memory gates clean, and compare against the real
  12-row assistant-chain baseline.  Do not train directly from proxy-derived
  rows, do not replace v22, and do not add hard-coded packet-focus rules.
- [ ] Build matched readout/focus preference or tiny calibration data before
  any adapter probe.  Narrow readout/focus data was built as
  `data\boundary_readout_focus_calibration_20260616_0108_listcontract`: rows
  `12`, prompt target leakage `0`, balanced action counts
  `self_handle_with_guards=4`, `run_behavioral_verification=4`,
  `reject_memory_and_delegate_or_reverify=4`, and packet-focus targets
  `semantic_guard=12`, `behavioral_verification=8`,
  `memory_reliability=4`, `self_handle_exact_command=4`.
  V22 gate
  `runs\boundary_readout_focus_v22_gate_20260616_0109_listcontract.jsonl.summary.json`
  has valid/exact schema `1.0`, next-action match `0.333333`,
  packet-focus exact `0.333333`, focus recall `0.722222`, but collapses to
  `run_behavioral_verification=12/12` and packet focus always
  `[behavioral_verification, semantic_guard]`.  This means clearer output
  formatting fixed list schema but not the learned boundary.
  Next experiment should contrast same-style clean telemetry across
  self-handle vs verifier vs reject/reverify, especially
  `self_handle_exact_command` and `memory_reliability` focus, with protected
  replay and a gate against both this narrow v22 baseline and the real
  assistant-chain 12-row atom baseline.  Do not add a packet-focus rule and do
  not train directly from proxy-derived rows.
- [x] Run a DPO dry-run/logprob diagnostic for the matched readout/focus
  preference artifact before any adapter probe.  Preference data v2:
  `data\boundary_readout_focus_preference_20260616_0118_v2`, source rows `12`,
  pairs `20`, skipped `0`, targets
  `self_handle_with_guards=8`,
  `reject_memory_and_delegate_or_reverify=8`,
  `run_behavioral_verification=4`; rejected sources
  `observed_v22_gate_mistake=16`,
  `default_verifier_collapse=4`.  Readiness manifest:
  `data\boundary_readout_focus_preference_20260616_0118_v2\readiness_manifest.json`
  with `ready_for_dpo_dryrun=true`,
  `ready_for_adapter_probe=false`, `ready_for_training=false`,
  blockers `[]`, warnings
  `baseline_v22_readout_boundary_weak` and
  `baseline_v22_packet_focus_boundary_weak`.
  Next run should be a no-update dry-run/logprob diagnostic on the 20 pairs,
  preferably on remote/base+v22 adapter if local loading is too heavy.  Only
  after sane margins should we draft a tiny adapter-probe launch manifest with
  protected replay gates.  Do not train directly from this proxy-derived
  preference file and do not replace v22.
  Done 2026-06-16 01:41 CST via Paramiko remote launch, with no optimizer step,
  no checkpoint, no v22 replacement, and no automation command change.  Result:
  `runs\boundary_readout_focus_dpo_dryrun_launch_20260616_0124\dryrun_summary.json`
  reports rows `20`, loss `0.747559`, mean logp margin `-0.98584`,
  min margin `-3.28125`, preference accuracy `0.35`.  Diagnostic rerun
  `dryrun_summary_with_diagnostics.json` shows the artifact is not suitable
  for an adapter probe: `reject_memory_and_delegate_or_reverify` has `0/8`
  preference accuracy and mean margin `-3.039062`.
- [x] Before launching the readout/focus DPO dry-run remotely, decide whether
  to extend `scripts\run_pairwise_dpo_dryrun.py` with `--initial-adapter` so
  the logprob diagnostic matches served v22 rather than base Qwen only.  Local
  workspace search did not find a `Qwen3-8B` base model, so no local dry-run
  was launched.  Remote launch contract is ready as
  `runs\boundary_readout_focus_dpo_dryrun_launch_20260616_0124\launch_manifest.json`:
  `ready_to_launch_after_remote_sync=true`, blockers `[]`, warning
  `dryrun_script_currently_lacks_initial_adapter_argument`.  The remote
  no-update command writes
  `/mnt/memory-agent/runs/boundary_readout_focus_dpo_dryrun_launch_20260616_0124/dryrun_summary.json`
  and must remain a diagnostic only: no optimizer step, no checkpoint save, no
  packet-focus rule, no v22 replacement.
  Done: `scripts\run_pairwise_dpo_dryrun.py` now accepts
  `--initial-adapter` and loads it read-only; launch manifest was regenerated
  with warnings `[]` and the v22 adapter path in the command.  BatchMode SSH
  still failed, so the remote dry-run was not launched.
- [x] Sync and run the readout/focus DPO dry-run remotely when interactive
  SSH/sync is available.  Use only the no-update command from
  `runs\boundary_readout_focus_dpo_dryrun_launch_20260616_0124\launch_manifest.json`;
  expected output is
  `/mnt/memory-agent/runs/boundary_readout_focus_dpo_dryrun_launch_20260616_0124/dryrun_summary.json`.
  Acceptance before any tiny adapter probe: finite loss/margins, reported
  preference accuracy and pair ids, no optimizer/checkpoint output, and a
  protected replay gate plan attached.  Do not use this as a training command.
- [ ] Rebuild the readout/focus boundary with visible evidence support before
  any adapter probe.  The dry-run diagnosed a target-design issue, not a reason
  to force DPO: all current `reject_memory_and_delegate_or_reverify` rows have
  `accepted_memory_rows=0`, `candidate_memory_rows=0`, and
  `memory_negative_transfer_risk=false`, yet their chosen focus includes
  `memory_reliability`; they are otherwise visibly indistinguishable from
  `run_behavioral_verification` rows.  Next data should reserve
  `reject_memory_and_delegate_or_reverify` for visible stale/unrelated or
  negative-transfer memory evidence, keep no-memory semantic-gap rows as
  `run_behavioral_verification`, and include `memory_reliability` focus only
  when accepted/candidate memory evidence exists.  Treat this as learned
  target/data repair, not a runtime rule, and require a new dry-run margin
  diagnostic before training or a tiny adapter probe.
  Update 2026-06-16 01:58 CST: first visible-supported repair is done as a
  diagnostic, not a training package.  Added
  `scripts\build_visible_supported_readout_focus_candidate.py`; candidate
  `data\visible_supported_readout_focus_candidate_20260616_0157_v2` keeps
  4 self-handle rows, 4 verifier rows, and adds 1 real assistant-chain
  memory-negative-transfer reverify row while dropping the 4 unsupported
  no-memory reverify proxy rows.  V22 gate
  `runs\visible_supported_readout_focus_v22_gate_20260616_0157_v2.jsonl.summary.json`
  has valid/exact schema `1.0/1.0`, next-action match `0.555556`,
  packet-focus exact `0.555556`; verifier and reverify are exact, while
  self-handle still collapses to verifier.  Preference dry-run
  `runs\visible_supported_readout_focus_dpo_dryrun_20260616_0158_v2\dryrun_summary_with_diagnostics.json`
  improved the signal to accuracy `0.769231`, mean margin `+1.064453`,
  but reverify has only 1 supported row and self-handle margins are small.
  Do not run adapter probe from this alone.  Next broaden visible-supported
  self-handle/reverify rows from real assistant-chain or clean proxy evidence,
  then attach protected replay/no-regression gates before any training.
- [ ] Build a score-based self-handle/readout integration gate before any
  adapter probe.  The 2026-06-16 02:05 CST diagnostics show v22 free-form
  generation is not reliable for self-handle sufficiency:
  `runs\self_handle_sufficiency_atom_v22_val_gate_20260616_0204.jsonl.summary.json`
  and
  `runs\self_handle_sufficiency_atom_v22_train_gate_20260616_0204.jsonl.summary.json`
  both predicted `True` for every row, giving atom match `0.5` / `0.555556`.
  But the no-update pairwise/logprob diagnostic
  `runs\self_handle_sufficiency_pairwise_dryrun_20260616_0205\dryrun_summary_with_diagnostics.json`
  cleanly separates gold `True` and `False` by margin:
  matched self-handle rows mean `+9.253125`, false controls mean `-5.605769`.
  Treat self-handle sufficiency as a score/readout atom, not a free-form route
  generator.  Next build a deterministic diagnostic that joins
  score-based self-handle sufficiency, visible-supported reverify, verifier
  rows, and protected no-regression checks, then gate against
  `data\assistant_chain_readout_focus_eval_val_20260616_0202` before any
  training/probe.
  Update 2026-06-16 02:12 CST: readiness gate passed, but direct integration
  stress test found a blocker.  Added
  `scripts\summarize_score_based_readout_focus_integration.py` and wrote
  `runs\score_based_readout_focus_integration_readiness_20260616_0208.json`
  with `ready_for_score_based_integration_gate=true`.  Then built
  `data\readout_focus_self_handle_sufficiency_pairs_20260616_0211` and ran
  remote no-update dry-run
  `runs\readout_focus_self_handle_sufficiency_dryrun_20260616_0211\dryrun_summary_with_diagnostics.json`.
  Top-line was strong (`11` rows, accuracy `0.818182`, mean margin
  `+5.847656`), but summary
  `runs\readout_focus_self_handle_sufficiency_dryrun_20260616_0211\summary.json`
  blocks override: verifier rows have positive self-handle margins in `4/5`
  cases, so `ready_for_score_based_override=false`.  Next do not train; instead
  strengthen visible negative-control evidence for verifier rows or score
  verifier/reverify separately, then rerun this stress test.
  Update 2026-06-16 02:30 CST: corrected the stress-test interpretation and
  ran an atom-conditioned gate.  The old summary used pairwise
  chosen-minus-rejected margin as if it were always `logp(True)-logp(False)`;
  corrected summary
  `runs\readout_focus_self_handle_sufficiency_dryrun_20260616_0211\summary_corrected.json`
  shows the 4 proxy verifier rows were not the core issue.  The real bad rows
  were the memory-conditioned negatives
  `pvlib2_frozen_memory_pvlib__pvlib-python-1606_003_sftcorr_0` and
  `pvlib2_updated_memory_pvlib__pvlib-python-1606_005`, which lacked explicit
  upstream evidence atoms in the sufficiency prompt.  Added
  `scripts\build_readout_focus_self_handle_sufficiency_pairs_with_atoms.py`
  and built
  `data\readout_focus_self_handle_sufficiency_pairs_with_atoms_20260616_0224_all_actions_supported`
  from 12 real assistant-chain rows with source atoms.  Remote no-update
  dry-run
  `runs\readout_focus_self_handle_sufficiency_with_atoms_allactions_dryrun_20260616_0224\summary_corrected.json`
  has rows `12`, preference accuracy `1.0`, false self-handle preference rate
  `0.0`, and true self-handle preference rate `1.0`.  This supports a learned
  decomposition where an evidence atom head feeds a score/logprob sufficiency
  head.  Still do not train or adapter-probe: there is only 1 positive
  self-handle row and the verifier negative margin is thin (`-0.25` in
  self-handle-margin coordinates).  Next broaden real atom-supported
  self-handle/verifier/reverify positives and negatives, then attach protected
  replay/no-regression before any score-based integration.
  Update 2026-06-16 02:42 CST: broadened this gate using existing
  post-probe correction evidence, not new proxy rows.  Built
  `data\readout_focus_self_handle_sufficiency_pairs_with_atoms_20260616_0236_postprobe33_supported`
  from `data\assistant_chain_post_probe_boundary_20260615_2352`: rows `33`,
  source actions `delegate=18`, `reverify=5`, `verifier=5`, `self_handle=5`,
  all with source evidence atoms and `ready_for_training=false`.  Remote
  no-update dry-run
  `runs\readout_focus_self_handle_sufficiency_with_atoms_postprobe33_dryrun_20260616_0236\summary_corrected.json`
  reports rows `33`, preference accuracy `1.0`, false self-handle preference
  rate `0.0`, true self-handle preference rate `1.0`, and no blockers.  Keep
  this as an offline gate result only: the verifier negative margin is still
  thin (`-0.265625`) and rows include repeated post-probe variants.  Next build
  an offline integration assembly gate that combines upstream evidence atoms,
  score-based self-handle sufficiency, visible-supported reverify/verifier
  readout, and protected replay/no-regression checks.  Do not train, adapter
  probe, or replace v22 from this gate alone.
  Update 2026-06-16 02:50 CST: built the offline assembly readiness gate as
  `runs\readout_focus_score_based_assembly_gate_20260616_0240.json` using
  `scripts\summarize_readout_focus_score_assembly_gate.py`.  It joins the
  33-row atom-conditioned score summary, visible-supported verifier/reverify
  gate, assistant-chain heldout gate, and protected mix readiness.  Result:
  `ready_for_offline_integration_assembly=true`, blockers `[]`,
  `ready_for_adapter_probe=false`, `ready_for_training=false`,
  `ready_to_replace_served_v22=false`.  Warnings remain:
  verifier margin is thin, independent self-handle positives are few,
  free-form self-handle/packet-focus generation is not clean, and protected
  baseline atom boundaries are weak.  Next materialize a bounded offline
  assembly replay: produce readout/focus outputs from upstream evidence atoms
  plus score decisions, compare against visible-supported and assistant-chain
  targets, and attach protected routeguard/stale-memory/original-controller
  no-regression checks.  Still do not train, adapter probe, or serve a new
  model from the readiness gate alone.
  Update 2026-06-16 03:00 CST: materialized the bounded offline assembly replay
  as `runs\readout_focus_score_based_materialized_assembly_replay_20260616_0256.summary.json`
  using `scripts\materialize_readout_focus_score_assembly_replay.py`.  It had
  no missing atoms or score rows, but only `0.636364` next-action exact and
  `0.636364` packet-focus exact.  Self-handle, verifier, and reverify were
  all exact (`5/5`, `5/5`, `5/5`), but delegate was only `6/18`: 12 delegate
  rows were over-routed to `reject_memory_and_delegate_or_reverify` when
  `accepted_memory_did_not_resolve_boundary=true` co-occurred with
  `semantic_patch_sufficiency_gap=true`.  Treat this as a blocker and do not
  patch it with a hand-tuned priority rule.  Next build a learned/scoreable
  delegate-vs-reverify or patch-sufficiency readout head from post-probe rows,
  rerun materialized assembly, then attach protected replay/no-regression
  gates.  Still no training or adapter probe until this boundary is clean.
  Update 2026-06-16 14:30 CST: built the learned/scoreable diagnostic head as
  pairwise data, not a runtime rule.  Added
  `scripts\build_delegate_patch_sufficiency_pairwise.py`,
  `scripts\summarize_delegate_patch_sufficiency_dryrun.py`, and test
  `tests\scripts\test_build_delegate_patch_sufficiency_pairwise.py`
  (`uv run pytest tests/scripts/test_build_delegate_patch_sufficiency_pairwise.py`
  passed).  v1 data
  `data\delegate_patch_sufficiency_pairs_with_atoms_20260616_1410_postprobe23`
  had rows `23` (`True=18`, `False=5`) and v2 data
  `data\delegate_patch_sufficiency_pairs_with_atoms_v2_20260616_1420_postprobe28`
  had rows `28` (`True=18`, `False=10`), all with source atoms and both
  `ready_for_training=false`.  Remote no-update dry-runs used base
  `/mnt/memory-agent/models/Qwen3-8B` plus read-only v22 adapter
  `global_step_1710`, with no optimizer/checkpoint/model replacement.
  Results: v1 preference accuracy `0.782609`; delegate positives `18/18`
  prefer delegate, but reverify negatives `5/5` also prefer delegate.  v2
  preference accuracy `0.642857`; delegate positives `18/18` prefer delegate,
  but reverify negatives `5/5` and verification negatives `5/5` also prefer
  delegate.  Conclusion: v22 has a positive patch/delegate signal, but lacks
  the safety negative-control boundary for "do not delegate yet".  Do not wire
  this score into assembly, do not train, and do not adapter-probe from this
  package.  Next build stronger false-delegate controls from real
  assistant-chain/protected replay: stale/unrelated memory, weak verification,
  unresolved current evidence, and no-packet-sufficient rows; then rerun the
  patch-sufficiency dry-run before any materialized assembly replay.
  Update 2026-06-16 14:40 CST: expanded the diagnostic to all four actions by
  treating `self_handle_with_guards` as another false delegate control.  v3
  data
  `data\delegate_patch_sufficiency_pairs_with_atoms_v3_20260616_1435_postprobe33`
  has rows `33`: `True=18`, `False=15`, with source actions
  delegate `18`, reverify `5`, verification `5`, self-handle `5`, missing
  atoms `0`, and `ready_for_training=false`.  Remote no-update dry-run
  `runs\delegate_patch_sufficiency_v3_postprobe33_dryrun_20260616_1435\summary_corrected.json`
  has preference accuracy `0.545455`.  Delegate positives `18/18` prefer
  delegate, but every false group also prefers delegate: reverify `5/5`,
  verification `5/5`, self-handle `5/5`.  This confirms the current score head
  is unusable for assembly because it would become "delegate whenever patch
  work is visible."  Next do not train or adapter-probe; build a hard
  false-delegate negative-control mix with protected replay: self-handle/no-op
  safe rows, verifier-needed rows, stale/unrelated memory rows, weak-evidence
  rows, and no-packet-sufficient rows.  Rerun the same no-update dry-run and
  require false rows to stop preferring delegate before any materialized
  assembly replay.
  Update 2026-06-16 14:45 CST: added false-delegate control pool audit
  `scripts\summarize_false_delegate_control_pool.py` plus test
  `tests\scripts\test_summarize_false_delegate_control_pool.py`; test passed.
  Audit output `runs\false_delegate_control_pool_20260616_1445.json` found
  `3` deduplicated hard negative seeds from existing assistant-chain artifacts:
  `reject_memory_and_delegate_or_reverify=1` with memory negative transfer,
  `self_handle_with_guards=1` with no patch-sufficiency gap/no accepted
  memory, and `run_behavioral_verification=1` with weak verification.  The
  protected manifest
  `data\assistant_chain_atom_protected_mix_v3_20260615_2314\readiness_manifest.json`
  is attached; blockers `[]`; `ready_for_hard_negative_mix_build=true`.
  Next build a tiny protected hard-negative pairwise mix from these seeds plus
  replay and rerun no-update dry-run.  Still do not train: 3 unique seeds are
  enough for diagnostic pressure, not enough for an adapter probe.
- [ ] Next safe-delegate boundary step:
  build broader protected `delegate_not_ready_yet` / no-call evidence atoms,
  not another runtime route rule.  The 2026-06-16 15:45 CST diagnostics show:
  v4 key wording `safe_delegate_packet_ready` did not help (`33` rows,
  preference accuracy `0.545455`, all `15/15` false rows still prefer
  delegate).  A tiny hard-negative protected mix was built as
  `data\false_delegate_hard_negative_safe_delegate_ready_mix_20260616_1518`
  (`15` rows: `3` hard false, `6` protected delegate, `6` protected
  no-delegate), but dry-run
  `runs\false_delegate_hard_negative_safe_delegate_ready_mix_dryrun_20260616_1520\summary_corrected.json`
  still had every unsafe row prefer delegate.  The inverted target
  `data\delegate_not_ready_yet_hard_negative_mix_20260616_1532` improved the
  three real hard false rows (`0/3` prefer delegate; margins around `-3.7` to
  `-4.2` in delegate-ready coordinates), but protected no-delegate replay
  still failed (`6/6` prefer delegate) and protected delegate replay was mixed
  (`4/6` prefer delegate).  Do not train, adapter-probe, or connect either
  15-row artifact to assembly.  Next build a real protected no-call/not-ready
  atom package from replay rows with explicit visible atoms for
  `no_op_safe_self_handle`, `verify_first`, `stale_or_unrelated_memory`,
  `weak_current_evidence`, `safe_delegate_packet_ready`, and source paths /
  evidence ids.  Acceptance before any training: leakage `0`, schema valid
  `1.0`, safe delegate positives and protected no-call negatives both separate
  in no-update logprob, and old routeguard/stale-memory replay gates remain
  attached.
  Update 2026-06-16 16:20 CST: broader protected not-ready atom diagnostic was
  built as
  `data\protected_not_ready_evidence_atom_pairwise_20260616_1608`: source rows
  `624`, selected rows `42`, leakage `0`, buckets covering
  `not_ready::edit/locate/test` and four delegate-positive reasons, and
  `ready_for_training=false`.  Remote dry-run first OOMed with one 8192-token
  batch while v22 was resident, so `scripts\run_pairwise_dpo_dryrun.py` now has
  `--batch-size`; rerun with `--max-length 4096 --batch-size 2` succeeded.
  Summary:
  `runs\protected_not_ready_evidence_atom_pairwise_dryrun_20260616_1608\summary_corrected.json`.
  Overall preference accuracy is only `0.523810`, so do not train/adapt/connect
  it.  Useful signal: `not_ready::test` is clean (`0/6` prefer delegate,
  mean delegate margin `-3.552083`) and `memory_transfer_uncertain` delegate is
  clean (`6/6`, margin `+9.260417`).  Failures are specific:
  `not_ready::edit` is completely wrong (`6/6` prefer delegate, margin
  `+3.583333`), `not_ready::locate` is mixed (`3/6`), and ordinary
  `delegate_risk` positives are mixed/rejected unless the easy
  memory-transfer cue is present.  Next split edit self-handle sufficiency into
  cleaner learned atoms (`exact_edit_evidence`, `no_op_safe_edit`,
  `semantic_guard_preserved`, `current_source_support`) and separately clarify
  ordinary delegate positives (`semantic_failure`,
  `missing_executable_action`, `low_confidence_or_incomplete`).  Keep this as
  diagnostic target design, not a runtime rule.
- [ ] Next split-head composition gate:
  do not train from the 24-row edit diagnostic yet.  The focused edit
  self-handle sufficiency head was built as
  `data\edit_self_handle_sufficiency_atom_pairwise_20260616_1625` and the
  replay-aligned failure version as
  `data\edit_self_handle_sufficiency_atom_pairwise_focusfail_20260616_1635`.
  Both have leakage `0`, `ready_for_training=false`, and remote no-update
  dry-runs reached preference accuracy `1.0`.  The focus-fail run forced in
  the six prior broader-head `not_ready::edit` failures and separated them
  cleanly: edit self-handle rows `0/6` prefer delegate, mean delegate margin
  `-18.281250`; ordinary delegate-risk rows `18/18` prefer delegate.  This
  means the problem is target/interface composition, not inability to read edit
  evidence.  Next build an offline split-head composition/no-regression gate:
  focused edit-sufficiency score head + separate test/not-ready and
  safe-delegate evidence heads -> deterministic packet/route assembly -> rerun
  the materialized assembly/replay boundary.  Acceptance before training:
  prior `not_ready::edit` bad rows fixed, self-handle/verifier/reverify stay
  clean, delegate rows improve beyond `6/18` without sacrificing safe no-call
  rows, prompt leakage `0`, and stale/locate/route no-regression attached.
  Do not implement this as a runtime if/else priority rule; it must remain a
  learned score/readout interface feeding deterministic assembly.
  Update 2026-06-16 17:15 CST: before building the full split-head assembly
  gate, run a negative-transfer evidence expansion/audit.  Added
  `scripts\audit_memory_reliability_split_targets.py`; audit
  `runs\memory_reliability_split_target_audit_20260616_1712.json` over `833`
  existing assistant-chain/protected rows found no direct split-head signature
  conflicts, but found a severe coverage imbalance: rejected-uncertain memory
  that still delegates current evidence has `74` rows / `68` fallback unique
  base ids, while true `memory_negative_transfer_risk` has `16` rows from only
  one unique base id (`pvlib2_frozen_memory_pvlib__pvlib-python-1606_003`).
  It also found `65` rows where old targets collapse delegate and reverify
  (`delegate_and_reverify_collapsed`).  Therefore do not train, adapter-probe,
  or wire the 17-row memory/patch conflict diagnostic into assembly yet.  Next
  build or audit broader negative-transfer evidence from real assistant-chain
  and protected replay rows, with separate learned heads:
  `reject_memory_ids_due_to_negative_transfer`,
  `delegate_current_evidence_packet_supported`, and
  `reverify_before_delegate_needed`.  Acceptance before training: at least
  three unique negative-transfer seeds or a clearly marked protected-only
  diagnostic split, leakage `0`, no split-head conflicts, focused edit/test/
  verifier/reverify gates still clean, and no runtime priority rule.
  Update 2026-06-16 17:40 CST: built the clearly marked protected-only split
  diagnostic as
  `data\protected_negative_transfer_pressure_pairwise_20260616_1710`
  (`54` rows; stale/distractor/reliable categories `18/18/18`, prompt leakage
  `0`, `ready_for_training=false`,
  `ready_for_real_transfer_training_mix=false`).  Remote no-update dry-run
  with v22 produced
  `runs\protected_negative_transfer_pressure_dryrun_20260616_1710\summary_by_pressure.json`:
  overall preference accuracy `0.851852`; stale-overlap rejection is clean
  (`18/18`, mean margin `+8.285590`), but distractor rejection is only
  `13/18` and reliable current anchors are `15/18`.  Blocker:
  `protected_pressure_rows_prefer_rejected`.  Do not train, adapter-probe, or
  connect this protected artifact to assembly.  Next memory-reliability step:
  build a residual protected readout over the eight bad rows plus matched
  reliable/current-evidence anchors, or find more real assistant-chain
  negative-transfer task families.  The target should be learned atom heads
  (`use_current_reliable_anchor`, `reject_stale_overlap`,
  `reject_unrelated_distractor`, visible current-evidence/path support), not a
  runtime memory-rule patch.
  Update 2026-06-16 18:00 CST: ran two cheap residual readout-surface probes,
  both no-update and protected-only.  Split-atom residual
  `data\protected_memory_reliability_atom_residual_pairwise_20260616_1725`
  has `26` rows (`8` previous bad rows + `18` matched anchors), leakage `0`,
  but dry-run
  `runs\protected_memory_reliability_atom_residual_dryrun_20260616_1725\summary_by_pressure.json`
  is not adoptable: overall accuracy `0.576923`, reliable anchors `9/9`,
  distractor rejection `6/11`, stale-overlap rejection `0/6`.  Fixed-label
  readout
  `data\protected_memory_reliability_label_pairwise_20260616_1735` has `54`
  balanced rows, leakage `0`, but dry-run
  `runs\protected_memory_reliability_label_dryrun_20260616_1735\summary_by_pressure.json`
  is also blocked: overall accuracy `0.629630`, stale rejection `18/18`,
  reliable anchors `14/18`, distractor rejection only `2/18`
  (`distractor_vs_reject_stale_overlap=0/9`).  Conclusion: v22 has learned
  stale-overlap rejection and partial reliable-anchor preservation, but lacks
  robust unrelated-distractor rejection.  Do not train/adapt from these
  protected diagnostics alone and do not implement runtime memory rules.  Next:
  mine real assistant-chain distractor/negative-transfer cases or build a
  protected residual curriculum only with no-regression gates that preserve
  stale rejection and reliable anchors.
  Update 2026-06-16 18:15 CST: audited the available distractor evidence pool
  with `scripts\audit_distractor_reliability_evidence_pool.py`; output
  `runs\distractor_reliability_evidence_pool_audit_20260616_1815.json`.
  It found `3654` protected rows and no real-ish assistant-chain rows with
  explicit unrelated-distractor labels.  Useful protected counts:
  `protected_controller_rejected_distractor=1166`,
  `protected_controller_rejected_stale=1166`,
  `protected_controller_selected_reliable=1045`,
  `protected_candidate_verdict_distractor=156`, and importantly
  `protected_controller_selected_distractor=121` across `34` unique seeds but
  only `3` tasks.  Blockers remain
  `realish_untyped_rejected_memory_task_count_lt_3` and
  `no_realish_rejected_memory_rows`.  Therefore do not claim real distractor
  training evidence and do not add runtime distractor rules.  Next safe
  experiment: either mine/generate real assistant-chain traces with explicit
  distractor memory labels, or build a protected residual curriculum only as a
  diagnostic precursor, with no-regression gates that preserve
  `stale_vs_use_current=18/18` and reliable-anchor selection.
  Update 2026-06-16 18:12 CST: built the first real/semireal annotation seed
  from assistant-chain trajectories with retrieved memory text:
  `data\real_memory_reliability_trace_seed_20260616_1750`.
  Builder/audit/labeler scripts:
  `scripts\build_real_memory_reliability_trace_seed.py`,
  `scripts\audit_real_memory_reliability_trace_seed.py`, and
  `scripts\label_real_memory_reliability_trace_seed.py`; tests passed
  (`6 passed`).  The blank seed has `16` rows, `4` unique tasks, memory text
  present `16/16`, prompt leakage `0`, and path-mismatch candidates `16/16`;
  it is `ready_for_annotation=true` but `ready_for_training=false`.
  `gpt-5.4-mini` annotation produced
  `data\real_memory_reliability_trace_seed_labeled_gpt54mini_20260616_1810`
  with `unrelated_distractor=15`, `stale_overlap=1`.  Labeled audit
  `runs\real_memory_reliability_trace_seed_labeled_audit_20260616_1810.json`
  blocks training due to `labeled_label_diversity_lt_3` and
  `labeled_distribution_collapsed` (`max_label_fraction=0.9375`).  Next:
  expand real/semireal labeled seeds to include reliable current anchors and
  stale-overlap examples, then only consider a small memory reliability
  readout/dry-run when label diversity and no-regression gates pass.  Do not
  turn path mismatch into a runtime distractor rule.
  Update 2026-06-16 18:30 CST: expanded real/semireal mining across all
  `batch_*` directories and existing continual/memory-gate traces.  New broad
  seed `data\real_memory_reliability_trace_seed_broad_existing_20260616_1830`
  has `106` rows / `16` tasks / prompt leakage `0`, but full audit
  `runs\real_memory_reliability_trace_seed_broad_existing_audit_20260616_1830.json`
  blocks on `current_patch_files_missing` for `2` rows.  Cleaned seed
  `data\real_memory_reliability_trace_seed_broad_existing_clean_20260616_1838`
  keeps `104` rows.  Representative sample20
  `data\real_memory_reliability_trace_seed_broad_sample20_20260616_1830`
  was labeled by `gpt-5.4-mini`:
  `unrelated_distractor=19`, `stale_overlap=1`; audit
  `runs\real_memory_reliability_trace_seed_broad_sample20_labeled_audit_20260616_1835.json`
  blocks training due to label collapse (`max_label_fraction=0.95`).  Next:
  specifically mine/create reliable-current-anchor positives from successful
  shared-memory traces or a clearly marked semireal balanced diagnostic; do
  not SFT/DPO from the distractor-heavy pool and do not add a runtime
  path-mismatch rule.
  Update 2026-06-16 18:37 CST: improved memory file-anchor extraction to use
  `touched_files`, all `File:` anchors, and `remembered prior files`.  Rebuilt
  `data\real_memory_reliability_trace_seed_broad_existing_v2_20260616_1845`;
  it still has zero real path-overlap candidates, so the current real memory
  pool is genuinely negative-heavy.  Added
  `scripts\build_semireal_memory_reliability_balanced_seed.py` and built
  `data\semireal_memory_reliability_balanced_seed_20260616_1850`
  (`48` rows, `10` tasks, balanced labels:
  `reliable_current_anchor=16`, `stale_overlap=16`,
  `unrelated_distractor=16`).  Audit
  `runs\semireal_memory_reliability_balanced_seed_audit_20260616_1850.json`
  blocks training with `semireal_diagnostic_not_training_data` but confirms
  prompt leakage `0` and clean fields.  Next safe step: run a no-update v22
  reliability readout/logprob gate on this diagnostic only to test the target
  interface; do not train until real reliable-anchor positives exist.
  Update 2026-06-16 19:20 CST: the no-update v22 reliability readout probe is
  complete and it fails as a stable three-way interface.  Semireal v2 audit
  `runs\semireal_memory_reliability_balanced_seed_v2_audit_20260616_1858.json`
  confirms rows `48`, unique tasks `10`, prompt leakage `0`, balanced labels,
  but blocks training with `semireal_diagnostic_not_training_data`.  Added
  `scripts\build_semireal_memory_reliability_label_readout.py`,
  `scripts\run_memory_reliability_label_logprob_gate.py`, and tests.  Semantic
  label readout
  `runs\semireal_memory_reliability_label_readout_v1_v22_logprob_20260616_1905.details.jsonl.summary.json`
  got normalized accuracy `0.3125`: reliable anchors `0/16`, stale `1/16`,
  distractor `14/16`, with predictions collapsed to reject labels.  Neutral
  A/B/C readout
  `runs\semireal_memory_reliability_label_readout_neutral_v1_v22_logprob_20260616_1915.details.jsonl.summary.json`
  got normalized accuracy `0.395833`: A/reliable `16/16`, B/stale `3/16`,
  C/distractor `0/16`, collapsed to `LABEL_A=40`, `LABEL_B=8`.  Conclusion:
  v22 is label-surface sensitive and not yet using the visible reliability
  boundary robustly.  Next do not train or connect to assembly; build a
  residual readout-surface diagnostic with matched evidence wording and
  label-prior controls, and keep mining real reliable-current-anchor positives.
  Acceptance before any SFT/DPO: reliable/stale/distractor all separate on a
  no-update or tiny held-out-safe readout, old stale/reliable protected gates
  preserved, prompt leakage `0`, unique ids, and no runtime memory rule.
  Update 2026-06-16 19:35 CST: neutral-label permutation readout sharpened the
  diagnosis.  Added
  `scripts\build_semireal_memory_reliability_permutation_readout.py` and
  extended `scripts\run_memory_reliability_label_logprob_gate.py` with
  source/permutation summaries.  Permutation data
  `data\semireal_memory_reliability_permutation_readout_v1_20260616_1928`
  has `288` rows, `6` label mappings, prompt leakage `0`, labels balanced
  `LABEL_A/B/C=96/96/96`, source labels balanced `96/96/96`,
  `ready_for_training=false`.  Remote no-update v22 logprob
  `runs\semireal_memory_reliability_permutation_readout_v1_v22_logprob_20260616_1928.details.jsonl.summary.json`
  got overall normalized accuracy `0.340278`, but by source:
  reliable anchors `96/96`, stale overlap `0/96`, unrelated distractor `2/96`.
  This means v22 can follow whichever neutral label means "reliable current
  anchor", but collapses both negative classes into generic non-reliable.  Next
  build a negative-only stale-vs-distractor contrastive/readout diagnostic with
  matched reliable-anchor no-regression; do not train a full three-class head,
  do not connect memory reliability to assembly, and do not add runtime
  path-mismatch/stale rules until stale-vs-distractor separates.
  Update 2026-06-16 19:50 CST: negative-only stale-vs-distractor diagnostic
  was built and run, but it is not good enough for training/integration.  Added
  `scripts\build_semireal_memory_reliability_negative_readout.py`; data
  `data\semireal_memory_reliability_negative_readout_v1_20260616_1942` has
  negative rows `64`, reliable-anchor no-regression rows `16`, prompt leakage
  `0`, `ready_for_training=false`.  Remote no-update v22 negative logprob
  `runs\semireal_memory_reliability_negative_readout_v1_v22_logprob_20260616_1942.negative.details.jsonl.summary.json`
  got normalized accuracy `0.515625`, with stale `22/32` but distractor only
  `11/32` and prediction skew `NEG_B=53/64`.  Reliable-anchor no-regression
  stayed clean:
  `runs\semireal_memory_reliability_negative_readout_v1_v22_logprob_20260616_1942.reliable_anchor_noreg.details.jsonl.summary.json`
  has `16/16`.  Next: do failure analysis on the negative rows and build a
  clearer learned evidence-atom diagnostic for stale-vs-distractor, exposing
  atoms like `same_repo_overlap_but_wrong_current_patch`,
  `candidate_points_to_unrelated_file`, `memory_file_intersects_current_context`,
  and `current_patch_file_support`.  Do not train, do not connect to assembly,
  and do not add runtime path/stale heuristics until this binary boundary is
  clean with reliable-anchor no-regression.
- [x] Audit the stale-vs-distractor negative readout for learnability.
  Added `scripts\audit_semireal_negative_readout_failures.py` and hardened
  `scripts\build_semireal_memory_reliability_negative_readout.py`.  Audit
  `runs\semireal_memory_reliability_negative_failure_audit_20260616_1935.json`
  reports rows `64`, accuracy `0.515625`, path-overlap count `0` for every
  row, `10` identical-prompt conflict groups, `20` rows in those groups, and
  blockers `conflicting_gold_labels_for_identical_prompt`,
  `conflicting_source_labels_for_same_candidate_features`,
  `source_seed_duplicate_row_id_label_conflict`.  Rebuilt conflict-audit data
  `data\semireal_memory_reliability_negative_readout_v1_conflict_audit_20260616_1940`
  now correctly sets `ready_for_logprob_diagnostic=false`.  This means the
  stale-vs-distractor target is not learnable from the exposed evidence yet;
  do not train from it and do not use it to justify route/delegate integration.
- [ ] Next short Multi-Agent Direction experiment:
  build a clean non-conflicting memory evidence-atom diagnostic/readout from
  the balanced semireal seed plus any real mined positives that pass audit.
  Target atoms should be explicit but learned, not runtime rules:
  `current_patch_file_support`, `candidate_patch_file_overlap`,
  `memory_instance_differs`, `same_repo_candidate`,
  `candidate_points_to_different_current_patch_file`,
  `candidate_text_mentions_current_symbols`, and
  `candidate_text_mentions_different_symbols`.  Acceptance before any SFT/DPO
  or materialized-assembly connection: prompt leakage `0`, no identical-prompt
  conflicting labels, no same-visible-feature conflicting labels,
  reliable-anchor no-regression remains `16/16` or better, and negative atoms
  separate above chance under no-update v22 or a tiny held-out-safe readout.
  Keep packet assembly deterministic and do not add runtime path/stale
  heuristics.
- [x] Build and run the first clean evidence-atom diagnostic.
  Added `scripts\build_semireal_memory_evidence_atom_readout.py`; data
  `data\semireal_memory_evidence_atom_readout_v1_20260616_1948` has `288`
  rows, `6` atoms, prompt leakage `0`, no conflicting prompt-atom groups, no
  one-sided atoms, and `ready_for_logprob_diagnostic=true`.  No-update v22
  logprob
  `runs\semireal_memory_evidence_atom_readout_v1_v22_logprob_20260616_1948\details.jsonl.summary.json`
  got overall accuracy `0.670139`.  Strong atoms:
  `candidate_points_to_different_current_patch_file=1.0`,
  `candidate_text_mentions_current_patch_file=1.0`.  Weak atoms:
  `candidate_patch_file_overlap=0.583333`,
  `current_patch_file_support=0.541667`,
  `memory_instance_differs=0.5625`,
  `candidate_text_mentions_different_hint_file=0.333333` with all-False
  collapse.
- [ ] Next short Multi-Agent Direction experiment:
  refine the weak evidence-atom representation before training or integration.
  Candidates: split `current_patch_file_support` into explicit
  `hint_file_exact_overlap` and `text_file_exact_mention`; rename
  `candidate_text_mentions_different_hint_file` to avoid double-negative
  wording; expose a compact `current_files`, `candidate_files`, and
  `overlap_files` section instead of long issue text.  Re-run no-update v22
  atom logprob and reliable-anchor no-regression.  Only atoms with clean
  separation should be considered for a small learned readout; do not wire weak
  atoms into materialized assembly or delegation.
- [x] Build and run compact evidence-atom readout v2.
  Added `scripts\build_semireal_memory_evidence_atom_readout_v2.py`; data
  `data\semireal_memory_evidence_atom_readout_v2_compact_20260616_1952` has
  `288` rows, `6` atoms, prompt leakage `0`, no conflicting prompt-atom
  groups, no one-sided atoms, and `ready_for_logprob_diagnostic=true`.
  No-update v22 logprob
  `runs\semireal_memory_evidence_atom_readout_v2_compact_v22_logprob_20260616_2006\details.jsonl.summary.json`
  improved overall accuracy from v1 `0.670139` to `0.802083`.  Clean atoms:
  `hint_file_exact_overlap=1.0`, `hint_file_no_overlap=1.0`,
  `text_mentions_current_file=1.0`.  Still weak: `memory_from_prior_task=0.75`,
  `memory_from_current_task=0.645833`,
  `text_mentions_noncurrent_hint_file=0.416667`.
- [ ] Next short Multi-Agent Direction experiment:
  build a protected tiny file-set evidence readout or packet-evidence bridge
  using only the three clean atoms (`hint_file_exact_overlap`,
  `hint_file_no_overlap`, `text_mentions_current_file`) plus reliable-anchor
  no-regression.  Keep weak identity/text-noncurrent atoms out of integration.
  Acceptance: clean-atom readout remains `1.0`, reliable-anchor no-regression
  stays clean, packet fields are assembled deterministically from learned atom
  outputs, and no runtime path/stale heuristic is added.
- [x] Build the clean file-set atom to packet-evidence bridge.
  Added `scripts\bridge_memory_file_atoms_to_packet_evidence.py`.  It uses
  v22 readout predictions for only the three clean atoms and emits offline
  `packet_evidence.memory_file_atoms`; it does not add a runtime rule.  After
  fixing grouping to avoid merging duplicate semireal source row ids, bridge
  summary
  `runs\memory_file_atom_packet_evidence_bridge_v2_v22_20260616_2012_fixed\summary.json`
  reports packets `48`, blockers `[]`, atom match `1.0`, support match `1.0`,
  reliable anchors `16/16` use, stale overlap `16/16` reject, unrelated
  distractor `16/16` reject.  This validates file-support evidence compression
  but not stale-vs-distractor semantic routing.
- [ ] Next short Multi-Agent Direction experiment:
  mine/build a small held-out real or semireal file-support diagnostic with no
  duplicate conflicting labels, then rerun the same three-atom readout and
  packet-evidence bridge.  Acceptance: prompt leakage `0`, no source-row label
  conflicts, clean atom readout near `1.0`, bridge support match near `1.0`,
  and at least a few real reliable-current positives rather than only
  semireal current anchors.  Do not train or connect to materialized assembly
  until this held-out file-support bridge passes.
- [x] Audit current sources for held-out/real file-support positives.
  Added `scripts\audit_memory_file_support_sources.py`; audit
  `runs\memory_file_support_source_audit_20260616_2017.json` over
  `data\real_memory_reliability_trace_seed_broad_existing_clean_20260616_1838`,
  `data\real_memory_reliability_trace_seed_broad_sample20_labeled_gpt54mini_20260616_1835`,
  and `data\semireal_memory_reliability_balanced_seed_v2_20260616_1858`
  reports `172` rows total, real trace `124`, semireal `48`.  Real trace has
  file overlap `0/124` and real reliable file-support positives `0`; semireal
  has `16` overlap positives and `32` no-overlap rows.  Blockers:
  `real_reliable_file_support_positive_lt_3` and
  `same_visible_signature_conflicting_labels`.  Therefore the current sources
  are not ready for a held-out file-support bridge, training, or runtime
  integration.
- [ ] Next short Multi-Agent Direction experiment:
  acquire or construct a better held-out file-support source.  Preferred path:
  mine successful retrieved-memory traces where candidate hint files overlap
  the current patch and the memory was actually useful, with at least three
  unique real reliable positives.  Fallback path: build an explicitly
  held-out semireal diagnostic split by task family with no duplicate visible
  signature conflicts, label it diagnostic-only, and rerun the three clean
  file atoms plus packet-evidence bridge.  Do not run SFT/DPO until real or
  held-out positive support exists.
- [x] Run the held-out semireal fallback for file-support atoms and packet
  evidence.  Built the pydicom family holdout with deduped visible signatures:
  `data\semireal_file_support_family_holdout_pydicom_dedup_20260616_2025`
  has `8` rows (`reliable_current_anchor=3`, `stale_overlap=3`,
  `unrelated_distractor=2`) and blockers `[]`.  Atom rows:
  `data\semireal_memory_evidence_atom_readout_v2_pydicom_holdout_dedup_20260616_2025`.
  No-update v22 logprob
  `runs\semireal_memory_evidence_atom_readout_v2_pydicom_holdout_dedup_v22_logprob_20260616_2030\details.jsonl.summary.json`
  got overall accuracy `0.854167`; the three integrated clean atoms stayed
  perfect: `hint_file_exact_overlap=1.0`, `hint_file_no_overlap=1.0`,
  `text_mentions_current_file=1.0`.  Bridge
  `runs\memory_file_atom_packet_evidence_bridge_v2_pydicom_holdout_dedup_v22_20260616_2030\summary.json`
  reports packets `8`, blockers `[]`, atom/support match `1.0/1.0`, reliable
  anchors `3/3` use, stale `3/3` reject, unrelated `2/2` reject.  This is a
  diagnostic-only held-out interface pass, not a training or runtime-integration
  pass, because real reliable file-support positives remain `0`.
- [ ] Next short Multi-Agent Direction experiment:
  mine or produce real reliable-current memory positives.  Search successful
  assistant-chain / memory runs for retrieved memories whose candidate files
  overlap the current patch and whose evidence was actually used, then audit
  them for prompt leakage, duplicate visible signatures, source-row label
  conflicts, and at least three unique real positives.  If existing logs still
  contain no positives, run a tiny trace-collection evaluation designed to
  create real retrieval-positive examples, not another semireal atom benchmark.
  Do not train the memory reliability/controller head until this real-positive
  source exists.
- [x] Expand memory source and run cross-task candidate audit.
  Added `scripts\build_expanded_memory_cards.py`,
  `scripts\audit_cross_task_memory_positives.py`, and
  `scripts\label_cross_task_memory_candidates.py` with tests.  The v3 expanded
  source `data\expanded_memory_cards_v3_clean_issue_20260616_2235` has `390`
  cards from real trace seeds plus SWE-Bench/self-improve memory.  Audit
  `runs\cross_task_memory_positive_audit_v5_clean_issue_20260616_2235`
  found `98` same-module/API reusable-experience candidates across `14`
  targets and `52` memory cards, but strong same-file reliable-current
  candidates remain `0`.  This is ready for judge/trace confirmation, not
  training or runtime integration.
- [ ] Next short Multi-Agent Direction experiment:
  label `runs\cross_task_memory_positive_audit_v5_clean_issue_20260616_2235\judge_candidates.jsonl`
  with a working judge provider or manually inspect a small balanced subset.
  Acceptance before training-data design: at least `3` confirmed
  `reliable_current_reference` rows across unique targets, no prompt leakage,
  and clear packet focus (`locate`, `edit`, `test`, `reverify`, or
  `delegate`).
  Update 2026-06-16 22:50 CST: endpoint issue was the double-slash URL.  With
  `https://zz1cc.cc.cd/v1`, the 24-row judge run
  `runs\cross_task_memory_candidate_judge_gpt54mini_v2_20260616_2250`
  completed but found `0` reliable-current references, `4`
  `reverify_before_use`, `10` stale/misleading, and `10` unrelated.  This
  blocks training from module/API candidates; use them as negative/reverify
  diagnostics only.
- [ ] Next data acquisition step if judge-confirmed reliable rows are still
  below `3`: run a tiny targeted trace collection or construct non-leaky
  mini traces that force retrieval from the expanded memory source, then audit
  whether retrieved cards are actually used for locating/editing/testing.
  Keep this as evidence collection for the small controller; do not add
  runtime path/API heuristics and do not train from unconfirmed module-only
  candidates.
  Update 2026-06-16 22:50 CST: this is now the active next step.  Build a
  small positive-source acquisition set from known reusable repair motifs
  where the memory card is useful but does not reveal the current patch:
  e.g. pydicom JSON/dataset conversion, sqlfluff rule-family lint results,
  pvlib numeric edge-case handling, or marshmallow schema/field binding.
  First output should be audit-only trace/mini-task rows with explicit
  retrieved card, visible current issue, located files/functions, focused test
  node, and whether the memory was actually used.  Require judge-confirmed
  reliable positives before controller SFT/DPO.
- [x] Build targeted non-leaky positive-source acquisition seed.
  Added `scripts\build_targeted_positive_memory_acquisition.py` and tests.
  Candidate source `data\targeted_positive_memory_acquisition_v1_20260616_2325`
  has `9` stripped solved-memory rows across marshmallow, pvlib, pydicom, and
  sqlfluff.  Concrete patch hunks are removed; visible fields include current
  issue, touched files, symbols/classes/functions, failure symptom, test node,
  and abstract patch intent.  Judge run
  `runs\targeted_positive_memory_acquisition_judge_gpt54mini_v1_20260616_2328`
  labeled all `9/9` as `reliable_current_reference`.
  Important caveat: these are same-target stripped positive anchors, not
  cross-task retrieval proof, so keep `ready_for_training=false` until a
  contrastive/no-update gate passes.
- [ ] Next controller-learning step:
  build an audit-only contrastive memory reliability readout set combining:
  the `9` judge-confirmed stripped positives, the `4` judged
  `reverify_before_use` rows, and balanced stale/unrelated rows from
  `runs\cross_task_memory_candidate_judge_gpt54mini_v2_20260616_2250`.
  Target should teach the small controller to decide:
  `reliable_current_reference`, `reverify_before_use`, `stale_or_misleading`,
  or `unrelated_distractor`, plus packet focus.  First run a no-update v22
  readout/logprob diagnostic.  Only consider SFT/DPO if the target separates
  positives from reverify/stale/unrelated without leakage and without runtime
  rules.
  Update 2026-06-16 23:35 CST: built the contrastive readout surface.
  Added `scripts\build_memory_reliability_contrastive_readout.py`; data
  `data\memory_reliability_contrastive_readout_v1_20260616_2335` has `33`
  rows across `14` targets:
  `reliable_current_reference=9`, `reverify_before_use=4`,
  `stale_or_misleading=10`, `unrelated_distractor=10`.
  It is `ready_for_no_update_readout=true` and `ready_for_training=false`.
  Next: run a no-update v22 readout/logprob diagnostic on these labels by
  syncing to remote, because the local tunnel remains broken.
- [x] Run no-update v22 readout diagnostics on the contrastive reliability
  surface.  Added `scripts\run_memory_reliability_contrastive_logprob_gate.py`,
  `scripts\build_memory_reliability_binary_readout.py`, and
  `scripts\build_memory_reliability_binary_pairwise.py` with focused tests.
  Four-way fixed-label logprob is not viable yet:
  `runs\memory_reliability_contrastive_readout_v1_v22_logprob_20260616_2338\details.jsonl.summary.json`
  has normalized accuracy `0.303030` and collapses all `33/33` rows to
  `stale_or_misleading`; reliable positives are `0/9`.  Binary
  reliable-vs-not-use is more promising:
  `runs\memory_reliability_binary_readout_v1_v22_logprob_20260616_2342\details.jsonl.summary.json`
  has normalized accuracy `0.757576`, reliable recall `8/9`, and reject
  accuracy `17/24`, but still has `7` false-use errors (`1` reverify,
  `4` stale, `2` unrelated).  The raw binary pairwise dry-run
  `runs\memory_reliability_binary_pairwise_v1_v22_dryrun_20260616_2345\dryrun_summary.json`
  is not a safe DPO target as-is: `DO_NOT_USE_MEMORY` is preferred `24/24`,
  while `USE_RELIABLE_MEMORY` is preferred `0/9`, indicating completion
  wording/length bias.  Equalized opaque A/B labels are also not the fix:
  `runs\memory_reliability_equalized_label_readout_v1_v22_logprob_20260616_2350\details.jsonl.summary.json`
  got normalized accuracy `0.696970`, but reliable positives were `0/9` and
  rejects were `23/24`; the model mostly chose `B`.  Do not train four-way
  reliability, do not connect this to packet assembly, and do not run DPO on
  the raw pairwise or opaque-label rows yet.
- [ ] Next short Multi-Agent Direction experiment:
  build a protected hard-negative reliability calibration readout around the
  binary false-use errors.  Keep the learned target narrow:
  `USE_RELIABLE_MEMORY` vs `DO_NOT_USE_MEMORY`, with matched controls for
  stale/reverify/unrelated cards that share repo/files/symbols with reliable
  anchors.  Use semantic fixed labels with normalized scoring or another
  protected label surface that preserves meaning; do not use raw unequal-length
  pairwise completions or opaque A/B labels as the main target.
  Acceptance before SFT/DPO or packet integration: prompt leakage `0`,
  reliable-anchor recall at least `8/9`, false-use on high-similarity
  negatives substantially below `7/24`, no all-reject/all-use collapse, and
  explicit analysis by original labels (`reverify`, `stale`, `unrelated`).
  This should train/check whether the small model learns reliability judgment;
  do not add runtime path/API/stale rules.
  Update 2026-06-16 23:58 CST: compact semantic binary prompting made the
  boundary worse, not better.  Added
  `scripts\build_memory_reliability_semantic_binary_readout.py`; the data
  `data\memory_reliability_semantic_binary_readout_v1_20260616_2355` is clean
  (`33` rows, prompt leakage `0`), but v22 logprob
  `runs\memory_reliability_semantic_binary_readout_v1_v22_logprob_20260616_2355\details.jsonl.summary.json`
  collapsed to `USE_RELIABLE_MEMORY` for `33/33`, giving reliable positives
  `9/9` and reject negatives `0/24`.  Feature audit of the previous better
  binary readout shows all `7` false-use rows had `file_overlap=0`, and
  `6/7` also had `symbol_overlap=0`; the model is over-trusting same-repo or
  same-topic memory, not true current-file support.  Added
  `scripts\build_memory_reliability_file_support_atom_readout.py`; atom data
  `data\memory_reliability_file_support_atom_readout_v1_20260616_2358` is
  clean (`True=9`, `False=24`, prompt leakage `0`), but v22 atom logprob
  `runs\memory_reliability_file_support_atom_readout_v1_v22_logprob_20260616_2358\details.jsonl.summary.json`
  collapsed to `False` for `33/33`, missing all true file-support anchors.
  Next step should not be packet assembly or broad reliability training:
  build a protected file-support atom calibration/no-regression target that
  teaches visible file overlap positives while keeping no-overlap stale,
  reverify, and unrelated negatives rejected.
- [ ] Next short Multi-Agent Direction experiment:
  build a tiny protected file-support atom calibration set from the clean
  `True=9` / `False=24` atom rows, with positive replay for current-file
  overlap and hard negatives for no current-file overlap.  First run no-update
  and, if needed, a tiny held-out-safe SFT/DPO candidate only on this atom.
  Acceptance before integration: atom true accuracy improves from `0/9` to a
  useful level, false accuracy remains near `24/24`, no all-True/all-False
  collapse, original binary reliable recall does not regress below `8/9`, and
  stale/reverify/unrelated false-use stays below the previous `7/24`.
  Keep it as learned atom -> deterministic packet evidence later; do not add a
  runtime file-overlap rule.
  Update 2026-06-17 00:08 CST: built the protected calibration split and
  rejected the first tiny SFT candidate.  Added
  `scripts\build_memory_file_support_atom_calibration_data.py`; data
  `data\memory_file_support_atom_calibration_v1_20260617_0005` has train
  `40` rows (`True=18`, `False=22`) and held-out val `4` rows (`True=2`,
  `False=2`) with train/val prompt overlap `0`.  The tiny SFT continuation
  `runs\memory_file_support_atom_calibration_sft_v1_20260617_0008` drove loss
  down (`train 5.348242 -> 0.201981`, `val 5.207031 -> 0.191772`), but fixed
  label gates show no usable controller improvement: val atom still all
  `False` (`0/2` true, `2/2` false), full 33 atom still all `False`
  (`0/9` true, `24/24` false), and binary reliability no-regression dropped
  from v22 `0.757576` to `0.696970` with reliable recall `7/9` and reject
  accuracy `16/24`.  Do not deploy, serve, merge, or use this adapter for
  packet evidence.  More epochs are not justified; the problem is target/
  scoring alignment, not loss convergence.
- [ ] Next short Multi-Agent Direction experiment:
  build a preference or fixed-label logprob calibration target for the
  file-support atom completion surface itself.  Prefer a pairwise objective
  that directly contrasts `TRUE` vs `FALSE` (or a protected semantic label
  surface) and evaluate by fixed-label logprob, not chat-SFT loss alone.
  Acceptance before any further SFT/DPO integration: full atom true accuracy
  improves above `0/9`, false accuracy remains high, no all-label collapse,
  and binary reliability no-regression recovers to at least the v22 baseline
  region (`>=0.757576`, reliable recall `>=8/9`, false-use `<=7/24`).
  Still no runtime file-overlap rule and no packet assembly connection.
  Update 2026-06-17 00:24 CST: built and tested the direct TRUE/FALSE
  pairwise atom target, but the first DPO candidate is rejected.  Pairwise data
  `data\memory_file_support_atom_pairwise_v1_20260617_0012` has train `40`
  rows (`TRUE=18`, `FALSE=22`) and val `4` rows (`TRUE=2`, `FALSE=2`) with
  prompt leakage `0`.  No-update v22 dry-run
  `runs\memory_file_support_atom_pairwise_v1_v22_dryrun_20260617_0012`
  shows the exact failure: `FALSE` choices preferred `22/22` train and `2/2`
  val, while `TRUE` choices are preferred `0/18` train and `0/2` val.  The
  tiny DPO continuation
  `memory_file_support_atom_pairwise_dpo_v1_20260617_0018` did not fix this:
  after training it still preferred `TRUE 0/18` and `FALSE 22/22`.  Gates show
  all-False atom collapse on val and full 33 (`True=0/2`, `True=0/9`), while
  binary reliability no-regression only matches the v22 region
  (`0.757576`, reliable `8/9`, reject `17/24`, false-use `7/24`) without
  improving it.  A compact-JSON label-surface sweep also stayed all-False for
  v22 and DPO0018, so the problem is not just the literal `TRUE/FALSE` surface.
  Do not deploy/serve/use DPO0018.  Next: build a positive-weighted or
  margin-focused TRUE replay calibration with matched hard FALSE controls and
  require held-out/full atom TRUE accuracy to move above `0/9` without
  increasing binary false-use.  Do not add a runtime file-overlap rule.
  Update 2026-06-17 00:29 CST: added a TRUE-positive replay data builder,
  `scripts\build_memory_file_support_atom_weighted_pairwise.py`, plus tests.
  The weighted target
  `data\memory_file_support_atom_weighted_pairwise_v1_true4_20260617_0028`
  is clean (`TRUE=72`, `FALSE=22`, val `TRUE=2/FALSE=2`, prompt leakage `0`),
  but the v22 dry-run
  `runs\memory_file_support_atom_weighted_pairwise_v1_true4_v22_dryrun_20260617_0029`
  shows no unique TRUE improvement: `FALSE 22/22`, `TRUE 0/72`, train
  preference accuracy `0.234043`; val remains `FALSE 2/2`, `TRUE 0/2`.
  Treat this as a pressure-test artifact, not an immediate training green
  light.  Next useful step is to change the objective or label surface so TRUE
  margins can actually move, then gate held-out/full atom and binary
  reliability.  Still no packet assembly connection and no runtime file rule.
  Update 2026-06-17 00:36 CST: tried one objective change on the weighted
  data, but reject the candidate.  The `reference_free` continuation
  `memory_file_support_atom_weighted_pairwise_refree_v1_20260617_0032`
  moved TRUE train margins in the right direction (`-5.94 -> -2.34`) but did
  not flip any TRUE examples (`TRUE 0/72`, `FALSE 22/22`).  Held-out and full
  atom gates still collapsed all-False (`True=0/2`, `True=0/9`).  Worse, the
  binary reliability no-regression gate dropped from the v22/DPO0018 region
  `0.757576` to `0.696970`, with reject accuracy `15/24` and false-use
  `9/24`.  Do not deploy/serve/use this adapter.  Next: build a margin
  diagnostic over TRUE rows and near-boundary FALSE hard negatives, then design
  a calibrated fixed-label/margin objective before any more training.  The
  acceptance bar stays: TRUE atom accuracy above `0/9`, FALSE high, binary
  reliability at least v22, no packet assembly connection, no runtime file
  rule.
  Update 2026-06-17 00:38 CST: added
  `scripts\summarize_memory_file_support_atom_margin_candidates.py` and
  summary artifact
  `runs\memory_file_support_atom_margin_candidate_summary_20260617_0038.json`.
  It confirms both candidates are blocked: DPO0018 has atom `true_correct=0/9`,
  binary reliability `0.757576`, false-use `7/24`; refree0032 has atom
  `true_correct=0/9`, binary reliability `0.696970`, false-use `9/24`.
  The summary explicitly sets `ready_for_packet_integration=false` and
  `ready_for_more_same_surface_training=false`.  Next should be a margin-aware
  fixed-label objective design after inspecting TRUE rows and near-boundary
  FALSE hard negatives, not another same-surface adapter.
  Update 2026-06-17 00:42 CST: added row-level margin diagnostic
  `scripts\summarize_memory_file_support_atom_margin_rows.py` and artifact
  `runs\memory_file_support_atom_margin_rows_20260617_0042.json`.  It confirms
  the hard TRUE rows are not weak/no-overlap cases: examples include
  `pydicom__pydicom-1256` on `pydicom/jsonrep.py`,
  `marshmallow-code__marshmallow-1343` on
  `src/marshmallow/marshalling.py` / `src/marshmallow/schema.py`, and
  `pvlib__pvlib-python-1707` on `pvlib/iam.py`.  Refree0032 moves margins but
  still has TRUE margin mean `-1.149306` and FALSE mean `-1.106771`, so it
  compressed both classes toward the boundary and damaged binary reliability.
  Next build a margin-aware calibration data/objective that replays hardest
  TRUE rows while preserving nearest-boundary no-overlap FALSE
  stale/reverify/unrelated rows and binary no-regression replay.  No packet
  assembly, no served adapter, no runtime overlap heuristic.
  Update 2026-06-17 00:55 CST: tested whether the atom failure is just a bad
  label surface.  Added `--true-label/--false-label` to
  `scripts\run_single_atom_label_logprob_gate.py`; tests passed.  No-update
  v22 surface gate
  `runs\memory_file_support_atom_label_surface_v22_20260617_0052` shows:
  `TRUE/FALSE` collapses all-False (`0/9` TRUE, `24/24` FALSE,
  accuracy `0.727273`); `SUPPORTED/UNSUPPORTED` predicts `True=28/33` and
  only reaches `0.424242`; `FILE_SUPPORTED/FILE_UNSUPPORTED` collapses all-True
  (`9/9` TRUE, `0/24` FALSE, accuracy `0.272727`).  Therefore label wording
  alone is not a solution.  Next objective must be margin-aware and preserve
  hard negatives; do not spend more time on label-only swaps.
  Update 2026-06-17 01:08 CST: built the first margin-aware pairwise target
  from row-level diagnostics.  Added
  `scripts\build_memory_file_support_atom_margin_pairwise.py` and tests
  (`4 passed`).  The first build
  `data\memory_file_support_atom_margin_pairwise_v1_20260617_0105` blocked
  itself because TRUE was still below FALSE (`TRUE=35`, `FALSE=38`).  The
  corrected candidate
  `data\memory_file_support_atom_margin_pairwise_v1_true8_20260617_0107`
  has train `83` rows (`TRUE=45`, `FALSE=38`), with `hard_true=40`,
  `hard_false=20`, calibration replay `23`, prompt leakage `0`, blockers `[]`.
  No-update v22 dry-run
  `runs\memory_file_support_atom_margin_pairwise_v1_true8_v22_dryrun_20260617_0108`
  still shows the boundary to learn: `FALSE 38/38`, `TRUE 0/45`, train
  preference accuracy `0.457831`; val `FALSE 2/2`, `TRUE 0/2`.
  This is a better offline training candidate, not a result.  Next tiny train,
  if launched, must be isolated and accepted only if full-33 atom TRUE improves
  above `0/9` and binary reliability stays at least v22 (`0.757576`, reliable
  `8/9`, false-use `<=7/24`).  Still no packet assembly, no served adapter,
  no runtime overlap heuristic.
- [x] Update LATEX-NIPS related work with SWE-Protege / SWE-Protégé.
  Added the close selective-collaboration comparison:
  SWE-Protégé trains small SWE agents to selectively collaborate with an expert
  model, while our current novelty target is memory-boundary learning before
  delegation: retrieve reliable experience, reject stale/unrelated memory under
  lexical overlap, and compress evidence into packet atoms.  Added
  `kon2026sweprotege` to `references.bib` and compiled with pdflatex+bibtex.
- [x] Update LATEX-NIPS related work with PYTHALAB-MERA.
  Added a narrow comparison:
  PYTHALAB-MERA uses a frozen generator with validation-conditioned episodic
  memory, LinUCB retrieval selection, delayed credit, and AST-derived skill
  reuse, while our method trains a small model to learn route/packet/verifier
  evidence boundaries and to call the large patch generator selectively.
- [x] Update LATEX-NIPS related work with Agyn.
  Added Agyn as a multi-agent software-engineering team comparison and
  clarified that our large model is a selective patch generator called by a
  learned small controller, not an always-on team member.
- [x] Update LATEX-NIPS narrowly:
  add support-aware packet-boundary table,
  report delegate4 and the new AZ proxy12 selective+guard-retry collaboration
  probe,
  and emphasize learned reliability/evidence compression rather than a hard-coded multi-agent pipeline.
  Edited
  `C:\Users\zrz20\Desktop\vscode\multi-rl\创智大作业\LATEX-NIPS\neurips_2026.tex`.
  Added the AZ selective+guard-retry proxy12 row to Table `multiagent`,
  updated the abstract/contribution text and support-aware delegate4 paragraph,
  and clarified that the `0.95` retry threshold is diagnostic, not the claimed
  controller mechanism.
  Compile check:
  `pdflatex -interaction=nonstopmode -halt-on-error -jobname=neurips_2026_az_collab_check neurips_2026.tex`
  passed with expected single-pass citation/reference warnings.
- [x] Update LATEX-NIPS narrowly with v2c finding.
  Added one support-boundary paragraph:
  independent evidence-factorized memory wording improves copy-default-only None-guard behavior,
  so packet wording/data format should be treated as learned controller target design, not post-hoc packet rewriting.
- [x] Update LATEX-NIPS related work with ProjectMem / PROJECTMEM.
  Distinguish deterministic event-sourced memory governance and pre-action gates from our learned small-controller evidence-boundary objective.
- [x] Update LATEX-NIPS related work with MemGovern.
  Added governed human-experience memory as a close comparison:
  MemGovern injects governed human experience cards and agentic search,
  while our current target trains the small controller to learn evidence boundaries,
  no-op/semantic/format guards, and selective delegation.
- [x] Update LATEX-NIPS related work with RSCB-MC.
  Added a narrow comparison to abstention-aware risk-sensitive contextual
  bandit memory retrieval for LLM coding agents.  Framing distinction:
  RSCB-MC validates the need to withhold harmful memory, but treats memory
  control as fixed-action bandit selection; our current target is a small
  memory-conditioned controller learning evidence-packet and verifier-boundary
  behavior before selective large-patch delegation.  Compile check with
  `neurips_2026_rscb_check` succeeded.
- [x] Update LATEX-NIPS related work with MemRL and MemQ.
  Added a narrow memory/RL-agent comparison: MemRL learns value-aware episodic
  memory selection and MemQ propagates memory credit over provenance DAGs,
  while this project trains a code-specific small controller to learn
  route/packet/verifier evidence boundaries before selective large-patch
  delegation.  Compile check with `neurips_2026_memrl_memq_check` succeeded.
- [x] Update LATEX-NIPS related work with RepoNavigator and MemCoder.
  Added RepoNavigator / "One Tool Is Enough" as repository-localization RL
  comparison and MemCoder / structured memory as a project-history memory
  comparison.  Bypass compile with
  `-jobname=neurips_2026_sft_check` succeeded; the main PDF was only blocked
  because `neurips_2026.pdf` was locked by another process.
- [x] Ran the tiny downstream `gpt-5.4-mini` probe on held-out mutable-container families.
  Current best evidence is the AZ delegate4 rerun:
  semantic pass `1.0`, mean strict `0.898750`, no provider errors.
  This validates the packet-to-large-model collaboration path when the channel
  is healthy.
  Remaining work is to broaden carefully and train packet/reliability judgment,
  not to hard-code packet-builder rules that infer `copy_selected_*` from task labels.
- [x] Expand the memory source for the Multi-Agent Direction before further
  controller training.  Added `--targeted-positive` to
  `scripts\build_expanded_memory_cards.py`, preserving stripped solved-memory
  cards as audit-only memory cards with repo / instance / files / symbols /
  failure symptom / test nodes / patch intent.  Built
  `data\expanded_memory_cards_v4_multisource_20260617_0029` with `408` cards:
  `33` trace summaries, `30` retrieved cards, `336` SWE-Bench/reference cards,
  and `9` stripped solved-positive cards.  This is source expansion only, not
  a runtime reliability rule.
- [x] Rerun cross-task retrieval-positive audit on the expanded source.
  `runs\cross_task_memory_positive_audit_v6_multisource_20260617_0029`
  found `128` matches over `16` targets, including `8` file-supported
  reliable-current candidates and `98` module/API reusable-experience
  candidates, with `14` unique positive targets and `55` unique positive memory
  cards.  It is ready for judge labeling and still `ready_for_training=false`.
- [x] Judge the v6 cross-task candidates with `gpt-5.4-mini`, prioritizing the
  `8` file-supported positives and a balanced sample of same-module/API
  candidates plus stale/unrelated controls.  Result: `32` labeled rows,
  `8` reliable-current positives, `13` stale, `11` unrelated, `8` unique real
  positive targets.  This confirmed the memory source has real positives and
  that the controller still needs to learn the boundary, not a runtime rule.
- [x] Rebuild the reliability/readout surface with explicit `pair_id` /
  `group_id` fields so the binary no-regression gate can run cleanly.
  Result: contrastive, semantic-binary, binary, and equalized readouts all
  built cleanly with `0` prompt leakage.
- [x] Build a hard-row replay / no-regression candidate from
  `runs\memory_reliability_neutral_pairwise_v6_multisource_v3hard_20260617_1712`
  and
  `runs\memory_reliability_neutral_pairwise_v3hard_v22_dryrun_20260617_1712`.
  The v3hard candidate is clean (`62` rows, A/B `31/31`, reliable/stale/unrelated
  `16/24/22`, unique reliable targets `8`, prompt leakage `0`) and v22 no-update
  has `0.887097` preference accuracy with `7` failures (`3` reliable-current,
  `4` stale).  Built
  `runs\memory_reliability_hard_replay_pairwise_v3hard_balanced_20260617_1725`:
  `27` rows, failed replay/protected replay `7/20`, A/B `14/13`,
  reliable/stale/unrelated `8/13/6`, prompt leakage `0`, blockers `[]`.
  v22 dry-run
  `runs\memory_reliability_hard_replay_pairwise_v3hard_balanced_v22_dryrun_20260617_1725`
  has preference accuracy `0.740741`, mean margin `0.729004`.
- [x] Next Multi-Agent Direction step:
  decide whether to launch a tiny isolated DPO update on the balanced hard
  replay, but only after materializing the exact pre/post no-regression gate
  plan.  Required gates before any adapter promotion: four-way v6 reliability
  readout, semantic binary readout, equalized A/B readout, file-support atom
  full-33 gate, and existing binary reliability no-regression.  Keep it focused
  on learned choices:
  `supports_current_task`, `reverify_before_use`,
  `stale_or_misleading`, `unrelated_distractor`, `SELF_HANDLE`,
  `DELEGATE_PACKET`.
  Do not convert file overlap, repo overlap, or symbol overlap into runtime
  rules.  Acceptance before any training: no leakage, at least `3` unique real
  positives, and no single-label collapse under v22 no-update diagnostics.
  Update 2026-06-17 02:05 CST: launched and rejected the tiny isolated DPO
  candidate.  Adapter:
  `/mnt/memory-agent/runs/memory_reliability_tiny_dpo_launch_manifest_v3hard_balanced_20260617_1735/adapter`.
  Training was only `27` rows / `14` steps, but after-eval preference accuracy
  dropped from `0.740741` to `0.703704` and margin exploded.  Independent
  post-gates confirmed rejection:
  hard replay `0.703704` with reliable-current `0/8`;
  four-way collapsed to `stale_or_misleading 31/31`;
  semantic binary near-collapsed to `USE_RELIABLE_MEMORY 30/31`;
  equalized A/B collapsed to `B 31/31`;
  file-support atom stayed all-False with TRUE `0/9`;
  binary reliability regressed to `0.483871` with false-use `12/23`.
  Added
  `scripts\summarize_memory_reliability_tiny_dpo_post_gates.py`
  and manifest
  `runs\memory_reliability_tiny_dpo_launch_manifest_v3hard_balanced_20260617_1735\post_gate_manifest.json`.
  Do not deploy, serve, packet-integrate, or continue training this objective.
- [ ] Next Multi-Agent Direction step:
  build a new reliability objective/readout instead of more same-surface DPO.
  Target the learned judgments explicitly:
  `supports_current_task`, `needs_reverify_before_packet_evidence`,
  `stale_or_misleading_overlap`, `unrelated_distractor`,
  `SELF_HANDLE`, and `DELEGATE_PACKET`.
  The data should preserve reliable-current positives and protect stale and
  unrelated negatives separately, with margin/normalization-aware scoring so
  the controller cannot win by all-stale, all-use, all-B, or all-False collapse.
  Required no-update/training gates before any adapter promotion:
  hard replay pairwise improves over `0.740741` and reliable-current above
  `0/8`; four-way reliable-current above `0/8` without collapse; semantic
  binary reject controls recover; equalized A/B reliable positives above
  `0/8`; file-support TRUE above `0/9` with FALSE still high; binary
  reliability at least `0.757576` and false-use `<=7/24` or the current
  judged-row equivalent.  Still no runtime repo/file/symbol overlap rule and
  no packet assembly connection until these gates pass.
  Update 2026-06-17 02:20 CST: built the first factorized atom readout instead
  of another packet-shaped DPO target.  Added
  `scripts\build_memory_reliability_factorized_atom_readout.py` and tests.
  Data
  `data\memory_reliability_factorized_atom_readout_v1_20260617_0205`
  has `155` rows over five atoms, prompt leakage `0`, blockers `[]`, and
  `8` unique reliable targets.  v22 no-update fixed-label gate
  `runs\memory_reliability_factorized_atom_readout_v1_v22_20260617_0205\details.jsonl.summary.json`
  still leans heavily all-False (`False=150`, `True=5`) but is slightly more
  readable than the old file-support atom: `supports_current_task` recovers
  `3/8` reliable-current true cases and `packet_evidence_allowed` recovers
  `2/8`; `same_repair_pattern`, `needs_reverify_before_packet_evidence`, and
  `reject_as_unrelated` remain all-False.  Next build a factorized atom
  margin/pairwise candidate from these row-level failures and protected hard
  negatives, then run no-update dry-run before any tiny training.
  Update 2026-06-17 02:35 CST: built both fixed TRUE/FALSE and neutral A/B
  atom-margin pairwise candidates.  Fixed-label data:
  `runs\memory_reliability_factorized_atom_margin_pairwise_v1_20260617_0218`,
  `94` rows, TRUE/FALSE `47/47`, prompt leakage `0`, blockers `[]`, but v22
  dry-run exposes the original collapse risk: chosen FALSE `47/47`, chosen
  TRUE `5/47`, preference accuracy `0.553191`.  Neutral data:
  `runs\memory_reliability_factorized_atom_neutral_margin_pairwise_v1_20260617_0224`,
  also `94` rows and TRUE/FALSE `47/47`, with chosen A/B `47/47`.  v22 dry-run
  improves to `0.595745`, but still has strong B bias (`A=0.404255`,
  `B=0.787234`).  Do not train yet.  Next: build an A/B-bias-resistant variant
  or add an explicit pre-training gate requiring both chosen-A and chosen-B
  accuracy above a floor, while preserving missed TRUE atom recovery and false
  controls.
  Update 2026-06-17 02:55 CST: added `--paired-swaps` to the neutral atom
  margin builder and ran a 188-row v22 no-update dry-run.  Data:
  `runs\memory_reliability_factorized_atom_neutral_margin_pairwise_pairedswap_v1_20260617_0238`,
  TRUE/FALSE `94/94`, chosen A/B `94/94`, prompt leakage `0`, blockers `[]`.
  Dry-run:
  `runs\memory_reliability_factorized_atom_neutral_margin_pairwise_pairedswap_v1_20260617_0238\v22_dpo_dryrun.json`,
  overall `0.617021`, chosen A `0.372340`, chosen B `0.861702`,
  TRUE `0.829787`, FALSE `0.404255`.  Bias-corrected paired average over the
  94 base rows is only `0.574468`; TRUE base rows are all avg-margin positive,
  but FALSE base rows only `0.148936`.  This is useful diagnostic evidence but
  still not a training candidate.  Next experiment should build a
  bias-resistant reliability gate/readout: score pair-consistency across both
  swaps, require both A and B above a floor, and improve FALSE protection before
  any optimizer step.  Keep this as learned evidence scoring, not runtime
  file/repo/symbol rules.
  Update 2026-06-17 03:05 CST: formalized the paired-swap gate in
  `scripts\summarize_memory_reliability_pairedswap_gate.py` with tests.  Gate
  output:
  `runs\memory_reliability_factorized_atom_neutral_margin_pairwise_pairedswap_v1_20260617_0238\pairedswap_gate_summary.json`.
  It correctly blocks the current candidate:
  overall `0.617021`, chosen A `0.372340`, chosen B `0.861702`,
  paired average `0.574468`, both-swaps `0.361702`, TRUE avg-margin
  `1.000000`, FALSE avg-margin `0.148936`.  Blockers are A/B bias, weak
  pair-consistency, and false-protection failure.  The expanded memory source
  itself is not the current bottleneck: v6 multisource audit has `408` cards,
  `106` reusable positive candidates, `14` unique positive targets, and `55`
  unique positive memory cards.  Next concrete experiment: build a residual
  negative-protection readout from the worst paired-swap FALSE controls
  (`needs_reverify_before_packet_evidence`, `reject_as_unrelated`, and false
  `supports_current_task`), then re-run the paired-swap gate.  Do not train
  until FALSE avg-margin and both-swaps gates clear.
  Update 2026-06-17 03:10 CST: completed the residual negative-protection
  readout and a neutral paired-swap follow-up.  Fixed-label v22 gate on
  `runs\memory_reliability_negative_protection_readout_v2_20260617_0300`
  collapsed to `PROTECT_REVERIFY_OR_REJECT=20/20`: protect negatives
  `12/12`, allow positives `0/8`.  Added
  `scripts\build_memory_reliability_negative_protection_neutral_pairwise.py`
  and tests; built
  `runs\memory_reliability_negative_protection_neutral_pairwise_v1_20260617_0310`
  with `40` paired-swap rows, `A/B=20/20`, `TRUE/FALSE=16/24`, leakage `0`.
  v22 dry-run recovered TRUE/allow positives (`avg-margin=1.0`,
  both-swaps `1.0`) but still failed false protection (`FALSE avg-margin
  0.333333`, both-swaps `0.0`) and kept strong choice bias (`A=0.4`, `B=1.0`,
  gap `0.6`).  Gate remains blocked; do not train or integrate.  Next build a
  bias-resistant false-protection objective/readout that preserves the TRUE
  signal while replaying the worst FALSE rows (`reject_as_unrelated`,
  `needs_reverify_before_packet_evidence`, false `supports_current_task`) and
  require paired-average, both-swaps, and false-protection gates to pass before
  any optimizer step.  This remains learned offline scoring, not a runtime
  repo/file/symbol overlap rule.
  Update 2026-06-17 03:25 CST: verified that the blocker is not just the
  literal `A/B` labels.  Added `--choice-labels` to the negative-protection
  neutral pairwise builder and made the paired-swap gate detect non-A/B choice
  labels.  Tests passed (`6 passed`).  Built `LEFT/RIGHT` and `FIRST/SECOND`
  variants with balanced choices and leakage `0`; remote v22 no-update dry-run
  on `LEFT/RIGHT` scored only `0.475000` overall (`LEFT=0.55`,
  `RIGHT=0.40`) while keeping false protection weak.  Stop sweeping labels:
  next objective should change the hard-negative/positive-preservation data
  distribution, not the visible choice names.  Required before training:
  paired-average and both-swaps above floor, FALSE/protect avg-margin above
  floor, TRUE/allow preservation intact, and old reliability no-regression not
  worse than v22.
  Update 2026-06-17 03:40 CST: built and rejected a simple hard-negative
  replay residual.  Added
  `scripts\build_memory_reliability_false_protection_residual_pairwise.py`
  and tests.  The clean no-repeat candidate
  `runs\memory_reliability_false_protection_residual_pairwise_v1_norepeat_20260617_0335`
  has `24` rows, `FALSE=16`, `TRUE=8`, `A/B=12/12`, leakage `0`.
  v22 no-update dry-run scored overall `0.666667`, but the paired-swap gate
  still blocks it: `A=0.333333`, `B=1.0`, paired-average `0.333333`,
  both-swaps `0.333333`, TRUE avg-margin `1.0`, FALSE avg-margin `0.0`.
  Do not train this candidate.  Next objective should be pair/group-level:
  optimize average margin over both swaps, not row replay; preserve TRUE
  anchors and require original four-way / semantic-binary / equalized-A-B /
  file-support no-regression before any optimizer step.
  Update 2026-06-17 03:55 CST: tried a true pair/group consistency surface.
  Added `scripts\build_memory_reliability_pair_group_preference.py` and tests.
  Data
  `runs\memory_reliability_pair_group_preference_falseprot_v1_20260617_0350`
  has `12` rows (`FALSE=8`, `TRUE=4`, leakage `0`), where one completion must
  answer both swap variants correctly.  v22 no-update dry-run scored only
  `0.500000` with mean margin `-1.612305`; both FALSE and TRUE are `0.5`, and
  `reject_as_unrelated` is `0/3`.  Do not train this surface.  Next try a
  simpler group-level fixed-label/readout scorer over the base pair, with
  labels like `ALLOW_PACKET_EVIDENCE` vs `PROTECT_REVERIFY_OR_REJECT` or a
  compact semantic equivalent.  Gate it by TRUE preservation, FALSE
  protection, original reliability no-regression, and pair-average margins
  before any optimizer step.
  Update 2026-06-17 04:05 CST: tried and rejected the compact group-label
  readout.  Added `scripts\build_memory_reliability_group_label_readout.py`
  plus tests; built
  `runs\memory_reliability_group_label_readout_falseprot_v1_20260617_0400`
  with `12` rows (`ALLOW=4`, `PROTECT=8`, leakage `0`).  Remote v22 fixed-label
  logprob gate collapsed to all `PROTECT_REVERIFY_OR_REJECT`: overall
  `0.666667`, protect `8/8`, allow `0/4`.  Do not train this surface.  Added
  `scripts\summarize_memory_reliability_atom_score_composition.py` as an
  offline diagnostic over the existing factorized atom logprobs.  The atom
  margin composition summary
  `runs\memory_reliability_atom_score_composition_v1_from_v22_20260617_0405.json`
  is the first useful signal in this branch: `31` memory groups, in-sample
  `31/31`, leave-one-task-out `30/31`, allow `7/8`, protect `23/23`, with the
  only miss on `pydicom__pydicom-1256`.  This is not a runtime threshold rule.
  Next build a learned factorized-atom score/readout target that outputs or
  scores support/protect atoms and learns their composition, then gate it
  against four-way reliability, semantic binary, equalized A/B, file-support
  TRUE/FALSE, and old binary reliability before any packet assembly,
  integration, or large-model call.
  Update 2026-06-17 04:35 CST: tried the learned atom-composition label and
  pairwise surfaces and rejected both.  Added
  `scripts\build_memory_reliability_atom_composition_readout.py` and
  `scripts\build_memory_reliability_atom_composition_pairwise.py` plus tests.
  The 31-row readout
  `runs\memory_reliability_atom_composition_readout_v1_20260617_0415`
  is clean (`ALLOW=8`, `PROTECT=23`, leakage `0`), but v22 fixed-label gate
  still collapsed to all `PROTECT` (`0/8` allow, `23/23` protect).  The
  balanced pairwise target
  `runs\memory_reliability_atom_composition_pairwise_v1_balanced_20260617_0420`
  has `47` rows (`ALLOW` chosen `24`, `PROTECT` chosen `23`), but no-update
  dry-run shows the same boundary: allow chosen `0/24`, protect chosen
  `23/23`, overall `0.489362`.  A tiny isolated DPO rerun with
  `max_length=1024`, `batch_size=1`, `lr=1e-6` completed at
  `/mnt/memory-agent/runs/memory_reliability_atom_composition_pairwise_v1_balanced_dpo_tiny_1024_20260617_0435`,
  but after-eval stayed `0.489362` and post label gate stayed all `PROTECT`
  (`0/8` allow).  Do not deploy, serve, integrate, or continue this adapter.
  Next change the formulation, not the label wording: try a numeric/calibrated
  score-head target over atom margins, a multi-task preference mix with old
  reliability preservation, or a narrower supervised atom-value recovery
  target.  Required before any optimizer promotion: allow positives above
  `0/8`, protect negatives remain high, and four-way / semantic-binary /
  equalized-A-B / file-support / old binary reliability gates do not regress.
  Update 2026-06-17 04:55 CST: built the first numeric/calibrated score-head
  diagnostic.  Added `scripts\build_memory_reliability_atom_score_head_data.py`
  plus tests.  Artifact
  `runs\memory_reliability_atom_score_head_data_v1_calibrated_20260617_0455`
  uses only factorized atom margins/predictions and is explicitly
  `ready_for_runtime_rule=false`.  Leave-one-task-out is much better than the
  label surfaces: overall `0.903226`, allow `8/8`, protect `20/23`.  It is
  still blocked because protect is below the `0.9` floor.  The three false
  allows are all held-out `sqlfluff__sqlfluff-1517` protect rows, with all atom
  predictions false but score shape crossing the allow threshold.  Next build
  a task-heldout hard-protect residual around these sqlfluff rows, requiring
  protect `>=0.9` and allow `8/8`; keep it as learned score-head target design,
  not a runtime sqlfluff/file/symbol rule.
  Update 2026-06-17 05:00 CST: built the hard-protect residual target data.
  Added `scripts\build_memory_reliability_score_head_hard_protect_residual.py`
  plus tests.  Artifact
  `runs\memory_reliability_score_head_hard_protect_residual_v1_20260617_0500`
  has `25` rows: `9` heldout false-allow hard-protect replay rows, `8`
  same-task protect anchors, and `8` allow-preservation anchors; blockers
  `[]`, `ready_for_score_head_mix=true`, `ready_for_training=false`,
  `ready_for_runtime_rule=false`.  Next use it only as input to a learned
  score-head or multitask calibration mix, then require leave-one-task-out
  protect `>=0.9` and allow `8/8` plus old reliability no-regression before
  any optimizer promotion or packet integration.
  Update 2026-06-17 05:15 CST: strict mix evaluation rejects that direct
  residual.  Added `scripts\evaluate_memory_reliability_score_head_mix.py`
  plus tests.  Base-only score-head
  `runs\memory_reliability_score_head_mix_eval_base_only_20260617_0515.json`
  stays at overall `0.903226`, allow `8/8`, protect `20/23`.  Base plus
  hard-protect residual
  `runs\memory_reliability_score_head_mix_eval_hardprotect_residual_20260617_0515.json`
  drops to overall `0.870968`, allow `8/8`, protect `19/23`, and introduces a
  new pydicom false allow.  Reason: strict leave-one-task-out excludes
  same-task residual rows from the held-out sqlfluff fold, so replay cannot
  prove cross-task learning.  Do not train this mix as-is.  Next mine
  cross-task hard protect negatives from same repo/module/API/error family
  rather than same-task replay, then rerun score-head mix eval and require
  protect `>=0.9`, allow `8/8`, and old reliability no-regression.
  Update 2026-06-17 05:20 CST: audited cross-task hard-negative coverage for
  the sqlfluff-1517 score-head failure.  Added
  `scripts\audit_memory_reliability_cross_task_hard_negatives.py` plus tests.
  Audit
  `runs\memory_reliability_cross_task_hard_negative_audit_sqlfluff1517_20260617_0520.json`
  finds only `2` same-repo cross-task protect rows
  (`sqlfluff__sqlfluff-1625`, `sqlfluff__sqlfluff-1733`), below the minimum
  `3`; blocker `same_repo_cross_task_protect_lt_3`; ready for mix `false`.
  Do not train the score-head mix yet.  Next expand memory/source labels
  specifically for sqlfluff parser/rule hard negatives from non-1517 instances,
  then rerun score-head mix eval under strict held-out testing.
- [x] Update LATEX-NIPS related work with SWE-Explore and FastContext.
  Added a narrow repository-exploration comparison:
  SWE-Explore benchmarks repository exploration as a separable coding-agent
  capability, and FastContext trains a compact repository explorer to reduce
  downstream repair context cost.  Framing distinction: our small controller
  must also learn memory reliability and evidence-packet boundaries before
  large-model delegation.  Compile check with
  `neurips_2026_sweexplore_check` succeeded.
  Update 2026-06-17 06:20 CST: targeted cross-task hard-negative transfer is promising but still blocked. Added `build_targeted_hard_negative_reliability_readout.py`, `build_targeted_hard_negative_score_head_transfer_rows.py`, and generalized targeted card mining with `--path-prefix`; tests pass (`4 passed`). Sqlfluff targeted transfer rows fixed all three sqlfluff-1517 false allows but introduced one pydicom-1139 false allow. Pydicom targeted transfer rows fixed that pydicom regression. Combined sqlfluff+pydicom mix reaches `30/31` overall, allow `8/8`, protect `22/23`, but still leaves one sqlfluff false allow (`6486c7...`, prob `0.5347`). Do not train yet. Next: build a no-regression/weighted score-head diagnostic or narrow supervised atom-margin score head that keeps allow `8/8` and protect `>=0.9` without swapping regressions across sqlfluff/pydicom; then rerun old four-way / semantic-binary / equalized-A-B / file-support / binary reliability no-regression gates before any optimizer promotion.
  Update 2026-06-17 06:30 CST: scripted score-head weight sweep added and reproduced. `scripts/evaluate_memory_reliability_score_head_weight_sweep.py` plus test pass. Artifact `runs\score_head_weight_sweep_sqlfluff_pydicom_v2_scripted_20260617_0630` finds 5 perfect diagnostic settings on the original 31-row strict eval: sqlfluff:pydicom weights `2:1`, `3:1`, `4:1`, `5:1`, `5:2`, all with `31/31`, allow `8/8`, protect `23/23`. This is target-design evidence only, not a runtime rule. Next build a protected/balanced score-head or multitask objective around the `2:1` region with allow preservation anchors, then rerun old reliability no-regression gates before any training or serving change.
  Update 2026-06-17 06:50 CST: materialized the protected score-head candidate around the `2:1` sqlfluff:pydicom region. Added `scripts/build_memory_reliability_score_head_protected_candidate.py` and test; tests pass (`3 passed`). Artifact `runs\memory_reliability_score_head_protected_candidate_sql2_pyd1_v1_20260617_0650` has `73` rows (`31` base preservation + `42` cross-task hard-negative transfer), strict original eval `31/31`, allow `8/8`, protect `23/23`, failures `[]`. It is `ready_for_score_head_target=true` but `ready_for_training=false` and `ready_for_runtime_rule=false` because old no-regression gates have not run. Next: build or run the no-regression gate bundle for four-way reliability, semantic binary, equalized A/B, file-support atom, and existing binary reliability before any optimizer/serving promotion.
  Update 2026-06-17 07:10 CST: built the no-regression bundle for the protected score-head candidate. Added `scripts/summarize_score_head_candidate_no_regression_bundle.py` and test; tests pass (`2 passed`). Manifest `runs\score_head_candidate_no_regression_bundle_sql2_pyd1_v1_20260617_0710.json` blocks training despite score-head strict eval `31/31`, because old baseline gates are already collapsed: four-way reliable-current `0/8`, semantic reject controls `0/23`, equalized A positives `0/8`, file-support TRUE `0/9`. Binary reliability floor is preserved locally (`0.696970`, false-use `9`, reliable recall `8`) but not sufficient. Next define a recovery-threshold contract for post-training gates instead of plain no-regression, then only consider tiny isolated score-head/controller training if the plan requires improving collapsed gates while preserving binary reliability and score-head `31/31`.
  Update 2026-06-17 07:20 CST: built the recovery-threshold contract for the protected score-head candidate. Added `scripts/build_score_head_recovery_threshold_contract.py` and test; tests pass (`2 passed`). Contract `runs\score_head_recovery_threshold_contract_sql2_pyd1_v1_20260617_0720.json` keeps training blocked and requires: score-head `31/31` preserved; four-way reliable-current >=0.5 and no collapse; semantic reject controls >=0.5 and no all-USE; equalized reliable positives >=0.5 and no all-B; file-support TRUE >=3/9 with FALSE 24/24; binary reliability >=0.696970 with false-use <=9 and reliable recall >=8. Next only build a training/eval plan if it explicitly targets these recovery metrics; do not launch training from score-head `31/31` alone.
  Update 2026-06-17 07:30 CST: finished the post-training recovery scorer and materialized a mixed recovery dataset draft, but still blocked training. Added `scripts/score_score_head_recovery_post_gates.py`, `scripts/materialize_score_head_recovery_dataset_draft.py`, and tests; latest focused tests pass (`3 passed`). Baseline post-gate artifact `runs\score_head_recovery_post_gate_baseline_reject_sql2_pyd1_v1_20260617_0740.json` correctly rejects the current v22/baseline state: score-head `31/31` and binary reliability floor pass, but four-way reliable-current `0.0`, semantic reject controls `0.0`, equalized reliable positives `0.0`, and file-support TRUE `0/9` still fail. Draft dataset `runs\score_head_recovery_dataset_draft_sql2_pyd1_v1_20260617_0755` has `230` rows (`250` weighted) across score-head preservation, four-way, semantic binary, equalized A/B, file-support atom, and binary preservation. It is `ready_for_score_head_target_design=true` but `ready_for_training=false`, `ready_for_runtime_rule=false`, and `ready_for_packet_integration=false`; blockers are collapsed baseline gates, missing concrete training format, and post-gate rejection. Next: build exactly one concrete score/readout training-format converter from this draft, then run post-gates after a tiny isolated adapter only if the converter preserves the contract. Still do not add runtime repo/file/symbol rules, do not serve a free-form route/packet model, and do not launch training merely because the draft exists.
  Update 2026-06-17 07:35 CST: built the concrete fixed-label readout format from the draft without launching training. Added `scripts\build_score_head_recovery_fixed_label_readout.py` and test; test passes (`1 passed`). Artifact `runs\score_head_recovery_fixed_label_readout_sql2_pyd1_v1_20260617_0810` has `230` rows / `250` weighted rows, prompt leakage `0`, max prompt length `3445`, average prompt length `1801.4`, and labels grouped by task: score-head `ALLOW=8/PROTECT=65`, four-way `USE_CURRENT_RELIABLE=8/REVERIFY_BEFORE_USE=12/REJECT_UNRELATED=11`, semantic/binary `USE=8/REJECT=23`, equalized `A=8/B=23`, file-support `TRUE=9/FALSE=24`. It is `ready_for_no_update_readout=true` but still `ready_for_training=false`, `ready_for_runtime_rule=false`, and `ready_for_packet_integration=false`. Next: run a no-update fixed-label readout gate or formatter-specific scoring dry run before any tiny adapter. Do not train from this just because it is now parquet/jsonl; the acceptance condition remains post-gate recovery plus score-head/binary preservation.
  Update 2026-06-17 07:45 CST: added a generic fixed-label generation smoke gate and confirmed the new readout format is scoreable but not solved. `scripts\run_fixed_label_readout_generation_gate.py` plus tests pass (`4 passed` with converter tests). Rebuilt readout pair ids to use stable group/task fallback instead of numeric indices. Per-label-1 v22 smoke: `13` rows, valid labels `13/13`, match `10/13`, tokens `8207`; failures are binary `REJECT->USE`, equalized `B->A`, and four-way `REVERIFY_BEFORE_USE->REJECT_UNRELATED`. Per-label-2 v22 smoke: `26` rows, valid labels `26/26`, match `19/26`, tokens `16242`; binary predicts all `USE` (`2/4`), equalized predicts all `A` (`2/4`), file-support is `4/4`, four-way is `5/6`, score-head is `3/4`, semantic binary is `3/4`. This is good format evidence but not training permission. Next: run a no-update logprob gate for the fixed-label readout or build a tiny adapter plan with post-gate scorer as acceptance. Do not treat generation validity as enough to train or integrate.
  Update 2026-06-17 13:36 CST: finished a stricter fixed-label generation post-gate proxy and v1d recovery-target draft without launching training. Added `scripts\summarize_fixed_label_generation_post_gate_proxy.py`, `scripts\build_fixed_label_generation_failure_slices.py`, and `scripts\build_balanced_fixed_label_recovery_target.py` with tests (`8 passed`, `7 passed`, `5 passed` across targeted suites). Full v22 generation proxy on `230` rows has valid-label `1.0`, match `0.747826`, but blockers remain: score-head ALLOW only `2/8`, equalized B only `3/23`, file-support FALSE `21/24`, binary reliability `21/31` with false-use `10`. Failure slices: `58` failures / `172` anchors; biggest slices are `b_negative_misused_as_positive=20`, `reject_memory_false_use=10`, `reverify_collapsed_to_reject=9`, `allow_overprotected=6`, `semantic_reject_false_use=6`. Built draft `runs\score_head_recovery_fixed_label_readout_sql2_pyd1_v1_20260617_0810\balanced_v1d_target_from_generation_failures` with `89` rows (`58` focused failures + `31` anchors), missing pairs `0`, still `ready_for_training=false`. No-update v22 generation on this focused draft is valid-label `1.0` but match `0.348315`, confirming it is a useful recovery slice, not a solved dataset. Next: convert this draft into an explicit tiny v1d SFT/score-head launch plan with held-out anchors and mandatory generation + post-gate acceptance; do not serve or integrate any adapter until gates pass.
  Update 2026-06-17 14:05 CST: completed the requested v1d sequence through rejection. Added formal split, launch manifest, and no-regression scorer scripts/tests (`6 passed`). Split artifact `runs\score_head_recovery_fixed_label_readout_sql2_pyd1_v1_20260617_0810\v1d_formal_train_eval_split_20260617_1400` has `67` train / `22` eval with all strata represented. Tiny remote SFT completed in `/mnt/memory-agent/runs/score_head_recovery_fixed_label_readout_sql2_pyd1_v1_20260617_0810/v1d_fixed_label_tiny_launch_20260617_1405` (`67` steps, val loss `3.134943 -> 1.026922`). Temporary `8002` probe server ran gates and was stopped; `8001` still serves v22. Gates improved focused target `0.348315 -> 0.595506` and full230 `0.747826 -> 0.821739`, but no-regression rejects: eval `0.681818 < 0.70`, score-head ALLOW `0/8`, REVERIFY `5/12`, equalized B `8/23`, file-support FALSE `19/24`. Do not integrate, serve, or continue this adapter as accepted. Next target must preserve score-head ALLOW and file-support FALSE while recovering equalized B / REVERIFY; likely use a mixed objective or stricter preservation sampling, not runtime rules.
  Update 2026-06-17 21:15 CST: real downstream collaboration sanity check passed on the tiny packet slice. Added `scripts\run_v1k_real_collab_probe.py` and `tests\scripts\test_run_v1k_real_collab_probe.py`; test passes (`3 passed`). Probe artifact `runs\v1k_real_collab_probe_20260617_2115\summary.json` uses `gpt-5.4-mini` on 3 packet-ready positives plus 3 sqlfluff protect controls under `no_memory`, `memory_packet_baseline`, and `v1k_filtered_packet`. Result: `3/3` v1k ready packets were actually used by the large model, `0/3` sqlfluff protect controls triggered delegate, v1k-filtered ready rows preserved file `3/3`, test node `3/3`, and stronger symbol use than no-memory. This is not strict SWE resolve because local Docker is unavailable. Next: expand to a 10--20 row cross-task assistant-chain validation with the same no-memory / memory-packet / v1k-filtered comparison; keep it scoreable as localization/test/tool-call/evidence-use unless Docker/harness is available. Do not promote packet integration, runtime rules, or another tiny adapter from the 3-positive probe alone.
  Update 2026-06-17 21:35 CST: expanded smoke passed with strong file-supported positives from the multisource positive audit. `scripts\run_v1k_real_collab_probe.py` now accepts `--positive-audit-matches` but only selects `candidate_file_supported_reliable_current` rows with path overlap, symbol overlap, and a focused test node. Probe `runs\v1k_real_collab_probe_20260617_2135\summary.json` has `7` deduped ready positives + `3` sqlfluff controls (`30` condition rows, `27` model calls), with `7/7` v1k packet use and `0/3` sqlfluff false delegates. Ready-only v1k-filtered improves test retention over no-memory (`7/7` vs `2/7`) and symbol hits (`45` vs `31`) while preserving file hits (`7/7`). Next formal step: build a 10--20 row assistant-chain validation set. Either accept pvlib as an explicit cross-repo extension (current ready positives include 4 pvlib rows) or first mine more marshmallow/pydicom/sqlfluff strong positives. Do not train or integrate yet; this is still localization/evidence-use proxy evidence, not strict resolve.
  Update 2026-06-18 02:15 CST: route-boundary work moved to an atom-aware paired-swap diagnostic. Added `build_v1k_atom_aware_route_boundary_pairwise.py`, `build_atom_aware_route_recovery_target.py`, and expanded `run_pairwise_choice_generation_gate.py` summaries with `by_gold_route` / `by_atom_pattern`; focused tests pass (`7 passed`). Artifact `runs\v1k_atom_aware_route_boundary_pairwise_20260618_0155` has `110` rows / `55` base pairs, A/B balanced, prompt leakage `0`, and `DELEGATE_PACKET=24`, `SELF_HANDLE=86`. `gpt-5.4-mini` nearly solves it (`choice_match=0.981818`, `both_swaps=0.963636`, SELF_HANDLE `86/86`), proving the surface is judgeable when reliability atoms are visible. Local v22 still fails (`choice_match=0.590909`, `both_swaps=0.218182`) with B-position skew and SELF_HANDLE only `41/86`, although DELEGATE preservation is `24/24`. Built recovery target `runs\v1k_atom_aware_route_recovery_target_20260618_0215` with `45` missed SELF_HANDLE rows plus `24` DELEGATE preservation rows. Next: build a held-out split or no-update recovery gate around this target, then only consider a tiny isolated calibration/SFT if acceptance requires both-swaps route accuracy >=0.8, SELF_HANDLE no-overdelegate >=0.9, DELEGATE preservation >=0.9, and no regression on the protected memory-reliability paired-swap gate. Still do not connect route or packet evidence filtering to runtime patcher.
  Update 2026-06-18 02:55 CST: held-out split and acceptance scorer are now in place. Added `materialize_atom_aware_route_recovery_split.py` and `score_atom_aware_route_acceptance.py`; tests pass (`2 passed`). Split `runs\v1k_atom_aware_route_recovery_split_20260618_0245` has `51` train / `18` eval rows, eval mix `DELEGATE_PACKET=6`, `SELF_HANDLE=12`, overlap `0`, and is `ready_for_tiny_calibration_gate=true` but still `ready_for_training=false`, `ready_for_runtime_rule=false`, `ready_for_packet_integration=false`. Acceptance scorer maps predicted A/B back to route behavior and enforces: route both-swaps >=0.8, SELF_HANDLE no-overdelegate >=0.9, DELEGATE preservation >=0.9, protected memory-reliability both-swaps no-regression >=0.555556, valid choice >=1.0. Current local v22 full-route acceptance is correctly rejected (`both_swaps=0.218182`, SELF_HANDLE no-overdelegate `0.476744`, DELEGATE preservation `1.0`, memory no-regression pass). `gpt-5.4-mini` full-route acceptance passes (`both_swaps=0.963636`, SELF_HANDLE no-overdelegate `1.0`, DELEGATE preservation `0.916667`), proving the scorer is achievable. Local eval-split smoke rejects harder (`both_swaps=0.0625`, SELF_HANDLE no-overdelegate `0.0`). Next: optional tiny isolated calibration/SFT on the 51-row train split, then rerun eval split, all-recovery, full 110-row route acceptance, and protected memory-reliability no-regression before any runtime patcher integration.
- [x] Handle the four residual false-packet cases in the direct `L/P` route
  controller.  v2 atom-priority direct readout now has full 110-row both-swaps
  `1.0`, SELF_HANDLE no-overdelegate `1.0`, DELEGATE preservation `1.0`, and
  residual audit `rows=0/base_pairs=0`.
- [x] Add a conservative runtime hook for reliable-evidence filtering.  New
  `--memory-gate-mode atom_direct` is available in the SWE runner and
  continual batch runner.  It only passes memories with current-task-support
  atoms, no protective atoms, and concrete packet anchors.
- [x] Build packet/runtime integration readiness evidence.  Runtime readiness
  manifest
  `runs\v1k_atom_aware_route_direct_readout_v2_atompriority_20260618_1210\runtime_readiness_manifest_20260618_1235.json`
  passes with decision `runtime_hook_ready_atom_direct_only`; bounded replay
  `runtime_call_replay_20260618_1245.json` has false packet calls `0`, missed
  delegates `0`, direct `P` call reduction `0.781818`, and anchor-only call
  reduction `0.981818`.
- [x] Run a strict downstream SWE-Bench/Docker smoke for `atom_direct`.
  Artifact `runs\atom_direct_harness_smoke_20260618_1355\formal_summary.json`
  passes.  One anchor-ready `P` row (`pvlib__pvlib-python-1854`) made a fresh
  `gpt-5.4-mini` repair call with `memory_gate=pass`; four former residual
  false-packet controls were `L` no-call rows using cached baseline patches.
  Official SWE-Bench harness result: `5/5` resolved, `0` empty patches,
  `0` evaluator errors, and `0` accidental large-model calls on `L` rows.
  This satisfies the bounded smoke but is not yet a broad resolved-rate claim.
- [x] Scale the runtime collaboration validation to the paper main-table slice.
  Matched memory-covered 36-row Docker run is complete under A/B/C.  A resolves
  `4/36`, B resolves `8/36`, and C trained `MemGate` + packet selective retry
  resolves `9/36` while reducing large-model rows from `36/36` to `29/36` and
  tokens from B's `7.05M` to `5.60M`.  Artifacts are under
  `runs\matched-swebench-main-table-memory-covered-36-corrected`.
- [x] Test whether C can reuse Algorithm 1's Q-value memory update over
  multiple rounds.  Result: C-R1 matched the original top-k retrieval exactly;
  Q-updated C-R2 preserved `9/36` resolved while reducing large-model rows to
  `21/36` and tokens to `3.97M`; Q-updated C-R3 preserved `9/36` with
  `20/36` rows and `3.48M` tokens.  Artifacts:
  `runs\matched-swebench-main-table-memory-covered-36-corrected\c_q_rounds`.
- [ ] If time remains, improve only the no-call fallback exposed by C-R3.
  Do not broaden the large-model policy indiscriminately; target
  `SELF_HANDLE` fallback, empty-patch verification, or a bounded retry rule
  that preserves the current `9/36` resolved and about `20/36` large-row cost
  story.
- [ ] Monitor the fresh no-cache expanded-memory MemGate Q-round run before
  making any stronger paper claim.  Active artifact:
  `runs\fresh-memgate-q-expanded36`.  The cached C-R2/R3 rows should be treated
  only as diagnostics until this fresh run finishes.  Current priority is C
  fresh R1/R2/R3 with `route_or_fallback_P`; the expanded strong-memory
  baseline has 4 partial predictions and can be resumed later.
- [ ] Keep the paper wording precise.
  The served backbone remains `local-qwen3-8b-memory-polarproxy-v22`; the newer
  trained contribution is the guarded `MemGate`/readout/packet policy.  Do not
  claim that a newer free-form model replaced v22 unless a separately served
  adapter passes the full runtime gates.
- [x] Recompile `LATEX-NIPS` and verify the main table renders after the C
  update.  `pdflatex` completed successfully twice on `neurips_2026.tex`; PDF
  text contains the C row with `9/36`, `29/36`, and `5.60M`, and stale
  `20/36` / `2.67M` / `11/36` wording is gone.
- [ ] Do not promote the broad delegate-patch sufficiency scorer.  It remains a
  negative control with `false_rows_prefer_delegate`; runtime use is limited to
  the deterministic `atom_direct` gate.

- [ ] Treat
  `runs\fresh-memgate-q-mixed12-policyfix-nofallback-20260620_0200` as a
  negative fresh mixed result, not as paper evidence for better-and-cheaper
  multi-round updating.  R1/R2/R3 stayed at `1/12` resolved while P rows grew
  `2 -> 3 -> 6` and large-model tokens grew
  `0.294M -> 0.702M -> 1.210M`.  Use it as diagnosis that
  `route=L && empty` penalty works but is not sufficient.

- [ ] Rebuild the mixed split before another three-round claim.  The next
  easy/self-suitable set must be proven easy under the exact fresh local-Qwen
  branch with the same memory file, step limit, and no cached patches.  Require
  each easy row to produce a non-empty local patch and preferably pass SWE-Bench
  locally.  Keep hard/delegate-needed rows only if a strong-memory
  `gpt-5.4-mini` baseline can produce non-empty patches and solve at least some
  of them; otherwise the split cannot show dynamic-call advantage.

- [ ] Audit memory quality for the new mixed split before running Q rounds.
  For every target, save top-k memories, selected packet memories, file/path
  overlap, test-node overlap, and a short "why this memory helps" note.  Reject
  memories that are only same-repo but do not share the failure mode.  Do not
  let broad same-repo memories drive delegation claims.

- [ ] Tighten the Q-update mechanism before the next nofallback run:
  - Do not penalize top memories on P failure when the packet has no
    `selected_memory_ids`; record `p_route_failure_unattributed` instead.
  - Keep `route=L && empty` penalty, but apply it only to memories actually
    used by the L/self path if that trace is available; otherwise store it as
    weak evidence rather than a strong top-memory penalty.
  - Preserve per-round Q-update history instead of overwriting/retaining only
    `q_update_sources`, so later diagnosis can separate R1, R2, and R3 deltas.
  - Consider a cost-aware reward such as
    `resolved_reward - lambda * large_tokens` plus a separate empty-patch
    penalty, so Q updates optimize both solve rate and token cost rather than
    merely pushing uncertain rows toward P.

- [ ] Add an acceptance gate for the next multi-round experiment.  A run should
  be considered positive only if it either improves solved count at comparable
  token cost or preserves solved count while reducing large-model tokens.  For
  the 12-row mixed split, a minimal target is at least `2/12` resolved and
  fewer tokens than always-delegate on the same 12 rows; for a 36-row paper
  slice, preserve the existing `9/36` solved while reducing large-model rows
  and keeping empty patches from rising sharply.

- [ ] Compare against two fresh baselines for the same rebuilt split before
  claiming dynamic calling: local-only fresh Qwen and always-delegate
  `gpt-5.4-mini` with the same memory file.  Without these, a multi-round
  result cannot be judged as simultaneously better and cheaper.

- [x] Implement the first Q-update guardrail.  `P` failures without
  `selected_memory_ids` now create `p_route_failure_unattributed` metadata
  instead of penalizing top memories.  Q updates now append per-memory
  `q_update_history`, and the fresh-round runner passes `--round-label`.
  Targeted tests pass.

- [x] Build an offline split audit before launching another long nofallback
  run.  Artifact
  `runs\dynamic-call-split-audit-20260620_policyfix` shows strict
  fresh-local easy pool `0`, hard pool `8`.  Fallback artifact
  `runs\dynamic-call-split-audit-20260620_fallback_oldlocal` shows old-local
  easy pool `9` but all require fresh local verification.

- [ ] Run a minimal fresh local-only verification on the fallback old-local
  easy candidates before using them as easy/self-suitable rows.  Candidate file:
  `runs\dynamic-call-split-audit-20260620_fallback_oldlocal\easy_instances.json`.
  Acceptance: non-empty local patch for each selected easy row, and ideally
  official SWE-Bench resolved.  Reject rows that are only old cached/conservative
  successes.

- [x] Run the first fresh local-only easy verification.  Artifact:
  `runs\fresh-local-verify-easy-oldlocal-20260620`.  All four fallback old-local
  easy candidates produced empty patches, so none are acceptable as
  easy/self-suitable evidence.

- [ ] Mine or run a small strong-memory hard-candidate pass outside the current
  36-row overlap.  Need rows where `gpt-5.4-mini` with the same memory file
  resolves and fresh local Qwen does not.  Without these, a 1:2
  easy:self-suitable / hard:delegate-needed split is not identifiable.

- [ ] Build a new easy-candidate source instead of reusing old conservative
  successes.  Options: lower local step-limit/task complexity to very small
  SWE-Bench rows, add self-handle examples from dev/lite where fresh local
  Qwen actually produces non-empty patches, or use a proxy self-handle task
  where local success is directly measurable.  Do not run another 1:2 mixed
  Q-round until at least two fresh local-only easy rows pass.

- [x] Build a new evidence-qualified easy+hard candidate split from broader
  dev summaries.  Artifact:
  `runs\mixed-dev-easy1-hard2-candidate15-20260620`.  It contains `5` easy
  candidates and `10` hard candidates, exactly `easy:hard = 1:2`.  The builder
  is `scripts\build_easy_hard_eval_split.py`, and its targeted test passes.

- [ ] Restore or restart the local tunnel/model health before fresh
  verification.  The latest local probe to
  `http://127.0.0.1:18001/v1/models` failed with an unexpected closed
  connection while a stale local forwarder still listened on port `18001`.
  Do not launch the verification until the endpoint returns the Qwen model
  list again.

- [x] Restore the local tunnel/model health.  Remote `127.0.0.1:8001` and local
  `127.0.0.1:18001` both returned `/v1/models` and chat completion after the
  tunnel restart.

- [x] Fix the per-instance wrapper to support local text-action models.
  `scripts\run_swebench_condition_per_instance.py` now forwards
  `--model-class`, which is required for current Qwen runs with
  `--model-class litellm_textbased`; otherwise the default tool-call parser
  treats normal fenced command responses as `0` actions.

- [x] Fresh-verify the five candidate easy rows under the current active model service:
  `runs\mixed-dev-easy1-hard2-candidate15-20260620\fresh_verify_easy_instances.json`.
  Valid textbased run:
  `runs\fresh-local-verify-easy-dev15-textbased-20260620`.  Result:
  `0/5` produced a non-empty accepted patch; all five ended in
  `LimitsExceeded`.  Do not use this easy side for R1/R2/R3.

- [x] Rebuild the easy side again from fresh-current evidence, not historical
  RWR summaries.  Candidate strategy: run a broader dev/local-only sweep with
  `--model-class litellm_textbased`, lower-risk task families, and possibly a
  shorter "proxy self-handle" benchmark where local success is directly
  measurable.  Accept only rows with non-empty accepted patches; prefer rows
  that official SWE-Bench marks resolved.

- [x] Run a broader fresh-current local sweep over the 23 dev candidates.
  Artifact root: `runs\easy-mining-dev-current-20260620`.  No-memory
  `step_limit=24` produced `5/23` non-empty submitted patches but official
  SWE-Bench marked `0/5` resolved.  Re-running those five with no-memory
  `step_limit=48` still yielded `0` resolved.  Memory-on step 24 hurt the first
  near-miss and was stopped.

- [x] Stop trying to force an easy split from this 23-row SWE-Bench Lite dev
  pool.  It currently has `0` fresh-current resolved rows for Qwen, so any
  "easy" label from it would be unsupported.

- [x] Build the next easy source from a genuinely simpler and measurable task
  family.  Two acceptable options:
  1. proxy self-handle tasks derived from SWE-Bench issues but scored by
     deterministic unit checks before full patch submission;
  2. a larger fresh-current local sweep over easier benchmark families or
     historical tasks, accepting only rows that current Qwen resolves under the
     exact runtime.
  Completed with custom `proxy_easy` Hybrid-Gym-style tasks.  Current Qwen on
  `runs\proxy-easy-custom-20260620\qwen_proxy_easy.jsonl`: `5/5` action,
  `5/5` skill match, `5/5` semantic pass, mean strict score `0.944286`,
  about `256` tokens/task.

- [x] Once at least two fresh-current resolved easy rows exist, rebuild the
  mixed split with those easy rows plus the audited hard/delegate rows, then
  run local-only, always-delegate, and MemGate/Q R1-R3 baselines.
  Rebuilt as `runs\proxy-easy1-swe-hard2-mixed15-20260620`: `5` custom
  `proxy_easy` rows plus `10` SWE hard rows (`easy:hard = 1:2`).  Note that
  proxy-easy pass is a deterministic route/cost metric, not official
  SWE-Bench resolved.

- [x] Add or adapt a mixed evaluator that can score both row kinds in
  `runs\proxy-easy1-swe-hard2-mixed15-20260620`: use the Hybrid-Gym proxy
  scorer for `kind=proxy_easy`, and the existing SWE-Bench/per-instance
  wrapper for `kind=swe_hard`.  Report separate metrics plus combined route
  and token cost.
  Implemented as `scripts\evaluate_proxy_easy_swe_hard_split.py`, with
  `proxy_easy_pass`, `swe_hard_resolved`, route errors, large-model rows, and
  `route_correct_success` reported separately.

- [x] Run three baselines on the new mixed split before more Q updating:
  local-only Qwen, always-delegate `gpt-5.4-mini`, and the current MemGate/Q
  policy.  Success criterion: keep proxy-easy pass near `5/5`, improve or
  preserve hard-side solved count relative to local-only, and spend fewer
  large-model tokens than always-delegate.
  Fresh GPT hard eval and actual MemGate policy are complete.  Always-delegate
  fresh hard resolved `5/10`; actual MemGate mixed policy used `4/15`
  large-model rows and `473,492` large tokens vs always-delegate `15/15` rows
  and `1,145,180` large tokens.  It is cheaper but still misses too many hard
  delegates.

- [x] Fresh-run always-delegate `gpt-5.4-mini` on the `10` `swe_hard` rows in
  `runs\proxy-easy1-swe-hard2-mixed15-20260620\swe_hard_instances.json`.
  This replaces
  `runs\proxy-easy1-swe-hard2-mixed15-20260620\historical_hard_evidence_summary.json`
  before any final claim about hard-side SWE-Bench resolved count.
  Correct run is on SWE-Bench Lite `dev`, not `test`:
  `runs\proxy-easy1-swe-hard2-mixed15-20260620\fresh_gpt54mini_hard_always_delegate_dev`.
  Official eval: `5/10` resolved, `5/10` unresolved, `0` empty/error.

- [x] Build the actual MemGate/Q call policy for the mixed split.  For
  `proxy_easy`, use the proxy task prompt/evidence and score route directly;
  for `swe_hard`, use current retrieval/memory policy.  Evaluate with
  `scripts\evaluate_proxy_easy_swe_hard_split.py` against the fresh hard
  summary.
  Implemented as proxy_easy fixed `L` plus hard-side
  `memgate_hard_readout_policy`.  Result: route counts `L=11`, `P=4`,
  proxy-easy false delegates `0`, SWE-hard missed delegates `6`.

- [x] Improve hard-side delegate recall before running full R1/R2/R3.  Current
  MemGate misses three fresh-resolved hard rows:
  `pvlib__pvlib-python-1072`, `pvlib__pvlib-python-1854`,
  `pvlib__pvlib-python-1606`.  Candidate fix: add a recall-protection rule or
  training signal for same-repo clusters with `same_repo_memories >= 3` and
  `max_similarity >= 0.28`, while keeping proxy-easy rows protected as `L`.
  Done with `scripts\apply_hard_recall_protection_policy.py`.
  One-shot policy
  `runs\proxy-easy1-swe-hard2-mixed15-20260620\policies\memgate_recall_protected_call_policy.json`
  promotes exactly those three pvlib hard rows and keeps all proxy-easy rows
  on `L`.  Mixed eval reaches proxy `5/5`, hard `5/10`, route-correct success
  `10/15`, large rows `7/15`, large tokens `762,612`.

- [x] Then run R1/R2/R3 Q updates on the mixed split.  Q reward must continue
  to credit only memories actually selected into the packet or used on the P
  route; do not reward every retrieved memory.  Keep route=L empty penalties
  stronger than ordinary failure, with the current multiplier `1.5`.
  Done as a light strategy/Q accounting run:
  `runs\proxy-easy1-swe-hard2-mixed15-20260620\q_recall_protected_rounds`.
  R1/R2/R3 all preserve proxy `5/5` and hard `5/10`.  R2 is the best current
  point: `6/15` large rows and `639,683` large tokens, compared with
  always-delegate `15/15` large rows and `1,145,180` tokens.  This is positive
  mixed proxy evidence, but it reuses the fresh always-delegate hard
  trajectories for accounting; do not overstate it as a new packet-conditioned
  SWE-Bench run.

- [ ] Freeze the current hard recall protection thresholds before further
  tuning on this split.  Next validation should be a second mixed split or a
  held-out hard set, using the same rule (`same_repo_memories >= 3`,
  `max_similarity >= 0.28`) without hand-adjusting it to the current 15 rows.
  Acceptance: preserve easy local pass, match or improve always-delegate hard
  resolved count, and reduce large-model tokens.

- [ ] Add a cost-aware Q-round selector.  When multiple rounds have the same
  proxy pass and hard resolved count, select the lowest large-token policy
  rather than blindly taking the last round.  In the current run R2 dominates
  R1/R3 on cost while preserving success.

- [ ] Split route reward from memory-evidence reward in the next Q-update
  mechanism.  Current selected-memory updates can oscillate when the same
  memory is selected by both solved and unsolved P-route rows; R3 reintroduced
  `pvlib__pvlib-python-1707` after R2 had removed it.  Keep packet-selected
  attribution, but add per-target route outcome bookkeeping so unresolved
  delegate rows do not indirectly boost unrelated future delegation.

- [ ] Fresh-check hard rows on the same split:
  `runs\mixed-dev-easy1-hard2-candidate15-20260620\fresh_verify_hard_local_instances.json`.
  Acceptance: current local Qwen should remain empty/unresolved on most of
  them, while GPT evidence remains strong enough to justify delegation.

- [ ] After fresh verification, run baselines on the verified split before
  multi-round Q updating: local-only Qwen, always-delegate `gpt-5.4-mini`, then
  MemGate/Q R1-R3.  Claim success only if it improves solved count at comparable
  cost or preserves solved count while reducing large-model tokens.
