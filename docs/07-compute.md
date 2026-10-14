# HF PRO, Kaggle and reproducibility

## Mandatory preflight

Check account identity, model access, real GPU quota, disk/RAM, GPU/VRAM/CUDA, internet access and available secrets. Print only variable names and present/absent status. Do not assume a subscription is authenticated on this machine.

Do not use fixed figures for credits or hours. HF PRO is not equal to free dedicated inference endpoints (S07). Kaggle assigns resources subject to availability; do not promise two GPUs or uninterrupted execution.

## Distribution

- Local CPU: case generation, contracts, transforms, scorer, reports and Space with saved results.
- Kaggle GPU: sequential synthesis and baselines, one model at a time, initial batch 1.
- HF Dataset: versioned distribution; HF Space CPU: audio and error exploration.
- ZeroGPU: optional interactive extension, never a dependency to reproduce the published result.

If Voxtral does not fit: measure peak, lower batch and use documented offload; treat quantization as a distinct system with explicit configuration. Do not silently switch models. If it stays blocked, leave the system pending, keep results for the available one and do not declare a two-model comparison completed.

## Required notebooks

generate: install pinned environment, load templates, verify rights, generate batches, save QA/provenance and per-clip checkpoint.
evaluate: receive frozen audio, download weights by SHA, transcribe per model and save predictions; gold is only mounted in a separate scoring stage.
reproduce: CPU and offline with the prepared bundle; verify hashes and regenerate all tables from included predictions.

Source code in importable scripts and thin notebook; avoid duplicated logic in cells. Kaggle input dataset private during preparation, public only when rights/release gates pass. Every output must survive restart from the versioned bundle, not ephemeral disk.

## Dependencies and artifacts

Resolve versions from official docs and verify installation; create per-profile locks core/tts/asr1/asr2/space. Record Python, torch, CUDA, hardware and precision. Do not use latest/main in release runs.

Bundle: manifests, gold, inputs, licenses, checksums, scripts/notebooks, locks, full predictions, report and dataset card. Weights are not redistributed by default; point to pinned official downloads. Human data as IDs/recipe or audio with attribution per rights.

## Accounts and spend

Use HF_TOKEN with minimal permissions and Kaggle Secrets for jobs. Never store kaggle.json or tokens in notebooks/outputs. Do not launch paid jobs or self-extend quota by default. Set max_paid_spend=0; the implementer can complete the core with available compute and prepare disabled paid adapters.

Missing auth or resources: document the exact diagnosis, prepared commands and next step; continue independent local work. Never request keys via chat nor infer credit from other accounts.

## Reproduction levels

Level 1 mandatory: identical offline scoring from frozen predictions on CPU.
Level 2 mandatory: fresh inference with same weights/config, accepting documented GPU differences.
Level 3 informational: re-synthesis from recipe, without promising byte equality.

Kaggle latency figures only describe that environment, not user-call performance.
