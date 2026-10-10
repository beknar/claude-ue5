"""Classify fig4's scan vertices into skin / hair / dress / stockings / shoes / choker,
smooth the labels over the mesh graph, and save the labels plus a color-coded preview.
Blender: -b -P segment_fig4.py -- src.glb work_dir"""
import bpy, bmesh, sys, math, numpy as np, mathutils

argv = sys.argv[sys.argv.index("--") + 1:]
src, work = argv[0], argv[1]
SKIN, HAIR, DRESS, STOCK, SHOE, CHOKER = range(6)
NAMES = ["skin", "hair", "dress", "stockings", "shoes", "choker"]
PALETTE = np.array([[1, .75, .6], [.1, .3, 1], [.9, .05, .05], [.9, .9, .9], [.1, .9, .2], [1, .9, 0]], np.float32)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
me = obj.data
co = np.load(f"{work}/co.npy"); col = np.load(f"{work}/col.npy")
n = len(co)
srgb = np.where(col <= 0.0031308, col * 12.92, 1.055 * np.power(np.clip(col, 0, None), 1 / 2.4) - 0.055)
r, g, b = srgb.T
v = srgb.max(1); s = np.where(v > 1e-4, (v - srgb.min(1)) / np.maximum(v, 1e-4), 0)
x, y, z = co.T

# --- raw per-vertex guess ---------------------------------------------------
lab = np.full(n, SKIN, np.int8)
dark = (v < 0.30) & ~((r > 1.6 * g) & (r > 0.15))           # near-black, not red
red = (r > 1.6 * g) & (r > 0.12) & (v < 0.75) & (s > 0.45)
white = (v > 0.72) & (s < 0.16)
lab[dark & (z > 0.20)] = HAIR
lab[red & (z > -0.12) & (z < 0.60)] = DRESS
lab[white & (z < -0.08) & (z > -0.82)] = STOCK
lab[(z < -0.74)] = SHOE
lab[(z < -0.74) & white & (z > -0.80)] = STOCK
# choker: a dark band round the neck, in front of / beside the neck column
neck_band = (z > 0.655) & (z < 0.715) & (np.abs(x) < 0.075) & (y < 0.0)
lab[dark & neck_band] = CHOKER

# --- smooth: majority vote over 1-ring neighbours (a few passes) --------------
ev = np.empty(len(me.edges) * 2, np.int32); me.edges.foreach_get("vertices", ev); ev = ev.reshape(-1, 2)
src_i = np.concatenate([ev[:, 0], ev[:, 1]]); dst_i = np.concatenate([ev[:, 1], ev[:, 0]])
for _ in range(6):
    votes = np.zeros((n, 6), np.float32)
    np.add.at(votes, (dst_i, lab[src_i]), 1.0)
    votes[np.arange(n), lab] += 1.5
    new = votes.argmax(1).astype(np.int8)
    # spatial guards so smoothing can't leak classes into impossible regions
    new[(new == SHOE) & (z > -0.70)] = lab[(new == SHOE) & (z > -0.70)]
    new[(new == STOCK) & (z > -0.05)] = lab[(new == STOCK) & (z > -0.05)]
    lab = new
# On the head, greyish "skin" is hair texture (streaks); real skin there is warm and light.
skinlike = ~((v < 0.42) | ((s < 0.07) & (v < 0.75)))
head = (z > 0.64) & (np.abs(x) < 0.2)        # above the T-posed arms
lab[(lab == SKIN) & head & ~skinlike] = HAIR
np.save(f"{work}/labels.npy", lab)
for k in range(6):
    m = lab == k
    print(f"LABEL {NAMES[k]:10s} {m.sum():7d} z[{z[m].min() if m.any() else 0:+.2f},{z[m].max() if m.any() else 0:+.2f}]")

# islands
bm = bmesh.new(); bm.from_mesh(me)
print("LOOSE PARTS (approx via linked faces):", end=" ")
bm.free()

# --- preview: vertex colors -> emission render --------------------------------
ca = me.color_attributes.new("seg", 'FLOAT_COLOR', 'POINT')
rgba = np.concatenate([PALETTE[lab], np.ones((n, 1), np.float32)], 1)
ca.data.foreach_set("color", rgba.ravel())
mat = bpy.data.materials.new("seg"); mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
a = nt.nodes.new("ShaderNodeAttribute"); a.attribute_name = "seg"
e = nt.nodes.new("ShaderNodeEmission"); o = nt.nodes.new("ShaderNodeOutputMaterial")
nt.links.new(a.outputs["Color"], e.inputs["Color"]); nt.links.new(e.outputs[0], o.inputs[0])
me.materials.clear(); me.materials.append(mat)
scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'FLAT'; scene.display.shading.color_type = 'VERTEX'
scene.render.resolution_x, scene.render.resolution_y = 700, 1100
cd = bpy.data.cameras.new("c"); cd.type = 'ORTHO'; cd.ortho_scale = 2.0
cam = bpy.data.objects.new("c", cd); scene.collection.objects.link(cam); scene.camera = cam
for name, d in (("front", (0, -1, 0)), ("back", (0, 1, 0)), ("side", (1, 0, 0))):
    dv = mathutils.Vector(d)
    cam.location = dv * 5
    cam.rotation_euler = (-dv).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = f"{work}/seg_{name}.png"
    bpy.ops.render.render(write_still=True)
