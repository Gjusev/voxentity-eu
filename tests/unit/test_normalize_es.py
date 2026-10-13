"""Spanish normalization: +34 without trunk zero, ES months/addresses."""

from voxentity_eu.scoring.normalize import (
    canonical_person_name,
    canonical_phone,
    canonical_street,
    parse_slot_value,
)


def test_national_nine_digit_mobile_becomes_international():
    assert canonical_phone("612345678", "es-ES") == "+34612345678"
    assert canonical_phone("612 345 678", "es-ES") == "+34612345678"
    assert canonical_phone("912345678", "es-ES") == "+34912345678"  # landline head 9


def test_es_has_no_trunk_zero_rule():
    # unlike de/fr, a leading 0 is NOT a national trunk in Spain: it stays
    # verbatim (and therefore fails comparison honestly)
    assert canonical_phone("0612345678", "es-ES") == "0612345678"


def test_international_forms_preserved():
    assert canonical_phone("+34 612 345 678", "es-ES") == "+34612345678"
    assert canonical_phone("0034 612345678", "es-ES") == "+34612345678"


def test_ene_and_accents_survive_lowercase():
    assert canonical_person_name("Úrsula Ordoñez") == "úrsula ordoñez"
    assert canonical_person_name("Úrsula Ordoñez") != canonical_person_name("Ursula Ordonez")


def test_street_abbreviations_es():
    assert canonical_street("C/ Mayor", "es-ES") == "calle mayor"
    assert canonical_street("Av. de la Vega", "es-ES") == "avenida de la vega"
    assert canonical_street("Pza. del Rosal", "es-ES") == "plaza del rosal"


def test_postal_address_es_shape():
    v = parse_slot_value("Calle del Roble 12, 46115 Valdefresno", "postal_address", "es-ES")
    assert (v.street, v.house_number, v.postal_code, v.locality) == (
        "Calle del Roble", "12", "46115", "Valdefresno",
    )
    v2 = parse_slot_value("Avenida de la Encomienda 111bis, 61636 Montearagón la Baja", "postal_address", "es-ES")
    assert v2.house_number == "111bis"


def test_calendar_spanish_months():
    v = parse_slot_value("16 de octubre de 2028", "calendar_value", "es-ES")
    assert (v.day, v.month, v.year) == (16, 10, 2028)
    v2 = parse_slot_value("5 de mayo", "calendar_value", "es-ES")
    assert (v2.day, v2.month, v2.year) == (5, 5, None)


def test_numeric_date_with_slashes():
    v = parse_slot_value("16/10/2028", "calendar_value", "es-ES")
    assert (v.day, v.month, v.year) == (16, 10, 2028)


def test_de_fr_phone_rules_unchanged():
    assert canonical_phone("0170 1234567", "de-DE") == "+491701234567"
    assert canonical_phone("0612345678", "fr-FR") == "+33612345678"
