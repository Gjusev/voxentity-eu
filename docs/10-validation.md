# Validation and gates

## Critical tests

| Area | Case | Expected |
| --- | --- | --- |
| Normalization | phone loses leading zero | incorrect |
| Normalization | ß vs ss, é vs e | different unless pre-declared variant |
| Normalization | code O vs 0 | incorrect |
| Email | domain/character change | incorrect |
| Correction | returns first mention | stale and incorrect |
| Calendar | requested component missing | incorrect; no gold inference |
| Address | street right, number wrong | slot incorrect |
| Integrity | duplicated row/unknown ID | run error |
| Integrity | timeout with valid ID | counts as failure |
| Integrity | prediction missing | incomplete run, no ranking |
| Gold | filename includes answer | inputs rejection |
| Split | pair in dev and test | corpus rejection |
| Audio | master/telephone without valid parent | rejection |
| Audio | right extension but corrupt bytes | rejection |
| Statistics | duplicated variants | does not increase independent N |
| Bootstrap | same seed/data | same result |
| Resumption | model/prompt/hash change | cache not reused |
| Agent | says correct value but does not store it | agent_slots failure |
| voice-evals | repeated texts in same manifest | rejection |
| Space | different table and audio | test fails |
| Publication | model/license/QA unresolved | blocked asset or explicit provisional |

Do not test ASR against a guaranteed answer: software regressions use fixtures; real models produce measured results, not an arbitrary accuracy gate.

## Delivery gates

G1 Contracts: schemas/examples/tests and semantics aligned.
G2 Rights: complete registry and authorized assets per evidence; pending ones excluded from the publishable bundle.
G3 Corpus: counts, splits, hashes, pairs, voices, QA and exclusions visible.
G4 Evaluation: two baselines, gold extractor, observed agent states; each run with cohort and failures.
G5 Honesty: synthetic/provisional/human control/mock differentiated in all media.
G6 Reproduction: tables regenerated offline from frozen results.
G7 Product: CPU Space opens, filters/audio/downloads work.
G8 Publication: real links, notices and dataset card match the bundle.

For each gate store the command, output summary and artifact paths. A failed gate does not require deleting work; it blocks the corresponding claim.

## Risks and contingency decisions

- Invalid TTS pronunciation: fix the recipe and re-run QA; keep the exclusion and attempt.
- No competent listener: provisional release, not verified.
- Only one TTS family: declare the limitation; do not extrapolate to humans.
- FLEURS known to models: use as control, not a generalization ranking.
- No GPU: complete scorer, UI and notebooks; inference explicitly pending.
- No external credentials: open results first, optional providers pending.
- Uncertain rights: do not distribute the affected audio; prepare own scripts/data and record the blockage.
- Results without differences: publish null results; do not change the test to manufacture a failure.
- Few cases per cell: CIs, counts and exploratory analysis, no universal claims.
- Normalization disagreement: publish literal and canonical, freeze the policy before inference.
