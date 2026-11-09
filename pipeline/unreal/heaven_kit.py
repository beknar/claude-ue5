"""Heaven's kit, shared by 908 (the city) and 909 (the fortress): its two materials (M_HV_Surface: a colour, metal, roughness and
glow; M_HV_Shield: the shield's), every instance of the surface material both scripts use (one table: PR #33's review found
the two scripts writing the same instances with their own values), and the merge of boxes into a mesh (saved: a merge makes
its mesh in memory only). Imported, not run: `import heaven_kit as hk; importlib.reload(hk)` (the editor keeps modules)."""
import unreal
eal = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary; AT = unreal.AssetToolsHelpers.get_asset_tools()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V = unreal.Vector
HV = "/Game/RandomDungeon/Heaven"; HVM = HV + "/Meshes"

def master():
    path = HV + "/M_HV_Surface"
    if eal.does_asset_exist(path): return unreal.load_asset(path)
    m = AT.create_asset("M_HV_Surface", HV, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("used_with_instanced_static_meshes", True)
    col = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -700, -200)
    col.set_editor_property("parameter_name", "Color"); col.set_editor_property("default_value", unreal.LinearColor(0.5, 0.5, 0.5, 1.0))
    met = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, 0)
    met.set_editor_property("parameter_name", "Metallic"); met.set_editor_property("default_value", 0.0)
    rou = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, 120)
    rou.set_editor_property("parameter_name", "Roughness"); rou.set_editor_property("default_value", 0.6)
    glo = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, 260)
    glo.set_editor_property("parameter_name", "Glow"); glo.set_editor_property("default_value", 0.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -400, 260)
    MEL.connect_material_expressions(col, "", mul, "A"); MEL.connect_material_expressions(glo, "", mul, "B")
    MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(met, "", unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(rou, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    print("HV1 compiling M_HV_Surface")
    MEL.recompile_material(m); eal.save_loaded_asset(m, False)
    return m


def shield_master():
    path = HV + "/M_HV_Shield"
    if eal.does_asset_exist(path): return unreal.load_asset(path)
    m = AT.create_asset("M_HV_Shield", HV, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    m.set_editor_property("used_with_static_lighting", False)
    fr = MEL.create_material_expression(m, unreal.MaterialExpressionFresnel, -800, 0)
    fr.set_editor_property("exponent", 2.2); fr.set_editor_property("base_reflect_fraction", 0.0)
    col = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -800, -250)
    col.set_editor_property("parameter_name", "Color"); col.set_editor_property("default_value", unreal.LinearColor(0.35, 0.75, 1.0, 1.0))
    glo = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -800, -100)
    glo.set_editor_property("parameter_name", "Glow"); glo.set_editor_property("default_value", 2.5)
    # (the shimmer: the glow breathing a little with time)
    tm = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -1000, 250)
    sn = MEL.create_material_expression(m, unreal.MaterialExpressionSine, -800, 250); sn.set_editor_property("period", 6.0)
    MEL.connect_material_expressions(tm, "", sn, "")
    k1 = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -800, 380); k1.set_editor_property("r", 0.2)
    sh = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, 300)
    MEL.connect_material_expressions(sn, "", sh, "A"); MEL.connect_material_expressions(k1, "", sh, "B")
    one = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -600, 420); one.set_editor_property("r", 1.0)
    br = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -450, 320)
    MEL.connect_material_expressions(sh, "", br, "A"); MEL.connect_material_expressions(one, "", br, "B")
    f2 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, 0)
    MEL.connect_material_expressions(fr, "", f2, "A"); MEL.connect_material_expressions(glo, "", f2, "B")
    k2 = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -600, 120); k2.set_editor_property("r", 0.12)
    f3 = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -450, 60)
    MEL.connect_material_expressions(f2, "", f3, "A"); MEL.connect_material_expressions(k2, "", f3, "B")
    em = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, -100)
    MEL.connect_material_expressions(col, "", em, "A"); MEL.connect_material_expressions(f3, "", em, "B")
    em2 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -150, -50)
    MEL.connect_material_expressions(em, "", em2, "A"); MEL.connect_material_expressions(br, "", em2, "B")
    MEL.connect_material_property(em2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    k3 = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -600, 560); k3.set_editor_property("r", 0.5)
    op = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -450, 520)
    MEL.connect_material_expressions(fr, "", op, "A"); MEL.connect_material_expressions(k3, "", op, "B")
    k4 = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -450, 640); k4.set_editor_property("r", 0.03)
    op2 = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -300, 560)
    MEL.connect_material_expressions(op, "", op2, "A"); MEL.connect_material_expressions(k4, "", op2, "B")
    MEL.connect_material_property(op2, "", unreal.MaterialProperty.MP_OPACITY)
    print("HV1 compiling M_HV_Shield")
    MEL.recompile_material(m); eal.save_loaded_asset(m, False)
    return m



