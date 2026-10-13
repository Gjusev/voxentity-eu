"""Kaggle GPU kernel: Voxtral-Mini-3B ASR run over the frozen inputs bundle.

Run from scripts/kaggle/ after uploading the src+inputs dataset. Produces
runs/voxtral-mini/{predictions.jsonl,run_manifest.json,cache.jsonl} in the
kernel output. Gold is never present in the inputs bundle.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SRC = Path("/kaggle/input/voxentity-eu-src/src")
INPUTS = Path("/kaggle/input/voxentity-eu-inputs")


def main() -> int:
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "-q",
            "pydantic>=2.7", "numpy", "scipy", "soundfile", "jiwer>=3.0",
            "transformers>=4.53", "accelerate", "librosa",
        ],
        check=False,
    )
    sys.path.insert(0, str(SRC))
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
