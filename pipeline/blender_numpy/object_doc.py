"""docs/objects.md and its pictures, from claude_ue5/SourceArt/object_gallery/objects.json (the weapons and items, their
section, group, use and looks), the renders of pipeline/unreal/904_object_gallery.py (shoot) and the animation survey
(902: each object's size and skeleton, and the project's clips): for each entry three pictures,
docs/images/objects/<id>_side.jpg, _quarter.jpg and _third.jpg (a frame of its own clip, or the far three-quarter view),
480 x 300.
An entry's animation note has three parts: the object's own clips (a skeletal gun's shot and reload, a lighter's lid),
the first-person arm clips made for it (the FPS packs: `fp` in the data, a folder and a clip-name pattern), and the
third-person animation sets of the project that wield its kind of weapon (`kind`, the WIELD table below).
Usage (a Python with Pillow):  object_doc.py <shots_dir>"""
import sys, os, io, re, json, collections
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_text
SHOTS = sys.argv[1]
ROOT = anim_text.ROOT
DATA = os.path.join(ROOT, "claude_ue5", "SourceArt", "object_gallery", "objects.json")
IMG = os.path.join(ROOT, "docs", "images", "objects"); DOC = os.path.join(ROOT, "docs", "objects.md")
W, H = 480, 300
SECTIONS = ["Fantasy weapons", "Modern weapons", "Futuristic weapons", "Non-weapon items"]
GROUPS = ["Swords and daggers", "Axes, hammers, maces and clubs", "Spears and polearms", "Primitive weapons", "Bows, crossbows and staves", "Shields",
          "Rifles, machine guns and shotguns", "Sniper rifles and launchers", "Pistols and revolvers", "Knives, melee weapons and grenades",
          "Energy and sci-fi guns", "Energy blades and shields", "Food and drink", "Potions and medicine", "Tools and devices", "Treasure, keys and books",
          "Helmets and masks"]


def groups(items):
    return sorted(dict.fromkeys(v["group"] for v in items), key=lambda g: GROUPS.index(g) if g in GROUPS else len(GROUPS))
WS = "[Weapon And Shield Animations](https://www.fab.com/listings/eb3cfd11-3525-4a0d-9f15-793f62847f6a) (35 clips: sword-and-shield attacks, blocks, hits, deaths, moves)"
WAR = "[92 Animations For Warrior](https://www.fab.com/listings/84b7b209-1450-4a0a-a46f-cc6d4ab61eac) (92 clips: 8 two-handed attacks, deaths, hits, moves; the same set comes with the orc, beast-warrior, dwarf and fantasy-character packs)"
SPS = "[Spear And Shield Animations](https://www.fab.com/listings/0302d959-984a-48be-9e4f-033dd545b525) (36 clips: 7 spear attacks, blocks, hits, moves)"
LAU = "[Launcher Animations](https://www.fab.com/listings/8556b5ba-9c44-4004-a0b5-7366e57ec888) (59 third-person clips with a shoulder launcher: attacks, reloads, moves)"
RIF = ("UE4-mannequin clips with a long gun: the Aliens Warrior pack's 47 (3 shots, a reload, aims in eight directions, moves), the Sci-Fi Characters pack's "
       "fire, crouch-walk and sprint with iron sights, and the rifle jog, sprint and crouch-walk that came with the Military, Cyber Characters and Monsters "
       "Underwater packs; and the UE5 template's rifle equip and reload (retargeted)")
WIELD = {  # weapon kind -> the third-person sets of the project that hold one
    "sword": "held by %s; the two-handed ones by %s." % (WS, WAR),
    "one": "held by %s." % WS,
    "two": "held by %s." % WAR,
    "spear": "held by %s." % SPS,
    "shield": "carried by %s and %s." % (WS, SPS),
    "dagger": "no third-person knife clips in the project; the first-person ones are in FPS Pistol And Knife, the FPS Starter Pack and Sci-Fi Hands With Knife.",
    "knife": "no third-person knife clips in the project.",
    "staff": "no staff or spell-casting clips in the project; a staff can borrow %s." % SPS,
    "bow": "no bow clips for the UE4 mannequin; the Dark Fantasy Weapons pack (`Medieval_Weapons`) has UE5-mannequin clips that aim a bow (retargeted).",
    "crossbow": "no crossbow clips for the UE4 mannequin; the Dark Fantasy Weapons pack has UE5-mannequin clips that aim a crossbow (retargeted).",
    "rifle": "held by %s." % RIF,
    "shotgun": "held by %s (a shotgun has no third-person clips of its own)." % RIF,
    "sniper": "held by %s (no third-person sniper clips)." % RIF,
    "pistol": "held by the UE5 template's pistol clips (`MF_Pistol_*`, `MM_Pistol_*`: idle, aim, fire, reload; retargeted).",
    "launcher": "held by %s." % LAU,
    "grenade": "no throwing clips in the project.",
    "melee": "swung by %s, or one-handed by %s." % (WAR, WS),
    "ammo": None, "item": None,
    "wear": None,
}


