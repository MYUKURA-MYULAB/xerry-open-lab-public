"""Tests for evaluator behaviour added after the first release.

They cover Unicode canonical equivalence (relevant for Spanish text), the optional
per-case error report, and the guarantee that the default output is unchanged.
These tests do not run a model.
"""

import json
import subprocess
import sys
import unicodedata
import unittest
from pathlib import Path

import evaluate_facts
from evaluate_facts import load_jsonl, score


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "benchmarks" / "evaluate_facts.py"
EN_REFERENCE = ROOT / "examples" / "synthetic-data" / "cases.jsonl"
EN_PREDICTIONS = ROOT / "examples" / "synthetic-data" / "scorer-demo-predictions.jsonl"

HISTORIC_KEYS = {
    "evidence_quote_occurrence_rate",
    "evidence_quote_occurrences",
    "f1",
    "false_negative",
    "false_positive",
    "interpretation",
    "precision",
    "predictions",
    "recall",
    "true_positive",
}


def fact(subject="patient", concept="nausea", value="", polarity="present",
         temporality="current", quote=""):
    return {
        "subject": subject,
        "concept": concept,
        "value": value,
        "polarity": polarity,
        "temporality": temporality,
        "evidence_quote": quote,
    }


def one_case(reference_facts, prediction_facts, text="Texto sintetico."):
    references = {"c": {"case_id": "c", "text": text, "facts": reference_facts}}
    predictions = {"c": {"case_id": "c", "text": text, "facts": prediction_facts}}
    return references, predictions


def report_for(reference_facts, prediction_facts, text="Texto sintetico."):
    references, predictions = one_case(reference_facts, prediction_facts, text)
    return evaluate_facts.per_case_report(references, predictions)[0]


class UnicodeEquivalenceTests(unittest.TestCase):
    TEXT = "Tengo náuseas desde ayer."

    def decomposed(self, value):
        return unicodedata.normalize("NFD", value)

    def test_decomposed_and_composed_spellings_are_the_same_fact(self):
        composed = fact(concept="náuseas", quote="náuseas desde ayer")
        decomposed = fact(
            concept=self.decomposed("náuseas"),
            quote=self.decomposed("náuseas desde ayer"),
        )
        self.assertNotEqual(composed["concept"], decomposed["concept"])
        references, predictions = one_case([composed], [decomposed], self.TEXT)
        result = score(references, predictions)
        self.assertEqual(result["true_positive"], 1)
        self.assertEqual(result["false_positive"], 0)
        self.assertEqual(result["false_negative"], 0)
        self.assertEqual(result["evidence_quote_occurrences"], 1)

    def test_missing_accent_is_still_a_mismatch(self):
        references, predictions = one_case(
            [fact(concept="días")], [fact(concept="dias")], self.TEXT
        )
        result = score(references, predictions)
        self.assertEqual(result["true_positive"], 0)
        self.assertEqual(result["false_positive"], 1)
        self.assertEqual(result["false_negative"], 1)


