"""mistward_castle: the looks of its tiers (the user's choice of 2026-10-26: by tier). The generator's TierThemes: tier 1 the
stone dungeon and crypt it has (the plain pieces, 770's), tier 2 the castle keep and its cells ("Castle": Medieval Castle's
stone walls, floors and pillars, its wooden ceilings), tier 3 the dwarven deep halls ("Dwarf": Dwarven Citadel's brick
walls, tall hall walls, floor tiles), tiers 4 and 5 all three mixed (each set of rooms one of them, MixedThemes). A theme's
piece is "<Theme>.<Name>" in the generator's Pieces; a set of rooms of that theme takes it in place of <Name> (RDSection::Pc),
and the plain one where the theme has none (the doors, the furniture, the containers, the torches).
Every piece is normalised to the dungeon frame as 770's are: a wall runs along Y with its room face toward +X (here 25 cm in
front of the tile's edge, its thickness behind), 300 cm wide; a floor tile 300 cm, its top at z 0; a ceiling tile flipped,
its underside at z 0. Run on the open mistward_castle (863). Args: none"""
import unreal, sys
# (which side of the blind arch walls faces the room: measured in play, see the README's Mistward notes)
CASTLE_FRONT = sys.argv[1] if len(sys.argv) > 1 else "+y"
eas =unreal.get_editor_subsystem(unreal.EditorActorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V = unreal.Vector
MAP = "/Game/RandomDungeon/Maps/mistward_castle"
YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
FACE = 25.0          # (a themed wall's room face, in front of the tile's edge)
def corners(b):
    return [V(x, y, z) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]
def piece(path, front="+y", mode="center", back=30.0, scale=(1, 1, 1), collision=True, shift=(0, 0, 0)):
    """770's normalisation: mesh frame -> dungeon frame (center: XY centred, bottom z 0; floor: top z 0; ceil: flipped,
    underside z 0; wall: back at x = back, Y centred, bottom z 0; wallface: the room face at x = FACE, thickness behind)"""
    m = unreal.load_asset(path)
    assert m, path
    sc = V(*scale)
    rot = unreal.Rotator(roll=180.0 if mode == "ceil" else 0.0, pitch=0.0, yaw=YAW[front])
    t0 = unreal.Transform(V(0, 0, 0), rot, sc)
    b = m.get_bounding_box()
    pts = [unreal.MathLibrary.transform_location(t0, c) for c in corners(b)]
    mn = V(min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)); mx = V(max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
    tx, ty, tz = -(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z
    if mode == "floor": tz = -mx.z
    elif mode == "wall": tx = back - mn.x
    elif mode == "wallface": tx = FACE - mx.x
    t = unreal.Transform(V(tx + shift[0], ty + shift[1], tz + shift[2]), rot, sc)
    p = unreal.RDPiece()
    p.mesh = m; p.adjust = t; p.size = V(mx.x - mn.x, mx.y - mn.y, mx.z - mn.z); p.collision = collision
    return p
MC = "/Game/Medieval_Castle/CastleKit/"; DW = "/Game/DwarvenCitadel/Meshes/"
P = {}
# ---------------------------------------------------------------- Castle: the keep (Medieval Castle's stone walls 315 x 115 x 310)
cw = lambda n: MC + "Walls_Stone/" + n
# (the keep's walls: Castle of Eternal Mist's blind arches, 400 x 93 x 601, solid; Medieval Castle's stone walls have doorways
# and windows right through them, which would show the void and let her out)
BL = "/Game/CastleofEternalMist/Meshes/Arch/Blind/"
CWALL = dict(front=CASTLE_FRONT, mode="wallface", scale=(0.75, 1, 1))
P["Castle.Wall_Block"] = piece(BL + "SM_ArchWall_Blind_4x6_A", **CWALL)
P["Castle.Wall_Stone"] = piece(BL + "SM_ArchWallStone_Blind_Column_F_4x6_B", **CWALL)
P["Castle.Wall_Corr"] = piece(BL + "SM_ArchWall_Blind_4x4_A", **CWALL)
P["Castle.Wall_Rough"] = piece(BL + "SM_ArchWall_Blind_4x6_B", **CWALL)
for i, n in enumerate(("SM_ArchWall_Blind_4x6_C", "SM_ArchWall_Blind_Column_F_4x6_A", "SM_ArchWall_Blind_Column_F_4x6_B", "SM_ArchWall_Blind_Column_F_4x6_C",
                       "SM_ArchWallStone_Blind_Column_F_4x6_A", "SM_ArchWallStone_Blind_Column_F_4x6_C")):
    P[f"Castle.Wall_Rough_{i + 2}"] = piece(BL + n, **CWALL)
fl = lambda n, s: piece(cw(n), front="+x", mode="floor", scale=(300 / s[0], 300 / s[1], 1))
for name, n, s in (("Floor_Stone", "SM_Stone_Floor_01a_NN", (338, 337)), ("Floor_Stone_Alt", "SM_Stone_Floor_01b_NN", (331, 336)),
                   ("Floor_Brick", "SM_Stone_Floor_02a_NN", (312, 309)), ("Floor_Brick_Alt", "SM_Stone_Floor_01b_NN", (331, 336)),
                   ("Floor_Brick2", "SM_Stone_Floor_01a_NN", (338, 337)), ("Floor_Random", "SM_Stone_Floor_02a_NN", (312, 309)),
                   ("Floor_Random_Alt", "SM_Stone_Floor_01a_NN", (338, 337)), ("Floor_Tiles", "SM_Stone_Floor_01b_NN", (331, 336)),
                   ("Floor_Tiles_Alt", "SM_Stone_Floor_02a_NN", (312, 309)), ("Floor_Corr", "SM_Stone_Floor_02a_NN", (312, 309)),
                   ("Floor_Corr_Alt", "SM_Stone_Floor_01b_NN", (331, 336))):
    P["Castle." + name] = fl(n, s)
P["Castle.Floor_Wood"] = piece(MC + "Wood_Structures/SM_Wood_Floor_01b_NN", front="+x", mode="floor", scale=(1.5, 1.5, 1))
P["Castle.Ceil_Room"] = piece(MC + "Wood_Structures/SM_Wood_Floor_01b_NN", front="+x", mode="ceil", scale=(1.5, 1.5, 1))
P["Castle.Ceil_Corr"] = piece(cw("SM_Stone_Floor_02a_NN"), front="+x", mode="ceil", scale=(300 / 312.0, 300 / 309.0, 1))
P["Castle.CornerColumn"] = piece(cw("SM_Castle_Stone_Pillar_01b_NN"), front="+x")
P["Castle.Column"] = piece(cw("SM_Castle_Stone_Pillar_01a_NN"), front="+x", scale=(1.25, 1.25, 3.0))
# ---------------------------------------------------------------- Dwarf: the deep halls (Dwarven Citadel)
P["Dwarf.Wall_Block"] = piece(DW + "SM_ST_MainHall_LargeWall_02", front="+x", mode="wallface", scale=(1, 1, 0.75))
P["Dwarf.Wall_Stone"] = piece(DW + "SM_ST_BrickWall_05", front="+y", mode="wallface", scale=(0.75, 1, 0.75))
P["Dwarf.Wall_Corr"] = piece(DW + "SM_ST_BrickWall_05", front="+y", mode="wallface", scale=(0.75, 1, 0.75))
P["Dwarf.Wall_Rough"] = piece(DW + "SM_ST_BrickWall_Displace", front="+y", mode="wallface", scale=(0.75, 1, 0.75))
P["Dwarf.Wall_Rough_2"] = piece(DW + "SM_ST_MainHall_BrickWall_06", front="+y", mode="wallface", scale=(0.75, 1, 0.75))
P["Dwarf.Wall_Rough_3"] = piece(DW + "SM_ST_BrickWall_05", front="+y", mode="wallface", scale=(0.75, 1, 0.75))
for name, n, s in (("Floor_Stone", "SM_ST_FloorTile_01", 400), ("Floor_Stone_Alt", "SM_ST_FloorTile_04_M01", 400), ("Floor_Brick", "SM_ST_FloorTile_04", 400),
                   ("Floor_Brick_Alt", "SM_ST_FloorTile_04_M02", 400), ("Floor_Brick2", "SM_ST_MainHall_PillarFloor_M_01", 300), ("Floor_Random", "SM_ST_FloorTile_04", 400),
                   ("Floor_Random_Alt", "SM_ST_FloorTile_01", 400), ("Floor_Tiles", "SM_ST_TreasureRoomFloor_02", 406), ("Floor_Tiles_Alt", "SM_ST_TreasureRoomFloor_01", 409),
                   ("Floor_Wood", "SM_ST_FloorTile_04", 400), ("Floor_Corr", "SM_ST_FloorTile_01", 400), ("Floor_Corr_Alt", "SM_ST_FloorTile_04", 400)):
    P["Dwarf." + name] = piece(DW + n, front="+x", mode="floor", scale=(300.0 / s, 300.0 / s, 1))
P["Dwarf.Ceil_Room"] = piece(DW + "SM_ST_FloorTile_04", front="+x", mode="ceil", scale=(0.75, 0.75, 1))
P["Dwarf.Ceil_Corr"] = piece(DW + "SM_ST_FloorTile_01", front="+x", mode="ceil", scale=(0.75, 0.75, 1))
P["Dwarf.CornerColumn"] = piece(DW + "SM_ST_MainHall_ColumnBrick_01", front="+x", scale=(0.5, 0.5, 0.75))
# ---------------------------------------------------------------- into the generator
if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
w = ues.get_editor_world(); assert w.get_path_name().startswith(MAP + "."), w.get_path_name()
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
pieces = dict(gen.get_editor_property("pieces"))
for k in [k for k in pieces if str(k).startswith(("Castle.", "Dwarf."))]: del pieces[k]
for k, p in P.items(): pieces[unreal.Name(k)] = p
gen.set_editor_property("pieces", pieces)
gen.set_editor_property("tier_themes", [unreal.Name(n) for n in ("None", "Castle", "Dwarf", "Mixed", "Mixed")])
gen.set_editor_property("mixed_themes", [unreal.Name(n) for n in ("None", "Castle", "Dwarf")])
les.save_current_level()
for k in sorted(P):
    p = P[k]; s = p.size
    print(f"PIECE {k:28s} {s.x:7.1f} x {s.y:7.1f} x {s.z:7.1f}  {p.mesh.get_name()}")
print("MISTWARD pieces", len(P), "| themes", [str(t) for t in gen.get_editor_property("tier_themes")], "| mixed", [str(t) for t in gen.get_editor_property("mixed_themes")])
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
