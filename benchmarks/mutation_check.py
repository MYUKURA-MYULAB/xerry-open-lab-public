#!/usr/bin/env python3
"""Check that the test suite can fail: inject known defects into a copy of the scorer.

For each mutant, the benchmarks and examples folders are copied to a temporary
directory, one source edit is applied to the copy of evaluate_facts.py, and the test
suite is run against the copy. A mutant is caught when at least one test fails, and
the failing test classes are reported. The repository files are never modified.
A mutation that no longer applies (the text it replaces has changed) is an error, so
stale mutants cannot pass silently. Standard library only.

Usage, from the repository root:  python3 benchmarks/mutation_check.py
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# (id, defect, [(text to replace, replacement), ...])
MUTANTS = [
    ("M1", "comparison becomes case-sensitive",
     [("composed.casefold()", "composed")]),
    ("M2", "no Unicode normalization in field comparison",
     [('composed = unicodedata.normalize("NFC", value)', "composed = value"),
      ('return unicodedata.normalize("NFC", composed.casefold())', "return composed.casefold()")]),
    ("M3", "polarity is ignored when matching",
     [('return tuple(normalize(fact[field]) for field in FACT_FIELDS)',
       'return tuple(normalize(fact[field]) for field in FACT_FIELDS if field != "polarity")')]),
    ("M4", "temporality is ignored when matching",
     [('return tuple(normalize(fact[field]) for field in FACT_FIELDS)',
       'return tuple(normalize(fact[field]) for field in FACT_FIELDS if field != "temporality")')]),
    ("M5", "any non-empty evidence quote counts as occurring",
     [("return bool(quote) and fold(quote) in fold(text)", "return bool(quote)")]),
    ("M6", "evidence quote compared without Unicode normalization",
     [("return bool(quote) and fold(quote) in fold(text)",
       "return bool(quote) and quote.casefold() in text.casefold()")]),
    ("M7", "duplicate facts are counted once",
     [('Counter(signature(fact) for fact in reference["facts"])',
       'Counter(set(signature(fact) for fact in reference["facts"]))'),
      ('Counter(signature(fact) for fact in prediction["facts"])',
       'Counter(set(signature(fact) for fact in prediction["facts"]))')]),
    ("M8", "only the first predicted fact of each case is read",
     [('Counter(signature(fact) for fact in prediction["facts"])',
       'Counter(signature(fact) for fact in prediction["facts"][:1])')]),
    ("M9", "a metric with a zero denominator is reported as 1.0",
     [("return numerator / denominator if denominator else 0.0",
       "return numerator / denominator if denominator else 1.0")]),
    ("M10", "an empty reference set is accepted",
     [("if not references:", "if False:")]),
    ("M11", "a count is missing from the output when it is zero",
     [('                "evidence_quote_occurrences",\n', "")]),
]

FAILURE = re.compile(r"^(?:FAIL|ERROR): \S+ \((\w+)\.(\w+)[.)]", re.MULTILINE)


def run_suite(tree):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(tree / "benchmarks"),
         "-p", "test_*.py"],
        cwd=tree, env=env, capture_output=True, text=True,
    )
    classes = sorted({name for _, name in FAILURE.findall(completed.stderr)})
    return completed.returncode, classes


def build_tree(destination, edits):
    ignore = shutil.ignore_patterns("__pycache__", "mutation_check.py")
    shutil.copytree(ROOT / "benchmarks", destination / "benchmarks", ignore=ignore)
    shutil.copytree(ROOT / "examples", destination / "examples")
    target = destination / "benchmarks" / "evaluate_facts.py"
    source = target.read_text(encoding="utf-8")
    for old, new in edits:
        if old not in source:
            raise SystemExit(f"mutation does not apply, update the mutant: {old!r}")
        source = source.replace(old, new)
    target.write_text(source, encoding="utf-8")


def main():
    with tempfile.TemporaryDirectory() as folder:
        baseline = Path(folder) / "baseline"
        build_tree(baseline, [])
        code, classes = run_suite(baseline)
        if code != 0:
            raise SystemExit(f"the unmodified suite fails: {classes}")
        print("unmodified copy: all tests pass\n")
        print("| Mutant | Injected defect | Caught | Failing test classes |")
        print("|---|---|---|---|")
        missed = 0
        for mutant_id, description, edits in MUTANTS:
            tree = Path(folder) / mutant_id
            build_tree(tree, edits)
            code, classes = run_suite(tree)
            caught = code != 0
            missed += not caught
            print(f"| {mutant_id} | {description} | {'yes' if caught else 'NO'} | "
                  f"{', '.join(classes) if classes else '-'} |")
    print(f"\n{len(MUTANTS) - missed} of {len(MUTANTS)} mutants caught")
    return 1 if missed else 0


if __name__ == "__main__":
    raise SystemExit(main())
