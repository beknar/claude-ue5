"""Shared interior builder (furniture kit, openables, room lining, lights) for buildings in any level.
Usage (from an editor script):  sys.path.insert(0, r"E:\\code\\claude-ue5\\pipeline\\unreal"); import interior_lib as IL
    r = IL.Room(frame_transform, floor_z, tag="fcl_int", folder="FCL/Interiors/<name>")
    r.line(x0, x1, y0, y1, height, door=("+y", 0.0, 150, 250)); r.floor(...); r.put("TableLong", x, y, r.z) ...
Local frame = the building actor's (x, y; z above its pivot). Kit props face +Y. Spawned actors carry `tag`.
Conventions and the furniture vocabulary follow pipeline/unreal/380_castle_furnish.py (castle_level)."""
import json, math, random, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
V = unreal.Vector
PACK = lambda n: f"/Game/Medieval_Fantasy_Village/Meshes/{n}"
LAKE = lambda n: f"/Game/Medieval_Lake_Village/Meshs/{n}"
FC = lambda n: f"/Game/FantasyCastle/Mesh/{n}"
KITH = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\castle_furniture\kit.json"))["_hinges"]
CONT_BP = eal.load_blueprint_class("/Game/Castle/Interactive/Blueprints/BP_Container")
WARD_BP = eal.load_blueprint_class("/Game/Castle/Interactive/Blueprints/BP_Wardrobe")
DOOR_BP = eal.load_blueprint_class("/Game/Castle/Interactive/Blueprints/BP_Door")
OPENABLE = {"Chest": "chest", "S:Trunk": "trunk", "Wardrobe": "wardrobe"}
SCAN_OFF = {"S:ChairWindsor": -90.0, "S:ChairB": -90.0, "S:ChairC": -90.0}
FACE = {"+y": 0.0, "-y": 180.0, "+x": -90.0, "-x": 90.0}
_cache = {}
def M(p):
    if p not in _cache:
        _cache[p] = unreal.load_asset(p if p.startswith("/") else (f"/Game/Castle/Furniture/Kit/SM_Kit_{p}" if not p.startswith("S:") else f"/Game/Castle/Furniture/Scans/SM_Scan_{p[2:]}"))
        assert _cache[p] is not None, p
    return _cache[p]
def rotv(rot, v): return unreal.MathLibrary.greater_greater_vector_rotator(v, rot)
def door_frame(base_tr, door_xy, floor_z, inward_xy):
    """world transform of a room frame: origin on the door wall at floor level, +Y into the room, +X along the wall.
    door_xy / floor_z / inward_xy are in base_tr's local space (pass unreal.Transform() for world coordinates)."""
    yaw = math.degrees(math.atan2(inward_xy[1], inward_xy[0])) - 90.0
    local = unreal.Transform(location=V(door_xy[0], door_xy[1], floor_z), rotation=unreal.Rotator(roll=0, pitch=0, yaw=yaw), scale=V(1, 1, 1))
    return unreal.MathLibrary.compose_transforms(local, base_tr)
def frame_extent(frame_tr, base_tr, corners_local):
    """x/y range of base-local points (e.g. room corners) expressed in the room frame"""
    pts = [frame_tr.inverse_transform_location(base_tr.transform_location(V(x, y, 0))) for x, y in corners_local]
    return min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts)
def clear(tag):
    n = 0
    for a in eas.get_all_level_actors():
        if unreal.Name(tag) in a.tags: eas.destroy_actor(a); n += 1
    return n
