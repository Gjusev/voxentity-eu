"""Original, deterministic value pools (no scraping of real people's data).

Fiction-policy (docs/03-data.md §A):
- emails use only example.com / example.org (IANA-reserved, S15);
- phone numbers are explicit test sequences: no DE/FR regulator-verified
  fictional range could be confirmed, so nothing here is claimed reserved;
- addresses are invented combinations, no geocoding, no associated identity;
- names are ordinary constructions; coincidental equality with real persons
  is possible and never claimed otherwise.
"""

from __future__ import annotations

import hashlib

MASTER_SEED = 20261013


def _rng_stream(label: str):
    """Deterministic integer stream derived from a stable label."""
    counter = 0
    while True:
        digest = hashlib.sha256(f"{MASTER_SEED}:{label}:{counter}".encode()).hexdigest()
        yield int(digest[:8], 16)
        counter += 1


# --- person names ----------------------------------------------------------------

# Deliberately includes graphemic traps: ß/ss, umlauts, accents, silent letters.
NAMES_DE = [
    "Weiß", "Weiss", "Strauß", "Großmann", "Grünwald", "Fröhlich", "Überall", "Müller-Bachmann",
    "Löwenstein", "Hübner", "Kühn", "Nüsslein", "Schäfer", "Jäger", "Krüger",
    "Thalberg", "Vogelsang", "Winterstein", "Zimmerling", "Amstein", "Bergmoser", "Dornbusch",
    "Eichkamp", "Feldner", "Glanzmann", "Hochrainer", "Kirchleitner", "Lamprecht", "Mondstein",
    "Nebelhorn", "Osterwalder", "Pfisterer", "Quenstedt", "Rabenhorst", "Steinbrecher",
]
FIRST_DE = [
    "Anna", "Ben", "Clara", "David", "Emil", "Frieda", "Gustav", "Hanna", "Jonas", "Katharina",
    "Lukas", "Marlene", "Niklas", "Ottilie", "Paul", "Rosa", "Stefan", "Theresia", "Ulrich", "Vera",
]
NAMES_FR = [
    "Thibault", "Christelle", "Guillemette", "Bérangère", "Cédric", "Françoise", "Éloi", "Maëlys",
    "Noémie", "Aurélie", "Séverine", "Rémi", "Loïc", "Yaël", "Armelle", "Vivienne",
    "Charbonnier", "Lefèvre", "Dumas-Regnier", "Beaulieu", "Châteauvert", "Montclair",
    "Rousselet", "Vandenberghe", "Périgord", "Larivière", "Marchandet", "Sauvageot",
    "Théroulde", "Vigneron", "Aubertin", "Brissot", "Courtemanche", "Delacroix-Verne",
]
FIRST_FR = [
    "Alice", "Bruno", "Camille", "Damien", "Élise", "Fabrice", "Géraldine", "Hugo", "Inès",
    "Jules", "Karine", "Léon", "Manon", "Nicolas", "Océane", "Pénélope", "Quentin", "Raphaëlle",
    "Simon", "Tatiana",
]
NAMES_ES = [
    "García", "Martínez", "Álvarez", "Fernández", "Muñoz", "Peña", "Núñez", "Jiménez-Villar",
    "Ordoñez", "Hernández", "Gómez", "Sáez", "Castañeda", "Ibáñez", "Moreno-Luna",
    "Belmonte", "Carrillo", "Villanueva", "Zamorano", "Alcaraz", "Escamilla", "Tejadillos",
    "Fontaneda", "Rascacielos", "Pradoverde", "Robledillo", "Sotoserrano", "Valdecantos",
    "Olmedillo", "Cruzada", "Arrevuelta", "Quintanilla", "Salceda", "Melgar de Arriba",
]
FIRST_ES = [
    "Ana", "Bruno", "Carmen", "David", "Elena", "Fernando", "Gloria", "Hugo", "Irene", "Javier",
    "Karen", "Lucas", "María", "Nicolás", "Olivia", "Pablo", "Raquel", "Sergio", "Tomás", "Úrsula",
]

