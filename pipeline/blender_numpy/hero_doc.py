"""docs/heroes.md and its pictures, from claude_ue5/SourceArt/hero_gallery/heroes.json (the candidates, their category,
role and looks), the renders of pipeline/unreal/901_hero_gallery.py (shoot) and the animation survey (902,
anim_text.py): for each hero three pictures,
docs/images/heroes/<id>_full.jpg / _bust.jpg / _action.jpg, 360 x 468.
Usage (a Python with Pillow):  hero_doc.py <shots_dir>"""
import sys, os, io, json
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_text
SHOTS = sys.argv[1]
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
DATA = os.path.join(ROOT, "claude_ue5", "SourceArt", "hero_gallery", "heroes.json")
IMG = os.path.join(ROOT, "docs", "images", "heroes"); DOC = os.path.join(ROOT, "docs", "heroes.md")
W, H = 360, 468
POSE = {"sword": "a sword strike", "heavy": "a two-handed axe blow", "spear": "a spear thrust", "rifle": "aiming a rifle", "unarmed": "a punch",
        "own": "an attack from its own pack"}
os.makedirs(IMG, exist_ok=True)
for f in os.listdir(IMG):
    if f.endswith(".jpg"): os.remove(os.path.join(IMG, f))
D = json.load(io.open(DATA, encoding="utf-8"))
heroes = D["heroes"]; cats = D.get("categories", {})
A = anim_text.Anims()
for h in heroes:
    for v in ("full", "bust", "action"):
        Image.open(os.path.join(SHOTS, "%s_%s.png" % (h["id"], v))).convert("RGB").resize((W, H), Image.LANCZOS).save(os.path.join(IMG, "%s_%s.jpg" % (h["id"], v)), quality=84, optimize=True)
order = list(dict.fromkeys(h["category"] for h in heroes))
out = ["""# Heroes and playable characters of the Fab library

Every character in the local Fab library cache (`I:\\game assets\\3d epicgames media packs\\VaultCache\\FabLibrary`) that could be a hero or a player character: fighters, soldiers, adventurers and other figures built to be played or to fight. All %d are in this project; each is shown three times, rendered in Unreal Engine:

- **full body:** standing in its model's reference pose;
- **upper body and head:** a closer look at the face and gear;
- **action:** a fighting pose.

## About the pictures

- **Action poses:** most packs come without attack clips. These characters all share the UE4-mannequin skeleton, so each pose is copied from another pack's clip at the moment of the blow: a sword strike, a two-handed axe blow, a spear thrust, rifle aim or a punch. Characters whose pack has attack clips of its own use one of those.
- **Props:** the weapons in the melee poses come from Medieval_Weapons; the rifle is MC_Environment's assault rifle. None of these props are the characters' own.
- **Animation:** each entry says what its character can play; the libraries they share are listed under [Animations](#animations).
- **Roles:** a role is a suggestion from the character's looks: what it wears, what it carries, how it is built.

The list is `claude_ue5/SourceArt/hero_gallery/heroes.json`; the pictures come from `pipeline/unreal/901_hero_gallery.py` and `pipeline/blender_numpy/hero_doc.py`, the animation notes from `pipeline/unreal/902_character_animations.py`. Many of them could be enemies as well: see [humanoid_enemies.md](humanoid_enemies.md). The sellers and listings of the packs are in [assets.md](assets.md).

## Categories

""" % len(heroes)]
for c in order:
    n = sum(1 for h in heroes if h["category"] == c)
    out.append("- [%s](#%s) (%d)%s\n" % (c, c.lower().replace(",", "").replace(" ", "-"), n, (": " + cats[c]) if c in cats else ""))
out.append("- [Animations](#animations)\n- [Not included](#not-included)\n")
for c in order:
    out.append("\n## %s\n" % c)
    if c in cats: out.append("\n%s\n" % cats[c])
    for h in [x for x in heroes if x["category"] == c]:
        link = "[%s](https://www.fab.com/listings/%s)" % (h["pack"], h["uid"]) if h.get("uid") else h["pack"]
        out.append("\n### %s\n\n" % h["name"])
        out.append("%s · **Role:** %s · **Pose:** %s · model `%s`\n\n" % (link, h.get("role") or "-", POSE.get(h["family"], h["family"]), h["mesh"].rsplit("/", 1)[1].split(".")[0]))
        if h.get("looks"): out.append("%s\n\n" % h["looks"])
        out.append("**Animations:** %s\n\n" % A.line(h["mesh"], h["pack"]))
        out.append("".join('<img src="images/heroes/%s_%s.jpg" width="270" alt="%s, %s"> ' % (h["id"], v, h["name"], lbl) for v, lbl in (("full", "full body"), ("bust", "upper body and head"), ("action", "action pose"))).rstrip() + "\n")
out.append("\n" + A.section())
out.append("""
## Not included

- **Civilians and townsfolk:** the NPC packs (villagers, kids, beggars, prisoners, the king and queen's court, the old gangster, the sailor NPC), the girl and the scientist. They could be played, but they are not built to fight.
- **Monsters and creatures:** see [monsters.md](monsters.md). The orcs are there too.
- **First-person arms and parts:** the FPS packs (hands only) and modular parts packs (heads, armour, clothing pieces: `MegaPost_Character`, `Tactical_masks`).
- **Unity-format packs:** character packs that exist only in Unity format and have no Unreal copy in the cache. All the hero packs in the cache have one, so none are left out for this.
""")
io.open(DOC, "w", encoding="utf-8", newline="\n").write("".join(out))
size = sum(os.path.getsize(os.path.join(IMG, f)) for f in os.listdir(IMG))
print("hero_doc: %d heroes, %d pictures, %.1f MB, %s" % (len(heroes), len(os.listdir(IMG)), size / 1e6, DOC))
