"""FF2 floating + sliding fix on the clips themselves (sole-based, see 285):
- grounding: every frame the lowest heel/toe point (relative to its rest height) is put on the floor by moving the pelvis
  vertically (light +-1 frame smoothing). All clips except Jump.
- foot locking (Walk, Run): the planted contact point should move backward at one constant speed. The pelvis gets a
  horizontal per-frame offset c_k = sum(-d_j) (d = contact-point motion while planted and moving backward), detrended so
  c_N = c_0 (seamless loop). Afterwards the contact point moves at exactly the loop's average stance speed, which is
  printed -> use it as the character's walk/run speed."""
import importlib, sys, os, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("sa", os.path.join(os.path.dirname(os.path.abspath(__file__)), "285_ff2_sole_analysis.py"))
SA = importlib.util.module_from_spec(spec); spec.loader.exec_module(SA)
APE = unreal.AnimPoseExtensions; eal = unreal.EditorAssetLibrary
REST_Z = {(s, nm): __import__("json").load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\ff2_anime\soles.json"))[s][nm][2] for s in ("l", "r") for nm in ("heel", "toe")}
opts = unreal.AnimPoseEvaluationOptions()
def fix(clip, lock, v_target=None):
    """v_target: planted-foot speed to lock to (cm/s). None = loop average (fine for walk, whose stance covers nearly the
    whole cycle); for run (short stance + flight) pass the measured stance speed so only stance deviations are corrected."""
    a = unreal.load_asset(f"/Game/FF2/Anims/AS_FF2_{clip}")
    n = unreal.AnimationLibrary.get_num_frames(a); L = unreal.AnimationLibrary.get_sequence_length(a); dt = L / max(n, 1)
    poses = [APE.get_anim_pose_at_time(a, min(L, k * dt), opts) for k in range(n + 1)]
    fr = [SA.soles(p) for p in poses]
    low = [min(f[key].z - REST_Z[key] for key in f) for f in fr]
    lowS = [sum(low[max(0, i - 1):i + 2]) / len(low[max(0, i - 1):i + 2]) for i in range(len(low))]
    cx = [0.0] * len(fr); cy = [0.0] * len(fr)
    if lock:
        rx = ry = 0.0
        for k in range(1, len(fr)):
            key = min(fr[k], key=lambda q: fr[k][q].z - REST_Z[q])
            prev = min(fr[k - 1], key=lambda q: fr[k - 1][q].z - REST_Z[q])
            if key[0] == prev[0]:                                  # same foot planted on both frames
                d = fr[k][key] - fr[k - 1][key]
                if d.y < 0:                                        # stance (moving backward)
                    if v_target is None: rx -= d.x; ry -= d.y      # cancel its own motion (detrend restores the pace)
                    else: rx -= d.x; ry -= d.y + v_target * dt     # only the deviation from the target pace
            cx[k], cy[k] = rx, ry
        N = len(fr) - 1
        sx, sy = cx[N] / N, cy[N] / N
        cx = [cx[k] - k * sx for k in range(len(fr))]; cy = [cy[k] - k * sy for k in range(len(fr))]
        speed = sy / dt if v_target is None else v_target - sy / dt
        print(f"  {clip}: lock offsets x {min(cx):.1f}..{max(cx):.1f} y {min(cy):.1f}..{max(cy):.1f} cm; stance speed {speed:.1f} cm/s")
    pos, rot, scl = [], [], []
    for k, p in enumerate(poses):
        loc = APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.LOCAL)
        parent = APE.get_bone_pose(p, "root", unreal.AnimPoseSpaces.WORLD)
        pos.append(loc.translation + parent.rotation.unrotate_vector(unreal.Vector(cx[k], cy[k], -lowS[k])))
        rot.append(loc.rotation); scl.append(loc.scale3d)
    ctrl = a.get_editor_property("controller")
    ctrl.open_bracket("foot fix", False); ok = ctrl.set_bone_track_keys("pelvis", pos, rot, scl, False); ctrl.close_bracket(False)
    eal.save_loaded_asset(a)
    srt, st, _, _ = SA.analyse(a)
    msg = f"{clip:9s} ok={ok} after: lowest sole min {srt[0]:.1f} p50 {srt[len(srt)//2]:.1f} max {srt[-1]:.1f}"
    for side in ("l", "r"):
        v = sorted(x[1] for x in st[side])
        if v: msg += f" | {side} vy p25 {v[len(v)//4]:.0f} med {v[len(v)//2]:.0f} p75 {v[3*len(v)//4]:.0f}"
    print(msg)
if __name__ == "__main__":
    only = sys.argv[1:]
    for clip in ("Idle", "Box", "CastSpell", "Shoot", "Dance"):
        if not only or clip in only: fix(clip, False)
    if not only or "Walk" in only: fix("Walk", True)
    if not only or "Run" in only:
        a = unreal.load_asset("/Game/FF2/Anims/AS_FF2_Run"); _, st, _, _ = SA.analyse(a)
        v = sorted(-x[1] for side in st for x in st[side] if x[1] < -150)       # planted, moving backward at running pace
        print("  Run measured stance speeds:", len(v), "median", round(v[len(v) // 2], 1))
        fix("Run", True, v_target=v[len(v) // 2])
