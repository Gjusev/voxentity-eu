"""Telephone channel simulation (docs/03-data.md §D).

Fixed recipe, versioned RECIPE_VERSION: Butterworth order-6 bandpass
300-3400 Hz in SOS form, resample to 8 kHz, seeded Gaussian noise at
20 dB SNR relative to active-speech power (measured before the codec),
G.711 A-law encode/decode, PCM16 mono 8 kHz output. This is a simulated
channel, not a PSTN call and not a claim about every codec.

Gain rule shared by the pair: the master is peak-normalized to -6 dBFS
before either condition is derived; nothing is normalized afterwards.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.signal import butter, resample_poly

RECIPE_VERSION = "tel-1"
TARGET_PEAK = 0.5  # -6 dBFS common gain rule for the master
BAND_HZ = (300.0, 3400.0)
FILTER_ORDER = 6
TARGET_RATE = 8000
MASTER_RATE = 16000
TARGET_SNR_DB = 20.0
VAD_FRAME_S = 0.030
VAD_THRESHOLD_REL = 0.05  # frame active if rms > 5% of the max frame rms

A_LAW_A = 87.6


def design_bandpass(fs: int) -> np.ndarray:
    sos = butter(FILTER_ORDER, BAND_HZ, btype="bandpass", fs=fs, output="sos")
    return sos


def apply_bandpass(x: np.ndarray, fs: int) -> np.ndarray:
    from scipy.signal import sosfilt

    return sosfilt(design_bandpass(fs), x)


def resample(x: np.ndarray, up: int, down: int) -> np.ndarray:
    return resample_poly(x, up, down).astype(np.float64)


def normalize_peak(x: np.ndarray, peak: float = TARGET_PEAK) -> np.ndarray:
    m = float(np.max(np.abs(x))) if x.size else 0.0
    if m == 0.0:
        return x
    return x * (peak / m)


def active_speech_power(x: np.ndarray, fs: int) -> float:
    """Mean square over active frames; frames of 30 ms, relative threshold."""

    frame = max(1, int(round(VAD_FRAME_S * fs)))
    n = len(x) // frame
    if n == 0:
        return float(np.mean(x * x)) if x.size else 0.0
    rms = np.sqrt(np.mean((x[: n * frame].reshape(n, frame)) ** 2, axis=1))
    active = rms > (VAD_THRESHOLD_REL * float(np.max(rms)))
    if not active.any():
        active = rms > 0
    sel = x[: n * frame].reshape(n, frame)[active]
    return float(np.mean(sel * sel))


def add_noise(x: np.ndarray, snr_db: float, seed: int, fs: int) -> tuple[np.ndarray, float]:
    """Seeded Gaussian noise across the whole clip; SNR on active speech."""

    speech_power = active_speech_power(x, fs)
    if speech_power <= 0.0:
        return x, float("nan")
    noise_power = speech_power / (10.0 ** (snr_db / 10.0))
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(len(x)) * np.sqrt(noise_power)
    mixed = x + noise
    measured = active_speech_power(x, fs) / max(np.mean(noise * noise), 1e-30)
    return mixed, float(10.0 * np.log10(measured))


# --- G.711 A-law (canonical g711.c algorithm, public domain) --------------------


_SEG_AEND = np.array([0x1F, 0x3F, 0x7F, 0xFF, 0x1FF, 0x3FF, 0x7FF, 0xFFF], dtype=np.int64)


def a_law_encode(x: np.ndarray) -> np.ndarray:
    """Linear PCM in [-1,1) -> 8-bit A-law codes (13-bit segments)."""

    pcm = np.clip(np.round(x * 32768.0), -32768, 32767).astype(np.int64)
    pcm13 = np.clip(pcm >> 3, -4096, 4095)
    sign_pos = pcm13 >= 0
    mag = np.where(sign_pos, pcm13, -pcm13)
    # segment = first index with mag <= _SEG_AEND[idx]; saturate at 8
    seg = np.full_like(mag, 8)
    for i, end in enumerate(_SEG_AEND):
        seg = np.where((seg == 8) & (mag <= end), i, seg)
    aval = seg << 4
    mantissa = np.where(
        seg < 2,
        (mag >> 1) & 0x0F,
        (mag >> seg) & 0x0F,
    )
    aval = aval | mantissa
    mask = np.where(sign_pos, 0xD5, 0x55)
    codes = (aval ^ mask) & 0xFF
    codes = np.where(seg >= 8, (0x7F ^ mask) & 0xFF, codes)
    return codes.astype(np.uint8)


def a_law_decode(codes: np.ndarray) -> np.ndarray:
    """8-bit A-law codes -> linear PCM in [-1,1)."""

    c = codes.astype(np.int64) ^ 0x55
    mantissa = (c & 0x0F) << 4
    seg = (c & 0x70) >> 4
    t = mantissa + 8 + np.where(seg > 0, 0x100, 0)
    t = np.where(seg > 1, t << (seg - 1), t)
    linear16 = np.where(c & 0x80, t, -t)
    return linear16.astype(np.float64) / 32768.0


@dataclass
class TelephoneResult:
    samples: np.ndarray
    sample_rate: int
    measured_snr_db: float
    clipping_fraction: float
    filter_config: dict[str, Any]
    noise_seed: int


def telephone_from_master(
    master: np.ndarray,
    master_rate: int,
    *,
    noise_seed: int,
) -> TelephoneResult:
    master = normalize_peak(np.asarray(master, dtype=np.float64))
    bandpassed = apply_bandpass(master, master_rate)
    at8k = resample(bandpassed, TARGET_RATE, master_rate)
    noisy, measured_snr = add_noise(at8k, TARGET_SNR_DB, noise_seed, TARGET_RATE)
    codes = a_law_encode(noisy)
    decoded = a_law_decode(codes)
    # scale back to int16 range with the common rule; count saturation
    pcm = np.clip(np.round(decoded * 32768.0), -32768, 32767)
    clipping = float(np.mean(np.abs(pcm) >= 32767)) if pcm.size else 0.0
    return TelephoneResult(
        samples=pcm,
        sample_rate=TARGET_RATE,
        measured_snr_db=measured_snr,
        clipping_fraction=clipping,
        filter_config={
            "type": "butterworth_bandpass_sos",
            "order": FILTER_ORDER,
            "band_hz": list(BAND_HZ),
        },
        noise_seed=noise_seed,
    )


def clean_from_master(master: np.ndarray, master_rate: int) -> np.ndarray:
    master = normalize_peak(np.asarray(master, dtype=np.float64))
    if master_rate != MASTER_RATE:
        return np.clip(np.round(resample(master, MASTER_RATE, master_rate) * 32768.0), -32768, 32767)
    return np.clip(np.round(master * 32768.0), -32768, 32767)


def noise_seed_for(audio_id: str) -> int:
    return int(hashlib.sha256(f"noise:{audio_id}".encode()).hexdigest()[:12], 16)


# --- CLI ---------------------------------------------------------------------------


def cli_transform(manifest_path: str, recipe: str, resume: bool = True) -> dict[str, Any]:
    """Apply the recipe to every accepted clean master in the audio manifest."""

    from pathlib import Path

    import soundfile as sf

    from ..commands import InvalidInput
    from ..contracts import AudioRecord, TransformRecord, read_jsonl
    from ..provenance import sha256_file, write_text_atomic

    manifest_file = Path(manifest_path)
    audio = list(read_jsonl(manifest_file, AudioRecord))
    audio_root = manifest_file.parent.parent / "audio"
    out_dir = manifest_file.parent
    transforms_path = out_dir / "transforms.jsonl"
    transforms: list[TransformRecord] = []
    done: set[str] = set()
    if resume and transforms_path.exists():
        transforms = list(read_jsonl(transforms_path, TransformRecord))
        done = {t.transform_id for t in transforms}

    new_records: list[AudioRecord] = []
    for a in audio:
        if a.corpus != "synthetic" or a.condition != "clean":
            continue
        src = audio_root / a.path
        if not src.exists():
            raise InvalidInput(f"master audio missing: {src}")
        master, rate = sf.read(src, dtype="float64", always_2d=False)
        tid = f"tr-{a.audio_id}-tel"
        current_input_sha = sha256_file(src)
        prior = {t.transform_id: t for t in transforms}
        if tid in done and prior[tid].input_sha256 == current_input_sha:
            # cached: keep the telephone manifest row present even if the
            # manifest was rewritten by a synthesis resume
            tel_path_cached = audio_root / "synthetic" / "telephone" / f"{a.audio_id}.wav"
            if tel_path_cached.exists() and f"{a.audio_id}-tel" not in {x.audio_id for x in audio}:
                import soundfile as _sf

                tel_data, tel_rate = _sf.read(tel_path_cached, dtype="int16", always_2d=False)
                new_records.append(
                    AudioRecord.model_validate(
                        {
                            "audio_id": f"{a.audio_id}-tel",
                            "scenario_id": a.scenario_id,
                            "corpus": "synthetic",
                            "condition": "telephone",
                            "parent_audio_id": a.audio_id,
                            "path": f"synthetic/telephone/{a.audio_id}.wav",
                            "sha256": prior[tid].output_sha256,
                            "sample_rate_hz": TARGET_RATE,
                            "num_samples": int(len(tel_data)),
                            "duration_seconds": len(tel_data) / TARGET_RATE,
                            "transform_id": tid,
                            "qa_status": "pending_review",
                        }
                    )
                )
                audio.append(new_records[-1])
            continue  # cached transform still matches the current master bytes
        result = telephone_from_master(master, rate, noise_seed=noise_seed_for(a.audio_id))
        tel_dir = audio_root / "synthetic" / "telephone"
        tel_dir.mkdir(parents=True, exist_ok=True)
        tel_path = tel_dir / f"{a.audio_id}.wav"
        sf.write(tel_path, result.samples.astype(np.int16), TARGET_RATE, subtype="PCM_16")
        record = TransformRecord(
            transform_id=tid,
            recipe_version=RECIPE_VERSION,
            input_sha256=sha256_file(src),
            output_sha256=sha256_file(tel_path),
            filter_config=result.filter_config,
            resampler=f"scipy.resample_poly(up={TARGET_RATE},down={rate})",
            codec="g711_alaw_roundtrip",
            noise_seed=result.noise_seed,
            target_snr_db=TARGET_SNR_DB,
            measured_snr_db=result.measured_snr_db,
            clipping_fraction=result.clipping_fraction,
            command_argv=[],
            tool_versions={"numpy": np.__version__, "scipy": __import__("scipy").__version__},
        )
        transforms = [t for t in transforms if t.transform_id != tid] + [record]
        new_records.append(
            AudioRecord.model_validate(
                {
                    "audio_id": f"{a.audio_id}-tel",
                    "scenario_id": a.scenario_id,
                    "corpus": "synthetic",
                    "condition": "telephone",
                    "parent_audio_id": a.audio_id,
                    "path": f"synthetic/telephone/{a.audio_id}.wav",
                    "sha256": record.output_sha256,
                    "sample_rate_hz": TARGET_RATE,
                    "num_samples": len(result.samples),
                    "duration_seconds": len(result.samples) / TARGET_RATE,
                    "transform_id": tid,
                    "qa_status": "pending_review",
                }
            )
        )

    write_text_atomic(
        transforms_path, "\n".join(t.model_dump_json() for t in transforms) + "\n"
    )
    merged: dict[str, AudioRecord] = {a.audio_id: a for a in audio}
    for rec in new_records:
        merged[rec.audio_id] = rec  # regenerated telephone replaces the stale row
    write_text_atomic(
        out_dir / "audio_manifest.jsonl",
        "\n".join(r.model_dump_json() for r in sorted(merged.values(), key=lambda r: r.audio_id)) + "\n",
    )
    return {
        "transforms_total": len(transforms),
        "new_transforms": len(new_records),
        "manifest": str(out_dir / "audio_manifest.jsonl"),
    }
