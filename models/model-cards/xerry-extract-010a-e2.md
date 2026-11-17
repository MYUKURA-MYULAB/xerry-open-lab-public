# Model card: XERRY_EXTRACT_010A_E2

## Summary

XERRY_EXTRACT_010A_E2 is an experimental compact model (roughly 80.9 million parameters) for generating candidate structured facts from Spanish clinical-style text. It is a research artifact, not a medical device and not an autonomous clinical documentation system.

## Status

- The checkpoint exists internally and is not distributed. No weights, tokenizer, adapters, training data, training code, or exported packages are included in this repository.
- One small on-device experiment on a phone was documented internally. On its synthetic fixtures, no candidate claim was accepted after a downstream evidence check.
- Export lineage and training provenance have not been independently confirmed.

## Intended use

Research on compact extraction, abstention, evidence grounding, and local inference. Outputs require independent validation and human review. The model must not be used to diagnose, recommend treatment, or create clinical records without a separate validation and governance process.

## Evidence and limitations

In the internal synthetic fixtures, the model emitted unsupported candidate strings or no claim, and the evidence guard accepted none. This is a negative result from a small fixture set, not a statistically representative benchmark.

Independently reproducible task-performance metrics are not yet available for this experimental model. No precision, recall, F1, clinical-validity, or generalization result is reported here.

Known gaps:

- incomplete training-data provenance;
- no public evaluation dataset;
- no independently reproduced evaluation;
- no verified public inference package;
- incomplete export lineage.

## Licensing and distribution

The Apache License 2.0 of this repository covers only the files published in it. No license is granted for the model, its tokenizer, or related artifacts, which are not included and not available for download. Do not redistribute such artifacts until model-base, dataset, code, and derivative-artifact rights are resolved.
