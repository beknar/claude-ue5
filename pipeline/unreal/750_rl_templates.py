"""random_level building templates: survey each Medieval_Docks building level instance (LI_Building_*_Fix) and write
SourceArt/random_level/templates.json (read by 752, which fills ARTTownGenerator.Templates):
- footprint (XY box of the building's meshes, moss foliage excluded) and the entry floor height (ground-floor door z)
- doors (SM_Door_01/02, pivot = hinge): local transform, which are exterior (one side roofed + enclosed, the other open),
  the main door = an exterior door on the entry floor, its outward direction (the generator turns it toward the street)
- containers: crate lids (SM_Crate_Lid_*) to make openable
- additions (bedrooms): a chest (SM_Kit_ChestBody / Lid) at the foot of every bed, and a wardrobe (SM_Kit_Wardrobe*, openable)
  against the nearest free wall within 3.5 m of the bed (else a washstand); each placement checked free with box overlaps
- walk-test path: flood fill (40 cm grid, Pawn capsule r 38) from just inside the main door over the entry floor; up to
  3 far points with their grid paths
Purpose: tavern (bar counters + many tables), home (beds), store (crates / kegs, no beds), workshop (the rest).
Args: [template names...] (default: all)"""
import sys, json, math, collections, heapq, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V = unreal.Vector
B = "/Game/Hivemind/Medieval_Docks/Levels/LI_Buildings/Buildings/LI_Building_"
NAMES = sys.argv[1:] or ["01a", "01b", "02", "03", "03a", "03b", "04a", "04b", "05", "06"]
OUT = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_level\templates.json"
import os; os.makedirs(os.path.dirname(OUT), exist_ok=True)
OT = [unreal.ObjectTypeQuery.ECC_WORLD_STATIC, unreal.ObjectTypeQuery.ECC_WORLD_DYNAMIC]
KIT = "/Game/Castle/Furniture/Kit/"
ADD_R = {"chest": 55.0, "trunk": 60.0, "wardrobe": 70.0, "washstand": 35.0}   # added furniture: radius kept clear by the walk paths
# entrances without a door leaf: (opening centre, outward direction, entry floor z)
OVERRIDE = {"02": ((-300.0, 600.0), (0.0, 1.0), 400.0),      # stone walkway on +y into the workshop half
            "06": ((-390.0, -306.0), (-1.0, 0.0), 0.0)}       # open-sided shed, walkway on -x
