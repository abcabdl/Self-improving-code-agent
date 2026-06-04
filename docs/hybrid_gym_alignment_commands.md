# Hybrid-Gym Alignment Commands

This document aligns our memory-agent offline training with the Hybrid-Gym paper setup.

Aligned paper setting:

- Student model: `Qwen/Qwen2.5-Coder-7B-Instruct`
- Training benchmarks:
  - `hybrid_gym_func_localize`
  - `hybrid_gym_issue_localize`
  - `hybrid_gym_dep_search`
  - `hybrid_gym_func_gen`
- Evaluation benchmarks:
  - SWE-Bench Verified
  - SWT-Bench Lite / Verified
  - Commit-0 Lite
- Training style:
  - Hybrid-Gym baseline: successful-trajectory SFT
  - Our method: memory reward-weighted offline training plus locate/edit/test skills

## 0. PowerShell Variables

Run on Windows PowerShell:

```powershell
$MINI = "C:\Users\zrz20\Desktop\vscode\multi-rl\创智大作业\mini-swe-agent"
$VERL = "C:\Users\zrz20\Desktop\vscode\multi-rl\PettingLLMs-main\verl"
$HYBRID = "C:\Users\zrz20\Desktop\vscode\multi-rl\创智大作业\Hybrid-Gym-main"

$BASE_MODEL = "Qwen/Qwen2.5-Coder-7B-Instruct"
$EXP = "hybridgym-align-qwen25coder7b-memory-v1"
```

## 1. Serve Base Model

Run on Linux/WSL with CUDA, or on your GPU server:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model Qwen/Qwen2.5-Coder-7B-Instruct \
  --served-model-name local-qwen25coder7b \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90
```

For trained checkpoint evaluation, serve the merged or adapter-loaded model as:

```bash
python -m vllm.entrypoints.openai.api_server \
  --model /path/to/qwen25coder7b-memory-rwr \
  --served-model-name local-qwen25coder7b-memory-rwr \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90
```

## 2. Generate Memory-Agent SWE Rollouts

Run on Windows PowerShell:

```powershell
cd $MINI

.\.venv\Scripts\python.exe scripts\run_agent_rl_rollouts.py `
  --out-dir runs\$EXP\agent_rl_rollouts `
  --initial-memory runs\memory\self_improve_memory.json `
  --subset lite `
  --split dev `
  --rollouts-per-instance 4 `
  --model openai/local-qwen25coder7b `
  --api-base http://127.0.0.1:8000/v1 `
  --memory-k 2 `
  --memory-strategy hybrid `
  --memory-stage-aware `
  --workers 1 `
  --eval-max-workers 1
```

Build reward-weighted Parquet:

```powershell
cd $MINI

.\.venv\Scripts\python.exe scripts\build_verl_agent_rl_data.py `
  --input runs\$EXP\agent_rl_rollouts\agent_rl_rollouts.jsonl `
  --output runs\$EXP\verl_agent_rwr `
  --output-format parquet `
  --val-ratio 0.05 `
  --seed 1
```

Build successful-only SFT Parquet:

```powershell
cd $MINI

.\.venv\Scripts\python.exe scripts\build_verl_agent_rl_data.py `
  --input runs\$EXP\agent_rl_rollouts\agent_rl_rollouts.jsonl `
  --output runs\$EXP\verl_agent_sft_success `
  --output-format parquet `
  --min-reward 0.8 `
  --only-success `
  --val-ratio 0.05 `
  --seed 1
```

Build locate/edit/test skill Parquet from our trajectories:

```powershell
cd $MINI

.\.venv\Scripts\python.exe scripts\build_memory_skill_data.py `
  --input runs\$EXP\agent_rl_rollouts\agent_rl_rollouts.jsonl `
  --output runs\$EXP\verl_memory_skills `
  --format parquet `
  --val-ratio 0.05 `
  --seed 1
```

Mix agent records with skill records:

```powershell
cd $MINI

.\.venv\Scripts\python.exe scripts\mix_agent_rl_data.py `
  --agent-train runs\$EXP\verl_agent_rwr\train.parquet `
  --agent-val runs\$EXP\verl_agent_rwr\val.parquet `
  --skills-train runs\$EXP\verl_memory_skills\train.parquet `
  --skills-val runs\$EXP\verl_memory_skills\val.parquet `
  --output runs\$EXP\verl_mixed `
  --agent-ratio 0.70 `
  --skill-ratio 0.20 `
  --failed-ratio 0.10 `
  --seed 1
