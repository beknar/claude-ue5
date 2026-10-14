"""Hero gallery for docs/heroes.md: three pictures of every possible hero / playable character of the Fab library that is
in this project: full body, upper body and head, and an action pose. The list is SourceArt/hero_gallery/heroes.json
(name, pack, mesh, category, pose family). Shot in the scratch level /Game/RandomLevel/Test/rl_scratch, left empty.
The action pose: the characters are UE4-mannequin rigs (the same bone names and bone axes), so a pose is copied from
another pack's clip: a one-frame AnimSequence on the hero's own skeleton (/Game/HeroGallery/Poses) holding the clip's
local bone rotations at its strike (the frame the right hand is farthest from the hips) on the hero's own bone lengths.
Families: sword (Weapon_Shield_Animations), heavy (Animations_Warrior, an axe), spear (Spear_And_Shield_Animations),
rifle (Sci_Fi_Characters_Pack's Fire_Rifle_Ironsights), unarmed (41_Animations_Monsters' straight punch, at the frame
the fist is farthest forward: the drunk man's swing of Drunk_Man_Animations left the arms out to the sides, and the
sailors' punch of Underwater_odyssey is on bones of other names);
(FF2's spell does not carry over: the Tripo rig's bone axes are not the UE4 mannequin's, and the body lay on the floor)
`own`: the hero's pack has attack clips of its own, played as they are. Melee heroes hold a Medieval_Weapons weapon
(gripped as in 790: a round handle under the hand, checked against the mesh), riflemen MC_Environment's assault rifle
laid along the line between their hands.
The editor world does not evaluate animations: the poses are shot in play-in-editor, which copies the staged actors.
One mode per call:
  stage [start count]  pose animations, then every hero (or a batch of them: all of them at once ran the editor out of
             memory with texture streaming off) twice (neutral; posed, with its weapon) in a row 2 km up, lights, a floor,
             the capture camera; texture streaming off
  shoot dir  (play-in-editor running) dir/<id>_full.png, <id>_bust.png, <id>_action.png
  clear      the staged actors removed (the level saved empty), texture streaming on
Args: mode [dir] [ids] | stage start count | stage ids <id,id,...>"""
import sys, os, re, json, math, unreal
MODE = sys.argv[1]
V = unreal.Vector; ML = unreal.MathLibrary; APE = unreal.AnimPoseExtensions; GS = unreal.GameplayStatics
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
DATA = r"E:\code\claude-ue5\claude_ue5\SourceArt\hero_gallery\heroes.json"
SCRATCH = "/Game/RandomLevel/Test/rl_scratch"; POSES = "/Game/HeroGallery/Poses"
TAG = unreal.Name("hero_gallery"); SP = 6000.0; ORIGIN = V(0, 0, 200000.0)
SRC = {"sword": "/Game/Weapon_Shield_Animations/Animations/Anim_Weapon_Shield_Attack_01", "heavy": "/Game/Animations_Warrior/Animations/With_Weapon/Anim_Warrior_Attack_1",
       "spear": "/Game/Spear_And_Shield_Animations/Animations/Anim_Spear_Shield_Attack_01", "rifle": "/Game/Sci_Fi_Characters_Pack/AnimDemoScene/Animations/Fire_Rifle_Ironsights",
       "unarmed": "/Game/41_Animations_Monsters/Animations/Anim_Monster_Attack_9", "cast": "/Game/FF2/Anims/AS_FF2_CastSpell"}
MW = "/Game/Medieval_Weapons/Meshes/VOL2/"
WEAPON = {"sword": (MW + "SM_Sword_1", 69.0), "heavy": (MW + "SM_Axe", 7.0), "spear": (MW + "SM_Spear", 95.0)}
RIFLE = "/Game/MC_Environment/Assets/SM_Gun_AssaultRifle"; RIFLE_GRIP = V(0, -10, -6)          # (barrel along +Y, up +Z; the pistol grip)
O_EVAL = unreal.AnimPoseEvaluationOptions()


def load_data(): return json.load(open(DATA, encoding="utf-8"))["heroes"]


def cleanup():
    import gc
    for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
    gc.collect()


