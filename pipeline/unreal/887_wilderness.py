"""Brokenspire's wilderness (the user's spec of 2026-11-03, docs/wilderness.txt; C++ RD/RDWild*.cpp): run on the open
brokenspire level (play stopped). Parts (argv, default "materials,data,level"):
  materials  /Game/RandomDungeon/Wild/M_RD_WildGround (the terrain chunks' ground: the world's colour from above in the
             vertex colour, its layers (rock, snow / sand, mud) in UV1 / UV2 carried by Hive Sherwood's, AlienPlanet's
             textures' detail; lava glowing from the vertex alpha), M_RD_WildWater with MI_RD_WildSea / MI_RD_WildSpring
             (depth in the vertex colour's red, a panning normal), M_RD_WildLava
  data       the generator's WildBiomes from SourceArt/wilderness/biomes.json (each plant and rock scaled to the height the
             table gives it, from its mesh's bounds; a missing mesh is reported and left out), WildPieces / WildPieceScale (the
             places' props), the fire and steam effects
  symbols    the map's symbols (blender_numpy/wild_symbols.py writes SourceArt/wilderness/symbols/wmap_*.png) into UIArt
  level      bWild on, the 4 km far-ground plane taken out (the terrain is the ground now; hidden, she still ran on it), the level saved
  trees      the aspen, birch and acacia made in Blender (blender_numpy/wild_trees.py) imported, their bark and leaf materials
  fixmats    FrozenNorseEnvironment's cliff, ice and runestone masters do not compile here ("MatLayerBlend_Simple: arithmetic
             between float3 and float4"): its boulders, cliffs, rock clusters, glaciers and ice get materials of our own made
             from each broken instance's textures (rock with snow on top, pale ice), set on the meshes (the pack's own copy here)
Args: [parts] e.g.  python ue_exec.py 887_wilderness.py data,level"""
import unreal, json, os, sys, gc

MEL = unreal.MaterialEditingLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary
D = "/Game/RandomDungeon/Wild"
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
JSON = os.path.join(REPO, "claude_ue5", "SourceArt", "wilderness", "biomes.json")
PARTS = (sys.argv[1] if len(sys.argv) > 1 else "materials,trees,fixmats,data,symbols,level").split(",")
SHAPES = {n: i for i, n in enumerate(["plains", "rolling", "hills", "moor", "mountains", "peaks", "glacial", "mesa", "canyon", "canyon_net", "volcano", "caldera",
                                     "lava_field", "marsh", "coastal", "rocky_coast", "steppe", "dunes"])}
CULL = {"tree": 110000, "ice": 110000, "rock": 60000, "bush": 25000, "log": 20000, "grass": 6000, "flower": 5000, "reed": 9000, "crop": 7000}
REPORT = []
WILD_FOG = {"falloff": 0.0015, "density": 0.02, "start": 25000.0, "max": 0.94}


def gen():
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.RDDungeonGenerator):
        return w, a
    raise RuntimeError("no RDDungeonGenerator in the open level")


def sampler_type(t):
    comp = t.get_editor_property("compression_settings"); srgb = t.get_editor_property("srgb")
    if t.get_editor_property("virtual_texture_streaming"):
        if comp == unreal.TextureCompressionSettings.TC_NORMALMAP: return unreal.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_NORMAL
        return unreal.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_COLOR if srgb else unreal.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_LINEAR_COLOR
    if comp == unreal.TextureCompressionSettings.TC_NORMALMAP: return unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    if comp in (unreal.TextureCompressionSettings.TC_GRAYSCALE, unreal.TextureCompressionSettings.TC_ALPHA):
        return unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE if not srgb else unreal.MaterialSamplerType.SAMPLERTYPE_GRAYSCALE
    if comp == unreal.TextureCompressionSettings.TC_MASKS: return unreal.MaterialSamplerType.SAMPLERTYPE_MASKS
    return unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR if not srgb else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR


