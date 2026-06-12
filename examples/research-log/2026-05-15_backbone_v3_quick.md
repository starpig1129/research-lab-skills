---
date: 2026-05-15
experiment: backbone_v3_quick
mode: exp
tags: [backbone, classification, quick-test]
follows:
reason_follows:
git_head: a3f8d12
slide_decks: []
amended: []
---

## Goal
Test the new backbone_v3 architecture (depthwise-separable convolutions + SE-blocks) on CIFAR-10 to verify it trains stably before committing to a full hyperparameter sweep.

## Analysis
backbone_v3 converged cleanly — no loss spikes, no dead ReLU warnings. Validation accuracy after 30 epochs: **87.4%** (baseline backbone_v2 was 84.1%). Parameter count dropped from 11.2M → 8.7M due to depthwise factorization. Training wall-time stayed the same despite fewer parameters (SE-block attention adds ~4% overhead).

Worth doing a proper LR sweep next to close the gap to SOTA (ResNet-50: 93.2%).

## Next Steps
- Run `finetune_lr_sweep` grid: LR ∈ {1e-3, 3e-4, 1e-4}, scheduler ∈ {cosine, step}
- Track val-accuracy plateau epoch for each combination
- If best run exceeds 91%, proceed to full CIFAR-100 evaluation
