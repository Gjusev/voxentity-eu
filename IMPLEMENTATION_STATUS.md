# Implementation status

Per-phase record with real evidence. Nothing here is checked in advance; a
checkbox without evidence is debt, not a result. Everything executed is
reproducible with the listed commands.

## Conventions

- `.venv` (Python 3.11, CPU): scoring, contracts, corpus, reports.
- `.venv-gpu` (torch 2.5.1+cu121): Qwen synthesis and local Whisper (GTX 1080).
- Kaggle (T4, user gjusev): Voxtral Mini; credential only in environment
  variables, never in the repo.
- SoX required on PATH for `qwen-tts`.

## P0 — Foundations: COMPLETED

- Installable package, full CLI (exit 0/1/2/3), Pydantic contracts with
  adversarial validation, 92 offline tests green, ruff clean.
- Evidence: `python -m pytest -q` → 92 passed (79 before rex-3).

## P1 — Scorer: COMPLETED (norm-2)

- `norm-1` frozen before inference; after the adversarial audit `norm-2` was
  published with explicit changes: street-abbreviation allowlist (locale keys
  corrected), FR number-first street bis/ter suffixes, and the international
  form with repeated trunk zero («+49 (0)…»).
- Metrics with explicit denominators; paired comparisons by
  (scenario_id, condition) — fixed the collapse by scenario_id that discarded
  half the rows.
- Evidence: scorer tests + `scripts/score_all.py`.

## P2 — Cases and rights: COMPLETED (provisional corpus)

- 180 scenarios; validate without errors; input export without gold with
  opaque ids and **order by input_id** (the audit found that ordering by
  audio_id leaked split/difficulty; fixed, with a regression test).
- Audit: duplicated dev/test frame in refs fixed (1 dev clip regenerated);
  irregular German ordinals (ersten/dritten/siebten) fixed (1 test clip
  regenerated and re-scored).
- Corpus status: automated-QA/provisional (no human listening).
- Human review prepared: `python scripts/review_package.py build` generates
  review/index.html (player + target text, no ASR outputs) and
  review/review.csv; `apply --reviewer NAME` validates verdicts
  (accepted/wrong_synthesis/ambiguous/truncated, reason mandatory if not
  accepted), writes data/generated/human_review.jsonl and excludes the clean
  clip and its telephone version from scoring. «verified» only with 180/180.

## P3 — Synthesis and QA: COMPLETED

- 180 Qwen3-TTS masters fp32/sdpa GTX 1080 (~9 s/clip), 0 failures; voices
  serena/dylan 8/7 per cell, alternating by index (not by difficulty).
- 1 clip truncated by QA (0.96 s) regenerated successfully (attempt 2 recorded
  in `synthesis_prev_attempts.jsonl`).
- Reference extractor: `rex-1` frozen before inference; after the corpus
  regeneration `rex-2` was published (ordinal stems) and, after review,
  `rex-3` (written form; see «rex-2 retraction»). Rex-3 ceiling over gold:
  synthesis_text 180/180; written_text dev 60/60, test 109/120 (90.8%).

## P4 — Channel: COMPLETED

- 360/360 files accepted by automated QA (180 clean 16 kHz + 180 telephone
  8 kHz); recipe tel-1 with per-file hashes.

## P5 — Baselines and runner: COMPLETED

- Whisper large-v3-turbo (fp16, GTX 1080): 360/360 synthetic complete, 0
  failures; plus 200/200 of the human control. Fixed the language mapping
  (Whisper expects 'german'/'french'); cache invalidated and re-run.
- Voxtral Mini 3B (bf16, Kaggle T4, self-contained kernel with embedded
  package): **360/360 complete, 0 failures**. Fixed the API route
  (transcription via `apply_transcription_request`, not chat template) and the
  new mount layout (`/kaggle/input/datasets/gjusev/...`); the failed kernel
  iterations stay versioned in Kaggle (v1-v8).
- Run manifests with real hashes (or explicit provenance gaps).

## P6 — Agent and voice-evals: COMPLETED

- Reference agent over 360 inputs (frozen Whisper transcripts): 360/360 with
  observable final state; stale-value and says-but-does-not-store tests green.
