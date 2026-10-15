"""random_dungeonmagic_level: the caster (girl-caster-tripo, character Caster of 600-620) and her fire spell.
Run after 600 / 610 / 615 / 620 for Caster (her mesh, her own clips: Idle, Walk, Run and the three casts that
blender_numpy/caster_clips.py made for her, the locomotion AnimBP, BP_JRPGCasterCharacter).
- her flinch and death: Animations_Warrior's Get_Hit_1 and Dead_1 (the axe fighter's: no shield in the off hand), retargeted
  from the pack's UE4-style mannequin onto her rig (IK_JRPG_Caster_Auto, from 610) into /Game/RandomDungeon/Magic/Anims
  (root locked)
- her casts: each clip measured on her skeleton: the bolt leaves where her right hand moves fastest (component space, the
  pelvis's own travel taken out); a cast is cut a little after it (the way back to the idle pose is blended out)
- the spell: the fire bolt's numbers and its effects, all from the effects docs/magic.md lists for a fire spell:
    charge and bolt  DarkHalls NS_FireEye (a ball of fire with a glow and flying streaks; it takes about half a second to
                     build up, so it grows on her hand while she winds up and that same system leaves her hand as the bolt)
    burst            the Starter Content P_Explosion (in Feather's demo folder), with DarkHalls NS_FirePool burning on
                     the spot for half a second (a fire with a blue core and a red glow)
  medium range: 14 m (a monster notices her at 10 m), 25 damage on the monster it meets, half of it on each other
  monster within 1.7 m of the burst
- BP_RDM_CasterCharacter (child of BP_JRPGCasterCharacter: a 36 cm capsule, as BP_SFC_Fem5Character has: her clips swing the
  hands and the robe wide) and BP_RDM_GameMode (BP_RD_GameMode with her as the pawn: the dungeon HUD stays)
Writes SourceArt/random_dungeon_magic/spell.json for 811. Idempotent. Args: none"""
import json, os, unreal
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions
V = unreal.Vector
CH = "Caster"
OUT = "/Game/RandomDungeon/Magic"; ANIMS = OUT + "/Anims"; RIGS = OUT + "/Rigs"
JSON = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_magic\spell.json"
tgt_mesh = unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{CH}"); tgt_rig = unreal.load_asset(f"/Game/JRPG/Rigs/IK_JRPG_{CH}_Auto")
assert tgt_mesh and tgt_rig, "run 600-620 for Caster first"
PACK, PREFIX, FLINCH, DEATH = "Animations_Warrior", "Anim_Warrior_", "Get_Hit_1", "Dead_1"
CASTS = ["Cast1", "Cast2", "Cast3"]
AFTER = 0.42                     # seconds of each cast kept after the release
SPELL = {"name": "Fire", "damage": 25.0, "reach": 1400.0, "rate": 1.15, "bolt_speed": 1700.0, "bolt_turn": 200.0, "splash": 170.0, "bone": "hand_r",
         "charge": "/Game/Feather/Demo/StarterContent/Particles/P_Sparks", "charge_scale": 0.3, "bolt": OUT + "/NS_RDM_FirePool_Warm", "bolt_scale": 0.2,
         "burst": "/Game/Feather/Demo/StarterContent/Particles/P_Explosion", "burst_scale": 1.0,
         "burst_flame": OUT + "/NS_RDM_FireWings_Warm", "burst_flame_scale": 0.35, "burst_flame_seconds": 0.35,
         "light": [1.0, 0.45, 0.12], "light_cd": 150.0}
# the DarkHalls fires build up over about a second from a few particles: a bolt that flies for less than that would be
# a speck all the way. Copies of them start warm (the system is run on for WARMUP seconds before it is first drawn);
# the pack's own systems are left as they are. (NS_FireEye, the third of them, is too faint at the dungeon's exposure:
# measured in a room, a few embers where the others are flames.)
WARMUP = 1.2
for src, dst in (("/Game/DarkHalls/VFX/NS_FirePool", OUT + "/NS_RDM_FirePool_Warm"), ("/Game/DarkHalls/VFX/NS_FireWings", OUT + "/NS_RDM_FireWings_Warm")):
    if eal.does_asset_exist(dst): eal.delete_asset(dst)
    s = eal.duplicate_asset(src, dst); assert s, dst
    s.set_editor_property("warmup_time", WARMUP); s.set_editor_property("warmup_tick_delta", 1.0 / 30.0); s.set_editor_property("warmup_tick_count", int(WARMUP * 30))
    eal.save_loaded_asset(s, only_if_is_dirty=False)
    s = unreal.load_asset(dst); print(f"RDMCASTER {dst.split('/')[-1]}: warm-up {s.get_editor_property('warmup_time'):.1f} s in {s.get_editor_property('warmup_tick_count')} ticks")
