"""ai models/Warrior3.glb, random_dungeonmagic_level5's Warrior (the user's of 2026-10-26: she replaces the Warrior there;
the other levels keep the old one): tripo_build.py's clip maker, tag Warrior3 (her own rig and proportions: nothing is
lengthened). Her GLB has Tripo's clips: idle, walk, run, slash (every two-handed sword's attack), five hit reactions,
box_01 / box_03, front_kick_02, clap, dance_01, wave_goodbye_02.

  - her own clips as Tripo made them, but where a clip holds her pelvis off its rest place (her run: the whole body 58 %
    of her height in front of where she stands, all through it; in the game her capsule would have been left behind)
    the pelvis is moved back by its mean offset across the clip, level (its children follow);
  - W5_Bow and W5_Shoot (weapon5_clips.py, W5_CLIPS=Bow,Shoot) solved on her own rig, as for the other heroes;
  - slash.json for the game (855) and the reel: as warrior2_clips.chop_numbers, for her slash.
The clips she takes over from the old Warrior (her sword-and-shield attacks, flinch, death) are retargeted in Unreal
(pipeline/unreal/862).
Writes <out_dir>/slash.json and (weapon5_clips) <out_dir>/w5_times.json.
Blender: tripo_build.py -- "ai models/Warrior3.glb" <out_dir> SK_JRPG_Warrior3 Warrior3 165 <this file>"""
import json, os, sys
import bpy
from mathutils import Matrix, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import warrior2_clips as W2
OFF_MAX = 0.05          # (of her height: a pelvis held further than this from its rest place, level, is moved back)


def recentre(arm, frames):
    """the clip's pelvis moved back level by its mean offset from its rest place (armature space); None if it is near"""
    P = arm.pose.bones; rest = arm.data.bones["pelvis"].head_local; offs = []
    for fr in frames:
        W2.pose(arm, fr); h = P["pelvis"].head; offs.append(Vector((h.x - rest.x, h.y - rest.y, 0.0)))
    mean = sum(offs, Vector()) / len(offs)
    if mean.length < OFF_MAX * W2_height(arm): return None, mean
    out = []
    for fr in frames:
        W2.pose(arm, fr); pb = P["pelvis"]; pb.matrix = Matrix.Translation(-mean) @ pb.matrix; bpy.context.view_layer.update()
        f2 = dict(fr); f2["pelvis"] = pb.matrix_basis.decompose(); out.append(f2)
    for pb in P: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    return out, mean


def W2_height(arm):
    me = next(o for o in bpy.context.scene.objects if o.type == 'MESH' and o.vertex_groups)
    zs = [(me.matrix_world @ v.co).z for v in me.data.vertices]
    return max(zs) - min(zs)


def make_clips(arm, scene, clips):
    out = {}
    for name, frames in clips.items():
        fixed, mean = recentre(arm, frames)
        if fixed is not None:
            out[name] = fixed
            print("WARRIOR3 %s: the pelvis held (%.2f, %.2f) of her height off its rest place on average: moved back" % (name, mean.x / W2_height(arm), mean.y / W2_height(arm)))
    if "Slash" in clips:
        nums = W2.chop_numbers(arm, scene, out.get("Slash", clips["Slash"]))
        print("WARRIOR3 slash:", json.dumps(nums))
        argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
        if len(argv) > 1: os.makedirs(argv[1], exist_ok=True); json.dump(nums, open(os.path.join(argv[1], "slash.json"), "w"), indent=1)
    os.environ["W5_CLIPS"] = "Bow,Shoot"
    import weapon5_clips as W5
    for pb in arm.pose.bones: pb.matrix_basis.identity()
    bpy.context.view_layer.update()
    out.update(W5.make_clips(arm, scene, clips))
    return out
