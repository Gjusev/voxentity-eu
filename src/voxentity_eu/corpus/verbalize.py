"""DE/FR verbalization: values -> speakable synthesis text.

Used by the corpus generator (writing synthesis_text) and mirrored by the
reference extractor (adapters/slots.py) which parses the words back. The
tables below are a documented design choice, not a claim of linguistic
exhaustiveness (docs/06 §Extractor determinista de referencia).
"""

from __future__ import annotations

import re

DIGITS_DE = ["null", "eins", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun"]
DIGITS_FR = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf"]

# German spelling alphabet (DIN 5009 style) used for segmented/spelled entities.
SPELL_DE = {
    "a": "Anton", "b": "Berta", "c": "Cäsar", "d": "Dora", "e": "Emil", "f": "Friedrich",
    "g": "Gustav", "h": "Heinrich", "i": "Ida", "j": "Julius", "k": "Kaufmann", "l": "Ludwig",
    "m": "Martha", "n": "Nord", "o": "Otto", "p": "Paula", "q": "Quelle", "r": "Richard",
    "s": "Samuel", "t": "Theodor", "u": "Ulrich", "v": "Viktor", "w": "Wilhelm",
    "x": "Xanthippen", "y": "Ypsilon", "z": "Zacharias",
}
# International alphabet for French (documented project choice).
SPELL_FR = {
    "a": "Alfa", "b": "Bravo", "c": "Charlie", "d": "Delta", "e": "Echo", "f": "Foxtrot",
    "g": "Golf", "h": "Hotel", "i": "India", "j": "Juliett", "k": "Kilo", "l": "Lima",
    "m": "Mike", "n": "November", "o": "Oscar", "p": "Papa", "q": "Quebec", "r": "Romeo",
    "s": "Sierra", "t": "Tango", "u": "Uniform", "v": "Victor", "w": "Whisky",
    "x": "X-ray", "y": "Yankee", "z": "Zulu",
}

MONTHS_DE = {
    1: "Januar", 2: "Februar", 3: "März", 4: "April", 5: "Mai", 6: "Juni",
    7: "Juli", 8: "August", 9: "September", 10: "Oktober", 11: "November", 12: "Dezember",
}
# Letter names as pronounced when reading a code aloud (not the spelling alphabet).
LETTER_NAMES_DE = {
    "a": "ah", "b": "beh", "c": "zeh", "d": "deh", "e": "eh", "f": "eff", "g": "geh",
    "h": "ha", "i": "ih", "j": "jott", "k": "kah", "l": "ell", "m": "emm", "n": "enn",
    "o": "oh", "p": "peh", "q": "kuh", "r": "err", "s": "ess", "t": "teh", "u": "uh",
    "v": "fau", "w": "weh", "x": "iks", "y": "üpsilon", "z": "tsett",
}
LETTER_NAMES_FR = {
    "a": "ah", "b": "bé", "c": "cé", "d": "dé", "e": "eu", "f": "effe", "g": "jé",
    "h": "ache", "i": "i", "j": "ji", "k": "ka", "l": "elle", "m": "emme", "n": "enne",
    "o": "o", "p": "pé", "q": "ku", "r": "erre", "s": "esse", "t": "té", "u": "u",
    "v": "vé", "w": "double vé", "x": "ixe", "y": "i grec", "z": "zède",
}
MONTHS_FR = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
    7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre",
}

AT_WORD = {"de-DE": "Ät", "fr-FR": "arobase"}
DOT_WORD = {"de-DE": "Punkt", "fr-FR": "point"}
DASH_WORD = {"de-DE": "Bindestrich", "fr-FR": "tiret"}
UNDERSCORE_WORD = {"de-DE": "Unterstrich", "fr-FR": "soulignement"}
PLUS_WORD = {"de-DE": "Plus", "fr-FR": "plus"}

_TENS_DE = {10: "zehn", 11: "elf", 12: "zwölf", 13: "dreizehn", 14: "vierzehn", 15: "fünfzehn",
            16: "sechzehn", 17: "siebzehn", 18: "achtzehn", 19: "neunzehn", 20: "zwanzig",
            30: "dreißig", 40: "vierzig", 50: "fünfzig", 60: "sechzig", 70: "siebzig",
            80: "achtzig", 90: "neunzig"}
_ONES_DE = {1: "ein", 2: "zwei", 3: "drei", 4: "vier", 5: "fünf", 6: "sechs", 7: "sieben", 8: "acht", 9: "neun"}


