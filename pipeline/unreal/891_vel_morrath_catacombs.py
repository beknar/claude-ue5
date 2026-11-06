"""vel_morrath: the catacombs under Vel Morrath's cathedral (the user's of 2026-11-06, docs/vel_morrath.txt: "catacombs that go
deeper than anyone has mapped ... the dungeon is underground ... the entrance from the central cathedral"; their choice:
"Floors going down. Each tier is a floor below the last, reached by stairs down from the floor above: tier 1 under the
cathedral, tier 5 the deepest, built and balanced like Mistward Castle's tiers"). A Save As copy of mistward_castle (its
heroes, balance, monsters, loot, traps, special rooms, bosses) with:
- the generator's bTierFloors: each tier's sets of rooms TierFloorDepth (450 cm) below the tier before's, every hallway out
  of a set toward a shallower one a stair over its StairTiles (4) nearest the border (RDSection's Plan / ShellColumn)
- its own counters and record (DungeonKey "vel_morrath": its tiers, bosses, prisoners and start loot kept apart from the
  castle's), its name (DungeonTitle), the town it comes back to (TownLevel brokenspire: the way out puts her at the
  cathedral's door, RDTownGame's ReturnToTown)
- its looks by tier (TierThemes): tier 1 the old stone crypts (the plain pieces), tier 2 the crypt stone ("Crypt":
  HallowedDepths' crypt walls and floors), tier 3 the buried cathedral's arches (the castle's "Castle" theme), tier 4 the
  deep halls older than the city ("Dwarf"), tier 5 all three mixed
- no final boss (Aurorim is Mistward Castle's), no menu (it is entered from the cathedral with her hero)
Run as `891 saveas` (it saves the copy and quits the editor: a copied map is opened only after a restart), then, the editor
started again, `891` (it sets the copy up, builds its start section and saves it). Args: [saveas]"""
import sys, unreal
SRC, DST = "/Game/RandomDungeon/Maps/mistward_castle", "/Game/RandomDungeon/Maps/vel_morrath"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
V = unreal.Vector
YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
FACE = 25.0


def corners(b): return [V(x, y, z) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]


def piece(path, front="+x", mode="center", scale=(1, 1, 1), collision=True):
    """864's normalisation (center: XY centred, bottom z 0; floor: top z 0; ceil: flipped, underside z 0; wallface: the room
    face at x = FACE, its thickness behind)"""
    m = unreal.load_asset(path)
    assert m, path
    rot = unreal.Rotator(roll=180.0 if mode == "ceil" else 0.0, pitch=0.0, yaw=YAW[front]); sc = V(*scale)
    t0 = unreal.Transform(V(0, 0, 0), rot, sc)
    pts = [unreal.MathLibrary.transform_location(t0, c) for c in corners(m.get_bounding_box())]
    mn = V(min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)); mx = V(max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
    tx, ty, tz = -(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z
    if mode == "floor": tz = -mx.z
    elif mode == "wallface": tx = FACE - mx.x
    p = unreal.RDPiece(); p.mesh = m; p.adjust = unreal.Transform(V(tx, ty, tz), rot, sc)
    p.size = V(mx.x - mn.x, mx.y - mn.y, mx.z - mn.z); p.collision = collision
    return p


if len(sys.argv) > 1 and sys.argv[1] == "saveas":
    assert not eal.does_asset_exist(DST), "vel_morrath exists: set it up with 891 (no argument)"
    if not ues.get_editor_world().get_path_name().startswith(SRC + "."): les.load_level(SRC)
    ok = unreal.EditorLoadingAndSavingUtils.save_map(ues.get_editor_world(), DST)
    print("VMC saved as", DST, ok, "| quitting: start the editor again and run 891")
    unreal.SystemLibrary.quit_editor()
else:
    if not ues.get_editor_world().get_path_name().startswith(DST + "."): les.load_level(DST)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(DST + "."), w.get_path_name()
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    # ------------------------------------------------------------ the crypt stone (HallowedDepths): a plain stone block wall,
    # 2 m thick, its two faces alike (measured: 162 vertices, a box), taken to 1 m (a thicker wall reached through the next
    # room's across a one-tile gap); its slab floors; the floor slab turned over for the ceilings
    HD = "/Game/HallowedDepths/Meshes/Modules/"
    P = {}
    wall = piece(HD + "SM_Wall_02_Crypt_Var_03", front="+x", mode="wallface", scale=(0.5, 1.0, 1.0))
    for n in ("Wall_Block", "Wall_Stone", "Wall_Corr", "Wall_Rough", "Wall_Rough_2", "Wall_Rough_3"): P["Crypt." + n] = wall
    f1 = piece(HD + "SM_Floor_Crypt_Var_01", front="+x", mode="floor", scale=(0.75, 300 / 399.6, 1.0))
    f2 = piece(HD + "SM_Floor_Crypt_Var_02", front="+x", mode="floor", scale=(0.5, 0.5, 1.0))
    for n in ("Floor_Stone", "Floor_Brick", "Floor_Brick2", "Floor_Random", "Floor_Tiles", "Floor_Wood", "Floor_Corr"):
        P["Crypt." + n] = f1; P["Crypt." + n + "_Alt"] = f2
    P["Crypt.Ceil_Room"] = piece(HD + "SM_Floor_Crypt_Var_01", front="+x", mode="ceil", scale=(0.75, 300 / 399.6, 1.0))
    P["Crypt.Ceil_Corr"] = P["Crypt.Ceil_Room"]
    pieces = dict(gen.get_editor_property("pieces"))
    for k in [k for k in pieces if str(k).startswith("Crypt.")]: del pieces[k]
    for k, p in P.items(): pieces[unreal.Name(k)] = p
    gen.set_editor_property("pieces", pieces)
    gen.set_editor_property("tier_themes", [unreal.Name(n) for n in ("None", "Crypt", "Castle", "Dwarf", "Mixed")])
    gen.set_editor_property("mixed_themes", [unreal.Name(n) for n in ("Crypt", "Castle", "Dwarf")])
    for k, v in (("tier_floors", True), ("tier_floor_depth", 450.0), ("stair_tiles", 4), ("dungeon_key", "vel_morrath"),
                 ("dungeon_title", "The Catacombs of Vel Morrath"), ("town_level", "/Game/RandomDungeon/Maps/brokenspire"),
                 ("catacombs_level", ""), ("final_boss_on", False), ("menu_level", "")):
        try: gen.set_editor_property(k, v)
        except Exception as e: print("VMC (no", k, ")", e)
    gen.modify(); gen.build_start_section()
    les.save_current_level()
    print("VMC", DST, "| floors", gen.get_editor_property("tier_floors"), gen.get_editor_property("tier_floor_depth"), gen.get_editor_property("stair_tiles"),
          "| key", gen.get_editor_property("dungeon_key"), "| title", gen.get_editor_property("dungeon_title"),
          "| themes", [str(t) for t in gen.get_editor_property("tier_themes")], "| final boss", gen.get_editor_property("final_boss_on"),
          "| town", gen.get_editor_property("town_level"), "| crypt pieces", len(P))
    del gen, pieces, P, wall, f1, f2, w
import gc
gc.collect()