class PerCaseReportTests(unittest.TestCase):
    def test_omission(self):
        report = report_for([fact(concept="fever", polarity="absent")], [])
        self.assertEqual(
            (report["true_positive"], report["false_positive"], report["false_negative"]),
            (0, 0, 1),
        )
        self.assertEqual([e["type"] for e in report["errors"]], ["omission"])
        self.assertEqual(report["errors"][0]["reference"]["concept"], "fever")
        self.assertEqual(report["error_events"], 1)

    def test_single_field_errors_are_one_event_but_one_fp_and_one_fn(self):
        cases = {
            "polarity": ({"polarity": "absent"}, {"polarity": "present"}),
            "subject": ({"subject": "mother"}, {"subject": "patient"}),
            "temporality": ({"temporality": "yesterday"}, {"temporality": "today"}),
            "value": ({"value": "right"}, {"value": "left"}),
        }
        for name, (gold_change, predicted_change) in cases.items():
            with self.subTest(field=name):
                report = report_for(
                    [fact(concept="pain", **gold_change)],
                    [fact(concept="pain", **predicted_change)],
                )
                self.assertEqual(
                    (report["true_positive"], report["false_positive"],
                     report["false_negative"]),
                    (0, 1, 1),
                )
                self.assertEqual(report["error_events"], 1)
                error = report["errors"][0]
                self.assertEqual(error["type"], "field_mismatch")
                self.assertEqual(error["fields"], [name])

    def test_several_differing_fields_are_listed_in_schema_order(self):
        report = report_for(
            [fact(concept="pain", polarity="absent", temporality="today")],
            [fact(concept="pain", polarity="present", temporality="yesterday")],
        )
        self.assertEqual(report["errors"][0]["fields"], ["polarity", "temporality"])

    def test_unsupported_prediction_has_no_reference_partner(self):
        report = report_for(
            [fact(concept="cough")],
            [fact(concept="cough"), fact(concept="hypertension")],
        )
        self.assertEqual(
            (report["true_positive"], report["false_positive"], report["false_negative"]),
            (1, 1, 0),
        )
        self.assertEqual([e["type"] for e in report["errors"]], ["unsupported_or_extra"])
        self.assertEqual(report["errors"][0]["predicted"]["concept"], "hypertension")

    def test_pairing_uses_one_reference_fact_per_prediction(self):
        earlier = fact(concept="fever", value="high", temporality="yesterday")
        later = fact(concept="fever", polarity="absent", temporality="today")
        report = report_for([earlier, later], [earlier])
        self.assertEqual([e["type"] for e in report["errors"]], ["omission"])
        self.assertEqual(report["errors"][0]["reference"]["temporality"], "today")

    def test_evidence_failure_is_reported_apart_from_fact_errors(self):
        gold = fact(concept="back_pain", quote="dolor de espalda")
        bad_quote = fact(concept="back_pain", quote="dolor lumbar cronico")
        report = report_for([gold], [bad_quote], text="Tengo dolor de espalda.")
        self.assertEqual(
            (report["true_positive"], report["false_positive"], report["false_negative"]),
            (1, 0, 0),
        )
        self.assertEqual(report["errors"], [])
        self.assertEqual(
            report["evidence_quotes_not_found"],
            [{"concept": "back_pain", "quote": "dolor lumbar cronico"}],
        )

    def test_missing_quote_counts_as_not_found(self):
        report = report_for([fact()], [fact(quote="")])
        self.assertEqual(len(report["evidence_quotes_not_found"]), 1)

    def test_empty_case_reports_zero_counts(self):
        report = report_for([], [])
        for key in ("true_positive", "false_positive", "false_negative",
                    "predictions", "reference_facts", "error_events"):
            self.assertEqual(report[key], 0, key)
        self.assertEqual(report["errors"], [])

    def test_per_case_counts_add_up_to_the_totals(self):
        references = load_jsonl(EN_REFERENCE)
        predictions = load_jsonl(EN_PREDICTIONS)
        totals = score(references, predictions)
        reports = evaluate_facts.per_case_report(references, predictions)
        for key in ("true_positive", "false_positive", "false_negative", "predictions"):
            self.assertEqual(sum(r[key] for r in reports), totals[key], key)
        self.assertEqual(
            sum(len(r["evidence_quotes_not_found"]) for r in reports),
            totals["predictions"] - totals["evidence_quote_occurrences"],
        )

    def test_english_demo_errors_by_case(self):
        reports = {
            r["case_id"]: r
            for r in evaluate_facts.per_case_report(
                load_jsonl(EN_REFERENCE), load_jsonl(EN_PREDICTIONS)
            )
        }
        self.assertEqual([e["type"] for e in reports["synthetic-001"]["errors"]], ["omission"])
        self.assertEqual(reports["synthetic-001"]["errors"][0]["reference"]["concept"], "fever")
        self.assertEqual(reports["synthetic-002"]["errors"][0]["fields"], ["polarity"])
        self.assertEqual(reports["synthetic-003"]["errors"], [])
        self.assertEqual(reports["synthetic-004"]["errors"][0]["fields"], ["value"])
        self.assertEqual(len(reports["synthetic-004"]["evidence_quotes_not_found"]), 1)
        self.assertEqual(reports["synthetic-001"]["evidence_quotes_not_found"], [])


class CommandLineTests(unittest.TestCase):
    def run_cli(self, *extra):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), str(EN_REFERENCE), str(EN_PREDICTIONS), *extra],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def test_default_output_is_unchanged(self):
        self.assertEqual(set(self.run_cli()), HISTORIC_KEYS)

    def test_per_case_flag_adds_detail_without_changing_totals(self):
        plain = self.run_cli()
        detailed = self.run_cli("--per-case")
        self.assertEqual({k: detailed[k] for k in HISTORIC_KEYS}, plain)
        self.assertEqual(set(detailed) - HISTORIC_KEYS, {"denominators", "per_case"})
        self.assertEqual(len(detailed["per_case"]), 4)

    def test_denominators_make_empty_results_interpretable(self):
        detailed = self.run_cli("--per-case")
        self.assertEqual(
            detailed["denominators"],
            {"precision": 4, "recall": 5, "evidence_quote_occurrence_rate": 4},
        )


if __name__ == "__main__":
    unittest.main()
