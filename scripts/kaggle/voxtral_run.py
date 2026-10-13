"""Kaggle GPU kernel: Voxtral-Mini-3B ASR run over the frozen inputs bundle.

Robust to dataset layout (files or zip); prints the mounted layout for
diagnosability. Gold is never present in the inputs dataset.
"""

from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

INPUTS = Path("/kaggle/input/voxentity-eu-inputs")


def find_package_root() -> Path:
    base = Path("/kaggle/input/voxentity-eu-src")
    candidates = [
        base / "src",                    # dataset ships src/voxentity_eu/...
        base,                            # dataset ships voxentity_eu/...
        base / "src" / "src",            # zipped src/ containing src/
    ]
    for c in candidates:
        if (c / "voxentity_eu" / "__init__.py").exists():
            return c
    # zip fallback: extract the first zip that contains the package
    for z in base.rglob("*.zip"):
        out = Path("/kaggle/working/pkg")
        if (out / "voxentity_eu" / "__init__.py").exists():
            return out
        out.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(z) as zf:
            zf.extractall(out)
        if (out / "voxentity_eu" / "__init__.py").exists():
            return out
        if (out / "src" / "voxentity_eu" / "__init__.py").exists():
            return out / "src"
    print("DATASET LAYOUT:", file=sys.stderr)
    for p in sorted(base.rglob("*"))[:40]:
        print("  ", p, file=sys.stderr)
    raise SystemExit(3)


def main() -> int:
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "-q",
            "pydantic>=2.7", "numpy", "scipy", "soundfile", "jiwer>=3.0",
            "transformers>=4.53", "accelerate", "librosa",
        ],
        check=False,
    )
    pkg = find_package_root()
    print("package root:", pkg, flush=True)
    sys.path.insert(0, str(pkg))
    import torch  # noqa: F401  (verifies CUDA torch availability)

    from voxentity_eu.runner import run_asr

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    dtype = "bfloat16" if device == "cuda:0" else "float32"
    result = run_asr(
        INPUTS,
        "voxtral-mini",
        Path("/kaggle/working/runs/voxtral-mini"),
        device=device,
        dtype=dtype,
        resume=True,
    )
    print(json.dumps(result, indent=1))
    return 0 if result["failed"] < result["rows"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
