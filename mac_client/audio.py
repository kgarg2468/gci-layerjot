from __future__ import annotations

from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf


def record_push_to_talk(
    output_file: Path,
    sample_rate: int = 16000,
    channels: int = 1,
    max_seconds: int = 20,
) -> Path:
    """
    Push-to-talk recorder for terminal usage.
    Press Enter to start and Enter to stop.
    """
    input("Press Enter to start recording...")
    print("Recording now. Press Enter to stop.")

    max_samples = sample_rate * max_seconds
    recording = sd.rec(max_samples, samplerate=sample_rate, channels=channels, dtype="float32")

    input()
    sd.stop()
    sd.wait()

    audio = np.squeeze(recording)
    if audio.ndim == 0:
        raise RuntimeError("No audio captured.")

    # Trim near-silence at the tail of a pre-allocated recording buffer.
    non_silent_idx = np.where(np.abs(audio) > 1e-4)[0]
    if len(non_silent_idx) > 0:
        audio = audio[: non_silent_idx[-1] + 1]

    if len(audio) == 0:
        raise RuntimeError("Captured empty audio. Please try again.")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_file), audio, sample_rate)
    return output_file
