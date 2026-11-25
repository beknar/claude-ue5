"""The list of 2026-11-22 (docs/improvements16.txt: "vary the Heaven dungeon with soldier variants, medics, differently colored/designed
drones and differently colored/designed mechs from the Dystopia and Sci-fi packs. also use aliens and monsters from the Aliens Warrior
Pack"; the plan docs/improvements16_plan.md), the fortress under Kratos Aurorim Research (`heaven_fortress`, 909), its phases 25 to 27:

    947_fortress.py monsters   phase 25: the defenders of SourceArt/heaven_fortress/defenders25.json added to 909's five (each a kind:
                               its clips found by name under its pack, its mesh's skeleton made compatible with them, measured as 909
                               measures; a colour variant's materials slot by slot from the pack's numbered set; a medic's heal (C++
                               RD/RDFortress25.cpp); a drone's hover); the castle's kinds' weights cut so the defenders are two in three
                               of each tier. Run 910 and 905 after it (they copy every dungeon's kinds to every map and give them their
                               wild bands), and again after any stage that writes the castle's monsters.

Run on the editor with any level open (it opens heaven_fortress and saves it)."""
import os, sys, re, json, math, gc
import unreal

DST = "/Game/RandomDungeon/Maps/heaven_fortress"
SA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "heaven_fortress"))
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
eal = unreal.EditorAssetLibrary
APE = unreal.AnimPoseExtensions; o_ = unreal.AnimPoseEvaluationOptions()
AR = unreal.AssetRegistryHelpers.get_asset_registry()
ABIL = {"None": unreal.RDMonsterAbility.NONE, "Poison": unreal.RDMonsterAbility.POISON, "Weaken": unreal.RDMonsterAbility.WEAKEN, "Slow": unreal.RDMonsterAbility.SLOW}


def length(a): return unreal.AnimationLibrary.get_sequence_length(a)


def clip_speed(anim):
    """909's (859's): the ground speed of a walk clip from its lowest bones while they are planted"""
    try:
        L = length(anim); p0 = APE.get_anim_pose_at_time(anim, 0.0, o_)
        names = list(APE.get_bone_names(p0))
        lowest = sorted(names[1:], key=lambda b: APE.get_bone_pose(p0, b, unreal.AnimPoseSpaces.WORLD).translation.z)[:6]
        feet = [b for b in names if any(k in str(b).lower() for k in ("foot", "toe", "ball")) and "ik_" not in str(b).lower()]
        feet = list(dict.fromkeys(feet + lowest))
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
    """909's: when the fastest bone peaks"""
    L = length(anim); n = 30
    names = APE.get_bone_names(APE.get_anim_pose_at_time(anim, 0.0, o_))
    pts = [[APE.get_bone_pose(p, b, unreal.AnimPoseSpaces.WORLD).translation for b in names] for p in (APE.get_anim_pose_at_time(anim, L * k / n, o_) for k in range(n + 1))]
    sp = [max((pts[k + 1][i] - pts[k][i]).length() for i in range(len(names))) / (L / n) for k in range(n)]
    sm = [sum(sp[max(0, k - 1):k + 2]) / len(sp[max(0, k - 1):k + 2]) for k in range(n)]
    k = max(range(n), key=lambda i: sm[i])
    return min(max(L * (k + 0.5) / n, 0.15), L - 0.1)


_packs = {}
def clip(pack, n):
    if pack not in _packs:
        flt = unreal.ARFilter(package_paths=[pack], class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "AnimSequence")], recursive_paths=True)
        _packs[pack] = {}
        for a in AR.get_assets(flt): _packs[pack].setdefault(str(a.asset_name), str(a.package_name))
    a = unreal.load_asset(_packs[pack][n]) if n in _packs[pack] else None
    assert a, (pack, n)
    return a


_mats = {}
def mat_named(root, name):
    """a material of that name anywhere under the pack's root"""
    if root not in _mats:
        _mats[root] = {}
        for cls in ("Material", "MaterialInstanceConstant"):
            flt = unreal.ARFilter(package_paths=[root], class_paths=[unreal.TopLevelAssetPath("/Script/Engine", cls)], recursive_paths=True)
            for a in AR.get_assets(flt): _mats[root].setdefault(str(a.asset_name), str(a.package_name))
    p = _mats[root].get(name)
    return unreal.load_asset(p) if p else None


