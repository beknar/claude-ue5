"""The list of 2026-11-22 (docs/improvements16.txt: "the skyscrapers and very tall office buildings can have the front door or entrances
transport them to a new level that holds only the skyscraper's floors"; the plan docs/improvements16_plan.md), its twenty-fourth phase:
the skyscrapers' level `heaven_tower`, a Save As copy of mistward_castle whose generator has bTower24 (RDTower24.cpp): no sets of rooms
or monsters; the tower built in play from the seed the game instance carries from Heaven's tower door.

    948_heaven_tower.py saveas   mistward_castle saved as heaven_tower (then the editor quits: start it again)
    948_heaven_tower.py level    heaven_tower's generator: bTower24, its pieces from SourceArt/heaven_tower/tower24.json (each pack mesh
                                 turned front to +X, centred, on z 0), its surfaces' materials, the glass, the ceiling lights' glow and the
                                 city's picture (M_HT24_View: the cube "View" sampled by the view's way, times "Scale"), the materials'
                                 instanced-mesh usage; its tactical maps and menu off, the way back to brokenspire
    948_heaven_tower.py town     brokenspire's generator: TowerLevel24 = heaven_tower (a Heaven tower's door opens it)

Run `saveas` once; then `level` and `town` (each opens its map and saves it)."""
import os, sys, json, gc
import unreal

SRC, DST = "/Game/RandomDungeon/Maps/mistward_castle", "/Game/RandomDungeon/Maps/heaven_tower"
WILD = "/Game/RandomDungeon/Maps/brokenspire"
SA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt", "heaven_tower"))
OWN = "/Game/RandomDungeon/HeavenTower"
V = unreal.Vector
EAL = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
TJ = json.load(open(os.path.join(SA, "tower24.json"), encoding="utf-8"))


def gen_of_open():
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def find(name, pack, cls="StaticMesh", mod="/Script/Engine"):
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    f = unreal.ARFilter(package_paths=["/Game/" + pack], recursive_paths=True, class_paths=[unreal.TopLevelAssetPath(mod, cls)])
    hits = [a for a in ar.get_assets(f) if str(a.asset_name) == name]
    assert hits, (name, pack, cls)
    return unreal.load_asset(str(hits[0].package_name) + "." + name)


def corners(b): return [V(x, y, z) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]


def piece(mesh, front, lift=0.0, height=None, collision=True, material=None):
    """the mesh turned so its front is +X, scaled to a height if given, centred on its footprint, its bottom on z 0 (plus lift)"""
    rot = unreal.Rotator(roll=0.0, pitch=0.0, yaw=YAW[front])
    b = mesh.get_bounding_box()
    sc = 1.0 if height is None else height / max(b.max.z - b.min.z, 1.0)
    t0 = unreal.Transform(V(0, 0, 0), rot, V(sc, sc, sc))
    pts = [unreal.MathLibrary.transform_location(t0, c) for c in corners(b)]
    mn = V(min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)); mx = V(max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
    p = unreal.RDPiece(); p.mesh = mesh
    p.adjust = unreal.Transform(V(-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z + lift), rot, V(sc, sc, sc))
    p.size = V(mx.x - mn.x, mx.y - mn.y, mx.z - mn.z); p.collision = collision
    if material is not None: p.material = material
    return p


def mat_asset(name):
    path = OWN + "/" + name
    if EAL.does_asset_exist(path):
        assert EAL.delete_asset(path), path
    return AT.create_asset(name, OWN, unreal.Material, unreal.MaterialFactoryNew())


def k3(m, rgb, x, y):
    c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, x, y); c.set_editor_property("constant", unreal.LinearColor(*rgb, 1.0)); return c


def k1(m, v, x, y):
    c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, x, y); c.set_editor_property("r", float(v)); return c


def glass_material(name, rgba):
    """a pane: unlit, see-through, its tint faint (the city's picture behind the facade's glass)"""
    m = mat_asset(name)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    m.set_editor_property("used_with_instanced_static_meshes", True)
    e = k3(m, [c * 0.08 for c in rgba[:3]], -400, 0); o = k1(m, rgba[3], -400, 200)
    assert MEL.connect_material_property(e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    assert MEL.connect_material_property(o, "", unreal.MaterialProperty.MP_OPACITY)
    print("948 the material %s: its last compile follows" % name)
    MEL.recompile_material(m); EAL.save_loaded_asset(m, False)
    return m


def light_material():
    m = mat_asset("M_HT24_Light")
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("used_with_instanced_static_meshes", True)
    L = TJ["light"]
    e = k3(m, [c * L["strength"] for c in L["emissive"]], -400, 0)
    assert MEL.connect_material_property(e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    print("948 the material M_HT24_Light: its last compile follows")
    MEL.recompile_material(m); EAL.save_loaded_asset(m, False)
    return m


def view_material():
    """the city round the tower: the cube picture sampled along the way from the eye to the point (the sphere drawn round her is at
    no distance that matters: the city reads at infinity), times Scale"""
    m = mat_asset("M_HT24_View")
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    cam = MEL.create_material_expression(m, unreal.MaterialExpressionCameraVectorWS, -900, 0)
    neg = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -700, 0)
    assert MEL.connect_material_expressions(cam, "", neg, "A") and MEL.connect_material_expressions(k1(m, -1.0, -900, 150), "", neg, "B")
    # (turned about the up axis by Turn (radians): the level's lobby doors face -Y, the tower's in Heaven its street)
    tr = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -900, 300)
    tr.set_editor_property("parameter_name", "Turn"); tr.set_editor_property("default_value", 0.0)
    cu = MEL.create_material_expression(m, unreal.MaterialExpressionCustom, -650, 150)
    ci = []
    for nm in ("D", "T"):
        x = unreal.CustomInput(); x.set_editor_property("input_name", nm); ci.append(x)
    cu.set_editor_property("inputs", ci)
    cu.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    cu.set_editor_property("code", "float c = cos(T), s = sin(T); return float3(c * D.x - s * D.y, s * D.x + c * D.y, D.z);")
    assert MEL.connect_material_expressions(neg, "", cu, "D") and MEL.connect_material_expressions(tr, "", cu, "T")
    tex = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameterCube, -400, 0)
    tex.set_editor_property("parameter_name", "View")
    tex.set_editor_property("texture", unreal.load_asset("/Engine/EngineResources/DefaultTextureCube.DefaultTextureCube"))
    assert MEL.connect_material_expressions(cu, "", tex, "UVs")
    sc = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -500, 250)
    sc.set_editor_property("parameter_name", "Scale"); sc.set_editor_property("default_value", 1.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, 100)
    assert MEL.connect_material_expressions(tex, "RGB", mul, "A") and MEL.connect_material_expressions(sc, "", mul, "B")
    assert MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    print("948 the material M_HT24_View: its last compile follows")
    MEL.recompile_material(m); EAL.save_loaded_asset(m, False)
    return m


