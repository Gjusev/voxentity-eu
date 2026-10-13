"""Smoke test: Qwen3-TTS CustomVoice on local GPU (one utterance per language/voice).

Produces data/smoke_tts/*.wav plus a JSON verdict. Never pretends a failed
download is a model result.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

OUT = Path("data/smoke_tts")
OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    import torch
    from qwen_tts import Qwen3TTSModel

    report: dict = {"torch": torch.__version__, "cuda": torch.cuda.is_available()}
    if not torch.cuda.is_available():
        report["error"] = "no cuda"
        (OUT / "report.json").write_text(json.dumps(report, indent=1))
        return 3
    report["gpu"] = torch.cuda.get_device_name(0)

    model = Qwen3TTSModel.from_pretrained(
        "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
        revision="85e237c12c027371202489a0ec509ded67b5e4b5",
        device_map="cuda:0",
        dtype=torch.float16,  # Pascal GTX 1080: no bf16 hardware, no flash-attn
        attn_implementation="sdpa",
    )
    report["speakers"] = model.get_supported_speakers()
    report["languages"] = model.get_supported_languages()

    import soundfile as sf

    texts = {
        "German": "Meine Rufnummer ist plus vier neun, eins sieben null, eins zwei drei vier fünf sechs sieben.",
        "French": "Mon numéro est le plus trois trois, six un, deux trois, quatre cinq, six sept, huit neuf.",
    }
    speakers = report["speakers"][:4] if isinstance(report["speakers"], list) else []
    ok: list[str] = []
    for speaker in speakers:
        for language, text in texts.items():
            try:
                wavs, sr = model.generate_custom_voice(text=text, speaker=speaker, language=language)
                name = f"{speaker}_{language}.wav".replace(" ", "_")
                sf.write(OUT / name, wavs[0], sr)
                dur = len(wavs[0]) / sr
                ok.append({"speaker": speaker, "language": language, "sr": sr, "duration_s": round(dur, 2), "file": name})
            except Exception as exc:  # noqa: BLE001
                ok.append({"speaker": speaker, "language": language, "error": f"{type(exc).__name__}: {exc}"})
    report["generations"] = ok
    (OUT / "report.json").write_text(json.dumps(report, indent=1, ensure_ascii=False))
    failed = sum(1 for g in ok if "error" in g)
    print(f"smoke: {len(ok) - failed}/{len(ok)} generations ok")
    return 0 if ok and failed < len(ok) else 3


if __name__ == "__main__":
    sys.exit(main())
