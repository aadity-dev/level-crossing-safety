"""Local auditory alert warning simulation and PCM WAV synthesis."""

import io
import wave
from typing import Optional
import numpy as np
from level_crossing.common.types import SeverityLevel
from level_crossing.common.logger import get_logger

logger = get_logger("sound_simulator")


class SoundSimulator:
    """Simulates localized acoustic alarms based on alert severity."""

    PATTERNS = {
        SeverityLevel.MEDIUM: {"frequency_hz": 800, "duration_ms": 250, "pulses": 2},
        SeverityLevel.HIGH: {"frequency_hz": 1200, "duration_ms": 400, "pulses": 3},
        SeverityLevel.CRITICAL: {"frequency_hz": 2000, "duration_ms": 600, "pulses": 5},
    }

    def __init__(self, enable_audio: bool = False):
        self.enable_audio = enable_audio

    def play_alert(self, severity: SeverityLevel) -> None:
        pattern = self.PATTERNS.get(severity)
        if not pattern:
            return

        logger.info(
            f"AUDIO ALARM TRIGGERED [{severity.value}]: {pattern['frequency_hz']}Hz, "
            f"{pattern['pulses']} pulses x {pattern['duration_ms']}ms"
        )

    @classmethod
    def synthesize_wav(cls, severity: SeverityLevel) -> bytes:
        """Synthesizes high-fidelity 16-bit PCM WAV audio bytes for browser playback."""
        pattern = cls.PATTERNS.get(severity)
        if not pattern:
            return b""

        sample_rate = 22050
        freq = pattern["frequency_hz"]
        pulse_duration = pattern["duration_ms"] / 1000.0
        gap_duration = 0.08
        pulses = pattern["pulses"]

        samples = []
        for p in range(pulses):
            num_samples = int(sample_rate * pulse_duration)
            t = np.linspace(0, pulse_duration, num_samples, endpoint=False)
            tone = np.sin(2 * np.pi * freq * t)

            # Smooth attack/decay envelope (15ms ramp) to prevent acoustic speaker pops
            env_len = min(int(sample_rate * 0.015), num_samples // 4)
            envelope = np.ones(num_samples, dtype=np.float32)
            if env_len > 0:
                envelope[:env_len] = np.linspace(0, 1, env_len)
                envelope[-env_len:] = np.linspace(1, 0, env_len)

            tone = (tone * envelope * 32767 * 0.75).astype(np.int16)
            samples.append(tone)

            # Inter-pulse silence
            if p < pulses - 1:
                gap_samples = int(sample_rate * gap_duration)
                samples.append(np.zeros(gap_samples, dtype=np.int16))

        full_audio = np.concatenate(samples)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)      # Mono
            wf.setsampwidth(2)      # 16-bit PCM
            wf.setframerate(sample_rate)
            wf.writeframes(full_audio.tobytes())

        return buf.getvalue()
