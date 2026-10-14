"""Shared check for the walk and combat tests of the dungeon and the village: is every container's moving part where it
belongs? A section builds a container in play as a base pivot (the piece frame: front +X, floor z 0) with the body mesh
on it and one pivot per moving part at its hinge. Counting open / closed states (the tests' `containers_opened`) says
nothing about where the lid is: for a long time every lid lay on the floor inside its body and every wardrobe door
stood in the middle of the wardrobe, and the tests passed.

    import container_check as CC
    rows = CC.measure(section)          # one row per container of that section, measured as it stands now
    bad = CC.faults(rows)               # what is wrong with them, as text; an empty list: all fine
    fit = CC.check_all(sections)        # both, over several sections: {"containers", "closed", "open", "by_body", "faults"}
    idx = CC.sample(section, rows, 4)   # container indices of up to 4 containers of each body mesh (for ToggleContainer)

A row: kind ("lid" or "doors"), the body and moving meshes, where it is, how far open, and the boxes of the body and of
each moving part in the base frame. Closed, a lid must lie on the body's top inside its footprint, and a wardrobe's
doors must stand on its front and cover it between them. Open, a lid must stand up over the back and a door out in
front. Rows that are neither closed nor fully open are not judged."""
import math, unreal

ML = unreal.MathLibrary


def _box(comp, base_tf):
    b = comp.static_mesh.get_bounding_box(); tf = comp.get_world_transform()
    pts = [ML.inverse_transform_location(base_tf, ML.transform_location(tf, unreal.Vector(x, y, z)))
           for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]
    return ([min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)], [max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)])


def measure(section):
    """the containers of a section (play only: the editor's sections have none)"""
    rows = []; root = section.root_component
    for base in root.get_children_components(False):
        if base.get_class().get_name() != "SceneComponent": continue
        kids = base.get_children_components(False)
        body = [k for k in kids if k.get_class().get_name() == "StaticMeshComponent" and k.static_mesh]
        pivots = [k for k in kids if k.get_class().get_name() == "SceneComponent"]
        moving = []
        for pv in pivots:
            moving += [(pv, m) for m in pv.get_children_components(False) if m.get_class().get_name() == "StaticMeshComponent" and m.static_mesh]
        if len(body) != 1 or not moving: continue                      # (a door leaf's pivot has no body beside it)
        tf = base.get_world_transform(); loc = tf.translation
        row = {"at": [round(loc.x), round(loc.y), round(loc.z)], "body": body[0].static_mesh.get_name(), "box": _box(body[0], tf), "parts": []}
        for pv, m in moving:
            q = pv.get_relative_transform().rotation                    # (a pivot is never turned when closed)
            row["parts"].append({"mesh": m.static_mesh.get_name(), "box": _box(m, tf), "turned": round(math.degrees(2.0 * math.acos(min(1.0, abs(q.w)))), 1)})
        row["kind"] = "doors" if len(moving) > 1 else "lid"
        rows.append(row)
    return rows


def _overlap(a0, a1, b0, b1): return max(0.0, min(a1, b1) - max(a0, b0))


def faults(rows):
    out = []
    for r in rows:
        (bn, bx) = r["box"]; name = "%s at (%d, %d)" % (r["body"], r["at"][0], r["at"][1])
        turned = [p["turned"] for p in r["parts"]]
        closed = all(t < 0.5 for t in turned); opened = all(t > 89.0 for t in turned)
        if r["kind"] == "lid":
            (mn, mx) = r["parts"][0]["box"]; depth = bx[0] - bn[0]
            if closed:
                if not (bx[2] - 8.0 <= mn[2] <= bx[2] + 3.0): out.append("%s: the closed lid's underside is at z %.0f, the body's top at %.0f" % (name, mn[2], bx[2]))
                area = (mx[0] - mn[0]) * (mx[1] - mn[1])
                inside = _overlap(mn[0], mx[0], bn[0] - 3, bx[0] + 3) * _overlap(mn[1], mx[1], bn[1] - 3, bx[1] + 3)
                if area <= 0 or inside / area < 0.9: out.append("%s: only %.0f%% of the closed lid is over the body" % (name, 100.0 * inside / max(area, 1e-6)))
            elif opened:
                if (mn[2] + mx[2]) / 2 < bx[2] + 0.25 * depth: out.append("%s: the open lid's middle is at z %.0f, the body's top at %.0f" % (name, (mn[2] + mx[2]) / 2, bx[2]))
                if (mn[0] + mx[0]) / 2 > (bn[0] + bx[0]) / 2: out.append("%s: the open lid stands over the front half (x %.0f)" % (name, (mn[0] + mx[0]) / 2))
        else:
            cover = 0.0
            for p in r["parts"]:
                (mn, mx) = p["box"]
                if closed:
                    if mn[0] < bx[0] - 6.0 or mx[0] > bx[0] + 12.0: out.append("%s: closed door %s spans x %.0f..%.0f, the body's front is at %.0f" % (name, p["mesh"], mn[0], mx[0], bx[0]))
                    if mn[2] < bn[2] - 2 or mx[2] > bx[2] + 2: out.append("%s: closed door %s spans z %.0f..%.0f, the body %.0f..%.0f" % (name, p["mesh"], mn[2], mx[2], bn[2], bx[2]))
                    cover += _overlap(mn[1], mx[1], bn[1], bx[1])
                elif opened:
                    if (mn[0] + mx[0]) / 2 < bx[0] + 10.0: out.append("%s: open door %s has its middle at x %.0f, the body's front is at %.0f" % (name, p["mesh"], (mn[0] + mx[0]) / 2, bx[0]))
            if closed and cover < 0.85 * (bx[1] - bn[1]): out.append("%s: the closed doors cover %.0f of the front's %.0f cm" % (name, cover, bx[1] - bn[1]))
    return out


def sample(section, rows, per_body=4):
    """container indices (for ToggleContainer; one per container: a wardrobe's doors go together) of up to per_body
    containers of each body mesh among rows"""
    want = {}; n = {}
    for r in rows:
        if n.get(r["body"], 0) < per_body: n[r["body"]] = n.get(r["body"], 0) + 1; want[(r["at"][0], r["at"][1])] = None
    for i in range(section.get_num_containers()):
        q = section.get_container_location(i); k = (round(q.x), round(q.y))
        if k in want and want[k] is None: want[k] = i
    return [i for i in want.values() if i is not None]


def check_all(sections):
    rows = []
    for s in sections:
        if s is not None: rows += measure(s)
    by = summary(rows)
    return {"containers": len(rows), "closed": sum(e["closed"] for e in by.values()), "open": sum(e["open"] for e in by.values()), "by_body": by, "faults": faults(rows)}


def summary(rows):
    """how many of each body mesh, and how many closed / open"""
    by = {}
    for r in rows:
        t = [p["turned"] for p in r["parts"]]
        e = by.setdefault(r["body"], {"n": 0, "closed": 0, "open": 0})
        e["n"] += 1; e["closed"] += all(x < 0.5 for x in t); e["open"] += all(x > 89.0 for x in t)
    return by
