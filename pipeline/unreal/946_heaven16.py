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
    946_heaven16.py streets   phase 19, Heaven's streets: the markings' paint (Heaven.Mark, a unit square stretched to each line), the
                              four-way signal (Heaven.Signal19) and its lens (Heaven.SignalLens19 in M_HV_SignalLens: its colour and
                              light per instance), the stop, street-name and district signs, the names and timings of
                              SourceArt/heaven/streets19.json; and the medieval things' modern stand-ins under Heaven's theme (the
                              wall lamp for the torch, a desk lamp for the candles, a ceiling light, a media wall for the hearth, a
                              cooker and pot for the tripod and cauldron, a wall shelf, a picture for the shield; in the streets a
                              trailer for the cart, a parked car for the wagon, a dumpster for the hay, pallets for the logs, a bin
                              for the sacks, a bollard light for the fire basket)
    946_heaven16.py storeys   phase 20, Heaven's storeys: the stair's flight (Heaven.Stair20: 15 steps of 20 cm over 6 m, 2.5 m wide, a
                              box each so each step is stood on), the rail round an opening (Heaven.Rail20), the lift shaft's glass side
                              (Heaven.LiftWall20), its platform (Heaven.LiftPlatform20), the upper storeys' ceiling panel
                              (Heaven.CeilingPanel20)
    946_heaven16.py shops     phase 21, Heaven's shops, services and containers: three gondola shelves full of goods (a grocery's, a
                              pharmacy's, a hardware store's: Heaven.Gondola21_<0-2>), the checkout (Heaven.Checkout21), the clinic's
                              desk (Heaven.Fountain), the bank's vault (Heaven.Town.StashChest), the gear shop's bench, vice and parts bin
                              (Heaven.Forge, .Anvil, .QuenchTub), the modern containers, each a body and its door or lid on its hinge
                              (Heaven.Barrel a fridge, .Barrel2 a filing cabinet, .Crate a tool chest, .Crate2 a bin, .Chest a safe,
                              .Wardrobe a locker, Heaven.Dumpster21 the yards' dumpster) and their words (ContainerWords21)
    946_heaven16.py goods     phase 22, Heaven's goods on every map of the game: the everyday items' modern twins of
                              SourceArt/heaven/goods22.json (copied from their likes, no weight in any draw) and their pictures
                              (SourceArt/heaven/art22/icons), the map's HeavenGoods22; run it after the item stages
    946_heaven16.py life      phase 22, Heaven's life on brokenspire: the neon tube, the billboard's frame and faces
                              (SourceArt/heaven/art22/billboards), the tables' modern food, the city's sounds (SourceArt/heaven/city22.json)
    946_heaven16.py all       the eight but goods (every map: ask for it by name)

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
    glow = hk.boxes("SM_HV_LampGlow", [(-24, 24, -16, 16, -4, 2, "panel")], mats)
    # (the facility's tower's red air lights and beacon: lit boxes (a point light lights faces round it and is cut at the town's 45 m;
    # these stand 70 to 160 m up: PR #125's review))
    air = hk.boxes("SM_HV_AirLight", [(-45, 45, -45, 45, -25, 25, "red")], mats)
    set_pieces(g, {"Heaven.LampGlow": raw(glow, collision=False), "Heaven.AirLight": raw(air, collision=False)})
    REPORT.append(f"lamps: the head at ({hx:.0f}, {hy:.0f}, {hz:.0f}) cm of the pole (its top {top:.0f}, its arm to {mx:.0f}; {how}); Heaven.LampGlow")


# ================================================================================================ the modern signs
def face_material():
    path = HV16 + "/M_HV_SignFace"
    # (made once and kept: the faces' instances are its children and the level holds them (PR #125's review: a delete of a used asset
    # leaves them parentless in memory if the new one is refused))
    if EAL.does_asset_exist(path): return unreal.load_asset(path)
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
    # (the panel hung from the arm by two short rods (PR #125's review: it hung 2.6 cm under the arm, unjoined); a new name for the new
    # shape (the level holds the old one: nothing it uses is deleted))
    board = hk.boxes("SM_HV_SignBoard2", [(58.9, 121.9, -3, 3, -113.1, -65.9, "dark"), (57.6, 123.2, -2.4, 2.4, -114.4, -64.6, "steel"),
                                          (0, 124, -2, 2, -62, -58, "steel"), (0, 3, -9, 9, -72, -48, "steel"),
                                          (64, 67, -1.2, 1.2, -65.5, -58, "steel"), (114, 117, -1.2, 1.2, -65.5, -58, "steel")], mats)
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


# ================================================================================================ phase 19: the streets
def lens_material():
    path = HV16 + "/M_HV_SignalLens"
    # (made once and kept, as the sign faces' (the level's lenses use it); its colour and light per instance: data 0-2 the colour,
    # 3 lit; dim when not lit)
    if EAL.does_asset_exist(path): return unreal.load_asset(path)
    m = AT.create_asset("M_HV_SignalLens", HV16, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("used_with_instanced_static_meshes", True)
    col = MEL.create_material_expression(m, unreal.MaterialExpressionPerInstanceCustomData3Vector, -800, 0); col.set_editor_property("data_index", 0)
    lit = MEL.create_material_expression(m, unreal.MaterialExpressionPerInstanceCustomData, -800, 200); lit.set_editor_property("data_index", 3)
    k = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -800, 350); k.set_editor_property("r", 30.0)
    k0 = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -800, 450); k0.set_editor_property("r", 0.04)
    mk = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -550, 250)
    assert MEL.connect_material_expressions(lit, "", mk, "A") and MEL.connect_material_expressions(k, "", mk, "B")
    ad = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -400, 300)
    assert MEL.connect_material_expressions(mk, "", ad, "A") and MEL.connect_material_expressions(k0, "", ad, "B")
    em = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, 150)
    assert MEL.connect_material_expressions(col, "", em, "A") and MEL.connect_material_expressions(ad, "", em, "B")
    kb = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -550, -100); kb.set_editor_property("r", 0.05)
    bc = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, -50)
    assert MEL.connect_material_expressions(col, "", bc, "A") and MEL.connect_material_expressions(kb, "", bc, "B")
    r = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -250, 400); r.set_editor_property("r", 0.2)
    assert MEL.connect_material_property(bc, "", unreal.MaterialProperty.MP_BASE_COLOR)
    assert MEL.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    assert MEL.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    print("946 streets: the lens material's last compile follows")
    MEL.recompile_material(m); EAL.save_loaded_asset(m, False)
    return m


