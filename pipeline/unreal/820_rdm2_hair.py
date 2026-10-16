"""The Warlock's hair (random_dungeonmagic_level2's caster, character DarkCaster): her hair swings as she runs, stops, turns and
jumps. Tripo's rig has no hair bones and her hair was skinned to the head, neck and spine: it moved as one stiff piece.
Run after blender_numpy/tripo_build.py with SourceArt/jrpg_darkcaster/hair.json (tripo_hair.py: six chains through the
hair, the hair skinned to them; the clips are the same and get no keys for them):
- SK_JRPG_DarkCaster imported again from SourceArt/jrpg_darkcaster/SK_JRPG_DarkCaster.fbx onto her own skeleton (which
  gains the hair bones; her clips, AnimBP, retargeters and the characters stay as they are); her material put back
- ABP_DarkCaster_Hair: a post-process AnimBP for the mesh (it runs after whatever animates her: her locomotion AnimBP,
  the dungeon's montages, a sequencer track): Input Pose -> one AnimDynamics node per chain -> Output. Each chain's root
  bone stays on the head; the others are bodies hung one from the next (a body's centre half way down its bone, from the
  reference pose), with swing / twist limits, an angular spring back to the animated shape, damping, gravity, and spheres
  they are kept out of (her head, her upper back). The numbers: SourceArt/jrpg_darkcaster/hair_dynamics.json.
Idempotent. Args: [noimport] (the AnimBP only)"""
import os, sys, json, unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); APE = unreal.AnimPoseExtensions; ML = unreal.MathLibrary
V = unreal.Vector
SRC = r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_darkcaster"
C = G_C = json.load(open(os.path.join(SRC, "hair_dynamics.json")))
sk = unreal.load_asset(C["mesh"]); skel = sk.get_editor_property("skeleton")
mat = sk.get_editor_property("materials")[0].material_interface
n0 = len(APE.get_bone_names(APE.get_reference_pose(skel)))
# ---- the mesh, imported again onto her own skeleton
if "noimport" not in sys.argv:
    sk.set_editor_property("post_process_anim_blueprint", None); eal.save_loaded_asset(sk, only_if_is_dirty=False)
    t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, "SK_JRPG_DarkCaster.fbx"); t.destination_path = "/Game/JRPG/Character"
    t.automated = True; t.replace_existing = True; t.save = True
    o = unreal.FbxImportUI(); o.import_mesh = True; o.import_as_skeletal = True; o.import_animations = False; o.import_materials = False; o.import_textures = False
    o.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH; o.skeleton = skel; t.options = o
    at.import_asset_tasks([t])
    sk = unreal.load_asset(C["mesh"])
    assert sk.get_editor_property("skeleton") == skel, "the mesh got another skeleton"
    sk.set_editor_property("materials", [unreal.SkeletalMaterial(material_interface=mat, material_slot_name=str(s.get_editor_property("material_slot_name"))) for s in sk.get_editor_property("materials")])
    sk.modify(); eal.save_loaded_asset(sk, only_if_is_dirty=False); eal.save_loaded_asset(skel, only_if_is_dirty=False)
