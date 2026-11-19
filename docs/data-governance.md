# Data governance decisions

These are the methodological rules we set for any external dataset, and how far each has actually been carried out. This repository does not list candidate datasets, their licenses, counts or any sample of third-party text. Its only data is fictional text written for the tests (see [examples](../examples/synthetic-data-es/README.md)).

**Scope of "applied".** It refers to one first-pass audit of candidate external sources, completed in September 2026. None of that material is in this repository. Nothing here is legal advice.

## Policy, practice and pending checks

| # | Policy | Applied so far | Pending, or limit |
|---|---|---|---|
| 1 | The license is read from the primary source (the repository or the publisher's record) and recorded with date and location. A secondary summary is not enough. | **Partly.** Licenses were recorded from the sources' own pages. For some sources the records conflict. | Resolution with the rights holders. |
| 2 | Missing or conflicting terms are treated as no permission until resolved. Where sources disagree, the more restrictive reading applies and the conflict is logged. | **Applied.** Sources with conflicting or non-commercial terms were classified as blocked, reference only, or pending legal review. | Replies from rights holders. |
| 3 | Each source has one of four statuses: usable with conditions, blocked, reference only, pending legal review. Non-commercial terms mean reference only. | **Applied** in that audit. | The statuses are our reading of the terms, not a legal determination. |
| 4 | Automation is triage and a person reviews before anything is promoted. | **Partly.** Scripts scored duplication, realism and license metadata, and review packages of candidate items were prepared for people. | **The human review itself.** No completed review is recorded, so nothing has been approved for use. |
| 5 | Evaluation material is kept apart. Protected items are registered by content hash, candidates are checked against the registry for exact matches, and a semantic-overlap check needs a custodian's attestation. Until it is given, promotion is blocked. Protected items are never used to build, prompt or tune a system or to generate material for them. | **Partly.** The exact-hash check was run once and found no exact match. | The custodian's semantic check. Hashes miss paraphrases and the miss rate is unmeasured. The check was not repeated for later additions. |
| 6 | Obligations travel with the data: for attribution licenses, record creator, license location, source location and a notice of modification; track share-alike terms as they propagate. | **Not applied yet.** Requirements were identified and notices drafted. As of the last record (August 2026) they were not placed in any deliverable. | Placement, and manual tracking of share-alike propagation. |
| 7 | Sources are inspected through small, distributed samples with a fixed random seed. Large corpora are not copied into deliverables. | **Applied** in that audit. Raw downloads were kept out of the review package. | A sample can miss rare problems. |
| 8 | No personal data in this repository. Every example is fictional text written for its test. No recordings, identifiable transcripts or clinical records are published. | **Applied** to this repository, which was scanned for personal and secret data before publication was prepared. | Fictional text cannot show how a system handles real speech. |
| 9 | Unknown provenance is stated, not omitted. | **Applied** in the model card and the research notes. | Disclosure does not fix a gap. |

## How much is automated

Little. Scripts computed heuristics for duplication, realism and license metadata, and the exact-hash check. Reading the licenses, deciding statuses, reviewing candidate items, handling attribution and any legal assessment are manual or pending. No step approves a dataset automatically, and the policies above are only as complete as the human steps behind them.
