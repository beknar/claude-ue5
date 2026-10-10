"""Natural ground speed of in-place loops: backward speed of the planted foot during stance."""
import unreal
def speed(path, fps=60):
    a = unreal.load_asset(path); L = a.get_play_length()
    opts = unreal.AnimPoseEvaluationOptions()
    n = int(L * fps)
    pts = {"ball_l": [], "ball_r": []}
    for i in range(n + 1):
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, i / fps, opts)
        for b in pts:
            t = unreal.AnimPoseExtensions.get_bone_pose(pose, b, unreal.AnimPoseSpaces.WORLD).translation
            pts[b].append((t.x, t.y, t.z))
    import statistics
    vs = []
    for b, P in pts.items():
        zmin = min(p[2] for p in P)
        for i in range(1, len(P)):
            if P[i][2] < zmin + 2.0 and P[i - 1][2] < zmin + 2.0:
                vs.append(-(P[i][1] - P[i - 1][1]) * fps)
    fwd = statistics.median(vs) if vs else 0
    return L, fwd, len(vs)
for p in ("/MetaHumanCharacter/Optional/Animation/UEFNAnimPreset/Locomotion/AS_MH_Neutral_Walk_Loop_F",
          "/MetaHumanCharacter/Optional/Animation/UEFNAnimPreset/Locomotion/AS_MH_Neutral_Run_Loop_F",
          "/Game/Fig4/Locomotion/Anims/MF_Unarmed_Walk_Fwd_Fig4", "/Game/Fig4/Locomotion/Anims/MF_Unarmed_Jog_Fwd_Fig4"):
    L, v, n = speed(p)
    print(f"{p.split('/')[-1]}: length {L:.2f}s, stance-foot speed {v:.1f} cm/s (+Y fwd) over {n} samples")
