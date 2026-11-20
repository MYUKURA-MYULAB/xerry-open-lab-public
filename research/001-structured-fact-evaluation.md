# 001: What a strict fact scorer can and cannot tell apart

**Type:** protocol-validation note. **Subject of study:** the scorer in [`benchmarks/evaluate_facts.py`](../benchmarks/evaluate_facts.py). **No model was run.** All predictions are hand-authored, and every number below describes the scorer's behavior on those inputs, not the performance of any model.

## Research question

Strict tuple scoring (exact match on subject, concept, value, polarity and temporality) plus a check that each evidence quote occurs in the source is the simplest metric for evidence-grounded extraction. Does it separate the failure types that change what an extracted fact means (omission, polarity, subject, temporality, correction, unsupported evidence), or do aggregate precision and recall hide them?

## Hypotheses

These follow from reading the scorer's definition. The run checks that the implementation behaves as the definition says; it cannot show that the definition is adequate for real model errors.

- **H1.** An omission appears only as a false negative. A fabricated fact appears only as a false positive.
- **H2.** One wrong field (polarity, subject, temporality, value) appears as one false positive plus one false negative. FP + FN therefore overstates the number of mistakes. Recovering error events needs a diagnostic pairing that the aggregate counts lack.
- **H3.** The quote check flags quotes absent from the source but cannot tell whether a present quote supports the fact. A wrong value with a valid quote passes it.
- **H4.** The scorer cannot recognize a correction failure. Reporting the superseded value looks like any other wrong value.
- **H5.** Free-text temporality labels turn a near miss ("yesterday" for "last night") into a full error.

## Experimental setup

- **Scorer:** standard library only. Fact fields are compared after Unicode NFC normalization, case folding and whitespace collapsing. Accents are significant. The quote check is a substring test after the same folding.
- **Data:** the four English cases in [`examples/synthetic-data/`](../examples/synthetic-data/) and the twelve Spanish cases in [`examples/synthetic-data-es/`](../examples/synthetic-data-es/). All are fictional and written by the authors, with reference facts and hand-authored predictions. In each case the prediction is either a control or contains one deliberate error (the Spanish set documents its design in its README).
- **Unit of analysis:** the *error event* reported by `--per-case`. A predicted fact with no exact match is paired with an unmatched reference fact of the same concept, and the differing fields are listed. This pairing is a diagnostic heuristic and does not change the precision and recall counts.
- **Defect found while building the Spanish set:** canonically equivalent accent encodings scored as one false positive plus one false negative. This is fixed and tested ([`test_evaluator_extensions.py`](../benchmarks/test_evaluator_extensions.py)); the historical English results did not change.

## Reproducibility

Python 3.9 or newer, standard library only, no network, deterministic. From the repository root:

    python3 -m unittest discover -s benchmarks -p 'test_*.py'
    python3 benchmarks/evaluate_facts.py examples/synthetic-data/cases.jsonl examples/synthetic-data/scorer-demo-predictions.jsonl --per-case
    python3 benchmarks/evaluate_facts.py examples/synthetic-data-es/cases.jsonl examples/synthetic-data-es/scorer-demo-predictions.jsonl --per-case

All 37 tests passed on Python 3.9.6 and 3.14.6. The expected values of the Spanish set in [`test_spanish_battery.py`](../benchmarks/test_spanish_battery.py) were derived by hand from the case design before the scorer was run on it.

## Observed results

| Set | Cases | Reference facts | Predicted | TP | FP | FN | Precision | Recall | F1 | Quote occurrence | Error events |
|---|---|---|---|---|---|---|---|---|---|---|---|
| English | 4 | 5 | 4 | 2 | 2 | 3 | 0.5 | 0.4 | 0.4444 | 0.75 | 3 |
| Spanish | 12 | 21 | 20 | 14 | 6 | 7 | 0.7 | 0.6667 | 0.6829 | 0.90 | 8 |

The F1 values reflect how many errors the authors planted. They are not model performance and should not be compared with one.

### Case-by-case analysis: the four English cases

| Case and source text | Phenomenon | Reference | Hand-authored prediction | Scorer outcome |
|---|---|---|---|---|
| `synthetic-001`: "I have had a dry cough since yesterday, but no fever." | Omission | cough (dry, since yesterday); fever absent | cough only | 1 TP, 1 FN; `omission` of fever; quote found |
| `synthetic-002`: "The nausea stopped two days ago." | Polarity | nausea **resolved**, two days ago | nausea **present**, two days ago | 1 FP + 1 FN; one `field_mismatch` on `polarity`; quote found |
| `synthetic-003`: "My sibling takes a daily medicine." | Control (subject: sibling) | medication use by sibling | identical | 1 TP |
| `synthetic-004`: "I first said left side, but correction: the pain is on my right side now." | Correction and evidence | pain location **right** side | pain location **left** side; quote absent from the text | 1 FP + 1 FN; one `field_mismatch` on `value`; quote not found |

