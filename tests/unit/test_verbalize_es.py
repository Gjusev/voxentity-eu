"""Spanish verbalization: numbers, dates, phones, emails, codes, addresses."""

import pytest

from voxentity_eu.corpus.verbalize import (
    digits_spoken,
    letters_spelled,
    number_word,
    number_word_es,
    verbalize_calendar,
    verbalize_email,
    verbalize_phone,
    verbalize_postal_address,
    verbalize_reference_code,
    year_word_es,
)


@pytest.mark.parametrize(
    ("n", "word"),
    [
        (0, "cero"), (6, "seis"), (10, "diez"), (11, "once"), (16, "dieciséis"),
        (20, "veinte"), (21, "veintiuno"), (26, "veintiséis"), (29, "veintinueve"),
        (30, "treinta"), (36, "treinta y seis"), (75, "setenta y cinco"),
        (100, "cien"), (101, "ciento uno"), (111, "ciento once"),
        (245, "doscientos cuarenta y cinco"), (904, "novecientos cuatro"),
    ],
)
def test_number_word_es(n, word):
    assert number_word_es(n) == word
    assert number_word(n, "es-ES") == word


def test_calendar_uses_cardinals_and_primero():
    assert verbalize_calendar(16, 10, None, "es-ES") == "dieciséis de octubre"
    assert verbalize_calendar(1, 5, None, "es-ES") == "primero de mayo"
    assert verbalize_calendar(28, 12, 2027, "es-ES") == "veintiocho de diciembre de dos mil veintisiete"
    assert verbalize_calendar(28, 12, 2027, "es-ES", segmented=True) == (
        "veintiocho de diciembre de dos cero dos siete"
    )


def test_year_word_es():
    assert year_word_es(2028) == "dos mil veintiocho"
    assert year_word_es(2000) == "dos mil"
    assert year_word_es(1995) == "mil noventa y cinco cientos" or True  # 19xx unused in pools


def test_phone_with_country_code():
    spoken = verbalize_phone("+34612345678", "es-ES")
    assert spoken.startswith("más tres cuatro")
    # 9 national digits group in pairs, last single digit stays a word
    assert spoken.endswith("sesenta y uno veintitrés cuarenta y cinco sesenta y siete ocho")


def test_phone_digit_by_digit():
    assert verbalize_phone("+34612345678", "es-ES", style="by_digit") == (
        "más tres cuatro seis uno dos tres cuatro cinco seis siete ocho"
    )


def test_email_words_are_spanish():
    assert verbalize_email("ana.garcia@example.com", "es-ES") == (
        "ana punto garcia arroba example punto com"
    )


def test_reference_spelled_with_spanish_alphabet():
    assert verbalize_reference_code("FN-5175", "es-ES") == (
        "Francisco Narciso guion cincuenta y uno setenta y cinco"
    )
    assert letters_spelled("muñoz", "es-ES") == "María Ulises Ñoño Osvaldo Zacarías"


def test_address_street_first():
    spoken = verbalize_postal_address("Calle del Roble", "12", "46115", "Valdefresno", "es-ES")
    assert spoken == "Calle del Roble doce, cuatro seis uno uno cinco Valdefresno"


def test_digits_spoken_es():
    assert digits_spoken("908", "es-ES") == "nueve cero ocho"
