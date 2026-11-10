"""The user's list of 2026-11-10 (docs/improvements10.txt), its first phase's data (the C++ is the rest: RD/RDConsoleCmds.cpp, the quick
bar's items, the anvil's mending and stacks, the quest window, the save drop-down, the horse's blocker, the ambushers). Steps (all
by default, or name some):
  brewers  "only mages and martial artists should be able to make healing potions and mana potions at the anvil": the generator's
           PotionBrewers (Mage, MartialArtist) on every map of the game
  horse    "horse travel should be at least 5x faster than what the player can move": brokenspire's HorseDef.SpeedMul 5.5
  food     "if there is food on a table, the player should be able to put it into the inventory": on the six dungeons of the game
           (the castle and its copies) the prep table is the bare one (890's SM_Kit_PrepTableBare) with the town's food pieces laid
           on it as things to take (bTableFood); the start section built again (its furniture is saved)
  noshield "the warrior should not have a default shield on": every map of the game and martial_arts checked again (899's rule:
           no start shield, no shield mesh on her weapons), a shield found anywhere taken off and said
The second phase (C++ RD/RDSkyFar.cpp):
  sky      "a disc in the sky in the day time, a visible border near the horizon, also at night": brokenspire's FarLandMaterial
           (M_RD_FarLand: the far land's ring lit, its colour the world model's ground by vertex, two-sided) and its clouds'
           SkyCoverRange (0.05 to 0.6: at 0.1 to 1 fair weather drew a grey deck over the whole sky, 884 sky10)
  stairs   "the stairway to get into the guard towers in mistward castle looks like a series of stairs was built up and angled until
           it reached the top" (E:\\temp\\stonestairway.jpg): brokenspire's StairBlockMaterial and StairWallMaterial (Castle of
           Eternal Mist's stair stone for the blocks, its pale brick for the coursed wall under them: RDTownPlan.cpp's CastleStairBuild)
  dungeon  "when the tier boss appears, a teleporter back to the first dungeon room or to brokenspire should spawn there with him"
           (bBossPorts) and "a library's bookshelves should contain either scrolls of that tier or below or crafting components for
           scrolls of that tier or below, could also contain tomes" (bLibraryShelves) on the six dungeons of the game
  crowd    "some of the NPC crowd in the Arena have no heads": each crowd body's head and hair (the NPC Characters pack's _Full_02
           bodies carry them as meshes of their own, Separate/, as 882's townsfolk) as CrowdParts, on every map with a crowd
  see      "if the player walks under a structure that blocks sight of her, make the structure see-through": brokenspire's bSeeThrough
C++ first (RD/RDList10b.cpp). Args: [brewers] [horse] [food] [noshield] [sky] [stairs] [dungeon] [crowd] [see]"""
import sys, unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
V = unreal.Vector
MAPS = "/Game/RandomDungeon/Maps/"
GAME_MAPS = ("brokenspire", "mistward_castle", "vel_morrath", "war_engine", "sewers", "kethrys_spire", "heaven_fortress")
DUNGEONS = GAME_MAPS[1:]
STEPS = [a for a in sys.argv[1:] if a in ("brewers", "horse", "food", "noshield", "sky", "stairs", "dungeon", "crowd", "see")] or ["brewers", "horse", "food", "noshield", "sky", "stairs", "dungeon", "crowd", "see"]
REPORT = []


def open_map(m):
    path = MAPS + m
    if not ues.get_editor_world().get_path_name().startswith(path + "."):
        les.load_level(path); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    w = ues.get_editor_world(); assert w.get_path_name().startswith(path + "."), w.get_path_name()
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def each(maps, fn, label):
    for m in maps:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"{label}: no map {m}"); continue
        g = open_map(m)
        what = fn(g)
        g.modify(); les.save_current_level()
        unreal.SystemLibrary.execute_console_command(None, "obj gc")
        REPORT.append(f"{label} {m}: {what}")


