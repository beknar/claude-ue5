"""Helpers for building textures, Substrate materials and profiles from Python."""
import os, unreal

mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()


def import_texture(png, dest, kind="color"):
    """kind: color (sRGB), linear, normal, height16"""
    name = os.path.splitext(os.path.basename(png))[0]
    t = unreal.AssetImportTask()
    t.filename = png; t.destination_path = dest; t.destination_name = name
    t.automated = True; t.replace_existing = True; t.save = False
    at.import_asset_tasks([t])
    tex = unreal.load_asset(f"{dest}/{name}")
    if kind == "color":
        tex.set_editor_property("srgb", True)
    elif kind == "normal":
        tex.set_editor_property("srgb", False)
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
    elif kind == "linear":
        tex.set_editor_property("srgb", False)
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
    elif kind == "height16":
        tex.set_editor_property("srgb", False)
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_GRAYSCALE)
    eal.save_loaded_asset(tex)
    return tex


def new_material(path):
    folder, name = path.rsplit("/", 1)
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    return at.create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())


def expr(m, cls, x, y, **props):
    e = mel.create_material_expression(m, cls, x, y)
    for k, v in props.items():
        e.set_editor_property(k, v)
    return e


def tex_sample(m, tex, x, y, sampler=None, uv=None, param=None):
    if param:
        e = expr(m, unreal.MaterialExpressionTextureSampleParameter2D, x, y, parameter_name=param, texture=tex)
    else:
        e = expr(m, unreal.MaterialExpressionTextureSample, x, y, texture=tex)
    if sampler is not None:
        e.set_editor_property("sampler_type", sampler)
    if uv is not None:
        mel.connect_material_expressions(uv, "", e, "UVs")
    return e


def scalar(m, name, val, x, y):
    return expr(m, unreal.MaterialExpressionScalarParameter, x, y, parameter_name=name, default_value=val)


def vector(m, name, rgb, x, y):
    return expr(m, unreal.MaterialExpressionVectorParameter, x, y, parameter_name=name,
                default_value=unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))


def const3(m, rgb, x, y):
    return expr(m, unreal.MaterialExpressionConstant3Vector, x, y, constant=unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1))


def mul(m, a, b, x, y, a_out="", b_out=""):
    e = expr(m, unreal.MaterialExpressionMultiply, x, y)
    mel.connect_material_expressions(a, a_out, e, "A"); mel.connect_material_expressions(b, b_out, e, "B")
    return e


def link(src, src_out, dst, dst_in):
    ok = mel.connect_material_expressions(src, src_out, dst, dst_in)
    if not ok:
        unreal.log_warning(f"link failed {src.get_name()}.{src_out} -> {dst.get_name()}.{dst_in}")
    return ok


def slab(m, x, y, **inputs):
    """inputs: pin name (spaces -> underscores) -> expression or (expression, output_name)"""
    s = expr(m, unreal.MaterialExpressionSubstrateSlabBSDF, x, y)
    for k, v in inputs.items():
        pin = k.replace("_", " ")
        if isinstance(v, tuple):
            link(v[0], v[1], s, pin)
        else:
            link(v, "", s, pin)
    return s


def specular_profile(path, lut_tex):
    folder, name = path.rsplit("/", 1)
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    sp = at.create_asset(name, folder, unreal.SpecularProfile, unreal.SpecularProfileFactory())
    st = sp.get_editor_property("settings")
    st.set_editor_property("texture", lut_tex)
    st.set_editor_property("format", unreal.SpecularProfileFormat.VIEW_LIGHT_VECTOR)
    sp.set_editor_property("settings", st)
    eal.save_loaded_asset(sp)
    return sp


def finish(m):
    mel.layout_material_expressions(m)
    mel.recompile_material(m)
    eal.save_loaded_asset(m)


def enable_nanite(mesh_path, displacement=False):
    sm = unreal.load_asset(mesh_path)
    ns = sm.get_editor_property("nanite_settings")
    ns.set_editor_property("enabled", True)
    ns.set_editor_property("fallback_relative_error", 0.0)
    sm.set_editor_property("nanite_settings", ns)
    eal.save_loaded_asset(sm)
    return sm
