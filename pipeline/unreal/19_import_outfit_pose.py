"""Import the skinned outfit (skeletal mesh) and the standing pose (animation) onto the MetaHuman
body skeleton via Interchange (pipeline sub-objects are edited in place)."""
import unreal
body = unreal.load_asset("/Game/MetaHumans/Fig4/Body/SKM_MHC_Fig4_Final_BodyMesh")
skel = body.get_editor_property("skeleton")
print("body skeleton:", skel.get_path_name())

def setp(obj, name, val):
    try:
        obj.set_editor_property(name, val)
    except Exception as e:
        print("  (skip)", name, str(e)[:80])

def import_fbx(path, dest, mesh=True, anim=False):
    pipe = unreal.InterchangeGenericAssetsPipeline()
    setp(pipe.common_skeletal_meshes_and_animations_properties, "skeleton", skel)
    mp = pipe.mesh_pipeline
    setp(mp, "import_skeletal_meshes", mesh); setp(mp, "import_static_meshes", False)
    setp(mp, "create_physics_asset", False)
    setp(pipe.animation_pipeline, "import_animations", anim)
    setp(pipe.material_pipeline, "import_materials", False)
    if mesh:
        setp(pipe.common_meshes_properties, "force_all_mesh_as_type", unreal.InterchangeForceMeshType.IFMT_SKELETAL_MESH)
    else:
        setp(pipe.common_skeletal_meshes_and_animations_properties, "import_only_animations", True)
    src = unreal.InterchangeManager.create_source_data(path)
    params = unreal.ImportAssetParameters()
    params.is_automated = True
    params.replace_existing = True
    params.override_pipelines.append(unreal.SoftObjectPath(pipe.get_path_name()))
    im = unreal.InterchangeManager.get_interchange_manager_scripted()
    try:
        res = im.import_asset(dest, src, params)
    except RuntimeError as e:
        print("(non-fatal)", str(e)[:160]); res = None
    print("imported", path.split("\\")[-1], "->", res)

import sys
if "pose_only" not in sys.argv:
    import_fbx(r"E:\code\claude-ue5\claude_ue5\SourceArt\fig4\fig4_outfit_skinned.fbx", "/Game/Fig4/Outfit", mesh=True, anim=False)
import_fbx(r"E:\code\claude-ue5\claude_ue5\SourceArt\fig4\fig4_pose.fbx", "/Game/Fig4/Anim", mesh=False, anim=True)
for d in ("/Game/Fig4/Outfit", "/Game/Fig4/Anim"):
    for a in unreal.EditorAssetLibrary.list_assets(d, recursive=True):
        print(" ", a, unreal.EditorAssetLibrary.find_asset_data(a).asset_class_path.asset_name)
