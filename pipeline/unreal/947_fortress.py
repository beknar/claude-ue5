"""The list of 2026-11-22 (docs/improvements16.txt: "vary the Heaven dungeon with soldier variants, medics, differently colored/designed
drones and differently colored/designed mechs from the Dystopia and Sci-fi packs. also use aliens and monsters from the Aliens Warrior
Pack"; the plan docs/improvements16_plan.md), the fortress under Kratos Aurorim Research (`heaven_fortress`, 909), its phases 25 to 27:

    947_fortress.py monsters   phase 25: the defenders of SourceArt/heaven_fortress/defenders25.json added to 909's five (each a kind:
                               its clips found by name under its pack, its mesh's skeleton made compatible with them, measured as 909
                               measures; a colour variant's materials slot by slot from the pack's numbered set; a medic's heal (C++
                               RD/RDFortress25.cpp); a drone's hover); the castle's kinds' weights cut so the defenders are two in three
                               of each tier. Run 910 and 905 after it (they copy every dungeon's kinds to every map and give them their
                               wild bands), and again after any stage that writes the castle's monsters.
    947_fortress.py building   phase 26: tiers 1 and 2 an office building (TierThemes "Office"): its walls (plaster over a wood or plaster
                               dado, a steel skirting), terrazzo, wood and grey floors, white ceilings with light panels (boxes merged in
                               Heaven's and Office_Environment's materials); the castle's furniture as Heaven's modern pieces of the same
                               names (brokenspire's, as text) with their containers' words; the machines by the walls as the tower's
                               office things (printers, water dispensers, shelving, planters, drawers); the start section built again

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
    M_X -> M_X_Set_0n): looked for in the material's own folder, then its parents' up to the pack's (PR #132's review: the whole pack
    held other models' materials of the same name); only a number after an underscore, of one or two digits"""
    out, changed = [], []
    for sm in sk.get_editor_property("materials"):
        mi = sm.get_editor_property("material_interface")
        new = None
        if mi:
            nm = mi.get_name()
            m = re.match(r"^(.*_)(\d{1,2})$", nm)
            cands = []
            if m: cands.append(m.group(1) + str(n).zfill(len(m.group(2))))
            cands.append(nm + "_Set_%02d" % n)
            parts = mi.get_path_name().split(".")[0].split("/")[:-1]
            for depth in range(len(parts), 2, -1):
                folder = "/".join(parts[:depth])
                for c in cands:
                    if c != nm:
                        new = mat_named(folder, c)
                        if new: break
                if new: break
        out.append(new or mi)
        if new: changed.append(f"{mi.get_path_name().split('.')[0]} -> {new.get_path_name().split('.')[0]}")
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
        for c_ in ch: print("947   variant", e["name"], c_)
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


# ================================================================================================ phase 26: tiers 1 and 2 an office building
WILD = "/Game/RandomDungeon/Maps/brokenspire"
YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
FACE = 25.0
V = unreal.Vector


def corners(b): return [V(x, y, z) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]


