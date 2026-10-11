"""sf-city-level structures with real interiors and automatic sci-fi blast doors (BP_SciFiDoor, 705: rises into the wall as
she approaches). Built from world-aligned city-texture boxes (704) + props from the Red_Echo / Diner / MC_Environment /
SilentZone / Mega_City packs, using interior_lib (frame: origin = front facade centre at ground level, +Y into the building).
  dock (city, beside the road head):  S1 Port Authority  - front office + armory (inner door)
                                      S2 Neon noodle bar  - one hall, neon bar counter, booths, kitchen line
                                      S3 Hab apartment    - living room + bedroom (inner door)
  Monolith plaza:                     S4 Excavation lab   - lab with a monolith relic + server room (inner door)
Each room: lining walls / ceiling, ceiling light panels + lights, capped-exposure post-process volume.
Actors tagged 'sfc_struct' (persistent level). Writes SourceArt/sf_city/structures.json (frames, rooms, door positions)."""
import json, math, sys, unreal
sys.path.insert(0, r"E:\code\claude-ue5\pipeline\unreal")
import importlib, interior_lib as IL; importlib.reload(IL)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert w.get_path_name().startswith("/Game/SFCityLevel/Maps/sf-city-level."), w.get_path_name()
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_current_level_by_name("sf-city-level")
TAG = "sfc_struct"; SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\sf_city"
print("cleared", IL.clear(TAG))
MAT = lambda n: f"/Game/SFCityLevel/Materials/{n}"
DOOR_BP = unreal.EditorAssetLibrary.load_blueprint_class("/Game/SFCityLevel/Blueprints/BP_SciFiDoor")
FABRIC = "/Game/Mega_City/Materials/Unique_textures/MI_fabric"
PROPS = {   # key: (mesh, its front axis)
    "console": ("/Game/Red_Echo/Meshes/Computer/SM_computer_01", "+y"), "console_low": ("/Game/Red_Echo/Meshes/Computer/SM_top_computer", "+y"),
    "chair": ("/Game/Red_Echo/Meshes/Chair/SM_chair", "+y"), "re_table": ("/Game/Red_Echo/Meshes/Table/SM_table", "+y"),
    "circ_crate": ("/Game/Red_Echo/Meshes/Crates/SM_circular_crate", "+y"), "re_crate1": ("/Game/Red_Echo/Meshes/Crates/SM_crate_01", "+y"),
    "re_crate2": ("/Game/Red_Echo/Meshes/Crates/SM_crate_02", "+y"), "jug": ("/Game/Red_Echo/Meshes/Kitchen_props/SM_jug", "+y"),
    "tray": ("/Game/Red_Echo/Meshes/Kitchen_props/SM_tray", "+y"),
    "booth": ("/Game/Diner/Meshes/Blocking/SM_chair", "-y"), "bar": ("/Game/Diner/Meshes/Blocking/SM_bar", "+y"),
    "stool": ("/Game/Diner/Meshes/Blocking/SM_stool", "+y"), "d_table": ("/Game/Diner/Meshes/Blocking/SM_table", "+y"),
    "stove": ("/Game/Diner/Meshes/Blocking/SM_kitchen_01", "+y"), "counter": ("/Game/Diner/Meshes/Blocking/SM_kitchen_02", "+y"),
    "counter_s": ("/Game/Diner/Meshes/Blocking/SM_kitchen_03", "+y"), "hood": ("/Game/Diner/Meshes/Blocking/SM_hood", "+y"),
    "pendant": ("/Game/Diner/Meshes/Blocking/SM_lamp_02", "+y"), "plate": ("/Game/Diner/Meshes/SM_plate", "+y"),
    "glass": ("/Game/Diner/Meshes/Blocking/SM_glass", "+y"), "pot": ("/Game/Diner/Meshes/Blocking/SM_pot", "+y"),
    "locker": ("/Game/MC_Environment/Assets/SM_ventilated_locker", "+x"), "wardrobe": ("/Game/MC_Environment/Assets/SM_ClothesCabinet", "+x"),
    "shelves": ("/Game/MC_Environment/Assets/SM_MetalShelves", "+x"), "mc_table": ("/Game/MC_Environment/Assets/SM_Table", "+x"),
    "mil_crate": ("/Game/MC_Environment/Assets/SM_MilitaryCrate_01", "+y"), "radio": ("/Game/MC_Environment/Assets/SM_MilitaryRadio", "+y"),
    "generator": ("/Game/MC_Environment/Assets/SM_Generator_01", "+y"), "extinguisher": ("/Game/MC_Environment/Assets/SM_FireExtinguisher", "+x"),
    "steel_cab": ("/Game/SilentZonePack/Assets/SM/SM_Steel_Cabinet_01a", "+y"), "bench": ("/Game/Mega_City/Meshes/Bench/SM_bench", "+y"),
    "city_crate": ("/Game/Mega_City/Meshes/Crates/SM_crate_07", "+y"), "city_crate_big": ("/Game/Mega_City/Meshes/Crates/SM_crate_02", "+y"),
    "sign_neon": ("/Game/Mega_City/Meshes/Signs/SM_sign_02", "+y"), "stone": ("/Game/Monolith_megastructure/Meshes/Stones/SM_stone_03", "+y"),
    "stone_s": ("/Game/Monolith_megastructure/Meshes/Stones/SM_stone_04", "+y"),
}
ANG = {"+x": 0.0, "+y": 90.0, "-x": 180.0, "-y": -90.0}
def P(r, key, x, y, facing, z=None, scale=1.0, coll=True, label=None):
    mesh, front = PROPS[key]
    return r.put(mesh, x, y, r.z if z is None else z, yaw=ANG[facing] - ANG[front], scale=scale, coll=coll, label=label or key)
