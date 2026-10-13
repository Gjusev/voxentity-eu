"""Error taxonomy (docs/05 §Informe de errores): heuristic, revisable.

digit_swap, missing_prefix, spelling_loss, accent_loss, correction_ignored,
address_component_loss, format_only, extra_slot, timeout, synthesis_issue.
Classification is automatic and reviewable; it is not ground truth about
model internals.
"""

from __future__ import annotations

import re
from typing import Any

from ..scoring.normalize import literal_form

TAXONOMY_VERSION = "errtax-1"


def classify_error(example: dict[str, Any], gold: Any, entity_type: str, locale: str) -> str:
    """One taxonomy label per incorrect example; order of checks matters."""

    if example.get("status") == "timeout":
        return "timeout"
    if example.get("error_type"):
        return "timeout" if example["status"] == "timeout" else "system_error"
    if example.get("extra_output") and example.get("outcome") == "correct":
        return "extra_slot"
    predicted = example.get("predicted_value") or ""
    if not predicted:
        return "omission"

    gold_lit = literal_form(gold)
    if entity_type == "phone":
        digits_gold = re.sub(r"\D", "", str(gold_lit))
        digits_pred = re.sub(r"\D", "", predicted)
        if digits_pred and digits_gold and sorted(digits_gold) == sorted(digits_pred):
            return "digit_swap"
        if digits_pred and digits_gold and digits_pred in digits_gold and len(digits_pred) < len(digits_gold):
            return "missing_prefix"
        return "digit_error"
    if entity_type == "person_name":
        a, b = str(gold_lit).lower(), predicted.lower()
        base = re.sub(r"[éèêë]", "e", re.sub(r"[àâä]", "a", b))
        gold_base = re.sub(r"[éèêë]", "e", re.sub(r"[àâä]", "a", a))
        if base == gold_base:
            return "accent_loss"
        if b.replace("ß", "ss") == a.replace("ß", "ss"):
            return "spelling_loss"
        return "name_error"
    if entity_type == "email":
        if "@" in predicted:
            local_p, _, dom_p = predicted.rpartition("@")
            local_g, _, dom_g = str(gold_lit).rpartition("@")
            if dom_p.lower() == dom_g.lower():
                return "local_part_error"
            return "domain_error"
        return "format_only"
    if entity_type == "calendar_value":
        return "calendar_component_loss"
    if entity_type == "postal_address":
        return "address_component_loss"
    if entity_type == "reference_code":
        digits_gold = re.sub(r"\D", "", str(gold_lit))
        digits_pred = re.sub(r"\D", "", predicted)
        if sorted(digits_gold) == sorted(digits_pred) if digits_pred else False:
            return "digit_swap"
        letters_gold = re.sub(r"[^A-Za-z]", "", str(gold_lit)).upper()
        letters_pred = re.sub(r"[^A-Za-z]", "", predicted).upper()
        if letters_pred == letters_gold and digits_pred != digits_gold:
            return "digit_error"
        return "code_error"
    return "other"


def enrich_with_taxonomy(scored: dict[str, Any], scenarios_by_id: dict[str, Any]) -> dict[str, Any]:
    """Attach a taxonomy label to each incorrect result; keep original fields."""

    for r in scored.get("results", []):
        sc = scenarios_by_id.get(r.get("scenario_id"))
        if r.get("outcome") == "correct":
            r["error_taxonomy"] = None
            continue
        if sc is None:
            r["error_taxonomy"] = "unknown_scenario"
            continue
        if r.get("stale_value"):
            r["error_taxonomy"] = "correction_ignored"
            continue
        entity = sc.entities[0]
        r["error_taxonomy"] = classify_error(
            {
                "status": r.get("status"),
                "error_type": r.get("error_type"),
                "predicted_value": r.get("predicted_value"),
                "extra_output": r.get("extra_output"),
                "outcome": r.get("outcome"),
            },
            entity.canonical_value,
            sc.entity_type,
            sc.locale,
        )
    scored["taxonomy_version"] = TAXONOMY_VERSION
    return scored