ref = APE.get_reference_pose(skel); names = [str(n) for n in APE.get_bone_names(ref)]
print("skeleton bones", n0, "->", len(names), "| hair bones", len([n for n in names if n.startswith("hair_")]), "| material", sk.get_editor_property("materials")[0].material_interface.get_name())
# The bones' rest places come from the MESH: an import onto an existing skeleton adds new bones to it but keeps its old
# reference pose for the bones it already had (the hair chains of an earlier build: a front lock's bodies were set up
# for bones twice as long as the mesh's, and stood at half their length). The mesh in a component without animation
# stands in its own reference pose.
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tmp = eas.spawn_actor_from_class(unreal.SkeletalMeshActor, V(0, 0, -100000), unreal.Rotator())
smc = tmp.skeletal_mesh_component; smc.set_skeletal_mesh_asset(sk); smc.set_world_location(V(0, 0, 0), False, True)
MREF = {n: smc.get_socket_transform(n, unreal.RelativeTransformSpace.RTS_COMPONENT) for n in names}
eas.destroy_actor(tmp)
stale = [n for n in names if n.startswith("hair_") and (MREF[n].translation - APE.get_bone_pose(ref, n, unreal.AnimPoseSpaces.WORLD).translation).length() > 0.5]
print("hair bones whose skeleton reference differs from the mesh's (the mesh's are used):", len(stale))
W = lambda b: MREF[b]
def fmt(v): return f"(X={v.x:.4f},Y={v.y:.4f},Z={v.z:.4f})"
AX = ("AxisX", "AxisY", "AxisZ")
# ---- one AnimDynamics node's settings per chain
def chain_text(ch, spheres, planes=()):
    C = dict(G_C); C.update(next((v for k, v in G_C.get("overrides", {}).items() if ch.startswith(k)), {}))      # (per chain: "overrides" by name prefix)
    spheres = [s for s in spheres if not s.get("chains") or any(ch.startswith(p) for p in s["chains"])]
    planes = [q for q in planes if not q.get("chains") or any(ch.startswith(p) for p in q["chains"])]
    bones = sorted([n for n in names if n.startswith(ch + "_") and n[len(ch) + 1:].isdigit()], key=lambda n: int(n.split("_")[-1]))
    sim = bones[1:]                                         # (_0 stays on the head)
    defs = []; centres = []
    for k, b in enumerate(sim):
        child = sim[k + 1] if k + 1 < len(sim) else ch + "_end"
        tf = W(b); d = W(child).translation - tf.translation
        off = ML.multiply_vector_float(ML.inverse_transform_direction(tf, d), 0.5)          # (the body's centre: half way down the bone)
        comps = [off.x, off.y, off.z]; ax = max(range(3), key=lambda i: abs(comps[i]))
        ext = [C["body_thickness_cm"]] * 3; ext[ax] = max(2.0 * abs(comps[ax]), C["body_thickness_cm"])
        tgt = [0.0, 0.0, 0.0]; tgt[ax] = 1.0 if comps[ax] > 0 else -1.0
        lim = [C["swing_deg"]] * 3; lim[ax] = C["twist_deg"]
        defs.append(f'(BoundBone=(BoneName="{b}"),BoxExtents=(X={ext[0]:.3f},Y={ext[1]:.3f},Z={ext[2]:.3f}),LocalJointOffset={fmt(off)},'
                    f'ConstraintSetup=(LinearXLimitType=Limited,LinearYLimitType=Limited,LinearZLimitType=Limited,LinearAxesMin=(X=0,Y=0,Z=0),LinearAxesMax=(X=0,Y=0,Z=0),'
                    f'AngularConstraintType=Angular,TwistAxis={AX[ax]},AngularTargetAxis={AX[ax]},ConeAngle=0,'
                    f'AngularLimitsMin=(X={-lim[0]:.2f},Y={-lim[1]:.2f},Z={-lim[2]:.2f}),AngularLimitsMax=(X={lim[0]:.2f},Y={lim[1]:.2f},Z={lim[2]:.2f}),'
                    f'AngularTarget=(X={tgt[0]:.1f},Y={tgt[1]:.1f},Z={tgt[2]:.1f})),CollisionType=CustomSphere,SphereCollisionRadius={C["collision_radius_cm"]:.2f})')
        centres.append(tf.translation + ML.quat_rotate_vector(tf.rotation, off))
    sph = []
    for s in spheres:
        btf = W(s["bone"]); c = V(*s["center_cm"])
        sph.append(f'(DrivingBone=(BoneName="{s["bone"]}"),SphereLocalOffset={fmt(ML.inverse_transform_location(btf, c))},LimitRadius={s["radius"]:.3f},LimitType=Outer)')
    pln = []
    for q in planes:
        # (a plane's normal is its transform's Z axis, in the driving bone's space; bodies stay on that side)
        btf = W(q["bone"]); nl = ML.inverse_transform_direction(btf, V(*q["normal"])).normal(); pt = ML.inverse_transform_location(btf, q["point"])
        r = ML.make_rot_from_z(nl).quaternion()
        pln.append(f'(DrivingBone=(BoneName="{q["bone"]}"),PlaneTransform=(Rotation=(X={r.x:.6f},Y={r.y:.6f},Z={r.z:.6f},W={r.w:.6f}),Translation={fmt(pt)},Scale3D=(X=1,Y=1,Z=1)))')
    txt = (f'BoundBone=(BoneName="{sim[0]}"),ChainEnd=(BoneName="{sim[-1]}"),bChain=True,PhysicsBodyDefinitions=({",".join(defs)}),'
           f'SimulationSpace={C["space"]},GravityScale={C["gravity_scale"]:.3f},bAngularSpring=True,AngularSpringConstant={C["angular_spring"]:.3f},'
           f'bOverrideLinearDamping=True,LinearDampingOverride={C["linear_damping"]:.3f},bOverrideAngularDamping=True,AngularDampingOverride={C["angular_damping"]:.3f},'
           f'bUsePlanarLimit={bool(pln)},PlanarLimits=({",".join(pln)}),bUseSphericalLimits={bool(sph) and C.get("use_spheres", True)},SphericalLimits=({",".join(sph)}),'
           f'ComponentLinearAccScale={fmt(V(*C.get("component_acc_scale", (0, 0, 0))))},ComponentAppliedLinearAccClamp={fmt(V(*C.get("component_acc_clamp", (100000, 100000, 100000))))},ComponentLinearVelScale={fmt(V(*C.get("component_vel_scale", (0, 0, 0))))},'
           f'SimSpaceSettings=(SimSpaceAngularAlpha={C.get("angular_alpha", 0.0):.3f},MaxAngularVelocity=10000.0,MaxAngularAcceleration=10000.0),'
           f'NumSolverIterationsPreUpdate={C.get("solver_iterations", (4, 1))[0]},NumSolverIterationsPostUpdate={C.get("solver_iterations", (4, 1))[1]}')
    return txt, sim, centres
