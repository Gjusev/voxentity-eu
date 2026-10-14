# Publication and professional evidence

## Final public README

Explain task and synthetic corpus in one sentence; show an audible example and a measured table with N and CI; give a reproducible CPU command; link dataset, notebook and demo. State what was implemented and what is extension. Replace placeholder links only after verified publication.

## Hugging Face Dataset

User namespace verified during preflight; proposed name voxentity-eu. Independent configs synthetic_core and human_control; dev/test splits and condition column. No artificial train split. PCM audio published as WAV/FLAC with explicit sampling rate and hashes of the served file.

Dataset card: composition, source, labels, generation, voices, versions, transform, QA, splits, licenses, limitations and unsupported uses. Explain that public test references may contaminate future models.

Publishing weights is never required. Version releases with the manifest SHA and checksum list. Keep a history of label corrections.

## CPU Space

English interface: language, entity, condition, system and error-type selectors; clean/telephone players synchronized per case; gold, transcript, captured slot and score. Show QA status and synthetic/human source near the audio.

Load frozen results table, paginate, offer downloadable CSV/JSON and the exact link to a case. Buttons for correct and error example, deterministic selection. Do not show invented values when there are no results: explicit empty state. No user-data forms or open generation needed.

Testing: loads without GPU/token, coherent filters, keyboard navigation, accessible transcript, legible names, visible audio failure, paths restricted to the bundle.

## Technical report

Questions: how much does accuracy change per condition; which entities fail; how much error does extraction add; whether corrections reach the stored state; whether ASR degradation also appears in human control.

Graphs: accuracy per entity/language with N; paired delta and CI; pass/fail matrix clean→telephone. A WER vs slot-accuracy plot illustrates discrepancies when data allows.

Include corpus/models/configs, prompts, operational failures, QA exclusions, intervals and limitations. Separate hypotheses from findings. Do not attribute an error to the language, gender or accent of real people based on synthetic voices.

## Release review

Run the checklist in docs/10-validation.md. Prepare GitHub/HF/Kaggle commands/scripts and create the local release bundle. The current brief creates a local repo and plan; effective external publication requires the implementation brief to include it. Do not send messages to third parties automatically.

Confirm a logged-out visitor sees permitted files and can load notebook/Space. Store verified release URLs in RELEASE_MANIFEST.json.

## Job-search use

Prepare a public technical case and a short demo backed by real results. CV template without fictitious figures:
'Built VoxEntity-EU, an open German/French spoken-entity benchmark; evaluated [systems] across [independent scenarios] with paired telephone-channel simulations, publishing reproducible results and final-slot failure analysis.'

Draft optional messages for voice teams with finding, impact and reproducible link; keep them as drafts. Prioritize checkable evidence and clarity of limits. Do not promise interviews, score job impact as science nor use stars as a success metric.

## Additional documentation

CONTRIBUTING: add models without seeing gold, licensed cases, corrections and test execution.
DATA_LICENSE: rights per component and notices.
REPORT: real results only.
MODEL_ADAPTERS: capabilities, limitations and format.
IMPLEMENTATION_STATUS: complete/blocked/not started with evidence.
