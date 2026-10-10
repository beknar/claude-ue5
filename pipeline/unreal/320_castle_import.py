"""Import the interactive village pieces (SourceArt/castle_interactive) into /Game/Castle/Interactive: open houses, door leaves,
container bodies/lids/liquids, splash meshes. Materials: pack instances by slot name (Interior -> MI_wood), plus new
M_Ale (barrel liquid) and M_Splash (translucent water, 'Opacity' parameter for fading). Collision complex-as-simple on
houses/doors/containers, none on liquid/splash."""
import os, sys, json, importlib, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mat_lib as L
importlib.reload(L)
eal = unreal.EditorAssetLibrary; mel = unreal.MaterialEditingLibrary
SRC = r"E:\code\claude-ue5\claude_ue5\SourceArt\castle_interactive"
D = "/Game/Castle/Interactive"; MP = "/Game/Medieval_Fantasy_Village/Materials"
PACK = {n: unreal.load_asset(f"{MP}/Props/{n}") for n in ("MI_details", "MI_walls", "MI_side_wall", "MI_roof_house", "MI_small_props", "MI_porch")}
PACK["Interior"] = unreal.load_asset(f"{MP}/MI_wood")
# --- materials
ale = L.new_material(f"{D}/Materials/M_Ale")
mel.connect_material_property(L.const3(ale, (0.10, 0.045, 0.012), -400, 0), "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(L.expr(ale, unreal.MaterialExpressionConstant, -400, 150, r=0.04), "", unreal.MaterialProperty.MP_ROUGHNESS)
mel.connect_material_property(L.expr(ale, unreal.MaterialExpressionConstant, -400, 250, r=0.8), "", unreal.MaterialProperty.MP_SPECULAR)
L.finish(ale)
spl = L.new_material(f"{D}/Materials/M_Splash")
spl.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT); spl.set_editor_property("two_sided", True)
spl.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE)
mel.connect_material_property(L.vector(spl, "Tint", (0.62, 0.74, 0.80), -500, 0), "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(L.expr(spl, unreal.MaterialExpressionConstant, -500, 120, r=0.05), "", unreal.MaterialProperty.MP_ROUGHNESS)
fr = L.expr(spl, unreal.MaterialExpressionFresnel, -700, 300)
op = L.expr(spl, unreal.MaterialExpressionMultiply, -350, 300)
lp = L.expr(spl, unreal.MaterialExpressionLinearInterpolate, -500, 300, const_a=0.12, const_b=0.75); L.link(fr, "", lp, "Alpha")
L.link(lp, "", op, "A"); L.link(L.scalar(spl, "Opacity", 0.8, -500, 450), "", op, "B")
mel.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
mel.connect_material_property(L.const3(spl, (0.01, 0.012, 0.015), -500, 550), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.connect_material_property(L.expr(spl, unreal.MaterialExpressionConstant, -500, 650, r=1.12), "", unreal.MaterialProperty.MP_REFRACTION)
L.finish(spl)
PACK["M_Ale"] = ale; PACK["Splash"] = spl
# --- meshes
def imp(fname):
    o = unreal.FbxImportUI()
    o.set_editor_property("import_mesh", True); o.set_editor_property("import_as_skeletal", False)
    o.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    o.set_editor_property("import_materials", False); o.set_editor_property("import_textures", False)
    sd = o.get_editor_property("static_mesh_import_data")
    sd.set_editor_property("combine_meshes", True); sd.set_editor_property("auto_generate_collision", False)
    sd.set_editor_property("generate_lightmap_u_vs", False)
    t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, fname); t.destination_path = D + "/Meshes"
    t.destination_name = os.path.splitext(fname)[0]; t.automated = True; t.replace_existing = True; t.save = True; t.options = o
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    return unreal.load_asset(f"{D}/Meshes/{t.destination_name}")
for f in sorted(os.listdir(SRC)):
    if not f.endswith(".fbx"): continue
    sm = imp(f); name = sm.get_name()
    for i, s in enumerate(sm.static_materials):
        slot = str(s.material_slot_name)
        key = next((k for k in PACK if k.lower() in slot.lower()), None)
        if "liquid" in name: key = "M_Ale"
        if "splash" in name: key = "Splash"
        if key is None and ("door" in name): key = "MI_details"
        if key: sm.set_material(i, PACK[key])
        else: print("  no material for", name, slot)
    bs = sm.get_editor_property("body_setup")
    if bs:
        bs.set_editor_property("collision_trace_flag",
            unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE if not any(k in name for k in ("liquid", "splash")) else unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
        sm.set_editor_property("body_setup", bs)
    eal.save_loaded_asset(sm, only_if_is_dirty=False)
    b = sm.get_bounding_box()
    print(f"{name}: slots {[str(s.material_slot_name) + '->' + (s.material_interface.get_name() if s.material_interface else '-') for s in sm.static_materials]} "
          f"bounds {tuple(round(v) for v in (b.min.x, b.min.y, b.min.z))}..{tuple(round(v) for v in (b.max.x, b.max.y, b.max.z))}")
