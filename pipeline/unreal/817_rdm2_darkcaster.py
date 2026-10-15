"""random_dungeonmagic_level2: the dark caster (girl-darkcaster-tripo, character DarkCaster of 600-620): a sword in her
right hand, fire from her left. Run after 600 / 610 / 615 / 620 for DarkCaster (her mesh, her own Idle / Walk / Run with
the right hand closed on the hilt, and the casts and cuts blender_numpy/darkcaster_clips.py made for her).
- her flinch and death: Animations_Warrior's Get_Hit_1 and Dead_1 retargeted onto her rig (IK_JRPG_DarkCaster_Auto), as
  810 does for the caster
- the sword: Medieval_Weapons SM_Sword_1 (random_dungeoncombat_level's), held as 790 holds it, the grip computed from her
  reference pose (arms out, palms down: the handle across the closed hand, the blade the way the thumb points). Its cuts
  (Slash1-3): the blow lands where her right hand moves fastest; 22 damage, 1.7 m reach, a 130 degree arc
- the fire spell, cast with its own keys while the sword stays in her hand (bAlongside), from her LEFT hand: CastL1 and
  CastL2, the bolt leaving where her left hand moves fastest; the numbers and effects of the caster's (810's spell.json:
  14 m, 25 damage, half on the monsters by the burst; the warm DarkHalls fire, the Starter Content explosion)
- BP_RDM2_DarkCasterCharacter (child of BP_JRPGDarkCasterCharacter with a 36 cm capsule) and BP_RDM2_GameMode
  (BP_RD_GameMode with her as the pawn)
Writes SourceArt/random_dungeon_magic2/weapons.json for 818. Idempotent. Args: none"""
import json, os, unreal
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions; ML = unreal.MathLibrary
V = unreal.Vector
CH = "DarkCaster"
OUT = "/Game/RandomDungeon/Magic2"; ANIMS = OUT + "/Anims"; RIGS = OUT + "/Rigs"
JSON = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_magic2\weapons.json"
SPELL1 = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_magic\spell.json"
tgt_mesh = unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{CH}"); tgt_rig = unreal.load_asset(f"/Game/JRPG/Rigs/IK_JRPG_{CH}_Auto")
assert tgt_mesh and tgt_rig, "run 600-620 for DarkCaster first"
PACK, PREFIX, FLINCH, DEATH = "Animations_Warrior", "Anim_Warrior_", "Get_Hit_1", "Dead_1"
SWORD = {"name": "Sword", "mesh": "/Game/Medieval_Weapons/Meshes/VOL2/SM_Sword_1", "hand_z": 69.0, "damage": 22.0, "reach": 170.0, "arc": 130.0, "rate": 1.15,
         "clips": ["Slash1", "Slash2", "Slash3"], "after": 0.36}
CASTS, CAST_AFTER = ["CastL1", "CastL2"], 0.42
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
def fastest(anim, bone):
    """length, and the time the hand moves fastest (relative to the pelvis): where the blow lands or the bolt leaves"""
    L = unreal.AnimationLibrary.get_sequence_length(anim); n = max(30, int(L * 60)); pts = []
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(anim, L * k / n, o)
        h = APE.get_bone_pose(p, bone, unreal.AnimPoseSpaces.WORLD).translation; q = APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.WORLD).translation
        pts.append(V(h.x - q.x, h.y - q.y, h.z - q.z))
    sp = [(pts[k + 1] - pts[k]).length() / (L / n) for k in range(n)]
    sm = [sum(sp[max(0, k - 2):k + 3]) / len(sp[max(0, k - 2):k + 3]) for k in range(n)]
    k = max(range(n), key=lambda i: sm[i])
    return L, L * (k + 0.5) / n, sm[k]
# ---- the grip, from her reference pose (component space: she faces +Y, her right arm points along -X), as 790's
ref = APE.get_reference_pose(tgt_mesh.skeleton)
bone = lambda n: APE.get_bone_pose(ref, n, unreal.AnimPoseSpaces.WORLD)
def xf(t): r = t.rotation.rotator(); return {"loc": [t.translation.x, t.translation.y, t.translation.z], "rot": [r.roll, r.pitch, r.yaw], "scale": [t.scale3d.x, t.scale3d.y, t.scale3d.z]}
def handle_end(path, hand_z):
    m = unreal.load_asset(path); vs = []
    for sec in range(m.get_num_sections(0)): vs += list(unreal.ProceduralMeshLibrary.get_section_from_static_mesh(m, 0, sec)[0])
    s = [v for v in vs if abs(v.z - hand_z) <= 3.0]
    assert s, f"{path}: nothing of the mesh at z {hand_z}"
    ex = max(v.x for v in s) - min(v.x for v in s); ey = max(v.y for v in s) - min(v.y for v in s)
    assert max(ex, ey) < 7.5 and max(ex, ey) < 1.8 * max(min(ex, ey), 0.1), f"{path}: no handle at z {hand_z}"
    b = m.get_bounding_box()
    return 1.0 if b.max.z - hand_z >= hand_z - b.min.z else -1.0
