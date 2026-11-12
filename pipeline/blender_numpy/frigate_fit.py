"""The frigate's proportions measured from its reference picture (frigate2.png, 1632 x 1216), not guessed: a pinhole
camera and the engine block's dimensions are solved together (scipy least squares) from points picked on the picture
(the stern's engine panel and red corner chamfer, the step to the superstructure) and its silhouette (the alpha
channel: the near bottom edge and the far top edge of the block); then every other feature picked on the picture is
carried back to the ship along the camera's ray to the plane it lies on (the near side, the step, the top, the
centreline), giving its place in metres. The block's height is the scale (16 m); frigate_build.py scales all of it to
the ship's length.
Frame: Blender's, as frigate_build.py: the near side of the picture is -X, the bow toward -Y, the stern at s = 0
(Y = +S0), up +Z.
With --elevation <degrees> the camera's height above the ship is held to that angle (the picture's deck shows it seen
from above more steeply than its corners alone give: an AI picture's perspective is not one camera's).
Python (numpy, scipy, Pillow): frigate_fit.py <picture.png> <out.json> [--elevation <degrees>]"""
import json, sys
import numpy as np
from PIL import Image
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

PIC, OUT = sys.argv[1], sys.argv[2]
ELEV = float(sys.argv[sys.argv.index("--elevation") + 1]) if "--elevation" in sys.argv else None
alpha = np.asarray(Image.open(PIC))[..., 3]
H_IMG, W_IMG = alpha.shape
CX, CY = W_IMG / 2, H_IMG / 2
S0 = 55.0
ZT, ZB = 8.0, -8.0                                                                # (the block's height: the scale)
# (the one assumption: one view cannot tell the block's width from the angle it is seen at, nor so its length: its cross-
# section is taken as 11.2 m wide (0.7 of its height; the width the silhouette's overlay of the first fit settled on), the
# engine panel 7 m of it, 45 degree chamfers at its corners and 1.5 m ones along its top. Taking the top edges as 3 m
# rounds (as the picture shows them) fitted worse, 11.4 px against 8.4, with a camera three times nearer: the problem is
# poorly conditioned, and this is the fit kept)
HW, WF, CT = 5.6, 3.5, 1.5
WT = HW - CT
ZT_FAR = 8.0
CS = HW - WF


def W(s, x, z):
    return np.array([x, S0 - s, z], float)


def sil(x, which):
    col = np.where(alpha[:, x] > 128)[0]
    return float(col.min() if which == "top" else col.max())


# ---------------------------------------------------------------- the picks (picture pixels)
PICK = {
    "face_TL": (80, 703), "face_BL": (86, 935), "face_TR": (157, 705), "face_BR": (160, 937),   # (the engine panel)
    "cham_T": (206, 688), "cham_B": (215, 958),                                                # (the red chamfer's side edge)
    "step_top": (548, 600),                                                                    # (the block's near top edge at the step)
}
NEAR_TOP = [(300, 650), (400, 628), (500, 608)]                                    # (the near top edge, where the side meets the chamfer)
BOTTOM = [(x, sil(x, "bot")) for x in (280, 320, 360, 400, 440)]                  # (the near bottom edge)
TOP = [(x, sil(x, "top")) for x in (240, 280, 320, 360, 400)]                      # (the far top edge)

# ---------------------------------------------------------------- unknowns: the camera, the block, the edge points' s
NAMES = ["cx", "cy", "cz", "rx", "ry", "rz", "f", "zf1", "zf0", "S1"] + \
        ["sb%d" % i for i in range(len(BOTTOM))] + ["st%d" % i for i in range(len(TOP))] + ["sn%d" % i for i in range(len(NEAR_TOP))]


def look_rot(C, at):
    """a camera rotation (world to camera, +Z the view, +Y down) looking from C at `at`"""
    fwd = (at - C) / np.linalg.norm(at - C)
    right = np.cross(fwd, [0, 0, 1.0]); right /= np.linalg.norm(right)
    down = np.cross(fwd, right)
    return np.vstack([right, down, fwd])


C0 = np.array([-120.0, 75.0, 68.0]); R0 = look_rot(C0, np.array([0, 0, 2.0]))


def unpack(p):
    d = dict(zip(NAMES, p)); d.update(hw=HW, wf=WF, wt=WT, cs=CS)
    C = np.array([d["cx"], d["cy"], d["cz"]])
    R = Rotation.from_rotvec([d["rx"], d["ry"], d["rz"]]).as_matrix() @ R0
    return d, C, R


def project(Xw, C, R, f):
    Xc = R @ (Xw - C)
    return np.array([CX + f * Xc[0] / Xc[2], CY + f * Xc[1] / Xc[2]])


def model_points(d):
    pts = {"face_TL": W(0, d["wf"], d["zf1"]), "face_BL": W(0, d["wf"], d["zf0"]), "face_TR": W(0, -d["wf"], d["zf1"]),
           "face_BR": W(0, -d["wf"], d["zf0"]), "cham_T": W(d["cs"], -d["hw"], d["zf1"]), "cham_B": W(d["cs"], -d["hw"], d["zf0"]),
           "step_top": W(d["S1"], -d["hw"], ZT - CT)}
    return pts


def resid(p):
    d, C, R = unpack(p)
    r = []
    mp = model_points(d)
    for k, uv in PICK.items(): r += list(project(mp[k], C, R, d["f"]) - uv)
    for i, uv in enumerate(BOTTOM): r += list(project(W(d["sb%d" % i], -d["hw"], ZB), C, R, d["f"]) - uv)
    for i, uv in enumerate(TOP): r += list(project(W(d["st%d" % i], d["wt"], ZT_FAR), C, R, d["f"]) - uv)
    for i, uv in enumerate(NEAR_TOP): r += list(project(W(d["sn%d" % i], -d["hw"], ZT - CT), C, R, d["f"]) - uv)
    if ELEV is not None:                                                         # (the camera's angle above the engine block)
        rel = C - W(12.0, 0.0, 0.0)
        r.append(200.0 * (np.degrees(np.arctan2(rel[2], np.hypot(rel[0], rel[1]))) - ELEV))
    return np.array(r)


