# Fact scorer

A small Python standard-library scorer for predicted structured facts against fictional reference cases. It scores JSONL files and performs no inference. Its inputs here are hand-authored, so its outputs describe the scorer, not a model.

## Run

From the repository root:

    python3 -m unittest discover -s benchmarks -p 'test_*.py'
    python3 benchmarks/evaluate_facts.py examples/synthetic-data/cases.jsonl examples/synthetic-data/scorer-demo-predictions.jsonl
    python3 benchmarks/evaluate_facts.py examples/synthetic-data-es/cases.jsonl examples/synthetic-data-es/scorer-demo-predictions.jsonl --per-case
    python3 benchmarks/mutation_check.py

Expected results on the hand-authored predictions:

| Set | TP | FP | FN | Precision | Recall | F1 | Quote occurrence |
|---|---|---|---|---|---|---|---|
| `synthetic-data` (English, 4 cases) | 2 | 2 | 3 | 0.5 | 0.4 | 0.4444 | 0.75 |
| `synthetic-data-es` (Spanish, 12 cases) | 14 | 6 | 7 | 0.7 | 0.6667 | 0.6829 | 0.9 |

The 68 tests passed on Python 3.9.6 and 3.14.6. To score a model run, replace the prediction path with its JSONL output and record the model revision, prompt, decoding, runtime and hardware separately.

## Input format

Each line of both files is a JSON object with `case_id` (unique string), `text` (source text) and `facts` (list). Each fact has the string fields `subject`, `concept`, `value`, `polarity`, `temporality`, and, in predictions, `evidence_quote`. Reference and prediction files must contain the same case identifiers and the same source text. Include a case with an empty `facts` list when nothing is predicted.

## How scoring works

- **Normalization.** Fact fields are compared after Unicode NFC normalization, case folding and whitespace collapsing. Accents are significant: `dias` is not `días`, but a precomposed accent equals its combining-accent spelling.
- **Matching.** The five-field tuple must match exactly. Facts are compared as a multiset per case, so a predicted duplicate beyond the reference count is a false positive.
- **Counts.** Precision, recall and F1 are micro-averaged over all cases. A fact with one wrong field counts as one false positive and one false negative.
- **Evidence quotes.** The evidence-quote occurrence rate is the share of predicted facts whose non-empty `evidence_quote` occurs in the source text after the same folding. A missing or empty quote counts as not occurring. Occurrence is not support: the scorer does not judge whether the quote entails the fact.
- **Empty data.** A metric whose denominator is zero is reported as 0.0, which is not the same as "no errors". With no predictions, precision and the quote rate print 0.0. Use `--per-case` to see the denominators. Every count is present in the output even when it is zero. A reference file with no cases is an error, not a score.

## `--per-case`

The flag adds two keys to the default output and leaves the other keys and values unchanged.

- `denominators`: the number of predicted facts (precision and quote rate) and of reference facts (recall).
- `per_case`: for each case, the counts and a list of classified errors.
  - `field_mismatch`: an unmatched predicted fact paired with an unmatched reference fact of the same `concept`, with the differing fields listed.
  - `unsupported_or_extra`: a predicted fact with no reference partner.
  - `omission`: a reference fact with no prediction.
  - `evidence_quotes_not_found`: predicted facts whose quote does not occur, reported apart from fact errors.

The pairing is a diagnostic heuristic and does not alter the counts above. A wrong `concept` code appears as an omission plus an unsupported fact. Values are shown in normalized form.

## Tests, controls and the mutation check

| File | What it covers |
|---|---|
| `test_evaluate_facts.py` | The original 11 tests: scoring, input validation, command line |
| `test_evaluator_extensions.py` | Unicode equivalence, the `--per-case` report, unchanged default output |
| `test_spanish_battery.py` | Expected counts and error classes for the Spanish battery |
| `test_scorer_controls.py` | Controls with known answers: ceiling, negative control, input order, normalization, evidence quotes, empty data, field errors |
| `mutation_check.py` | Injects 11 known defects into a temporary copy of the scorer and reports which test classes catch each one |

Each control class states what it verifies and what it does not. Some tests are marked as characterization: they record behavior that is arguably wrong (for example, a quote that matches part of a word still counts) so that changing it is a deliberate decision. See [research note 004](../research/004-what-validating-a-scorer-shows.md) for what these checks establish and what they leave open.

## What it does not measure

The scorer does not assess whether a label is correct, whether a quote supports a fact, or whether any system is clinically safe. The example sets are fictional protocol fixtures, not representative data; see [research note 001](../research/001-structured-fact-evaluation.md) for what the scorer can and cannot distinguish.

## Dependencies and security

Python 3.9 or newer, no third-party packages. The evaluator reads only the paths given on the command line, parses JSON, does not execute input content, and prints aggregate metrics rather than source text. It keeps all cases in memory, so use it only with small, trusted local files. Do not pass patient or other private data.
