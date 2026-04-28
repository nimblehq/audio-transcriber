from __future__ import annotations

import wave
from pathlib import Path

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("soundfile")
pytest.importorskip("noisereduce")
pytest.importorskip("pyloudnorm")

from backend.services.audio_preprocessor import (  # noqa: E402
    HIGHPASS_CUTOFF_HZ,
    NOISE_PROP_DECREASE,
    TARGET_LUFS,
    preprocess_audio,
)


def _create_wav(path: Path, duration_s: float = 0.5, sample_rate: int = 16000) -> None:
    """Create a WAV file with a 440 Hz sine wave."""
    n_samples = int(sample_rate * duration_s)
    t = np.linspace(0, duration_s, n_samples, endpoint=False)
    signal = (np.sin(2 * np.pi * 440 * t) * 16000).astype(np.int16)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(signal.tobytes())


class TestPreprocessAudio:
    def test_returns_preprocessed_path(self, tmp_path: Path):
        wav = tmp_path / "audio.wav"
        _create_wav(wav)

        result = preprocess_audio(wav)

        assert result == tmp_path / "audio_preprocessed.wav"
        assert result.exists()

    def test_preserves_original_file(self, tmp_path: Path):
        wav = tmp_path / "audio.wav"
        _create_wav(wav)
        original_size = wav.stat().st_size

        preprocess_audio(wav)

        assert wav.exists()
        assert wav.stat().st_size == original_size

    def test_output_is_valid_wav(self, tmp_path: Path):
        import soundfile as sf

        wav = tmp_path / "audio.wav"
        _create_wav(wav)

        result = preprocess_audio(wav)

        data, sr = sf.read(str(result))
        assert sr == 16000
        assert len(data) > 0

    def test_stereo_input_produces_mono_output(self, tmp_path: Path):
        import soundfile as sf

        wav = tmp_path / "stereo.wav"
        n_samples = 8000
        stereo = np.column_stack(
            [
                np.sin(2 * np.pi * 440 * np.linspace(0, 0.5, n_samples)),
                np.sin(2 * np.pi * 880 * np.linspace(0, 0.5, n_samples)),
            ]
        )
        sf.write(str(wav), stereo, 16000)

        result = preprocess_audio(wav)

        data, _ = sf.read(str(result))
        assert data.ndim == 1

    def test_constants_match_spec(self):
        assert HIGHPASS_CUTOFF_HZ == 80
        assert NOISE_PROP_DECREASE == 0.75
        assert TARGET_LUFS == -23.0
