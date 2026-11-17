# Evaluation methodology

## Evaluation units

Measure each stage separately and then measure the full pipeline. A result from one stage must not be presented as an end-to-end result.

- Speech recognition: word error rate, with language, normalization policy, segmentation, and audio provenance reported.
- Speaker attribution: diarization error rate and its collar/overlap policy, with speaker count and recording conditions reported.
- Structured extraction: precision, recall, and F1 for facts, plus separate error rates for polarity, subject, temporal status, corrections, and unsupported claims.
- Evidence grounding: whether the quoted span occurs in the source and whether it supports the predicted fact under a published annotation policy.
- Document drafting: factual support, omissions, contradictions, and human correction burden. Fluency alone is not a quality measure.
- Runtime: cold and warm latency, peak and steady-state memory, energy if available, device and software versions, and concurrency.

## Protocol requirements

Every reported run should record:

1. Immutable model and tokenizer identifiers or hashes.
2. Dataset version, license, source provenance, split definition, and leakage checks.
3. Prompt, decoding, preprocessing, quantization, and runtime configuration.
4. Hardware, operating system, framework, and measurement method.
5. Per-case predictions or a privacy-safe reproducibility package.
6. Metrics with denominators, uncertainty where appropriate, and failure categories.
7. Whether the run was training, validation, held-out testing, or a smoke test.

Do not use training or validation loss as a substitute for task metrics. Do not choose a checkpoint on a held-out test set and then report that set as an unbiased final evaluation.

## Synthetic benchmark in this repository

The included cases are fictional protocol examples, not a representative clinical dataset. A hand-authored prediction file is included to exercise the scorer; it is not model output. The scorer reports strict fact precision, recall, F1, and whether predicted evidence quotes occur in the input text. It does not judge whether a label is clinically correct or whether a quote semantically supports the fact.

A serious evaluation needs expert-reviewed annotation guidance, independently reviewed cases, representative languages and conditions, and a separate locked test set. It should report errors that could change subject, negation, time, dose, or certainty.

## Comparisons

Compare encoder and generative systems on the same examples, gold labels, hardware, and preprocessing. Report model-specific context limits and tuning budget. Measure quality and runtime together; do not generalize one device or quantization result to another.
