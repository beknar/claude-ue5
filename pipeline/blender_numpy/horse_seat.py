"""The list of 2026-11-16, item 6 ("the player's position on the horse is too far back, she should be in the middle of the saddle,
and she should be holding the reigns"): the riding horse's saddle measured on the model itself. The Tripo horse
(tripo_animals.py's SK_Tripo_Horse.fbx, the mesh the game rides) carries a modelled saddle, dark leather on a pale back; its
`saddle` bone, which the game seats her pelvis on, was placed by farm_animals.py's proportions for the Blender horse and stands on
the saddle's cantle, its back edge (she rode on the croup).

Along the horse's length, 10 cm slices of the back's top within 15 cm of its middle line: the saddle is the run of dark slices
(the top's mean brightness under 0.3; the croup is white, 0.9) that holds the slice nearest the bone; its seat is the run's lowest
top, between the cantle and the pommel; the rein grip is 8 cm past the pommel (the run's front) and 12 cm over the top there,
where a rider's hands hold the reins over the withers. Written as offsets from the bone in centimetres along the horse's length
(+ toward its head), across it and up, for 927 horse (HorseDef's seat and rein grip).
    blender -b -P horse_seat.py -- <SK_Tripo_Horse.fbx> <T_Tripo_Horse.png> <out.json>"""
import bpy, sys, json, os
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
FBX, TEX, OUT = argv[0], argv[1], argv[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX)
arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
mesh = next(o for o in bpy.context.scene.objects if o.type == "MESH")
img = bpy.data.images.load(TEX); W, H = img.size
px = np.array(img.pixels[:], dtype=np.float32).reshape(H, W, 4)
me = mesh.data; mw = mesh.matrix_world; uv = me.uv_layers.active.data
vcol = np.zeros((len(me.vertices), 3), np.float32); seen = np.zeros(len(me.vertices), bool)
for l in me.loops:
    v = l.vertex_index
    if seen[v]: continue
    u, w = uv[l.index].uv
    vcol[v] = px[min(H - 1, max(0, int(w * H))), min(W - 1, max(0, int(u * W))), :3]; seen[v] = True
P = np.array([tuple(mw @ v.co) for v in me.vertices], np.float32)
lum = vcol @ np.array([0.299, 0.587, 0.114], np.float32)
sad = [float(c) for c in (arm.matrix_world @ arm.data.bones["saddle"].head_local)]
ext = P.max(0) - P.min(0)
L = 0 if ext[0] >= ext[1] else 1; Wd = 1 - L
mid = float(np.median(P[:, Wd]))
hb = next((b for b in arm.data.bones if b.name.lower().startswith("head")), None)
head_way = 1 if (arm.matrix_world @ hb.head_local)[L] > sad[L] else -1
# (the slices along the length, toward the head positive; the file's units found by the horse's length: metres under 20)
M = 1.0 if ext[L] < 20 else 100.0                 # (a metre in the file's units)
step = 0.1 * M                                    # (10 cm)
slices = []
x = float(P[:, L].min())
while x < float(P[:, L].max()):
    s = (P[:, L] >= x) & (P[:, L] < x + step) & (np.abs(P[:, Wd] - mid) < 1.5 * step)
    if s.sum() >= 5:
        tz = float(P[s, 2].max()); topm = s & (P[:, 2] > tz - 0.8 * step)
        slices.append((float(x + step / 2), tz, float(lum[topm].mean())))
    x += step
slices.sort(key=lambda t: t[0] * head_way)
near = min(range(len(slices)), key=lambda i: abs(slices[i][0] - sad[L]))
dark = [s_[2] < 0.3 for s_ in slices]
# (the saddle's run: dark slices through the one nearest the bone, a light slice or two inside it allowed (its stitching))
i0 = near
while i0 > 0 and (dark[i0 - 1] or (i0 > 1 and dark[i0 - 2])): i0 -= 1
i1 = near
while i1 < len(slices) - 1 and (dark[i1 + 1] or (i1 < len(slices) - 2 and dark[i1 + 2])): i1 += 1
run = slices[i0:i1 + 1]
# (the seat: the lowest top between the cantle (the highest of the run's back half) and the pommel (the highest of its front half);
# the run's own lowest can be its end, where the back drops to the croup)
half = len(run) // 2
ci = max(range(0, max(1, half)), key=lambda i: run[i][1]); pi = max(range(half, len(run)), key=lambda i: run[i][1])
between = run[ci + 1:pi] or [run[(ci + pi) // 2]]
seat = min(between, key=lambda t: t[1])
front = run[-1]
u = 100.0 / M                                     # (to centimetres)
# (the bit: the mouth's corner, 12 cm behind the nose's tip at the lower third of the head there; from the head bone's place, which
# the game reads each frame (the head bobs in a gallop), along the horse and up. The reins run from it to her hands)
hd = [float(c) for c in (arm.matrix_world @ hb.head_local)]
tip = float(P[:, L].max()) if head_way > 0 else float(P[:, L].min())
nose = P[np.abs(P[:, L] - tip) < 0.15 * M]
zlo, zhi = float(nose[:, 2].min()), float(nose[:, 2].max())
bit_l = tip - head_way * 0.12 * M; bit_z = zlo + (zhi - zlo) * 0.33
res = {"fbx": os.path.basename(FBX), "length_axis": "XY"[L], "head_way": head_way,
       "saddle_bone_cm": [round(float(c) * u, 1) for c in sad],
       "saddle_run_cm": [round(run[0][0] * u, 1), round(run[-1][0] * u, 1)],
       "seat": {"ahead_cm": round((seat[0] - sad[L]) * head_way * u, 1), "up_cm": round((seat[1] - sad[2]) * u, 1)},
       "bit_from_head_bone": {"ahead_cm": round((bit_l - hd[L]) * head_way * u, 1), "up_cm": round((bit_z - hd[2]) * u, 1)},
       # (her hands' hold: a rider's, chosen, not measured: 25 cm ahead of her pelvis and 25 cm over it, 22 cm apart, within every
       # hero's reach (the withers' grip measured first, 38 cm ahead and 5 cm up, was out of reach of the Tripo heroes' arms))
       "rein_grip": {"ahead_cm": 25.0, "up_cm": 25.0, "apart_cm": 22.0, "from": "her pelvis"},
       "profile": [[round(t[0] * u, 1), round(t[1] * u, 1), round(t[2], 2)] for t in slices]}
json.dump(res, open(OUT, "w"), indent=1)
print("HORSESEAT", json.dumps({k: v for k, v in res.items() if k != "profile"}))
