"""Door leaves for BP_Door (it swings the Leaf component about its own origin): re-pivot UE-exported door meshes so the origin sits
on the hinge edge at floor level - leaf along +X from the hinge, centred in thickness (all cm, UE-exported FBX in, UE FBX out).
Blender: -b -P fcl_leaf_pivot.py -- fbx_in_dir out_dir name [name ...]   ->  out_dir/<name>_Leaf.fbx"""
import bpy, sys, os
from mathutils import Matrix
argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT, NAMES = argv[0], argv[1], argv[2:]
os.makedirs(OUT, exist_ok=True)
for name in NAMES:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
    bpy.ops.import_scene.fbx(filepath=os.path.join(SRC, name + ".fbx"))
    ob = next(o for o in sc.objects if o.type == 'MESH'); mw = ob.matrix_world.copy()
    for o in list(sc.objects):
        if o is not ob: bpy.data.objects.remove(o, do_unlink=True)
    ob.parent = None; ob.matrix_world = Matrix.Identity(4); ob.data.transform(mw)
    xs = [v.co.x for v in ob.data.vertices]; ys = [v.co.y for v in ob.data.vertices]; zs = [v.co.z for v in ob.data.vertices]
    ob.data.transform(Matrix.Translation((-min(xs), -(min(ys) + max(ys)) / 2, -min(zs))))
    ob.name = name + "_Leaf"
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, name + "_Leaf.fbx"), use_selection=True, object_types={'MESH'}, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_NONE', mesh_smooth_type='FACE', use_tspace=False, path_mode='STRIP', bake_anim=False)
    print(f"{name}: leaf {max(xs) - min(xs):.0f} wide x {max(zs) - min(zs):.0f} tall, {max(ys) - min(ys):.0f} thick")