# the spheres: a sphere that would hold a body of the rest pose is shrunk to clear it
allc = {}
for ch in C["chains"]: allc[ch] = chain_text(ch, [])[2]
spheres = []
for s in C["spheres"]:
    c = V(*s["center_cm"]); mine = [p for ch, v in allc.items() if not s.get("chains") or any(ch.startswith(q) for q in s["chains"]) for p in v]
    need = min((p - c).length() for p in mine) - C["collision_radius_cm"] - C["margin_cm"]
    spheres.append(dict(s, radius=min(s["radius_cm"], need))); print(f"sphere on {s['bone']}: radius {s['radius_cm']:.1f} -> {min(s['radius_cm'], need):.1f} cm (nearest body centre {need + C['collision_radius_cm'] + C['margin_cm']:.1f} cm)")
# the planes: as close under the hair as its rest pose allows (its nearest body centre, less the collision radius and the margin)
planes = []
for q in C.get("planes", []):
    n_ = V(*q["normal_cm"]).normal(); mine = [p for ch, v in allc.items() if not q.get("chains") or any(ch.startswith(s_) for s_ in q["chains"]) for p in v]
    d = min(p.dot(n_) for p in mine) - C["collision_radius_cm"] - C["margin_cm"]
    o = W(q["bone"]).translation; pt = o + n_ * (d - o.dot(n_))
    planes.append(dict(q, normal=q["normal_cm"], point=pt)); print(f"plane on {q['bone']}: normal {q['normal_cm']}, {d - o.dot(n_):+.1f} cm from the bone along it")
# ---- the post-process AnimBP
P = C["abp"]; folder, name = P.rsplit("/", 1)
# (an AnimBP deleted while loaded and made again under its name comes back without its graphs: it is emptied instead)
if eal.does_asset_exist(P): abp = unreal.load_asset(P)
else:
    f = unreal.AnimBlueprintFactory(); f.set_editor_property("target_skeleton", skel)
    abp = at.create_asset(name, folder, unreal.AnimBlueprint, f)
ag = {g.get_name(): g for g in T.list_graphs(abp)}["AnimGraph"]
# (the Input Pose node stays: one made again is not the graph's input any more, and the pose that came out was the
# reference pose, her T-pose)
for n in T.find_nodes(ag, ""):
    if n.get_class().get_name() not in ("AnimGraphNode_Root", "AnimGraphNode_LinkedInputPose"): T.delete_node(n)
for n in T.find_nodes(ag, ""):
    if n.get_class().get_name() == "AnimGraphNode_LinkedInputPose":
        for p in T.get_node_infos([n])[0].output_pins:
            for q in p.get_editor_property("connected_pins"): T.break_pins(p.pin_id, q)
