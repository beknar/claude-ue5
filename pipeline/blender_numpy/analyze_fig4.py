"""Sample fig4's base color per vertex and print height profiles so the hair / dress /
stocking / shoe / skin regions can be separated. Blender, run with -b -P ... -- src out_dir"""
import bpy, sys, numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
src, out_dir = argv[0], argv[1]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
me = obj.data
mw = np.array(obj.matrix_world)

n = len(me.vertices)
co = np.empty(n * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
co = co @ mw[:3, :3].T + mw[:3, 3]

# per-vertex UV (from loops)
uvl = me.uv_layers.active.data
luv = np.empty(len(uvl) * 2, np.float32); uvl.foreach_get("uv", luv); luv = luv.reshape(-1, 2)
lvi = np.empty(len(me.loops), np.int32); me.loops.foreach_get("vertex_index", lvi)
vuv = np.zeros((n, 2), np.float32); vuv[lvi] = luv

mat = me.materials[0]
img = next(nd.image for nd in mat.node_tree.nodes if nd.type == 'TEX_IMAGE' and nd.image and 'base' in (nd.label + nd.name + nd.image.name).lower()) \
    if any(nd.type == 'TEX_IMAGE' for nd in mat.node_tree.nodes) else None
# pick the image linked to Base Color
bsdf = next(nd for nd in mat.node_tree.nodes if nd.type == 'BSDF_PRINCIPLED')
link = bsdf.inputs['Base Color'].links[0]
nd = link.from_node
while nd.type != 'TEX_IMAGE':
    nd = nd.inputs[0].links[0].from_node
img = nd.image
w, h = img.size
px = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(h, w, 4)
xi = np.clip((vuv[:, 0] % 1.0) * w, 0, w - 1).astype(int)
yi = np.clip((vuv[:, 1] % 1.0) * h, 0, h - 1).astype(int)
col = px[yi, xi, :3]
np.save(f"{out_dir}/co.npy", co); np.save(f"{out_dir}/col.npy", col)

lum = col @ np.array([0.2126, 0.7152, 0.0722])
mx, mn = col.max(1), col.min(1)
sat = np.where(mx > 1e-4, (mx - mn) / np.maximum(mx, 1e-4), 0)
z = co[:, 2]
print("BOUNDS", co.min(0), co.max(0))
print("z   n     dark  red  white  skin   x-extent(skin)  y-range")
for zb in np.arange(z.min(), z.max(), 0.05):
    m = (z >= zb) & (z < zb + 0.05)
    if not m.any(): continue
    c = col[m]; l = lum[m]; s = sat[m]
    dark = (l < 0.12).mean()
    red = ((c[:, 0] > c[:, 1] * 1.8) & (l < 0.35) & (l >= 0.02)).mean()
    white = ((l > 0.6) & (s < 0.12)).mean()
    skin = ((s > 0.12) & (s < 0.55) & (l > 0.3) & (c[:, 0] > c[:, 2])).mean()
    print(f"{zb:+.2f} {m.sum():6d} {dark:.2f} {red:.2f} {white:.2f} {skin:.2f}  "
          f"x[{co[m,0].min():+.2f},{co[m,0].max():+.2f}] y[{co[m,1].min():+.2f},{co[m,1].max():+.2f}]")