def piece(mesh):
    """a piece in the dungeon frame, footprint centred, bottom at z 0, no collision (890's piece() for a static mesh)"""
    p = unreal.RDPiece(); p.mesh = mesh
    b = mesh.get_bounding_box()
    p.adjust = unreal.Transform(V(-(b.min.x + b.max.x) / 2, -(b.min.y + b.max.y) / 2, -b.min.z), unreal.Rotator(0, 0, 0), V(1, 1, 1))
    p.size = V(b.max.x - b.min.x, b.max.y - b.min.y, b.max.z - b.min.z)
    p.collision = False
    return p


if "brewers" in STEPS:
    def brewers(g):
        g.set_editor_property("potion_brewers", [unreal.Name("Mage"), unreal.Name("MartialArtist")])
        heroes = [str(h.name) for h in g.get_editor_property("heroes")]
        return f"potion brewers Mage, MartialArtist (heroes here: {', '.join(heroes)})"
    each(GAME_MAPS, brewers, "brewers")

if "horse" in STEPS:
    def horse(g):
        d = g.get_editor_property("horse_def")
        was = d.get_editor_property("speed_mul")
        d.set_editor_property("speed_mul", 5.5); g.set_editor_property("horse_def", d)
        return f"the horse {was} -> 5.5 times her speed"
    each(["brokenspire"], horse, "horse")

if "food" in STEPS:
    bare = unreal.load_asset("/Game/RandomDungeon/Town7/SM_Kit_PrepTableBare")
    K = "/Game/Castle/Furniture/Kit/"
    foods = {}
    for n, m in (("FoodBread", "SM_Kit_BreadLoaf"), ("FoodBreadRound", "SM_Kit_BreadRound"), ("FoodCheese", "SM_Kit_Cheese"), ("FoodApples", "SM_Kit_AppleBasket")):
        a = unreal.load_asset(K + m)
        if a: foods["Town." + n] = piece(a)
        else: REPORT.append("food: MISSING " + m)
    if not bare: REPORT.append("food: no bare prep table (run 890 town first)")

    def food(g):
        P = g.get_editor_property("pieces")
        pk = unreal.Name("PrepTable")
        if pk not in P: return "no PrepTable piece: nothing to lay food on"
        pt = P[pk]; was = pt.mesh.get_name() if pt.mesh else "none"
        if bare: pt.mesh = bare; P[pk] = pt
        for k, v in foods.items(): P[unreal.Name(k)] = v
        g.set_editor_property("pieces", P)
        items = {str(i.get_editor_property("name")) for i in g.get_editor_property("items")}
        missing = [n for n in ("Bread", "Cheese", "Fruit") if n not in items]
        g.set_editor_property("table_food", True)
        g.modify(); g.build_start_section()
        return f"prep table {was} -> {bare.get_name() if bare else was}, {len(foods)} food pieces, table food on" + (f"; MISSING items {missing}" if missing else "")
    if bare: each(DUNGEONS, food, "food")

if "noshield" in STEPS:
    def noshield(g):
        ss = dict(g.get_editor_property("start_shield"))
        had = str(ss.pop(unreal.Name("Warrior"), "none"))
        g.set_editor_property("start_shield", ss)
        def strip(ws):
            n = 0; out = []
            for w in ws:
                m = w.get_editor_property("off_hand_mesh")
                if m and "shield" in m.get_name().lower(): w.set_editor_property("off_hand_mesh", None); n += 1
                out.append(w)
            return out, n
        heroes = list(g.get_editor_property("heroes")); hn = 0
        for h in heroes:
            if str(h.name) != "Warrior": continue
            ws, k = strip(list(h.weapons)); h.weapons = ws; hn += k
        g.set_editor_property("heroes", heroes)
        lw, ln = strip(list(g.get_editor_property("weapons"))); g.set_editor_property("weapons", lw)
        return f"start shield {had}; shield meshes taken off {hn} of her weapons and {ln} of the level's"
    each(GAME_MAPS + ("martial_arts",), noshield, "noshield")

