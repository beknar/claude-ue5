"""castle_level interiors by building purpose (replaces 340's placeholder furniture; keeps its floors, doors, exposure volumes):
 tavern  (Cube_95, house_04)  taproom + bar + kegs + hearth, kitchen; upper floor: 2 guest rooms; attic storage
 manor   (Cube_094, house_04) great hall with long table, kitchen; upper floor: master + guest bedroom; attic storage
 home    (Cube_089 / Cube_90, house_03) hearth kitchen + dining; sleeping loft
 bakery  (Cube_075, house_02) bread ovens, kneading tables, flour, bread racks, counter; baker's loft
 stable  (Cube_91, house_01)  horse stalls, troughs, tack; hayloft
 barn    (Plane_039, house_01) cart, hay, tools, grain; hayloft
 storehouse (SM_house_01, house_01) racks of goods, barrels, crates, sacks, ledger desk; storage loft
 smithy  (SM_house_2, house_01) forge, anvil, quench tub, tools; smith's loft
House-local UE coords (x across, y along, z above the house base); kit props face +Y. Actors tagged 'castle_furn'.
Upper floors at F+300, attics at F+600 (stairs rise 300). Run after 340 (which rebuilds floors/doors)."""
import json, math, random, sys, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
CINE = "cine" in sys.argv                     # refurnish castle_level_Cine in place (then re-run 356 for the auto-opens)
assert ("castle_level_Cine." in w.get_path_name()) if CINE else ("castle_level." in w.get_path_name()), w.get_path_name()
TAGF, TAGG = unreal.Name("castle_furn"), unreal.Name("castle_gen")
OLD = {"TableTop", "TableLeg", "Bench", "BenchLeg", "BedFrame", "Pillow", "SM_barrel_group_01", "SM_crate_group_02", "SM_bag", "SM_bag_03",
       "InteriorLight", "InteriorFill"}
for a in eas.get_all_level_actors():
    lab = a.get_actor_label()
    if TAGF in a.tags or (TAGG in a.tags and (lab.split("_")[0] in OLD or lab in OLD or lab.endswith("_in") or lab.rstrip("0123456789") in OLD)):
        eas.destroy_actor(a)
PURPOSE = {"SM_models_Cube_95": "tavern", "SM_models_Cube_094": "manor", "SM_models_Cube_089": "home", "SM_models_Cube_90": "home",
           "SM_models_Cube_075": "bakery", "SM_models_Cube_91": "stable", "SM_models_Plane_039": "barn", "SM_house_01": "storehouse", "SM_house_2": "smithy"}
INFO = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\castle_interactive\interactive.json"))
CONT_BP = eal.load_blueprint_class("/Game/Castle/Interactive/Blueprints/BP_Container")
WARD_BP = eal.load_blueprint_class("/Game/Castle/Interactive/Blueprints/BP_Wardrobe")
KITH = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\castle_furniture\kit.json"))["_hinges"]
OPENABLE = {"Chest": "chest", "S:Trunk": "trunk", "Wardrobe": "wardrobe"}      # these always open (F)
_cache = {}
def M(p):
    if p not in _cache:
        _cache[p] = unreal.load_asset(p if p.startswith("/") else (f"/Game/Castle/Furniture/Kit/SM_Kit_{p}" if not p.startswith("S:") else f"/Game/Castle/Furniture/Scans/SM_Scan_{p[2:]}"))
        assert _cache[p] is not None, p
    return _cache[p]