def octagon(x0, x1, zc, w, mk):
    """a regular octagon w across in the y-z plane (its middle at y 0, z zc), x0 to x1 thick, as three boxes"""
    s_ = w / (1 + 2 ** 0.5); c = (w - s_) / 2
    return [(x0, x1, -w / 2, w / 2, zc - s_ / 2, zc + s_ / 2, mk), (x0, x1, -s_ / 2, s_ / 2, zc - w / 2, zc + w / 2, mk),
            (x0, x1, -(w - c) / 2, (w - c) / 2, zc - (w - c) / 2, zc + (w - c) / 2, mk)]


def copy_piece(src, collision=None):
    p = unreal.RDPiece(); p.mesh = src.mesh; p.adjust = src.adjust; p.size = src.size; p.material = src.material
    p.collision = src.collision if collision is None else collision
    return p


def streets(g):
    data = json.load(open(os.path.join(SA, "heaven", "streets19.json"), encoding="utf-8"))
    mats = hk.materials()
    lens = lens_material()
    pcs = g.get_editor_property("pieces")
    B = lambda n, parts: hk.boxes(n, parts, mats)
    add = {}
    # ---- the streets: paint, the signal, its lens, the signs (each sign's frame: its face +X, the street sign's blades along +X and +Y)
    add["Heaven.Mark"] = raw(B("SM_HV_Mark19", [(-50, 50, -50, 50, 2.3, 3.5, "paint")]))
    sig = B("SM_HV_Signal19", [(-20, 20, -20, 20, 0, 4, "steel"), (-8, 8, -8, 8, 4, 300, "steel"), (-22, 22, -22, 22, 300, 410, "dark"), (-24, 24, -24, 24, 410, 414, "steel")])
    add["Heaven.Signal19"] = raw(sig, collision=True)
    lp = raw(B("SM_HV_SignalLens19", [(0, 3, -10, 10, -10, 10, "steel")])); lp.material = lens
    add["Heaven.SignalLens19"] = lp
    add["Heaven.StopSign19"] = raw(B("SM_HV_StopSign19", [(-3, 3, -3, 3, 0, 262, "steel")] + octagon(-1.5, 0, 225, 78, "steel") + octagon(0, 1.5, 225, 76, "stopred")), collision=True)
    add["Heaven.StreetSign19"] = raw(B("SM_HV_StreetSign19", [(-4, 4, -4, 4, 0, 350, "steel"), (8, 142, -2, 2, 300, 322, "signgreen"), (-2, 2, 8, 142, 326, 348, "signgreen")]), collision=True)
    add["Heaven.DistrictSign19"] = raw(B("SM_HV_DistrictSign19", [(-4, 4, -144, -136, 0, 300, "steel"), (-4, 4, 136, 144, 0, 300, "steel"), (-4, 4, -150, 150, 210, 300, "signblue")]), collision=True)
    # ---- the medieval things' stand-ins (each in its original's frame: the torch's back on the wall at x 0, out +X, its light's point the
    # hinge; the hearth's front +X; the shield's picture as its board stood; things on the floor at z 0)
    t = raw(B("SM_HV_WallLamp19", [(0, 3, -9, 9, 40, 72, "steel"), (3, 15, -7, 7, 44, 68, "panel")])); t.hinge = V(15, 0, 56)
    add["Heaven.Torch"] = t
    add["Heaven.Candles"] = raw(B("SM_HV_DeskLamp19", [(-7, 7, -7, 7, 0, 2, "steel"), (-1, 1, -1, 1, 2, 30, "steel"), (-10, 10, -10, 10, 30, 40, "white"), (-7, 7, -7, 7, 28.5, 30, "panel")]))
    add["Heaven.Chandelier"] = raw(B("SM_HV_CeilingLight19", [(-1.5, 1.5, -1.5, 1.5, 12, 60, "steel"), (-50, 50, -50, 50, 6, 12, "white"), (-46, 46, -46, 46, 3, 6, "panel")]))
    add["Heaven.Fireplace"] = raw(B("SM_HV_Media19", [(-25, 20, -110, 110, 0, 55, "dark"), (-25, 20, -110, 110, 55, 58, "white"), (-25, -21, -80, 80, 95, 190, "glass"),
                                                       (-21, -20.5, -76, 76, 99, 186, "screen"), (-25, -22, -6, 6, 58, 95, "steel")]), collision=True)
    add["Heaven.Tripod"] = raw(B("SM_HV_Cooker19", [(-38, 38, -30, 30, 0, 88, "white"), (-38, 38, -30, 30, 88, 92, "dark"), (38, 39, -24, 24, 25, 65, "glass")]), collision=True)
    add["Heaven.Cauldron"] = raw(B("SM_HV_Pot19", [(-15, 15, -15, 15, 92, 110, "steel"), (-2, 2, 15, 26, 104, 107, "dark")]))
    add["Heaven.PotRack"] = raw(B("SM_HV_WallShelf19", [(-12, 12, -65, 65, 150, 153, "steel"), (-12, -9, -60, -57, 130, 150, "steel"), (-12, -9, 57, 60, 130, 150, "steel"),
                                                         (-8, 8, -50, -30, 153, 163, "steel"), (-9, 9, -10, 10, 153, 168, "steel"), (-7, 7, 30, 48, 153, 160, "steel")]))
    add["Heaven.Shield"] = raw(B("SM_HV_Picture19", [(27, 31, -42, 42, -30, 30, "dark"), (31, 32, -38, 38, -26, 26, "art")]))
    add["Heaven.Town.Cart"] = raw(B("SM_HV_Trailer19", [(-160, 140, -75, 75, 45, 55, "steel"), (-150, 140, -72, 72, 55, 60, "dark"), (-150, 140, 72, 75, 60, 100, "steel"),
                                                         (-150, 140, -75, -72, 60, 100, "steel"), (-153, -150, -75, 75, 60, 100, "steel"), (137, 140, -75, 75, 60, 100, "steel"),
                                                         (140, 235, -3, 3, 45, 52, "steel"), (-45, 15, 78, 96, 0, 60, "tyre"), (-45, 15, -96, -78, 0, 60, "tyre"),
                                                         (-45, 15, 75, 100, 58, 64, "steel"), (-45, 15, -100, -75, 58, 64, "steel")]), collision=True)
    add["Heaven.Town.Hay"] = raw(B("SM_HV_Dumpster19", [(-90, 90, -55, 55, 15, 125, "dumpster"), (-92, 92, -57, 57, 125, 131, "dark"), (-80, -65, -45, -30, 0, 15, "tyre"),
                                                         (65, 80, -45, -30, 0, 15, "tyre"), (-80, -65, 30, 45, 0, 15, "tyre"), (65, 80, 30, 45, 0, 15, "tyre")]), collision=True)
    pal = []
    for k in range(3):
        z0 = k * 14
        pal += [(-60, 60, y0, y0 + 10, z0, z0 + 11, "pallet") for y0 in (-50, -5, 40)] + [(-60, 60, -50, 50, z0 + 11, z0 + 14, "pallet")]
    add["Heaven.Town.Logs"] = raw(B("SM_HV_Pallets19", pal + [(-55, 55, -45, 45, 42, 120, "carton")]), collision=True)
    add["Heaven.Town.Lamp"] = raw(B("SM_HV_Bollard19", [(-10, 10, -10, 10, 0, 100, "steel"), (-10.5, 10.5, -10.5, 10.5, 78, 92, "panel"), (-11, 11, -11, 11, 100, 104, "dark")]), collision=True)
    car = pcs.get(unreal.Name("Heaven.Car_3")); bin_ = pcs.get(unreal.Name("Heaven.Bin"))
    assert car and car.mesh and bin_ and bin_.mesh, "946 streets: no Heaven.Car_3 or Heaven.Bin (908 first)"
    add["Heaven.Town.Cart2"] = copy_piece(car, True); add["Heaven.Town.Sacks"] = copy_piece(bin_, True)
    set_pieces(g, add)
    g.set_editor_property("heaven_street_names19", data["street_names"]); g.set_editor_property("heaven_district_names19", data["districts"])
    g.set_editor_property("signal_green19", data["signal"]["green"]); g.set_editor_property("signal_amber19", data["signal"]["amber"])
    g.set_editor_property("signal_all_red19", data["signal"]["all_red"]); g.set_editor_property("heaven_lots19", data["lots"])
    g.set_editor_property("signal_head19", V(22.0, 0.0, 355.0)); g.set_editor_property("stop_sign_face19", 225.0)
    g.set_editor_property("street_blade19", V(75.0, 311.0, 337.0)); g.set_editor_property("district_face19", 255.0)
    REPORT.append(f"streets: {len(add)} pieces ({', '.join(sorted(add))}); {len(data['street_names'])} street names, districts {', '.join(data['districts'])}")


