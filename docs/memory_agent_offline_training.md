# Memory-Agent Offline Training

This pipeline trains a memory-conditioned mini-SWE-agent action policy from
saved rollouts. It is offline reward-weighted training, not online PPO/GRPO.

## 1. Collect rollouts

```powershell
.\.venv\Scripts\python.exe scripts\run_agent_rl_rollouts.py `
  --out-dir runs\agent-rl-rollouts-v1 `
  --initial-memory runs\memory\self_improve_memory.json `
  --subset lite `
  --split dev `
  --rollouts-per-instance 4 `
  --memory-k 2 `
  --memory-strategy hybrid `
  --memory-stage-aware `
  --workers 1 `
  --eval-max-workers 1
```

## 2. Build Parquet data

Reward-weighted data keeps failed records:

```powershell
.\.venv\Scripts\python.exe scripts\build_verl_agent_rl_data.py `
  --input runs\agent-rl-rollouts-v1\agent_rl_rollouts.jsonl `
  --output runs\agent-rl-rollouts-v1\verl `
  --output-format parquet `
  --val-ratio 0.05 `
  --seed 1
```

SFT warmup data keeps only successful or high-reward records:

```powershell
.\.venv\Scripts\python.exe scripts\build_verl_agent_rl_data.py `
  --input runs\agent-rl-rollouts-v1\agent_rl_rollouts.jsonl `
  --output runs\agent-rl-rollouts-v1\verl_sft_success `
  --output-format parquet `
  --min-reward 0.8 `
  --only-success `
  --val-ratio 0.05 `
  --seed 1
```

Hybrid-Gym-style auxiliary locate/edit/test data:

```powershell
.\.venv\Scripts\python.exe scripts\build_memory_skill_data.py `
  --input runs\agent-rl-rollouts-v1\agent_rl_rollouts.jsonl `
  --output runs\agent-rl-rollouts-v1\memory_skills `
  --format parquet `
  --val-ratio 0.05 `
  --seed 1
```

Optional 70/20/10 mixed data:

```powershell
.\.venv\Scripts\python.exe scripts\mix_agent_rl_data.py `
  --agent-train runs\agent-rl-rollouts-v1\verl\train.parquet `
  --agent-val runs\agent-rl-rollouts-v1\verl\val.parquet `
  --skills-train runs\agent-rl-rollouts-v1\memory_skills\train.parquet `
  --skills-val runs\agent-rl-rollouts-v1\memory_skills\val.parquet `
  --output runs\agent-rl-rollouts-v1\verl_mixed `
  --agent-ratio 0.70 `
  --skill-ratio 0.20 `
  --failed-ratio 0.10 `
  --seed 1
```

## 3. Train LoRA with verl

Run from `C:\Users\zrz20\Desktop\vscode\multi-rl\PettingLLMs-main\verl`.
Use `verl_sft_success` for warmup, `verl` for reward-weighted training, or
`verl_mixed` for the auxiliary skill mix.

```powershell
torchrun --standalone --nnodes=1 --nproc_per_node=1 -m verl.trainer.fsdp_sft_trainer `
  data.train_files="C:/Users/zrz20/Desktop/vscode/multi-rl/创智大作业/mini-swe-agent/runs/agent-rl-rollouts-v1/verl_mixed/train.parquet" `
  data.val_files="C:/Users/zrz20/Desktop/vscode/multi-rl/创智大作业/mini-swe-agent/runs/agent-rl-rollouts-v1/verl_mixed/val.parquet" `
  data.custom_cls.path="verl/utils/dataset/agent_rl_dataset.py" `
  data.custom_cls.name=AgentRLDataset `
  data.max_length=8192 `
  data.truncation=left `
  data.train_batch_size=32 `
  data.micro_batch_size_per_gpu=1 `
  model.partial_pretrain=Qwen/Qwen3-4B `
  model.trust_remote_code=true `
  model.lora_rank=32 `
  model.lora_alpha=64 `
  model.target_modules=all-linear `
  optim.lr=1e-5 `
  trainer.total_epochs=2 `
  trainer.project_name=memory-agent-rl `
  trainer.experiment_name=agent-rwr-v1 `
  trainer.default_local_dir="C:/Users/zrz20/Desktop/vscode/multi-rl/创智大作业/mini-swe-agent/runs/checkpoints/memory-agent-rwr-v1" `
  trainer.logger='["console"]'
```

## 4. Evaluate

```powershell
.\.venv\Scripts\python.exe scripts\run_memory_gate_ablation.py `
  --out-root runs\memory-agent-rwr-v1-eval `
  --initial-memory runs\memory\self_improve_memory.json `
  --initial-strategy-memory runs\strategy\strategy_r0.json `
  --subset lite `
  --split dev `
  --batch-size 5 `
  --limit 30 `
  --model openai/local-memory-agent-rwr-v1 `
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
