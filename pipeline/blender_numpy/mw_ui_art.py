"""mistward_castle's reel: the painted interface's pieces with the castle's pictures added, for rdm_reel_overlay.py and
rdm4_reel_assemble.py (which draw the HUD from a folder of pieces and its layout.json).

    python mw_ui_art.py <ui_art export dir> <icons dir> <out dir>

<ui_art export dir>: rdm4_ui_cut.py --export's folder (claude_ue5/SourceArt/random_dungeon_magic4/ui_art); <icons dir>: the
pictures 867 shot and mw_icons.py cut (mw_<objects id>.png for the 22 shields, mw_torch.png, mw_w_<weapon>.png for the 29
weapons of the table). The out dir gets every piece and picture, and a layout.json with the pictures as pieces of their own
and the items' and weapons' icons (the shields by their docs/objects.md id, as 865 names them; the found weapons for every
hero, as the overlay looks them up: "<hero>/<weapon>")."""
import sys, os, json, shutil, glob
from PIL import Image
SRC, ICONS, OUT = (os.path.abspath(a) for a in sys.argv[1:4])
HERE = os.path.dirname(os.path.abspath(__file__))
SA = os.path.join(HERE, "..", "..", "claude_ue5", "SourceArt")
os.makedirs(OUT, exist_ok=True)
L = json.load(open(os.path.join(SRC, "layout.json")))
for f in glob.glob(os.path.join(SRC, "*.png")): shutil.copy2(f, OUT)
def snake(n): return "".join(ch if ch.isalnum() else "_" for ch in n.lower()).strip("_").replace("__", "_")
objs = {o["name"]: o for o in json.load(open(os.path.join(SA, "object_gallery", "objects.json"), encoding="utf-8"))["objects"]}
shields = {s["name"]: s.get("gallery", s["name"]) for s in json.load(open(os.path.join(SA, "mistward", "shields.json"), encoding="utf-8"))["shields"]}
weapons = [w["name"] for w in json.load(open(os.path.join(SA, "random_dungeon_magic5", "weapons_table.json"), encoding="utf-8"))["weapons"]]
icons, wmap = dict(L.get("_icons", {})), dict(L.get("_weapons", {}))
added = 0
def piece(name):
    global added
    p = os.path.join(ICONS, name + ".png")
    if not os.path.exists(p): print("no picture", name); return None
    shutil.copy2(p, OUT); w, h = Image.open(p).size
    L[name] = {"kind": "icon", "size": [w, h], "border": [0, 0, 0, 0], "inner": [0.0, 0.0, 1.0, 1.0]}; added += 1
    return name
for s, g in shields.items():           # (the table's name -> the gallery's, where its picture is)
    n = piece("mw_" + objs[g]["id"]) if g in objs else None
    if n: icons[s] = n
if piece("mw_torch"): icons["Torch"] = "mw_torch"
for w in weapons:
    n = piece("mw_w_" + snake(w))
    if n:
        icons[w] = n
        for hero in ("Warrior", "Mage", "Warlock", "Rogue", "Summoner"): wmap.setdefault("%s/%s" % (hero, w), n)
L["_icons"], L["_weapons"] = icons, wmap
json.dump(L, open(os.path.join(OUT, "layout.json"), "w"), indent=1)
print("MWUIART %d pictures added to %d pieces in %s" % (added, sum(1 for k in L if not k.startswith("_")), OUT))
