"""The Warrior's and the Warlock's arms lengthened in Unreal (blender_numpy/tripo_proportions.py lengthens them in the
build: their arms were about 60 % of a person's, shoulder joint to wrist 33.7 and 34.8 cm on a body 170 tall, and a
two-handed sword folded or crossed them; the user's reference: examples/katana_2handed.mp4).
Run after blender_numpy/tripo_build.py has built SourceArt/jrpg_<ch>/SK_JRPG_<CH>.fbx again (the Warrior:
`tripo_build.py "ai models/Warrior.glb" <abs>/jrpg_fem5 SK_JRPG_Fem5 Fem5 165`; the Warlock with darkcaster_clips.py
and hair.json, as README says). Per hero:
- SK_JRPG_<CH> imported again from that FBX onto its own skeleton (its materials, physics asset and post-process AnimBP
  kept), the skeleton's reference pose updated from it (an import onto an existing skeleton otherwise keeps the old
  reference pose for the bones it had: 615's grounding, 790's and 817's grips and 855 read it)
- every AnimSequence on that skeleton (her own clips, the retargeted ones of 610, 790 and 817, the level 5 weapon
  clips): an AnimSequence keeps each bone's translation, so a clip made on the old rig pulls the arms back to their old
  length. The translation keys of the bones whose rest offset changed (the forearm, the hand and the twist bones) are
  set to the new mesh's; their turns and scales are kept, so each clip moves exactly as before, on longer arms
- measured: the mesh's and the skeleton's shoulder joint to wrist; in every clip, at its start, middle and end, each
  arm's upper arm (shoulder joint to elbow) and forearm (elbow to wrist) against the reference pose's (RDARMS lines;
  "ok" when every clip is within 0.1 cm. Not the shoulder joint to the wrist: that shortens as the elbow bends)
Idempotent (the keys are set to the reference: a second run changes nothing). Args: [measure] [CH ...] (default Fem5
DarkCaster; measure: no import and no keys, only the measuring)
`860 shield` (after `790_rdc_weapons.py grips`): the shield lies along the forearm at 55 % from the elbow, so its grip
moved with the longer forearm (8.1 -> 12.1 cm from the wrist). Levels 4 and 5 and their menus keep copies of the
combat level's weapons (825, 852, 826): every off-hand grip at the old place is set to weapons.json's, in the combat
level's weapons and in every hero's on those maps (each map opened, changed and saved; nothing else touched)."""
import os, sys, json, unreal
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); APE = unreal.AnimPoseExtensions; AL = unreal.AnimationLibrary
V = unreal.Vector
MEASURE = "measure" in sys.argv[1:]
CHS = [a for a in sys.argv[1:] if a not in ("measure", "shield")] or ["Fem5", "DarkCaster"]
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
# (the upper arm too: the shoulders were widened as well, so its offset from the collarbone changed)
ARM = [f"{b}_{s}" for s in "rl" for b in ("upperarm", "lowerarm", "lowerarm_twist_01", "upperarm_twist_01", "hand")]
opts = unreal.AnimPoseEvaluationOptions()


def mesh_ref(sk, names):
    """the mesh in a component without animation: its own reference pose (component and parent-bone space)"""
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    tmp = eas.spawn_actor_from_class(unreal.SkeletalMeshActor, V(0, 0, -100000), unreal.Rotator())
    smc = tmp.skeletal_mesh_component; smc.set_skeletal_mesh_asset(sk); smc.set_world_location(V(0, 0, 0), False, True)
    cs = {n: smc.get_socket_transform(n, unreal.RelativeTransformSpace.RTS_COMPONENT) for n in names}
    ps = {n: smc.get_socket_transform(n, unreal.RelativeTransformSpace.RTS_PARENT_BONE_SPACE) for n in names}
    eas.destroy_actor(tmp)
    return cs, ps


def arm_len(get, s):
    return (get(f"hand_{s}") - get(f"upperarm_{s}")).length()


def segs(get, s):
    """(upper arm, forearm) lengths"""
    return (get(f"lowerarm_{s}") - get(f"upperarm_{s}")).length(), (get(f"hand_{s}") - get(f"lowerarm_{s}")).length()


