"""Shared check for the dungeon tests: the broken walls (Wall_Rough*) have holes right through them. Through them she saw
the void behind and the backs of the rooms beyond, and she could climb into the bigger ones and fall out of the dungeon.
Each broken segment has a backing (a stone plate inside the wall's thickness, 15.5 to 23.5 cm behind the wall line) and a
seal (an invisible box over the wall's face, to 30 cm in front of the line; 770's Wall_Rough_Back / Wall_Rough_Seal), and
the generator puts her back where she last stood if she drops below the floor (FallResetDepth).

    import wall_check as WC
    r = WC.rays(world, sections, ignore)     # what is seen of every broken segment of those sections, from its room
    r = yield from WC.walk_in(world, pawn, r["spots"], wait, now)    # she pushes into holes and jumps: does she get in?
    r = yield from WC.fall(gen, pawn, wait)  # she is dropped below the floor: is she put back where she stood?

rays: from 1.5 m in front of each segment, straight at it, on a grid over its face (the seals switched off for the
measurement: they are invisible, and what is measured is what is seen). Each ray ends on the wall's face (or a crater
in it, or furniture in front of it: "face"), on the backing seen through a hole ("hole"), or beyond the wall's
thickness ("leak": what she saw before). In play only (the editor's sections are not traced the same way)."""
import math, unreal

ML = unreal.MathLibrary; V = unreal.Vector
FACE_X = 10.0         # (cm in front of the wall line: the wall's face is at 33, a crater may go a little deeper)
BACK_X = -25.0        # (behind the backing's back: anything farther is beyond the wall)


def _seals(section, on, backing=False):
    """the hidden blockers' components (the seals and the cell blockers share the engine's cube); with backing, the
    stone plates' too (SM_Wall_A: shared with the intact walls, so a measurement without them leaves those out)"""
    n = 0
    for c in section.get_components_by_class(unreal.InstancedStaticMeshComponent):
        m = c.static_mesh.get_name() if c.static_mesh is not None else ""
        if (m == "Cube" and not c.is_visible()) or (backing and m == "SM_Wall_A"):
            c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS if on else unreal.CollisionEnabled.NO_COLLISION); n += 1
    return n


def rays(world, sections, ignore=(), without_backing=False, ys=(-135, -100, -65, -30, 0, 30, 65, 100, 135), zs=(15, 50, 85, 120, 155, 190, 225, 260, 295), top=590.0):
    """without_backing: the plates left out too (what she saw before them; the intact variant's segments are skipped)"""
    out = {"sections": 0, "segments": 0, "by_piece": {}, "rays": 0, "face": 0, "hole": 0, "leak": 0, "leaks": [], "spots": []}
    for sec in sections:
        tfs, names = sec.get_backed_wall_segments()
        if not tfs: continue
        out["sections"] += 1; _seals(sec, False, without_backing)
        try:
            floor = sec.get_actor_location().z
            for tf, nm in zip(tfs, names):
                nm = str(nm)
                if without_backing and nm == "Wall_Rough_5": continue      # (770's intact variant, SM_Wall_A itself: switched off with the plates)
                out["segments"] += 1; out["by_piece"][nm] = out["by_piece"].get(nm, 0) + 1
                for y in ys:
                    for z in zs:
                        a = ML.transform_location(tf, V(150.0, y, z)); b = ML.transform_location(tf, V(-150.0, y, z))
                        if a.z - floor > top: continue
                        out["rays"] += 1
                        h = unreal.SystemLibrary.line_trace_single(world, a, b, unreal.TraceTypeQuery.ECC_VISIBILITY, True, list(ignore), unreal.DrawDebugTrace.NONE, True)
                        h = h.to_tuple() if h is not None else (False,)           # (None: nothing hit)
                        lx = ML.inverse_transform_location(tf, h[4]).x if h[0] else -999.0
                        if lx >= FACE_X: out["face"] += 1
                        elif lx >= BACK_X:
                            out["hole"] += 1
                            # (a hole she could walk or jump into: low on the wall)
                            if 30.0 <= a.z - floor <= 190.0: out["spots"].append((tf, y, a.z - floor, nm))
                        else:
                            out["leak"] += 1
                            if len(out["leaks"]) < 12: out["leaks"].append({"piece": nm, "at": [round(a.x), round(a.y), round(a.z)], "local_y": y, "local_z": z, "hit_x": round(lx)})
        finally:
            _seals(sec, True, without_backing)
    return out