for k in ("charge", "bolt", "burst", "burst_flame"): assert unreal.load_asset(SPELL[k]), SPELL[k]
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
def release(anim):
    """length, and the time her right hand moves fastest (relative to the pelvis): where the bolt leaves"""
    L = unreal.AnimationLibrary.get_sequence_length(anim); n = max(30, int(L * 60)); pts = []
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(anim, L * k / n, o)
        h = APE.get_bone_pose(p, "hand_r", unreal.AnimPoseSpaces.WORLD).translation; q = APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.WORLD).translation
        pts.append(V(h.x - q.x, h.y - q.y, h.z - q.z))
    sp = [(pts[k + 1] - pts[k]).length() / (L / n) for k in range(n)]
    sm = [sum(sp[max(0, k - 2):k + 3]) / len(sp[max(0, k - 2):k + 3]) for k in range(n)]
    k = max(range(n), key=lambda i: sm[i])
    return L, L * (k + 0.5) / n, sm[k]
# ---- flinch and death, retargeted from the pack's mannequin
src_mesh = unreal.load_asset(f"/Game/{PACK}/Mesh/SK_Mannequin"); assert src_mesh, PACK
rig = make(unreal.IKRigDefinition, unreal.IKRigDefinitionFactory(), "IK_RDM_Warrior_Source", RIGS)
c = unreal.IKRigController.get_controller(rig); c.set_skeletal_mesh(src_mesh); ok = c.apply_auto_generated_retarget_definition()
try: c.apply_auto_fbik()
except Exception: pass
eal.save_loaded_asset(rig)
rtg = make(unreal.IKRetargeter, unreal.IKRetargetFactory(), f"RTG_RDM_Warrior_To_{CH}", RIGS)
rc = unreal.IKRetargeterController.get_controller(rtg)
rc.add_default_ops()
rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, rig); rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
rc.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, src_mesh); rc.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, tgt_mesh)
rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, rig); rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
rm = rc.get_op_controller(rc.get_index_of_op_by_name("Root Motion"))       # (add_default_ops leaves it without bones)
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
# ---- her casts
casts = []
for n in CASTS:
    p = f"/Game/JRPG/{CH}Anims/AS_{CH}_{n}"; a = unreal.load_asset(p); assert a, p
    a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
    L, hit, speed = release(a)
    casts.append({"clip": p, "length": round(L, 3), "hit": round(hit, 3), "end": round(min(L, hit + AFTER), 3), "hand_speed": round(speed)})
res = dict(SPELL, casts=casts, flinch=f"{ANIMS}/{PREFIX}{FLINCH}_{CH}", death=f"{ANIMS}/{PREFIX}{DEATH}_{CH}")
os.makedirs(os.path.dirname(JSON), exist_ok=True); json.dump(res, open(JSON, "w"), indent=1)
secs = [x["end"] / SPELL["rate"] for x in casts]
print(f"RDMCASTER flinch / death retargeted from {PACK} (rig ok={ok}) | " + ", ".join(f"{n} bolt at {x['hit']:.2f} s (hand {x['hand_speed']} cm/s), cut at {x['end']:.2f} of {x['length']:.2f} s" for n, x in zip(CASTS, casts))
      + f" | a bolt every {sum(secs) / len(secs):.2f} s, {SPELL['damage']:.0f} damage, reach {SPELL['reach'] / 100:.0f} m")
# ---- her dungeon character and game mode
G = "/Game/RandomDungeon/Blueprints"; CHP = f"{G}/BP_RDM_CasterCharacter"; GM = f"{G}/BP_RDM_GameMode"
if not eal.does_asset_exist(CHP):
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.load_asset(f"/Game/JRPG/Game/BP_JRPG{CH}Character").generated_class())
    at.create_asset("BP_RDM_CasterCharacter", G, unreal.Blueprint, f)
chbp = unreal.load_asset(CHP); unreal.BlueprintEditorLibrary.compile_blueprint(chbp)
unreal.get_default_object(chbp.generated_class()).get_component_by_class(unreal.CapsuleComponent).set_editor_property("capsule_radius", 36.0)
unreal.BlueprintEditorLibrary.compile_blueprint(chbp); eal.save_loaded_asset(chbp, only_if_is_dirty=False)
if eal.does_asset_exist(GM): eal.delete_asset(GM)
gm = eal.duplicate_asset(f"{G}/BP_RD_GameMode", GM); cdo = unreal.get_default_object(gm.generated_class())
cdo.set_editor_property("default_pawn_class", chbp.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(gm); eal.save_loaded_asset(gm, only_if_is_dirty=False)
cdo = unreal.get_default_object(unreal.load_asset(GM).generated_class())
print("RDMCASTER", GM, "-> pawn", cdo.get_editor_property("default_pawn_class").get_name(), "hud", cdo.get_editor_property("hud_class").get_name(), "| saved", JSON)
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