def ground(x, y):
    h = unreal.SystemLibrary.line_trace_single(w, V(x, y, 3000), V(x, y, -2000), unreal.TraceTypeQuery.ECC_VISIBILITY, False, [], unreal.DrawDebugTrace.NONE, True)
    return h.to_tuple()[4].z if h else None
FT, CEIL, TH, DW, DH = 3.0, 450.0, 30.0, 210.0, 262.0        # floor top (near flush: a 10 cm sill caught her toes), ceiling, wall thickness, doorway w / h
OUT = []
def glow(r, x, y, z, sx, sy, sz, color="Cyan", label="Glow"):
    a = r.box(x, y, z, sx, sy, sz, label=label, mat=MAT(f"MI_SFC_Glow{color}")); a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    a.static_mesh_component.set_editor_property("cast_shadow", False); return a
def door(r, x, yc, label):
    a = eas.spawn_actor_from_class(DOOR_BP, r.W(x, yc, r.z), r.R(0.0)); r._fin(a, label)
    return a
def wall_with_doors(r, xa, xb, yc, z0, z1, doors, mat, label):
    """wall along X from xa to xb centred on y = yc, thickness TH, from z0 to z1, with doorway gaps (x centres)"""
    cuts = [xa]
    for dx in sorted(doors): cuts += [dx - DW / 2, dx + DW / 2]
    cuts.append(xb)
    for k in range(0, len(cuts), 2):
        if cuts[k + 1] - cuts[k] > 2: r.box((cuts[k] + cuts[k + 1]) / 2, yc, z0, cuts[k + 1] - cuts[k], TH, z1 - z0, label=label, mat=mat)
    for dx in doors: r.box(dx, yc, r.z + DH, DW, TH, z1 - (r.z + DH), label=label + "Lintel", mat=mat)
def door_trim(r, x, yc, side, color="Cyan"):
    """glowing jambs + header on one face (side = -1 front face / +1 back face) of a wall centred at yc"""
    yf = yc + side * (TH / 2 + 1.5)
    for sx in (-1, 1): glow(r, x + sx * (DW / 2 + 6), yf, r.z, 8, 3, DH + 8, color, "DoorJamb")
    glow(r, x, yf, r.z + DH + 4, DW + 20, 3, 6, color, "DoorHeader")
