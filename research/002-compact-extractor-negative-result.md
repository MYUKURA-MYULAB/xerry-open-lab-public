# 002: Five tests of a compact extractor, no accepted facts

**Type:** negative-result report. **Status:** one internal run, summarized from an internal report (September 2026) that is not published. **Not reproducible from this repository:** the model, its tokenizer and the test inputs are withheld. Raw outputs, timings, memory figures and the device are also withheld. Nothing below should be read as a benchmark.

## Question

In one on-device run of a compact experimental model (about 80.9 million parameters, see the [model card](../models/model-cards/xerry-extract-010a-e2.md)), does a downstream check that accepts a fact only when the source supports it stop unsupported output from reaching the next stage?

## Context

The run was a technical feasibility test on a phone. The model generated candidate facts from short inputs, a parser read them, and an evidence check accepted or rejected each one. A drafting stage after the check was to run only if at least one fact was accepted.

## Procedure

Five tests were run, each with one input and one generation. Decoding was deterministic. The inputs are described only by kind, because the internal report does not state how they were produced. They are **short test fixtures**, and should not be read as synthetic data or as real clinical data.

## Observations

| # | Input kind | Model output | Evidence check |
|---|---|---|---|
| 1 | One short sentence stating a symptom | A candidate fact not supported by the source | Rejected |
| 2 | Four-turn consultation with a symptom and a medication | No claim | Nothing to check |
| 3 | Transcript deliberately fragmented to mimic recognition errors | No claim | Nothing to check |
| 4 | Multi-turn medication exchange | A candidate fact not supported by the source | Rejected |
| 5 | One short sentence stating a medication | A candidate fact not supported by the source | Rejected |

- Three of five tests produced a candidate fact the source did not support, and **the check rejected all three in this run**.
- Two of five produced no claim. One of those two used a deliberately degraded input.
- No fact was accepted, so the state after the check stayed empty and the drafting stage did not run.

## Interpretation

In this run the check behaved as designed: nothing unsupported passed to the next stage. The model did not produce an acceptable candidate in any of the five tests, which is a failure at generation, not at the check. Five tests with one generation each cannot show how often either behavior occurs.

## Threats to validity

- **Sample.** Five inputs, one generation each, one device, one decoding setting.
- **Provenance.** The origin of the inputs is not documented, so representativeness is unknown.
- **Confounded cause.** Learned weights, prompt, decoding, tokenizer, and conversion to the on-device runtime were not separated, and no ablation exists. The failure cannot be attributed to the model alone.
- **Degraded input.** One of the two no-claim outputs came from an input made fragmentary on purpose.
- **No metrics.** No annotation protocol, held-out set or re-scoring package exists. Independently reproducible task-performance metrics are not yet available for this experimental model.
- **The check is untested here.** Rejecting three unsupported candidates does not show that it would reject other kinds of unsupported output.

## Next experiment (proposed, not executed)

Run the same five inputs and the [Spanish battery](../examples/synthetic-data-es/README.md) with raw outputs retained, in four controlled variants that change one factor at a time: the reference implementation against the on-device export on identical inputs (token by token), the prompt, the decoding setting, and the tokenizer. Score the parsed outputs with the scorer in this repository. If the reference implementation and the export already differ on identical inputs, the conversion is the first thing to fix. If they agree, the failure belongs to the model or the prompt.