# ================================================================================================ phase 20: the storeys
def storeys(g):
    mats = hk.materials()
    B = lambda n, parts: hk.boxes(n, parts, mats)
    add = {}
    # (a flight in its own frame: its foot at x 0, rising along +x 300 cm over 600 in 15 steps of 20 by 40, 250 wide (the walls stand
    # 20 cm into a tile's edge: at 270 the flight by the back wall went 5 cm into it (PR #127's review), a new name for the new shape),
    # each step's dark nosing)
    steps = [(40 * i, 40 * (i + 1), -125, 125, 0, 20 * (i + 1), "concrete") for i in range(15)]
    steps += [(40 * i, 40 * (i + 1), -125, 125, 20 * (i + 1) - 2, 20 * (i + 1), "dark") for i in range(15)]
    add["Heaven.Stair20"] = raw(B("SM_HV_Stair20b", steps), collision=True)
    # (a rail along its own Y, 300 long: a glass panel 1 m high between a base and a steel top bar)
    add["Heaven.Rail20"] = raw(B("SM_HV_Rail20", [(-3, 3, -150, 150, 0, 10, "steel"), (-1, 1, -148, 148, 10, 100, "glass"), (-2.5, 2.5, -150, 150, 100, 106, "steel"),
                                                  (-3, 3, -150, -144, 0, 106, "steel"), (-3, 3, 144, 150, 0, 106, "steel")]), collision=True)
    # (the shaft's side: a storey's height of glass in a steel frame along its own Y)
    add["Heaven.LiftWall20"] = raw(B("SM_HV_LiftWall20", [(-2, 2, -148, 148, 0, 300, "glass"), (-4, 4, -150, -144, 0, 300, "steel"), (-4, 4, 144, 150, 0, 300, "steel"),
                                                          (-4, 4, -150, 150, 0, 8, "steel"), (-4, 4, -150, 150, 292, 300, "steel")]), collision=True)
    # (the platform: a steel plate 2.5 m square (clear of the walls' 20 cm into the tile), its top at its origin, a hazard stripe round its rim)
    add["Heaven.LiftPlatform20"] = raw(B("SM_HV_LiftPlatform20b", [(-125, 125, -125, 125, -20, -1, "plate"), (-125, 125, -125, 125, -1, 0, "plate"),
                                                                   (-125, 125, -125, -115, 0, 0.6, "hazard"), (-125, 125, 115, 125, 0, 0.6, "hazard"),
                                                                   (-125, -115, -115, 115, 0, 0.6, "hazard"), (115, 125, -115, 115, 0, 0.6, "hazard")]), collision=True)
    add["Heaven.CeilingPanel20"] = raw(B("SM_HV_CeilingPanel20", [(-62, 62, -32, 32, 0, 2, "steel"), (-60, 60, -30, 30, -1, 0, "panel")]))
    # (the roof's slabs and parapet collide where a core reaches the roof (the section asks for it only there); 908 made them without:
    # run this after 908)
    pcs = g.get_editor_property("pieces")
    for k in ("Modern.Roof", "Modern.Parapet"):
        p_ = pcs.get(unreal.Name(k)); assert p_ and p_.mesh, f"946 storeys: no {k} (908 first)"
        add[k] = copy_piece(p_, True)
    set_pieces(g, add)
    REPORT.append(f"storeys: {len(add)} pieces ({', '.join(sorted(add))})")


