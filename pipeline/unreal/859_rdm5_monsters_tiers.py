"""random_dungeonmagic_level5's monsters by the tiers of docs/monsters.md (SourceArt/random_dungeon_magic5/monster_tiers.json:
the 55 gallery monsters whose clips the game can play, each with its tier). For each, measured as 770 and 791 measure the
dungeon's own: its capsule from its mesh's bounds, its walking speed from its feet in its walk clip (in place), up to three
attack clips (the short ones) and when each blow lands (where its fastest bone peaks); its hit points and damage within
its tier by its rank there (0.8 to 1.2 of the tier's average), its reach by its size, its sound set and ability from the
file. A warrior of the Orcs, Animals Warrior and Aliens Warrior packs gets its pack's weapon mesh (the StaticMesh named
*Weapon* in its model's folder) on its skeleton's weapon socket (weapon_r, else hand_r).
The generator: Monsters (the old six kinds are among them, by their names), TierHealth / TierDamage / TierSpeed /
TierAttackInterval / TierAbility (the file's tiers). Prints each monster and each tier's average monster. Saves the level.
Args: [names...] only measure and print those (no save)"""
import json, math, os, sys, unreal
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_magic5"
MT = json.load(open(os.path.join(SA, "monster_tiers.json"), encoding="utf-8"))
LEVEL = "/Game/RandomDungeon/Maps/random_dungeonmagic_level5"
eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ar = unreal.AssetRegistryHelpers.get_asset_registry()
ABIL = {"None": unreal.RDMonsterAbility.NONE, "Poison": unreal.RDMonsterAbility.POISON, "Weaken": unreal.RDMonsterAbility.WEAKEN, "Slow": unreal.RDMonsterAbility.SLOW}
ONLY = sys.argv[1:]
# (the dungeon's first six keep their names: tests, the reels and the Knight spell name them)
OLD = {"Troll": "Troll", "Daemon": "Daemon", "Horned": "Horned", "Ripper dog": "Ripper_dog", "Spider": "Spider", "Mutant": "Mutant"}
o_ = unreal.AnimPoseEvaluationOptions()


def length(a): return unreal.AnimationLibrary.get_sequence_length(a)


