"""Animated Tripo character GLB (UE4-mannequin-named rig + glTF clips) -> UE-ready FBX pair, generalised from ff2_build.py:
  <name>.fbx        skinned mesh only (native-centimetre rig, HEIGHT cm, baked mesh transforms, identity parent-inverse)
  <name>_Clips.fbx  every glTF clip re-keyed on the scaled armature as action A_<Clip> (bone translations scaled with the rig)
Clips in the mesh FBX would make UE rebind the skin to a clip pose, hence two files. Textures extracted as T_<tag>_<role>.png.
clip_maker: a Python file with make_clips(arm, scene, clips) -> {name: frames} (frames as sampled here: per frame, each pose
bone's matrix_basis decomposed, on the GLB's own armature) for clips the GLB lacks (caster_clips.py: an idle and spell casts).
hair.json: hair chains added to the rig and the hair skinned to them (tripo_hair.py; the bones get no keys in the clips).
Blender: -b -P tripo_build.py -- model.glb out_dir name tag [height_cm] [clip_maker.py | -] [hair.json]"""
import bpy, sys, os, json
from mathutils import Matrix
argv = sys.argv[sys.argv.index("--") + 1:]
src, out, NAME, TAG = argv[0], argv[1], argv[2], argv[3]; HEIGHT_CM = float(argv[4]) if len(argv) > 4 else 165.0
MAKER = argv[5] if len(argv) > 5 and argv[5] != "-" else None
HAIR = argv[6] if len(argv) > 6 else None
os.makedirs(out, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=src)
sc.render.fps = 24
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
meshes = [o for o in sc.objects if o.type == 'MESH' and o.vertex_groups]      # skip the importer's bone-shape icosphere
for o in [o for o in sc.objects if o.type == 'MESH' and o not in meshes]: bpy.data.objects.remove(o, do_unlink=True)
arm.name = "Armature"; arm.data.name = "Armature"; meshes[0].name = NAME
ad = arm.animation_data
if ad:
    for t in list(ad.nla_tracks): ad.nla_tracks.remove(t)
else: ad = arm.animation_data_create()
roles = {}
for m in bpy.data.materials:                                    # name each texture by what it feeds
    if not m.use_nodes: continue
    for n in m.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image:
            for l in n.outputs[0].links:
                roles[n.image.name] = {"BSDF_PRINCIPLED": "Color", "SEPARATE_COLOR": "MetalRough", "NORMAL_MAP": "Normal"}.get(l.to_node.type, "Tex")
tex = {}
for img in bpy.data.images:
    if img.packed_file or img.has_data:
        p = os.path.join(out, f"T_{TAG}_{roles.get(img.name, img.name.replace(' ', '_'))}.png")
        img.filepath_raw = p; img.file_format = 'PNG'; img.save(); tex[roles.get(img.name, img.name)] = p; print("texture", img.name, "->", p)
for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'
clips = {}
for act in list(bpy.data.actions):
    name = act.name.split(".")[0]; name = name[:1].upper() + name[1:]
    ad.action = act
    if hasattr(ad, "action_slot") and act.slots: ad.action_slot = act.slots[0]
    f0, f1 = [int(round(v)) for v in act.frame_range]
    frames = []
    for t in range(f0, f1 + 1):
        sc.frame_set(t); frames.append({pb.name: pb.matrix_basis.decompose() for pb in arm.pose.bones})
    clips[name] = frames; print("sampled", name, f0, f1, len(frames))
ad.action = None
for a in list(bpy.data.actions): bpy.data.actions.remove(a)
for pb in arm.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
if MAKER:
    import importlib.util
    spec = importlib.util.spec_from_file_location("clip_maker", MAKER); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    for name, frames in mod.make_clips(arm, sc, clips).items():
        clips[name] = frames; print("made", name, len(frames))
    for pb in arm.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
zs = [(meshes[0].matrix_world @ v.co).z for v in meshes[0].data.vertices]
h = max(zs) - min(zs); S = HEIGHT_CM / h
print("source height m", round(h, 4), "unit scale", round(S, 3))
sc.unit_settings.system = 'METRIC'; sc.unit_settings.scale_length = 0.01
for o in meshes:
    mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
for o in [arm] + meshes: o.matrix_world = Matrix.Scale(S, 4) @ o.matrix_world
bpy.ops.object.select_all(action='DESELECT')
for o in [arm] + meshes: o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
for o in meshes:
    o.parent = arm; o.matrix_parent_inverse.identity()
    mods = [m for m in o.modifiers if m.type == 'ARMATURE'] or [o.modifiers.new("Armature", 'ARMATURE')]
    for m in mods: m.object = arm
bpy.context.view_layer.update()
hair_report = None
if HAIR:
    import importlib.util
    spec = importlib.util.spec_from_file_location("tripo_hair", os.path.join(os.path.dirname(os.path.abspath(__file__)), "tripo_hair.py"))
    th = importlib.util.module_from_spec(spec); spec.loader.exec_module(th)
    hair_report = th.add_hair(arm, meshes[0], json.load(open(HAIR)), tex["Color"])
    print("hair", json.dumps({k: v for k, v in hair_report.items() if k != "chains"}), "| chains", sorted(hair_report["chains"]))
    bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
for o in [arm] + meshes: o.select_set(True)
bpy.ops.export_scene.fbx(filepath=os.path.join(out, NAME + ".fbx"), use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                         bake_anim=False, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', use_armature_deform_only=False,
                         mesh_smooth_type='FACE', use_tspace=True, path_mode='STRIP')
ad = arm.animation_data_create()
for name, frames in clips.items():
    new = bpy.data.actions.new("A_" + name); new.use_fake_user = True; ad.action = new
    if hasattr(ad, "action_slot") and hasattr(new, "slots"):
        try: ad.action_slot = new.slots.new('OBJECT', "Armature")
        except Exception: pass
    for i, fr in enumerate(frames):
        for pb in arm.pose.bones:
            if pb.name not in fr: continue          # (the hair chains: no keys, Unreal swings them)
            loc, rot, scl = fr[pb.name]
            pb.location = loc * S; pb.rotation_quaternion = rot; pb.scale = scl
            pb.keyframe_insert("location", frame=i, group=pb.name); pb.keyframe_insert("rotation_quaternion", frame=i, group=pb.name)
            pb.keyframe_insert("scale", frame=i, group=pb.name)
    print("keyed", name, len(frames))
ad.action = None
for pb in arm.pose.bones: pb.matrix_basis.identity()
B = arm.data.bones
print("rest: head z", round(B["head"].head_local.z, 1), "pelvis z", round(B["pelvis"].head_local.z, 1))
bpy.ops.object.select_all(action='DESELECT')
for o in [arm] + meshes: o.select_set(True)
bpy.ops.export_scene.fbx(filepath=os.path.join(out, NAME + "_Clips.fbx"), use_selection=True, object_types={'ARMATURE', 'MESH'}, add_leaf_bones=False,
                         bake_anim=True, bake_anim_use_all_actions=True, bake_anim_use_nla_strips=False, bake_anim_force_startend_keying=True,
                         bake_anim_simplify_factor=0.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE',
                         use_armature_deform_only=False, mesh_smooth_type='FACE', use_tspace=True, path_mode='STRIP')
json.dump({"clips": {k: len(v) for k, v in clips.items()}, "textures": tex, "height_cm": HEIGHT_CM, "hair": hair_report}, open(os.path.join(out, "build.json"), "w"), indent=1)
print("EXPORT DONE")
