#!/usr/bin/env python3
"""ENCORE. Welcome: runs the first time someone logs in to ENCORE. OS.

1. the welcome video (Skip is always there)
2. plug in your gear: pick what plays and what records, play a test sound
3. your studio: what's where
4. ENCORE. (only if [welcome] music_url is set in the defaults; the button opens it in its own window)
5. all set: opens ENCORE. Home

When it's done (or closed) it leaves ~/.config/encore-os/welcome-done so it doesn't come
back; `encore-welcome --again` shows it anyway.
"""
import re
import sys

sys.path.insert(0, "/usr/lib/encore-os")
from encore_os import SHARE, STATE, Gdk, GLib, Gtk, apply_weights, read_defaults, run, setting, wordmark  # noqa: E402

try:
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst
    Gst.init(None)
except (ImportError, ValueError):
    Gst = None


def label(text, cls=None, xalign=0.5, wrap=True, markup=False):
    lab = Gtk.Label(xalign=xalign)
    lab.set_markup(text) if markup else lab.set_text(text)
    lab.set_line_wrap(wrap)
    if wrap:
        lab.set_max_width_chars(68)
    lab.set_justify(Gtk.Justification.CENTER if xalign == 0.5 else Gtk.Justification.LEFT)
    if cls:
        for c in cls.split():
            lab.get_style_context().add_class(c)
    return lab


def button(text, cls="", cb=None):
    b = Gtk.Button(label=text)
    for c in cls.split():
        b.get_style_context().add_class(c)
    if cb:
        b.connect("clicked", lambda *_: cb())
    return b


def page(*widgets, width=760):
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    box.set_halign(Gtk.Align.CENTER)
    box.set_valign(Gtk.Align.CENTER)
    box.set_size_request(width, -1)
    for w in widgets:
        box.pack_start(w, False, False, 0)
    return box


# ---------- audio devices (PipeWire, through its PulseAudio side) ----------

