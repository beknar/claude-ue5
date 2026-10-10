"""castle_level: open houses + working doors, openable crates/barrels, furnished lit interiors, no grass indoors.
Uses SourceArt/castle_interactive/interactive.json (Blender coords: UE = (x, -y, z)). Re-runnable: removes what it placed
before (actors tagged 'castle_gen') and restores the original house meshes first."""
import json, math, random, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if "castle_level." not in unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name():
    les.load_level("/Game/Castle/Maps/castle_level")          # re-loading the open map from Python can crash the editor
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
INFO = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\castle_interactive\interactive.json"))
D = "/Game/Castle/Interactive"; MV = "/Game/Medieval_Fantasy_Village/Meshes"
SM = lambda p: unreal.load_asset(p)
DOOR_BP = unreal.EditorAssetLibrary.load_blueprint_class(f"{D}/Blueprints/BP_Door")
CONT_BP = unreal.EditorAssetLibrary.load_blueprint_class(f"{D}/Blueprints/BP_Container")
TAG = unreal.Name("castle_gen")
for a in eas.get_all_level_actors():
    if TAG in a.tags or a.get_class().get_name() in ("BP_Door_C", "BP_Container_C"): eas.destroy_actor(a)
def V(x, y, z): return unreal.Vector(x, y, z)
def rotv(rot, v): return unreal.MathLibrary.greater_greater_vector_rotator(v, rot)      # rotate vector by rotator
def ue(p): return V(p[0], -p[1], p[2])                         # Blender -> UE local
def tag(a, label):
    a.tags = list(a.tags) + [TAG]; a.set_actor_label(label); a.set_folder_path("CastleGen"); return a
def trace(a, b, ignore=()):
    h = unreal.SystemLibrary.line_trace_single(w, a, b, unreal.TraceTypeQuery.ECC_VISIBILITY, True, list(ignore), unreal.DrawDebugTrace.NONE, True)
    t = h.to_tuple() if h else None
    return (t[4], t[9]) if t and (t[0] or t[1]) else (None, None)
def trace_to(a, b, want, ignore=()):
    """first hit on an actor satisfying want(actor); anything else in between (pack foliage/props inside the houses) is skipped"""
    ign = list(ignore)
    for _ in range(12):
        p, act = trace(a, b, ign)
        if p is None or (act and want(act)): return p, act
        if act is None: return None, None
        ign.append(act)
    return None, None
IS_LAND = lambda x: x.get_class().get_name() == "Landscape" or "LandscapeStreamingProxy" in x.get_class().get_name()
def pick_yaw(d, inward):
    for th in (92.0, -92.0):                     # just past square: the open leaf stays clear of the doorway
        r = rotv(unreal.Rotator(roll=0, pitch=0, yaw=th), d)
        if r.x * inward.x + r.y * inward.y > 0: return th
    return 92.0
def lid_roll(front):
    for th in (105.0, -105.0):
        if rotv(unreal.Rotator(roll=th, pitch=0, yaw=0), front).z > 0: return th
    return 105.0
# ---------------- containers ----------------
CONT = {}
for name, rec in INFO["containers"].items():
    CONT[name] = {"body": SM(f"{D}/Meshes/{name}_body"), "lid": SM(f"{D}/Meshes/{name}_lid"),
                  "lid_loc": ue(rec["hinge"]), "liquid": SM(f"{D}/Meshes/{name}_liquid") if rec["kind"] == "cyl" else None,
                  "top": rec["top"], "kind": rec["kind"]}
