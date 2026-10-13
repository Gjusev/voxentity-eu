"""Versioned value normalization, separate literal and canonical passes.

Policy summary (docs/04-contracts.md §Normalización versionada), frozen as
NORMALIZER_VERSION before any inference:

- literal: NFC + exterior trim only.
- person_name: NFC, repeated whitespace collapsed to one, Unicode *lowercase*
  (not casefold: ß must survive). Accents and internal punctuation preserved.
- phone: presentation separators removed, 00-prefix → +, national trunk "0" →
  "+<country code>" under the declared locale rule only. All digits and any
  leading zeros after the prefix are preserved. No O/0 or l/1 equivalence.
- email: domain lowercased, local part preserved verbatim. Spaces around @ or
  dots are an extractor concern, never silently forgiven here.
- calendar_value: component-wise comparison; a missing year never inherits one.
- postal_address: per-field; street NFC+space-collapse+lowercase with a frozen
  public abbreviation allowlist; house number and suffix exact; postal code is
  a string (leading zeros preserved).
- reference_code: NFC, exterior spaces stripped, internal presentation spaces
  removed, case folded only when the case contract declares it insensitive.
  Zero, O, I, 1, hyphens and digits are never conflated.

The normalizer never sees the gold when scoring a prediction: it is a pure
function applied symmetrically to both sides.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from ..contracts import CalendarValue, EntityType, Locale, PostalAddressValue

NORMALIZER_VERSION = "norm-2"

# Public abbreviation allowlist for postal streets. Frozen; extending it is a
# new NORMALIZER_VERSION. Keys are compared after lowercase+NFC.
STREET_ABBREVIATIONS: dict[str, str] = {
    "de-DE": {
        "str.": "straße",
        "str": "straße",
        "pl.": "platz",
    },
    "fr-FR": {
        "av.": "avenue",
        "bd": "boulevard",
        "bvd": "boulevard",
        "r.": "rue",
        "ste": "sainte",
        "st": "saint",
    },
}

COUNTRY_CODES: dict[str, str] = {"de-DE": "49", "fr-FR": "33"}

_PHONE_SEPARATOR_RE = re.compile(r"[\s.\-()\u2013\u2014/\u00a0]")
_REF_SPACE_RE = re.compile(r"[\s\u00a0]+")
_WS_RE = re.compile(r"\s+")


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def literal_form(value: Any) -> str:
    """Literal score: NFC + exterior trim. Structured values serialize stably."""
    if isinstance(value, PostalAddressValue):
        return nfc(f"{value.street} {value.house_number}, {value.postal_code} {value.locality}").strip()
    if isinstance(value, CalendarValue):
        base = f"{value.day:02d}.{value.month:02d}"
        return nfc(f"{base}.{value.year}" if value.year else base)
    return nfc(str(value)).strip()


# --- per-type canonical passes ------------------------------------------------


def canonical_person_name(value: str) -> str:
    text = nfc(value)
    text = _WS_RE.sub(" ", text).strip()
    return text.lower()  # Unicode lowercase keeps ß as ß


def canonical_phone(value: str, locale: Locale) -> str:
    text = nfc(value)
    text = _PHONE_SEPARATOR_RE.sub("", text)
    if text.startswith("00"):
        text = "+" + text[2:]
    elif text.startswith("0"):
        # Declared locale rule: national trunk zero → +country code.
        # Only the single trunk zero is consumed; later zeros are preserved.
        cc = COUNTRY_CODES.get(locale)
        if cc is None:
            raise ValueError(f"no declared phone rule for locale {locale}")
        text = "+" + cc + text[1:]
    # international form that repeats the trunk zero after the country code,
    # e.g. "+49 (0)171 2345678" → drop that single in-parens trunk zero
    for cc in COUNTRY_CODES.values():
        prefix = "+" + cc + "0"
        if text.startswith(prefix):
            text = "+" + cc + text[len(prefix):]
            break
    return text


def canonical_email(value: str) -> str:
    text = nfc(value).strip()
    if "@" not in text:
        return text  # not parseable as email; compare verbatim (an error anyway)
    local, _, domain = text.rpartition("@")
    return f"{local}@{domain.lower()}"


def canonical_calendar(value: CalendarValue) -> tuple[int, int, int | None]:
    # No year inference: a missing year is a distinct value from any year.
    return (value.day, value.month, value.year)


def canonical_street(street: str, locale: Locale) -> str:
    text = _WS_RE.sub(" ", nfc(street)).strip().lower()
    allow = STREET_ABBREVIATIONS.get(locale, {})
    for short, full in allow.items():
        pattern = re.compile(rf"(?<!\w){re.escape(short)}(?!\w)")
        text = pattern.sub(full, text)
    return text


def canonical_postal_address(value: PostalAddressValue, locale: Locale) -> tuple[str, str, str, str]:
    return (
        canonical_street(value.street, locale),
        nfc(value.house_number).strip(),  # number and suffix exact
        nfc(value.postal_code).strip(),
        _WS_RE.sub(" ", nfc(value.locality)).strip().lower(),
    )


def canonical_reference_code(value: str, case_sensitive: bool = True) -> str:
    text = nfc(value)
    text = _REF_SPACE_RE.sub("", text).strip()
    if not case_sensitive:
        text = text.upper()
    return text


def canonical_form(
    value: str | PostalAddressValue | CalendarValue,
    entity_type: EntityType,
    locale: Locale,
    *,
    case_sensitive: bool = True,
) -> Any:
    if entity_type == "person_name":
        return canonical_person_name(str(value))
    if entity_type == "phone":
        return canonical_phone(str(value), locale)
    if entity_type == "email":
        return canonical_email(str(value))
    if entity_type == "calendar_value":
        if isinstance(value, CalendarValue):
            return canonical_calendar(value)
        return literal_form(value)  # unparseable shape: compare verbatim (fails honestly)
    if entity_type == "postal_address":
        if isinstance(value, PostalAddressValue):
            return canonical_postal_address(value, locale)
        return literal_form(value)
    if entity_type == "reference_code":
        return canonical_reference_code(str(value), case_sensitive=case_sensitive)
    raise ValueError(f"unknown entity type {entity_type}")


# --- parsing helpers for slot values (predictions are plain strings) ----------


def parse_slot_value(raw: str, entity_type: EntityType, locale: Locale) -> str | PostalAddressValue | CalendarValue:
    """Best-effort structuring of a predicted string into the gold value shape.

    Returns the raw string when the shape cannot be recovered; the canonical
    comparison then fails, which is the honest outcome.
    """
    text = nfc(raw).strip()
    if entity_type == "postal_address" and isinstance(raw, str):
        return _parse_postal_address(text, locale)
    if entity_type == "calendar_value" and isinstance(raw, str):
        return _parse_calendar(text, locale)
    return text


_POSTAL_RE = {
    "de-DE": re.compile(
        r"^(?P<street>.+?)\s+(?P<number>\d+\s*(?:[a-zA-Z]{1,4}|bis|ter)?(?:\s*-\s*\d+)?)\s*,?\s*(?P<postal>\d{5})\s+(?P<locality>\S.*)$"
    ),
    "fr-FR": re.compile(
        r"^(?P<number>\d+\s*[a-zA-Z]?),?\s+(?P<street>.+?)\s*,?\s*(?P<postal>\d{5})\s+(?P<locality>\S.*)$"
    ),
}

_MONTH_WORDS: dict[str, dict[str, int]] = {
    "de-DE": {
        "januar": 1,
        "februar": 2,
        "märz": 3,
        "maerz": 3,
        "april": 4,
        "mai": 5,
        "juni": 6,
        "juli": 7,
        "august": 8,
        "september": 9,
        "oktober": 10,
        "november": 11,
        "dezember": 12,
    },
    "fr-FR": {
        "janvier": 1,
        "février": 2,
        "fevrier": 2,
        "mars": 3,
        "avril": 4,
        "mai": 5,
        "juin": 6,
        "juillet": 7,
        "août": 8,
        "aout": 8,
        "septembre": 9,
        "octobre": 10,
        "novembre": 11,
        "décembre": 12,
        "decembre": 12,
    },
}

_DIGIT_WORD_RE = re.compile(r"\d+")


def _parse_postal_address(text: str, locale: Locale) -> str | PostalAddressValue:
    # locale shape first, then the other shape as fallback: both "street number"
    # and "number street" are legitimate textual address forms.
    for key in (locale, "fr-FR" if locale == "de-DE" else "de-DE"):
        pattern = _POSTAL_RE.get(key)
        if pattern is None:
            continue
        m = pattern.match(text)
        if m:
            return PostalAddressValue(
                street=m.group("street").strip(),
                house_number=_WS_RE.sub(" ", m.group("number")).strip(),
                postal_code=m.group("postal"),
                locality=m.group("locality").strip(),
            )
    return text


def _parse_calendar(text: str, locale: Locale) -> str | CalendarValue:
    # numeric form first: "14.05", "09.03.2026", "14/05/2027"
    m = re.fullmatch(r"\s*(\d{1,2})[./](\d{1,2})(?:[./](\d{4}))?\s*", text)
    if m:
        try:
            return CalendarValue(day=int(m.group(1)), month=int(m.group(2)),
                                 year=int(m.group(3)) if m.group(3) else None)
        except Exception:  # noqa: BLE001
            return text
    words = text.lower()
    day = month = year = None
    for word, num in _MONTH_WORDS.get(locale, {}).items():
        if word in words:
            month = num
            break
    days = _DIGIT_WORD_RE.findall(text)
    nums = [int(d) for d in days]
    if month is not None:
        # heuristics kept deliberately narrow: day is 1..31, a 4-digit >1000 is a year
        for n in nums:
            if 1000 < n <= 2100 and year is None:
                year = n
            elif day is None and 1 <= n <= 31:
                day = n
        if day is not None:
            try:
                return CalendarValue(day=day, month=month, year=year)
            except Exception:  # noqa: BLE001 - fall back to raw string
                return text
    return text