# (every instance: name, colour, metal, roughness, glow)
MATS = {"stone": ("MI_HV_Stone", (0.2, 0.21, 0.23), 0.0, 0.7), "brick": ("MI_HV_Brick", (0.36, 0.17, 0.12), 0.0, 0.85),
        "concrete": ("MI_HV_Concrete", (0.5, 0.5, 0.48), 0.0, 0.85), "dark": ("MI_HV_DarkConcrete", (0.16, 0.17, 0.19), 0.0, 0.8),
        "glass": ("MI_HV_Glass", (0.025, 0.05, 0.075), 1.0, 0.06), "steel": ("MI_HV_Steel", (0.13, 0.14, 0.16), 0.85, 0.32),
        "white": ("MI_HV_White", (0.82, 0.84, 0.86), 0.0, 0.45), "asphalt": ("MI_HV_Asphalt", (0.045, 0.045, 0.05), 0.0, 0.92),
        "paving": ("MI_HV_Paving", (0.42, 0.41, 0.39), 0.0, 0.85), "roof": ("MI_HV_Roof", (0.3, 0.3, 0.31), 0.0, 0.9),
        "panel": ("MI_HV_LightPanel", (0.9, 0.95, 1.0), 0.0, 0.5, 6.0), "red": ("MI_HV_RedLight", (1.0, 0.06, 0.04), 0.0, 0.5, 12.0),
        "cyan": ("MI_HV_CyanStrip", (0.2, 0.85, 1.0), 0.0, 0.4, 8.0), "hazard": ("MI_HV_Hazard", (0.75, 0.55, 0.05), 0.2, 0.5),
        "plate": ("MI_HV_FloorPlate", (0.22, 0.23, 0.25), 0.7, 0.45)}


def materials():
    """the surface material, the shield's, and every instance (saved), as {key: instance}, the shield under 'shield'"""
    surf = master(); shield = shield_master()
    out = {"shield": shield}
    for k, spec in MATS.items():
        name, rgb, metal, rough = spec[:4]; glow = spec[4] if len(spec) > 4 else 0.0
        path = HV + "/" + name
        if not eal.does_asset_exist(path): AT.create_asset(name, HV, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        m = unreal.load_asset(path); MEL.set_material_instance_parent(m, surf)
        MEL.set_material_instance_vector_parameter_value(m, "Color", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        MEL.set_material_instance_scalar_parameter_value(m, "Metallic", metal)
        MEL.set_material_instance_scalar_parameter_value(m, "Roughness", rough)
        MEL.set_material_instance_scalar_parameter_value(m, "Glow", glow)
        MEL.update_material_instance(m); eal.save_loaded_asset(m, False)
        out[k] = m
    return out


def boxes(name, parts, mat, rebuild=False):
    """a mesh merged from boxes (x0, x1, y0, y1, z0, z1, material key), its pivot the world's origin, saved under HVM; made
    again with rebuild. Returns None when the merge made nothing"""
    path = f"{HVM}/{name}"
    if eal.does_asset_exist(path) and not rebuild: return unreal.load_asset(path)
    if eal.does_asset_exist(path): eal.delete_asset(path)
    cube = unreal.load_asset("/Engine/BasicShapes/Cube")
    acts = []
    for (x0, x1, y0, y1, z0, z1, mk) in parts:
        a = eas.spawn_actor_from_object(cube, V((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        a.set_actor_scale3d(V(max(x1 - x0, 0.2) / 100.0, max(y1 - y0, 0.2) / 100.0, max(z1 - z0, 0.2) / 100.0))
        a.static_mesh_component.set_material(0, mat[mk])
        acts.append(a)
    merge(acts, name)
    m = unreal.load_asset(path)
    if m: eal.save_loaded_asset(m, False)
    return m


def merge(acts, name):
    """the actors' static meshes merged into HVM/name (the merge puts "SM_" before the name it is given), the actors destroyed"""
    o = unreal.MergeStaticMeshActorsOptions()
    o.set_editor_property("base_package_name", f"{HVM}/{name[3:]}"); o.set_editor_property("destroy_source_actors", True); o.set_editor_property("spawn_merged_actor", False)
    ms = o.get_editor_property("mesh_merging_settings")
    ms.set_editor_property("pivot_type", unreal.MeshMergePivotType.WORLD_ORIGIN); ms.set_editor_property("merge_physics_data", True)
    ms.set_editor_property("merge_materials", False); ms.set_editor_property("generate_light_map_uv", False)
    o.set_editor_property("mesh_merging_settings", ms)
    unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem).merge_static_mesh_actors(acts, o)
    for a in acts:
        try: a.destroy_actor()
        except Exception: pass
