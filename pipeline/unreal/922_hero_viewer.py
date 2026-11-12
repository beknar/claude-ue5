"""The heroes' animations for the three.js viewer (the user's of 2026-11-12: "put all of the heroes into the three.js viewer so their
animations can be viewed ... there should be a choice as to which hero to view"): each hero of the hero menu exported from the
game as glTF, her mesh once (her skeleton, skin weights and base colour: the exporter's simple material bake; its default bake
of proxy materials crashed the editor, an assertion in a shared pointer) and every clip on her skeleton (the asset registry's
AnimSequences whose skeleton is hers: locomotion, attacks, spells, the rider's and the swim clips), each without its mesh.
pipeline/blender_numpy/hero_viewer.py then merges each hero's clips onto her mesh and writes the page.
Writes <out>/<Hero>/mesh.glb, <out>/<Hero>/clips/<clip>.glb and <out>/<Hero>/clips.json (the clips' names, assets, lengths).
Args: <out dir> [hero,hero,...]"""
import json, os, sys, unreal
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "HeroViewer")
ONLY = [h for a in sys.argv[2:] for h in a.split(",") if h]
# (the hero menu's six and their rigs: hero_rigs.py, shared with 913 and 921)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hero_rigs, importlib
importlib.reload(hero_rigs)
HERO_RIG = hero_rigs.HERO_RIG
ar = unreal.AssetRegistryHelpers.get_asset_registry()
REPORT = []


def options(mesh):
    o = unreal.GLTFExportOptions()
    o.set_editor_property("bake_material_inputs", unreal.GLTFMaterialBakeMode.SIMPLE if mesh else unreal.GLTFMaterialBakeMode.DISABLED)
    o.set_editor_property("export_proxy_materials", False)
    o.set_editor_property("export_preview_mesh", bool(mesh))
    o.set_editor_property("export_level_sequences", False); o.set_editor_property("export_cameras", False); o.set_editor_property("export_lights", False)
    return o


def export(asset, path, mesh):
    r = unreal.GLTFExporter.export_to_gltf(asset, path, options(mesh), set())
    errs = list(r.get_editor_property("errors")) if r else ["no result"]
    return os.path.exists(path) and not errs, errs


all_seqs = ar.get_assets(unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "AnimSequence")]))
for hero, rig in HERO_RIG.items():
    if ONLY and hero not in ONLY: continue
    mesh = unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{rig}")
    if not mesh: REPORT.append(f"{hero}: no mesh SK_JRPG_{rig}"); continue
    sk = mesh.get_editor_property("skeleton").get_path_name()
    d = os.path.join(OUT, hero); os.makedirs(os.path.join(d, "clips"), exist_ok=True)
    ok, errs = export(mesh, os.path.join(d, "mesh.glb"), True)
    if not ok: REPORT.append(f"{hero}: the mesh did not export {errs}"); continue
    clips, failed = [], []
    for a in sorted(all_seqs, key=lambda x: str(x.package_name)):
        if sk not in str(a.get_tag_value("Skeleton")): continue
        seq = unreal.load_asset(str(a.package_name))
        if not seq: continue
        name = str(a.asset_name)
        # (two clips of one name in different folders (a pack's and our own): the file takes its folder too, or the second
        # overwrote the first (48 files for 50 clips))
        stem = name if name not in {c["file"] for c in clips} else f"{name}__{str(a.package_path).rsplit('/', 1)[-1]}"
        ok, errs = export(seq, os.path.join(d, "clips", stem + ".glb"), False)
        if ok: clips.append({"name": name, "file": stem, "folder": str(a.package_path), "asset": str(a.package_name), "length": round(seq.get_play_length(), 3)})
        else: failed.append((name, errs[:1]))
    json.dump({"hero": hero, "rig": rig, "mesh": mesh.get_path_name(), "clips": clips}, open(os.path.join(d, "clips.json"), "w"), indent=1)
    REPORT.append(f"{hero} ({rig}): {len(clips)} clips" + (f", failed {failed[:4]}" if failed else ""))
print("922 " + OUT + " | " + " | ".join(REPORT))
import gc; gc.collect()