PACK = lambda n: f"/Game/Medieval_Fantasy_Village/Meshes/{n}"
V = unreal.Vector
def rotv(rot, v): return unreal.MathLibrary.greater_greater_vector_rotator(v, rot)
FACE = {"+y": 0.0, "-y": 180.0, "+x": -90.0, "-x": 90.0}           # kit front (+Y) toward that local direction
SCAN_OFF = {"S:ChairWindsor": -90.0, "S:ChairB": -90.0, "S:ChairC": -90.0}   # scanned chairs face +X
class House:
    def __init__(s, actor, F):
        s.a = actor; s.tr = actor.get_actor_transform(); s.rot = actor.get_actor_rotation(); s.F = F; s.n = 0
    def openable(s, kind, x, y, z, yaw=0.0, label=None):
        """chests / trunks (BP_Container with a hinged lid) and wardrobes (BP_Wardrobe, two doors); kit origin = bottom centre"""
        rot = unreal.MathLibrary.compose_rotators(unreal.Rotator(roll=0, pitch=0, yaw=yaw), s.rot)
        loc = s.tr.transform_location(V(x, y, z))
        if kind == "wardrobe":
            a = eas.spawn_actor_from_class(WARD_BP, loc, rot)
        else:
            a = eas.spawn_actor_from_class(CONT_BP, loc, rot); key = "Chest" if kind == "chest" else "Trunk"; hg = KITH[key]
            c = {k.get_name(): k for k in a.get_components_by_class(unreal.SceneComponent)}
            c["Body"].set_static_mesh(M(f"{key}Body")); c["Lid"].set_static_mesh(M(f"{key}Lid"))
            c["Lid"].set_editor_property("relative_location", V(hg[0], -hg[1], hg[2])); c["Contents"].set_static_mesh(None)
            c["Prompt"].set_editor_property("relative_location", V(0, 0, hg[2] + 45))
            for th in (105.0, -105.0):
                if rotv(unreal.Rotator(roll=th, pitch=0, yaw=0), V(0, 1, 0)).z > 0: a.set_editor_property("OpenRoll", th); break
        a.tags = [TAGF]; a.set_actor_label(label or f"Open{kind.title()}"); a.set_folder_path("CastleFurn"); s.n += 1
        return a
    def put(s, mesh, x, y, z, yaw=0.0, scale=1.0, coll=True, label="Furn"):
        """bbox bottom-centre of `mesh` at local (x, y, z above base), local yaw (deg), uniform or xyz scale"""
        if mesh in OPENABLE: return s.openable(OPENABLE[mesh], x, y, z, yaw, label if label != "Furn" else None)
        sm = M(mesh); b = sm.get_bounding_box(); sc = V(scale, scale, scale) if isinstance(scale, (int, float)) else V(*scale)
        yaw = yaw + SCAN_OFF.get(mesh, 0.0)
        rl = unreal.Rotator(roll=0, pitch=0, yaw=yaw)
        off = rotv(rl, V(-(b.min.x + b.max.x) / 2 * sc.x, -(b.min.y + b.max.y) / 2 * sc.y, -b.min.z * sc.z))
        act = eas.spawn_actor_from_class(unreal.StaticMeshActor, s.tr.transform_location(V(x, y, z) + off), unreal.MathLibrary.compose_rotators(rl, s.rot))
        act.static_mesh_component.set_static_mesh(sm); act.set_actor_scale3d(sc)
        if not coll: act.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        act.tags = [TAGF]; act.set_actor_label(label); act.set_folder_path("CastleFurn"); s.n += 1
        return act
    def slab(s, x0, x1, y0, y1, top, th=12.0, label="LoftFloor"):
        """plank floor slab (pack floor planks) with its top at `top`"""
        nx, ny = max(1, int(round((x1 - x0) / 300))), max(1, int(round((y1 - y0) / 300)))
        for i in range(nx):
            for j in range(ny):
                s.put(PACK("Planks/SM_floor_plank"), x0 + (x1 - x0) * (i + 0.5) / nx, y0 + (y1 - y0) * (j + 0.5) / ny, top - th,
                      scale=((x1 - x0) / nx / 613.0 * 1.01, (y1 - y0) / ny / 303.0 * 1.01, th / 64.0), label=label)
    def beam(s, xa, ya, xb, yb, z, sz=22.0, label="Beam"):
        L = math.hypot(xb - xa, yb - ya); yaw = math.degrees(math.atan2(yb - ya, xb - xa))
        s.put("Beam", (xa + xb) / 2, (ya + yb) / 2, z, yaw=yaw, scale=(L / 100.0, sz / 22.0, sz / 22.0), label=label)
    def post(s, x, y, z0, z1, sz=22.0):
        sm = M("Beam")
        act = s.put("Beam", x, y, z0, yaw=0, scale=((z1 - z0) / 100.0, sz / 22.0, sz / 22.0), label="Post")
        act.set_actor_rotation(unreal.MathLibrary.compose_rotators(unreal.Rotator(roll=0, pitch=90, yaw=0), s.rot), False)
        act.set_actor_location(s.tr.transform_location(V(x, y, (z0 + z1) / 2)), False, False)
    def rail(s, xa, ya, xb, yb, z):
        L = math.hypot(xb - xa, yb - ya); n = max(1, int(round(L / 200))); yaw = math.degrees(math.atan2(yb - ya, xb - xa))
        for k in range(n):
            u = (k + 0.5) / n; s.put("Railing", xa + (xb - xa) * u, ya + (yb - ya) * u, z, yaw=yaw, scale=(L / n / 205.0, 1, 1), label="Railing")
    def wall(s, xa, ya, xb, yb, z, h, gaps=(), th=12.0):
        """partition wall along a line, with door gaps given as (from, to) distances along it"""
        L = math.hypot(xb - xa, yb - ya); yaw = math.degrees(math.atan2(yb - ya, xb - xa)); ux, uy = (xb - xa) / L, (yb - ya) / L
        cuts = [0.0] + [v for g in sorted(gaps) for v in g] + [L]
        for k in range(0, len(cuts), 2):
            a0, a1 = cuts[k], cuts[k + 1]
            if a1 - a0 < 5: continue
            m = (a0 + a1) / 2; s.put("Panel", xa + ux * m, ya + uy * m, z, yaw=yaw, scale=((a1 - a0) / 100.0, th / 100.0, h / 100.0), label="Partition")
        for g in gaps:                                                              # lintel + frame over each gap
            m = (g[0] + g[1]) / 2; s.put("Panel", xa + ux * m, ya + uy * m, z + 215, yaw=yaw, scale=((g[1] - g[0]) / 100.0, th / 100.0, (h - 215) / 100.0), label="Partition")
            s.put("Beam", xa + ux * m, ya + uy * m, z + 210, yaw=yaw, scale=((g[1] - g[0] + 20) / 100.0, (th + 6) / 22.0, 0.55), label="DoorFrame")
    def stairs(s, x, y_top, z0, toward="-y"):
        """stairs rising 300 from z0 toward `toward`, top edge at y_top; returns the footprint"""
        yaw = 0.0 if toward == "+y" else 180.0
        act = eas.spawn_actor_from_class(unreal.StaticMeshActor, s.tr.transform_location(V(x, y_top, z0)), unreal.MathLibrary.compose_rotators(unreal.Rotator(roll=0, pitch=0, yaw=yaw), s.rot))
        act.static_mesh_component.set_static_mesh(M("Stairs300")); act.tags = [TAGF]; act.set_actor_label("Stairs"); act.set_folder_path("CastleFurn"); s.n += 1
    def light(s, x, y, z, cd, color=(255, 216, 178), radius=900.0, label="RoomLight"):
        cd = cd * 0.6                                                        # interiors adapt their exposure (capped): keep lamps modest
        act = eas.spawn_actor_from_class(unreal.PointLight, s.tr.transform_location(V(x, y, z)), unreal.Rotator())
        lc = act.get_component_by_class(unreal.PointLightComponent)
        lc.set_editor_property("intensity", cd); lc.set_editor_property("attenuation_radius", radius); lc.set_editor_property("source_radius", 10.0)
        lc.set_editor_property("light_color", unreal.Color(r=color[0], g=color[1], b=color[2], a=255)); lc.set_editor_property("cast_shadows", True)
        lc.set_editor_property("volumetric_scattering_intensity", 0.0)            # the village fog smeared every lamp into a glowing streak
        act.tags = [TAGF]; act.set_actor_label(label); act.set_folder_path("CastleFurn"); return act
    def fire_light(s, x, y, z):
        act = s.light(x, y, z, 55.0, (255, 160, 85), 900.0, "FireLight")
        if act: act.get_component_by_class(unreal.PointLightComponent).set_editor_property("source_radius", 45.0)
    def container(s, kind, x, y, z, yaw=0.0):
        rec = INFO["containers"][kind]; D = "/Game/Castle/Interactive/Meshes"
        a = eas.spawn_actor_from_class(CONT_BP, s.tr.transform_location(V(x, y, z)), unreal.MathLibrary.compose_rotators(unreal.Rotator(roll=0, pitch=0, yaw=yaw), s.rot))
        c = {k.get_name(): k for k in a.get_components_by_class(unreal.SceneComponent)}
        c["Body"].set_static_mesh(unreal.load_asset(f"{D}/{kind}_body")); c["Lid"].set_static_mesh(unreal.load_asset(f"{D}/{kind}_lid"))
        c["Lid"].set_editor_property("relative_location", V(rec["hinge"][0], -rec["hinge"][1], rec["hinge"][2]))
        if rec["kind"] == "cyl": c["Contents"].set_static_mesh(unreal.load_asset(f"{D}/{kind}_liquid"))
        else:
            c["Contents"].set_static_mesh(unreal.load_asset(PACK("Small_props/SM_bag_03"))); c["Contents"].set_editor_property("relative_location", V(0, 0, 4))
            c["Contents"].set_editor_property("relative_scale3d", V(0.5, 0.5, 0.5))
        c["Prompt"].set_editor_property("relative_location", V(0, 0, rec["top"] + 30))
        for th in (105.0, -105.0):
            if rotv(unreal.Rotator(roll=th, pitch=0, yaw=0), V(0, 1, 0)).z > 0: a.set_editor_property("OpenRoll", th); break
        a.tags = [TAGF]; a.set_actor_label(f"Open_{kind[3:]}_furn"); a.set_folder_path("CastleFurn")
    # ---------- composite helpers ----------
    def table_set(s, x, y, z, yaw, length, places=4, rich=False, rng=random):
        """plates + tankards/goblets + bread on a table top at height z, table long axis along local yaw"""
        r = unreal.Rotator(roll=0, pitch=0, yaw=yaw)
        for k in range(places):
            side = 1 if k % 2 == 0 else -1; u = (k // 2 + 0.5) / max(1, (places + 1) // 2) - 0.5
            p = V(x, y, 0) + rotv(r, V(u * length * 0.8, side * 22, 0))
            s.put("S:Plate", p.x, p.y, z, coll=False, label="Plate")
            q = V(x, y, 0) + rotv(r, V(u * length * 0.8 + 16, side * 26, 0))
            s.put("Goblet" if rich else "Tankard", q.x, q.y, z, yaw=rng.uniform(0, 360), coll=False, label="Cup")
        s.put("BreadLoaf", x, y, z, yaw=yaw + rng.uniform(-20, 20), coll=False, label="Bread")
        c = V(x, y, 0) + rotv(r, V(length * 0.3, 0, 0)); s.put("Candles", c.x, c.y, z, coll=False, label="Candles")
        if rich:
            c = V(x, y, 0) + rotv(r, V(-length * 0.3, 0, 0)); s.put("Cheese", c.x, c.y, z, coll=False, label="Cheese")
            c = V(x, y, 0) + rotv(r, V(-length * 0.15, 4, 0)); s.put("AppleBasket", c.x, c.y, z, coll=False, label="Apples")
    def dining(s, x, y, yaw, kind="long", seats="bench", rich=False):
        tbl = "TableLong" if kind == "long" else "TableSmall"; L = 230 if kind == "long" else 120
        s.put(tbl, x, y, s.z, yaw=yaw, label="Table")
        r = unreal.Rotator(roll=0, pitch=0, yaw=yaw)
        if seats == "bench":
            for side in (-1, 1):
                p = V(x, y, 0) + rotv(r, V(0, side * 62, 0)); s.put("Bench", p.x, p.y, s.z, yaw=yaw, scale=(L / 230.0 * 1.0 if kind == "long" else 0.7, 1, 1), label="Bench")
        else:
            chairs = ["S:ChairA", "S:ChairB", "S:ChairC", "S:ChairWindsor"]
            n = 3 if kind == "long" else 2
            for side in (-1, 1):
                for k in range(n):
                    u = (k + 0.5) / n - 0.5; p = V(x, y, 0) + rotv(r, V(u * L * 0.8, side * 58, 0))
                    s.put(chairs[(k + (side > 0)) % 4], p.x, p.y, s.z, yaw=yaw + (180 if side > 0 else 0) + random.uniform(-6, 6), label="Chair")
        s.table_set(x, y, s.z + 76, yaw, L, places=6 if kind == "long" else 4, rich=rich)
    def hearth(s, x, y, facing, cauldron=True):
        """fireplace with its back on a wall, opening toward `facing`; cauldron on a tripod in front"""
        yaw = FACE[facing]; r = unreal.Rotator(roll=0, pitch=0, yaw=yaw)
        s.put("Fireplace", x, y, s.z, yaw=yaw, label="Fireplace")
        f = V(x, y, 0) + rotv(r, V(0, 120, 0)); s.fire_light(f.x, f.y, s.z + 125)      # out of the firebox: no blown-out stone next to the light
        if cauldron:
            c = V(x, y, 0) + rotv(r, V(0, 95, 0)); s.put("Tripod", c.x, c.y, s.z, yaw=yaw, label="Tripod"); s.put("Cauldron", c.x, c.y, s.z + 8, yaw=yaw, label="Cauldron")
        w = V(x, y, 0) + rotv(r, V(150, 20, 0)); s.put("Firewood", w.x, w.y, s.z, yaw=yaw + 90, label="Firewood")
    def bedroom(s, x0, x1, y0, y1, z, beds=("BedDouble",), wall="-y", rich=False):
        """beds against `wall` (head to wall), chest at the foot, plus washstand / wardrobe / candle"""
        yaw = {"-y": 0.0, "+y": 180.0, "-x": -90.0, "+x": 90.0}[wall]
        n = len(beds); span = (x1 - x0) if wall in ("-y", "+y") else (y1 - y0)
        for k, b in enumerate(beds):
            u = (k + 0.5) / n
            if wall in ("-y", "+y"):
                bx = x0 + span * u; by = (y0 + 110) if wall == "-y" else (y1 - 110)
                cx, cy = bx, by + (140 if wall == "-y" else -140)
            else:
                by = y0 + span * u; bx = (x0 + 110) if wall == "-x" else (x1 - 110)
                cx, cy = bx + (140 if wall == "-x" else -140), by
            s.put(b, bx, by, z, yaw=yaw, label="Bed")
            s.put("Chest", cx, cy, z, yaw=yaw + 180, label="BedChest")
        if wall in ("-y", "+y"):
            s.put("Washstand", x1 - 50, (y0 + y1) / 2, z, yaw=90, label="Washstand"); s.put("S:Jug", x1 - 40, (y0 + y1) / 2 + 12, z + 76, coll=False, label="Jug")
            s.put("Wardrobe", x0 + 70, (y1 if wall == "-y" else y0) - (40 if wall == "-y" else -40), z, yaw=yaw + 180, label="Wardrobe")
            s.put("S:SquareTable", x1 - 60, (y0 + 70) if wall == "-y" else (y1 - 70), z, scale=0.85, label="Nightstand")
            s.put("CandleStick", x1 - 60, (y0 + 70) if wall == "-y" else (y1 - 70), z + 42, coll=False, label="Candle")
        if rich: s.put("Rug", (x0 + x1) / 2, (y0 + y1) / 2 + (60 if wall == "-y" else -60), z + 0.5, yaw=0, coll=False, label="Rug")
        else: s.put("FurRug", (x0 + x1) / 2, (y0 + y1) / 2, z + 0.5, yaw=random.uniform(0, 30), coll=False, label="FurRug")
        s.light((x0 + x1) / 2, (y0 + y1) / 2, z + 220, 45.0, radius=700.0, label="BedroomLight")
    def storage(s, x, y, z, rng, n=6, spread=150):
        packs = ["SM_bag", "SM_bag_02", "SM_bag_03"]; scans = [PACK("Small_props/SM_barrel_01"), PACK("Small_props/SM_barrel_02")]     # scanned barrels render as a grey patchwork
        for k in range(n):
            px, py = x + rng.uniform(-spread, spread) * 0.5, y + rng.uniform(-spread, spread) * 0.5
            if k % 3 == 0: s.put(rng.choice(scans), px, py, z, yaw=rng.uniform(0, 360), label="Barrel")
            elif k % 3 == 1: s.put(PACK("Small_props/" + rng.choice(packs)), px, py, z, yaw=rng.uniform(0, 360), label="Sack")
            else: s.put(PACK("Small_props/SM_crate_group_01"), px, py, z, yaw=rng.choice((0, 90, 180)), label="Crates")
# ---------- layouts ----------
def upper_floor_house04(h, x0, x1, y0, y1, edge=250):
    """upper floor over y < edge, stairs on the +x wall (rail on the room side), gallery railing, beams + posts"""
    U = h.F + 300; h.slab(x0, x1, y0, edge, U)
    for yb in range(int(y0) + 150, int(edge), 260): h.beam(x0, yb, x1, yb, U - 34)
    for xp in (-380, 0, 380): h.post(xp, edge - 12, h.F, U - 12)
    h.beam(x0, edge - 12, x1, edge - 12, U - 34, label="EdgeBeam")
    h.stairs(x1 - 66, edge, h.F, toward="-y")
    h.rail(x0, edge - 4, x1 - 135, edge - 4, U)
    return U
def attic(h, x0, x1, y0, edge, U, rng):
    A = U + 300; h.slab(-285, 285, y0, edge, A, label="AtticFloor")
    h.stairs(200, edge, U, toward="-y")
    h.rail(-285, edge - 4, 135, edge - 4, A)
    h.put("S:Trunk", -180, y0 + 80, A, yaw=0); h.put("Chest", 0, y0 + 60, A, yaw=0)
    h.storage(-100, (y0 + edge) / 2, A, rng, n=7, spread=200)
    h.put("HayPile", 150, y0 + 150, A, scale=0.55, label="OldStraw"); h.put("S:ChairB", 60, edge - 120, A, yaw=150)
    h.put("S:WagonWheel", 230, y0 + 300, A, yaw=90, scale=0.7)
    h.light(0, (y0 + edge) / 2, A + 230, 25.0, radius=650.0, label="AtticLight")
def L_tavern(h, x0, x1, y0, y1, rng):
    h.z = h.F; edge = 250
    # taproom (double height), hearth on the far end wall
    h.hearth(0, y1 - 50, "-y", cauldron=False)
    for (tx, ty, kind, yaw, seats) in ((-300, 520, "long", 90, "bench"), (250, 520, "long", 90, "bench"), (-300, 860, "small", 0, "chairs"), (300, 860, "small", 0, "chairs")):
        h.dining(tx, ty, yaw, kind, seats)
    for tx, ty in ((0, 680),):
        h.put("S:RoundTable", tx, ty, h.z); h.put("Stool", tx - 55, ty, h.z); h.put("Stool", tx + 55, ty + 10, h.z)
        h.put("Tankard", tx - 10, ty, h.z + 52, coll=False); h.put("Tankard", tx + 14, ty + 6, h.z + 52, coll=False)
    h.put("Chandelier", -150, 700, h.F + 520, label="Chandelier"); h.put("Chandelier", 200, 700, h.F + 520, label="Chandelier")
    for ax, ay, yaw in ((x0 + 4, 600, -90), (x1 - 4, 760, 90)): h.put("S:Antlers", ax, ay, h.z + 230, yaw=yaw, scale=3.0, coll=False, label="Antlers")
    # bar under the gallery: counter facing the taproom, kegs + shelves behind
    for bx in (-200, -50, 100): h.put("S:BarCounter", bx, edge - 70, h.z, yaw=180, label="Bar")
    for k, bx in enumerate((-230, -130, -30, 70)):
        h.put("S:KegStand", bx, edge - 190, h.z, label="Keg")
    for k in range(5): h.put("Tankard", -230 + k * 60, edge - 70, h.z + 106, yaw=rng.uniform(0, 360), coll=False)
    h.put("ShelfRack", 260, edge - 230, h.z, yaw=0, label="BarShelf")
    for k in range(4): h.put("S:Jug", 230 + k * 20, edge - 230, h.z + 103, coll=False); h.put("Bowl", 230 + k * 20, edge - 230, h.z + 148, coll=False)
    # kitchen under the upper floor (y0 end): cooking hearth, oven, prep, pots, larder
    h.hearth(-150, y0 + 50, "+y", cauldron=True)
    h.put("BreadOven", 320, y0 + 110, h.z, yaw=0)
    h.put("PrepTable", -100, y0 + 330, h.z, yaw=0); h.put("PotRack", 150, y0 + 330, h.z, yaw=0)
    h.put("ShelfRack", x0 + 30, y0 + 300, h.z, yaw=-90)
    for k in range(3): h.put("Bowl", x0 + 30, y0 + 270 + k * 25, h.z + 103, coll=False); h.put("BreadRound", x0 + 30, y0 + 280 + k * 25, h.z + 58, coll=False)
    h.container("SM_barrel_02", x1 - 60, y0 + 330, h.z); h.container("SM_crate_01", x1 - 70, y0 + 430, h.z, 90)
    h.storage(x1 - 120, y0 + 560, h.z, rng, n=5)
    h.light(0, y0 + 300, h.F + 195, 70.0, label="KitchenLight"); h.light(0, 600, h.F + 450, 110.0, radius=1300, label="TaproomLight")
    U = upper_floor_house04(h, x0, x1, y0, y1, edge)
    # upper floor: two guest rooms + landing
    h.wall(x0, -560, x1, -560, U, 270, gaps=((520, 620),))
    h.bedroom(x0 + 20, x1 - 20, y0 + 10, -575, U, beds=("BedDouble",), wall="-y", rich=True)
    h.bedroom(x0 + 20, 100, -545, 160, U, beds=("BedSingle", "BedSingleGreen", "BedSingle"), wall="-x")     # guest dormitory
    h.light(-150, 20, U + 230, 40.0, label="LandingLight")
    attic(h, x0, x1, y0 + 10, -320, U, rng)          # attic edge pulled back: its stairs end 1.3 m inside the upper floor
def L_manor(h, x0, x1, y0, y1, rng):
    h.z = h.F; edge = 250
    h.hearth(0, y1 - 50, "-y", cauldron=False)
    h.put("Rug", 0, 640, h.z + 0.5, yaw=90, scale=(1.6, 1.3, 1), coll=False)
    for ty in (520, 760): h.dining(0, ty, 90, "long", "chairs", rich=True)
    h.put("Chandelier", 0, 640, h.F + 540)
    for ax, ay, yaw in ((x0 + 4, 500, -90), (x0 + 4, 820, -90), (x1 - 4, 660, 90)): h.put("S:Antlers", ax, ay, h.z + 240, yaw=yaw, scale=3.0, coll=False)
    h.put("Chest", x1 - 60, 900, h.z, yaw=90); h.put("S:Trunk", x0 + 70, 900, h.z, yaw=-90)
    h.put("Wardrobe", x1 - 45, 420, h.z, yaw=90, label="Cupboard")
    h.put("Firewood", x1 - 45, 640, h.z, yaw=90); h.put(PACK("Small_props/SM_barrel_02"), x1 - 45, 725, h.z)    # also covers plants rooted just outside the wall
    h.put(PACK("Small_props/SM_bag_02"), x1 - 50, 800, h.z, yaw=20)
    # kitchen
    h.hearth(-150, y0 + 50, "+y", cauldron=True); h.put("PrepTable", 150, y0 + 300, h.z); h.put("PotRack", -150, y0 + 330, h.z)
    h.put("ShelfRack", x1 - 30, y0 + 250, h.z, yaw=90)
    for k in range(4): h.put("S:Jug", x1 - 30, y0 + 210 + k * 25, h.z + 103, coll=False)
    h.container("SM_barrel_01", x0 + 60, y0 + 300, h.z); h.container("SM_crate_02", x0 + 60, y0 + 400, h.z, -90)
    h.storage(x0 + 120, y0 + 560, h.z, rng, n=5)
    h.light(0, y0 + 300, h.F + 195, 70.0, label="KitchenLight"); h.light(0, 640, h.F + 470, 120.0, radius=1300, label="HallLight")
    U = upper_floor_house04(h, x0, x1, y0, y1, edge)
    h.wall(x0, -520, x1, -520, U, 270, gaps=((520, 620),))
    h.bedroom(x0 + 20, x1 - 20, y0 + 10, -535, U, beds=("BedDouble",), wall="-y", rich=True)
    h.bedroom(x0 + 20, 100, -505, 160, U, beds=("BedSingle", "BedSingleGreen"), wall="-x", rich=True)       # guest bedroom
    h.light(-150, 20, U + 230, 40.0, label="LandingLight")
    attic(h, x0, x1, y0 + 10, -320, U, rng)
def loft_house03(h, x0, x1, y0, y1, edge=-20):
    U = h.F + 300; h.slab(x0, x1, y0, edge, U)
    for yb in (y0 + 140, y0 + 330): h.beam(x0, yb, x1, yb, U - 34)
    for xp in (-150, 300): h.post(xp, edge - 12, h.F, U - 12)
    h.beam(x0, edge - 12, x1, edge - 12, U - 34, label="EdgeBeam")
    h.stairs(x0 + 66, edge, h.F, toward="-y")
    h.rail(x0 + 135, edge - 4, x1, edge - 4, U)
    return U
def L_home(h, x0, x1, y0, y1, rng):
    h.z = h.F
    h.hearth(0, y1 - 50, "-y", cauldron=True)                                      # hearth on the end wall near the door
    h.put("PotRack", -280, y1 - 60, h.z, yaw=180); h.put("PrepTable", 300, y1 - 230, h.z, yaw=90)
    h.put("S:Bucket", 330, y1 - 340, h.z); h.put("S:Jug", 300, y1 - 230, h.z + 89, coll=False)
    h.dining(60, -230, 0, "small", "chairs")                                      # family table under the loft
    h.put("ShelfRack", x1 - 30, -300, h.z, yaw=90)
    for k in range(3): h.put("Bowl", x1 - 30, -330 + k * 28, h.z + 58, coll=False); h.put("S:Plate", x1 - 30, -330 + k * 28, h.z + 103, coll=False)
    h.container("SM_barrel_02", x1 - 60, y0 + 60, h.z); h.container("SM_crate_02", x1 - 160, y0 + 50, h.z)
    h.put(PACK("Small_props/SM_bag_02"), x0 + 200, y0 + 60, h.z); h.put("AppleBasket", x0 + 290, y0 + 60, h.z, coll=False)
    h.put("Bench", -150, 250, h.z, yaw=90); h.put("Stool", 150, 220, h.z)
    h.light(0, 150, h.F + 260, 60.0, label="HomeLight"); h.light(0, -250, h.F + 180, 35.0, label="DiningLight")
    U = loft_house03(h, x0, x1, y0, y1)
    h.bedroom(x0 + 140, x1 - 10, y0 + 10, -35, U, beds=("BedDouble", "BedSingle", "BedSingleGreen"), wall="-y")
def L_bakery(h, x0, x1, y0, y1, rng):
    h.z = h.F
    h.put("BreadOven", -250, y1 - 105, h.z, yaw=180); h.put("BreadOven", 120, y1 - 105, h.z, yaw=180)
    h.fire_light(-70, y1 - 300, h.z + 140)
    h.put("Firewood", 380, y1 - 60, h.z, yaw=90); h.put("Firewood", 380, y1 - 140, h.z, yaw=90)
    for tx, ty in ((-200, 120), (150, 120)):
        h.put("PrepTable", tx, ty, h.z, yaw=0)
        for k in range(4): h.put("BreadLoaf", tx - 45 + k * 30, ty - 20, h.z + 80, yaw=rng.uniform(-15, 15), coll=False)
    for k, ry in enumerate((-80, -260)):
        h.put("ShelfRack", x1 - 30, ry, h.z, yaw=90)
        for lvl in (11, 58, 103, 148):
            for j in range(3): h.put("BreadRound" if (j + lvl) % 2 else "BreadLoaf", x1 - 30, ry - 40 + j * 40, h.z + lvl, yaw=90, coll=False)
    for k in range(7): h.put(PACK("Small_props/" + ("SM_bag" if k % 2 else "SM_bag_03")), x0 + 70 + (k % 3) * 55, y0 + 340 + (k // 3) * 60, h.z, yaw=rng.uniform(0, 360))
    h.container("SM_barrel_01", x0 + 60, 200, h.z); h.container("SM_barrel_02", x0 + 60, 300, h.z)
    h.put("S:SquareTable", 420, 330, h.z, scale=1.2); h.put("AppleBasket", 420, 330, h.z + 60, coll=False); h.put("BreadRound", 400, 320, h.z + 60, coll=False)
    h.light(0, 100, h.F + 260, 70.0, label="BakeryLight")
    U = loft_house03(h, x0, x1, y0, y1)
    h.bedroom(x0 + 140, x1 - 10, y0 + 10, -35, U, beds=("BedSingle",), wall="-y")
    h.put("TableSmall", 250, -150, U, yaw=90); h.put("S:ChairWindsor", 180, -150, U, yaw=90); h.put("CandleStick", 250, -150, U + 76, coll=False)
    h.storage(-150, -250, U, rng, n=4, spread=120)
def loft_house01(h, x0, x1, y0, y1, edge=300):
    """loft over y > edge, stairs on the -x wall climbing toward +y (rail on the room side)"""
    U = h.F + 300; h.slab(x0, x1, edge, y1, U)
    for yb in range(edge + 150, int(y1), 260): h.beam(x0, yb, x1, yb, U - 34)
    for xp in (-300, 100, 450): h.post(xp, edge + 12, h.F, U - 12)
    h.beam(x0, edge + 12, x1, edge + 12, U - 34, label="EdgeBeam")
    h.stairs(x0 + 66, edge, h.F, toward="+y")
    h.rail(x0 + 135, edge + 4, x1, edge + 4, U)
    return U
def hayloft(h, x0, x1, edge, y1, U, rng):
    for k in range(10):
        h.put("HayBale", rng.uniform(x0 + 80, x1 - 80), rng.uniform(edge + 300, y1 - 60), U + (43 if k > 6 else 0), yaw=rng.choice((0, 90)) + rng.uniform(-8, 8))
    h.put("HayPile", 0, y1 - 250, U, scale=1.2); h.put("HayPile", -250, y1 - 150, U, scale=0.9)
    h.put("Pitchfork", x1 - 30, edge + 200, U, yaw=0, coll=False)
    h.light(0, (edge + y1) / 2, U + 230, 30.0, radius=800, label="LoftLight")
def L_stable(h, x0, x1, y0, y1, rng):
    h.z = h.F
    for side, wx in ((-1, x0), (1, x1)):                                         # 3 stalls per side along y0 end
        for k in range(4):
            py = y0 + k * 210
            h.put("StallPartition", wx - side * 150, py, h.z, yaw=0, scale=(0.97, 1, 1), label="Stall")
        for k in range(3):
            cy = y0 + 105 + k * 210
            h.put("Trough", wx - side * 40, cy, h.z, yaw=90, label="Trough"); h.put("HayPile", wx - side * 160, cy, h.z, scale=0.45, label="StallHay")
            h.put("S:Bucket", wx - side * 260, cy + 60, h.z)
    h.put("Beam", x0 + 8, -60, h.z + 120, yaw=90, scale=(2.5, 1, 1), label="SaddleRack")
    for k in range(3): h.put("S:Saddle", x0 + 30, -150 + k * 60, h.z + 131, yaw=90, coll=False)
    for k in range(4): h.put("S:Horseshoe", x1 - 3, -200 + k * 25, h.z + 180, yaw=90, coll=False, label="Horseshoe")
    h.put("S:WagonWheel", x1 - 40, 80, h.z, yaw=90, label="Wheel"); h.put("Chest", x0 + 60, 100, h.z, yaw=-90, label="TackChest")
    for k in range(6): h.put("HayBale", -200 + (k % 3) * 100, 200 + (k // 3) * 55, h.z, yaw=rng.uniform(-6, 6))
    h.container("SM_barrel_02", 300, 200, h.z)
    h.light(0, y0 + 300, h.F + 280, 55.0, label="StableLight"); h.light(0, 100, h.F + 280, 45.0, label="StableLight2")
    U = loft_house01(h, x0, x1, y0, y1); hayloft(h, x0, x1, 300, y1, U, rng)
    for k in range(4): h.put("HayBale", -150 + k * 100, 650 + (k % 2) * 60, h.z, yaw=rng.uniform(-8, 8))
def L_barn(h, x0, x1, y0, y1, rng):
    h.z = h.F
    h.put("Cart", 100, y0 + 330, h.z, yaw=90)
    for k in range(14): h.put("HayBale", rng.uniform(x0 + 80, -150), rng.uniform(y0 + 80, y0 + 520), h.z + (43 if k > 8 else 0), yaw=rng.choice((0, 90)) + rng.uniform(-6, 6))
    h.put("HayPile", 300, y0 + 650, h.z, scale=1.0)
    for k, t in enumerate(("Pitchfork", "Rake", "Shovel")): h.put(t, x1 - 15, -120 + k * 40, h.z, yaw=90, coll=False)
    h.put("S:WagonWheel", x1 - 40, 120, h.z, yaw=90); h.put("S:WagonWheel", x1 - 70, 230, h.z, yaw=80)
    h.put("Trough", 0, 120, h.z); h.put("S:Bucket", 90, 140, h.z)
    for k in range(8): h.put(PACK("Small_props/" + ("SM_bag" if k % 2 else "SM_bag_02")), x0 + 70 + (k % 4) * 60, 150 + (k // 4) * 60, h.z, yaw=rng.uniform(0, 360))
    h.container("SM_barrel_01", x0 + 60, 50, h.z); h.container("SM_crate_01", x0 + 70, -40, h.z, -90)
    h.light(0, y0 + 400, h.F + 300, 60.0, label="BarnLight"); h.light(0, 150, h.F + 280, 40.0, label="BarnLight2")
    U = loft_house01(h, x0, x1, y0, y1); hayloft(h, x0, x1, 300, y1, U, rng)
    h.put("Ladder", 200, 320, h.F, yaw=0, coll=False)
def L_storehouse(h, x0, x1, y0, y1, rng):
    h.z = h.F
    for row in range(3):                                                        # aisles of racks
        ry = y0 + 150 + row * 230
        for k in range(4):
            rx = x0 + 120 + k * 140
            h.put("ShelfRack", rx, ry, h.z, yaw=0)
            for lvl in (11, 58, 103):
                h.put(PACK("Small_props/" + rng.choice(("SM_bag_02", "SM_bag_03", "SM_crate_02"))), rx + rng.uniform(-25, 25), ry, h.z + lvl, yaw=rng.uniform(0, 360), coll=False)
            h.put(PACK("Small_props/SM_barrel_02"), rx + 30, ry, h.z + 148, scale=0.55, coll=False)
    for k in range(8): h.put(PACK("Small_props/" + rng.choice(("SM_barrel_01", "SM_barrel_02"))), x1 - 60, y0 + 80 + k * 75, h.z, yaw=rng.uniform(0, 360))
    for k in range(4): h.put(PACK("Small_props/SM_crate_group_02"), x1 - 220, y0 + 120 + k * 150, h.z, yaw=rng.choice((0, 90)))
    h.put("TableSmall", 0, 120, h.z, yaw=0); h.put("S:ChairA", 0, 70, h.z, yaw=0); h.put("S:Book", 10, 125, h.z + 76, yaw=90, coll=False)
    h.put("CandleStick", -40, 120, h.z + 76, coll=False); h.put("Chest", 120, 160, h.z, yaw=180)
    h.container("SM_crate_01", -250, 100, h.z); h.container("SM_crate_02", -250, 180, h.z); h.container("SM_barrel_02", -350, 140, h.z)
    h.light(0, y0 + 350, h.F + 300, 60.0, label="StoreLight"); h.light(0, 130, h.F + 250, 40.0, label="DeskLight")
    U = loft_house01(h, x0, x1, y0, y1)
    h.storage(-150, 650, U, rng, n=10, spread=500); h.put("S:Trunk", 300, y1 - 70, U, yaw=180)
    h.light(0, 650, U + 230, 30.0, radius=800, label="LoftLight")
def L_smithy(h, x0, x1, y0, y1, rng):
    h.z = h.F
    h.put("Forge", 0, y0 + 75, h.z, yaw=0); h.fire_light(0, y0 + 230, h.z + 150)
    h.put("Anvil", 30, y0 + 260, h.z, yaw=90); h.put("QuenchTub", 170, y0 + 230, h.z)
    h.put("ToolBoard", x1 - 3, y0 + 200, h.z + 100, yaw=90, coll=False); h.put("ToolBoard", x0 + 3, y0 + 200, h.z + 100, yaw=-90, coll=False)
    h.put("PrepTable", -260, y0 + 260, h.z, yaw=90, label="Workbench")
    h.put("Firewood", -250, y0 + 60, h.z, yaw=0); h.put(PACK("Small_props/SM_bag"), 250, y0 + 60, h.z, label="CoalSack")
    for k in range(4): h.put("S:Horseshoe", x0 + 3, y0 + 380 + k * 22, h.z + 170, yaw=-90, coll=False)
    h.put("S:WagonWheel", x1 - 40, y0 + 450, h.z, yaw=90); h.put("S:Bucket", 220, y0 + 330, h.z)
    h.container("SM_barrel_01", x1 - 60, -50, h.z); h.container("SM_crate_01", x1 - 70, 50, h.z, 90)
    h.put("TableSmall", 0, 100, h.z, yaw=0); h.put("Stool", -40, 50, h.z); h.put("Tankard", 10, 100, h.z + 76, coll=False); h.put("BreadLoaf", -20, 110, h.z + 76, coll=False)
    h.light(0, y0 + 350, h.F + 280, 50.0, label="SmithyLight")
    U = loft_house01(h, x0, x1, y0, y1)
    h.bedroom(x0 + 20, x1 - 20, 330, y1 - 10, U, beds=("BedSingle",), wall="+y")
    h.put("TableSmall", 200, 500, U, yaw=0); h.put("S:ChairB", 200, 450, U, yaw=0); h.put("CandleStick", 230, 500, U + 76, coll=False)
LAYOUT = {"tavern": L_tavern, "manor": L_manor, "home": L_home, "bakery": L_bakery, "stable": L_stable, "barn": L_barn, "storehouse": L_storehouse, "smithy": L_smithy}
RECT = {"SM_house_04": (-598, 595, -1040, 1040), "SM_house_03": (-609, 595, -510, 510), "SM_house_02": (-609, 595, -510, 510), "SM_house_01": (-596, 595, -1040, 1040)}
report = []
for a in eas.get_all_level_actors():
    lab = a.get_actor_label()
    if lab not in PURPOSE or not isinstance(a, unreal.StaticMeshActor): continue
    hname = a.static_mesh_component.static_mesh.get_name().replace("_open", "")
    tr = a.get_actor_transform(); base = a.get_actor_location().z
    tops = [act.get_actor_bounds(False) for act in eas.get_all_level_actors() if TAGG in act.tags and act.get_actor_label() == "Floor"
            and (act.get_actor_location() - a.get_actor_location()).length() < 1500]
    tops = [o.z + e.z - base for o, e in tops]
    F = max(tops) if tops else 18.0
    h = House(a, F); rng = random.Random(len(lab) * 97 + int(F))
    x0, x1, y0, y1 = RECT[hname]
    LAYOUT[PURPOSE[lab]](h, x0, x1, y0, y1, rng)
    for pv in eas.get_all_level_actors():                                       # exposure volume covers every level now
        if TAGG in pv.tags and pv.get_actor_label() == "InteriorExposure" and (pv.get_actor_location() - a.get_actor_location()).length() < 900:
            loc = tr.transform_location(V((x0 + x1) / 2, (y0 + y1) / 2, F + 600)); pv.set_actor_location(loc, False, False)
            sc = pv.get_actor_scale3d(); pv.set_actor_scale3d(V(sc.x, sc.y, 1300.0 / 200.0))
            ps = pv.settings                                                      # modest adaptation, no bloom/flare streaks indoors
            for k, v in (("auto_exposure_bias", 0.0), ("auto_exposure_max_brightness", 0.5), ("auto_exposure_min_brightness", -1.5), ("bloom_intensity", 0.15), ("lens_flare_intensity", 0.0)):
                ps.set_editor_property("override_" + k, True); ps.set_editor_property(k, v)
            pv.set_editor_property("settings", ps)
    report.append(f"{lab:22s} {PURPOSE[lab]:10s} floor +{F:.0f}  pieces {h.n}")
print("\n".join(report))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level(); print("saved")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
