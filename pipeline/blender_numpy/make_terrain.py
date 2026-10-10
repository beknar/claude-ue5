"""Terrain grid from terrain_h.npy (400 m, metres), 3 rock variants, a grass clump. Exported as glb.
Blender: -b -P make_terrain.py -- src_dir out_dir"""
import bpy, bmesh, sys, math, random
import numpy as np
argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)

def export(obj, name):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True); bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.gltf(filepath=f"{out}/{name}.glb", export_format='GLB', use_selection=True,
                              export_apply=True, export_normals=True, export_texcoords=True)
    print("exported", name)

# --- terrain ------------------------------------------------------------------------
H = np.load(f"{src}/terrain_h.npy"); G = H.shape[0]; S = 400.0
xs = np.linspace(-S / 2, S / 2, G)
X, Y = np.meshgrid(xs, xs)
verts = np.stack([X.ravel(), Y.ravel(), H.ravel()], -1)
i = np.arange(G - 1)[:, None] * G + np.arange(G - 1)[None, :]
i = i.ravel()
quads = np.stack([i, i + 1, i + G + 1, i + G], -1)
me = bpy.data.meshes.new("SM_Terrain")
me.vertices.add(len(verts)); me.vertices.foreach_set("co", verts.ravel().astype(np.float32))
me.loops.add(quads.size); me.loops.foreach_set("vertex_index", quads.ravel().astype(np.int32))
me.polygons.add(len(quads)); me.polygons.foreach_set("loop_start", (np.arange(len(quads)) * 4).astype(np.int32))
uv = me.uv_layers.new(name="UVMap")
lv = quads.ravel()
uvs = np.stack([verts[lv, 0], verts[lv, 1]], -1) / 1.0          # 1 UV unit = 1 m (material scales per layer)
uv.data.foreach_set("uv", uvs.ravel().astype(np.float32))
me.update(); me.validate()
me.polygons.foreach_set("use_smooth", np.ones(len(quads), dtype=bool))
ter = bpy.data.objects.new("SM_Terrain", me); bpy.context.scene.collection.objects.link(ter)
export(ter, "SM_Terrain")
bpy.data.objects.remove(ter)

# --- rocks: displaced, flattened icospheres -------------------------------------------
for k, (seed, sx, sy, sz) in enumerate(((3, 1.3, 1.0, 0.75), (7, 1.0, 0.8, 1.1), (11, 1.6, 1.2, 0.55))):
    random.seed(seed)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=7, radius=1.0)
    o = bpy.context.active_object; o.name = f"SM_Rock_{'ABC'[k]}"; o.data.name = o.name
    o.scale = (sx, sy, sz); bpy.ops.object.transform_apply(scale=True)
    for name, ttype, size, strength in (("big", 'VORONOI', 0.9, 0.35), ("mid", 'CLOUDS', 0.35, 0.12), ("fine", 'CLOUDS', 0.06, 0.025)):
        t = bpy.data.textures.new(f"{o.name}_{name}", ttype)
        if ttype == 'CLOUDS': t.noise_scale = size; t.noise_depth = 4
        else: t.noise_scale = size; t.distance_metric = 'DISTANCE'
        m = o.modifiers.new(name, 'DISPLACE'); m.texture = t; m.strength = strength; m.mid_level = 0.5
        m.texture_coords = 'OBJECT' if False else 'LOCAL'
    bpy.ops.object.convert(target='MESH')
    # sink: flatten underside so it sits in the ground
    for v in o.data.vertices:
        if v.co.z < -0.25 * sz: v.co.z = -0.25 * sz + (v.co.z + 0.25 * sz) * 0.15
    bpy.ops.object.shade_smooth()
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=2.0); bpy.ops.object.mode_set(mode='OBJECT')
    export(o, o.name)
    bpy.data.objects.remove(o)

# --- grass clump: ~60 curved, tapered blades (two-sided material in UE) -------------------
random.seed(5)
bm = bmesh.new(); uvl = bm.loops.layers.uv.new("UVMap")
SEG = 5
for b in range(60):
    a = random.uniform(0, 2 * math.pi); rr = 0.12 * math.sqrt(random.random())
    bx, by = rr * math.cos(a), rr * math.sin(a)
    h = random.uniform(0.18, 0.48); w = random.uniform(0.006, 0.011)
    face = random.uniform(0, 2 * math.pi)                     # blade facing
    lean = random.uniform(0.15, 0.7) * h                      # how far the tip arcs over
    ldir = a + random.uniform(-0.6, 0.6)
    fx, fy = math.cos(face), math.sin(face)                   # width direction
    rows = []
    for s in range(SEG + 1):
        t = s / SEG
        z = h * t - 0.08 * lean * t * t
        off = lean * t * t
        cx, cy = bx + off * math.cos(ldir), by + off * math.sin(ldir)
        ww = w * (1 - t ** 1.6) + 0.0005
        rows.append((bm.verts.new((cx - fx * ww, cy - fy * ww, z)), bm.verts.new((cx + fx * ww, cy + fy * ww, z)), t))
    for s in range(SEG):
        (a0, b0, t0), (a1, b1, t1) = rows[s], rows[s + 1]
        f = bm.faces.new((a0, b0, b1, a1))
        for loop, uvv in zip(f.loops, ((0, t0), (1, t0), (1, t1), (0, t1))):
            loop[uvl].uv = uvv
me = bpy.data.meshes.new("SM_GrassClump"); bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
g = bpy.data.objects.new("SM_GrassClump", me); bpy.context.scene.collection.objects.link(g)
export(g, "SM_GrassClump")
print("TERRAIN done")
