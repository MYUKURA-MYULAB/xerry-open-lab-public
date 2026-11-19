# Xerry Open Lab

Xerry Open Lab is a research workspace on compact, task-specific models for speech-to-document pipelines, centered on evidence-grounded fact extraction. This repository publishes what can be inspected and rerun today: a strict fact scorer, two fictional benchmark sets (English and Spanish), a protocol-validation note, and one negative result from an internal experiment. It contains no model, tokenizer, training data or inference runner.

## 1. The scientific problem

In a pipeline from audio to a clinical-style document, a wrong output can come from transcription, speaker attribution, extraction or drafting, and the errors do not weigh the same. Omitting a fact, inverting its polarity ("no fever" becomes "fever"), attributing a relative's condition to the patient, shifting its time, or keeping a value the speaker had just corrected each change what the document says. Aggregate scores hide which of these happened.

We study how to evaluate evidence-grounded extraction so that these error types stay separable, starting with Spanish clinical-style text, and whether small task-specific models on local hardware can meet that bar under data-governance constraints.

## 2. Working hypotheses

| # | Hypothesis | Evidence available here | Pending test |
|---|---|---|---|
| 1 | A strict tuple scorer with an evidence-quote check separates omissions, field errors, unsupported facts and evidence failures. | [Note 001](research/001-structured-fact-evaluation.md): holds on 16 hand-authored cases, by construction, and shows where it fails. | Score real model output; two-annotator agreement. |
| 2 | A compact task-specific extractor can reach useful quality on a restricted fact schema. | One internal run accepted no facts ([note 002](research/002-compact-extractor-negative-result.md)). No metrics. | External baseline on the Spanish battery, then a locked test set. |
| 3 | A downstream check that rejects unsupported facts makes extraction fail closed. | Observed once in that run; no reproducible implementation. | Public implementation tested on the battery. |
| 4 | Splitting the pipeline into stages makes errors easier to attribute than an end-to-end system. | None. | Same inputs through staged and end-to-end systems. |
| 5 | Local execution can meet data-control constraints at acceptable quality and cost. | The internal run executed on a phone; no latency or memory claim. | Benchmark on a fixed device and runtime. |

## 3. The experiment available here

The experiment that can be rerun validates the metric, not a model. It asks whether the scorer distinguishes the error types above, using sixteen fictional cases (four English, twelve Spanish) whose predictions were written by hand with planted errors. The architecture page marks every component as implemented, executed internally, or proposed: [docs/architecture.md](docs/architecture.md).

## 4. Reproduce

Python 3.9 or newer; standard library only; no network, models or accelerator. From the repository root:

    python3 -m unittest discover -s benchmarks -p 'test_*.py'
    python3 benchmarks/evaluate_facts.py examples/synthetic-data/cases.jsonl examples/synthetic-data/scorer-demo-predictions.jsonl --per-case
    python3 benchmarks/evaluate_facts.py examples/synthetic-data-es/cases.jsonl examples/synthetic-data-es/scorer-demo-predictions.jsonl --per-case

The 37 tests pass on Python 3.9.6 and 3.14.6. The scoring rules and output fields are in the [benchmark guide](benchmarks/README.md), and the evaluation protocol in [docs/evaluation-methodology.md](docs/evaluation-methodology.md).

## 5. What we observed

| Set | Cases | Reference facts | TP | FP | FN | Precision | Recall | F1 | Quote occurrence | Error events |
|---|---|---|---|---|---|---|---|---|---|---|
| English | 4 | 5 | 2 | 2 | 3 | 0.5 | 0.4 | 0.4444 | 0.75 | 3 |
| Spanish | 12 | 21 | 14 | 6 | 7 | 0.7 | 0.6667 | 0.6829 | 0.90 | 8 |

These are scorer outputs on hand-authored predictions. They measure no model.

- One wrong field costs one false positive and one false negative, so the 8 error events in the Spanish set appear as 13 false counts.
- The quote check passes a wrong dose whose quote occurs verbatim (`es-011`), and a correct fact with an absent quote still counts as a true positive (`es-009`).
- The scorer cannot recognize a correction failure or a near-miss time; both look like an ordinary value or temporality error.
- The four English cases never exercise a subject or temporality error. The Spanish set does.
- Building the Spanish set exposed a defect: canonically equivalent accent encodings scored as an error. It is fixed and tested.
- Negative result: in five short internal tests the compact extractor produced three unsupported candidates and two outputs with no claim; the evidence check rejected the three candidates in that run ([note 002](research/002-compact-extractor-negative-result.md)).

## 6. What we cannot conclude

- Nothing here measures a model. The F1 values (0.44 English, 0.68 Spanish) reflect how many errors the authors planted.
- The internal run supports no accuracy claim in either direction, its cause is not isolated, and independently reproducible task-performance metrics are not yet available for this experimental model.
- Sixteen short fictional cases, one annotation pass, and the same authors for references, predictions and scorer make the validation circular. Real speech adds disfluency, overlap and transcription errors that these cases do not.
- Nothing here addresses speech recognition, speaker attribution, an encoder comparison, document generation, or clinical validity. Do not submit patient data or identifiable audio to anything in this repository.
- Local execution can reduce some data transfers. Privacy, security and compliance depend on the whole deployment.

## 7. Next research lines

All of these are proposed; none is implemented here.

1. **External baseline.** An openly licensed compact model, labeled as not Xerry, on the Spanish battery with fixed prompts and decoding, scored per phenomenon ([note 001](research/001-structured-fact-evaluation.md#next-experiment-proposed-not-executed)).
2. **Controlled diagnosis of the internal extractor,** varying model, prompt and decoding, tokenizer and export one at a time ([note 002](research/002-compact-extractor-negative-result.md#next-diagnostic-proposed-not-executed)).
3. **A larger battery** of about 100 cases with two annotators and per-field agreement.
4. **Open questions:** a specialized ASR stage, an encoder against a generator for extraction, document generation from accepted facts only, and end-to-end traceability.

## Repository map

| Path | Content |
|---|---|
| `research/` | Note 001 (scorer validation) and note 002 (negative result) |
| `benchmarks/` | Fact scorer, its tests and the [benchmark guide](benchmarks/README.md) |
| `examples/synthetic-data/` | Four English fictional cases and hand-authored predictions |
| `examples/synthetic-data-es/` | Twelve Spanish fictional cases and hand-authored predictions |
| `docs/` | [Architecture](docs/architecture.md) and [evaluation methodology](docs/evaluation-methodology.md) |
| `models/model-cards/` | A bounded card for one experimental model; no model files |
| `LICENSE`, `NOTICE` | Apache License 2.0 and attribution notice |

## License

Copyright 2026 MYULAB INNOVATION, S.L.

The source code, documentation, and synthetic examples in this repository are licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for the full text and [NOTICE](NOTICE) for the attribution notice.

The license covers only the files published in this repository. This repository does not contain, and the license does not grant rights in, model weights, checkpoints, tokenizers, adapters, datasets, or any other artifact described in the model card. Section 6 of the license does not grant permission to use names or marks except as needed to describe the origin of the work.
