# Extension: second TTS family (Piper) on the core test scenarios

Same 120 core test scenarios and text, synthesized with Piper (thorsten DE, siwis FR; one voice per locale) instead of Qwen3-TTS, then the same simulated telephone channel. Whisper large-v3-turbo -> extractor rex-4. Synthetic speech, automated QA only. Gate and rights: research/second-tts-gate.md.

| synthesizer | N items | exact slot accuracy |
| --- | --- | --- |
| Qwen3-TTS (core, serena/dylan) | 240 | 34.2 |
| Piper (thorsten/siwis) | 240 | 44.2 |

Paired Qwen - Piper (same scenario and condition, n=240): -10.0 pp [-15.4, -4.2].

| cell | Qwen | Piper |
| --- | --- | --- |
| de-DE calendar_value | 90.0 | 100.0 |
| de-DE email | 5.0 | 0.0 |
| de-DE person_name | 65.0 | 50.0 |
| de-DE phone | 15.0 | 70.0 |
| de-DE postal_address | 0.0 | 5.0 |
| de-DE reference_code | 50.0 | 60.0 |
| fr-FR calendar_value | 75.0 | 100.0 |
| fr-FR email | 0.0 | 0.0 |
| fr-FR person_name | 25.0 | 30.0 |
| fr-FR phone | 15.0 | 55.0 |
| fr-FR postal_address | 20.0 | 15.0 |
| fr-FR reference_code | 50.0 | 45.0 |

A single synthesizer per locale is a limitation: differences mix TTS family and voice.