def usage(mats, nanite=False):
    """the instanced-mesh usage (and Nanite's for a Nanite mesh) on the base materials, saved (a package draws without it in the default)"""
    done = 0
    for mi in mats:
        if not mi: continue
        b = mi.get_base_material()
        if not b or not b.get_path_name().startswith("/Game/"): continue
        ch = False
        if not b.get_editor_property("used_with_instanced_static_meshes"): b.set_editor_property("used_with_instanced_static_meshes", True); ch = True
        if nanite and not b.get_editor_property("used_with_nanite"): b.set_editor_property("used_with_nanite", True); ch = True
        if ch: MEL.recompile_material(b); EAL.save_loaded_asset(b, False); done += 1
    return done


def level():
    les.load_level(DST)
    g = gen_of_open()
    light = light_material()
    pcs = {}
    for name, d in TJ["pieces"].items():
        mesh = find(d["mesh"], d["pack"])
        pcs[unreal.Name(name)] = piece(mesh, d["front"], float(d.get("lift", 0.0)), d.get("height"), bool(d.get("collision", True)), light if d.get("material") == "light" else None)
    g.set_editor_property("tower_pieces24", pcs)
    mats = {}
    for prop, nm in TJ["materials"].items():
        mats[prop] = find(nm, "Office_Environment", "MaterialInstanceConstant")
        g.set_editor_property(prop, mats[prop])
    G = TJ["glass"]
    g.set_editor_property("tower_glass_mat24", glass_material("M_HT24_Glass", G["outer"]))
    g.set_editor_property("tower_inner_glass_mat24", glass_material("M_HT24_InnerGlass", G["inner"]))
    g.set_editor_property("tower_door_glass_mat24", glass_material("M_HT24_DoorGlass", G["door"]))
    g.set_editor_property("tower_view_mat24", view_material())
    g.set_editor_property("tower_cube24", unreal.load_asset("/Engine/BasicShapes/Cube"))
    g.set_editor_property("tower_sphere24", unreal.load_asset("/Engine/BasicShapes/Sphere"))
    for k, v in (("tower24", True), ("tactical_maps", False), ("dungeon_key", "tower:test"), ("dungeon_title", "Heaven's tower"),
                 ("town_level", WILD), ("catacombs_level", ""), ("final_boss_on", False), ("menu_level", "")):
        g.set_editor_property(k, v)
    # (the pieces' and surfaces' materials: their instanced-mesh usage)
    n = 0
    for p in pcs.values():
        ms = [p.material] if p.material else [p.mesh.get_material(i) for i in range(len(p.mesh.get_editor_property("static_materials")))]
        n += usage(ms, p.mesh.get_editor_property("nanite_settings").enabled)
    n += usage(list(mats.values()))
    g.modify(); les.save_current_level()
    print("948 level", DST, "| pieces", len(pcs), "| materials", len(mats), "| bases given the usage", n,
          "| sizes", {str(k): [round(x) for x in (p.size.x, p.size.y, p.size.z)] for k, p in list(pcs.items())[:6]})


def town():
    les.load_level(WILD)
    g = gen_of_open()
    g.set_editor_property("tower_level24", DST)
    g.modify(); les.save_current_level()
    print("948 town: brokenspire's towers open", g.get_editor_property("tower_level24"))


arg = sys.argv[1] if len(sys.argv) > 1 else "level"
if arg == "saveas":
    assert not EAL.does_asset_exist(DST), "heaven_tower exists: set it up with 948 level"
    if not ues.get_editor_world().get_path_name().startswith(SRC + "."): les.load_level(SRC)
    ok = unreal.EditorLoadingAndSavingUtils.save_map(ues.get_editor_world(), DST)
    print("948 saved as", DST, ok, "| quitting: start the editor again and run 948 level")
    unreal.SystemLibrary.quit_editor()
elif arg == "level": level()
elif arg == "town": town()
else: raise SystemExit("948: saveas | level | town")
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