def facade(r, W, D, H, fd, accent):
    """exterior detail, all above head height or on the roof (no collision): lit window bands on the front and both sides,
    a glowing sign plate over the door, wall-mounted AC units, a roof antenna"""
    zb, zt = 320.0, 420.0
    for xa, xb in ((-W / 2 + 70, fd - 170), (fd + 170, W / 2 - 70)):
        if xb - xa > 120:
            a = r.box((xa + xb) / 2, -4, zb, xb - xa, 8, zt - zb, label="WindowBand", mat=MAT("MI_SFC_WallDark")); a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            for z in (zb - 4, zt): glow(r, (xa + xb) / 2, -9, z, xb - xa, 3, 4, "White", "WindowGlow")
    for sx in (-1, 1):
        a = r.box(sx * (W / 2 + 4), D / 2, zb, 8, D - 160, zt - zb, label="WindowBand", mat=MAT("MI_SFC_WallDark")); a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        for z in (zb - 4, zt): glow(r, sx * (W / 2 + 9), D / 2, z, 3, D - 160, 4, "White", "WindowGlow")
        r.put("/Game/Mega_City/Meshes/House_detail/SM_house_detail_01", sx * (W / 2 + 47), D * 0.78, 210, yaw=-90 * sx, coll=False, label="ACUnit")
    glow(r, fd, -11, DH + 30, 260, 4, 24, accent, "DoorSign")
    r.put("/Game/Mega_City/Meshes/Antennas/SM_antenna_02", W * 0.3, D * 0.65, H + 35, coll=False, label="Antenna")
def structure(name, cx, cy, inward, W, D, H, rooms, front_door, ext_mat, accent):
    """rooms: list of (purpose, y0, y1); consecutive rooms share a partition at their boundary with a door at the given x
    (rooms[k] = (purpose, y0, y1, door_x_into_next or None))"""
    gz = ground(cx, cy); assert gz is not None, name + ": no ground"
    fr = IL.door_frame(unreal.Transform(), (cx, cy), gz, inward)
    r = IL.Room(fr, FT, TAG, f"SFC/Structures/{name}")
    r.box(0, D / 2, -60, W, D, 60 + FT, label="FloorSlab", mat=MAT("MI_SFC_Floor"))        # top at FT, sunk 60 into the ground
    wall_with_doors(r, -W / 2, W / 2, TH / 2, -60, H, [front_door], MAT(ext_mat), "FrontWall")
    r.box(0, D - TH / 2, -60, W, TH, H + 60, label="BackWall", mat=MAT(ext_mat))
    for sx in (-1, 1): r.box(sx * (W / 2 - TH / 2), D / 2, -60, TH, D - 2 * TH, H + 60, label="SideWall", mat=MAT(ext_mat))
    r.box(0, D / 2, H, W + 80, D + 80, 35, label="Roof", mat=MAT("MI_SFC_WallDark"))
    glow(r, 0, -41, H + 8, W + 82, 3, 10, accent, "RoofNeon")                                 # neon line along the front roof edge
    for sx in (-1, 1): glow(r, sx * (W / 2 + 2), -2, 0, 6, 6, H, accent, "CornerNeon")
    facade(r, W, D, H, front_door, accent)
    door(r, front_door, TH / 2, f"{name}_FrontDoor"); door_trim(r, front_door, TH / 2, -1, accent)
    info = {"name": name, "frame": [fr.translation.x, fr.translation.y, fr.translation.z, fr.rotation.rotator().yaw], "rooms": [],
            "doors": [[list(r.W(front_door, -150, FT).to_tuple()), list(r.W(front_door, TH / 2, FT).to_tuple()), list(r.W(front_door, 150, FT).to_tuple())]]}
    x0, x1 = -W / 2 + TH, W / 2 - TH
    for k, (purpose, y0, y1, dnext) in enumerate(rooms):
        ry0 = y0 + (TH if k == 0 else TH / 2); ry1 = y1 - (TH if k == len(rooms) - 1 else TH / 2)
        doors = []
        if k == 0: doors.append(("-y", front_door, DW, DH))
        else: doors.append(("-y", rooms[k - 1][3], DW, DH))
        if dnext is not None:
            doors.append(("+y", dnext, DW, DH))
            wall_with_doors(r, x0, x1, y1, -10, H, [dnext], MAT("MI_SFC_WallDark"), "Partition")
            door(r, dnext, y1, f"{name}_InnerDoor"); door_trim(r, dnext, y1, -1, accent); door_trim(r, dnext, y1, 1, accent)
            info["doors"].append([list(r.W(dnext, y1 - 150, FT).to_tuple()), list(r.W(dnext, y1, FT).to_tuple()), list(r.W(dnext, y1 + 150, FT).to_tuple())])
        r.line(x0 + 2, x1 - 2, ry0 + 2, ry1 - 2, CEIL, doors=doors, th=4.0, ceiling=False, mat=MAT("MI_SFC_WallPanel"), label="Lining")
        r.box((x0 + x1) / 2, (ry0 + ry1) / 2, r.z + CEIL, x1 - x0 + 4, ry1 - ry0 + 4, 14, label="Ceiling", mat=MAT("MI_SFC_Ceiling"))
        n_l = max(1, int(round((x1 - x0) / 450)))
        for i in range(n_l):                                                              # ceiling light panels + lights
            lx = x0 + (x1 - x0) * (i + 0.5) / n_l; ly = (ry0 + ry1) / 2
            glow(r, lx, ly, r.z + CEIL - 6, 160, min(90, (ry1 - ry0) * 0.3), 4, "White", "CeilingPanel")
            r.light(lx, ly, r.z + CEIL - 40, 38.0, (225, 235, 255), radius=900.0, label="RoomLight")
        r.exposure(x0, x1, ry0, ry1, -20, CEIL + 40)
        vx, vy = VISIT.get(purpose, ((x0 + x1) / 2, (ry0 + ry1) / 2))                         # a free spot in the room for the walk test
        info["rooms"].append({"purpose": purpose, "box": [x0, x1, ry0, ry1], "centre": list(r.W(vx, vy, FT).to_tuple())})
        FURNISH[purpose](r, x0, x1, ry0, ry1)
    OUT.append(info); print(f"{name}: {r.n} actors, ground {gz:.0f}")
    return r