### Case-by-case analysis: the twelve Spanish cases

Source texts and the designed errors are in the [battery README](../examples/synthetic-data-es/README.md).

| Case | Phenomenon | Scorer classification | TP/FP/FN | Quote check |
|---|---|---|---|---|
| `es-001` | Negation | `omission` (cough) | 2/0/1 | found |
| `es-002` | Negation | `field_mismatch`: polarity (nausea) | 2/1/1 | found |
| `es-003` | Resolved symptom | none (control) | 2/0/0 | found |
| `es-004` | Resolved symptom | `field_mismatch`: temporality (dizziness) | 0/1/1 | found |
| `es-005` | Laterality correction | `field_mismatch`: value (pain location) | 0/1/1 | found |
| `es-006` | Laterality correction | none (control) | 1/0/0 | found |
| `es-007` | Patient/relative | `field_mismatch`: subject (diabetes) | 1/1/1 | found |
| `es-008` | Patient/relative | none (control) | 2/0/0 | found |
| `es-009` | Temporality | none at tuple level | 1/0/0 | **not found** (back_pain) |
| `es-010` | Temporality | `omission` (fever absent today) | 1/0/1 | found |
| `es-011` | Dose | `field_mismatch`: value (ibuprofen_use) | 0/1/1 | found |
| `es-012` | Medication | `unsupported_or_extra` (hypertension) | 2/1/0 | **not found** (hypertension) |

Phenomena exercised by an error, by set:

| Phenomenon | English | Spanish |
|---|---|---|
| Omission | 001 | 001, 010 |
| Polarity | 002 | 002 |
| Subject | none | 007 |
| Temporality | none | 004 |
| Value or dose | none | 011 |
| Correction | 004 | 005 |
| Evidence quote | 004 | 009, 012 |

## Interpretation

- **H1 holds**, trivially: omissions (EN-001, ES-001, ES-010) are false negatives only, and the fabricated hypertension (ES-012) is a false positive only.
- **H2 holds.** The English set contains 3 error events but 5 false counts (2 FP + 3 FN). The Spanish set contains 8 events and 13 false counts. Precision and recall charge one wrong field twice, and the aggregate cannot say whether 13 false counts mean 13 mistakes or 8.
- **H3 holds.** ES-011 reports a wrong dose interval with a quote that occurs verbatim in the text, and the quote check passes it. ES-009 is the reverse: a correct tuple whose quote is not in the text counts as a true positive. The tuple metrics and the quote metric are independent, and neither establishes that the quote supports the fact.
- **H4 holds.** EN-004 and ES-005 are both reported as a `value` mismatch. That they are correction failures is the authors' annotation, not something the scorer detects.
- **H5 holds.** ES-004 ("yesterday" against "last night") costs a full FP and FN.
- **Coverage gap.** The four English cases never exercise a subject error or a temporality error. A scorer validated only on them would not have been tested on two of the six phenomena.
- **Pairing limits.** A wrong concept code is reported as an omission plus an unsupported fact, not as a concept mismatch.

This shows the scorer implements its definition and that its aggregate counts hide the distinctions listed above. It does not show that the definition is valid for the errors real models make.

## Threats to validity

- **Circularity.** The same authors wrote the references, the predictions and the scorer, so planted errors are detected by construction.
- **Size and structure.** There are 16 cases with at most one planted error each, apart from the combined evidence failures in EN-004 and ES-012. Real outputs mix errors.
- **Simplicity of the text.** The sentences are short and single-clause. Real speech has disfluency, overlap and transcription errors.
- **Label vocabulary.** The Spanish battery uses English concept codes and normalized English temporality labels. A system not given this vocabulary would be penalized for naming. Temporality records the time expression, not whether it marks onset or resolution.
- **Annotation.** One annotation pass, with no agreement measure.
- **Accent policy.** Accent-sensitive comparison is a choice. Treating "dias" as "días" would change some outcomes.

## Next experiment (proposed, not executed)

Run one openly licensed compact language model as an external baseline, clearly labeled as not Xerry, on the Spanish battery. Use a fixed prompt that supplies the label vocabulary, deterministic decoding, and three prompt variants. Score each run with `--per-case`, and record the prompt, decoding settings, runtime and raw outputs alongside the predictions.

- **Prediction to test:** if the vocabulary is adequate, errors concentrate in polarity and subject. If they are dominated by omission plus unsupported pairs on the same concept, the label vocabulary rather than extraction is the main source of error.
- **Before scaling the battery to about 100 cases:** have two annotators label them independently and report agreement per field. If agreement on temporality is low, replace exact-string temporality with a controlled vocabulary before scoring anything else.
