"""Per-clip motion report for the animated Tripo GLB: root/pelvis travel, pelvis height range, stance-foot speed.
Blender: -b -P ff2_inspect.py -- model.glb"""
import bpy, sys, math
src = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=src)
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
print("scene fps", sc.render.fps, "actions", [a.name for a in bpy.data.actions])
ad = arm.animation_data or arm.animation_data_create()
print("nla tracks", [t.name for t in ad.nla_tracks], "active", ad.action.name if ad.action else None)
for t in ad.nla_tracks: t.mute = True
H = 100 * 1.686           # source metres -> final cm (165 cm character)
for act in bpy.data.actions:
    ad.action = act
    if hasattr(ad, "action_slot") and act.slots: ad.action_slot = act.slots[0]
    f0, f1 = [int(round(v)) for v in act.frame_range]
    R, P, F = [], [], []
    for t in range(f0, f1 + 1):
        sc.frame_set(t)
        R.append((arm.matrix_world @ arm.pose.bones["root"].head).copy())
        P.append((arm.matrix_world @ arm.pose.bones["pelvis"].head).copy())
        F.append([(arm.matrix_world @ arm.pose.bones[b].head).copy() for b in ("ball_l", "ball_r")])
    fps = sc.render.fps
    sp = []
    for i in range(1, len(F)):
        lo = min((0, 1), key=lambda k: F[i][k].z)
        if F[i][lo].z < min(f[0].z for f in F) + 0.01 or F[i][lo].z < min(f[1].z for f in F) + 0.01:
            d = F[i][lo] - F[i - 1][lo]; sp.append(math.hypot(d.x, d.y) * fps)
    sp.sort()
    dr = R[-1] - R[0]; dp = P[-1] - P[0]
    pz = [p.z for p in P]
    print(f"{act.name:20s} f{f0}-{f1} ({(f1-f0)/fps:.2f}s) root d=({dr.x*H:.0f},{dr.y*H:.0f},{dr.z*H:.0f}) pelvis d=({dp.x*H:.0f},{dp.y*H:.0f},{dp.z*H:.0f}) "
          f"pelvis z {min(pz)*H:.0f}..{max(pz)*H:.0f} start {pz[0]*H:.0f} | stance speed med {sp[len(sp)//2]*H if sp else 0:.0f} cm/s | feet start l=({F[0][0].x*H:.0f},{F[0][0].y*H:.0f}) r=({F[0][1].x*H:.0f},{F[0][1].y*H:.0f})")
    if "jump" in act.name:
        print("   jump pelvis z per 3f:", [round(z * H) for z in pz[::3]])
