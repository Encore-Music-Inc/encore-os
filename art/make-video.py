"""The ENCORE. OS welcome video (a placeholder until Jimmy records the real one).

    python3 make-video.py <out.mp4>        (needs ffmpeg, Pillow and numpy)

About 22 seconds at 1280x720, 30 fps: the mark builds, "your studio.", Record. Mix.
Release., the apps that come with it, then "Let’s get you set up." A soft synth pad plays
under it, with a low thump when the orange dot lands. Everything is drawn here, no
footage or samples, so it can be rebuilt any time.
"""
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
import brand as B

W, H, FPS = 1280, 720, 30
LENGTH = 22.0
SR = 48000

# scenes: (start, end) in seconds; neighbours cross-fade over FADE
FADE = 0.6
SCENES = [(0.0, 4.0), (4.0, 8.6), (8.6, 13.6), (13.6, 18.2), (18.2, LENGTH)]

APPS = [("Basement Studio", "Record and mix"), ("ENCORE.", "Put your music out"), ("Vox", "Your vocal chain"),
        ("Master", "Ready to release"), ("Hydrogen", "Drum machine"), ("VLC", "Plays anything"),
        ("Writer", "Lyrics and notes"), ("Files", "Your songs")]


def blank():
    return Image.new("RGB", (W, H), B.BG)


def rise(d, xy, text, f, fill, k, dy=24, anchor="mm"):
    """Text that fades in while rising dy px (k = 0..1)."""
    if k <= 0:
        return
    x, y = xy
    d.text((x, y + (1 - B.ease_out(k)) * dy), text, font=f, fill=B.mix(B.BG, fill, B.ease_out(k)), anchor=anchor)


def scene0(t):
    img = blank()
    B.mark(img, t - 0.2, W / 2, H / 2 - 30, 230)
    d = ImageDraw.Draw(img)
    k = B.ease_out(B.span(t, 1.5, 2.1))
    if k > 0:
        B.spaced(d, (W / 2, H / 2 + 130 + (1 - k) * 12), "ENCORE. OS", B.font(26, mono=True), B.mix(B.BG, B.SOFT, k), tracking=0.42)
    return img


def scene1(t):
    img = blank()
    d = ImageDraw.Draw(img)
    rise(d, (W / 2, H / 2 - 70), "Welcome to", B.font(34, 500), B.SOFT, B.span(t, 0.2, 0.8))
    f = B.font(118, 800)
    words = ["your", "studio"]
    widths = [d.textlength(w + " ", font=f) for w in words]
    dot = d.textlength(".", font=f)
    x = W / 2 - (sum(widths) - d.textlength(" ", font=f) + dot) / 2
    for i, w in enumerate(words):
        k = B.span(t, 0.6 + i * 0.25, 1.3 + i * 0.25)
        if k > 0:
            d.text((x, H / 2 + 50 + (1 - B.ease_out(k)) * 30), w, font=f, fill=B.mix(B.BG, B.PAPER, B.ease_out(k)), anchor="lm")
        x += widths[i]
    x -= d.textlength(" ", font=f)
    k = B.span(t, 1.3, 1.7)
    if k > 0:
        d.text((x, H / 2 + 50), ".", font=f, fill=B.mix(B.BG, B.ORANGE, B.ease_out(k)), anchor="lm")
    # an orange line draws itself under it
    k = B.ease_in_out(B.span(t, 1.6, 2.6))
    if k > 0:
        lw = 460
        d.rectangle([W / 2 - lw / 2, H / 2 + 135, W / 2 - lw / 2 + lw * k, H / 2 + 141], fill=B.ORANGE)
    rise(d, (W / 2, H / 2 + 190), "It boots up ready to play.", B.font(26, 400), B.DIM, B.span(t, 2.4, 3.0))
    return img


