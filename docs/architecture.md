# Reference architecture

The diagram separates three states that are easy to confuse: what is **implemented** in this repository, what was **executed internally** without public reproduction, and what is **proposed** research. Only the fact scorer and its fixtures are implemented here. Everything else is either an internal experiment that cannot be rerun from this repository or a design.

```mermaid
flowchart LR
    AUDIO(["Audio input"]):::neutral
    ASR["Specialized ASR<br/>PROPOSED"]:::proposed
    SPK["Speaker attribution<br/>PROPOSED"]:::proposed
    EXT["Compact extractor, ~80.9M<br/>EXECUTED INTERNALLY<br/>no public reproduction"]:::internal
    ENC["Encoder-based extractor<br/>PROPOSED"]:::proposed
    GUARD["Evidence check<br/>EXECUTED INTERNALLY<br/>no public reproduction"]:::internal
    DRAFT["Document generation<br/>from accepted facts<br/>PROPOSED"]:::proposed
    REVIEW["Human review<br/>PROPOSED"]:::proposed
    CASES[("Synthetic cases<br/>4 English, 12 Spanish<br/>IMPLEMENTED")]:::implemented
    SCORER["Fact scorer<br/>benchmarks/evaluate_facts.py<br/>IMPLEMENTED"]:::implemented

    subgraph CROSS["Cross-cutting, all PROPOSED"]
        direction TB
        TRACE["End-to-end traceability<br/>PROPOSED"]:::proposed
        DEPLOY["Modular local deployment<br/>PROPOSED"]:::proposed
    end

    AUDIO --> ASR --> SPK --> EXT --> GUARD --> DRAFT --> REVIEW
    SPK -.-> ENC -.-> GUARD
    EXT -.->|"candidate facts (JSONL)"| SCORER
    ENC -.->|"candidate facts (JSONL)"| SCORER
    CASES --> SCORER

    classDef implemented fill:#d1fae5,stroke:#047857,stroke-width:3px,color:#064e3b
    classDef internal fill:#fef3c7,stroke:#b45309,stroke-width:2px,stroke-dasharray:6 3,color:#78350f
    classDef proposed fill:#f3f4f6,stroke:#6b7280,stroke-width:1px,stroke-dasharray:2 4,color:#374151
    classDef neutral fill:#ffffff,stroke:#6b7280,color:#111827
```

Solid arrows show the intended data flow. Dotted arrows are an alternative path (encoder) or an evaluation tap (scoring candidate facts against reference cases). The status is written in each node so it does not depend on color: green with a heavy border is implemented, dashed amber was executed internally, dotted grey is proposed.

## Status of each component

| Component | Status | What this repository contains |
|---|---|---|
| Fact scorer | Implemented | `benchmarks/evaluate_facts.py` and its tests; see [research note 001](../research/001-structured-fact-evaluation.md) |
| Synthetic cases | Implemented | Four English and twelve Spanish fictional cases with hand-authored predictions |
| Compact extractor | Executed internally | A [model card](../models/model-cards/xerry-extract-010a-e2.md) and a [negative-result note](../research/002-compact-extractor-negative-result.md); no model files |
| Evidence check | Executed internally | Described in note 002; no implementation |
| Specialized ASR, speaker attribution | Proposed | Nothing; interface contract below. A third-party recognition model was run internally on one recording ([note 003](../research/003-one-recording-repeated-runs.md)); no specialized ASR exists |
| Encoder-based extractor | Proposed | Nothing; the comparison is an open question |
| Document generation, human review | Proposed | Nothing; interface contract below |
| Traceability, modular deployment | Proposed | Nothing |

## Interface contract per stage

| Stage | Role | Minimum contract |
|---|---|---|
| Speech recognition | Convert audio to text segments | Model version, language, segment timing, uncertainty signal |
| Speaker attribution | Assign segments to speakers | Speaker labels, overlap handling, uncertainty signal |
| Candidate fact extraction | Propose structured facts from text | Subject, concept, value, polarity, temporality, evidence quote, abstention state |
| Evidence check | Test candidates against the source | Accept or reject with a reason; no silent repair |
| Document generation | Draft from accepted facts only | Accepted facts and source references as the only inputs |
| Human review | Approve, correct, or reject output | Recorded decision and the version reviewed |

The extraction contract is the schema read by the scorer.

## Why separate stages

Separating transcription, speaker attribution, extraction and drafting makes it possible to attribute errors to a stage and to stop when an earlier stage is uncertain. Modularity also adds integration errors and latency, so it is a hypothesis to test against end-to-end systems, not an assumption. A drafting component should use only accepted facts and should not repair missing evidence with plausible text.

## Boundary

This page omits product services, endpoints, production orchestration, device design and customer integrations. It does not describe a deployable system.
