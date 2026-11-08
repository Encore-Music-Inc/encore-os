"""Shared by ENCORE. Home and ENCORE. Welcome: the defaults file, the look, launching apps."""
import os
import subprocess
from pathlib import Path

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Pango", "1.0")
from gi.repository import Gdk, Gio, GLib, Gtk, Pango  # noqa: E402

SHARE = Path(os.environ.get("ENCORE_OS_SHARE", "/usr/share/encore-os"))
DEFAULTS = Path(os.environ.get("ENCORE_OS_DEFAULTS", "/etc/encore-os/defaults.conf"))
STATE = Path(GLib.get_user_config_dir()) / "encore-os"


def read_defaults(path=DEFAULTS):
    """{section: {"keys": {k: v}, "lines": [str]}} from the INI-like defaults file."""
    out, sec = {}, None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return out
    for raw in text.splitlines():
        line = raw.strip()
        if not line or (line.startswith("#") and not line.startswith("##")):
            continue
        if line.startswith("[") and line.endswith("]"):
            sec = out.setdefault(line[1:-1].strip(), {"keys": {}, "lines": []})
            continue
        if sec is None:
            continue
        sec["lines"].append(line)
        if "=" in line and not line.startswith("##"):
            k, v = line.split("=", 1)
            sec["keys"][k.strip()] = v.strip()
    return out


def setting(d, section, key, default=""):
    return d.get(section, {}).get("keys", {}).get(key, default) or default


def home_rows(d):
    """[(title, [(DesktopAppInfo, label)])] for the Home screen; uninstalled apps are skipped."""
    rows, cur = [], None
    for line in d.get("home", {}).get("lines", []):
        if line.startswith("##"):
            cur = (line.lstrip("#").strip(), [])
            rows.append(cur)
            continue
        if cur is None:
            cur = ("", [])
            rows.append(cur)
        ids, _, label = line.partition("|")
        for app_id in [x.strip() for x in ids.split(",") if x.strip()]:
            try:
                info = Gio.DesktopAppInfo.new(app_id)
            except TypeError:
                info = None
            if info:
                cur[1].append((info, label.strip() or info.get_display_name()))
                break
    return [r for r in rows if r[1]]


def load_css():
    css = Gtk.CssProvider()
    css.load_from_path(str(SHARE / "encore.css"))
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    Gtk.Settings.get_default().set_property("gtk-application-prefer-dark-theme", True)


def launch(info):
    """Start an app from its DesktopAppInfo, detached, the way the menu would."""
    try:
        ctx = Gdk.Display.get_default().get_app_launch_context()
        info.launch([], ctx)
        return True
    except GLib.Error:
        return False


def run(*cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def wordmark(size_class="wordmark"):
    """ENCORE. with the orange full stop, as a label."""
    lab = Gtk.Label()
    lab.set_markup('ENCORE<span foreground="#ff3b00">.</span>')
    lab.get_style_context().add_class(size_class)
    return lab


def first_name():
    import pwd
    try:
        full = pwd.getpwuid(os.getuid()).pw_gecos.split(",")[0].strip()
    except KeyError:
        full = ""
    name = full or GLib.get_user_name()
    return name.split()[0][:1].upper() + name.split()[0][1:] if name else ""


# Text weights, set on the text itself. (Raspberry Pi OS's GTK applies the stylesheet's sizes
# and colours but not its font-weight, so headings came out regular there.)
WEIGHTS = {"greeting": 800, "headline": 800, "wordmark": 800, "wordmark-big": 800, "clock": 800,
           "tile-label": 700, "lead": 400, "mono": 700}


def apply_weights(widget):
    if isinstance(widget, Gtk.Label):
        ctx = widget.get_style_context()
        w = next((v for k, v in WEIGHTS.items() if ctx.has_class(k)), None)
        if w is None and isinstance(widget.get_parent(), Gtk.Button):
            w = 700
        if w is not None:
            attrs = widget.get_attributes() or Pango.AttrList()
            attrs.insert(Pango.attr_weight_new(Pango.Weight(w)))
            widget.set_attributes(attrs)
    if isinstance(widget, Gtk.Container):
        widget.forall(apply_weights)
