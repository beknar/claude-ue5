"""The Summoner (ai models/Summoner.glb, a Tripo model with a smart rig of generic bone names Bone_000..Bone_068 and no clips)
renamed to the UE4-mannequin names the other heroes have, so that tripo_build.py, 600-620 and the Mage's clips work on her.

    blender -b -P summoner_rig.py -- "ai models/Summoner.glb" <out.glb> [face.json]

Her rig, read from its hierarchy (glTF +X is her left):
  Bone_000 hips (the root of the rig, at hip height)    -> pelvis
  Bone_001 above it, the legs and the spine hang from it -> pelvis_hub
  Bone_005 / 004 / 003 / 002 the spine, 002 the chest    -> spine_01 / 02 / 03 / 04
  Bone_018 / 017 / 016 neck, head, head end              -> neck_01 / head / head_end
  Bone_023 / 022 / 021 / 020 / 019 left arm              -> clavicle_l / upperarm_l / lowerarm_l / hand_l / palm_l
  Bone_028 / 027 / 026 / 025 / 024 right arm             -> the same with _r
  five 4-bone chains under each palm: the fingers        -> thumb / index / middle / ring / pinky _01.._03 (+ _04)
  Bone_010 / 009 / 008 / 007 / 006 left leg              -> thigh_l / calf_l / foot_l / ball_l / toe_l
  Bone_015 / 014 / 013 / 012 / 011 right leg             -> the same with _r
Which finger chain is which is measured, not assumed: the thumb is the base farthest from the line through the other four,
the four are ordered along that line from the side where the thumb ends (index, middle, ring, pinky; its base lies half way
across the palm, and ordering from it gave index and pinky the wrong way round).
A root bone is added at the floor under her (the other heroes' rigs have one; the clips' root stays put).
face.json (summoner_face.py): the shape keys of her face are added to the mesh before it is written.
Prints the mapping ("SUMMONER bones") and a check that every mannequin bone the clips use is there."""
import bpy, sys, os, json
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
SRC, OUT = argv[0], argv[1]
FACE = argv[2] if len(argv) > 2 else None
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
mesh = next(o for o in sc.objects if o.type == 'MESH' and o.vertex_groups)
for o in [o for o in sc.objects if o.type == 'MESH' and o is not mesh]: bpy.data.objects.remove(o, do_unlink=True)
B = arm.data.bones
W = lambda b: arm.matrix_world @ B[b].head_local
NAMES = {"Bone_000": "pelvis", "Bone_001": "pelvis_hub", "Bone_005": "spine_01", "Bone_004": "spine_02", "Bone_003": "spine_03", "Bone_002": "spine_04",
         "Bone_018": "neck_01", "Bone_017": "head", "Bone_016": "head_end",
         "Bone_010": "thigh_l", "Bone_009": "calf_l", "Bone_008": "foot_l", "Bone_007": "ball_l", "Bone_006": "toe_l",
         "Bone_015": "thigh_r", "Bone_014": "calf_r", "Bone_013": "foot_r", "Bone_012": "ball_r", "Bone_011": "toe_r"}
ARMS = {"l": ["Bone_023", "Bone_022", "Bone_021", "Bone_020", "Bone_019"], "r": ["Bone_028", "Bone_027", "Bone_026", "Bone_025", "Bone_024"]}
# (the side is checked, not assumed: her left is glTF +X, which the importer turns into Blender +X)
assert W("Bone_022").x > 0 > W("Bone_027").x and W("Bone_010").x > 0 > W("Bone_015").x, "sides"
fingers = {}
for s, chain in ARMS.items():
    for b, n in zip(chain, ("clavicle", "upperarm", "lowerarm", "hand", "palm")): NAMES[b] = f"{n}_{s}"
    palm = B[chain[4]]
    roots = [c for c in palm.children]
    assert len(roots) == 5, (s, [c.name for c in roots])
    base = {c.name: arm.matrix_world @ c.head_local for c in roots}
    def off_line(k):
        others = [base[o] for o in base if o != k]
        c = sum(others, Vector()) / 4; d = (others[0] - others[-1]).normalized()
        # (the line through the other four: its direction by their spread)
        best = max(((a - b_).normalized() for a in others for b_ in others if (a - b_).length > 1e-4), key=lambda v: abs(v.dot(d)))
        p = base[k] - c; return (p - best * p.dot(best)).length, c, best
    thumb = max(base, key=lambda k: off_line(k)[0])
    _, c, line = off_line(thumb)
    rest = sorted((k for k in base if k != thumb), key=lambda k: (base[k] - base[thumb]).dot(line))
    # (the index is the finger on the thumb's side: nearest where the thumb ends, not where it starts, which lies half
    # way across the palm)
    tb = B[thumb]
    while tb.children: tb = tb.children[0]
    ttip = arm.matrix_world @ tb.tail_local
    if abs((base[rest[0]] - ttip).dot(line)) > abs((base[rest[-1]] - ttip).dot(line)): rest = rest[::-1]
    order = [thumb] + rest
    for fname, root in zip(("thumb", "index", "middle", "ring", "pinky"), order):
        b = B[root]; i = 1
        while b is not None:
            NAMES[b.name] = f"{fname}_{i:02d}_{s}"; i += 1
            b = b.children[0] if b.children else None
    fingers[s] = {f: o for f, o in zip(("thumb", "index", "middle", "ring", "pinky"), order)}
missing = [b.name for b in B if b.name not in NAMES]
assert not missing, missing
print("SUMMONER fingers", json.dumps(fingers))
# rename (the vertex groups follow their bones' names)
for old, new in NAMES.items():
    B[old].name = new
    g = mesh.vertex_groups.get(old)
    if g: g.name = new
print("SUMMONER bones", json.dumps(NAMES))
# a root bone at the floor under her
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.data.edit_bones
r = eb.new("root"); hip = eb["pelvis"].head.copy()
r.head = Vector((hip.x, hip.y, 0.0)); r.tail = Vector((hip.x, hip.y + 0.1, 0.0))
eb["pelvis"].parent = r
bpy.ops.object.mode_set(mode='OBJECT')
need = ["root", "pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head", "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l", "clavicle_r", "upperarm_r",
        "lowerarm_r", "hand_r", "thigh_l", "calf_l", "foot_l", "ball_l", "thigh_r", "calf_r", "foot_r", "ball_r"] + \
       [f"{f}_0{i}_{s}" for f in ("thumb", "index", "middle", "ring", "pinky") for i in (1, 2, 3) for s in "lr"]
print("SUMMONER mannequin bones present:", all(n in arm.data.bones for n in need), [n for n in need if n not in arm.data.bones])
if FACE:
    import importlib.util
    spec = importlib.util.spec_from_file_location("summoner_face", os.path.join(os.path.dirname(os.path.abspath(__file__)), "summoner_face.py"))
    sf = importlib.util.module_from_spec(spec); spec.loader.exec_module(sf)
    print("SUMMONER face shapes", sf.add_shapes(mesh, json.load(open(FACE))))
bpy.ops.object.select_all(action='DESELECT'); arm.select_set(True); mesh.select_set(True)
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=OUT, use_selection=True, export_format='GLB', export_animations=False, export_morph=True, export_skins=True)
print("SUMMONER written", OUT)
