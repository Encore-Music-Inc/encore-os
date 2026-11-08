#!/usr/bin/env python3
"""ENCORE. Home: the screen you land on after logging in.

Big tiles for the apps listed in /etc/encore-os/defaults.conf ([home]), a clock and a
greeting, a search box that finds any installed app, and a power menu. Only one Home runs:
starting it again (the panel button, the menu) brings the open one to the front.
"""
import sys
import time

sys.path.insert(0, "/usr/lib/encore-os")
from encore_os import Gdk, Gio, GLib, Gtk, apply_weights, first_name, home_rows, launch, load_css, read_defaults, run, wordmark, setting  # noqa: E402

ICON = 56


class Tile(Gtk.Button):
    def __init__(self, info, label, sub=""):
        super().__init__()
        self.info = info
        self.get_style_context().add_class("tile")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        icon = info.get_icon() or Gio.ThemedIcon.new("application-x-executable")
        img = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.DIALOG)
        img.set_pixel_size(ICON)
        img.set_halign(Gtk.Align.START)
        img.set_margin_bottom(14)
        box.pack_start(img, False, False, 0)
        name = Gtk.Label(label=label, xalign=0)
        name.get_style_context().add_class("tile-label")
        name.set_ellipsize(3)
        box.pack_start(name, False, False, 0)
        desc = Gtk.Label(label=sub or (info.get_description() or info.get_generic_name() or ""), xalign=0)
        desc.get_style_context().add_class("tile-sub")
        desc.set_ellipsize(3)
        box.pack_start(desc, False, False, 0)
        self.add(box)
        self.set_size_request(200, 150)
        self.set_tooltip_text(info.get_display_name())
        self.connect("clicked", lambda *_: self.open())

    def open(self):
        if launch(self.info):
            # step out of the way: the app opens on top, Home stays one click away
            GLib.timeout_add(600, lambda: (self.get_toplevel().iconify(), False)[1])


def tile_grid(items):
    flow = Gtk.FlowBox()
    flow.set_selection_mode(Gtk.SelectionMode.NONE)
    flow.set_homogeneous(True)
    flow.set_min_children_per_line(2)
    flow.set_max_children_per_line(8)
    flow.set_column_spacing(14)
    flow.set_row_spacing(14)
    for info, label in items:
        flow.add(Tile(info, label))
    return flow


