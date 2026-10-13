"""Gold->extractor ceiling: run the reference extractor over gold text.

Reports both forms: synthesis_text (spoken, what the TTS read) and
written_text (what an ideal ASR emits). The spoken ceiling alone is circular.

Uses the exact scorer path (parse_slot_value + canonical + variants) so the
ceiling measures what track B will measure. Dev drives iteration; test is
reported but must not drive rule changes (docs/05, docs/06).
"""

from __future__ import annotations

import sys
from collections import Counter

from voxentity_eu.adapters.slots import EXTRACTOR_VERSION, extract
from voxentity_eu.corpus.generate import build_corpus
from voxentity_eu.scoring.normalize import canonical_form, parse_slot_value


def check(s, split=None, field="synthesis_text"):
    if split and s.split != split:
        return None
    r = extract(getattr(s, field), s.entity_type, s.locale)
    e = s.entities[0]
    cs = (e.case_sensitive or True) if s.entity_type == "reference_code" else True
    want = canonical_form(e.canonical_value, s.entity_type, s.locale, case_sensitive=cs)
    variants = [
        canonical_form(v, s.entity_type, s.locale, case_sensitive=cs) for v in e.accepted_variants
    ]
    if r.status != "ok":
        return ("unsupported", s, r.slots[0]["value"] if r.slots else "", want)
    raw = r.slots[0]["value"]
    structured = parse_slot_value(raw, s.entity_type, s.locale)
    got = canonical_form(structured, s.entity_type, s.locale, case_sensitive=cs)
    ok = repr(got) == repr(want) or repr(got) in [repr(v) for v in variants]
    return ("ok" if ok else "mismatch", s, raw, want)


def main() -> int:
    corpus = build_corpus()
    for field in ("synthesis_text", "written_text"):
        for split in ("dev", "test"):
            results = [r for r in (check(s, split, field) for s in corpus) if r]
            counts = Counter(r[0] for r in results)
            print(f"[{field} {split}] ok={counts['ok']} mismatch={counts['mismatch']} unsupported={counts['unsupported']} / {len(results)}")
            for status, s, got, want in results:
                if status != "ok":
                    print(f"  {s.scenario_id} {status}: got={got!r} want={want!r}")
                    print(f"    text: {getattr(s, field)[:120]}")
    print(f"extractor version: {EXTRACTOR_VERSION}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
