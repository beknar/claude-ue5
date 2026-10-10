"""No landscape grass inside the houses: a world-space mask (black under every house footprint) multiplies each grass input of a
COPY of the pack's landscape master (/Game/Castle/Landscape); castle_level's landscape uses the copy (pack map untouched)."""
import os, json, struct, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary; mel = unreal.MaterialEditingLibrary
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert "castle_level" in w.get_path_name(), w.get_path_name()
X0, Y0, SIZE, RES = -12000.0, -12000.0, 24000.0, 2048
buf = bytearray(b"\xff" * (RES * RES))                     # 8-bit grey, written as an uncompressed TGA (no PIL in UE Python)
def px(p): return ((p.x - X0) / SIZE * RES, (p.y - Y0) / SIZE * RES)
def fill_quad(q):
    xs = [p[0] for p in q]; ys = [p[1] for p in q]
    def inside(x, y):
        s = None
        for (ax, ay), (bx, by) in zip(q, q[1:] + q[:1]):
            c = (bx - ax) * (y - ay) - (by - ay) * (x - ax)
            if s is None: s = c > 0
            elif (c > 0) != s and abs(c) > 1e-9: return False
        return True
    for yy in range(max(0, int(min(ys))), min(RES, int(max(ys)) + 1)):
        for xx in range(max(0, int(min(xs))), min(RES, int(max(xs)) + 1)):
            if inside(xx + 0.5, yy + 0.5): buf[yy * RES + xx] = 0
n = 0
# interiors only (inner faces of the walls) of the houses that have floors; the ground outside stays as authored
FURNISHED = {"SM_models_Cube_95", "SM_models_Cube_094", "SM_models_Cube_089", "SM_models_Cube_90", "SM_models_Cube_075",
             "SM_models_Cube_91", "SM_models_Plane_039", "SM_house_01", "SM_house_2"}
PADX, PADY = 44.0, 120.0   # side walls 28 cm, gable/chimney end walls ~112 cm (inner faces 613-627 / 528, 1058): mask up to the outer faces
RECT = {"SM_house_04": (-598, 595, -1040, 1040), "SM_house_03": (-609, 595, -510, 510), "SM_house_02": (-609, 595, -510, 510), "SM_house_01": (-596, 595, -1040, 1040)}
for a in eas.get_all_level_actors():
    if a.get_actor_label() in FURNISHED and isinstance(a, unreal.StaticMeshActor):
        x0, x1, y0, y1 = RECT[a.static_mesh_component.static_mesh.get_name().replace("_open", "")]; tr = a.get_actor_transform()
        x0, x1, y0, y1 = x0 - PADX, x1 + PADX, y0 - PADY, y1 + PADY    # RECT is 18 cm inside the inner wall face: grass under the walls leans into the rooms
        pts = [tr.transform_location(unreal.Vector(x, y, 0)) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        fill_quad([px(p) for p in pts]); n += 1
png = r"E:\code\claude-ue5\claude_ue5\SourceArt\castle_interactive\T_GrassMask.tga"
with open(png, "wb") as fh:                                  # TGA type 3 (greyscale), origin top-left -> row 0 = Y0
    fh.write(struct.pack("<BBBHHBHHHHBB", 0, 0, 3, 0, 0, 0, 0, 0, RES, RES, 8, 0x20)); fh.write(bytes(buf))
t = unreal.AssetImportTask(); t.filename = png; t.destination_path = "/Game/Castle/Landscape"; t.automated = True; t.replace_existing = True; t.save = True
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
mask = unreal.load_asset("/Game/Castle/Landscape/T_GrassMask")
mask.set_editor_property("srgb", False); mask.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_GRAYSCALE)
mask.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP); mask.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
# a streamed-in low mip blurs the house rects away and the grass maps (built from it) leak grass through the floors
mask.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS); mask.set_editor_property("never_stream", True)
mask.set_editor_property("filter", unreal.TextureFilter.TF_NEAREST); eal.save_loaded_asset(mask)
SRC_M, SRC_MI = "/Game/Medieval_Fantasy_Village/Landscape/M_landscape_Master", "/Game/Medieval_Fantasy_Village/Landscape/MI_landscape"
DM, DMI = "/Game/Castle/Landscape/M_landscape_Castle", "/Game/Castle/Landscape/MI_landscape_Castle"
for p in (DMI, DM):
    if eal.does_asset_exist(p): eal.delete_asset(p)
m = eal.duplicate_asset(SRC_M, DM); mi = eal.duplicate_asset(SRC_MI, DMI)
gout = next(e for e in unreal.ObjectIterator(unreal.MaterialExpressionLandscapeGrassOutput) if e.get_outer() == m)
srcs = mel.get_inputs_for_material_expression(m, gout)
names = [str(g.get_editor_property("name")) for g in gout.get_editor_property("grass_types")]
wp = mel.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1400, 2200)
cm = mel.create_material_expression(m, unreal.MaterialExpressionComponentMask, -1200, 2200); cm.set_editor_property("r", True); cm.set_editor_property("g", True)
mel.connect_material_expressions(wp, "", cm, "")
sub = mel.create_material_expression(m, unreal.MaterialExpressionSubtract, -1050, 2200)
off = mel.create_material_expression(m, unreal.MaterialExpressionConstant2Vector, -1200, 2320); off.set_editor_property("r", X0); off.set_editor_property("g", Y0)
mel.connect_material_expressions(cm, "", sub, "A"); mel.connect_material_expressions(off, "", sub, "B")
div = mel.create_material_expression(m, unreal.MaterialExpressionDivide, -900, 2200); div.set_editor_property("const_b", SIZE)
mel.connect_material_expressions(sub, "", div, "A")
ts = mel.create_material_expression(m, unreal.MaterialExpressionTextureSample, -700, 2200); ts.set_editor_property("texture", mask)
ts.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE)   # mask is sRGB off: plain GRAYSCALE fails to compile -> checker landscape
mel.connect_material_expressions(div, "", ts, "UVs")
done = []
for i, nm in enumerate(names):
    src = srcs[i] if i < len(srcs) else None
    if src is None: continue
    out = mel.get_input_node_output_name_for_material_expression(gout, src)
    mul = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -450, 2200 + 140 * i)
    mel.connect_material_expressions(src, out, mul, "A"); mel.connect_material_expressions(ts, "R", mul, "B")
    mel.connect_material_expressions(mul, "", gout, nm); done.append(nm)
mel.recompile_material(m); eal.save_loaded_asset(m)
assert mel.get_statistics(m).num_pixel_shader_instructions > 0, "M_landscape_Castle failed to compile"
mel.set_material_instance_parent(mi, m); eal.save_loaded_asset(mi)
land = next(a for a in eas.get_all_level_actors() if a.get_class().get_name() == "Landscape")
land.set_editor_property("landscape_material", mi)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("houses masked", n, "| grass inputs masked", done, "| landscape material ->", land.get_editor_property("landscape_material").get_path_name())
