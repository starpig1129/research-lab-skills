---
date: 2026-05-10
experiment: esa_baseline
mode: exp
tags: [nlp, esa, gpt-4, baseline, educational-assessment]
follows:
reason_follows:
git_head: b4c1a09
slide_decks: []
amended: []
---

## Goal
Establish a GPT-4 zero-shot baseline for **Automated Short-Answer Scoring (ESAS)** on the Kaggle ASAP-SAS dataset (8 prompts, ~4000 student responses, score range 0–3). This gives us a ceiling reference before any fine-tuning. If GPT-4 zero-shot already hits QWK > 0.80, the case for fine-tuning weakens.

## Analysis
GPT-4 zero-shot lands at QWK = **0.674** (macro-avg across 8 prompts, range 0.58–0.76). Well below the supervised SOTA (~0.85), but stronger than naive majority-class baseline (QWK = 0.00). Key observations:
- Prompts 1, 3, 5 score above 0.70 — these have concrete factual anchors the model can latch onto.
- Prompts 2, 7 score below 0.62 — these require scoring *argumentation structure*, which zero-shot GPT-4 consistently conflates with content accuracy.
- Score-distribution bias: GPT-4 overestimates mid-range (score=2) by ~18%, underestimates low-end (score=0). Suggests the model is reluctant to assign the minimum score without explicit rubric grounding.

Fine-tuning hypothesis: a model with explicit rubric conditioning on the ASAP-SAS training split should close most of the 0.674 → 0.85 gap. Starting with `bert-base-uncased` + regression head.

## Next Steps
- Fine-tune `bert-base-uncased` on ASAP-SAS train split (prompts 1–8 combined), regression head, QWK loss
- Ablate: (a) per-prompt fine-tuning vs. cross-prompt, (b) rubric text as auxiliary input
- Target: QWK ≥ 0.82 on held-out val set before considering cross-lingual extension