# ---------------- furnishing (room-local: x0..x1 across, y0 (front) .. y1 (back)) ----------------
def f_office(r, x0, x1, y0, y1):
    for cx in (x0 + 260, x0 + 620):                                                    # consoles against the back wall, screens into the room
        P(r, "console", cx, y1 - 75, "-y", label="Console"); P(r, "chair", cx, y1 - 230, "+y", label="OperatorChair")
    for k in range(2): P(r, "locker", x0 + 50, y0 + 110 + k * 152, "+x", label="Locker")
    glow(r, x0 + 3, y0 + 430, r.z + 150, 4, 200, 110, "Cyan", "WallScreen")
    P(r, "shelves", x1 - 55, (y0 + y1) / 2 + 40, "-x", label="Shelves")
    P(r, "bench", 200, y0 + 60, "+y", label="WaitingBench")
    P(r, "city_crate", x1 - 100, y0 + 80, "+y", label="Crate"); P(r, "re_crate2", x1 - 100, y0 + 190, "+y", label="Crate")
    P(r, "extinguisher", x0 + 12, y1 - 30, "+x", z=r.z + 80, label="Extinguisher")
def f_armory(r, x0, x1, y0, y1):
    for k in range(4): P(r, "locker", x0 + 110 + k * 152, y1 - 50, "-y", label="ArmoryLocker")
    cy = (y0 + y1) / 2
    P(r, "mc_table", 0, cy, "+y", label="Table"); P(r, "radio", 0, cy, "+y", z=r.z + 93, label="Radio", coll=False)
    for k in range(2): P(r, "mil_crate", x1 - 80, y0 + 60 + k * 70, "-x", label="AmmoCrate")
    P(r, "mil_crate", x1 - 80, y0 + 60, "-x", z=r.z + 51, label="AmmoCrate")
