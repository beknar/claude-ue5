"""fantasy_castle_level castle interiors, in the three doorway-cut buildings on the castle's east terrace (411):
  SM_Build2  -> great hall: dais with the high table, two long feasting tables with benches, hearth, chandeliers, knights
  SM_House3  -> armory: spear racks, armour stands, tool/weapon board, openable chests, barrels, quartermaster's table
  SM_House4  -> barracks: bunks with openable foot chests, wardrobe, mess table, hearth, spears by the door
Each room: lining (world-aligned castle stone, slate floor, timber ceiling) inside the single-sided shell, a BP_Door in the
doorway (F), capped-exposure post-process volume, lamps. Room frames: blender_numpy/fcl_castle_rooms.py (castle_rooms_geo.json).
Actors tagged 'fcl_int_castle'. Frame: origin = doorway centre at floor level, +Y into the room, +X along the door wall."""
import json, math, random, sys, unreal
sys.path.insert(0, r"E:\code\claude-ue5\pipeline\unreal")
import importlib, interior_lib as IL; importlib.reload(IL)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert "fantasy_castle_level." in w.get_path_name(), w.get_path_name()
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_current_level_by_name("fantasy_castle_level")
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\fantasy_castle"; TAG = "fcl_int_castle"
GEO = json.load(open(SA + r"\castle_rooms_geo.json")); ROOMS = json.load(open(SA + r"\castle_rooms.json"))
MAT = lambda n: f"/Game/FantasyCastleLevel/Materials/{n}"
LEAF = "/Game/FantasyCastleLevel/Meshes/SM_M_Door01_Leaf"
FC = IL.FC; LAKE = IL.LAKE
print("cleared", IL.clear(TAG))
def room_for(mesh, folder, wall_mat, h_max):
    label = next(k for k, v in ROOMS.items() if v["mesh"] == mesh); g = GEO[mesh]
    a = next(x for x in eas.get_all_level_actors() if x.get_actor_label() == label)
    base = a.get_actor_transform()
    fr = IL.door_frame(base, g["door"], g["floor"], (-g["normal"][0], -g["normal"][1]))
    x0, x1, y0, y1 = g["room"]
    xa, xb, ya, yb = IL.frame_extent(fr, base, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    r = IL.Room(fr, 0.0, TAG, folder)
    H = min(h_max, g["ceiling"] - g["floor"] - 30)
    W, D = xb - xa, yb
    r.box((xa + xb) / 2, D / 2, -10, W + 20, D + 20, 12, label="Floor", mat=MAT("MI_FCL_CastleFloor"))
    r.line(xa, xb, 0, D, H, doors=(("-y", 0.0, 170, 265),), ceiling=False, mat=MAT(wall_mat))
    r.box((xa + xb) / 2, D / 2, H, W + 14, D + 14, 14, label="Ceiling", mat=MAT("MI_FCL_WoodCeiling"))
    for k in range(int(D // 250)):                                              # ceiling beams across the room
        r.beam(xa, 180 + k * 250, xb, 180 + k * 250, H - 26, sz=26)
    r.door(LEAF, -85, 0, 0, width=170, height=262, label="Door")
    r.exposure(xa, xb, 0, D, -20, H + 20)
    print(f"{label} {folder}: {W:.0f} x {D:.0f} cm, ceiling {H:.0f}")
    return r, xa, xb, D, H
rng = random.Random(7)
# ---------------- great hall ----------------
r, xa, xb, D, H = room_for("SM_Build2", "FCL/Interiors/GreatHall", "MI_FCL_CastleWall", 760)
dz = 28.0
r.box(0, D - 170, 0, xb - xa - 40, 300, dz, label="Dais", mat=MAT("MI_FCL_CastleFloor"))
r.put("TableLong", 0, D - 210, dz, yaw=0, label="HighTable")
for k, x in enumerate((-80, 0, 80)):
    r.put("S:ChairWindsor" if k == 1 else "S:ChairA", x, D - 150, dz, yaw=180, label="HighChair")
r.table_set(0, D - 210, dz + 76, 0, 230, places=4, rich=True, rng=rng)
for x in (xa + 70, xb - 70):
    r.put(FC("SM_Knight_posed"), x, D - 110, dz, yaw=180, label="KnightArmour")
z0 = r.z
for x in (-(xb - xa) / 4, (xb - xa) / 4):
    r.dining(x, D * 0.42, 90, kind="long", seats="bench", rich=True)
    r.put("Chandelier", x, D * 0.42, H - 150, label="Chandelier", coll=False)
    r.light(x, D * 0.42, H - 175, 160.0, radius=1300.0, label="ChandelierLight")
r.put("Rug", 0, 140, 0.5, yaw=90, scale=(1.4, 1.0, 1.0), coll=False, label="Runner")
r.put("Rug", 0, D * 0.45, 0.5, yaw=90, scale=(1.4, 1.0, 1.0), coll=False, label="Runner")
r.hearth(xa + 45, D * 0.45, "+x", cauldron=False)
for y in (D * 0.25, D * 0.7):
    r.put("S:Antlers", xb - 4, y, 260, yaw=90, scale=3.0, coll=False, label="Antlers")
r.put(IL.PACK("Small_props/SM_barrel_01"), xb - 60, 90, 0, label="AleBarrel"); r.put(IL.PACK("Small_props/SM_barrel_02"), xb - 60, 170, 0, label="AleBarrel")
r.put("Chest", xa + 70, 90, 0, yaw=90, label="HallChest")
r.light(0, 120, 300, 60.0, radius=900.0, label="EntryLight")
# ---------------- armory ----------------
r, xa, xb, D, H = room_for("SM_House3", "FCL/Interiors/Armory", "MI_FCL_StoneBlock", 480)
n = int((D - 200) // 45)
for k in range(n):                                                            # spear rack along the left wall
    r.put(FC("SM_Spear_low"), xa + 22, 150 + k * 45, 0, yaw=rng.uniform(0, 360), label="Spear")
r.beam(xa + 12, 120, xa + 12, 150 + n * 45, 150, sz=14, label="SpearRail")
r.put("ToolBoard", xb - 6, D * 0.3, 110, yaw=90, label="WeaponBoard")
for x in (xa + 90, xb - 90):
    r.put(FC("SM_Knight_posed"), x, D - 80, 0, yaw=180, label="ArmourStand")
r.put("Chest", xb - 45, D * 0.55, 0, yaw=90, label="ArmsChest"); r.put("S:Trunk", xb - 45, D * 0.75, 0, yaw=90, label="ArmsTrunk")
r.put(IL.PACK("Small_props/SM_barrel_01"), xb - 50, 70, 0, label="ArrowBarrel"); r.put(IL.PACK("Small_props/SM_crate_group_01"), xa + 70, D - 190, 0, yaw=90, label="Crates")
r.put("TableSmall", 0, D * 0.55, 0, yaw=0, label="QuartermasterTable"); r.put("Stool", 0, D * 0.55 - 60, 0, label="Stool")
r.put("S:Book", -15, D * 0.55, 76, yaw=20, coll=False, label="Ledger"); r.put("CandleStick", 25, D * 0.55, 76, coll=False, label="Candle")
r.light(0, D * 0.3, H - 60, 70.0, radius=900.0, label="ArmoryLight"); r.light(0, D * 0.75, H - 60, 70.0, radius=900.0, label="ArmoryLight")
# ---------------- barracks ----------------
r, xa, xb, D, H = room_for("SM_House4", "FCL/Interiors/Barracks", "MI_FCL_Plaster", 480)
for k, y in enumerate((260, 420, 580)):                                       # clear of the doorway
    if y + 80 < D - 40: r.bed("BedSingle" if k % 2 == 0 else "BedSingleGreen", xa + 105, y, -90)
r.hearth(xb - 130, D - 45, "-y", cauldron=True)
r.dining(xb - 140, D * 0.45, 90, kind="small", seats="bench")
r.put("Wardrobe", xb - 45, 210, 0, yaw=-90, label="Wardrobe")
for k in range(3): r.put(FC("SM_Spear_low"), xb - 20, 60 + k * 35, 0, yaw=rng.uniform(0, 360), label="Spear")
r.put("FurRug", (xa + xb) / 2, D * 0.5, 0.5, yaw=15, coll=False, label="FurRug")
r.light((xa + xb) / 2, D * 0.35, H - 60, 60.0, radius=900.0, label="BarracksLight")
r.put("CandleStick", xb - 140, D * 0.45, 76, coll=False, label="Candle")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True); print("saved")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
