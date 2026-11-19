# Synthetic Spanish cases

**Fictional material, not real clinical data.** Twelve short Spanish texts with reference facts, plus a hand-authored prediction file. Every string was written for this test. Nothing comes from clinical records, patient-facing material, or restricted corpora, and no personal data is involved. Doses are illustrative and are not recommendations.

The predictions are **not model output**. Each case is either a control (the prediction equals the reference) or contains one deliberate error of a known type, chosen to exercise the scorer. The 12 cases are far too few to evaluate a model; they are a protocol fixture.

## Coverage and designed errors

| Phenomenon | Case | Source text | Designed prediction error |
|---|---|---|---|
| Negation | `synthetic-es-001` | No tengo fiebre ni tos, pero me duele la garganta desde ayer. | omission: the negated cough is missing |
| Negation | `synthetic-es-002` | Refiere dolor de cabeza, sin náuseas ni mareos. | polarity: nausea reported as present |
| Resolved symptom | `synthetic-es-003` | La tos se resolvió hace una semana, pero todavía tengo congestión nasal. | none (control) |
| Resolved symptom | `synthetic-es-004` | El mareo desapareció ayer por la noche. | temporality: "yesterday" instead of "last night" |
| Laterality correction | `synthetic-es-005` | Primero dije que el dolor era en el lado izquierdo, pero me corrijo: es en el lado derecho. | value: the superseded side is reported |
| Laterality correction | `synthetic-es-006` | Me duele la rodilla izquierda, perdón, quise decir la derecha. | none (control) |
| Patient/relative | `synthetic-es-007` | Mi madre tiene diabetes, pero yo no. | subject: the mother's diabetes is attributed to the patient |
| Patient/relative | `synthetic-es-008` | Mi hermano tiene asma y a mí me dan ataques de tos por la noche. | none (control) |
| Temporality | `synthetic-es-009` | Tengo dolor de espalda desde hace tres semanas. | evidence: correct fact, quote not in the text |
| Temporality | `synthetic-es-010` | Ayer tuve fiebre alta, pero hoy no tengo fiebre. | omission: the later absence of fever is missing |
| Medication or dose | `synthetic-es-011` | Tomo ibuprofeno de 400 mg cada ocho horas desde el lunes. | value: wrong dose interval, quote occurs |
| Medication or dose | `synthetic-es-012` | Mi padre toma metformina, pero yo no tomo ningún medicamento. | unsupported: an extra condition not in the text |

## Label conventions

- `subject`: `patient`, `mother`, `father`, or `sibling`.
- `concept`: English snake_case code, for example `nasal_congestion`. The source text is Spanish and the labels are English, so a scored system must reproduce these codes exactly. A system that was not given this vocabulary will be penalized for naming, not only for extraction.
- `polarity`: `present`, `absent`, or `resolved`.
- `temporality`: a normalized English label for the time expression in the source (`current` when there is none). It records the expression, not its semantic role: in case 003 it anchors the resolution, in case 009 the onset. The scorer compares the label as a string, so a near miss such as "yesterday" against "last night" counts as a full error.
- A statement and its later contrast about the same concept are separate facts (case 010).

Files are UTF-8 in Unicode NFC. The scorer compares accents (`dias` is not `días`) but treats composed and decomposed spellings of the same accent as equal.

## Run

From the repository root:

    python3 benchmarks/evaluate_facts.py examples/synthetic-data-es/cases.jsonl examples/synthetic-data-es/scorer-demo-predictions.jsonl --per-case

Expected totals: 14 true positives, 6 false positives, 7 false negatives, 20 predicted facts, precision 0.7, recall 0.6667, F1 0.6829, evidence-quote occurrence 0.9. These describe the scorer on hand-authored input. They are not a measure of any model.