def f_bar(r, x0, x1, y0, y1):
    P(r, "bar", x1 - 470, y1 - 380, "-y", label="NeonBar")                                    # neon side (customers) faces the room
    for k in range(4): P(r, "stool", x1 - 730 + k * 150, y1 - 640, "+y", label="BarStool")    # 53 cm in front of the counter face (y1 - 565)
    P(r, "stove", x1 - 600, y1 - 65, "-y", label="Stove"); P(r, "counter", x1 - 360, y1 - 65, "-y", label="Counter")
    P(r, "counter_s", x1 - 140, y1 - 65, "-y", label="Counter")
    P(r, "hood", x1 - 420, y1 - 20, "-y", z=r.z + 215, coll=False, label="Hood")
    for tx, ty in ((x0 + 230, y0 + 190), (x0 + 230, y0 + 490), (x0 + 230, y0 + 790)):        # one row along the left wall: the aisle stays open
        P(r, "d_table", tx, ty, "+y", label="Table")
        P(r, "booth", tx, ty - 95, "+y", label="Booth"); P(r, "booth", tx, ty + 95, "-y", label="Booth")
        P(r, "plate", tx - 40, ty, "+y", z=r.z + 76, coll=False, label="Bowl"); P(r, "glass", tx + 45, ty + 10, "+y", z=r.z + 76, coll=False, label="Glass")
        P(r, "pendant", tx, ty, "+y", z=r.z + CEIL - 132, coll=False, label="Pendant")
        r.light(tx, ty, r.z + CEIL - 150, 22.0, (255, 120, 210), radius=500.0, label="PendantLight")
    glow(r, x0 + 3, (y0 + y1) / 2, r.z + 300, 4, (y1 - y0) - 100, 8, "Pink", "WallNeon")
    glow(r, x0 + 3, (y0 + y1) / 2, r.z + 60, 4, (y1 - y0) - 100, 6, "Cyan", "WallNeon")
def f_living(r, x0, x1, y0, y1):
    cy = (y0 + y1) / 2 + 30
    P(r, "booth", x0 + 60, cy, "+x", label="Sofa"); P(r, "d_table", x0 + 250, cy, "+x", label="CoffeeTable")
    P(r, "jug", x0 + 250, cy + 20, "+y", z=r.z + 76, coll=False, label="Jug")
    glow(r, x1 - 3, cy, r.z + 110, 4, 280, 150, "Cyan", "WallScreen"); P(r, "console_low", x1 - 75, cy, "-x", label="MediaConsole")
    P(r, "counter", x1 - 160, y0 + 75, "+y", label="Kitchenette"); P(r, "steel_cab", x1 - 340, y0 + 30, "+y", label="Fridge")
    P(r, "pot", x1 - 160, y0 + 80, "+y", z=r.z + 91, coll=False, label="Pot")
    P(r, "re_table", -60, y1 - 140, "+y", label="DiningTable")
    for sx in (-1, 1): P(r, "stool", -60 + sx * 90, y1 - 40, "+y", label="Stool")
def f_bedroom(r, x0, x1, y0, y1):
    bx, by = x0 + 260, (y0 + y1) / 2
    r.box(bx, by, r.z, 230, 170, 32, label="BedBase", mat=MAT("MI_SFC_WallDark"))
    m = r.box(bx + 5, by, r.z + 32, 215, 160, 22, label="Mattress"); m.static_mesh_component.set_material(0, unreal.load_asset(FABRIC))
    for sy in (-1, 1):
        p = r.box(bx - 85, by + sy * 38, r.z + 54, 40, 62, 12, label="Pillow"); p.static_mesh_component.set_material(0, unreal.load_asset(FABRIC))
    r.box(bx - 125, by, r.z, 12, 190, 110, label="Headboard", mat=MAT("MI_SFC_Trim"))
    glow(r, bx - 118, by, r.z + 100, 3, 180, 5, "Cyan", "HeadboardGlow")
    P(r, "steel_cab", bx - 60, by - 140, "+y", scale=0.6, label="NightStand")
    P(r, "wardrobe", x1 - 70, (y0 + y1) / 2, "-x", label="Wardrobe")
    r.light(bx + 40, by, r.z + 210, 14.0, (150, 200, 255), radius=420.0, label="BedLight")