- voice-evals exporter with duplicate rejection; contract test against the
  pinned local checkout (commit 3f6f9dd).

## P7 — Human control: COMPLETED

- FLEURS via official parquet export (commit resolved and recorded; no dataset
  scripts executed). 50+50 unique rows by path hash; 300 files (originals
  preserved + clean + telephone); CC-BY-4.0 attribution with modifications
  indicated.
- Whisper over human control: WER clean 0.115 vs telephone 0.221 (the
  telephone channel nearly doubles WER on human speech; denominators 2172
  words, 100 utterances per condition).

## P8 — Reports and demo: COMPLETED (measured results, rex-3)

See `reports/report.md` (regenerable offline: `python scripts/run_tracks.py`
→ `python scripts/score_all.py` → `voxentity compare …` → `voxentity report`).
Current measured numbers (test split, n=240 scenario×condition per system,
extractor rex-3, norm-2):

| system | slot accuracy | 95% CI | macro12 clean / tel |
| --- | --- | --- | --- |
| gold spoken→extractor (sanity) | 100% | [100, 100] | 100 / 100 |
| gold written→extractor (relevant ceiling) | 90.8% | [87.5, 94.2] | 90.8 / 90.8 |
| voxtral-mini→slots | 37.1% | [30.0, 43.8] | 39.2 / 35.0 |
| whisper-turbo→slots | 34.2% | [28.3, 40.4] | 36.7 / 31.7 |
| reference-agent (final state) | 34.2% | [28.3, 40.4] | 36.7 / 31.7 |

The agent re-processes the frozen Whisper transcripts, so it matches
whisper→slots by construction; it measures state persistence, not ASR.

Paired comparison whisper − voxtral (n=240, stratified bootstrap, 2000
replicas): −2.9 pp, 95% CI [−7.1, +1.3]; voxtral better in 17 pairs, whisper
in 10 — **no conclusive difference**; null result published as such.

Paired telephone channel by scenario (clean − telephone, bootstrap 95%):
whisper +5.0 pp [+0.8, +10.0] (detectable degradation), voxtral +4.2 pp
[−0.8, +9.2] (not conclusive). SVG figures in reports/figures/ (accuracy per
cell with written ceiling; paired differences with CIs).

Space (space/app.py) verified in browser with gradio 6.17: fixed 4 failures
that blocked its use (clean audio overwritten by the telephone one, missing
audio paths, case_id duplicates across conditions, missing transcripts) and
wired the deterministic example buttons from docs/08. Not deployed.

Reading: with the written ceiling at ~91%, both ASR families land at ~34–37%;
the remaining gap is mostly ASR (dictated/spelled emails, phones, names,
codes). Weakest cells: email (0–20%), phone (10–25%), DE addresses in whisper
(0%). Exception: FR postal_address has a written ceiling of only 20% on test
(test template families not covered by rules tuned on dev); that cell is
still extractor-limited and must not be read as an ASR failure. Telephone
channel: −4 to −5 pp on synthetic; on human speech WER nearly doubles
(0.115 → 0.221). Provisional corpus (automated QA, no human listening).

Synthetic WER (0.706 whisper / 0.644 voxtral) is computed against the spoken
form (synthesis_text) and counts mostly formatting differences
(«einhundertdreiundvierzig» vs «143»); against the written form it fails the
other way (one spelling = 1 token). It is not a recognition metric and is not
comparable with the human-control WER; not used as a finding.

### rex-2 retraction

The previous version of this document claimed «the bottleneck is the ASR
layer» with ~21% (whisper 20.8%, voxtral 21.2%) against a 100% ceiling. It
was wrong: the ceiling was measured only over synthesis_text (spoken form),
while ASRs emit written form. rex-2 over test written_text gave 26/120
(21.7%), the same as the ASRs: it was measuring extractor coverage (tokenizer
that dropped `+` and `@`, numeric dates, «11. Dezember», codes «MMJ-0105»,
«55a», FR street-number order). rex-3 fixes it; rex-2 numbers remain in git
history.

Dev/test discipline: the rex-3 rules were derived from dev failures
(written_text and dev ASR transcripts). During diagnosis ~15 Whisper test
transcripts were inspected; two rules were seen there first (postal code
without comma «Weg 61 37672 Ort» and dots next to «at»), though they are
general writing conventions. The rex-3 test numbers therefore have limited
test exposure and are declared as such.

