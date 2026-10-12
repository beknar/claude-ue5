"""random_isometric_village_level: the villagers. Fills the villager list of the open level's AIVVillageGenerator
(FIVVillagerDef: whole-body mesh + idle / in-place walk clip on the pack's own UE5 mannequin skeleton) and its coverage
(villagers per building of every 250 m section: 0.3). Villagers are spawned by the sections in play only (AIVVillager:
no controller, moved along the nav grid), so nothing here is built into the level.
Models, all unarmed: townsmen (NPC_Characters_Pack), youths and a young woman (NPC_Kids_Pack, scaled down), peasants and
women (NPC_Beggars_Pack: the able-bodied ones), a servant pair, the elder, a physician and a lady (NPC_King_And_Queen).
Left out: the Vikings / Knights / Warriors packs (armed or armoured), beggars that need crutch or sitting clips.
The walk clip's ground speed is measured from the pack's MM_Walk_Fwd root track.
Called by 780 (playable level) and 783 (the _Cine copy, with noblock). Run on its own after changing the list.
Args: [noblock] (the cinematic's scripted walker passes through villagers) [nosave] [coverage=0.3]"""
import sys, unreal
ARGS = globals().get("ARGS", sys.argv[1:])
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
CH, KD, KQ, BG = "NPC_Characters_Pack", "NPC_Kids_Pack", "NPC_King_And_Queen", "NPC_Beggars_Pack"
# (name, pack, mesh path under /Game/<pack>/Mesh, scale, weight)
MODELS = [
    ("Townsman1", CH, "NPC_Character_01/Mesh_UE5/Full/SKM_NPC_Character_01_Full_01", 1.0, 1.0),
    ("Townsman2", CH, "NPC_Character_02/Mesh_UE5/Full/SKM_NPC_Character_02_Full_01", 1.0, 1.0),
    ("Townsman3", CH, "NPC_Character_03/Mesh_UE5/Full/SKM_NPC_Character_03_Full_01", 1.0, 1.0),
    ("Townsman4", CH, "NPC_Character_04/Mesh_UE5/Full/SKM_NPC_Character_04_Full_01", 1.0, 1.0),
    ("OldMan", CH, "NPC_Character_05/Mesh_UE5/Full/SKM_NPC_Character_05_Full_01", 0.97, 1.0),
    ("Peasant1", BG, "NPC_Beggar_02/Mesh_UE5/Full/SK_UE5_NPC_Beggar_02_Full_01", 1.0, 1.0),
    ("Peasant2", BG, "NPC_Beggar_05/Mesh_UE5/Full/SK_UE5_NPC_Beggar_05_Full_01", 1.0, 1.0),
    ("OldWoman", BG, "NPC_Beggar_03/Mesh_UE5/Full/SK_UE5_NPC_Beggar_03_Full_01", 0.94, 1.3),
    ("Woman", BG, "NPC_Beggar_03/Mesh_UE5/Full/SK_UE5_NPC_Beggar_03_Full_03", 0.96, 1.4),
    ("YoungWoman", KD, "NPC_Kid_05/Mesh_UE5/Full/SK_UE5_NPC_Kid_05_Full_01", 0.93, 1.4),
    ("Girl", KD, "NPC_Kid_04/Mesh_UE5/Full/SK_UE5_NPC_Kid_04_Full_01", 0.80, 0.7),
    ("Boy1", KD, "NPC_Kid_02/Mesh_UE5/Full/SK_UE5_NPC_Kid_02_Full_01", 0.80, 0.7),
    ("Boy2", KD, "NPC_Kid_03/Mesh_UE5/Full/SK_UE5_NPC_Kid_03_Full_01", 0.82, 0.7),
    ("Youth1", KD, "NPC_Kid_01/Mesh_UE5/Full/SK_UE5_NPC_Kid_01_Full_01", 0.88, 0.6),
    ("Youth2", KD, "NPC_Kid_01/Mesh_UE5/Full/SK_UE5_NPC_Kid_01_Full_03", 0.88, 0.6),
    ("Servant1", KQ, "NPC_Servant/Mesh_UE5/Full/SK_UE5_NPC_Servant_Full_01", 1.0, 0.3),
    ("Servant2", KQ, "NPC_Servant/Mesh_UE5/Full/SK_UE5_NPC_Servant_Full_02", 1.0, 0.3),
    ("Elder", KQ, "NPC_King/Mesh_UE5/Full/SK_UE5_NPC_King_Full_02", 1.0, 0.3),
    ("Physician", KQ, "NPC_Plague_doctor/Mesh_UE5/Full/SK_UE5_NPC_Plague_doctor_Full_02", 1.0, 0.25),
    ("Lady", KQ, "NPC_Queen/Mesh_UE5/Full/SK_UE5_NPC_Queen_Full_01", 0.97, 0.35),
]
clips = {}
def pack_clips(pack):
    if pack not in clips:
        a = f"/Game/{pack}/Demoscene_UE5/Animations/"
        idle, walk, fwd = unreal.load_asset(a + "MM_Idle"), unreal.load_asset(a + "MM_Walk_InPlace"), unreal.load_asset(a + "MM_Walk_Fwd")
        speed = 237.0
        if fwd:
            n = unreal.AnimationLibrary.get_num_frames(fwd)
            d = unreal.AnimationLibrary.get_bone_pose_for_frame(fwd, "root", n - 1, False).translation - unreal.AnimationLibrary.get_bone_pose_for_frame(fwd, "root", 0, False).translation
            if d.length() > 50: speed = d.length() / fwd.get_play_length()
        clips[pack] = (idle, walk, speed)
    return clips[pack]
defs = []
for name, pack, path, scale, weight in MODELS:
    mesh = unreal.load_asset(f"/Game/{pack}/Mesh/{path}"); idle, walk, speed = pack_clips(pack)
    if not (mesh and idle and walk) or mesh.skeleton != walk.get_skeleton():
        print("  MISSING villager", name, path, "(mesh, clips or a different skeleton)"); continue
    d = unreal.IVVillagerDef()
    for k, v in (("name", name), ("mesh", mesh), ("idle", idle), ("walk", walk), ("walk_clip_speed", speed), ("scale", scale), ("mesh_yaw", -90.0), ("weight", weight)):
        d.set_editor_property(k, v)
    defs.append(d)
gens = [a for a in eas.get_all_level_actors() if a.get_class().get_name() == "IVVillageGenerator"]
assert len(gens) == 1, "open random_isometric_village_level (or its _Cine copy) first"
gen = gens[0]
coverage = next((float(a.split("=")[1]) for a in ARGS if a.startswith("coverage=")), 0.3)
gen.set_editor_property("villagers", defs); gen.set_editor_property("villager_coverage", coverage)
gen.set_editor_property("villagers_block_pawns", "noblock" not in ARGS)
print("villagers:", len(defs), "models, coverage", coverage, "per building, walk clip %.0f cm/s," % (defs[0].walk_clip_speed if defs else 0),
      "blocking pawns" if "noblock" not in ARGS else "not blocking pawns")
if "nosave" not in ARGS:
    les.save_current_level()
    print("saved", ues.get_editor_world().get_path_name())
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
