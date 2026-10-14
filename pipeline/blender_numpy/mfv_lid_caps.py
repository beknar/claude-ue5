"""The underside of the container lids (crate_01/02, barrel_01/02 of castle_interactive).
mfv_interactive_build.py cuts each lid off its prop and closes the cut with a filled face. That face had no UVs of its
own on the prop's atlas material, so it showed whatever lies in the atlas's corner: a patch that looked like the
reflection of a table's edge, seen as soon as a lid stood open. Here the faces of the cut go to a material slot
'Interior' (the slot of the body's liner: plain wood, MI_wood in UE, see 320_castle_import.py) with planar UVs at the
liner's scale.
Reads <dir>/SM_<prop>_lid.fbx (cm, origin at the hinge: the cut is the plane z = 0, facing down) and writes it back.
Idempotent: a lid that has the slot already just gets its cut faces set again. mfv_interactive_build.py does the same
when it builds the lids from the pack.
Blender: -b -P mfv_lid_caps.py -- dir      then in the editor: 320_castle_import.py _lid"""
import bpy, bmesh, sys, os
from mathutils import Matrix
D = sys.argv[sys.argv.index("--") + 1]


def load_cm(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
    bpy.ops.import_scene.fbx(filepath=path)
    ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    mw = ob.matrix_world.copy()
    for o in list(bpy.context.scene.objects):
        if o is not ob: bpy.data.objects.remove(o, do_unlink=True)
    ob.parent = None; ob.matrix_world = Matrix.Identity(4); ob.data.transform(mw)
    return ob


for name in ("SM_crate_01", "SM_crate_02", "SM_barrel_01", "SM_barrel_02"):
    path = os.path.join(D, name + "_lid.fbx")
    ob = load_cm(path); ob.name = name + "_lid"
    co = [v.co for v in ob.data.vertices]
    lo = [min(c[k] for c in co) for k in range(3)]; hi = [max(c[k] for c in co) for k in range(3)]
    assert abs(lo[2]) < 0.2 and 2.0 < hi[2] < 12.0, (name, lo, hi)           # the cut at z 0, a lid a few cm thick: the units are right
    mat = bpy.data.materials.get("Interior") or bpy.data.materials.new("Interior")
    names = [m.name if m else "" for m in ob.data.materials]
    if "Interior" not in names: ob.data.materials.append(mat); names.append("Interior")
    mi = names.index("Interior")
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.normal_update()
    uvl = bm.loops.layers.uv.active or bm.loops.layers.uv.new()
    n = 0; area = 0.0
    for f in bm.faces:
        if f.normal.z < -0.9 and all(abs(v.co.z) < 0.05 for v in f.verts):
            f.material_index = mi; n += 1; area += f.calc_area()
            for l in f.loops: l[uvl].uv = (l.vert.co.x / 60.0, l.vert.co.y / 60.0)
    assert n > 0, name + ": no cut face found"
    bm.to_mesh(ob.data); bm.free()
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'MESH'}, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_NONE', mesh_smooth_type='FACE', use_tspace=False, path_mode='STRIP', bake_anim=False)
    print("LIDCAP %s: %d cut face(s), %.0f cm2 of %.0f x %.0f cm, slots %s, box (%.1f %.1f %.1f)..(%.1f %.1f %.1f)" % (
        name, n, area, hi[0] - lo[0], hi[1] - lo[1], names, lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]))
