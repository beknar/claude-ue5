"""docs/vehicles.md and its pictures, from claude_ue5/SourceArt/vehicle_gallery/vehicles.json (the vehicles, mounts and
beast-drawn carts, their category, use and looks), the renders of pipeline/unreal/903_vehicle_gallery.py (shoot) and the
animation survey (902: each model's size and skeleton): for each entry three pictures, docs/images/vehicles/<id>_quarter.jpg,
_side.jpg and _third.jpg (a frame of its clip, or the model from above), 480 x 300.
Usage (a Python with Pillow):  vehicle_doc.py <shots_dir>"""
import sys, os, io, re, json, collections
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_text
SHOTS = sys.argv[1]
ROOT = anim_text.ROOT
DATA = os.path.join(ROOT, "claude_ue5", "SourceArt", "vehicle_gallery", "vehicles.json")
IMG = os.path.join(ROOT, "docs", "images", "vehicles"); DOC = os.path.join(ROOT, "docs", "vehicles.md")
W, H = 480, 300
# the kinds of a vehicle's or a beast's clips, in this order (the first that matches)
KINDS = [("rider", r"climb|get_off|getoff"), ("take-off and landing", r"takeoff|take_off|landing|launch"),
         ("attacks and shots", r"attack|shot|fire|grenade|bomb|shout"), ("aiming", r"muzzle|tower_\d|aim"),
         ("deaths", r"dead|death"), ("hit reactions", r"hit"), ("idles", r"idle"),
         ("moves and turns", r"walk|run|fly|flight|soar|move|rotat|turn|jump|loop|strafe"), ("doors", r"door|disembark")]


def vkind(clip):
    n = clip.lower()
    if n.startswith("sk_"): return "all"
    for k, rx in KINDS:
        if re.search(rx, n): return k
    return "other"


ONE = {"rider": "rider clip", "take-off and landing": "take-off or landing", "attacks and shots": "attack or shot", "deaths": "death", "hit reactions": "hit reaction",
       "idles": "idle", "moves and turns": "move or turn", "doors": "door clip", "other": "other"}


def vcounts(clips):
    c = collections.Counter(vkind(x) for x in clips)
    out = ["%d %s" % (c[k], (k if k != "rider" else "rider clips") if c[k] > 1 else ONE[k]) for k, _ in KINDS + [("other", None)] if c[k]]
    if c["all"]: out.append("all of them on one timeline")
    return ", ".join(out)


def anim_line(v, A, info):
    """the **Animations:** paragraph of one entry"""
    skels = info.get("skeletons", [])
    if not skels:
        s = "none: a static mesh, which moves only as a whole (by code, physics or a sequence); wheels, sails and oars are part of the one mesh."
        if len(v["meshes"]) > 1: s = "none of its own: %d static meshes (body, wheels and the rest) that code or a sequence can move separately." % len(v["meshes"])
    else:
        clips = sorted({x for m in v["meshes"] if m in A.chars for x in A.chars[m]["own"]})
        if v.get("clip_filter"): clips = [x for x in clips if re.search(v["clip_filter"], x)]
        bones = max(A.chars[m]["bones"] for m in v["meshes"] if m in A.chars)
        s = ("a skeletal mesh (%d bones) with %d clip%s of its own: %s." % (bones, len(clips), "" if len(clips) == 1 else "s", vcounts(clips))) if clips else \
            "a skeletal mesh (%d bones) without clips: its bones can be posed by code, a control rig or a sequence." % bones
    if v.get("anim_note"): s += " " + v["anim_note"]
    return s


os.makedirs(IMG, exist_ok=True)
for f in os.listdir(IMG):
    if f.endswith(".jpg"): os.remove(os.path.join(IMG, f))
D = json.load(io.open(DATA, encoding="utf-8")); vs = D["vehicles"]; cats = D.get("categories", {})
A = anim_text.Anims(); INFO = json.load(io.open(anim_text.DATA, encoding="utf-8")).get("vehicles", {})
for v in vs:
    for k in ("quarter", "side", "third"):
        Image.open(os.path.join(SHOTS, "%s_%s.png" % (v["id"], k))).convert("RGB").resize((W, H), Image.LANCZOS).save(os.path.join(IMG, "%s_%s.jpg" % (v["id"], k)), quality=84, optimize=True)