def f_lab(r, x0, x1, y0, y1):
    for yy in (y0 + 160, y0 + 470):
        P(r, "console_low", x0 + 75, yy, "+x", label="LabConsole"); P(r, "chair", x0 + 230, yy, "-x", label="LabChair")
    cx, cy = (x0 + x1) / 2 + 60, (y0 + y1) / 2
    r.box(cx, cy, r.z, 260, 200, 40, label="RelicPlinth", mat=MAT("MI_SFC_WallDark")); glow(r, cx, cy, r.z + 40, 266, 206, 4, "Red", "RelicRing")
    P(r, "stone", cx, cy, "+y", z=r.z + 44, scale=5.5, label="MonolithRelic")
    r.light(cx, cy, r.z + 330, 18.0, (255, 90, 70), radius=500.0, label="RelicLight")
    P(r, "re_table", -150, y1 - 90, "-y", label="SampleTable")
    for k, key in enumerate(("tray", "jug", "stone_s", "stone_s")):
        P(r, key, -240 + k * 60, y1 - 90, "-y", z=r.z + 77, coll=False, label="Sample")
    P(r, "shelves", x1 - 55, y0 + 200, "-x", label="Shelves")
    for k in range(4): P(r, "circ_crate", x1 - 150 - k * 60, y0 + 60, "+y", label="SampleCase")
    P(r, "re_crate1", x1 - 200, y0 + 140, "+y", label="Crate")
def f_server(r, x0, x1, y0, y1):
    for k in range(4): P(r, "generator", x0 + 200 + k * 300, y1 - 60, "-y", label="ServerUnit")
    for k in range(3): P(r, "steel_cab", x0 + 90 + k * 95, y0 + 25, "+y", label="Cabinet")
    glow(r, (x0 + x1) / 2, y1 - 3, r.z + 230, (x1 - x0) - 100, 4, 8, "Red", "ServerGlow")
    r.light((x0 + x1) / 2, (y0 + y1) / 2, r.z + 300, 16.0, (255, 80, 60), radius=600.0, label="ServerLight")
VISIT = {"bar": (300.0, 190.0), "armory": (250.0, 770.0), "lab": (-300.0, 200.0), "server": (0.0, 790.0), "office": (0.0, 250.0)}
FURNISH = {"office": f_office, "armory": f_armory, "bar": f_bar, "living": f_living, "bedroom": f_bedroom, "lab": f_lab, "server": f_server}
# ---------------- the four structures (origin = front facade centre facing the boulevard / the Monolith gate) ----------------
s1 = structure("PortAuthority", -17800, -54500, (-1, 0), 1400, 1000, 600, [("office", 0, 640, 380), ("armory", 640, 1000, None)], -300, "MI_SFC_Concrete", "Cyan")
s2 = structure("NoodleBar", -12200, -53000, (1, 0), 1600, 1000, 600, [("bar", 0, 1000, None)], 0, "MI_SFC_WallDark", "Pink")
P(s2, "sign_neon", 0, -60, "-y", z=FT + 330, scale=0.55, coll=False, label="NeonSign")
s3 = structure("HabApartment", -17800, -49400, (-1, 0), 1200, 1000, 600, [("living", 0, 640, 300), ("bedroom", 640, 1000, None)], -250, "MI_SFC_Concrete", "Cyan")
s4 = structure("ExcavationLab", -20500, -93100, (-1, 0), 1400, 1000, 600, [("lab", 0, 680, 350), ("server", 680, 1000, None)], -300, "MI_SFC_WallDark", "Red")
json.dump(OUT, open(SA + r"\structures.json", "w"), indent=1)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True); print("saved")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
