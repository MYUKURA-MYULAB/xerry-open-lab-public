"""Tests for the synthetic JSONL scorer; these tests do not run a model."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evaluate_facts import load_jsonl, score


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_PATH = ROOT / "examples" / "synthetic-data" / "cases.jsonl"
DEMO_PREDICTIONS_PATH = (
    ROOT / "examples" / "synthetic-data" / "scorer-demo-predictions.jsonl"
)


class EvaluateFactsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.references = load_jsonl(REFERENCE_PATH)

    def write_jsonl(self, rows, content=None):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "input.jsonl"
        if content is not None:
            path.write_text(content, encoding="utf-8")
        else:
            path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
        return path

    def test_identical_reference_predictions_score_perfect(self):
        result = score(self.references, self.references)
        self.assertEqual(result["true_positive"], 5)
        self.assertEqual(result["false_positive"], 0)
        self.assertEqual(result["false_negative"], 0)
        self.assertEqual(result["precision"], 1.0)
        self.assertEqual(result["recall"], 1.0)
        self.assertEqual(result["f1"], 1.0)
        self.assertEqual(result["evidence_quote_occurrence_rate"], 1.0)

    def test_hand_authored_demo_has_expected_errors_and_metrics(self):
        result = score(self.references, load_jsonl(DEMO_PREDICTIONS_PATH))
        self.assertEqual(result["true_positive"], 2)
        self.assertEqual(result["false_positive"], 2)
        self.assertEqual(result["false_negative"], 3)
        self.assertEqual(result["predictions"], 4)
        self.assertEqual(result["evidence_quote_occurrences"], 3)
        self.assertEqual(result["precision"], 0.5)
        self.assertEqual(result["recall"], 0.4)
        self.assertAlmostEqual(result["f1"], 4 / 9)
        self.assertEqual(result["evidence_quote_occurrence_rate"], 0.75)

    def test_zero_predictions_are_scored_without_division_error(self):
        predictions = {
            case_id: {**row, "facts": []}
            for case_id, row in self.references.items()
        }
        result = score(self.references, predictions)
        self.assertEqual(result["true_positive"], 0)
        self.assertEqual(result["false_positive"], 0)
        self.assertEqual(result["false_negative"], 5)
        self.assertEqual(result["precision"], 0.0)
        self.assertEqual(result["recall"], 0.0)
        self.assertEqual(result["f1"], 0.0)
        self.assertEqual(result["evidence_quote_occurrence_rate"], 0.0)

    def test_case_identifier_mismatch_is_rejected(self):
        predictions = dict(self.references)
        predictions.pop("synthetic-004")
        with self.assertRaisesRegex(ValueError, "case_id mismatch"):
            score(self.references, predictions)

    def test_source_text_mismatch_is_rejected(self):
        predictions = dict(self.references)
        changed = dict(predictions["synthetic-001"])
        changed["text"] = "different synthetic text"
        predictions["synthetic-001"] = changed
        with self.assertRaisesRegex(ValueError, "text mismatch"):
            score(self.references, predictions)

    def test_malformed_json_is_rejected(self):
        path = self.write_jsonl([], content='{"case_id":\n')
        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            load_jsonl(path)

    def test_non_object_json_row_is_rejected(self):
        path = self.write_jsonl([], content="[]\n")
        with self.assertRaisesRegex(ValueError, "must be an object"):
            load_jsonl(path)

    def test_duplicate_case_identifier_is_rejected(self):
        row = {
            "case_id": "duplicate",
            "text": "Synthetic text.",
            "facts": [],
        }
        path = self.write_jsonl([row, row])
        with self.assertRaisesRegex(ValueError, "duplicate case_id"):
            load_jsonl(path)

    def test_missing_fact_field_is_rejected(self):
        path = self.write_jsonl(
            [
                {
                    "case_id": "case",
                    "text": "Synthetic text.",
                    "facts": [{"subject": "patient"}],
                }
            ]
        )
        with self.assertRaisesRegex(ValueError, "concept"):
            load_jsonl(path)

    def test_cli_emits_json_and_succeeds_for_hand_authored_demo(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "benchmarks" / "evaluate_facts.py"),
                str(REFERENCE_PATH),
                str(DEMO_PREDICTIONS_PATH),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["true_positive"], 2)
        self.assertEqual(result["false_positive"], 2)
        self.assertAlmostEqual(result["f1"], 4 / 9)

    def test_cli_returns_nonzero_and_clear_error_for_identifier_mismatch(self):
        reference_path = self.write_jsonl(
            [{"case_id": "expected", "text": "Synthetic text.", "facts": []}]
        )
        prediction_path = self.write_jsonl(
            [{"case_id": "unexpected", "text": "Synthetic text.", "facts": []}]
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "benchmarks" / "evaluate_facts.py"),
                str(reference_path),
                str(prediction_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("case_id mismatch", completed.stderr)
        self.assertEqual(completed.stdout, "")


if __name__ == "__main__":
    unittest.main()