FIRSTS = {"de-DE": FIRST_DE, "fr-FR": FIRST_FR, "es-ES": FIRST_ES}
SURNAMES = {"de-DE": NAMES_DE, "fr-FR": NAMES_FR, "es-ES": NAMES_ES}
GRAPHEMIC_TRAPS = {"de-DE": "ßüöä", "fr-FR": "éèëïôç", "es-ES": "ñáéíóú"}


def person_pool(locale: str, count: int, *, tricky_only: bool = False) -> list[str]:
    firsts = FIRSTS[locale]
    lasts = SURNAMES[locale]
    if tricky_only:
        traps = GRAPHEMIC_TRAPS[locale]
        lasts = [n for n in lasts if any(c in n.lower() for c in traps)]
    stream = _rng_stream(f"person-{locale}" + ("-tricky" if tricky_only else ""))
    combos: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    while len(combos) < count:
        pair = (next(stream) % len(firsts), next(stream) % len(lasts))
        if pair in seen:
            continue
        seen.add(pair)
        combos.append(pair)
    return [f"{firsts[a]} {lasts[b]}" for a, b in combos]


# --- phones ----------------------------------------------------------------------

def _national_phone(locale: str, stream) -> str:
    if locale == "de-DE":
        # mobile-style national form: 017x + 7 digits (11 digits incl trunk)
        return "017" + str(next(stream) % 10) + f"{next(stream) % 10**7:07d}"
    if locale == "fr-FR":
        return "0" + str(6 + next(stream) % 2) + f"{next(stream) % 10**8:08d}"
    # es-ES: 9-digit national number, mobile heads 6/7, NO trunk zero
    return str(6 + next(stream) % 2) + f"{next(stream) % 10**8:08d}"


# locales whose national form has no trunk zero (ES keeps all 9 digits)
TRUNKLESS = {"de-DE": False, "fr-FR": False, "es-ES": True}


def phone_pool(locale: str, count: int) -> list[str]:
    from .verbalize import COUNTRY_CODES

    cc = COUNTRY_CODES[locale]
    stream = _rng_stream(f"phone-{locale}")
    out: list[str] = []
    seen: set[str] = set()
    while len(out) < count:
        national = _national_phone(locale, stream)
        rest = national if TRUNKLESS[locale] else national[1:]
        intl = "+" + cc + rest
        if intl in seen:
            continue
        seen.add(intl)
        out.append(intl)
    return out


def tricky_phone_pool(locale: str, count: int) -> list[str]:
    """Phonetically hard numbers: repeats, runs, confusable pairs (60/70 in FR)."""

    from .verbalize import COUNTRY_CODES

    cc = COUNTRY_CODES[locale]
    base = {"de-DE": "17", "fr-FR": "6", "es-ES": "6"}[locale]
    patterns = [
        base + "55" + "4433", base + "12" + "3456", base + "77" + "7700",
        base + "66" + "0660", base + "19" + "9911", base + "80" + "0808",
    ]
    if locale == "fr-FR":
        patterns += [base + "60" + "7060", base + "70" + "0670", base + "16" + "6161"]
    elif locale == "es-ES":
        # 60/70 and seis/siete confusions under a 9-digit national number
        patterns += [base + "60" + "7060", base + "17" + "0717", base + "16" + "6161"]
    else:
        patterns += [base + "62" + "2662", base + "90" + "0909", base + "45" + "5445"]
    out: list[str] = []
    for i, p in enumerate(patterns):
        out.append(f"+{cc}{p}{i:02d}")
        if len(out) >= count:
            break
    return out


# --- emails ----------------------------------------------------------------------

EMAIL_DOMAINS = ["example.com", "example.org"]


# base chain for surname-derived local parts: EXACTLY the historical de/fr
# behavior (no umlauts here — "kühn" must stay "kühn" in the de/fr corpus)
_BASE_LOCAL = str.maketrans("ßéèëïôç", "seeeioc")
# FR post-local strip (historical); ES strip for its own pool
_FR_LOCAL = str.maketrans("éèçïê", "eecie")
_ES_LOCAL = str.maketrans("áéíóúñü", "aeiounu")


