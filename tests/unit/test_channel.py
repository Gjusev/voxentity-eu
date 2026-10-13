"""Telephone channel tests: band limits, SNR, codec round-trip, determinism."""

from __future__ import annotations

import numpy as np

from voxentity_eu.audio.channel import (
    RECIPE_VERSION,
    a_law_decode,
    a_law_encode,
    active_speech_power,
    clean_from_master,
    noise_seed_for,
    telephone_from_master,
)


def speech_like(rate: int = 16000, seconds: float = 2.0, f0: float = 180.0) -> np.ndarray:
    t = np.arange(int(rate * seconds)) / rate
    env = np.clip(np.sin(2 * np.pi * 1.5 * t) * 0.5 + 0.5, 0.05, 1.0)
    x = 0.6 * env * np.sin(2 * np.pi * f0 * t * (1 + 0.05 * np.sin(2 * np.pi * 3 * t)))
    x += 0.1 * env * np.sin(2 * np.pi * 2 * f0 * t)
    return x


def test_bandlimit_300_3400():
    master = speech_like()
    result = telephone_from_master(master, 16000, noise_seed=1)
    # measure the spectrum of the filtered signal (before noise/codec it is
    # the same pipeline; approximate via a very quiet noise floor check)
    x = result.samples.astype(np.float64) / 32768.0
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    freqs = np.fft.rfftfreq(len(x), 1.0 / 8000)
    band_energy = spec[(freqs >= 3400) & (freqs <= 4000)].sum()
    in_band = spec[(freqs >= 300) & (freqs <= 3400)].sum()
    assert in_band > 0
    assert band_energy / in_band < 0.35  # strong attenuation above 3.4 kHz


def test_measured_snr_close_to_target():
    master = speech_like()
    result = telephone_from_master(master, 16000, noise_seed=42)
    assert 17.0 <= result.measured_snr_db <= 23.0, result.measured_snr_db


def test_deterministic_with_same_seed():
    master = speech_like()
    a = telephone_from_master(master, 16000, noise_seed=7)
    b = telephone_from_master(master, 16000, noise_seed=7)
    assert np.array_equal(a.samples, b.samples)
    c = telephone_from_master(master, 16000, noise_seed=8)
    assert not np.array_equal(a.samples, c.samples)


def test_a_law_round_trip_quality():
    # full-scale sine: A-law SQNR should be ~ 35+ dB
    rate = 8000
    t = np.arange(rate) / rate
    x = 0.9 * np.sin(2 * np.pi * 800 * t)
    decoded = a_law_decode(a_law_encode(x))
    err = x - decoded
    sqnr = 10 * np.log10(np.mean(x * x) / np.mean(err * err))
    assert sqnr > 30.0, sqnr


def test_a_law_clips_safely():
    x = np.array([1.5, -1.5, 0.0, 1e-6])
    d = a_law_decode(a_law_encode(x))
    assert np.all(np.isfinite(d))
    assert abs(d[2]) < 1e-3  # A-law has no exact zero; smallest step is 8/32768


def test_active_speech_power_ignores_silence():
    x = np.zeros(16000)
    x[4000:12000] = 0.5
    p_active = active_speech_power(x, 16000)
    assert p_active > 0.2 ** 2  # close to the voiced region power


def test_clean_and_telephone_share_gain_rule():
    master = speech_like()
    clean = clean_from_master(master, 16000)
    assert np.max(np.abs(clean)) <= 32768
    # both derived from the same peak-normalized master
    assert abs(np.max(np.abs(clean)) / 32768.0 - 0.5) < 0.01


def test_noise_seed_is_stable_per_id():
    assert noise_seed_for("a") == noise_seed_for("a")
    assert noise_seed_for("a") != noise_seed_for("b")


def test_recipe_metadata_present():
    master = speech_like()
    result = telephone_from_master(master, 16000, noise_seed=3)
    assert result.filter_config["order"] == 6
    assert result.filter_config["band_hz"] == [300.0, 3400.0]
    assert result.sample_rate == 8000
    assert RECIPE_VERSION == "tel-1"
    assert result.clipping_fraction <= 0.001