def variant(sk, n):
    """the mesh's materials slot by slot, each swapped for the pack's colour set n where it has one (M_X_1 -> M_X_n, M_X_01 -> M_X_0n,
    M_X -> M_X_Set_0n); the slots changed"""
    root = "/" + "/".join(sk.get_path_name().split("/")[1:3])
    out, changed = [], []
    for sm in sk.get_editor_property("materials"):
        mi = sm.get_editor_property("material_interface")
        new = None
        if mi:
            nm = mi.get_name()
            m = re.match(r"^(.*?)(\d+)$", nm)
            cands = []
            if m: cands.append(m.group(1) + str(n).zfill(len(m.group(2))))
            cands.append(nm + "_Set_%02d" % n)
            for c in cands:
                if c != nm:
                    new = mat_named(root, c)
                    if new: break
        out.append(new or mi)
        if new: changed.append(f"{mi.get_name()}->{new.get_name()}")
    return out, changed


def monsters():
    les.load_level(DST)
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    MJ = json.load(open(os.path.join(SA, "monsters.json"), encoding="utf-8"))
    DJ = json.load(open(os.path.join(SA, "defenders25.json"), encoding="utf-8"))
    guns = dict(MJ["guns"]); guns.update(DJ["guns_extra"])
    snd_keys = {str(k) for k in gen.get_editor_property("sounds").keys()}
    heal_fx = unreal.load_asset(DJ["heal_fx"])
    names = {e["name"] for e in DJ["monsters"]}; old = {e["name"] for e in MJ["monsters"]}
    all_mons = list(gen.get_editor_property("monsters"))
    keep = [m for m in all_mons if str(m.get_editor_property("name")) not in names]
    added, rows = [], []
    for e in DJ["monsters"]:
        sk = unreal.load_asset(e["mesh"]); assert sk, e["mesh"]
        pk = e["pack"]
        idle = clip(pk, e["idle"]); walk = clip(pk, e["walk"]); hit = clip(pk, e["hit"]); death = clip(pk, e["death"]); shot = clip(pk, e["shot"])
        att = [clip(pk, a) for a in e["attacks"]]
        s = sk.skeleton
        for cs in {c.get_editor_property("skeleton").get_path_name(): c.get_editor_property("skeleton") for c in [idle, walk, hit, death, shot] + att}.values():
            if cs != s and not any(x == cs for x in s.get_editor_property("compatible_skeletons")):
                s.add_compatible_skeleton(cs); eal.save_loaded_asset(s, only_if_is_dirty=False)
        sc = float(e.get("scale", 1.0))
        b = sk.get_bounds(); ext = b.box_extent; org = b.origin
        zmin = (org.z - ext.z) * sc
        hv = e.get("hover")
        hh = max(40.0, min(ext.z * sc, 160.0)) if not hv else max(40.0, min(ext.z * sc, 90.0)); rad = min(90.0, max(28.0, min(ext.x, ext.y) * 0.8 * sc))
        spd = (clip_speed(walk) if (walk != idle and not hv) else None) or 150.0
        d = unreal.RDMonsterDef(); d.name = e["name"]; d.title = e["title"]; d.mesh = sk; d.idle = idle; d.walk = walk
        d.walk_clip_speed = max(spd * sc, 60.0); d.walk_speed = max(90.0, min(220.0, spd * sc))
        d.capsule_radius = rad; d.capsule_half_height = hh
        d.mesh_z = -hh - zmin - float(e.get("drop", 0.0)); d.mesh_yaw = -90.0; d.scale = sc; d.weight = float(e.get("weight", 2))
        d.death_drop = float(e.get("death_drop", 0.0))
        ft = DJ.get("feet", {}).get(e["name"])
        if ft: d.mesh_z = d.mesh_z - float(ft["bottom"])          # (its measured feet onto the floor)
        d.attacks = att; d.hit_times = [blow_time(a) for a in att]; d.get_hit = hit; d.death = death
        f = 1.2 if e["tier"] >= 4 else 1.0
        if "Mech" in e["name"]: f *= 1.3
        if hv: f *= 0.7
        d.health_factor = f; d.damage_factor = 1.2 if e["tier"] >= 4 else 1.0
        d.reach = round(70.0 + 0.9 * rad); d.attack_interval = 1.8
        snd = e["sound"] if any(k.startswith("Monster.%s." % e["sound"]) for k in snd_keys) else "Horned"
        d.sound_set = snd; d.step_length = round(40.0 + 0.25 * ext.z * 2 * sc)
        d.tier = e["tier"]; d.ability = ABIL[e["ability"]]
        # (a colour or design of its own: the pack's numbered set, slot by slot)
        ch = []
        if e.get("variant"):
            mats, ch = variant(sk, int(e["variant"]))
            assert ch, ("no variant materials for", e["name"], e["variant"])
            d.set_editor_property("materials", mats)
        if hv:
            d.hover_height = float(hv["height"]); d.hover_bob = float(hv.get("bob", 10)); d.hover_period = float(hv.get("period", 2.0))
        r = e.get("ranged")
        d.shoots = bool(r)
        if r:
            kind = r["range"]; gun = guns[r["gun"]]
            d.ranged_range = float(MJ["ranges"][kind]); d.ranged_min = float(MJ["ranges"]["min"])
            d.ranged_damage = float(MJ["damage"][kind]); d.ranged_cooldown = float(MJ["cooldown"][kind]) * d.attack_interval
            d.ranged_speed = float(MJ["speed"][kind])
            d.ranged_fx = unreal.load_asset(gun["projectile"]); d.ranged_muzzle_fx = unreal.load_asset(gun["muzzle"]); d.ranged_hit_fx = unreal.load_asset(gun["hit"])
            d.ranged_fx_scale = 1.0; d.ranged_theme = gun["theme"]
            d.ranged_clip = shot; d.ranged_release = min(blow_time(shot), 0.5)
        hl = e.get("heals")
        if hl:
            d.heals = True; d.heal_range = float(hl["range"]); d.heal_share = float(hl["share"]); d.heal_below = float(hl["below"]); d.heal_cooldown = float(hl["cooldown"])
            hc = clip(pk, hl["clip"]); d.heal_clip = hc; d.heal_release = round(min(0.8, max(0.3, blow_time(hc) / max(length(hc), 0.1))), 2)
            d.heal_fx = heal_fx; d.heal_fx_scale = 1.0
        added.append(d)
        rows.append([e["name"], e["tier"], round(ext.z * 2 * sc), round(rad), round(hh), round(spd), snd, len(ch), bool(r), bool(hl), bool(hv)])
    # (the castle's kinds' weights cut so the defenders (909's and these) are two in three of each tier)
    defs = [m for m in keep if str(m.get_editor_property("name")) in old] + added
    castle = [m for m in keep if str(m.get_editor_property("name")) not in old and float(m.get_editor_property("weight")) > 0]
    mw = {}
    for d in defs: mw[int(d.tier)] = mw.get(int(d.tier), 0.0) + float(d.weight)
    by_t = {}
    for m in castle: by_t.setdefault(int(m.get_editor_property("tier")), []).append(m)
    for t, ms in by_t.items():
        if t in mw and ms:
            for m in ms: m.set_editor_property("weight", round(mw[t] * 0.5 / len(ms), 3))
    # (909's kinds' feet: from the MeshZ they were measured with, so a second run moves nothing)
    fixed = {}
    for m in keep:
        ft = DJ.get("feet", {}).get(str(m.get_editor_property("name")))
        if ft and "mesh_z" in ft:
            m.set_editor_property("mesh_z", float(ft["mesh_z"]) - float(ft["bottom"])); fixed[str(m.get_editor_property("name"))] = round(float(ft["mesh_z"]) - float(ft["bottom"]), 1)
    print("947 909's kinds' feet:", fixed)
    gen.set_editor_property("monsters", keep + added)
    gen.modify(); les.save_current_level()
    print("947 monsters", DST, "| added", len(added), "| defenders by tier", {t: round(w, 1) for t, w in sorted(mw.items())},
          "| castle kinds weighted", len(castle))
    for r_ in rows: print("947  ", r_)


arg = sys.argv[1] if len(sys.argv) > 1 else "monsters"
if arg == "monsters": monsters()
else: raise SystemExit("947: monsters")
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
