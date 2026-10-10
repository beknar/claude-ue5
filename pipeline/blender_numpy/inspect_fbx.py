"""Import a UE-exported FBX and report objects, materials, bounds, armature. Optionally dump the
mesh whose material matches a substring to npz (co/nr/tri). Blender: -- in.fbx [mat_substr out.npz]"""
import bpy, sys, numpy as np
argv = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=argv[0])
for o in bpy.context.scene.objects:
    if o.type == 'ARMATURE':
        bones = o.data.bones
        print("ARMATURE", o.name, len(bones), "scale", tuple(o.scale), "rot", tuple(o.rotation_euler))
        for b in list(bones)[:6]: print("  bone", b.name, tuple(round(c, 3) for c in (o.matrix_world @ b.head_local)))
        for nm in ("head", "neck_01", "pelvis", "foot_l", "hand_l", "upperarm_l", "ball_l"):
            if nm in bones: print("  ", nm, tuple(round(c, 3) for c in (o.matrix_world @ bones[nm].head_local)))
    if o.type == 'MESH':
        me = o.data
        co = np.array([o.matrix_world @ v.co for v in me.vertices])
        print("MESH", o.name, len(me.vertices), "mats", [m.name for m in me.materials],
              "min", co.min(0).round(3), "max", co.max(0).round(3), "groups", len(o.vertex_groups))
if len(argv) > 2:
    sub, out = argv[1], argv[2]
    for o in bpy.context.scene.objects:
        if o.type != 'MESH': continue
        me = o.data
        mi = [i for i, m in enumerate(me.materials) if m and sub.lower() in m.name.lower()]
        if not mi: continue
        me.calc_loop_triangles()
        tris = [t for t in me.loop_triangles if t.material_index in mi]
        tri = np.array([t.vertices[:] for t in tris])
        used = np.unique(tri)
        mw = np.array(o.matrix_world)
        co = np.array([v.co for v in me.vertices])[used] @ mw[:3, :3].T + mw[:3, 3]
        nr = np.array([v.normal for v in me.vertices])[used] @ mw[:3, :3].T
        nr /= np.linalg.norm(nr, axis=1, keepdims=True) + 1e-9
        remap = -np.ones(len(me.vertices), int); remap[used] = np.arange(len(used))
        np.savez(out, co=co, nr=nr, tri=remap[tri], src_index=used)
        print("DUMPED", out, len(used), "verts from", o.name, [me.materials[i].name for i in mi])