def short_names(clips):
    """clip names without the words they all share (Anim_Sci_Fi_Shield_Open / _Close: open, close)"""
    toks = [re.sub(r"^(Anim_|AS_)", "", re.sub(r"_Anim$", "", x)).split("_") for x in clips]
    k = 0
    while len(toks) > 1 and all(len(t) > k + 1 for t in toks) and len({t[k] for t in toks}) == 1: k += 1
    return sorted({re.sub(r"\s*\d+$", "", " ".join(t[k:]).lower()).strip() for t in toks})


def own_line(v, A, info):
    skels = info.get("skeletons", [])
    if not skels: return "a static mesh, no clips of its own."
    if v["kind"] == "wear": return "a part of its character, skinned to the character's skeleton: it plays whatever the character plays."
    clips = sorted({x for m in v["meshes"] if m in A.chars for x in A.chars[m]["own"]})
    bones = max([A.chars[m]["bones"] for m in v["meshes"] if m in A.chars] or [0])
    if bones >= 30 and any(re.search(r"idle|walk|run", x, re.I) for x in clips):        # (skinned to a character's skeleton: those are the character's clips)
        return "a part skinned to its character's skeleton (%d bones): it moves with that character's clips." % bones
    if not clips: return "a skeletal mesh (%d bone%s) without clips of its own." % (bones, "" if bones == 1 else "s")
    names = short_names(clips) if len(clips) > 1 else [anim_text.tidy(clips[0], anim_text.prefix(clips))]
    return "a skeletal mesh (%d bones) with %d clip%s of its own: %s." % (bones, len(clips), "" if len(clips) == 1 else "s", ", ".join(names))


def fp_line(v, A):
    out = []
    for folder, rx, label in v.get("fp", []):
        clips = sorted({x for l in A.libs if l["folder"] == folder and l["rig"] != "own" for x in l["clips"] if re.search(rx, x)})
        if clips: out.append("%d in %s: %s" % (len(clips), label, anim_text.counts(clips)))
    return ("first-person arm clips: " + "; ".join(out) + ".") if out else None


def anim_line(v, A, info):
    parts = ["**Own:** " + own_line(v, A, info)]
    f = fp_line(v, A)
    if f: parts.append("**First person:** " + f[0].upper() + f[1:])
    w = WIELD.get(v["kind"])
    if w: parts.append("**Third person:** " + w[0].upper() + w[1:])
    return " ".join(parts)


os.makedirs(IMG, exist_ok=True)
for f in os.listdir(IMG):
    if f.endswith(".jpg"): os.remove(os.path.join(IMG, f))
D = json.load(io.open(DATA, encoding="utf-8")); obs = D["objects"]; blurbs = D.get("blurbs", {})
A = anim_text.Anims(); INFO = json.load(io.open(anim_text.DATA, encoding="utf-8")).get("objects", {})
for v in obs:
    for k in ("side", "quarter", "third"):
        Image.open(os.path.join(SHOTS, "%s_%s.png" % (v["id"], k))).convert("RGB").resize((W, H), Image.LANCZOS).save(os.path.join(IMG, "%s_%s.jpg" % (v["id"], k)), quality=84, optimize=True)
