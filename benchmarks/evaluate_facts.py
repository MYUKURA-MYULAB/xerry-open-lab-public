#!/usr/bin/env python3
"""Score JSONL fact predictions against synthetic reference cases."""

import argparse
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path


FACT_FIELDS = ("subject", "concept", "value", "polarity", "temporality")
CONCEPT_INDEX = FACT_FIELDS.index("concept")


def fold(value):
    """Case-fold after Unicode NFC normalization; accents are kept.

    Canonically equivalent spellings (for example a precomposed "á" and "a" plus a
    combining accent) compare equal; "dias" and "días" do not.
    """
    composed = unicodedata.normalize("NFC", value)
    return unicodedata.normalize("NFC", composed.casefold())


def normalize(value):
    return " ".join(fold(value).split())


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


def quote_occurs(fact, text):
    """True when the fact has a non-empty evidence quote found in the source text."""
    quote = fact.get("evidence_quote", "")
    return bool(quote) and fold(quote) in fold(text)


def score(references, predictions):
    if not references:
        raise ValueError(
            "reference file contains no cases; refusing to score an empty benchmark"
        )
    if references.keys() != predictions.keys():
        missing = sorted(references.keys() - predictions.keys())
        extra = sorted(predictions.keys() - references.keys())
        raise ValueError(f"case_id mismatch; missing predictions={missing}, extra={extra}")

    # Every count is present in the output even when it is zero.
    totals = Counter(
        {
            key: 0
            for key in (
                "true_positive",
                "false_positive",
                "false_negative",
                "predictions",
                "evidence_quote_occurrences",
            )
        }
    )
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
            if quote_occurs(fact, prediction["text"]):
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


def fact_fields(signature_tuple):
    return dict(zip(FACT_FIELDS, signature_tuple))


def case_report(case_id, reference, prediction):
    """Counts and classified errors for one case.

    A predicted fact that matches no reference fact is paired with an unmatched
    reference fact of the same concept, if any; the fields in which the two differ
    are reported as one field_mismatch event. Unpaired predictions are
    unsupported_or_extra and unpaired reference facts are omissions. The pairing is
    a diagnostic heuristic: it does not change the precision/recall counts, in which
    a field_mismatch still counts as one false positive and one false negative.
    Field values are shown in their normalized form (case-folded, NFC).
    """
    gold = Counter(signature(fact) for fact in reference["facts"])
    predicted = Counter(signature(fact) for fact in prediction["facts"])
    unmatched_reference = list((gold - predicted).elements())
    unmatched_predicted = list((predicted - gold).elements())

    errors = []
    for predicted_fact in unmatched_predicted:
        partner = next(
            (
                candidate
                for candidate in unmatched_reference
                if candidate[CONCEPT_INDEX] == predicted_fact[CONCEPT_INDEX]
            ),
            None,
        )
        if partner is None:
            errors.append(
                {"type": "unsupported_or_extra", "predicted": fact_fields(predicted_fact)}
            )
            continue
        unmatched_reference.remove(partner)
        errors.append(
            {
                "type": "field_mismatch",
                "fields": [
                    name
                    for name, mine, theirs in zip(FACT_FIELDS, predicted_fact, partner)
                    if mine != theirs
                ],
                "predicted": fact_fields(predicted_fact),
                "reference": fact_fields(partner),
            }
        )
    for reference_fact in unmatched_reference:
        errors.append({"type": "omission", "reference": fact_fields(reference_fact)})

    return {
        "case_id": case_id,
        "reference_facts": sum(gold.values()),
        "predictions": sum(predicted.values()),
        "true_positive": sum((gold & predicted).values()),
        "false_positive": sum((predicted - gold).values()),
        "false_negative": sum((gold - predicted).values()),
        "error_events": len(errors),
        "errors": errors,
        "evidence_quotes_not_found": [
            {"concept": fact["concept"], "quote": fact.get("evidence_quote", "")}
            for fact in prediction["facts"]
            if not quote_occurs(fact, prediction["text"])
        ],
    }


def per_case_report(references, predictions):
    """Per-case reports in reference-file order; inputs must already pass score()."""
    return [
        case_report(case_id, reference, predictions[case_id])
        for case_id, reference in references.items()
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("references", help="reference JSONL file")
    parser.add_argument("predictions", help="prediction JSONL file")
    parser.add_argument(
        "--per-case",
        action="store_true",
        help="also report denominators and, per case, counts and classified errors",
    )
    args = parser.parse_args()
    try:
        references = load_jsonl(args.references)
        predictions = load_jsonl(args.predictions)
        result = score(references, predictions)
        if args.per_case:
            result["denominators"] = {
                "precision": result["true_positive"] + result["false_positive"],
                "recall": result["true_positive"] + result["false_negative"],
                "evidence_quote_occurrence_rate": result["predictions"],
            }
            result["per_case"] = per_case_report(references, predictions)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
