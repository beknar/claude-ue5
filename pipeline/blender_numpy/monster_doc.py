"""docs/monsters.md and its pictures, from claude_ue5/SourceArt/monster_gallery/monsters.json (the ranking) and the
renders of pipeline/unreal/900_monster_gallery.py (shoot): for each monster one strip, docs/images/monsters/<rank>_<name>.jpg,
with its own colours and the three recoloured versions side by side, all four cropped to the same box around the
monster (its mask render) and labelled.
Usage (a Python with Pillow):  monster_doc.py <shots_dir>"""
import sys, os, re, io, json
from PIL import Image, ImageDraw, ImageFont
SHOTS = sys.argv[1]
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DATA = os.path.join(ROOT, "claude_ue5", "SourceArt", "monster_gallery", "monsters.json")
IMG = os.path.join(ROOT, "docs", "images", "monsters")
DOC = os.path.join(ROOT, "docs", "monsters.md")
LOOKS = (("original", "original"), ("infernal", "infernal"), ("venom", "venom"), ("frost", "frost"))
TW, TH, GAP, CAP = 150, 188, 4, 18
os.makedirs(IMG, exist_ok=True)
font = ImageFont.truetype("arial.ttf", 13)


def slug(s): return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def strip(rank, name):
    mask = Image.open(os.path.join(SHOTS, "%03d_mask.png" % rank)).convert("L").point(lambda v: 255 if v > 6 else 0)
    W, H = mask.size
    bb = mask.getbbox() or (0, 0, W, H)
    # the box: the monster with a margin, widened or heightened to the tiles' shape, kept inside the picture
    cx, cy = (bb[0] + bb[2]) / 2.0, (bb[1] + bb[3]) / 2.0; w, h = (bb[2] - bb[0]) * 1.16 + 8, (bb[3] - bb[1]) * 1.1 + 8
    if w / h > TW / TH: h = w * TH / TW
    else: w = h * TW / TH
    w, h = min(w, W), min(h, H)
    x0 = min(max(cx - w / 2, 0), W - w); y0 = min(max(cy - h / 2, 0), H - h)
    box = tuple(int(round(v)) for v in (x0, y0, x0 + w, y0 + h))
    out = Image.new("RGB", (TW * 4 + GAP * 3, TH + CAP), (18, 18, 18)); dr = ImageDraw.Draw(out)
    for k, (look, label) in enumerate(LOOKS):
        im = Image.open(os.path.join(SHOTS, "%03d_%s.png" % (rank, look))).convert("RGB").crop(box).resize((TW, TH), Image.LANCZOS)
        x = k * (TW + GAP); out.paste(im, (x, 0))
        tw = dr.textlength(label, font=font); dr.text((x + (TW - tw) / 2, TH + 2), label, fill=(225, 225, 225), font=font)
    fn = "%03d_%s.jpg" % (rank, slug(name))
    out.save(os.path.join(IMG, fn), quality=84, optimize=True)
    return fn


D = json.load(io.open(DATA, encoding="utf-8"))["monsters"]
for f in os.listdir(IMG):                                  # (a renamed monster must not leave its old strip behind)
    if f.endswith(".jpg"): os.remove(os.path.join(IMG, f))
rows = {}
for e in D:
    fn = strip(e["rank"], e["name"])
    rows.setdefault(e["tier"], []).append("| %d | %s | %s | %s | %s | %s | ![%s](images/monsters/%s) |" % (
        e["rank"], e["name"], e["pack"], e["model"], e["height"], e["looks"], e["name"], fn))

HEAD = """# Monsters of the Fab library, ranked by looks

Every monster in the local Fab library cache (`I:\\game assets\\3d epicgames media packs\\VaultCache\\FabLibrary`), ranked from the one that looks easiest to defeat (1) to the one that looks toughest to beat (107). **Looks only**: nothing here comes from hit points, animations or any game data, just what the model looks like standing in front of you.

What counts as tougher-looking: size and bulk; armour, shells and plates; blades, claws, scythes, spikes and horns; extra limbs; teeth. What counts as easier: small, thin, legless or crippled, trapped, unarmed, or drawn as a cartoon.

## How the list was made

- **Which packs:** every pack in the cache whose models are creatures rather than people, props or rooms: the packs tagged *Monster* or *Creature* in their listing data, plus the orcs, zombies, aliens and beast warriors.
- **Rendering:** every model was rendered in this project in its reference pose (arms out), with its own textures. A 180 cm post stands beside it for scale (it is cut off in the pictures of small creatures).
- **Unity-only packs:** the Creatures Insects Pack and the Humanoids Monsters Pack exist only in Unity format, so they were unpacked (`pipeline/blender_numpy/unity_extract.py`) and imported for this (`pipeline/unreal/900_monster_gallery.py unity`).
- **Heights:** the height column is the model's bounding box in that pose, in cm. Most humanoids come out at about 180–200 cm whatever their build, so bulk matters more than the number. For models holding something up (a staff, horns, wings), the item is included.

## The pictures

Each monster is shown four times, left to right:

- **original:** its own textures and colours.
- **infernal:** charred red-black skin with ember highlights; a cracked-stone pattern, some of whose cracks glow.
- **venom:** sickly green to yellow, with scales.
- **frost:** pale ice-blue and glossier, with crystal facets and a cold glint along their edges.

The three alternates come from one material (`M_MON_Variant`). It keeps the model's own normal map, and maps the brightness of its own colour texture onto the scheme's dark, middle and light colours, so the original's painted detail survives. It then adds a pattern computed from the position on the body, so it covers every model the same way and stays put however the monster moves.

Pictures and this page are made by `pipeline/unreal/900_monster_gallery.py` (`stage`, `warm`, `shoot`) and `pipeline/blender_numpy/monster_doc.py`. The ranking itself is `claude_ue5/SourceArt/monster_gallery/monsters.json`.
"""
TAIL = """
## Not ranked

- **Pack animals:** the camel (`SK_Camel_Full`) and the laden buffalo (`SK_Bull_Fantasy_Full`) of the Fantasy Animal (Pack). They carry baggage; they are not monsters.
- **Creatures Mega Pack models that are not imported:** `Fat`, `Organic_trap`, `Poisonous_claw`, `Cocoon` and `Character_01` are in the cached pack but not in this project, so they could not be seen on their own.
- **Not creatures:**
  - Baby In Capsule: a human baby.
  - Sci-FI Creocapsule: a capsule prop overgrown with organic matter.
  - Sci-Fi Experimental: a lab with a specimen lying on the table, with no character model.
  - The scientist (`NPC_Scientist`) of Monster In Capsule.
"""
parts = [HEAD]
for tier in [t for t in dict.fromkeys(e["tier"] for e in D)]:
    parts.append("\n## %s\n\n| # | Monster | Pack | Model | Height | Looks | original · infernal · venom · frost |\n|---|---|---|---|---|---|---|\n" % tier)
    parts.append("\n".join(rows[tier]) + "\n")
parts.append(TAIL)
io.open(DOC, "w", encoding="utf-8", newline="\n").write("".join(parts))
size = sum(os.path.getsize(os.path.join(IMG, f)) for f in os.listdir(IMG))
print("monster_doc: %d strips, %.1f MB, %s" % (len(D), size / 1e6, DOC))