def clip_speed(anim):
    """ground speed of a walk clip: the horizontal speed of its lowest bones while they are planted (770's, with the
    bones nearest the floor instead of the ones named foot: many packs name them otherwise, and a crawler walks on its hands)"""
    try:
        L = length(anim); p0 = APE.get_anim_pose_at_time(anim, 0.0, o_)
        names = list(APE.get_bone_names(p0))
        lowest = sorted(names[1:], key=lambda b: APE.get_bone_pose(p0, b, unreal.AnimPoseSpaces.WORLD).translation.z)[:6]
        feet = [b for b in names if any(k in str(b).lower() for k in ("foot", "toe", "ball")) and "ik_" not in str(b).lower()]
        feet = list(dict.fromkeys(feet + lowest))
        if not feet: return None
        n = 60; speeds = []
        for f in feet:
            pts = [APE.get_bone_pose(APE.get_anim_pose_at_time(anim, L * i / n, o_), f, unreal.AnimPoseSpaces.WORLD).translation for i in range(n + 1)]
            zmin = min(p.z for p in pts)
            for i in range(n):
                if pts[i].z < zmin + 4 and pts[i + 1].z < zmin + 4: speeds.append(math.hypot(pts[i + 1].x - pts[i].x, pts[i + 1].y - pts[i].y) / (L / n))
        speeds = sorted(s for s in speeds if s > 5)
        return speeds[len(speeds) // 2] if speeds else None
    except Exception as e:
        print("   clip speed failed:", e); return None


def blow_time(anim):
    """when the creature's fastest bone peaks: where the blow lands (791's)"""
    L = length(anim); n = 30
    names = APE.get_bone_names(APE.get_anim_pose_at_time(anim, 0.0, o_))
    pts = [[APE.get_bone_pose(p, b, unreal.AnimPoseSpaces.WORLD).translation for b in names] for p in (APE.get_anim_pose_at_time(anim, L * k / n, o_) for k in range(n + 1))]
    sp = [max((pts[k + 1][i] - pts[k][i]).length() for i in range(len(names))) / (L / n) for k in range(n)]
    sm = [sum(sp[max(0, k - 1):k + 2]) / len(sp[max(0, k - 1):k + 2]) for k in range(n)]
    k = max(range(n), key=lambda i: sm[i])
    return min(max(L * (k + 0.5) / n, 0.15), L - 0.1)


def weapon_of(mesh_path):
    """the pack's weapon mesh in the model's folder (its sub-folders too; else the one above it): a skeletal one made on
    the body's skeleton (it follows the body as a part), else a static one (on the hand's socket). Returns (path, skeletal)"""
    folder = mesh_path.rsplit("/", 1)[0]; parent = folder.rsplit("/", 1)[0]
    # (the folder above: all of it when it is the model's own (Alien_Warrior_05/Full and /Weapon), else not its other models')
    own = parent.rsplit("/", 1)[-1].lower() in mesh_path.rsplit("/", 1)[-1].lower()
    for d, deep in ((folder, True), (parent, own)):
        found = [a for a in ar.get_assets_by_path(d, recursive=deep) if "weapon" in str(a.asset_name).lower()]
        sk = [a for a in found if str(a.asset_class_path.asset_name) == "SkeletalMesh"]
        sm = [a for a in found if str(a.asset_class_path.asset_name) == "StaticMesh"]
        if sk: return str(sk[0].package_name), True
        if sm: return str(sm[0].package_name), False
    return None, False


USED = set()
def name_of(e):
    n = OLD.get(e["name"], "".join(c if c.isalnum() else "_" for c in e["name"]).strip("_").replace("__", "_"))
    if n in USED: n = e["pack"].split()[0].strip("0123456789") + "_" + n          # (two gallery monsters named Fat)
    USED.add(n)
    return n


MON = []; rows = []
by_tier = {}
for e in MT["monsters"]: by_tier.setdefault(e["tier"], []).append(e)
for t, es in by_tier.items(): es.sort(key=lambda x: x["rank"])
for e in MT["monsters"]:
    sk = unreal.load_asset(e["mesh"]); idle = unreal.load_asset(e["idle"]); walk = unreal.load_asset(e["walk"])
    hit = unreal.load_asset(e["hit"]); death = unreal.load_asset(e["death"])
    att = [unreal.load_asset(a) for a in e["attacks"]]
    att = [a for a in att if a]
    short = [a for a in att if length(a) <= 2.8]
    att = (short or sorted(att, key=length)[:1])[:3]
    assert sk and idle and walk and hit and death and att, e["name"]
    b = sk.get_bounds(); ext = b.box_extent; org = b.origin
    zmin = org.z - ext.z
    hh = max(40.0, ext.z); rad = min(80.0, max(28.0, min(ext.x, ext.y) * 0.8))
    spd = clip_speed(walk) or 150.0
    d = unreal.RDMonsterDef(); d.name = name_of(e); d.title = e["name"]; d.mesh = sk; d.idle = idle; d.walk = walk
    if ONLY and e["name"] not in ONLY and str(d.name) not in ONLY: continue
    d.walk_clip_speed = max(spd, 60.0); d.walk_speed = max(90.0, min(220.0, spd));     # (a hoverer's lowest bones hardly travel) d.capsule_radius = rad; d.capsule_half_height = hh
    d.mesh_z = -hh - zmin; d.mesh_yaw = -90.0; d.scale = 1.0; d.weight = 1.0
    d.attacks = att; d.hit_times = [blow_time(a) for a in att]; d.get_hit = hit; d.death = death
    es = by_tier[e["tier"]]; k = es.index(e)
    f = 0.8 + 0.4 * k / max(len(es) - 1, 1)              # (within its tier: the gallery's weakest 0.8, its strongest 1.2)
    d.health_factor = round(f, 3); d.damage_factor = round(f, 3)
    d.reach = round(70.0 + 0.9 * rad); d.attack_interval = 1.9 if hh > 140 else 1.6
    d.sound_set = e["sound"]; d.step_length = round(40.0 + 0.25 * e["height"])
    d.tier = e["tier"]; d.ability = ABIL[e["ability"]]
    d.parts = [unreal.load_asset(p) for p in e["parts"] if eal.does_asset_exist(p)]
    wp = None
    if e.get("weapon"):
        wp, skel = weapon_of(e["mesh"])
        if wp and skel:
            d.parts = list(d.parts) + [unreal.load_asset(wp)]
        elif wp:
            d.weapon_mesh = unreal.load_asset(wp)
            d.weapon_bone = "weapon_r" if sk.find_socket("weapon_r") else "hand_r"
            d.weapon_grip = unreal.Transform()
    MON.append(d)
    rows.append([str(d.name), e["tier"], round(ext.z * 2), round(rad), round(hh), round(spd), [round(h, 2) for h in d.hit_times], round(f, 2), str(e["ability"]), e["sound"], wp.rsplit("/", 1)[-1] if wp else None, len(d.parts)])
report = {"monsters": len(MON), "rows": rows}
if not ONLY:
    if not ues.get_editor_world().get_path_name().startswith(LEVEL + "."): unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    gen.set_editor_property("monsters", MON)
    T = MT["tiers"]
    for k, prop in (("health", "tier_health"), ("damage", "tier_damage"), ("speed", "tier_speed"), ("attack_interval", "tier_attack_interval"), ("ability", "tier_ability")):
        gen.set_editor_property(prop, [float(v) for v in T[k]])
    gen.modify(); les.save_current_level()
    # (each tier's average monster against her: by the sections of that ring)
    report["tier average"] = {t: [round(gen.get_monster_health(unreal.IntPoint(t - 1, 0))), round(gen.get_monster_damage(unreal.IntPoint(t - 1, 0)), 1)] for t in range(1, 6)}
print("RDM5MONSTERS", json.dumps(report, ensure_ascii=False))
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
