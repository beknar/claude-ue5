"""Preview render of the Meshy biped + per-animation pelvis travel / yaw (root-motion survey).
Blender: -b -P meshy_inspect.py -- src_dir out_dir"""
import bpy, sys, os, math, json
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
os.makedirs(out, exist_ok=True)
files = sorted(f for f in os.listdir(src) if f.endswith(".glb"))
report = {}
for k, f in enumerate(files):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(src, f))
    arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    act = arm.animation_data.action if arm.animation_data else None
    name = f.replace("Meshy_AI_biped_Animation_", "").replace("_withSkin.glb", "")
    fr = [int(v) for v in act.frame_range]
    sc = bpy.context.scene
    pts, yaws = [], []
    for t in range(fr[0], fr[1] + 1):
        sc.frame_set(t)
        pb = arm.pose.bones["pelvis"]
        m = arm.matrix_world @ pb.matrix
        pts.append(tuple(m.translation)); yaws.append(math.degrees(m.to_euler().z))
    d = Vector(pts[-1]) - Vector(pts[0])
    dur = (fr[1] - fr[0]) / sc.render.fps
    report[name] = dict(frames=fr, fps=sc.render.fps, dur=round(dur, 3), dx=round(d.x, 3), dy=round(d.y, 3), dz=round(d.z, 3),
                        speed_cm_s=round(100 * math.hypot(d.x, d.y) / max(dur, 1e-6), 1), yaw_change=round(yaws[-1] - yaws[0], 1),
                        z_min=round(min(p[2] for p in pts), 3), z_max=round(max(p[2] for p in pts), 3))
    if k == 0:
        mesh = next(o for o in sc.objects if o.type == 'MESH')
        bb = [mesh.matrix_world @ Vector(c) for c in mesh.bound_box]
        report["_mesh"] = dict(height=round(max(v.z for v in bb) - min(v.z for v in bb), 3), verts=len(mesh.data.vertices),
                               bones=[b.name for b in arm.data.bones], rest_pelvis=list(arm.data.bones["pelvis"].head_local))
        sc.frame_set(fr[0])
        for b in arm.pose.bones: b.matrix_basis.identity()     # rest pose for the preview
        cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
        sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN')); sc.collection.objects.link(sun)
        sun.rotation_euler = (math.radians(50), 0, math.radians(30)); sun.data.energy = 3
        sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.4, 0.4, 0.45)
        sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
        sc.render.resolution_x, sc.render.resolution_y = 900, 1200
        h = report["_mesh"]["height"]
        for view, (x, y, rz) in {"front": (0, -3.2, 0), "side": (3.2, 0, 90), "back": (0, 3.2, 180)}.items():
            cam.location = (x, y, h * 0.55); cam.rotation_euler = (math.radians(90), 0, math.radians(rz))
            cam.data.lens = 50
            sc.render.filepath = os.path.join(out, f"preview_{view}.png"); bpy.ops.render.render(write_still=True)
json.dump(report, open(os.path.join(out, "anim_report.json"), "w"), indent=1)
print("REPORT", json.dumps(report))
