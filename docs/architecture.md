# Reference architecture

The diagram describes a research target, not a completed product. Each stage should expose its version, input, output, confidence or abstention state, and the evidence needed by the next stage.

    Audio
      -> speech recognition
      -> speaker attribution
      -> candidate fact extraction with source evidence
      -> validation and review of candidate facts
      -> separate document drafting
      -> human review

## Stage roles and interface contracts

| Stage | Role | Minimum contract |
|---|---|---|
| Speech recognition | Convert audio to text segments | Model version, language, segment timing, uncertainty signal |
| Speaker attribution | Assign segments to speakers | Speaker labels, overlap handling, uncertainty signal |
| Candidate fact extraction | Propose structured facts from text | Subject, concept, value, polarity, temporality, evidence quote, abstention state |
| Validation | Check candidates against the source | Accept or reject decision with a reason; no silent repair |
| Document drafting | Draft from accepted facts only | Accepted facts and source references as the only inputs |
| Human review | Approve, correct, or reject output | Recorded decision and the version reviewed |

The fact schema in the contract above is the one read by the scorer in `benchmarks/`. No other stage is implemented in this repository.

## Why separate stages

Separating transcription, speaker attribution, extraction, and drafting makes it possible to evaluate distinct error sources. It also allows a system to stop when an earlier stage is uncertain. Modularity can add integration errors and latency, so end-to-end evaluation remains necessary.

The extractor should produce candidate facts with source evidence, polarity, time, and subject. A deterministic validator or reviewer can reject candidates that cannot be grounded. A drafting component should use only accepted material and should not silently repair missing evidence with plausible text.

## Deployment boundary

This reference architecture intentionally omits product services, endpoints, production orchestration, device design, and customer integrations. It does not specify a deployable medical device or clinical workflow.
