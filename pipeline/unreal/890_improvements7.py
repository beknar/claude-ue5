"""The user's list of 2026-11-04 (docs/improvements7.txt) on brokenspire (the town and the wilderness; C++ RD/RDTown7.cpp,
RDSky.cpp, RDWildLife.cpp and the rest named there). Run on the open brokenspire level, play stopped. Parts (argv[1], default
all but icons, in this order):
  signs   the trades' signs' words (blender_numpy/bs_signs.py's pictures, Almendra): T_BS_Sign_<WORDS>, a masked gold-leaf
          material each, pieces Town.SignFace_<WORDS> (a plane standing facing +Y, 58 x 42 cm)
  town    the mill's house (Old Windmill's packed level actor; its sails are Town.Mill, put on it by RDTownPlan.cpp), the gate's
          levers (a post and an arm), the food set out on tables (the kit's bread, cheese, apples), the prep table without
          its food (a copy with the triangles over its top taken out: the town sets its food as things to take), what each
          garden crop gives
  sky     the clouds (an instance of the engine's simple volumetric cloud material), the stars' dome, the moon's disc
          (blender_numpy/wild_sky.py's moon), the moonlight and the night's sky light, the rain, snow and wind effects
  wind    a parameter collection (Strength, which the weather sets) and swaying copies of Hive Sherwood's grass materials
          (M_Clasters, M_Foliage_01: SimpleGrassWind by the height in the mesh), given to the wilderness's grass and the town's
  items   the gardens' ingredients (Wheat, Wild Carrot, Pumpkin, Sunflower Seeds, Herbs) and Cheese, on brokenspire and
          mistward_castle (what she carries goes between them); the oven's recipes (Station Oven) on brokenspire
  icons   <dir>: the ingredients' and the cheese's pictures (rdm4_ui_cut.py --export) into both levels' UIArt
  fauna   the wild animals (Wildlands' deer, wolf, squirrel; the farm's rabbit as a hare) and the swarms and birds
  music   SourceArt/brokenspire/audio7 (rdc_sound_prep.py of music7.json): Music.Town, Music.TownNight, Music.Wild,
          Music.WildNight, Weather.Rain, Weather.Wind on brokenspire
  level   the generator's switches, the town built again (build_start_section) and the level saved
Args: [parts] [icons dir]   e.g.  ue_exec.py 890_improvements7.py signs,town,sky,wind,items,fauna,music,level"""
import unreal, os, sys, json, gc

PARTS = (sys.argv[1] if len(sys.argv) > 1 else "signs,town,sky,wind,items,fauna,music,level").split(",")
ICONS = sys.argv[2] if len(sys.argv) > 2 else None
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SA = os.path.join(REPO, "claude_ue5", "SourceArt")
MAP = "/Game/RandomDungeon/Maps/brokenspire"; CASTLE = "/Game/RandomDungeon/Maps/mistward_castle"
MEL = unreal.MaterialEditingLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V = unreal.Vector
REPORT = []
D7 = "/Game/RandomDungeon/Town7"; SKY = "/Game/RandomDungeon/Sky"; WILD = "/Game/RandomDungeon/Wild"


def open_map(m):
    if not ues.get_editor_world().get_path_name().startswith(m + "."): les.load_level(m)
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def folder(p):
    if not eal.does_directory_exist(p): eal.make_directory(p)


def import_tex(path, dest, name, ui=False, alpha=True):
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", path); t.set_editor_property("destination_path", dest)
    t.set_editor_property("destination_name", name); t.set_editor_property("replace_existing", True)
    t.set_editor_property("automated", True); t.set_editor_property("save", False)
    at.import_asset_tasks([t])
    a = unreal.load_asset(f"{dest}/{name}")
    if not a: raise RuntimeError(f"890: {name} was not imported")
    a.set_editor_property("srgb", True)
    if ui:
        a.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        a.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
        a.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS); a.set_editor_property("never_stream", True)
        a.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP); a.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    else:
        a.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP); a.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    eal.save_loaded_asset(a, False)
    return a


class MB:
    """a material built node by node, cleared and built again in place when it exists"""
    def __init__(self, path):
        d, n = path.rsplit("/", 1); folder(d)
        if eal.does_asset_exist(path): self.m = unreal.load_asset(path); MEL.delete_all_material_expressions(self.m)
        else: self.m = at.create_asset(n, d, unreal.Material, unreal.MaterialFactoryNew())
        self.y = 0
    def n(self, cls, x=-600, **props):
        self.y += 110
        e = MEL.create_material_expression(self.m, cls, x, self.y)
        for k, v in props.items(): e.set_editor_property(k, v)
        return e
    def c(self, a, ap, b, bp): MEL.connect_material_expressions(a, ap, b, bp)
    def out(self, e, pin, prop): MEL.connect_material_property(e, pin, prop)
    def mul(self, a, b, ap="", bp=""):
        e = self.n(unreal.MaterialExpressionMultiply, -300); self.c(a, ap, e, "A"); self.c(b, bp, e, "B"); return e
    def finish(self):
        print("890 MATERIAL-FINAL", self.m.get_name())
        MEL.recompile_material(self.m); eal.save_loaded_asset(self.m)
        REPORT.append(f"{self.m.get_name()}: {MEL.get_statistics(self.m).num_pixel_shader_instructions} instructions")
        return self.m


