"""ENCORE. OS wallpapers: the desktop (encore-dark) and the login screen (encore-login).

    python3 make-wallpapers.py <out dir>      (2560x1440; the desktop crops to fit any screen)
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import brand as B

W, H = 2560, 1440


def glow(img, cx, cy, r, colour, strength):
    g = Image.new("L", img.size, 0)
    ImageDraw.Draw(g).ellipse([cx - r, cy - r, cx + r, cy + r], fill=round(255 * strength))
    g = g.filter(ImageFilter.GaussianBlur(r * 0.6))
    img.paste(Image.new("RGB", img.size, colour), (0, 0), g)


def grain(img, amount=3):
    """A touch of noise (about +-amount levels) so the dark gradients don't band on 8-bit screens."""
    import numpy as np
    rng = np.random.default_rng(7)
    a = np.asarray(img).astype(np.int16) + rng.integers(-amount, amount + 1, size=(img.size[1], img.size[0], 1))
    return Image.fromarray(a.clip(0, 255).astype("uint8"))


def desktop():
    img = Image.new("RGB", (W, H), B.BG)
    glow(img, W * 0.86, H * 0.92, 700, B.EMBER, 0.10)
    # a huge, quiet E. off to the right; the dot keeps its colour
    B.mark(img, 99, W * 0.79, H * 0.53, 1000, ink=B.mix(B.BG, B.PAPER, 0.05), dot=B.mix(B.BG, B.ORANGE, 0.55), glow=False, build=False)
    d = ImageDraw.Draw(img)
    img = grain(img)
    d = ImageDraw.Draw(img)
    B.spaced(d, (120, H - 110), "ENCORE. OS", B.font(26, mono=True), B.mix(B.BG, B.DIM, 0.55), tracking=0.42, anchor="l")
    return img


def login():
    img = Image.new("RGB", (W, H), B.BG)
    glow(img, W / 2, H * 1.05, 900, B.EMBER, 0.13)
    img = grain(img)
    B.mark(img, 99, W / 2, H * 0.24, 150, glow=True, build=False)
    return img


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "build")
    out.mkdir(parents=True, exist_ok=True)
    desktop().save(out / "encore-dark.png", optimize=True)
    login().save(out / "encore-login.png", optimize=True)
    print("wallpapers:", out)
