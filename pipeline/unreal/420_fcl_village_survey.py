"""fantasy_castle_level: survey the Lake Village's modular houses (fcl_lake_village sub-level). The houses are assembled from
SM_M_Wall*/Door*/Window*/Roof* pieces, so they are hollow; a house = one SM_M_Door* with the room found by tracing out from a
point 2 m inside the door. Records the door (world), inward direction, floor height (ground just inside), room box (world,
axis-aligned to the door's facing) and ceiling. Writes SourceArt/fantasy_castle/village_rooms.json."""
import json, math, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert "fantasy_castle_level." in w.get_path_name(), w.get_path_name()
def trace(a, b, ignore=()):
    r = unreal.SystemLibrary.line_trace_single(w, a, b, unreal.TraceTypeQuery.ECC_VISIBILITY, True, list(ignore), unreal.DrawDebugTrace.NONE, True)
    t = r.to_tuple() if r else None
    return (t[4], t[9]) if t and (t[0] or t[1]) else (None, None)
doors = [a for a in eas.get_all_level_actors() if "fcl_lake_village" in a.get_level().get_path_name() and isinstance(a, unreal.StaticMeshActor)
         and a.static_mesh_component.static_mesh and a.static_mesh_component.static_mesh.get_name().startswith("SM_M_Door")]
rooms = []
for d in doors:
    o, e = d.get_actor_bounds(False); yaw = d.get_actor_rotation().yaw
    fwd = unreal.MathLibrary.get_right_vector(d.get_actor_rotation())          # door leaves are thin in local Y: the wall normal
    best = None
    for sgn in (1, -1):                                                        # which side is inside: the one with a roof above
        p = V(o.x, o.y, o.z) + fwd * (sgn * 200)
        up, ua = trace(V(p.x, p.y, o.z - o.z + d.get_actor_location().z + 100), V(p.x, p.y, d.get_actor_location().z + 1500), [d])
        if up is not None:
            fl, fa = trace(V(p.x, p.y, d.get_actor_location().z + 150), V(p.x, p.y, d.get_actor_location().z - 300), [d])
            if fl is not None and (best is None or up.z < best[1]): best = (sgn, up.z, fl.z, p)
    if best is None: continue
    sgn, ceil, floor, p = best; inward = fwd * sgn; side = V(-inward.y, inward.x, 0)
    zc = floor + 120; c0 = V(p.x, p.y, zc)
    reach = {}
    for k, dv in {"in": inward, "out": inward * -1, "l": side, "r": side * -1}.items():
        h, ha = trace(c0, c0 + dv * 2500, [d])
        reach[k] = (h - c0).length() if h else 2500.0
    # room box in the door frame: u along inward (from the door plane), v along side
    u0 = 200 - reach["out"]; u1 = 200 + reach["in"]; v0 = -reach["r"]; v1 = reach["l"]
    rooms.append({"door": d.get_actor_label(), "door_mesh": d.static_mesh_component.static_mesh.get_name(),
                  "door_xy": [round(d.get_actor_location().x), round(d.get_actor_location().y)], "door_z": round(d.get_actor_location().z),
                  "inward": [round(inward.x, 3), round(inward.y, 3)], "floor": round(floor, 1), "ceiling": round(ceil, 1),
                  "u": [round(u0), round(u1)], "v": [round(v0), round(v1)]})
# one room per house: merge rooms whose door-inside points are within 3 m (double doors / two doors of one house)
merged = []
for r in rooms:
    pin = (r["door_xy"][0] + r["inward"][0] * 200, r["door_xy"][1] + r["inward"][1] * 200)
    if any(math.hypot(pin[0] - m["_pin"][0], pin[1] - m["_pin"][1]) < 300 for m in merged): continue
    r["_pin"] = pin; merged.append(r)
for r in merged: r.pop("_pin")
json.dump(merged, open(r"E:\code\claude-ue5\claude_ue5\SourceArt\fantasy_castle\village_rooms.json", "w"), indent=1)
for r in merged: print(r["door"], r["door_mesh"], "xy", r["door_xy"], "in", r["inward"], "floor", r["floor"], "ceil", r["ceiling"], "u", r["u"], "v", r["v"])
print(len(doors), "doors ->", len(merged), "rooms")
