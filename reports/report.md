# VoxEntity-EU measured results

Synthetic speech, simulated telephone channel. All numbers come from frozen prediction files; corpus-level provisional status is tracked in IMPLEMENTATION_STATUS.md. N counts scenarios, not audio files.

## Systems

| system | track | N | slot accuracy | 95% CI | coverage | macro12 clean | macro12 tel | stale-rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gold-extractor | asr_slots | 240 | 100.0 | [100.0, 100.0] | 100.0 | 100.0 | 100.0 | 0.0 |
| reference-agent | asr_slots | 240 | 20.8 | [15.4, 26.2] | 100.0 | 21.7 | 20.0 | 0.0 |
| voxtral-mini-slots | asr_slots | 240 | 21.2 | [15.4, 27.1] | 100.0 | 21.7 | 20.8 | 0.0 |
| whisper-turbo-slots | asr_slots | 240 | 20.8 | [15.4, 26.2] | 100.0 | 21.7 | 20.0 | 0.0 |

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

## Paired degradation — reference-agent

- N pairs: 120
- accuracy clean: 21.7
- accuracy telephone: 20.0
- delta: +1.7 percentage points
- transitions: {"fail->pass": 3, "pass->fail": 5, "pass->pass": 21, "fail->fail": 91}

### 12-cell matrix (accuracy clean / telephone)

| cell | N | clean % | telephone % |
| --- | --- | --- | --- |
| de-DE|calendar_value | 20 | 0 | 0 |
| de-DE|email | 20 | 0 | 0 |
| de-DE|person_name | 20 | 70 | 60 |
| de-DE|phone | 20 | 10 | 20 |
| de-DE|postal_address | 20 | 0 | 0 |
| de-DE|reference_code | 20 | 20 | 30 |
| fr-FR|calendar_value | 20 | 80 | 70 |
| fr-FR|email | 20 | 0 | 0 |
| fr-FR|person_name | 20 | 30 | 20 |
| fr-FR|phone | 20 | 20 | 10 |
| fr-FR|postal_address | 20 | 20 | 20 |
| fr-FR|reference_code | 20 | 10 | 10 |

## Paired degradation — voxtral-mini-slots

- N pairs: 120
- accuracy clean: 21.7
- accuracy telephone: 20.8
- delta: +0.8 percentage points
- transitions: {"fail->pass": 2, "pass->fail": 3, "pass->pass": 23, "fail->fail": 92}

### 12-cell matrix (accuracy clean / telephone)

| cell | N | clean % | telephone % |
| --- | --- | --- | --- |
| de-DE|calendar_value | 20 | 0 | 0 |
| de-DE|email | 20 | 0 | 0 |
| de-DE|person_name | 20 | 70 | 60 |
| de-DE|phone | 20 | 10 | 10 |
| de-DE|postal_address | 20 | 30 | 30 |
| de-DE|reference_code | 20 | 0 | 10 |
| fr-FR|calendar_value | 20 | 80 | 80 |
| fr-FR|email | 20 | 0 | 0 |
| fr-FR|person_name | 20 | 30 | 20 |
| fr-FR|phone | 20 | 10 | 10 |
| fr-FR|postal_address | 20 | 20 | 20 |
| fr-FR|reference_code | 20 | 10 | 10 |

## Paired degradation — whisper-turbo-slots

- N pairs: 120
- accuracy clean: 21.7
- accuracy telephone: 20.0
- delta: +1.7 percentage points
- transitions: {"fail->pass": 3, "pass->fail": 5, "pass->pass": 21, "fail->fail": 91}

### 12-cell matrix (accuracy clean / telephone)

| cell | N | clean % | telephone % |
| --- | --- | --- | --- |
| de-DE|calendar_value | 20 | 0 | 0 |
| de-DE|email | 20 | 0 | 0 |
| de-DE|person_name | 20 | 70 | 60 |
| de-DE|phone | 20 | 10 | 20 |
| de-DE|postal_address | 20 | 0 | 0 |
| de-DE|reference_code | 20 | 20 | 30 |
| fr-FR|calendar_value | 20 | 80 | 70 |
| fr-FR|email | 20 | 0 | 0 |
| fr-FR|person_name | 20 | 30 | 20 |
| fr-FR|phone | 20 | 20 | 10 |
| fr-FR|postal_address | 20 | 20 | 20 |
| fr-FR|reference_code | 20 | 10 | 10 |

## Error taxonomy (heuristic, revisable)

- **gold-extractor**: {"correct": 240}
- **reference-agent**: {"omission": 101, "correct": 50, "digit_error": 26, "name_error": 22, "address_component_loss": 14, "digit_swap": 11, "missing_prefix": 5, "calendar_component_loss": 4, "domain_error": 3, "local_part_error": 3, "code_error": 1}
- **voxtral-mini-slots**: {"omission": 93, "correct": 51, "digit_error": 29, "name_error": 21, "address_component_loss": 17, "digit_swap": 16, "missing_prefix": 4, "calendar_component_loss": 4, "code_error": 2, "local_part_error": 1, "domain_error": 1, "accent_loss": 1}
- **whisper-turbo-slots**: {"omission": 101, "correct": 50, "digit_error": 26, "name_error": 22, "address_component_loss": 14, "digit_swap": 11, "missing_prefix": 5, "calendar_component_loss": 4, "domain_error": 3, "local_part_error": 3, "code_error": 1}

## Human control (FLEURS, known corpus)

FLEURS is likely present in ASR training data; this control measures channel transfer on human speech, not generalization.
- wer_clean: 0.1151012891344383  (denominator 2172, 100 utterances)
- wer_telephone: 0.2214548802946593  (denominator 2172, 100 utterances)
- cer_clean: 0.033946251768033946  (denominator 14041, 100 utterances)
- cer_telephone: 0.0838048090523338  (denominator 14041, 100 utterances)
