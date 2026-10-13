"""random_dungeoncombat_level: blood and wounds. Builds the materials in /Game/RandomDungeon/Combat/Materials (in place when
they exist) and sets the generator's gore properties. Run with random_dungeoncombat_level open, after the C++ build.

  M_RDC_BloodDrop    the drops of a splash (opaque, wet, a little emissive so they read in the dark); one instanced
                     sphere mesh for all of them (URDBloodComponent stretches each along its path)
  M_RDC_BloodSpray   the spray of a splash: camera-facing sprites with the RealisticBlood splatter masks; per-instance
                     custom data 0 = fade, 1 = which mask
  M_RDC_Wounds       the overlay material of a wounded monster. Its wounds are spheres in the mesh's *reference pose*
                     (vector parameters Wound0..Wound9: centre xyz, radius in a), compared with the pre-skinned vertex
                     position, so a wound stays on the skin whatever the pose. Each has a ragged edge (value noise), a
                     stain, a ring of torn flesh, a dark open middle and blood running down from it (-Z of the
                     reference pose); Bleed (0..1, set from the monster's lost hit points) lengthens the runs and
                     smears more and more of the body (patches placed by Seed, different for every monster). Every
                     monster gets its own dynamic instance with its first wound: nothing is changed in the pack's
                     materials, and no other monster shows it.
  M_RDC_BloodDecal   where a drop lands and under a body: a deferred decal (dark, wet) cut out by one of the
                     RealisticBlood pack's masks, with instances MI_RDC_BloodSplat_* / MI_RDC_BloodPool_* (one per
                     mask). The pack's own decal material is not used: it does not compile with Substrate, which
                     this project has on (the engine then draws the default material: pale squares on the floor).

Args: none. Prints "RDCGORE ok" with the shader instruction counts (0 = a material that failed to compile)."""
import gc, unreal

DIR = "/Game/RandomDungeon/Combat/Materials"
TEX = "/Game/HallowedDepths/RealisticBlood/_Commons/Textures/Decals/"
mel = unreal.MaterialEditingLibrary; eal = unreal.EditorAssetLibrary
MP = unreal.MaterialProperty


def material(name):
    path = DIR + "/" + name
    if eal.does_asset_exist(path):
        m = unreal.load_asset(path); mel.delete_all_material_expressions(m)
    else:
        m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, DIR, unreal.Material, unreal.MaterialFactoryNew())
    return m


def node(m, cls, x, y, **props):
    e = mel.create_material_expression(m, cls, x, y)
    for k, v in props.items(): e.set_editor_property(k, v)
    return e


def const(m, v, x, y):
    if isinstance(v, (int, float)): return node(m, unreal.MaterialExpressionConstant, x, y, r=float(v))
    return node(m, unreal.MaterialExpressionConstant3Vector, x, y, constant=unreal.LinearColor(v[0], v[1], v[2], 1.0))


def link(a, out, b, inp):
    assert mel.connect_material_expressions(a, out, b, inp), ("connect", a.get_name(), out, b.get_name(), inp)


def finish(m, usages):
    for u in usages: mel.set_base_material_usage(m, u)
    unreal.log("RDCGORE final compile of " + m.get_name() + " (a 'Failed to compile' after this line is real; earlier ones are of the half-built graph)")
    mel.recompile_material(m)
    eal.save_loaded_asset(m, only_if_is_dirty=False)
    return mel.get_statistics(m).num_pixel_shader_instructions


# ---------------------------------------------------------------------------------------------- drops
m = material("M_RDC_BloodDrop")
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
col = node(m, unreal.MaterialExpressionVectorParameter, -500, 0, parameter_name="Color", default_value=unreal.LinearColor(0.11, 0.002, 0.004, 1.0))
glow = node(m, unreal.MaterialExpressionScalarParameter, -500, 220, parameter_name="Glow", default_value=0.22)
em = node(m, unreal.MaterialExpressionMultiply, -250, 160); link(col, "", em, "A"); link(glow, "", em, "B")
mel.connect_material_property(col, "", MP.MP_BASE_COLOR); mel.connect_material_property(em, "", MP.MP_EMISSIVE_COLOR)
mel.connect_material_property(const(m, 0.12, -250, 320), "", MP.MP_ROUGHNESS); mel.connect_material_property(const(m, 0.7, -250, 400), "", MP.MP_SPECULAR)
n_drop = finish(m, [unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES])
drop_mat = m

