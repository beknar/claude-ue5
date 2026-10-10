"""Medieval Fantasy Village -> interactive pieces (all cm, UE-exported FBX in, UE-ready FBX out):
- houses: door leaves (5 planks + hinges/straps/handle) cut out -> SM_<house>_open.fbx, each leaf -> SM_<house>_door<i>.fbx with its
  pivot on the hinge axis (bottom).  JSON: pivot, leaf direction (hinge -> free edge), door wall side.
- containers: crate_01/02, barrel_01/02 -> SM_<prop>_body.fbx (open top + inner liner + rim, liner/rim on slot 'Interior') and
  SM_<prop>_lid.fbx (pivot on the back hinge edge); barrels also SM_<prop>_liquid.fbx (liquid disc).
- splash: SM_splash_crown.fbx (petal crown + droplets), SM_splash_ring.fbx (ripple ring).
Coordinates in the JSON are Blender's (UE = (x, -y, z)).
Blender: -b -P mfv_interactive_build.py -- fbx_in_dir out_dir"""
import bpy, bmesh, sys, os, json, math, random
from mathutils import Vector, Matrix
argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = argv[0], argv[1]
os.makedirs(OUT, exist_ok=True)
INFO = {"houses": {}, "containers": {}}

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
def load_cm(name):
    """import a UE-exported FBX and bake it to 1 BU = 1 cm, identity transform"""
    reset()
    bpy.ops.import_scene.fbx(filepath=os.path.join(SRC, name + ".fbx"))
    ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    mw = ob.matrix_world.copy()                      # includes the FBX root's scale: capture before unparenting
    for o in list(bpy.context.scene.objects):
        if o is not ob: bpy.data.objects.remove(o, do_unlink=True)
    ob.parent = None; ob.matrix_world = Matrix.Identity(4)
    ob.data.transform(mw)                            # scene is in cm (scale_length 0.01) so the importer already gives cm
    zs = [v.co.z for v in ob.data.vertices]; print(f"  [{name}] height {max(zs) - min(zs):.1f} cm")
    ob.name = name; return ob
def export(objs, path):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'MESH'}, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_NONE', mesh_smooth_type='FACE', use_tspace=False, path_mode='STRIP', bake_anim=False)
def parts(ob):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    seen = set(); out = []
    for f in bm.faces:
        if f.index in seen: continue
        st = [f]; comp = []; seen.add(f.index)
        while st:
            g = st.pop(); comp.append(g.index)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen: seen.add(h.index); st.append(h)
        P = [v.co for v in {v for i in comp for v in bm.faces[i].verts}]
        a = Vector((min(p.x for p in P), min(p.y for p in P), min(p.z for p in P))); b = Vector((max(p.x for p in P), max(p.y for p in P), max(p.z for p in P)))
        out.append({"faces": comp, "min": a, "max": b})
    bm.free(); return out
def split_faces(ob, keep_idx, name, remove=True):
    """new object with only faces keep_idx (copy of ob); removes them from ob unless remove=False
    (face indices refer to ob's current mesh, so extract several pieces with remove=False)"""
    new = ob.copy(); new.data = ob.data.copy(); new.name = name; bpy.context.scene.collection.objects.link(new)
    keep = set(keep_idx)
    for target, inv in (((new, False), (ob, True)) if remove else ((new, False),)):
        bm = bmesh.new(); bm.from_mesh(target.data); bm.faces.ensure_lookup_table()
        dele = [f for f in bm.faces if (f.index in keep) == inv]
        bmesh.ops.delete(bm, geom=dele, context='FACES'); bm.to_mesh(target.data); bm.free()
    return new
def is_plank(p):
    e = p["max"] - p["min"]; s = sorted((e.x, e.y))
    return 220 < e.z < 245 and 6 <= s[0] <= 13 and 24 <= s[1] <= 33

