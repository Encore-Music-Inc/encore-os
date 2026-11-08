"""ENCORE. OS artwork: the colours, fonts and the animated "E." mark.

The boot animation (make-boot.py), the welcome video (make-video.py) and the wallpapers
(make-wallpapers.py) all draw the mark with mark() so it moves the same way everywhere.
Pillow only. Times are in seconds.
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"

# encore-tokens.css
BG = (12, 10, 9)          # --bg-base-default #0c0a09
SURFACE = (23, 20, 18)    # --bg-surface-default #171412
PAPER = (242, 239, 232)   # --brand-paper #f2efe8
ORANGE = (255, 59, 0)     # --brand-primary #ff3b00
EMBER = (255, 110, 40)    # --brand-ember #ff6e28
SOFT = (189, 180, 169)    # --text-secondary #bdb4a9
DIM = (145, 136, 125)     # --text-muted #91887d

# The mark, in the 100-unit box of brand/encore-icon.svg
BAR = (31.0, 18.0, 41.06, 82.0)
ARMS = [(31.0, 18.0, 58.43, 27.14), (31.0, 44.06, 54.86, 53.20), (31.0, 72.86, 58.43, 82.0)]
DOT = (61.63, 72.31, 71.32, 82.0)
MARK_CX, MARK_CY = (31.0 + 71.32) / 2, 50.0   # centre of the mark
MARK_H = 64.0                                  # units tall

INTRO = 1.45      # the mark has finished building by now
PULSE = 1.6       # then the dot breathes, once per this many seconds


def font(size, weight=700, mono=False, italic=False):
    if mono:
        return ImageFont.truetype(str(FONTS / ("SpaceMono-Bold.ttf" if weight >= 600 else "SpaceMono-Regular.ttf")), size)
    f = ImageFont.truetype(str(FONTS / ("DMSans-Italic.ttf" if italic else "DMSans.ttf")), size)
    try:
        f.set_variation_by_axes([min(40, max(9, size / 2)), weight])   # optical size, weight
    except Exception:
        pass
    return f


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_back(x, s=2.2):
    x = clamp(x)
    return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2


def span(t, a, b):
    return clamp((t - a) / (b - a))


def mix(c1, c2, k):
    return tuple(round(c1[i] + (c2[i] - c1[i]) * k) for i in range(3))


def mark(img, t, cx, cy, height, ink=PAPER, dot=ORANGE, bg=BG, glow=True, build=True):
    """Draw the mark centred on (cx, cy), `height` px tall, as it looks t seconds in.
    build=False draws it finished (t still drives the breathing dot)."""
    s = height / MARK_H
    X = lambda u: cx + (u - MARK_CX) * s
    Y = lambda u: cy + (u - MARK_CY) * s
    tb = t if build else 99.0
    d = ImageDraw.Draw(img)

    # the dot drops in with a bounce, then breathes; its glow goes underneath the E
    kd = span(tb, 0.78, 1.28)
    x0, y0, x1, y1 = DOT
    drop = (1 - ease_back(kd)) * -26
    breathe = 0.0 if tb < INTRO else 0.5 - 0.5 * math.cos(2 * math.pi * (t - INTRO) / PULSE)
    if glow and kd > 0:
        g = Image.new("L", img.size, 0)
        gd = ImageDraw.Draw(g)
        r = (x1 - x0) * s * (0.9 + 0.5 * breathe)
        mx, my = X((x0 + x1) / 2), Y((y0 + y1) / 2 + drop)
        gd.ellipse([mx - r, my - r, mx + r, my + r], fill=round(255 * (0.25 + 0.3 * breathe) * clamp(kd * 2)))
        g = g.filter(ImageFilter.GaussianBlur(max(2, r * 0.8)))
        img.paste(Image.new("RGB", img.size, dot), (0, 0), g)
    d = ImageDraw.Draw(img)

    # the upright grows down, then the three arms slide out, one after another
    k = ease_out(span(tb, 0.0, 0.42))
    if k > 0:
        bx0, by0, bx1, by1 = BAR
        d.rectangle([X(bx0), Y(by0), X(bx1), Y(by0 + (by1 - by0) * k)], fill=ink)
    for i, (ax0, ay0, ax1, ay1) in enumerate(ARMS):
        k = ease_out(span(tb, 0.22 + i * 0.1, 0.58 + i * 0.1))
        if k > 0:
            d.rectangle([X(ax0), Y(ay0), X(ax0 + (ax1 - ax0) * k), Y(ay1)], fill=ink)
    if kd <= 0:
        return
    k = kd
    d.rectangle([X(x0), Y(y0 + drop), X(x1), Y(y1 + drop)], fill=mix(bg, dot, clamp(k * 3)))


def wordmark(img, xy, size, ink=PAPER, dot=ORANGE, anchor="ls", alpha=1.0, bg=BG):
    """ENCORE. in DM Sans heavy, with the orange full stop. xy is the text's anchor point."""
    d = ImageDraw.Draw(img)
    f = font(size, 800)
    word = "ENCORE"
    w = d.textlength(word, font=f)
    dw = d.textlength(".", font=f)
    x, y = xy
    if anchor[0] == "m":
        x -= (w + dw) / 2
    elif anchor[0] == "r":
        x -= w + dw
    a = "l" + anchor[1]
    d.text((x, y), word, font=f, fill=mix(bg, ink, alpha), anchor=a)
    d.text((x + w, y), ".", font=f, fill=mix(bg, dot, alpha), anchor=a)
    return w + dw


def spaced(d, xy, text, f, fill, tracking=0.25, anchor="m"):
    """Letter-spaced caps (Space Mono labels). anchor 'm' centres on x."""
    gap = f.size * tracking
    widths = [d.textlength(c, font=f) for c in text]
    total = sum(widths) + gap * (len(text) - 1)
    x, y = xy
    if anchor == "m":
        x -= total / 2
    for c, w in zip(text, widths):
        d.text((x, y), c, font=f, fill=fill, anchor="lm")
        x += w + gap
    return total