def email_pool(locale: str, count: int) -> list[str]:
    firsts = FIRSTS[locale]
    lasts = [n.split()[0].lower().translate(_BASE_LOCAL) for n in SURNAMES[locale]]
    stream = _rng_stream(f"email-{locale}")
    out: list[str] = []
    seen: set[str] = set()
    while len(out) < count:
        style = next(stream) % 4
        f = firsts[next(stream) % len(firsts)].lower()
        last_name = lasts[next(stream) % len(lasts)]
        domain = EMAIL_DOMAINS[next(stream) % 2]
        if style == 0:
            local = f"{f}.{last_name}"
        elif style == 1:
            local = f"{f}{last_name}{next(stream) % 100:02d}"
        elif style == 2:
            local = f"{f}_{last_name}"
        else:
            local = f"{f}.{last_name}{next(stream) % 10}"
        if locale == "fr-FR":
            local = local.translate(_FR_LOCAL)
        elif locale == "es-ES":
            local = local.translate(_ES_LOCAL)
        addr = f"{local}@{domain}"
        if addr in seen:
            continue
        seen.add(addr)
        out.append(addr)
    return out


def tricky_email_pool(locale: str, count: int) -> list[str]:
    """Local parts with visually/phonetically ambiguous characters."""

    stream = _rng_stream(f"email-tricky-{locale}")
    shapes = ["arnold.m{d}", "cornelia.l{d}", "oliver.b{d}", "silke.rn{d}", "marion.in{d}",
              "hildegard.m{d}", "florian.v{d}", "isabelle.lle{d}", "maximilian.nn{d}", "sylvie.w{d}"]
    out = []
    for i, shape in enumerate(shapes):
        domain = EMAIL_DOMAINS[i % 2]
        local = shape.format(d=next(stream) % 100)
        out.append(f"{local}@{domain}")
        if len(out) >= count:
            break
    return out


# --- calendars ---------------------------------------------------------------------

def calendar_pool(locale: str, count: int) -> list[tuple[int, int, int | None]]:
    stream = _rng_stream(f"cal-{locale}")
    out: list[tuple[int, int, int | None]] = []
    seen: set[tuple[int, int, int | None]] = set()
    years = [2026, 2027, 2028, None]
    while len(out) < count:
        year = years[next(stream) % len(years)]
        month = 1 + next(stream) % 12
        day = 1 + next(stream) % 28
        key = (day, month, year)
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def tricky_calendar_pool(locale: str, count: int) -> list[tuple[int, int, int | None]]:
    """Digit-swap-prone dates: 13/30, 2026/2062, juin/juillet, März/Mai."""

    base = [
        (13, 6, 2026), (30, 6, 2026), (2, 6, 2027), (17, 7, 2027), (9, 6, 2062),
        (30, 7, 2026), (5, 3, 2032), (5, 5, 2032), (23, 3, 2063), (23, 5, 2036),
        (14, 1, 2029),
    ]
    return base[:count]


# --- addresses ----------------------------------------------------------------------

STREETS_DE = [
    "Ahornweg", "Birkenstraße", "Clematisweg", "Dahlienweg", "Eichenweg", "Falkenstraße",
    "Gartenweg", "Hainbuchenstraße", "Immenweg", "Jasminenweg", "Kastanienallee",
    "Lindenstraße", "Magnolienweg", "Nelkenweg", "Orchideenweg", "Platanenallee",
    "Quittenweg", "Rosenstraße", "Silberweg", "Tulpenweg", "Ulmenweg", "Veilchenweg",
    "Weidenstraße", "Wiesengang",
]
LOCALITIES_DE = [
    "Blumental", "Felsenbrunn", "Hainstadt", "Kirchseeon am Wald", "Lindenhain", "Morgenfeld",
    "Nordwalde", "Osterheim", "Rosental", "Steinbach", "Talheim", "Wiesendorf",
]
STREETS_FR = [
    "Rue des Acacias", "Rue des Bleuets", "Chemin des Cerisiers", "Rue des Dahlias",
    "Allée des Érables", "Rue des Fontaines", "Chemin des Glycines", "Rue des Hortensias",
    "Allée des Iris", "Rue des Jonquilles", "Chemin des Lilas", "Rue des Marguerites",
    "Allée des Noisetiers", "Rue des Orchidées", "Chemin des Pivoines", "Rue des Quinconces",
    "Allée des Robiniers", "Rue des Seringats", "Chemin des Tilleuls", "Rue des Vignes",
]
LOCALITIES_FR = [
    "Beaulieu-sur-Orne", "Clairval", "Fontenoy-le-Bois", "Grandvaux", "Montreuil-le-Sec",
    "Neuville-aux-Bois", "Perrigny", "Roquevaire", "Saint-Éloi-sur-Loire", "Valbonnet",
    "Verneuil-l'Étang", "Villefranche-le-Vert",
]


