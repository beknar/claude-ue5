"""random_dungeonmagic_level5's Warrior is Warrior3 (ai models/Warrior3.glb; the user's of 2026-10-26: she replaces the
Warrior on level 5 and its menu only; the other levels keep the old Warrior, SK_JRPG_Fem5). Run after
blender_numpy/tripo_build.py (warrior3_clips.py) into SourceArt/jrpg_warrior3, 600 / 610 / 615 / 620 for Warrior3.
- her sword-and-shield attacks, flinch and death: the old Warrior's (the Weapon_Shield_Animations pack's Attack_01 / 03 /
  08, Get_Hit, Dead_01), retargeted from the pack onto her (790's source rig IK_RDC_Sword_Source, her rig
  IK_JRPG_Warrior3_Auto) into /Game/RandomDungeon/Magic5/Anims/Warrior3/<clip>_Warrior3; the blow where her hand moves
  fastest, each clip cut 0.55 s after it (790's)
- the sword in her right hand and the shield on her left forearm as 790 holds them, from her own reference pose (her
  hands are turned otherwise than the old Warrior's: the old grips would have put them askew)
- her dungeon character BP_RDM5_Warrior3Character (a child of BP_JRPGWarrior3Character, capsule radius 36 as the old
  Warrior's); 819 gives her the walk / run switch
- the level's hero "Warrior": the same card (name, health, bonuses, wears, controls), her pawn, her sword with her
  clips and grips. 855 then gives her the found weapons (two-handed swords: her own slash), 856 / 857 her armour
Prints the clips' blows and the grips; saves the level. Args: none"""
import json, os, unreal
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions; ML = unreal.MathLibrary
V = unreal.Vector
MAP = "/Game/RandomDungeon/Maps/random_dungeonmagic_level5"
CH = "Warrior3"; SKM = f"/Game/JRPG/Character/SK_JRPG_{CH}"; ANIMS = f"/Game/RandomDungeon/Magic5/Anims/{CH}"; RIGS = "/Game/RandomDungeon/Magic5/Rigs"
PAWN = "/Game/RandomDungeon/Blueprints/BP_RDM5_Warrior3Character"
MW = "/Game/Medieval_Weapons/Meshes/VOL2/"
SWORD, HAND_Z, SHIELD, SHIELD_SCALE, AFTER = MW + "SM_Sword_1", 69.0, MW + "SM_Shield_1", 0.8, 0.55
PACK, PREFIX, ATTACKS, FLINCH, DEATH = "Weapon_Shield_Animations", "Anim_Weapon_Shield_", ["Attack_01", "Attack_03", "Attack_08"], "Get_Hit", "Dead_01"
tgt_mesh = unreal.load_asset(SKM); tgt_rig = unreal.load_asset(f"/Game/JRPG/Rigs/IK_JRPG_{CH}_Auto"); src_rig = unreal.load_asset("/Game/RandomDungeon/Combat/Rigs/IK_RDC_Sword_Source")
src_mesh = unreal.load_asset(f"/Game/{PACK}/Mesh/SK_Mannequin")
assert tgt_mesh and tgt_rig and src_rig and src_mesh, "600 / 610 Warrior3 and 790 first"
ar = unreal.AssetRegistryHelpers.get_asset_registry()


def find(name):
    for a in ar.get_assets_by_path("/Game/" + PACK, recursive=True):
        if str(a.asset_name) == name and str(a.asset_class_path.asset_name) == "AnimSequence": return a
    raise RuntimeError(name)


o = unreal.AnimPoseEvaluationOptions()
def measure(anim):
    """length and the time her weapon hand moves fastest (790's)"""
    L = unreal.AnimationLibrary.get_sequence_length(anim); n = max(30, int(L * 60)); pts = []
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(anim, L * k / n, o)
        h = APE.get_bone_pose(p, "hand_r", unreal.AnimPoseSpaces.WORLD).translation; q = APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.WORLD).translation
        pts.append(V(h.x - q.x, h.y - q.y, h.z - q.z))
    sp = [(pts[k + 1] - pts[k]).length() / (L / n) for k in range(n)]
    sm = [sum(sp[max(0, k - 2):k + 3]) / len(sp[max(0, k - 2):k + 3]) for k in range(n)]
    k = max(range(n), key=lambda i: sm[i]); return L, L * (k + 0.5) / n


# ---- her clips
rtg_path = f"{RIGS}/RTG_RDM5_Sword_To_{CH}"
if eal.does_asset_exist(rtg_path): eal.delete_asset(rtg_path)
rtg = at.create_asset(rtg_path.split("/")[-1], RIGS, unreal.IKRetargeter, unreal.IKRetargetFactory())
rc = unreal.IKRetargeterController.get_controller(rtg)
rc.add_default_ops()
rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
rc.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, src_mesh); rc.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, tgt_mesh)
rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
rm = rc.get_op_controller(rc.get_index_of_op_by_name("Root Motion"))
rm.set_source_root_bone("root"); rm.set_target_root_bone("root"); rm.set_target_pelvis_bone("pelvis")
try: rc.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
except Exception as e: print("W3 align", e)
eal.save_loaded_asset(rtg)
names = [PREFIX + n for n in ATTACKS + [FLINCH, DEATH]]
for n in names:
    if eal.does_asset_exist(f"{ANIMS}/{n}_{CH}"): eal.delete_asset(f"{ANIMS}/{n}_{CH}")