def rot_vec(yaw, x, y):
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)); return (x * c - y * s, x * s + y * c)
# random_level holds these maps as level instances: open a scratch level first (created if missing)
SCRATCH = "/Game/RandomLevel/Test/rl_scratch"
if unreal.EditorAssetLibrary.does_asset_exist(SCRATCH): les.load_level(SCRATCH)
else: les.new_level(SCRATCH)
try: allt = json.load(open(OUT))
except Exception: allt = {}
for nm in NAMES:
    les.load_level(B + nm + "_Fix")
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    LT = lambda a, b: unreal.SystemLibrary.line_trace_single(w, a, b, unreal.TraceTypeQuery.ECC_VISIBILITY, True, [], unreal.DrawDebugTrace.NONE, True)
    def hitz(x, y, z0, z1):
        r = LT(V(x, y, z0), V(x, y, z1)); t = r.to_tuple() if r else None
        return t[4].z if t and t[0] else None
    def hitd(p, d, L):
        r = LT(p, p + d * L); t = r.to_tuple() if r else None
        return t[3] if t and t[0] else None                              # (hit tuple: 2 time, 3 distance)
    acts = eas.get_all_level_actors()
    # right after an editor restart the maps' collision is cooked asynchronously: traces miss everything and the
    # templates would come out empty. Refuse instead (re-run once the maps have been loaded / cooked).
    _c = next((x for x in acts if isinstance(x, unreal.StaticMeshActor)), None)
    if _c:
        _o, _e = _c.get_actor_bounds(False)
        assert hitz(_o.x, _o.y, _o.z + _e.z + 200, _o.z - _e.z - 200) is not None, f"{nm}: no collision yet (async cooking after a restart) - run 750 again"
    lo, hi = [1e9] * 3, [-1e9] * 3; doors, frames, lids, beds, pillows, wardrobes, counts = [], [], [], [], [], [], collections.Counter()
    for a in acts:
        if isinstance(a, unreal.InstancedFoliageActor): continue
        cn = a.get_class().get_name()
        if "Wardrobe" in cn: wardrobes.append(a.get_actor_location())
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            sm = c.get_editor_property("static_mesh")
            if not sm or isinstance(c, unreal.InstancedStaticMeshComponent): continue
            n = sm.get_name(); counts[n] += 1
            o, e = c.get_editor_property("bounds").origin if False else (None, None)
            bb = c.get_local_bounds(); tr = c.get_world_transform()
            for cx in (bb[0].x, bb[1].x):
                for cy in (bb[0].y, bb[1].y):
                    for cz in (bb[0].z, bb[1].z):
                        p = tr.transform_location(V(cx, cy, cz))
                        for i, v in enumerate((p.x, p.y, p.z)): lo[i] = min(lo[i], v); hi[i] = max(hi[i], v)
            l, r = c.get_world_location(), c.get_world_rotation()
            rec = {"mesh": sm.get_path_name().split(".")[0], "loc": [round(l.x, 1), round(l.y, 1), round(l.z, 1)], "rot": [round(r.pitch, 2), round(r.yaw, 2), round(r.roll, 2)],
                   "scale": [round(v, 4) for v in (c.get_world_scale().x, c.get_world_scale().y, c.get_world_scale().z)]}
            if n in ("SM_Door_01", "SM_Door_02"): doors.append(rec)
            elif n in ("SM_Wall_Door_01", "SM_Wall_Door_02"): frames.append(rec)
            elif n.startswith("SM_Crate_Lid"): lids.append(rec)
            elif n == "SM_Bed": beds.append(rec)
            elif n == "SM_Pillow": pillows.append(l)
    # ---- doors: exterior / entry
    def side_info(p):
        """inside = (almost) no sky: rays straight up and at 55 deg elevation in 8 directions all hit within 25 m
        (outside, even under eaves / a porch roof, several slanted rays escape)"""
        o = p + V(0, 0, 150); dirs = [V(0, 0, 1)] + [V(math.cos(math.radians(a)) * 0.574, math.sin(math.radians(a)) * 0.574, 0.819) for a in range(0, 360, 45)]
        return sum(1 for d in dirs if hitd(o, d, 2500) is None) <= 1
    # the leaves stand ajar in these maps: the closed orientation comes from the nearest door-frame wall piece
    # (SM_Wall_Door_01/02, 400 cm along local x, opening in the middle); closed yaw = frame yaw or +180, whichever puts
    # the leaf middle nearer the frame centre
    for d in doors:
        px_, py_ = d["loc"][0], d["loc"][1]; half = 58 * (1 if d["mesh"].endswith("01") else -1)
        best = None
        for f_ in frames:
            fy = f_["rot"][1]; cx_, cy_ = f_["loc"][0] + rot_vec(fy, 200, 0)[0], f_["loc"][1] + rot_vec(fy, 200, 0)[1]
            if abs(f_["loc"][2] - d["loc"][2]) > 60: continue
            for cand in (fy, fy + 180):
                mx, my = px_ + rot_vec(cand, half, 0)[0], py_ + rot_vec(cand, half, 0)[1]
                dd = math.hypot(mx - cx_, my - cy_)
                if best is None or dd < best[0]: best = (dd, cand % 360, mx, my)
        if best is None or best[0] > 150:
            d["exterior"] = False; d["closed_yaw"] = d["rot"][1]; d["mid"] = [px_, py_]; d["out"] = [0, 0]; continue
        _, cyaw, mx, my = best; nx, ny = rot_vec(cyaw, 0, 1)
        a = side_info(V(mx + nx * 120, my + ny * 120, d["loc"][2])); b = side_info(V(mx - nx * 120, my - ny * 120, d["loc"][2]))
        d["exterior"] = a != b; d["closed_yaw"] = round(cyaw, 2)
        d["out"] = [round(nx, 3), round(ny, 3)] if (b and not a) else [round(-nx, 3), round(-ny, 3)]
        d["mid"] = [round(mx, 1), round(my, 1)]
    ext = [d for d in doors if d["exterior"]]
    floor_z = min((d["loc"][2] for d in ext), default=min((d["loc"][2] for d in doors), default=0.0))
    entry = [d for d in ext if abs(d["loc"][2] - floor_z) < 40]
    main = None
    if entry:                                                            # prefer a door whose outward side is clear for 6 m
        main = max(entry, key=lambda d: (hitd(V(d["mid"][0] + d["out"][0] * 60, d["mid"][1] + d["out"][1] * 60, floor_z + 120), V(d["out"][0], d["out"][1], 0), 800) or 800))
    if nm in OVERRIDE:                                                   # open doorways (no leaf), read off the floor plans
        (ox, oy), out, floor_z = OVERRIDE[nm]
        main = {"mid": [ox, oy], "out": list(out), "loc": [ox, oy, floor_z], "open": True}
    # ---- additions: chest at each bed foot, wardrobe (or washstand) on a nearby wall
    adds = []
    def free_box(c, ext_, yaw, ign=None):
        """oriented box (yaw) overlaps nothing but moss foliage: a zero-length box sweep reports initial overlaps"""
        r = unreal.SystemLibrary.box_trace_multi_for_objects(w, c, c + V(0, 0, 0.1), ext_, unreal.Rotator(roll=0, pitch=0, yaw=yaw), OT, False, [], unreal.DrawDebugTrace.NONE, True)
        hits = r[1] if isinstance(r, tuple) else r
        return not [h for h in (hits or []) if not isinstance(h.to_tuple()[9], unreal.InstancedFoliageActor)]
    def place(kind, cx, cy, z, yaw, he):
        """he = half extents (x, y, z) in the piece's frame; the box is checked at the piece's yaw"""
        f = hitz(cx, cy, z + 60, z - 60)
        if f is None or abs(f - z) > 12: return None
        if not free_box(V(cx, cy, f + he[2] + 4), V(he[0] + 2, he[1] + 2, he[2]), yaw): return None
        return f
    for bd in beds:
        yaw = bd["rot"][1]; bx, by, bz = bd["loc"]
        # SM_Bed spans local x 0..143 (width), y 0..273 (length); head = the end nearest a pillow
        ends = [(0.0, 0.0), (0.0, 273.0)]
        cen = lambda lx, ly: (bx + rot_vec(yaw, lx, ly)[0], by + rot_vec(yaw, lx, ly)[1])
        hy = 0.0
        if pillows:
            d0 = min(math.hypot(p.x - cen(71, 20)[0], p.y - cen(71, 20)[1]) for p in pillows); d1 = min(math.hypot(p.x - cen(71, 253)[0], p.y - cen(71, 253)[1]) for p in pillows)
            hy = 0.0 if d0 < d1 else 273.0
        foot = 273.0 - hy; sgn = 1 if foot > hy else -1                     # +local y toward the foot when the head is at y 0
        # chest at the foot: centred on the bed width, 40 cm past the foot end, lid hinge toward the bed
        # (front = local +y of the chest, away from the bed; hinge at the back)
        foot_yaw = yaw + (0 if sgn > 0 else 180)
        cands = [(71.5, foot + sgn * 40, foot_yaw), (71.5, foot + sgn * 60, foot_yaw),
                 (-38, foot - sgn * 75, yaw + 90), (181, foot - sgn * 75, yaw - 90),           # beside the foot end
                 (-38, foot - sgn * 135, yaw + 90), (181, foot - sgn * 135, yaw - 90)]
        for lx, ly, cyaw in cands:
            cx, cy = cen(lx, ly)
            f = place("chest", cx, cy, bz, cyaw, (46, 27, 23))
            if f is not None: adds.append({"kind": "chest", "loc": [round(cx, 1), round(cy, 1), round(f, 1)], "yaw": round(cyaw % 360, 1)}); break
        # wardrobe / washstand against a wall near the bed
        best = None
        for gx in range(-14, 15):
            for gy in range(-14, 15):
                px, py = bx + gx * 25, by + gy * 25
                bcx, bcy = cen(71.5, 136.5)
                dist = math.hypot(px - bcx, py - bcy)
                if dist > 350 or dist < 150: continue
                for dyaw, (dx, dy) in ((0, (0, -1)), (90, (1, 0)), (180, (0, 1)), (270, (-1, 0))):   # back toward the wall
                    h = hitd(V(px, py, bz + 120), V(dx, dy, 0), 60)
                    if h is None or h < 25: continue
                    for kind, he in (("wardrobe", (58, 30, 99)), ("washstand", (28, 20, 44))):
                        wx_, wy_ = px + dx * (h - he[1] - 3), py + dy * (h - he[1] - 3)
                        fyaw = (math.degrees(math.atan2(-dy, -dx)) - 90) % 360      # front (+local y) away from the wall
                        f = place(kind, wx_, wy_, bz, fyaw, he)
                        if f is None: continue
                        fx, fy = wx_ - dx * (he[1] + 45), wy_ - dy * (he[1] + 45)          # clearance in front
                        if not free_box(V(fx, fy, f + 60), V(he[0], 30, 50), 0): continue
                        if any(math.hypot(wx_ - a_["loc"][0], wy_ - a_["loc"][1]) < 140 for a_ in adds): continue
                        sc = dist + (0 if kind == "wardrobe" else 150)
                        if best is None or sc < best[0]: best = (sc, {"kind": kind, "loc": [round(wx_, 1), round(wy_, 1), round(f, 1)], "yaw": round(fyaw, 1)})
                        break
        if best: adds.append(best[1])
    # ---- purpose
    has = lambda k: sum(n for m, n in counts.items() if k in m)
    purpose = "tavern" if has("Counter") >= 15 and has("Table") + has("Chair") >= 10 else "home" if beds else "store" if has("Crate") + has("Keg") + has("Barrel") >= 6 else "workshop"
    # ---- walk-test path from just inside the main door over the entry floor
    paths = []
    if main:
        s = (main["mid"][0] - main["out"][0] * 90, main["mid"][1] - main["out"][1] * 90)
        G = 40.0; cell = lambda x, y: (int(round(x / G)), int(round(y / G)))
        fits = {}
        def fit(c):
            if c not in fits:
                x, y = c[0] * G, c[1] * G; f = hitz(x, y, floor_z + 80, floor_z - 60)
                ok = f is not None and abs(f - floor_z) < 25 and not unreal.SystemLibrary.capsule_overlap_actors(w, V(x, y, f + 100), 38.0, 80.0, OT, None, [])
                # the added furniture is not in the level: keep the path clear of it too
                ok = ok and all(math.hypot(x - a_["loc"][0], y - a_["loc"][1]) > 38 + ADD_R[a_["kind"]] for a_ in adds if abs(a_["loc"][2] - floor_z) < 80)
                fits[c] = ok
            return fits[c]
        s0 = cell(*s); seen = {s0: None}; q = collections.deque([s0]) if fit(s0) else collections.deque()
        while q and len(seen) < 6000:
            c = q.popleft()
            for a_, b_ in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (c[0] + a_, c[1] + b_)
                if n in seen or not fit(n): continue
                p0 = V(c[0] * G, c[1] * G, floor_z + 60); p1 = V(n[0] * G, n[1] * G, floor_z + 60)
                if hitd(p0, V(a_, b_, 0), G) is not None: continue
                seen[n] = c; q.append(n)
        far = sorted(seen, key=lambda c: -math.hypot(c[0] - s0[0], c[1] - s0[1]))
        picks = []
        for c in far:
            if all(math.hypot(c[0] - p[0], c[1] - p[1]) > 6 for p in picks): picks.append(c)
            if len(picks) == 3: break
        for p in picks:
            chain = []; c = p
            while c is not None: chain.append(c); c = seen[c]
            chain = chain[::-1]
            simp = [chain[0]]                                              # keep turning points
            for i in range(1, len(chain) - 1):
                if (chain[i][0] - chain[i - 1][0], chain[i][1] - chain[i - 1][1]) != (chain[i + 1][0] - chain[i][0], chain[i + 1][1] - chain[i][1]): simp.append(chain[i])
            simp.append(chain[-1])
            paths.append([[round(c[0] * G, 1), round(c[1] * G, 1)] for c in simp])
        print(f"  walk area {len(seen)} cells, paths {[len(p) for p in paths]}")
    allt[nm] = {"level": B + nm + "_Fix", "purpose": purpose, "lo": [round(v, 1) for v in lo], "hi": [round(v, 1) for v in hi], "floor_z": round(floor_z, 1),
                "doors": doors, "main": doors.index(main) if main in doors else -1,
                "entry": {"mid": main["mid"], "out": main["out"]} if main else None, "lids": lids, "adds": adds, "paths": paths,
                "beds": len(beds), "fireplaces": has("Fireplace"), "tables": has("Table"), "chairs": has("Chair") + has("Stool") + has("Bench")}
    print(nm, purpose, "| size", [round(hi[i] - lo[i]) for i in range(3)], "| floor", round(floor_z), "| doors", len(doors), "ext", len(ext), "main", main["mid"] if main else None, main["out"] if main else None,
          "| lids", len(lids), "| adds", collections.Counter(a_["kind"] for a_ in adds), "/ beds", len(beds))
json.dump(allt, open(OUT, "w"), indent=1)
print("wrote", OUT, len(allt))