def reimport(CH, sk, skel, fbx):
    """the mesh again from the build's FBX, onto her own skeleton, the skeleton's reference pose with it"""
    mats = list(sk.get_editor_property("materials")); phys = sk.get_editor_property("physics_asset")
    ppab = sk.get_editor_property("post_process_anim_blueprint")
    t = unreal.AssetImportTask(); t.filename = fbx; t.destination_path = "/Game/JRPG/Character"
    t.automated = True; t.replace_existing = True; t.save = True
    o = unreal.FbxImportUI(); o.import_mesh = True; o.import_as_skeletal = True; o.import_animations = False; o.import_materials = False; o.import_textures = False
    o.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH; o.skeleton = skel
    o.skeletal_mesh_import_data.set_editor_property("update_skeleton_reference_pose", True)
    o.skeletal_mesh_import_data.set_editor_property("import_morph_targets", True)
    t.options = o
    at.import_asset_tasks([t])
    sk = unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{CH}")
    assert sk.get_editor_property("skeleton") == skel, "the mesh got another skeleton"
    slots = sk.get_editor_property("materials")
    sk.set_editor_property("materials", [unreal.SkeletalMaterial(material_interface=(mats[i].material_interface if i < len(mats) else s.material_interface),
                                                                 material_slot_name=str(s.get_editor_property("material_slot_name"))) for i, s in enumerate(slots)])
    if phys: sk.set_editor_property("physics_asset", phys)
    if ppab: sk.set_editor_property("post_process_anim_blueprint", ppab)
    sk.modify(); eal.save_loaded_asset(sk, only_if_is_dirty=False); eal.save_loaded_asset(skel, only_if_is_dirty=False)
    return sk


def shield_grips(old=(0.0, -8.11, 6.0)):
    """the off-hand (shield) grips at the old place set to 790's weapons.json, on every map that keeps a copy"""
    WJ = json.load(open(os.path.join(SA, "random_dungeon_combat", "weapons.json")))
    new = {tuple(round(v, 2) for v in w["shield_grip"]["loc"]) for w in WJ["weapons"].values() if w.get("shield_grip")}
    assert len(new) == 1, new
    nl = V(*next(iter(new)))
    ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    def fix(d):
        t = d.get_editor_property("off_hand_grip"); l = t.translation
        if abs(l.x - old[0]) < 0.05 and abs(l.y - old[1]) < 0.05 and abs(l.z - old[2]) < 0.05:
            d.set_editor_property("off_hand_grip", unreal.Transform(nl, t.rotation.rotator(), t.scale3d)); return 1
        return 0
    out = {}
    for m in ("random_dungeoncombat_level", "random_dungeonmagic_level4", "random_dungeonmagic_level4_select", "random_dungeonmagic_level5", "random_dungeonmagic_level5_select"):
        path = "/Game/RandomDungeon/Maps/" + m
        if not eal.does_asset_exist(path): continue
        if not ues.get_editor_world().get_path_name().startswith(path + "."): les.load_level(path)
        n = 0
        for a in eas.get_all_level_actors():
            if isinstance(a, unreal.RDDungeonGenerator):
                ws = list(a.get_editor_property("weapons")); k = sum(fix(d) for d in ws)
                if k: a.set_editor_property("weapons", ws); n += k
            if isinstance(a, (unreal.RDDungeonGenerator, unreal.RDHeroSelect)):
                hs = list(a.get_editor_property("heroes")); k = 0
                for h in hs:
                    hw = list(h.get_editor_property("weapons")); kk = sum(fix(d) for d in hw)
                    if kk: h.set_editor_property("weapons", hw); k += kk
                if k: a.set_editor_property("heroes", hs); n += k
            if n: a.modify()
        if n: les.save_current_level()
        out[m] = n
    print("RDARMS shield grips set to (%.2f, %.2f, %.2f): %s" % (nl.x, nl.y, nl.z, json.dumps(out)))


if "shield" in sys.argv[1:]:
    shield_grips(); CHS = []
