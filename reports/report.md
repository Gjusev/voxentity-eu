# VoxEntity-EU measured results

Synthetic speech, simulated telephone channel. All numbers come from frozen prediction files; corpus-level provisional status is tracked in IMPLEMENTATION_STATUS.md. N counts scenarios, not audio files.

## Systems

Ceiling controls: `gold-extractor` feeds the extractor the spoken gold text the TTS read (sanity check, not a ceiling for ASR: ASR emits written forms); `gold-written-extractor` feeds the written gold text, the form an ideal ASR would emit, and is the relevant ceiling for the ASR rows. `reference-agent` replays the frozen whisper-turbo transcripts, so it matches `whisper-turbo-slots` by construction; it checks persisted final state, not ASR.

| system | track | N | slot accuracy | 95% CI | coverage | macro12 clean | macro12 tel | stale-rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gold-extractor | asr_slots | 240 | 100.0 | [100.0, 100.0] | 100.0 | 100.0 | 100.0 | 0.0 |
| gold-written-extractor | asr_slots | 240 | 90.8 | [87.5, 94.2] | 100.0 | 90.8 | 90.8 | 0.0 |
| reference-agent | asr_slots | 240 | 34.2 | [28.3, 40.4] | 100.0 | 36.7 | 31.7 | 0.0 |
| voxtral-mini-slots | asr_slots | 240 | 37.1 | [30.0, 43.8] | 100.0 | 39.2 | 35.0 | 0.0 |
| whisper-turbo-slots | asr_slots | 240 | 34.2 | [28.3, 40.4] | 100.0 | 36.7 | 31.7 | 0.0 |

## Figures

![Slot accuracy by cell](figures/cell_accuracy.svg)

Bars: exact slot accuracy per locale × entity cell (values in the 12-cell tables below). Gray tick: extractor fed the written gold text; where bars sit far below it the loss is ASR, where the tick itself is low the extractor is the limit.

![Paired differences](figures/paired_deltas.svg)

| comparison | Δ pp | 95% CI | n |
| --- | --- | --- | --- |
| Whisper turbo − Voxtral Mini (both conditions) | -2.9 | [-7.1, +1.3] | 240 |
| Whisper turbo: clean − telephone | +5.0 | [+0.8, +10.0] | 120 |
| Voxtral Mini: clean − telephone | +4.2 | [-0.8, +9.2] | 120 |

## Paired degradation — gold-extractor

- N pairs: 120
- accuracy clean: 100.0
- accuracy telephone: 100.0
- delta: +0.0 percentage points
- transitions: {"fail->pass": 0, "pass->fail": 0, "pass->pass": 120, "fail->fail": 0}

### 12-cell matrix (accuracy clean / telephone)

| cell | N | clean % | telephone % |
| --- | --- | --- | --- |
| de-DE|calendar_value | 20 | 100 | 100 |
| de-DE|email | 20 | 100 | 100 |
| de-DE|person_name | 20 | 100 | 100 |
| de-DE|phone | 20 | 100 | 100 |
| de-DE|postal_address | 20 | 100 | 100 |
| de-DE|reference_code | 20 | 100 | 100 |
| fr-FR|calendar_value | 20 | 100 | 100 |
| fr-FR|email | 20 | 100 | 100 |
| fr-FR|person_name | 20 | 100 | 100 |
| fr-FR|phone | 20 | 100 | 100 |
| fr-FR|postal_address | 20 | 100 | 100 |
| fr-FR|reference_code | 20 | 100 | 100 |

## Paired degradation — gold-written-extractor

- N pairs: 120
- accuracy clean: 90.8
- accuracy telephone: 90.8
- delta: +0.0 percentage points
- transitions: {"fail->pass": 0, "pass->fail": 0, "pass->pass": 109, "fail->fail": 11}

### 12-cell matrix (accuracy clean / telephone)

| cell | N | clean % | telephone % |
| --- | --- | --- | --- |
| de-DE|calendar_value | 20 | 100 | 100 |
| de-DE|email | 20 | 100 | 100 |
| de-DE|person_name | 20 | 100 | 100 |
| de-DE|phone | 20 | 100 | 100 |
| de-DE|postal_address | 20 | 80 | 80 |
| de-DE|reference_code | 20 | 100 | 100 |
| fr-FR|calendar_value | 20 | 100 | 100 |
| fr-FR|email | 20 | 90 | 90 |
| fr-FR|person_name | 20 | 100 | 100 |
| fr-FR|phone | 20 | 100 | 100 |
| fr-FR|postal_address | 20 | 20 | 20 |
| fr-FR|reference_code | 20 | 100 | 100 |

## Paired degradation — reference-agent

- N pairs: 120
- accuracy clean: 36.7
- accuracy telephone: 31.7
- delta: +5.0 percentage points
- transitions: {"fail->pass": 2, "pass->fail": 8, "pass->pass": 36, "fail->fail": 74}

