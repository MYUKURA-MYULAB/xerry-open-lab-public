"""Tests for the Spanish synthetic battery; these tests do not run a model.

The predictions file is hand-authored: each case either is a control (identical to
the reference) or contains one deliberate error of a known type. The expected values
below were derived by hand from the case design, not copied from scorer output.
"""

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

import evaluate_facts
from evaluate_facts import load_jsonl, score


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = ROOT / "examples" / "synthetic-data-es" / "cases.jsonl"
PREDICTIONS_PATH = ROOT / "examples" / "synthetic-data-es" / "scorer-demo-predictions.jsonl"

# case_id -> (true positives, false positives, false negatives)
EXPECTED_COUNTS = {
    "synthetic-es-001": (2, 0, 1),
    "synthetic-es-002": (2, 1, 1),
    "synthetic-es-003": (2, 0, 0),
    "synthetic-es-004": (0, 1, 1),
    "synthetic-es-005": (0, 1, 1),
    "synthetic-es-006": (1, 0, 0),
    "synthetic-es-007": (1, 1, 1),
    "synthetic-es-008": (2, 0, 0),
    "synthetic-es-009": (1, 0, 0),
    "synthetic-es-010": (1, 0, 1),
    "synthetic-es-011": (0, 1, 1),
    "synthetic-es-012": (2, 1, 0),
}

# case_id -> [(error type, differing fields or None, concept)]
EXPECTED_ERRORS = {
    "synthetic-es-001": [("omission", None, "cough")],
    "synthetic-es-002": [("field_mismatch", ["polarity"], "nausea")],
    "synthetic-es-003": [],
    "synthetic-es-004": [("field_mismatch", ["temporality"], "dizziness")],
    "synthetic-es-005": [("field_mismatch", ["value"], "pain_location")],
    "synthetic-es-006": [],
    "synthetic-es-007": [("field_mismatch", ["subject"], "diabetes")],
    "synthetic-es-008": [],
    "synthetic-es-009": [],
    "synthetic-es-010": [("omission", None, "fever")],
    "synthetic-es-011": [("field_mismatch", ["value"], "ibuprofen_use")],
    "synthetic-es-012": [("unsupported_or_extra", None, "hypertension")],
}

# Phenomena named in the battery README; two cases each.
PHENOMENA = {
    "negation": ("synthetic-es-001", "synthetic-es-002"),
    "resolved symptom": ("synthetic-es-003", "synthetic-es-004"),
    "laterality correction": ("synthetic-es-005", "synthetic-es-006"),
    "patient/relative attribution": ("synthetic-es-007", "synthetic-es-008"),
    "temporality": ("synthetic-es-009", "synthetic-es-010"),
    "medication or dose": ("synthetic-es-011", "synthetic-es-012"),
}


class SpanishBatteryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.references = load_jsonl(REFERENCE_PATH)
        cls.predictions = load_jsonl(PREDICTIONS_PATH)
        cls.reports = {
            r["case_id"]: r
            for r in evaluate_facts.per_case_report(cls.references, cls.predictions)
        }

    def test_twelve_cases_with_unique_spanish_identifiers(self):
        self.assertEqual(len(self.references), 12)
        self.assertTrue(all(c.startswith("synthetic-es-") for c in self.references))
        self.assertEqual(set(self.references), set(EXPECTED_COUNTS))

    def test_each_named_phenomenon_has_two_cases_in_the_battery(self):
        for name, case_ids in PHENOMENA.items():
            for case_id in case_ids:
                self.assertIn(case_id, self.references, name)

    def test_source_texts_look_fictional(self):
        for case_id, row in self.references.items():
            text = row["text"]
            self.assertNotRegex(text, r"@|https?://|www\.", case_id)
            if case_id != "synthetic-es-011":
                self.assertNotRegex(text, r"\d", case_id)
        digits = re.findall(r"\d+", self.references["synthetic-es-011"]["text"])
        self.assertEqual(digits, ["400"])

    def test_reference_scores_perfectly_against_itself(self):
        result = score(self.references, self.references)
        self.assertEqual(result["true_positive"], 21)
        self.assertEqual(result["false_positive"], 0)
        self.assertEqual(result["false_negative"], 0)
        self.assertEqual(result["evidence_quote_occurrence_rate"], 1.0)

    def test_hand_authored_predictions_totals(self):
        result = score(self.references, self.predictions)
        self.assertEqual(result["true_positive"], 14)
        self.assertEqual(result["false_positive"], 6)
        self.assertEqual(result["false_negative"], 7)
        self.assertEqual(result["predictions"], 20)
        self.assertEqual(result["evidence_quote_occurrences"], 18)
        self.assertAlmostEqual(result["precision"], 14 / 20)
        self.assertAlmostEqual(result["recall"], 14 / 21)
        self.assertAlmostEqual(result["f1"], 2 * (14 / 20) * (14 / 21) / (14 / 20 + 14 / 21))
        self.assertAlmostEqual(result["evidence_quote_occurrence_rate"], 0.9)

    def test_per_case_counts(self):
        for case_id, expected in EXPECTED_COUNTS.items():
            report = self.reports[case_id]
            self.assertEqual(
                (report["true_positive"], report["false_positive"], report["false_negative"]),
                expected,
                case_id,
            )

    def test_error_classification_by_case(self):
        for case_id, expected in EXPECTED_ERRORS.items():
            actual = []
            for error in self.reports[case_id]["errors"]:
                partner = error.get("reference") or error["predicted"]
                actual.append((error["type"], error.get("fields"), partner["concept"]))
            self.assertEqual(actual, expected, case_id)

    def test_eight_error_events_produce_thirteen_false_counts(self):
        events = sum(r["error_events"] for r in self.reports.values())
        false_counts = sum(r["false_positive"] + r["false_negative"] for r in self.reports.values())
        self.assertEqual(events, 8)
        self.assertEqual(false_counts, 13)

    def test_evidence_failures_are_found_only_where_designed(self):
        failing = {
            case_id: [q["concept"] for q in report["evidence_quotes_not_found"]]
            for case_id, report in self.reports.items()
            if report["evidence_quotes_not_found"]
        }
        self.assertEqual(
            failing,
            {"synthetic-es-009": ["back_pain"], "synthetic-es-012": ["hypertension"]},
        )

    def test_wrong_value_with_an_occurring_quote_is_invisible_to_the_quote_check(self):
        report = self.reports["synthetic-es-011"]
        self.assertEqual(report["false_positive"], 1)
        self.assertEqual(report["evidence_quotes_not_found"], [])

    def test_cli_runs_on_the_spanish_battery(self):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "benchmarks" / "evaluate_facts.py"),
             str(REFERENCE_PATH), str(PREDICTIONS_PATH), "--per-case"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["true_positive"], 14)
        self.assertEqual(len(result["per_case"]), 12)


if __name__ == "__main__":
    unittest.main()