def number_word_de(n: int) -> str:
    if n < 10:
        return DIGITS_DE[n]
    if n in _TENS_DE:
        return _TENS_DE[n]
    if n < 100:
        tens, ones = n // 10 * 10, n % 10
        return f"{_ONES_DE[ones]}und{_TENS_DE[tens]}"
    if n < 1000:
        h, rest = divmod(n, 100)
        prefix = "einhundert" if h == 1 else f"{_ONES_DE[h]}hundert"
        return prefix + (number_word_de(rest) if rest else "")
    raise ValueError(f"number_word_de supports 0..999, got {n}")


_TENS_FR = {10: "dix", 11: "onze", 12: "douze", 13: "treize", 14: "quatorze", 15: "quinze",
            16: "seize", 20: "vingt", 30: "trente", 40: "quarante", 50: "cinquante",
            60: "soixante", 80: "quatre-vingts"}
_ONES_FR = {1: "un", 2: "deux", 3: "trois", 4: "quatre", 5: "cinq", 6: "six", 7: "sept",
            8: "huit", 9: "neuf"}


def number_word_fr(n: int) -> str:
    if n < 10:
        return DIGITS_FR[n]
    if n in _TENS_FR:
        return _TENS_FR[n]
    if n < 20:
        return f"dix-{DIGITS_FR[n - 10]}"
    if n < 70 or 80 <= n < 90:
        tens, ones = n // 10 * 10, n % 10
        base = _TENS_FR[tens]
        if ones == 1 and tens < 80:
            return f"{base}-et-un"
        if ones == 0:
            return base
        if tens == 80:
            base = base[:-1]  # quatre-vingts -> quatre-vingt- before a unit
        return f"{base}-{DIGITS_FR[ones]}"
    if n == 71:
        return "soixante-et-onze"
    if n == 81:
        return "quatre-vingt-un"
    if 70 <= n < 80:
        return f"soixante-{number_word_fr(n - 60)}"
    if 90 <= n < 100:
        return f"quatre-vingt-{number_word_fr(n - 80)}"
    if n < 1000:
        h, rest = divmod(n, 100)
        if h == 1:
            return "cent" + (f" {number_word_fr(rest)}" if rest else "")
        base = f"{number_word_fr(h)} cent"
        if not rest:
            return base + "s"
        return f"{base} {number_word_fr(rest)}"
    raise ValueError(f"number_word_fr supports 0..999, got {n}")


def number_word(n: int, locale: str) -> str:
    return number_word_de(n) if locale == "de-DE" else number_word_fr(n)


def digits_spoken(value: str, locale: str, *, by_digit: bool = True, group: int = 0) -> str:
    """Speak a digit string. by_digit: one word per digit. group>0: chunks of
    that many digits spoken as numbers (natural blocks)."""

    digits = [c for c in value if c.isdigit()]
    if by_digit:
        table = DIGITS_DE if locale == "de-DE" else DIGITS_FR
        return " ".join(table[int(d)] for d in digits)
    if group:
        chunks = ["".join(digits[i : i + group]) for i in range(0, len(digits), group)]
        return " ".join(number_word(int(c.lstrip("0") or "0"), locale) if c else "" for c in chunks)
    return " ".join(digits)


def letters_spelled(value: str, locale: str) -> str:
    table = SPELL_DE if locale == "de-DE" else SPELL_FR
    return " ".join(table.get(ch, ch) for ch in value.lower() if ch.isalpha())


# --- entity verbalizers ---------------------------------------------------------


def verbalize_phone(number: str, locale: str, *, style: str = "grouped") -> str:
    """style: grouped (2-digit blocks as numbers) | by_digit | grouped3."""

    cc = "49" if locale == "de-DE" else "33"
    rest = number
    prefix = ""
    if number.startswith("+"):
        rest = number[1:]
        prefix = f"{PLUS_WORD[locale]} {digits_spoken(rest[:len(cc)], locale)} "
        rest = rest[len(cc):]
    if style == "by_digit":
        return prefix + digits_spoken(rest, locale)
    size = 3 if style == "grouped3" else 2
    chunks = [rest[i : i + size] for i in range(0, len(rest), size)]
    words = []
    for c in chunks:
        lead_zeros = len(c) - len(c.lstrip("0"))
        if lead_zeros == len(c):
            words.append(" ".join(number_word(0, locale) for _ in c))
        elif lead_zeros:
            words.append(
                " ".join([number_word(0, locale)] * lead_zeros + [number_word(int(c.lstrip("0")), locale)])
            )
        else:
            words.append(number_word(int(c), locale))
    return prefix + " ".join(words)


