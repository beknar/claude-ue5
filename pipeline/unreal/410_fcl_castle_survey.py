"""fantasy_castle_level: survey the castle buildings that get interiors (closed single-shell meshes from the Fantasy Castle pack).
Per building: the side whose outside ground is walkable and level with the building's base (door goes there, centred on that
wall), the outer wall point + outward normal (local), the floor height (local z of that ground), and the room box inside.
Writes SourceArt/fantasy_castle/castle_rooms.json (read by blender_numpy/fcl_castle_open.py and 411/412).
Args: none (buildings listed in PICK: label of the actor or (mesh, approx world xy))."""
import json, math, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert "fantasy_castle_level." in w.get_path_name(), w.get_path_name()
# purpose per building, by mesh + approximate world position (the castle's east terrace, next to the player start)
PICK = [("SM_House6", (5925, 120081), "barracks"), ("SM_House3", (4479, 120072), "armory"),
        ("SM_Build2", (5531, 117813), "great_hall"), ("SM_House4", (931, 120068), "chapel")]
acts = [a for a in eas.get_all_level_actors() if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh]
def ground(p, ignore):
    h = unreal.SystemLibrary.line_trace_single(w, V(p.x, p.y, p.z + 600), V(p.x, p.y, p.z - 1500), unreal.TraceTypeQuery.ECC_VISIBILITY, True, ignore, unreal.DrawDebugTrace.NONE, True)
    t = h.to_tuple() if h else None
    return (t[4].z, t[9]) if t and (t[0] or t[1]) else (None, None)
out = {}
for mesh, xy, purpose in PICK:
    a = min((x for x in acts if x.static_mesh_component.static_mesh.get_name() in (mesh, mesh + "_open")), key=lambda x: math.hypot(x.get_actor_location().x - xy[0], x.get_actor_location().y - xy[1]))
    tr = a.get_actor_transform(); inv = tr.inverse_transform_location; sc = a.get_actor_scale3d()
    b = a.static_mesh_component.static_mesh.get_bounding_box(); lo, hi = b.min, b.max
    comp = a.static_mesh_component
    best = None
    for side, (ax, sgn) in {"+x": ("x", 1), "-x": ("x", -1), "+y": ("y", 1), "-y": ("y", -1)}.items():
        # outer wall point: trace from 8 m outside toward the centre, 1.5 m above the lowest point, against this building only
        cx, cy = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2
        for zoff in (150.0, 250.0, 350.0):
            zl = lo.z + zoff
            s_l = V(cx + sgn * ((hi.x - lo.x) / 2 + 800), cy, zl) if ax == "x" else V(cx, cy + sgn * ((hi.y - lo.y) / 2 + 800), zl)
            r = comp.line_trace_component(tr.transform_location(s_l), tr.transform_location(V(cx, cy, zl)), True, False, False)
            if r: break
        if not r: continue
        face = inv(r[0]); n_l = V(sgn, 0, 0) if ax == "x" else V(0, sgn, 0)
        outside = tr.transform_location(face + n_l * 220)
        gz, gact = ground(outside, [a])
        if gz is None: continue
        g_l = inv(V(outside.x, outside.y, gz)).z
        okflat = all(ground(tr.transform_location(face + n_l * d + V(0, o, 0) if ax == "x" else face + n_l * d + V(o, 0, 0)), [a])[0] is not None for d in (150, 350) for o in (-120, 120))
        dist = math.hypot(outside.x - 6250, outside.y - 118450)
        score = dist + (0 if okflat else 5000) + abs(g_l - lo.z) * 3
        if best is None or score < best[0]:
            best = (score, side, face, n_l, g_l, gact.get_actor_label() if gact else None, round(gz))
    assert best, mesh + ": no door side"
    _, side, face, n_l, g_l, gname, gz = best
    # room inside: from the centre at floor + 150, against this building's collision (double-sided trace), inset 30 cm
    cx, cy = (lo.x + hi.x) / 2, (lo.y + hi.y) / 2; zc = g_l + 150
    ext = {}
    for k, d in {"+x": V(1, 0, 0), "-x": V(-1, 0, 0), "+y": V(0, 1, 0), "-y": V(0, -1, 0), "+z": V(0, 0, 1)}.items():
        far = V(cx, cy, zc) + d * 6000
        r = comp.line_trace_component(tr.transform_location(V(cx, cy, zc)), tr.transform_location(far), True, False, False)
        ext[k] = (inv(r[0]) - V(cx, cy, zc)).length() if r else None
    half = lambda k, fb: (ext[k] - 30) if ext[k] else fb
    room = {"x0": cx - half("-x", (hi.x - lo.x) / 2 - 80), "x1": cx + half("+x", (hi.x - lo.x) / 2 - 80),
            "y0": cy - half("-y", (hi.y - lo.y) / 2 - 80), "y1": cy + half("+y", (hi.y - lo.y) / 2 - 80),
            "h": min(600.0, (ext["+z"] + 150 - 40) if ext["+z"] else 450.0)}
    out[a.get_actor_label()] = {"mesh": a.static_mesh_component.static_mesh.get_name().replace("_open", ""), "purpose": purpose, "side": side,
                                "door": [round(face.x, 1), round(face.y, 1)], "normal": [n_l.x, n_l.y], "floor": round(g_l, 1), "w": 160.0, "h": 260.0,
                                "ground_world_z": gz, "ground_actor": gname, "scale": [sc.x, sc.y, sc.z], "room": {k: round(v, 1) for k, v in room.items()},
                                "inside_hits": {k: (round(v) if v else None) for k, v in ext.items()}}
    print(a.get_actor_label(), mesh, purpose, "door", side, out[a.get_actor_label()]["door"], "floor", round(g_l), "ground", gz, gname, "room", out[a.get_actor_label()]["room"], "inside", out[a.get_actor_label()]["inside_hits"])
json.dump(out, open(r"E:\code\claude-ue5\claude_ue5\SourceArt\fantasy_castle\castle_rooms.json", "w"), indent=1)