def walk_in(world, pawn, spots, wait, now, n=8):
    """she stands 1.2 m in front of a hole low on the wall, pushes toward it and jumps: how close to the wall line does she
    get? (the seal's face is 30 cm in front of it, her capsule's radius more)"""
    used = set(); res = []
    # (each broken piece in turn, its holes from the lowest up: a try for every kind of hole, low and jump high)
    by = {}
    for s in sorted(spots, key=lambda s: s[2]): by.setdefault(s[3], []).append(s)
    def zig(v):
        out_, i, j = [], 0, len(v) - 1
        while i <= j:
            out_.append(v[i])
            if i != j: out_.append(v[j])
            i += 1; j -= 1
        return out_
    lists = [zig(v) for v in by.values()]; order = []
    for k in range(max((len(v) for v in lists), default=0)):
        order += [v[k] for v in lists if k < len(v)]
    for tf, y, zh, nm in order:
        key = (round(tf.translation.x), round(tf.translation.y), round(tf.translation.z))      # (one try a segment)
        if key in used: continue
        used.add(key)
        stand = ML.transform_location(tf, V(120.0, y, 0.0)); stand = V(stand.x, stand.y, tf.translation.z + 100.0)
        pawn.set_actor_location(stand, False, True); yield from wait(0.4)
        if (pawn.get_actor_location() - stand).length() > 30.0: continue          # (something stands there)
        into = ML.transform_direction(tf, V(-1.0, 0.0, 0.0)); t0 = now(); closest = 999.0; jumped = False
        while now() - t0 < 1.8:
            pawn.add_movement_input(into, 1.0, True)
            if not jumped and now() - t0 > 0.35: pawn.jump(); jumped = True
            closest = min(closest, ML.inverse_transform_location(tf, pawn.get_actor_location()).x)
            yield
        pawn.stop_jumping()
        r_ = pawn.capsule_component.get_scaled_capsule_radius()
        res.append({"piece": nm, "hole_height_cm": round(zh), "closest_to_wall_line_cm": round(closest, 1), "capsule_radius": round(r_), "kept_out": closest >= 30.0 + r_ - 6.0})
        if len(res) >= n: break
    return {"tries": res, "ok": len(res) > 0 and all(t["kept_out"] for t in res)}


def cells(world, sections, ignore=(), zs=(200.0, 280.0), dirs=24):
    """the prison cells (the section's GetPrisonCells): from each cell's middle, a 15 cm ball sent in every direction above
    the hay pile must meet bars (their invisible blockers), a cell door or a wall before it leaves the cell's 3 x 3 m tile; a
    capsule dropped on each hay pile (the queries her movement makes) must land on it"""
    out = {"cells": 0, "cell_sides_with_bars": 0, "doors_open": 0, "rays": 0, "leak": 0, "leaks": [], "hay": 0, "hay_blocks": 0, "hay_tops_cm": []}
    for sec in sections:
        frames, hay = sec.get_prison_cells()
        out["cells"] += len(frames); out["cell_sides_with_bars"] += sec.get_prison_cell_sides()
        doors = [d for d in range(sec.get_num_doors()) if sec.is_door_cell(d)]
        for tf, h in zip(frames, hay):
            # (a cell whose door someone opened (a walk test presses F at closed doors) is open: its rays are not counted)
            own = [d for d in doors if abs(ML.inverse_transform_location(tf, sec.get_door_location(d)).x - 150.0) < 40.0
                   and abs(ML.inverse_transform_location(tf, sec.get_door_location(d)).y) < 150.0]
            door_open = any(sec.get_door_open_alpha(d) > 0.01 for d in own)
            out["doors_open"] += int(door_open)
            for z in (() if door_open else zs):
                for k in range(dirs):
                    a = k * 2.0 * math.pi / dirs; c, s = math.cos(a), math.sin(a)
                    lim = 150.0 / max(abs(c), abs(s)) + 30.0
                    o = ML.transform_location(tf, V(0.0, 0.0, z)); e = ML.transform_location(tf, V(c * (lim + 120.0), s * (lim + 120.0), z))
                    out["rays"] += 1
                    # (a 15 cm ball, not a line: a gap narrower than 30 cm is no way out, and a line exactly on a blocker's
                    # middle at 90 degrees missed it where lines 2 cm either side hit its face)
                    r = unreal.SystemLibrary.sphere_trace_single(world, o, e, 15.0, unreal.TraceTypeQuery.ECC_VISIBILITY, True, list(ignore), unreal.DrawDebugTrace.NONE, True)
                    r = r.to_tuple() if r is not None else (False,)
                    d = (r[4] - o).length() if r[0] else 9999.0
                    if d > lim:
                        out["leak"] += 1
                        if len(out["leaks"]) < 10: out["leaks"].append({"cell_at": [round(tf.translation.x), round(tf.translation.y)], "dir_deg": round(math.degrees(a)), "z": z, "hit_cm": round(d), "limit_cm": round(lim)})
            out["hay"] += 1
            r = unreal.SystemLibrary.capsule_trace_single(world, V(h.x, h.y, h.z + 400.0), V(h.x, h.y, h.z - 20.0), 30.0, 60.0, unreal.TraceTypeQuery.ECC_VISIBILITY, False, list(ignore), unreal.DrawDebugTrace.NONE, True)
            r = r.to_tuple() if r is not None else (False,)
            comp = r[10] if r[0] else None
            if comp is not None and comp.static_mesh is not None and comp.static_mesh.get_name() == "SM_Kit_HayPile":
                out["hay_blocks"] += 1; out["hay_tops_cm"].append(round(r[4].z - 60.0 - h.z))     # (the capsule's foot on the pile)
    out["ok"] = out["cells"] > 0 and out["leak"] == 0 and out["hay_blocks"] == out["hay"]
    t = out["hay_tops_cm"]; out["hay_tops_cm"] = [min(t), round(sum(t) / len(t)), max(t)] if t else []
    return out


def fall(gen, pawn, wait):
    """she stands, then is dropped 15 m below the floor: the generator must put her back where she stood"""
    yield from wait(0.6)
    here = pawn.get_actor_location(); n0 = gen.get_editor_property("fall_resets")
    pawn.set_actor_location(V(here.x, here.y, gen.get_actor_location().z - 1500.0), False, True); yield from wait(0.5)
    back = pawn.get_actor_location(); n1 = gen.get_editor_property("fall_resets")
    d = (back - here).length()
    return {"resets": n1 - n0, "put_back_cm_from_where_she_stood": round(d, 1), "ok": n1 - n0 == 1 and d < 60.0}
