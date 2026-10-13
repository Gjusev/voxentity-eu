"""Hashing, atomic writes and environment fingerprints."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import tempfile
from pathlib import Path
from typing import Any

ENVIRONMENT_LABELS = ("python", "numpy", "scipy", "soundfile", "pydantic", "torch")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_json(obj: Any) -> str:
    """Hash of the strict canonical JSON encoding (sorted keys)."""
    payload = json.dumps(obj, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))
    return sha256_text(payload)


def sha256_file(path: Path | str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def write_atomic(path: Path | str, data: bytes) -> None:
    """Write bytes so readers never observe a partial file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_text_atomic(path: Path | str, text: str) -> None:
    write_atomic(path, text.encode("utf-8"))


def environment_hash(include: tuple[str, ...] = ENVIRONMENT_LABELS) -> str:
    """Fingerprint of interpreter + pinned-relevant package versions.

    Deliberately excludes dates and machine identifiers beyond the platform:
    reproducibility follows from versions, not wall-clock.
    """
    parts: dict[str, str] = {"python": platform.python_version(), "implementation": platform.python_implementation()}
    for name in include:
        if name == "python":
            continue
        try:
            module = __import__(name)
            parts[name] = str(getattr(module, "__version__", "unknown"))
        except ImportError:
            parts[name] = "absent"
    parts["system"] = f"{sys.platform}"
    return sha256_json(parts)


def dependency_lock_hash(lock_file: Path | str) -> str:
    lock_file = Path(lock_file)
    if not lock_file.exists():
        raise FileNotFoundError(f"dependency lock not found: {lock_file}")
    return sha256_file(lock_file)


def code_commit(git_dir: Path | str = ".") -> str:
    """Current commit hash; 'unknown' outside a git worktree."""
    head = Path(git_dir) / ".git" / "HEAD"
    git_dir_path = Path(git_dir) / ".git"
    if git_dir_path.is_file():  # worktree pointer
        text = git_dir_path.read_text(encoding="utf-8").strip()
        pointer = text.split("gitdir:", 1)[1].strip() if "gitdir:" in text else None
        if pointer:
            head = Path(pointer) / "HEAD"
    if not head.exists():
        return "unknown"
    text = head.read_text(encoding="utf-8").strip()
    if text.startswith("ref:"):
        ref = head.parent / text[4:].strip()
        if ref.exists():
            return ref.read_text(encoding="utf-8").strip()
        return "unknown"
    return text