def strike_time(anim, mid=False, high=False, forward=False):
    """the frame the right hand is farthest from the hips (the blow), or highest (`high`: an axe's wind-up), or the middle"""
    L = unreal.AnimationLibrary.get_sequence_length(anim)
    if mid: return L * 0.5
    best = (0.0, L * 0.4)
    for k in range(41):
        p = APE.get_anim_pose_at_time(anim, L * k / 40, O_EVAL)
        try:
            hr = APE.get_bone_pose(p, "hand_r", unreal.AnimPoseSpaces.WORLD).translation
            d = hr.z if high else (hr.y - APE.get_bone_pose(p, "spine_03", unreal.AnimPoseSpaces.WORLD).translation.y) if forward else \
                (hr - APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.WORLD).translation).length()
        except Exception: continue
        if d > best[0]: best = (d, L * k / 40)
    return best[1]


def pose_anim(skel, family):
    """the one-frame pose of `family` on `skel` (made once per skeleton and family)"""
    name = "A_%s_%s" % (re.sub(r"[^A-Za-z0-9]+", "_", skel.get_path_name().split(".")[0].replace("/Game/", ""))[-60:], family)
    path = POSES + "/" + name
    if eal.does_asset_exist(path): eal.delete_asset(path)
    src = unreal.load_asset(SRC[family]); assert src, SRC[family]
    sp = APE.get_anim_pose_at_time(src, strike_time(src, family == "rifle", False, family == "unarmed"), O_EVAL)      # (an axe at its wind-up turned the body away: the blow it is)
    sref = APE.get_reference_pose(src.get_editor_property("skeleton")); ref = APE.get_reference_pose(skel)
    sb = set(str(b) for b in APE.get_bone_names(sp))
    f = unreal.AnimSequenceFactory(); f.set_editor_property("target_skeleton", skel)
    anim = at.create_asset(name, POSES, unreal.AnimSequence, f)
    ctrl = anim.get_editor_property("controller")
    ctrl.open_bracket("hero pose", True); ctrl.set_frame_rate(unreal.FrameRate(30, 1), True); ctrl.set_number_of_frames(unreal.FrameNumber(1), True)
    shared = 0
    for b in APE.get_bone_names(ref):
        bn = str(b); rt = APE.get_bone_pose(ref, b, unreal.AnimPoseSpaces.LOCAL); rot = rt.rotation; loc = rt.translation
        if bn in sb:
            shared += 1; rot = APE.get_bone_pose(sp, b, unreal.AnimPoseSpaces.LOCAL).rotation
            if bn == "pelvis":                          # (the hips' drop and sway, scaled to this body)
                s = APE.get_bone_pose(sp, b, unreal.AnimPoseSpaces.LOCAL).translation; r0 = APE.get_bone_pose(sref, b, unreal.AnimPoseSpaces.LOCAL).translation
                k = rt.translation.length() / max(r0.length(), 1e-3); loc = V(loc.x + (s.x - r0.x) * k, loc.y + (s.y - r0.y) * k, loc.z + (s.z - r0.z) * k)
        ctrl.add_bone_curve(b, True); ctrl.set_bone_track_keys(b, [loc, loc], [rot, rot], [V(1, 1, 1), V(1, 1, 1)], True)
    ctrl.close_bracket(True); eal.save_loaded_asset(anim, only_if_is_dirty=False)
    return anim, shared


def handle_end(path, hand_z):
    m = unreal.load_asset(path); vs = []
    for sec in range(m.get_num_sections(0)): vs += list(unreal.ProceduralMeshLibrary.get_section_from_static_mesh(m, 0, sec)[0])
    s = [v for v in vs if abs(v.z - hand_z) <= 3.0]
    ex = max(v.x for v in s) - min(v.x for v in s); ey = max(v.y for v in s) - min(v.y for v in s)
    assert max(ex, ey) < 7.5 and max(ex, ey) < 1.8 * max(min(ex, ey), 0.1), (path, hand_z, ex, ey)
    b = m.get_bounding_box(); return 1.0 if b.max.z - hand_z >= hand_z - b.min.z else -1.0


def grip(skel, path, hand_z):
    """a one-handed weapon in hand_r, from the reference pose (790's grip: the handle across the palm, the business end
    the way the thumb points, the edge along the forearm)"""
    ref = APE.get_reference_pose(skel); bone = lambda n: APE.get_bone_pose(ref, n, unreal.AnimPoseSpaces.WORLD)
    hand = bone("hand_r"); fore = (hand.translation - bone("lowerarm_r").translation).normal()
    thumb = V(0, 1, 0); thumb = (thumb - fore * thumb.dot(fore)).normal()
    palm = hand.translation + fore * 6.5 + V(0, 0, -2.5)
    rot = ML.make_rot_from_xz(fore, thumb * handle_end(path, hand_z))
    return ML.make_relative_transform(unreal.Transform(palm - ML.get_up_vector(rot) * hand_z, rot, V(1, 1, 1)), hand)