if "sky" in STEPS:
    MEL = unreal.MaterialEditingLibrary; path = "/Game/RandomDungeon/Sky/M_RD_FarLand"
    if eal.does_asset_exist(path): eal.delete_asset(path)
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_RD_FarLand", "/Game/RandomDungeon/Sky", unreal.Material, unreal.MaterialFactoryNew())
    vc = MEL.create_material_expression(m, unreal.MaterialExpressionVertexColor, -400, 0)
    rough = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 200); rough.set_editor_property("r", 1.0)
    MEL.connect_material_property(vc, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    m.set_editor_property("two_sided", True)
    MEL.recompile_material(m); eal.save_loaded_asset(m, only_if_is_dirty=False)
    def sky(g):
        g.set_editor_property("far_land_material", m)
        g.set_editor_property("sky_cover_range", unreal.Vector2D(0.05, 0.6))
        return f"far land {m.get_name()}, cover 0.05 to 0.6, clouds traced {g.get_editor_property('sky_cloud_trace_km')} km"
    each(["brokenspire"], sky, "sky")

if "stairs" in STEPS:
    CK = "/Game/Medieval_Castle/CastleKit/Walls_Stone/Materials/"
    # (the wall under the steps in Castle of Eternal Mist's pale brick, the pack's own wall under its stairs (its ExtendDown
    # pieces), as the hall's walls are: Castle Forge's wall stone read dark brown against them (884 k10h's picture))
    # (the blocks in the same pack's stair stone, at its stairs' scale (312 cm a repeat): Castle Forge's stair stone is laid out for
    # its spiral's pieces and drew the blocks' ends near black (884 k10i))
    blk = unreal.load_asset("/Game/CastleofEternalMist/Material/Instances/MI_Stairs"); wal = unreal.load_asset("/Game/CastleofEternalMist/Material/Instances/MI_BrickStoneWall_Disp")
    def stairs(g):
        g.set_editor_property("stair_block_material", blk); g.set_editor_property("stair_wall_material", wal)
        g.set_editor_property("stair_block_uv_cm", 312.0); g.set_editor_property("stair_wall_uv_cm", 400.0)
        return f"blocks {blk.get_name() if blk else 'MISSING'}, wall {wal.get_name() if wal else 'MISSING'}"
    each(["brokenspire"], stairs, "stairs")

if "dungeon" in STEPS:
    def dungeon(g):
        g.set_editor_property("boss_ports", True); g.set_editor_property("library_shelves", True)
        return f"boss teleporters on, library shelves on (shelf chance {g.get_editor_property('shelf_loot_chance')})"
    each(DUNGEONS, dungeon, "dungeon")

if "crowd" in STEPS:
    def crowd(g):
        cm = list(g.get_editor_property("crowd_meshes"))
        if not cm: return "no crowd"
        out = []; heads = 0
        for mesh in cm:
            cp = unreal.RDCrowdParts(); parts = []
            mn = mesh.get_name() if mesh else ""
            # (882's way: the pack's _Full_02 bodies' head, hair, beard and moustache from Separate/)
            if mesh and "NPC_Characters_Pack" in mesh.get_path_name() and "_Full_02" in mn:
                base = mesh.get_path_name().rsplit("/Full/", 1)[0] + "/Separate/" + mn.split("_Full_02")[0]
                for part in ("_Head", "_Hair", "_Beard", "_Mustache"):
                    if eal.does_asset_exist(base + part): parts.append(unreal.load_asset(base + part))
                heads += 1 if any(str(x.get_name()).endswith("_Head") for x in parts) else 0
            cp.set_editor_property("parts", parts); out.append(cp)
        g.set_editor_property("crowd_parts", out)
        return f"{len(cm)} bodies, {sum(len(c.get_editor_property('parts')) for c in out)} parts, {heads} heads given"
    each(GAME_MAPS, crowd, "crowd")

if "see" in STEPS:
    def see(g):
        g.set_editor_property("see_through", True)
        return f"see-through on (hold {g.get_editor_property('see_through_hold')} s)"
    each(["brokenspire"], see, "see")

open_map("mistward_castle")
print("LIST10 " + " | ".join(REPORT))
import gc
gc.collect()
