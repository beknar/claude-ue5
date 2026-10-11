"""Import the Meshy JRPG character (SK_JRPG_Fem1, 170 cm, UE-mannequin-named Meshy rig + root, no clips) + its glTF PBR
textures; M_JRPG_Fem1 (glTF metal/rough: G = roughness, B = metallic; OpenGL normal -> flip green; two-sided).
Args: [Fem1|Fem3]  (source art SourceArt/jrpg_<ch>, assets /Game/JRPG; texture names per character in TEX)"""
import os, sys, importlib, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mat_lib as L
importlib.reload(L)
mel = L.mel; eal = L.eal
CH = sys.argv[1] if len(sys.argv) > 1 else "Fem1"
NAME = "SK_JRPG_" + CH
SRC = r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_" + CH.lower(); D = "/Game/JRPG"
TEX = {"Fem1": ("texture_0.png", "texture_0_normal.png", "texture_0_metallic-texture_0_roughness.png"),
       "Fem3": ("Image_0.png", "Image_2.png", "Image_1.png"), "Fem4": ("Image_0.png", "Image_2.png", "Image_1.png")}[CH]                 # (base colour, normal, metal/rough)
t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, NAME + ".fbx"); t.destination_path = D + "/Character"
t.automated = True; t.replace_existing = True; t.save = True
o = unreal.FbxImportUI(); o.import_mesh = True; o.import_as_skeletal = True; o.import_animations = False; o.import_materials = True; o.import_textures = False
o.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
t.options = o
_w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
_cv = unreal.SystemLibrary.get_console_variable_int_value("Interchange.FeatureFlags.Import.FBX")
unreal.SystemLibrary.execute_console_command(_w, "Interchange.FeatureFlags.Import.FBX 0")   # Interchange drops the Blender-rigged mesh payload (fem3); legacy FBX import works
try: L.at.import_asset_tasks([t])
finally: unreal.SystemLibrary.execute_console_command(_w, f"Interchange.FeatureFlags.Import.FBX {_cv}")
kinds = {}
for p in t.imported_object_paths:
    a = unreal.load_asset(p); kinds.setdefault(a.get_class().get_name(), []).append(p)
for k, v in kinds.items(): print(k, v)
def tex(name, kind):
    tx = L.import_texture(os.path.join(SRC, name), D + "/Textures", kind)
    if kind == "normal": tx.set_editor_property("flip_green_channel", True); eal.save_loaded_asset(tx)
    return tx
T = {"bc": tex(TEX[0], "color"), "n": tex(TEX[1], "normal"), "mr": tex(TEX[2], "linear")}
path = f"{D}/Materials/M_JRPG_{CH}"
if eal.does_asset_exist(path): m = unreal.load_asset(path); mel.delete_all_material_expressions(m)
else: m = L.new_material(path)
m.set_editor_property("use_material_attributes", True); m.set_editor_property("two_sided", True)
S = unreal.MaterialSamplerType
bc = L.tex_sample(m, T["bc"], -900, -300)
mr = L.tex_sample(m, T["mr"], -900, 0, sampler=S.SAMPLERTYPE_MASKS)
nm = L.tex_sample(m, T["n"], -900, 300, sampler=S.SAMPLERTYPE_NORMAL)
tint = L.vector(m, "AlbedoTint", (1.0, 1.0, 1.0), -900, -500)
alb = L.expr(m, unreal.MaterialExpressionMultiply, -600, -350); L.link(bc, "RGB", alb, "A"); L.link(tint, "", alb, "B")
rs = L.expr(m, unreal.MaterialExpressionMultiply, -600, 50); L.link(mr, "G", rs, "A"); L.link(L.scalar(m, "RoughnessScale", 1.0, -800, 150), "", rs, "B")
rc = L.expr(m, unreal.MaterialExpressionClamp, -450, 50); L.link(rs, "", rc, ""); rc.set_editor_property("min_default", 0.25); rc.set_editor_property("max_default", 1.0)
mma = L.expr(m, unreal.MaterialExpressionMakeMaterialAttributes, -200, 0)
L.link(alb, "", mma, "BaseColor"); L.link(mr, "B", mma, "Metallic"); L.link(rc, "", mma, "Roughness")
L.link(nm, "RGB", mma, "Normal"); L.link(L.scalar(m, "Specular", 0.45, -450, 250), "", mma, "Specular")
mel.connect_material_property(mma, "", unreal.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
try: m.set_editor_property("used_with_skeletal_mesh", True)
except Exception: pass
L.finish(m)
sk = unreal.load_asset(kinds["SkeletalMesh"][0])
sk.set_editor_property("materials", [unreal.SkeletalMaterial(material_interface=m, material_slot_name=str(s.get_editor_property("material_slot_name")))
                                     for s in sk.get_editor_property("materials")])            # struct elements are copies: fresh ones
sk.modify(); eal.save_loaded_asset(sk, only_if_is_dirty=False)
for p in kinds.get("Material", []):
    if eal.does_asset_exist(p.split(".")[0]): print("delete blank", p, eal.delete_asset(p.split(".")[0]))
sk = unreal.load_asset(kinds["SkeletalMesh"][0])
print("slots", [(str(s.material_slot_name), s.material_interface.get_name() if s.material_interface else None) for s in sk.get_editor_property("materials")])
b = sk.get_bounds(); print("bounds", b.origin, b.box_extent)
ref = unreal.AnimPoseExtensions.get_reference_pose(sk.get_editor_property("skeleton"))
for bn in ("root", "pelvis", "head", "hand_l", "foot_l", "ball_l"):
    tr = unreal.AnimPoseExtensions.get_bone_pose(ref, bn, unreal.AnimPoseSpaces.WORLD); print(bn, tr.translation, tr.scale3d if bn == "root" else "")
print("anim sequences imported:", len(kinds.get("AnimSequence", [])))
