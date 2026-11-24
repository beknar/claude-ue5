"""The list of 2026-11-22 (docs/improvements16.txt, "the city of heaven"; the plan docs/improvements16_plan.md), Heaven's stages on
`brokenspire` (946 the city, 947 its fortress, 948 the skyscrapers' level). Phase 18, Heaven's first fixes:

    946_heaven16.py lamps     the street light's lamp head measured on its mesh (the arm's far end, the head's underside, in the piece's
                              frame) into the generator's HeavenLampHead16; a glowing lens under it (Heaven.LampGlow, a box in the
                              kit's lit panel, no collision)
    946_heaven16.py signs     Heaven's modern sign board (Heaven.Town.Sign: a 63 x 47 cm dark panel with a steel rim on an arm, the
                              faces' plane where the town's shield board has its) and its lit faces (Heaven.Town.SignFace_<WORDS>:
                              bs_signs.py --modern's pictures in SourceArt/heaven/signs16, an emissive material of our own)
    946_heaven16.py symbols   the 19 map pictograms of SourceArt/heaven/art16/map (hvmap_*.png) into the generator's UI art
                              under their ids (T_RDM4_<id> under /Game/RandomDungeon/UI)
    946_heaven16.py all       the three

Run on the editor with any level open (it opens brokenspire and saves it)."""
import os, sys, json, importlib
import unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heaven_kit as hk; importlib.reload(hk)
import ui_tex; importlib.reload(ui_tex)

V = unreal.Vector
EAL = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MAP = "/Game/RandomDungeon/Maps/brokenspire"
SA = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "claude_ue5", "SourceArt"))
HV16 = "/Game/RandomDungeon/Heaven/List16"
REPORT = []


def gen():
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def set_pieces(g, add):
    pcs = g.get_editor_property("pieces")
    for k, p in add.items(): pcs[unreal.Name(k)] = p
    g.set_editor_property("pieces", pcs)


def raw(mesh, size=None, collision=False, material=None):
    p = unreal.RDPiece(); p.mesh = mesh; p.adjust = unreal.Transform()
    b = mesh.get_bounding_box()
    p.size = V(*size) if size else V(b.max.x - b.min.x, b.max.y - b.min.y, b.max.z - b.min.z)
    p.collision = collision
    if material is not None: p.material = material
    return p


# ================================================================================================ the street lamps
def lamps(g):
    pcs = g.get_editor_property("pieces")
    p = pcs.get(unreal.Name("Heaven.StreetLight"))
    assert p and p.mesh, "946 lamps: no Heaven.StreetLight (908 first)"
    m = p.mesh; adj = p.adjust
    pts = []
    try:
        for sec in range(m.get_num_sections(0)):
            r = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(m, 0, sec)
            pts += [unreal.MathLibrary.transform_location(adj, v) for v in r[0]]
    except Exception as e:
        REPORT.append(f"lamps: no vertices read ({str(e)[:80]})")
    if pts:
        mx = max(q.x for q in pts); top = max(q.z for q in pts)
        # (the head: the vertices of the arm's last 45 cm over 3 m up; the light under its underside, at its middle across)
        head = [q for q in pts if q.x > mx - 45.0 and q.z > 300.0]
        hx = sum(q.x for q in head) / len(head); hy = sum(q.y for q in head) / len(head); hz = min(q.z for q in head)
        how = f"{len(pts)} vertices, the head {len(head)}"
    else:
        b = m.get_bounding_box()
        c = [unreal.MathLibrary.transform_location(adj, V(x, y, z)) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]
        mx = max(q.x for q in c); top = max(q.z for q in c); hx, hy, hz = mx - 30.0, 0.0, top - 45.0
        how = "the bounds (no vertices)"
    g.set_editor_property("heaven_lamp_head16", V(hx, hy, hz))
    mats = hk.materials()
    glow = hk.boxes("SM_HV_LampGlow", [(-24, 24, -16, 16, -4, 2, "panel")], mats, rebuild=True)
    set_pieces(g, {"Heaven.LampGlow": raw(glow, collision=False)})
    REPORT.append(f"lamps: the head at ({hx:.0f}, {hy:.0f}, {hz:.0f}) cm of the pole (its top {top:.0f}, its arm to {mx:.0f}; {how}); Heaven.LampGlow")


