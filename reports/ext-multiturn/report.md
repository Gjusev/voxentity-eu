# Extension: cross-turn corrections (DE/FR)

Separate suite, not part of the core 180 scenarios. 48 two-turn cases (16 dev / 32 test), same synthetic voice for both turns; kinds: correction (turn 2 replaces the value with a near-miss), confirmation (turn 2 confirms without restating), repeat (turn 2 restates the same value). Reference agent: ASR -> extractor -> store_slot per turn (replacement semantics) -> persisted final state read back. Extractor rex-4. Synthetic speech, simulated telephone channel, automated QA only. Test N = 32 cases x 2 conditions = 64.

| input | final-state accuracy | 95% CI | stale | spurious change | omission | wrong value | accuracy when both turns extracted correctly (n) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| gold-written | 100.0 | [100.0, 100.0] | 0 | 0 | 0 | 0 | 100.0 (64) |
| gold-spoken | 100.0 | [100.0, 100.0] | 0 | 0 | 0 | 0 | 100.0 (64) |
| whisper-turbo | 42.2 | [29.7, 54.7] | 0 | 2 | 19 | 16 | 100.0 (19) |

## Whisper-turbo agent by kind / condition / entity (test)

| group | n | final-state accuracy | stale | spurious change |
| --- | --- | --- | --- | --- |
| kind: correction | 32 | 43.8 | 0 | 0 |
| kind: confirmation | 16 | 25.0 | 0 | 0 |
| kind: repeat | 16 | 56.2 | 0 | 2 |
| condition: clean | 32 | 40.6 | 0 | 1 |
| condition: telephone | 32 | 43.8 | 0 | 1 |
| entity: phone | 16 | 43.8 | 0 | 0 |
| entity: email | 16 | 0.0 | 0 | 0 |
| entity: calendar_value | 16 | 100.0 | 0 | 0 |
| entity: reference_code | 16 | 25.0 | 0 | 2 |

Rows with stale or spurious outcomes (test, whisper-turbo):

- `mt-test-fr-ref-005` clean repeat: turn values ['CHX-9782', 'CÀ-9782'] -> final `CÀ-9782` (spurious_change)
- `mt-test-fr-ref-005` telephone repeat: turn values ['CHX-9782', 'CÀ-69782'] -> final `CÀ-69782` (spurious_change)
