"""Utterance frames per locale × entity × difficulty.

Frames are plain carrier sentences; the entity value is inserted verbally by
the generator. Dev and test draw from disjoint frame halves of the same
family pool, and every family is bound to exactly one split
(docs/03-data.md §A).
"""

from __future__ import annotations

# frame placeholder: {e} = spoken entity, {prev} = spoken previous value.
FRAMES: dict[tuple[str, str], dict[str, list[str]]] = {
    ("de-DE", "person_name"): {
        "direct": [
            "Mein Name ist {e}.",
            "Ich heiße {e}.",
            "Der Name lautet {e}, bitte notieren.",
            "Auf den Namen {e} bitte.",
        ],
        "tricky": [
            "Es ist Herr {e}.",
            "Frau {e}, genau so geschrieben.",
            "Der Name ist {e}, mit Umlaut.",
            "Ich bin {e}.",
        ],
        "segmented": [
            "Mein Nachname ist {e}, ich buchstabiere.",
            "Der Name ist {e}, ich buchstabiere das.",
            "Nachname {e}, Buchstabiert bitte mit.",
            "Ich diktiere den Namen: {e}.",
        ],
        "correction": [
            "Der Name ist {prev}, entschuldigen Sie, {e}.",
            "Ich heiße {prev}, Moment, ich korrigiere mich, {e}.",
            "Es ist {prev}, nein, falsch, richtig ist {e}.",
            "Verzeihung, nicht {prev}, sondern {e}.",
        ],
    },
    ("de-DE", "phone"): {
        "direct": [
            "Meine Rufnummer ist {e}.",
            "Sie erreichen mich unter {e}.",
            "Notieren Sie bitte die Nummer {e}.",
            "Die Durchwahl ist {e}.",
        ],
        "tricky": [
            "Meine Nummer ist {e}, hören Sie genau zu.",
            "Die Nummer {e} hat viele gleiche Ziffern.",
            "Wiederholt ist die Nummer {e}.",
            "Die Rufnummer lautet {e}.",
        ],
        "segmented": [
            "Die Nummer ist {e}, Ziffer für Ziffer.",
            "Ich sage die Nummer langsam: {e}.",
            "Nummer {e}, Ziffer für Ziffer notiert.",
            "Langsam wiederhole ich: {e}.",
        ],
        "correction": [
            "Die Nummer ist {prev}, Moment, ich korrigiere, es ist {e}.",
            "Sie erreichen mich unter {prev}, nein, falsch, richtig ist {e}.",
            "Es ist {prev}, Entschuldigung, {e}.",
            "Nicht {prev}, sondern {e}.",
        ],
    },
    ("de-DE", "email"): {
        "direct": [
            "Meine E-Mail-Adresse ist {e}.",
            "Schicken Sie es an {e}.",
            "Die Adresse im System ist {e}.",
            "Ich diktiere: {e}.",
        ],
        "tricky": [
            "Die E-Mail ist {e}, hören Sie genau zu.",
            "Achtung, die Adresse ist {e}.",
            "Die Mailadresse lautet {e}.",
            "Notieren Sie {e}.",
        ],
        "segmented": [
            "Die Adresse ist {e}, ich buchstabiere alles.",
            "Ich buchstabiere die Adresse: {e}.",
            "E-Mail {e}, Zeichen für Zeichen.",
            "Langsam: {e}.",
        ],
        "correction": [
            "Die Adresse ist {prev}, pardon, ich korrigiere, {e}.",
            "Schicken Sie es an {prev}, nein, Moment, richtig ist {e}.",
            "Es ist {prev}, Entschuldigung, es muss {e} sein.",
            "Nicht {prev}, sondern {e}.",
        ],
    },
    ("de-DE", "calendar_value"): {
        "direct": [
            "Ich hätte gern einen Termin am {e}.",
            "Tragen Sie mich für den {e} ein.",
            "Der Termin ist am {e}.",
            "Am {e} passt es mir.",
        ],
        "tricky": [
            "Der Termin ist am {e}, hören Sie genau zu.",
            "Am {e}, bitte genau notieren.",
            "Für den {e} bitte.",
            "Der Termin soll der {e} sein.",
        ],
        "segmented": [
            "Der Termin: {e}.",
            "Ich sage es in Teilen: {e}.",
            "Das Datum ist {e}, Teil für Teil.",
            "Termin notiert? {e}.",
        ],
        "correction": [
            "Am {prev}, Moment, ich korrigiere, am {e}.",
            "Der Termin ist am {prev}, nein, richtig ist der {e}.",
            "Für den {prev}, Entschuldigung, für den {e}.",
            "Nicht am {prev}, sondern am {e}.",
        ],
    },
    ("de-DE", "postal_address"): {
        "direct": [
            "Meine Adresse ist {e}.",
            "Liefern Sie an {e}.",
            "Die Lieferadresse lautet {e}.",
            "Ich wohne in der Straße {e}.",
        ],
        "tricky": [
            "Die Adresse ist {e}, hören Sie genau zu.",
            "Lieferung an {e}, bitte alles notieren.",
            "Die Adresse lautet {e}.",
            "Schicken Sie es an {e}.",
        ],
        "segmented": [
            "Die Adresse, in Teilen: {e}.",
            "Ich diktiere die Adresse: {e}.",
            "Adresse {e}, Bestandteil für Bestandteil.",
            "Langsam die Adresse: {e}.",
        ],
        "correction": [
            "Die Adresse ist {prev}, entschuldigen Sie, {e}.",
            "Liefern Sie an {prev}, Moment, richtig ist {e}.",
            "Es ist {prev}, nein, korrigiert: {e}.",
            "Nicht {prev}, sondern {e}.",
        ],
    },
    ("de-DE", "reference_code"): {
        "direct": [
            "Meine Referenz ist {e}.",
            "Die Vorgangsnummer ist {e}.",
            "Notieren Sie die Referenz {e}.",
            "Der Auftrag hat die Nummer {e}.",
        ],
        "tricky": [
            "Die Referenz ist {e}, hören Sie genau zu.",
            "Referenznummer {e}, bitte genau.",
            "Die Vorgangsnummer lautet {e}.",
            "Wichtig ist die Referenz {e}.",
        ],
        "segmented": [
            "Die Referenz ist {e}, ich buchstabiere.",
            "Ich buchstabiere die Referenz: {e}.",
            "Referenz {e}, Zeichen für Zeichen.",
            "Langsam: {e}.",
        ],
        "correction": [
            "Die Referenz ist {prev}, pardon, {e}.",
            "Es ist {prev}, Moment, ich korrigiere mich, {e}.",
            "Die Vorgangsnummer ist {prev}, nein, richtig ist {e}.",
            "Nicht {prev}, sondern {e}.",
        ],
    },
    ("fr-FR", "person_name"): {
        "direct": [
            "Je m'appelle {e}.",
            "Mon nom est {e}.",
            "C'est au nom de {e}.",
            "Le nom est {e}, notez bien.",
        ],
        "tricky": [
            "C'est Madame {e}.",
            "Monsieur {e}, avec les accents.",
            "Le nom est {e}.",
            "Je suis {e}.",
        ],
        "segmented": [
            "Mon nom de famille est {e}, je l'épelle.",
            "Le nom est {e}, j'épelle.",
            "Nom {e}, épelle-le avec moi.",
            "Je vous dicte le nom : {e}.",
        ],
        "correction": [
            "Le nom est {prev}, pardon, {e}.",
            "Je m'appelle {prev}, je corrige, {e}.",
            "C'est {prev}, non, c'est {e}.",
            "Excusez-moi, pas {prev}, mais {e}.",
        ],
    },
    ("fr-FR", "phone"): {
        "direct": [
            "Mon numéro est le {e}.",
            "Vous pouvez me joindre au {e}.",
            "Notez bien le numéro {e}.",
            "C'est le {e}.",
        ],
        "tricky": [
            "Mon numéro est le {e}, écoutez bien.",
            "Le numéro {e} a beaucoup de chiffres pareils.",
            "Je répète le numéro : {e}.",
            "Le numéro est le {e}.",
        ],
        "segmented": [
            "Le numéro est le {e}, chiffre par chiffre.",
            "Je dis le numéro lentement : {e}.",
            "Numéro {e}, notez chiffre par chiffre.",
            "Je répète lentement : {e}.",
        ],
        "correction": [
            "Le numéro est le {prev}, pardon, je corrige, c'est le {e}.",
            "Vous pouvez me joindre au {prev}, non, c'est le {e}.",
            "C'est le {prev}, excusez-moi, le {e}.",
            "Pas le {prev}, mais le {e}.",
        ],
    },
    ("fr-FR", "email"): {
        "direct": [
            "Mon adresse e-mail est {e}.",
            "Envoyez-le à {e}.",
            "L'adresse dans le système est {e}.",
            "Je vous dicte : {e}.",
        ],
        "tricky": [
            "L'adresse e-mail est {e}, écoutez bien.",
            "Attention, l'adresse est {e}.",
            "L'adresse est {e}.",
            "Notez {e}.",
        ],
        "segmented": [
            "L'adresse est {e}, j'épelle tout.",
            "J'épelle l'adresse : {e}.",
            "E-mail {e}, caractère par caractère.",
            "Lentement : {e}.",
        ],
        "correction": [
            "L'adresse est {prev}, pardon, je corrige, {e}.",
            "Envoyez-le à {prev}, non, attends, c'est {e}.",
            "C'est {prev}, excusez-moi, c'est {e}.",
            "Pas {prev}, mais {e}.",
        ],
    },
    ("fr-FR", "calendar_value"): {
        "direct": [
            "Je voudrais un rendez-vous le {e}.",
            "Inscrivez-moi pour le {e}.",
            "Le rendez-vous est le {e}.",
            "Le {e} me convient.",
        ],
        "tricky": [
            "Le rendez-vous est le {e}, écoutez bien.",
            "Le {e}, notez précisément.",
            "C'est pour le {e}.",
            "Le rendez-vous doit être le {e}.",
        ],
        "segmented": [
            "Le rendez-vous : {e}.",
            "Je le dis en parties : {e}.",
            "La date est {e}, partie par partie.",
            "Rendez-vous noté ? {e}.",
        ],
        "correction": [
            "Le {prev}, pardon, je corrige, le {e}.",
            "Le rendez-vous est le {prev}, non, c'est le {e}.",
            "Pour le {prev}, excusez-moi, pour le {e}.",
            "Pas le {prev}, mais le {e}.",
        ],
    },
    ("fr-FR", "postal_address"): {
        "direct": [
            "Mon adresse est {e}.",
            "Livrez à {e}.",
            "L'adresse de livraison est {e}.",
            "J'habite au {e}.",
        ],
        "tricky": [
            "L'adresse est {e}, écoutez bien.",
            "Livraison à {e}, notez tout.",
            "L'adresse est {e}.",
            "Envoyez-le à {e}.",
        ],
        "segmented": [
            "L'adresse, en parties : {e}.",
            "Je vous dicte l'adresse : {e}.",
            "Adresse {e}, élément par élément.",
            "Lentement l'adresse : {e}.",
        ],
        "correction": [
            "L'adresse est {prev}, pardon, {e}.",
            "Livrez à {prev}, attends, c'est {e}.",
            "C'est {prev}, non, corrigé : {e}.",
            "Pas {prev}, mais {e}.",
        ],
    },
    ("fr-FR", "reference_code"): {
        "direct": [
            "Ma référence est {e}.",
            "Le numéro de dossier est {e}.",
            "Notez la référence {e}.",
            "Le dossier porte le numéro {e}.",
        ],
        "tricky": [
            "La référence est {e}, écoutez bien.",
            "Référence {e}, précisément.",
            "Le numéro de dossier est {e}.",
            "L'important est la référence {e}.",
        ],
        "segmented": [
            "La référence est {e}, j'épelle.",
            "J'épelle la référence : {e}.",
            "Référence {e}, caractère par caractère.",
            "Lentement : {e}.",
        ],
        "correction": [
            "La référence est {prev}, pardon, {e}.",
            "C'est {prev}, je corrige, {e}.",
            "Le numéro de dossier est {prev}, non, c'est {e}.",
            "Pas {prev}, mais {e}.",
        ],
    },
}


def frames_for(locale: str, entity: str, difficulty: str, split: str, index: int) -> str:
    """Deterministic disjoint halves: dev takes even positions, test odd ones."""

    pool = FRAMES[(locale, entity)][difficulty]
    half = [pool[i] for i in range(len(pool)) if i % 2 == (0 if split == "dev" else 1)]
    return half[index % len(half)]


def template_family(locale: str, entity: str, difficulty: str, split: str) -> str:
    lang = locale.split("-")[0]
    return f"{lang}_{entity}_{difficulty}_{split}"
