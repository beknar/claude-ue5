"""The villages' terraces measured without a game (the list of 2026-11-20's seventh phase, docs/improvements15_plan.md): two grids
written by the C++ probe round one village, with the terraces and without (RD/RDWildProbe.cpp, no game and no GPU):

    UnrealEditor-Cmd.exe <uproject> -run=RDWildProbe -nullrhi -unattended -Seed=<n> -X=<m> -Y=<m> -Half=90 -Step=1 -Heights -Out=<with>
    UnrealEditor-Cmd.exe <uproject> -run=RDWildProbe -nullrhi -unattended -Seed=<n> -X=<m> -Y=<m> -Half=90 -Step=1 -NoTerraces -Out=<without>
    python terrace_check.py <with> <without> [--json out.json]

For the village whose pads the "with" grid's info.txt lists (the one nearest the window's middle):
- each pad level: the drawn ground (Sample's height) over the pad, 1 m in from its edges, within 5 cm of the pad's height;
- what she walks on (Height) and what is drawn agree over it (the probe's hdiff, -Heights);
- on foot: from the square's middle, every house's front door and the land beyond the village reached by steps climbing at most
  0.75 of their length (37 degrees), never through water or a wall's band;
- every step the terraces add (a step of 1.5 m or more between two neighbouring samples, four times the steps beside it, found in
  the grid with them and not in the one without) lies on a pad's edge (within 2.5 m of it, the wall's band and a sample), where its
  retaining wall stands; and none away from them;
- the ground beyond 90 m of the village's middle the same in both grids (no change outside the village).
Exit code 1 when any check fails. Needs numpy."""
import argparse, json, math, os, sys
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("with_dir"); ap.add_argument("without_dir")
ap.add_argument("--json", default="")
a = ap.parse_args()


def load(d):
    info = {"pads": [], "villages": []}
    for l in open(os.path.join(d, "info.txt"), encoding="utf-8"):
        p = l.strip().split("|")
        if p[0] == "grid": info.update(n=int(p[1]), x0=float(p[2]), y0=float(p[3]), step=float(p[4]))
        if p[0] == "village": info["villages"].append({"id": int(p[1]), "name": p[2], "x": float(p[3]), "y": float(p[4]), "houses": int(p[5])})
        if p[0] == "pad": info["pads"].append({"village": int(p[1]), "kind": int(p[2]), "x": float(p[3]), "y": float(p[4]), "yaw": float(p[5]), "hx": float(p[6]), "hy": float(p[7]), "h": float(p[8])})
    n = info["n"]
    h = np.fromfile(os.path.join(d, "h.bin"), np.float32).reshape(n, n)
    wet = np.fromfile(os.path.join(d, "water.bin"), np.float32).reshape(n, n) > -1e8
    hd = np.fromfile(os.path.join(d, "hdiff.bin"), np.float32).reshape(n, n) if os.path.exists(os.path.join(d, "hdiff.bin")) else None
    return info, h, wet, hd


def steps(h, wet, lo=1.5, ratio=4.0):
    out = set()
    for ax in (0, 1):
        hh = h if ax == 0 else h.T; ww = wet if ax == 0 else wet.T
        d = np.abs(np.diff(hh, axis=0)); dry = ~(ww[:-1] | ww[1:])
        before = np.zeros_like(d); before[1:] = d[:-1]; after = np.zeros_like(d); after[:-1] = d[1:]
        m = dry & (d > lo) & (d > ratio * np.maximum(before, after)); m[0] = m[-1] = False
        for i, j in zip(*np.nonzero(m)): out.add((i, j, ax, float(d[i, j])))
    return out


Ia, Ha, Wa, Da = load(a.with_dir)
Ib, Hb, Wb, _ = load(a.without_dir)
n, x0, y0, st = Ia["n"], Ia["x0"], Ia["y0"], Ia["step"]
mid = (x0 + (n - 1) * st / 2, y0 + (n - 1) * st / 2)
vil = min(Ia["villages"], key=lambda v: math.hypot(v["x"] - mid[0], v["y"] - mid[1])) if Ia["villages"] else None
res = {"grid": [n, x0, y0, st], "village": vil, "ok": False}
if not vil:
    print("no village in the window"); res["error"] = "no village"