```

## 3. Generate Hybrid-Gym Training Trajectories

Run on WSL/Linux inside `Hybrid-Gym-main`.

First configure OpenHands `config.toml`:

```toml
[llm.qwen25_coder_7b]
model = "openai/local-qwen25coder7b"
base_url = "http://127.0.0.1:8000/v1"
api_key = "EMPTY"
```

Then run:

```bash
cd "/mnt/c/Users/zrz20/Desktop/vscode/multi-rl/创智大作业/Hybrid-Gym-main"

export EXP_NAME=hybridgym_align_qwen25coder7b_train
export RUN_WITH_BROWSING=false
export USE_HINT_TEXT=false

bash evaluation/benchmarks/hybrid_gym_func_localize/scripts/run_infer.sh \
  llm.qwen25_coder_7b local CodeActAgent 500 100 1 \
  hybrid-gym/hybrid_gym_func_localize train 1 swe issue_func \
  hybrid_gym_func_localize_train

bash evaluation/benchmarks/hybrid_gym_issue_localize/scripts/run_infer.sh \
  llm.qwen25_coder_7b local CodeActAgent 500 100 1 \
  SWE-Gym/SWE-Gym-Raw test 1 swe \
  hybrid_gym_issue_localize_train

python evaluation/benchmarks/hybrid_gym_dep_search/run_infer.py \
  --llm-config llm.qwen25_coder_7b \
  --agent-cls CodeActAgent \
  --dataset hybrid-gym/hybrid_gym_dep_search \
  --max-iterations 30 \
  --eval-num-workers 1 \
  --eval-output-dir evaluation/evaluation_outputs/hybrid_gym_dep_search_train

bash evaluation/benchmarks/hybrid_gym_func_gen/scripts/run_infer.sh \
  llm.qwen25_coder_7b local CodeActAgent 500 30 1 \
  hybrid-gym/hybrid_gym_func_gen train 1 \
  hybrid_gym_func_gen_train
```

Strict alignment requires converting Hybrid-Gym/OpenHands `output.jsonl` into the same verl Parquet schema:

```text
prompt
response
reward_model
data_source
extra_info
```

The converter is not included yet. Until that converter exists, use the memory skill data from Section 2 as the weak-alignment training source.

## 4. Train Hybrid-Gym-Style Successful SFT

Run on Linux/WSL with CUDA from `PettingLLMs-main/verl`.

```powershell
cd $VERL

torchrun --standalone --nnodes=1 --nproc_per_node=1 -m verl.trainer.fsdp_sft_trainer `
  data.train_files="$MINI/runs/$EXP/verl_agent_sft_success/train.parquet" `
  data.val_files="$MINI/runs/$EXP/verl_agent_sft_success/val.parquet" `
  data.custom_cls.path="verl/utils/dataset/agent_rl_dataset.py" `
  data.custom_cls.name=AgentRLDataset `
  data.max_length=8192 `
  data.truncation=left `
  data.train_batch_size=8 `
  data.micro_batch_size_per_gpu=1 `
  model.partial_pretrain=$BASE_MODEL `
  model.trust_remote_code=true `
  model.lora_rank=32 `
  model.lora_alpha=64 `
  model.target_modules=all-linear `
  optim.lr=5e-5 `
  trainer.total_epochs=5 `
  trainer.project_name=hybridgym-align `
  trainer.experiment_name="$EXP-sft-success" `
  trainer.default_local_dir="$MINI/runs/$EXP/checkpoints/sft_success" `
  trainer.logger='["console"]'
```

## 5. Train Memory RWR + Skills

Run on Linux/WSL with CUDA from `PettingLLMs-main/verl`.

```powershell
cd $VERL

torchrun --standalone --nnodes=1 --nproc_per_node=1 -m verl.trainer.fsdp_sft_trainer `
  data.train_files="$MINI/runs/$EXP/verl_mixed/train.parquet" `
  data.val_files="$MINI/runs/$EXP/verl_mixed/val.parquet" `
  data.custom_cls.path="verl/utils/dataset/agent_rl_dataset.py" `
  data.custom_cls.name=AgentRLDataset `
  data.max_length=8192 `
  data.truncation=left `
  data.train_batch_size=8 `
  data.micro_batch_size_per_gpu=1 `
  model.partial_pretrain=$BASE_MODEL `
  model.trust_remote_code=true `
  model.lora_rank=32 `
  model.lora_alpha=64 `
  model.target_modules=all-linear `
  optim.lr=5e-5 `
  trainer.total_epochs=5 `
  trainer.project_name=hybridgym-align `
  trainer.experiment_name="$EXP-memory-rwr-mixed" `
  trainer.default_local_dir="$MINI/runs/$EXP/checkpoints/memory_rwr_mixed" `
  trainer.logger='["console"]'
