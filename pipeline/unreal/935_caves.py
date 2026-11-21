"""caves: the cave complex under every landmark tower (the user's list of 2026-11-20, docs/improvements15.txt, item 23; the plan's ninth
phase; their choice: every landmark tower holds a cave entrance, one cave level serves them all, its tier the region's). A Save As copy
of mistward_castle (its heroes, balance, loot, traps, special rooms and bosses) with:
- the generator's bCave15: the tower's key and tier read from the game instance as play begins (RD/RDList15h.cpp's ApplyCave15), every
  tier of the level the region's one game tier; no key chain, final boss, arena, cells or bosses' unique rewards; its beasts the wilds'
  kinds of its tier (CaveExclude15: no people with firearms, no machines)
- its looks: the Cave theme on every tier (the Cave pack's rock walls, uneven rock floors and ceilings, stalagmites for columns,
  rock arches round the doorways), stones, stalagmites and boulders by the walls, the light tinted cold and dim; its floors going
  down (bTierFloors, as the catacombs and the sewers); the saved first hall built again without the castle's carpet, throne, banners
  and chandeliers (RDSection.cpp's cave hall)
- the wilds' monsters (their wild tier bands) copied from brokenspire's generator as text, so every tier of the game has its kinds
- solid copies of the pack's rock meshes (their collision their own faces: the pack's have no simple shapes) under
  /Game/RandomDungeon/Caves/Solid
On brokenspire (`935 wild`): the cave level's path and the mouth laid at every landmark tower's foot (the pack's rock arch, a dark slab
inside it in a material of our own).
Run as `935 saveas` (it saves the copy and quits the editor), then, the editor started again, `935` (the cave level: monsters, then
its setup and start section) and `935 wild`. Args: [saveas | level | wild]   (no argument: level)"""
import sys, os, json, gc, unreal
SRC, DST = "/Game/RandomDungeon/Maps/mistward_castle", "/Game/RandomDungeon/Maps/caves"
WILD = "/Game/RandomDungeon/Maps/brokenspire"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\caves"
SOLID = "/Game/RandomDungeon/Caves/Solid"
MATS = "/Game/RandomDungeon/Caves/Materials"
K = "/Game/Cave/Asset/"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
V = unreal.Vector
YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
FACE = 25.0
CJ = json.load(open(os.path.join(SA, "cave15.json"), encoding="utf-8"))


def corners(b): return [V(x, y, z) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]


def solid(path):
    """a copy of a pack's mesh whose collision is its own faces (the pack's rocks have no simple shapes: walked through)"""
    name = path.rsplit("/", 1)[1]
    dst = SOLID + "/" + name
    if not eal.does_asset_exist(dst):
        assert eal.duplicate_asset(path, dst), dst
    m = unreal.load_asset(dst)
    bs = m.get_editor_property("body_setup")
    if bs and bs.get_editor_property("collision_trace_flag") != unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE:
        bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        m.modify(); eal.save_loaded_asset(m, False)
    return dst


