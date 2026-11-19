"""Controls for the fact scorer: what each group of tests verifies and what it does not.

Every control uses known inputs with a known correct outcome. None runs a model, and
none says anything about whether the reference labels or a model's output are right.
Each class states the property it verifies and the property it leaves unchecked. Some
tests record current behavior that is arguably undesirable (marked "characterization");
they exist so that changing the behavior is a visible decision.
"""

import copy
import itertools
import json
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path

import evaluate_facts
from evaluate_facts import load_jsonl, score


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "benchmarks" / "evaluate_facts.py"
SETS = {
    "english": (
        ROOT / "examples" / "synthetic-data" / "cases.jsonl",
        ROOT / "examples" / "synthetic-data" / "scorer-demo-predictions.jsonl",
    ),
    "spanish": (
        ROOT / "examples" / "synthetic-data-es" / "cases.jsonl",
        ROOT / "examples" / "synthetic-data-es" / "scorer-demo-predictions.jsonl",
    ),
}
FIELDS = ("subject", "concept", "value", "polarity", "temporality")


def fact(subject="patient", concept="back_pain", value="", polarity="present",
         temporality="current", quote="dolor de espalda"):
    return {
        "subject": subject, "concept": concept, "value": value,
        "polarity": polarity, "temporality": temporality, "evidence_quote": quote,
    }


TEXT = "Tengo dolor de espalda desde hace tres semanas"


def one_case(reference_facts, prediction_facts, text=TEXT):
    return (
        {"c": {"case_id": "c", "text": text, "facts": reference_facts}},
        {"c": {"case_id": "c", "text": text, "facts": prediction_facts}},
    )


def counts(result):
    return (result["true_positive"], result["false_positive"], result["false_negative"])


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, args)],
        check=False, capture_output=True, text=True, encoding="utf-8",
    )


class CeilingControlTests(unittest.TestCase):
    """Verifies: a prediction identical to the reference scores 1.0 on every metric.
    Does not verify: that the reference labels are correct."""

    def test_reference_as_prediction_is_perfect_in_both_languages(self):
        for name, (reference_path, _) in SETS.items():
            with self.subTest(set=name):
                references = load_jsonl(reference_path)
                result = score(references, references)
                self.assertEqual(
                    (result["precision"], result["recall"], result["f1"],
                     result["evidence_quote_occurrence_rate"]),
                    (1.0, 1.0, 1.0, 1.0),
                )


class NegativeControlTests(unittest.TestCase):
    """Verifies: facts that belong to other cases earn nothing, and every one is
    charged as a false positive and a false negative.
    Does not verify: that evidence quotes from another case are rejected. Short
    quotes can occur in an unrelated text by coincidence (for example "pero yo no"),
    so no quote-rate bound is asserted."""

    @staticmethod
    def rotated(references):
        ids = list(references)
        return {
            case_id: {
                **references[case_id],
                "facts": copy.deepcopy(references[ids[(i + 1) % len(ids)]]["facts"]),
            }
            for i, case_id in enumerate(ids)
        }

    def test_facts_from_the_next_case_score_zero(self):
        for name, (reference_path, _) in SETS.items():
            with self.subTest(set=name):
                references = load_jsonl(reference_path)
                total = sum(len(r["facts"]) for r in references.values())
                result = score(references, self.rotated(references))
                self.assertEqual(counts(result), (0, total, total))
                self.assertEqual((result["precision"], result["recall"], result["f1"]),
                                 (0.0, 0.0, 0.0))


