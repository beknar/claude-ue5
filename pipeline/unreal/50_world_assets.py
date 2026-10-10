"""Outdoor world assets: Nanite terrain/rocks/grass, ground texture sets, terrain/rock/grass materials.
Trail centre line (shared with placement): Y = 400 * sin(X / 2500)  (cm)."""
import os, sys, importlib, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mat_lib as L
importlib.reload(L)
mel = L.mel
SRC = r"E:\code\claude-ue5\claude_ue5\SourceArt\terrain"
D = "/Game/Fig4/World"

# ---------- meshes ----------  (arg "mats_only": rebuild materials without re-importing)
MATS_ONLY = "mats_only" in sys.argv
meshes = {}
for f in ([] if MATS_ONLY else  ("SM_Terrain", "SM_Rock_A", "SM_Rock_B", "SM_Rock_C", "SM_GrassClump")):
    t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, f + ".glb"); t.destination_path = D + "/Meshes"
    t.automated = True; t.replace_existing = True; t.save = True
    L.at.import_asset_tasks([t])
    for p in t.imported_object_paths:
        a = unreal.load_asset(p)
        if isinstance(a, unreal.StaticMesh): meshes[f] = a
        elif isinstance(a, unreal.MaterialInterface): pass
if MATS_ONLY:
    meshes = {k: unreal.load_asset(f"{D}/Meshes/{k}/StaticMeshes/{k}") for k in ("SM_Terrain", "SM_Rock_A", "SM_Rock_B", "SM_Rock_C", "SM_GrassClump")}
print("meshes", {k: v.get_path_name() for k, v in meshes.items()})

# ---------- textures ----------
T = {}
for s in ("Grass", "Dirt", "Rock"):
    for suf, kind in (("BC", "color"), ("R", "linear"), ("N", "normal"), ("H", "height16")):
        T[f"{s}_{suf}"] = unreal.load_asset(f"{D}/Textures/T_{s}_{suf}") if MATS_ONLY else L.import_texture(os.path.join(SRC, f"T_{s}_{suf}.png"), D + "/Textures", kind)

_orig_new = importlib.reload(L).new_material
def new_mat(path):
    if L.eal.does_asset_exist(path):
        mt = unreal.load_asset(path); mel.delete_all_material_expressions(mt); return mt
    return _orig_new(path)
L.new_material = new_mat
def C(m, v, x, y): return L.expr(m, unreal.MaterialExpressionConstant, x, y, r=v)
def op(m, cls, a, b, x, y, a_out="", b_out=""):
    e = L.expr(m, cls, x, y)
    if isinstance(a, (int, float)): e.set_editor_property("const_a", a)
    else: L.link(a, a_out, e, "A")
    if isinstance(b, (int, float)): e.set_editor_property("const_b", b)
    else: L.link(b, b_out, e, "B")
    return e
def lerp(m, a, b, t, x, y, t_out=""):
    e = L.expr(m, unreal.MaterialExpressionLinearInterpolate, x, y)
    L.link(a[0], a[1], e, "A"); L.link(b[0], b[1], e, "B"); L.link(t, t_out, e, "Alpha"); return e
def sat(m, a, x, y, out=""):
    e = L.expr(m, unreal.MaterialExpressionSaturate, x, y); L.link(a, out, e, ""); return e
def layer(m, name, tiling, x, y):
    uv = L.expr(m, unreal.MaterialExpressionTextureCoordinate, x - 300, y, u_tiling=tiling, v_tiling=tiling)
    S = unreal.MaterialSamplerType
    return dict(
        bc=L.tex_sample(m, T[f"{name}_BC"], x, y, uv=uv),
        r=L.tex_sample(m, T[f"{name}_R"], x, y + 250, uv=uv, sampler=S.SAMPLERTYPE_MASKS),
        n=L.tex_sample(m, T[f"{name}_N"], x, y + 500, uv=uv, sampler=S.SAMPLERTYPE_NORMAL),
        h=L.tex_sample(m, T[f"{name}_H"], x, y + 750, uv=uv, sampler=S.SAMPLERTYPE_LINEAR_GRAYSCALE))
