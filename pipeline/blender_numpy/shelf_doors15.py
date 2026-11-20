"""The list of 2026-11-20 (item 7, "bookshelf doors should open when searched"): two door leaves for the Gothic pack's bookshelf
(SM_Prop_Cabinet_D, the castle's Bookshelf and Bookshelf2 pieces). The cabinet has no doors: its back panel (a board 8 cm thick, 144
cm wide and 266 cm tall) faced the room because the pieces' Adjust turned it the wrong way (934 shelves turns it round). The leaves
are that panel's own mesh (its wood, its UVs on the cabinet's texture), cut down the middle, each half narrowed to the room between
the front pillars (66 cm) and laid in the piece's frame: the cabinet's front +X (its open side, toward the room), its middle at y 0,
the leaf's face across X. Each leaf's origin is its hinge (on the floor's height), the leaf running along +Y from it (the right
leaf, hinged at -Y) or -Y (the left, hinged at +Y); closed it stands FRONT_X in front of the piece's middle.

Run:  blender -b -P shelf_doors15.py -- <cabinet_d.fbx> <out dir>
Writes <out dir>/SM_RD_ShelfDoorL15.fbx, SM_RD_ShelfDoorR15.fbx and shelf_doors15.json (the hinge places and the leaf's size, cm, in
the piece's frame, for 934)."""
import bpy, bmesh, json, os, sys
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = argv[0], argv[1]
os.makedirs(OUT, exist_ok=True)
# (the piece's Adjust after 934's turn: the mesh's +Y (its open front) to +X; its middle (x 8.42 cm off in the mesh's y) to 0)
ADJ_X, ADJ_Y = -8.4168, -0.0575
HINGE = 66.0          # (cm from the middle: the front pillars' inner faces)
FRONT_Y_MESH = 27.0    # (cm, the mesh's y the closed leaves stand at: in front of the shelves' boards (y 23), behind the pillars' fronts)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC)
lod0 = next(o for o in bpy.context.scene.objects if o.type == "MESH" and o.name.endswith("LOD0"))
for o in list(bpy.context.scene.objects):
    if o is not lod0: bpy.data.objects.remove(o, do_unlink=True)
bpy.context.view_layer.objects.active = lod0
lod0.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
me = lod0.data

# (the source mesh's units are the engine's cm once its parent (the FBX's 0.01 empty) is gone: x, -y, z)
def ue(v): return Vector((v.x, -v.y, v.z))

# ---- the back panel: the loose part whose box is x +-72, the engine's y -21..-13, z 27..293
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
seen = set(); panel = None
for f in bm.faces:
    if f.index in seen: continue
    st = [f]; isl = []; seen.add(f.index)
    while st:
        x = st.pop(); isl.append(x)
        for e in x.edges:
            for g in e.link_faces:
                if g.index not in seen: seen.add(g.index); st.append(g)
    vs = [ue(v.co) for ff in isl for v in ff.verts]
    lo = Vector((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs))); hi = Vector((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    if hi.x - lo.x > 130 and hi.z - lo.z > 240 and hi.y - lo.y < 12 and lo.y < -10: panel = (set(ff.index for ff in isl), lo, hi)
assert panel, "no back panel found in the cabinet"
keep, plo, phi = panel
print("SHELF15 panel", [round(c, 1) for c in plo], [round(c, 1) for c in phi])
for f in [f for f in bm.faces if f.index not in keep]: bm.faces.remove(f)
for v in [v for v in bm.verts if not v.link_faces]: bm.verts.remove(v)
bm.to_mesh(me); bm.free()

out = {"hinge_y": HINGE, "front_x": FRONT_Y_MESH + ADJ_X, "height": [round(plo.z, 1), round(phi.z, 1)], "thickness": round(phi.y - plo.y, 1)}
mid_y = (plo.y + phi.y) * 0.5
for side, keep_pos in (("L", False), ("R", True)):
    # (the half: a copy cut at x 0, its other half's faces taken away)
    o = lod0.copy(); o.data = lod0.data.copy(); bpy.context.scene.collection.objects.link(o)
    b = bmesh.new(); b.from_mesh(o.data)
    geom = b.verts[:] + b.edges[:] + b.faces[:]
    r = bmesh.ops.bisect_plane(b, geom=geom, plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_inner=keep_pos, clear_outer=not keep_pos)
    edges = [e for e in r["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    if edges: bmesh.ops.edgeloop_fill(b, edges=edges)
    # (into the piece's frame, in Blender's units: engine (x, y, z) cm -> piece x = mesh y moved to the front + ADJ_X, piece y = -mesh x
    # narrowed to the hinge, z the same; Blender's y is the engine's -y)
    for v in b.verts:
        u = ue(v.co)
        px = (u.y - mid_y + FRONT_Y_MESH) + ADJ_X
        py = -(u.x * HINGE / 72.0) + ADJ_Y
        v.co = Vector((px / 100.0, -py / 100.0, u.z / 100.0))
    b.to_mesh(o.data); b.free()
    # (the origin at the hinge: the mesh's x 0 was the middle; the hinge is the far edge of this half: piece y -HINGE for the half
    # that was the mesh's +x (the right leaf, R), +HINGE for the left; on the floor (z 0), at the leaf's middle in x)
    hy = -HINGE + ADJ_Y if keep_pos else HINGE + ADJ_Y
    hx = FRONT_Y_MESH + ADJ_X
    for v in o.data.vertices: v.co -= Vector((hx / 100.0, -hy / 100.0, 0.0))
    o.name = f"SM_RD_ShelfDoor{side}15"
    out[side] = {"hinge": [round(hx, 2), round(hy, 2)], "verts": len(o.data.vertices)}
    for x in bpy.context.scene.objects: x.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    path = os.path.join(OUT, f"SM_RD_ShelfDoor{side}15.fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, global_scale=1.0, apply_unit_scale=True, axis_forward="-Y", axis_up="Z",
                             mesh_smooth_type="FACE", use_mesh_modifiers=True, add_leaf_bones=False, bake_anim=False)
    vs = [Vector((v.co.x * 100.0, -v.co.y * 100.0, v.co.z * 100.0)) for v in o.data.vertices]
    out[side]["box"] = [[round(min(c[i] for c in vs), 1) for i in range(3)], [round(max(c[i] for c in vs), 1) for i in range(3)]]
    print("SHELF15", side, out[side])
json.dump(out, open(os.path.join(OUT, "shelf_doors15.json"), "w"), indent=1)
print("SHELF15 done", OUT)
