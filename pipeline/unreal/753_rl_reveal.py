"""random_level generation indicator (run on random_level after 752, and on random_level_Cine if it exists):
- M_RT_RevealPP (post process, after tonemapping): for each of ARTTownGenerator::RevealSlots freshly generated cells
  (vector params Rect<i> = min x, min y, max x, max y; Info<i> = wave origin x, y, start time) a glowing line on the
  cell border and a scan wave (Speed cm/s) sweeping across the cell from the side nearest the player, a 4 m grid of
  light trailing behind it; ahead of the wave the new cell is drawn as a cyan ghost. Fades out over Duration s.
- M_RT_RevealCurtain (unlit additive, two-sided): the translucent wall ARTCell::ShowCurtain raises on the new cell's
  border (UV.y 0 at the ground, 1 at the top; scalar param StartTime), exposure-independent (EyeAdaptationInverse).
Assigns both to the level's RTTownGenerator and saves the level."""
import unreal
MEL = unreal.MaterialEditingLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary
D = "/Game/RandomLevel/Materials"
SLOTS, DUR, SPEED = 6, 7.0, 11000.0
COL = unreal.LinearColor(0.32, 0.86, 1.0, 1.0)
def fresh(name):
    """rebuilt in place (generators in random_level and random_level_Cine reference these materials)"""
    p = f"{D}/{name}"
    if eal.does_asset_exist(p):
        m = unreal.load_asset(p); MEL.delete_all_material_expressions(m); return m
    return at.create_asset(name, D, unreal.Material, unreal.MaterialFactoryNew())
def node(m, cls, x, y): return MEL.create_material_expression(m, cls, x, y)
def scalar(m, name, v, y):
    n = node(m, unreal.MaterialExpressionScalarParameter, -900, y); n.set_editor_property("parameter_name", name); n.set_editor_property("default_value", v); return n
def vector(m, name, v, y):
    n = node(m, unreal.MaterialExpressionVectorParameter, -900, y); n.set_editor_property("parameter_name", name); n.set_editor_property("default_value", v); return n
def custom(m, code, inputs, out_type=unreal.CustomMaterialOutputType.CMOT_FLOAT3):
    """inputs: [(name, expression, output pin)]"""
    c = node(m, unreal.MaterialExpressionCustom, -300, 0)
    c.set_editor_property("code", code); c.set_editor_property("output_type", out_type); c.set_editor_property("description", "RTReveal")
    ins = []
    for nm, _, _ in inputs:
        ci = unreal.CustomInput(); ci.set_editor_property("input_name", nm); ins.append(ci)
    c.set_editor_property("inputs", ins)
    for nm, e, pin in inputs: assert MEL.connect_material_expressions(e, pin, c, nm), (nm, pin)
    return c
def check(m):
    MEL.recompile_material(m); eal.save_loaded_asset(m)
    st = MEL.get_statistics(m)
    assert st.num_pixel_shader_instructions > 0, m.get_name() + " failed to compile (see the editor log)"
    print(m.get_name(), "compiled: pixel instructions", st.num_pixel_shader_instructions)

