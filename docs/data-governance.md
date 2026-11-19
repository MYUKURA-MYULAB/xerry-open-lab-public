# Data governance decisions

These are the methodological rules we apply when considering any external dataset. They are decisions about process. This repository does not list candidate datasets, their licenses, counts or any sample of third-party text. Its only data is fictional text written for the tests (see [examples](../examples/synthetic-data-es/README.md)).

| # | Decision | Rule | Reason | Limit |
|---|---|---|---|---|
| 1 | Evidence of license | The license is read from the primary source (the repository, the publisher's record) and recorded with date and location. A secondary summary is not enough. | Mirrors and catalog cards drift from the original terms. | A primary source can itself be ambiguous. |
| 2 | Missing or conflicting terms | They are treated as no permission until resolved. Where sources disagree, the more restrictive reading applies and the conflict is logged. | Silence is not consent, and the cost of a wrong yes is higher than a delay. | Slows adoption; a resolved conflict needs the rights holder. |
| 3 | Status of each source | One of: usable with conditions, blocked, reference only, or pending legal review. Non-commercial terms mean reference only. | A fixed vocabulary stops informal exceptions. | Statuses are our reading of the terms, not a legal determination. |
| 4 | Automation is triage | Heuristics for duplication, realism and license route items, and a person reviews before anything is promoted. | Heuristics have unmeasured error rates. | Review capacity limits throughput. |
| 5 | Evaluation material is kept apart | Protected evaluation items are registered by content hash. Candidate material is checked against the registry for exact matches, and a semantic-overlap check needs a custodian's attestation. Until it is given, promotion is blocked. Protected items are never used to build, prompt or tune a system or to generate material for them. | Contamination makes a benchmark measure memory. | Hashes miss paraphrases; the semantic check is slower and depends on a person. |
| 6 | Obligations travel with the data | For attribution licenses, record creator, license location, source location and a notice of modification. Share-alike terms are tracked as they propagate to derivatives. | Obligations are easy to lose once data is transformed. | Tracking is manual. |
| 7 | Sample instead of copy | Sources are inspected through small, distributed samples with a fixed random seed. Large corpora are not copied into deliverables. | Limits exposure and makes the inspection repeatable. | A sample can miss rare problems. |
| 8 | No personal data here | Every example in this repository is fictional text written for its test. No recordings, identifiable transcripts or clinical records are published. | Consent and de-identification cannot be verified after publication. | Fictional text cannot show how a system handles real speech. |
| 9 | Gaps are reported | Unknown provenance is stated, for example in the model card, instead of omitted. | A reader can only discount what is disclosed. | Disclosure does not fix the gap. |

## Status

The process above is a triage, not legal advice. Legal review of the rights involved is pending, the semantic-overlap check in decision 5 is pending, and we have not measured how often the hash check misses a paraphrased duplicate.