def verbalize_email(email: str, locale: str, *, spell_local: bool = False) -> str:
    local, _, domain = email.partition("@")
    at = AT_WORD[locale]
    dot = DOT_WORD[locale]
    digit_table = DIGITS_DE if locale == "de-DE" else DIGITS_FR
    spell_table = SPELL_DE if locale == "de-DE" else SPELL_FR
    if spell_local:
        words = []
        for ch in local:
            if ch.isalpha():
                words.append(spell_table.get(ch.lower(), ch))
            elif ch.isdigit():
                words.append(digit_table[int(ch)])
            elif ch == ".":
                words.append(dot)
            elif ch == "-":
                words.append(DASH_WORD[locale])
            elif ch == "_":
                words.append(UNDERSCORE_WORD[locale])
        local_part = " ".join(words)
    else:
        # digit runs inside the local part are dictated digit by digit
        expanded = re.sub(r"\d+", lambda m: " " + " ".join(digit_table[int(c)] for c in m.group()) + " ", local)
        local_part = (
            expanded.replace(".", f" {dot} ").replace("_", f" {UNDERSCORE_WORD[locale]} ")
        )
    domain_part = domain.replace(".", f" {dot} ")
    return f"{local_part} {at} {domain_part}"


def verbalize_reference_code(code: str, locale: str, *, spell: bool = True) -> str:
    """Letters via the spelling alphabet (spell) or letter names, digits in
    2-digit numbers, '-' as word."""

    names = LETTER_NAMES_DE if locale == "de-DE" else LETTER_NAMES_FR
    parts: list[str] = []
    token = re.split(r"([A-Za-z]+|\d+)", code)
    for seg in token:
        if not seg:
            continue
        if seg.isalpha():
            parts.append(letters_spelled(seg, locale) if spell else " ".join(names.get(c, c) for c in seg.lower()))
        elif seg.isdigit():
            if len(seg) == 1:
                parts.append(digits_spoken(seg, locale))
            else:
                chunks = [seg[i : i + 2] for i in range(0, len(seg), 2)]
                parts.extend(
                    digits_spoken(c, locale) if c.startswith("0") else number_word(int(c), locale)
                    for c in chunks
                )
        elif seg == "-":
            parts.append(DASH_WORD[locale])
    return " ".join(parts)


def verbalize_calendar(day: int, month: int, year: int | None, locale: str, *, segmented: bool = False) -> str:
    if locale == "de-DE":
        irregular = {1: "ersten", 3: "dritten", 7: "siebten", 8: "achten"}
        day_word = irregular.get(day) or f"{number_word_de(day)}ten"
        text = f"{day_word} {MONTHS_DE[month]}"
        if year is not None:
            text += f" {year_word_de(year, segmented=segmented)}"
    else:
        text = f"{number_word_fr(day)} {MONTHS_FR[month]}"
        if year is not None:
            text += f" {year_word_fr(year, segmented=segmented)}"
    return text


def year_word_de(year: int, *, segmented: bool = False) -> str:
    if segmented:
        return digits_spoken(str(year), "de-DE")
    h, rest = divmod(year, 100)
    if h == 20:  # 2000-2099: "zweitausend..." is the year form
        return "zweitausend" + (number_word_de(rest) if rest else "")
    return f"{number_word_de(h)}hundert" + (number_word_de(rest) if rest else "")


def year_word_fr(year: int, *, segmented: bool = False) -> str:
    if segmented:
        return digits_spoken(str(year), "fr-FR")
    h, rest = divmod(year, 100)
    if h == 20:
        return "deux mille" + (f" {number_word_fr(rest)}" if rest else "")
    if h == 19:
        return "mille neuf cent" + (f" {number_word_fr(rest)}" if rest else "")
    return ("cent" if h == 1 else f"{number_word_fr(h)} cents") + (
        f" {number_word_fr(rest)}" if rest else ""
    )


def verbalize_postal_address(
    street: str, house_number: str, postal_code: str, locality: str, locale: str
) -> str:
    postal = digits_spoken(postal_code, locale)  # digit by digit, the postal convention
    if locale == "de-DE":
        return f"{street} {digits_and_suffix(house_number, locale)}, {postal} {locality}"
    return f"{digits_and_suffix(house_number, locale)} {street}, {postal} {locality}"


def digits_and_suffix(house_number: str, locale: str) -> str:
    m = re.match(r"(\d+)([A-Za-z]*)", house_number)
    if not m:
        return house_number
    digits, suffix = m.groups()
    spoken = number_word(int(digits), locale)
    if suffix:
        if suffix.lower() in ("bis", "ter"):
            return f"{spoken} {suffix.lower()}"  # French suffix words are spoken as words
        table = SPELL_DE if locale == "de-DE" else SPELL_FR
        return f"{spoken} {table.get(suffix.lower(), suffix)}"
    return spoken