def rifle_grip(anim):
    """the rifle in hand_r, its barrel along the line from the right hand to the left in the pose"""
    p = APE.get_anim_pose_at_time(anim, 0.0, O_EVAL)
    hr = APE.get_bone_pose(p, "hand_r", unreal.AnimPoseSpaces.WORLD); hl = APE.get_bone_pose(p, "hand_l", unreal.AnimPoseSpaces.WORLD)
    fwd = (hl.translation - hr.translation).normal(); up = V(0, 0, 1); up = (up - fwd * up.dot(fwd)).normal()
    rot = ML.make_rot_from_yz(fwd, up)
    fore = (hr.translation - APE.get_bone_pose(p, "lowerarm_r", unreal.AnimPoseSpaces.WORLD).translation).normal()
    palm = hr.translation + fore * 7.0
    g = unreal.Transform(V(0, 0, 0), rot, V(1, 1, 1)); off = ML.transform_location(g, RIFLE_GRIP)
    return ML.make_relative_transform(unreal.Transform(palm - off, rot, V(1, 1, 1)), hr)


# ================================================================================================ modes
if MODE == "stage":
    if not ues.get_editor_world().get_path_name().startswith(SCRATCH + "."): les.load_level(SCRATCH)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(SCRATCH + "."), w.get_path_name()
    for a in eas.get_all_level_actors():
        if TAG in a.tags: eas.destroy_actor(a)
    unreal.SystemLibrary.execute_console_command(w, "r.TextureStreaming 0")
    def spawn(cls, loc, rot=None, tags=()):
        a = eas.spawn_actor_from_class(cls, loc, rot or unreal.Rotator()); a.tags = [TAG] + [unreal.Name(t) for t in tags]; return a
    H = load_data(); poses = {}; report = []
    IDS = set(sys.argv[3].split(",")) if len(sys.argv) > 3 and sys.argv[2] == "ids" else None
    B0 = int(sys.argv[2]) if len(sys.argv) > 2 and not IDS else 0; BN = int(sys.argv[3]) if len(sys.argv) > 3 and not IDS else len(H)
    fl = spawn(unreal.StaticMeshActor, ORIGIN + V(SP * len(H) / 2, 0, 0)); fl.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Plane"))
    fl.set_actor_scale3d(V(SP * (len(H) + 4) / 100.0, 400, 1))
    key = spawn(unreal.DirectionalLight, ORIGIN + V(0, 0, 1000), unreal.Rotator(roll=0, pitch=-35, yaw=-115)); key.light_component.set_intensity(6.0)
    fill = spawn(unreal.DirectionalLight, ORIGIN + V(0, 0, 1000), unreal.Rotator(roll=0, pitch=-15, yaw=-55)); fill.light_component.set_intensity(2.2); fill.light_component.set_cast_shadows(False)
    rim = spawn(unreal.DirectionalLight, ORIGIN + V(0, 0, 1000), unreal.Rotator(roll=0, pitch=-25, yaw=80)); rim.light_component.set_intensity(3.0); rim.light_component.set_cast_shadows(False)
    sky = spawn(unreal.SkyLight, ORIGIN + V(0, 0, 500)); sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)
    sky.light_component.set_editor_property("cubemap", unreal.load_asset("/Engine/EngineResources/GrayLightTextureCube")); sky.light_component.set_intensity(1.3)
    spawn(unreal.SceneCapture2D, ORIGIN, tags=("H_CAP",))
    for i, h in enumerate(H):
        if not B0 <= i < B0 + BN or (IDS and h["id"] not in IDS): continue
        mesh = unreal.load_asset(h["mesh"]); assert mesh, h["mesh"]
        skel = mesh.skeleton
        for posed in (False, True):
            a = spawn(unreal.SkeletalMeshActor, ORIGIN + V(SP * i + (SP / 2 if posed else 0), 0, 0), tags=("H_%03d_%s" % (i, "P" if posed else "N"),))
            smc = a.skeletal_mesh_component; smc.set_skinned_asset_and_update(mesh); smc.set_editor_property("forced_lod_model", 1)
            smc.set_editor_property("visibility_based_anim_tick_option", unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)
            if not posed: continue
            fam = h["family"]
            if fam == "own":
                clip = unreal.load_asset(h["clip"]); assert clip, h["clip"]; anim, t = clip, strike_time(clip); shared = -1
            else:
                k = (skel.get_path_name(), fam)
                if k not in poses: poses[k] = pose_anim(skel, fam)
                (anim, shared), t = poses[k], 0.0
            smc.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE); smc.override_animation_data(anim, False, False, t, 0.0)
            wp = None
            if fam in WEAPON: wp = (WEAPON[fam][0], grip(skel, *WEAPON[fam]))
            elif fam == "rifle": wp = (RIFLE, rifle_grip(anim))
            if wp:
                wa = spawn(unreal.StaticMeshActor, a.get_actor_location(), tags=("H_%03d_W" % i,)); wa.static_mesh_component.set_static_mesh(unreal.load_asset(wp[0]))
                wa.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE); wa.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                wa.attach_to_actor(a, "hand_r", unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, False)
                wa.set_actor_relative_transform(wp[1], False, False)
            report.append((h["id"], fam, shared))
    print("HEROGAL staged", len(report), "heroes,", len(poses), "pose animations | bones shared with the pose clip (min):", min(s for _, _, s in report if s >= 0))
    for hid, fam, shared in report:
        if 0 <= shared < 40: print("HEROGAL few shared bones", hid, fam, shared)

