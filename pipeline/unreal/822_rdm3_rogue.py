"""random_dungeonmagic_level3: the Rogue (ai models/Rogue.glb, character Rogue of 600-620): a dagger in each hand, a
crossbow, a roll. Run after 600 / 610 / 615 / 620 for Rogue (her mesh, her own Walk / Run with both hands closed on a
grip, and the Idle, stabs, shot and rolls that blender_numpy/rogue_clips.py made for her).
- her flinch and death: Animations_Warrior's Get_Hit_1 and Dead_1 retargeted onto her rig, as 817 does
- the daggers: Medieval_Weapons SM_Dagger in each hand, held as 817 holds the sword: the grip computed from her reference
  pose (arms out, palms down), the handle across the closed hand at a slant: the blade the way her THUMB points there (from
  her own thumb and finger bones) leaning toward her fingers by rogue_clips.py's GRIP_TILT (times.json's grip_tilt; the
  clips aim the blade as near as her wrist allows). Stab1 (right), Stab2 (left), Stab3 (both): the
  blow lands where the striking hand moves fastest; 15 damage, 1.5 m reach, a 110 degree arc. Carried on her thighs
  (blade down along the outside of each thigh) while the crossbow is drawn
- the crossbow: Medieval_Weapons SM_Crossbow (its front is the mesh's -X, the rail on top +Z) in her right hand, the stock
  through the closed hand along the thumb, slanting toward the fingers as the dagger does (by its own GRIP_TILT), the rail
  on the side away from her fingers; a spell weapon whose bolt is a
  mesh (SM_Arrow_Var1 cut down to a 37 cm bolt) shot from the front of the rail (bBoltFromWeapon) straight at the
  monster she turned to (BoltTurnRate 0), 34 damage, 26 m, 45 m/s, no splash; the next bolt lies on the rail until the
  shot is over; a bolt that strikes a wall stays there 8 s. The shot leaves at the release of her Shoot clip
  (SourceArt/jrpg_rogue/times.json: no hand speed marks it). A copy of the Medieval_Weapons arrow trail flies with it
  (P_RDM3_BoltTrail: the pack's is 2 cm wide at 13 % alpha, nothing to see on a bolt; tuned as 800 tunes its
  contrails: 3 cm, pale, 0.1 s: 4.5 m behind the bolt, a point every 20 cm instead of 2.5 m), the pack's P_Impact sparks
  where it strikes (MagicProjectilesVol4's arrow hits are blue magic). Carried on her back while the daggers are drawn
- BP_RDM3_RogueCharacter (child of BP_JRPGRogueCharacter with a 36 cm capsule) and BP_RDM3_GameMode (BP_RD_GameMode with
  her as the pawn)
Writes SourceArt/random_dungeon_magic3/weapons.json for 823. Idempotent. Args: none"""
import json, math, os, unreal
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions; ML = unreal.MathLibrary
V = unreal.Vector
CH = "Rogue"
OUT = "/Game/RandomDungeon/Magic3"; ANIMS = OUT + "/Anims"; RIGS = OUT + "/Rigs"
JSON = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_magic3\weapons.json"
TIMES = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_rogue\times.json"))
tgt_mesh = unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{CH}"); tgt_rig = unreal.load_asset(f"/Game/JRPG/Rigs/IK_JRPG_{CH}_Auto")
assert tgt_mesh and tgt_rig, "run 600-620 for Rogue first"
PACK, PREFIX, FLINCH, DEATH = "Animations_Warrior", "Anim_Warrior_", "Get_Hit_1", "Dead_1"
MW = "/Game/Medieval_Weapons"
DAGGER = {"name": "Daggers", "mesh": f"{MW}/Meshes/VOL2/SM_Dagger", "hand_z": 28.5, "damage": 15.0, "reach": 150.0, "arc": 110.0, "rate": 1.0,
          "clips": [("Stab1", ["hand_r"]), ("Stab2", ["hand_l"]), ("Stab3", ["hand_r", "hand_l"])], "after": 0.24}