inp = unreal.IKRetargetBatchOperationInputs()
inp.set_editor_property("assets_to_retarget", [find(n) for n in names])
inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", "_" + CH)
inp.set_editor_property("target_path", ANIMS); inp.set_editor_property("include_referenced_assets", False)
inp.set_editor_property("overwrite_existing_files", True)
unreal.IKRetargetBatchOperation.run_batch_retarget(inp)
clips = {}
for n in names:
    p = f"{ANIMS}/{n}_{CH}"; a = unreal.load_asset(p); assert a, p
    a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
    clips[n] = a
attacks = []
for n in ATTACKS:
    a = clips[PREFIX + n]; L, hit = measure(a); attacks.append((a, hit, min(L, hit + AFTER), L))
# ---- her grips (790's, from her reference pose: she faces +Y, her right arm along -X)
ref = APE.get_reference_pose(tgt_mesh.skeleton)
bone = lambda n: APE.get_bone_pose(ref, n, unreal.AnimPoseSpaces.WORLD)


def weapon_grip(path, hand_z):
    hand = bone("hand_r"); fore = (hand.translation - bone("lowerarm_r").translation).normal()
    thumb = V(0, 1, 0); thumb = (thumb - fore * thumb.dot(fore)).normal()
    palm = hand.translation + fore * 6.5 + V(0, 0, -2.5)
    m = unreal.load_asset(path); b = m.get_bounding_box(); end = 1.0 if b.max.z - hand_z >= hand_z - b.min.z else -1.0
    rot = ML.make_rot_from_xz(fore, thumb * end)
    return ML.make_relative_transform(unreal.Transform(palm - ML.get_up_vector(rot) * hand_z, rot, V(1, 1, 1)), hand)


def shield_grip(path):
    elbow = bone("lowerarm_l"); hand = bone("hand_l").translation
    fore = (hand - elbow.translation).normal(); back = V(0, 0, 1); back = (back - fore * back.dot(fore)).normal()
    w = unreal.Transform(elbow.translation + (hand - elbow.translation) * 0.55 + back * 6.0, ML.make_rot_from_zy(fore * -1.0, back), V(SHIELD_SCALE, SHIELD_SCALE, SHIELD_SCALE))
    b = unreal.load_asset(path).get_bounds().origin
    w = unreal.Transform(ML.transform_location(w, V(-b.x, -b.y, -b.z)), w.rotation.rotator(), w.scale3d)
    return ML.make_relative_transform(w, elbow)


grip, off_grip = weapon_grip(SWORD, HAND_Z), shield_grip(SHIELD)
# ---- her dungeon character
if not eal.does_asset_exist(PAWN):
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.load_asset(f"/Game/JRPG/Game/BP_JRPG{CH}Character").generated_class())
    at.create_asset(PAWN.split("/")[-1], PAWN.rsplit("/", 1)[0], unreal.Blueprint, f)
bp = unreal.load_asset(PAWN); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.get_default_object(bp.generated_class()).get_component_by_class(unreal.CapsuleComponent).set_editor_property("capsule_radius", 36.0)
unreal.BlueprintEditorLibrary.compile_blueprint(bp); eal.save_loaded_asset(bp, only_if_is_dirty=False)
# ---- the level's Warrior
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not ues.get_editor_world().get_path_name().startswith(MAP + "."): unreal.EditorLoadingAndSavingUtils.load_map(MAP)
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
heroes = list(gen.get_editor_property("heroes")); i = next(k for k, h in enumerate(heroes) if str(h.name) == "Warrior")
h = unreal.RDHeroDef(); h.import_text(heroes[i].export_text())
h.pawn_class = bp.generated_class()
ws = []
for wd in h.weapons:
    if str(wd.name) == "Sword":
        wd.set_editor_property("attacks", [a[0] for a in attacks]); wd.set_editor_property("attack_starts", [0.0] * len(attacks))
        wd.set_editor_property("attack_ends", [float(a[2]) for a in attacks]); wd.set_editor_property("hit_times", [float(a[1]) for a in attacks])
        wd.set_editor_property("get_hit", clips[PREFIX + FLINCH]); wd.set_editor_property("death", clips[PREFIX + DEATH])
        wd.set_editor_property("grip", grip); wd.set_editor_property("off_hand_grip", off_grip)
    ws.append(wd)
h.weapons = ws; heroes[i] = h
gen.set_editor_property("heroes", heroes)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
back = next(x for x in gen.get_editor_property("heroes") if str(x.name) == "Warrior")
print("W3 clips:", ", ".join("%s blow %.2f s, cut at %.2f of %.2f" % (a[0].get_name(), a[1], a[2], a[3]) for a in attacks), "| flinch", clips[PREFIX + FLINCH].get_name(), "| death", clips[PREFIX + DEATH].get_name())
print("W3 grips: sword", grip.translation, grip.rotation.rotator(), "| shield", off_grip.translation)
print("W3 level: Warrior's pawn", back.pawn_class.get_name(), "| weapons", [str(w.name) for w in back.weapons], "| attacks", [a.get_name() for a in back.weapons[0].attacks], "| saved")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