elif MODE == "shoot":
    OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
    ONLY = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
    w = ues.get_game_world(); assert w, "play-in-editor is not running"
    H = load_data()
    acts = {}
    for a in GS.get_all_actors_with_tag(w, TAG):
        for t in a.tags:
            if str(t).startswith("H_"): acts[str(t)] = a
    cap = acts["H_CAP"]; comp = cap.capture_component2d
    rt = unreal.RenderingLibrary.create_render_target2d(w, 640, 832, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    comp.texture_target = rt; comp.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    comp.capture_every_frame = False; comp.capture_on_movement = False; comp.always_persist_rendering_state = True
    VF = math.atan(math.tan(math.radians(15.0)) * 832.0 / 640.0)            # (the vertical half field for a 30 degree horizontal one)
    def shoot(name, look, half_h, half_w, yaw_deg, pitch_up=0.08, fov=30.0):
        comp.fov_angle = fov
        d = max(half_h / math.tan(VF), half_w / math.tan(math.radians(fov / 2))) * 1.12
        yaw = math.radians(90.0 - yaw_deg)
        cam = V(look.x + math.cos(yaw) * d, look.y + math.sin(yaw) * d, look.z + d * pitch_up)
        cap.set_actor_location(cam, False, False); cap.set_actor_rotation(ML.find_look_at_rotation(cam, look), False)
        for _ in range(6): comp.capture_scene()
        unreal.RenderingLibrary.export_render_target(w, rt, OUT, name)
    n = 0
    for i, h in enumerate(H):
        if (ONLY and h["id"] not in ONLY) or ("H_%03d_N" % i) not in acts: continue
        a = acts["H_%03d_N" % i]; p = acts["H_%03d_P" % i]; smc = a.skeletal_mesh_component
        org, ext = a.get_actor_bounds(False)
        base = a.get_actor_location(); top = org.z + ext.z; bottom = org.z - ext.z
        shoot("%s_full.png" % h["id"], V(base.x, base.y, (top + bottom) / 2), (top - bottom) / 2 + 8, ext.x + 10, 22.0)
        try:
            hz = smc.get_socket_location("head").z; sz = smc.get_socket_location("spine_01").z
            head_top = min(top, hz + 26.0); lo = sz - 6.0
            assert hz > (top + bottom) / 2 and head_top - lo > 40.0          # (a model whose head bone is not where its head is)
        except Exception:
            head_top, lo = top, bottom + (top - bottom) * 0.5
        shoot("%s_bust.png" % h["id"], V(base.x, base.y, (head_top + lo) / 2), (head_top - lo) / 2 + 4, 40.0, 18.0, 0.04)
        porg, pext = p.get_actor_bounds(False, True)
        shoot("%s_action.png" % h["id"], porg, pext.z + 6, max(pext.x, pext.y) * 0.9 + 10, 26.0)
        n += 1
    print("HEROGAL shot", n, "heroes")

elif MODE == "clear":
    w = ues.get_editor_world()
    if w.get_path_name().startswith(SCRATCH + "."):
        for a in eas.get_all_level_actors():
            if TAG in a.tags: eas.destroy_actor(a)
        les.save_current_level()
    unreal.SystemLibrary.execute_console_command(w, "r.TextureStreaming 1")
    print("HEROGAL cleared")
cleanup()
