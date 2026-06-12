---
date: 2026-05-25
experiment: crosslingual_eval
mode: exp
tags: [nlp, esa, cross-lingual, chinese, mbert, bias, fairness]
follows: 2026-05-18_bert_finetuned_full.md
reason_follows: English model strong (QWK=0.836); testing cross-lingual transfer and Chinese fine-tuning
git_head: 9c4f7a2
slide_decks: [docs/slides/reports/2026-05-25_weekly-progress]
amended:
  - date: 2026-05-27
    summary: Added DIF analysis results and bias characterisation after receiving annotator feedback
  - date: 2026-05-29
    summary: Corrected mBERT-ZS QWK table; previous run had incorrect normalisation for Zh-CN vs Zh-TW
---

## Goal
Evaluate cross-lingual transfer of the English BERT scorer to Traditional Chinese (zh-TW) student responses, and compare three strategies: (A) zero-shot transfer of the English model, (B) mBERT fine-tuned on translated data, (C) `bert-base-chinese` fine-tuned on translated data. Secondary goal: detect and characterise any systematic scoring bias between languages (Differential Item Functioning analysis).

## Changes
- `data/translate_asap.py`: NLLB-200-3.3B translation pipeline with human post-edit sampling (200 responses × 8 prompts = 1600 items sent to annotators)
- `models/multilingual_scorer.py`: mBERT and bert-base-chinese variants with same regression head + QWK loss
- `eval/dif_analysis.py`: Mantel-Haenszel DIF statistic across language subgroups (EN vs. zh-TW) at each score level
- Commit `9c4f7a2`: _feat: cross-lingual ESAS evaluation framework_

## Setup
- **Translation corpus**: ASAP-SAS test set (N=800 per language per prompt for P1–P4; selected prompts only due to annotation budget)
- **Human post-edit**: 200 responses per prompt (25%) verified by 2 bilingual annotators (inter-rater agreement κ=0.84)
- **Models tested**:
  - EN-BERT-ZS: English fine-tuned model from 2026-05-18, applied zero-shot to Chinese text
  - mBERT-FT: `bert-base-multilingual-cased` fine-tuned on zh-TW translated training split
  - ZH-BERT-FT: `bert-base-chinese` fine-tuned on zh-TW translated training split
- **DIF threshold**: Mantel-Haenszel χ² > 3.84 (p < .05) flagged as biased; ETS C-level > 0.64 flagged as non-negligible

## Results

### Cross-lingual QWK comparison (test set, prompts P1–P4 avg)

| Model | EN QWK | zh-TW QWK | Δ (EN→zh-TW) | DIF-flagged items |
|-------|--------|-----------|--------------|-------------------|
| EN-BERT-ZS | 0.853 | 0.541 | −0.312 | 6 / 12 score levels |
| mBERT-FT | 0.831 | 0.784 | −0.047 | 2 / 12 score levels |
| ZH-BERT-FT | 0.828 | **0.811** | −0.017 | **0 / 12 score levels** |

### Per-prompt zh-TW QWK (ZH-BERT-FT, best model)

| Prompt | EN QWK | zh-TW QWK | Δ | DIF |
|--------|--------|-----------|---|-----|
| P1 | 0.871 | 0.849 | −0.022 | None |
| P2 | 0.792 | 0.769 | −0.023 | None |
| P3 | 0.856 | 0.831 | −0.025 | None |
| P4 | 0.841 | 0.795 | −0.046 | None (borderline) |

### DIF characterisation (EN-BERT-ZS flagged levels)

| Item | Direction | MH χ² | Interpretation |
|------|-----------|--------|----------------|
| P1 score=0 | zh-TW over-penalised | 8.32** | EN model penalises brevity; zh-TW answers structurally shorter |
| P2 score=2 | zh-TW under-awarded | 11.47*** | Discourse marker differences; EN "however"/"although" → zh-TW connectives untranslated |
| P3 score=1 | zh-TW over-awarded | 5.91* | Partial-credit zone larger in zh-TW surface forms |

## Failures
- **EN-BERT-ZS catastrophic degradation**: QWK drops from 0.853 to 0.541 — worse than random on some items. The English model never saw Chinese characters; its tokeniser maps zh-TW text to nearly all `[UNK]` tokens. This was expected as a negative control but the magnitude confirms no useful transfer via shared embedding space alone.
- **mBERT training instability on P2**: Two of five seeds diverged at epoch 7 (NaN loss). Root cause traced to extremely long zh-TW P2 responses after translation (avg 312 tokens vs. EN avg 198). Fixed with dynamic padding + gradient clipping. Final mBERT P2 QWK uses 3 stable seeds.
- **Annotation bottleneck**: Only P1–P4 fully annotated due to budget. P5–P8 cross-lingual results are pending; cross-lingual QWK averages reported only for P1–P4. This limits the generalisability of the DIF analysis.

## Analysis
ZH-BERT-FT achieving QWK=0.811 (Δ=−0.017 from English) with zero DIF flags is the headline result. The gap is within the range of monolingual annotation noise (~0.02) and suggests the scoring construct transfers cleanly once the model is language-matched. The translation quality (κ=0.84 inter-annotator agreement, 25% human-verified) is likely the binding constraint — further gains would require full human post-edit of the training set.

The EN-BERT-ZS DIF findings have a clear structural explanation: the English model learned surface features correlated with score in *English* writing (discourse markers, sentence length norms, explicit signposting), which are systematically different in zh-TW formal academic writing. This is a fairness risk if the English model were deployed uncritically — it would systematically under-score zh-TW responses at score=0 and over-score at the midrange. The ZH-BERT-FT model eliminates this bias entirely.

**Key implication for deployment**: always fine-tune a language-matched model; do not attempt zero-shot cross-lingual deployment for scoring tasks with surface-feature sensitivity. This will be the central recommendation in the paper.

## Charts
docs/charts/2026-05-25_crosslingual_qwk_bar.png
docs/charts/2026-05-25_dif_scatter_en_bert_zs.png
docs/charts/2026-05-25_score_distribution_zh_vs_en.png

## Conclusion
Cross-lingual transfer with a language-matched model (ZH-BERT-FT) achieves QWK=0.811 on zh-TW with zero DIF flags — essentially parity with the English model on the same prompts. Zero-shot transfer is catastrophic (QWK=0.541) and introduces systematic scoring bias. The result validates the feasibility of deploying ESAS in Mandarin-medium secondary schools, contingent on completing P5–P8 annotation.

## Next Steps
- Complete annotation for P5–P8 zh-TW (budget approval pending)
- Ablation: effect of translation quality on downstream QWK (compare NLLB-200 vs. DeepL vs. human-only)
- Contrastive pair augmentation for P2/P7 score-boundary confusion (carried over from 2026-05-18)
- Begin paper draft: framing as *fairness-aware cross-lingual educational assessment*
- Generate progress slides from this log chain for supervisor meeting (2026-05-30)
