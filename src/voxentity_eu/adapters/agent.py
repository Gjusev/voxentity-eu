"""Reference agent with observable slot persistence (docs/06 §Agente).

Local process-level design: a JSONL event log plus a final-state document
per session. store_slot REPLACES the previous value of the same slot type
(within-turn corrections included). The scorer reads the final state file,
never the agent's words. Sessions are strictly reset per case; no external
calls, no telephony, no provider accounts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..contracts import SCHEMA_VERSION
from ..provenance import write_text_atomic

AGENT_VERSION = "ref-agent-1"


class AgentStore:
    """Event-sourced slot store; the final state is derived, then frozen."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.events_dir = self.root / "events"
        self.states_dir = self.root / "states"
        self.events_dir.mkdir(parents=True, exist_ok=True)
        self.states_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, dict[str, Any]] = {}

    def create_session(self, session_id: str, requested_type: str) -> None:
        if session_id in self._sessions:
            raise ValueError(f"session {session_id} exists; strict reset violated")
        self._sessions[session_id] = {
            "schema_version": SCHEMA_VERSION,
            "session_id": session_id,
            "requested_type": requested_type,
            "events": [],
            "slots": {},  # type -> value (last store wins; correction replaces)
        }

    def store_slot(self, session_id: str, slot_type: str, value: str) -> dict[str, Any]:
        self._require(session_id)
        session = self._sessions[session_id]
        seq = len(session["events"]) + 1
        event = {
            "seq": seq,
            "ts_source": "monotonic-counter",  # no fabricated wall-clock timings
            "event": "store_slot",
            "type": slot_type,
            "value": value,
            "replaces": session["slots"].get(slot_type),
        }
        session["events"].append(event)
        session["slots"][slot_type] = value  # replacement semantics
        self._append_event(session_id, event)
        return event

    def finalize(self, session_id: str) -> Path:
        """Freeze the observed final state; readable via an independent path."""

        self._require(session_id)
        session = self._sessions[session_id]
        state = {
            "schema_version": SCHEMA_VERSION,
            "session_id": session_id,
            "requested_type": session["requested_type"],
            "agent_version": AGENT_VERSION,
            "final_slots": [
                {"type": t, "value": v} for t, v in sorted(session["slots"].items())
            ],
            "event_count": len(session["events"]),
        }
        path = self.states_dir / f"{session_id}.json"
        write_text_atomic(path, json.dumps(state, ensure_ascii=False, indent=1))
        del self._sessions[session_id]  # strict reset: session cannot continue
        return path

    def read_state(self, session_id: str) -> dict[str, Any]:
        """Independent read API over frozen states (no live memory access)."""

        path = self.states_dir / f"{session_id}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def _require(self, session_id: str) -> None:
        if session_id not in self._sessions:
            raise ValueError(f"unknown or finalized session {session_id}")

    def _append_event(self, session_id: str, event: dict[str, Any]) -> None:
        with open(self.events_dir / f"{session_id}.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")


class ReferenceAgent:
    """Audio -> ASR -> extractor -> store_slot -> observable final state."""

    def __init__(self, asr, store: AgentStore, extractor=None) -> None:
        self.asr = asr
        self.store = store
        if extractor is None:
            from .slots import extract

            self._extract_fn = extract
        else:
            self._extract_fn = extractor

    def evaluate(self, audio_path: str, requested_type: str, locale: str, session_id: str) -> dict[str, Any]:
        self.store.create_session(session_id, requested_type)
        try:
            asr_result = self.asr.transcribe(audio_path, locale)
            transcript = asr_result.transcript if asr_result.status == "ok" else None
            slots: list[dict[str, str]] = []
            if transcript is not None:
                extraction = self._extract_fn(transcript, requested_type, locale)
                slots = extraction.slots if extraction.status == "ok" else []
                for slot in slots:
                    # single-slot suite: exactly one store per requested type
                    self.store.store_slot(session_id, slot["type"], slot["value"])
            state_path = self.store.finalize(session_id)
        except BaseException:
            # never leave a session half-open: finalize what exists
            try:
                state_path = self.store.finalize(session_id)
            except Exception:  # noqa: BLE001
                raise
            raise
        return {
            "session_id": session_id,
            "transcript": transcript,
            "observed_final_state_path": str(state_path),
            "slots": slots,
        }
