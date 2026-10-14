"""Monster gallery for docs/monsters.md: a picture of every monster ranked there, with its own textures, and three
recoloured versions of it. The list is SourceArt/monster_gallery/monsters.json (rank, name, pack, the meshes of the
model, its looks). Everything is shot in the scratch level /Game/RandomLevel/Test/rl_scratch, which is left empty.
One mode per call: shaders compile and textures stream in between editor ticks, never inside one Python call (a first
try shot most monsters with the engine's grey placeholder: their materials were still compiling).
  unity      import the two packs that exist only in Unity format (pipeline/blender_numpy/unity_extract.py them into
             SourceArt/fab_unity/<Pack> first): Creatures Insects Pack and Humanoids Monsters Pack -> /Game/<Pack>: the
             five meshes of each, their textures and one material each (an instance of M_MON_Variant with its own colours,
             Unity's metallic / smoothness map, the normal map's green flipped); writes their meshes into monsters.json
  materials  M_MON_Variant and M_MON_VariantMasked (/Game/MonsterGallery/Materials): base colour, normal and metallic /
             smoothness textures; with Recolor 0 the texture's own colours, with Recolor 1 a scheme: the base colour's
             brightness mapped onto three colours (dark, mid, light) and a pattern that follows the body (computed from
             the pre-skinned position, so it is the same in any pose): 1 cracked stone, 2 scales, 3 crystal facets, with
             glowing edges where EdgeGlow is set. The masked one (two-sided, opacity from the base colour's alpha) is for
             hair, fur and wool.
  stage      every monster in a row 2 km above the scratch level (one actor per mesh), lights, a floor, texture
             streaming off (all mips load)
  warm       the three schemes put once on every staged monster: the master's shaders compile for each kind of mesh
             while the editor runs (shot at once, a mesh new to them came out grey)
  shoot dir [ranks|all] [masks]  for each monster: its own materials, then the three schemes -> dir/<rank>_<look>.png
             (look: original, infernal, venom, frost; a 180 cm post stands beside it for scale), and <rank>_mask.png (the
             monster alone on black: monster_doc.py crops to it); `masks`: only the masks
  clear      the staged actors removed, texture streaming back on
Args: mode [dir]"""
import sys, os, re, json, math, unreal
MODE = sys.argv[1]
V = unreal.Vector; ML = unreal.MathLibrary; MEL = unreal.MaterialEditingLibrary; MP = unreal.MaterialProperty
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
DATA = os.path.join(SA, "monster_gallery", "monsters.json")
MDIR = "/Game/MonsterGallery/Materials"
SCRATCH = "/Game/RandomLevel/Test/rl_scratch"
TAG = unreal.Name("mon_gallery")
SPACING = 6000.0; ORIGIN = V(0, 0, 200000.0)
# the three schemes: dark / mid / light colours, pattern kind, its size (cm), strength, glowing edges, roughness, metallic
SCHEMES = {
    "infernal": {"Dark": (0.012, 0.004, 0.003), "Mid": (0.22, 0.03, 0.012), "Light": (0.95, 0.42, 0.08), "Kind": 1.0, "Scale": 13.0, "Strength": 0.7, "EdgeGlow": (3.5, 0.8, 0.1), "Roughness": 0.75, "Metallic": 0.0},
    "venom": {"Dark": (0.01, 0.025, 0.006), "Mid": (0.16, 0.36, 0.03), "Light": (0.85, 0.95, 0.25), "Kind": 2.0, "Scale": 3.2, "Strength": 0.8, "EdgeGlow": (0.0, 0.0, 0.0), "Roughness": 0.38, "Metallic": 0.0},
    "frost": {"Dark": (0.02, 0.05, 0.12), "Mid": (0.28, 0.5, 0.78), "Light": (0.92, 0.97, 1.0), "Kind": 3.0, "Scale": 6.0, "Strength": 0.6, "EdgeGlow": (0.25, 0.6, 1.0), "Roughness": 0.2, "Metallic": 0.15},
}


def load_data(): return json.load(open(DATA, encoding="utf-8"))


def cleanup():
    import gc
    for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
    gc.collect()


