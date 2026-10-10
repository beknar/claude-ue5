"""Import the Meshy biped FBX (skeletal mesh + skeleton + 18 animations) and its textures into /Game/Meshy."""
import os, sys, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, mat_lib as L
importlib.reload(L)
SRC = r"E:\code\claude-ue5\claude_ue5\SourceArt\meshy_biped"
D = "/Game/Meshy"
t = unreal.AssetImportTask()
t.filename = os.path.join(SRC, "SK_Meshy_Biped.fbx"); t.destination_path = D + "/Character"
t.automated = True; t.replace_existing = True; t.save = True
L.at.import_asset_tasks([t])
paths = list(t.imported_object_paths)
kinds = {}
for p in paths:
    a = unreal.load_asset(p)
    kinds.setdefault(a.get_class().get_name(), []).append(p)
for k, v in kinds.items(): print(k, len(v), v[:3])
# textures
for name, kind in (("texture_0", "color"), ("texture_0_normal", "normal"), ("texture_0_metallic-texture_0_roughness", "linear")):
    tex = L.import_texture(os.path.join(SRC, name + ".png"), D + "/Textures", kind)
    print("tex", tex.get_path_name())
sk = [unreal.load_asset(p) for p in kinds.get("SkeletalMesh", [])]
if sk:
    m = sk[0]
    b = m.get_bounds()
    print("bounds origin", b.origin, "extent", b.box_extent)
    skel = m.get_editor_property("skeleton")
    ref = unreal.AnimPoseExtensions.get_reference_pose(skel)
    names = [str(n) for n in unreal.AnimPoseExtensions.get_bone_names(ref)]
    print("bones", len(names), names[:6])
    for bn in ("root", "pelvis", "head", "ball_l"):
        print(bn, unreal.AnimPoseExtensions.get_bone_pose(ref, bn, unreal.AnimPoseSpaces.WORLD).translation)
