"""Fantasy Castle shell buildings -> walk-in versions. Per building (UE-exported FBX, cm):
  1. slice the shell at floor + 120 cm, rasterise the cut (5 cm cells), flood-fill from outside: the rest is the interior
  2. largest inscribed axis-aligned rectangle of the interior (inset 15 cm) = the room
  3. doorway (160 x 260) through the wall on the requested side, centred on the room, boolean-cut -> <name>_open.fbx
  4. ceiling: ray up from the room centre
Spec JSON: {name: {"floor": z_local, "side": "+x"|"-x"|"+y"|"-y"}} (UE local). Writes <out>/castle_rooms_geo.json (UE local).
Blender: -b -P fcl_castle_rooms.py -- spec.json fbx_in_dir out_dir"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
argv = sys.argv[sys.argv.index("--") + 1:]
SPEC, SRC, OUT = json.load(open(argv[0])), argv[1], argv[2]
os.makedirs(OUT, exist_ok=True)
CELL, DW, DH = 5.0, 160.0, 260.0
res = {}
def load(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
    bpy.ops.import_scene.fbx(filepath=os.path.join(SRC, name + ".fbx"))
    ob = next(o for o in sc.objects if o.type == 'MESH'); mw = ob.matrix_world.copy()
    for o in list(sc.objects):
        if o is not ob: bpy.data.objects.remove(o, do_unlink=True)
    ob.parent = None; ob.matrix_world = Matrix.Identity(4); ob.data.transform(mw); return ob
def section(ob, z):
    """segments of the mesh cut by the plane z (Blender coords)"""
    segs = []; me = ob.data; V = me.vertices
    for p in me.polygons:
        pts = [V[i].co for i in p.vertices]; cut = []
        for a, b in zip(pts, pts[1:] + pts[:1]):
            if (a.z - z) * (b.z - z) < 0:
                t = (z - a.z) / (b.z - a.z); cut.append((a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t))
        if len(cut) >= 2: segs.append((cut[0], cut[1]))
    return segs
def largest_rect(mask):
    """largest all-True axis-aligned rectangle in a 2D bool array -> (i0, i1, j0, j1) inclusive (rows i, cols j)"""
    best = (0, None); h = np.zeros(mask.shape[1], int)
    for i in range(mask.shape[0]):
        h = np.where(mask[i], h + 1, 0); st = []
        for j in range(len(h) + 1):
            cur = h[j] if j < len(h) else 0; start = j
            while st and st[-1][1] >= cur:
                s, hh = st.pop(); area = hh * (j - s)
                if area > best[0]: best = (area, (i - hh + 1, i, s, j - 1))
                start = s
            st.append((start, cur))
    return best[1]
for name, d in SPEC.items():
    ob = load(name)
    vs = np.array([v.co[:] for v in ob.data.vertices]); lo, hi = vs.min(0), vs.max(0)
    floor = d["floor"]; zc = floor + 120.0
    segs = section(ob, zc)
    nx, ny = int((hi[0] - lo[0]) / CELL) + 3, int((hi[1] - lo[1]) / CELL) + 3
    wall = np.zeros((ny, nx), bool)
    for (ax, ay), (bx, by) in segs:                                  # rasterise every cut segment
        n = int(max(abs(bx - ax), abs(by - ay)) / (CELL * 0.5)) + 1
        for k in range(n + 1):
            x = ax + (bx - ax) * k / n; y = ay + (by - ay) * k / n
            wall[int((y - lo[1]) / CELL) + 1, int((x - lo[0]) / CELL) + 1] = True
    outside = np.zeros_like(wall); st = [(0, 0)]; outside[0, 0] = True
    while st:
        i, j = st.pop()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = i + di, j + dj
            if 0 <= a < ny and 0 <= b < nx and not wall[a, b] and not outside[a, b]: outside[a, b] = True; st.append((a, b))
    inside = ~outside & ~wall
    # erode by 3 cells (15 cm) so furniture / lining keep off the shell
    er = inside.copy()
    for _ in range(3):
        e2 = er.copy(); e2[1:] &= er[:-1]; e2[:-1] &= er[1:]; e2[:, 1:] &= er[:, :-1]; e2[:, :-1] &= er[:, 1:]; er = e2
    r = largest_rect(er)
    if not r: print(name, "no interior"); continue
    i0, i1, j0, j1 = r
    bx0, bx1 = lo[0] + (j0 - 1) * CELL, lo[0] + (j1 - 1 + 1) * CELL
    by0, by1 = lo[1] + (i0 - 1) * CELL, lo[1] + (i1 - 1 + 1) * CELL
    # UE local: x same, y = -blender y
    ux0, ux1, uy0, uy1 = bx0, bx1, -by1, -by0
    side = d["side"]; cxu, cyu = (ux0 + ux1) / 2, (uy0 + uy1) / 2
    if side in ("+x", "-x"): wall_x = ux1 if side == "+x" else ux0; door_u = (wall_x, cyu); normal = (1 if side == "+x" else -1, 0)
    else: wall_y = uy1 if side == "+y" else uy0; door_u = (cxu, wall_y); normal = (0, 1 if side == "+y" else -1)
    # outer face along the normal from the room edge (ray in Blender coords)
    bvh = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
    o_b = Vector((door_u[0] - normal[0] * 10, -(door_u[1] - normal[1] * 10), zc)); dir_b = Vector((normal[0], -normal[1], 0))
    far = o_b + dir_b * 2000; hit = bvh.ray_cast(far, -dir_b)      # from outside back in: the outer face
    thick = ((far - hit[0]).length if hit[0] else 2000.0)
    thick = 2000.0 - thick + 10 if hit[0] else 60.0
    up = bvh.ray_cast(Vector((cxu, -cyu, zc)), Vector((0, 0, 1)))
    ceiling = (up[0].z if up[0] else hi[2])
    # doorway cut
    bpy.ops.mesh.primitive_cube_add(size=1.0); cut = bpy.context.active_object
    depth = thick + 160.0
    if side in ("+x", "-x"): cut.scale = (depth, DW, DH); cut.location = (door_u[0] + normal[0] * (depth / 2 - 40), -door_u[1], floor + DH / 2 - 5)
    else: cut.scale = (DW, depth, DH); cut.location = (door_u[0], -(door_u[1] + normal[1] * (depth / 2 - 40)), floor + DH / 2 - 5)
    # and hollow out the whole room volume: some shells are double-walled / partly solid inside, and the room gets its own lining
    hr = min(d.get("h", 480.0), ceiling - floor - 30.0)
    bpy.ops.mesh.primitive_cube_add(size=1.0); room = bpy.context.active_object
    room.scale = (ux1 - ux0 - 2, uy1 - uy0 - 2, hr + 10); room.location = ((ux0 + ux1) / 2, -(uy0 + uy1) / 2, floor - 5 + (hr + 10) / 2)
    bpy.context.view_layer.update()
    m2 = ob.modifiers.new("roomvol", 'BOOLEAN'); m2.operation = 'DIFFERENCE'; m2.object = room; m2.solver = 'EXACT'
    bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier=m2.name)
    bpy.data.objects.remove(room, do_unlink=True)
    bpy.context.view_layer.update()
    mod = ob.modifiers.new("doorway", 'BOOLEAN'); mod.operation = 'DIFFERENCE'; mod.object = cut; mod.solver = 'EXACT'
    bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cut, do_unlink=True); ob.name = name + "_open"
    bpy.ops.object.select_all(action='DESELECT'); ob.select_set(True)
    bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, name + "_open.fbx"), use_selection=True, object_types={'MESH'}, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_NONE', mesh_smooth_type='FACE', use_tspace=False, path_mode='STRIP', bake_anim=False)
    res[name] = {"room": [round(ux0, 1), round(ux1, 1), round(uy0, 1), round(uy1, 1)], "floor": floor, "ceiling": round(ceiling, 1),
                 "door": [round(door_u[0], 1), round(door_u[1], 1)], "normal": list(normal), "wall": round(thick, 1), "side": side}
    print(name, res[name], "interior cells", int(inside.sum()))
json.dump(res, open(os.path.join(OUT, "castle_rooms_geo.json"), "w"), indent=1)
