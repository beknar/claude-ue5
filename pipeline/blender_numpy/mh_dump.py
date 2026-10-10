"""Dump the MetaHuman's face skin, body surface, bones and body skin weights (rest/bind pose,
Blender world space) to npz. Blender: -- face.fbx body.fbx out.npz"""
import bpy, sys, numpy as np
argv = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=argv[0])
face = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
face.name = "MH_Face"
bpy.ops.import_scene.fbx(filepath=argv[1])
body = next(o for o in bpy.context.scene.objects if o.type == 'MESH' and o is not face)
arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE' and o in [m.parent for m in [body]] or o.type == 'ARMATURE' and body.find_armature() == o)

def mesh_arrays(o, mat_sub=None):
    me = o.data; mw = np.array(o.matrix_world)
    me.calc_loop_triangles()
    tris = [t for t in me.loop_triangles if mat_sub is None or (me.materials[t.material_index] and mat_sub in me.materials[t.material_index].name)]
    tri = np.array([t.vertices[:] for t in tris]); used = np.unique(tri)
    co = np.array([v.co for v in me.vertices])[used] @ mw[:3, :3].T + mw[:3, 3]
    nr = np.array([v.normal for v in me.vertices])[used] @ mw[:3, :3].T
    nr /= np.linalg.norm(nr, axis=1, keepdims=True) + 1e-9
    remap = -np.ones(len(me.vertices), int); remap[used] = np.arange(len(used))
    return co, nr, remap[tri], used

fco, fnr, ftri, _ = mesh_arrays(face, "Skin_Baked_LOD0")
bco, bnr, btri, bused = mesh_arrays(body)
# body weights (top 4 per vertex)
names = [g.name for g in body.vertex_groups]
W = np.zeros((len(body.data.vertices), 4)); I = np.zeros((len(body.data.vertices), 4), int)
for v in body.data.vertices:
    gs = sorted(((g.weight, g.group) for g in v.groups), reverse=True)[:4]
    s = sum(w for w, _ in gs) or 1
    for k, (w, gi) in enumerate(gs):
        W[v.index, k] = w / s; I[v.index, k] = gi
W, I = W[bused], I[bused]
bones = [b.name for b in arm.data.bones]
amw = np.array(arm.matrix_world)
heads = np.array([amw[:3, :3] @ np.array(b.head_local) + amw[:3, 3] for b in arm.data.bones])
tails = np.array([amw[:3, :3] @ np.array(b.tail_local) + amw[:3, 3] for b in arm.data.bones])
np.savez(argv[2], face_co=fco, face_nr=fnr, face_tri=ftri, body_co=bco, body_nr=bnr, body_tri=btri,
         body_w=W, body_wi=I, group_names=np.array(names), bones=np.array(bones), heads=heads, tails=tails)
print("MHDUMP face", len(fco), "body", len(bco), "bones", len(bones), "armature", arm.name)
for n in ("head", "neck_01", "pelvis", "spine_05", "upperarm_l", "lowerarm_l", "hand_l", "thigh_l", "calf_l", "foot_l", "ball_l"):
    i = bones.index(n); print(f"  {n:12s} head {heads[i].round(3)} tail {tails[i].round(3)}")