BAG = SM(f"{MV}/Small_props/SM_bag_03")
def spawn_container(name, loc, rot, scale=V(1, 1, 1), label=None):
    c = CONT[name]
    a = eas.spawn_actor_from_class(CONT_BP, loc, rot)
    a.set_actor_scale3d(scale)
    comps = {x.get_name(): x for x in a.get_components_by_class(unreal.SceneComponent)}
    comps["Body"].set_static_mesh(c["body"]); comps["Lid"].set_static_mesh(c["lid"]); comps["Lid"].set_editor_property("relative_location", c["lid_loc"])
    if c["liquid"]: comps["Contents"].set_static_mesh(c["liquid"])
    else:
        comps["Contents"].set_static_mesh(BAG); comps["Contents"].set_editor_property("relative_location", V(0, 0, 4))
        comps["Contents"].set_editor_property("relative_scale3d", V(0.55, 0.55, 0.55) if "01" in name else V(0.5, 0.5, 0.5))
    comps["Prompt"].set_editor_property("relative_location", V(0, 0, c["top"] + 30))
    a.set_editor_property("OpenRoll", lid_roll(V(0, 1, 0)))
    return tag(a, label or name.replace("SM_", "Open_"))
# village props -> openable containers, from the placements recorded off the pack map (339_village_containers.py)
replaced = 0
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh and a.static_mesh_component.static_mesh.get_name() in CONT:
        eas.destroy_actor(a)
for r_ in json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\castle_interactive\village_containers.json")):
    spawn_container(r_["mesh"], V(*r_["loc"]), unreal.Rotator(roll=r_["rot"][0], pitch=r_["rot"][1], yaw=r_["rot"][2]), V(*r_["scale"])); replaced += 1
print("village containers (openable):", replaced)
# ---------------- houses ----------------
FLOOR = SM(f"{MV}/Planks/SM_floor_plank"); LEG = SM(f"{MV}/Pillar/SM_pillar_02")
STATIC = {k: SM(f"{MV}/Small_props/{k}") for k in ("SM_barrel_group_01", "SM_crate_group_02", "SM_bag", "SM_bag_02", "SM_bag_03", "SM_crate_group_01")}
def bbox(sm):
    b = sm.get_bounding_box(); return b.min, b.max
def place(sm, house, cx, cy, z0, size=None, yaw=0.0, label="prop", coll=True):
    """put mesh sm with its bbox bottom-centre at house-local (cx, cy, z0), scaled to size (local xyz cm) if given"""
    lo, hi = bbox(sm); ext = hi - lo
    s = V(size[0] / ext.x, size[1] / ext.y, size[2] / ext.z) if size else V(1, 1, 1)
    rot_l = unreal.Rotator(roll=0, pitch=0, yaw=yaw)
    off = rotv(rot_l, V(-(lo.x + ext.x / 2) * s.x, -(lo.y + ext.y / 2) * s.y, -lo.z * s.z))
    loc_l = V(cx, cy, z0) + off
    tr = house.get_actor_transform()
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, tr.transform_location(loc_l), unreal.MathLibrary.compose_rotators(rot_l, house.get_actor_rotation()))
    a.static_mesh_component.set_static_mesh(sm); a.set_actor_scale3d(s)
    if not coll: a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return tag(a, label)
def light(house, cx, cy, z, inten, label):
    tr = house.get_actor_transform()
    a = eas.spawn_actor_from_class(unreal.PointLight, tr.transform_location(V(cx, cy, z)), unreal.Rotator())
    lc = a.get_component_by_class(unreal.PointLightComponent)
    lc.set_editor_property("intensity", inten); lc.set_editor_property("attenuation_radius", 1300.0)
    lc.set_editor_property("light_color", unreal.Color(r=255, g=210, b=165, a=255)); lc.set_editor_property("source_radius", 8.0)
    lc.set_editor_property("cast_shadows", True)
    return tag(a, label)
foliage = [c for f in eas.get_all_level_actors() if f.get_class().get_name() == "InstancedFoliageActor" for c in f.get_components_by_class(unreal.InstancedStaticMeshComponent)]
houses = [a for a in eas.get_all_level_actors() if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh
          and a.static_mesh_component.static_mesh.get_name().replace("_open", "") in INFO["houses"]]
