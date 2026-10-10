"""Find the door leaves inside the merged Medieval Fantasy Village house meshes (exported FBX, cm). A door leaf = run of
5 vertical planks (28 x 9 x 233 cm, either orientation) + the hinges / straps / handle in front of it.
Blender: -b -P mfv_doors.py -- fbx_dir out.json SM_house_01 ..."""
import bpy, bmesh, sys, os, json
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
src, out_json, names = argv[0], argv[1], argv[2:]
def parts_of(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH'); M = ob.matrix_world
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    seen = set(); parts = []
    for f in bm.faces:
        if f.index in seen: continue
        st = [f]; comp = []; seen.add(f.index)
        while st:
            g = st.pop(); comp.append(g.index)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen: seen.add(h.index); st.append(h)
        P = [M @ v.co * 100 for v in {v for i in comp for v in bm.faces[i].verts}]
        a = Vector((min(p.x for p in P), min(p.y for p in P), min(p.z for p in P))); b = Vector((max(p.x for p in P), max(p.y for p in P), max(p.z for p in P)))
        parts.append({"faces": comp, "min": a, "max": b})
    return parts
def is_plank(p):
    e = p["max"] - p["min"]
    return 220 < e.z < 245 and sorted((round(e.x), round(e.y))) [0] in range(6, 13) and sorted((round(e.x), round(e.y)))[1] in range(24, 33)
res = {}
for name in names:
    parts = parts_of(os.path.join(src, name + ".fbx"))
    planks = [p for p in parts if is_plank(p)]
    # group planks into doors: same orientation, aligned, adjacent
    doors = []
    for p in sorted(planks, key=lambda p: (p["min"].z, p["min"].x, p["min"].y)):
        along_x = (p["max"].x - p["min"].x) > (p["max"].y - p["min"].y)
        for d in doors:
            if d["along_x"] == along_x and abs(d["min"].z - p["min"].z) < 5:
                if along_x and abs(d["min"].y - p["min"].y) < 5 and (p["min"].x - d["max"].x) < 6 and (d["min"].x - p["max"].x) < 6:
                    d["planks"].append(p); d["min"] = Vector(map(min, d["min"], p["min"])); d["max"] = Vector(map(max, d["max"], p["max"])); break
                if not along_x and abs(d["min"].x - p["min"].x) < 5 and (p["min"].y - d["max"].y) < 6 and (d["min"].y - p["max"].y) < 6:
                    d["planks"].append(p); d["min"] = Vector(map(min, d["min"], p["min"])); d["max"] = Vector(map(max, d["max"], p["max"])); break
        else:
            doors.append({"along_x": along_x, "planks": [p], "min": p["min"].copy(), "max": p["max"].copy()})
    doors = [d for d in doors if len(d["planks"]) >= 4]
    out = []
    for d in doors:
        lo, hi = d["min"].copy(), d["max"].copy()
        # hardware sits proud of the planks on one side: grow the thin axis by 14 cm both ways, the long axis by 3
        if d["along_x"]: lo.x -= 3; hi.x += 3; lo.y -= 14; hi.y += 14
        else: lo.y -= 3; hi.y += 3; lo.x -= 14; hi.x += 14
        lo.z -= 2; hi.z += 3
        inside = [i for i, p in enumerate(parts) if all(lo[k] <= p["min"][k] and p["max"][k] <= hi[k] for k in range(3))]
        hw = [i for i in inside if not is_plank(parts[i])]
        out.append({"along_x": d["along_x"], "planks_min": list(d["min"]), "planks_max": list(d["max"]), "region_min": list(lo), "region_max": list(hi),
                    "parts": inside, "n_planks": len(d["planks"]), "n_hardware": len(hw),
                    "hardware_boxes": [[list(parts[i]["min"]), list(parts[i]["max"])] for i in hw]})
        print(f"{name}: door along_{'x' if d['along_x'] else 'y'} planks {len(d['planks'])} hw {len(hw)} planks box {tuple(round(v) for v in d['min'])}..{tuple(round(v) for v in d['max'])}")
    res[name] = out
    print(f"{name}: {len(out)} door(s), {len(planks)} plank parts total")
json.dump(res, open(out_json, "w"), indent=1)