# ---------------------------------------------------------------------------------------------- spray
m = material("M_RDC_BloodSpray")
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
m.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_VOLUMETRIC_NON_DIRECTIONAL)
m.set_editor_property("two_sided", True)
masks = []
for i, t in enumerate(("T_BloodSplatter_01", "T_BloodSplotch_02")):
    s = node(m, unreal.MaterialExpressionTextureSample, -900, i * 260, texture=unreal.load_asset(TEX + t), sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_ALPHA)
    masks.append(s)
fade = node(m, unreal.MaterialExpressionPerInstanceCustomData, -900, 560, data_index=0, const_default_value=1.0)
which = node(m, unreal.MaterialExpressionPerInstanceCustomData, -900, 680, data_index=1, const_default_value=0.0)
rnd = node(m, unreal.MaterialExpressionRound, -700, 680); link(which, "", rnd, "")
mask = node(m, unreal.MaterialExpressionLinearInterpolate, -500, 200); link(masks[0], "R", mask, "A"); link(masks[1], "R", mask, "B"); link(rnd, "", mask, "Alpha")
# (the sprite's corners are never opaque, whatever the mask)
uv = node(m, unreal.MaterialExpressionTextureCoordinate, -900, 820)
c2 = node(m, unreal.MaterialExpressionConstant2Vector, -900, 980, r=0.5, g=0.5)
rad = node(m, unreal.MaterialExpressionDistance, -700, 900); link(uv, "", rad, "A"); link(c2, "", rad, "B")
rim = node(m, unreal.MaterialExpressionSmoothStep, -500, 900)
link(const(m, 0.36, -700, 1000), "", rim, "Min"); link(const(m, 0.5, -700, 1060), "", rim, "Max"); link(rad, "", rim, "Value")
edge = node(m, unreal.MaterialExpressionOneMinus, -350, 900); link(rim, "", edge, "")
op = node(m, unreal.MaterialExpressionMultiply, -300, 300); link(mask, "", op, "A"); link(fade, "", op, "B")
op2 = node(m, unreal.MaterialExpressionMultiply, -150, 360); link(op, "", op2, "A"); link(edge, "", op2, "B")
dens = node(m, unreal.MaterialExpressionScalarParameter, -300, 500, parameter_name="Density", default_value=1.6)
op3 = node(m, unreal.MaterialExpressionMultiply, 0, 420); link(op2, "", op3, "A"); link(dens, "", op3, "B")
sat = node(m, unreal.MaterialExpressionSaturate, 150, 420); link(op3, "", sat, "")
col = node(m, unreal.MaterialExpressionVectorParameter, -300, -100, parameter_name="Color", default_value=unreal.LinearColor(0.12, 0.002, 0.004, 1.0))
glow = node(m, unreal.MaterialExpressionScalarParameter, -300, 80, parameter_name="Glow", default_value=0.3)
em = node(m, unreal.MaterialExpressionMultiply, -100, 20); link(col, "", em, "A"); link(glow, "", em, "B")
mel.connect_material_property(col, "", MP.MP_BASE_COLOR); mel.connect_material_property(em, "", MP.MP_EMISSIVE_COLOR); mel.connect_material_property(sat, "", MP.MP_OPACITY)
n_spray = finish(m, [unreal.MaterialUsage.MATUSAGE_INSTANCED_STATIC_MESHES])
spray_mat = m