def blend(m, A, B, mask, x, y):
    """A, B: dicts of (expression, output) pairs"""
    return {k: (lerp(m, A[k], B[k], mask, x, y + 150 * i), "") for i, k in enumerate(("bc", "r", "n", "h"))}
def as_pair(L_):
    return {k: (v, "RGB" if k in ("bc", "n") else "R") for k, v in L_.items()}
def height_mask(m, base_mask, hA, hB, x, y, contrast=6.0):
    """height-aware transition: saturate((mask - 0.5 + (hB - hA) * 0.5) * contrast + 0.5)"""
    d = op(m, unreal.MaterialExpressionSubtract, hB[0], hA[0], x, y, hB[1], hA[1])
    d2 = op(m, unreal.MaterialExpressionMultiply, d, 0.5, x + 120, y)
    s = op(m, unreal.MaterialExpressionAdd, base_mask, d2, x + 240, y)
    s2 = op(m, unreal.MaterialExpressionSubtract, s, 0.5, x + 360, y)
    s3 = op(m, unreal.MaterialExpressionMultiply, s2, contrast, x + 480, y)
    s4 = op(m, unreal.MaterialExpressionAdd, s3, 0.5, x + 600, y)
    return sat(m, s4, x + 720, y)
def finish_attrs(m, P, x, y, disp_mul=None):
    mma = L.expr(m, unreal.MaterialExpressionMakeMaterialAttributes, x, y)
    L.link(P["bc"][0], P["bc"][1], mma, "BaseColor"); L.link(P["r"][0], P["r"][1], mma, "Roughness")
    L.link(P["n"][0], P["n"][1], mma, "Normal"); L.link(P["h"][0], P["h"][1], mma, "Displacement")
    L.link(C(m, 0.4, x - 200, y + 600), "", mma, "Specular")
    mel.connect_material_property(mma, "", unreal.MaterialProperty.MP_MATERIAL_ATTRIBUTES)

