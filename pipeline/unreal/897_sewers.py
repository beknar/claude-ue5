"""sewers: The Sewers of Graymourne, under the port's sluice house (the user's spec of 2026-11-07, docs/graymourne.txt: "the
dungeon is located in the sewers. take a sewer entrance to get there"; their choice: the project's monsters). A Save As copy of
mistward_castle (its heroes, balance, loot, traps, special rooms and bosses) with:
- its floors going down, as Vel Morrath's catacombs (bTierFloors: each tier 4.5 m under the one before, ramps between)
- its own counters and record (DungeonKey "sewers"), its name (DungeonTitle), the town it comes back to (TownLevel
  brokenspire: the way out puts her before the sluice house's door, the game instance's ReturnAt / ReturnTown)
- its looks by tier (TierThemes): tiers 1, 2 and 4 the sewer's brick ("Sewer": the Sewer pack's brick walls and concrete
  floors), tier 3 the founders' vaulted cistern (the castle's "Castle" theme), tier 5 both mixed; the drowned things by every
  room's walls (ThemeProps: sludge, rags, rubbish, dead men, barrels, crates and ropes washed down from the ships)
- the drowned (SourceArt/sewers/monsters.json): measured as 895 measures the machines and added to the castle's kinds; the
  castle's kinds' weight lowered so that two in three monsters of a tier are these; a kind with no fighting clips of its own
  plays the Fantasy Pack's (its skeleton made compatible, saved)
- no final boss (Aurorim is Mistward Castle's), no menu (it is entered from the sluice house with her hero)
Run as `897 saveas` (it saves the copy and quits the editor: a copied map is opened only after a restart), then, the editor
started again, `897` (it sets the copy up, builds its start section and saves it). Args: [saveas]"""
import sys, os, json, math, unreal
SRC, DST = "/Game/RandomDungeon/Maps/mistward_castle", "/Game/RandomDungeon/Maps/sewers"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\sewers"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
APE = unreal.AnimPoseExtensions; o_ = unreal.AnimPoseEvaluationOptions()
V = unreal.Vector
YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
FACE = 25.0
ABIL = {"None": unreal.RDMonsterAbility.NONE, "Poison": unreal.RDMonsterAbility.POISON, "Weaken": unreal.RDMonsterAbility.WEAKEN, "Slow": unreal.RDMonsterAbility.SLOW}


def corners(b): return [V(x, y, z) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]


