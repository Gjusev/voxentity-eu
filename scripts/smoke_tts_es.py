"""Spanish smoke for the ES suite: one Qwen3-TTS clip per core voice + Whisper round trip.

The round trip is an automated intelligibility alert only (never a corpus
filter); it cannot replace listening. Writes data/smoke_tts/es_report.json.
"""

import json
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

from voxentity_eu.adapters.whisper import WhisperTurbo
from voxentity_eu.audio.synthesize import MODEL_ID, MODEL_REVISION

TEXT = "Mi número de teléfono es más tres cuatro seis uno dos, tres cuatro cinco, seis siete ocho."
out = Path("data/smoke_tts")
model = Qwen3TTSModel.from_pretrained(MODEL_ID, revision=MODEL_REVISION, device_map="cuda:0",
                                      dtype=torch.float32, attn_implementation="sdpa")
report = {"text": TEXT, "trials": []}
for voice in ("serena", "dylan"):
    wavs, sr = model.generate_custom_voice(text=TEXT, speaker=voice, language="spanish")
    path = out / f"es_{voice}.wav"
    sf.write(path, (np.asarray(wavs[0]) * 32767).astype(np.int16), sr)
    report["trials"].append({"voice": voice, "file": path.name, "seconds": round(len(wavs[0]) / sr, 2)})
del model
torch.cuda.empty_cache()
asr = WhisperTurbo()
asr.load()
for t in report["trials"]:
    t["whisper"] = asr.transcribe(str(out / t["file"]), "es-ES").transcript
(out / "es_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=1))