report = {}
for CH in CHS:
    src = os.path.join(SA, "jrpg_" + CH.lower()); fbx = os.path.join(src, f"SK_JRPG_{CH}.fbx")
    build = json.load(open(os.path.join(src, "build.json")))
    sk = unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{CH}"); skel = sk.get_editor_property("skeleton")
    cs0, _ = mesh_ref(sk, ARM + ["upperarm_r", "upperarm_l"])
    before = arm_len(lambda n: cs0[n].translation, "r")
    if not MEASURE: sk = reimport(CH, sk, skel, fbx)
    names = [str(n) for n in APE.get_bone_names(APE.get_reference_pose(skel))]
    cs, ps = mesh_ref(sk, names)
    ref = APE.get_reference_pose(skel)
    after = arm_len(lambda n: cs[n].translation, "r"); skel_len = arm_len(lambda n: APE.get_bone_pose(ref, n, unreal.AnimPoseSpaces.WORLD).translation, "r")
    k = (build.get("proportions") or {}).get("factor")
    print(f"RDARMS {CH}: the mesh's shoulder joint to wrist {before:.1f} -> {after:.1f} cm (the build's factor {k}); the skeleton's reference {skel_len:.1f} cm")
    # ---- every clip on her skeleton: the arm bones' translations set to the new reference
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    f = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "AnimSequence")], recursive_paths=True, package_paths=["/Game"])
    sp = skel.get_path_name(); seqs = []
    for a in ar.get_assets(f):
        tag = str(a.get_tag_value("Skeleton") or "")
        if tag.endswith(sp) or tag.split("'")[1:2] == [sp]: seqs.append(str(a.package_name))
    want = {b: ps[b].translation for b in ARM if b in ps}
    worst = 0.0; rows = []
    for path in sorted(seqs):
        a = unreal.load_asset(path)
        n = AL.get_num_frames(a); L = AL.get_sequence_length(a)
        oks = []
        if not MEASURE:
            tracks = {}
            for b in want:
                pos, rot, scl = [], [], []
                for i in range(n + 1):
                    p = APE.get_anim_pose_at_time(a, min(L, i * L / max(n, 1)), opts)
                    loc = APE.get_bone_pose(p, b, unreal.AnimPoseSpaces.LOCAL)
                    pos.append(want[b]); rot.append(loc.rotation); scl.append(loc.scale3d)
                tracks[b] = (pos, rot, scl)
            ctrl = a.get_editor_property("controller")
            ctrl.open_bracket("arm lengths", False)
            for b, (pos, rot, scl) in tracks.items():
                ok = ctrl.set_bone_track_keys(b, pos, rot, scl, False)
                if not ok:
                    ctrl.add_bone_curve(b, False); ok = ctrl.set_bone_track_keys(b, pos, rot, scl, False)
                oks.append(ok)
            ctrl.close_bracket(False)
            eal.save_loaded_asset(a, only_if_is_dirty=False)
        # (measured: each arm's two segments at the start, the middle and the end)
        d = 0.0
        for tt in (0.0, 0.5 * L, L):
            p = APE.get_anim_pose_at_time(a, tt, opts)
            for s in "rl":
                got = segs(lambda n_: APE.get_bone_pose(p, n_, unreal.AnimPoseSpaces.WORLD).translation, s); ref_ = segs(lambda n_: cs[n_].translation, s)
                d = max(d, abs(got[0] - ref_[0]), abs(got[1] - ref_[1]))
        worst = max(worst, d); rows.append((path.split("/")[-1], n, ("-" if MEASURE else all(oks)), round(d, 2)))
    for r in rows: print("RDARMS   %-44s %4d frames, keys set %s, upper arm and forearm off the reference by %.2f cm" % r)
    print(f"RDARMS {CH}: {len(rows)} clips on her skeleton; the worst segment off the reference {worst:.2f} cm -> {'ok' if worst < 0.1 else 'FAILED'}")
    report[CH] = {"mesh_before_cm": round(before, 1), "mesh_after_cm": round(after, 1), "skeleton_cm": round(skel_len, 1), "clips": len(rows), "worst_cm": round(worst, 2)}
print("RDARMS done " + json.dumps(report))
for _n in ("sk", "skel", "ref", "a"):
    globals().pop(_n, None)
import gc; gc.collect()