# ================================================================================================ phase 21: shops, services, containers
GOODS21 = {0: ["prod_red", "prod_yellow", "prod_orange", "prod_green", "prod_blue", "prod_brown", "white"],
           1: ["white", "white", "prod_mint", "prod_blue", "prod_green", "prod_mint"],
           2: ["steel", "prod_orange", "prod_yellow", "dark", "prod_red", "hazard"]}


def gondola21(kind):
    """a double-sided gondola shelf in its frame (long along Y, 120 cm; 90 deep along X; 170 tall), four shelves each side, each shelf
    full of the shop's goods (boxes of the kind's colours, sizes by a seeded draw)"""
    import random
    rr = random.Random(2100 + kind)
    parts = [(-45, 45, -60, 60, 0, 10, "dark"), (-2, 2, -60, 60, 10, 170, "white"), (-45, 45, -61, -59, 0, 170, "steel"), (-45, 45, 59, 61, 0, 170, "steel")]
    levels = [10, 50, 90, 130]
    for sgn in (-1, 1):
        for z in levels:
            parts.append((2 if sgn > 0 else -45, 45 if sgn > 0 else -2, -59, 59, z, z + 2, "white"))
            y = -57.0
            while True:
                w = rr.uniform(7.0, 17.0)
                if y + w > 57.0: break
                d = rr.uniform(24.0, 38.0); h = rr.uniform(11.0, 34.0)
                x0, x1 = (3.0, 3.0 + d) if sgn > 0 else (-3.0 - d, -3.0)
                parts.append((x0, x1, y, y + w, z + 2, z + 2 + h, rr.choice(GOODS21[kind])))
                y += w + rr.uniform(0.6, 2.0)
    return parts