XBOW = {"name": "Crossbow", "mesh": f"{MW}/Meshes/VOL2/SM_Crossbow", "grip": (31.0, 0.0, 0.5), "damage": 34.0, "reach": 2600.0, "speed": 4500.0,
        "bolt": f"{MW}/Meshes/VOL2/SM_Arrow_Var1", "bolt_tip_z": 48.28, "bolt_len_scale": 0.42, "bolt_thick": 0.8,
        "muzzle": (-32.0, 0.0, 5.6), "loaded_tip": (-30.0, 0.0, 5.6), "trail": "/Game/RandomDungeon/Magic3/FX/P_RDM3_BoltTrail", "trail_scale": 1.0,
        "trail_from": f"{MW}/VFX/P_ArrowTrail", "trail_tune": (3.0, (1.3, 1.2, 1.0, 0.4), 0.10),
        "hit": f"{MW}/VFX/P_Impact", "hit_scale": 1.0, "stick": 8.0}
def make(cls, fac, name, folder):
    p = f"{folder}/{name}"
    if eal.does_asset_exist(p): eal.delete_asset(p)
    return at.create_asset(name, folder, cls, fac) or unreal.load_asset(p)
ar = unreal.AssetRegistryHelpers.get_asset_registry()
def find(pack, name):
    for a in ar.get_assets_by_path("/Game/" + pack, recursive=True):
        if str(a.asset_name) == name and str(a.asset_class_path.asset_name) == "AnimSequence": return a
    raise RuntimeError(f"{pack}: no clip {name}")
o = unreal.AnimPoseEvaluationOptions()
def fastest(anim, bones, after=0.0):
    """length, and the time one of the hands moves fastest (relative to the pelvis) after the wind-up: where the blow lands
    (the hand going up to strike, fast in a backhand and a cut from above, is not the blow)"""
    L = unreal.AnimationLibrary.get_sequence_length(anim); n = max(30, int(L * 60)); best = (0.0, 0.0)
    for bone in bones:
        pts = []
        for k in range(n + 1):
            p = APE.get_anim_pose_at_time(anim, L * k / n, o)
            h = APE.get_bone_pose(p, bone, unreal.AnimPoseSpaces.WORLD).translation; q = APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.WORLD).translation
            pts.append(V(h.x - q.x, h.y - q.y, h.z - q.z))
        sp = [(pts[k + 1] - pts[k]).length() / (L / n) for k in range(n)]
        sm = [sum(sp[max(0, k - 2):k + 3]) / len(sp[max(0, k - 2):k + 3]) for k in range(n)]
        k = max((i for i in range(n) if L * (i + 0.5) / n >= after), key=lambda i: sm[i])
        if sm[k] > best[1]: best = (L * (k + 0.5) / n, sm[k])
    return L, best[0], best[1]
# ---- the reference pose (component space: she faces +Y, her right arm points along -X)
ref = APE.get_reference_pose(tgt_mesh.skeleton)
bone = lambda n: APE.get_bone_pose(ref, n, unreal.AnimPoseSpaces.WORLD)
def xf(t): r = t.rotation.rotator(); return {"loc": [t.translation.x, t.translation.y, t.translation.z], "rot": [r.roll, r.pitch, r.yaw], "scale": [t.scale3d.x, t.scale3d.y, t.scale3d.z]}
def mesh_verts(path):
    m = unreal.load_asset(path); vs = []
    for sec in range(m.get_num_sections(0)): vs += list(unreal.ProceduralMeshLibrary.get_section_from_static_mesh(m, 0, sec)[0])
    return m, vs
def handle_end(path, hand_z):
    m, vs = mesh_verts(path)
    s = [v for v in vs if abs(v.z - hand_z) <= 3.0]
    assert s, f"{path}: nothing of the mesh at z {hand_z}"
    ex = max(v.x for v in s) - min(v.x for v in s); ey = max(v.y for v in s) - min(v.y for v in s)
    assert max(ex, ey) < 7.5 and max(ex, ey) < 1.8 * max(min(ex, ey), 0.1), f"{path}: no handle at z {hand_z}"
    b = m.get_bounding_box()
    return 1.0 if b.max.z - hand_z >= hand_z - b.min.z else -1.0
