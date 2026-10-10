"""Inspect Dystopia_Soldier_02: mesh size, materials, armature, bones; and the animation FBX (frame ranges, pelvis travel).
Blender: -b -P soldier_inspect.py -- src_dir"""
import bpy, sys, os, math
from mathutils import Vector
src = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(src, "Mesh", "Dystopia_Soldier_02_Mesh.FBX"))
sc = bpy.context.scene
for o in sc.objects:
    print("OBJ", o.type, o.name, "scale", tuple(round(s, 4) for s in o.scale), "rot", tuple(round(math.degrees(r)) for r in o.rotation_euler), "parent", o.parent.name if o.parent else None)
    if o.type == 'MESH':
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        print("   verts", len(o.data.vertices), "height", round(max(v.z for v in bb) - min(v.z for v in bb), 3), "y-extent", round(max(v.y for v in bb) - min(v.y for v in bb), 3),
              "mats", [m.name for m in o.data.materials], "vgroups", len(o.vertex_groups))
    if o.type == 'ARMATURE':
        bones = [b.name for b in o.data.bones]
        print("   bones", len(bones), bones)
        for b in ("pelvis", "head", "foot_l", "ball_l", "hand_r"):
            if b in o.data.bones: print("   ", b, tuple(round(v, 3) for v in (o.matrix_world @ o.data.bones[b].head_local)))
anims = sorted(f for f in os.listdir(os.path.join(src, "Animations")) if f.lower().endswith(".fbx"))
print("ANIM FILES", len(anims))
for f in anims:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=os.path.join(src, "Animations", f))
    arm = next((o for o in bpy.context.scene.objects if o.type == 'ARMATURE'), None)
    if not arm or not arm.animation_data or not arm.animation_data.action: print("  ", f, "NO ACTION"); continue
    act = arm.animation_data.action; fr = act.frame_range
    sc = bpy.context.scene
    sc.frame_set(int(fr[0])); p0 = (arm.matrix_world @ arm.pose.bones["pelvis"].head).copy() if "pelvis" in arm.pose.bones else Vector()
    sc.frame_set(int(fr[1])); p1 = (arm.matrix_world @ arm.pose.bones["pelvis"].head).copy() if "pelvis" in arm.pose.bones else Vector()
    d = p1 - p0; dur = (fr[1] - fr[0]) / sc.render.fps
    print(f"  {f.split('@')[-1][:-4]:26s} frames {int(fr[0])}-{int(fr[1])} fps {sc.render.fps} dur {dur:5.2f}s travel ({d.x:6.2f},{d.y:6.2f},{d.z:5.2f}) bones {len(arm.data.bones)}")