```

## 6. Evaluate on SWE-Bench Lite First

Run on Windows PowerShell:

```powershell
cd $MINI

.\.venv\Scripts\python.exe scripts\run_memory_gate_ablation.py `
  --out-root runs\$EXP\eval_swebench_lite `
  --initial-memory runs\memory\self_improve_memory.json `
  --initial-strategy-memory runs\strategy\strategy_r0.json `
  --subset lite `
  --split dev `
  --batch-size 5 `
  --limit 30 `
  --model openai/local-qwen25coder7b-memory-rwr `
  --api-base http://127.0.0.1:8000/v1 `
  --memory-k 2 `
  --memory-strategy hybrid `
  --memory-same-repo-k 2 `
  --memory-global-k 1 `
  --memory-gate-min-similarity 0.18 `
  --memory-gate-min-q 0.25 `
  --memory-stage-aware `
  --no-tool-bandit
```

## 7. Evaluate on SWE-Bench Verified

Run on WSL/Linux inside `Hybrid-Gym-main`.

Configure:

```toml
[llm.qwen25_coder_7b_memory_rwr]
model = "openai/local-qwen25coder7b-memory-rwr"
base_url = "http://127.0.0.1:8000/v1"
api_key = "EMPTY"
```

Then:

```bash
cd "/mnt/c/Users/zrz20/Desktop/vscode/multi-rl/创智大作业/Hybrid-Gym-main"

export EXP_NAME=hybridgym_align_memory_rwr_swe_verified

bash evaluation/benchmarks/swe_bench/scripts/run_infer.sh \
  llm.qwen25_coder_7b_memory_rwr local CodeActAgent 500 100 1 \
  princeton-nlp/SWE-bench_Verified test 1 swe
```

## 8. Evaluate on SWT-Bench

SWT-Bench Lite:

```bash
cd "/mnt/c/Users/zrz20/Desktop/vscode/multi-rl/创智大作业/Hybrid-Gym-main"

export EXP_NAME=hybridgym_align_memory_rwr_swt_lite

bash evaluation/benchmarks/swe_bench/scripts/run_infer.sh \
  llm.qwen25_coder_7b_memory_rwr local CodeActAgent 200 100 1 \
  logic-star-ai/SWT-Bench_Lite test 1 swt
```

SWT-Bench Verified:

```bash
cd "/mnt/c/Users/zrz20/Desktop/vscode/multi-rl/创智大作业/Hybrid-Gym-main"

export EXP_NAME=hybridgym_align_memory_rwr_swt_verified

bash evaluation/benchmarks/swe_bench/scripts/run_infer.sh \
  llm.qwen25_coder_7b_memory_rwr local CodeActAgent 500 100 1 \
  logic-star-ai/SWT-Bench_Verified test 1 swt
```

## 9. Evaluate on Commit-0 Lite

```bash
cd "/mnt/c/Users/zrz20/Desktop/vscode/multi-rl/创智大作业/Hybrid-Gym-main"

export EXP_NAME=hybridgym_align_memory_rwr_commit0_lite

bash evaluation/benchmarks/commit0/scripts/run_infer.sh \
  lite llm.qwen25_coder_7b_memory_rwr local CodeActAgent 200 100 1 \
  wentingzhao/commit0_combined test 1
```

## 10. Final Experiment Matrix

Report these systems:

```text
Base:
Qwen2.5-Coder-7B-Instruct

Hybrid-Gym aligned:
Qwen2.5-Coder-7B + successful SFT

Ours:
Qwen2.5-Coder-7B + memory RWR

Ours + Hybrid-Gym:
Qwen2.5-Coder-7B + memory RWR + locate/edit/test skills
```

Report these metrics:

```text
SWE-Bench Verified: resolved / localized / non-loop
SWT-Bench Lite: resolved
SWT-Bench Verified: resolved
Commit-0 Lite: resolved
```