p0 = np.array([*C0, 0, 0, 0, 1600.0, 6.0, -6.0, 40.0] + [10 + 8 * i for i in range(len(BOTTOM))] + [8 + 7 * i for i in range(len(TOP))]
              + [10 + 9 * i for i in range(len(NEAR_TOP))])
fit = least_squares(resid, p0, x_scale="jac", max_nfev=20000)
d, C, R = unpack(fit.x)
rr = (resid(fit.x)[:-1] if ELEV is not None else resid(fit.x)).reshape(-1, 2)
print("FIT cost %.2f, rms %.2f px, worst %.2f px" % (fit.cost, np.sqrt((rr ** 2).sum(1).mean()), np.sqrt((rr ** 2).sum(1)).max()))
print("CAMERA C", C.round(2), "f", round(d["f"], 1))
print("BLOCK", {k: round(d[k], 2) for k in ["hw", "wt", "wf", "cs", "zf1", "zf0", "S1"]})


# ---------------------------------------------------------------- the other features, carried back to their planes
def ray(uv):
    v = np.array([(uv[0] - CX) / d["f"], (uv[1] - CY) / d["f"], 1.0])
    return C, R.T @ v


def on_plane(uv, axis, value):
    o, v = ray(uv)
    t = (value - o[axis]) / v[axis]
    X = o + v * t
    return {"s": round(S0 - X[1], 2), "x": round(X[0], 2), "z": round(X[2], 2)}


SIDE, STEP = 0, 1                                                                    # (the planes: x =, y =)
out = {"camera": {"C": C.tolist(), "R": R.tolist(), "f": d["f"], "cx": CX, "cy": CY}, "block": {k: d[k] for k in ["hw", "wt", "wf", "cs", "zf1", "zf0", "S1"]},
       "scale_height": ZT - ZB, "rms_px": float(np.sqrt((rr ** 2).sum(1).mean()))}
# the mid hull's near side: the step's outer corner (on the step's plane, s = S1)
yS1 = S0 - d["S1"]
corner = [on_plane(uv, STEP, yS1) for uv in [(615, 575), (615, 665)]]
hm = -np.mean([c["x"] for c in corner])
out["mid_side_x"] = float(hm); out["step_corner"] = corner
print("MID SIDE half width %.2f (the step's corner %s)" % (hm, corner))
# features on the mid hull's near side (x = -hm) and on the block's (x = -hw)
FEAT_MID = {
    "mid_top_near@600": (600, 560), "mid_top_near@700": (700, 520), "mid_top_near@860": (860, 452), "mid_top_near@1000": (1000, 408),
    "mid_top_near@1140": (1140, 380), "cap_front_top": (1190, 398), "cap_front_bottom": (1200, 432),
    "mid_bottom@640": (640, 842), "mid_bottom@800": (800, 790), "mid_bottom@900": (900, 760), "mid_bottom@1000": (1000, 735),
    "portholes_first": (895, 600), "portholes_last": (965, 622), "red_stripe_aft": (1040, 512), "red_stripe_fore": (1190, 500),
    "red_stripe_low": (1045, 548), "red_wedge_top_aft": (1060, 578), "red_wedge_top_fore": (1120, 572),
    "red_wedge_low_aft": (1020, 668), "light_bar_top": (1185, 585), "light_bar_bottom": (1172, 632),
    "pod_front_top": (1488, 472), "pod_front_bottom": (1488, 512), "pod_root_top": (1190, 478),
    "wedge_tip_top": (1605, 523), "wedge_tip_bottom": (1548, 607), "wedge_root_bottom": (1110, 690), "wedge_root_top": (1200, 528),
    "upper_blade_tip": (1518, 452), "upper_blade_root": (1205, 432), "lower_blade_tip": (1512, 670), "lower_blade_root": (1300, 680),
    "fin_root_aft": (700, 840), "fin_root_fore": (840, 822),
}
FEAT_BLOCK = {"portholes_aft_block": (480, 638), "pad_engine_glow": (610, 822)}
for k, uv in FEAT_MID.items(): out[k] = on_plane(uv, SIDE, -hm)
for k, uv in FEAT_BLOCK.items(): out[k] = on_plane(uv, SIDE, -d["hw"])
# the sensor head and the barrels: on the centreline plane x = 0 (their near faces stand off it by their half widths)
for k, uv in {"head_top_aft": (575, 392), "head_top_fore": (690, 398), "head_bottom_aft": (575, 470), "barrel1_tip": (707, 290),
              "barrel2_tip": (752, 312), "barrel3_tip": (796, 302), "barrel_base": (715, 380)}.items():
    out[k] = on_plane(uv, SIDE, -3.0 if k.startswith("head") else 0.0)
# the fin's tip: the fin falls outward; on a plane 8 m out from the mid side (an assumption: one view cannot tell)
for k, uv in {"fin_tip_fore": (1000, 905), "fin_tip_aft": (960, 932)}.items(): out[k] = on_plane(uv, SIDE, -hm - 8.0)
for k, v in out.items():
    if isinstance(v, dict) and "s" in v: print("%-22s s %7.2f  z %6.2f" % (k, v["s"], v["z"]))
json.dump(out, open(OUT, "w"), indent=1)
print("FIT DONE", OUT)