def shops(g):
    mats = hk.materials()
    B = lambda n, parts: hk.boxes(n, parts, mats)
    add = {}
    for k in range(3):
        add[f"Heaven.Gondola21_{k}"] = raw(B(f"SM_HV_Gondola21_{k}", gondola21(k)), collision=True)
    # (the checkout: its length along its X, the clerk's side its +Y (the screen toward the clerk), the belt and scanner on its top)
    add["Heaven.Checkout21"] = raw(B("SM_HV_Checkout21", [(-90, 90, -35, 35, 0, 95, "dark"), (-92, 92, -37, 37, 95, 98, "steel"), (-85, 20, -30, 30, 98, 99, "tyre"),
                                                           (25, 45, -20, 0, 98, 99, "glass"), (40, 44, 10, 30, 110, 140, "glass"), (41, 43, 18, 22, 98, 110, "steel")]), collision=True)
    # (the clinic's desk, its front +X toward the door, a cyan band across it, a screen on it)
    add["Heaven.Fountain"] = raw(B("SM_HV_ClinicDesk21", [(-40, 40, -100, 100, 0, 105, "white"), (-42, 42, -102, 102, 105, 108, "steel"), (40, 41, -100, 100, 60, 72, "cyan"),
                                                          (-20, -16, -30, 10, 108, 150, "glass"), (-19, -17, -12, -8, 108, 115, "steel")]), collision=True)
    # (the bank's vault: its door in a steel plate against the back wall, its front +X, a wheel and bolts)
    vault = raw(B("SM_HV_Vault21", [(-15, -5, -110, 110, 0, 230, "steel"), (-5, 8, -80, 80, 20, 210, "plate"), (8, 14, -25, 25, 100, 106, "steel"),
                                                            (8, 14, -3, 3, 78, 128, "steel"), (8, 12, -60, -50, 60, 170, "dark"), (8, 12, 50, 60, 60, 170, "dark")]), collision=True)
    # (the service's point is 90 cm in from the back wall's line: the plate's back set onto the wall's face (PR #128's review: it stood
    # 75 cm out))
    vault.adjust = unreal.Transform(V(-55, 0, 0), unreal.Rotator(0, 0, 0), V(1, 1, 1)); add["Heaven.Town.StashChest"] = vault
    # (the gear shop: a workbench with a pegboard of tools for the forge, a vice on a stand for the anvil, a parts bin for the quench tub)
    add["Heaven.Forge"] = raw(B("SM_HV_Workbench21", [(-40, 40, -95, 95, 0, 86, "steel"), (-42, 42, -97, 97, 86, 92, "pallet"), (-45, -42, -95, 95, 92, 200, "plate"),
                                                      (-42, -38, -70, -60, 120, 170, "hazard"), (-42, -38, -30, -25, 110, 180, "dark"), (-42, -38, 20, 40, 130, 150, "prod_red"), (-42, -38, 60, 66, 115, 175, "steel")]), collision=True)
    add["Heaven.Anvil"] = raw(B("SM_HV_Vice21", [(-25, 25, -40, 40, 0, 85, "steel"), (-27, 27, -42, 42, 85, 88, "dark"), (-10, 10, -15, 15, 88, 104, "dark"), (8, 14, -3, 3, 92, 98, "steel")]), collision=True)
    add["Heaven.QuenchTub"] = raw(B("SM_HV_PartsBin21", [(-40, 40, -40, 40, 0, 50, "prod_blue"), (-38, 38, -38, 38, 50, 52, "dark")]), collision=True)
    # (the containers: a body, its moving part's mesh from its hinge (a door along +Y or -Y from an upright hinge, a lid along +X from its
    # back), the piece's hinge in the body's frame; front +X)
    def cont(name, body, mov, hinge, mov2=None, hinge2=None, word=None):
        p = raw(B(f"SM_HV_{name}21", body), collision=True)
        p.moving = B(f"SM_HV_{name}21_Door", mov); p.hinge = V(*hinge)
        if mov2:
            p.moving2 = B(f"SM_HV_{name}21_Door2", mov2); p.hinge2 = V(*hinge2)
        return p
    def shell(x0, x1, y0, y1, z0, z1, t, mk, open_x=True):
        """a box open at its front (+X): back, sides, top, bottom"""
        return [(x0, x0 + t, y0, y1, z0, z1, mk), (x0, x1, y0, y0 + t, z0, z1, mk), (x0, x1, y1 - t, y1, z0, z1, mk), (x0, x1, y0, y1, z1 - t, z1, mk), (x0, x1, y0, y1, z0, z0 + t, mk)]
    add["Heaven.Barrel"] = cont("Fridge", shell(-32, 30, -33, 33, 0, 175, 4, "white") + [(-28, 28, -29, 29, z, z + 1.5, "glass") for z in (55, 105, 140)],
                                [(0, 5, 0, 66, 0, 165, "white"), (5, 8, 58, 61, 80, 130, "steel")], (30, -33, 6))
    add["Heaven.Barrel2"] = cont("Filing", shell(-25, 23, -23, 23, 0, 132, 3, "steel") + [(-22, 20, -20, 20, z, z + 1.5, "dark") for z in (33, 66, 99)],
                                 [(0, 3, 0, 46, 0, 128, "steel")] + [(3, 5, 18, 28, z, z + 3, "dark") for z in (25, 57, 89, 121)], (23, -23, 2))
    add["Heaven.Crate"] = cont("ToolChest", [(-22, 22, -38, 38, 0, 80, "stopred"), (-22, 22, -38, -35, 80, 95, "stopred"), (-22, 22, 35, 38, 80, 95, "stopred"), (-22, -19, -38, 38, 80, 95, "stopred"),
                                             (19, 22, -38, 38, 80, 95, "stopred"), (-19, 19, -35, 35, 79, 81, "dark")] + [(22, 23, -34, 34, z, z + 2, "dark") for z in (15, 35, 55, 75)],
                               [(0, 44, -38, 38, 0, 6, "stopred"), (18, 26, -15, 15, 6, 9, "steel")], (-22, 0, 95))
    add["Heaven.Crate2"] = cont("Bin", [(-30, 30, -28, -25, 10, 105, "dumpster"), (-30, 30, 25, 28, 10, 105, "dumpster"), (-30, -27, -28, 28, 10, 105, "dumpster"), (27, 30, -28, 28, 10, 105, "dumpster"),
                                        (-30, 30, -28, 28, 10, 13, "dumpster"), (-34, -24, -30, -20, 0, 10, "tyre"), (-34, -24, 20, 30, 0, 10, "tyre")],
                               [(0, 62, -30, 30, 0, 4, "dumpster")], (-30, 0, 105))
    add["Heaven.Chest"] = cont("Safe", shell(-30, 30, -30, 30, 0, 70, 6, "plate") + [(-24, 24, -24, 24, 35, 36, "steel")],
                               [(0, 8, 0, 60, 0, 64, "plate"), (8, 11, 38, 46, 36, 44, "steel"), (8, 11, 44, 48, 20, 30, "steel")], (30, -30, 3))
    add["Heaven.Wardrobe"] = cont("Locker", shell(-30, 30, -60, 60, 0, 196, 3, "steel") + [(-27, 27, -1, 1, 3, 193, "steel"), (-27, 27, -57, 57, 160, 161.5, "steel")],
                                  [(0, 3, 0, 59, 0, 186, "steel")] + [(3, 4, 15, 45, z, z + 2, "dark") for z in (160, 165, 170)], (30, -60, 4),
                                  [(0, 3, -59, 0, 0, 186, "steel")] + [(3, 4, -45, -15, z, z + 2, "dark") for z in (160, 165, 170)], (30, 60, 4))
    add["Heaven.Dumpster21"] = cont("Dumpster", [(-90, 90, -55, -52, 15, 125, "dumpster"), (-90, 90, 52, 55, 15, 125, "dumpster"), (-90, -87, -55, 55, 15, 125, "dumpster"), (87, 90, -55, 55, 15, 125, "dumpster"),
                                                 (-90, 90, -55, 55, 15, 18, "dumpster"), (-80, -65, -45, -30, 0, 15, "tyre"), (65, 80, -45, -30, 0, 15, "tyre"), (-80, -65, 30, 45, 0, 15, "tyre"), (65, 80, 30, 45, 0, 15, "tyre")],
                                    [(0, 182, -57, 57, 0, 5, "dark")], (-90, 0, 125))
    set_pieces(g, add)
    words = g.get_editor_property("container_words21")
    for k, w in {"Heaven.Barrel": "fridge", "Heaven.Barrel2": "filing cabinet", "Heaven.Crate": "tool chest", "Heaven.Crate2": "bin", "Heaven.Chest": "safe",
                 "Heaven.Wardrobe": "locker", "Heaven.Dumpster21": "dumpster"}.items():
        words[unreal.Name(k)] = w
    g.set_editor_property("container_words21", words)
    REPORT.append(f"shops: {len(add)} pieces ({', '.join(sorted(add))}); the containers' words")


