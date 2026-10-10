"""Import the Tripo anime female (SK_FF_Anime, 165 cm, UE4-mannequin-named skeleton) + its glTF PBR textures and build
M_FF_Anime (glTF metal/rough: G = roughness, B = metallic; OpenGL normal -> flip green; two-sided)."""
import os, sys, importlib, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mat_lib as L
importlib.reload(L)
mel = L.mel; eal = L.eal
SRC = r"E:\code\claude-ue5\claude_ue5\SourceArt\ff_anime"
D = "/Game/FF"
t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, "SK_FF_Anime.fbx"); t.destination_path = D + "/Character"
t.automated = True; t.replace_existing = True; t.save = True
L.at.import_asset_tasks([t])
kinds = {}
for p in t.imported_object_paths:
    a = unreal.load_asset(p); kinds.setdefault(a.get_class().get_name(), []).append(p)
for k, v in kinds.items(): print(k, v)
def tex(name, kind):
    tx = L.import_texture(os.path.join(SRC, name), D + "/Textures", kind)
    if kind == "normal": tx.set_editor_property("flip_green_channel", True); eal.save_loaded_asset(tx)
    return tx
T = {"bc": tex("T_FF_Color.png", "color"), "n": tex("T_FF_Normal.png", "normal"), "mr": tex("T_FF_MetalRough.png", "linear")}
path = f"{D}/Materials/M_FF_Anime"
if eal.does_asset_exist(path):
    m = unreal.load_asset(path); mel.delete_all_material_expressions(m)
else:
    m = L.new_material(path)
m.set_editor_property("use_material_attributes", True)
m.set_editor_property("two_sided", True)
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
new = []                                                      # struct elements are copies: build fresh ones
for s in sk.get_editor_property("materials"):
    new.append(unreal.SkeletalMaterial(material_interface=m, material_slot_name=str(s.get_editor_property("material_slot_name"))))
sk.set_editor_property("materials", new)
sk.modify(); eal.save_loaded_asset(sk, only_if_is_dirty=False)
for p in kinds.get("Material", []) + [x for x in eal.list_assets(D + "/Character", recursive=False) if "tripo_mat" in x]:
    if eal.does_asset_exist(p.split(".")[0]): print("delete blank", p, eal.delete_asset(p.split(".")[0]))
sk = unreal.load_asset(kinds["SkeletalMesh"][0])
print("slots", [(str(s.material_slot_name), s.material_interface.get_path_name() if s.material_interface else None) for s in sk.get_editor_property("materials")])
b = sk.get_bounds(); print("bounds", b.origin, b.box_extent)
ref = unreal.AnimPoseExtensions.get_reference_pose(sk.get_editor_property("skeleton"))
for bn in ("root", "pelvis", "head", "hand_l", "foot_l"):
    tr = unreal.AnimPoseExtensions.get_bone_pose(ref, bn, unreal.AnimPoseSpaces.WORLD); print(bn, tr.translation, tr.scale3d if bn == "root" else "")
