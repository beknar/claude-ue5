"""Import an animated Tripo character built by blender_numpy/tripo_build.py (generalised 240_ff2_import.py):
skeletal mesh -> /Game/JRPG/Character/SK_JRPG_<CH>, its own clips (separate FBX, imported onto that skeleton) ->
/Game/JRPG/<CH>Anims/AS_<CH>_<Clip>, material M_JRPG_<CH> (base colour; normal / metal-rough if the GLB had them; two-sided).
Args: CH (e.g. Fem5)."""
import os, sys, json, importlib, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mat_lib as L
importlib.reload(L)
mel = L.mel; eal = L.eal
CH = sys.argv[1] if len(sys.argv) > 1 else "Fem5"
SRC = r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_" + CH.lower(); NAME = "SK_JRPG_" + CH
D = "/Game/JRPG"; A = f"{D}/{CH}Anims"
info = json.load(open(os.path.join(SRC, "build.json")))
t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, NAME + ".fbx"); t.destination_path = D + "/Character"
t.automated = True; t.replace_existing = True; t.save = True
o = unreal.FbxImportUI(); o.import_mesh = True; o.import_as_skeletal = True; o.import_animations = False; o.import_materials = False; o.import_textures = False
o.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH; t.options = o
L.at.import_asset_tasks([t])
kinds = {}
for p in t.imported_object_paths:
    a = unreal.load_asset(p)
    if a: kinds.setdefault(a.get_class().get_name(), []).append(p)
print({k: len(v) for k, v in kinds.items()})
sk = unreal.load_asset(kinds["SkeletalMesh"][0]); skel = sk.get_editor_property("skeleton")
o = unreal.FbxImportUI()
o.set_editor_property("import_mesh", False); o.set_editor_property("import_as_skeletal", True)
o.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
o.set_editor_property("skeleton", skel); o.set_editor_property("import_animations", True)
o.set_editor_property("import_materials", False); o.set_editor_property("import_textures", False)
ta = unreal.AssetImportTask(); ta.filename = os.path.join(SRC, NAME + "_Clips.fbx"); ta.destination_path = D + "/_ClipImport"
ta.automated = True; ta.replace_existing = True; ta.save = True; ta.options = o
L.at.import_asset_tasks([ta])
for p in ta.imported_object_paths:
    a = unreal.load_asset(p)
    if isinstance(a, unreal.AnimSequence):
        clip = p.split(".")[-1].split("Armature_A_")[-1]; dst = f"{A}/AS_{CH}_{clip}"
        if eal.does_asset_exist(dst): eal.delete_asset(dst)
        eal.rename_asset(p.split(".")[0], dst)
for p in eal.list_assets(D + "/_ClipImport", recursive=True): eal.delete_asset(p.split(".")[0])
eal.delete_directory(D + "/_ClipImport")
print("clips:", sorted((a.split(".")[-1], round(unreal.load_asset(a.split(".")[0]).get_play_length(), 2)) for a in eal.list_assets(A, recursive=False)))
T = {}
for role, kind in (("Color", "color"), ("Normal", "normal"), ("MetalRough", "linear")):
    f = os.path.join(SRC, f"T_{CH}_{role}.png")
    if os.path.exists(f):
        T[role] = L.import_texture(f, D + "/Textures", kind)
        if kind == "normal": T[role].set_editor_property("flip_green_channel", True); eal.save_loaded_asset(T[role])
path = f"{D}/Materials/M_JRPG_{CH}"
if eal.does_asset_exist(path): m = unreal.load_asset(path); mel.delete_all_material_expressions(m)
else: m = L.new_material(path)
m.set_editor_property("use_material_attributes", True); m.set_editor_property("two_sided", True)
S = unreal.MaterialSamplerType
mma = L.expr(m, unreal.MaterialExpressionMakeMaterialAttributes, -200, 0)
bc = L.tex_sample(m, T["Color"], -900, -300)
tint = L.vector(m, "AlbedoTint", (1.0, 1.0, 1.0), -900, -500)
alb = L.expr(m, unreal.MaterialExpressionMultiply, -600, -350); L.link(bc, "RGB", alb, "A"); L.link(tint, "", alb, "B"); L.link(alb, "", mma, "BaseColor")
if "MetalRough" in T:
    mr = L.tex_sample(m, T["MetalRough"], -900, 0, sampler=S.SAMPLERTYPE_MASKS); L.link(mr, "B", mma, "Metallic"); L.link(mr, "G", mma, "Roughness")
else:
    L.link(L.scalar(m, "Roughness", 0.6, -450, 50), "", mma, "Roughness")
if "Normal" in T:
    nm = L.tex_sample(m, T["Normal"], -900, 300, sampler=S.SAMPLERTYPE_NORMAL); L.link(nm, "RGB", mma, "Normal")
L.link(L.scalar(m, "Specular", 0.4, -450, 250), "", mma, "Specular")
mel.connect_material_property(mma, "", unreal.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
try: m.set_editor_property("used_with_skeletal_mesh", True)
except Exception: pass
L.finish(m)
sk.set_editor_property("materials", [unreal.SkeletalMaterial(material_interface=m, material_slot_name=str(s.get_editor_property("material_slot_name"))) for s in sk.get_editor_property("materials")])
sk.modify(); eal.save_loaded_asset(sk, only_if_is_dirty=False)
for p in eal.list_assets(D + "/Character", recursive=False):
    if "tripo_" in p.lower() and eal.does_asset_exist(p.split(".")[0]): print("delete placeholder", p.split("/")[-1], eal.delete_asset(p.split(".")[0]))
sk = unreal.load_asset(kinds["SkeletalMesh"][0])
print("slots", [(str(s.material_slot_name), s.material_interface.get_name() if s.material_interface else None) for s in sk.get_editor_property("materials")])
b = sk.get_bounds(); print("bounds", b.origin, b.box_extent)
ref = unreal.AnimPoseExtensions.get_reference_pose(skel)
for bn in ("root", "pelvis", "head", "foot_l", "ball_l"):
    tr = unreal.AnimPoseExtensions.get_bone_pose(ref, bn, unreal.AnimPoseSpaces.WORLD); print(bn, [round(v, 1) for v in (tr.translation.x, tr.translation.y, tr.translation.z)])
