"""Preflight diagnostics.

Prints variable names and present/absent status only; never secret values,
never fixed quota figures (docs/07-compute.md).
"""

from __future__ import annotations

import importlib.util
import os
import shutil
from typing import Any


def _has_module(name: str) -> str:
    return "present" if importlib.util.find_spec(name) is not None else "absent"


def _has_env(name: str) -> str:
    return "present" if os.environ.get(name) else "absent"


def _has_file(path: str) -> str:
    from pathlib import Path

    home = Path.home()
    return "present" if (home / path).exists() else "absent"


def _gpu_status() -> dict[str, str]:
    if importlib.util.find_spec("torch") is None:
        return {"torch": "absent", "cuda": "not queried (no torch)"}
    import torch

    if not torch.cuda.is_available():
        return {"torch": "present", "cuda": "unavailable"}
    props = torch.cuda.get_device_properties(0)
    return {
        "torch": "present",
        "cuda": "available",
        "gpu_name": props.name,
        "gpu_memory_gb": f"{props.total_memory / (1 << 30):.1f}",
    }


def run_doctor(profile: str) -> dict[str, Any]:
    checks: dict[str, Any] = {
        "profile": profile,
        "python": _python_version(),
        "core_deps": {m: _has_module(m) for m in ("pydantic", "numpy", "scipy", "soundfile", "jiwer")},
        "optional_deps": {m: _has_module(m) for m in ("torch", "transformers", "huggingface_hub", "datasets")},
    }
    if profile == "local":
        checks["gpu"] = _gpu_status()
        checks["ffmpeg"] = "present" if shutil.which("ffmpeg") else "absent"
    elif profile == "hf":
        checks["env"] = {"HF_TOKEN": _has_env("HF_TOKEN"), "HUGGING_FACE_HUB_TOKEN": _has_env("HUGGING_FACE_HUB_TOKEN")}
        checks["token_file"] = _has_file(".cache/huggingface/token")
        if importlib.util.find_spec("huggingface_hub") is not None:
            from huggingface_hub import HfApi  # local metadata only; no secret printing

            try:
                checks["whoami"] = HfApi().whoami().get("name", "unknown")
            except Exception as exc:  # noqa: BLE001
                checks["whoami"] = f"unavailable ({type(exc).__name__})"
        else:
            checks["whoami"] = "not queried (no huggingface_hub)"
    elif profile == "kaggle":
        checks["env"] = {
            "KAGGLE_API_TOKEN": _has_env("KAGGLE_API_TOKEN"),
            "KAGGLE_USERNAME": _has_env("KAGGLE_USERNAME"),
            "KAGGLE_KEY": _has_env("KAGGLE_KEY"),
        }
        checks["kaggle_json"] = _has_file(".kaggle/kaggle.json")
        checks["kaggle_cli"] = "present" if importlib.util.find_spec("kaggle") is not None else "absent"
    checks["network"] = "not probed (offline by default)"
    return {"doctor": checks}


def _python_version() -> str:
    import platform

    return platform.python_version()
