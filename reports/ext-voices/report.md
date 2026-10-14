# Extension: voice coverage (DE/FR core test scenarios, four voices)

The 120 core test scenarios (x clean/telephone) re-synthesized with Qwen3-TTS voices vivian and ryan; serena/dylan are the core corpus voices (one per scenario). Whisper large-v3-turbo -> extractor rex-4. Synthetic speech, simulated telephone channel, automated QA only.

| voice | scenarios covered | N items | exact slot accuracy |
| --- | --- | --- | --- |
| serena (core) | 60 | 120 | 29.2 |
| dylan (core) | 60 | 120 | 39.2 |
| vivian | 120 | 240 | 35.0 |
| ryan | 120 | 240 | 34.2 |

Paired vivian - ryan (same scenarios and conditions, n=240): +0.8 pp [-3.3, +5.0].

Confound check: the core gap serena vs dylan could come from the scenarios each voice got. Same split, but scored with the new voices:

| scenarios originally voiced by | vivian accuracy | ryan accuracy | core voice accuracy |
| --- | --- | --- | --- |
| serena | 33.3 | 33.3 | 29.2 |
| dylan | 36.7 | 35.0 | 39.2 |

If vivian and ryan also score higher on dylan's scenarios, the core voice gap reflects scenario difficulty, not the voice.
