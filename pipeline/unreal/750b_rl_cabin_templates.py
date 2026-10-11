"""random_level: Sherwood house prefabs (BP_House_A/B/C, log-cabin storehouses) as building templates, appended to
SourceArt/random_level/templates.json as cabin_A/B/C. Each is spawned in the scratch level /Game/RandomLevel/Test/rl_scratch (created if missing)
(actor frame = template frame); the door (SM_door, pivot = hinge) stands ajar in A and C: its closed yaw was found by
tracing through the wall on both sides of the hinge (A, B: yaw 0, doorway on the +y wall; C: yaw 90, doorway on x = 0).
Walk paths: flood fill (40 cm grid, capsule r 38) from 1 m inside the doorway."""
import json, math, collections, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V = unreal.Vector
OUT = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_level\templates.json"
CLOSED = {"A": (0.0, (0.0, 1.0)), "B": (0.0, (0.0, 1.0)), "C": (90.0, (-1.0, 0.0))}      # closed yaw, outward
OT = [unreal.ObjectTypeQuery.ECC_WORLD_STATIC, unreal.ObjectTypeQuery.ECC_WORLD_DYNAMIC]
SCRATCH = "/Game/RandomLevel/Test/rl_scratch"
if unreal.EditorAssetLibrary.does_asset_exist(SCRATCH): les.load_level(SCRATCH)
else: les.new_level(SCRATCH)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for a in eas.get_all_level_actors():
    if a.get_class().get_name().startswith("BP_House"): eas.destroy_actor(a)
T = json.load(open(OUT))
for i, k in enumerate("ABC"):
    cls = unreal.EditorAssetLibrary.load_blueprint_class("/Game/Hive_Sherwood/Blueprints/BP_House_" + k)
    org = V(i * 4000.0, 6000.0, 0.0)
    a = eas.spawn_actor_from_class(cls, org, unreal.Rotator()); tr = a.get_actor_transform()
    lo, hi = [1e9] * 3, [-1e9] * 3; door = None
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm = c.get_editor_property("static_mesh")
        if not sm: continue
        bb = c.get_local_bounds(); wt = c.get_world_transform()
        for cx in (bb[0].x, bb[1].x):
            for cy in (bb[0].y, bb[1].y):
                for cz in (bb[0].z, bb[1].z):
                    p = tr.inverse_transform_location(wt.transform_location(V(cx, cy, cz)))
                    for j, v in enumerate((p.x, p.y, p.z)): lo[j] = min(lo[j], v); hi[j] = max(hi[j], v)
        if sm.get_name() == "SM_door":
            l = tr.inverse_transform_location(c.get_world_location())
            door = {"mesh": sm.get_path_name().split(".")[0], "loc": [round(l.x, 1), round(l.y, 1), round(l.z, 1)], "rot": [0.0, round(c.get_world_rotation().yaw, 2), 0.0],
                    "scale": [1.0, 1.0, 1.0], "exterior": True}
    cyaw, out = CLOSED[k]
    door["closed_yaw"] = cyaw
    mx, my = door["loc"][0] + 48 * math.cos(math.radians(cyaw)), door["loc"][1] + 48 * math.sin(math.radians(cyaw))
    door["mid"] = [round(mx, 1), round(my, 1)]; door["out"] = list(out)
    # flood over the floor from 1 m inside (door leaf ignored)
    G = 40.0; s = (mx - out[0] * 100, my - out[1] * 100); dcomp = [c for c in a.get_components_by_class(unreal.StaticMeshComponent) if c.get_editor_property("static_mesh") and c.get_editor_property("static_mesh").get_name() == "SM_door"]
    def W(x, y): return tr.transform_location(V(x, y, 0))
    def hitz(x, y):
        r = unreal.SystemLibrary.line_trace_single(w, W(x, y) + V(0, 0, 80), W(x, y) - V(0, 0, 60), unreal.TraceTypeQuery.ECC_VISIBILITY, True, [], unreal.DrawDebugTrace.NONE, True)
        t = r.to_tuple() if r else None; return t[4].z - org.z if t and t[0] else None
    fits = {}
    def fit(c):
        if c not in fits:
            x, y = c[0] * G, c[1] * G
            if not (lo[0] + 40 < x < hi[0] - 40 and lo[1] + 40 < y < hi[1] - 40): fits[c] = False; return False
            f = hitz(x, y)
            o = unreal.SystemLibrary.capsule_overlap_components(w, W(x, y) + V(0, 0, (f or 0) + 100), 38.0, 80.0, OT, None, [])
            o = [q for q in (o or []) if q not in dcomp and not (isinstance(q, unreal.StaticMeshComponent) and q.get_owner() != a)]
            fits[c] = f is not None and abs(f) < 25 and not o
        return fits[c]
    s0 = (int(round(s[0] / G)), int(round(s[1] / G))); seen = {s0: None}; q = collections.deque([s0]) if fit(s0) else collections.deque()
    while q and len(seen) < 3000:
        c = q.popleft()
        for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c[0] + da, c[1] + db)
            if n not in seen and fit(n): seen[n] = c; q.append(n)
    paths = []
    far = sorted(seen, key=lambda c: -math.hypot(c[0] - s0[0], c[1] - s0[1]))
    picks = []
    for c in far:
        if all(math.hypot(c[0] - p[0], c[1] - p[1]) > 5 for p in picks): picks.append(c)
        if len(picks) == 2: break
    for p in picks:
        ch = []; c = p
        while c is not None: ch.append(c); c = seen[c]
        ch = ch[::-1]; simp = [ch[0]] + [ch[j] for j in range(1, len(ch) - 1) if (ch[j][0] - ch[j - 1][0], ch[j][1] - ch[j - 1][1]) != (ch[j + 1][0] - ch[j][0], ch[j + 1][1] - ch[j][1])] + [ch[-1]]
        paths.append([[round(c[0] * G, 1), round(c[1] * G, 1)] for c in simp])
    T["cabin_" + k] = {"actor_class": "/Game/Hive_Sherwood/Blueprints/BP_House_" + k, "purpose": "cabin", "lo": [round(v, 1) for v in lo], "hi": [round(v, 1) for v in hi],
                       "floor_z": 0.0, "doors": [door], "main": 0, "entry": {"mid": door["mid"], "out": door["out"]}, "lids": [], "adds": [], "paths": paths}
    print("cabin", k, "size", [round(hi[j] - lo[j]) for j in range(3)], "door", door["loc"], "closed", cyaw, "| walk cells", len(seen), "paths", [len(p) for p in paths])
    eas.destroy_actor(a)
json.dump(T, open(OUT, "w"), indent=1)