## P9 — Delivery: STRUCTURE COMPLETED

- PUBLISHING.md: prior gates, `gh`/`hf` commands (syntax verified against the
  installed CLI) and communication drafts; nothing executed or sent.
- Reproduction gate: run_tracks → score_all → compare → report leaves
  reports/ identical to the commit.
- Second synthesizer: research/second-tts-gate.md (Piper, conditional).

- Official LICENSE Apache-2.0, DATA_LICENSE, THIRD_PARTY_NOTICES, dataset
  card, CONTRIBUTING, bundle validator (secrets + checksums + rights).
- External publication NOT executed (pending authorization): commands prepared
  in PUBLISHING.md (tier 1 without synthetic audio / tier 2 blocked by rights
  decision) and plan in docs/launch/LAUNCH.md.

### Delivery gates (docs/10), executed on the final commit

| gate | status | evidence |
| --- | --- | --- |
| G1 contracts | OK | pytest (all green, incl. importing every module), ruff, check_links |
| G2 rights | OK with synthetic audio blocked | registry: S04/S05/S06/S16 verified; S03 (Qwen output) and piper conditional with evidence; bundle without audio |
| G3 corpus | OK | `corpus validate`: core 180, codeswitch 56, multiturn 96, voices 240, piper 120, es 90; 0 errors |
| G4 evaluation | OK | `scripts/release_gates.py`: 5 core runs 240/240, complete, coverage 100% |
| G5 honesty | OK | scan for prohibited claims; synthetic/simulated/provisional/N in README, card, reports, Space and figure |
| G6 reproduction | OK | offline regeneration of core + 5 extensions byte-identical (`reports/release_gates.md`) |
| G7 product | OK | Space tested in browser in full and tier 1 (no audio) mode |
| G8 publication | PENDING by design | no real URLs until publishing; notices and dataset card match the bundle |

Findings from this pass, fixed: 4 extension suites failed validation
(validator assumed the core layout) and 40 multi-turn turn labels were wrong;
`ext/codeswitch.py` broken since the ES refactor (nothing imported it; new
import test); S03 `license_url` pointed to a nonexistent LICENSE; PUBLISHING.md
uploaded synthetic audio against the rights registry; launch drafts with
excessive claims.

## Adversarial audit

26-agent workflow (4 dimensions × refutation verification): 22 confirmed
findings, all fixed in commits labeled «audit fixes» and «rex-2». A later
review found the rex-2 ceiling circular (see «rex-2 retraction»); fixed in
rex-3. Findings and their resolution are in git history.

## Blockages and limitations

- Human listening of the corpus: pending → corpus «provisional», not «verified».
- Synthetic audio rights: conditional (see DATA_LICENSE.md).
- Transcripts entirely unrelated to the text (e.g. FR emails turned into
  unrelated sentences) do not allow distinguishing TTS failure from ASR
  failure without listening; listening of a sample is required.
- Voxtral: completed and scored; the local bundle `release_bundle/` passes
  `release validate` (no credentials, checksums verified).
- HF Space and dataset: local artifacts ready; external publication requires
  explicit authorization.

## Extensions (separate suites; never mixed with the core tables)

All of them: synthetic speech, simulated telephone channel, automated QA only,
Whisper large-v3-turbo → extractor rex-4 (frozen before scoring ASR in each
suite; its rules come from dev). Data in `data/ext/<suite>/`, reports in
`reports/ext-<suite>/`, CPU scoring with `python scripts/ext_suites.py <suite>`.

### Code-switching (`codeswitch`): COMPLETED

- 56 DE/FR scenarios (16 dev / 40 test) with English separators and digits,
  NATO alphabet in German and non-DE/FR names; values disjoint from the core.
- rex-3 frozen failed 16/56 on the correct written text; rex-4 fixes the dev
  failures (whole-word correction markers: «manon» was being cut to «non»;
  dot/underscore/dash and English digits; O' surnames;
  «double vé»/«i grec»). Core: 0 changes in 720 predictions.