# ================================================================================================ materials
CODE = r"""
struct FMon
{
    float3 h3(float3 p) { p = float3(dot(p, float3(127.1, 311.7, 74.7)), dot(p, float3(269.5, 183.3, 246.1)), dot(p, float3(113.5, 271.9, 124.6))); return frac(sin(p) * 43758.5453); }
    float3 vor(float3 x)
    {
        float3 i = floor(x), f = frac(x); float d1 = 8.0, d2 = 8.0, id = 0.0;
        for (int a = -1; a <= 1; a++) for (int b = -1; b <= 1; b++) for (int c = -1; c <= 1; c++)
        {
            float3 g = float3(a, b, c); float3 o = h3(i + g); float3 r = g + o - f; float d = dot(r, r);
            if (d < d1) { d2 = d1; d1 = d; id = o.x; } else if (d < d2) { d2 = d; }
        }
        return float3(sqrt(d1), sqrt(d2), id);
    }
};
FMon F;
float3 base = Base.rgb;
float L = saturate(dot(base, float3(0.299, 0.587, 0.114)) * 1.6);
float3 g = L < 0.5 ? lerp(Dark, Mid, L * 2.0) : lerp(Mid, Light, L * 2.0 - 1.0);
float3 v = F.vor(P / max(Scale, 0.1));
float edge = 1.0 - smoothstep(0.0, 0.045, v.y - v.x);
float pat = 0.0;
if (Kind < 0.5) pat = 0.0;
else if (Kind < 1.5) pat = -edge * 0.9 + (v.z - 0.5) * 0.35;                                   // cracked stone
else if (Kind < 2.5) pat = (0.3 - v.x) * 1.3 + (v.z - 0.5) * 0.3 - edge * 0.7;                 // scales
else pat = (v.z - 0.5) * 0.6 + edge * 0.6;                                                      // crystal facets
float3 col = saturate(g * (1.0 + pat * Strength));
float lit = Kind < 1.5 ? step(0.55, v.z) : 1.0;                                                // (only some cracks glow)
return float4(lerp(base, col, Recolor), edge * lit * Recolor * step(0.5, Kind));
"""


def node(m, cls, x, y, **props):
    e = MEL.create_material_expression(m, cls, x, y)
    for k, v in props.items(): e.set_editor_property(k, v)
    return e


def link(a, out, b, inp): assert MEL.connect_material_expressions(a, out, b, inp), ("connect", a.get_name(), out, b.get_name(), inp)


