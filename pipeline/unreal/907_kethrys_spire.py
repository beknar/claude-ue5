"""kethrys_spire: the dungeon inside Kethrys Spire's black tower (the user's list of 2026-11-08b, docs/improvements9.txt, its
fourth phase: "a mage-city clustered around a black tower that hasn't opened its gates in a century"; the tower's dungeon is the
chain's fifth: its key, the Spire Key, dropped by the Sewers of Graymourne's boss; it drops Heaven's). A Save As copy of
mistward_castle (its heroes, balance, loot, traps, special rooms and bosses; its halls spread out by tier as the castle's) with:
- its own counters and record (DungeonKey "kethrys"), its name (DungeonTitle), the town it comes back to (TownLevel
  brokenspire: the way out puts her before the tower's door, the game instance's ReturnAt / ReturnTown)
- its looks by tier (TierThemes): the arcane halls ("Arcane": Mystic Dungeon's walls and stone tiles in darkened copies of
  their own stone (MI_Arcane_*), its damaged walls for the rough ones, a ring mosaic among the floors) in tiers 1, 2 and 4, the castle's in 3, both in 5; the
  tower's props by the walls (ThemeProps: ice crystals (Alien Planet), Gothic Props' candle stands, rune stones (Relics));
  its lights drawn toward a cold violet (DungeonLightTint, DungeonLightTintShare 0.6)
- its casters (SourceArt/kethrys_spire/monsters.json): measured as 895 measures the machines and added to the castle's kinds;
  the castle's kinds' weight lowered so that two in three monsters of a tier are casters; each shoots from afar (879's
  ranged monsters: Magic Projectiles Vol. 5's bolts); their clips (Mystic Dungeon's on its own mannequin) made playable on
  their meshes' skeletons (compatible skeletons, saved); a kind's parts worn over its body
- no final boss (Aurorim is Mistward Castle's), no menu (it is entered from the tower with her hero)
Run as `907 saveas` (it saves the copy and quits the editor: a copied map is opened only after a restart), then, the editor
started again, `907` (it sets the copy up, builds its start section and saves it). Then 905 (the chain's items on it). Args: [saveas]"""
import sys, os, json, math, unreal
SRC, DST = "/Game/RandomDungeon/Maps/mistward_castle", "/Game/RandomDungeon/Maps/kethrys_spire"
SA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "claude_ue5", "SourceArt", "kethrys_spire"))
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
APE = unreal.AnimPoseExtensions; o_ = unreal.AnimPoseEvaluationOptions()
V = unreal.Vector
YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
FACE = 25.0
ABIL = {"None": unreal.RDMonsterAbility.NONE, "Poison": unreal.RDMonsterAbility.POISON, "Weaken": unreal.RDMonsterAbility.WEAKEN, "Slow": unreal.RDMonsterAbility.SLOW}
VOL = {"V4": "/Game/MagicProjectilesVol4/Particles/NiagaraSystems", "V5": "/Game/MagicProjectilesVol5/Particles/NiagaraSystems"}


def corners(b): return [V(x, y, z) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]


def piece(path, front="+x", mode="center", scale=(1, 1, 1), collision=True, fit=None):
    """864's normalisation (895's), fit: (x, y) the footprint to scale it to"""
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


def fx(key, role):
    """879's: 'V5:Orb01' -> NS_<Role>_Orb01 (Vol. 5 keeps them in Projectiles / Muzzles / Hits)"""
    vol, name = key.split(":")
    sub = {"Projectile": "Projectiles", "Muzzle": "Muzzles", "Hit": "Hits"}[role] if vol == "V5" else ""
    return unreal.load_asset(f"{VOL[vol]}/{sub + '/' if sub else ''}NS_{role}_{name}")


if len(sys.argv) > 1 and sys.argv[1] == "saveas":
    assert not eal.does_asset_exist(DST), "kethrys_spire exists: set it up with 907 (no argument)"
    if not ues.get_editor_world().get_path_name().startswith(SRC + "."): les.load_level(SRC)
    ok = unreal.EditorLoadingAndSavingUtils.save_map(ues.get_editor_world(), DST)
    print("KSD saved as", DST, ok, "| quitting: start the editor again and run 907")
    unreal.SystemLibrary.quit_editor()