def weapon_grip(path, hand_z):
    hand = bone("hand_r"); fore = (hand.translation - bone("lowerarm_r").translation).normal()
    thumb = V(0, 1, 0); thumb = (thumb - fore * thumb.dot(fore)).normal()
    palm = hand.translation + fore * 6.5 + V(0, 0, -2.5)        # (in the closed hand: past the wrist, a little under the bones)
    rot = ML.make_rot_from_xz(fore, thumb * handle_end(path, hand_z))
    return ML.make_relative_transform(unreal.Transform(palm - ML.get_up_vector(rot) * hand_z, rot, V(1, 1, 1)), hand)
# ---- flinch and death
src_mesh = unreal.load_asset(f"/Game/{PACK}/Mesh/SK_Mannequin"); assert src_mesh, PACK
rig = make(unreal.IKRigDefinition, unreal.IKRigDefinitionFactory(), "IK_RDM2_Warrior_Source", RIGS)
c = unreal.IKRigController.get_controller(rig); c.set_skeletal_mesh(src_mesh); ok = c.apply_auto_generated_retarget_definition()
try: c.apply_auto_fbik()
except Exception: pass
eal.save_loaded_asset(rig)
rtg = make(unreal.IKRetargeter, unreal.IKRetargetFactory(), f"RTG_RDM2_Warrior_To_{CH}", RIGS)
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
def clips(names_, hand, after):
    out = []
    for n in names_:
        p = f"/Game/JRPG/{CH}Anims/AS_{CH}_{n}"; a = unreal.load_asset(p); assert a, p
        a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
        L, hit, speed = fastest(a, hand)
        out.append({"clip": p, "length": round(L, 3), "hit": round(hit, 3), "end": round(min(L, hit + after), 3), "hand_speed": round(speed)})
    return out
sword = {k: SWORD[k] for k in ("name", "mesh", "damage", "reach", "arc", "rate")}
sword.update({"grip": xf(weapon_grip(SWORD["mesh"], SWORD["hand_z"])), "hand_bone": "hand_r", "attacks": clips(SWORD["clips"], "hand_r", SWORD["after"]), "flinch": flinch, "death": death})
spell = json.load(open(SPELL1)); spell.update({"bone": "hand_l", "alongside": True, "casts": clips(CASTS, "hand_l", CAST_AFTER), "flinch": flinch, "death": death})
res = {"order": ["Sword", "Fire"], "weapons": {"Sword": sword, "Fire": spell}}
os.makedirs(os.path.dirname(JSON), exist_ok=True); json.dump(res, open(JSON, "w"), indent=1)
for n, e in (("Sword", sword["attacks"]), ("Fire", spell["casts"])):
    print(f"RDM2 {n}: " + ", ".join(f"{os.path.basename(x['clip'])} at {x['hit']:.2f} s (hand {x['hand_speed']} cm/s), cut at {x['end']:.2f} of {x['length']:.2f}" for x in e))
# ---- her dungeon character and game mode
G = "/Game/RandomDungeon/Blueprints"; CHP = f"{G}/BP_RDM2_DarkCasterCharacter"; GM = f"{G}/BP_RDM2_GameMode"
if not eal.does_asset_exist(CHP):
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.load_asset(f"/Game/JRPG/Game/BP_JRPG{CH}Character").generated_class())
    at.create_asset("BP_RDM2_DarkCasterCharacter", G, unreal.Blueprint, f)
chbp = unreal.load_asset(CHP); unreal.BlueprintEditorLibrary.compile_blueprint(chbp)
unreal.get_default_object(chbp.generated_class()).get_component_by_class(unreal.CapsuleComponent).set_editor_property("capsule_radius", 36.0)
unreal.BlueprintEditorLibrary.compile_blueprint(chbp); eal.save_loaded_asset(chbp, only_if_is_dirty=False)
if eal.does_asset_exist(GM): eal.delete_asset(GM)
gm = eal.duplicate_asset(f"{G}/BP_RD_GameMode", GM); unreal.get_default_object(gm.generated_class()).set_editor_property("default_pawn_class", chbp.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(gm); eal.save_loaded_asset(gm, only_if_is_dirty=False)
print("RDM2", GM, "-> pawn", unreal.get_default_object(unreal.load_asset(GM).generated_class()).get_editor_property("default_pawn_class").get_name(), "| retarget rig ok", ok, "| saved", JSON)
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