def mi(path, parent, scalars=None, textures=None):
    d, n = path.rsplit("/", 1); folder(d)
    if not eal.does_asset_exist(path): at.create_asset(n, d, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    m = unreal.load_asset(path); MEL.set_material_instance_parent(m, parent)
    for k, v in (scalars or {}).items(): MEL.set_material_instance_scalar_parameter_value(m, k, v)
    for k, v in (textures or {}).items(): MEL.set_material_instance_texture_parameter_value(m, k, v)
    eal.save_loaded_asset(m, only_if_is_dirty=False)
    return m


def piece(mesh_or_actor, front="+x", mode="center", scale=(1, 1, 1), collision=True, size=None, material=None, rot=None):
    """a generator piece in the dungeon frame (882's rules): the mesh's front to +X; center (footprint centred, bottom z 0) or raw"""
    YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
    p = unreal.RDPiece()
    if isinstance(mesh_or_actor, unreal.StaticMesh):
        m = mesh_or_actor; p.mesh = m
        r = rot or unreal.Rotator(roll=0.0, pitch=0.0, yaw=YAW[front]); t0 = unreal.Transform(V(0, 0, 0), r, V(*scale))
        b = m.get_bounding_box(); cs = [V(x, y, z) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]
        pts = [unreal.MathLibrary.transform_location(t0, c) for c in cs]
        mn = V(min(q.x for q in pts), min(q.y for q in pts), min(q.z for q in pts)); mx = V(max(q.x for q in pts), max(q.y for q in pts), max(q.z for q in pts))
        tx, ty, tz = (-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z) if mode == "center" else (0.0, 0.0, 0.0)
        p.adjust = unreal.Transform(V(tx, ty, tz), r, V(*scale)); p.size = V(*size) if size else V(mx.x - mn.x, mx.y - mn.y, mx.z - mn.z)
    else:
        p.actor_class = mesh_or_actor; p.adjust = unreal.Transform(V(0, 0, 0), unreal.Rotator(0, 0, 0), V(*scale)); p.size = V(*(size or (100, 100, 100)))
    p.collision = collision
    if material is not None: p.material = material
    return p


def set_pieces(g, add):
    P = g.get_editor_property("pieces")
    for k, v in add.items(): P[unreal.Name(k)] = v
    g.set_editor_property("pieces", P)


# ================================================================================================ the signs
def signs():
    g = open_map(MAP)
    src = os.path.join(SA, "brokenspire", "signs")
    files = sorted(f for f in os.listdir(src) if f.startswith("sign_") and f.endswith(".png")) if os.path.isdir(src) else []
    if not files: REPORT.append("signs: no pictures (run blender_numpy/bs_signs.py SourceArt/brokenspire/signs first)"); return
    b = MB(f"{D7}/M_BS_SignFace")
    tx = b.n(unreal.MaterialExpressionTextureSampleParameter2D, -700, parameter_name="Tex")
    b.out(tx, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    b.out(tx, "A", unreal.MaterialProperty.MP_OPACITY_MASK)
    b.out(b.n(unreal.MaterialExpressionConstant, -400, r=0.42), "", unreal.MaterialProperty.MP_ROUGHNESS)
    # (gold leaf a little metallic where the letters are; the dark edge not)
    lum = b.n(unreal.MaterialExpressionComponentMask, -500, r=True); b.c(tx, "RGB", lum, "")
    b.out(b.mul(lum, b.n(unreal.MaterialExpressionConstant, -500, r=0.7)), "", unreal.MaterialProperty.MP_METALLIC)
    b.m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    b.m.set_editor_property("opacity_mask_clip_value", 0.35)
    b.m.set_editor_property("used_with_instanced_static_meshes", True)
    base = b.finish()
    plane = unreal.load_asset("/Engine/BasicShapes/Plane")
    add = {}
    for f in files:
        key = f[5:-4]
        t = import_tex(os.path.join(src, f), D7, "T_BS_Sign_" + key)
        m = mi(f"{D7}/MI_BS_Sign_{key}", base, textures={"Tex": t})
        p = unreal.RDPiece(); p.mesh = plane; p.collision = False; p.material = m
        # (the plane's +Z turned to +Y, its X along the board (her right as she faces it), its height down -Z: 0.58 x 0.42 m)
        r = unreal.MathLibrary.make_rot_from_zx(V(0, 1, 0), V(1, 0, 0))
        p.adjust = unreal.Transform(V(0, 0, 0), r, V(0.58, 0.42, 1.0)); p.size = V(58, 2, 42)
        add[f"Town.SignFace_{key}"] = p
    set_pieces(g, add)
    REPORT.append(f"signs: {len(add)} sign faces")


# ================================================================================================ the town's pieces
def bare_prep_table():
    """the kit's prep table with what lies on it taken off (the triangles over its top at 80 cm)"""
    dst = f"{D7}/SM_Kit_PrepTableBare"
    if eal.does_asset_exist(dst):
        if unreal.load_asset(dst).get_bounding_box().max.z < 81.0: return unreal.load_asset(dst)
        eal.delete_asset(dst)
    src = unreal.load_asset("/Game/Castle/Furniture/Kit/SM_Kit_PrepTable")
    dm = unreal.DynamicMesh()
    o = unreal.GeometryScriptCopyMeshFromAssetOptions(); lod = unreal.GeometryScriptMeshReadLOD()
    dm, oc = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(src, dm, o, lod)
    box = unreal.Box(V(-500, -500, 80.3), V(500, 500, 500))
    sel = unreal.GeometryScript_MeshSelection.select_mesh_elements_in_box(dm, box, unreal.GeometryScriptMeshSelectionType.TRIANGLES, False, 1)
    if isinstance(sel, tuple): dm, sel = sel[0], sel[1]
    r = unreal.GeometryScript_MeshEdits.delete_selected_triangles_from_mesh(dm, sel)
    if isinstance(r, tuple): dm = r[0]
    no = unreal.GeometryScriptCreateNewStaticMeshAssetOptions(); no.set_editor_property("enable_nanite", False); no.set_editor_property("enable_collision", True)
    sm, oc2 = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dm, dst, no)
    for i, s in enumerate(src.static_materials):
        if i < len(sm.static_materials): sm.set_material(i, s.material_interface)
    eal.save_loaded_asset(sm, only_if_is_dirty=False)
    b0, b1 = src.get_bounding_box(), sm.get_bounding_box()
    REPORT.append(f"the bare prep table: {round(b0.max.z)} cm high before, {round(b1.max.z)} after ({oc}, {oc2})")
    return sm


def town():
    g = open_map(MAP)
    folder(D7)
    add = {}
    house = eal.load_blueprint_class("/Game/Old_Windmill/Blueprint/BPP_L_PLA_Mill")
    if house: add["Town.MillHouse"] = piece(house, size=(1400, 1600, 1900))
    else: REPORT.append("MISSING the mill house")
    post = unreal.load_asset("/Game/ModularWoodenBuildings/StaticMeshes/WoodenShacks/Fence/SM_FencePost_01")
    arm = unreal.load_asset("/Game/Medieval_Castle/CastleKit/Wood_Structures/SM_Castle_Wooden_Beam_1m_01a_NN")
    if post: add["Town.LeverPost"] = piece(post, scale=(1.6, 1.6, 0.62))
    if arm: add["Town.LeverArm"] = piece(arm, scale=(0.45, 0.4, 0.95), collision=False)
    K = "/Game/Castle/Furniture/Kit/"
    for n, m in (("FoodBread", "SM_Kit_BreadLoaf"), ("FoodBreadRound", "SM_Kit_BreadRound"), ("FoodCheese", "SM_Kit_Cheese"), ("FoodApples", "SM_Kit_AppleBasket")):
        a = unreal.load_asset(K + m)
        if a: add["Town." + n] = piece(a, collision=False)
        else: REPORT.append("MISSING " + m)
    set_pieces(g, add)
    # (the town's prep table: the bare one; its food is set on it as things to take)
    bare = bare_prep_table()
    P = g.get_editor_property("pieces")
    pk = unreal.Name("PrepTable")
    if pk in P and bare:
        pt = P[pk]; pt.mesh = bare; P[pk] = pt; g.set_editor_property("pieces", P)
    g.set_editor_property("town_crop_items", [unreal.Name(n) for n in ("Wild Carrot", "Wheat", "Pumpkin", "Sunflower Seeds", "Herbs", "Herbs")])
    REPORT.append(f"town: {len(add)} pieces, the prep table bare")


# ================================================================================================ the sky
def sky():
    g = open_map(MAP)
    folder(SKY)
    moon_png = os.path.join(SA, "wilderness", "sky", "moon.png")
    moon = import_tex(moon_png, SKY, "T_RD_Moon") if os.path.exists(moon_png) else None
    stars_t = unreal.load_asset("/Engine/EngineSky/T_Sky_Stars")
    def sky_flags(m, additive):
        m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE if additive else unreal.BlendMode.BLEND_TRANSLUCENT)
        m.set_editor_property("two_sided", True)
        for k, v in (("apply_fogging", False), ("use_translucency_vertex_fog", False), ("disable_depth_test", False)):
            try: m.set_editor_property(k, v)
            except Exception: pass
    # the stars: the engine's star field tiled over the dome, twinkling a little, as bright as "Bright"
    b = MB(f"{SKY}/M_RD_SkyStars")
    # (tiled 18 x 9 and its faint points cut away (a power of 2.5): at 6 x 3 they were big soft flakes, like snow)
    uv = b.n(unreal.MaterialExpressionTextureCoordinate, -1100, u_tiling=18.0, v_tiling=9.0)
    st = b.n(unreal.MaterialExpressionTextureSample, -900, texture=stars_t); b.c(uv, "", st, "UVs")
    pw = b.n(unreal.MaterialExpressionPower, -800, const_exponent=2.5); b.c(st, "RGB", pw, "Base")
    br = b.n(unreal.MaterialExpressionScalarParameter, -900, parameter_name="Bright", default_value=1.0)
    k = b.mul(b.mul(pw, br), b.n(unreal.MaterialExpressionConstant, -700, r=9.0))
    b.out(k, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    sky_flags(b.m, True); stars = b.finish()
    # the moon: its disc's picture, its alpha its edge
    b = MB(f"{SKY}/M_RD_SkyMoon")
    mt = b.n(unreal.MaterialExpressionTextureSample, -900, texture=moon) if moon else b.n(unreal.MaterialExpressionConstant4Vector, -900, constant=unreal.LinearColor(1, 1, 1, 1))
    br = b.n(unreal.MaterialExpressionScalarParameter, -900, parameter_name="Bright", default_value=1.0)
    b.out(b.mul(b.mul(mt, br, ap="RGB"), b.n(unreal.MaterialExpressionConstant, -700, r=3.5)), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    op = b.n(unreal.MaterialExpressionMultiply, -400); b.c(mt, "A", op, "A"); cl = b.n(unreal.MaterialExpressionSaturate, -500)
    b.c(b.mul(br, b.n(unreal.MaterialExpressionConstant, -700, r=3.0)), "", cl, ""); b.c(cl, "", op, "B")
    b.out(op, "", unreal.MaterialProperty.MP_OPACITY)
    sky_flags(b.m, False); moonm = b.finish()
    # high thin clouds (another kind than the volumetric layer's heaps): the engine's cloud texture drifting over the dome
    b = MB(f"{SKY}/M_RD_SkyHigh")
    # (the list of 2026-11-07: "the sky when looking straight up looks like a giant circle"; the sphere's own UVs pinched the
    # cloud texture into rays at the top (888 sky8's pictures). The clouds are laid flat over the sky instead: their place is
    # the way to them over its height (a ceiling's), drifting, thinning out toward the horizon where the ceiling's are
    # stretched)
    # (laid flat from the view's way instead, the engine's cloud picture (not made to tile) showed its seams as straight lines
    # running to the horizon: the sphere's UVs are kept and the high clouds thin out toward the top, where they pinched)
    # (the list of 2026-11-10: "there is still a disc in the sky in the day time": faded out between 0.55 and 0.85 the high
    # clouds left a clear round patch overhead with wisps all round it, a disc against the blue (884 sky10's pictures straight
    # up). They then thinned over most of the sky's height, nothing left only at the top where they pinched)
    # (2026-11-10, the shipping game: "there is still a disc in the sky that rotates faster than the sky closer to the horizon":
    # the dome was turned about the zenith (0.6 degrees a second) and its texture panned along the sphere's U, which is a turn
    # about the zenith too, while the volumetric clouds below drift in a straight line: overhead the high clouds spun as a disc.
    # They are a flat layer now (a ceiling SkyHighHeight up, the way to it from the camera), drawn from the material's own
    # gradient noise (tiling: the engine's cloud picture does not tile, and laid flat its seams ran to the horizon, 2026-11-07),
    # stretched along the wind as high clouds are, and moved only by the drift along the wind the game sets (Drift, wrapped at
    # TileCm, where both layers' noise repeats): no turn, no pinch at the top, nothing to fade there)
    def layer(reps, stretch, z):
        cu = b.n(unreal.MaterialExpressionCustom, -1000)
        cu.set_editor_property("code", "float3 d = normalize(P - C);\nfloat t = H / max(d.z, 0.03);\nfloat2 w = C.xy + d.xy * t;\n"
                                       "float2 a = normalize(Wd.xy + float2(1e-5, 0.0));\nfloat u = dot(w, a) - Dr;\nfloat v = dot(w, float2(-a.y, a.x));\n"
                                       f"return float3(u * {reps:.1f} / T, v * {reps * stretch:.1f} / T, {z});")
        cu.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        ins = []
        for nm in ("P", "C", "H", "T", "Dr", "Wd"):
            ci = unreal.CustomInput(); ci.set_editor_property("input_name", nm); ins.append(ci)
        cu.set_editor_property("inputs", ins)
        for pin, src in (("P", wp), ("C", cam), ("H", hp), ("T", tp), ("Dr", dp), ("Wd", wdm)): b.c(src, "", cu, pin)
        return cu
    wp = b.n(unreal.MaterialExpressionWorldPosition, -1300); cam = b.n(unreal.MaterialExpressionCameraPositionWS, -1300)
    hp = b.n(unreal.MaterialExpressionScalarParameter, -1300, parameter_name="Height", default_value=900000.0)
    tp = b.n(unreal.MaterialExpressionScalarParameter, -1300, parameter_name="TileCm", default_value=2.4e7)
    dp = b.n(unreal.MaterialExpressionScalarParameter, -1300, parameter_name="Drift", default_value=0.0)
    wd = b.n(unreal.MaterialExpressionVectorParameter, -1300, parameter_name="WindDir", default_value=unreal.LinearColor(1, 0, 0, 0))
    wdm = b.n(unreal.MaterialExpressionComponentMask, -1200, r=True, g=True, b=True); b.c(wd, "", wdm, "")
    # (the noise repeats every 64 of its cells in each axis (a multiple of 4, as the gradient noise needs; its levels repeat with
    # it): the streaks are 64 cells along the wind in a 240 km tile (3.75 km each) and 2.5 times finer across (repeating every
    # 96 km), the breaks in them 192 along (1.25 km) and 1.6 times finer across (every 50 km): along the wind both repeat at the
    # tile, where the drift wraps)
    def noise(q, levels):
        n = b.n(unreal.MaterialExpressionNoise, -800, noise_function=unreal.NoiseFunction.NOISEFUNCTION_GRADIENT_ALU, scale=1.0, quality=1,
                turbulence=False, levels=levels, level_scale=2.0, output_min=0.0, output_max=1.0, tiling=True, repeat_size=64)
        # (its pin is "World Position": joined as "Position" nothing was joined, silently, and the noise read the world's
        # centimetres, a grain of 1 cm cells over the whole sky (884 skyspin's first pictures))
        assert MEL.connect_material_expressions(q, "", n, "World Position"), "the noise's position pin"
        return n
    n1 = noise(layer(64.0, 2.5, 0.37), 4); n2 = noise(layer(192.0, 1.6, 3.71), 3)
    sh = b.n(unreal.MaterialExpressionCustom, -600)
    # (faded out toward the horizon from 20 degrees up to 3: below it the layer, seen nearly edge on, drew a band of scales)
    sh.set_editor_property("code", "float3 d = normalize(P - C);\nfloat f = smoothstep(0.05, 0.34, d.z);\n"
                                   "return saturate((A * 0.72 + B * 0.28 - Th) * K) * f;")
    sh.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    ins = []
    for nm in ("P", "C", "A", "B", "Th", "K"):
        ci = unreal.CustomInput(); ci.set_editor_property("input_name", nm); ins.append(ci)
    sh.set_editor_property("inputs", ins)
    # (0.52 and 3: soft wisps; at 0.47 and 4 hard grey patches toward the horizon, at 0.56 and 2.2 barely any (884 skyspin's
    # pictures of the three, 2026-11-10))
    th = b.n(unreal.MaterialExpressionScalarParameter, -800, parameter_name="Thresh", default_value=0.52)
    kk = b.n(unreal.MaterialExpressionScalarParameter, -800, parameter_name="Contrast", default_value=3.0)
    for pin, src in (("P", wp), ("C", cam), ("A", n1), ("B", n2), ("Th", th), ("K", kk)): b.c(src, "", sh, pin)
    br = b.n(unreal.MaterialExpressionScalarParameter, -900, parameter_name="Bright", default_value=1.0)
    col = b.n(unreal.MaterialExpressionConstant3Vector, -800, constant=unreal.LinearColor(0.9, 0.92, 0.96, 1))
    b.out(b.mul(b.mul(col, br), sh), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    # (Amount: the game thins the layer as the cloud cover closes (a translucent layer is drawn over the volumetric clouds, which
    # are below it: in cloudy weather its wisps lay on the lower clouds))
    am = b.n(unreal.MaterialExpressionScalarParameter, -800, parameter_name="Amount", default_value=1.0)
    b.out(b.mul(b.mul(sh, b.n(unreal.MaterialExpressionConstant, -700, r=0.45)), am), "", unreal.MaterialProperty.MP_OPACITY)
    sky_flags(b.m, False); high = b.finish()
    # the rain and snow of our own: thin planes round her camera, falling by their world position offset (the packs' rain
    # system did not show round the camera); Amount, Origin (the field's corner), Wind, Bright set in play
    b = MB(f"{SKY}/M_RD_Drops")
    cu = b.n(unreal.MaterialExpressionCustom, -500)
    cu.set_editor_property("code", "float3 rel = P - O;\nfloat lz = rel.z;\nfloat nz = frac((lz - T * S) / H) * H;\nfloat dz = nz - lz;\n"
                                   "float sw = Sw * sin(T * 1.3 + rel.x * 0.013 + rel.y * 0.017);\nreturn float3(-dz * 0.3 * W + sw, sw * 0.7, dz);")
    cu.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    ins = []
    for nm in ("P", "O", "T", "S", "H", "W", "Sw"):
        ci = unreal.CustomInput(); ci.set_editor_property("input_name", nm); ins.append(ci)
    cu.set_editor_property("inputs", ins)
    wp = b.n(unreal.MaterialExpressionWorldPosition, -900)
    org = b.n(unreal.MaterialExpressionVectorParameter, -900, parameter_name="Origin", default_value=unreal.LinearColor(0, 0, 0, 0))
    om = b.n(unreal.MaterialExpressionComponentMask, -750, r=True, g=True, b=True); b.c(org, "", om, "")
    tm = b.n(unreal.MaterialExpressionTime, -900)
    sp = {k: b.n(unreal.MaterialExpressionScalarParameter, -900, parameter_name=k, default_value=v) for k, v in (("Speed", 950.0), ("Height", 1800.0), ("Wind", 0.3), ("Sway", 0.0))}
    for pin, src in (("P", wp), ("O", om), ("T", tm), ("S", sp["Speed"]), ("H", sp["Height"]), ("W", sp["Wind"]), ("Sw", sp["Sway"])): b.c(src, "", cu, pin)
    b.out(cu, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    am = b.n(unreal.MaterialExpressionScalarParameter, -900, parameter_name="Amount", default_value=1.0)
    br = b.n(unreal.MaterialExpressionScalarParameter, -900, parameter_name="Bright", default_value=1.0)
    col = b.n(unreal.MaterialExpressionVectorParameter, -900, parameter_name="Color", default_value=unreal.LinearColor(0.75, 0.8, 0.9, 1))
    opq = b.n(unreal.MaterialExpressionScalarParameter, -900, parameter_name="Opacity", default_value=0.3)
    # (the list of 2026-11-07: "the rain does not look like raindrops, instead they look like white rods": flat, hard-edged and
    # glowing near-white by day. Each drop is now soft: thin toward its ends along its length and across its width (the plane's
    # UVs, either way round), dimmer and bluer, about as see-through as a drop against the sky; the snow's flakes round)
    sh = b.n(unreal.MaterialExpressionCustom, -500)
    sh.set_editor_property("code", "float a = sin(saturate(U.x) * 3.14159265);\nfloat c = sin(saturate(U.y) * 3.14159265);\nreturn pow(a, 1.6) * pow(c, 1.6);")
    sh.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    ci = unreal.CustomInput(); ci.set_editor_property("input_name", "U"); sh.set_editor_property("inputs", [ci])
    b.c(b.n(unreal.MaterialExpressionTextureCoordinate, -900, coordinate_index=0), "", sh, "U")
    b.out(b.mul(col, br), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    b.out(b.mul(b.mul(opq, am), sh), "", unreal.MaterialProperty.MP_OPACITY)
    sky_flags(b.m, False); b.m.set_editor_property("used_with_instanced_static_meshes", True)
    drops = b.finish()
    rain_mi = mi(f"{SKY}/MI_RD_Rain", drops, scalars={"Speed": 950.0, "Height": 1800.0, "Sway": 0.0, "Opacity": 0.42})
    MEL.set_material_instance_vector_parameter_value(rain_mi, "Color", unreal.LinearColor(0.42, 0.47, 0.55, 1)); eal.save_loaded_asset(rain_mi, only_if_is_dirty=False)
    snow_mi = mi(f"{SKY}/MI_RD_Snow", drops, scalars={"Speed": 130.0, "Height": 1800.0, "Sway": 28.0, "Opacity": 1.0})
    MEL.set_material_instance_vector_parameter_value(snow_mi, "Color", unreal.LinearColor(1.3, 1.3, 1.35, 1)); eal.save_loaded_asset(snow_mi, only_if_is_dirty=False)
    cloud_parent = unreal.load_asset("/Engine/EngineSky/VolumetricClouds/m_SimpleVolumetricCloud_Inst")
    clouds = mi(f"{SKY}/MI_RD_Clouds", cloud_parent)
    for prop, val in (("sky7", True), ("sky_cloud_material", clouds), ("sky_stars_material", stars), ("sky_moon_material", moonm), ("sky_high_cloud_material", high),
                      ("sky_dome_mesh", unreal.load_asset("/Engine/EngineSky/SM_SkySphere")), ("sky_quad_mesh", unreal.load_asset("/Engine/BasicShapes/Plane")),
                      # (the packs' rain and snow did not show round her camera, and the blowing leaves drew huge green blobs
                      # (pictures of 2026-11-05): the drops are ours; the wind is the grass's sway and its sound)
                      ("rain_fx", None), ("snow_fx", None), ("wind_fx", None),
                      ("drop_mesh", unreal.load_asset("/Engine/BasicShapes/Plane")), ("rain_drop_material", rain_mi), ("snow_drop_material", snow_mi),
                      ("moon_lux", 2.4), ("night_sky_share", 0.17), ("night_exposure_bias", -0.6)):
        try: g.set_editor_property(prop, val)
        except Exception as e: REPORT.append(f"sky: {prop} not set ({e})")
    REPORT.append("sky: clouds, stars, moon, high clouds, rain / snow / wind effects; moonlight 2.4 lux, the night's sky light 17 %")


# ================================================================================================ the wind
def wind():
    g = open_map(MAP)
    folder(WILD)
    mp = f"{WILD}/MPC_RD_Wind"
    if not eal.does_asset_exist(mp): at.create_asset("MPC_RD_Wind", WILD, unreal.MaterialParameterCollection, unreal.MaterialParameterCollectionFactoryNew())
    mpc = unreal.load_asset(mp)
    sp = unreal.CollectionScalarParameter(); sp.set_editor_property("parameter_name", "Strength"); sp.set_editor_property("default_value", 0.3)
    mpc.set_editor_property("scalar_parameters", [sp]); eal.save_loaded_asset(mpc, only_if_is_dirty=False)
    fn = unreal.load_asset("/Engine/Functions/Engine_MaterialFunctions01/WorldPositionOffset/SimpleGrassWind")
    made = {}
    for src, dst in (("/Game/Hive_Sherwood/Materials/M_Clasters", f"{WILD}/M_RD_Clasters_Wind"), ("/Game/Hive_Sherwood/Materials/M_Foliage_01", f"{WILD}/M_RD_Foliage01_Wind")):
        if eal.does_asset_exist(dst): eal.delete_asset(dst)
        m = eal.duplicate_asset(src, dst)
        if not m: REPORT.append(f"wind: {src} not copied"); continue
        y = 900
        def node(cls, **pr):
            nonlocal y; y += 120
            e = MEL.create_material_expression(m, cls, -1400, y)
            for k, v in pr.items(): e.set_editor_property(k, v)
            return e
        cp = node(unreal.MaterialExpressionCollectionParameter, collection=mpc, parameter_name="Strength")
        k = node(unreal.MaterialExpressionMultiply, const_b=1.6); MEL.connect_material_expressions(cp, "", k, "A")
        lp = node(unreal.MaterialExpressionLocalPosition)
        lz = node(unreal.MaterialExpressionComponentMask, b=True); MEL.connect_material_expressions(lp, "", lz, "")
        wd = node(unreal.MaterialExpressionDivide, const_b=55.0); MEL.connect_material_expressions(lz, "", wd, "A")
        ws = node(unreal.MaterialExpressionSaturate); MEL.connect_material_expressions(wd, "", ws, "")
        f = node(unreal.MaterialExpressionMaterialFunctionCall); f.set_material_function(fn)
        MEL.connect_material_expressions(k, "", f, "WindIntensity"); MEL.connect_material_expressions(ws, "", f, "WindWeight")
        spd = node(unreal.MaterialExpressionConstant, r=1.6); MEL.connect_material_expressions(spd, "", f, "WindSpeed")
        zero = node(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(0, 0, 0, 0)); MEL.connect_material_expressions(zero, "", f, "AdditionalWPO")
        MEL.connect_material_property(f, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
        m.set_editor_property("used_with_instanced_static_meshes", True)
        print("890 MATERIAL-FINAL", m.get_name()); MEL.recompile_material(m); eal.save_loaded_asset(m)
        made[src.rsplit("/", 1)[1]] = m
    # (each grass material instance of those masters, copied onto the swaying one)
    swayed = {}
    def sway_of(mi_):
        if mi_ is None: return None
        if mi_.get_path_name() in swayed: return swayed[mi_.get_path_name()]
        base = mi_.get_base_material() if hasattr(mi_, "get_base_material") else None
        bn = base.get_name() if base else ""
        if bn not in made or not isinstance(mi_, unreal.MaterialInstanceConstant): return None
        dst = f"{WILD}/{mi_.get_name()}_Wind"
        if eal.does_asset_exist(dst): eal.delete_asset(dst)
        c = eal.duplicate_asset(mi_.get_path_name().split(".")[0], dst)
        MEL.set_material_instance_parent(c, made[bn]); eal.save_loaded_asset(c, only_if_is_dirty=False)
        swayed[mi_.get_path_name()] = c
        return c
    bios = g.get_editor_property("wild_biomes"); n = 0
    for B in bios:
        fol = B.get_editor_property("foliage")
        for F in fol:
            if str(F.kind) not in ("grass", "bush", "flower") or not F.mesh: continue
            mats = [sway_of(s.material_interface) for s in F.mesh.static_materials]
            if any(mats): F.set_editor_property("materials", [m_ if m_ else s.material_interface for m_, s in zip(mats, F.mesh.static_materials)]); n += 1
        B.set_editor_property("foliage", fol)
    g.set_editor_property("wild_biomes", bios)
    # (the town's grass and bushes: a piece's material for all its slots)
    P = g.get_editor_property("pieces"); tn = 0
    for k in list(P.keys()):
        ks = str(k)
        if not (ks.startswith("Town.GrassShort") or ks in ("Town.Grass", "Town.Bush")): continue
        p = P[k]
        if not p.mesh: continue
        mats = [sway_of(s.material_interface) for s in p.mesh.static_materials]
        if mats and mats[0]: p.material = mats[0]; P[k] = p; tn += 1
    g.set_editor_property("pieces", P)
    g.set_editor_property("wind_collection", mpc)
    REPORT.append(f"wind: {len(made)} swaying masters, {len(swayed)} instances, {n} wild plants and {tn} town pieces sway")


# ================================================================================================ the items and the oven
INGREDIENTS = [("Wheat", "ripe wheat from a town garden"), ("Wild Carrot", "carrots pulled from a town garden"), ("Pumpkin", "a pumpkin from a town garden"),
               ("Sunflower Seeds", "a sunflower's seeds from a town garden"), ("Herbs", "herbs cut in a town garden")]
OVEN = [("Bread", {"Wheat": 2}), ("Hardtack", {"Wheat": 3}), ("Nuts and Seeds", {"Sunflower Seeds": 3}), ("Sweet Roll", {"Wheat": 2, "Sunflower Seeds": 2}),
        ("Travel Cake", {"Wheat": 2, "Wild Carrot": 1, "Pumpkin": 1}), ("Fruit", {"Pumpkin": 1, "Herbs": 1})]


def items_on(map_path, recipes):
    g = open_map(map_path)
    its = list(g.get_editor_property("items"))
    names = {str(i.name) for i in its}
    bread = next((i for i in its if str(i.name) == "Bread"), None)
    for n, looks in INGREDIENTS:
        if n in names: continue
        it = unreal.RDItemDef(); it.name = n; it.kind = unreal.RDItemKind.COMPONENT; it.weight = 0.0; it.found_max = 1
        it.icon = unreal.Name({"Wheat": "ingredient_wheat", "Wild Carrot": "ingredient_carrot", "Pumpkin": "ingredient_pumpkin", "Sunflower Seeds": "ingredient_sunflower_seeds", "Herbs": "ingredient_herbs"}[n])
        it.looks = looks; its.append(it)
    if "Cheese" not in names and bread is not None:
        c = unreal.RDItemDef(); c.import_text(bread.export_text())
        c.name = "Cheese"; c.icon = unreal.Name("cheese"); c.looks = "a wedge of the town's cheese, set out on a table"; its.append(c)
    g.set_editor_property("items", its)
    if recipes:
        rs = [r for r in g.get_editor_property("recipes") if str(r.station) != "Oven"]
        for item, takes in OVEN:
            r = unreal.RDRecipe(); r.item = item; r.station = "Oven"; parts = []
            for k, v in takes.items():
                p = unreal.RDRecipePart(); p.label = k.lower(); p.any_of = [unreal.Name(k)]; p.count = v; parts.append(p)
            r.parts = parts; rs.append(r)
        g.set_editor_property("recipes", rs)
    g.modify(); les.save_current_level()
    return len(its)


def items():
    n1 = items_on(CASTLE, False)
    n2 = items_on(MAP, True)
    REPORT.append(f"items: the ingredients and cheese on mistward_castle ({n1} items) and brokenspire ({n2}), {len(OVEN)} oven recipes")


def icons():
    if not ICONS or not os.path.isdir(ICONS): REPORT.append("icons: give the folder rdm4_ui_cut.py --export wrote"); return
    want = ("ingredient_", "cheese")
    tex = {}
    for f in sorted(os.listdir(ICONS)):
        if f.endswith(".png") and f.startswith(want): tex[f[:-4]] = import_tex(os.path.join(ICONS, f), "/Game/RandomDungeon/UI", "T_RDM4_" + f[:-4], ui=True)
    for m in (CASTLE, MAP):
        g = open_map(m)
        ua = g.get_editor_property("ui_art")
        for n, a in tex.items():
            art = unreal.RDUIArt(); art.set_editor_property("texture", a)
            art.set_editor_property("border", unreal.Vector4(0, 0, 0, 0)); art.set_editor_property("inner", unreal.Vector4(0, 0, 1, 1))
            ua[unreal.Name(n)] = art
        g.set_editor_property("ui_art", ua); g.modify(); les.save_current_level()
    REPORT.append(f"icons: {len(tex)} pictures on both levels")


# ================================================================================================ the animals, insects and birds
def clip_speed(clip):
    try:
        n = unreal.AnimationLibrary.get_num_frames(clip)
        for bone in ("root", "Root", "pelvis", "Hips"):
            a = unreal.AnimationLibrary.get_bone_pose_for_frame(clip, bone, 0, False).translation
            b = unreal.AnimationLibrary.get_bone_pose_for_frame(clip, bone, n - 1, False).translation
            d = (b - a).length()
            if d > 30: return d / clip.get_play_length()
    except Exception: pass
    return 0.0


def fauna():
    g = open_map(MAP)
    WL = "/Game/Wildlands/Creatures/"
    TEMPERATE = ["grasslands", "meadows", "hills", "plains", "temperate autumn forests", "temperate aspen", "pine forests", "boreal pine forest", "taigas", "highland moorland", "coastal regions", "wetlands", "farms"]
    COLD = ["tundras", "taigas", "boreal pine forest", "cold steppes", "arctic regions", "mountains", "mountains and peaks", "glacial", "hills", "volcanic tundra"]
    FOREST = ["temperate autumn forests", "temperate aspen", "pine forests", "boreal pine forest", "taigas", "meadows"]
    OPEN = ["grasslands", "meadows", "farms", "plains", "savannahs", "cold steppes", "tundras", "highland moorland", "coastal regions", "mesas"]
    out = []
    def kind(name, mesh, idle, eat, walk, run, biomes, per_km2, walk_v, run_v, flee=(100.0, 300.0), half=60.0, scale=1.0):
        m = unreal.load_asset(mesh)
        if not m: REPORT.append("fauna: MISSING " + mesh); return
        F = unreal.RDWildFauna(); F.name = name; F.mesh = m
        for k, p in (("idle", idle), ("eat", eat), ("walk", walk), ("run", run)):
            if p: F.set_editor_property(k, unreal.load_asset(p))
        b = m.get_bounds(); ext = b.box_extent
        # (a pack's creatures face +Y or +X: the longer way of its box is its length)
        F.mesh_yaw = -90.0 if ext.y > ext.x * 1.15 else 0.0
        F.scale = scale
        wc = clip_speed(F.walk) if F.walk else 0.0; rc = clip_speed(F.run) if F.run else 0.0
        F.walk_speed = walk_v; F.run_speed = run_v
        F.walk_clip_speed = wc if wc > 10 else walk_v; F.run_clip_speed = rc if rc > 10 else run_v
        F.flee_min, F.flee_max = flee; F.biomes = biomes; F.per_km2 = per_km2; F.half_length = half
        out.append(F)
        REPORT.append(f"fauna {name}: clips' ground speed walk {wc:.0f} run {rc:.0f} cm/s (none: the speeds given), yaw {F.mesh_yaw}")
    A = WL + "Animations/"
    kind("Deer", WL + "Meshes/SKM_Deer", A + "Deer_Idle", A + "Deer_Eating", A + "Deer_Walk", A + "Deer_Run", TEMPERATE, 30, 130, 850, half=90)
    kind("Wolf", WL + "Meshes/SKM_Wolf", A + "Wolf_Idle", A + "Wolf_Eating", A + "Wolf_Walk", A + "Wolf_Run", COLD, 8, 140, 900, half=70)
    kind("Squirrel", WL + "Meshes/SKM_Squirell", A + "Squirrel_Idle", None, A + "Squirrel_Walk", A + "Squirrel_Run", FOREST, 40, 60, 380, flee=(100.0, 200.0), half=20)
    hare = next((t for t in g.get_editor_property("town_animals") if str(t.name).lower().startswith("rabbit")), None)
    if hare:
        F = unreal.RDWildFauna(); F.name = "Hare"; F.mesh = hare.mesh; F.idle = hare.idle; F.eat = hare.graze; F.walk = hare.walk; F.run = hare.walk
        F.scale = hare.scale * 1.15; F.mesh_yaw = hare.mesh_yaw; F.walk_speed = max(hare.walk_speed, 30.0); F.walk_clip_speed = max(hare.walk_speed, 30.0) / max(hare.scale, 0.1)
        F.run_speed = 420.0; F.run_clip_speed = 140.0 / max(hare.scale, 0.1); F.flee_min, F.flee_max = 100.0, 300.0; F.biomes = OPEN; F.per_km2 = 45; F.half_length = 25
        out.append(F)
    g.set_editor_property("wild_fauna", out)
    # the insects and the birds
    sw = []
    def swarm(name, path, biomes, day, night, layer, height, scale, count, coast=2):
        s = unreal.load_asset(path)
        if not s: REPORT.append("swarms: MISSING " + path); return
        S = unreal.RDWildSwarm(); S.name = name; S.system = s; S.biomes = biomes; S.day = day; S.night = night
        S.layer = layer; S.height = height; S.scale = scale; S.count = count; S.coast = coast; sw.append(S)
    FLOWERS = ["meadows", "grasslands", "farms", "plains", "temperate aspen", "temperate autumn forests", "coastal regions", "highland moorland", "town"]
    swarm("Butterflies", "/Game/Wildlands/VFX/FX/NS_Butterfly_01", FLOWERS, True, False, 0, 0.8, 1.0, 3)
    swarm("Fireflies", "/Game/Wildlands/VFX/FX/NS_Fireflies", ["meadows", "wetlands", "marshes", "temperate autumn forests", "temperate aspen", "pine forests", "grasslands", "town"], False, True, 0, 1.0, 1.0, 3)
    swarm("Flies", "/Game/Volstok_District/VFX/NS_Flies_01a", ["marshes", "wetlands", "savannahs", "farms", "town"], True, True, 0, 0.6, 1.0, 2)
    swarm("Bird flock", "/Game/Medieval_Lake_Village/VFX/NS_BirdFlock", ["*"], True, False, 1, 45.0, 1.0, 2)
    swarm("Crows", "/Game/Volstok_District/VFX/NS_Flying_Birds_01a", ["farms", "grasslands", "plains", "hills", "town", "temperate autumn forests", "tundras", "moor", "highland moorland"], True, False, 1, 30.0, 1.0, 1)
    swarm("Gulls", "/Game/Wildlands/VFX/FX/NS_SeagullFlock", ["*"], True, False, 1, 25.0, 1.0, 2, coast=1)
    g.set_editor_property("wild_swarms", sw)
    REPORT.append(f"fauna: {len(out)} animals, {len(sw)} swarms and flocks")


# ================================================================================================ the music and the weather's sounds
def music():
    g = open_map(MAP)
    aud = os.path.join(SA, "brokenspire", "audio7")
    idx = os.path.join(aud, "index.json")
    if not os.path.exists(idx): REPORT.append("music: run rdc_sound_prep.py SourceArt/brokenspire/music7.json SourceArt/brokenspire/audio7 first"); return
    I = json.load(open(idx, encoding="utf-8"))
    J = json.load(open(os.path.join(SA, "brokenspire", "music7.json"), encoding="utf-8"))
    dest = "/Game/RandomDungeon/Audio/Music7"; folder(dest)
    snd = g.get_editor_property("sounds")
    for key, spec in J["sets"].items():
        files = [f for f in sorted(os.listdir(aud)) if f.startswith(key.replace(".", "_") + "_") and f.endswith(".wav")]
        waves = []
        for f in files:
            t = unreal.AssetImportTask(); t.set_editor_property("filename", os.path.join(aud, f)); t.set_editor_property("destination_path", dest)
            t.set_editor_property("destination_name", "SW_" + f[:-4]); t.set_editor_property("replace_existing", True); t.set_editor_property("automated", True)
            at.import_asset_tasks([t])
            w = unreal.load_asset(f"{dest}/SW_{f[:-4]}")
            if w:
                w.set_editor_property("looping", bool(spec.get("loop"))); eal.save_loaded_asset(w, False); waves.append(w)
        if not waves: REPORT.append(f"music: no files for {key}"); continue
        s = unreal.RDSoundSet(); s.set_editor_property("sounds", waves); s.set_editor_property("volume", float(spec.get("volume", 1.0)))
        snd[unreal.Name(key)] = s
    g.set_editor_property("sounds", snd)
    REPORT.append("music: " + ", ".join(f"{k} {len(snd[unreal.Name(k)].sounds)}" for k in J["sets"] if unreal.Name(k) in snd))


# ================================================================================================ the level
def level():
    g = open_map(MAP)
    g.build_start_section()
    REPORT.append("Brokenspire built again")
    les.save_current_level()
    REPORT.append("level saved")


for part in PARTS:
    part = part.strip()
    if not part: continue
    try:
        {"signs": signs, "town": town, "sky": sky, "wind": wind, "items": items, "icons": icons, "fauna": fauna, "music": music, "level": level}[part]()
        if part not in ("items", "icons", "level"):
            les.save_current_level()
    except Exception as e:
        import traceback
        REPORT.append(f"{part}: FAILED {e!r}"); traceback.print_exc()
print("890 " + " | ".join(REPORT))
gc.collect()
