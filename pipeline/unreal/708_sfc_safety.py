"""sf-city-level fall safety: invisible barrier walls along every edge she could fall off into the void (or down a deep drop).
1. flood fill from the PlayerStart on a STEP grid with the Pawn collision profile, the way she can move: walk (step <= 45),
   jump up (<= 115: railings, crates), drop down (<= 250); a move is blocked if a horizontal trace at +50 / +140 hits.
   Steep cells (normal z < 0.7) count as reachable too (she could jump onto them and slide). BP_SciFiDoor actors are
   ignored (doors open as she approaches).
   Multi-level: a grid cell keeps one floor per level, so stacked walkways and the ground under them are both explored.
2. every move whose target has no floor within 4 m ('void', or nothing above -30000) or a floor more than 2.5 m down
   ('deep') is a fall edge -> a wall on the cell boundary (20 cm thick, from floor-120 to floor+520), merged into runs per
   3 m height band. Also when the move is blocked by something thinner than a cell with the void behind it (a railing or
   lip she could jump onto and drop off: 'fenced'), unless a barrier already stands there.
   Walls block Pawn only (InvisibleWall profile, visibility / camera ignored), hidden in game. With STEP = 100 the gap
   between a real floor edge and its wall is < 50 cm: narrower than her capsule (72 cm), so nothing can slip through.
3. repeat until a flood finds no unguarded fall edge (max 3 passes).
Writes SourceArt/sf_city/reach.json (final reachable cells, walls). Actors tagged 'sfc_safety'.  Args: [step]"""
import sys, json, math, collections, time, unreal
STEP = float(sys.argv[1]) if len(sys.argv) > 1 else 100.0
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert w.get_path_name().startswith("/Game/SFCityLevel/Maps/sf-city-level."), w.get_path_name()
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_current_level_by_name("sf-city-level")
TAG = unreal.Name("sfc_safety"); SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\sf_city"
for a in eas.get_all_level_actors():
    if TAG in a.tags: eas.destroy_actor(a)
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
X0, X1, Y0, Y1 = -60000.0, 145000.0, -160000.0, 65000.0
start = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.PlayerStart)).get_actor_location()
LT = unreal.SystemLibrary.line_trace_single_by_profile; NONE = unreal.DrawDebugTrace.NONE
def ignore(): return [a for a in eas.get_all_level_actors() if a.get_class().get_name() == "BP_SciFiDoor_C"]
def flood(IGN):
    def hit(a, b):
        r = LT(w, a, b, "Pawn", False, IGN, NONE, True)
        if not r: return None
        t = r.to_tuple(); return (t[4], t[7]) if t[0] else None
    def floor(x, y, ztop, zbot):
        h = hit(V(x, y, ztop), V(x, y, zbot)); return (h[0].z, h[1].z) if h else None
    def guarded(a, b):
        """a barrier wall (this script's or the road's) already stands between a and b. Traced from both ends: the first
        blocking hit may be the railing on one side of the barrier, never on both."""
        for p, q in ((a, b), (b, a)):
            r = LT(w, p, q, "Pawn", False, IGN, NONE, True)
            ac = r.to_tuple()[9] if (r and r.to_tuple()[0]) else None
            if ac and (TAG in ac.tags or (unreal.Name("sfc_road") in ac.tags and ac.get_actor_label().startswith("RoadWall"))): return True
        return False
    X = lambda i: X0 + i * STEP; Y = lambda j: Y0 + j * STEP
    s = (int(round((start.x - X0) / STEP)), int(round((start.y - Y0) / STEP)))
    f0 = floor(X(s[0]), Y(s[1]), start.z + 50, start.z - 400); assert f0, "no floor under the PlayerStart"
    # multi-level: a grid cell keeps one floor per level (floors > 60 cm apart), so stacked walkways and the ground
    # under them are both explored
    Z = {s: [f0[0]]}; q = collections.deque([(s, f0[0])]); edges = []; kinds = collections.Counter()
    seen = lambda n, z: any(abs(v - z) < 60 for v in Z.get(n, ()))
    while q:
        c, z0 = q.popleft(); cx, cy = X(c[0]), Y(c[1])
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c[0] + di, c[1] + dj)
            nx, ny = X(n[0]), Y(n[1])
            if not (X0 <= nx <= X1 and Y0 <= ny <= Y1): kinds["bounds"] += 1; continue
            f = floor(nx, ny, z0 + 125, z0 - 400)
            zt = max(z0, f[0]) if f else z0
            if hit(V(cx, cy, zt + 50), V(nx, ny, zt + 50)) or hit(V(cx, cy, zt + 140), V(nx, ny, zt + 140)):
                kinds["wall"] += 1
                # a railing / lip / parapet thinner than a cell: she can jump onto it and drop off the far side, so a
                # blocked move with void or a deep drop behind it gets a barrier too
                if (f is None or f[0] < z0 - 250) and (c[0], c[1], di, dj, int(z0 // 300)) not in DONE and not guarded(V(cx, cy, z0 + 100), V(nx, ny, z0 + 100)):
                    edges.append((c[0], c[1], di, dj, round(z0, 1), "fenced")); kinds["fenced"] += 1
                continue
            if f is None:
                deep = floor(nx, ny, z0 - 400, -30000)
                edges.append((c[0], c[1], di, dj, round(z0, 1), "void" if deep is None else "deep")); kinds["void" if deep is None else "deep"] += 1; continue
            z1, nz = f
            if z1 < z0 - 250: edges.append((c[0], c[1], di, dj, round(z0, 1), "deep")); kinds["deep"] += 1; continue
            if seen(n, z1): continue
            if hit(V(nx, ny, z1 + 30), V(nx, ny, z1 + 170)): kinds["low"] += 1; continue
            kinds["steep" if nz < 0.7 else "jump" if z1 > z0 + 45 else "drop" if z1 < z0 - 60 else "walk"] += 1
            Z.setdefault(n, []).append(z1); q.append((n, z1))
    return Z, edges, kinds
def wall(cx, cy, z0, z1, length, along_x, k):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, V(cx, cy, (z0 + z1) / 2), unreal.Rotator(roll=0, pitch=0, yaw=0 if along_x else 90))
    a.static_mesh_component.set_static_mesh(CUBE); a.set_actor_scale3d(V(length / 100.0, 0.2, (z1 - z0) / 100.0))
    c = a.static_mesh_component; c.set_collision_profile_name("InvisibleWall")
    for ch in (unreal.CollisionChannel.ECC_VISIBILITY, unreal.CollisionChannel.ECC_CAMERA): c.set_collision_response_to_channel(ch, unreal.CollisionResponseType.ECR_IGNORE)
    c.set_editor_property("hidden_in_game", True); c.set_editor_property("cast_shadow", False); a.set_actor_hidden_in_game(True)
    a.tags = [TAG]; a.set_actor_label(f"FallWall_{k:04d}"); a.set_folder_path("SFC/Safety"); return a
def build(edges, k0):
    """merge boundary edges into straight runs and spawn walls; returns wall records"""
    groups = collections.defaultdict(list)
    for i, j, di, dj, z0, kind in edges:                           # grouped per 3 m height band: stacked levels get their own walls
        DONE.add((i, j, di, dj, int(z0 // 300)))                    # (this boundary now has a barrier: later passes skip it)
        if di: groups[("x", i * 2 + di, int(z0 // 300))].append((j, z0))   # boundary plane x = X0 + (i + di/2) * STEP, runs along y
        else: groups[("y", j * 2 + dj, int(z0 // 300))].append((i, z0))   # plane y = ..., runs along x
    recs = []; k = k0
    for (axis, p2, _band), items in groups.items():
        items = sorted(set(items)); runs = []; cur = [items[0]]
        for it in items[1:]:
            zs = [z for _, z in cur] + [it[1]]
            if it[0] == cur[-1][0] + 1 and max(zs) - min(zs) < 600: cur.append(it)
            else: runs.append(cur); cur = [it]
        runs.append(cur)
        plane = (X0 if axis == "x" else Y0) + p2 * STEP / 2
        for run in runs:
            a0 = (Y0 if axis == "x" else X0) + (run[0][0] - 0.5) * STEP - 12; a1 = (Y0 if axis == "x" else X0) + (run[-1][0] + 0.5) * STEP + 12
            zlo = min(z for _, z in run) - 120; zhi = max(z for _, z in run) + 520; mid = (a0 + a1) / 2
            if axis == "x": wall(plane, mid, zlo, zhi, a1 - a0, False, k)
            else: wall(mid, plane, zlo, zhi, a1 - a0, True, k)
            recs.append({"axis": axis, "plane": plane, "a": [a0, a1], "z": [zlo, zhi], "floor": [zlo + 120, zhi - 520], "n": len(run)}); k += 1
    return recs
walls = []; DONE = set()
for pas in range(4):
    t0 = time.time(); Z, edges, kinds = flood(ignore())
    nc = sum(len(v) for v in Z.values())
    print(f"pass {pas}: reachable {nc} cells on {len(Z)} grid positions ({nc * STEP * STEP / 1e4:.0f} m2), fall edges {len(edges)} | {dict(kinds)} | {time.time() - t0:.0f}s")
    if not edges or pas == 3: break
    recs = build(edges, len(walls)); walls += recs; print(f"  + {len(recs)} walls")
zs = sorted(z for v in Z.values() for z in v)
json.dump({"step": STEP, "x0": X0, "y0": Y0, "cells": [[k[0], k[1], round(z, 1)] for k, v in Z.items() for z in v], "remaining_edges": edges, "walls": walls,
           "zmin": zs[0], "zmax": zs[-1]}, open(SA + r"\reach.json", "w"))
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
print(f"walls {len(walls)} | remaining fall edges {len(edges)} | walkable z {zs[0]:.0f} .. {zs[-1]:.0f}")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
