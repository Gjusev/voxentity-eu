# Release-gate evidence

Regenerate with `python scripts/release_gates.py` (exit 1 if any gate fails).
Committed so the gate output itself is versioned alongside reports/.

```
G4 gold-extractor: scored 240/240 incomplete=False coverage=1.0 failure_rate=0.0 ok
G4 gold-written-extractor: scored 240/240 incomplete=False coverage=1.0 failure_rate=0.0 ok
G4 reference-agent: scored 240/240 incomplete=False coverage=1.0 failure_rate=0.0 ok
G4 voxtral-mini-slots: scored 240/240 incomplete=False coverage=1.0 failure_rate=0.0 ok
G4 whisper-turbo-slots: scored 240/240 incomplete=False coverage=1.0 failure_rate=0.0 ok
G6 regenerated core + 5 extension reports; byte-identical
{'G4': True, 'G6': True}
```