# ================================================================================================ phase 22: the goods (every map of the game)
MAPS22 = "/Game/RandomDungeon/Maps/"


def goods_maps():
    return json.load(open(os.path.join(SA, "caves", "treasure16.json"), encoding="utf-8"))["maps"]


def goods(g):
    """the everyday items' modern twins (SourceArt/heaven/goods22.json) on every map of the game: each copied from its like (kind,
    numbers, tiers, buff), with its own name, picture and words and no weight in any draw; the map's HeavenGoods22 (like -> twin); their
    pictures (SourceArt/heaven/art22/icons/icon_<icon>.png) in the UI art. Idempotent: its twins taken out first, by name. Run after the
    item stages (910, 905, 911, 918, 925, 928, 929, 937, 938, 943, 945 items), which write the items anew"""
    G = json.load(open(os.path.join(SA, "heaven", "goods22.json"), encoding="utf-8"))
    src = os.path.join(SA, "heaven", "art22", "icons")
    icons = sorted({x["icon"] for x in G["goods"]})
    lost = [n for n in icons if not os.path.exists(os.path.join(src, f"icon_{n}.png"))]
    assert not lost, f"946 goods: no picture for {lost} (rdm4_ui_cut.py --export SourceArt/heaven/art22/icons first)"
    tex = {n: ui_tex.ui_texture(os.path.join(src, f"icon_{n}.png"), "/Game/RandomDungeon/UI/Heaven22", f"T_HV22_{n}") for n in icons}
    mine = {x["name"] for x in G["goods"]} | set(G.get("retired", []))
    out = []
    for m in goods_maps():
        if not EAL.does_asset_exist(MAPS22 + m): out.append(f"goods: no map {m}"); continue
        les.load_level(MAPS22 + m); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        gg = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
        its = [i for i in gg.get_editor_property("items") if str(i.name) not in mine]
        tw = {}; missing = []
        for x in G["goods"]:
            like = next((i for i in its if str(i.name) == x["like"]), None)
            if not like: missing.append(x["like"]); continue
            it = unreal.RDItemDef(); it.import_text(like.export_text())
            it.set_editor_property("name", x["name"]); it.set_editor_property("icon", unreal.Name(x["icon"]))
            it.set_editor_property("looks", x["looks"]); it.set_editor_property("weight", 0.0)
            its.append(it); tw[unreal.Name(x["like"])] = unreal.Name(x["name"])
        gg.set_editor_property("items", its)
        gg.set_editor_property("heaven_goods22", tw)
        # (a recipe that asks for a like takes its twin as well (PR #129's review: Heaven sells no Jerky, and its Beef Jerky Pack did not
        # count for the recipes that ask for Jerky); the twins taken out of every part first, so a rerun adds them once)
        twin_of = {str(k): str(v) for k, v in tw.items()}
        recs = []; joined = 0
        for r in gg.get_editor_property("recipes"):
            ps = []
            for p_ in r.parts:
                q = unreal.RDRecipePart(); q.label = p_.label; q.count = p_.count
                keep = [a_ for a_ in p_.any_of if str(a_) not in mine]
                add = [twin_of[str(a_)] for a_ in keep if str(a_) in twin_of and twin_of[str(a_)] not in [str(b_) for b_ in keep]]
                q.any_of = keep + [unreal.Name(n_) for n_ in add]; joined += len(add); ps.append(q)
            r.parts = ps; recs.append(r)
        gg.set_editor_property("recipes", recs)
        ua = gg.get_editor_property("ui_art")
        for n, t in tex.items():
            art = unreal.RDUIArt(); art.set_editor_property("texture", t)
            art.set_editor_property("border", unreal.Vector4(0, 0, 0, 0)); art.set_editor_property("inner", unreal.Vector4(0, 0, 1, 1))
            ua[unreal.Name(n)] = art
        gg.set_editor_property("ui_art", ua)
        gg.modify(); les.save_current_level()
        out.append(f"goods {m}: {len(tw)} twins, {len(tex)} pictures, {joined} recipe parts take a twin" + (f"; no like for {missing}" if missing else ""))
        gg = None; import gc as _gc; _gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    REPORT.extend(out)