else:
    pads = [p for p in Ia["pads"] if p["village"] == vil["id"]]
    X = x0 + np.arange(n)[:, None] * st; Y = y0 + np.arange(n)[None, :] * st

    def sdf(p):
        c, s = math.cos(math.radians(p["yaw"])), math.sin(math.radians(p["yaw"]))
        lx = (X - p["x"]) * c + (Y - p["y"]) * s; ly = -(X - p["x"]) * s + (Y - p["y"]) * c
        return np.maximum(np.abs(lx) - p["hx"], np.abs(ly) - p["hy"])
    E = np.min(np.stack([sdf(p) for p in pads]), axis=0)
    # (a wall's band: within 2.5 m outside a house pad's long side (the walls stand there; the door sides and the square ramp))
    def wall_zone(p):
        c, s = math.cos(math.radians(p["yaw"])), math.sin(math.radians(p["yaw"]))
        lx = (X - p["x"]) * c + (Y - p["y"]) * s; ly = -(X - p["x"]) * s + (Y - p["y"]) * c
        ex, ey = np.abs(lx) - p["hx"], np.abs(ly) - p["hy"]
        return (p["kind"] == 1) & (ey > ex) & (np.maximum(ex, ey) > 0) & (np.maximum(ex, ey) < 2.5)
    WZ = np.any(np.stack([wall_zone(p) for p in pads]), axis=0)
    # (each pad level, 1 m in from its edges; and walked against drawn)
    flat = []
    for p in pads:
        inside = sdf(p) < -1.0
        if inside.sum() == 0: continue
        dev = float(np.abs(Ha[inside] - p["h"]).max())
        flat.append({"kind": p["kind"], "at": [round(p["x"], 1), round(p["y"], 1)], "h": p["h"], "samples": int(inside.sum()), "max_off_m": round(dev, 3),
                     "land_range_m": round(float(Hb[inside].max() - Hb[inside].min()), 2), "walked_vs_drawn_m": round(float(np.abs(Da[inside]).max()), 3) if Da is not None else None})
    # (the steps the terraces add, against the pads' edges)
    sa = steps(Ha, Wa); sb = {(i, j, ax) for i, j, ax, _ in steps(Hb, Wb)}
    new = [s for s in sa if (s[0], s[1], s[2]) not in sb]
    on_edge, off_edge = [], []
    for i, j, ax, dv in new:
        i2, j2 = (i + 1, j) if ax == 0 else (j, i + 1)
        i1, j1 = (i, j) if ax == 0 else (j, i)
        e = min(abs(E[i1, j1]), abs(E[i2, j2]))
        (on_edge if e <= 2.5 else off_edge).append({"x": round(float(X[i1, 0]), 1), "y": round(float(Y[0, j1]), 1), "step_m": round(dv, 2), "edge_m": round(float(e), 2)})
    # (on foot: every sample she can walk to from the square's middle (a step to a neighbour climbing at most 0.75 of its length, not
    # water, not a wall's band); each house's front door (its +X edge's middle, 1 m in) and the land beyond 90 m among them)
    from collections import deque
    ok_cell = ~Wa & ~WZ
    seen = np.zeros_like(ok_cell); sq = [p for p in pads if p["kind"] == 0][0]
    si, sj = int(round((sq["x"] - x0) / st)), int(round((sq["y"] - y0) / st))
    dq = deque([(si, sj)]); seen[si, sj] = True; lim = 0.75 * st
    while dq:
        i0, j0 = dq.popleft()
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            i1, j1 = i0 + di, j0 + dj
            if 0 <= i1 < n and 0 <= j1 < n and not seen[i1, j1] and ok_cell[i1, j1] and abs(Ha[i1, j1] - Ha[i0, j0]) <= lim:
                seen[i1, j1] = True; dq.append((i1, j1))
    doors = []
    for p in pads:
        if p["kind"] != 1: continue
        c, s = math.cos(math.radians(p["yaw"])), math.sin(math.radians(p["yaw"]))
        dx, dy = p["x"] + c * (p["hx"] - 1.0), p["y"] + s * (p["hx"] - 1.0)
        di_, dj_ = int(round((dx - x0) / st)), int(round((dy - y0) / st))
        doors.append(bool(0 <= di_ < n and 0 <= dj_ < n and seen[di_, dj_]))
    beyond = bool((seen & (np.hypot(X - vil["x"], Y - vil["y"]) > 90.0)).any())
    far = np.hypot(X - vil["x"], Y - vil["y"]) > 90.0
    far_diff = float(np.abs(Ha[far] - Hb[far]).max()) if far.any() else 0.0
    res.update(pads=len(pads), houses=vil["houses"], flat=flat, new_steps=len(new), on_edge=len(on_edge), off_edge=off_edge[:20], off_edge_n=len(off_edge),
               largest_edge_step_m=max([s["step_m"] for s in on_edge], default=0.0), far_diff_m=round(far_diff, 4),
               land_range_under_pads_m=max([f["land_range_m"] for f in flat], default=0.0))
    res.update(doors_reached=sum(doors), doors=len(doors), out_of_the_village=beyond, walkable_samples=int(seen.sum()))
    res["ok"] = bool(flat) and all(f["max_off_m"] <= 0.05 and (f["walked_vs_drawn_m"] is None or f["walked_vs_drawn_m"] <= 0.05) for f in flat) and not off_edge and far_diff <= 0.01 and all(doors) and beyond
    print(f"{vil['name']} ({vil['x']:.0f}, {vil['y']:.0f}): {vil['houses']} houses, {len(pads)} pads; the land under a pad spans up to {res['land_range_under_pads_m']} m; "
          f"pads level within {max(f['max_off_m'] for f in flat):.3f} m (walked vs drawn {max((f['walked_vs_drawn_m'] or 0) for f in flat):.3f}); "
          f"steps added {len(new)}: {len(on_edge)} on pads' edges (largest {res['largest_edge_step_m']} m), {len(off_edge)} elsewhere; "
          f"front doors reached on foot from the square {sum(doors)} of {len(doors)}, the land beyond 90 m {'reached' if beyond else 'NOT reached'}; beyond 90 m the ground differs by {far_diff:.4f} m -> {'ok' if res['ok'] else 'FAILED'}")
if a.json:
    with open(a.json, "w") as f: json.dump(res, f, indent=1)
sys.exit(0 if res["ok"] else 1)