def anchor(s): return re.sub(r"[^a-z0-9 -]", "", s.lower()).replace(" ", "-")
n_clip = sum(1 for v in obs if v.get("clip"))
out = ["""# Weapons and items of the Fab library

The weapons and the handheld or wearable items in the local Fab library cache (`I:\\game assets\\3d epicgames media packs\\VaultCache\\FabLibrary` and the environment packs downloaded through it), in four parts: fantasy weapons, modern weapons, futuristic weapons and non-weapon items. All %d are in this project. Each is shown three times, rendered in Unreal Engine:

- **side view:** its broad face, level (or from above if it lies flat);
- **three-quarter view;**
- a **frame of its own clip** for the %d that have one (a gun's reload or shot, a can's lid, a syringe's plunger), or the **far three-quarter view** for the rest.

## About the pictures and notes

- **Sizes:** each entry gives the object's three extents in centimetres, from its bounds; every picture is framed to fill, from a 2 cm coin to a 1.5 m flamethrower.
- **Kept together:** the flamethrower (gun, hose, tank) and the riot shield with its club are several meshes, shown as they sit in their packs.
- **Variants:** many packs have several versions of a weapon (silencers, sights, paint, the ten knives of the FPS Starter Pack, eight pistols and revolvers in `Safehouse`); one of each kind is shown.
- **Animations:** each entry says what clips the object has of its own, which first-person arm clips were made for it (the FPS packs: arms only, a camera rig's), and which third-person animation sets in the project hold that kind of weapon on a UE4-mannequin character (see [heroes.md](heroes.md#animations) for those sets). Bows, crossbows, staves, knives and grenades have no third-person clips here.
- **Uses:** a use is a suggestion from the object's looks.

The list is `claude_ue5/SourceArt/object_gallery/objects.json`; the pictures come from `pipeline/unreal/904_object_gallery.py` and `pipeline/blender_numpy/object_doc.py`, the sizes and animation notes from `pipeline/unreal/902_character_animations.py`. The sellers and listings of the packs are in [assets.md](assets.md).

## Contents

""" % (len(obs), n_clip)]
for s in SECTIONS:
    items = [v for v in obs if v["section"] == s]
    out.append("- [%s](#%s) (%d)\n" % (s, anchor(s), len(items)))
    for g in groups(items):
        out.append("  - [%s](#%s) (%d)\n" % (g, anchor(g), sum(1 for v in items if v["group"] == g)))
out.append("- [Not included](#not-included)\n")
for s in SECTIONS:
    out.append("\n## %s\n" % s)
    if s in blurbs: out.append("\n%s\n" % blurbs[s])
    items = [v for v in obs if v["section"] == s]
    for g in groups(items):
        out.append("\n### %s\n" % g)
        for v in [x for x in items if x["group"] == g]:
            info = INFO.get(v["id"], {})
            link = "[%s](https://www.fab.com/listings/%s)" % (v["pack"], v["uid"]) if v.get("uid") else v["pack"]
            model = "`%s`" % v["meshes"][0].rsplit("/", 1)[1].split(".")[0] + (" and %d more meshes" % (len(v["meshes"]) - 1) if len(v["meshes"]) > 1 else "")
            size = " · %d × %d × %d cm" % tuple(info["size_cm"]) if info.get("size_cm") else ""
            out.append("\n#### %s\n\n" % v["name"])
            out.append("%s · **Use:** %s · model %s%s\n\n" % (link, v.get("use") or "-", model, size))
            if v.get("looks"): out.append("%s\n\n" % v["looks"])
            out.append("**Animations.** %s\n\n" % anim_line(v, A, info))
            third = "a frame of its clip" if v.get("clip") and info.get("skeletons") else "far three-quarter view"
            out.append("".join('<img src="images/objects/%s_%s.jpg" width="280" alt="%s, %s"> ' % (v["id"], k, v["name"], lbl)
                               for k, lbl in (("side", "side view"), ("quarter", "three-quarter view"), ("third", third))).rstrip() + "\n")
out.append("""
## Not included

- **Parts:** magazines, cartridges, bullets, sleeves, sights, silencers, flashlights, scabbards and holsters, sold with the guns and blades as separate meshes.
- **Duplicates and variants:** the same weapon in several volumes or colours, the fake toy weapons of `HOLIDAY`, a pack's second and third version of a shield, sword or spear.
- **Scenery:** tables, racks and shelves with weapons on them (`Safehouse`'s gunsmith tables), weapon statues, spike barriers, the `Crownfall` spear-knight statues; furniture, lamps, food stalls and other set dressing.
- **Clothing:** bags, belts, backpacks and armour pieces that only make sense on their character; a few helmets and masks are shown as wearable items.
- **The project's own:** the castle furniture kit's props (the tankard, the cart), modelled for this project.
""")
io.open(DOC, "w", encoding="utf-8", newline="\n").write("".join(out))
size = sum(os.path.getsize(os.path.join(IMG, f)) for f in os.listdir(IMG))
print("object_doc: %d entries, %d pictures, %.1f MB, %s" % (len(obs), len(os.listdir(IMG)), size / 1e6, DOC))
