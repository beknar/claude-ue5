"""The list of 2026-11-10 (docs/improvements10.txt), its sixth phase, the wilderness, on brokenspire (C++ first: RD/RDWild10.cpp).
Steps (all by default, or name some):
  houses   "the buildings in the wilderness do not have an interior and there is no way to get inside or climb any stairs on the
           outside": the village houses' open copies (/Game/Castle/Interactive/Meshes/SM_house_0N_open, their door leaves _doorK and
           hinges from SourceArt/castle_interactive/interactive.json) measured (their room by traces from the middle at 1.2 m), written
           as the generator's WildHouses; WildPieces' "house" entries the five open houses and "farmhouse" the three that fit a
           farmstead's yard (02, 03, 05), all at WILD_HOUSE_SCALE (their 2.3 m doors 1.85 m for her; the closed ones stood 9 m high
           and their doors would have been 1.5 m); the Lake Village barn and farmhouse given their mesh as collision (they had none:
           she walked through them); the stone of the plinths and steps (the dungeon's Floor_Stone material)
  map      the farmsteads on the big map (bWildFarmsOnMap; the symbol wmap_farmstead: blender_numpy/wild_symbols.py, then
           `887 symbols`)
  life     the liveliness ideas built: travellers on the roads (bWildTravellers, their roles), hens loose in the square (TownHens),
           the watch's lanterns at night (bNightLanterns, the Lantern prop)
Run it after 887 (its data step writes WildPieces anew) and 886 (TownProps). Args: [houses] [map] [life]"""
import os, sys, json, unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
V = unreal.Vector
STEPS = [a for a in sys.argv[1:] if a in ("houses", "map", "life")] or ["houses", "map", "life"]
SA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "claude_ue5", "SourceArt"))
MAP = "/Game/RandomDungeon/Maps/brokenspire"
D = "/Game/Castle/Interactive/Meshes"
WILD_HOUSE_SCALE = 0.8
FARM_HOUSES = ("SM_house_02", "SM_house_03", "SM_house_05")
REPORT = []

if not ues.get_editor_world().get_path_name().startswith(MAP + "."):
    les.load_level(MAP); unreal.SystemLibrary.execute_console_command(None, "obj gc")
g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))