def scene2(t):
    img = blank()
    d = ImageDraw.Draw(img)
    f = B.font(128, 800)
    lines = [("Record", "BASEMENT STUDIO"), ("Mix", "THE ENCORE. PLUGINS"), ("Release", "ENCORE.")]
    for i, (word, tag) in enumerate(lines):
        k = B.ease_out(B.span(t, 0.2 + i * 0.45, 0.9 + i * 0.45))
        if k <= 0:
            continue
        y = 190 + i * 150
        x = 150 - (1 - k) * 80
        d.text((x, y), word, font=f, fill=B.mix(B.BG, B.PAPER, k), anchor="lm")
        wx = x + d.textlength(word, font=f)
        d.text((wx, y), ".", font=f, fill=B.mix(B.BG, B.ORANGE, k), anchor="lm")
        k2 = B.ease_out(B.span(t, 0.6 + i * 0.45, 1.2 + i * 0.45))
        if k2 > 0:
            B.spaced(d, (wx + 80, y + 14), tag, B.font(20, mono=True), B.mix(B.BG, B.DIM, k2), tracking=0.3, anchor="l")
    return img


def tile(img, box, title, sub, k, accent):
    x0, y0, x1, y1 = box
    lift = (1 - B.ease_out(k)) * 24
    y0, y1 = y0 + lift, y1 + lift
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, y0, x1, y1], radius=20, fill=B.mix(B.BG, B.SURFACE, k), outline=B.mix(B.BG, (44, 39, 35), k), width=2)
    s = 54
    d.rounded_rectangle([x0 + 22, y0 + 22, x0 + 22 + s, y0 + 22 + s], radius=14, fill=B.mix(B.BG, accent, k))
    d.text((x0 + 22 + s / 2, y0 + 22 + s / 2 + 1), title[0], font=B.font(30, 800), fill=B.mix(B.BG, B.PAPER, k), anchor="mm")
    d.text((x0 + 22, y1 - 52), title, font=B.font(24, 700), fill=B.mix(B.BG, B.PAPER, k), anchor="ls")
    d.text((x0 + 22, y1 - 24), sub, font=B.font(18, 400), fill=B.mix(B.BG, B.DIM, k), anchor="ls")


def scene3(t):
    img = blank()
    d = ImageDraw.Draw(img)
    rise(d, (W / 2, 92), "Everything’s already here.", B.font(50, 800), B.PAPER, B.span(t, 0.1, 0.7))
    cols, tw, th, gap = 4, 262, 200, 22
    x0 = (W - (cols * tw + (cols - 1) * gap)) / 2
    for i, (title, sub) in enumerate(APPS):
        k = B.span(t, 0.5 + i * 0.12, 1.1 + i * 0.12)
        if k <= 0:
            continue
        c, r = i % cols, i // cols
        accent = B.ORANGE if i == 0 else (B.EMBER if i < 3 else (60, 53, 47))
        tile(img, (x0 + c * (tw + gap), 170 + r * (th + gap), x0 + c * (tw + gap) + tw, 170 + r * (th + gap) + th), title, sub, k, accent)
    return img


def scene4(t):
    img = blank()
    d = ImageDraw.Draw(img)
    rise(d, (W / 2, H / 2 - 120), "Plug in. Press record.", B.font(64, 800), B.PAPER, B.span(t, 0.1, 0.7))
    B.mark(img, t - 0.5, W / 2, H / 2 + 40, 120)
    d = ImageDraw.Draw(img)
    rise(d, (W / 2, H / 2 + 165), "Let’s get you set up.", B.font(30, 500), B.SOFT, B.span(t, 1.6, 2.2))
    # fade to black at the very end
    k = B.span(t, LENGTH - SCENES[4][0] - 0.7, LENGTH - SCENES[4][0])
    if k > 0:
        img = Image.blend(img, blank(), B.ease_in_out(k))
    return img


DRAW = [scene0, scene1, scene2, scene3, scene4]