report = []
for hi, house in enumerate(houses):
    random.seed(hi * 31 + 7)
    hname = house.static_mesh_component.static_mesh.get_name().replace("_open", "")
    house.static_mesh_component.set_static_mesh(SM(f"{D}/Meshes/{hname}_open"))
    tr = house.get_actor_transform(); rot = house.get_actor_rotation(); base = house.get_actor_location().z
    to_w = lambda x, y, z: tr.transform_location(V(x, y, z))
    # interior extents from the centre (local axes), at 1.2 m
    c0 = to_w(0, 0, 120); ext = {}
    for key, d in {"+x": V(1, 0, 0), "-x": V(-1, 0, 0), "+y": V(0, 1, 0), "-y": V(0, -1, 0)}.items():
        p, _ = trace_to(c0, c0 + rotv(rot, d) * 3000, lambda x, h=house: x == h)
        ext[key] = (p - c0).length() if p else 600.0
    x0, x1, y0, y1 = -ext["-x"] + 18, ext["+x"] - 18, -ext["-y"] + 18, ext["+y"] - 18
    # loose path cobbles (Small_rocks actors) also sit inside the houses
    inv = tr.inverse_transform_location; gone = 0
    for r_ in eas.get_all_level_actors():
        if isinstance(r_, unreal.StaticMeshActor) and r_.static_mesh_component.static_mesh and "/Small_rocks/" in r_.static_mesh_component.static_mesh.get_path_name():
            q = inv(r_.get_actor_location())
            if x0 - 15 < q.x < x1 + 15 and y0 - 15 < q.y < y1 + 15 and q.z < 120: eas.destroy_actor(r_); gone += 1
    # landscape inside -> floor height
    hs = []
    for i in range(7):
        for j in range(7):
            p, act = trace_to(to_w(x0 + (x1 - x0) * i / 6, y0 + (y1 - y0) * j / 6, 400), to_w(x0 + (x1 - x0) * i / 6, y0 + (y1 - y0) * j / 6, -400), IS_LAND, ignore=[house])
            if p is not None: hs.append(p.z - base)
    hs.sort(); top = max(18.0, hs[int(len(hs) * 0.97)] + 17.0) if hs else 18.0      # landscape small-rocks grass grows up to ~16 cm: keep it under the floor
    reachable = top <= 130.0
    # doors (+ a stair landing inside each door when the floor had to be raised over the landscape)
    doors = []; landings = []
    for di, d in enumerate(INFO["houses"][hname]):
        piv = ue(d["pivot"]); dirv = ue(d["leaf_dir"]); inward = V(-1 if piv.x > 0 else 1, 0, 0)
        a = eas.spawn_actor_from_class(DOOR_BP, tr.transform_location(piv), rot)
        tag(a, f"Door_{house.get_actor_label()}_{di}")
        comps = {x.get_name(): x for x in a.get_components_by_class(unreal.SceneComponent)}
        comps["Leaf"].set_static_mesh(SM(f"{D}/Meshes/{hname}_door{di}"))
        comps["Prompt"].set_editor_property("relative_location", V(-inward.x * 40, dirv.y * 74, 150))
        dcx, dcy = piv.x, piv.y + dirv.y * 74
        swing_in = False                                          # outward: never scrapes the raised floor / stairs
        a.set_editor_property("OpenYaw", pick_yaw(dirv, inward if swing_in else V(-inward.x, 0, 0)))
        if not reachable: a.set_editor_property("NearDist", 0.0)
        doors.append((dcx, dcy))
        if reachable and top > 6.0:
            n = int(math.ceil((top - 1.5) / 35.0)); depth = 38.0
            wall_in = x1 if piv.x > 0 else x0
            lx0, lx1 = sorted((wall_in, wall_in + inward.x * (n * depth + 10)))
            landings.append((lx0, lx1, dcy - 95, dcy + 95))
            for k in range(1, n + 1):
                h = 1.5 + (top - 1.5) * k / n
                sx = wall_in + inward.x * (depth * (k - 0.5))
                place(FLOOR, house, sx, dcy, h - 64, size=(depth + 1, 190, 64), label="Step")
            fill_x = wall_in + inward.x * (n * depth + 5)
            place(FLOOR, house, fill_x, dcy, top - 64, size=(12, 190, 64), label="StepTop")
    if not reachable:      # sunk into the hillside / overlapping a neighbouring house: doors stay shut, no interior
        report.append(f"{house.get_actor_label()} {hname}: ground inside {top:.0f} cm above the door sill -> doors kept shut, no interior"); continue
    # floor: 100 cm cells at `top`, cells overlapping a landing are covered by the pieces outside it
    W, Hh = x1 - x0, y1 - y0; nx, ny = max(1, int(round(W / 100))), max(1, int(round(Hh / 100)))
    def rect_minus(r, h):
        (a0, a1, b0, b1), (c0, c1, d0, d1) = r, h
        if c1 <= a0 or c0 >= a1 or d1 <= b0 or d0 >= b1: return [r]
        out = []
        if c0 > a0: out.append((a0, c0, b0, b1))
        if c1 < a1: out.append((c1, a1, b0, b1))
        mx0, mx1 = max(a0, c0), min(a1, c1)
        if d0 > b0: out.append((mx0, mx1, b0, d0))
        if d1 < b1: out.append((mx0, mx1, d1, b1))
        return out
    cells = [(x0 + W * i / nx, x0 + W * (i + 1) / nx, y0 + Hh * j / ny, y0 + Hh * (j + 1) / ny) for i in range(nx) for j in range(ny)]
    for L_ in landings: cells = [p for c in cells for p in rect_minus(c, L_)]
    # merge cells column-wise to keep the actor count down
    nfl = 0
    for (a0, a1, b0, b1) in cells:
        if a1 - a0 < 1 or b1 - b0 < 1: continue
        place(FLOOR, house, (a0 + a1) / 2, (b0 + b1) / 2, top - 64, size=(a1 - a0 + 1.5, b1 - b0 + 1.5, 64), label="Floor"); nfl += 1

    # keep-out: door swing circles
    def clear(x, y, r):
        return all(math.hypot(x - dx, y - dy) > r + 190 for dx, dy in doors) and x0 + r < x < x1 - r and y0 + r < y < y1 - r
    door_side = 1 if sum(dx for dx, _ in doors) > 0 else -1          # wall the (first) door is on
    back = -door_side
    # table + benches near the centre, offset toward the back wall
    tx, ty = back * min(180, (x1 - x0) * 0.18), (y0 + y1) / 2 + random.uniform(-80, 80)
    if clear(tx, ty, 110):
        place(FLOOR, house, tx, ty, top + 72, size=(150, 85, 6), label="TableTop")
        for sx in (-62, 62):
            for sy in (-34, 34): place(LEG, house, tx + sx, ty + sy, top, size=(9, 9, 72), label="TableLeg")
        for sy in (-80, 80):
            place(FLOOR, house, tx, ty + sy, top + 42, size=(130, 30, 5), label="Bench")
            for sx in (-50, 50): place(LEG, house, tx + sx, ty + sy, top, size=(8, 8, 42), label="BenchLeg")
    # bed along a side wall at the back
    bx, by = back * ((x1 - x0) / 2 - 140), y1 - 70
    if clear(bx, by, 110):
        place(FLOOR, house, bx, by, top, size=(200, 100, 38), yaw=0, label="BedFrame")
        place(STATIC["SM_bag_02"], house, bx + back * 70, by, top + 38, size=(45, 70, 22), label="Pillow")
    # openable containers + static clutter in the back corners
    corners = [(back * ((x1 - x0) / 2 - 60), y0 + 60), (back * ((x1 - x0) / 2 - 60), y0 + 150), (back * ((x1 - x0) / 2 - 150), y0 + 55),
               (-back * ((x1 - x0) / 2 - 70), y0 + 60), (back * ((x1 - x0) / 2 - 60), (y0 + y1) / 2 - 140)]
    kinds = ["SM_crate_01", "SM_barrel_02", "SM_crate_02", "SM_barrel_01", "SM_barrel_02"]
    nc = 0
    for (cx, cy), k in zip(corners, kinds):
        if clear(cx, cy, 55):
            spawn_container(k, to_w(cx, cy, top), unreal.MathLibrary.compose_rotators(unreal.Rotator(0, 0, random.uniform(-20, 20)), rot), label=f"{k.replace('SM_', 'Open_')}_in")
            nc += 1
    for k, (cx, cy) in (("SM_barrel_group_01", (-back * ((x1 - x0) / 2 - 110), y1 - 110)), ("SM_crate_group_02", (back * 40, y0 + 80)),
                        ("SM_bag", (back * ((x1 - x0) / 2 - 220), y0 + 45)), ("SM_bag_03", (back * ((x1 - x0) / 2 - 260), y0 + 50))):
        if clear(cx, cy, 70): place(STATIC[k], house, cx, cy, top, yaw=random.uniform(0, 360), label=k)
    # lights
    light(house, back * (x1 - x0) * 0.15, (y0 + y1) / 2, top + 300, 120.0, "InteriorLight")
    light(house, -back * (x1 - x0) * 0.25, (y0 + y1) / 2 + (y1 - y0) * 0.25, top + 280, 40.0, "InteriorFill")
    # interior exposure: the village post-process clamps exposure to the sunlit outdoor range; let it adapt indoors
    pv = eas.spawn_actor_from_class(unreal.PostProcessVolume, to_w((x0 + x1) / 2, (y0 + y1) / 2, top + 300), rot)
    pv.set_actor_scale3d(V((x1 - x0) / 200.0, (y1 - y0) / 200.0, 600.0 / 200.0))
    pv.set_editor_property("unbound", False); pv.set_editor_property("priority", 2.0); pv.set_editor_property("blend_radius", 120.0)
    ps = pv.settings
    for k, v in (("auto_exposure_min_brightness", -3.0), ("auto_exposure_max_brightness", 1.0), ("auto_exposure_bias", 0.6), ("auto_exposure_speed_up", 2.0), ("auto_exposure_speed_down", 2.0)):
        ps.set_editor_property("override_" + k, True); ps.set_editor_property(k, v)
    pv.set_editor_property("settings", ps); tag(pv, "InteriorExposure")
    # grass out of the house
    # only instances standing inside the interior walls (the ground outside, under eaves and porches stays as authored)
    corners = [to_w(cx, cy, 0) for cx, cy in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    box = unreal.Box(min=V(min(p.x for p in corners), min(p.y for p in corners), base - 300), max=V(max(p.x for p in corners), max(p.y for p in corners), base + 400))
    removed = 0
    for comp in foliage:
        idx = comp.get_instances_overlapping_box(box, True) or []
        inside = []
        for i in idx:
            q = inv(comp.get_instance_transform(i, True).translation)
            if x0 <= q.x <= x1 and y0 <= q.y <= y1: inside.append(i)
        if inside:
            comp.remove_instances(inside); removed += len(inside)
    report.append(f"{house.get_actor_label()} {hname}: interior x[{x0:.0f},{x1:.0f}] y[{y0:.0f},{y1:.0f}] floor +{top:.1f} (landscape p95 {hs[int(len(hs)*0.95)] if hs else 0:.1f}) "
                  f"doors {len(doors)} landings {len(landings)} floor pieces {nfl} containers {nc} cobbles {gone} grass {removed}")
print("\n".join(report))
les.save_current_level()
print("saved")
# drop this script's globals (actor/component wrappers): the remote-exec interpreter is shared, and stale wrappers have
# crashed the editor later when PIE duplicated the world
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()