if "houses" in STEPS:
    INFO = json.load(open(os.path.join(SA, "castle_interactive", "interactive.json"), encoding="utf-8"))["houses"]
    w = ues.get_editor_world()
    def trace(a, b):
        h = unreal.SystemLibrary.line_trace_single(w, a, b, unreal.TraceTypeQuery.ECC_VISIBILITY, True, [], unreal.DrawDebugTrace.NONE, True)
        if h is None: return None
        t = h.to_tuple(); return t[4] if t[0] else None
    houses = []; pieces = dict((str(k), v) for k, v in g.get_editor_property("wild_pieces").items()); scales = dict((str(k), v) for k, v in g.get_editor_property("wild_piece_scale").items())
    opens = {}
    for n in range(1, 6):
        nm = f"SM_house_0{n}"
        m = unreal.load_asset(f"{D}/{nm}_open")
        if not m or nm not in INFO: REPORT.append(f"{nm}: no open mesh"); continue
        # (its room: traced from its middle at 1.2 m to each wall, spawned far under the level and taken away)
        a = eas.spawn_actor_from_object(m, V(0, 0, -50000)); a.set_actor_location(V(0, 0, -50000), False, True)
        c = V(0, 0, -50000 + 120); ext = {}
        for k, d in (("+x", V(1, 0, 0)), ("-x", V(-1, 0, 0)), ("+y", V(0, 1, 0)), ("-y", V(0, -1, 0))):
            p = trace(c, c + d * 3000); ext[k] = (p - c).length() if p else 500.0
        eas.destroy_actor(a)
        h = unreal.RDWildHouse(); h.set_editor_property("mesh", m)
        # (18 cm in from the walls: 340's margin; Python takes the In off InMin / InMax: min, max)
        h.set_editor_property("min", unreal.Vector2D(-ext["-x"] + 18, -ext["-y"] + 18)); h.set_editor_property("max", unreal.Vector2D(ext["+x"] - 18, ext["+y"] - 18))
        ds = []
        for k, dd in enumerate(INFO[nm]):
            leaf = unreal.load_asset(f"{D}/{nm}_door{k}")
            if not leaf: continue
            hd = unreal.RDWildHouseDoor(); hd.set_editor_property("leaf", leaf)
            # (interactive.json holds Blender's y: Unreal's is the negative (the dungeon rules' note))
            pv = dd["pivot"]; hd.set_editor_property("pivot", V(pv[0], -pv[1], pv[2]))
            # (its width signed by the way the leaf runs from its hinge in Unreal's axes: leaf_dir's y negated)
            ly = -float(dd.get("leaf_dir", [0, 1, 0])[1]); hd.set_editor_property("width", float(dd["width"]) * (1.0 if ly >= 0 else -1.0))
            ds.append(hd)
        h.set_editor_property("doors", ds); houses.append(h); opens[nm] = m
        REPORT.append(f"{nm}: room x {-ext['-x']:.0f}..{ext['+x']:.0f}, y {-ext['-y']:.0f}..{ext['+y']:.0f}, {len(ds)} doors")
    g.set_editor_property("wild_houses", houses)
    # (the wilds' "house" pieces the open ones, the farmhouses the three short ones; each at WILD_HOUSE_SCALE)
    for k in [k for k in pieces if k.startswith("house") or k.startswith("farmhouse")]: pieces.pop(k)
    for i, nm in enumerate(sorted(opens)): pieces[f"house{i + 1}"] = opens[nm]
    for i, nm in enumerate([x for x in FARM_HOUSES if x in opens]): pieces[f"farmhouse{i + 1}"] = opens[nm]
    for nm, m in opens.items(): scales[m.get_name()] = WILD_HOUSE_SCALE
    g.set_editor_property("wild_pieces", {unreal.Name(k): v for k, v in pieces.items()})
    g.set_editor_property("wild_piece_scale", {unreal.Name(k): float(v) for k, v in scales.items()})
    # (the Lake Village barn and farmhouse: no simple collision, used as default: walked through. Their mesh as their collision now)
    for p in ("/Game/Medieval_Lake_Village/Meshs/SM_StorageSet", "/Game/Medieval_Lake_Village/Meshs/SM_HouseSet01"):
        m = unreal.load_asset(p)
        if not m: continue
        bs = m.get_editor_property("body_setup")
        if bs.get_editor_property("collision_trace_flag") != unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE:
            bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE); m.modify(); eal.save_loaded_asset(m, only_if_is_dirty=False)
            REPORT.append(f"{m.get_name()}: its mesh as its collision")
    fs = g.get_editor_property("pieces").get(unreal.Name("Floor_Stone"))
    stone = (fs.get_editor_property("material") or fs.get_editor_property("mesh").get_material(0)) if fs else None
    g.set_editor_property("wild_plinth_material", stone)
    g.set_editor_property("wild_house_insides", True)
    REPORT.append(f"houses: {len(houses)} open houses, pieces house {sorted(k for k in pieces if k.startswith('house'))}, farmhouse {sorted(k for k in pieces if k.startswith('farmhouse'))}, plinth {stone.get_name() if stone else None}")

if "map" in STEPS:
    g.set_editor_property("wild_farms_on_map", True)
    REPORT.append("map: the farmsteads on it")

if "life" in STEPS:
    g.set_editor_property("wild_travellers", True); g.set_editor_property("wild_traveller_groups", 3); g.set_editor_property("wild_traveller_m", 450.0)
    g.set_editor_property("wild_traveller_roles", [unreal.Name(r) for r in ("Townsfolk", "Refugee", "Soldier")])
    g.set_editor_property("town_hens", 8); g.set_editor_property("night_lanterns", True)
    # (the lantern in the watch's right fist, hanging: its up along the hand bone's -X (the arm's way up when it hangs), its foot
    # its height toward the fingers)
    lm = unreal.load_asset("/Game/Hivemind/Medieval_Docks/Static_Meshes/Props/Lanterns/SM_Lantern")
    props = g.get_editor_property("town_props")
    if lm:
        b = lm.get_bounding_box(); hgt = b.max.z - b.min.z; sc = 32.0 / max(hgt, 1.0)
        p = unreal.RDTownProp(); p.set_editor_property("mesh", lm); p.set_editor_property("bone", "hand_r")
        p.set_editor_property("grip", unreal.Transform(V(hgt * sc + 6.0, 0.0, -2.0), unreal.Rotator(roll=0.0, pitch=90.0, yaw=0.0), V(sc, sc, sc)))
        props[unreal.Name("Lantern")] = p; g.set_editor_property("town_props", props)
        REPORT.append(f"life: travellers on, 8 hens, lanterns ({lm.get_name()} {hgt:.0f} cm at {sc:.2f})")

g.modify(); les.save_current_level()
print("WILD10 " + " | ".join(REPORT))
del g
import gc
gc.collect()