def hand_frame(s):
    """the closed hand on the reference pose: the palm point, the forearm's way and the thumb's way (square to it)"""
    hand = bone(f"hand_{s}"); h = hand.translation
    fore = (h - bone(f"lowerarm_{s}").translation).normal()
    th = bone(f"thumb_01_{s}").translation - h; along = (bone(f"middle_01_{s}").translation - h).normal()
    th = th - along * th.dot(along); th = (th - fore * th.dot(fore)).normal()
    return hand, h + fore * 6.5 + V(0, 0, -2.5), fore, th
TILT = TIMES["grip_tilt"]          # (rogue_clips.py's: the handle and the stock slant across the palm, the blade and the front lean toward the fingers)
def slant(th, fore, deg):
    g = math.radians(deg); return (th * math.cos(g) + fore * math.sin(g)).normal()
def dagger_grip(s):
    hand, palm, fore, th = hand_frame(s)
    rot = ML.make_rot_from_zx(slant(th, fore, TILT["dagger"]) * handle_end(DAGGER["mesh"], DAGGER["hand_z"]), fore)
    return ML.make_relative_transform(unreal.Transform(palm - ML.get_up_vector(rot) * DAGGER["hand_z"], rot, V(1, 1, 1)), hand), th
def crossbow_grip():
    hand, palm, fore, th = hand_frame("r")
    g = math.radians(TILT["crossbow"])
    rot = ML.make_rot_from_xz(slant(th, fore, TILT["crossbow"]) * -1.0, th * math.sin(g) - fore * math.cos(g))   # (the front, -X; the rail, +Z, away from the fingers. NB -v negates v in place)
    g = XBOW["grip"]; X, Z = ML.get_forward_vector(rot), ML.get_up_vector(rot)
    return ML.make_relative_transform(unreal.Transform(palm - X * g[0] - Z * g[2], rot, V(1, 1, 1)), hand), th
def holster_thigh(s):
    """a dagger along the outside of a thigh, blade down, the guard by the top of the thigh"""
    th = bone(f"thigh_{s}"); down = (bone(f"calf_{s}").translation - th.translation).normal()
    out = V(-1, 0, 0) if s == "r" else V(1, 0, 0); out = (out - down * out.dot(down)).normal()
    rot = ML.make_rot_from_zy(down * -1.0, out)
    at_ = th.translation + down * 16.0 + out * 8.5 + V(0, 2.0, 0)
    return ML.make_relative_transform(unreal.Transform(at_ - ML.get_up_vector(rot) * 20.0, rot, V(1, 1, 1)), th)
def holster_back():
    """the crossbow across her back: its front down toward her left hip, the rail against her, the limbs flat on her back"""
    sp = bone("spine_03"); back = V(0, -1, 0)
    front = (V(0, 0, -1) * 0.82 + V(1, 0, 0) * 0.57).normal()
    rot = ML.make_rot_from_xz(front * -1.0, back * -1.0)
    at_ = sp.translation + back * 25.0 + V(0, 0, -6.0)
    return ML.make_relative_transform(unreal.Transform(at_ - ML.get_forward_vector(rot) * 4.0, rot, V(1, 1, 1)), sp)
def bolt_transform():
    """the bolt mesh in the bolt's frame: its head (+Z of the arrow mesh) along +X, the point at the origin, cut down"""
    rot = ML.make_rot_from_zx(V(1, 0, 0), V(0, 0, -1))
    s = V(XBOW["bolt_thick"], XBOW["bolt_thick"], XBOW["bolt_len_scale"])
    return unreal.Transform(V(-XBOW["bolt_tip_z"] * XBOW["bolt_len_scale"], 0, 0), rot, s)
