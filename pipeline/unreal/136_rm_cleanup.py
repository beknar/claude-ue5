"""Leg sweep / spin kick: root carries only smoothed ground travel (no yaw; the hip-line yaw flips during these
moves); pelvis re-baked in root space so the body pose is unchanged."""
import unreal
APE = unreal.AnimPoseExtensions; ML = unreal.MathLibrary
for clip in ("Leg_Sweep", "Step_Step_Turn_Kick"):
    a = unreal.load_asset(f"/Game/Meshy/Anims/AS_Meshy_{clip}")
    a.set_editor_property("enable_root_motion", False)
    L = unreal.AnimationLibrary.get_sequence_length(a)
    nf = unreal.AnimationLibrary.get_num_frames(a)
    opts = unreal.AnimPoseEvaluationOptions()
    roots, pelv = [], []
    for k in range(nf + 1):
        p = APE.get_anim_pose_at_time(a, min(L, k * L / nf), opts)
        roots.append(APE.get_bone_pose(p, "root", unreal.AnimPoseSpaces.WORLD))
        pelv.append(APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.WORLD))
    # smoothed planar root path (centered moving average, ~0.3 s), pinned to start/end
    W = 4
    xy = [(r.translation.x, r.translation.y) for r in roots]
    sm = []
    for k in range(len(xy)):
        lo, hi = max(0, k - W), min(len(xy), k + W + 1)
        sm.append((sum(v[0] for v in xy[lo:hi]) / (hi - lo), sum(v[1] for v in xy[lo:hi]) / (hi - lo)))
    sm[0] = (0.0, 0.0); sm[-1] = xy[-1]
    rpos, rrot, rscl, ppos, prot, pscl = [], [], [], [], [], []
    for k in range(len(xy)):
        rpos.append(unreal.Vector(sm[k][0], sm[k][1], 0.0)); rrot.append(unreal.Quat(0, 0, 0, 1)); rscl.append(unreal.Vector(1, 1, 1))
        pc = pelv[k]
        ppos.append(pc.translation - unreal.Vector(sm[k][0], sm[k][1], 0.0)); prot.append(pc.rotation); pscl.append(unreal.Vector(1, 1, 1))
    ctrl = a.get_editor_property("controller")
    ctrl.open_bracket("root motion cleanup", False)
    ok1 = ctrl.set_bone_track_keys("root", rpos, rrot, rscl, False)
    ok2 = ctrl.set_bone_track_keys("pelvis", ppos, prot, pscl, False)
    ctrl.close_bracket(False)
    a.set_editor_property("enable_root_motion", True)
    unreal.EditorAssetLibrary.save_loaded_asset(a)
    a.set_editor_property("enable_root_motion", False)
    chk = []
    for k in range(0, len(xy), max(1, len(xy) // 6)):
        p = APE.get_anim_pose_at_time(a, min(L, k * L / nf), opts)
        r = APE.get_bone_pose(p, "root", unreal.AnimPoseSpaces.WORLD); pv = APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.WORLD)
        chk.append("(%d,%d,y%d | pelvis %d,%d,%d)" % (r.translation.x, r.translation.y, r.rotation.rotator().yaw, pv.translation.x, pv.translation.y, pv.translation.z))
    a.set_editor_property("enable_root_motion", True); unreal.EditorAssetLibrary.save_loaded_asset(a)
    print(clip, "keys", len(xy), "set", ok1, ok2, " ".join(chk))
