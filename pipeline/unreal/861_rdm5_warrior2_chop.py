"""random_dungeonmagic_level5: the chop test of ai models/Warrior2.glb (the user's: Warrior2 alone, her own clip on her
own rig; the heroes and their clips are not touched). Run after blender_numpy/tripo_build.py built her with
warrior2_clips.py into SourceArt/jrpg_warrior2 and 600_tripo_import.py Warrior2 imported her (SK_JRPG_Warrior2 on a
skeleton of her own, /Game/JRPG/Warrior2Anims/AS_Warrior2_<Clip>).
- her clips: no root motion, the root locked (warrior2_clips put the chop's root at rest)
- in the level (tags, made again on each run): a SkeletalMeshActor RDM5_Warrior2 (her mesh, the chop as its animation,
  not playing) and the Plate Knight's Sword RDM5_Warrior2Sword attached to her right hand, both hidden in play, without
  collision, out of the way under the level; 815's way "chop2" brings them out for the reel
- the sword in her right hand as weapon5_clips holds a sword (the blade the thumb's way leaning 25 degrees toward the
  fingers), its grip point (where a hand closes, 4.5 cm under the guard) chop.json's left_on cm along the blade from the
  right palm: where the clip's left palm comes along the hilt (it is the upper hand); the left hand is left where the clip
  puts it (chop.json's left_off: how far off the hilt line)
Prints the grip and what was placed, saves the level. Args: none"""
import json, math, os, unreal
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
MAP = "/Game/RandomDungeon/Maps/random_dungeonmagic_level5"
CH = "Warrior2"; ANIMS = f"/Game/JRPG/{CH}Anims"; SKM = f"/Game/JRPG/Character/SK_JRPG_{CH}"
SWORD = "PlateKnightSSword"
FR = json.load(open(os.path.join(SA, "random_dungeon_magic5", "weapon_frames.json"), encoding="utf-8"))["weapons"]
CHOP = json.load(open(os.path.join(SA, "jrpg_warrior2", "chop.json")))
eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions; ML = unreal.MathLibrary; V = unreal.Vector
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def vec(a): return V(*a)
def frame_xf(origin, x, y): return unreal.Transform(origin, ML.make_rot_from_xy(x, y), V(1, 1, 1))
def mesh_frame(k): f = FR[k]; return frame_xf(vec(f["origin"]), vec(f["x"]), vec(f["y"]))
def grip_from(frame_in_hand, k): return ML.compose_transforms(ML.invert_transform(mesh_frame(k)), frame_in_hand)


def sword_in_hand(out):
    """the sword's frame in the right hand (hand-bone space): 855's two-handed frame, `out` cm further along the blade"""
    ref = APE.get_reference_pose(unreal.load_asset(SKM).get_editor_property("skeleton"))
    bone = lambda n: APE.get_bone_pose(ref, n, unreal.AnimPoseSpaces.WORLD)
    hand = bone("hand_r"); h = hand.translation
    fore = (h - bone("lowerarm_r").translation).normal()
    th = bone("thumb_01_r").translation - h; along = (bone("middle_01_r").translation - h).normal()
    th = th - along * th.dot(along); th = (th - fore * th.dot(fore)).normal()
    palm = h + fore * 6.5 + V(0, 0, -2.5)
    g = math.radians(25.0); x = (th * math.cos(g) + fore * math.sin(g)).normal(); y = (along - x * along.dot(x)).normal()
    return ML.make_relative_transform(frame_xf(palm + x * out, x, y), hand)


# ---- her clips
clips = {}
for p in eal.list_assets(ANIMS, recursive=False):
    a = unreal.load_asset(p.split(".")[0])
    if isinstance(a, unreal.AnimSequence):
        a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
        clips[a.get_name()] = a
chop = clips[f"AS_{CH}_Chop"]
# ---- the level
if not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name().startswith(MAP + "."):
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
for a in eas.get_all_level_actors():
    if a.actor_has_tag("RDM5_Warrior2") or a.actor_has_tag("RDM5_Warrior2Sword"): eas.destroy_actor(a)
away = V(0, 0, -6000)
w2 = eas.spawn_actor_from_class(unreal.SkeletalMeshActor, away)
w2.set_actor_label("RDM5_Warrior2"); w2.tags = ["RDM5_Warrior2"]
sk = w2.skeletal_mesh_component
sk.set_skinned_asset_and_update(unreal.load_asset(SKM))
sk.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
sk.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)
ad = sk.get_editor_property("animation_data"); ad.set_editor_property("anim_to_play", chop); ad.set_editor_property("saved_looping", False)
ad.set_editor_property("saved_playing", False); sk.set_editor_property("animation_data", ad)
w2.set_actor_hidden_in_game(True)
sw = eas.spawn_actor_from_class(unreal.StaticMeshActor, away)
sw.set_actor_label("RDM5_Warrior2Sword"); sw.tags = ["RDM5_Warrior2Sword"]
sw.static_mesh_component.set_static_mesh(unreal.load_asset(FR[SWORD]["mesh"]))
sw.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
sw.set_mobility(unreal.ComponentMobility.MOVABLE)
sw.attach_to_component(sk, "hand_r", unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, unreal.AttachmentRule.KEEP_RELATIVE, False)
grip = grip_from(sword_in_hand(CHOP["left_on"]), SWORD)
sw.root_component.set_relative_transform(grip, False, False)
sw.set_actor_hidden_in_game(True)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
# ---- what was placed: the sword's grip point against her right palm in the reference pose
hand = sk.get_socket_transform("hand_r", unreal.RelativeTransformSpace.RTS_WORLD)
gp = sw.root_component.get_world_transform().transform_location(vec(FR[SWORD]["origin"]))
print("WARRIOR2CHOP clips", sorted(clips), "| chop %.2f s, the blow at %.2f s" % (unreal.AnimationLibrary.get_sequence_length(chop), CHOP["blow"]))
print("WARRIOR2CHOP the sword's grip point %.1f cm from her right hand bone (left_on %.1f along the blade from the palm); the left palm off the hilt line in the clip: %s"
      % ((gp - hand.translation).length(), CHOP["left_on"], CHOP["left_off"]))
print("WARRIOR2CHOP placed", w2.get_actor_label(), sw.get_actor_label(), "attached to", sw.get_attach_parent_actor().get_actor_label() if sw.get_attach_parent_actor() else None, "| level saved")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
