"""Fantasy Castle buildings are closed single shells: cut a doorway through one wall so an interior can be built inside.
Spec JSON (from pipeline/unreal/410_fcl_castle_survey.py): {name: {"door": [x, y] (UE local, on the outer wall face),
"normal": [nx, ny] (UE local outward normal), "floor": z (UE local), "w": width, "h": height}}.
The cut is a box through the wall (1.2 m deep, centred on the face); its new faces take the nearest existing material.
Blender: -b -P fcl_castle_open.py -- spec.json fbx_in_dir out_dir   ->  out_dir/<name>_open.fbx"""
import bpy, sys, os, json
from mathutils import Matrix, Vector
argv = sys.argv[sys.argv.index("--") + 1:]
SPEC, SRC, OUT = json.load(open(argv[0])), argv[1], argv[2]
os.makedirs(OUT, exist_ok=True)
for name, d in SPEC.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
    bpy.ops.import_scene.fbx(filepath=os.path.join(SRC, name + ".fbx"))
    ob = next(o for o in sc.objects if o.type == 'MESH'); mw = ob.matrix_world.copy()
    for o in list(sc.objects):
        if o is not ob: bpy.data.objects.remove(o, do_unlink=True)
    ob.parent = None; ob.matrix_world = Matrix.Identity(4); ob.data.transform(mw)
    # UE local (x, y, z) -> Blender (x, -y, z)
    cx, cy = d["door"][0], -d["door"][1]; nx, ny = d["normal"][0], -d["normal"][1]
    w, h, fz = d["w"], d["h"], d["floor"]
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    cut = bpy.context.active_object
    cut.scale = (120.0 if abs(nx) > abs(ny) else w, w if abs(nx) > abs(ny) else 120.0, h)
    cut.location = (cx, cy, fz + h / 2 - 5)                       # 5 cm below the floor so no sill remains
    bpy.context.view_layer.update()
    mod = ob.modifiers.new("doorway", 'BOOLEAN'); mod.operation = 'DIFFERENCE'; mod.object = cut; mod.solver = 'EXACT'
    bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cut, do_unlink=True)
    ob.name = name + "_open"
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, name + "_open.fbx"), use_selection=True, object_types={'MESH'}, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_NONE', mesh_smooth_type='FACE', use_tspace=False, path_mode='STRIP', bake_anim=False)
    print(f"{name}: doorway {w:.0f}x{h:.0f} at ({d['door'][0]:.0f}, {d['door'][1]:.0f}) floor {fz:.0f}, faces {len(ob.data.polygons)}")