else:
    if not ues.get_editor_world().get_path_name().startswith(DST + "."): les.load_level(DST)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(DST + "."), w.get_path_name()
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    # ------------------------------------------------------------ the arcane halls (Mystic Dungeon: a 3 m kit)
    # (its stone darkened (the kit's own M_Tiles instances, copied: "Albedo Multiply", "Albedo Desaturate"): in its own cream the
    # start hall read as Mistward Castle's great hall (884 ks1's picture), as the sewers' clean stone had read as a hall)
    MEL = unreal.MaterialEditingLibrary
    def dark(name, parent, mul, desat):
        MDm = "/Game/RandomDungeon/Materials/Arcane"; path = MDm + "/" + name
        if not eal.does_asset_exist(path):
            unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MDm, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mi = unreal.load_asset(path); MEL.set_material_instance_parent(mi, unreal.load_asset(parent))
        MEL.set_material_instance_scalar_parameter_value(mi, "Albedo Multiply (S)", mul)
        MEL.set_material_instance_scalar_parameter_value(mi, "Albedo Desaturate", desat)
        MEL.update_material_instance(mi); eal.save_loaded_asset(mi, False)
        return mi
    MI = "/Game/MysticDungeon/Material/Instances/"
    WALLM = dark("MI_Arcane_Wall", MI + "MI_Wall_Dungeon_A", 0.32, 0.45)
    FLOORM = dark("MI_Arcane_Floor", MI + "MI_Stone_Square_Tiles_A", 0.42, 0.4)
    CEILM = dark("MI_Arcane_Ceil", MI + "MI_Floor_Tiles_A", 0.3, 0.45)
    MD = "/Game/MysticDungeon/Meshes/"
    P = {}
    w1 = piece(MD + "Walls/SM_Wall_A", front="+y", mode="wallface")
    w2 = piece(MD + "Walls/SM_Wall_A", front="+y", mode="wallface")
    r1 = piece(MD + "Walls/SM_Wall_A_DMG_A", front="+y", mode="wallface"); r2 = piece(MD + "Walls/SM_Wall_A_DMG_B", front="+y", mode="wallface"); r3 = piece(MD + "Walls/SM_Wall_A_DMG_D", front="+y", mode="wallface")
    for p in (w1, w2, r1, r2, r3): p.material = WALLM
    for n, p in (("Wall_Block", w1), ("Wall_Stone", w2), ("Wall_Corr", w1), ("Wall_Rough", r1), ("Wall_Rough_2", r2), ("Wall_Rough_3", r3)): P["Arcane." + n] = p
    f1 = piece(MD + "Floor/SM_Floor_Stone_Square_Tiles_A", mode="floor", fit=(300, 300))
    f2 = piece(MD + "Floor/SM_floor_tiles_A", mode="floor", fit=(300, 300))
    fm = piece(MD + "Floor/SM_floor_Ring_Mosaic_A", mode="floor", fit=(300, 300))
    f1.material = FLOORM
    for n in ("Floor_Stone", "Floor_Brick", "Floor_Brick2", "Floor_Random", "Floor_Tiles", "Floor_Wood", "Floor_Corr"):
        P["Arcane." + n] = f1; P["Arcane." + n + "_Alt"] = f2
    P["Arcane.Floor_Tiles_Alt"] = fm
    P["Arcane.Ceil_Room"] = piece(MD + "Floor/SM_Floor_Tiles_B", mode="ceil", fit=(300, 300)); P["Arcane.Ceil_Room"].material = CEILM
    P["Arcane.Ceil_Corr"] = P["Arcane.Ceil_Room"]
    # ------------------------------------------------------------ the tower's props by the walls
    PROPS = {
        "Tower.Crystal": piece("/Game/AlienPlanet/Meshes/Foliage/SM_IceCrystal01", scale=1.3, collision=False),
        "Tower.Candles": piece("/Game/Gothic_Props/Assets/Meshes/SM_Prop_CandleStand_A"),
        "Tower.Rune": piece("/Game/Relics/VOL2_ForgottenRelics/Meshes/LP/SM_Rune_01b", scale=0.7),
        "Tower.Cauldron": piece("/Game/CauldronFX_VDB/Meshes/SM_Cauldron"),
    }
    P.update(PROPS)
    pieces = dict(gen.get_editor_property("pieces"))
    for k in [k for k in pieces if str(k).startswith(("Arcane.", "Tower."))]: del pieces[k]
    for k, p in P.items(): pieces[unreal.Name(k)] = p
    gen.set_editor_property("pieces", pieces)
    gen.set_editor_property("tier_themes", [unreal.Name(n) for n in ("Arcane", "Arcane", "Castle", "Arcane", "Mixed")])
    gen.set_editor_property("mixed_themes", [unreal.Name(n) for n in ("Arcane", "Castle")])
    gen.set_editor_property("theme_props", [unreal.Name(n) for n in ("Tower.Crystal", "Tower.Candles", "Tower.Rune", "Tower.Crystal", "Tower.Cauldron", "Tower.Candles")])
    gen.set_editor_property("theme_prop_spacing", 500.0); gen.set_editor_property("theme_prop_chance", 0.3)
    # (its light cold and violet: the castle's torches drawn 0.6 toward it (the tower's halls read as the castle's in its orange))
    gen.set_editor_property("dungeon_light_tint", unreal.LinearColor(0.5, 0.42, 1.0, 1.0)); gen.set_editor_property("dungeon_light_tint_share", 0.6)
    for k, v in (("tier_floors", False), ("dungeon_key", "kethrys"), ("dungeon_title", "The Black Tower of Kethrys Spire"),
                 ("town_level", "/Game/RandomDungeon/Maps/brokenspire"), ("catacombs_level", ""), ("final_boss_on", False), ("menu_level", "")):
        try: gen.set_editor_property(k, v)
        except Exception as e: print("KSD (no", k, ")", e)
    # ------------------------------------------------------------ the casters
    MJ = json.load(open(os.path.join(SA, "monsters.json"), encoding="utf-8"))
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    flt = unreal.ARFilter(package_paths=[MJ["clip_pack"]], class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "AnimSequence")], recursive_paths=True)
    by_name = {}
    for a in ar.get_assets(flt): by_name.setdefault(str(a.asset_name), str(a.package_name))
    def clip(n):
        a = unreal.load_asset(by_name[n]) if n in by_name else None
        assert a, n
        return a
    mons = [m for m in gen.get_editor_property("monsters") if not str(m.get_editor_property("name")) in {e["name"] for e in MJ["monsters"]}]
    added = []; rows = []
    for e in MJ["monsters"]:
        sk = unreal.load_asset(e["mesh"])
        assert sk, e["mesh"]
        idle = clip(e["idle"]); walk = clip(e["walk"]); hit = clip(e["hit"]); death = clip(e["death"])
        att = [clip(a) for a in e["attacks"]]
        # (the clips' skeleton made compatible with the mesh's, saved: Mystic Dungeon's mannequin to the mesh's own)
        cs = idle.get_editor_property("skeleton"); s = sk.skeleton
        if cs != s and not any(x == cs for x in s.get_editor_property("compatible_skeletons")):
            s.add_compatible_skeleton(cs); eal.save_loaded_asset(s, only_if_is_dirty=False)
        sc = float(e.get("scale", 1.0))
        b = sk.get_bounds(); ext = b.box_extent; org = b.origin
        zmin = (org.z - ext.z) * sc
        hh = max(40.0, ext.z * sc); rad = min(90.0, max(28.0, min(ext.x, ext.y) * 0.8 * sc))
        spd = clip_speed(walk) or 150.0
        d = unreal.RDMonsterDef(); d.name = e["name"]; d.title = e["title"]; d.mesh = sk; d.idle = idle; d.walk = walk
        d.parts = [unreal.load_asset(p) for p in e.get("parts", []) if unreal.load_asset(p)]
        d.walk_clip_speed = max(spd * sc, 60.0); d.walk_speed = max(90.0, min(220.0, spd * sc))
        d.capsule_radius = rad; d.capsule_half_height = hh
        d.mesh_z = -hh - zmin; d.mesh_yaw = -90.0; d.scale = sc; d.weight = float(e.get("weight", 3))
        d.attacks = att; d.hit_times = [blow_time(a) for a in att]; d.get_hit = hit; d.death = death
        f = 1.2 if e["tier"] >= 4 else 1.0
        d.health_factor = f; d.damage_factor = f
        d.reach = round(70.0 + 0.9 * rad); d.attack_interval = 1.8
        d.sound_set = e["sound"]; d.step_length = round(40.0 + 0.25 * ext.z * 2 * sc)
        d.tier = e["tier"]; d.ability = ABIL[e["ability"]]
        r = e.get("ranged")
        if r:
            kind = r["range"]
            d.shoots = True
            d.ranged_range = float(MJ["ranges"][kind]); d.ranged_min = float(MJ["ranges"]["min"])
            d.ranged_damage = float(MJ["damage"][kind]); d.ranged_cooldown = float(MJ["cooldown"][kind]) * d.attack_interval
            d.ranged_speed = float(MJ["speed"][kind])
            d.ranged_fx = fx(r["fx"], "Projectile"); d.ranged_muzzle_fx = fx(r["fx"], "Muzzle"); d.ranged_hit_fx = fx(r["fx"], "Hit")
            d.ranged_fx_scale = float(r.get("scale", 1.0)); d.ranged_theme = r.get("theme", "a bolt of arcane fire")
        added.append(d)
        rows.append([e["name"], e["tier"], round(ext.z * 2 * sc), round(rad), round(hh), round(spd), [round(h, 2) for h in d.hit_times], bool(d.ranged_fx)])
    # (the castle's kinds lighter: in each tier the casters' weight twice the castle's together)
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
    print("KSD", DST, "| key", gen.get_editor_property("dungeon_key"), "| title", gen.get_editor_property("dungeon_title"),
          "| themes", [str(t) for t in gen.get_editor_property("tier_themes")], "| final boss", gen.get_editor_property("final_boss_on"),
          "| pieces", len(P), "| casters", rows, "| castle kinds", len(mons))
    del gen, pieces, P, w, mons, added
import gc
gc.collect()