# ---------------- houses ----------------
for hname in ("SM_house_01", "SM_house_02", "SM_house_03", "SM_house_04", "SM_house_05"):
    ob = load_cm(hname); P = parts(ob)
    planks = [p for p in P if is_plank(p)]
    groups = []
    for p in sorted(planks, key=lambda p: (p["min"].x, p["min"].y)):
        ax = (p["max"].x - p["min"].x) > (p["max"].y - p["min"].y)     # plank long side along x -> door spans x
        for g in groups:
            if g["along_x"] == ax and abs(g["thin"] - (p["min"].y if ax else p["min"].x)) < 5 and \
               (p["min"].x if ax else p["min"].y) - (g["max"].x if ax else g["max"].y) < 6:
                g["min"] = Vector(map(min, g["min"], p["min"])); g["max"] = Vector(map(max, g["max"], p["max"])); g["n"] += 1; break
        else:
            groups.append({"along_x": ax, "thin": p["min"].y if ax else p["min"].x, "min": p["min"].copy(), "max": p["max"].copy(), "n": 1})
    doors = []
    for g in [g for g in groups if g["n"] >= 4]:
        lo, hi = g["min"].copy(), g["max"].copy(); A, T = (0, 1) if g["along_x"] else (1, 0)     # along axis, thin axis
        lo[A] -= 3; hi[A] += 3; lo[T] -= 14; hi[T] += 14; lo.z -= 2; hi.z += 3
        inside = [p for p in P if all(lo[k] <= p["min"][k] and p["max"][k] <= hi[k] for k in range(3))]
        pins = [p for p in inside if not is_plank(p) and 14 < (p["max"].z - p["min"].z) < 25 and max(p["max"][A] - p["min"][A], p["max"][T] - p["min"][T]) < 12]
        pin_a = sum((p["min"][A] + p["max"][A]) / 2 for p in pins) / max(len(pins), 1)
        hinge_at_min = abs(pin_a - g["min"][A]) < abs(pin_a - g["max"][A])
        pivot = Vector((0, 0, g["min"].z)); pivot[A] = g["min"][A] if hinge_at_min else g["max"][A]; pivot[T] = (g["min"][T] + g["max"][T]) / 2
        leaf_dir = [0.0, 0.0, 0.0]; leaf_dir[A] = 1.0 if hinge_at_min else -1.0
        faces = [i for p in inside for i in p["faces"]]
        doors.append({"pivot": list(pivot), "leaf_dir": leaf_dir, "thin_axis": "xy"[T], "width": g["max"][A] - g["min"][A],
                      "height": g["max"].z - g["min"].z, "faces": faces, "n_parts": len(inside), "pins": len(pins)})
    leaves = []
    for i, d in enumerate(doors):
        leaf = split_faces(ob, d.pop("faces"), f"{hname}_door{i}", remove=False)
        leaf.data.transform(Matrix.Translation(-Vector(d["pivot"])))
        export([leaf], os.path.join(OUT, f"{hname}_door{i}.fbx")); leaves.append(leaf)
        bpy.data.objects.remove(leaf, do_unlink=True)
    # faces were removed from ob progressively: split_faces uses face indices of the ORIGINAL mesh, so redo on a fresh copy
    ob = load_cm(hname); P2 = parts(ob)
    all_leaf_faces = []
    for d in doors:
        piv = Vector(d["pivot"]); A = 0 if d["thin_axis"] == "y" else 1; T = 1 - A
        lo = piv.copy(); hi = piv.copy(); s = d["leaf_dir"][A]
        lo[A] = min(piv[A], piv[A] + s * d["width"]) - 3; hi[A] = max(piv[A], piv[A] + s * d["width"]) + 3
        lo[T] -= 4.5 + 14; hi[T] += 4.5 + 14; lo.z -= 2; hi.z = piv.z + d["height"] + 3
        all_leaf_faces += [i for p in P2 if all(lo[k] <= p["min"][k] and p["max"][k] <= hi[k] for k in range(3)) for i in p["faces"]]
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    rm = set(all_leaf_faces); bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index in rm], context='FACES')
    # the shell has a continuous interior wall behind each door: slice it along the opening and delete the inside pieces
    cut_total = 0
    for d in doors:
        piv = Vector(d["pivot"]); A = 0 if d["thin_axis"] == "y" else 1; T = 1 - A; s = d["leaf_dir"][A]
        a0, a1 = sorted((piv[A] + 1.0 * s, piv[A] + s * (d["width"] - 1.0)))
        t0, t1 = piv[T] - 70, piv[T] + 70; z0, z1 = piv.z - 1, piv.z + d["height"] - 1
        def in_prism(c): return a0 < c[A] < a1 and t0 < c[T] < t1 and z0 < c.z < z1
        def touches(f):
            vs = [v.co for v in f.verts]
            return (min(v[A] for v in vs) < a1 and max(v[A] for v in vs) > a0 and min(v[T] for v in vs) < t1 and max(v[T] for v in vs) > t0
                    and min(v.z for v in vs) < z1 and max(v.z for v in vs) > z0)
        for co, no in (((a0 if A == 0 else 0, a0 if A == 1 else 0, 0), (1 if A == 0 else 0, 1 if A == 1 else 0, 0)),
                       ((a1 if A == 0 else 0, a1 if A == 1 else 0, 0), (1 if A == 0 else 0, 1 if A == 1 else 0, 0)),
                       ((0, 0, z1), (0, 0, 1))):
            sub = [f for f in bm.faces if touches(f)]
            g = list({e for f in sub for e in f.edges}) + list({v for f in sub for v in f.verts}) + sub
            bmesh.ops.bisect_plane(bm, geom=g, plane_co=co, plane_no=no)
        bm.faces.ensure_lookup_table(); bm.normal_update()
        dele = [f for f in bm.faces if in_prism(f.calc_center_median()) and abs(f.normal[T]) > 0.7]
        cut_total += len(dele)
        bmesh.ops.delete(bm, geom=dele, context='FACES')
    print(f"  {hname}: doorway wall faces removed {cut_total}")
    bm.to_mesh(ob.data); bm.free()
    export([ob], os.path.join(OUT, f"{hname}_open.fbx"))
    INFO["houses"][hname] = doors
    print(hname, "doors", [(round(d["pivot"][0]), round(d["pivot"][1]), d["thin_axis"], d["leaf_dir"], d["n_parts"], d["pins"]) for d in doors], "removed faces", len(rm))