def build_master(name, masked):
    path = MDIR + "/" + name
    if eal.does_asset_exist(path): m = unreal.load_asset(path); MEL.delete_all_material_expressions(m)
    else: m = at.create_asset(name, MDIR, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED if masked else unreal.BlendMode.BLEND_OPAQUE)
    m.set_editor_property("two_sided", masked)
    T = unreal.MaterialSamplerType
    btex = node(m, unreal.MaterialExpressionTextureSampleParameter2D, -1700, -300, parameter_name="BaseTex", sampler_type=T.SAMPLERTYPE_COLOR,
                texture=unreal.load_asset("/Engine/EngineResources/WhiteSquareTexture"))
    ntex = node(m, unreal.MaterialExpressionTextureSampleParameter2D, -1700, 300, parameter_name="NormalTex", sampler_type=T.SAMPLERTYPE_NORMAL,
                texture=unreal.load_asset("/Engine/EngineMaterials/DefaultNormal"))
    mtex = node(m, unreal.MaterialExpressionTextureSampleParameter2D, -1700, 700, parameter_name="MetalSmoothTex", sampler_type=T.SAMPLERTYPE_LINEAR_COLOR,
                texture=unreal.load_asset("/Engine/EngineResources/Black"))
    pre = node(m, unreal.MaterialExpressionPreSkinnedPosition, -1700, -700)
    vi = node(m, unreal.MaterialExpressionVertexInterpolator, -1500, -700); link(pre, "", vi, "VS")
    ap = node(m, unreal.MaterialExpressionAppendVector, -1450, -380); link(btex, "RGB", ap, "A"); link(btex, "A", ap, "B")
    cu = node(m, unreal.MaterialExpressionCustom, -1000, -500, code=CODE, output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT4, description="MonRecolor")
    ins = []
    for n in ("Base", "P", "Dark", "Mid", "Light", "Recolor", "Kind", "Scale", "Strength"):
        ci = unreal.CustomInput(); ci.set_editor_property("input_name", n); ins.append(ci)
    cu.set_editor_property("inputs", ins)
    link(ap, "", cu, "Base"); link(vi, "", cu, "P")
    y = -900
    for n, d in (("Dark", (0, 0, 0)), ("Mid", (0.5, 0.5, 0.5)), ("Light", (1, 1, 1))):
        p = node(m, unreal.MaterialExpressionVectorParameter, -1300, y, parameter_name=n, default_value=unreal.LinearColor(d[0], d[1], d[2], 1)); link(p, "", cu, n); y += 140
    params = {}
    for n, d in (("Recolor", 0.0), ("Kind", 0.0), ("Scale", 6.0), ("Strength", 0.7), ("Roughness", 0.6), ("Metallic", 0.0), ("UseMetalSmooth", 0.0), ("FlipNormalG", 0.0)):
        params[n] = node(m, unreal.MaterialExpressionScalarParameter, -1300, y, parameter_name=n, default_value=d); y += 90
    for n in ("Recolor", "Kind", "Scale", "Strength"): link(params[n], "", cu, n)
    def mask(src, k, x, yy):
        e = node(m, unreal.MaterialExpressionComponentMask, x, yy)
        for c, on in zip("rgba", [i == k for i in range(4)] if isinstance(k, int) else [c in k for c in "rgba"]): e.set_editor_property(c, on)
        link(src, "", e, ""); return e
    col = mask(cu, "rgb", -700, -500); edge = mask(cu, 3, -700, -380)
    glow = node(m, unreal.MaterialExpressionVectorParameter, -700, -260, parameter_name="EdgeGlow", default_value=unreal.LinearColor(0, 0, 0, 1))
    em = node(m, unreal.MaterialExpressionMultiply, -450, -320); link(edge, "", em, "A"); link(glow, "", em, "B")
    MEL.connect_material_property(col, "", MP.MP_BASE_COLOR); MEL.connect_material_property(em, "", MP.MP_EMISSIVE_COLOR)
    # normal: the green flipped where the map is Unity's (OpenGL)
    sgn = node(m, unreal.MaterialExpressionLinearInterpolate, -1300, 450, const_a=1.0, const_b=-1.0); link(params["FlipNormalG"], "", sgn, "Alpha")
    gv = node(m, unreal.MaterialExpressionAppendVector, -1150, 420); link(node(m, unreal.MaterialExpressionConstant, -1300, 380, r=1.0), "", gv, "A"); link(sgn, "", gv, "B")
    g3 = node(m, unreal.MaterialExpressionAppendVector, -1000, 420); link(gv, "", g3, "A"); link(node(m, unreal.MaterialExpressionConstant, -1150, 520, r=1.0), "", g3, "B")
    nm = node(m, unreal.MaterialExpressionMultiply, -850, 350); link(ntex, "RGB", nm, "A"); link(g3, "", nm, "B")
    MEL.connect_material_property(nm, "", MP.MP_NORMAL)
    # roughness / metallic: the texture's (Unity: metallic in R, smoothness in A) or constants; a scheme's in place of them
    sm1 = node(m, unreal.MaterialExpressionOneMinus, -1450, 760); link(mtex, "A", sm1, "")
    r0 = node(m, unreal.MaterialExpressionLinearInterpolate, -1150, 700, const_a=0.65); link(sm1, "", r0, "B"); link(params["UseMetalSmooth"], "", r0, "Alpha")
    m0 = node(m, unreal.MaterialExpressionLinearInterpolate, -1150, 820, const_a=0.0); link(mtex, "R", m0, "B"); link(params["UseMetalSmooth"], "", m0, "Alpha")
    r1 = node(m, unreal.MaterialExpressionLinearInterpolate, -700, 700); link(r0, "", r1, "A"); link(params["Roughness"], "", r1, "B"); link(params["Recolor"], "", r1, "Alpha")
    m1 = node(m, unreal.MaterialExpressionLinearInterpolate, -700, 820); link(m0, "", m1, "A"); link(params["Metallic"], "", m1, "B"); link(params["Recolor"], "", m1, "Alpha")
    MEL.connect_material_property(r1, "", MP.MP_ROUGHNESS); MEL.connect_material_property(m1, "", MP.MP_METALLIC)
    if masked: MEL.connect_material_property(btex, "A", MP.MP_OPACITY_MASK)
    MEL.set_base_material_usage(m, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH)
    unreal.log("MONGAL final compile of " + name + " (a 'Failed to compile' after this line is real)")
    MEL.recompile_material(m); eal.save_loaded_asset(m, only_if_is_dirty=False)
    print("MONGAL material", name, "pixel instructions", MEL.get_statistics(m).num_pixel_shader_instructions)
    return m