# ---- flinch and death
src_mesh = unreal.load_asset(f"/Game/{PACK}/Mesh/SK_Mannequin"); assert src_mesh, PACK
rig = make(unreal.IKRigDefinition, unreal.IKRigDefinitionFactory(), "IK_RDM3_Warrior_Source", RIGS)
c = unreal.IKRigController.get_controller(rig); c.set_skeletal_mesh(src_mesh); ok = c.apply_auto_generated_retarget_definition()
try: c.apply_auto_fbik()
except Exception: pass
eal.save_loaded_asset(rig)
rtg = make(unreal.IKRetargeter, unreal.IKRetargetFactory(), f"RTG_RDM3_Warrior_To_{CH}", RIGS)
rc = unreal.IKRetargeterController.get_controller(rtg)
rc.add_default_ops()
rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, rig); rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
rc.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, src_mesh); rc.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, tgt_mesh)
rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, rig); rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
rm = rc.get_op_controller(rc.get_index_of_op_by_name("Root Motion"))
rm.set_source_root_bone("root"); rm.set_target_root_bone("root"); rm.set_target_pelvis_bone("pelvis")
try: rc.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
except Exception as e: print("  align", e)
eal.save_loaded_asset(rtg)
names = [PREFIX + FLINCH, PREFIX + DEATH]
for n in names:
    if eal.does_asset_exist(f"{ANIMS}/{n}_{CH}"): eal.delete_asset(f"{ANIMS}/{n}_{CH}")
inp = unreal.IKRetargetBatchOperationInputs()
inp.set_editor_property("assets_to_retarget", [find(PACK, n) for n in names])
inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", "_" + CH)
inp.set_editor_property("target_path", ANIMS); inp.set_editor_property("include_referenced_assets", False)
inp.set_editor_property("overwrite_existing_files", True)
unreal.IKRetargetBatchOperation.run_batch_retarget(inp)
for n in names:
    p = f"{ANIMS}/{n}_{CH}"; a = unreal.load_asset(p); assert a, p
    a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
flinch, death = f"{ANIMS}/{PREFIX}{FLINCH}_{CH}", f"{ANIMS}/{PREFIX}{DEATH}_{CH}"
def clip(n):
    p = f"/Game/JRPG/{CH}Anims/AS_{CH}_{n}"; a = unreal.load_asset(p); assert a, p
    a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
    return p, a
attacks = []
for n, hands in DAGGER["clips"]:
    p, a = clip(n); L, hit, speed = fastest(a, hands, TIMES["Stabs"][n]["wind"])
    attacks.append({"clip": p, "length": round(L, 3), "hit": round(hit, 3), "end": round(min(L, hit + DAGGER["after"]), 3), "hand_speed": round(speed)})
gr, thr = dagger_grip("r"); gl, thl = dagger_grip("l")
daggers = {k: DAGGER[k] for k in ("name", "mesh", "damage", "reach", "arc", "rate")}
daggers.update({"grip": xf(gr), "hand_bone": "hand_r", "off_mesh": DAGGER["mesh"], "off_bone": "hand_l", "off_grip": xf(gl), "attacks": attacks,
                "holster_bone": "thigh_r", "holster": xf(holster_thigh("r")), "off_holster_bone": "thigh_l", "off_holster": xf(holster_thigh("l")),
                "flinch": flinch, "death": death})
p, a = clip("Shoot"); L = unreal.AnimationLibrary.get_sequence_length(a)
xg, _ = crossbow_grip()
bt = bolt_transform()
lt = ML.compose_transforms(bt, unreal.Transform(V(*XBOW["loaded_tip"]), unreal.Rotator(roll=0, pitch=0, yaw=180), V(1, 1, 1)))
crossbow = {"name": XBOW["name"], "mesh": XBOW["mesh"], "damage": XBOW["damage"], "reach": XBOW["reach"], "arc": 0.0, "rate": 1.0, "spell": True,
            "grip": xf(xg), "hand_bone": "hand_r",
            "attacks": [{"clip": p, "length": round(L, 3), "hit": TIMES["Shoot"]["release"], "end": round(min(L, TIMES["Shoot"]["length"]), 3)}],
            "bolt_speed": XBOW["speed"], "bolt_turn": 0.0, "splash": 0.0, "bolt_mesh": XBOW["bolt"], "bolt_xf": xf(bt), "muzzle": list(XBOW["muzzle"]),
            "loaded_xf": xf(lt), "stick": XBOW["stick"], "trail": XBOW["trail"], "trail_scale": XBOW["trail_scale"], "hit_fx": XBOW["hit"], "hit_scale": XBOW["hit_scale"],
            "holster_bone": "spine_03", "holster": xf(holster_back()), "flinch": flinch, "death": death}