class OrderInvarianceTests(unittest.TestCase):
    """Verifies: totals do not depend on fact order, case order, or line order in the
    prediction file; counts do not depend on fact order within a case.
    Does not verify: that the labels given to errors by --per-case are order
    independent. When several unmatched facts share a concept, the pairing is
    first-come and the labels may change with order; only the counts are guaranteed."""

    def test_reversing_facts_inside_cases_changes_nothing(self):
        for name, (reference_path, prediction_path) in SETS.items():
            with self.subTest(set=name):
                references = load_jsonl(reference_path)
                predictions = load_jsonl(prediction_path)
                reversed_facts = {
                    c: {**row, "facts": list(reversed(row["facts"]))}
                    for c, row in predictions.items()
                }
                self.assertEqual(score(references, reversed_facts),
                                 score(references, predictions))

    def test_reordering_cases_changes_nothing(self):
        for name, (reference_path, prediction_path) in SETS.items():
            with self.subTest(set=name):
                references = load_jsonl(reference_path)
                predictions = load_jsonl(prediction_path)
                shuffled = dict(reversed(list(predictions.items())))
                self.assertEqual(score(references, shuffled), score(references, predictions))

    def test_reversing_the_lines_of_the_prediction_file_changes_nothing(self):
        for name, (reference_path, prediction_path) in SETS.items():
            with self.subTest(set=name), tempfile.TemporaryDirectory() as folder:
                lines = prediction_path.read_text(encoding="utf-8").splitlines()
                flipped = Path(folder) / "flipped.jsonl"
                flipped.write_text("\n".join(reversed(lines)) + "\n", encoding="utf-8")
                self.assertEqual(
                    score(load_jsonl(reference_path), load_jsonl(flipped)),
                    score(load_jsonl(reference_path), load_jsonl(prediction_path)),
                )

    def test_counts_are_the_same_for_every_permutation_of_predicted_facts(self):
        gold = [
            fact(concept="fever", value="high", temporality="yesterday"),
            fact(concept="fever", polarity="absent", temporality="today"),
            fact(concept="fever", polarity="absent", temporality="last week"),
        ]
        predicted = [
            fact(concept="fever", value="high", temporality="yesterday"),
            fact(concept="fever", polarity="present", temporality="today"),
            fact(concept="fever", polarity="absent", temporality="two days ago"),
        ]
        seen = set()
        for permutation in itertools.permutations(predicted):
            references, predictions = one_case(gold, list(permutation))
            seen.add(counts(score(references, predictions)))
        self.assertEqual(seen, {(1, 2, 2)})


class NormalizationTests(unittest.TestCase):
    """Verifies: which spelling differences in a fact field are ignored (case,
    surrounding or repeated whitespace, Unicode composition) and which are not.
    Does not verify: that the strict choices are desirable. Accents, punctuation,
    inflection and synonyms all count as different facts (characterization)."""

    def match_count(self, reference_value, predicted_value):
        references, predictions = one_case(
            [fact(value=reference_value)], [fact(value=predicted_value)]
        )
        return score(references, predictions)["true_positive"]

    def test_equivalent_spellings_are_accepted(self):
        reference = "dolor lumbar"
        for label, variant in {
            "upper case": "DOLOR LUMBAR",
            "surrounding spaces": "  dolor lumbar  ",
            "repeated spaces and tabs": "dolor \t  lumbar",
            "newline": "dolor\nlumbar",
        }.items():
            with self.subTest(variant=label):
                self.assertEqual(self.match_count(reference, variant), 1)

    def test_composed_and_decomposed_accents_are_the_same(self):
        composed = "náusea intensa"
        self.assertEqual(self.match_count(composed, unicodedata.normalize("NFD", composed)), 1)

    def test_whitespace_only_value_equals_empty_value(self):
        self.assertEqual(self.match_count("", "   "), 1)

    def test_different_spellings_are_rejected(self):
        for label, (reference, predicted) in {
            "missing accent": ("náusea", "nausea"),
            "trailing period": ("dolor lumbar", "dolor lumbar."),
            "plural": ("dolor", "dolores"),
            "translation": ("tos seca", "dry cough"),
        }.items():
            with self.subTest(variant=label):
                self.assertEqual(self.match_count(reference, predicted), 0)


