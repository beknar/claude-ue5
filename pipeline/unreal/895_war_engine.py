"""war_engine: The War Engine, the factory under Ashenreach's Great Foundry (the user's spec of 2026-11-07, docs/ashenreach.txt:
"the dungeon is located in a besieged factory ... The War Engine - industrial themed build, lots of mechanical monsters,
half-mechanical monsters"; their choice: the project's own monsters). A Save As copy of mistward_castle (its heroes, balance,
loot, traps, special rooms and bosses; its halls spread out by tier as the castle's) with:
- its own counters and record (DungeonKey "war_engine"), its name (DungeonTitle), the town it comes back to (TownLevel
  brokenspire: the way out puts her before the foundry's door, the game instance's ReturnAt / ReturnTown)
- its looks by tier (TierThemes): tiers 1 and 2 the foundry's brick ("Foundry": Dwarven Citadel's brick walls and floor
  tiles), tier 3 the dwarven forge halls ("Dwarf"), tier 4 the brick again, tier 5 both mixed; the factory's props by every room's walls (ThemeProps: rusted gears and chain piles (Junkyard), ore carts
  (Old Mine), anvils, brick kilns, oil barrels (Warehouse))
- its machines (SourceArt/war_engine/monsters.json): measured as 859 measures the gallery's (capsule, walk speed, blows) and
  added to the castle's kinds; the castle's kinds' weight lowered so that two in three monsters of a tier are machines; a
  kind with no fighting clips of its own plays the Fantasy Pack's (its skeleton made compatible, saved)
- no final boss (Aurorim is Mistward Castle's), no menu (it is entered from the foundry with her hero)
Run as `895 saveas` (it saves the copy and quits the editor: a copied map is opened only after a restart), then, the editor
started again, `895` (it sets the copy up, builds its start section and saves it). Args: [saveas]"""
import sys, os, json, math, unreal
SRC, DST = "/Game/RandomDungeon/Maps/mistward_castle", "/Game/RandomDungeon/Maps/war_engine"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\war_engine"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
APE = unreal.AnimPoseExtensions; o_ = unreal.AnimPoseEvaluationOptions()
V = unreal.Vector
YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
FACE = 25.0
ABIL = {"None": unreal.RDMonsterAbility.NONE, "Poison": unreal.RDMonsterAbility.POISON, "Weaken": unreal.RDMonsterAbility.WEAKEN, "Slow": unreal.RDMonsterAbility.SLOW}


def corners(b): return [V(x, y, z) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]


def piece(path, front="+x", mode="center", scale=(1, 1, 1), collision=True, fit=None):
    """864's normalisation (891's), fit: (x, y) the footprint to scale it to"""
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
    assert not eal.does_asset_exist(DST), "war_engine exists: set it up with 895 (no argument)"
    if not ues.get_editor_world().get_path_name().startswith(SRC + "."): les.load_level(SRC)
    ok = unreal.EditorLoadingAndSavingUtils.save_map(ues.get_editor_world(), DST)
    print("WAR saved as", DST, ok, "| quitting: start the editor again and run 895")
    unreal.SystemLibrary.quit_editor()
