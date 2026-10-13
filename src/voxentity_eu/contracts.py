"""Typed data contracts for VoxEntity-EU.

All records are strict: closed enums, mandatory schema_version on top-level
files, no NaN, no duplicate IDs, no paths escaping the corpus root and no
broken cross-references. See docs/04-contracts.md.
"""

from __future__ import annotations

import json
import math
from pathlib import Path, PurePosixPath
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "0.2"

# --- enums -----------------------------------------------------------------

Split = Literal["dev", "test"]
Locale = Literal["de-DE", "fr-FR"]
EntityType = Literal[
    "person_name",
    "phone",
    "email",
    "calendar_value",
    "postal_address",
    "reference_code",
]
Corpus = Literal["synthetic", "human_control"]
Condition = Literal["clean", "telephone"]
QaStatus = Literal[
    "accepted",
    "wrong_synthesis",
    "ambiguous",
    "truncated",
    "pending_review",
]
Track = Literal["asr", "asr_slots", "audio_slots", "agent_slots"]
PredStatus = Literal["ok", "error", "timeout", "unsupported"]
AccessMode = Literal["local", "remote"]
DifficultyTag = Literal[
    "direct",
    "orthographic",
    "phonetic",
    "segmented",
    "spelling",
    "correction",
]



class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        frozen=True,
    )


def _reject_nan(value: Any) -> None:
    """Reject float NaN/inf anywhere pydantic hands us a bare float."""

    def walk(node: Any) -> None:
        if isinstance(node, float) and (math.isnan(node) or math.isinf(node)):
            raise ValueError("NaN/inf values are not allowed")
        if isinstance(node, dict):
            for child in node.values():
                walk(child)
        elif isinstance(node, (list, tuple)):
            for child in node:
                walk(child)

    walk(value)


class _NoNaNModel(StrictModel):
    @model_validator(mode="after")
    def _check_nan(self) -> Self:
        _reject_nan(self.model_dump())
        return self


# --- value objects -----------------------------------------------------------


class PostalAddressValue(StrictModel):
    street: str = Field(min_length=1)
    house_number: str = Field(min_length=1)
    postal_code: str = Field(min_length=1)  # never an int: leading zeros matter
    locality: str = Field(min_length=1)


class CalendarValue(StrictModel):
    day: int = Field(ge=1, le=31)
    month: int = Field(ge=1, le=12)
    year: int | None = Field(default=None, ge=1900, le=2100)


class Entity(StrictModel):
    entity_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    type: EntityType
    canonical_value: str | PostalAddressValue | CalendarValue
    accepted_variants: list[str] = Field(default_factory=list)
    mention_text: str = Field(min_length=1)
    target: bool = True
    # Public per-type policy; must not vary with the secret value.
    case_sensitive: bool | None = None

    @model_validator(mode="after")
    def _value_shape_matches_type(self) -> Self:
        t, v = self.type, self.canonical_value
        if t == "postal_address" and not isinstance(v, PostalAddressValue):
            raise ValueError("postal_address requires {street, house_number, postal_code, locality}")
        if t == "calendar_value" and not isinstance(v, CalendarValue):
            raise ValueError("calendar_value requires {day, month, year?}")
        if t in ("person_name", "phone", "email", "reference_code"):
            if not isinstance(v, str) or not v.strip():
                raise ValueError(f"{t} requires a non-empty string canonical_value")
        if t == "reference_code" and self.case_sensitive is None:
            object.__setattr__(self, "case_sensitive", True)
        if t != "reference_code" and self.case_sensitive is not None:
            raise ValueError("case_sensitive is only defined for reference_code")
        return self


class PreviousMention(StrictModel):
    type: EntityType
    value: str | PostalAddressValue | CalendarValue

    @model_validator(mode="after")
    def _value_shape_matches_type(self) -> Self:
        t, v = self.type, self.value
        if t == "postal_address" and not isinstance(v, PostalAddressValue):
            raise ValueError("postal_address previous mention requires the address object")
        if t == "calendar_value" and not isinstance(v, CalendarValue):
            raise ValueError("calendar_value previous mention requires the calendar object")
        if t in ("person_name", "phone", "email", "reference_code") and not isinstance(v, str):
            raise ValueError(f"{t} previous mention requires a string value")
        return self


class Scenario(_NoNaNModel):
    schema_version: str
    scenario_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    split: Split
    locale: Locale
    entity_type: EntityType
    template_family: str = Field(min_length=1)
    difficulty_tags: list[DifficultyTag] = Field(min_length=1)
    written_text: str = Field(min_length=1)
    synthesis_text: str = Field(min_length=1)
    entities: list[Entity] = Field(min_length=1)
    previous_mentions: list[PreviousMention] = Field(default_factory=list)
    seed: int = Field(ge=0)

    @model_validator(mode="after")
    def _invariants(self) -> Self:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"scenario schema_version must be {SCHEMA_VERSION}")
        if self.entities[0].type != self.entity_type:
            raise ValueError("first entity type must match scenario entity_type")
        targets = [e for e in self.entities if e.target]
        if len(targets) != 1:
            raise ValueError("exactly one target entity per scenario")
        if self.entities[0].entity_id != "target-1":
            raise ValueError("single-target scenarios must name the target entity 'target-1'")
        for m in self.previous_mentions:
            if m.type != self.entity_type:
                raise ValueError("previous_mentions must share the scenario entity_type")
        if "correction" in self.difficulty_tags and not self.previous_mentions:
            raise ValueError("correction scenarios need previous_mentions")
        return self