### 12-cell matrix (accuracy clean / telephone)

| cell | N | clean % | telephone % |
| --- | --- | --- | --- |
| de-DE|calendar_value | 20 | 90 | 90 |
| de-DE|email | 20 | 10 | 0 |
| de-DE|person_name | 20 | 70 | 60 |
| de-DE|phone | 20 | 10 | 20 |
| de-DE|postal_address | 20 | 0 | 0 |
| de-DE|reference_code | 20 | 50 | 50 |
| fr-FR|calendar_value | 20 | 80 | 70 |
| fr-FR|email | 20 | 0 | 0 |
| fr-FR|person_name | 20 | 30 | 20 |
| fr-FR|phone | 20 | 20 | 10 |
| fr-FR|postal_address | 20 | 20 | 20 |
| fr-FR|reference_code | 20 | 60 | 40 |

## Paired degradation — voxtral-mini-slots

- N pairs: 120
- accuracy clean: 39.2
- accuracy telephone: 35.0
- delta: +4.2 percentage points
- transitions: {"fail->pass": 3, "pass->fail": 8, "pass->pass": 39, "fail->fail": 70}

### 12-cell matrix (accuracy clean / telephone)

| cell | N | clean % | telephone % |
| --- | --- | --- | --- |
| de-DE|calendar_value | 20 | 90 | 90 |
| de-DE|email | 20 | 20 | 20 |
| de-DE|person_name | 20 | 70 | 60 |
| de-DE|phone | 20 | 30 | 20 |
| de-DE|postal_address | 20 | 30 | 30 |
| de-DE|reference_code | 20 | 40 | 30 |
| fr-FR|calendar_value | 20 | 80 | 80 |
| fr-FR|email | 20 | 10 | 0 |
| fr-FR|person_name | 20 | 30 | 20 |
| fr-FR|phone | 20 | 10 | 10 |
| fr-FR|postal_address | 20 | 20 | 20 |
| fr-FR|reference_code | 20 | 40 | 40 |

## Paired degradation — whisper-turbo-slots

- N pairs: 120
- accuracy clean: 36.7
- accuracy telephone: 31.7
- delta: +5.0 percentage points
- transitions: {"fail->pass": 2, "pass->fail": 8, "pass->pass": 36, "fail->fail": 74}

### 12-cell matrix (accuracy clean / telephone)

| cell | N | clean % | telephone % |
| --- | --- | --- | --- |
| de-DE|calendar_value | 20 | 90 | 90 |
| de-DE|email | 20 | 10 | 0 |
| de-DE|person_name | 20 | 70 | 60 |
| de-DE|phone | 20 | 10 | 20 |
| de-DE|postal_address | 20 | 0 | 0 |
| de-DE|reference_code | 20 | 50 | 50 |
| fr-FR|calendar_value | 20 | 80 | 70 |
| fr-FR|email | 20 | 0 | 0 |
| fr-FR|person_name | 20 | 30 | 20 |
| fr-FR|phone | 20 | 20 | 10 |
| fr-FR|postal_address | 20 | 20 | 20 |
| fr-FR|reference_code | 20 | 60 | 40 |

## Error taxonomy (heuristic, revisable)

- **gold-extractor**: {"correct": 240}
- **gold-written-extractor**: {"correct": 218, "address_component_loss": 20, "omission": 2}
- **reference-agent**: {"correct": 82, "omission": 70, "digit_error": 26, "name_error": 22, "address_component_loss": 17, "digit_swap": 6, "calendar_component_loss": 6, "missing_prefix": 5, "domain_error": 3, "local_part_error": 2, "code_error": 1}
- **voxtral-mini-slots**: {"correct": 89, "omission": 49, "digit_error": 29, "name_error": 21, "address_component_loss": 18, "digit_swap": 10, "local_part_error": 8, "calendar_component_loss": 6, "missing_prefix": 4, "code_error": 3, "domain_error": 2, "accent_loss": 1}
- **whisper-turbo-slots**: {"correct": 82, "omission": 70, "digit_error": 26, "name_error": 22, "address_component_loss": 17, "digit_swap": 6, "calendar_component_loss": 6, "missing_prefix": 5, "domain_error": 3, "local_part_error": 2, "code_error": 1}

## Human control (FLEURS, known corpus)

FLEURS is likely present in ASR training data; this control measures channel transfer on human speech, not generalization.
- wer_clean: 0.1151012891344383  (denominator 2172, 100 utterances)
- wer_telephone: 0.2214548802946593  (denominator 2172, 100 utterances)
- cer_clean: 0.033946251768033946  (denominator 14041, 100 utterances)
- cer_telephone: 0.0838048090523338  (denominator 14041, 100 utterances)