# ---------------- containers ----------------
def box_uv(bm, uv_layer, scale=100.0):
    for f in bm.faces:
        n = f.normal; ax = max(range(3), key=lambda k: abs(n[k]))
        for l in f.loops:
            c = l.vert.co; u, v = [(c.y, c.z), (c.x, c.z), (c.x, c.y)][ax]
            l[uv_layer].uv = (u / scale, v / scale)
def add_shell(ob, kind, cut_z, inset, floor_z):
    """liner (inward-facing walls + floor) and rim at cut_z, material slot 'Interior'"""
    mat = bpy.data.materials.get("Interior") or bpy.data.materials.new("Interior")
    ob.data.materials.append(mat); mi = len(ob.data.materials) - 1
    bm = bmesh.new(); bm.from_mesh(ob.data); uvl = bm.loops.layers.uv.active or bm.loops.layers.uv.new()
    if kind == "box":
        xs = [v.co.x for v in bm.verts]; ys = [v.co.y for v in bm.verts]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        outer = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        inner = [(x0 + inset, y0 + inset), (x1 - inset, y0 + inset), (x1 - inset, y1 - inset), (x0 + inset, y1 - inset)]
    else:
        ring = [v.co for v in bm.verts if abs(v.co.z - cut_z) < 0.6]
        R = max(math.hypot(c.x, c.y) for c in ring) if ring else 25.0
        N = 28
        outer = [(R * math.cos(2 * math.pi * k / N), R * math.sin(2 * math.pi * k / N)) for k in range(N)]
        inner = [((R - inset) * math.cos(2 * math.pi * k / N), (R - inset) * math.sin(2 * math.pi * k / N)) for k in range(N)]
    n = len(inner); new = []
    vi_top = [bm.verts.new((x, y, cut_z)) for x, y in inner]; vi_bot = [bm.verts.new((x, y, floor_z)) for x, y in inner]
    vo_top = [bm.verts.new((x, y, cut_z)) for x, y in outer]
    for k in range(n):
        j = (k + 1) % n
        new.append(bm.faces.new((vi_top[k], vi_bot[k], vi_bot[j], vi_top[j])))        # liner wall, facing inward
        new.append(bm.faces.new((vo_top[k], vi_top[k], vi_top[j], vo_top[j])))        # rim
    new.append(bm.faces.new(list(reversed(vi_bot))) if kind == "box" else bm.faces.new(vi_bot[::-1]))     # floor (up)
    for f in new: f.material_index = mi
    bm.normal_update()
    # make sure liner faces point inward / rim + floor up
    for f in new:
        c = f.calc_center_median()
        if abs(f.normal.z) < 0.5 and f.normal.dot(Vector((c.x, c.y, 0))) > 0: f.normal_flip()
        if abs(f.normal.z) >= 0.5 and f.normal.z < 0: f.normal_flip()
    for f in new:
        nz = f.normal; ax = max(range(3), key=lambda k: abs(nz[k]))
        for l in f.loops:
            c = l.vert.co; u, v = [(c.y, c.z), (c.x, c.z), (c.x, c.y)][ax]; l[uvl].uv = (u / 60.0, v / 60.0)
    bm.to_mesh(ob.data); bm.free()
    return (outer, inner)
