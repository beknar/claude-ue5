"""heaven_fortress: the mechanised fortress under Kratos Aurorim Research's facility in Heaven (the user's list of 2026-11-08b,
docs/improvements9.txt, its fourth phase: "the dungeon is a mechanized fortress with modern and sci-fi defenders armed with
firearms. the outside and entrance of the dungeon is a foreboding research facility called 'Kratos Aurorim Research, LLC'"; the
chain's last dungeon: its key, the Kratos Keycard, dropped by the Black Tower of Kethrys Spire's boss). A Save As copy of
mistward_castle (its heroes, balance, loot, traps, special rooms and bosses; its halls spread out by tier as the castle's) with:
- its own counters and record (DungeonKey "heaven"), its name (DungeonTitle "Kratos Aurorim Research"), the town it comes back to
  (TownLevel brokenspire: the way out puts her before the facility's door, the game instance's ReturnAt / ReturnTown)
- its looks by tier (TierThemes): the fortress's halls ("Facility": steel and concrete walls with their light strips, steel
  floors, ceilings of light panels: boxes merged into meshes in Heaven's own materials (908's M_HV_Surface)) in tiers 1 to 4,
  the fortress and the castle mixed in 5; its machines by the walls (ThemeProps: Data_Center's servers and chillers, the sci-fi
  racks, generators and power boxes); its lights drawn toward a cold white (DungeonLightTint, share 0.7)
- its defenders (SourceArt/heaven_fortress/monsters.json): measured as 907 measures the casters and added to the castle's kinds;
  the castle's kinds' weight lowered so that two in three monsters of a tier are defenders; each shoots (879's ranged monsters:
  its shot clip, a tracer for its round, a muzzle flash, a bullet's impact); clips on another skeleton made playable on the
  mesh's (compatible skeletons, saved)
- no final boss (Aurorim is Mistward Castle's), no menu (it is entered from the facility with her hero)
Run 908 first (its materials). Run as `909 saveas` (it saves the copy and quits the editor: a copied map is opened only after a
restart), then, the editor started again, `909` (it sets the copy up, builds its start section and saves it). Then 905 (the
chain's items on it). Args: [saveas] [rebuild]"""
import sys, os, json, math, unreal
SRC, DST = "/Game/RandomDungeon/Maps/mistward_castle", "/Game/RandomDungeon/Maps/heaven_fortress"
SA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "claude_ue5", "SourceArt", "heaven_fortress"))
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
APE = unreal.AnimPoseExtensions; o_ = unreal.AnimPoseEvaluationOptions()
V = unreal.Vector
YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
FACE = 25.0
ABIL = {"None": unreal.RDMonsterAbility.NONE, "Poison": unreal.RDMonsterAbility.POISON, "Weaken": unreal.RDMonsterAbility.WEAKEN, "Slow": unreal.RDMonsterAbility.SLOW}
HV = "/Game/RandomDungeon/Heaven"; HVM = HV + "/Meshes"
REBUILD = "rebuild" in sys.argv[1:]


def corners(b): return [V(x, y, z) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]


def piece(path, front="+x", mode="center", scale=(1, 1, 1), collision=True, fit=None):
    """864's normalisation (895's), fit: (x, y) the footprint to scale it to"""
    m = unreal.load_asset(path) if isinstance(path, str) else path
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




