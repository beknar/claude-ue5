"""The list of 2026-11-11's fourth phase (docs/improvements11.txt): the farmsteads' designs on brokenspire (C++ RD/RDWildFarm11.cpp
first). Reads SourceArt/wilderness/farm_designs.json (pipeline/blender_numpy/farm_designs.py: 60 designs, each a farmhouse and a
barn of the town's kit, sheds, coops, granaries, gardens, pens of three shapes with the town's farm animals, yard things) into the
generator's FarmDesigns, and its loot (what the farms' and the wild houses' chests, barrels, crates, wardrobes, barns, granaries,
coops and sheds give) into FarmLoot; checks that every kit piece, furniture piece, crop, animal and item they name is on the level
(a missing one is reported: the game leaves it out). Saves the level.
    919_farms11.py            (play stopped; the editor on any level: it opens brokenspire and saves it)"""
import unreal, json, os
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
MAP = "/Game/RandomDungeon/Maps/brokenspire"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
D = json.load(open(os.path.join(SA, "wilderness", "farm_designs.json"), encoding="utf-8"))
if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
designs = []
for d in D["designs"]:
    ds = unreal.RDFarmDesign(); ds.set_editor_property("name", d["name"]); parts = []
    for p in d["parts"]:
        pt = unreal.RDFarmPart()
        for k, v in (("kind", unreal.Name(p["kind"])), ("u", float(p["u"])), ("v", float(p["v"])), ("yaw", float(p["yaw"])), ("nx", int(p["nx"])), ("ny", int(p["ny"])),
                     ("hu", float(p["hu"])), ("hv", float(p["hv"])), ("style", int(p["style"])), ("shape", int(p["shape"])), ("animals", p["animals"]), ("variant", p["variant"])):
            pt.set_editor_property(k, v)
        parts.append(pt)
    ds.set_editor_property("parts", parts); designs.append(ds)
g.set_editor_property("farm_designs", designs)
g.set_editor_property("farm_loot", {unreal.Name(k): v for k, v in D["loot"].items()})
# (what they name, on the level)
pieces = {str(k) for k in g.get_editor_property("pieces").keys()}
need = set()
for st in ("Timber", "Stone", "Thatch"):
    for part in ("Floor", "Wall", "Doorway", "Door", "WallWindow", "Pillar", "Roof", "RoofTrim", "RoofEndL", "RoofEndR", "GableNeg", "GablePos"):
        need.add(f"Town.{st}_{part}")
need |= {f"Town.Crop{i}" for i in range(1, 7)} | {"Fireplace", "Bed", "Chest", "TableLong", "Bench", "Barrel", "Crate", "Wardrobe"}
missing_pieces = sorted(n for n in need if n not in pieces)
items = {str(i.name) for i in g.get_editor_property("items")}
loot_items = {e.split("|")[0] for v in D["loot"].values() for e in v.split(";")}
crop_items = [str(n) for n in g.get_editor_property("town_crop_items")]
missing_items = sorted(n for n in loot_items | set(crop_items) if n not in items and n != "None")
animals = {str(a.name) for a in g.get_editor_property("town_animals") if a.mesh}
want_animals = {a.split(":")[0] for d in D["designs"] for p in d["parts"] for a in p["animals"].split(",") if a}
missing_animals = sorted(a for a in want_animals if a not in animals)
g.modify(); les.save_current_level()
print(f"919 farms: {len(designs)} designs, {len(D['loot'])} loot kinds on brokenspire | missing pieces {missing_pieces} | missing items {missing_items} | "
      f"missing animals {missing_animals} | crops {crop_items} | wild houses inside {g.get_editor_property('wild_house_insides')}")
del g, designs
import gc; gc.collect()
