"""Export the built face + body skeletal meshes (whatever SKM_*_FaceMesh / _BodyMesh the build made)
to FBX. Args: out_dir"""
import sys, os, unreal
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
eal = unreal.EditorAssetLibrary
found = {}
for a in eal.list_assets("/Game/MetaHumans/Fig4", recursive=True):
    base = a.split(".")[-1]
    if "Final" not in base:
        continue
    if base.endswith("_FaceMesh"): found["fig4_mh_face"] = a.split(".")[0]
    if base.endswith("_BodyMesh"): found["fig4_mh_body"] = a.split(".")[0]
print("meshes:", found)
for name, path in found.items():
    mesh = unreal.load_asset(path)
    t = unreal.AssetExportTask()
    t.object = mesh; t.filename = os.path.join(out, name + ".fbx")
    t.automated = True; t.replace_identical = True; t.prompt = False
    opt = unreal.FbxExportOption()
    opt.level_of_detail = False; opt.collision = False; opt.export_morph_targets = False
    opt.vertex_color = False; opt.ascii = False
    t.options = opt
    ok = unreal.Exporter.run_asset_export_task(t)
    print("EXPORT", name, ok, os.path.getsize(t.filename) if os.path.exists(t.filename) else -1)