# ---------- terrain material ----------
m = L.new_material(D + "/Materials/M_Terrain")
m.set_editor_property("use_material_attributes", True)
m.set_editor_property("enable_tessellation", True)
ds = m.get_editor_property("displacement_scaling"); ds.magnitude = 4.0; ds.center = 0.5
m.set_editor_property("displacement_scaling", ds)
# grass: two scales averaged (breaks visible tiling at distance) and tinted less yellow
G_ = blend(m, as_pair(layer(m, "Grass", 1 / 1.5, -3600, -2600)), as_pair(layer(m, "Grass", 1 / 6.7, -3600, -1600)), C(m, 0.5, -3300, -1700), -3000, -2000)
G_["bc"] = (op(m, unreal.MaterialExpressionMultiply, G_["bc"][0], L.const3(m, (0.80, 0.94, 0.82), -2900, -2300), -2800, -2200), "")
Dl = layer(m, "Dirt", 1 / 2.0, -3000, -600)
R_ = layer(m, "Rock", 1 / 4.0, -3000, 400)
# masks: macro dirt patches (large-scale dirt height) + trail along Y = 400 sin(X / 2500)
uvm = L.expr(m, unreal.MaterialExpressionTextureCoordinate, -3300, 1500, u_tiling=1 / 37.0, v_tiling=1 / 37.0)
macro = L.tex_sample(m, T["Dirt_H"], -3000, 1500, uv=uvm, sampler=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE)
patch = sat(m, op(m, unreal.MaterialExpressionMultiply, op(m, unreal.MaterialExpressionSubtract, macro, 0.62, -2700, 1500, "R"), 3.0, -2550, 1500), -2400, 1500)
wp = L.expr(m, unreal.MaterialExpressionWorldPosition, -3300, 1900)
wx = L.expr(m, unreal.MaterialExpressionComponentMask, -3100, 1900, r=True, g=False, b=False, a=False); L.link(wp, "", wx, "")
wy = L.expr(m, unreal.MaterialExpressionComponentMask, -3100, 2000, r=False, g=True, b=False, a=False); L.link(wp, "", wy, "")
sn = L.expr(m, unreal.MaterialExpressionSine, -2800, 1900, period=6.283185); L.link(op(m, unreal.MaterialExpressionDivide, wx, 2500.0, -2950, 1900), "", sn, "")
cy = op(m, unreal.MaterialExpressionMultiply, sn, 400.0, -2650, 1900)
dy = L.expr(m, unreal.MaterialExpressionAbs, -2350, 1950); L.link(op(m, unreal.MaterialExpressionSubtract, wy, cy, -2500, 1950), "", dy, "")
# wobble the edge with the macro texture: d' = d + (macro - 0.5) * 120 ; trail = saturate((150 - d') / 60)
wob = op(m, unreal.MaterialExpressionMultiply, op(m, unreal.MaterialExpressionSubtract, macro, 0.5, -2700, 2100, "R"), 140.0, -2550, 2100)
dd = op(m, unreal.MaterialExpressionAdd, dy, wob, -2200, 2000)
trail = sat(m, op(m, unreal.MaterialExpressionDivide, op(m, unreal.MaterialExpressionSubtract, 150.0, dd, -2050, 2000), 60.0, -1900, 2000), -1750, 2000)
dmask = L.expr(m, unreal.MaterialExpressionMax, -1600, 1800); L.link(patch, "", dmask, "A"); L.link(trail, "", dmask, "B")
gd_mask = height_mask(m, dmask, G_["h"], (Dl["h"], "R"), -1500, 1600)
GD = blend(m, G_, as_pair(Dl), gd_mask, -600, -1200)
# slope -> rock
vn = L.expr(m, unreal.MaterialExpressionVertexNormalWS, -3300, 2400)
vz = L.expr(m, unreal.MaterialExpressionComponentMask, -3100, 2400, r=False, g=False, b=True, a=False); L.link(vn, "", vz, "")
slope = sat(m, op(m, unreal.MaterialExpressionMultiply, op(m, unreal.MaterialExpressionSubtract, 0.86, vz, -2900, 2400), 7.0, -2750, 2400), -2600, 2400)
rk_mask = height_mask(m, slope, GD["h"], (R_["h"], "R"), -1500, 2400, 4.0)
P = blend(m, GD, as_pair(R_), rk_mask, -200, -400)
# large-scale tonal variation
uvv = L.expr(m, unreal.MaterialExpressionTextureCoordinate, -600, 2800, u_tiling=1 / 61.0, v_tiling=1 / 61.0)
var = L.tex_sample(m, T["Grass_H"], -400, 2800, uv=uvv, sampler=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE)
tone = op(m, unreal.MaterialExpressionAdd, op(m, unreal.MaterialExpressionMultiply, var, 0.35, -150, 2800, "R"), 0.82, 0, 2800)
P["bc"] = (op(m, unreal.MaterialExpressionMultiply, P["bc"][0], tone, 200, -600), "")
finish_attrs(m, P, 500, 0)
L.finish(m)
print("M_Terrain compiled")

# ---------- rock material (moss on up-facing surfaces) ----------
rm = L.new_material(D + "/Materials/M_Rock")
rm.set_editor_property("use_material_attributes", True)
rm.set_editor_property("enable_tessellation", True)
ds = rm.get_editor_property("displacement_scaling"); ds.magnitude = 2.5; ds.center = 0.5
rm.set_editor_property("displacement_scaling", ds)
R2 = layer(rm, "Rock", 1 / 1.2, -2500, -800)
G2 = layer(rm, "Grass", 1 / 0.8, -2500, 300)
vn = L.expr(rm, unreal.MaterialExpressionVertexNormalWS, -2500, 1400)
vz = L.expr(rm, unreal.MaterialExpressionComponentMask, -2300, 1400, r=False, g=False, b=True, a=False); L.link(vn, "", vz, "")
up = sat(rm, op(rm, unreal.MaterialExpressionMultiply, op(rm, unreal.MaterialExpressionSubtract, vz, 0.72, -2100, 1400), 4.0, -1950, 1400), -1800, 1400)
mm = height_mask(rm, up, (R2["h"], "R"), (G2["h"], "R"), -1600, 1400, 3.0)
P = blend(rm, as_pair(R2), as_pair(G2), mm, -600, -400)
finish_attrs(rm, P, 0, 0)
L.finish(rm)

