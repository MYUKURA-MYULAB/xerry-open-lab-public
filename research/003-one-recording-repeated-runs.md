# 003: One scripted recording, twelve identical runs

**Type:** methodological analysis of an internal experiment. **Status:** summarized from internal engineering records (August and November 2026) that are not published. **Not reproducible from this repository:** no audio, script, transcript, configuration, error values or timings are released, and the error values are withheld because the method that produced them cannot be reconstructed from the available records. This note does not report a benchmark, and its findings do not generalize to other recordings.

## Question

An internal experiment chose a decoding configuration for a third-party speech-recognition model, compared processing a recording in fixed-length chunks with processing it whole, and repeated the pipeline many times. What do those repeats establish, and what does the design make impossible to conclude?

## Context

The model is a third-party, quantized recognition model, not a Xerry model. It ran on a small edge device (8 GB of unified memory) as one stage of a longer pipeline. Only the transcription stage is discussed here. Speaker attribution was evaluated separately on other material and is out of scope.

## Procedure as documented

| Step | What was done |
|---|---|
| Material | One recording: a script read aloud for about five minutes by two people, in 24 script segments. The script has a few hundred words; the exact reference text is not recoverable. |
| Configuration selection | On 16 August 2026, four configurations of the same model each processed the recording. One of the two with the lowest error on that recording was adopted. |
| Comparison | The same recording was processed in fixed-length chunks and as a single pass, and the transcription error of the two was compared. |
| Repeats | On 17 August 2026, ten full passes: five under each of two device power settings, run as two blocks, the second on a warmer device. In November 2026, two more passes on an isolated copy of the scripts. Twelve passes in total. |

## What is and is not recoverable

| Element | State |
|---|---|
| Recording, script, number of words | Documented |
| Passes, dates, device class, power-setting blocks | Documented |
| Decoding settings | Documented internally, not released here |
| How the error rate was computed (formula, text normalization, tool) | **Not recovered** |
| What the error rate was computed against (the script, or a transcript of what was actually said) | **Not recovered** |
| Per-pass raw outputs | Not available to this review |

## Observations

1. The transcription-error measure and the number of output segments were identical in all twelve passes, under both power settings.
2. In each pass the internal record reports lower error for chunked processing than for single-pass processing. The records do not give a measure of uncertainty, and the difference is a small number of words in a script of a few hundred words.
3. The adopted configuration was selected on the same recording that was later used to report error.
4. Run times differ between the August and November entries. The records attribute this, without verification, to a later change in another stage. A separate internal audit states that the error values were not re-measured under the later configuration, so the records disagree on whether the November passes used it.

## Interpretation

**Technical repeatability is not generalization.** The twelve passes show that, for one input and one configuration, this pipeline is deterministic, and that the two power settings did not change the transcript. That is useful for auditing and regression testing. It says nothing about other recordings, because a deterministic procedure repeated on the same input has zero variance by construction.

| What is repeated | What it can test | Done here |
|---|---|---|
| Same recording, same settings | Determinism of the pipeline | Yes, twelve passes |
| Same recording, other device setting | Whether the setting changes the output | Yes, for this recording |
| Other recordings, same readers | Sensitivity to content | No |
| Other speakers, noise, speaking styles | Whether the result generalizes | No |

The unit of replication for a claim about recognition quality is the recording (and the speaker). Twelve passes leave n = 1. If per-recording error varies with standard deviation s, the uncertainty of an average over n recordings is about s/√n; with one recording it cannot be estimated.

**Selection and reporting on the same sample.** Choosing the configuration for its error on one recording and then reporting that error biases the reported figure downward. The comparison of chunked against single-pass processing is likewise not held out from the choice of configuration.

**What the record supports.** On this recording, under the configuration of August 2026, chunked processing had lower recorded error than single-pass processing in all passes. **What it does not support:** any recognition error for conversational or clinical audio, a ranking of configurations, a preference for chunking, an effect of the power setting on accuracy, or the accuracy of the pipeline as it is configured now.

## Threats to validity

- **One recording, two readers.** Speaker and content diversity is minimal.
- **Read speech.** A scripted reading is easier than conversation. The size of that effect was not measured here.
- **Same sample for selection and reporting** (see above).
- **Undefined reference and metric.** Without the formula, normalization and reference text, no figure can be checked or compared with any other figure.
- **Configuration drift.** The pipeline changed after August, and the records conflict on whether the later passes reflect that change.
- **One device.** Nothing is known about other hardware.
- **No independent annotation.** The people who wrote and read the script also ran the experiment.

## Next experiment (proposed, not executed)

1. **Data.** Recordings that are consented or redistributable, split by speaker into a development set (to choose a configuration) and a held-out test set, with a stratum of unscripted conversation.
2. **Reference.** Transcripts made by an annotator listening to the audio, not copied from a script, with a tenth of the recordings annotated twice.
3. **Metric fixed in advance.** A named open-source error-rate implementation and written normalization rules (case, punctuation, numerals).
4. **Size.** Pilot on five recordings to estimate the per-recording standard deviation s, then n = (1.96 · s / h)² held-out recordings for a target half-width h of 0.02 absolute. For example, an assumed s of 0.08 gives n = 62. This is arithmetic on an assumed value, not a result.
5. **Analysis.** Chunked minus single-pass error per recording, with a bootstrap 95% interval over recordings. No preference is claimed unless the interval excludes zero.
6. **Repeats.** Run each configuration twice, only to confirm determinism.