- Test: whisper 31.2% [22.5, 38.8] against a written ceiling 65.0% [55.0, 75.0];
  phones with English digits 70%; email and names extractor-limited
  (ceiling 20-40%).

### Cross-turn corrections (`multiturn`): COMPLETED

- 48 DE/FR cases × 2 turns (same voice): correction (near-identical value),
  confirmation, repetition; 96 clips, 0 failures; whisper 192/192.
- Test (n=64): final state 42.2% [29.7, 54.7]; gold-text ceiling 100%.
  0 stale values; 19/19 correct when both turns extract well: persistence
  works and the loss is perception. 2 real spurious changes (a misheard
  repetition overwrote a correct value).
- Outcome rule corrected before publishing: a misheard turn 1 that turn 2
  does not touch is a wrong value, not a spurious change (the first pass
  mislabeled 8); test pins the rule.

### More voices (`voices`): COMPLETED

- Motivation (coverage analysis): in the core dylan beats serena by ~10 pp
  with both ASRs, but voice and scenario were confounded.
- All 120 test scenarios with vivian and ryan (240 clips, 0 failures, 480 QA
  ok, whisper 480/480). vivian − ryan paired +0.8 pp [−3.3, +5.0]. The
  serena/dylan gap splits into ~3 pp of scenario difficulty and ~7 pp of voice.

### Second TTS family (`piper`): COMPLETED

- Gate: research/second-tts-gate.md. Piper voices pinned (thorsten CC0,
  siwis CC BY 4.0 verified in the dataset license); GPL runtime in an isolated
  venv, not a package dependency. 120/120 synthesized, 240 QA ok,
  whisper 240/240.
- Qwen − Piper paired −10.0 pp [−15.4, −4.2] (Piper 44.2% vs 34.2%);
  phones 15% → 70% (DE) and 55% (FR); emails ~0% with both. The absolute core
  figures depend on the synthesizer (warned in README).

### Spanish (`es`): COMPLETED

- 90-scenario suite (30 dev / 60 test) in `data/ext/es/generated/`,
  hash `fd8762328c78df8fe8aa5f598be7c9482f36c16a35fff6fad407c1bdaf345701`.
  Text phase done on the ext-es branch by the other instance and verified
  independently here (suite green; 0 changes in the 720 core predictions and
  0/112 code-switching with its extractor); merged fast-forward.
- Spanish Qwen3-TTS smoke passed (serena and dylan; exact Whisper round-trip).
  90/90 synthesized, 180 clips QA ok, whisper (language 'spanish') 180/180.
- Test (60 scenarios × 2 conditions): whisper 50.8% [41.7, 60.0] against a
  written ceiling 96.7% [91.7, 100.0] and spoken 95.0%. Cells: dates 90%,
  codes 75%, names 60%, phones 60%, addresses 20%, emails 0%. Clean −
  telephone +8.3 pp. Not directly comparable with DE/FR (34.2%): different
  scenarios and templates; only the pattern matches (emails 0% in all three
  languages).

### Commercial providers: BLOCKED

- Requires an explicit provider and budget (AGENTS.md: this brief does not
  authorize paid inference). Not started.

## Publication decision (owner) and advice

- Owner: "everything public". Recorded in the rights registry: S03 (Qwen3-TTS
  audio) and S17 (Piper voices) `verified` as an owner decision over the
  license evidence (Apache-2.0 without output terms; CC0 / CC BY 4.0), with a
  takedown path via GitHub issues. Not a legal opinion.
- Advice (independent perspectives): Munger, Taleb and Torvalds → publish
  everything, with the decision recorded, takedown contact and order
  GitHub → CI green → clean clone → HF; Kahneman → listen first. Taleb and
  Kahneman: hold the announcement (post) until a listening spot check.
- Automated synthesis-failure alert (`scripts/tts_alert.py`, alert and not
  filter): 7/180 clean clips with both ASRs far from the written and spoken
  text (email 2, phone 3, address 1, code 1); none excluded from scoring.
- Technical risks of the advice resolved before publishing: `.gitattributes`
  (LF), 8 build logs removed from the index, gradio pinned to the tested
  version (6.17.3) in requirements and Space frontmatter, absolute links to
  GitHub in the dataset card and Space README, no secrets or local paths.
