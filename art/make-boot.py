"""The ENCORE. OS boot animation, as a Plymouth theme.

    python3 make-boot.py <out dir>      (writes encore.plymouth, encore.script and the frames)

The E builds itself, the orange dot drops in, "ENCORE. OS" fades up underneath, then the
dot breathes until the desktop is ready. Frames are drawn for a 1080p screen and the script
scales them for other sizes. Shutdown and restart show the finished mark with a message.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw
import brand as B

FPS = 25
W, H = 640, 400
MARK_H = 180
CY = 165


def frame(t, build=True):
    img = Image.new("RGB", (W, H), B.BG)
    B.mark(img, t, W / 2, CY, MARK_H, build=build)
    k = B.ease_out(B.span(t if build else 99, 1.1, 1.6))
    if k > 0:
        d = ImageDraw.Draw(img)
        f = B.font(22, mono=True)
        B.spaced(d, (W / 2, CY + MARK_H / 2 + 58 + (1 - k) * 10), "ENCORE. OS", f, B.mix(B.BG, B.SOFT, k), tracking=0.42)
    return img


SCRIPT = r"""// ENCORE. OS boot animation (made by os/art/make-boot.py)
Window.SetBackgroundTopColor(%(bg)s);
Window.SetBackgroundBottomColor(%(bg)s);

scale = Window.GetHeight() / 1080;
if (scale < 0.5) scale = 0.5;
if (scale > 2) scale = 2;

intro_count = %(intro)d;
loop_count = %(loop)d;
for (i = 0; i < intro_count; i++) intro[i] = Image("intro-" + i + ".png").Scale(%(w)d * scale, %(h)d * scale);
for (i = 0; i < loop_count; i++) loop[i] = Image("loop-" + i + ".png").Scale(%(w)d * scale, %(h)d * scale);
still = Image("still.png").Scale(%(w)d * scale, %(h)d * scale);

logo = Sprite();
logo.SetX(Window.GetX() + Window.GetWidth() / 2 - %(w)d * scale / 2);
logo.SetY(Window.GetY() + Window.GetHeight() / 2 - %(h)d * scale / 2);

stopping = (Plymouth.GetMode() == "shutdown" || Plymouth.GetMode() == "reboot");
tick = 0;

fun refresh() {
  if (stopping) { logo.SetImage(still); return; }
  // Plymouth refreshes 50 times a second; the frames are 25 a second
  n = Math.Int(tick / 2);
  if (n < intro_count) logo.SetImage(intro[n]);
  else logo.SetImage(loop[(n - intro_count) %% loop_count]);
  tick++;
}
Plymouth.SetRefreshFunction(refresh);

// messages (shutdown, disk checks) in small text under the mark
msg = Sprite();
fun show_message(text) {
  msg.SetImage(Image.Text(text, %(soft)s, "DM Sans 14"));
  msg.SetX(Window.GetX() + Window.GetWidth() / 2 - msg.GetImage().GetWidth() / 2);
  msg.SetY(Window.GetY() + Window.GetHeight() * 0.82);
}
Plymouth.SetMessageFunction(show_message);
if (Plymouth.GetMode() == "shutdown") show_message("Shutting down");
if (Plymouth.GetMode() == "reboot") show_message("Restarting");

// a password prompt, in case it's ever needed (an encrypted disk)
fun display_password(prompt, bullets) {
  t = prompt; for (i = 0; i < bullets; i++) t = t + " *";
  show_message(t);
}
Plymouth.SetDisplayPasswordFunction(display_password);
fun display_normal() { msg.SetOpacity(1); }
Plymouth.SetDisplayNormalFunction(display_normal);
"""

THEME = """[Plymouth Theme]
Name=ENCORE.
Description=ENCORE. OS boot animation
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/encore
ScriptFile=/usr/share/plymouth/themes/encore/encore.script
"""


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    intro = round(B.INTRO * FPS) + 8          # a little past the build, so the subtitle lands
    loop = round(B.PULSE * FPS)
    for i in range(intro):
        frame(i / FPS).save(out / f"intro-{i}.png", optimize=True)
    t0 = intro / FPS
    for i in range(loop):
        frame(t0 + i / FPS).save(out / f"loop-{i}.png", optimize=True)
    frame(99, build=False).save(out / "still.png", optimize=True)
    rgb = lambda c: ", ".join(f"{v / 255:.3f}" for v in c)
    (out / "encore.script").write_text(SCRIPT % dict(bg=rgb(B.BG), soft=rgb(B.SOFT), intro=intro, loop=loop, w=W, h=H))
    (out / "encore.plymouth").write_text(THEME)
    size = sum(p.stat().st_size for p in out.iterdir())
    print(f"boot animation: {intro} intro + {loop} loop frames, {size // 1024} KB in {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build/plymouth")
