"""docs/humanoid_enemies.md and its pictures, from claude_ue5/SourceArt/enemy_gallery/enemies.json (the candidates, their
category, role and looks), the renders of pipeline/unreal/901_hero_gallery.py (enemies shoot) and the animation survey
(902, anim_text.py): for each enemy three pictures, docs/images/enemies/<id>_full.jpg / _bust.jpg / _action.jpg,
360 x 468. An enemy that is also on docs/heroes.md (`hero`) shows the hero's pictures.
Usage (a Python with Pillow):  enemy_doc.py <shots_dir>"""
import sys, os, io, json
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_text
SHOTS = sys.argv[1]
ROOT = anim_text.ROOT
DATA = os.path.join(ROOT, "claude_ue5", "SourceArt", "enemy_gallery", "enemies.json")
IMG = os.path.join(ROOT, "docs", "images", "enemies"); DOC = os.path.join(ROOT, "docs", "humanoid_enemies.md")
W, H = 360, 468
POSE = {"sword": "a sword strike", "heavy": "a two-handed axe blow", "spear": "a spear thrust", "rifle": "aiming a rifle", "unarmed": "a punch",
        "own": "an attack from its own pack"}
os.makedirs(IMG, exist_ok=True)
for f in os.listdir(IMG):
    if f.endswith(".jpg"): os.remove(os.path.join(IMG, f))
D = json.load(io.open(DATA, encoding="utf-8"))
ens = D["enemies"]; cats = D.get("categories", {})
A = anim_text.Anims()
for e in ens:
    if e.get("hero"): continue
    for v in ("full", "bust", "action"):
        Image.open(os.path.join(SHOTS, "%s_%s.png" % (e["id"], v))).convert("RGB").resize((W, H), Image.LANCZOS).save(os.path.join(IMG, "%s_%s.jpg" % (e["id"], v)), quality=84, optimize=True)
order = list(dict.fromkeys(e["category"] for e in ens))
n_hero = sum(1 for e in ens if e.get("hero"))
out = ["""# Humanoid enemies of the Fab library

Every humanoid character in the local Fab library cache (`I:\\game assets\\3d epicgames media packs\\VaultCache\\FabLibrary`) that could be fought as an enemy: undead, orcs and trolls, demons, mutants, beast-men, thugs, soldiers and aliens. A humanoid here walks or crawls on a human body plan: two arms, a head, and two legs or a torso dragging itself (four-legged beasts, spiders, dragons and vehicles are on [monsters.md](monsters.md) only). All %d are in this project; %d of them are also on [heroes.md](heroes.md), since a soldier or a dark knight can be either, and show the same pictures there. Each is shown three times, rendered in Unreal Engine:

- **full body:** standing in its model's reference pose;
- **upper body and head:** a closer look at the face and gear;
- **action:** a fighting pose.

## About the pictures

- **Action poses:** a character whose pack has attack clips of its own on its own skeleton strikes with one of them (at the frame its right hand reaches farthest). The others are UE4-mannequin rigs without attack clips of their own: their pose is copied from another pack's clip, as on [heroes.md](heroes.md): a two-handed axe blow (92 Animations For Warrior), rifle aim (Sci-Fi Characters) or a punch (41 Animations For Monsters). The orcs' pack comes with the same 92 warrior clips the axe blow is taken from, so theirs is their own pack's blow too.
- **Props:** the axes come from Medieval_Weapons and the rifle is MC_Environment's assault rifle; they are not the characters' own. The orcs' and the fantasy enemies' own weapons are separate meshes in their packs and are not shown.
- **Several meshes:** the crawlers and one fish-man are made of several skeletal meshes (body, head, guts, shell), all posed alike.
- **Roles:** a role is a suggestion from the character's looks: how big it is, what it wears and carries, how it would fight.

The list is `claude_ue5/SourceArt/enemy_gallery/enemies.json`; the pictures come from `pipeline/unreal/901_hero_gallery.py` (`enemies`) and `pipeline/blender_numpy/enemy_doc.py`, the animation notes from `pipeline/unreal/902_character_animations.py`. The sellers and listings of the packs are in [assets.md](assets.md).

## Categories

""" % (len(ens), n_hero)]
for c in order:
    n = sum(1 for e in ens if e["category"] == c)
    out.append("- [%s](#%s) (%d)%s\n" % (c, c.lower().replace(",", "").replace(" ", "-"), n, (": " + cats[c]) if c in cats else ""))
out.append("- [Animations](#animations)\n- [Not included](#not-included)\n")
for c in order:
    out.append("\n## %s\n" % c)
    if c in cats: out.append("\n%s\n" % cats[c])
    for e in [x for x in ens if x["category"] == c]:
        link = "[%s](https://www.fab.com/listings/%s)" % (e["pack"], e["uid"]) if e.get("uid") else e["pack"]
        out.append("\n### %s\n\n" % e["name"])
        out.append("%s · **Role:** %s · **Pose:** %s · model `%s`\n\n" % (link, e.get("role") or "-", POSE.get(e["family"], e["family"]), e["mesh"].rsplit("/", 1)[1].split(".")[0]))
        if e.get("looks"): out.append("%s\n\n" % e["looks"])
        also = []
        if e.get("hero"): also.append("also a hero on [heroes.md](heroes.md)")
        if e.get("monster_rank"): also.append("ranked %d of 107 by looks on [monsters.md](monsters.md)" % e["monster_rank"])
        if also: out.append("%s.\n\n" % "; ".join(also).capitalize())
        out.append("**Animations:** %s\n\n" % A.line(e["mesh"], e["pack"]))
        d, pid = ("heroes", e["hero"]) if e.get("hero") else ("enemies", e["id"])
        out.append("".join('<img src="images/%s/%s_%s.jpg" width="270" alt="%s, %s"> ' % (d, pid, v, e["name"], lbl) for v, lbl in (("full", "full body"), ("bust", "upper body and head"), ("action", "action pose"))).rstrip() + "\n")
out.append("\n" + A.section())
out.append("""
## Not included

- **Beasts and vehicles:** four-legged creatures, spiders, the raptor mount, the war elephants, the dragon, the hounds, the cartoon rat and the zombie tank: see [monsters.md](monsters.md).
- **Trapped or harmless:** the man hanging in a sack of gut, the baby in a capsule; civilians and townsfolk (the NPC packs: villagers, kids, beggars, the court), unless they are prisoners or gangsters.
- **Parts and arms:** first-person arms and modular parts packs (heads, masks, armour and clothing pieces: `MegaPost_Character`, `Tactical_masks`).
- **Heroes that do not look hostile:** the rest of [heroes.md](heroes.md) (knights, monks, astronauts, survivors) could be enemies in a story, but nothing in their looks says so.
""")
io.open(DOC, "w", encoding="utf-8", newline="\n").write("".join(out))
size = sum(os.path.getsize(os.path.join(IMG, f)) for f in os.listdir(IMG))
print("enemy_doc: %d enemies (%d heroes' pictures), %d pictures, %.1f MB, %s" % (len(ens), n_hero, len(os.listdir(IMG)), size / 1e6, DOC))
