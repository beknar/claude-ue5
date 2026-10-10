"""Per-frame grounding for the FF2 standing clips (Idle, Box, CastSpell, Shoot, Dance): these move between standing, crouching
and kneeling with the hips pinned, so one offset per clip cannot work. Each frame's pelvis is lowered by that frame's
lowest-foot lift (smoothed over +-3 frames) so a foot stays planted throughout. Idempotent (re-run measures ~0)."""
import unreal
eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions
sk = unreal.load_asset("/Game/FF2/Character/SK_FF2_Anime")
ref = APE.get_reference_pose(sk.get_editor_property("skeleton"))
BONES = ("foot_l", "foot_r", "ball_l", "ball_r")
REST = {b: APE.get_bone_pose(ref, b, unreal.AnimPoseSpaces.WORLD).translation.z for b in BONES}
opts = unreal.AnimPoseEvaluationOptions()
def sample(a):
    n = unreal.AnimationLibrary.get_num_frames(a); L = unreal.AnimationLibrary.get_sequence_length(a)
    return [APE.get_anim_pose_at_time(a, min(L, k * L / max(n, 1)), opts) for k in range(n + 1)]
def lifts(poses):
    return [min(APE.get_bone_pose(p, b, unreal.AnimPoseSpaces.WORLD).translation.z - REST[b] for b in BONES) for p in poses]
for clip in ("Idle", "Box", "CastSpell", "Shoot", "Dance"):
    a = unreal.load_asset(f"/Game/FF2/Anims/AS_FF2_{clip}")
    poses = sample(a); raw = lifts(poses); N = len(raw)
    sm = [sum(raw[max(0, i - 3):i + 4]) / len(raw[max(0, i - 3):i + 4]) for i in range(N)]
    pos, rot, scl = [], [], []
    for p, off in zip(poses, sm):
        loc = APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.LOCAL)
        parent = APE.get_bone_pose(p, "root", unreal.AnimPoseSpaces.WORLD)
        pos.append(loc.translation + parent.rotation.unrotate_vector(unreal.Vector(0, 0, -off))); rot.append(loc.rotation); scl.append(loc.scale3d)
    ctrl = a.get_editor_property("controller")
    ctrl.open_bracket("ground frames", False); ok = ctrl.set_bone_track_keys("pelvis", pos, rot, scl, False); ctrl.close_bracket(False)
    eal.save_loaded_asset(a)
    after = sorted(lifts(sample(a)))
    print(f"{clip}: before min {min(raw):.1f} max {max(raw):.1f} -> after min {after[0]:.1f} p50 {after[len(after)//2]:.1f} max {after[-1]:.1f} ok={ok}")