def devices(kind):
    """[(name, description)] of 'sinks' (outputs) or 'sources' (inputs), monitors left out."""
    out, cur = [], {}
    for line in run("pactl", "list", kind).splitlines():
        line = line.strip()
        if line.startswith(("Sink #", "Source #")):
            if cur.get("name"):
                out.append(cur)
            cur = {}
        elif line.startswith("Name:"):
            cur["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("Description:"):
            cur["desc"] = line.split(":", 1)[1].strip()
    if cur.get("name"):
        out.append(cur)
    return [(d["name"], d.get("desc", d["name"])) for d in out if not d["name"].endswith(".monitor")]


def default(kind):
    return run("pactl", "get-default-sink" if kind == "sinks" else "get-default-source").strip()


class Welcome(Gtk.Window):
    def __init__(self):
        super().__init__(title="Welcome to ENCORE. OS")
        self.get_style_context().add_class("encore")
        self.set_icon_name("encore-os")
        self.defaults = read_defaults()
        self.music_url = setting(self.defaults, "welcome", "music_url")
        self.connect("delete-event", lambda *_: self.finish(open_home=True))

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(350)
        root.pack_start(self.stack, True, True, 0)

        # footer: dots in the middle, Back / Next on the sides
        foot = Gtk.Box(spacing=10)
        foot.set_margin_start(40); foot.set_margin_end(40); foot.set_margin_bottom(30)
        self.back = button("Back", "ghost", self.go_back)
        self.next = button("Next", "primary big", self.go_next)
        self.dots = Gtk.Box(spacing=8)
        self.dots.get_style_context().add_class("dots")
        foot.pack_start(self.back, False, False, 0)
        foot.set_center_widget(self.dots)
        foot.pack_end(self.next, False, False, 0)
        root.pack_end(foot, False, False, 0)
        self.foot = foot

        self.pages = ["video", "gear", "studio"] + (["music"] if self.music_url else []) + ["done"]
        self.stack.add_named(self.video_page(), "video")
        self.stack.add_named(self.gear_page(), "gear")
        self.stack.add_named(self.studio_page(), "studio")
        if self.music_url:
            self.stack.add_named(self.music_page(), "music")
        self.stack.add_named(self.done_page(), "done")
        for _ in self.pages:
            self.dots.pack_start(Gtk.Label(label="●"), False, False, 0)
        self.at = 0
        disp = Gdk.Display.get_default()
        mon = disp.get_primary_monitor() or disp.get_monitor(0)
        if mon:
            g = mon.get_geometry()
            self.set_default_size(g.width, g.height)
        self.fullscreen()
        self.show_all()
        apply_weights(self)
        self.show_page(0)

    # ----- pages -----
    def video_page(self):
        overlay = Gtk.Overlay()
        self.player = None
        path = setting(self.defaults, "welcome", "video", str(SHARE / "welcome.mp4"))
        sink = Gst.ElementFactory.make("gtksink", None) if Gst else None
        if sink and GLib.file_test(path, GLib.FileTest.EXISTS):
            self.player = Gst.ElementFactory.make("playbin", None)
            self.player.set_property("uri", Gst.filename_to_uri(path))
            self.player.set_property("video-sink", sink)
            bus = self.player.get_bus()
            bus.add_signal_watch()
            bus.connect("message::eos", lambda *_: self.go_next())
            bus.connect("message::error", lambda *_: self.go_next())
            area = sink.get_property("widget")
            overlay.add(area)
        else:
            overlay.add(page(wordmark("wordmark-big"), label("Welcome to your studio.", "headline")))
        skip = button("Skip", "ghost", self.go_next)
        skip.set_halign(Gtk.Align.END); skip.set_valign(Gtk.Align.START)
        skip.set_margin_top(24); skip.set_margin_end(30)
        overlay.add_overlay(skip)
        return overlay

    def gear_page(self):
        self.out_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.in_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        cols = Gtk.Box(spacing=18, homogeneous=True)
        for title, box in [("SOUND COMES OUT OF", self.out_box), ("RECORD FROM", self.in_box)]:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            card.get_style_context().add_class("card")
            card.pack_start(label(title, "mono", xalign=0), False, False, 0)
            card.pack_start(box, False, False, 0)
            cols.pack_start(card, True, True, 0)
        test = button("Play a test sound", "", lambda: GLib.spawn_async(["pw-play", str(SHARE / "test-sound.wav")], flags=GLib.SpawnFlags.SEARCH_PATH))
        test.set_halign(Gtk.Align.CENTER)
        self.fill_devices()
        GLib.timeout_add_seconds(2, self.fill_devices)   # interfaces plugged in now show up
        return page(label("Plug in your gear.", "headline"),
                    label("Connect your audio interface, USB mic or headphones. It shows up here by itself. "
                          "Pick what plays and what records; you can change it any time from the speaker in the panel.", "lead"),
                    cols, test, width=880)

    def fill_devices(self):
        for kind, box in [("sinks", self.out_box), ("sources", self.in_box)]:
            devs = devices(kind)
            key = tuple(devs)
            if getattr(box, "_key", None) == key:
                continue
            box._key = key
            for c in box.get_children():
                box.remove(c)
            cur, group = default(kind), None
            if not devs:
                box.pack_start(label("Nothing yet. Plug something in.", "dim", xalign=0), False, False, 0)
            for name, desc in devs:
                rb = Gtk.RadioButton.new_with_label_from_widget(group, re.sub(r"\s+", " ", desc))
                group = group or rb
                rb.set_active(name == cur)
                rb.connect("toggled", lambda b, n=name, k=kind: b.get_active() and run("pactl", "set-default-sink" if k == "sinks" else "set-default-source", n))
                box.pack_start(rb, False, False, 0)
            box.show_all()
            apply_weights(box)
        return True

    def studio_page(self):
        grid = Gtk.Grid(column_spacing=18, row_spacing=18, column_homogeneous=True)
        items = [("Home", "Everything starts here. It opens when you log in; the ENCORE. button in the panel brings it back."),
                 ("Basement Studio", "Record, mix and master. Your ENCORE. plugins are already in it."),
                 ("ENCORE.", "Your ENCORE. account, your music and your fans, in its own window. Needs the internet."),
                 ("Your files", "Songs, recordings and exports live in your home folder, under Music.")]
        for i, (t, d) in enumerate(items):
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            card.get_style_context().add_class("card")
            card.pack_start(label(t, "greeting", xalign=0), False, False, 0)
            card.pack_start(label(d, "soft", xalign=0), False, False, 0)
            grid.attach(card, i % 2, i // 2, 1, 1)
        return page(label("Your studio.", "headline"), label("Here’s where everything lives.", "lead"), grid, width=900)

    def music_page(self):
        join = button("Open ENCORE.", "primary big", lambda: GLib.spawn_async(["encore-music"], flags=GLib.SpawnFlags.SEARCH_PATH))
        join.set_halign(Gtk.Align.CENTER)
        return page(label('Put your music out<span foreground="#ff3b00">.</span>', "headline", markup=True),
                    label("ENCORE. is where your songs go when they’re done: put them out, sell them and share them with your fans.", "lead"),
                    join, label("You can do this later too.", "dim"))

    def done_page(self):
        go = button("Open ENCORE. Home", "primary big", lambda: self.finish(open_home=True))
        go.set_halign(Gtk.Align.CENTER)
        return page(wordmark("wordmark-big"), label("You’re all set.", "headline"),
                    label("Plug in, press record. Have fun.", "lead"), go)

    # ----- moving around -----
    def show_page(self, i):
        self.at = max(0, min(len(self.pages) - 1, i))
        name = self.pages[self.at]
        self.stack.set_visible_child_name(name)
        for k, d in enumerate(self.dots.get_children()):
            (d.get_style_context().add_class if k == self.at else d.get_style_context().remove_class)("on")
        self.back.set_visible(0 < self.at)
        self.next.set_visible(name not in ("video", "done"))
        self.foot.set_visible(name != "video")
        if self.player:
            self.player.set_state(Gst.State.PLAYING if name == "video" else Gst.State.NULL)

    def go_next(self):
        self.show_page(self.at + 1)

    def go_back(self):
        self.show_page(self.at - 1)

    def finish(self, open_home=False):
        if self.player:
            self.player.set_state(Gst.State.NULL)
        STATE.mkdir(parents=True, exist_ok=True)
        (STATE / "welcome-done").write_text("1\n")
        if open_home:
            GLib.spawn_async(["encore-home"], flags=GLib.SpawnFlags.SEARCH_PATH)
        Gtk.main_quit()
        return False


def main():
    if (STATE / "welcome-done").exists() and "--again" not in sys.argv:
        GLib.spawn_async(["encore-home"], flags=GLib.SpawnFlags.SEARCH_PATH)
        return
    from encore_os import load_css
    load_css()
    w = Welcome()
    if "--page" in sys.argv:
        w.show_page(int(sys.argv[sys.argv.index("--page") + 1]))
    Gtk.main()


if __name__ == "__main__":
    main()