def boxes(name, parts, MAT):
    """908's: a mesh merged from boxes (x0, x1, y0, y1, z0, z1, material key), its pivot the world's origin, saved"""
    path = f"{HVM}/{name}"
    if eal.does_asset_exist(path) and not REBUILD: return unreal.load_asset(path)
    if eal.does_asset_exist(path): eal.delete_asset(path)
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    acts = []
    for (x0, x1, y0, y1, z0, z1, mk) in parts:
        a = eas.spawn_actor_from_object(cube, V((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        a.set_actor_scale3d(V(max(x1 - x0, 0.2) / 100.0, max(y1 - y0, 0.2) / 100.0, max(z1 - z0, 0.2) / 100.0))
        a.static_mesh_component.set_material(0, MAT[mk])
        acts.append(a)
    o = unreal.MergeStaticMeshActorsOptions()
    o.set_editor_property("base_package_name", f"{HVM}/{name[3:]}"); o.set_editor_property("destroy_source_actors", True); o.set_editor_property("spawn_merged_actor", False)
    ms = o.get_editor_property("mesh_merging_settings")
    ms.set_editor_property("pivot_type", unreal.MeshMergePivotType.WORLD_ORIGIN); ms.set_editor_property("merge_physics_data", True)
    ms.set_editor_property("merge_materials", False); ms.set_editor_property("generate_light_map_uv", False)
    o.set_editor_property("mesh_merging_settings", ms)
    unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).merge_static_mesh_actors(acts, o)
    for a in acts:
        try: a.destroy_actor()
        except Exception: pass
    m = unreal.load_asset(path)
    assert m, path
    eal.save_loaded_asset(m, False)
    return m


if len(sys.argv) > 1 and sys.argv[1] == "saveas":
    assert not eal.does_asset_exist(DST), "heaven_fortress exists: set it up with 909 (no argument)"
    if not ues.get_editor_world().get_path_name().startswith(SRC + "."): les.load_level(SRC)
    ok = unreal.EditorLoadingAndSavingUtils.save_map(ues.get_editor_world(), DST)
    print("HVF saved as", DST, ok, "| quitting: start the editor again and run 909")
    unreal.SystemLibrary.quit_editor()
else:
    if not ues.get_editor_world().get_path_name().startswith(DST + "."): les.load_level(DST)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(DST + "."), w.get_path_name()
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    MEL = unreal.MaterialEditingLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
    SURF = unreal.load_asset(HV + "/M_HV_Surface"); assert SURF, "run 908 first (M_HV_Surface)"
    def mi(name, rgb, metal=0.0, rough=0.6, glow=0.0):
        path = HV + "/" + name
        if not eal.does_asset_exist(path): AT.create_asset(name, HV, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        m = unreal.load_asset(path); MEL.set_material_instance_parent(m, SURF)
        MEL.set_material_instance_vector_parameter_value(m, "Color", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        MEL.set_material_instance_scalar_parameter_value(m, "Metallic", metal); MEL.set_material_instance_scalar_parameter_value(m, "Roughness", rough)
        MEL.set_material_instance_scalar_parameter_value(m, "Glow", glow)
        MEL.update_material_instance(m); eal.save_loaded_asset(m, False)
        return m
    MAT = {"steel": mi("MI_HV_Steel", (0.13, 0.14, 0.16), 0.85, 0.32), "dark": mi("MI_HV_DarkConcrete", (0.16, 0.17, 0.19), 0.0, 0.8),
           "concrete": mi("MI_HV_Concrete", (0.5, 0.5, 0.48), 0.0, 0.85), "panel": mi("MI_HV_LightPanel", (0.9, 0.95, 1.0), 0.0, 0.5, 6.0),
           "cyan": mi("MI_HV_CyanStrip", (0.2, 0.85, 1.0), 0.0, 0.4, 8.0), "hazard": mi("MI_HV_Hazard", (0.75, 0.55, 0.05), 0.2, 0.5),
           "red": mi("MI_HV_RedLight", (1.0, 0.06, 0.04), 0.0, 0.5, 12.0), "plate": mi("MI_HV_FloorPlate", (0.22, 0.23, 0.25), 0.7, 0.45)}
    # ------------------------------------------------------------ the fortress's halls (built with their room face +X, then 907's
    # normalisation: a wall's face at FACE, a floor's top at 0, a ceiling turned over)
    H = 151.0
    def wall(name, base, panel, strip):
        return boxes(name, [(-40, 0, -H, H, 0, 40, "dark"), (-40, -4, -H, H, 40, 560, panel), (-4, 0, -H, H, 40, 560, panel),
                            (-1, 2, -H, H, 246, 256, strip), (-40, 2, -H, -146, 40, 560, "steel"), (-40, 2, 146, H, 40, 560, "steel"),
                            (-40, 0, -H, H, 560, 600, base)], MAT)
    w1 = wall("SM_HVF_Wall", "dark", "steel", "cyan"); w2 = wall("SM_HVF_WallConcrete", "dark", "concrete", "cyan"); r1 = wall("SM_HVF_WallWarn", "dark", "steel", "red")
    r2 = boxes("SM_HVF_WallHazard", [(-40, 0, -H, H, 0, 600, "steel"), (-1, 2, -H, H, 30, 70, "hazard"), (-1, 2, -H, H, 246, 256, "red")], MAT)
    P = {}
    pw1 = piece(w1, mode="wallface"); pw2 = piece(w2, mode="wallface"); pr1 = piece(r1, mode="wallface"); pr2 = piece(r2, mode="wallface")
    for n, p in (("Wall_Block", pw1), ("Wall_Stone", pw2), ("Wall_Corr", pw1), ("Wall_Rough", pr1), ("Wall_Rough_2", pr2), ("Wall_Rough_3", pr1)): P["Facility." + n] = p
    f1 = piece(boxes("SM_HVF_Floor", [(-H, H, -H, H, -20, 0, "plate"), (-H, H, -2, 2, -1, 0.5, "dark"), (-2, 2, -H, H, -1, 0.5, "dark")], MAT), mode="floor")
    f2 = piece(boxes("SM_HVF_FloorConcrete", [(-H, H, -H, H, -20, 0, "concrete"), (-H, H, 130, H, -1, 0.5, "hazard")], MAT), mode="floor")
    for n in ("Floor_Stone", "Floor_Brick", "Floor_Brick2", "Floor_Random", "Floor_Tiles", "Floor_Wood", "Floor_Corr"):
        P["Facility." + n] = f1; P["Facility." + n + "_Alt"] = f2
    P["Facility.Ceil_Room"] = piece(boxes("SM_HVF_Ceil", [(-H, H, -H, H, 0, 15, "dark"), (-60, 60, -60, 60, 15, 17, "panel")], MAT), mode="ceil")
    P["Facility.Ceil_Corr"] = P["Facility.Ceil_Room"]
    # ------------------------------------------------------------ the fortress's machines by the walls
    PROPS = {
        "Fortress.Server": piece("/Game/Data_Center/Meshes/Server/SM_server"),
        "Fortress.Chiller": piece("/Game/Data_Center/Meshes/Chiller/SM_chiller_01"),
        "Fortress.Rack": piece("/Game/SciFiPropPack_V1/Meshes/SM_Rack"),
        "Fortress.Generator": piece("/Game/SciFiPropPack_V1/Meshes/SM_Generator"),
        "Fortress.PowerBox": piece("/Game/SciFiPropPack_V1/Meshes/SM_PowerBox"),
        "Fortress.Cabinet": piece("/Game/Scene_Warehouse/Assets/MS/3D/Ind_War_Cabinet_Electric_Metal_Dirty_01/SM_Ind_War_Cabinet_Electric_Metal_Dirty_01"),
    }
    P.update({k: v for k, v in PROPS.items() if v})
    pieces = dict(gen.get_editor_property("pieces"))
    for k in [k for k in pieces if str(k).startswith(("Facility.", "Fortress."))]: del pieces[k]
    for k, p in P.items(): pieces[unreal.Name(k)] = p
    gen.set_editor_property("pieces", pieces)
    gen.set_editor_property("tier_themes", [unreal.Name(n) for n in ("Facility", "Facility", "Facility", "Facility", "Mixed")])
    gen.set_editor_property("mixed_themes", [unreal.Name(n) for n in ("Facility", "Castle")])
    gen.set_editor_property("theme_props", [unreal.Name(n) for n in PROPS if PROPS[n]])
    gen.set_editor_property("theme_prop_spacing", 450.0); gen.set_editor_property("theme_prop_chance", 0.35)
    # (its light cold and white: the castle's torches drawn 0.7 toward it)
    gen.set_editor_property("dungeon_light_tint", unreal.LinearColor(0.75, 0.88, 1.0, 1.0)); gen.set_editor_property("dungeon_light_tint_share", 0.7)
    for k, v in (("tier_floors", False), ("dungeon_key", "heaven"), ("dungeon_title", "Kratos Aurorim Research"),
                 ("town_level", "/Game/RandomDungeon/Maps/brokenspire"), ("catacombs_level", ""), ("final_boss_on", False), ("menu_level", "")):
        try: gen.set_editor_property(k, v)
        except Exception as e: print("HVF (no", k, ")", e)
    # ------------------------------------------------------------ the defenders
    MJ = json.load(open(os.path.join(SA, "monsters.json"), encoding="utf-8"))
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    packs = {}
    def clip(pack, n):
        if pack not in packs:
            flt = unreal.ARFilter(package_paths=[pack], class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "AnimSequence")], recursive_paths=True)
            packs[pack] = {}
            for a in ar.get_assets(flt): packs[pack].setdefault(str(a.asset_name), str(a.package_name))
        a = unreal.load_asset(packs[pack][n]) if n in packs[pack] else None
        assert a, (pack, n)
        return a
    mons = [m for m in gen.get_editor_property("monsters") if not str(m.get_editor_property("name")) in {e["name"] for e in MJ["monsters"]}]
    added = []; rows = []
    for e in MJ["monsters"]:
        sk = unreal.load_asset(e["mesh"]); assert sk, e["mesh"]
        pk = e["pack"]
        idle = clip(pk, e["idle"]); walk = clip(pk, e["walk"]); hit = clip(pk, e["hit"]); death = clip(pk, e["death"]); shot = clip(pk, e["shot"])
        att = [clip(pk, a) for a in e["attacks"]]
        cs = idle.get_editor_property("skeleton"); s = sk.skeleton
        if cs != s and not any(x == cs for x in s.get_editor_property("compatible_skeletons")):
            s.add_compatible_skeleton(cs); eal.save_loaded_asset(s, only_if_is_dirty=False)
        sc = float(e.get("scale", 1.0))
        b = sk.get_bounds(); ext = b.box_extent; org = b.origin
        zmin = (org.z - ext.z) * sc
        hh = max(40.0, min(ext.z * sc, 160.0)); rad = min(90.0, max(28.0, min(ext.x, ext.y) * 0.8 * sc))
        spd = (clip_speed(walk) if walk != idle else None) or 150.0
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
        r = e["ranged"]; kind = r["range"]; gun = MJ["guns"][r["gun"]]
        d.shoots = True
        d.ranged_range = float(MJ["ranges"][kind]); d.ranged_min = float(MJ["ranges"]["min"])
        d.ranged_damage = float(MJ["damage"][kind]); d.ranged_cooldown = float(MJ["cooldown"][kind]) * d.attack_interval
        d.ranged_speed = float(MJ["speed"][kind])
        d.ranged_fx = unreal.load_asset(gun["projectile"]); d.ranged_muzzle_fx = unreal.load_asset(gun["muzzle"]); d.ranged_hit_fx = unreal.load_asset(gun["hit"])
        d.ranged_fx_scale = 1.0; d.ranged_theme = gun["theme"]
        # (the round leaves the barrel early in the shot: the fastest bone peaks late in a long burst (3.0 s in the trooper's), so at most 0.5 s)
        d.ranged_clip = shot; d.ranged_release = min(blow_time(shot), 0.5)
        added.append(d)
        rows.append([e["name"], e["tier"], round(ext.z * 2 * sc), round(rad), round(hh), round(spd), [round(h, 2) for h in d.hit_times], round(d.ranged_release, 2),
                     bool(d.ranged_fx), bool(d.ranged_muzzle_fx), bool(d.ranged_hit_fx)])
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
    print("HVF", DST, "| key", gen.get_editor_property("dungeon_key"), "| title", gen.get_editor_property("dungeon_title"),
          "| themes", [str(t) for t in gen.get_editor_property("tier_themes")], "| final boss", gen.get_editor_property("final_boss_on"),
          "| pieces", len(P), "| defenders", rows, "| castle kinds", len(mons))
    del gen, pieces, P, w, mons, added
import gc
gc.collect()
