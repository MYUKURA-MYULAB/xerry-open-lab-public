# 004: What validating a scorer can and cannot show

**Type:** protocol-validation note. **Subject of study:** the scorer in [`benchmarks/evaluate_facts.py`](../benchmarks/evaluate_facts.py). Every result below can be reproduced with the commands at the end. **No model is scored, and nothing here says how good any model or any set of labels is.**

## Question

For a scorer of structured facts, which properties can be verified with code alone, which need human judgments, and which need model outputs? Concretely: what do consistency checks, constructed-error controls and a mutation check establish for the scorer in this repository, and what remains unverified?

## Context

The scorer matches facts exactly on five fields and checks that evidence quotes occur in the source text (see [note 001](001-structured-fact-evaluation.md)). This branch adds 31 controls and a mutation check. An internal evaluator of the same kind went through the same kind of validation; only qualitative lessons from it are reported here, and its figures and data are not released.

## Four layers of evidence

| Layer | Question | What it needs | This scorer | Internal evaluator |
|---|---|---|---|---|
| 1. Consistency | Same input, same output; invariant to input order? | Code and examples | Tested | Its validation report regenerates identically (internal data only) |
| 2. Constructed controls | Does it reject known-bad inputs and accept known-equivalent ones? | Known-answer inputs written by the authors | 31 controls and a mutation check | Done |
| 3. Human agreement | Does it agree with experts on equivalence and support? | Blinded human labels | **Not done** | Sample prepared, **not labeled**; its semantic judge has **not been run** with a real model |
| 4. Model quality | How good is a model? | Model outputs and trusted references | **Not claimed** | **Not claimed** |

A scorer can pass layers 1 and 2 completely and still disagree with every clinician. Passing them supports "it follows its documented rules and rejects these known-bad inputs", and nothing more.

## Protocol

Each control group is a test class that states what it verifies and what it does not.

| Control | Property verified | Not verified |
|---|---|---|
| Ceiling | A prediction identical to the reference scores 1.0 on every metric | That the reference labels are correct |
| Negative | Facts taken from other cases earn nothing and are all charged | That quotes from other cases are rejected: short quotes can occur by coincidence |
| Input order | Totals do not depend on fact order, case order or file line order; counts do not depend on fact order inside a case | That the labels given to errors are order independent when several unmatched facts share a concept |
| Normalization | Case, repeated whitespace and Unicode composition are ignored; accents, punctuation, inflection and translation are not | That strictness is desirable |
| Evidence quotes | When a quote counts as occurring in the text | That the quote supports the fact; partial-word matches and unrelated quotes still count |
| Empty data | Zero denominators print 0.0; an empty benchmark is refused; every count is always present | Any convention beyond 0.0, which does not mean "no errors" |
| Field errors | One wrong field is one event but one false positive plus one false negative; a wrong concept is an omission plus an unsupported fact; duplicates are counted | That these charges are the right weights |

The **mutation check** ([`benchmarks/mutation_check.py`](../benchmarks/mutation_check.py)) tests the tests. It injects 11 known defects, one at a time, into a temporary copy of the scorer and runs the suite. A defect is caught when a test fails. A defect the suite cannot see means a control is missing or empty.

## Observations

**1. Suite.** 68 tests (11 original, 15 for the per-case report and Unicode handling, 11 for the Spanish battery, 31 controls) pass on Python 3.9.6 and 3.14.6.

**2. Mutation check.** All 11 defects were caught on both Python versions.

| Mutant | Injected defect | Test classes that fail |
|---|---|---|
| M1 | comparison becomes case-sensitive | 2 |
| M2 | no Unicode normalization in field comparison | 3 |
| M3 | polarity ignored when matching | 5 |
| M4 | temporality ignored when matching | 4 |
| M5 | any non-empty quote counts as occurring | 5 |
| M6 | quote compared without Unicode normalization | 2 |
| M7 | duplicate facts counted once | **1** |
| M8 | only the first predicted fact per case is read | 8 |
| M9 | zero-denominator metric reported as 1.0 | 3 |
| M10 | empty reference set accepted | **1** |
| M11 | a zero count missing from the output | 3 |

M7 and M10 each depend on a single test class, so one broken test would hide them.

**3. What the controls found.** Writing and running the controls exposed problems that the first 37 tests had not.

| # | Finding | Action |
|---|---|---|
| F1 | An empty reference file was scored as all zeros with exit code 0, so a pipeline that loads no cases looks like a valid run | Now refused with an error |
| F2 | Counts that were zero (predictions, quote occurrences) were missing from the output, so the output keys depended on the data; this also crashed the `--per-case` option when nothing was predicted | Every count is now always present |
| F3 | One of the new controls could not fail: a decomposed-accent quote was tested against unaccented text. The mutation check showed mutant M6 caught only by an older test | Control rewritten to use accented text, and M6 is now caught by both |
| F4 | Characterized, not changed: partial-word quote matches count; whitespace in the source is not collapsed although whitespace in fields is; a quote unrelated to the fact counts; error labels may vary with input order when several unmatched facts share a concept; a zero denominator prints 0.0 | Documented as tests that record current behavior, so any change is deliberate |

**4. Internal evaluator, qualitatively.** A negative control (facts from another case) caught a defect that its authors had not noticed in the first version: a large share of reference facts scored as correct against another case's facts. One constructed-error control (laterality) had no applicable cases, so that property was never tested. These are layer-2 findings. The evaluator has no layer-3 evidence.

## Interpretation

The scorer follows its documented rules on these inputs, and the suite would fail for 11 specific defects. Where a control group is the only one catching a defect, that defect is protected by one test class. Nothing here supports a claim that the scorer's equivalence rules match expert judgment, or that any model is accurate.

## Threats to validity

- **Circularity.** The same authors wrote the scorer, the controls and the mutants. The mutants are the ones we thought of.
- **Characterization tests.** Several tests lock in behavior that is arguably wrong (F4). Passing them does not make it right.
- **Size.** The examples are 16 short fictional cases. Controls on real, noisy outputs would meet inputs these do not cover.
- **Scope.** Command-line error handling is tested for three cases only. Only the standard library on two Python versions was exercised.

## Next experiment (proposed, not executed)

A layer-3 study. Take the unmatched pairs reported by `--per-case` on the outputs proposed in [note 001](001-structured-fact-evaluation.md), 25 per phenomenon (150 in all). Two annotators label each pair, blind to the scorer's decision, as equivalent or not equivalent, and each quote as supporting the fact or not. Report agreement between annotators (Cohen's kappa) and between the scorer and the annotators' consensus, with bootstrap intervals. Adopt a tolerance rule (for example accent-insensitive matching or equivalent time expressions) only if it raises scorer-annotator agreement without failing the negative control or letting a mutant survive.

## Reproduce

    python3 -m unittest discover -s benchmarks -p 'test_*.py'
    python3 benchmarks/mutation_check.py