def piece(path, front="+x", mode="center", scale=(1, 1, 1), collision=True, fit=None):
    """895's normalisation; fit: (x, y) the footprint to scale it to"""
    m = unreal.load_asset(path)
    assert m, path
    if isinstance(scale, (int, float)): scale = (scale,) * 3
    rot = unreal.Rotator(roll=180.0 if mode == "ceil" else 0.0, pitch=0.0, yaw=YAW[front])
    if fit:
        t1 = unreal.Transform(V(0, 0, 0), rot, V(1, 1, 1))
        pts = [unreal.MathLibrary.transform_location(t1, c) for c in corners(m.get_bounding_box())]
        sx = fit[0] / max(max(p.x for p in pts) - min(p.x for p in pts), 1.0); sy = fit[1] / max(max(p.y for p in pts) - min(p.y for p in pts), 1.0)
        scale = (sx, sy, 1.0)
    sc = V(*scale)
    t0 = unreal.Transform(V(0, 0, 0), rot, sc)
    pts = [unreal.MathLibrary.transform_location(t0, c) for c in corners(m.get_bounding_box())]
    mn = V(min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)); mx = V(max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
    tx, ty, tz = -(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z
    if mode == "floor": tz = -mx.z
    elif mode == "wallface": tx = FACE - mx.x
    p = unreal.RDPiece(); p.mesh = m; p.adjust = unreal.Transform(V(tx, ty, tz), rot, sc)
    p.size = V(mx.x - mn.x, mx.y - mn.y, mx.z - mn.z); p.collision = collision
    return p


def length(a): return unreal.AnimationLibrary.get_sequence_length(a)


def clip_speed(anim):
    """859's: the ground speed of a walk clip from its lowest bones while they are planted"""
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
    """859's: when the fastest bone peaks"""
    L = length(anim); n = 30
    names = APE.get_bone_names(APE.get_anim_pose_at_time(anim, 0.0, o_))
    pts = [[APE.get_bone_pose(p, b, unreal.AnimPoseSpaces.WORLD).translation for b in names] for p in (APE.get_anim_pose_at_time(anim, L * k / n, o_) for k in range(n + 1))]
    sp = [max((pts[k + 1][i] - pts[k][i]).length() for i in range(len(names))) / (L / n) for k in range(n)]
    sm = [sum(sp[max(0, k - 1):k + 2]) / len(sp[max(0, k - 1):k + 2]) for k in range(n)]
    k = max(range(n), key=lambda i: sm[i])
    return min(max(L * (k + 0.5) / n, 0.15), L - 0.1)


if len(sys.argv) > 1 and sys.argv[1] == "saveas":
    assert not eal.does_asset_exist(DST), "sewers exists: set it up with 897 (no argument)"
    if not ues.get_editor_world().get_path_name().startswith(SRC + "."): les.load_level(SRC)
    ok = unreal.EditorLoadingAndSavingUtils.save_map(ues.get_editor_world(), DST)
    print("SEW saved as", DST, ok, "| quitting: start the editor again and run 897")
    unreal.SystemLibrary.quit_editor()
else:
    if not ues.get_editor_world().get_path_name().startswith(DST + "."): les.load_level(DST)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(DST + "."), w.get_path_name()
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    # ------------------------------------------------------------ the sewer's brick (the Sewer pack: a 200 x 3 x 200 panel faced
    # +y, made 300 x 300; its concrete floor tile, 200 x 200, made a tile; the same tile turned over for the ceilings)
    K = "/Game/Sewer/Meshes/"
    P = {}
    # (damp: the pack's clean cream brick and pale concrete read as a lit hall under the castle's torches (884 gd1's picture);
    # copies of their instances, darkened toward green-grey and wetter, made here as 894's soot stone)
    MEL = unreal.MaterialEditingLibrary; MD = "/Game/RandomDungeon/Materials/Sewer"
    def damp(name, parent, tint, rough):
        path = MD + "/" + name
        if not eal.does_asset_exist(path):
            unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MD, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mi = unreal.load_asset(path)
        MEL.set_material_instance_parent(mi, unreal.load_asset(parent))
        MEL.set_material_instance_vector_parameter_value(mi, "Albedo tint", unreal.LinearColor(*tint, 1.0))
        MEL.set_material_instance_scalar_parameter_value(mi, "Roughness Strength", rough)
        MEL.update_material_instance(mi); eal.save_loaded_asset(mi, False)
        return mi
    BRICK = damp("MI_Sewer_DampBrick", K + "Kit_Brick/MI_Brick_Kit", (0.36, 0.40, 0.32), 0.55)
    CONC = damp("MI_Sewer_DampFloor", K + "Kit_Concrete/Floor/MI_SMI_Sewer_Floor_01a", (0.34, 0.37, 0.30), 0.45)
    wb = piece(K + "Kit_Brick/SM_Sewer_Wall_Brick_01a", front="+y", mode="wallface", scale=(1.5, 1.0, 1.5)); wb.material = BRICK
    for n in ("Wall_Block", "Wall_Stone", "Wall_Corr", "Wall_Rough", "Wall_Rough_2", "Wall_Rough_3"): P["Sewer." + n] = wb
    f1 = piece(K + "Kit_Concrete/Floor/SM_Sewer_Floor_01a", front="+x", mode="floor", fit=(300, 300)); f1.material = CONC
    for n in ("Floor_Stone", "Floor_Brick", "Floor_Brick2", "Floor_Random", "Floor_Tiles", "Floor_Wood", "Floor_Corr"):
        P["Sewer." + n] = f1; P["Sewer." + n + "_Alt"] = f1
    P["Sewer.Ceil_Room"] = piece(K + "Kit_Concrete/Floor/SM_Sewer_Floor_01a", front="+x", mode="ceil", fit=(300, 300)); P["Sewer.Ceil_Room"].material = CONC
    P["Sewer.Ceil_Corr"] = P["Sewer.Ceil_Room"]
    # ------------------------------------------------------------ what the water left by the walls
    UO = "/Game/Underwater_odyssey/Mesh/SK_SM/"
    PROPS = {
        "Drowned.Sludge": piece(K + "Mud/SM_Sewer_Mud_01a", collision=False),
        "Drowned.Sludge2": piece(K + "Mud/SM_Sewer_Mud_01b", collision=False),
        "Drowned.Rag": piece(K + "Rags_and_Crumpled_Paper/SM_Rag_01a", collision=False),
        "Drowned.Trash": piece(K + "Trashbags/SM_Trash_Bag_01a"),
        "Drowned.Dead": piece("/Game/PiratesAge/VOL5_Prisioners/Meshes/LP/SM_Dead_Pirate_01c", collision=False),
        "Drowned.Dead2": piece("/Game/PiratesAge/VOL5_Prisioners/Meshes/LP/SM_Dead_Pirate_01d", collision=False),
        "Drowned.Barrel": piece(UO + "SM_Barrel"),
        "Drowned.Box": piece(UO + "SM_Box"),
        "Drowned.Ropes": piece(UO + "SM_Ropes", collision=False),
    }
    P.update(PROPS)
    pieces = dict(gen.get_editor_property("pieces"))
    for k in [k for k in pieces if str(k).startswith(("Sewer.", "Drowned."))]: del pieces[k]
    for k, p in P.items(): pieces[unreal.Name(k)] = p
    gen.set_editor_property("pieces", pieces)
    gen.set_editor_property("tier_themes", [unreal.Name(n) for n in ("Sewer", "Sewer", "Castle", "Sewer", "Mixed")])
    gen.set_editor_property("mixed_themes", [unreal.Name(n) for n in ("Sewer", "Castle")])
    gen.set_editor_property("theme_props", [unreal.Name(n) for n in ("Drowned.Sludge", "Drowned.Sludge2", "Drowned.Rag", "Drowned.Trash", "Drowned.Dead", "Drowned.Dead2", "Drowned.Barrel", "Drowned.Box", "Drowned.Ropes", "Drowned.Sludge")])
    gen.set_editor_property("theme_prop_spacing", 450.0); gen.set_editor_property("theme_prop_chance", 0.35)
    for k, v in (("tier_floors", True), ("tier_floor_depth", 450.0), ("stair_tiles", 4), ("dungeon_key", "sewers"), ("dungeon_title", "The Sewers of Graymourne"),
                 ("town_level", "/Game/RandomDungeon/Maps/brokenspire"), ("catacombs_level", ""), ("final_boss_on", False), ("menu_level", "")):
        try: gen.set_editor_property(k, v)
        except Exception as e: print("SEW (no", k, ")", e)
    # ------------------------------------------------------------ the drowned
    MJ = json.load(open(os.path.join(SA, "monsters.json"), encoding="utf-8"))
    fantasy = unreal.load_asset(MJ["fantasy_skeleton"])
    mons = [m for m in gen.get_editor_property("monsters") if not str(m.get_editor_property("name")) in {e["name"] for e in MJ["monsters"]}]
    added = []; rows = []
    for e in MJ["monsters"]:
        sk = unreal.load_asset(e["mesh"])
        assert sk, e["mesh"]
        if e.get("compat") and fantasy:
            s = sk.skeleton
            if s != fantasy and not any("Fantasy_Pack" in str(x) for x in s.get_editor_property("compatible_skeletons")):
                s.add_compatible_skeleton(fantasy); eal.save_loaded_asset(s, only_if_is_dirty=False)
        idle = unreal.load_asset(e["idle"]); walk = unreal.load_asset(e["walk"]); hit = unreal.load_asset(e["hit"]); death = unreal.load_asset(e["death"])
        att = [unreal.load_asset(a) for a in e["attacks"]]; att = [a for a in att if a]
        assert idle and walk and hit and death and att, e["name"]
        sc = float(e.get("scale", 1.0))
        b = sk.get_bounds(); ext = b.box_extent; org = b.origin
        zmin = (org.z - ext.z) * sc
        hh = max(40.0, ext.z * sc); rad = min(90.0, max(28.0, min(ext.x, ext.y) * 0.8 * sc))
        spd = clip_speed(walk) or 150.0
        d = unreal.RDMonsterDef(); d.name = e["name"]; d.title = e["title"]; d.mesh = sk; d.idle = idle; d.walk = walk
        d.walk_clip_speed = max(spd * sc, 60.0); d.walk_speed = max(90.0, min(220.0, spd * sc))
        d.capsule_radius = rad; d.capsule_half_height = hh
        d.mesh_z = -hh - zmin; d.mesh_yaw = -90.0; d.scale = sc; d.weight = float(e.get("weight", 3))
        d.attacks = att; d.hit_times = [blow_time(a) for a in att]; d.get_hit = hit; d.death = death
        f = 1.2 if e["tier"] >= 4 else 1.0
        d.health_factor = f; d.damage_factor = f
        d.reach = round(70.0 + 0.9 * rad); d.attack_interval = 1.9 if hh > 140 else 1.6
        d.sound_set = e["sound"]; d.step_length = round(40.0 + 0.25 * ext.z * 2 * sc)
        d.tier = e["tier"]; d.ability = ABIL[e["ability"]]
        parts = [unreal.load_asset(p) for p in e.get("parts", [])]
        if parts: d.parts = [p for p in parts if p]
        added.append(d)
        rows.append([e["name"], e["tier"], round(ext.z * 2 * sc), round(rad), round(hh), round(spd), [round(h, 2) for h in d.hit_times]])
    # (the castle's kinds lighter: in each tier the drowned's weight twice the castle's together)
    by_t = {}
    for m in mons: by_t.setdefault(int(m.get_editor_property("tier")), []).append(m)
    mw = {}
    for d in added: mw[int(d.tier)] = mw.get(int(d.tier), 0.0) + float(d.weight)
    for t, ms in by_t.items():
        if t in mw and ms:
            for m in ms: m.set_editor_property("weight", round(mw[t] * 0.5 / len(ms), 3))
    gen.set_editor_property("monsters", mons + added)
    gen.modify(); gen.build_start_section()
    les.save_current_level()
    print("SEW", DST, "| floors", gen.get_editor_property("tier_floors"), "| key", gen.get_editor_property("dungeon_key"), "| title", gen.get_editor_property("dungeon_title"),
          "| themes", [str(t) for t in gen.get_editor_property("tier_themes")], "| final boss", gen.get_editor_property("final_boss_on"),
          "| pieces", len(P), "| drowned", rows, "| castle kinds", len(mons))
    del gen, pieces, P, w, mons, added, fantasy
import gc
gc.collect()