# ---------- grass blade material: two-sided, tip gradient, per-instance tint, wind ----------
gm = L.new_material(D + "/Materials/M_GrassBlade")
gm.set_editor_property("two_sided", True)
uv = L.expr(gm, unreal.MaterialExpressionTextureCoordinate, -1600, 0)
v = L.expr(gm, unreal.MaterialExpressionComponentMask, -1400, 0, r=False, g=True, b=False, a=False); L.link(uv, "", v, "")
base = L.const3(gm, (0.025, 0.045, 0.012), -1400, -300)
tip_a = L.const3(gm, (0.11, 0.15, 0.035), -1400, -200)
tip_b = L.const3(gm, (0.20, 0.18, 0.08), -1400, -100)
pir = L.expr(gm, unreal.MaterialExpressionPerInstanceRandom, -1600, 300)
tip = lerp(gm, (tip_a, ""), (tip_b, ""), op(gm, unreal.MaterialExpressionMultiply, pir, 0.7, -1300, 300), -1100, -200)
grad = L.expr(gm, unreal.MaterialExpressionPower, -1200, 0); L.link(v, "", grad, "Base"); grad.set_editor_property("const_exponent", 0.8)
col = lerp(gm, (base, ""), (tip, ""), grad, -900, -250)
mel.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(C(gm, 0.55, -600, 0), "", unreal.MaterialProperty.MP_ROUGHNESS)
mel.connect_material_property(C(gm, 0.35, -600, 80), "", unreal.MaterialProperty.MP_SPECULAR)
# wind: offset = (sin(t*1.7 + phase) * 6 + 2) * v^2 along (1, 0.4, 0), phase from world position
tm = L.expr(gm, unreal.MaterialExpressionTime, -1600, 600)
ap = L.expr(gm, unreal.MaterialExpressionObjectPositionWS, -1600, 700)
ax = L.expr(gm, unreal.MaterialExpressionComponentMask, -1400, 700, r=True, g=False, b=False, a=False); L.link(ap, "", ax, "")
ay = L.expr(gm, unreal.MaterialExpressionComponentMask, -1400, 780, r=False, g=True, b=False, a=False); L.link(ap, "", ay, "")
ph = op(gm, unreal.MaterialExpressionMultiply, op(gm, unreal.MaterialExpressionAdd, ax, ay, -1250, 740), 0.004, -1100, 740)
arg = op(gm, unreal.MaterialExpressionAdd, op(gm, unreal.MaterialExpressionMultiply, tm, 1.7, -1250, 600), ph, -950, 650)
sw = L.expr(gm, unreal.MaterialExpressionSine, -800, 650, period=6.283185); L.link(arg, "", sw, "")
amp = op(gm, unreal.MaterialExpressionAdd, op(gm, unreal.MaterialExpressionMultiply, sw, 5.0, -650, 650), 2.0, -500, 650)
v2 = op(gm, unreal.MaterialExpressionMultiply, v, v, -650, 800)
mag = op(gm, unreal.MaterialExpressionMultiply, amp, v2, -350, 700)
wdir = L.const3(gm, (1.0, 0.4, 0.0), -350, 850)
wpo = op(gm, unreal.MaterialExpressionMultiply, mag, wdir, -150, 750)
mel.connect_material_property(wpo, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
L.finish(gm)

# ---------- Nanite + collision + material assignment ----------
def setup(sm, mat, collide, wpo_dist=None):
    ns = sm.get_editor_property("nanite_settings"); ns.set_editor_property("enabled", True)
    sm.set_editor_property("nanite_settings", ns)
    sm.set_material(0, mat)
    bs = sm.get_editor_property("body_setup")
    if bs:
        bs.set_editor_property("collision_trace_flag",
                               unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE if collide else unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
    L.eal.save_loaded_asset(sm)
if not MATS_ONLY:     # materials are edited in place, mesh assignments stay valid
    setup(meshes["SM_Terrain"], m, True)
    for k in ("SM_Rock_A", "SM_Rock_B", "SM_Rock_C"): setup(meshes[k], rm, True)
    setup(meshes["SM_GrassClump"], gm, False)
print("WORLD assets done")