# ================================================================================================ textures of a material
def tex_roles(mi):
    """(base colour, normal, opacity) textures of a material, from its textures' names and settings"""
    texs = []; x = mi
    while isinstance(x, unreal.MaterialInstance):                   # (an instance's own textures first, then its parents')
        texs += [p.parameter_value for p in x.get_editor_property("texture_parameter_values") if isinstance(p.parameter_value, unreal.Texture2D)]
        x = x.get_editor_property("parent")
    if isinstance(x, unreal.Material): texs += [t for t in MEL.get_used_textures(x) if isinstance(t, unreal.Texture2D) and t not in texs]
    def nm(t): return t.get_name().lower()
    normal = [t for t in texs if t.compression_settings == unreal.TextureCompressionSettings.TC_NORMALMAP or re.search(r"normal|_n$|_nrm|_nor$", nm(t))]
    rest = [t for t in texs if t not in normal]
    opac = [t for t in rest if re.search(r"opacity|alpha|_mask|transp", nm(t))]
    base = [t for t in rest if t not in opac and re.search(r"albedo|basecolor|base_color|diffuse|_d$|_bc$|color|_alb", nm(t))]
    base = base or [t for t in rest if t not in opac and t.srgb and not re.search(r"rough|metal|_ao|occlusion|orm|mask|spec|height|emiss", nm(t))]
    return (base[0] if base else None), (normal[0] if normal else None), (opac[0] if opac else None), texs


def blend_of(mi):
    x = mi
    while isinstance(x, unreal.MaterialInstance): x = x.get_editor_property("parent")
    return x.get_editor_property("blend_mode") if x else unreal.BlendMode.BLEND_OPAQUE


# ================================================================================================ modes
if MODE == "materials":
    build_master("M_MON_Variant", False); build_master("M_MON_VariantMasked", True)

