"""Code-switching suite: DE/FR carrier sentences with English pieces.

Cells (locale x entity), 7 cases each (2 dev + 5 test, disjoint template
families):
- email: dictated with English separators ("at", "dot", "underscore", "dash").
- phone: digits read in English after a DE/FR carrier ("plus four nine ...").
- reference_code: DE uses the NATO alphabet instead of DIN 5009 + German
  numbers; FR uses NATO letters + English digits + "dash".
- person_name: names of non-DE/FR origin (invented combinations, not real
  people) inside a DE/FR sentence.

Values come from the core pools past index 30 and are checked disjoint from
every core value, so nothing here duplicates the main corpus. Written by
build_suite(); synthesis, channel, export, ASR and scoring reuse the core
pipeline because each case is a regular single-audio Scenario.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..contracts import SCHEMA_VERSION, Scenario
from ..corpus import pools
from ..corpus.verbalize import SPELL, number_word
from ..provenance import sha256_text, write_text_atomic

SUITE = "codeswitch"
LOCALES = ("de-DE", "fr-FR")
ENTITIES = ("email", "phone", "reference_code", "person_name")
DEV, TEST = 2, 5
EN_DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
SHORT = {"email": "mail", "phone": "phone", "reference_code": "ref", "person_name": "name"}

# invented first/last combinations of non-DE/FR origin (not real people)
FOREIGN_FIRST = ["Siobhan", "Wojciech", "Oluwaseun", "Joaquín", "Saoirse", "Bartłomiej", "Thandiwe",
                 "Niamh", "Grzegorz", "Chiamaka", "Íñigo", "Aoife", "Przemysław", "Ngozi"]
FOREIGN_LAST = ["O'Callaghan", "Kowalczyk", "Adeyemi", "Echeverría", "Mac Giolla", "Wiśniewski",
                "Dlamini", "Ní Bhriain", "Szczepański", "Okonkwo", "Goikoetxea", "Ó Súilleabháin",
                "Brzęczyszczykiewicz", "Eze"]

CARRIERS = {
    ("de-DE", "email"): (["Meine Mail ist {v}.", "Schreiben Sie an {v}."],
                         ["Die Adresse lautet {v}, bitte notieren.", "Sie erreichen mich unter {v}.",
                          "Notieren Sie bitte {v}."]),
    ("fr-FR", "email"): (["Mon mail est {v}.", "Écrivez à {v}."],
                         ["L'adresse est {v}, merci de noter.", "Vous pouvez m'écrire à {v}.",
                          "Notez bien {v}."]),
    ("de-DE", "phone"): (["Meine Nummer ist {v}.", "Rufen Sie {v} an."],
                         ["Die Nummer lautet {v}.", "Sie erreichen mich unter {v}.", "Notieren Sie {v}."]),
    ("fr-FR", "phone"): (["Mon numéro est le {v}.", "Appelez le {v}."],
                         ["Le numéro, c'est le {v}.", "Vous pouvez me joindre au {v}.", "Notez le {v}."]),
    ("de-DE", "reference_code"): (["Meine Referenz ist {v}.", "Die Vorgangsnummer ist {v}."],
                                  ["Referenz {v}, bitte notieren.", "Notieren Sie die Referenz {v}.",
                                   "Es geht um den Vorgang {v}."]),
    ("fr-FR", "reference_code"): (["Ma référence est {v}.", "Le dossier est {v}."],
                                  ["Référence {v}, merci de noter.", "Notez la référence {v}.",
                                   "C'est le dossier {v}."]),
    ("de-DE", "person_name"): (["Mein Name ist {v}.", "Ich heiße {v}."],
                               ["Der Termin ist auf {v}.", "Notieren Sie bitte {v}.", "Hier spricht {v}."]),
    ("fr-FR", "person_name"): (["Je m'appelle {v}.", "Mon nom est {v}."],
                               ["Le rendez-vous est au nom de {v}.", "Notez bien {v}.", "Ici {v}."]),
}


def _email_en(email: str) -> str:
    local, _, domain = email.partition("@")
    words = {".": " dot ", "_": " underscore ", "-": " dash "}
    spoken_local = "".join(words.get(c, f" {EN_DIGITS[int(c)]} " if c.isdigit() else c) for c in local)
    return " ".join(f"{spoken_local} at {domain.replace('.', ' dot ')}".split())


def _phone_en(number: str) -> str:
    return "plus " + " ".join(EN_DIGITS[int(c)] for c in number.lstrip("+"))


def _ref_switch(code: str, locale: str) -> str:
    letters, _, digits = code.partition("-")
    nato = " ".join(SPELL["fr-FR"][c.lower()] for c in letters)
    if locale == "de-DE":
        chunks = [digits[i : i + 2] for i in range(0, len(digits), 2)]
        nums = " ".join(" ".join(number_word(int(d), locale) for d in c) if c.startswith("0") else number_word(int(c), locale)
                        for c in chunks)
        return f"{nato} Bindestrich {nums}"
    return f"{nato} dash " + " ".join(EN_DIGITS[int(c)] for c in digits)


def _values(locale: str, entity: str, n: int) -> list:
    if entity == "person_name":
        off = 0 if locale == "de-DE" else 7
        return [f"{FOREIGN_FIRST[(i + off) % 14]} {FOREIGN_LAST[(i * 3 + off) % 14]}" for i in range(n)]
    pool = {"email": pools.email_pool, "phone": pools.phone_pool, "reference_code": pools.reference_pool}[entity]
    return pool(locale, 30 + n)[30:]


def _spoken(value: str, locale: str, entity: str) -> str:
    if entity == "email":
        return _email_en(value)
    if entity == "phone":
        return _phone_en(value)
    if entity == "reference_code":
        return _ref_switch(value, locale)
    return value


def build_scenarios() -> list[Scenario]:
    out: list[Scenario] = []
    for locale in LOCALES:
        for entity in ENTITIES:
            dev_frames, test_frames = CARRIERS[(locale, entity)]
            for i, value in enumerate(_values(locale, entity, DEV + TEST)):
                split = "dev" if i < DEV else "test"
                frames = dev_frames if split == "dev" else test_frames
                frame = frames[i % len(frames)]
                ent = {"entity_id": "target-1", "type": entity, "canonical_value": value,
                       "accepted_variants": [], "mention_text": value, "target": True}
                if entity == "reference_code":
                    ent["case_sensitive"] = True
                sid = f"cs-{split}-{locale[:2]}-{SHORT[entity]}-{i:03d}"
                out.append(Scenario.model_validate({
                    "schema_version": SCHEMA_VERSION, "scenario_id": sid, "split": split,
                    "locale": locale, "entity_type": entity,
                    "template_family": f"cs_{locale[:2]}_{entity}_{split}",
                    "difficulty_tags": ["phonetic"] if entity == "person_name" else ["segmented"],
                    "written_text": frame.format(v=value),
                    "synthesis_text": frame.format(v=_spoken(value, locale, entity)),
                    "entities": [ent], "previous_mentions": [],
                    "seed": int(sha256_text(sid)[:8], 16),
                }))
    return out


def build_suite(out_dir: Path, core: list[Scenario]) -> dict:
    """Writes gold/scenarios.jsonl + corpus_manifest.json under out_dir."""

    scenarios = build_scenarios()
    core_values = {json.dumps(e.canonical_value if isinstance(e.canonical_value, str) else e.canonical_value.model_dump(),
                              sort_keys=True) for s in core for e in s.entities}
    clash = [s.scenario_id for s in scenarios if json.dumps(s.entities[0].canonical_value) in core_values]
    if clash:
        raise ValueError(f"code-switch values overlap the core corpus: {clash}")
    lines = "\n".join(s.model_dump_json() for s in scenarios) + "\n"
    write_text_atomic(out_dir / "gold" / "scenarios.jsonl", lines)
    manifest = {"suite": SUITE, "total_scenarios": len(scenarios),
                "splits": {sp: sum(s.split == sp for s in scenarios) for sp in ("dev", "test")},
                "cells": {f"{loc}|{e}": DEV + TEST for loc in LOCALES for e in ENTITIES},
                "corpus_hash": sha256_text(lines)}
    write_text_atomic(out_dir / "corpus_manifest.json", json.dumps(manifest, indent=1))
    return manifest