def pin(n, nm, out):
    i = T.get_node_infos([n])[0]
    for p in (i.output_pins if out else i.input_pins):
        if str(p.name) == nm: return p.pin_id
    raise KeyError(nm)
root = [n for n in T.find_nodes(ag, "") if n.get_class().get_name() == "AnimGraphNode_Root"][0]
old_in = [n for n in T.find_nodes(ag, "") if n.get_class().get_name() == "AnimGraphNode_LinkedInputPose"]
prev = old_in[0] if old_in else T.create_node(ag, "Animation|LinkedAnimGraphs|InputPose", unreal.IntPoint(-1800, 0))
l2c = T.create_node(ag, "Animation|ConvertSpaces|LocalToComponent", unreal.IntPoint(-1550, 0))
T.connect_pins(pin(prev, "Pose", True), pin(l2c, "LocalPose", False)); prev, pname = l2c, "ComponentPose"
report = {}
for k, ch in enumerate(C["chains"]):
    txt, sim, cen = chain_text(ch, spheres, planes)
    n = T.create_node(ag, "Animation|Dynamics|AnimDynamics", unreal.IntPoint(-1300 + 220 * k, 0))
    nd = n.get_editor_property("node"); r = nd.import_text("(" + txt + ")"); n.set_editor_property("node", nd)      # (a struct's text is in parentheses)
    assert f'BoundBone=(BoneName="{sim[0]}")' in n.get_editor_property("node").export_text(), ("settings not taken", ch, r)
    T.connect_pins(pin(prev, pname, True), pin(n, "ComponentPose", False)); prev, pname = n, "Pose"
    report[ch] = sim
c2l = T.create_node(ag, "Animation|ConvertSpaces|ComponentToLocal", unreal.IntPoint(-1300 + 220 * len(C["chains"]), 0))
T.connect_pins(pin(prev, pname, True), pin(c2l, "ComponentPose", False))
T.connect_pins(pin(c2l, "Pose", True), pin(root, "Result", False))
ok = unreal.BlueprintEditorLibrary.compile_blueprint(abp); eal.save_loaded_asset(abp, only_if_is_dirty=False)
# (read back what the compiled nodes hold)
back = []
for n in T.find_nodes(ag, ""):
    if n.get_class().get_name() == "AnimGraphNode_AnimDynamics":
        t_ = n.get_editor_property("node").export_text()
        back.append((t_.split('BoundBone=(BoneName="')[1].split('"')[0], t_.count("LocalJointOffset="), "SimulationSpace=World" in t_, t_.count("LimitType=Outer")))
sk = unreal.load_asset(C["mesh"]); sk.set_editor_property("post_process_anim_blueprint", abp.generated_class()); sk.modify(); eal.save_loaded_asset(sk, only_if_is_dirty=False)
# (the tests measure against the mesh's rest places too)
LIM = {"_spheres": [{"bone": s["bone"], "local": list((lambda v: (v.x, v.y, v.z))(ML.inverse_transform_location(W(s["bone"]), V(*s["center_cm"])))), "radius": s["radius"], "chains": s.get("chains")} for s in spheres],
       "_planes": [{"bone": q["bone"], "local_point": list((lambda v: (v.x, v.y, v.z))(ML.inverse_transform_location(W(q["bone"]), q["point"]))),
                    "local_normal": list((lambda v: (v.x, v.y, v.z))(ML.inverse_transform_direction(W(q["bone"]), V(*q["normal"])).normal())), "chains": q.get("chains")} for q in planes]}
json.dump(dict({n: {"t": [MREF[n].translation.x, MREF[n].translation.y, MREF[n].translation.z], "q": [MREF[n].rotation.x, MREF[n].rotation.y, MREF[n].rotation.z, MREF[n].rotation.w]}
                for n in names if n.startswith("hair_")}, **LIM), open(os.path.join(SRC, "hair_ref.json"), "w"), indent=0)
print("ABP", P, "compile", ok, "| chains", {k: v for k, v in report.items()}, "| read back (bound bone, bodies, world space, spheres)", back,
      "| mesh post-process", unreal.load_asset(C["mesh"]).get_editor_property("post_process_anim_blueprint").get_name())
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
