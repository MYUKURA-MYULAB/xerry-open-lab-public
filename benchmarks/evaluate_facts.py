#!/usr/bin/env python3
"""Score JSONL fact predictions against synthetic reference cases."""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


FACT_FIELDS = ("subject", "concept", "value", "polarity", "temporality")


def normalize(value):
    return " ".join(value.casefold().split())


def load_jsonl(path):
    rows = {}
    with Path(path).open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except (json.JSONDecodeError, RecursionError) as error:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {error}") from error
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: each JSONL row must be an object")
            case_id = row.get("case_id")
            text = row.get("text")
            facts = row.get("facts")
            if not isinstance(case_id, str) or not case_id:
                raise ValueError(f"{path}:{line_number}: case_id must be a non-empty string")
            if case_id in rows:
                raise ValueError(f"{path}:{line_number}: duplicate case_id {case_id!r}")
            if not isinstance(text, str) or not isinstance(facts, list):
                raise ValueError(f"{path}:{line_number}: text must be a string and facts a list")
            for fact in facts:
                if not isinstance(fact, dict):
                    raise ValueError(f"{path}:{line_number}: each fact must be an object")
                for field in FACT_FIELDS:
                    if not isinstance(fact.get(field), str):
                        raise ValueError(
                            f"{path}:{line_number}: fact field {field!r} must be a string"
                        )
                quote = fact.get("evidence_quote", "")
                if not isinstance(quote, str):
                    raise ValueError(
                        f"{path}:{line_number}: evidence_quote must be a string when present"
                    )
            rows[case_id] = row
    return rows


def signature(fact):
    return tuple(normalize(fact[field]) for field in FACT_FIELDS)


def divide(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def score(references, predictions):
    if references.keys() != predictions.keys():
        missing = sorted(references.keys() - predictions.keys())
        extra = sorted(predictions.keys() - references.keys())
        raise ValueError(f"case_id mismatch; missing predictions={missing}, extra={extra}")

    totals = Counter()
    for case_id, reference in references.items():
        prediction = predictions[case_id]
        if reference["text"] != prediction["text"]:
            raise ValueError(f"text mismatch for case_id {case_id!r}")

        gold = Counter(signature(fact) for fact in reference["facts"])
        predicted = Counter(signature(fact) for fact in prediction["facts"])
        matched = gold & predicted
        totals["true_positive"] += sum(matched.values())
        totals["false_positive"] += sum((predicted - gold).values())
        totals["false_negative"] += sum((gold - predicted).values())

        for fact in prediction["facts"]:
            totals["predictions"] += 1
            quote = fact.get("evidence_quote", "")
            if quote and quote.casefold() in prediction["text"].casefold():
                totals["evidence_quote_occurrences"] += 1

    tp = totals["true_positive"]
    precision = divide(tp, tp + totals["false_positive"])
    recall = divide(tp, tp + totals["false_negative"])
    f1 = divide(2 * precision * recall, precision + recall)
    return {
        **totals,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "evidence_quote_occurrence_rate": divide(
            totals["evidence_quote_occurrences"], totals["predictions"]
        ),
        "interpretation": (
            "Synthetic protocol score only; not a clinical quality or safety measure."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("references", help="reference JSONL file")
    parser.add_argument("predictions", help="prediction JSONL file")
    args = parser.parse_args()
    try:
        result = score(load_jsonl(args.references), load_jsonl(args.predictions))
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
