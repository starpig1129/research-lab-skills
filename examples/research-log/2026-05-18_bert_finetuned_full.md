---
date: 2026-05-18
experiment: bert_finetuned
mode: exp
tags: [nlp, esa, bert, fine-tuning, qwk, asap-sas]
follows: 2026-05-10_esa_baseline_quick.md
reason_follows: Baseline confirmed fine-tuning is necessary (QWK=0.674); now training supervised model
git_head: f2d8e31
slide_decks: [examples/report-slides/deck.pptx]
amended:
  - date: 2026-05-20
    summary: Added per-prompt QWK breakdown after completing full evaluation run; revised analysis section
---

## Goal
Fine-tune `bert-base-uncased` on the ASAP-SAS training set and validate two hypotheses: (1) per-prompt fine-tuning outperforms cross-prompt, (2) prepending the rubric text as a prefix improves scoring of argumentation-heavy prompts (2, 7) where the baseline struggled.

## Changes
- Implemented `BertScorer` (regression head + custom QWK loss via soft labels) in `models/bert_scorer.py`
- Added rubric prefix injection in `data/asap_dataset.py` — rubric text prepended before `[SEP]` token
- Training loop in `train.py` supports `--per-prompt` flag (8 separate models) vs. default cross-prompt
- Commit `f2d8e31`: _feat: add BertScorer with QWK loss and rubric-prefix conditioning_

## Setup
- **Base model**: `bert-base-uncased` (HuggingFace)
- **Dataset**: ASAP-SAS, official 60/20/20 split; score range normalised to [0, 1] for regression, re-scaled post-prediction
- **Hyperparameters**: LR=2e-5, batch=16, epochs=10, warmup=0.1, weight decay=0.01, max-seq=256
- **Hardware**: 2× A100 40 GB, ~40 min per cross-prompt run, ~8 min per per-prompt model

## Results

### Cross-prompt vs. per-prompt (val QWK, macro-avg)

| Configuration | QWK (val) | QWK (test) | Δ vs. Baseline |
|---------------|-----------|------------|----------------|
| GPT-4 zero-shot (baseline) | 0.674 | 0.671 | — |
| BERT cross-prompt, no rubric | 0.801 | 0.795 | +0.124 |
| BERT cross-prompt + rubric | 0.823 | **0.819** | +0.148 |
| BERT per-prompt + rubric | **0.841** | 0.836 | +0.165 |

### Per-prompt test QWK (best model: per-prompt + rubric)

| Prompt | QWK (test) | Score range | Notes |
|--------|-----------|-------------|-------|
| P1 | 0.871 | 0–3 | Factual science; strong |
| P2 | 0.792 | 0–3 | Argumentation; rubric prefix helped most (+0.09 vs. no-rubric) |
| P3 | 0.856 | 0–2 | Short answer; converged quickly |
| P4 | 0.841 | 0–3 | Mixed; stable |
| P5 | 0.863 | 0–3 | Factual; strong |
| P6 | 0.829 | 0–3 | Explanation; moderate |
| P7 | 0.798 | 0–3 | Argumentation; still weakest |
| P8 | 0.848 | 0–3 | Mixed; good |

## Failures
- **Per-prompt model for P7 diverged twice** before converging: gradient norm spiked at epoch 3 in two of three seeds. Fixed by reducing LR to 1e-5 for P7 only and adding `--clip-grad 1.0`. Final P7 QWK=0.798 is the average of 3 seeds (σ=0.011).
- **Rubric prefix truncation on long prompts**: P4 and P6 rubric + student response exceeded 256 tokens in ~12% of samples. Handled by truncating the student response (not the rubric), but this may explain P6's relatively lower QWK. Re-running with max-seq=384 is scheduled.
- **Score-boundary confusion persists at P2, P7**: model still assigns score=2 to ~9% of true score=0 responses on argumentation prompts. Hypothesis: BERT's pre-training data skews toward assertive, fluent text, making it harder to penalise *absence of argument* vs. *presence of factual error*.

## Analysis
Rubric prefix conditioning is the single highest-value change (+0.022 QWK cross-prompt). This validates the hypothesis that argumentation prompts fail in zero-shot primarily because the model lacks explicit criteria, not because the task is inherently hard. Per-prompt fine-tuning adds another +0.017 on top, likely by specialising the token distribution to prompt-specific vocabulary.

The score-boundary confusion at P2/P7 is a structural problem: the model learns from examples, but the argumentation quality gradient is much sparser in ASAP-SAS's annotation than factual correctness. A future experiment with **contrastive pairs** (score=0 vs. score=1 near-identical responses annotated for the boundary) could address this.

QWK=0.836 on test is a strong result within the monolingual English setting. The key open question is cross-lingual generalisation — the Taiwanese MOE is interested in deploying this for Mandarin-medium secondary schools. Cross-lingual evaluation is the next experiment.

## Charts
docs/charts/2026-05-18_qwk_crossmodel_comparison.png
docs/charts/2026-05-18_per_prompt_qwk_breakdown.png
docs/charts/2026-05-18_score_distribution_shift.png

## Conclusion
`bert-base-uncased` fine-tuned per-prompt with rubric prefix conditioning reaches QWK=0.836, a +16.5pp improvement over the GPT-4 zero-shot baseline. Rubric conditioning is essential for argumentation prompts. Score-boundary confusion at P2/P7 is a known limitation requiring contrastive pair augmentation. The model is ready for cross-lingual extension.

## Next Steps
- Cross-lingual evaluation: translate ASAP-SAS to Traditional Chinese via NLLB-200 + human post-editing (sample 200 per prompt)
- Test zero-shot transfer: apply current English model to Chinese responses (expect significant drop)
- Fine-tune `bert-base-chinese` on translated set; compare with multilingual mBERT baseline
- Investigate score-boundary augmentation strategy for P2/P7
- Extend max-seq to 384 for P4/P6 re-run (see Failures)