class Home(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="ENCORE. Home")
        self.get_style_context().add_class("encore")
        self.set_icon_name("encore-os")
        # a home screen, not a window: no title bar (an empty client-side title bar means the
        # desktop doesn't draw one of its own either)
        self.set_titlebar(Gtk.Box())
        self.set_decorated(False)
        self.defaults = read_defaults()

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        outer.set_margin_start(56)
        outer.set_margin_end(56)
        outer.set_margin_top(34)
        outer.set_margin_bottom(28)
        self.add(outer)

        # top bar: wordmark, search, power
        bar = Gtk.Box(spacing=12)
        bar.pack_start(wordmark(), False, False, 0)
        self.search = Gtk.SearchEntry(placeholder_text="Search apps")
        self.search.set_width_chars(28)
        self.search.connect("search-changed", self.on_search)
        self.search.connect("activate", self.on_search_go)
        bar.set_center_widget(self.search)
        power = Gtk.MenuButton(label="Power")
        power.get_style_context().add_class("ghost")
        pop = Gtk.Popover()
        pop.get_style_context().add_class("encore")
        pbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        pbox.set_margin_start(8); pbox.set_margin_end(8); pbox.set_margin_top(8); pbox.set_margin_bottom(8)
        for text, cmd in [("Lock", ["loginctl", "lock-session"]), ("Log out", ["loginctl", "terminate-user", GLib.get_user_name()]),
                          ("Restart", ["systemctl", "reboot"]), ("Shut down", ["systemctl", "poweroff"])]:
            b = Gtk.Button(label=text)
            b.get_style_context().add_class("ghost")
            b.connect("clicked", lambda _b, c=cmd: (pop.popdown(), GLib.spawn_async(c, flags=GLib.SpawnFlags.SEARCH_PATH)))
            pbox.pack_start(b, False, False, 0)
        pbox.show_all()
        pop.add(pbox)
        power.set_popover(pop)
        bar.pack_end(power, False, False, 0)
        desk = Gtk.Button(label="Desktop")
        desk.get_style_context().add_class("ghost")
        desk.set_tooltip_text("Show the desktop (Home stays in the panel)")
        desk.connect("clicked", lambda *_: self.iconify())
        bar.pack_end(desk, False, False, 0)
        outer.pack_start(bar, False, False, 0)

        # greeting and clock
        head = Gtk.Box(spacing=24)
        head.set_margin_top(44)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.greeting = Gtk.Label(xalign=0)
        self.greeting.get_style_context().add_class("greeting")
        left.pack_start(self.greeting, False, False, 0)
        sub = Gtk.Label(label="What are we making today?", xalign=0)
        sub.get_style_context().add_class("lead")
        left.pack_start(sub, False, False, 0)
        head.pack_start(left, True, True, 0)
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.clock = Gtk.Label(xalign=1)
        self.clock.get_style_context().add_class("clock")
        self.date = Gtk.Label(xalign=1)
        self.date.get_style_context().add_class("date")
        right.pack_start(self.clock, False, False, 0)
        right.pack_start(self.date, False, False, 0)
        head.pack_end(right, False, False, 0)
        outer.pack_start(head, False, False, 0)

        # the rows of tiles (or search results)
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_margin_top(18)
        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.scroll.add(self.body)
        outer.pack_start(self.scroll, True, True, 0)

        foot = Gtk.Label(xalign=0)
        foot.get_style_context().add_class("mono")
        foot.set_text(f"{setting(self.defaults, 'os', 'name', 'ENCORE. OS').upper()} {setting(self.defaults, 'os', 'version', '')}  ·  {GLib.get_host_name()}")
        outer.pack_end(foot, False, False, 0)

        self.show_rows()
        self.tick()
        GLib.timeout_add_seconds(5, self.tick)
        self.connect("key-press-event", self.on_key)
        self.fill_screen()

    def fill_screen(self):
        scr = self.get_screen()
        try:
            mon = Gdk.Display.get_default().get_primary_monitor() or Gdk.Display.get_default().get_monitor(0)
            g = mon.get_workarea()
            self.set_default_size(g.width, g.height)
        except Exception:
            self.set_default_size(scr.get_width(), scr.get_height())
        self.maximize()

    def tick(self):
        h = time.localtime().tm_hour
        part = "morning" if 5 <= h < 12 else "afternoon" if h < 17 else "evening"
        name = first_name()
        self.greeting.set_text(f"Good {part}{', ' + name if name else ''}.")
        self.clock.set_text(time.strftime("%-I:%M"))
        self.date.set_text(time.strftime("%A, %B %-d"))
        return True

    def clear(self):
        for c in self.body.get_children():
            self.body.remove(c)

    def show_rows(self):
        self.clear()
        for title, items in home_rows(self.defaults):
            if title:
                t = Gtk.Label(label=title.upper(), xalign=0)
                t.get_style_context().add_class("row-title")
                self.body.pack_start(t, False, False, 0)
            self.body.pack_start(tile_grid(items), False, False, 0)
        self.body.show_all()
        apply_weights(self)

    def on_search(self, entry):
        q = entry.get_text().strip().lower()
        if not q:
            self.show_rows()
            return
        apps = [a for a in Gio.AppInfo.get_all() if a.should_show()]
        hits = []
        for a in apps:
            hay = " ".join(filter(None, [a.get_display_name(), a.get_description() or "", getattr(a, "get_generic_name", lambda: "")() or "",
                                         " ".join(getattr(a, "get_keywords", lambda: [])() or [])])).lower()
            if q in hay:
                hits.append((0 if a.get_display_name().lower().startswith(q) else 1, a.get_display_name().lower(), a))
        hits.sort(key=lambda h: h[:2])
        self.clear()
        t = Gtk.Label(label=("RESULTS" if hits else "NOTHING FOUND"), xalign=0)
        t.get_style_context().add_class("row-title")
        self.body.pack_start(t, False, False, 0)
        if hits:
            self.body.pack_start(tile_grid([(h[2], h[2].get_display_name()) for h in hits[:24]]), False, False, 0)
        self.body.show_all()
        apply_weights(self.body)

    def on_search_go(self, entry):
        flow = next((c for c in self.body.get_children() if isinstance(c, Gtk.FlowBox)), None)
        if flow and flow.get_children():
            flow.get_children()[0].get_child().open()
            entry.set_text("")

    def on_key(self, _w, ev):
        if ev.keyval == Gdk.KEY_Escape:
            if self.search.get_text():
                self.search.set_text("")
            else:
                self.iconify()
            return True
        # typing anywhere goes into the search box
        if not self.search.has_focus() and ev.string and ev.string.isprintable() and not (ev.state & Gdk.ModifierType.CONTROL_MASK):
            self.search.grab_focus_without_selecting()
            return self.search.event(ev)
        return False


class App(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="studio.encoremusic.os.Home", flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.win = None

    def do_activate(self):
        if not self.win:
            load_css()
            self.win = Home(self)
            self.win.show_all()
        self.win.deiconify()
        self.win.present()


if __name__ == "__main__":
    sys.exit(App().run(sys.argv))
