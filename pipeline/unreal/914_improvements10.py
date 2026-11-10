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
C++ first. Args: [brewers] [horse] [food] [noshield]"""
import sys, unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
V = unreal.Vector
MAPS = "/Game/RandomDungeon/Maps/"
GAME_MAPS = ("brokenspire", "mistward_castle", "vel_morrath", "war_engine", "sewers", "kethrys_spire", "heaven_fortress")
DUNGEONS = GAME_MAPS[1:]
STEPS = [a for a in sys.argv[1:] if a in ("brewers", "horse", "food", "noshield")] or ["brewers", "horse", "food", "noshield"]
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

open_map("mistward_castle")
print("LIST10 " + " | ".join(REPORT))
import gc
gc.collect()
