"""Asks Pango (no GTK styles involved) which DM Sans face it loads for each weight."""
import gi
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Pango, PangoCairo

fm = PangoCairo.FontMap.get_default()
ctx = fm.create_context()
for desc in ["DM Sans 34", "DM Sans Medium 34", "DM Sans Bold 34", "DM Sans Ultra-Bold 34", "DM Sans Heavy 34"]:
    fd = Pango.FontDescription.from_string(desc)
    font = fm.load_font(ctx, fd)
    print(f"{desc:24} -> {font.describe().to_string() if font else None}")
fam = [f for f in fm.list_families() if "DM Sans" in f.get_name()]
for f in fam:
    print("family", f.get_name(), [(x.get_face_name(), int(x.describe().get_weight())) for x in f.list_faces()])