class MB:
    """a material built node by node"""
    def __init__(self, name):
        # (an existing one is cleared and built again in place: deleted, it left every mesh slot that named it empty)
        p = f"{D}/{name}"
        if eal.does_asset_exist(p):
            self.m = unreal.load_asset(p); MEL.delete_all_material_expressions(self.m)
        else: self.m = at.create_asset(name, D, unreal.Material, unreal.MaterialFactoryNew())
        self.y = 0
    def n(self, cls, x=-600, **props):
        self.y += 110
        e = MEL.create_material_expression(self.m, cls, x, self.y)
        for k, v in props.items(): e.set_editor_property(k, v)
        return e
    def c(self, a, ap, b, bp): MEL.connect_material_expressions(a, ap, b, bp)
    def out(self, e, pin, prop): MEL.connect_material_property(e, pin, prop)
    def mask(self, src, pin, r=False, g=False, b=False, a=False):
        e = self.n(unreal.MaterialExpressionComponentMask, r=r, g=g, b=b, a=a); self.c(src, pin, e, ""); return e
    def tex(self, path, uv, x=-1000):
        t = unreal.load_asset(path)
        if not t: raise RuntimeError(f"no texture {path}")
        s = self.n(unreal.MaterialExpressionTextureSample, x, texture=t, sampler_type=sampler_type(t), sampler_source=unreal.SamplerSourceMode.SSM_WRAP_WORLD_GROUP_SETTINGS)
        self.c(uv, "", s, "UVs"); return s
    def mul(self, a, b, ap="", bp="", x=-400):
        e = self.n(unreal.MaterialExpressionMultiply, x); self.c(a, ap, e, "A"); self.c(b, bp, e, "B"); return e
    def lerp(self, a, b, al, ap="", bp="", alp="", x=-300):
        e = self.n(unreal.MaterialExpressionLinearInterpolate, x); self.c(a, ap, e, "A"); self.c(b, bp, e, "B"); self.c(al, alp, e, "Alpha"); return e
    def const(self, v, x=-800): return self.n(unreal.MaterialExpressionConstant, x, r=v)
    def const3(self, rgb, x=-800): return self.n(unreal.MaterialExpressionConstant3Vector, x, constant=unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    def finish(self):
        MEL.recompile_material(self.m); eal.save_loaded_asset(self.m)
        st = MEL.get_statistics(self.m)
        REPORT.append(f"{self.m.get_name()}: {st.num_pixel_shader_instructions} pixel instructions, {st.num_samplers} samplers")
        return self.m


def materials():
    if not eal.does_directory_exist(D): eal.make_directory(D)
    S = "/Game/Hive_Sherwood/Textures/"
    # ---- the ground
    b = MB("M_RD_WildGround")
    # (the detail's coordinates from the world position, a repeat every 4 m: the procedural mesh keeps its UVs at half
    # precision, and the continent's coordinates (up to 75000 repeats) came out as one texel everywhere)
    wpos = b.n(unreal.MaterialExpressionWorldPosition, -1700)
    wxy = b.mask(wpos, "", r=True, g=True)
    uv0 = b.n(unreal.MaterialExpressionDivide, -1500); b.c(wxy, "", uv0, "A"); uv0.set_editor_property("const_b", 400.0)
    uv0b = b.n(unreal.MaterialExpressionMultiply, -1350); b.c(uv0, "", uv0b, "A"); uv0b.set_editor_property("const_b", 0.5)
    uv1 = b.n(unreal.MaterialExpressionTextureCoordinate, -1500, coordinate_index=1)
    uv2 = b.n(unreal.MaterialExpressionTextureCoordinate, -1500, coordinate_index=2)
    # (the road's own layer since the list of 2026-11-04: "the road outside brokenspire is ... not visible in the wilderness":
    # it was 80 % of the mud. UV3's U, the lake village's soil road)
    uv3 = b.n(unreal.MaterialExpressionTextureCoordinate, -1500, coordinate_index=3)
    rock = b.mask(uv1, "", r=True); snow = b.mask(uv1, "", g=True); sand = b.mask(uv2, "", r=True); mud = b.mask(uv2, "", g=True); road = b.mask(uv3, "", r=True)
    ML = "/Game/Medieval_Lake_Village/Textures/"
    L = {"grass": (S + "T_Grass_BC", S + "T_Grass_N", uv0), "rock": (S + "T_RockyCliff_A_basecolor", S + "T_RockyCliff_A_normal", uv0b),
         "sand": (S + "T_Sand_basecolor", S + "T_Sand_normal", uv0), "mud": (S + "T_Mud_BC", S + "T_Mud_N", uv0),
         "road": (ML + "T_SoilRoad_BC", ML + "T_SoilRoad_N", uv0),
         "snow": ("/Game/AlienPlanet/Textures/Snow/T_Snow_B", "/Game/AlienPlanet/Textures/Snow/T_Snow_N", uv0)}
    T = {k: (b.tex(bc, u), b.tex(nm, u)) for k, (bc, nm, u) in L.items()}
    def chain(i):
        e = b.lerp(T["grass"][i], T["rock"][i], rock)
        e = b.lerp(e, T["sand"][i], sand)
        e = b.lerp(e, T["mud"][i], mud)
        e = b.lerp(e, T["road"][i], road)
        return b.lerp(e, T["snow"][i], snow)
    det = chain(0)
    # (the texture gives its detail as brightness against its own average (its coarsest mip); the hue is the world's own, from
    # above; a constant for the average clamped every pixel to the floor: no detail at all)
    avg = {}
    for k, (bc, nm, u) in L.items():
        s = b.tex(bc, u); s.set_editor_property("mip_value_mode", unreal.TextureMipValueMode.TMVM_MIP_LEVEL); s.set_editor_property("const_mip_value", 12)
        avg[k] = s
    def chain_avg():
        e = b.lerp(avg["grass"], avg["rock"], rock); e = b.lerp(e, avg["sand"], sand); e = b.lerp(e, avg["mud"], mud); e = b.lerp(e, avg["road"], road); return b.lerp(e, avg["snow"], snow)
    da = chain_avg()
    lum = b.n(unreal.MaterialExpressionDotProduct, -200); b.c(det, "", lum, "A"); b.c(b.const3((0.30, 0.59, 0.11)), "", lum, "B")
    lua = b.n(unreal.MaterialExpressionDotProduct, -200); b.c(da, "", lua, "A"); b.c(b.const3((0.30, 0.59, 0.11)), "", lua, "B")
    lmx = b.n(unreal.MaterialExpressionMax, -150); b.c(lua, "", lmx, "A"); lmx.set_editor_property("const_b", 0.01)
    ln = b.n(unreal.MaterialExpressionDivide, -100); b.c(lum, "", ln, "A"); b.c(lmx, "", ln, "B")
    cl = b.n(unreal.MaterialExpressionClamp, 0, min_default=0.35, max_default=1.9); b.c(ln, "", cl, "")
    # (large soft patches: the macro variation texture at 160 m)
    mu = b.n(unreal.MaterialExpressionMultiply, -1300); b.c(uv0, "", mu, "A"); mu.set_editor_property("const_b", 0.025)
    mac = b.tex("/Engine/EngineMaterials/T_Default_MacroVariation", mu)
    mv = b.n(unreal.MaterialExpressionLinearInterpolate, -100, const_a=0.82, const_b=1.12); b.c(mac, "R", mv, "Alpha")
    dl0 = b.lerp(b.const(1.0), cl, b.const(0.85), x=50)
    dl = b.mul(dl0, mv, x=80)
    vc = b.n(unreal.MaterialExpressionVertexColor, -600)
    tint = b.mask(vc, "", r=True, g=True, b=True)
    base = b.mul(tint, dl, x=150)
    # (the list of 2026-11-07: a farm field's rows at every pixel. The chunk gives each vertex its field's way (UV0's U, of half a
    # turn) and crop (UV0's V x 16 since the list of 2026-11-08b's thirteen crops; x 8 before) and the field's weight (UV3's V); a row's leaves over a share of it (the crop's cover), the
    # soil between, both against the field's average colour that the vertex colour already holds; faded out where a row comes
    # under about three pixels (fwidth) so that far fields do not shimmer. The crops' colours and spacing from biomes.json)
    farms = next((x for x in json.load(open(JSON, encoding="utf-8"))["biomes"] if x["name"] == "farms"), {})
    lin = lambda c: ", ".join(f"{(v / 255.0) ** 2.2:.4f}" for v in c)
    # (the chunk packs the crop as (crop + 0.5) / 16 (FRDWildWorld::MaxCrops): a 17th would read as no crop at all)
    assert len(farms.get("crops", [])) <= 16, f"{len(farms['crops'])} crops in biomes.json's farms: the ground's rows hold 16 (FRDWildWorld::MaxCrops)"
    cases = "".join(f"{'else ' if i else ''}if (k == {i}) {{ rowm = {float(c.get('row', 1.0)):.3f}; cover = {float(c.get('cover', 0.5)):.3f}; soil = float3({lin(c['soil'])}); leaf = float3({lin(c['leaf'])}); }}\n"
                    for i, c in enumerate(farms.get("crops", [])))
    rows = b.n(unreal.MaterialExpressionCustom, -100)
    rows.set_editor_property("code", "float wt = saturate(Wt);\nif (wt <= 0.001) return float3(1, 1, 1);\nint k = (int)floor(F.y * 16.0);\n"
                             "float rowm = 1.0; float cover = 0.5; float3 soil = float3(0.1, 0.07, 0.04); float3 leaf = float3(0.07, 0.13, 0.03);\n" + cases +
                             "float ang = F.x * 3.14159265;\nfloat2 acr = float2(-sin(ang), cos(ang));\nfloat ph = dot(P.xy * 0.01, acr) / rowm;\n"
                             "float fw = max(fwidth(ph), 1e-5);\nfloat d = abs(frac(ph) - 0.5) * 2.0;\nfloat s = max(0.12, fw * 1.5);\n"
                             "float band = 1.0 - smoothstep(cover - s, cover + s, d);\nfloat aa = saturate(1.6 - fw * 4.0);\n"
                             "float3 avg = lerp(soil, leaf, cover);\nfloat3 rc = lerp(soil, leaf, band);\nreturn lerp(float3(1, 1, 1), rc / max(avg, 0.005), wt * aa);")
    rows.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    ins = []
    for nm in ("P", "F", "Wt"):
        ci = unreal.CustomInput(); ci.set_editor_property("input_name", nm); ins.append(ci)
    rows.set_editor_property("inputs", ins)
    uvf = b.n(unreal.MaterialExpressionTextureCoordinate, -1500, coordinate_index=0)
    fw_ = b.mask(uv3, "", g=True)
    b.c(wpos, "", rows, "P"); b.c(uvf, "", rows, "F"); b.c(fw_, "", rows, "Wt")
    base = b.mul(base, rows, x=200)
    b.out(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    b.out(chain(1), "", unreal.MaterialProperty.MP_NORMAL)
    rough = b.lerp(b.const(0.92), b.const(0.55), snow, x=150)
    rough2 = b.lerp(rough, b.const(0.45), mud, x=200)
    b.out(rough2, "", unreal.MaterialProperty.MP_ROUGHNESS)
    em = b.mul(b.const3((9.0, 2.2, 0.4)), vc, bp="A", x=150)
    b.out(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    b.finish()
    # ---- water: depth in the vertex colour's red; two normals drifting across each other
    w = MB("M_RD_WildWater")
    wwp = w.n(unreal.MaterialExpressionWorldPosition, -1700)
    wwxy = w.mask(wwp, "", r=True, g=True)
    wp = w.n(unreal.MaterialExpressionDivide, -1500); w.c(wwxy, "", wp, "A"); wp.set_editor_property("const_b", 1600.0)
    t_ = w.n(unreal.MaterialExpressionTime, -1500)
    pans = []
    for k, (sx, sy, sc) in enumerate(((0.012, 0.007, 1.0), (-0.009, 0.011, 0.63))):
        p = w.n(unreal.MaterialExpressionPanner, -1300, speed_x=sx, speed_y=sy)
        m_ = w.n(unreal.MaterialExpressionMultiply, -1400); w.c(wp, "", m_, "A"); m_.set_editor_property("const_b", sc)
        w.c(m_, "", p, "Coordinate"); w.c(t_, "", p, "Time")
        pans.append(w.tex("/Game/Hivemind/Medieval_Docks/Water/Textures/Normals/T_Water_TilingNormal_Waves_02", p))
    nb = w.n(unreal.MaterialExpressionAdd, -300); w.c(pans[0], "", nb, "A"); w.c(pans[1], "", nb, "B")
    nn = w.n(unreal.MaterialExpressionNormalize, -200); w.c(nb, "", nn, "")
    flat = w.lerp(w.const3((0, 0, 1)), nn, w.const(0.55))
    shallow = w.n(unreal.MaterialExpressionVectorParameter, -800, parameter_name="Shallow", default_value=unreal.LinearColor(0.05, 0.11, 0.10, 1))
    deep = w.n(unreal.MaterialExpressionVectorParameter, -800, parameter_name="Deep", default_value=unreal.LinearColor(0.008, 0.035, 0.05, 1))
    wvc = w.n(unreal.MaterialExpressionVertexColor, -800)
    depth = w.mask(wvc, "", r=True)
    col = w.lerp(shallow, deep, depth)
    w.out(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    w.out(flat, "", unreal.MaterialProperty.MP_NORMAL)
    w.out(w.n(unreal.MaterialExpressionScalarParameter, -400, parameter_name="Roughness", default_value=0.05), "", unreal.MaterialProperty.MP_ROUGHNESS)
    w.out(w.const(1.0), "", unreal.MaterialProperty.MP_SPECULAR)
    glow = w.n(unreal.MaterialExpressionVectorParameter, -800, parameter_name="Glow", default_value=unreal.LinearColor(0, 0, 0, 1))
    w.out(glow, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    wm = w.finish()
    for name, sh, dp, gl, ro in (("MI_RD_WildSea", (0.03, 0.10, 0.12), (0.004, 0.022, 0.045), (0, 0, 0), 0.07), ("MI_RD_WildSpring", (0.10, 0.42, 0.42), (0.03, 0.22, 0.26), (0.01, 0.04, 0.04), 0.03)):
        p = f"{D}/{name}"
        if not eal.does_asset_exist(p): at.create_asset(name, D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mi = unreal.load_asset(p); MEL.set_material_instance_parent(mi, wm)
        MEL.set_material_instance_vector_parameter_value(mi, "Shallow", unreal.LinearColor(*sh, 1)); MEL.set_material_instance_vector_parameter_value(mi, "Deep", unreal.LinearColor(*dp, 1))
        MEL.set_material_instance_vector_parameter_value(mi, "Glow", unreal.LinearColor(*gl, 1)); MEL.set_material_instance_scalar_parameter_value(mi, "Roughness", ro)
        eal.save_loaded_asset(mi, only_if_is_dirty=False)
    # ---- lava: glowing, slowly churning
    v = MB("M_RD_WildLava")
    vwp = v.n(unreal.MaterialExpressionWorldPosition, -1700)
    vwxy = v.mask(vwp, "", r=True, g=True)
    vt = v.n(unreal.MaterialExpressionDivide, -1500); v.c(vwxy, "", vt, "A"); vt.set_editor_property("const_b", 1600.0)
    vtm = v.n(unreal.MaterialExpressionMultiply, -1400); v.c(vt, "", vtm, "A"); vtm.set_editor_property("const_b", 0.25)
    vp = v.n(unreal.MaterialExpressionPanner, -1300, speed_x=0.01, speed_y=0.004); v.c(vtm, "", vp, "Coordinate")
    mac = v.tex("/Engine/EngineMaterials/T_Default_MacroVariation", vp)
    crust = v.n(unreal.MaterialExpressionSmoothStep, -500, const_min=0.35, const_max=0.62); v.c(mac, "R", crust, "Value")
    hot = v.lerp(v.const3((14.0, 3.2, 0.5)), v.const3((0.25, 0.04, 0.01)), crust)
    v.out(hot, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    v.out(v.lerp(v.const3((0.3, 0.06, 0.02)), v.const3((0.05, 0.04, 0.04)), crust), "", unreal.MaterialProperty.MP_BASE_COLOR)
    v.out(v.const(0.6), "", unreal.MaterialProperty.MP_ROUGHNESS)
    v.finish()


FN = "/Game/FrozenNorseEnvironment"
FIX = {   # the broken instance: (kind, base colour texture, normal, ORM, base colour tiling)
    "MI_Cliffs_Asset01": ("rock", FN + "/Textures/T_Cliff/T_Rough_Cliff_BC", FN + "/Textures/SM_Cliff_01/T_Cliff_01_N", FN + "/Textures/SM_Cliff_01/T_Cliff_01_ORM", 7.0),
    "MI_Cliffs_RockCluster": ("rock", FN + "/Textures/T_Cliff/T_Rough_Cliff_BC", FN + "/Textures/SM_RockCluster/T_RockCluster_N", FN + "/Textures/SM_RockCluster/T_RockCluster_ORM", 5.0),
    "MI_Ice_GlacialsKit": ("ice", None, FN + "/Textures/SM_GlacialsPack/T_Glacials_N", None, 1.0),
    "MI_Ice_Icicle_Kit": ("ice", None, FN + "/Textures/SM_Ice_Kit/T_Icicle_Kit_N", None, 1.0),
    "MI_Ice_IceFormation": ("ice", None, FN + "/Textures/SM_Ice_Formation/T_IceFormation_N", None, 1.0),
}


def fixmats():
    made = {}
    for mi, (kind, bc, nm, orm, tile) in FIX.items():
        b = MB(f"M_RD_Fix_{mi[3:]}")
        uv = b.n(unreal.MaterialExpressionTextureCoordinate, -1500, coordinate_index=0)
        nrm = b.tex(nm, uv)
        b.out(nrm, "", unreal.MaterialProperty.MP_NORMAL)
        wn = b.n(unreal.MaterialExpressionVertexNormalWS, -900)
        up = b.n(unreal.MaterialExpressionSmoothStep, -700, const_min=0.55, const_max=0.85); b.c(wn, "B", up, "Value")
        snowc = b.const3((0.80, 0.83, 0.88))
        if kind == "rock":
            ut = b.n(unreal.MaterialExpressionMultiply, -1300); b.c(uv, "", ut, "A"); ut.set_editor_property("const_b", tile)
            col = b.tex(bc, ut); o = b.tex(orm, uv)
            ao = b.mul(col, o, bp="R")
            base = b.lerp(ao, snowc, up)
            b.out(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
            b.out(b.lerp(o, b.const(0.6), up, ap="G"), "", unreal.MaterialProperty.MP_ROUGHNESS)
        else:
            fr = b.n(unreal.MaterialExpressionFresnel, -700, exponent=3.0)
            base = b.lerp(b.const3((0.42, 0.62, 0.74)), b.const3((0.78, 0.88, 0.94)), fr)
            b.out(b.lerp(base, snowc, up), "", unreal.MaterialProperty.MP_BASE_COLOR)
            b.out(b.const(0.12), "", unreal.MaterialProperty.MP_ROUGHNESS)
            b.out(b.const(0.8), "", unreal.MaterialProperty.MP_SPECULAR)
            b.out(b.const3((0.015, 0.04, 0.06)), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        b.m.set_editor_property("used_with_instanced_static_meshes", True)
        made[mi] = b.finish()
    # every FrozenNorse mesh wearing one of them gets ours
    n = 0
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    for ad in reg.get_assets_by_path(FN + "/Meshes", recursive=True):
        if str(ad.asset_class_path.asset_name) != "StaticMesh": continue
        m = ad.get_asset()
        mats = m.get_editor_property("static_materials"); ch = False; new = []
        # (run again: a mesh already given ours names the one made anew by its own name)
        by_fix = {f"M_RD_Fix_{k[3:]}": v for k, v in made.items()}
        for sm in mats:
            mt = sm.get_editor_property("material_interface"); slot = str(sm.get_editor_property("material_slot_name"))
            key = mt.get_name() if mt else ""
            if key in by_fix: key = "MI_" + key[9:]
            if key not in made and slot in made: key = slot
            if key not in made and not mt:
                # (a slot left empty by an earlier run that deleted our material: its mesh's kind names it)
                mn = m.get_name()
                key = ("MI_Ice_IceFormation" if "Ice_Formation" in mn else "MI_Ice_GlacialsKit" if "Glaciar" in mn else "MI_Ice_Icicle_Kit" if "Ice" in mn
                       else "MI_Cliffs_RockCluster" if "RockCluster" in mn else "MI_Cliffs_Asset01" if any(k in mn for k in ("Boulder", "Cliff", "Mountain", "Horst")) else "")
            if key in made: ch = True
            new.append(unreal.StaticMaterial(material_interface=made[key] if key in made else mt, material_slot_name=sm.get_editor_property("material_slot_name")))
        if ch:
            m.modify(); m.set_editor_property("static_materials", new); eal.save_loaded_asset(m, only_if_is_dirty=False); n += 1
    REPORT.append(f"fixmats: {len(made)} materials, {n} FrozenNorse meshes given them")


def srgb(c):
    return unreal.LinearColor(*[(x / 255.0) ** 2.2 for x in c], 1.0)


def mesh_height(m):
    bb = m.get_bounding_box()
    return max(1.0, bb.max.z - bb.min.z)


def data():
    w, g = gen()
    J = json.load(open(JSON, encoding="utf-8"))
    out = []; missing = []
    # (the list of 2026-11-04: more of each kind, sizes that vary more, bushes and ferns added by groups of biomes)
    L7 = J.get("list7", {}); DENS = L7.get("density", {}); SCALE = L7.get("scale", {})
    EXTRA = {}
    for names, entry in L7.get("extra", []):
        for n in names: EXTRA.setdefault(n, []).append(entry)
    for b in J["biomes"]:
        b = dict(b); b["foliage"] = list(b.get("foliage", [])) + EXTRA.get(b["name"], [])
        B = unreal.RDWildBiome()
        B.set_editor_property("name", b["name"]); B.set_editor_property("shape", SHAPES[b["shape"]])
        B.set_editor_property("base", float(b["base"])); B.set_editor_property("amp", float(b["amp"]))
        B.set_editor_property("color_a", srgb(b["a"])); B.set_editor_property("color_b", srgb(b["b"])); B.set_editor_property("rock", srgb(b["rock"]))
        B.set_editor_property("snow", float(b.get("snow", 0))); B.set_editor_property("canopy", float(b.get("canopy", 0)))
        B.set_editor_property("ponds", float(b.get("ponds", 0))); B.set_editor_property("steam", float(b.get("steam", 0)))
        Ly = b.get("layers", [0, 0, 0, 0]); B.set_editor_property("layers", unreal.Vector4(*[float(x) for x in Ly]))
        # (the list of 2026-11-07: a farm's fields' crops (898): their soil and leaves seen from afar, their rows' spacing)
        crops = []
        for c in b.get("crops", []):
            C = unreal.RDWildCrop()
            C.set_editor_property("name", c["name"]); C.set_editor_property("soil", srgb(c["soil"])); C.set_editor_property("leaf", srgb(c["leaf"]))
            C.set_editor_property("cover", float(c.get("cover", 0.5))); C.set_editor_property("row_m", float(c.get("row", 1.0)))
            # (the list of 2026-11-08b: how often a field grows it, the commonest medieval crops first)
            C.set_editor_property("weight", float(c.get("weight", 1.0)))
            crops.append(C)
        B.set_editor_property("crops", crops)
        fol = []
        for f in b.get("foliage", []):
            path, kind, dens, hm, flags = f[:5]
            row = f[5] if len(f) > 5 else {}
            m = unreal.load_asset(path)
            if not m or not isinstance(m, unreal.StaticMesh): missing.append(f"{b['name']}: {path}"); continue
            sc = hm * 100.0 / mesh_height(m)
            F = unreal.RDWildFoliage()
            F.set_editor_property("mesh", m); F.set_editor_property("kind", kind); F.set_editor_property("density", float(dens) * float(DENS.get(kind, 1.0)))
            lo, hi = SCALE.get(kind, [0.8, 1.2])
            F.set_editor_property("scale_min", sc * lo); F.set_editor_property("scale_max", sc * hi)
            s = 30.0
            if "s" in flags:
                i = flags.index("s"); s = float("".join(ch for ch in flags[i + 1:] if ch.isdigit()) or 30)
            elif kind in ("grass", "flower", "reed", "crop"): s = 38.0
            elif kind == "tree": s = 32.0
            elif kind in ("rock", "ice"): s = 55.0
            F.set_editor_property("slope_max", s)
            sink_cm = {"tree": 20.0, "rock": hm * 100 * 0.2, "ice": hm * 100 * 0.25, "log": 8.0}.get(kind, 3.0)
            F.set_editor_property("sink", sink_cm / sc)
            F.set_editor_property("cull_distance", float(CULL.get(kind, 30000) if not (kind == "rock" and hm < 1.5) else 20000))
            F.set_editor_property("collision", "c" in flags); F.set_editor_property("align", "a" in flags)
            F.set_editor_property("near_only", "n" in flags); F.set_editor_property("clump", 0.8 if "k" in flags else 0.0)
            F.set_editor_property("near_water", -1.0 if "W" in flags else (1.0 if "w" in flags else 0.0))
            # (a field crop: planted in its field's rows, step m apart along them; per hectare only weighs its kinds)
            if "crop" in row:
                F.set_editor_property("crop", int(row["crop"])); F.set_editor_property("step_m", float(row.get("step", 0.8)))
                F.set_editor_property("density", float(dens))
            fol.append(F)
        B.set_editor_property("foliage", fol)
        out.append(B)
    g.set_editor_property("wild_biomes", out)
    pieces = {}; scales = {}
    for kind, paths in J["pieces"].items():
        for i, path in enumerate(paths):
            m = unreal.load_asset(path)
            if not m or not isinstance(m, unreal.StaticMesh): missing.append(f"piece {kind}: {path}"); continue
            pieces[f"{kind}{i + 1}"] = m
            scales[m.get_name()] = J["heights"].get(kind, 2.0) * 100.0 / mesh_height(m)
    g.set_editor_property("wild_pieces", pieces); g.set_editor_property("wild_piece_scale", scales)
    fire = unreal.load_asset("/Game/Medieval_Lake_Village/VFX/NS_Fire"); steam = unreal.load_asset("/Game/UndergroundBunker/Particles/NS1_Smoke/NS_NS1_Steam")
    if fire: g.set_editor_property("wild_fire_fx", fire)
    if steam: g.set_editor_property("wild_steam_fx", steam)
    for p, prop in ((f"{D}/M_RD_WildGround", "wild_ground_material"), (f"{D}/M_RD_WildWater", "wild_water_material"), (f"{D}/MI_RD_WildSea", "wild_sea_material"),
                    (f"{D}/MI_RD_WildSpring", "wild_spring_material"), (f"{D}/M_RD_WildLava", "wild_lava_material")):
        a = unreal.load_asset(p)
        if a: g.set_editor_property(prop, a)
        else: missing.append(f"material {p}")
    REPORT.append(f"{len(out)} biomes, {sum(len(b.get_editor_property('foliage')) for b in out)} plants and rocks, {len(pieces)} pieces")
    if missing: REPORT.append("MISSING: " + "; ".join(missing))


def level():
    w, g = gen()
    g.set_editor_property("wild", True)
    # (one continent for every game: the towns the spec names stand where it says, and a test sees what a player sees)
    g.set_editor_property("wild_seed_fixed", 20261103)
    # (the level's kill height came from the castle's: the sea floor is 117 m below Brokenspire's ground, the marshes 45 m;
    # a pawn below it was destroyed (her too, and the wilderness's tick waited for a pawn for ever))
    ws = w.get_world_settings(); ws.set_editor_property("kill_z", -5000000.0)
    REPORT.append("kill z -50 km")
    # the fog: nearly the same at every height (the town's thickened sharply below its own height, and washed out the coasts
    # and valleys 50 m and more below Brokenspire's ground), from 250 m on, so that the 2 km of terrain round her fades out
    for f in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.ExponentialHeightFog):
        c = f.get_component_by_class(unreal.ExponentialHeightFogComponent)
        c.set_editor_property("fog_height_falloff", float(WILD_FOG["falloff"])); c.set_editor_property("fog_density", float(WILD_FOG["density"]))
        c.set_editor_property("start_distance", float(WILD_FOG["start"])); c.set_editor_property("fog_max_opacity", float(WILD_FOG["max"]))
        # (the volumetric fog lies over the first tens of metres whatever the start distance: the near ground came out washed white)
        c.set_editor_property("enable_volumetric_fog", False)
        REPORT.append(f"fog {WILD_FOG}")
    # (881's 4 km far-ground plane at z -6 cm: the terrain is the ground now. Hidden with its collision set off it still stood
    # in play (the component's collision call did not keep in the saved level): within 2 km of Brokenspire she ran on it 2 m
    # over the drawn ground wherever the land dips (the list of 2026-11-07, 888 ground8: "running in the air"). Taken out)
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.StaticMeshActor):
        if a.get_actor_label() == "BS_FarGround":
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(a)
            REPORT.append("BS_FarGround taken out")
    # (the saved town built again with the gate open: no leaves, bar or blocker)
    g.build_start_section()
    REPORT.append("Brokenspire built again (the gate open)")
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    REPORT.append("level saved")


def trees():
    """the aspen, birch and acacia made in Blender (blender_numpy/wild_trees.py -> SourceArt/wilderness/trees) imported, with
    their bark and leaves (a masked, two-sided material for the leaf cards)"""
    src = os.path.join(REPO, "claude_ue5", "SourceArt", "wilderness", "trees")
    if not os.path.isdir(src): REPORT.append(f"trees: none in {src} (run blender_numpy/wild_trees.py)"); return
    dest = f"{D}/Trees"
    pngs = [f for f in sorted(os.listdir(src)) if f.endswith(".png")]
    fbxs = [f for f in sorted(os.listdir(src)) if f.endswith(".fbx")]
    tasks = []
    for f in pngs:
        tk = unreal.AssetImportTask(); tk.set_editor_property("filename", os.path.join(src, f)); tk.set_editor_property("destination_path", dest)
        tk.set_editor_property("replace_existing", True); tk.set_editor_property("automated", True); tk.set_editor_property("save", True); tasks.append(tk)
    for f in fbxs:
        o = unreal.FbxImportUI(); o.import_mesh = True; o.import_materials = False; o.import_textures = False; o.import_as_skeletal = False
        o.static_mesh_import_data.combine_meshes = True; o.static_mesh_import_data.auto_generate_collision = True; o.static_mesh_import_data.generate_lightmap_u_vs = False
        tk = unreal.AssetImportTask(); tk.set_editor_property("filename", os.path.join(src, f)); tk.set_editor_property("destination_path", dest)
        tk.set_editor_property("replace_existing", True); tk.set_editor_property("automated", True); tk.set_editor_property("save", True); tk.set_editor_property("options", o); tasks.append(tk)
    at.import_asset_tasks(tasks)
    # the two masters: bark, leaves (masked, both faces); used on instanced meshes (a packaged game draws them only so)
    def master(name, leaf):
        b = MB(name)
        tx = unreal.load_asset(f"{dest}/T_Wild_Aspen{'Leaves' if leaf else 'Bark'}")
        uv = b.n(unreal.MaterialExpressionTextureCoordinate, -1500, coordinate_index=0)
        s = b.n(unreal.MaterialExpressionTextureSampleParameter2D, -1000, parameter_name="Tex", texture=tx, sampler_type=sampler_type(tx))
        b.c(uv, "", s, "UVs")
        b.out(s, "", unreal.MaterialProperty.MP_BASE_COLOR)
        b.out(b.const(0.72 if leaf else 0.88), "", unreal.MaterialProperty.MP_ROUGHNESS)
        if leaf:
            b.m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED); b.m.set_editor_property("two_sided", True)
            b.out(s, "A", unreal.MaterialProperty.MP_OPACITY_MASK)
        b.m.set_editor_property("used_with_instanced_static_meshes", True)
        return b.finish()
    mb, ml = master("M_RD_WildBark", False), master("M_RD_WildLeaves", True)
    n = 0
    for kind in ("Aspen", "Birch", "Acacia"):
        mis = []
        for part, parent in (("Bark", mb), ("Leaves", ml)):
            nm = f"MI_RD_Wild{kind}{part}"; pth = f"{dest}/{nm}"
            if not eal.does_asset_exist(pth): at.create_asset(nm, dest, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
            mi = unreal.load_asset(pth); MEL.set_material_instance_parent(mi, parent)
            tx = unreal.load_asset(f"{dest}/T_Wild_{kind}{part}")
            if tx: MEL.set_material_instance_texture_parameter_value(mi, "Tex", tx)
            eal.save_loaded_asset(mi, only_if_is_dirty=False); mis.append(mi)
        for v in ("A", "B"):
            m = unreal.load_asset(f"{dest}/SM_Wild_{kind}_{v}")
            if not m: REPORT.append(f"tree SM_Wild_{kind}_{v} not imported"); continue
            # (the slots' list built anew: its elements are copies, set one by one they kept the default material)
            new = []
            for i, s_ in enumerate(m.get_editor_property("static_materials")):
                nm_ = s_.get_editor_property("material_slot_name")
                new.append(unreal.StaticMaterial(material_interface=mis[1] if "Leaves" in str(nm_) or (i == 1 and "Bark" not in str(nm_)) else mis[0], material_slot_name=nm_))
            m.modify(); m.set_editor_property("static_materials", new); eal.save_loaded_asset(m, only_if_is_dirty=False)
            got = [x.get_editor_property("material_interface").get_name() for x in m.get_editor_property("static_materials")]
            if any(g_ == "WorldGridMaterial" for g_ in got): REPORT.append(f"tree {m.get_name()} kept the default material")
            n += 1
    REPORT.append(f"trees: {n} meshes")


def symbols():
    """the map's symbols (blender_numpy/wild_symbols.py's PNGs) into the generator's UIArt as wmap_<kind>"""
    src = os.path.join(REPO, "claude_ue5", "SourceArt", "wilderness", "symbols")
    files = {f[:-4]: os.path.join(src, f) for f in sorted(os.listdir(src)) if f.startswith("wmap_") and f.endswith(".png")} if os.path.isdir(src) else {}
    if not files: REPORT.append(f"symbols: none in {src} (run blender_numpy/wild_symbols.py)"); return
    dest = f"{D}/Map"
    tasks = []
    for n, p in files.items():
        tk = unreal.AssetImportTask(); tk.set_editor_property("filename", p); tk.set_editor_property("destination_path", dest)
        tk.set_editor_property("destination_name", "T_" + n); tk.set_editor_property("replace_existing", True); tk.set_editor_property("automated", True); tk.set_editor_property("save", False)
        tasks.append(tk)
    at.import_asset_tasks(tasks)
    w, g = gen()
    ua = g.get_editor_property("ui_art")
    for n in files:
        a = unreal.load_asset(f"{dest}/T_{n}")
        if not a: REPORT.append(f"symbol {n} not imported"); continue
        a.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
        a.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
        a.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP if n == "wmap_fog" else unreal.TextureMipGenSettings.TMGS_SIMPLE_AVERAGE)
        a.set_editor_property("never_stream", True); a.set_editor_property("srgb", True)
        eal.save_loaded_asset(a, False)
        art = unreal.RDUIArt(); art.set_editor_property("texture", a)
        art.set_editor_property("border", unreal.Vector4(0, 0, 0, 0)); art.set_editor_property("inner", unreal.Vector4(0, 0, 1, 1))
        ua[unreal.Name(n)] = art
    g.set_editor_property("ui_art", ua)
    REPORT.append(f"symbols: {len(files)}")


if "materials" in PARTS: materials()
if "trees" in PARTS: trees()
if "fixmats" in PARTS: fixmats()
if "data" in PARTS: data()
if "symbols" in PARTS: symbols()
if "level" in PARTS: level()
print("WILD887 " + " | ".join(REPORT))
del MEL, at, eal
gc.collect()
