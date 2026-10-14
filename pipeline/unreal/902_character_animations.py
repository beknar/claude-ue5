"""Which animations each character of docs/heroes.md and docs/humanoid_enemies.md can play, for those pages
(SourceArt/character_animations/animations.json, read by hero_doc.py and enemy_doc.py).
For every character (heroes.json, enemies.json): its skeleton, the clips of the project on that same skeleton (its
pack's own), and the kind of rig: `ue4` (UE4-mannequin bone names: pelvis, spine_01..03, neck_01, head, the arm and
leg chains), `ue5` (the UE5 mannequin's, spine_05 and neck_02 as well) or `own` (a rig of its own: CAT, Maya
AdvancedSkeleton, custom names). And the animation libraries of the project: every skeleton with clips, its folder,
its clips and its rig. A clip of a `ue4` library plays on a `ue4` character as it is (the hero gallery's action poses
did exactly that); `ue5` clips need the IK retargeter; an `own` rig plays only its own clips.
Clips made by this project (its levels, the galleries' poses, retargeted copies) are left out: see SKIP.
Args: none"""
import os, json, unreal
ROOT = r"E:\code\claude-ue5\claude_ue5\SourceArt"
OUT = os.path.join(ROOT, "character_animations", "animations.json")
SKIP = ("HeroGallery", "RandomDungeon", "RandomLevel", "JRPG", "FF", "FF2", "Fig4", "Meshy", "Feather", "TheMessenger", "MetaHumans", "Soldier",
        "MonsterGallery", "StarshipLevel")
CORE = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head", "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l", "clavicle_r", "upperarm_r",
        "lowerarm_r", "hand_r", "thigh_l", "calf_l", "foot_l", "thigh_r", "calf_r", "foot_r"]
APE = unreal.AnimPoseExtensions
ar = unreal.AssetRegistryHelpers.get_asset_registry()


def rig(skel):
    names = set(str(b) for b in APE.get_bone_names(APE.get_reference_pose(skel)))
    if not all(b in names for b in CORE): return "own", len(names)
    return ("ue5" if "spine_05" in names and "neck_02" in names else "ue4"), len(names)


groups = {}                                         # skeleton path -> [clip package paths]
for ad in ar.get_assets_by_class(unreal.TopLevelAssetPath("/Script/Engine", "AnimSequence"), True):
    pkg = str(ad.package_name)
    if pkg.split("/")[2] in SKIP: continue
    sk = str(ad.get_tag_value("Skeleton") or "")
    sk = sk.split("'")[1] if "'" in sk else sk
    if sk: groups.setdefault(sk.split(".")[0], []).append(pkg)
libs, rigs = [], {}
for sk, clips in sorted(groups.items()):
    s = unreal.load_asset(sk)
    if not s: continue
    rigs[sk] = rig(s)
    libs.append({"skeleton": sk, "folder": sk.split("/")[2], "rig": rigs[sk][0], "bones": rigs[sk][1], "clips": sorted(c.rsplit("/", 1)[1] for c in clips)})
chars = {}
for gal, key in (("hero_gallery", "heroes"), ("enemy_gallery", "enemies")):
    for h in json.load(open(os.path.join(ROOT, gal, key + ".json"), encoding="utf-8"))[key]:
        p = h["mesh"]
        if p in chars: continue
        m = unreal.load_asset(p)
        if not m: print("CHARANIM missing", p); continue
        sk = m.skeleton.get_path_name().split(".")[0]
        r = rigs.get(sk) or rig(m.skeleton)
        chars[p] = {"skeleton": sk, "rig": r[0], "bones": r[1], "own": sorted(c.rsplit("/", 1)[1] for c in groups.get(sk, []))}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump({"libraries": libs, "characters": chars}, open(OUT, "w", encoding="utf-8"), indent=1)
print("CHARANIM %d libraries (%d clips), %d characters: %s" % (len(libs), sum(len(l["clips"]) for l in libs), len(chars),
      {k: sum(1 for c in chars.values() if c["rig"] == k) for k in ("ue4", "ue5", "own")}))
