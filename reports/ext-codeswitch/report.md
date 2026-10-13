# Extension: code-switching (DE/FR with English pieces)

Separate suite, not part of the core 180 scenarios: 56 scenarios (16 dev / 40 test), emails with English separators, phone digits in English, NATO spelling in German, non-DE/FR names. Synthetic speech (Qwen3-TTS), clean + simulated telephone, automated QA only. Whisper large-v3-turbo through extractor rex-4 (frozen before this suite's ASR scoring; its rules come from this suite's dev split only). Test N = 40 scenarios x 2 conditions.


Synthetic speech, simulated telephone channel. All numbers come from frozen prediction files; corpus-level provisional status is tracked in IMPLEMENTATION_STATUS.md. N counts scenarios, not audio files.

## Systems

Ceiling controls: `gold-extractor` feeds the extractor the spoken gold text the TTS read (sanity check, not a ceiling for ASR: ASR emits written forms); `gold-written-extractor` feeds the written gold text, the form an ideal ASR would emit, and is the relevant ceiling for the ASR rows. `reference-agent` replays the frozen whisper-turbo transcripts, so it matches `whisper-turbo-slots` by construction; it checks persisted final state, not ASR.

| system | track | N | slot accuracy | 95% CI | coverage | macro12 clean | macro12 tel | stale-rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gold-extractor | asr_slots | 80 | 67.5 | [57.5, 77.5] | 100.0 | 67.5 | 67.5 | - |
| gold-written-extractor | asr_slots | 80 | 65.0 | [55.0, 75.0] | 100.0 | 65.0 | 65.0 | - |
| whisper-turbo-slots | asr_slots | 80 | 31.2 | [22.5, 38.8] | 100.0 | 35.0 | 27.5 | - |

## Paired degradation — gold-extractor

- N pairs: 40
- accuracy clean: 67.5
- accuracy telephone: 67.5
- delta: +0.0 percentage points
- transitions: {"fail->pass": 0, "pass->fail": 0, "pass->pass": 27, "fail->fail": 13}

### Cell matrix: locale × entity (accuracy clean / telephone)

| cell | N | clean % | telephone % |
| --- | --- | --- | --- |
| de-DE|email | 10 | 40 | 40 |
| de-DE|person_name | 10 | 20 | 20 |
| de-DE|phone | 10 | 100 | 100 |
| de-DE|reference_code | 10 | 100 | 100 |
| fr-FR|email | 10 | 60 | 60 |
| fr-FR|person_name | 10 | 20 | 20 |
| fr-FR|phone | 10 | 100 | 100 |
| fr-FR|reference_code | 10 | 100 | 100 |

## Paired degradation — gold-written-extractor

- N pairs: 40
- accuracy clean: 65.0
- accuracy telephone: 65.0
- delta: +0.0 percentage points
- transitions: {"fail->pass": 0, "pass->fail": 0, "pass->pass": 26, "fail->fail": 14}

### Cell matrix: locale × entity (accuracy clean / telephone)

| cell | N | clean % | telephone % |
| --- | --- | --- | --- |
| de-DE|email | 10 | 40 | 40 |
| de-DE|person_name | 10 | 20 | 20 |
| de-DE|phone | 10 | 100 | 100 |
| de-DE|reference_code | 10 | 100 | 100 |
| fr-FR|email | 10 | 40 | 40 |
| fr-FR|person_name | 10 | 20 | 20 |
| fr-FR|phone | 10 | 100 | 100 |
| fr-FR|reference_code | 10 | 100 | 100 |

## Paired degradation — whisper-turbo-slots

- N pairs: 40
- accuracy clean: 35.0
- accuracy telephone: 27.5
- delta: +7.5 percentage points
- transitions: {"fail->pass": 2, "pass->fail": 5, "pass->pass": 9, "fail->fail": 24}

### Cell matrix: locale × entity (accuracy clean / telephone)

| cell | N | clean % | telephone % |
| --- | --- | --- | --- |
| de-DE|email | 10 | 0 | 0 |
| de-DE|person_name | 10 | 0 | 0 |
| de-DE|phone | 10 | 100 | 40 |
| de-DE|reference_code | 10 | 40 | 40 |
| fr-FR|email | 10 | 0 | 0 |
| fr-FR|person_name | 10 | 0 | 0 |
| fr-FR|phone | 10 | 80 | 60 |
| fr-FR|reference_code | 10 | 60 | 80 |

## Error taxonomy (heuristic, revisable)

- **gold-extractor**: {"correct": 54, "name_error": 16, "local_part_error": 10}
- **gold-written-extractor**: {"correct": 52, "name_error": 16, "local_part_error": 10, "omission": 2}
- **whisper-turbo-slots**: {"correct": 25, "name_error": 20, "omission": 20, "digit_swap": 4, "domain_error": 4, "digit_error": 3, "local_part_error": 2, "code_error": 2}