# ---- post process
PP_CODE = f"""
float3 c = Scene.rgb;
float3 add = 0;
float ghost = 0;
float3 wp = WP;
float camd = length(wp - Cam);
float4 R[{SLOTS}] = {{ {", ".join(f"Rect{i}" for i in range(SLOTS))} }};
float4 I[{SLOTS}] = {{ {", ".join(f"Info{i}" for i in range(SLOTS))} }};
float gw = max(3.0, camd * 0.0009);
float2 g = abs(frac(wp.xy / 400.0 + 0.5) - 0.5) * 400.0;
float grid = (1.0 - smoothstep(gw, gw * 2.5, min(g.x, g.y))) * saturate(1.0 - camd / 45000.0);
[unroll] for (int i = 0; i < {SLOTS}; i++)
{{
    float age = T - I[i].z;
    if (age < 0.0 || age > Dur) continue;
    float fade = 1.0 - smoothstep(Dur - 1.5, Dur, age);
    float2 dIn = min(wp.xy - R[i].xy, R[i].zw - wp.xy);
    float e = min(dIn.x, dIn.y);
    float bw = max(40.0, camd * 0.0025);
    add += Col.rgb * exp(-(e * e) / (bw * bw)) * fade * 0.9;
    float inside = saturate(e / bw + 0.5);
    float x = distance(wp.xy, I[i].xy) - age * Speed;
    float rw = max(220.0, camd * 0.004);
    float ring = exp(-(x * x) / (rw * rw));
    float halo = exp(-(x * x) / (2500.0 * 2500.0)) * 0.3;
    float behind = saturate(-x / 400.0);
    float trail = behind * exp(min(x, 0.0) / 5000.0);
    float ahead = 1.0 - behind;
    ghost = max(ghost, ahead * inside * fade);
    add += Col.rgb * inside * fade * (ring * 1.2 + halo + grid * (trail * 0.9 + ahead * 0.3));
}}
float l = dot(c, float3(0.3, 0.59, 0.11));
c = lerp(c, Col.rgb * (0.12 + l * 0.8), ghost * 0.8);
return c + add;
"""
pp = fresh("M_RT_RevealPP")
pp.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
pp.set_editor_property("blendable_location", unreal.BlendableLocation.BL_SCENE_COLOR_AFTER_TONEMAPPING)
st = node(pp, unreal.MaterialExpressionSceneTexture, -900, -600); st.set_editor_property("scene_texture_id", unreal.SceneTextureId.PPI_POST_PROCESS_INPUT0)
wp = node(pp, unreal.MaterialExpressionWorldPosition, -900, -500)
cam = node(pp, unreal.MaterialExpressionCameraPositionWS, -900, -420)
tm = node(pp, unreal.MaterialExpressionTime, -900, -360)
ins = [("Scene", st, "Color"), ("WP", wp, ""), ("Cam", cam, ""), ("T", tm, ""),
       ("Dur", scalar(pp, "Duration", DUR, -300), ""), ("Speed", scalar(pp, "Speed", SPEED, -240), ""), ("Col", vector(pp, "Color", COL, -180), "RGBA")]
for i in range(SLOTS):
    ins.append((f"Rect{i}", vector(pp, f"Rect{i}", unreal.LinearColor(0, 0, 0, 0), i * 120), "RGBA"))
    ins.append((f"Info{i}", vector(pp, f"Info{i}", unreal.LinearColor(0, 0, -1.0e6, 0), i * 120 + 60), "RGBA"))
MEL.connect_material_property(custom(pp, PP_CODE, ins), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
check(pp)

# ---- curtain
CU_CODE = """
float age = T - Start;
if (age < 0.0 || age > Dur) return 0;
float v = UV.y;
float top = saturate(age / 0.8);
float m = 1.0 - smoothstep(top - 0.015, top, v);
float base = pow(1.0 - v, 2.0);
float band = exp(-pow((v - top) / 0.012, 2.0)) * (1.0 - 0.6 * saturate(age - 0.8));
float scan = pow(frac(v * 3.0 - T * 0.6), 12.0) * 0.8;
float streak = 0.8 + 0.2 * sin(UV.x * 6.2832 * 4.0 + T * 3.0);
float fade = 1.0 - smoothstep(Dur - 1.8, Dur, age);
float flash = 1.0 + 1.5 * exp(-age * 2.0);
return Col.rgb * ((base * streak * (0.7 + scan) * flash) * m + band * 2.5) * fade * Intensity;
"""
cu = fresh("M_RT_RevealCurtain")
cu.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
cu.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
cu.set_editor_property("two_sided", True)
uvn = node(cu, unreal.MaterialExpressionTextureCoordinate, -900, -500)
tm = node(cu, unreal.MaterialExpressionTime, -900, -420)
c = custom(cu, CU_CODE, [("UV", uvn, ""), ("T", tm, ""), ("Start", scalar(cu, "StartTime", -1.0e6, -360), ""), ("Dur", scalar(cu, "Duration", DUR, -300), ""),
                         ("Col", vector(cu, "Color", COL, -240), "RGBA"), ("Intensity", scalar(cu, "Intensity", 0.6, -180), "")])
ea = node(cu, unreal.MaterialExpressionEyeAdaptationInverse, -100, 0)
pins = MEL.get_material_expression_input_names(ea) if hasattr(MEL, "get_material_expression_input_names") else []
assert MEL.connect_material_expressions(c, "", ea, pins[0] if pins else "LightValue"), pins
MEL.connect_material_property(ea, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
check(cu)

# ---- generator
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
gens = [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if isinstance(a, unreal.RTTownGenerator)]
assert len(gens) == 1, (w.get_path_name(), len(gens))
g = gens[0]
for k, v in (("reveal_effect", True), ("reveal_post_material", pp), ("reveal_curtain_material", cu), ("reveal_duration", DUR)): g.set_editor_property(k, v)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("generator", g.get_actor_label(), "in", w.get_path_name(), ": reveal materials set, level saved")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
