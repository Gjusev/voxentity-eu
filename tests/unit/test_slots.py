"""Reference extractor: written-form regression cases (dev split only, rex-3)."""

import pytest

from voxentity_eu.adapters.slots import extract
from voxentity_eu.corpus.generate import build_corpus
from voxentity_eu.scoring.normalize import canonical_form, parse_slot_value


@pytest.mark.parametrize(
    ("text", "etype", "locale", "want"),
    [
        ("Meine Rufnummer ist +491742707270.", "phone", "de-DE", "+491742707270"),
        ("Meine E-Mail-Adresse ist lukas_zimmerling@example.com.", "email", "de-DE", "lukas_zimmerling@example.com"),
        ("E-Mail gustav.kühn@example.com, Zeichen für Zeichen.", "email", "de-DE", "gustav.kühn@example.com"),
        ("Am 13.05, Moment, ich korrigiere, am 14.05.", "calendar_value", "de-DE", "14.05"),
        ("Die Referenz ist XWJ-9690, pardon, XWJ-9609.", "reference_code", "de-DE", "XWJ-9609"),
        ("Notez bien la référence Bravo Oscar-0081.", "reference_code", "fr-FR", "BO-0081"),
        ("Adresse Veilchenweg 55a, 81907 Felsenbrunn, Bestandteil für Bestandteil.", "postal_address", "de-DE",
         "Veilchenweg 55a, 81907 Felsenbrunn"),
        ("Mon adresse est Allée des Érables 28ter, 96359 Montreuil-le-Sec.", "postal_address", "fr-FR",
         "Allée Des Érables 28ter, 96359 Montreuil-Le-Sec"),
    ],
)
def test_written_forms(text, etype, locale, want):
    r = extract(text, etype, locale)
    assert r.status == "ok"
    assert r.slots[0]["value"] == want


@pytest.mark.parametrize(
    ("text", "etype", "locale", "want"),
    [  # rex-4, from code-switching dev cases
        ("Écrivez à manon_yael@example.com.", "email", "fr-FR", "manon_yael@example.com"),  # 'non' inside a word
        ("Schreiben Sie an emil dot weiss nine at example dot com.", "email", "de-DE", "emil.weiss9@example.com"),
        ("Appelez le plus three three six two four three seven nine five zero two.", "phone", "fr-FR", "+33624379502"),
        ("Ma référence est Echo Golf dash zero three five five.", "reference_code", "fr-FR", "EG-0355"),
        ("Mein Name ist Siobhan O'Callaghan.", "person_name", "de-DE", "siobhan o'callaghan"),
        ("Pardon, l'adresse est rue des Lilas", "person_name", "fr-FR", None),  # elisions still split
    ],
)
def test_rex4_codeswitch_forms(text, etype, locale, want):
    r = extract(text, etype, locale)
    if want is None:
        assert all("l'" not in s["value"] for s in r.slots)
    else:
        assert r.slots[0]["value"] == want


def test_ordinal_day_with_written_period():
    r = extract("Am 11. Dezember passt es mir.", "calendar_value", "de-DE")
    assert r.slots[0]["value"] == "11.12"


@pytest.mark.parametrize("field", ["synthesis_text", "written_text"])
def test_dev_ceiling_both_forms(field):
    """Both the spoken and the written gold form must extract exactly on dev."""

    for s in build_corpus():
        if s.split != "dev":
            continue
        r = extract(getattr(s, field), s.entity_type, s.locale)
        assert r.status == "ok", (s.scenario_id, field)
        e = s.entities[0]
        got = canonical_form(parse_slot_value(r.slots[0]["value"], s.entity_type, s.locale), s.entity_type, s.locale)
        want = canonical_form(e.canonical_value, s.entity_type, s.locale)
        assert got == want, (s.scenario_id, field, got, want)
