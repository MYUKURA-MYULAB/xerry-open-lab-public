# Synthetic fact-evaluation utility

This directory contains a small Python standard-library scorer for predictions against fictional reference cases. It is a scoring utility, not an inference demo and not a validated clinical benchmark.

## Reproduce the scorer demonstration

From the repository root, run the tests:

    python3 -m unittest discover -s benchmarks -p 'test_*.py'

Score the included hand-authored example:

    python3 benchmarks/evaluate_facts.py examples/synthetic-data/cases.jsonl examples/synthetic-data/scorer-demo-predictions.jsonl

The example includes omissions, incorrect facts, and one quote that does not occur in the source. It is hand-authored to exercise the scorer. It is not output from a model. Expected totals are 2 true positives, 2 false positives, 3 false negatives, precision 0.5, recall 0.4, F1 about 0.4444, and evidence-quote occurrence 0.75.

The 11 unit tests were run on Python 3.9.6 and 3.14.6 and passed. The scorer performs no inference, so no device or model benchmark is implied.

To score a model run, replace the prediction path with its JSONL output. Record the model revision, prompt, decoding configuration, runtime, and hardware separately.

## JSONL format

Each line in both files is a JSON object with:

- case_id: unique string
- text: source text
- facts: list of fact objects

Each fact object has string fields subject, concept, value, polarity, and temporality. Prediction facts should also include evidence_quote. The normalized five-field fact tuple is matched exactly. Duplicate predicted facts beyond the number of matching reference facts count as false positives.

Reference and prediction files must contain exactly the same case identifiers and source text. Include a case with an empty facts list when there are no predictions for it.

## What the metrics mean

The scorer reports micro exact-tuple precision, recall, and F1. Evidence-quote occurrence is the fraction of predicted quotes that occur as a case-insensitive substring of the source text.

Quote occurrence is not semantic evidence support. The script does not assess whether a quote entails a fact, whether the gold labels are correct, or whether a model is clinically safe. The four examples are not representative data and cannot establish model quality or generalization.

## Dependencies and security

Python 3.9 or newer; no third-party runtime dependencies. The evaluator reads only the paths supplied on the command line, parses JSON, does not execute input content, and emits aggregate metrics rather than source text. It keeps all cases in memory, so use it only with small, trusted local files. Do not pass patient or other private data.