def piece(m, front="+x", mode="center", collision=True, lift=0.0, height=None):
    """909's normalisation (front to +X; a wall's face at FACE, a floor's top at 0, a ceiling turned over), with 948's lift and height"""
    rot = unreal.Rotator(roll=180.0 if mode == "ceil" else 0.0, pitch=0.0, yaw=YAW[front])
    b = m.get_bounding_box()
    sc = 1.0 if height is None else height / max(b.max.z - b.min.z, 1.0)
    t0 = unreal.Transform(V(0, 0, 0), rot, V(sc, sc, sc))
    pts = [unreal.MathLibrary.transform_location(t0, c) for c in corners(b)]
    mn = V(min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)); mx = V(max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
    tx, ty, tz = -(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z + lift
    if mode == "floor": tz = -mx.z
    elif mode == "wallface": tx = FACE - mx.x
    p = unreal.RDPiece(); p.mesh = m; p.adjust = unreal.Transform(V(tx, ty, tz), rot, V(sc, sc, sc))
    p.size = V(mx.x - mn.x, mx.y - mn.y, mx.z - mn.z); p.collision = collision
    return p


def find_mesh(name, pack):
    flt = unreal.ARFilter(package_paths=["/Game/" + pack], recursive_paths=True, class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh")])
    hits = [a for a in AR.get_assets(flt) if str(a.asset_name) == name]
    assert hits, (name, pack)
    return unreal.load_asset(str(hits[0].package_name) + "." + name)


def building():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import importlib, heaven_kit as hk
    importlib.reload(hk)
    # ---- the castle's furniture names the fortress has, and Heaven's modern pieces of the same names (brokenspire's, as text)
    les.load_level(DST)
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    plain = [str(k) for k in g.get_editor_property("pieces").keys() if "." not in str(k)]
    del g; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    les.load_level(WILD)
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    hp = g.get_editor_property("pieces")
    texts = {n: hp[unreal.Name("Heaven." + n)].export_text() for n in plain if unreal.Name("Heaven." + n) in hp}
    words = {str(k)[7:]: str(v) for k, v in g.get_editor_property("container_words21").items() if str(k).startswith("Heaven.")}
    del g, hp; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    les.load_level(DST)
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    MAT = dict(hk.materials())
    OE = "Office_Environment"
    def mi(n):
        flt = unreal.ARFilter(package_paths=["/Game/" + OE], recursive_paths=True, class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "MaterialInstanceConstant")])
        hits = [a for a in AR.get_assets(flt) if str(a.asset_name) == n]
        assert hits, n
        return unreal.load_asset(str(hits[0].package_name) + "." + n)
    MAT.update({"plaster": mi("MI_White_Painted_Plaster"), "terrazzo": mi("MI_Terrazzo_Floor"), "wood": mi("MI_MT00026-Clean_Gray_Wood"), "carpetgrey": mi("MI_Soft_Granite_Floor")})
    H = 151.0
    def wall(name, dado):
        # (the room's face +X: a steel skirting, a dado of wood or plaster to 1 m, white plaster above, a white cornice; pilasters at the ends)
        return hk.boxes(name, [(-40, 0, -H, H, 0, 600, "plaster"), (-40, 2, -H, H, 0, 14, "steel"), (-40, 1.5, -H, H, 14, 100, dado),
                               (-40, 1.5, -H, H, 100, 104, "steel"), (-40, 3, -H, -145, 0, 560, "white"), (-40, 3, 145, H, 0, 560, "white"),
                               (-40, 4, -H, H, 560, 600, "white")], MAT, False)
    w1 = wall("SM_HVO_Wall", "wood"); w2 = wall("SM_HVO_WallPlain", "plaster")
    P = {}
    for n, w in (("Wall_Block", w1), ("Wall_Stone", w2), ("Wall_Corr", w2), ("Wall_Rough", w1), ("Wall_Rough_2", w2), ("Wall_Rough_3", w1), ("Wall_Rough_4", w2), ("Wall_Rough_5", w1)):
        P["Office." + n] = piece(w, mode="wallface")
    f1 = piece(hk.boxes("SM_HVO_Floor", [(-H, H, -H, H, -20, 0, "terrazzo")], MAT, False), mode="floor")
    f2 = piece(hk.boxes("SM_HVO_FloorWood", [(-H, H, -H, H, -20, 0, "wood")], MAT, False), mode="floor")
    f3 = piece(hk.boxes("SM_HVO_FloorCarpet", [(-H, H, -H, H, -20, 0, "carpetgrey")], MAT, False), mode="floor")
    for n in ("Floor_Stone", "Floor_Brick", "Floor_Brick2", "Floor_Random", "Floor_Tiles", "Floor_Corr"):
        P["Office." + n] = f1; P["Office." + n + "_Alt"] = f3
    P["Office.Floor_Wood"] = f2; P["Office.Floor_Wood_Alt"] = f2
    P["Office.Ceil_Room"] = piece(hk.boxes("SM_HVO_Ceil", [(-H, H, -H, H, 0, 15, "white"), (-70, 70, -70, 70, 15, 16.5, "panel"), (-H, H, -1, 1, 15, 15.6, "steel"), (-1, 1, -H, H, 15, 15.6, "steel")], MAT, False), mode="ceil")
    P["Office.Ceil_Corr"] = P["Office.Ceil_Room"]
    # ---- the furniture: Heaven's modern pieces under the castle's names (never over the shell's own pieces)
    for n, txt in texts.items():
        if ("Office." + n) in P: continue
        p = unreal.RDPiece(); p.import_text(txt); P["Office." + n] = p
    # ---- the castle's pieces an office has no use for: each given an office's own in the box the castle's takes (its mesh's box through
    # its Adjust), or left out (the gibbets, cages, bones, hay, tombs, weapons on the walls)
    cp = g.get_editor_property("pieces")
    def box_of(n):
        q = cp[unreal.Name(n)]
        pts = [unreal.MathLibrary.transform_location(q.adjust, c) for c in corners(q.mesh.get_bounding_box())]
        return (min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts), min(p.z for p in pts), max(p.z for p in pts)), q
    def raw(m, like, collision=True):
        p = unreal.RDPiece(); p.mesh = m; p.adjust = unreal.Transform(); p.size = like.size; p.collision = collision
        p.hinge = like.hinge
        return p
    (x0, x1, y0, y1, z0, z1), dw = box_of("Doorway")
    (x0_, x1_, y0_, y1_, z0_, z1_), dl0 = box_of("DoorLeaf")
    ow = float(dl0.hinge.y) + 5.0          # (half the opening: from the leaves' hinges (PR #133's review), and a margin)
    P["Office.Doorway"] = raw(hk.boxes("SM_HVO_Doorway", [(x0, x1, y0, -ow, z0, z1, "plaster"), (x0, x1, ow, y1, z0, z1, "plaster"), (x0, x1, -ow, ow, 230, z1, "plaster"),
                                                           (x0 - 1, x1 + 1, -ow - 6, -ow, z0, 236, "steel"), (x0 - 1, x1 + 1, ow, ow + 6, z0, 236, "steel"), (x0 - 1, x1 + 1, -ow, ow, 230, 236, "steel")], MAT, False), dw)
    (x0, x1, y0, y1, z0, z1), dl = box_of("DoorLeaf")
    P["Office.DoorLeaf"] = raw(hk.boxes("SM_HVO_DoorLeaf", [(x0, x1, y0, y1, z0, z1, "glass"), (x0 - 0.5, x1 + 0.5, y0, y0 + 5, z0, z1, "steel"), (x0 - 0.5, x1 + 0.5, y1 - 5, y1, z0, z1, "steel"),
                                                            (x0 - 0.5, x1 + 0.5, y0, y1, z0, z0 + 8, "steel"), (x0 - 0.5, x1 + 0.5, y0, y1, z1 - 5, z1, "steel")], MAT, False), dl)
    for n, parts in (("Column", lambda b: [(b[0], b[1], b[2], b[3], b[4], b[5], "white"), (b[0] - 2, b[1] + 2, b[2] - 2, b[3] + 2, b[4], b[4] + 14, "steel")]),
                     ("CornerColumn", lambda b: [(b[0], b[1], b[2], b[3], b[4], b[5], "white")]),
                     ("Dais", lambda b: [(b[0], b[1], b[2], b[3], b[4], b[5] - 3, "white"), (b[0], b[1], b[2], b[3], b[5] - 3, b[5], "steel")]),
                     ("Carpet", lambda b: [(b[0], b[1], b[2], b[3], 0, 2, "carpetgrey")]), ("CarpetLong", lambda b: [(b[0], b[1], b[2], b[3], 0, 2, "carpetgrey")])):
        bb, like = box_of(n)
        P["Office." + n] = raw(hk.boxes("SM_HVO_" + n, parts(bb), MAT, False), like, n not in ("Carpet", "CarpetLong"))
    # (the cells, the gratings and the tiers' seals: steel frames round glass in the castle pieces' boxes, their collision theirs; the
    # cell's door a glass leaf on the castle's hinge (PR #133's review: they stood in castle iron))
    def panel(b):
        return [(b[0], b[1], b[2], b[3], b[4], b[5], "glass"), (b[0] - 1, b[1] + 1, b[2], b[2] + 6, b[4], b[5], "steel"), (b[0] - 1, b[1] + 1, b[3] - 6, b[3], b[4], b[5], "steel"),
                (b[0] - 1, b[1] + 1, b[2], b[3], b[4], b[4] + 8, "steel"), (b[0] - 1, b[1] + 1, b[2], b[3], b[5] - 6, b[5], "steel")]
    for n in ("CellFrame", "CellBlock", "CellBlockHalf", "Grating", "CellDoor"):
        if unreal.Name(n) not in cp or not cp[unreal.Name(n)].mesh: continue
        bb, like = box_of(n)
        q = raw(hk.boxes("SM_HVO_" + n, panel(bb), MAT, False), like)
        if like.moving: q.moving = like.moving
        P["Office." + n] = q
    for n, mk in (("ShrinePlinth", "white"), ("Wall_Rough_Back", "plaster")):
        if unreal.Name(n) not in cp or not cp[unreal.Name(n)].mesh: continue
        bb, like = box_of(n)
        P["Office." + n] = raw(hk.boxes("SM_HVO_" + n, [(bb[0], bb[1], bb[2], bb[3], bb[4], bb[5], mk)], MAT, False), like)
    if "Bench" in texts and "Pew" not in texts:
        p = unreal.RDPiece(); p.import_text(texts["Bench"]); P["Office.Pew"] = p
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    for n in ("Books", "Gibbet", "CageHanging", "CageLarge", "Chain", "Shackles", "Bones", "BonePile", "BonePile2", "HayPile", "Firewood", "Debris", "Tomb1", "Tomb2", "Tomb3", "Tomb4",
              "Crystal", "Spear", "SpearFlat", "Axe", "AxeFlat", "Sword", "SwordFlat"):
        if unreal.Name(n) not in cp: continue
        h = unreal.RDPiece(); h.mesh = cube; h.adjust = unreal.Transform(V(0, 0, -100000), unreal.Rotator(), V(0.001, 0.001, 0.001)); h.size = V(1, 1, 1); h.collision = False; h.hidden = True
        P["Office." + n] = h
    if "Chest" in texts:
        p = unreal.RDPiece(); p.import_text(texts["Chest"]); P["Office.Trunk"] = p; words["Trunk"] = words.get("Chest", "safe"); texts["Trunk"] = texts["Chest"]
    # ---- the props by the walls (the fortress's machines' names: an office's things in their place) from the tower's table
    TJ = json.load(open(os.path.join(SA, "..", "heaven_tower", "tower24.json"), encoding="utf-8"))["pieces"]
    def tp(nm):
        e = TJ[nm]; return piece(find_mesh(e["mesh"], e["pack"]), e["front"], "center", bool(e.get("collision", True)), float(e.get("lift", 0.0)), e.get("height"))
    for fort, tw in (("Server", "Tower.Printer"), ("Chiller", "Tower.WaterDispenser"), ("Rack", "Tower.Shelving"), ("Generator", "Tower.Planter"),
                     ("PowerBox", "Tower.Drawers"), ("Cabinet", "Tower.StorageShelving")):
        P["Office.Fortress." + fort] = tp(tw)
    # (and the castle's furniture an office reads as other things: the brazier and the plinth planters, the altar a desk, the thrones a
    # chair, the stool a chair, the tool board a cork board, the banner and painting a picture)
    for n, tw in (("ShrineStatue", "Tower.WaterDispenser"), ("Brazier", "Tower.Planter"), ("Pedestal", "Tower.PlanterBox"), ("Altar", "Tower.Desk"), ("Throne", "Tower.OfficeChair"), ("ThroneRoyal", "Tower.OfficeChair"),
                  ("Stool", "Tower.Chair"), ("ToolBoard", "Tower.CorkBoard"), ("Banner", "Tower.Painting"), ("Painting", "Tower.Painting")):
        if n not in texts: P["Office." + n] = tp(tw)
    pieces = dict(g.get_editor_property("pieces"))
    for k in [k for k in pieces if str(k).startswith("Office.")]: del pieces[k]
    for k, p in P.items(): pieces[unreal.Name(k)] = p
    g.set_editor_property("pieces", pieces)
    cw = dict(g.get_editor_property("container_words21"))
    for k in [k for k in cw if str(k).startswith("Office.")]: del cw[k]
    for n, wd in words.items():
        if n in texts: cw[unreal.Name("Office." + n)] = wd
    g.set_editor_property("container_words21", cw)
    tt = [str(t) for t in g.get_editor_property("tier_themes")]
    tt[0] = "Office"; tt[1] = "Office"
    g.set_editor_property("tier_themes", [unreal.Name(t) for t in tt])
    g.modify(); g.build_start_section()
    les.save_current_level()
    print("947 building", DST, "| office pieces", len(P), "| Heaven's furniture under the castle's names", sorted(texts), "| words", {n: words[n] for n in words if n in texts},
          "| themes", tt)


arg = sys.argv[1] if len(sys.argv) > 1 else "monsters"
if arg == "monsters": monsters()
elif arg == "building": building()
else: raise SystemExit("947: monsters | building")
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