# ================================================================================================ phase 22: Heaven's life (brokenspire)
def life(g):
    """the neon tube (Heaven.Neon22: a 100 cm bar along X in the lens material, its colour and light per instance), the billboard's frame
    (Heaven.Billboard22) and its faces (Heaven.BillboardFace22_<i>: SourceArt/heaven/art22/billboards/bb_*.png in the sign faces'
    emissive material, a Glow the game sets by the hour), the tables' modern food (Heaven.Town.Food*), the city's sounds
    (SourceArt/heaven/city22.json, converted first by `rdc_sound_prep.py SourceArt/heaven/city22.json SourceArt/heaven/audio_city`)"""
    mats = hk.materials()
    B = lambda n, parts: hk.boxes(n, parts, mats)
    add = {}
    tube = raw(B("SM_HV_Neon22", [(-50, 50, -2, 2, -2, 2, "steel")])); tube.material = lens_material()
    add["Heaven.Neon22"] = tube
    # (the billboard in its own frame: its face +X, three legs on the roof at y -280, 0, 280, a catwalk before the face, the panel's back
    # 6.6 by 3.3 m from 2.6 m up)
    add["Heaven.Billboard22"] = raw(B("SM_HV_Billboard22", [(-14, -6, y - 6, y + 6, 0, 262, "steel") for y in (-280, 0, 280)]
                                      + [(-12, -2, -335, 335, 258, 592, "dark"), (-14, 4, -338, 338, 590, 596, "steel"), (-14, 4, -338, 338, 254, 260, "steel"),
                                         (-14, 4, -338, -332, 254, 596, "steel"), (-14, 4, 332, 338, 254, 596, "steel"), (0, 60, -330, 330, 236, 240, "plate")]), collision=True)
    bsrc = os.path.join(SA, "heaven", "art22", "billboards")
    files = sorted(f for f in os.listdir(bsrc) if f.startswith("bb_") and f.endswith(".png")) if os.path.isdir(bsrc) else []
    assert files, "946 life: no billboard pictures in SourceArt/heaven/art22/billboards"
    base = face_material(); plane = unreal.load_asset("/Engine/BasicShapes/Plane")
    # (the face: the plane's +Z to the frame's +X, its X along -Y (the picture's left to right seen from the street), 6.4 x 3.2 m on the
    # panel at 4.25 m (the sign faces' frame turned a quarter)
    rot = unreal.MathLibrary.make_rot_from_zx(V(1, 0, 0), V(0, -1, 0))
    for i, f in enumerate(files):
        key = f[3:-4]
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", os.path.join(bsrc, f)); t.set_editor_property("destination_path", HV16)
        t.set_editor_property("destination_name", "T_HV_Board22_" + key); t.set_editor_property("replace_existing", True)
        t.set_editor_property("automated", True); t.set_editor_property("save", True)
        AT.import_asset_tasks([t])
        tex = unreal.load_asset(f"{HV16}/T_HV_Board22_{key}"); assert tex, f"946 life: {f} was not imported"
        mp = f"{HV16}/MI_HV_Board22_{key}"
        mi = unreal.load_asset(mp) if EAL.does_asset_exist(mp) else AT.create_asset(f"MI_HV_Board22_{key}", HV16, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, base)
        MEL.set_material_instance_texture_parameter_value(mi, "Face", tex)
        MEL.set_material_instance_scalar_parameter_value(mi, "Glow", 0.9)
        MEL.update_material_instance(mi); EAL.save_loaded_asset(mi, False)
        p = unreal.RDPiece(); p.mesh = plane; p.collision = False; p.material = mi
        p.adjust = unreal.Transform(V(2, 0, 425), rot, V(6.4, 3.2, 1.0)); p.size = V(2, 640, 320)
        add[f"Heaven.BillboardFace22_{i}"] = p
    g.set_editor_property("billboard_faces22", len(files))
    # (the tables' modern food: a sandwich in its wedge pack, a takeaway box, a packet of crackers, a fruit cup; on the table's top at z 0)
    add["Heaven.Town.FoodBread"] = raw(B("SM_HV_FoodSandwich22", [(-9, 9, -6, 6, 0, 6, "prod_brown"), (-9.5, 9.5, -6.5, 6.5, 0, 7, "glass"), (-3, 3, -6.7, -6.5, 2, 5, "white")]))
    add["Heaven.Town.FoodBreadRound"] = raw(B("SM_HV_FoodBox22", [(-8, 8, -8, 8, 0, 7, "white"), (-8.2, 8.2, -2, 2, 0, 7.2, "prod_green")]))
    add["Heaven.Town.FoodCheese"] = raw(B("SM_HV_FoodCrackers22", [(-7, 7, -4, 4, 0, 2.5, "prod_orange"), (-7.5, -7, -4, 4, 0, 2.5, "steel"), (7, 7.5, -4, 4, 0, 2.5, "steel")]))
    # (the tavern's still outside the hotel: an air conditioner's condenser for the still's pot, recycling bins for its kegs)
    add["Heaven.Town.StillPot"] = raw(B("SM_HV_Condenser22", [(-45, 45, -35, 35, 0, 85, "white"), (45, 46, -28, 28, 12, 76, "dark"), (-45, 45, -35, 35, 85, 88, "steel"),
                                                                   (-40, -30, -30, -20, -6, 0, "dark"), (30, 40, 20, 30, -6, 0, "dark")]), collision=True)
    add["Heaven.Town.Keg"] = raw(B("SM_HV_Recycle22", [(-30, 30, -30, 30, 0, 100, "prod_blue"), (-32, 32, -33, 32, 100, 105, "dark"), (-33, -29, -25, 25, 85, 90, "dark")]), collision=True)
    add["Heaven.Town.FoodApples"] = raw(B("SM_HV_FoodCup22", [(-3.5, 3.5, -3.5, 3.5, 0.3, 6.5, "prod_red"), (-4, 4, -4, 4, 0, 9, "glass"), (-4.5, 4.5, -4.5, 4.5, 9, 10, "white")]))
    set_pieces(g, add)
    # ---- the city's sounds (as 921 imports the water's: every field of the set; the loops kept looping)
    aud = os.path.join(SA, "heaven", "audio_city"); idx = os.path.join(aud, "index.json")
    assert os.path.exists(idx), "946 life: run rdc_sound_prep.py SourceArt/heaven/city22.json SourceArt/heaven/audio_city first"
    I = json.load(open(idx, encoding="utf-8")); J = json.load(open(os.path.join(SA, "heaven", "city22.json"), encoding="utf-8"))
    dest = "/Game/RandomDungeon/Audio/Heaven22"
    if not EAL.does_directory_exist(dest): EAL.make_directory(dest)
    snd = g.get_editor_property("sounds"); n = 0
    for key, spec in J["sets"].items():
        waves = []
        for f in I.get(key, {}).get("files", []):
            t = unreal.AssetImportTask(); t.set_editor_property("filename", os.path.join(aud, f)); t.set_editor_property("destination_path", dest)
            t.set_editor_property("destination_name", "SW_" + f[:-4]); t.set_editor_property("replace_existing", True); t.set_editor_property("automated", True)
            AT.import_asset_tasks([t])
            w = unreal.load_asset(f"{dest}/SW_{f[:-4]}")
            if w: w.set_editor_property("looping", bool(spec.get("loop", False))); EAL.save_loaded_asset(w, False); waves.append(w)
        assert waves, f"946 life: no files for {key}"
        s = unreal.RDSoundSet(); s.set_editor_property("sounds", waves)
        s.set_editor_property("volume", float(spec.get("volume", 1.0))); s.set_editor_property("pitch", float(spec.get("pitch", 1.0)))
        s.set_editor_property("pitch_variation", float(spec.get("pitch_var", 0.05))); s.set_editor_property("inner_radius", float(spec.get("inner", 200.0)))
        s.set_editor_property("falloff_distance", float(spec.get("falloff", 2500.0))); s.set_editor_property("b2d", bool(spec.get("loop", False)))
        snd[unreal.Name(key)] = s; n += len(waves)
    g.set_editor_property("sounds", snd)
    REPORT.append(f"life: {len(add)} pieces ({len(files)} billboard faces: {', '.join(f[3:-4] for f in files)}); {len(J['sets'])} sound sets, {n} files")


PARTS = {"lamps": lamps, "signs": signs, "symbols": symbols, "streets": streets, "storeys": storeys, "shops": shops, "life": life}
args = sys.argv[1:] or ["all"]
todo = list(PARTS) if args[0] == "all" else args[0].split(",")
if "goods" in todo:
    todo.remove("goods")
    goods(None)          # (every map; it ends with the last one open)
g = gen()
for t in todo: PARTS[t](g)
g.modify(); les.save_current_level()
for l in REPORT: print("946", l)
del g
import gc; gc.collect()