# ---------------------------------------------------------------------------------------------- wounds
WOUNDS = 10
CODE = """
struct RDW
{
    float h(float3 v) { return frac(sin(dot(v, float3(127.1, 311.7, 74.7))) * 43758.5453); }
    float n(float3 p)
    {
        float3 i = floor(p); float3 f = frac(p); f = f * f * (3.0 - 2.0 * f);
        return lerp(lerp(lerp(h(i), h(i + float3(1, 0, 0)), f.x), lerp(h(i + float3(0, 1, 0)), h(i + float3(1, 1, 0)), f.x), f.y),
                    lerp(lerp(h(i + float3(0, 0, 1)), h(i + float3(1, 0, 1)), f.x), lerp(h(i + float3(0, 1, 1)), h(i + float3(1, 1, 1)), f.x), f.y), f.z);
    }
    // x: the stain around the wound, y: its dark open middle, z: blood running down from it, w: the torn flesh between
    void w(float3 P, float4 W, float n1, float n2, float drip, inout float4 acc)
    {
        float r = max(W.w, 0.001);
        float3 d = P - W.xyz;
        float dd = length(d) / r + (n1 - 0.5) * 0.8;
        float m = 1.0 - smoothstep(0.7, 1.05, dd);
        float c = 1.0 - smoothstep(0.16, 0.36, dd);
        float fl = (1.0 - smoothstep(0.42, 0.66, dd)) * (1.0 - c);
        float dx = length(d.xy) / r + (n2 - 0.5) * 0.4;
        float dz = -d.z / r;
        float s = (1.0 - smoothstep(0.1, 0.5, dx)) * smoothstep(0.0, 0.5, dz) * (1.0 - smoothstep(drip * 0.45, drip, dz));
        acc = max(acc, float4(m, c, s, fl) * step(0.01, W.w));
    }
};
RDW F;
float n1 = F.n(P * 0.3) * 0.65 + F.n(P * 0.85) * 0.35;
float n2 = F.n(P * float3(0.45, 0.45, 0.05) + 17.0);
float drip = 0.8 + 3.6 * Bleed;
float4 acc = float4(0, 0, 0, 0);
%s
// the worse off it is, the more of it is smeared with blood (patches of its own: Seed)
float n3 = F.n(P * 0.055 + Seed) * 0.7 + F.n(P * 0.21 + Seed) * 0.3;
float th = lerp(0.9, 0.52, Bleed);
float smear = smoothstep(th, th + 0.07, n3) * step(0.03, Bleed) * 0.8;
acc.x = max(acc.x, smear);
return acc;
""" % "\n".join("F.w(P, W%d, n1, n2, drip, acc);" % i for i in range(WOUNDS))
m = material("M_RDC_Wounds")
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
m.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
pre = node(m, unreal.MaterialExpressionPreSkinnedPosition, -1500, 0)
vi = node(m, unreal.MaterialExpressionVertexInterpolator, -1300, 0); link(pre, "", vi, "VS")
cu = node(m, unreal.MaterialExpressionCustom, -800, 0, code=CODE, output_type=unreal.CustomMaterialOutputType.CMOT_FLOAT4, description="RDWounds")
ins = []
for nme in ["P", "Bleed", "Seed"] + ["W%d" % i for i in range(WOUNDS)]:
    ci = unreal.CustomInput(); ci.set_editor_property("input_name", nme); ins.append(ci)
cu.set_editor_property("inputs", ins)
link(vi, "", cu, "P")
bleed = node(m, unreal.MaterialExpressionScalarParameter, -1100, 120, parameter_name="Bleed", default_value=0.0); link(bleed, "", cu, "Bleed")
seed = node(m, unreal.MaterialExpressionVectorParameter, -1100, -140, parameter_name="Seed", default_value=unreal.LinearColor(0.0, 0.0, 0.0, 0.0)); link(seed, "", cu, "Seed")
for i in range(WOUNDS):
    p = node(m, unreal.MaterialExpressionVectorParameter, -1100, 240 + i * 200, parameter_name="Wound%d" % i, default_value=unreal.LinearColor(0.0, 0.0, 0.0, 0.0))
    ap = node(m, unreal.MaterialExpressionAppendVector, -950, 240 + i * 200); link(p, "", ap, "A"); link(p, "A", ap, "B")
    link(ap, "", cu, "W%d" % i)
def channel(k, y):
    e = mel.create_material_expression(m, unreal.MaterialExpressionComponentMask, -500, y)
    for c, on in zip("rgba", (k == 0, k == 1, k == 2, k == 3)): e.set_editor_property(c, on)
    link(cu, "", e, ""); return e