class QuoteCheckTests(unittest.TestCase):
    """Verifies: when an evidence quote is counted as occurring in the source text.
    Does not verify: that the quote supports the fact. A valid quote attached to a
    wrong fact, or to a fact it does not mention, still counts (characterization)."""

    def quote_found(self, quote, text=TEXT, include_key=True):
        predicted = fact(quote=quote)
        if not include_key:
            del predicted["evidence_quote"]
        references, predictions = one_case([fact()], [predicted], text)
        return score(references, predictions)["evidence_quote_occurrences"] == 1

    def test_accepted_quotes(self):
        for label, quote in {
            "exact": "dolor de espalda",
            "different case": "DOLOR DE ESPALDA",
            "whole text": TEXT,
        }.items():
            with self.subTest(quote=label):
                self.assertTrue(self.quote_found(quote))

    def test_decomposed_accent_in_the_quote_is_accepted(self):
        quote = unicodedata.normalize("NFD", "náuseas desde")
        self.assertNotEqual(quote, "náuseas desde")
        self.assertTrue(self.quote_found(quote, text="Tengo náuseas desde ayer"))

    def test_rejected_quotes(self):
        for label, quote in {
            "invented": "dolor lumbar cronico",
            "one word changed": "dolor de cintura",
            "added trailing period": "dolor de espalda.",
            "empty": "",
        }.items():
            with self.subTest(quote=label):
                self.assertFalse(self.quote_found(quote))

    def test_missing_quote_field_is_rejected(self):
        self.assertFalse(self.quote_found("", include_key=False))

    def test_characterization_partial_word_matches_count(self):
        self.assertTrue(self.quote_found("dolor de esp"))

    def test_characterization_whitespace_in_the_source_is_not_collapsed(self):
        self.assertFalse(self.quote_found("dolor de espalda", text="Tengo dolor  de espalda"))

    def test_characterization_a_quote_unrelated_to_the_fact_still_counts(self):
        self.assertTrue(self.quote_found("tres semanas"))


class EmptyInputTests(unittest.TestCase):
    """Verifies: how empty inputs are scored and that an empty benchmark is refused.
    Does not verify: any convention for undefined metrics beyond the documented one.
    A metric with a zero denominator is reported as 0.0, which does not mean "no
    errors"; the denominators printed by --per-case are the way to tell."""

    def test_cases_without_facts_on_both_sides_score_zero_without_error(self):
        references, predictions = one_case([], [])
        result = score(references, predictions)
        self.assertEqual(counts(result), (0, 0, 0))
        self.assertEqual(
            (result["precision"], result["recall"], result["f1"],
             result["evidence_quote_occurrence_rate"]),
            (0.0, 0.0, 0.0, 0.0),
        )
        report = evaluate_facts.per_case_report(references, predictions)[0]
        self.assertEqual((report["error_events"], report["errors"]), (0, []))

    def test_predictions_for_a_case_without_reference_facts_are_all_false_positives(self):
        references, predictions = one_case([], [fact(), fact(concept="fever")])
        result = score(references, predictions)
        self.assertEqual(counts(result), (0, 2, 0))
        self.assertEqual(result["recall"], 0.0)
        report = evaluate_facts.per_case_report(references, predictions)[0]
        self.assertEqual([e["type"] for e in report["errors"]],
                         ["unsupported_or_extra", "unsupported_or_extra"])

    def test_output_has_the_same_keys_when_every_count_is_zero(self):
        references, predictions = one_case([fact()], [])
        self.assertEqual(
            set(score(references, predictions)),
            {"true_positive", "false_positive", "false_negative", "predictions",
             "evidence_quote_occurrences", "precision", "recall", "f1",
             "evidence_quote_occurrence_rate", "interpretation"},
        )

    def test_cli_per_case_works_when_nothing_is_predicted(self):
        reference_path, _ = SETS["english"]
        with tempfile.TemporaryDirectory() as folder:
            emptied = Path(folder) / "none.jsonl"
            rows = [json.loads(line) for line in reference_path.read_text(encoding="utf-8").splitlines()]
            emptied.write_text(
                "".join(json.dumps({**row, "facts": []}) + "\n" for row in rows),
                encoding="utf-8",
            )
            completed = run_cli(reference_path, emptied, "--per-case")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["denominators"], {"precision": 0, "recall": 5,
                                                  "evidence_quote_occurrence_rate": 0})
        self.assertEqual((result["false_negative"], result["predictions"]), (5, 0))

    def test_empty_reference_set_is_refused(self):
        with self.assertRaisesRegex(ValueError, "no cases"):
            score({}, {})

    def test_cli_refuses_an_empty_reference_file(self):
        with tempfile.TemporaryDirectory() as folder:
            empty = Path(folder) / "empty.jsonl"
            empty.write_text("\n\n", encoding="utf-8")
            completed = run_cli(empty, empty)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("no cases", completed.stderr)
        self.assertEqual(completed.stdout, "")

    def test_blank_lines_between_rows_are_ignored(self):
        reference_path, _ = SETS["english"]
        with tempfile.TemporaryDirectory() as folder:
            spaced = Path(folder) / "spaced.jsonl"
            body = reference_path.read_text(encoding="utf-8").replace("\n", "\n\n")
            spaced.write_text(body, encoding="utf-8")
            self.assertEqual(load_jsonl(spaced), load_jsonl(reference_path))

    def test_cli_reports_a_missing_prediction_file(self):
        reference_path, _ = SETS["english"]
        completed = run_cli(reference_path, "does-not-exist.jsonl")
        self.assertEqual(completed.returncode, 2)
        self.assertTrue(completed.stderr.startswith("error:"))