else:
    if not ues.get_editor_world().get_path_name().startswith(DST + "."): les.load_level(DST)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(DST + "."), w.get_path_name()
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    # ------------------------------------------------------------ the foundry's brick (Dwarven Citadel: 400 x 23 x 401 a wall)
    DW = "/Game/DwarvenCitadel/Meshes/"
    P = {}
    w1 = piece(DW + "SM_ST_BrickWall_05", front="+y", mode="wallface", scale=(0.75, 1, 0.75))
    w2 = piece(DW + "SM_ST_MainHall_BrickWall_06", front="+y", mode="wallface", scale=(0.75, 1, 0.75))
    for n, p in (("Wall_Block", w1), ("Wall_Stone", w2), ("Wall_Corr", w1), ("Wall_Rough", w2), ("Wall_Rough_2", w1), ("Wall_Rough_3", w2)): P["Foundry." + n] = p
    f1 = piece(DW + "SM_ST_FloorTile_04", front="+x", mode="floor", fit=(300, 300))
    f2 = piece(DW + "SM_ST_FloorTile_01", front="+x", mode="floor", fit=(300, 300))
    for n in ("Floor_Stone", "Floor_Brick", "Floor_Brick2", "Floor_Random", "Floor_Tiles", "Floor_Wood", "Floor_Corr"):
        P["Foundry." + n] = f1; P["Foundry." + n + "_Alt"] = f2
    P["Foundry.Ceil_Room"] = piece(DW + "SM_ST_FloorTile_04", front="+x", mode="ceil", fit=(300, 300))
    P["Foundry.Ceil_Corr"] = P["Foundry.Ceil_Room"]
    # ------------------------------------------------------------ the factory's props by the walls
    JY = "/Game/Scene_Junkyard/Assets/MS/3D/"; OM = "/Game/Scene_OldMine/Assets/Megascans/3D_Assets/"; WH = "/Game/Scene_Warehouse/Assets/MS/3D/"
    PROPS = {
        "Engine.Gear": piece(JY + "Ind_Jun_Gear_Metal_Rusty_02/SM_Ind_Jun_Gear_Metal_Rusty_02", scale=9.0),
        "Engine.Chain": piece(JY + "Ind_Fac_Chain_Pile_Metal_Rusty_01/SM_Ind_Fac_Chain_Pile_Metal_Rusty_01"),
        "Engine.Cart": piece(OM + "Ind_Min_Cart_Metal_Old_02/SM_Ind_Min_Cart_Metal_Old_02", front="+y"),
        "Engine.Anvil": piece("/Game/HouseForge_01/Viking_Village_Props/Meshes/Props/BlackSmith/Anvil/sm_Anvil_01a"),
        "Engine.Kiln": piece("/Game/HouseForge_01/Meshes/Misc/SM_Forge", scale=1.2),
        "Engine.Barrel": piece(WH + "Ind_Aba_Storage_Barrel_Metal_Rust_01/SM_Ind_Aba_Storage_Barrel_Metal_Rust_01"),
    }
    P.update(PROPS)
    pieces = dict(gen.get_editor_property("pieces"))
    for k in [k for k in pieces if str(k).startswith(("Foundry.", "Engine."))]: del pieces[k]
    for k, p in P.items(): pieces[unreal.Name(k)] = p
    gen.set_editor_property("pieces", pieces)
    # (tier 1 in the foundry's brick too: with the plain pieces the start set read as Mistward Castle's great hall, banners and
    # all (884 ad1's picture))
    gen.set_editor_property("tier_themes", [unreal.Name(n) for n in ("Foundry", "Foundry", "Dwarf", "Foundry", "Mixed")])
    gen.set_editor_property("mixed_themes", [unreal.Name(n) for n in ("Foundry", "Dwarf")])
    gen.set_editor_property("theme_props", [unreal.Name(n) for n in ("Engine.Gear", "Engine.Chain", "Engine.Cart", "Engine.Anvil", "Engine.Kiln", "Engine.Barrel", "Engine.Chain")])
    gen.set_editor_property("theme_prop_spacing", 500.0); gen.set_editor_property("theme_prop_chance", 0.3)
    for k, v in (("tier_floors", False), ("dungeon_key", "war_engine"), ("dungeon_title", "The War Engine"),
                 ("town_level", "/Game/RandomDungeon/Maps/brokenspire"), ("catacombs_level", ""), ("final_boss_on", False), ("menu_level", "")):
        try: gen.set_editor_property(k, v)
        except Exception as e: print("WAR (no", k, ")", e)
    # ------------------------------------------------------------ the machines
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
        if e.get("material"): d.material = unreal.load_asset(e["material"])
        added.append(d)
        rows.append([e["name"], e["tier"], round(ext.z * 2 * sc), round(rad), round(hh), round(spd), [round(h, 2) for h in d.hit_times]])
    # (the castle's kinds lighter: in each tier the machines' weight twice the castle's together)
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
    print("WAR", DST, "| key", gen.get_editor_property("dungeon_key"), "| title", gen.get_editor_property("dungeon_title"),
          "| themes", [str(t) for t in gen.get_editor_property("tier_themes")], "| final boss", gen.get_editor_property("final_boss_on"),
          "| pieces", len(P), "| machines", rows, "| castle kinds", len(mons))
    del gen, pieces, P, w, mons, added, fantasy
import gc
gc.collect()