mk, core, run, flesh = channel(0, -80), channel(1, 20), channel(2, 120), channel(3, 220)
blood = node(m, unreal.MaterialExpressionVectorParameter, -500, -720, parameter_name="Blood", default_value=unreal.LinearColor(0.085, 0.002, 0.004, 1.0))
torn = node(m, unreal.MaterialExpressionVectorParameter, -500, -520, parameter_name="Flesh", default_value=unreal.LinearColor(0.28, 0.02, 0.018, 1.0))
deep = node(m, unreal.MaterialExpressionVectorParameter, -500, -320, parameter_name="Deep", default_value=unreal.LinearColor(0.012, 0.0, 0.001, 1.0))
c1 = node(m, unreal.MaterialExpressionLinearInterpolate, -250, -600); link(blood, "", c1, "A"); link(torn, "", c1, "B"); link(flesh, "", c1, "Alpha")
colr = node(m, unreal.MaterialExpressionLinearInterpolate, -100, -420); link(c1, "", colr, "A"); link(deep, "", colr, "B"); link(core, "", colr, "Alpha")
glow = node(m, unreal.MaterialExpressionScalarParameter, -100, -220, parameter_name="Glow", default_value=0.06)
em = node(m, unreal.MaterialExpressionMultiply, 60, -280); link(colr, "", em, "A"); link(glow, "", em, "B")
a1 = node(m, unreal.MaterialExpressionMultiply, -300, 0); link(mk, "", a1, "A"); link(const(m, 0.97, -500, 340), "", a1, "B")
a2 = node(m, unreal.MaterialExpressionMultiply, -300, 120); link(run, "", a2, "A"); link(const(m, 0.88, -500, 420), "", a2, "B")
amax = node(m, unreal.MaterialExpressionMax, -120, 60); link(a1, "", amax, "A"); link(a2, "", amax, "B")
rough = node(m, unreal.MaterialExpressionLinearInterpolate, -200, 300); link(const(m, 0.18, -400, 520), "", rough, "A"); link(const(m, 0.5, -400, 580), "", rough, "B"); link(core, "", rough, "Alpha")
mel.connect_material_property(colr, "", MP.MP_BASE_COLOR); mel.connect_material_property(em, "", MP.MP_EMISSIVE_COLOR)
mel.connect_material_property(amax, "", MP.MP_OPACITY); mel.connect_material_property(rough, "", MP.MP_ROUGHNESS); mel.connect_material_property(const(m, 0.6, -200, 660), "", MP.MP_SPECULAR)
n_wound = finish(m, [unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH])
wound_mat = m

# ---------------------------------------------------------------------------------------------- decals
m = material("M_RDC_BloodDecal")
m.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)
# (with Substrate a decal has to say how it blends: grey transmittance = plain alpha)
m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT_GREY_TRANSMITTANCE if hasattr(unreal.BlendMode, "BLEND_TRANSLUCENT_GREY_TRANSMITTANCE") else unreal.BlendMode.BLEND_TRANSLUCENT)
try: m.set_editor_property("material_decal_response", unreal.MaterialDecalResponse.MDR_COLOR_NORMAL_ROUGHNESS)
except Exception as e: print("decal response:", str(e)[:80])
msk = node(m, unreal.MaterialExpressionTextureSampleParameter2D, -1000, 0, parameter_name="Mask", texture=unreal.load_asset(TEX + "T_BloodSplotch_01"), sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_ALPHA)
nrm = node(m, unreal.MaterialExpressionTextureSampleParameter2D, -1000, 300, parameter_name="Normal", texture=unreal.load_asset(TEX + "T_BloodSplotch_N_01"), sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
cut = node(m, unreal.MaterialExpressionScalarParameter, -1000, 600, parameter_name="Cut", default_value=0.12)
gain = node(m, unreal.MaterialExpressionScalarParameter, -1000, 700, parameter_name="Gain", default_value=5.0)
sub = node(m, unreal.MaterialExpressionSubtract, -700, 80); link(msk, "R", sub, "A"); link(cut, "", sub, "B")
mul = node(m, unreal.MaterialExpressionMultiply, -550, 80); link(sub, "", mul, "A"); link(gain, "", mul, "B")
sat = node(m, unreal.MaterialExpressionSaturate, -400, 80); link(mul, "", sat, "")
life = node(m, unreal.MaterialExpressionDecalLifetimeOpacity, -550, 220)
alpha = node(m, unreal.MaterialExpressionScalarParameter, -550, 320, parameter_name="Alpha", default_value=0.94)
o1 = node(m, unreal.MaterialExpressionMultiply, -250, 120); link(sat, "", o1, "A"); link(life, "", o1, "B")
o2 = node(m, unreal.MaterialExpressionMultiply, -100, 160); link(o1, "", o2, "A"); link(alpha, "", o2, "B")
thin = node(m, unreal.MaterialExpressionVectorParameter, -700, -420, parameter_name="Thin", default_value=unreal.LinearColor(0.13, 0.003, 0.005, 1.0))
thick = node(m, unreal.MaterialExpressionVectorParameter, -700, -220, parameter_name="Thick", default_value=unreal.LinearColor(0.035, 0.0, 0.002, 1.0))
colr = node(m, unreal.MaterialExpressionLinearInterpolate, -400, -300); link(thin, "", colr, "A"); link(thick, "", colr, "B"); link(msk, "R", colr, "Alpha")
flat = node(m, unreal.MaterialExpressionConstant3Vector, -700, 420, constant=unreal.LinearColor(0.0, 0.0, 1.0, 1.0))
nl2 = node(m, unreal.MaterialExpressionLinearInterpolate, -400, 380); link(flat, "", nl2, "A"); link(nrm, "RGB", nl2, "B"); link(const(m, 0.6, -700, 520), "", nl2, "Alpha")
mel.connect_material_property(colr, "", MP.MP_BASE_COLOR); mel.connect_material_property(o2, "", MP.MP_OPACITY); mel.connect_material_property(nl2, "", MP.MP_NORMAL)
mel.connect_material_property(const(m, 0.1, -250, 420), "", MP.MP_ROUGHNESS); mel.connect_material_property(const(m, 0.6, -250, 500), "", MP.MP_SPECULAR)
n_decal = finish(m, [])
decal_mat = m


def instance(name, mask, normal):
    path = DIR + "/" + name
    mi = unreal.load_asset(path) if eal.does_asset_exist(path) else unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, decal_mat)
    mel.set_material_instance_texture_parameter_value(mi, "Mask", unreal.load_asset(TEX + mask))
    mel.set_material_instance_texture_parameter_value(mi, "Normal", unreal.load_asset(TEX + normal))
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi, only_if_is_dirty=False)
    return mi


