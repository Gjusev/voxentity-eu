# Changelog

Versions, not dates (project policy). Scorer and extractor rule sets are
versioned separately because a change in either moves reported numbers.

## 0.1.0 (unreleased, local)

### Corpus and data
- Core: 180 DE/FR synthetic scenarios (60 dev / 120 test), Qwen3-TTS voices
  serena/dylan, clean 16 kHz + simulated telephone 8 kHz; automated QA only.
- Human-speech control: FLEURS DE/FR, 100 utterances per condition, CC-BY-4.0.
- Extension suites, each with its own data and report: `codeswitch` (56),
  `multiturn` (48 two-turn cases), `voices` (core test re-voiced by vivian and
  ryan), `piper` (core test, second TTS family), `es` (90 Spanish scenarios).

### Scorer
- `norm-2`: street-abbreviation allowlist keyed per locale, FR bis/ter house
  numbers, "+49 (0)…" international form. Paired comparisons key on
  (scenario, condition).

### Reference extractor
- `rex-4`: correction markers match whole words; English separators and digit
  words; Irish O' surnames; French two-word letter names; Spanish rules (dev).
  Core predictions unchanged versus rex-3 (0 of 720 differ).
- `rex-3`: parses the written forms ASR systems emit (+49…, emails, numeric
  dates, 11. Dezember, MMJ-0105, 55a, FR street-first addresses).
- `rex-2` (retracted conclusion): exercised only on the spoken gold text, so its
  100% ceiling was circular; the "ASR bottleneck" reading based on it was
  wrong. Details in IMPLEMENTATION_STATUS.md.

### Release tooling
- Release bundle with checksums, nested extension runs, extension gold, no
  audio; `release validate`; `scripts/release_gates.py` (G4, G6) with versioned
  evidence in `reports/release_gates.md`.
- Corpus validation is suite-aware (core layout vs each extension's declared size).