class Room:
    def __init__(s, tr, floor_z, tag, folder):
        s.tr = tr; s.rot = tr.rotation.rotator(); s.z = floor_z
        s.tag = unreal.Name(tag); s.folder = folder; s.n = 0
    def _fin(s, a, label):
        a.tags = [s.tag]; a.set_actor_label(label); a.set_folder_path(s.folder); s.n += 1; return a
    def W(s, x, y, z): return s.tr.transform_location(V(x, y, z))
    def R(s, yaw): return unreal.MathLibrary.compose_rotators(unreal.Rotator(roll=0, pitch=0, yaw=yaw), s.rot)
    # ---------- primitives ----------
    def put(s, mesh, x, y, z, yaw=0.0, scale=1.0, coll=True, label="Furn"):
        """bbox bottom-centre of `mesh` at local (x, y, z), local yaw, uniform or xyz scale"""
        if mesh in OPENABLE: return s.openable(OPENABLE[mesh], x, y, z, yaw, label if label != "Furn" else None)
        sm = M(mesh); b = sm.get_bounding_box(); sc = V(scale, scale, scale) if isinstance(scale, (int, float)) else V(*scale)
        yaw = yaw + SCAN_OFF.get(mesh, 0.0); rl = unreal.Rotator(roll=0, pitch=0, yaw=yaw)
        off = rotv(rl, V(-(b.min.x + b.max.x) / 2 * sc.x, -(b.min.y + b.max.y) / 2 * sc.y, -b.min.z * sc.z))
        a = eas.spawn_actor_from_class(unreal.StaticMeshActor, s.tr.transform_location(V(x, y, z) + off), s.R(yaw))
        a.static_mesh_component.set_static_mesh(sm); a.set_actor_scale3d(sc)
        if not coll: a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        return s._fin(a, label)
    def box(s, x, y, z, sx, sy, sz, yaw=0.0, mesh="Panel", label="Lining", mat=None):
        """kit panel (100 cube, bottom-centre origin) scaled to sx * sy * sz cm, bottom-centre at local (x, y, z)"""
        a = s.put(mesh, x, y, z, yaw=yaw, scale=(sx / 100.0, sy / 100.0, sz / 100.0), label=label)
        if mat: a.static_mesh_component.set_material(0, unreal.load_asset(mat))
        return a
    def openable(s, kind, x, y, z, yaw=0.0, label=None):
        """chests / trunks (BP_Container, hinged lid) and wardrobes (BP_Wardrobe, two doors)"""
        loc = s.W(x, y, z); rot = s.R(yaw)
        if kind == "wardrobe": a = eas.spawn_actor_from_class(WARD_BP, loc, rot)
        else:
            a = eas.spawn_actor_from_class(CONT_BP, loc, rot); key = "Chest" if kind == "chest" else "Trunk"; hg = KITH[key]
            c = {k.get_name(): k for k in a.get_components_by_class(unreal.SceneComponent)}
            c["Body"].set_static_mesh(M(f"{key}Body")); c["Lid"].set_static_mesh(M(f"{key}Lid"))
            c["Lid"].set_editor_property("relative_location", V(hg[0], -hg[1], hg[2])); c["Contents"].set_static_mesh(None)
            c["Prompt"].set_editor_property("relative_location", V(0, 0, hg[2] + 45))
            for th in (105.0, -105.0):
                if rotv(unreal.Rotator(roll=th, pitch=0, yaw=0), V(0, 1, 0)).z > 0: a.set_editor_property("OpenRoll", th); break
        return s._fin(a, label or f"Open{kind.title()}")
    def door(s, leaf_mesh, x_hinge, y, z, width=None, height=None, open_yaw=95.0, label="Door"):
        """BP_Door (F to open) in a wall that runs along the frame's X axis at depth y: hinge at x_hinge, leaf along +X,
        swings into the room (+Y). leaf_mesh: pivot on the hinge at the bottom, leaf along +X (blender_numpy/fcl_leaf_pivot.py).
        width / height rescale the leaf to the opening."""
        a = eas.spawn_actor_from_class(DOOR_BP, s.W(x_hinge, y, z), s.R(0.0))
        c = {k.get_name(): k for k in a.get_components_by_class(unreal.SceneComponent)}
        c["Leaf"].set_static_mesh(unreal.load_asset(leaf_mesh))
        b = c["Leaf"].static_mesh.get_bounding_box(); wdt, hgt = b.max.x - b.min.x, b.max.z - b.min.z
        sx = (width / wdt) if width else 1.0; sz = (height / hgt) if height else 1.0
        c["Leaf"].set_editor_property("relative_scale3d", V(sx, 1.0, sz))
        c["Prompt"].set_editor_property("relative_location", V(wdt * sx / 2, -45, 150))       # outside (-Y) of the door
        a.set_editor_property("OpenYaw", open_yaw)                                           # +yaw turns the leaf toward +Y (inside)
        return s._fin(a, label)
    def light(s, x, y, z, cd, color=(255, 216, 178), radius=900.0, label="RoomLight"):
        a = eas.spawn_actor_from_class(unreal.PointLight, s.W(x, y, z), unreal.Rotator())
        lc = a.get_component_by_class(unreal.PointLightComponent)
        lc.set_editor_property("intensity", cd * 0.6); lc.set_editor_property("attenuation_radius", radius); lc.set_editor_property("source_radius", 10.0)
        lc.set_editor_property("light_color", unreal.Color(r=color[0], g=color[1], b=color[2], a=255)); lc.set_editor_property("cast_shadows", True)
        lc.set_editor_property("volumetric_scattering_intensity", 0.0)
        return s._fin(a, label)
    def fire_light(s, x, y, z):
        a = s.light(x, y, z, 55.0, (255, 160, 85), 900.0, "FireLight")
        a.get_component_by_class(unreal.PointLightComponent).set_editor_property("source_radius", 45.0); return a
    def exposure(s, x0, x1, y0, y1, z0, z1, label="InteriorExposure"):
        """unbound=False post-process volume over the room: capped auto exposure so the room is neither black nor blown out"""
        a = eas.spawn_actor_from_class(unreal.PostProcessVolume, s.W((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), s.R(0))
        a.set_actor_scale3d(V((x1 - x0) / 200.0, (y1 - y0) / 200.0, (z1 - z0) / 200.0))
        a.set_editor_property("unbound", False); a.set_editor_property("priority", 5.0); a.set_editor_property("blend_radius", 150.0)
        pp = a.get_editor_property("settings")
        for k, v in (("auto_exposure_min_brightness", -1.5), ("auto_exposure_max_brightness", 0.5), ("auto_exposure_bias", 0.0), ("bloom_intensity", 0.15), ("lens_flare_intensity", 0.0)):
            pp.set_editor_property("override_" + k, True); pp.set_editor_property(k, v)
        a.set_editor_property("settings", pp)
        return s._fin(a, label)
    # ---------- shells ----------
    def floor(s, x0, x1, y0, y1, top, th=12.0, kind="plank", label="Floor"):
        """floor slab with its top at `top`: pack floor planks (wood) or the castle's stone floor tile"""
        if kind == "stone":
            sm = M(FC("SM_FloorType1")); b = sm.get_bounding_box()
            return s.put(FC("SM_FloorType1"), (x0 + x1) / 2, (y0 + y1) / 2, top - (b.max.z - b.min.z),
                         scale=((x1 - x0) / (b.max.x - b.min.x), (y1 - y0) / (b.max.y - b.min.y), 1.0), label=label)
        nx, ny = max(1, int(round((x1 - x0) / 300))), max(1, int(round((y1 - y0) / 300)))
        for i in range(nx):
            for j in range(ny):
                s.put(PACK("Planks/SM_floor_plank"), x0 + (x1 - x0) * (i + 0.5) / nx, y0 + (y1 - y0) * (j + 0.5) / ny, top - th,
                      scale=((x1 - x0) / nx / 613.0 * 1.01, (y1 - y0) / ny / 303.0 * 1.01, th / 64.0), label=label)
    def line(s, x0, x1, y0, y1, h, doors=(), th=14.0, ceiling=True, mat=None, label="Lining"):
        """line a room's inner walls (and ceiling) with kit panels so a single-sided shell still reads as walls from inside.
        doors: (side '+x'|'-x'|'+y'|'-y', centre along that wall, width, height) -> gap + lintel"""
        z = s.z
        walls = {"-y": ((x0, y0), (x1, y0)), "+y": ((x0, y1), (x1, y1)), "-x": ((x0, y0), (x0, y1)), "+x": ((x1, y0), (x1, y1))}
        for side, ((xa, ya), (xb, yb)) in walls.items():
            L = math.hypot(xb - xa, yb - ya); ux, uy = (xb - xa) / L, (yb - ya) / L; yaw = math.degrees(math.atan2(yb - ya, xb - xa))
            gaps = sorted([((c - (xa if side in ("-y", "+y") else ya)) - w / 2, (c - (xa if side in ("-y", "+y") else ya)) + w / 2, dh) for sd, c, w, dh in doors if sd == side])
            cuts = [0.0]
            for g0, g1, _ in gaps: cuts += [g0, g1]
            cuts.append(L)
            for k in range(0, len(cuts), 2):
                a0, a1 = cuts[k], cuts[k + 1]
                if a1 - a0 > 5: m = (a0 + a1) / 2; s.box(xa + ux * m, ya + uy * m, z, a1 - a0, th, h, yaw=yaw, label=label, mat=mat)
            for g0, g1, dh in gaps:
                m = (g0 + g1) / 2; s.box(xa + ux * m, ya + uy * m, z + dh, g1 - g0, th, h - dh, yaw=yaw, label=label, mat=mat)
        if ceiling: s.box((x0 + x1) / 2, (y0 + y1) / 2, z + h, x1 - x0 + th, y1 - y0 + th, th, label="Ceiling", mat=mat)
    def beam(s, xa, ya, xb, yb, z, sz=22.0, label="Beam"):
        L = math.hypot(xb - xa, yb - ya); yaw = math.degrees(math.atan2(yb - ya, xb - xa))
        s.put("Beam", (xa + xb) / 2, (ya + yb) / 2, z, yaw=yaw, scale=(L / 100.0, sz / 22.0, sz / 22.0), label=label)
    # ---------- composites (castle_level vocabulary) ----------
    def table_set(s, x, y, z, yaw, length, places=4, rich=False, rng=random):
        r = unreal.Rotator(roll=0, pitch=0, yaw=yaw)
        for k in range(places):
            side = 1 if k % 2 == 0 else -1; u = (k // 2 + 0.5) / max(1, (places + 1) // 2) - 0.5
            p = V(x, y, 0) + rotv(r, V(u * length * 0.8, side * 22, 0)); s.put("S:Plate", p.x, p.y, z, coll=False, label="Plate")
            q = V(x, y, 0) + rotv(r, V(u * length * 0.8 + 16, side * 26, 0)); s.put("Goblet" if rich else "Tankard", q.x, q.y, z, yaw=rng.uniform(0, 360), coll=False, label="Cup")
        s.put("BreadLoaf", x, y, z, yaw=yaw + rng.uniform(-20, 20), coll=False, label="Bread")
        c = V(x, y, 0) + rotv(r, V(length * 0.3, 0, 0)); s.put("Candles", c.x, c.y, z, coll=False, label="Candles")
        if rich:
            c = V(x, y, 0) + rotv(r, V(-length * 0.3, 0, 0)); s.put("Cheese", c.x, c.y, z, coll=False, label="Cheese")
            c = V(x, y, 0) + rotv(r, V(-length * 0.15, 4, 0)); s.put("AppleBasket", c.x, c.y, z, coll=False, label="Apples")
    def dining(s, x, y, yaw, kind="long", seats="bench", rich=False):
        tbl = "TableLong" if kind == "long" else "TableSmall"; L = 230 if kind == "long" else 120
        s.put(tbl, x, y, s.z, yaw=yaw, label="Table"); r = unreal.Rotator(roll=0, pitch=0, yaw=yaw)
        if seats == "bench":
            for side in (-1, 1):
                p = V(x, y, 0) + rotv(r, V(0, side * 62, 0)); s.put("Bench", p.x, p.y, s.z, yaw=yaw, scale=(1.0 if kind == "long" else 0.7, 1, 1), label="Bench")
        else:
            chairs = ["S:ChairA", "S:ChairB", "S:ChairC", "S:ChairWindsor"]; n = 3 if kind == "long" else 2
            for side in (-1, 1):
                for k in range(n):
                    u = (k + 0.5) / n - 0.5; p = V(x, y, 0) + rotv(r, V(u * L * 0.8, side * 58, 0))
                    s.put(chairs[(k + (side > 0)) % 4], p.x, p.y, s.z, yaw=yaw + (180 if side > 0 else 0) + random.uniform(-6, 6), label="Chair")
        s.table_set(x, y, s.z + 76, yaw, L, places=6 if kind == "long" else 4, rich=rich)
    def hearth(s, x, y, facing, cauldron=True):
        yaw = FACE[facing]; r = unreal.Rotator(roll=0, pitch=0, yaw=yaw)
        s.put("Fireplace", x, y, s.z, yaw=yaw, label="Fireplace")
        f = V(x, y, 0) + rotv(r, V(0, 120, 0)); s.fire_light(f.x, f.y, s.z + 125)
        if cauldron:
            c = V(x, y, 0) + rotv(r, V(0, 95, 0)); s.put("Tripod", c.x, c.y, s.z, yaw=yaw, label="Tripod"); s.put("Cauldron", c.x, c.y, s.z + 8, yaw=yaw, label="Cauldron")
        w = V(x, y, 0) + rotv(r, V(150, 20, 0)); s.put("Firewood", w.x, w.y, s.z, yaw=yaw + 90, label="Firewood")
    def bed(s, mesh, x, y, yaw, chest=True):
        """bed with its head toward local -Y rotated by yaw, chest at the foot (opens with F)"""
        r = unreal.Rotator(roll=0, pitch=0, yaw=yaw); s.put(mesh, x, y, s.z, yaw=yaw, label="Bed")
        if chest: c = V(x, y, 0) + rotv(r, V(0, 140, 0)); s.put("Chest", c.x, c.y, s.z, yaw=yaw + 180, label="BedChest")
    def storage(s, x, y, rng, n=6, spread=150):
        packs = ["SM_bag", "SM_bag_02", "SM_bag_03"]
        for k in range(n):
            px, py = x + rng.uniform(-spread, spread) * 0.5, y + rng.uniform(-spread, spread) * 0.5
            if k % 3 == 0: s.put(PACK("Small_props/" + rng.choice(("SM_barrel_01", "SM_barrel_02"))), px, py, s.z, yaw=rng.uniform(0, 360), label="Barrel")
            elif k % 3 == 1: s.put(PACK("Small_props/" + rng.choice(packs)), px, py, s.z, yaw=rng.uniform(0, 360), label="Sack")
            else: s.put(PACK("Small_props/SM_crate_group_01"), px, py, s.z, yaw=rng.choice((0, 90, 180)), label="Crates")