order = list(dict.fromkeys(v["category"] for v in vs))
n_anim = sum(1 for v in vs if v.get("clip"))
out = ["""# Vehicles, mounts and beast-drawn carts of the Fab library

Every vehicle in the local Fab library cache (`I:\\game assets\\3d epicgames media packs\\VaultCache\\FabLibrary` and the environment packs downloaded through it): animals built to be ridden, carts and wagons for a draught animal or a pair of hands, siege engines, boats and ships, cars, buses and mine carts, military vehicles and drones, and sci-fi craft. All %d are in this project. Each is shown three times, rendered in Unreal Engine:

- **three-quarter view;**
- **side view;**
- **in motion** (the %d that come with clips: a frame of one of them) or **from above** (the others, from the opposite corner).

## About the pictures

- **Sizes:** each entry gives the model's length, width and height in metres, from its bounds (a skeletal mesh in its reference pose: the dragon with its wings spread).
- **Scale:** every model is framed to fill its pictures, so a 60 cm drone and a 115 m cargo ship look the same size: read the sizes.
- **Several meshes:** the armoured car (body, wheels, hubs, gun) and the ballista (frame and wheels) are made of separate meshes, shown together.
- **No draught animals:** the carts and wagons come without a horse or an ox, and there is no horse in the library (only a horse statue, saddles and horseshoes); the beasts of burden are the pack bull, the camel and the elephants.
- **Uses:** a use is a suggestion from the model's looks.

The list is `claude_ue5/SourceArt/vehicle_gallery/vehicles.json`; the pictures come from `pipeline/unreal/903_vehicle_gallery.py` and `pipeline/blender_numpy/vehicle_doc.py`, the sizes and the animation notes from `pipeline/unreal/902_character_animations.py`. The sellers and listings of the packs are in [assets.md](assets.md); the riders' clips and the other animation libraries are on [heroes.md](heroes.md#animations).

## Categories

""" % (len(vs), n_anim)]
for c in order:
    n = sum(1 for v in vs if v["category"] == c)
    out.append("- [%s](#%s) (%d)%s\n" % (c, re.sub(r"[^a-z0-9 -]", "", c.lower()).replace(" ", "-"), n, (": " + cats[c]) if c in cats else ""))
out.append("- [Not included](#not-included)\n")
for c in order:
    out.append("\n## %s\n" % c)
    if c in cats: out.append("\n%s\n" % cats[c])
    for v in [x for x in vs if x["category"] == c]:
        info = INFO.get(v["id"], {})
        link = "[%s](https://www.fab.com/listings/%s)" % (v["pack"], v["uid"]) if v.get("uid") else v["pack"]
        model = "`%s`" % v["meshes"][0].rsplit("/", 1)[1].split(".")[0] + (" and %d more meshes" % (len(v["meshes"]) - 1) if len(v["meshes"]) > 1 else "")
        size = " · %.1f × %.1f × %.1f m" % tuple(info["size_m"]) if info.get("size_m") else ""
        out.append("\n### %s\n\n" % v["name"])
        out.append("%s · **Use:** %s · model %s%s\n\n" % (link, v.get("use") or "-", model, size))
        if v.get("looks"): out.append("%s\n\n" % v["looks"])
        out.append("**Animations:** %s\n\n" % anim_line(v, A, info))
        third = "in motion" if v.get("clip") else "from above"
        out.append("".join('<img src="images/vehicles/%s_%s.jpg" width="280" alt="%s, %s"> ' % (v["id"], k, v["name"], lbl)
                           for k, lbl in (("quarter", "three-quarter view"), ("side", "side view"), ("third", third))).rstrip() + "\n")
out.append("""
## Not included

- **Wrecks in pieces and ship modules:** the sunken ship of `Underwater_shipwreck` (bow, midship and stern modules) and the cargo ship's separate hull modules; the wrecked ship and boat above are whole meshes.
- **Parts and props:** loose wheels, wagon wheels, saddles, horseshoes, boat stands and lifts, hand trucks, a push cart, a wheelchair, the gas and supply carts of the hospital pack, a fryer cart, and `SilentZonePack`'s `SM_eleccar`, an untextured grey shell.
- **Duplicates:** the same boats in several `Docks` volumes, the Mega City shuttle's flying version, the hover tank's two other paint schemes (`SK_Tank_Full_02`, `_03`) and the war elephant of `Animals_Warrior_Pack`, which is an elephant-headed warrior (on [heroes.md](heroes.md)).
- **Beasts without a saddle:** the hounds, spiders and other creatures of [monsters.md](monsters.md), and the beast-headed warriors of [humanoid_enemies.md](humanoid_enemies.md).
- **The project's own:** the starship_level fighter, kitbashed from pack meshes by `801`, and the castle furniture kit's cart, modelled for this project.
""")
io.open(DOC, "w", encoding="utf-8", newline="\n").write("".join(out))
size = sum(os.path.getsize(os.path.join(IMG, f)) for f in os.listdir(IMG))
print("vehicle_doc: %d entries, %d pictures, %.1f MB, %s" % (len(vs), len(os.listdir(IMG)), size / 1e6, DOC))