elif MODE == "unity":
    UPACKS = {"Creatures Insects Pack": ("Creatures_Insects_Pack", r"Creature_Insect_(\d\d)_Mesh\.FBX$", "Creature Insect"),
              "Humanoids Monsters Pack": ("Humanoids_Monsters_Pack", r"Monster_(\d\d)_Mesh\.FBX$", "Monster")}
    master = unreal.load_asset(MDIR + "/M_MON_Variant"); assert master, "run the materials mode first"
    D = load_data()
    def imp(path, dest, name, opts=None):
        t = unreal.AssetImportTask(); t.filename = path; t.destination_path = dest; t.destination_name = name
        t.automated = True; t.replace_existing = True; t.save = True
        if opts: t.options = opts
        at.import_asset_tasks([t]); return unreal.load_asset(dest + "/" + name)
    for pack, (folder, pat, label) in UPACKS.items():
        root = os.path.join(SA, "fab_unity", folder)
        fbx = []
        for d, _, fs in os.walk(root):
            for f in fs:
                m = re.search(pat, f)
                if m and "Animations" not in d: fbx.append((m.group(1), os.path.join(d, f)))
        for num, path in sorted(fbx):
            G = f"/Game/{folder}"
            o = unreal.FbxImportUI()
            o.set_editor_property("import_mesh", True); o.set_editor_property("import_as_skeletal", True); o.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
            o.set_editor_property("import_materials", False); o.set_editor_property("import_textures", False); o.set_editor_property("import_animations", False)
            o.set_editor_property("create_physics_asset", False)
            sk = imp(path, G + "/Mesh", f"SK_{label.replace(' ', '_')}_{num}", o)
            assert sk, path
            # textures beside the mesh: <..>/Textures/*_Albedo / _Normals / _Metallic
            tdir = os.path.join(os.path.dirname(os.path.dirname(path)), "Textures"); tx = {}
            for f in sorted(os.listdir(tdir)):
                for role, key in (("base", "_Albedo"), ("normal", "_Normals"), ("metal", "_Metallic")):
                    if key.lower() in f.lower():
                        t = imp(os.path.join(tdir, f), G + "/Textures", "T_" + os.path.splitext(f)[0])
                        if role == "normal":
                            t.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP); t.set_editor_property("srgb", False)
                            t.set_editor_property("flip_green_channel", True)                     # (Unity's normal maps are OpenGL's)
                        if role == "metal": t.set_editor_property("srgb", False)
                        eal.save_loaded_asset(t, only_if_is_dirty=False); tx[role] = t
            mp = f"{G}/Materials/MI_{label.replace(' ', '_')}_{num}"
            if eal.does_asset_exist(mp): eal.delete_asset(mp)
            mi = at.create_asset(mp.rsplit("/", 1)[1], G + "/Materials", unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
            MEL.set_material_instance_parent(mi, master)
            MEL.set_material_instance_texture_parameter_value(mi, "BaseTex", tx["base"]); MEL.set_material_instance_texture_parameter_value(mi, "NormalTex", tx["normal"])
            if "metal" in tx: MEL.set_material_instance_texture_parameter_value(mi, "MetalSmoothTex", tx["metal"]); MEL.set_material_instance_scalar_parameter_value(mi, "UseMetalSmooth", 1.0)
            MEL.update_material_instance(mi); eal.save_loaded_asset(mi, only_if_is_dirty=False)
            mats = []
            for s in sk.materials:
                s.set_editor_property("material_interface", mi); mats.append(s)
            sk.modify(); sk.set_editor_property("materials", mats); eal.save_loaded_asset(sk, only_if_is_dirty=False)
            b = sk.get_bounds()
            print(f"MONGAL imported {pack} {label} {num}: {sk.get_path_name()} height {b.box_extent.z * 2:.0f} cm, textures {sorted(tx)}")
        print("MONGAL", pack, len(fbx), "models")
    print("MONGAL unity done: assign the imported meshes to the cover-only entries of monsters.json by their looks")

elif MODE == "stage":
    if not ues.get_editor_world().get_path_name().startswith(SCRATCH + "."): les.load_level(SCRATCH)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(SCRATCH + "."), w.get_path_name()
    for a in eas.get_all_level_actors():
        if TAG in a.tags: eas.destroy_actor(a)
    unreal.SystemLibrary.execute_console_command(w, "r.TextureStreaming 0")
    def spawn(cls, loc, rot=None, label=None):
        a = eas.spawn_actor_from_class(cls, loc, rot or unreal.Rotator()); a.tags = [TAG]
        if label: a.set_actor_label(label)
        return a
    D = load_data(); n = 0
    fl = spawn(unreal.StaticMeshActor, ORIGIN + V(SPACING * 60, 0, 0), label="MON_Floor"); fl.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Plane"))
    fl.set_actor_scale3d(V(SPACING * 130 / 100.0, 400, 1))
    key = spawn(unreal.DirectionalLight, ORIGIN + V(0, 0, 1000), unreal.Rotator(roll=0, pitch=-40, yaw=-120), "MON_Key"); key.light_component.set_intensity(6.0)
    fill = spawn(unreal.DirectionalLight, ORIGIN + V(0, 0, 1000), unreal.Rotator(roll=0, pitch=-20, yaw=-40), "MON_Fill"); fill.light_component.set_intensity(2.0); fill.light_component.set_cast_shadows(False)
    sky = spawn(unreal.SkyLight, ORIGIN + V(0, 0, 500), label="MON_Sky"); sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    sky.light_component.set_editor_property("cubemap", unreal.load_asset("/Engine/EngineResources/GrayLightTextureCube")); sky.light_component.set_intensity(1.5)
    for e in D["monsters"]:
        if not e["meshes"]: continue
        at_ = ORIGIN + V(SPACING * e["rank"], 0, 0)
        for p in e["meshes"]:
            m = unreal.load_asset(p); assert m, p
            a = spawn(unreal.SkeletalMeshActor, at_, label=f"MON_{e['rank']:03d}"); a.skeletal_mesh_component.set_skinned_asset_and_update(m)
            a.skeletal_mesh_component.set_editor_property("forced_lod_model", 1)
        n += 1
    print("MONGAL staged", n, "monsters")

elif MODE == "warm":
    masters = (unreal.load_asset(MDIR + "/M_MON_Variant"), unreal.load_asset(MDIR + "/M_MON_VariantMasked")); n = 0
    for a in eas.get_all_level_actors():
        if TAG not in a.tags or not isinstance(a, unreal.SkeletalMeshActor): continue
        smc = a.skeletal_mesh_component
        for i in range(smc.get_num_materials()):
            mi = smc.get_material(i)
            if isinstance(mi, unreal.MaterialInstanceDynamic): continue
            masked = blend_of(mi) in (unreal.BlendMode.BLEND_MASKED, unreal.BlendMode.BLEND_TRANSLUCENT)
            dm = smc.create_dynamic_material_instance(i, masters[1 if masked else 0]); dm.set_scalar_parameter_value("Recolor", 1.0); n += 1
        smc.set_editor_property("forced_lod_model", 1)
    print("MONGAL warm: scheme material on", n, "slots (shoot puts the originals back)")

elif MODE == "shoot":
    OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
    ONLY = set(int(x) for x in sys.argv[3].split(",")) if len(sys.argv) > 3 and sys.argv[3] != "all" else None
    MASKS_ONLY = "masks" in sys.argv[3:]
    w = ues.get_editor_world(); assert w.get_path_name().startswith(SCRATCH + "."), w.get_path_name()
    masters = (unreal.load_asset(MDIR + "/M_MON_Variant"), unreal.load_asset(MDIR + "/M_MON_VariantMasked"))
    groups = {}
    for a in eas.get_all_level_actors():
        if TAG in a.tags and a.get_actor_label().startswith("MON_") and a.get_actor_label()[4:7].isdigit(): groups.setdefault(int(a.get_actor_label()[4:7]), []).append(a)
    MESHES = {e["rank"]: e["meshes"] for e in load_data()["monsters"]}
    made = []
    def spawn(cls, loc, rot=None):
        a = eas.spawn_actor_from_class(cls, loc, rot or unreal.Rotator()); a.tags = [TAG]; made.append(a); return a
    report = {}
    try:
        post = spawn(unreal.StaticMeshActor, ORIGIN); post.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube")); post.set_actor_scale3d(V(0.06, 0.06, 1.8))
        cap = spawn(unreal.SceneCapture2D, ORIGIN); comp = cap.capture_component2d
        rt = unreal.RenderingLibrary.create_render_target2d(w, 640, 800, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
        comp.texture_target = rt; comp.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR; comp.fov_angle = 30.0
        comp.capture_every_frame = False; comp.capture_on_movement = False; comp.always_persist_rendering_state = True
        for rank in sorted(groups):
            if ONLY and rank not in ONLY: continue
            acts = groups[rank]; mn = mx = None
            for p in MESHES[rank]:
                b = unreal.load_asset(p).get_bounds()
                lo = b.origin - b.box_extent; hi = b.origin + b.box_extent
                mn = lo if mn is None else V(min(mn.x, lo.x), min(mn.y, lo.y), min(mn.z, lo.z)); mx = hi if mx is None else V(max(mx.x, hi.x), max(mx.y, hi.y), max(mx.z, hi.z))
            O = ORIGIN + V(SPACING * rank, 0, 0)
            for a in acts: a.set_actor_location(O + V(0, 0, -mn.z), False, False)
            c = V((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, (mx.z - mn.z) / 2); ext = V((mx.x - mn.x) / 2, (mx.y - mn.y) / 2, (mx.z - mn.z) / 2)
            post.set_actor_location(O + V(mn.x - 25.0, c.y, 90.0), False, False)
            # framing: the half width the camera sees (65 degrees round from +X: both the width and the depth count, plus
            # the post) against the 30 degree horizontal field, the half height against the portrait frame's taller one
            yaw = math.radians(65.0); hw = (ext.x + 30.0) * math.sin(yaw) + ext.y * math.cos(yaw)
            d = max(hw / math.tan(math.radians(15.0)), ext.z / math.tan(math.atan(math.tan(math.radians(15.0)) * 800.0 / 640.0))) * 1.12 + ext.y * 0.4
            cam = O + V(c.x + math.cos(yaw) * d, c.y + math.sin(yaw) * d, c.z + d * 0.12)
            cap.set_actor_location(cam, False, False); cap.set_actor_rotation(ML.find_look_at_rotation(cam, O + c), False)
            # the original materials of every slot, and the textures the schemes recolour
            # (from the mesh asset: `warm` left scheme materials on the components)
            orig = [[(i, s.material_interface) for i, s in enumerate(a.skeletal_mesh_component.get_editor_property("skeletal_mesh_asset").materials)] for a in acts]
            info = []
            for looks in ([] if MASKS_ONLY else ["original"] + list(SCHEMES)):
                for a, slots in zip(acts, orig):
                    smc = a.skeletal_mesh_component
                    for i, mi in slots:
                        if looks == "original": smc.set_material(i, mi); continue
                        base, normal, opac, texs = tex_roles(mi)
                        masked = blend_of(mi) in (unreal.BlendMode.BLEND_MASKED, unreal.BlendMode.BLEND_TRANSLUCENT)
                        dm = smc.create_dynamic_material_instance(i, masters[1 if masked else 0])
                        if isinstance(mi, unreal.MaterialInstance) and mi.get_editor_property("parent") in masters:
                            for pn in ("BaseTex", "NormalTex", "MetalSmoothTex"):
                                t = MEL.get_material_instance_texture_parameter_value(mi, pn)
                                if t: dm.set_texture_parameter_value(pn, t)
                            dm.set_scalar_parameter_value("UseMetalSmooth", MEL.get_material_instance_scalar_parameter_value(mi, "UseMetalSmooth"))
                        else:
                            if base: dm.set_texture_parameter_value("BaseTex", base)
                            if normal: dm.set_texture_parameter_value("NormalTex", normal)
                        s = SCHEMES[looks]
                        for k in ("Dark", "Mid", "Light", "EdgeGlow"): dm.set_vector_parameter_value(k, unreal.LinearColor(s[k][0], s[k][1], s[k][2], 1.0))
                        for k in ("Kind", "Scale", "Strength", "Roughness", "Metallic"): dm.set_scalar_parameter_value(k, s[k])
                        dm.set_scalar_parameter_value("Recolor", 1.0)
                        if looks == "infernal": info.append({"slot": i, "material": mi.get_name() if mi else None, "base": base.get_name() if base else None,
                                                             "normal": normal.get_name() if normal else None, "masked": masked})
                for _ in range(8): comp.capture_scene()
                unreal.RenderingLibrary.export_render_target(w, rt, OUT, f"{rank:03d}_{looks}.png")
            for a, slots in zip(acts, orig):
                for i, mi in slots: a.skeletal_mesh_component.set_material(i, mi)
            # the mask: the monster alone, unlit, on black (the doc crops all four pictures to it)
            comp.primitive_render_mode = unreal.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST
            for a in acts: comp.show_only_actor_components(a, False)
            comp.capture_source = unreal.SceneCaptureSource.SCS_BASE_COLOR
            for _ in range(2): comp.capture_scene()
            unreal.RenderingLibrary.export_render_target(w, rt, OUT, f"{rank:03d}_mask.png")
            comp.primitive_render_mode = unreal.SceneCapturePrimitiveRenderMode.PRM_RENDER_SCENE_PRIMITIVES; comp.clear_show_only_components()
            comp.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
            report[rank] = info
            print(f"MONGAL shot {rank}: " + "; ".join(f"{x['material']} base={x['base']} normal={x['normal']}{' masked' if x['masked'] else ''}" for x in info))
    finally:
        for a in made:
            try: eas.destroy_actor(a)
            except Exception: pass
    old = {}
    rp = os.path.join(OUT, "materials.json")
    if os.path.isfile(rp): old = json.load(open(rp))
    old.update({str(k): v for k, v in report.items()}); json.dump(old, open(rp, "w"), indent=1)

elif MODE == "clear":
    w = ues.get_editor_world()
    if w.get_path_name().startswith(SCRATCH + "."):
        for a in eas.get_all_level_actors():
            if TAG in a.tags: eas.destroy_actor(a)
        les.save_current_level()                          # (empty again, as it was; a dirty level would ask before the next map loads)
    unreal.SystemLibrary.execute_console_command(w, "r.TextureStreaming 1")
    print("MONGAL cleared")
cleanup()
