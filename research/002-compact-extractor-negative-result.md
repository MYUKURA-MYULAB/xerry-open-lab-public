# 002: A negative result from a compact extractor on synthetic fixtures

**Type:** negative-result report. **Status:** one internal run, summarized from an internal report (September 2026) that is not published. **Not reproducible from this repository:** the model, its tokenizer and the fixtures are withheld. The statements below are the only ones released.

## Question

Can a compact experimental model (about 80.9 million parameters, see the [model card](../models/model-cards/xerry-extract-010a-e2.md)) extract evidence-grounded facts on a phone, when every candidate fact must pass a downstream check that accepts it only if the source supports it?

## What was done

The model was run locally on a phone over a small set of synthetic fixtures. Its candidate facts were passed to the evidence check.

## What was observed

- **No fact was accepted** on the documented fixtures.
- **Two failure shapes.** Some outputs were well-formed candidate facts that the source did not support. Others were "no claim" although the source contained positive content.
- **The check failed closed.** Every unsupported candidate was rejected, and no unsupported fact reached the later drafting stage, which was therefore not run.

## Interpretation

On these fixtures the failure is in candidate generation. The check behaved as intended: it rejected unsupported claims instead of passing them on. There is no evidence that relaxing it would be appropriate. This is a negative result on a few synthetic cases. It is not an estimate of the model's accuracy in either direction.

## What cannot be concluded

- **The cause.** Learned weights, prompt or decoding, tokenizer, and export to the on-device runtime are not separated. No ablation was recorded.
- **Any metric.** No locked evaluation set, annotation protocol or reproducible package exists to re-score the cases, and none of precision, recall or F1 is reported. Independently reproducible task-performance metrics are not yet available for this experimental model.
- **Generalization.** Nothing follows about other inputs, languages or devices.

## Next diagnostic (proposed, not executed)

Rerun the same kind of synthetic fixtures through a controlled comparison that varies model, prompt and decoding, tokenizer, and export one at a time. Record inputs, raw outputs, parser results and evidence decisions per case, and score the outputs with the scorer in this repository on the [Spanish battery](../examples/synthetic-data-es/README.md). Until this is done, the run is a record of safe failure, not evidence of useful extraction.
