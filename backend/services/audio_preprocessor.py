from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

HIGHPASS_CUTOFF_HZ = 80
NOISE_PROP_DECREASE = 0.75
TARGET_LUFS = -23.0


def preprocess_audio(audio_path: Path) -> Path:
    """Apply audio preprocessing: high-pass filter, noise reduction, loudness normalization.

    Returns the path to the preprocessed WAV file (saved alongside the original).
    """
    import numpy as np
    import soundfile as sf
    from scipy.signal import butter, sosfilt

    logger.info("Preprocessing audio: %s", audio_path.name)

    data, sample_rate = sf.read(audio_path, dtype="float64")

    # Convert stereo to mono if needed
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    # 1. High-pass filter (80 Hz, 4th-order Butterworth)
    sos = butter(4, HIGHPASS_CUTOFF_HZ, btype="high", fs=sample_rate, output="sos")
    data = sosfilt(sos, data)

    # 2. Noise reduction (conservative)
    import noisereduce as nr

    data = nr.reduce_noise(
        y=data,
        sr=sample_rate,
        prop_decrease=NOISE_PROP_DECREASE,
        stationary=False,
    )

    # 3. Loudness normalization to -23 LUFS
    import pyloudnorm as pyln

    meter = pyln.Meter(sample_rate)
    loudness = meter.integrated_loudness(data)

    if not np.isinf(loudness):
        data = pyln.normalize.loudness(data, loudness, TARGET_LUFS)

    # Save preprocessed copy
    output_path = audio_path.parent / "audio_preprocessed.wav"
    sf.write(str(output_path), data, sample_rate)

    logger.info("Preprocessed audio saved: %s", output_path.name)
    return output_path
