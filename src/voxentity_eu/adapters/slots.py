"""Reference slot extractor: deterministic DE/FR parsers (docs/05, docs/06).

Design contract: the grammar may know the *task structure* (what a phone
number sounds like) but never template ids or canonical values. Parsing
failures return status="unsupported_parse" instead of guessing. Correction
markers replace the entity of the same type in scope (last mention wins),
not just any earlier number.

EXTRACTOR_VERSION freezes the rule set; changes require a new version and
must be re-frozen on dev before any test-set comparison is reported.

rex-3: also parses the written form ASR systems emit ("+49…", "a.b@c.de",
"11. Dezember", "09.03.2026", "MMJ-0105", "55a", FR street-first addresses).
rex-2 only covered the spoken form, so its 100% gold ceiling was circular.

rex-4 (from code-switching dev failures): correction markers match whole
words only (substring matching cut "manon" at "non"); English separators
(dot/underscore/dash) and digit words (zero..nine) are accepted; Irish "O'"
surnames stay one token.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from ..corpus.verbalize import (
    DIGITS_DE,
    DIGITS_FR,
    LETTER_NAMES_DE,
    LETTER_NAMES_FR,
    MONTHS_DE,
    MONTHS_FR,
    SPELL_DE,
    SPELL_FR,
)

EXTRACTOR_VERSION = "rex-4"

# --- correction markers (design list, not a linguistic census) -------------------

CORRECTION_MARKERS: dict[str, list[str]] = {
    "de-DE": [
        "entschuldigen sie", "entschuldigung", "moment, ich korrigiere mich",
        "moment, ich korrigiere", "ich korrigiere mich", "ich korrigiere",
        "moment", "nein, falsch", "richtig ist", "nicht", "sondern", "pardon",
        "verzeihung", "falsch", "nein",
    ],
    "fr-FR": [
        "pardon, je corrige", "pardon", "je corrige", "non, en fait",
        "en fait", "excusez-moi", "non", "corrigé", "mais", "pas", "attends", "c'est",
    ],
}

# --- reverse maps -----------------------------------------------------------------


def _invert(d: dict[str, str]) -> dict[str, str]:
    return {v.lower(): k for k, v in d.items()}


def _number_word_maps(locale: str) -> dict[str, int]:
    from ..corpus.verbalize import number_word

    out: dict[str, int] = {}
    for n in range(1000):
        try:
            out[number_word(n, locale)] = n
        except ValueError:
            break
    return out


def _compound_numbers(locale: str) -> dict[str, str]:
    """Number words >= 10 -> decimal digits (substituted before tokenizing).

    Only >= 10: single digit words stay words (digit map handles them), and
    articles like FR "un" / DE "ein" are never touched.
    """

    maps = _number_word_maps(locale)
    return {w: str(v) for w, v in maps.items() if v >= 10}


class LocaleMaps:
    def __init__(self, locale: str) -> None:
        self.locale = locale
        self.digits = _invert({str(i): (DIGITS_DE if locale == "de-DE" else DIGITS_FR)[i] for i in range(10)})
        self.digits.update({w: str(i) for i, w in enumerate(DIGITS_EN)})  # code-switched digits
        self.spell = _invert(SPELL_DE if locale == "de-DE" else SPELL_FR)
        self.letter_names = _invert(LETTER_NAMES_DE if locale == "de-DE" else LETTER_NAMES_FR)
        self.months = _invert(MONTHS_DE if locale == "de-DE" else MONTHS_FR)
        self.numbers = _number_word_maps(locale)
        # both alphabets accepted on input regardless of locale (ASR may echo either)
        other_spell = _invert(SPELL_FR if locale == "de-DE" else SPELL_DE)
        self.spell.update(other_spell)
        self.letter_to_word: dict[str, str] = {}
        for src in (self.spell, self.letter_names):
            for word, letter in src.items():
                self.letter_to_word.setdefault(letter, word)


@dataclass
class ExtractionResult:
    slots: list[dict[str, str]] = field(default_factory=list)
    status: str = "ok"  # ok | unsupported_parse | empty
    corrections_applied: int = 0
    evidence: str = ""


# --- tokenizer ----------------------------------------------------------------------


_TOKEN_RE = re.compile(r"(?<![\w'])o'[\w-]+|[\wäöüßéèêëïîôçûàâÄÖÜÉÈÊËÏÎÔÇÛÀÂ-]+|[.,;:!?+@]")
DIGITS_EN = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
DOT_WORDS = ("punkt", "point", "dot", ".")
UNDERSCORE_WORDS = ("unterstrich", "soulignement", "underscore")
DASH_WORDS = ("bindestrich", "tiret", "dash", "-")


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text)
    return [t for t in _TOKEN_RE.findall(text)]


def normalize_tokens(tokens: list[str]) -> list[str]:
    return [t.lower() for t in tokens]


def digits_in(token: str) -> str:
    return "".join(ch for ch in token if ch.isdigit())


# --- number sequence parsing -----------------------------------------------------------


def parse_number_stream(tokens: list[str], maps: LocaleMaps, *, allow_plus: bool = True) -> tuple[str, bool] | None:
    """Concatenate digit words / number words / raw digits into one digit string.

    Returns (digits, had_plus) or None if no numeric content. Bare number
    words (cardinals) contribute their value with natural zero padding:
    2-digit words -> 2 chars, with leading zero preserved as '0' + digits
    when the spoken chunk was a single digit word.
    """

    parts: list[str] = []
    had_plus = False
    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        if tok in (",", ".", ";"):
            i += 1
            continue
        if allow_plus and tok in ("plus", "+"):
            had_plus = True
            i += 1
            continue
        raw = digits_in(tok)
        if raw and not tok.replace(raw, "").isalpha():
            parts.append(raw)
            i += 1
            continue
        if tok in maps.digits:
            parts.append(maps.digits[tok])
            i += 1
            continue
        if tok in maps.numbers:
            value = maps.numbers[tok]
            parts.append(f"{value:02d}")
            i += 1
            continue
        i += 1
    if not parts:
        return None
    return "".join(parts), had_plus


def parse_letter_stream(tokens: list[str], maps: LocaleMaps) -> str | None:
    """Map spelling-alphabet words / letter names / raw letters to a string."""

    letters: list[str] = []
    for tok in tokens:
        if tok in maps.spell:
            letters.append(maps.spell[tok])
        elif tok in maps.letter_names and len(tok) > 1:
            letters.append(maps.letter_names[tok])
        elif len(tok) == 1 and tok.isalpha():
            letters.append(tok)
        else:
            return None if letters else None  # stop at first non-letter token
    return "".join(letters) if letters else None


def contiguous_letter_run(tokens: list[str], maps: LocaleMaps) -> list[str]:
    """Longest prefix (or any window) of pure letter tokens."""

    runs: list[list[str]] = []
    current: list[str] = []
    for tok in tokens:
        if tok in maps.spell or tok in maps.letter_names or (len(tok) == 1 and tok.isalpha()):
            current.append(tok)
        else:
            if current:
                runs.append(current)
            current = []
    if current:
        runs.append(current)
    return max(runs, key=len) if runs else []


# --- per-type parsers ----------------------------------------------------------------


def _segments(transcript: str, locale: str) -> list[list[str]]:
    """Split on correction markers; substitute compound numbers; tokenize."""

    text = " " + unicodedata.normalize("NFC", transcript.lower()) + " "
    markers = sorted(CORRECTION_MARKERS[locale], key=len, reverse=True)
    for marker in markers:
        text = re.sub(rf"(?<![\w']){re.escape(marker)}(?![\w'])", " ¤ ", text)
    for word, digits in sorted(_compound_numbers(locale).items(), key=lambda kv: -len(kv[0])):
        text = re.sub(rf"(?<![\w-]){re.escape(word)}(?![\w-])", digits, text)
    segments = [seg.strip() for seg in text.split("¤") if seg.strip()]
    out = [normalize_tokens(tokenize(seg)) for seg in segments]
    return [seg for seg in out if seg]


def extract(transcript: str, requested_type: str, locale: str) -> ExtractionResult:
    maps = LocaleMaps(locale)
    segments = _segments(transcript, locale)
    if not segments:
        return ExtractionResult(status="empty")

    result = ExtractionResult()
    candidates: list[str] = []
    for seg in segments:
        value = _extract_from_segment(seg, requested_type, maps, locale)
        if value is not None:
            candidates.append(value)
    result.corrections_applied = max(0, len(segments) - 1) if candidates else 0
    if not candidates:
        result.status = "unsupported_parse"
        return result
    value = candidates[-1]  # correction semantics: last mention wins
    result.slots = [{"type": requested_type, "value": value}]
    return result


def _extract_from_segment(seg: list[str], entity: str, maps: LocaleMaps, locale: str) -> str | None:
    if entity == "phone":
        return _extract_phone(seg, maps)
    if entity == "reference_code":
        return _extract_reference(seg, maps)
    if entity == "email":
        return _extract_email(seg, maps)
    if entity == "calendar_value":
        return _extract_calendar(seg, maps)
    if entity == "postal_address":
        return _extract_address(seg, maps, locale)
    if entity == "person_name":
        return _extract_person(seg, maps, locale)
    return None


CC = {"de-DE": "49", "fr-FR": "33"}


def _extract_phone(seg: list[str], maps: LocaleMaps) -> str | None:
    parsed = parse_number_stream(seg, maps)
    if parsed is None:
        return None
    digits, had_plus = parsed
    if had_plus or digits.startswith("00"):
        if digits.startswith("00"):
            return "+" + digits[2:]
        if digits.startswith(CC[maps.locale]):
            return "+" + digits
        return "+" + digits
    # national form: trunk zero rule mirrors the declared locale normalizer
    if digits.startswith("0"):
        return "+" + CC[maps.locale] + digits[1:]
    return digits


_WRITTEN_CODE = re.compile(r"([a-z]{1,4})-(\d{2,})")


def _extract_reference(seg: list[str], maps: LocaleMaps) -> str | None:
    written = None
    for tok in seg:
        m = _WRITTEN_CODE.fullmatch(tok)
        if m and m.group(1) not in maps.spell:
            written = f"{m.group(1).upper()}-{m.group(2)}"
    if written:
        return written
    # "Bravo Oscar-0081": alphabet word glued to the digits by a hyphen
    split: list[str] = []
    for tok in seg:
        head, sep, tail = tok.rpartition("-")
        if sep and tail.isdigit() and (head in maps.spell or head in maps.letter_names):
            split.extend([head, "-", tail])
        else:
            split.append(tok)
    seg = split
    # pattern: letters (alphabet or letter names or raw) [hyphen word] digits
    letter_run = contiguous_letter_run(seg, maps)
    letters = parse_letter_stream(letter_run, maps) if letter_run else None
    parsed = parse_number_stream(seg, maps, allow_plus=False)
    digits = parsed[0] if parsed else ""
    if letters and digits:
        return f"{letters.upper()}-{digits}"
    if letters and any(t in DASH_WORDS for t in seg):
        return letters.upper()
    return None


def _extract_email(seg: list[str], maps: LocaleMaps) -> str | None:
    at_words = ("ät", "arobase", "at", "@")
    at_idx = None
    for i, tok in enumerate(seg):
        if tok in at_words:
            at_idx = i
            break
    if at_idx is None:
        return None
    local_toks = seg[:at_idx]
    domain_toks = seg[at_idx + 1 :]
    local = _join_local(local_toks, maps).strip(".")
    domain = _join_domain(domain_toks, maps).strip(".")
    if not local or not domain:
        return None
    return f"{local}@{domain}"


_LOCAL_STOPS = {
    # carrier words that terminate a dictated local part when scanning back
    "meine", "die", "der", "ist", "an", "das", "im", "system", "schicken", "sie",
    "es", "adresse", "mailadresse", "e", "mail", "la", "le", "dans", "envoyez",
    "diktiere", "buchstabiere", "achtung", "notieren", "ich", "langen", "langsam",
    "notez", "j", "vous", "lentement", "caractère", "par", "signe", "à",
    "l'adresse", "mon", "c'est", "est", "attention", "pardon", "korrigiere",
    "nein", "moment", "richtig", "nicht", "sondern", "ma", "lautet",
    "wiederhole", "nummer", "répète", "système", "delivrée",
}


def _join_local(tokens: list[str], maps: LocaleMaps) -> str:
    """Scan backwards from the @ marker until a carrier word or the start."""

    out: list[str] = []
    # a lone alphabet word ("gustav.kühn") is a name, not a spelled letter
    spelled = sum(t in maps.spell for t in tokens) >= 2
    for tok in reversed(tokens):
        if tok in _LOCAL_STOPS or tok in (",", ":", ";"):
            break
        if tok in DOT_WORDS:
            out.append(".")
        elif tok in UNDERSCORE_WORDS:
            out.append("_")
        elif tok in DASH_WORDS[:-1]:
            out.append("-")
        elif spelled and tok in maps.spell:
            out.append(maps.spell[tok])
        elif tok in maps.letter_names and len(tok) > 2:
            out.append(maps.letter_names[tok])
        elif tok in maps.numbers:
            out.append(str(maps.numbers[tok]))
        elif tok in maps.digits:
            out.append(maps.digits[tok])
        elif tok.replace("_", "").isalnum():
            out.append(tok)
        elif (
            "-" in tok
            and all(part.isalnum() for part in tok.split("-"))
            and not any(part in _LOCAL_STOPS for part in tok.split("-"))
        ):
            out.append(tok)
        else:
            break
    return "".join(reversed(out))


def _join_domain(tokens: list[str], maps: LocaleMaps) -> str:
    """Domain = word (punkt word)*; anything after the last part without a
    following punkt is frame tail and stops the scan."""

    def wordish(tok: str) -> bool:
        if tok in maps.spell and len(tok) > 3:
            return True
        return tok.isalnum() and len(tok) <= 10

    parts: list[str] = []
    current: list[str] = []
    saw_dot = False
    for tok in tokens:
        if tok in DOT_WORDS:
            if current:
                parts.append("".join(current))
                current = []
            saw_dot = True
            continue
        if wordish(tok):
            if saw_dot and current:
                break  # word after TLD without another dot -> frame tail
            current.append(maps.spell.get(tok, tok) if (tok in maps.spell and len(tok) > 3) else tok)
        else:
            break
    if current:
        parts.append("".join(current))
    return ".".join(parts) if parts else ""


_NUMERIC_DATE = re.compile(r"(?<!\d)(\d{1,2}) \. (\d{1,2})(?: \. (\d{4}))?(?!\d)")


def _extract_calendar(seg: list[str], maps: LocaleMaps) -> str | None:
    found = None
    for m in _NUMERIC_DATE.finditer(" ".join(seg)):
        d, mo = int(m.group(1)), int(m.group(2))
        if 1 <= d <= 31 and 1 <= mo <= 12:
            found = f"{d:02d}.{mo:02d}" + (f".{m.group(3)}" if m.group(3) else "")
    if found:
        return found
    month = None
    month_idx = None
    for i, tok in enumerate(seg):
        if tok in maps.months:
            month = maps.months[tok]
            month_idx = i
            break
    if month is None:
        return None
    before = seg[:month_idx]
    while before and before[-1] == ".":  # written ordinal "11. Dezember"
        before = before[:-1]
    after = seg[month_idx + 1 :]
    day = _parse_day(before, maps)
    if day is None:
        return None
    year = _parse_year(after, maps)
    return f"{day:02d}.{month:02d}" + (f".{year}" if year else "")


_DE_ORDINAL_STEMS = {"erst": 1, "dritt": 3, "sieb": 7, "ach": 8}


def _parse_day(tokens: list[str], maps: LocaleMaps) -> int | None:
    if not tokens:
        return None
    tok = tokens[-1]
    if maps.locale == "de-DE":
        for suffix in ("ten", "en", "te"):
            if tok.endswith(suffix):
                stem = tok[: -len(suffix)]
                if stem in maps.numbers:
                    return maps.numbers[stem]
                if stem in maps.digits:
                    return int(maps.digits[stem])
                if stem in _DE_ORDINAL_STEMS:
                    return _DE_ORDINAL_STEMS[stem]
    else:
        if tok.endswith("er"):
            tok = tok[:-2]
        if tok.startswith("1er"):
            tok = "premier"
    if tok in maps.numbers:
        return maps.numbers[tok]
    if tok in maps.digits:
        return int(maps.digits[tok])
    raw = digits_in(tok)
    if raw and len(raw) <= 2:
        return int(raw)
    return None


def _parse_year(tokens: list[str], maps: LocaleMaps) -> int | None:
    if not tokens:
        return None
    joined = parse_number_stream(tokens, maps, allow_plus=False)
    if joined and len(joined[0]) == 4:
        return int(joined[0])
    # FR "deux mille vingt-sept" (compound substitution keeps 'mille' apart)
    if "mille" in tokens:
        i = tokens.index("mille")
        if i > 0:
            head = digits_in(tokens[i - 1]) or maps.digits.get(tokens[i - 1], "")
            if head:
                rest = parse_number_stream(tokens[i + 1 :], maps, allow_plus=False)
                rest_digits = rest[0] if rest else "0"
                return int(head) * 1000 + int(rest_digits)
    tok = tokens[0]
    if tok in maps.numbers and 1900 <= maps.numbers[tok] <= 2100:
        return maps.numbers[tok]
    if maps.locale == "de-DE":
        m = re.match(r"zweitausend(.+)", tok)
        if m and m.group(1) in maps.numbers:
            return 2000 + maps.numbers[m.group(1)]
        m = re.match(r"(\w+)hundert(\w*)", tok)
        if m:
            h = maps.numbers.get(m.group(1))
            rest = maps.numbers.get(m.group(2)) if m.group(2) else 0
            if h is not None and rest is not None and 1000 <= h * 100 + rest <= 2100:
                return h * 100 + rest
    return None


_STREET_CARRIERS_DE = {
    "meine", "adresse", "ist", "die", "lautet", "lieferadresse", "liefern",
    "sie", "an", "ich", "wohne", "in", "der", "das", "strasse", "straße", "lieferung",
    "schicken", "es", "für", "bitte",
    "entschuldigen", "moment", "korrigiere", "richtig", "ganz", "alles",
}
_STREET_CARRIERS_FR = {
    "mon", "adresse", "est", "de", "livraison", "l", "la", "le", "c'est",
    "j'habite", "au", "livrez", "envoyez", "chez", "pour", "pardon", "non",
    "corrigé", "attend", "mais", "attention", "notez", "tout",
}
_HOUSE_SUFFIX_WORDS = {"bis": "bis", "ter": "ter"}


def _extract_address(seg: list[str], maps: LocaleMaps, locale: str) -> str | None:
    labeled_keys = {"postleitzahl", "hausnummer", "ort", "code", "numéro", "numero", "ville"}
    if any(t in labeled_keys for t in seg):
        return _extract_address_labeled(seg, maps, locale)
    seg = _split_house_suffixes(seg)
    runs = _joined_digit_runs(seg, maps)[0]
    postal = None
    postal_span = None
    for run, span in runs:
        if len(run) == 5:
            postal, postal_span = run, span  # prefer the last 5-run
        elif len(run) > 5 and len(seg[span[1]]) == 5 and seg[span[1]].isdigit():
            # written "Weg 61 37672 Ort" without comma: last token is the postal code
            postal, postal_span = seg[span[1]], (span[1], span[1])
    if postal is None:
        return None
    start, end = postal_span
    _loc_tail = {"bitte", "alles", "notieren", "notez", "tout", "attends", "écoutez", "teilen"}
    locality_toks = []
    for t in seg[end + 1 :]:
        if t in (",", ".", ";", ":", "!", "?"):
            if locality_toks:
                break
            continue
        if (t.isalpha() or "-" in t) and t not in _loc_tail:
            locality_toks.append(t)
    locality = " ".join(t.title() for t in locality_toks[:4])
    if not locality:
        return None
    before = seg[:start]
    carriers = _STREET_CARRIERS_DE if locale == "de-DE" else _STREET_CARRIERS_FR
    if locale == "fr-FR":
        # spoken FR order: [house run] [street words] , [postal] [locality]
        house, house_end = _first_house_run(before, maps)
        if house is not None:
            street = " ".join(
                t for t in before[house_end + 1 :] if t.isalpha() and t not in carriers
            ).title()
            if street:
                return f"{street} {house}, {postal} {locality}"
    # DE order, also written FR: [street words] [house run] , [postal] [locality]
    house, street_end = _house_run_before(before, maps)
    if house is None:
        return None
    street = " ".join(t for t in before[:street_end] if t.isalpha() and t not in carriers).title()
    if not street:
        return None
    return f"{street} {house}, {postal} {locality}"


_HOUSE_SUFFIX_TOKEN = re.compile(r"(\d{1,4})(bis|ter|[a-z])")


def _split_house_suffixes(seg: list[str]) -> list[str]:
    out: list[str] = []
    for tok in seg:
        m = _HOUSE_SUFFIX_TOKEN.fullmatch(tok)
        out.extend([m.group(1), m.group(2)] if m else [tok])
    return out


def _house_run_before(tokens: list[str], maps: LocaleMaps) -> tuple[str | None, int]:
    """Last digit run before the postal run; optional spelled suffix lowercase.

    Returns (house, street_end) where street_end excludes the house run.
    """

    runs = _joined_digit_runs(tokens, maps)[0]
    if not runs:
        return None, -1
    run, (start, end) = runs[-1]
    if len(run) > 3:
        return None, -1
    house = str(int(run)) if not run.startswith("0") else run
    if end + 1 < len(tokens):
        nxt = tokens[end + 1]
        if nxt in maps.spell and len(nxt) > 2:
            house += maps.spell[nxt]  # DE suffix convention: lowercase
        elif nxt in _HOUSE_SUFFIX_WORDS or (len(nxt) == 1 and nxt.isalpha()):
            house += nxt  # written "55a" / "28ter" split by _split_house_suffixes
    return house, start


def _first_house_run(tokens: list[str], maps: LocaleMaps) -> tuple[str | None, int]:
    """First digit run (FR: number comes first); returns (house, house_end_inclusive)."""

    runs = _joined_digit_runs(tokens, maps)[0]
    if not runs:
        return None, -1
    run, (start, end) = runs[0]
    if len(run) > 3:
        return None, -1
    house = str(int(run)) if not run.startswith("0") else run
    suffix_end = end
    if end + 1 < len(tokens):
        nxt = tokens[end + 1]
        if nxt in _HOUSE_SUFFIX_WORDS:
            house += _HOUSE_SUFFIX_WORDS[nxt]
            suffix_end = end + 1
    return house, suffix_end


def _extract_address_labeled(seg: list[str], maps: LocaleMaps, locale: str) -> str | None:
    def find_idx(*keys: str) -> int | None:
        for i, t in enumerate(seg):
            if t in keys:
                return i
        return None

    street_key = find_idx("strasse", "straße", "rue", "chemin", "allee", "allée", "weg")
    house_key = find_idx("hausnummer", "numéro", "numero")
    postal_key = find_idx("postleitzahl", "code")
    city_key = find_idx("ort", "stadt", "ville")
    if street_key is None or house_key is None or postal_key is None:
        return None
    street = " ".join(
        t for t in seg[street_key + 1 : min(house_key, postal_key)]
        if t.isalpha() and t not in ("ist", "le", "la", "est", "die", "der", "das", "l")
    ).title()
    house_run = _joined_digit_runs(seg[house_key + 1 : house_key + 6], maps)[0]
    house = None
    if house_run:
        run, _ = house_run[0]
        house = str(int(run))
    if locale == "de-DE" and house_run:
        for nxt in seg[house_key + 1 : house_key + 6]:
            if nxt in maps.spell and len(nxt) > 2:
                house = (house or "") + maps.spell[nxt]
                break
    elif locale == "fr-FR":
        for t in seg[house_key + 1 : house_key + 5]:
            if t in _HOUSE_SUFFIX_WORDS and house:
                house += _HOUSE_SUFFIX_WORDS[t]
    postal_run = _joined_digit_runs(seg[postal_key + 1 : postal_key + 8], maps)[0]
    postal = next((r for r, _ in postal_run if len(r) == 5), None)
    locality = None
    if city_key is not None:
        _loc_stops = {"ist", "für", "teil", "bestandteil", "est", "élément", "par", "pour",
                     "bitte", "alles", "notieren", "écoutez", "notez", "tout"}
        locality = " ".join(
            t.title() for t in seg[city_key + 1 :]
            if (t.isalpha() or "-" in t) and t not in _loc_stops
        )
    if street and house and postal and locality:
        return f"{street} {house}, {postal} {locality}"
    return None


def _joined_digit_runs(seg: list[str], maps: LocaleMaps) -> tuple[list[tuple[str, tuple[int, int]]], list[int]]:
    runs: list[tuple[str, tuple[int, int]]] = []
    current: list[str] = []
    start = None
    for i, tok in enumerate(seg):
        is_num = (
            tok in maps.digits
            or (tok in maps.numbers and maps.numbers[tok] < 100)
            or (digits_in(tok) and not tok.replace(digits_in(tok), "").isalpha())
        )
        if is_num:
            if start is None:
                start = i
            if tok in maps.digits:
                current.append(maps.digits[tok])
            elif tok in maps.numbers:
                current.append(f"{maps.numbers[tok]:02d}")
            else:
                current.append(digits_in(tok))
        else:
            if current:
                runs.append(("".join(current), (start, i - 1)))
                current, start = [], None
    if current:
        runs.append(("".join(current), (start, len(seg) - 1)))
    return runs, []


def _extract_person(seg: list[str], maps: LocaleMaps, locale: str) -> str | None:
    # spelled surname: alphabet run IS the surname; keep spoken first names
    letter_run = contiguous_letter_run(seg, maps)
    if letter_run and len(letter_run) >= 3:
        spelled = parse_letter_stream(letter_run, maps)
        if spelled:
            tokens = [t for t in seg if t not in letter_run]
            words = _name_words(tokens, locale)
            return " ".join(words + [spelled.title()])
    words = _name_words(seg, locale)
    if not words:
        return None
    return " ".join(words)


_NAME_STOP_DE = {
    "mein", "name", "ist", "ich", "heiße", "heisse", "der", "die", "das", "auf", "den",
    "bitte", "notieren", "frau", "herr", "es", "ganz", "so", "geschrieben", "mit",
    "umlaut", "nachname", "buchstabiere", "diktiere", "und", "sie", "hören", "genau",
    "zu", "lautet", "namen", "bin", "mich", "vorname", "moment", "korrigiere", "buchstabiert",
    "entschuldigen", "pardon", "verzeihung", "richtig", "falsch", "nein", "sondern",
    "wiederhole", "langsam", "sage", "zahlen", "pareil", "viele", "gleiche",
}
_NAME_STOP_FR = {
    "je", "m", "appelle", "mon", "nom", "est", "c'est", "au", "de", "madame",
    "monsieur", "le", "la", "avec", "les", "accents", "notez", "bien", "épelle",
    "dicte", "famille", "écoutez", "et", "précisément", "me", "convient", "pour",
    "inscrivez", "rendez", "vous", "être", "un", "une", "voudrais", "passe", "c",
    "écoute", "beaucoup", "chiffres", "répète", "lentement", "parties", "partie",
    "corrigé", "excusez", "non", "mais", "pas", "en", "fait", "moi", "épelle-le", "suis",
}


def _name_words(tokens: list[str], locale: str) -> list[str]:
    stop = _NAME_STOP_DE if locale == "de-DE" else _NAME_STOP_FR
    words = [
        t
        for t in tokens
        if t.replace("-", "").replace("'", "").isalpha() and t not in stop and len(t) > 1
    ]
    if not words:
        return []
    return words[:3]  # first + last (+ particle); documented grammar bound