for cname, kind, lid_t, inset in (("SM_crate_01", "box", 6.0, 3.0), ("SM_crate_02", "box", 6.0, 3.0),
                                  ("SM_barrel_01", "cyl", 4.0, 3.0), ("SM_barrel_02", "cyl", 4.0, 2.5)):
    ob = load_cm(cname)
    zs = [v.co.z for v in ob.data.vertices]; top = max(zs); cut = top - lid_t
    lid = ob.copy(); lid.data = ob.data.copy(); lid.name = cname + "_lid"; bpy.context.scene.collection.objects.link(lid)
    for target, keep_above in ((ob, False), (lid, True)):
        bm = bmesh.new(); bm.from_mesh(target.data)
        g = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=g, plane_co=(0, 0, cut), plane_no=(0, 0, 1), clear_inner=keep_above, clear_outer=not keep_above)
        if keep_above:
            edges = [e for e in bm.edges if all(abs(v.co.z - cut) < 0.01 for v in e.verts) and len(e.link_faces) < 2]
            try: bmesh.ops.holes_fill(bm, edges=edges, sides=0)
            except Exception as ex: print("lid fill", ex)
        bm.to_mesh(target.data); bm.free()
    outer, inner = add_shell(ob, kind, cut, inset, 4.0 if kind == "box" else 7.0)
    ys = [v.co.y for v in lid.data.vertices]
    hinge = Vector((0.0, max(ys), cut))                          # back edge (Blender +y = UE -y)
    lid.data.transform(Matrix.Translation(-hinge))
    export([ob], os.path.join(OUT, cname + "_body.fbx")); export([lid], os.path.join(OUT, cname + "_lid.fbx"))
    rec = {"kind": kind, "cut_z": cut, "top": top, "hinge": list(hinge), "inner": inner[:4] if kind == "box" else [abs(inner[0][0])]}
    if kind == "cyl":
        r = abs(inner[0][0]) - 0.6; reset()
        bpy.ops.mesh.primitive_circle_add(vertices=28, radius=r, fill_type='NGON', location=(0, 0, cut - 14))
        liq = bpy.context.active_object; liq.name = cname + "_liquid"
        export([liq], os.path.join(OUT, cname + "_liquid.fbx")); rec["liquid_z"] = cut - 14
    INFO["containers"][cname] = rec
    print(cname, "cut", round(cut, 1), "hinge", tuple(round(v, 1) for v in hinge))

# ---------------- splash ----------------
reset(); random.seed(7)
bm = bmesh.new(); uvl = bm.loops.layers.uv.new()
N = 18; rings = []
for j, (r, z) in enumerate(((10, 0), (13, 7), (16, 14))):
    rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / N), r * math.sin(2 * math.pi * k / N), z)) for k in range(N)])
tips = []
for k in range(N):
    a = 2 * math.pi * (k + 0.5) / N; h = 22 + 6 * random.random()
    tips.append(bm.verts.new((19 * math.cos(a), 19 * math.sin(a), h)))
for j in range(2):
    for k in range(N):
        f = bm.faces.new((rings[j][k], rings[j][(k + 1) % N], rings[j + 1][(k + 1) % N], rings[j + 1][k]))
for k in range(N): bm.faces.new((rings[2][k], rings[2][(k + 1) % N], tips[k]))
for k in range(9):                                   # droplets
    a = random.uniform(0, 2 * math.pi); r = random.uniform(8, 22); z = random.uniform(18, 36); s = random.uniform(0.9, 1.6)
    ret = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=s, matrix=Matrix.Translation((r * math.cos(a), r * math.sin(a), z)))
for f in bm.faces:
    for l in f.loops: l[uvl].uv = (l.vert.co.x / 40 + 0.5, l.vert.co.z / 40)
me = bpy.data.meshes.new("SM_splash_crown"); bm.to_mesh(me); bm.free()
crown = bpy.data.objects.new("SM_splash_crown", me); bpy.context.scene.collection.objects.link(crown)
crown.data.materials.append(bpy.data.materials.new("Splash"))
export([crown], os.path.join(OUT, "SM_splash_crown.fbx"))
reset()
bm = bmesh.new(); uvl = bm.loops.layers.uv.new(); N = 40
vin = [bm.verts.new((17 * math.cos(2 * math.pi * k / N), 17 * math.sin(2 * math.pi * k / N), 0.4)) for k in range(N)]
vout = [bm.verts.new((20 * math.cos(2 * math.pi * k / N), 20 * math.sin(2 * math.pi * k / N), 0.4)) for k in range(N)]
for k in range(N):
    f = bm.faces.new((vin[k], vout[k], vout[(k + 1) % N], vin[(k + 1) % N]))
    for l in f.loops: l[uvl].uv = (k / N, 1.0 if l.vert in vout else 0.0)
me = bpy.data.meshes.new("SM_splash_ring"); bm.to_mesh(me); bm.free()
for p in me.polygons:
    if p.normal.z < 0: p.flip()
ring = bpy.data.objects.new("SM_splash_ring", me); bpy.context.scene.collection.objects.link(ring)
ring.data.materials.append(bpy.data.materials.new("Splash"))
export([ring], os.path.join(OUT, "SM_splash_ring.fbx"))
json.dump(INFO, open(os.path.join(OUT, "interactive.json"), "w"), indent=1)
print("BUILD DONE")
