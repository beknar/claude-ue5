"""Sole-based contact analysis of the FF2 clips: per frame, heel/toe points of both shoes (from soles.json, carried by
foot_/ball_ bones) -> lowest sole height (floating) and planted-foot speed (sliding)."""
import json, unreal
APE = unreal.AnimPoseExtensions
SOLES = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\ff2_anime\soles.json"))
sk = unreal.load_asset("/Game/FF2/Character/SK_FF2_Anime")
ref = APE.get_reference_pose(sk.get_editor_property("skeleton"))
PTS = []                                    # (side, name, bone, local point)
for side in ("l", "r"):
    for nm in ("heel", "toe"):
        bone = f"foot_{side}" if nm == "heel" else f"ball_{side}"
        rest = APE.get_bone_pose(ref, bone, unreal.AnimPoseSpaces.WORLD)
        PTS.append((side, nm, bone, rest.inverse_transform_location(unreal.Vector(*SOLES[side][nm]))))
opts = unreal.AnimPoseEvaluationOptions()
def soles(pose):
    out = {}
    for side, nm, bone, lp in PTS:
        out[(side, nm)] = APE.get_bone_pose(pose, bone, unreal.AnimPoseSpaces.WORLD).transform_location(lp)
    return out
def analyse(a):
    n = unreal.AnimationLibrary.get_num_frames(a); L = unreal.AnimationLibrary.get_sequence_length(a); dt = L / max(n, 1)
    fr = [soles(APE.get_anim_pose_at_time(a, min(L, k * dt), opts)) for k in range(n + 1)]
    low = [min(p.z for p in f.values()) for f in fr]
    stance = {"l": [], "r": []}
    for k in range(1, len(fr)):
        for side in ("l", "r"):
            c = min(("heel", "toe"), key=lambda nm: fr[k][(side, nm)].z)
            if fr[k][(side, c)].z < low[k] + 0.8 and fr[k - 1][(side, c)].z < low[k - 1] + 1.2:
                d = fr[k][(side, c)] - fr[k - 1][(side, c)]; stance[side].append((d.x / dt, d.y / dt))
    srt = sorted(low)
    return srt, stance, n, L
if __name__ == "__main__":
    for clip in ("Idle", "Walk", "Run", "Jump", "Box", "CastSpell", "Shoot", "Dance"):
        a = unreal.load_asset(f"/Game/FF2/Anims/AS_FF2_{clip}")
        srt, st, n, L = analyse(a)
        msg = f"{clip:9s} lowest sole z: min {srt[0]:5.1f} p10 {srt[len(srt)//10]:5.1f} p50 {srt[len(srt)//2]:5.1f} max {srt[-1]:5.1f}"
        for side in ("l", "r"):
            v = st[side]
            if v:
                vy = sorted(x[1] for x in v); vx = sorted(x[0] for x in v)
                msg += f" | {side}: n={len(v)} vy med {vy[len(vy)//2]:6.1f} p25 {vy[len(vy)//4]:6.1f} p75 {vy[3*len(vy)//4]:6.1f} vx med {vx[len(vx)//2]:5.1f}"
        print(msg)