# --- provenance records ------------------------------------------------------


class SynthesisRecord(StrictModel):
    synthesis_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    model_id: str = Field(min_length=1)
    model_revision: str = Field(min_length=40, max_length=40)
    speaker_id: str = Field(min_length=1)
    language_arg: str = Field(min_length=1)
    generation_config: dict[str, Any] = Field(default_factory=dict)
    seed: int = Field(ge=0)
    environment_hash: str = Field(min_length=1)
    text_sha256: str = Field(min_length=64, max_length=64)
    master_sha256: str = Field(min_length=64, max_length=64)
    attempt: int = Field(ge=1)
    quality_decision: Literal["accepted", "rejected"]
    superseded_by: str | None = None


class TransformRecord(StrictModel):
    transform_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    recipe_version: str = Field(min_length=1)
    input_sha256: str = Field(min_length=64, max_length=64)
    output_sha256: str = Field(min_length=64, max_length=64)
    filter_config: dict[str, Any]
    resampler: str
    codec: str
    noise_seed: int
    target_snr_db: float
    measured_snr_db: float
    clipping_fraction: float = Field(ge=0.0, le=1.0)
    command_argv: list[str] = Field(default_factory=list)
    tool_versions: dict[str, str] = Field(default_factory=dict)


class AudioRecord(_NoNaNModel):
    audio_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    scenario_id: str | None = None
    corpus: Corpus
    condition: Condition
    parent_audio_id: str | None = None
    path: str = Field(min_length=1)
    sha256: str = Field(min_length=64, max_length=64)
    sample_rate_hz: int = Field(gt=0)
    channels: int = Field(default=1)
    encoding: str = Field(default="pcm_s16le")
    num_samples: int = Field(ge=0)
    duration_seconds: float = Field(gt=0.0)
    synthesis_id: str | None = None
    transform_id: str | None = None
    qa_status: QaStatus
    source_id: str | None = None
    external_row_id: str | None = None
    external_split: str | None = None
    transcript: str | None = None

    @model_validator(mode="after")
    def _invariants(self) -> Self:
        if self.channels != 1:
            raise ValueError("corpus audio is mono (channels=1)")
        if self.corpus == "human_control":
            missing = [
                name
                for name in ("external_row_id", "external_split", "transcript", "source_id")
                if getattr(self, name) in (None, "")
            ]
            if missing:
                raise ValueError(f"human_control audio requires {', '.join(missing)}")
            if self.scenario_id is not None:
                raise ValueError("human_control audio must not reference synthetic scenarios")
        else:
            if self.scenario_id is None:
                raise ValueError("synthetic audio requires scenario_id")
            if self.external_row_id is not None:
                raise ValueError("external_row_id is reserved for human_control")
            if self.condition == "telephone":
                if self.parent_audio_id is None or self.transform_id is None:
                    raise ValueError("telephone audio requires parent_audio_id and transform_id")
        if self.condition == "clean" and self.parent_audio_id is not None:
            raise ValueError("clean audio must not have a parent")
        # relative POSIX path, no traversal
        p = PurePosixPath(self.path)
        if p.is_absolute() or ".." in p.parts or "\\" in self.path:
            raise ValueError(f"path must be relative within corpus root: {self.path}")
        return self


# --- predictions -------------------------------------------------------------


class Slot(StrictModel):
    type: EntityType
    value: str = Field(min_length=0)  # empty string is a valid (wrong) prediction
    evidence: str | None = None


class Prediction(_NoNaNModel):
    run_id: str = Field(min_length=1)
    audio_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]*$")
    track: Track
    status: PredStatus
    transcript: str | None = None
    predicted_slots: list[Slot] = Field(default_factory=list)
    error_type: str | None = None
    raw_artifact_path: str | None = None
    observed_final_state_path: str | None = None

    @model_validator(mode="after")
    def _invariants(self) -> Self:
        if self.status == "ok" and self.track == "asr" and self.transcript is None:
            raise ValueError("ok asr prediction requires a transcript (may be empty string)")
        if self.status in ("error", "timeout") and self.error_type is None:
            raise ValueError(f"{self.status} prediction requires error_type")
        if self.status == "ok" and self.error_type is not None:
            raise ValueError("ok prediction must not carry error_type")
        return self