# ES streets and localities are invented combinations of generic street types
# and toponymic morphemes; no geocoding, no associated identity (same fiction
# policy as DE/FR, docs/03 §A).
STREETS_ES = [
    "Calle del Aliso", "Calle de los Nogales", "Avenida de la Vega", "Camino del Cerezo",
    "Paseo de las Acacias", "Plaza de la Fuente", "Calle del Olmedo", "Avenida de los Chopos",
    "Camino de la Dehesa", "Calle de las Adelfas", "Paseo del Mirador", "Calle del Tejo",
    "Avenida de la Encomienda", "Plaza del Rosal", "Calle de los Tilos", "Camino del Prado",
    "Paseo de la Alameda", "Calle del Madroño", "Avenida de los Fresnos", "Plaza de la Cisterna",
]
LOCALITIES_ES = [
    "Valdefresno", "Sotillo de la Vega", "Fuentealmendra", "Villarejo del Monte",
    "Casas de la Pradera", "El Saz Nuevo", "Montearagón la Baja", "Robledal de Arriba",
    "La Nava Chica", "Peñalcordero", "Torreveladiego", "Aldehuela del Campo",
]
STREETS = {"de-DE": STREETS_DE, "fr-FR": STREETS_FR, "es-ES": STREETS_ES}
LOCALITIES = {"de-DE": LOCALITIES_DE, "fr-FR": LOCALITIES_FR, "es-ES": LOCALITIES_ES}
SUFFIXES = {"de-DE": ["", "a", "b"], "fr-FR": ["", "bis", "ter"], "es-ES": ["", "bis"]}


def address_pool(locale: str, count: int, *, variant: str = "") -> list[dict]:
    streets = STREETS[locale]
    localities = LOCALITIES[locale]
    stream = _rng_stream(f"addr-{locale}{variant}")
    out: list[dict] = []
    seen: set[tuple] = set()
    suffixes = SUFFIXES[locale]
    while len(out) < count:
        street = streets[next(stream) % len(streets)]
        num = 1 + next(stream) % 180
        suffix = suffixes[next(stream) % len(suffixes)] if next(stream) % 3 == 0 else ""
        house = f"{num}{suffix}"
        postal = f"{10000 + next(stream) % 89999:05d}"
        locality = localities[next(stream) % len(localities)]
        key = (street, house, postal, locality)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "street": street,
                "house_number": house,
                "postal_code": postal,
                "locality": locality,
            }
        )
    return out


# --- reference codes ------------------------------------------------------------------

def reference_pool(locale: str, count: int) -> list[str]:
    stream = _rng_stream(f"ref-{locale}")
    letters = "ABCDEFGHJKLMNPRSTUWXYZ"  # excludes easily-confused I, O, Q
    out: list[str] = []
    seen: set[str] = set()
    while len(out) < count:
        n_letters = 2 if next(stream) % 2 == 0 else 3
        code = "".join(letters[next(stream) % len(letters)] for _ in range(n_letters))
        digits = f"{next(stream) % 10000:04d}"
        ref = f"{code}-{digits}"
        if ref in seen:
            continue
        seen.add(ref)
        out.append(ref)
    return out


def tricky_reference_pool(locale: str, count: int) -> list[str]:
    """Codes whose letter shapes collide with digits (O~0, B~8, S~5, Z~2)."""

    shapes = ["BO-0081", "OS-5052", "ZB-2280", "SB-8855", "GO-0047", "DZ-2025",
              "BOS-8005", "ZOS-2008", "GSB-5588", "GDZ-2022"]
    return shapes[:count]