def frame(t):
    # the scenes on screen now (two of them during a cross-fade), and how much of the later one
    live = [i for i, (a, b) in enumerate(SCENES) if (a - FADE / 2 if i else 0) <= t < (b + FADE / 2 if i < len(SCENES) - 1 else b + 1)]
    if not live:
        return blank()
    if len(live) == 1:
        return DRAW[live[0]](t - SCENES[live[0]][0])
    i, j = live[0], live[1]
    w = B.ease_in_out((t - (SCENES[j][0] - FADE / 2)) / FADE)
    return Image.blend(DRAW[i](t - SCENES[i][0]), DRAW[j](t - SCENES[j][0]), w)


# ---------- the music: a warm pad, a soft pluck, a thump when the dot lands ----------

def note(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def pad_voice(freq, length, t0, out):
    n = int(length * SR)
    t = np.arange(n) / SR
    env = np.minimum(1, t / 1.4) * np.minimum(1, (length - t) / 1.6).clip(0, 1)
    vib = 1 + 0.0025 * np.sin(2 * np.pi * 0.23 * t)
    sig = np.zeros(n)
    for h, a in [(1, 1.0), (2, 0.35), (3, 0.18), (4, 0.08)]:
        for det in (-0.004, 0.004):   # two slightly detuned copies for width
            sig += a * np.sin(2 * np.pi * freq * h * (1 + det) * t * vib + h)
    s = int(t0 * SR)
    out[s:s + n] += sig * env * 0.05


def pluck(freq, t0, out, amp=0.12):
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    sig = (np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(4 * np.pi * freq * t)) * np.exp(-t * 4.5)
    s = int(t0 * SR)
    m = min(n, len(out) - s)
    if m > 0:
        out[s:s + m] += sig[:m] * amp


def thump(t0, out, amp=0.5):
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    f = 52 + 70 * np.exp(-t * 18)
    sig = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    s = int(t0 * SR)
    out[s:s + n] += sig * amp


def music(path):
    out = np.zeros(int((LENGTH + 2) * SR))
    # Cmaj9, Am9, Fmaj9, G6/9, then home to C
    chords = [[48, 55, 64, 71, 74], [45, 52, 60, 67, 71], [41, 48, 57, 64, 67], [43, 50, 59, 64, 69], [48, 55, 64, 67, 71]]
    starts = [0.0, 4.4, 8.8, 13.2, 17.6]
    for c, s in zip(chords, starts):
        for n in c:
            pad_voice(note(n), 5.4 if s < 17 else LENGTH - s + 0.4, s, out)
    # the dot lands at 0.2 + 1.03 s in scene 0, and again in the last scene
    thump(1.25, out)
    thump(SCENES[4][0] + 0.5 + 1.03, out, 0.35)
    # a gentle arpeggio through Record. Mix. Release. and the apps
    beat = 60 / 96 / 2
    t = 8.6
    seq = [72, 76, 79, 83, 79, 76]
    i = 0
    while t < 18.0:
        chord = chords[min(4, int((t + 0.01) // 4.4))]
        top = [n + 24 for n in chord[1:]]
        pluck(note(top[i % len(top)]), t, out, 0.07)
        t += beat
        i += 1
    # soften the top end, then level it
    y = np.zeros_like(out)
    a = 0.18
    for k in range(1, len(out)):
        y[k] = y[k - 1] + a * (out[k] - y[k - 1])
    y = y[: int(LENGTH * SR)]
    y /= np.max(np.abs(y)) / 0.7
    st = np.stack([y, np.roll(y, 240) * 0.96], axis=1)
    pcm = (st * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main(out):
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    wav = out.with_suffix(".wav")
    music(wav)
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", str(wav), "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.0",
                           "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest", str(out)], stdin=subprocess.PIPE)
    for i in range(int(LENGTH * FPS)):
        ff.stdin.write(frame(i / FPS).tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        sys.exit("ffmpeg failed")
    wav.unlink()
    print(f"welcome video: {out} ({out.stat().st_size // 1024} KB, {LENGTH:.0f} s)")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--still":
        frame(float(sys.argv[2])).save(sys.argv[3])
    else:
        main(sys.argv[1] if len(sys.argv) > 1 else "build/welcome.mp4")
