"""Spanish extractor (rex-4 ES rules): written-form cases + dev ceiling.

ES rules were tuned ONLY on the ES dev split (docs/06 discipline); these
tests pin that behavior. de/fr behavior is pinned separately by
test_slots.py — rex-4 keeps it identical to rex-3.
"""

import pytest

from voxentity_eu.adapters.slots import EXTRACTOR_VERSION, extract
from voxentity_eu.corpus.generate import build_corpus_es
from voxentity_eu.scoring.normalize import canonical_form, parse_slot_value


@pytest.mark.parametrize(
    ("text", "etype", "want"),
    [
        ("Mi número es +34612345678.", "phone", "+34612345678"),
        ("Puede llamarme al 612 345 678.", "phone", "+34612345678"),
        ("Mi correo es ana.garcia@example.com.", "email", "ana.garcia@example.com"),
        ("Mi correo es ana punto garcia arroba example punto com.", "email", "ana.garcia@example.com"),
        ("Mi cita es el 16 de octubre de 2028.", "calendar_value", "16.10.2028"),
        ("La cita es el 16/10/2028.", "calendar_value", "16.10.2028"),
        ("Mi referencia es EKH-6742.", "reference_code", "EKH-6742"),
        (
            "La referencia es ka uvedoble guion cero cero once.",
            "reference_code",
            "KW-0011",
        ),
        (
            "Mi dirección es Calle del Roble 12, 46115 Valdefresno.",
            "postal_address",
            "Calle Del Roble 12, 46115 Valdefresno",
        ),
        ("Me llamo Sergio Quintanilla.", "person_name", "sergio quintanilla"),
    ],
)
def test_es_written_and_spoken_forms(text, etype, want):
    r = extract(text, etype, "es-ES")
    assert r.status == "ok", (text, r.status)
    assert r.slots[0]["value"] == want


def test_es_correction_marker_is_word_bounded():
    # "nombre" contains "no"; the marker must not split it (regression)
    r = extract("El nombre es Úrsula Ordoñez.", "person_name", "es-ES")
    assert r.slots[0]["value"] == "úrsula ordoñez"  # extraction normalizes case


def test_es_correction_last_mention_wins():
    r = extract("El número es +34653784634, momento, me corrijo, es +34653784643.", "phone", "es-ES")
    assert r.slots[0]["value"] == "+34653784643"


def test_es_treinta_y_forms_do_not_fragment():
    # "treinta y seis" must resolve to the digit run 36, not 3|6
    r = extract("Mi dirección es Avenida de la Vega treinta y seis, uno cuatro cuatro tres seis Sotillo de la Vega.", "postal_address", "es-ES")
    assert r.slots[0]["value"].startswith("Avenida De La Vega 36,")


def test_es_street_starts_at_type_word():
    # frame carriers before the street type are never part of the street
    r = extract("La dirección de entrega es Paseo de las Acacias 175, 81796 El Saz Nuevo.", "postal_address", "es-ES")
    assert r.slots[0]["value"] == "Paseo De Las Acacias 175, 81796 El Saz Nuevo"


@pytest.mark.parametrize("field", ["synthesis_text", "written_text"])
def test_es_dev_ceiling_both_forms(field):
    """Both the spoken and the written gold form must extract exactly on dev."""

    failures = []
    for s in build_corpus_es():
        if s.split != "dev":
            continue
        r = extract(getattr(s, field), s.entity_type, s.locale)
        assert r.status == "ok", (s.scenario_id, field, r.status)
        e = s.entities[0]
        cs = (e.case_sensitive if e.case_sensitive is not None else True) if s.entity_type == "reference_code" else True
        got = canonical_form(
            parse_slot_value(r.slots[0]["value"], s.entity_type, s.locale),
            s.entity_type, s.locale, case_sensitive=cs,
        )
        want = canonical_form(e.canonical_value, s.entity_type, s.locale, case_sensitive=cs)
        if got != want:
            failures.append((s.scenario_id, field, got, want))
    assert not failures, failures


def test_extractor_version_is_rex4():
    assert EXTRACTOR_VERSION == "rex-4"
