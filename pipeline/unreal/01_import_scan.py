"""Import fig4's scan + conform target as static meshes and report where her face points."""
import unreal

SRC = r"E:\code\claude-ue5\claude_ue5\SourceArt\fig4"
JOBS = [
    (rf"{SRC}\fig4_scan_full.glb", "/Game/Fig4/Scan"),
    (rf"{SRC}\fig4_body_target_clean.glb", "/Game/Fig4/Conform"),
]

tasks = []
for f, dest in JOBS:
    t = unreal.AssetImportTask()
    t.filename = f; t.destination_path = dest
    t.automated = True; t.replace_existing = True; t.save = True
    tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
for t in tasks:
    print("IMPORTED", t.filename, "->", list(t.imported_object_paths))

mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
for t in tasks:
    for p in t.imported_object_paths:
        a = unreal.load_asset(p)
        if not isinstance(a, unreal.StaticMesh):
            continue
        b = a.get_bounding_box()
        print("MESH", p, "min", b.min, "max", b.max)
        verts, idx, *_ = mhs.get_mesh_data_for_conforming(a)
        # nose tip = the most forward vertex at nose height, in each horizontal direction
        top = b.max.z
        nose = [v for v in verts if top - 22 < v.z < top - 12]
        for axis in ("x", "y"):
            vals = [getattr(v, axis) for v in nose]
            print(f"  nose-band {axis}: min {min(vals):.1f} max {max(vals):.1f}  (verts {len(nose)})")