def piece(path, front="+x", mode="center", size=None, scale=None, collision=True, lift=0.0, raw=False):
    """897's normalisation; size: (x, y, z) the box (cm) it is scaled to in the dungeon's frame (front +X), any of them None to keep
    the others' scale; lift: cm added to the placed height; raw: the mesh as it is (its own collision: the engine's cube)"""
    m = unreal.load_asset(solid(path) if (collision and not raw) else path)
    assert m, path
    rot = unreal.Rotator(roll=180.0 if mode == "ceil" else 0.0, pitch=0.0, yaw=YAW[front])
    t1 = unreal.Transform(V(0, 0, 0), rot, V(1, 1, 1))
    pts = [unreal.MathLibrary.transform_location(t1, c) for c in corners(m.get_bounding_box())]
    ext = [max(getattr(p, a) for p in pts) - min(getattr(p, a) for p in pts) for a in "xyz"]
    if scale is not None:
        sc = [scale] * 3 if isinstance(scale, (int, float)) else list(scale)
    else:
        f = [None if s is None else s / max(e, 1.0) for s, e in zip(size, ext)]
        known = [x for x in f if x is not None]
        sc = [x if x is not None else (sum(known) / len(known)) for x in f]
    # (the scale is along the dungeon frame's axes: turned back into the mesh's own for the transform)
    if YAW[front] in (90.0, -90.0): sc = [sc[1], sc[0], sc[2]]
    t0 = unreal.Transform(V(0, 0, 0), rot, V(*sc))
    pts = [unreal.MathLibrary.transform_location(t0, c) for c in corners(m.get_bounding_box())]
    mn = V(min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)); mx = V(max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
    tx, ty, tz = -(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z
    if mode == "floor": tz = -mx.z
    elif mode == "wallface": tx = FACE - mx.x
    p = unreal.RDPiece(); p.mesh = m; p.adjust = unreal.Transform(V(tx, ty, tz + lift), rot, V(*sc))
    p.size = V(mx.x - mn.x, mx.y - mn.y, mx.z - mn.z); p.collision = collision
    return p


def tinted(name, parent, tint):
    """a child of one of the pack's world-aligned instances, its layers' tint darkened (the pack's limestone read as a lit hall)"""
    MEL = unreal.MaterialEditingLibrary
    path = MATS + "/" + name
    if not eal.does_asset_exist(path):
        unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi = unreal.load_asset(path)
    MEL.set_material_instance_parent(mi, unreal.load_asset(parent))
    names = [str(x) for x in MEL.get_vector_parameter_names(mi)]
    want = [v for v in ("L1_Tint", "L2_Tint", "L3_Tint", "Tint") if v in names]
    assert want, (name, names)
    for v in want:
        MEL.set_material_instance_vector_parameter_value(mi, v, unreal.LinearColor(*tint, 1.0))
    MEL.update_material_instance(mi); eal.save_loaded_asset(mi, False)
    got = MEL.get_material_instance_vector_parameter_value(mi, want[0])
    assert abs(got.r - tint[0]) < 0.01, (name, got)
    return mi


def dark_material():
    """an unlit near-black for the mouth's inside (no light reaches it from the open)"""
    path = MATS + "/M_RD_CaveDark"
    if eal.does_asset_exist(path): return unreal.load_asset(path)
    MEL = unreal.MaterialEditingLibrary
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_RD_CaveDark", MATS, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -300, 0)
    c.set_editor_property("constant", unreal.LinearColor(0.004, 0.004, 0.005, 1.0))
    assert MEL.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); eal.save_loaded_asset(m, False)
    return m


def gen_of_open():
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def wild_monsters_text():
    """brokenspire's monsters (the castle's kinds and every later dungeon's, with their wild tier bands) as text"""
    les.load_level(WILD)
    g = gen_of_open()
    txt = g.get_editor_property("monsters")
    out = [m.export_text() for m in txt]
    n = len(out)
    del g, txt
    gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    print("CAVE brokenspire's kinds", n)
    return out


def level():
    texts = wild_monsters_text()
    les.load_level(DST)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(DST + "."), w.get_path_name()
    gen = gen_of_open()
    # ------------------------------------------------------------ the rock: the castle's walls, floors and ceilings as solid boxes of their
    # sizes in the pack's world-aligned rock and ground, darkened (the pack's rock walls and ground slabs are blobs: laid a segment or a
    # tile each they left the void showing between them, the first pictures); the pack's rock faces stand along the walls as props
    P = {}
    pieces = dict(gen.get_editor_property("pieces"))
    # (the walls and ceilings in the pack's rock wall material (by UV: the world-aligned rock projects from above and left the walls' faces
    # flat grey, the second pictures); the floors in its world-aligned ground)
    ROCK = tinted("MI_RD_CaveRock", K + "RockWall/C/MI_RockWall_C_Simple", CJ["rock_tint"])
    GROUND = tinted("MI_RD_CaveGround", K + "Ground/MI_Ground_WA", CJ["ground_tint"])
    CUBE = "/Engine/BasicShapes/Cube"
    def box(of, mode, mat):
        b = pieces[unreal.Name(of)]
        p = piece(CUBE, mode=mode, size=(b.size.x, b.size.y, b.size.z), collision=True, raw=True); p.material = mat
        return p
    for n in ("Wall_Block", "Wall_Stone", "Wall_Corr", "Wall_Rough", "Wall_Rough_2", "Wall_Rough_3", "Wall_Rough_4", "Wall_Rough_5"):
        if unreal.Name(n) in pieces: P["Cave." + n] = box(n, "wallface", ROCK)
    for n in ("Floor_Stone", "Floor_Brick", "Floor_Brick2", "Floor_Random", "Floor_Tiles", "Floor_Wood", "Floor_Corr"):
        P["Cave." + n] = box("Floor_Stone", "floor", GROUND); P["Cave." + n + "_Alt"] = P["Cave." + n]
    P["Cave.Ceil_Room"] = box("Ceil_Room", "ceil", ROCK); P["Cave.Ceil_Corr"] = box("Ceil_Corr", "ceil", ROCK)
    for n, src in (("Face_A", "RockWall/C/SM_RockWall_C"), ("Face_B", "RockWall/A/SM_RockWall_A"), ("Face_C", "RockWall/E/SM_RockWall_E")):
        P["Cave." + n] = piece(K + src, size=(110, 280, 420))
    col = pieces.get(unreal.Name("Column")); dw = pieces.get(unreal.Name("Doorway"))
    P["Cave.Column"] = piece(K + "stalactite/A/SM_Stalacite_A", size=(None, None, float(gen.get_editor_property("room_height"))))
    if dw:
        # (a rock arch round the doorway, its size the castle doorway's; seen only: the walls either side still stop her)
        P["Cave.Doorway"] = piece(K + "Arch/A/SM_Arch_A", front="+y", size=(dw.size.x, dw.size.y + 60, dw.size.z + 40), collision=False)
    # ------------------------------------------------------------ what lies by the walls
    for n, src, h in (("Stone_A", "Stone/A/SM_Stone_A", 70), ("Stone_B", "Stone/B/SM_Stone_B", 80), ("Stone_C", "Stone/C/SM_Stone_C", 90), ("Stone_D", "Stone/D/SM_Stone_D", 55),
                      ("Mite_A", "stalactite/A/SM_Stalacite_A", 260), ("Mite_B", "stalactite/B/SM_Stalacite_B", 220), ("Mite_C", "stalactite/C/SM_Stalacite_C", 240),
                      ("Boulder", "Boulder/A/SM_Boulder_A", 120)):
        P["Cave." + n] = piece(K + src, size=(None, None, h))
    for k in [k for k in pieces if str(k).startswith("Cave.")]: del pieces[k]
    for k, p in P.items(): pieces[unreal.Name(k)] = p
    gen.set_editor_property("pieces", pieces)
    gen.set_editor_property("tier_themes", [unreal.Name("Cave")] * 5)
    gen.set_editor_property("mixed_themes", [unreal.Name("Cave")])
    gen.set_editor_property("theme_props", [unreal.Name(n) for n in CJ["props"]])
    gen.set_editor_property("theme_prop_spacing", float(CJ["prop_spacing"])); gen.set_editor_property("theme_prop_chance", float(CJ["prop_chance"]))
    gen.set_editor_property("dungeon_light_tint", unreal.LinearColor(*CJ["light"], 1.0)); gen.set_editor_property("dungeon_light_tint_share", float(CJ["light_share"]))
    for k, v in (("tier_floors", True), ("tier_floor_depth", 450.0), ("stair_tiles", 4), ("max_tier", int(CJ["max_tier"])), ("dungeon_key", "cave:test"),
                 ("dungeon_title", CJ["title"]), ("town_level", WILD), ("catacombs_level", ""), ("final_boss_on", False), ("menu_level", ""),
                 ("dungeon_tier_base", 0), ("dungeon_tier_cap", 1), ("cave15", True), ("cave_exclude15", CJ["exclude"]), ("cave_default_tier15", 1)):
        gen.set_editor_property(k, v)
    # ------------------------------------------------------------ the wilds' kinds (their bands), as text
    mons = []
    for t in texts:
        d = unreal.RDMonsterDef(); d.import_text(t); mons.append(d)
    gen.set_editor_property("monsters", mons)
    banded = [m for m in mons if m.wild_tier_max > 0]
    gen.modify(); gen.build_start_section()
    les.save_current_level()
    print("CAVE", DST, "| pieces", len(P), "| kinds", len(mons), "banded", len(banded), "| themes", [str(t) for t in gen.get_editor_property("tier_themes")],
          "| max tier", gen.get_editor_property("max_tier"), "| floors", gen.get_editor_property("tier_floors"), "| doorway arch", "Cave.Doorway" in P,
          "| column", round(P["Cave.Column"].size.z), "| wall", [round(x) for x in (P["Cave.Wall_Rough"].size.x, P["Cave.Wall_Rough"].size.y, P["Cave.Wall_Rough"].size.z)])
    del gen, pieces, P, w, mons, banded, col, dw


def wild():
    les.load_level(WILD)
    gen = gen_of_open()
    gen.set_editor_property("cave_level15", DST)
    gen.set_editor_property("cave_mouth_mesh15", unreal.load_asset(solid(K + "Arch/A/SM_Arch_A")))
    # (the pack's arch is a quarter round (its picture: 6.6 m across, 6.5 m up, its foot at its own X -624, its top at X 35 (the first whole
    # mouth, placed the other way, stood as two horns), its depth along Y): turned a quarter so its depth runs out from the tower, its top
    # on the mouth's middle, and mirrored across it (a whole round
    # arch 13 m across); sunk 40 cm for the slope across it. Inside it a dark half disc: the engine's cylinder stood on its side, its
    # middle at the ground (the first mouth, half an arch beside a dark box, read as a broken doorway))
    gen.set_editor_property("cave_mouth_yaw15", 90.0)
    gen.set_editor_property("cave_mouth_offset15", V(90.0, -35.0, -40.0))
    gen.set_editor_property("cave_mouth_scale15", V(1.0, 1.0, 1.0))
    gen.set_editor_property("cave_mouth_mirror15", True)
    # (the gap between two buttresses: the kit's buttresses stand at 0, 72, ... degrees of the tower's frame in Unreal as in Blender (no
    # flip of y: at +36 degrees the first mouths stood inside a buttress and the test stood her on its top, 28 m up)
    gen.set_editor_property("cave_gap_deg15", -36.0)
    gen.set_editor_property("cave_dark_mesh15", unreal.load_asset("/Engine/BasicShapes/Cylinder"))
    gen.set_editor_property("cave_dark_material15", dark_material())
    gen.set_editor_property("cave_dark_turn15", unreal.Rotator(roll=0.0, pitch=90.0, yaw=0.0))
    gen.set_editor_property("cave_dark_offset15", V(30.0, 0.0, -40.0))
    gen.set_editor_property("cave_dark_scale15", V(10.4, 10.4, 0.4))          # (at 11 its top showed through the arch's keystone gap)
    gen.modify(); les.save_current_level()
    print("CAVE wild: level", gen.get_editor_property("cave_level15"), "| mouth", gen.get_editor_property("cave_mouth_mesh15").get_path_name())
    del gen


arg = sys.argv[1] if len(sys.argv) > 1 else "level"
if arg == "saveas":
    assert not eal.does_asset_exist(DST), "caves exists: set it up with 935 (no argument)"
    if not ues.get_editor_world().get_path_name().startswith(SRC + "."): les.load_level(SRC)
    ok = unreal.EditorLoadingAndSavingUtils.save_map(ues.get_editor_world(), DST)
    print("CAVE saved as", DST, ok, "| quitting: start the editor again and run 935")
    unreal.SystemLibrary.quit_editor()
elif arg == "level": level()
elif arg == "wild": wild()
else: raise SystemExit("935: saveas | level | wild")
gc.collect()
