"""Seams in the wilderness's ground: steps far bigger than the ground on either side of them (the user's of 2026-11-08: "a wall
of earth that is a sheer drop that can't be climbed", 12 km from Brokenspire; the regions' mixing jumped where a mountain
region gained its place, and a lake's bank stopped dead 120 m out).

A steep face (a mountain's flank, a canyon's stepped wall) rises over many samples alike; a seam is one step with gentle
ground before and after it. Reads a grid written by the C++ probe (RD/RDWildProbe.cpp, no game and no GPU):

    UnrealEditor-Cmd.exe <uproject> -run=RDWildProbe -nullrhi -unattended -Seed=<n> -X=<m> -Y=<m> -Half=<m> -Step=<m> -Out=<dir>
    python wild_seams.py <dir> [--min 6] [--ratio 4] [--json out.json]

A step counts as a seam when it is more than --min metres and more than --ratio times the larger of the steps before and after
it along the same line (water's samples left out). Exit code 1 when any is found. Needs numpy."""
import argparse, json, os, sys
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("dir")
ap.add_argument("--min", type=float, default=6.0)
ap.add_argument("--ratio", type=float, default=4.0)
ap.add_argument("--json", default="")
a = ap.parse_args()

info = {}
for l in open(os.path.join(a.dir, "info.txt")):
    p = l.strip().split("|")
    if p[0] == "grid": info.update(n=int(p[1]), x0=float(p[2]), y0=float(p[3]), step=float(p[4]))
    if p[0] == "seed": info["seed"] = int(p[1])
n, x0, y0, st = info["n"], info["x0"], info["y0"], info["step"]
h = np.fromfile(os.path.join(a.dir, "h.bin"), np.float32).reshape(n, n)
wet = np.fromfile(os.path.join(a.dir, "water.bin"), np.float32).reshape(n, n) > -1e8

seams = []
for ax in (0, 1):
    hh = h if ax == 0 else h.T
    ww = wet if ax == 0 else wet.T
    d = np.abs(np.diff(hh, axis=0))                       # d[i] is the step from row i to i + 1
    dry = ~(ww[:-1] | ww[1:])
    before = np.zeros_like(d); before[1:] = d[:-1]
    after = np.zeros_like(d); after[:-1] = d[1:]
    side = np.maximum(before, after)
    m = dry & (d > a.min) & (d > a.ratio * side)
    m[0] = m[-1] = False
    for i, j in zip(*np.nonzero(m)):
        x, y = (x0 + i * st, y0 + j * st) if ax == 0 else (x0 + j * st, y0 + i * st)
        seams.append({"x": round(x, 1), "y": round(y, 1), "way": "north" if ax == 0 else "east", "step_m": round(float(d[i, j]), 2),
                      "side_m": round(float(side[i, j]), 2), "low_m": round(float(min(hh[i, j], hh[i + 1, j])), 1)})
seams.sort(key=lambda s: -s["step_m"])
res = {"seed": info.get("seed"), "grid": [n, x0, y0, st], "min_m": a.min, "ratio": a.ratio, "seams": len(seams),
       "largest_step_m": seams[0]["step_m"] if seams else 0.0, "worst": seams[:20],
       "steps_over_min": int(sum(int((np.abs(np.diff(h, axis=k)) > a.min).sum()) for k in (0, 1)))}
print(f"seed {res['seed']}: grid {n} x {n} at {st} m from ({x0:.0f}, {y0:.0f}); steps over {a.min} m: {res['steps_over_min']}; "
      f"seams (over {a.ratio} x the ground either side): {len(seams)}")
for s in seams[:12]:
    print(f"  {s['step_m']:7.2f} m step (the ground either side {s['side_m']:.2f} m) at ({s['x']:.0f}, {s['y']:.0f}) going {s['way']}, its foot at {s['low_m']:.0f} m")
if a.json:
    with open(a.json, "w") as f: json.dump(res, f, indent=1)
sys.exit(1 if seams else 0)