for k in ("hit_fx", "bolt_mesh", "mesh"): assert unreal.load_asset(crossbow[k]), crossbow[k]
# the bolt's trail: a tuned copy of the pack's arrow trail (the Starship module's tuner, as 800's contrails)
if not eal.does_asset_exist(XBOW["trail"]): assert eal.duplicate_asset(XBOW["trail_from"], XBOW["trail"]), XBOW["trail"]
ps = unreal.load_asset(XBOW["trail"]); sz, col, life = XBOW["trail_tune"]
n = unreal.SSFXLibrary.tune_particle_system(ps, sz, unreal.LinearColor(*col), life, None); assert n >= 3, f"trail: only {n} modules tuned"
# (the pack's trail spawns a point every 2.5 m: a 5 m shot had two at most, often none alive in a frame; every 20 cm, and one
# where it starts)
n = unreal.SSFXLibrary.set_spawn_per_unit(ps, 20.0, True); assert n >= 2, f"trail: spawn per unit set on {n} modules"
eal.save_loaded_asset(ps, only_if_is_dirty=False)
rolls = {"forward": clip("RollF")[0], "back": clip("RollB")[0], "length": TIMES["Roll"]["length"]}
res = {"order": ["Daggers", "Crossbow"], "weapons": {"Daggers": daggers, "Crossbow": crossbow}, "roll": rolls,
       "thumb_check": {"r": [round(v, 3) for v in (thr.x, thr.y, thr.z)], "l": [round(v, 3) for v in (thl.x, thl.y, thl.z)]}}
os.makedirs(os.path.dirname(JSON), exist_ok=True); json.dump(res, open(JSON, "w"), indent=1)
print("RDM3 Daggers: " + ", ".join(f"{os.path.basename(x['clip'])} at {x['hit']:.2f} s (hand {x['hand_speed']} cm/s), cut at {x['end']:.2f} of {x['length']:.2f}" for x in attacks))
print("RDM3 Crossbow: shot at", crossbow["attacks"][0]["hit"], "of", crossbow["attacks"][0]["length"], "| thumbs (component space)", res["thumb_check"])
# ---- her dungeon character and game mode
G = "/Game/RandomDungeon/Blueprints"; CHP = f"{G}/BP_RDM3_RogueCharacter"; GM = f"{G}/BP_RDM3_GameMode"
PARENT = unreal.load_asset(f"/Game/JRPG/Game/BP_JRPG{CH}Character").generated_class()
if not eal.does_asset_exist(CHP):
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", PARENT)
    at.create_asset("BP_RDM3_RogueCharacter", G, unreal.Blueprint, f)
chbp = unreal.load_asset(CHP)
if unreal.BlueprintEditorLibrary.get_blueprint_parent_class(chbp) != PARENT:
    # (620 deletes and makes BP_JRPG<CH>Character again: the editor hands its children to the class above it)
    print("RDM3 reparented", chbp.get_name(), "from", unreal.BlueprintEditorLibrary.get_blueprint_parent_class(chbp).get_name())
    unreal.BlueprintEditorLibrary.reparent_blueprint(chbp, PARENT)
unreal.BlueprintEditorLibrary.compile_blueprint(chbp)
unreal.get_default_object(chbp.generated_class()).get_component_by_class(unreal.CapsuleComponent).set_editor_property("capsule_radius", 36.0)
unreal.BlueprintEditorLibrary.compile_blueprint(chbp); eal.save_loaded_asset(chbp, only_if_is_dirty=False)
if eal.does_asset_exist(GM): eal.delete_asset(GM)
gm = eal.duplicate_asset(f"{G}/BP_RD_GameMode", GM); unreal.get_default_object(gm.generated_class()).set_editor_property("default_pawn_class", chbp.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(gm); eal.save_loaded_asset(gm, only_if_is_dirty=False)
print("RDM3", GM, "-> pawn", unreal.get_default_object(unreal.load_asset(GM).generated_class()).get_editor_property("default_pawn_class").get_name(), "| retarget rig ok", ok, "| saved", JSON)
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