# ================================================================================================ the modern signs
def face_material():
    path = HV16 + "/M_HV_SignFace"
    if EAL.does_asset_exist(path): EAL.delete_asset(path)
    m = AT.create_asset("M_HV_SignFace", HV16, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("used_with_instanced_static_meshes", True)
    t = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -600, 0); t.set_editor_property("parameter_name", "Face")
    g_ = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -600, 250); g_.set_editor_property("parameter_name", "Glow"); g_.set_editor_property("default_value", 2.2)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, 150)
    assert MEL.connect_material_expressions(t, "RGB", mul, "A") and MEL.connect_material_expressions(g_, "", mul, "B")
    r = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, 300); r.set_editor_property("r", 0.15)
    assert MEL.connect_material_property(t, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    assert MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    assert MEL.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    print("946 signs: the face material's last compile follows")
    MEL.recompile_material(m); EAL.save_loaded_asset(m, False)
    return m


def signs(g):
    src = os.path.join(SA, "heaven", "signs16")
    files = sorted(f for f in os.listdir(src) if f.startswith("sign_") and f.endswith(".png")) if os.path.isdir(src) else []
    assert files, "946 signs: no pictures (run blender_numpy/bs_signs.py SourceArt/heaven/signs16 --modern first)"
    mats = hk.materials()
    # (the board: a panel 63 x 6 x 47.2 cm about the faces' middle (x 90.4, z -89.5 in the sign's frame), a steel rim round it 2 cm
    # proud and thinner (the faces stand on the panel's), an arm to the wall and its plate)
    board = hk.boxes("SM_HV_SignBoard", [(58.9, 121.9, -3, 3, -113.1, -65.9, "dark"), (57.6, 123.2, -2.4, 2.4, -114.4, -64.6, "steel"),
                                         (0, 60, -2, 2, -62, -58, "steel"), (0, 3, -9, 9, -72, -48, "steel")], mats, rebuild=True)
    add = {"Heaven.Town.Sign": raw(board, collision=False)}
    base = face_material()
    plane = unreal.load_asset("/Engine/BasicShapes/Plane")
    for f in files:
        key = f[5:-4]
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", os.path.join(src, f)); t.set_editor_property("destination_path", HV16)
        t.set_editor_property("destination_name", "T_HV_Sign_" + key); t.set_editor_property("replace_existing", True)
        t.set_editor_property("automated", True); t.set_editor_property("save", True)
        AT.import_asset_tasks([t])
        tex = unreal.load_asset(f"{HV16}/T_HV_Sign_{key}")
        assert tex, f"946 signs: {f} was not imported"
        mp = f"{HV16}/MI_HV_Sign_{key}"
        mi = unreal.load_asset(mp) if EAL.does_asset_exist(mp) else AT.create_asset(f"MI_HV_Sign_{key}", HV16, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, base)
        MEL.set_material_instance_texture_parameter_value(mi, "Face", tex)
        MEL.update_material_instance(mi); EAL.save_loaded_asset(mi, False)
        p = unreal.RDPiece(); p.mesh = plane; p.collision = False; p.material = mi
        # (as 890's faces: the plane's +Z turned to +Y, its X along the board, its height down -Z: the board's 63 x 47.25 cm)
        r = unreal.MathLibrary.make_rot_from_zx(V(0, 1, 0), V(1, 0, 0))
        p.adjust = unreal.Transform(V(0, 0, 0), r, V(0.63, 0.4725, 1.0)); p.size = V(63, 2, 47.25)
        add[f"Heaven.Town.SignFace_{key}"] = p
    set_pieces(g, add)
    REPORT.append(f"signs: Heaven.Town.Sign and {len(files)} faces: {', '.join(f[5:-4] for f in files)}")


# ================================================================================================ the map's pictograms
def symbols(g):
    src = os.path.join(SA, "heaven", "art16", "map")          # (the chosen pictures, as spec.json's "chosen" names them, beside it)
    files = sorted(f for f in os.listdir(src) if f.startswith("hvmap_") and f.endswith(".png"))
    assert len(files) >= 12, f"946 symbols: {len(files)} pictures in {src}"
    ua = g.get_editor_property("ui_art")
    for f in files:
        n = f[:-4]
        tex = ui_tex.ui_texture(os.path.join(src, f), "/Game/RandomDungeon/UI", "T_RDM4_" + n)
        art = unreal.RDUIArt(); art.set_editor_property("texture", tex)
        art.set_editor_property("border", unreal.Vector4(0, 0, 0, 0)); art.set_editor_property("inner", unreal.Vector4(0, 0, 1, 1))
        ua[unreal.Name(n)] = art
    g.set_editor_property("ui_art", ua)
    REPORT.append(f"symbols: {len(files)} pictograms into the UI art")


PARTS = {"lamps": lamps, "signs": signs, "symbols": symbols}
args = sys.argv[1:] or ["all"]
todo = list(PARTS) if args[0] == "all" else args[0].split(",")
g = gen()
for t in todo: PARTS[t](g)
g.modify(); les.save_current_level()
for l in REPORT: print("946", l)
del g
import gc; gc.collect()