class FieldErrorTests(unittest.TestCase):
    """Verifies: an error in exactly one field is charged as one false positive plus
    one false negative and reported as one event naming that field; a wrong concept is
    reported as an omission plus an unsupported fact; duplicates are counted.
    Does not verify: that these charges are the right way to weigh the errors."""

    def test_each_single_field_error(self):
        wrong = {"subject": "mother", "value": "severe", "polarity": "absent",
                 "temporality": "yesterday"}
        for field, replacement in wrong.items():
            with self.subTest(field=field):
                references, predictions = one_case([fact()], [fact(**{field: replacement})])
                self.assertEqual(counts(score(references, predictions)), (0, 1, 1))
                report = evaluate_facts.per_case_report(references, predictions)[0]
                self.assertEqual(report["error_events"], 1)
                self.assertEqual(report["errors"][0]["type"], "field_mismatch")
                self.assertEqual(report["errors"][0]["fields"], [field])

    def test_wrong_concept_is_an_omission_plus_an_unsupported_fact(self):
        references, predictions = one_case([fact()], [fact(concept="neck_pain")])
        self.assertEqual(counts(score(references, predictions)), (0, 1, 1))
        report = evaluate_facts.per_case_report(references, predictions)[0]
        self.assertEqual(sorted(e["type"] for e in report["errors"]),
                         ["omission", "unsupported_or_extra"])

    def test_two_wrong_fields_are_one_event(self):
        references, predictions = one_case(
            [fact()], [fact(polarity="absent", temporality="yesterday")]
        )
        self.assertEqual(counts(score(references, predictions)), (0, 1, 1))
        report = evaluate_facts.per_case_report(references, predictions)[0]
        self.assertEqual(report["error_events"], 1)
        self.assertEqual(report["errors"][0]["fields"], ["polarity", "temporality"])

    def test_a_repeated_prediction_is_a_false_positive(self):
        references, predictions = one_case([fact()], [fact(), fact()])
        self.assertEqual(counts(score(references, predictions)), (1, 1, 0))

    def test_a_repeated_reference_fact_needs_a_repeated_prediction(self):
        references, predictions = one_case([fact(), fact()], [fact()])
        self.assertEqual(counts(score(references, predictions)), (1, 0, 1))

    def test_a_wrong_quote_does_not_change_the_fact_counts(self):
        references, predictions = one_case([fact()], [fact(quote="texto inventado")])
        result = score(references, predictions)
        self.assertEqual(counts(result), (1, 0, 0))
        self.assertEqual(result["evidence_quote_occurrences"], 0)


if __name__ == "__main__":
    unittest.main()
