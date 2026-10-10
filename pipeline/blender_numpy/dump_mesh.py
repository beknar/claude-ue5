"""Dump a glb's vertices, vertex normals and triangles (Blender world space, Z-up) to .npz.
Blender: -b -P dump_mesh.py -- in.glb out.npz"""
import bpy, sys, numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
me = obj.data
mw = np.array(obj.matrix_world)
n = len(me.vertices)
co = np.empty(n * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
nr = np.empty(n * 3, np.float32); me.vertices.foreach_get("normal", nr); nr = nr.reshape(-1, 3)
co = co @ mw[:3, :3].T + mw[:3, 3]
nr = nr @ mw[:3, :3].T; nr /= np.linalg.norm(nr, axis=1, keepdims=True) + 1e-9
me.calc_loop_triangles()
tri = np.empty(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get("vertices", tri)
np.savez(argv[1], co=co, nr=nr, tri=tri.reshape(-1, 3))
print("DUMPED", argv[1], n, len(tri) // 3)