splats = [instance("MI_RDC_BloodSplat_%02d" % (i + 1), mk, nm) for i, (mk, nm) in enumerate([
    ("T_BloodSplotch_01", "T_BloodSplotch_N_01"), ("T_BloodSplotch_02", "T_BloodSplotch_N_02"), ("T_BloodSplotch_03", "T_BloodSplotch_N_03"), ("T_BloodSplotch_04", "T_BloodSplotch_N_04"),
    ("T_BloodSplotch_05", "T_BloodSplotch_N_05"), ("T_BloodSpots_01", "T_BloodSpots_N_01"), ("T_BloodSplatter_01", "T_BloodSplatter_N_01"), ("T_BloodDirectionalSpots_01", "T_BloodDirectionalSpots_N_01")])]
pools = [instance("MI_RDC_BloodPool_%02d" % (i + 1), mk, nm) for i, (mk, nm) in enumerate([("T_BloodDecal_03", "T_BloodPuddle_N_03"), ("T_BloodSplotch_03", "T_BloodSplotch_N_03")])]

# ---------------------------------------------------------------------------------------------- generator
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
gens = list(unreal.GameplayStatics.get_all_actors_of_class(w, unreal.RDDungeonGenerator))
assert len(gens) == 1 and gens[0].get_editor_property("combat"), "open random_dungeoncombat_level"
gen = gens[0]
gen.modify()
gen.set_editor_property("blood_drop_mesh", unreal.load_asset("/Engine/BasicShapes/Sphere"))
gen.set_editor_property("blood_drop_material", drop_mat)
gen.set_editor_property("blood_spray_mesh", unreal.load_asset("/Engine/BasicShapes/Plane"))
gen.set_editor_property("blood_spray_material", spray_mat)
gen.set_editor_property("blood_decals", splats)
gen.set_editor_property("blood_pools", pools)
gen.set_editor_property("wound_material", wound_mat)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("RDCGORE ok | shader instructions: drop %d, spray %d, wounds %d, decal %d | %d splat decals, %d pool decals" % (n_drop, n_spray, n_wound, n_decal, len(splats), len(pools)))
del gen, gens, w, m, drop_mat, spray_mat, wound_mat, decal_mat, splats, pools
gc.collect()
