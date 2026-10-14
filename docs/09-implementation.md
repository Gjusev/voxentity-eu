# Implementation backlog

Order by dependencies, no calendar. A checked box cites its evidence; writing documentation does not mean having implemented functionality.

## P0 — Foundations

- [x] Create pyproject, package, CLI and separate extras; choose lock tool and record the decision. — evidence: pyproject + CLI `voxentity`, extras tts/asr-*/space; lock `uv-core.lock`.
- [x] Implement schemas and validate examples. — evidence: contracts.py; tests/unit/test_contracts.py.
- [x] Create tests for IDs, paths, types, duplicates and gold isolation. — evidence: tests/unit/test_contracts.py, test_corpus.py.
- [x] Add offline CPU CI, lint and internal link validation. — evidence: `.github/workflows/ci.yml` (ruff, scripts/check_links.py, pytest over uv-core.lock).
Acceptance: clean install, import without torch/GPU/network; CLI help and examples parseable; adversarial tests pass.

## P1 — Scorer

Depends on P0.
- [x] Per-entity normalization with literal/canonical separated. — evidence: scoring/normalize.py (norm-2); test_normalize.py.
- [x] Scoring with failures, omission, substitution, extras and corrections. — evidence: scoring/match.py; outcomes in runs/scored/*.json.
- [x] Aggregation, paired comparison and cluster intervals. — evidence: scoring/aggregate.py + bootstrap.py; `voxentity compare` (test_compare_cli.py).
- [x] Fixtures with hand-calculated results and negative controls. — evidence: tests/unit/test_normalize.py.
Acceptance: one-digit/accent errors are detected; global rates keep denominators; incomplete runs unranked; CPU-repeatable report.

## P2 — Cases and rights

Depends on P0.
- [x] Write original DE/FR pools and templates, 180-case matrix. — evidence: corpus/pools.py; 180 scenarios.
- [x] Split 60 dev/120 test without overlap of equivalent family/values. — evidence: corpus validate without errors; test_corpus.py.
- [x] Manifest of sources and rights checklist per asset. — evidence: rights_registry.jsonl.
- [x] Export of inputs without gold and opaque IDs. — evidence: data/inputs (opaque ids, order by input_id).
Acceptance: exact counts, difficulty and voice balance, semantic validation of corrections, no development dates added.

## P3 — Synthesis and QA

Depends on P2.
- [x] Resolve Qwen and speaker IDs; smoke test per language/voice. — evidence: scripts/smoke_tts.py; data/smoke_tts/report*.json.
- [x] Resumable generator, provenance, hashes and attempt logs. — evidence: synthesis.jsonl + synthesis_prev_attempts.jsonl.
- [ ] QA automation, available audio review flow and exclusion flow. — QA automation and exclusion flow ready (`review_package.py apply`: verdict with reason, clean + telephone clip excluded from scoring, gold intact); the human listening itself is missing.
- [x] Review package for pending cases. — evidence: `scripts/review_package.py build` (review/index.html + review.csv, 180 clean clips, no ASR outputs).
Acceptance: 180 clean accepted for verified or explicit provisional state; TTS errors not labeled as ASR errors; no filter based on evaluated-model results.

## P4 — Channel

Depends on P3.
- [x] Implement pinned recipe, seeded noise, codec and audio checks. — evidence: audio/channel.py tel-1; test_channel.py.
- [x] Generate 180 pairs and verify relations. — evidence: 360/360 QA accepted (qa.jsonl).
Acceptance: 360 valid files when P3 complete; sample rates and hashes match; band/SNR test without assuming real latency.

## P5 — Baselines and runner

Depends on P1/P4.
- [x] Doctor Kaggle/HF; locks and smoke tests per backend. — evidence: doctor.py profiles hf/kaggle.
- [x] Whisper and Voxtral adapters, resume, timeouts and cache. — evidence: adapters/whisper.py, voxtral.py.
- [x] Common extractor and gold→extractor control. — evidence: rex-3; spoken ceiling 100% and written 90.8% (test).
- [x] Full runs with isolated inputs. — evidence: whisper 360/360, voxtral 360/360.
Acceptance: at least two ASR families actually run; per-clip artifacts; comparison with same cohort; OOM/error not hidden.

## P6 — Persisted slots and voice-evals

Depends on P5.
- [x] Reference agent and instrumented storage. — evidence: adapters/agent.py; tests/integration/test_agent.py.
- [x] Correction within the turn; stale-value negative control. — evidence: tests/integration/test_agent.py.
- [x] Export fixtures separated by voice/condition and explicit 8→16 kHz conversion. — evidence: adapters/voice_evals_export.py (8→16 kHz explicit).
- [x] Contract test against pinned voice-evals version. — evidence: tests/contract/test_voice_evals.py (commit 3f6f9dd).
Acceptance: scorer reads real final state; replay does not fabricate timings; duplicated text does not overwrite audio; core works without voice-evals installed.

## P7 — Human control and sensitivity

Depends on P1/P5.
- [x] Selective FLEURS download by revision, IDs and attribution. — evidence: data/human_control/attribution.json.
- [x] Deterministic sampling 50 per language and acoustic versions. — evidence: human_control_manifest.jsonl.
- [x] Separate WER/CER evaluation. — evidence: runs/scored/human_control_wer.json.
- [x] Investigate/implement second synthesizer only if rights resolved; report the gate. — evidence: research/second-tts-gate.md (Piper thorsten CC0 + siwis CC-BY 4.0, pinned revision; conditional state, not executed).
Acceptance: human control executed or verifiable blockage without false recruitment; all tables distinguish corpus; TTS alternative does not block the core release.

## P8 — Reports and demo

Depends on P5/P6; integrate P7 when available.
- [x] Tables, bootstrap, error taxonomy and report in English. — evidence: reports/report.md.
- [x] CPU Space of precomputed results. — evidence: space/app.py + scripts/build_space_data.py (not deployed).
- [x] Generation, evaluation and reproduction notebooks. — evidence: notebooks/*; reproduce verified identical to the bundle.
Acceptance: demo reproduces report numbers, correct audio per ID, no numeric placeholder presented as a finding.

## P9 — Publishable delivery

Depends on P8.
- [x] Official licenses, notices, dataset card, README and CONTRIBUTING. — evidence: LICENSE, DATA_LICENSE.md, THIRD_PARTY_NOTICES.md, dataset_card/, CONTRIBUTING.md.
- [x] Bundle with checksums, manifest and release controls. — evidence: release.py build_bundle; `release validate` ok; test_release.py.
- [x] Publication commands and communication drafts. — evidence: PUBLISHING.md (gates, `gh`/`hf` commands verified against the installed CLI, drafts; nothing executed) and space/README.md (HF metadata).
- [x] Update IMPLEMENTATION_STATUS with executed commands/evidence. — evidence: IMPLEMENTATION_STATUS.md.
Acceptance: fresh-environment offline scoring identical, no credentials, rights resolved for published assets, names and claims coherent.

## Extensions after the core

- [ ] Two voice providers with access and budget, verifiable final state. — blocked: requires explicit provider and budget.
- [x] Cross-turn corrections and code-switching. — evidence: reports/ext-multiturn/report.md, reports/ext-codeswitch/report.md (own suites in data/ext/).
- [x] Spanish and new corpus version. — evidence: es suite (90 scenarios, data/ext/es/generated) and reports/ext-es/report.md; DE/FR corpus intact.
- [x] More voices/cases if analysis shows insufficient coverage. — evidence: coverage analysis (voice effect confused with scenario) → reports/ext-voices/report.md; also second TTS family in reports/ext-piper/report.md.

Each extension has its own suite. Do not inflate main corpus size nor complete checkboxes with mocks.
