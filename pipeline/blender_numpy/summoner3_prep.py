"""Summoner3 (ai models/Summoner3.glb: a Tripo model with a UE4-mannequin-named rig and her own walk and run) turned to face
-Y as the other Tripo heroes do (Blender; they face +Y in Unreal, 620's yaw -90 then turns them to the character's +X).
Her GLB faces -X: measured, not assumed, from her feet (each foot bone's head to its ball's) in the rest pose. Her root
objects are turned about the vertical by the angle between that and -Y (to the nearest quarter turn) and the GLB written
again with her clips; the importer's bone-shape icosphere is left out.

    blender -b -P summoner3_prep.py -- "ai models/Summoner3.glb" <out.glb>"""
import bpy, sys, math, mathutils
argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = argv[0], argv[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
for o in [o for o in bpy.context.scene.objects if o.type == "MESH" and not o.vertex_groups]: bpy.data.objects.remove(o, do_unlink=True)
B = arm.data.bones; mw = arm.matrix_world
fwd = mathutils.Vector((0, 0, 0))
for s in ("l", "r"): fwd += (mw @ B["ball_" + s].head_local) - (mw @ B["foot_" + s].head_local)
fwd.z = 0; fwd.normalize()
ang = math.atan2(fwd.y, fwd.x) - math.atan2(-1.0, 0.0)                 # from where she faces to -Y
ang = round(ang / (math.pi / 2)) * (math.pi / 2)
print("SUMMONER3 faces", tuple(round(c, 3) for c in fwd), "| turning by %.0f degrees" % math.degrees(-ang))
R = mathutils.Matrix.Rotation(-ang, 4, "Z")
for o in [o for o in bpy.context.scene.objects if o.parent is None]: o.matrix_world = R @ o.matrix_world
bpy.context.view_layer.update()
fwd2 = mathutils.Vector((0, 0, 0))
for s in ("l", "r"): fwd2 += (arm.matrix_world @ B["ball_" + s].head_local) - (arm.matrix_world @ B["foot_" + s].head_local)
print("SUMMONER3 now faces", tuple(round(c, 3) for c in fwd2.normalized()), "| clips", [a.name for a in bpy.data.actions])
bpy.ops.export_scene.gltf(filepath=OUT, export_format="GLB", export_animations=True, export_animation_mode="ACTIONS")
print("SUMMONER3 written", OUT)