def validate_measured_evidence(predictions: list[Prediction]) -> None:
    """Release gate: an ok agent_slots row is only measured evidence when the
    final state was actually read from the agent's store (examples/README.md).
    """

    for p in predictions:
        if p.track == "agent_slots" and p.status == "ok" and p.observed_final_state_path is None:
            raise ValueError(
                f"ok agent_slots prediction for {p.audio_id} lacks observed_final_state_path; "
                "not acceptable as measured evidence"
            )


class RunManifest(_NoNaNModel):
    run_id: str = Field(min_length=1)
    schema_version: str
    suite_version: str = Field(min_length=1)
    dataset_hash: str = Field(min_length=64, max_length=64)
    eligible_audio_ids_hash: str = Field(min_length=64, max_length=64)
    code_commit: str
    dependency_lock_hash: str = Field(min_length=64, max_length=64)
    model_id: str
    model_revision: str
    backend: str
    device: str
    precision: str
    decoding_config: dict[str, Any] = Field(default_factory=dict)
    prompt_hash: str | None = None
    normalizer_version: str
    seed: int
    input_audio_policy: str
    track: Track
    expected_count: int = Field(ge=0)
    completed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    access_mode: AccessMode
    charge_limit: float
    observed_usage: dict[str, Any] | None = None
    incomplete: bool = False

    @model_validator(mode="after")
    def _invariants(self) -> Self:
        if self.schema_version != SCHEMA_VERSION:
            raise ValueError(f"run manifest schema_version must be {SCHEMA_VERSION}")
        if self.completed_count + self.failed_count > self.expected_count:
            raise ValueError("completed+failed cannot exceed expected")
        counts_match = self.completed_count + self.failed_count == self.expected_count
        if self.incomplete and counts_match:
            raise ValueError("incomplete=true contradicts full counts")
        if not self.incomplete and not counts_match:
            raise ValueError("run with missing rows must set incomplete=true")
        return self


# --- registry / rights --------------------------------------------------------


class RightsEntry(StrictModel):
    source_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    url: str
    revision: str
    file: str | None = None
    sha256: str | None = None
    declared_license: str
    license_url: str
    rights_holder: str
    transformations: str = Field(default="none")
    redistribution: Literal["allowed", "conditional", "blocked"]
    review_status: Literal["verified", "conditional", "blocked"]
    notes: str = Field(default="")


# --- I/O helpers ---------------------------------------------------------------


def dumps_strict(obj: Any) -> str:
    """Strict UTF-8 JSON: sorted keys, no NaN, no ASCII escaping."""
    return json.dumps(obj, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def read_jsonl(path: Path | str, model: type[StrictModel]) -> list[StrictModel]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(model.model_validate(json.loads(line)))
            except Exception as exc:  # noqa: BLE001 - rewrap with location
                raise ValueError(f"{path}:{lineno}: {exc}") from exc
    return rows


def read_json(path: Path | str, model: type[StrictModel]) -> StrictModel:
    with open(path, encoding="utf-8") as fh:
        return model.model_validate(json.load(fh))


def check_unique_ids(rows: list[StrictModel], field: str = "id") -> None:
    seen: set[str] = set()
    for row in rows:
        rid = getattr(row, field)
        if rid in seen:
            raise ValueError(f"duplicate {field}: {rid}")
        seen.add(rid)


def check_references(
    audio_rows: list[AudioRecord],
    scenario_ids: set[str],
    synthesis_ids: set[str] | None = None,
    transform_ids: set[str] | None = None,
) -> None:
    """Join by ID, never by row order."""
    for a in audio_rows:
        if a.scenario_id is not None and a.scenario_id not in scenario_ids:
            raise ValueError(f"{a.audio_id}: unknown scenario_id {a.scenario_id}")
        if a.synthesis_id is not None and synthesis_ids is not None and a.synthesis_id not in synthesis_ids:
            raise ValueError(f"{a.audio_id}: unknown synthesis_id {a.synthesis_id}")
        if a.transform_id is not None and transform_ids is not None and a.transform_id not in transform_ids:
            raise ValueError(f"{a.audio_id}: unknown transform_id {a.transform_id}")
        if a.parent_audio_id is not None:
            if a.parent_audio_id == a.audio_id:
                raise ValueError(f"{a.audio_id}: self parent")
            siblings = {x.audio_id for x in audio_rows}
            if a.parent_audio_id not in siblings:
                raise ValueError(f"{a.audio_id}: unknown parent_audio_id {a.parent_audio_id}")


def validate_predictions_against_audio(
    predictions: list[Prediction], audio_ids: set[str]
) -> None:
    seen: set[str] = set()
    for p in predictions:
        key = (p.run_id, p.audio_id)
        if key in seen:
            raise ValueError(f"duplicate prediction row for {p.audio_id} in run {p.run_id}")
        seen.add(key)
        if p.audio_id not in audio_ids:
            raise ValueError(f"prediction references unknown audio_id {p.audio_id}")
