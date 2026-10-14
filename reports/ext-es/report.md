# Extension: Spanish (es-ES)

Separate suite, not part of the core DE/FR corpus: 90 scenarios (30 dev / 60 test), same six entity types and difficulty mix as the core. Synthetic speech (Qwen3-TTS voices serena/dylan, language 'spanish'), clean + simulated telephone, automated QA only. Whisper large-v3-turbo (language 'spanish') through extractor rex-4, whose Spanish rules were tuned on the Spanish dev split only, before any Spanish audio existed. Test N = 60 scenarios x 2 conditions.


Synthetic speech, simulated telephone channel. All numbers come from frozen prediction files; corpus-level provisional status is tracked in IMPLEMENTATION_STATUS.md. N counts scenarios, not audio files.

## Systems

Ceiling controls: `gold-extractor` feeds the extractor the spoken gold text the TTS read (sanity check, not a ceiling for ASR: ASR emits written forms); `gold-written-extractor` feeds the written gold text, the form an ideal ASR would emit, and is the relevant ceiling for the ASR rows. `reference-agent` replays the frozen whisper-turbo transcripts, so it matches `whisper-turbo-slots` by construction; it checks persisted final state, not ASR.

| system | track | N | slot accuracy | 95% CI | coverage | macro12 clean | macro12 tel | stale-rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gold-extractor | asr_slots | 120 | 95.0 | [90.0, 100.0] | 100.0 | 95.0 | 95.0 | 0.0 |
| gold-written-extractor | asr_slots | 120 | 96.7 | [91.7, 100.0] | 100.0 | 96.7 | 96.7 | 0.0 |
| whisper-turbo-slots | asr_slots | 120 | 50.8 | [41.7, 60.0] | 100.0 | 55.0 | 46.7 | 0.0 |

## Paired degradation — gold-extractor

- N pairs: 60
- accuracy clean: 95.0
- accuracy telephone: 95.0
- delta: +0.0 percentage points
- transitions: {"fail->pass": 0, "pass->fail": 0, "pass->pass": 57, "fail->fail": 3}

### Cell matrix: locale × entity (accuracy clean / telephone)

| cell | N | clean % | telephone % |
| --- | --- | --- | --- |
| es-ES|calendar_value | 20 | 100 | 100 |
| es-ES|email | 20 | 80 | 80 |
| es-ES|person_name | 20 | 100 | 100 |
| es-ES|phone | 20 | 100 | 100 |
| es-ES|postal_address | 20 | 90 | 90 |
| es-ES|reference_code | 20 | 100 | 100 |

## Paired degradation — gold-written-extractor

- N pairs: 60
- accuracy clean: 96.7
- accuracy telephone: 96.7
- delta: +0.0 percentage points
- transitions: {"fail->pass": 0, "pass->fail": 0, "pass->pass": 58, "fail->fail": 2}

### Cell matrix: locale × entity (accuracy clean / telephone)

| cell | N | clean % | telephone % |
| --- | --- | --- | --- |
| es-ES|calendar_value | 20 | 100 | 100 |
| es-ES|email | 20 | 80 | 80 |
| es-ES|person_name | 20 | 100 | 100 |
| es-ES|phone | 20 | 100 | 100 |
| es-ES|postal_address | 20 | 100 | 100 |
| es-ES|reference_code | 20 | 100 | 100 |

## Paired degradation — whisper-turbo-slots

- N pairs: 60
- accuracy clean: 55.0
- accuracy telephone: 46.7
- delta: +8.3 percentage points
- transitions: {"fail->pass": 0, "pass->fail": 5, "pass->pass": 28, "fail->fail": 27}

### Cell matrix: locale × entity (accuracy clean / telephone)

| cell | N | clean % | telephone % |
| --- | --- | --- | --- |
| es-ES|calendar_value | 20 | 90 | 90 |
| es-ES|email | 20 | 0 | 0 |
| es-ES|person_name | 20 | 60 | 60 |
| es-ES|phone | 20 | 60 | 60 |
| es-ES|postal_address | 20 | 30 | 10 |
| es-ES|reference_code | 20 | 90 | 60 |

## Error taxonomy (heuristic, revisable)

- **gold-extractor**: {"correct": 114, "local_part_error": 4, "address_component_loss": 2}
- **gold-written-extractor**: {"correct": 116, "local_part_error": 4}
- **whisper-turbo-slots**: {"correct": 61, "omission": 27, "address_component_loss": 8, "name_error": 8, "digit_error": 7, "digit_swap": 4, "local_part_error": 3, "missing_prefix": 2}
