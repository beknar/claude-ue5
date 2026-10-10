"""Ground the FF2 clips: Tripo pins the hips at rest height, so bent-knee poses lift the feet. Per clip, measure how far
the lowest foot/ball sits above its rest height (20th percentile over frames = planted foot) and lower the pelvis track by
that amount (world -Z expressed in the pelvis' parent space). Jump is left as is (airborne hop).
Idempotent: the measured lift after correction is ~0, so re-running changes nothing."""
import unreal
eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions
sk = unreal.load_asset("/Game/FF2/Character/SK_FF2_Anime")
ref = APE.get_reference_pose(sk.get_editor_property("skeleton"))
BONES = ("foot_l", "foot_r", "ball_l", "ball_r")
REST = {b: APE.get_bone_pose(ref, b, unreal.AnimPoseSpaces.WORLD).translation.z for b in BONES}
opts = unreal.AnimPoseEvaluationOptions()
def lift(a):
    n = unreal.AnimationLibrary.get_num_frames(a); L = unreal.AnimationLibrary.get_sequence_length(a)
    m = []
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(a, min(L, k * L / max(n, 1)), opts)
        m.append(min(APE.get_bone_pose(p, b, unreal.AnimPoseSpaces.WORLD).translation.z - REST[b] for b in BONES))
    m.sort(); return m[int(len(m) * 0.2)], m[0], m[len(m) // 2]
for clip in ("Idle", "Walk", "Run", "Box", "CastSpell", "Shoot", "Dance"):
    a = unreal.load_asset(f"/Game/FF2/Anims/AS_FF2_{clip}")
    off, lo, med = lift(a)
    if off < 0.3: print(f"{clip}: lift {off:.2f} cm -> already grounded"); continue
    n = unreal.AnimationLibrary.get_num_frames(a); L = unreal.AnimationLibrary.get_sequence_length(a)
    pos, rot, scl = [], [], []
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(a, min(L, k * L / max(n, 1)), opts)
        loc = APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.LOCAL)
        parent = APE.get_bone_pose(p, "root", unreal.AnimPoseSpaces.WORLD)          # pelvis' parent
        d = parent.inverse_transform_vector_no_scale(unreal.Vector(0, 0, -off)) if hasattr(parent, "inverse_transform_vector_no_scale") \
            else parent.rotation.unrotate_vector(unreal.Vector(0, 0, -off))
        pos.append(loc.translation + d); rot.append(loc.rotation); scl.append(loc.scale3d)
    ctrl = a.get_editor_property("controller")
    ctrl.open_bracket("ground", False)
    ok = ctrl.set_bone_track_keys("pelvis", pos, rot, scl, False)
    ctrl.close_bracket(False)
    eal.save_loaded_asset(a)
    off2, lo2, med2 = lift(a)
    print(f"{clip}: lift p20 {off:.2f} (min {lo:.2f}, median {med:.2f}) -> after {off2:.2f} (min {lo2:.2f}) keys ok={ok}")
