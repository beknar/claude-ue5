"""The ridable horse (the user's list of 2026-11-08b, docs/improvements9.txt, its eighth phase: "make a rideable horse for a player
to buy and ride with increased speed across the wilderness"; the horse built in Blender as the farm animals are, the user's
choice). Steps (all by default, or name some):
  import   the horse (pipeline/blender_numpy/farm_animals.py -- claude_ue5/SourceArt/brokenspire/horse only=horse: SK_Farm_Horse.fbx
           and its grey, SK_Farm_Horse_B.fbx) into /Game/RandomDungeon/Town/Animals/Horse; its clips at the lengths Blender built
  rider    the Animals pack's camel rider's clips (Anim_Rider_Idle_01, _Walk, _Run on its UE4 mannequin) retargeted to each hero's
           rig (an IK rig on the pack's mannequin, a retargeter per hero onto IK_JRPG_<rig>_Auto) into /Game/RandomDungeon/Horse/Anims
  level    brokenspire's HorseDef (meshes, clips, the soles' speeds from farm_animals.json, price, speed) and RiderClips by hero
C++ first (RD/RDHorse.cpp). Args: [import] [rider] [level]"""
import os, sys, json, unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
SA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "claude_ue5", "SourceArt", "brokenspire", "horse"))
STEPS = [a for a in sys.argv[1:] if a in ("import", "rider", "level")] or ["import", "rider", "level"]
DH = "/Game/RandomDungeon/Town/Animals/Horse"; RIGS = "/Game/RandomDungeon/Horse/Rigs"; ANIMS = "/Game/RandomDungeon/Horse/Anims"
# (the hero menu's six and their rigs, and the retarget onto them: hero_rigs.py, shared with 921 and 922)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hero_rigs, importlib
importlib.reload(hero_rigs)
HERO_RIG = hero_rigs.HERO_RIG
RIDER = {"Idle": "Anim_Rider_Idle_01", "Walk": "Anim_Rider_Walk", "Run": "Anim_Rider_Run"}
J = json.load(open(os.path.join(SA, "farm_animals.json"), encoding="utf-8"))["Horse"]
REPORT = []


def fbx_task(path, dest, skeleton=None, anims=True):
    o = unreal.FbxImportUI()
    o.set_editor_property("import_mesh", True); o.set_editor_property("import_as_skeletal", True)
    o.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    if skeleton: o.set_editor_property("skeleton", skeleton)
    o.set_editor_property("import_animations", anims); o.set_editor_property("import_materials", True); o.set_editor_property("import_textures", False)
    t = unreal.AssetImportTask(); t.filename = path; t.destination_path = dest
    t.automated = True; t.replace_existing = True; t.save = True; t.options = o
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    return [unreal.load_asset(p) for p in t.imported_object_paths]


def horse_assets():
    assets = [unreal.load_asset(p.split(".")[0]) for p in eal.list_assets(DH, recursive=True)] if eal.does_directory_exist(DH) else []
    meshes = sorted([a for a in assets if isinstance(a, unreal.SkeletalMesh)], key=lambda a: a.get_name())
    seqs = {a.get_name().split("_")[-1]: a for a in assets if isinstance(a, unreal.AnimSequence)}
    return meshes, seqs


if "import" in STEPS:
    # (its clips first, then its meshes and skeleton: deleted the other way round the clips lost their skeleton (886's lesson))
    if eal.does_directory_exist(DH):
        ps = [p.split(".")[0] for p in eal.list_assets(DH, recursive=True)]
        order = lambda p: 0 if isinstance(unreal.load_asset(p), unreal.AnimSequence) else 1 if isinstance(unreal.load_asset(p), unreal.SkeletalMesh) else 2
        for p in sorted(ps, key=order): eal.delete_asset(p)
    got = fbx_task(os.path.join(SA, "SK_Farm_Horse.fbx"), DH)
    sk = next((a for a in got if isinstance(a, unreal.SkeletalMesh)), None); assert sk, "the horse did not import"
    fbx_task(os.path.join(SA, "SK_Farm_Horse_B.fbx"), DH, skeleton=sk.get_editor_property("skeleton"), anims=False)
    meshes, seqs = horse_assets()
    # (Interchange takes Blender's 30 fps at its own rate: each clip plays at the length Blender built it to)
    for k, a in seqs.items():
        L = float(J["clips"].get(k, {}).get("length_s", a.get_play_length()))
        if L > 0 and abs(a.get_play_length() - L) > 0.02: a.set_editor_property("rate_scale", a.get_play_length() / L)
        eal.save_loaded_asset(a, only_if_is_dirty=False)
    bones = [str(n) for n in unreal.SkeletalMeshLibrary.get_bone_names(sk)] if hasattr(unreal, "SkeletalMeshLibrary") else []
    REPORT.append(f"import: {[m.get_name() for m in meshes]}, clips {sorted(seqs)}, saddle bone {'saddle' in bones if bones else '?'}")

if "rider" in STEPS:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    clips = {}
    for k, n in RIDER.items():
        a = next((x for x in ar.get_assets_by_path("/Game/Animals_Pack", recursive=True) if str(x.asset_name) == n and str(x.asset_class_path.asset_name) == "AnimSequence"), None)
        assert a, n; clips[k] = a
    src_mesh = unreal.load_asset("/Game/Animals_Pack/Demoscene/Mesh/SK_Mannequin"); assert src_mesh, "the Animals pack's mannequin"
    for hero, (ch, made, why) in hero_rigs.retarget_onto_heroes(src_mesh, [str(a.package_name) for a in clips.values()], RIGS, ANIMS, "Rider", "RIDER").items():
        REPORT.append(f"rider {hero}: {why}" if why else f"rider {hero} ({ch}): {len(made)} of {len(RIDER)}")

if "level" in STEPS:
    MAP = "/Game/RandomDungeon/Maps/brokenspire"
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."):
        les.load_level(MAP); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    meshes, seqs = horse_assets()
    d = unreal.RDHorseDef()
    d.set_editor_property("mesh", meshes[0]); d.set_editor_property("mesh_b", meshes[1] if len(meshes) > 1 else meshes[0])
    for k in ("Idle", "Walk", "Run"): d.set_editor_property(k.lower(), seqs.get(k))
    d.set_editor_property("walk_clip_speed", float(J["walk_speed_cm_s"])); d.set_editor_property("run_clip_speed", float(J.get("run_speed_cm_s", 260.0)))
    d.set_editor_property("gallop_from", 250.0); d.set_editor_property("saddle_bone", "saddle")
    # (the list of 2026-11-10: "at least 5x faster than what the player can move": 5.5 her own speed, 2.2 until then)
    d.set_editor_property("price", 60.0); d.set_editor_property("speed_mul", 5.5); d.set_editor_property("rider_lift", 14.0)          # (her pelvis this far over the saddle bone)
    g.set_editor_property("horse_def", d)
    rc_map = {}
    for hero, ch in HERO_RIG.items():
        r = unreal.RDRiderClips()
        for k, n in RIDER.items(): r.set_editor_property(k.lower(), unreal.load_asset(f"{ANIMS}/{ch}/{n}_{ch}"))
        rc_map[hero] = r
    g.set_editor_property("rider_clips", rc_map)
    g.modify(); les.save_current_level()
    REPORT.append(f"level: horse {meshes[0].get_name()}, clips {sorted(seqs)}, walk {J['walk_speed_cm_s']} / run {J.get('run_speed_cm_s')} cm/s, riders {sorted(rc_map)}")
    del g
print("HORSE " + " | ".join(REPORT))
import gc
gc.collect()
