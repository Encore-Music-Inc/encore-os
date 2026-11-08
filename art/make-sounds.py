"""ENCORE. OS sounds: the test sound the Welcome plays (a soft two-note chime, C then G).

    python3 make-sounds.py <out dir>
"""
import sys
import wave
from pathlib import Path
import numpy as np

SR = 48000


def chime(path):
    t = np.arange(int(1.8 * SR)) / SR
    out = np.zeros_like(t)
    for f, start in [(523.25, 0.0), (783.99, 0.22)]:
        tt = np.clip(t - start, 0, None)
        env = (t >= start) * (1 - np.exp(-tt * 300)) * np.exp(-tt * 3.2)
        out += env * (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt) + 0.08 * np.sin(6 * np.pi * f * tt))
    out = out / np.max(np.abs(out)) * 0.5
    pcm = (np.stack([out, out], axis=1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "build")
    out.mkdir(parents=True, exist_ok=True)
    chime(out / "test-sound.wav")
    print("sounds:", out / "test-sound.wav")
