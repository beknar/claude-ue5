"""Split fig4's scan by the labels from segment_fig4.py and export glbs at real scale
(feet on the ground, total height TOTAL_HEIGHT_M):
  fig4_scan_full.glb    whole scan (reference / Nanite statue)
  fig4_body_target.glb  scan minus hair and shoes  -> MetaHuman conform target
  fig4_hair_shell.glb   hair surface only           -> groom guide shape
  fig4_outfit.glb       dress + stockings + choker + shoes
Blender: -b -P export_parts.py -- src.glb work_dir out_dir"""
import bpy, bmesh, sys, numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
src, work, out = argv[0], argv[1], argv[2]
TOTAL_HEIGHT_M = 1.72
SKIN, HAIR, DRESS, STOCK, SHOE, CHOKER = range(6)
lab = np.load(f"{work}/labels.npy")


def load():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
    obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    # bake the import's Y-up -> Z-up rotation, scale to real height, feet at z = 0
    bpy.context.view_layer.objects.active = obj
    for o in bpy.context.scene.objects: o.select_set(o == obj)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    zs = np.array([v.co.z for v in obj.data.vertices])
    s = TOTAL_HEIGHT_M / (zs.max() - zs.min())
    obj.scale = (s, s, s); obj.location.z = -zs.min() * s
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=True)
    return obj


def keep_only(obj, keep_labels):
    me = obj.data
    bm = bmesh.new(); bm.from_mesh(me)
    keep = np.isin(lab, keep_labels)
    dead = [f for f in bm.faces if sum(keep[v.index] for v in f.verts) * 2 < len(f.verts)]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(me); bm.free()


def export(obj, name):
    obj.name = obj.data.name = name
    bpy.ops.export_scene.gltf(filepath=f"{out}/{name}.glb", export_format='GLB', use_selection=False,
                              export_yup=True, export_apply=True)
    print("EXPORTED", name, len(obj.data.vertices), "verts", len(obj.data.polygons), "faces")


if len(argv) > 3 and argv[3] == "outfit_parts":
    for lab_id, name in ((DRESS, "dress"), (STOCK, "stockings"), (SHOE, "shoes"), (CHOKER, "choker")):
        o = load(); keep_only(o, [lab_id]); export(o, f"fig4_outfit_{name}")
else:
    export(load(), "fig4_scan_full")
    o = load(); keep_only(o, [SKIN, DRESS, STOCK, CHOKER]); export(o, "fig4_body_target")
    o = load(); keep_only(o, [HAIR]); export(o, "fig4_hair_shell")
    o = load(); keep_only(o, [DRESS, STOCK, SHOE, CHOKER]); export(o, "fig4_outfit")
