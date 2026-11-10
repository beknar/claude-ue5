"""The wilderness's small points of interest and its encounter director (the user's list of 2026-11-08b, docs/improvements9.txt,
its seventh phase: "the player should be able to interact or encounter something every 40 seconds when roaming the wilderness"),
from SourceArt/wilderness/poi.json onto brokenspire: the generator's WildPoiKinds (each kind's regions, layer, road, props, use,
things, text, blessing, monsters), WildPoiFill, WildEncounterGap and WildEngageM. Every prop prefix must be a wild piece's
(biomes.json's 'pieces', 887) and every thing an item of the level: the report says which are not.
C++ first (RD/RDWildPoi.cpp, FRDWildWorld::PoisIn). Args: none"""
import os, json, unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "claude_ue5", "SourceArt"))
D = json.load(open(os.path.join(SA, "wilderness", "poi.json"), encoding="utf-8"))
MAP = "/Game/RandomDungeon/Maps/brokenspire"
if not ues.get_editor_world().get_path_name().startswith(MAP + "."):
    les.load_level(MAP); unreal.SystemLibrary.execute_console_command(None, "obj gc")
g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
pieces = [str(k) for k in g.get_editor_property("wild_pieces").keys()]
items = {str(i.get_editor_property("name")) for i in g.get_editor_property("items")}
biomes = {str(b.get_editor_property("name")) for b in g.get_editor_property("wild_biomes")} if hasattr(g, "wild_biomes") else set()
report = []
kinds = []
for k in D["kinds"]:
    p = unreal.RDWildPoiKind()
    p.set_editor_property("name", k["name"]); p.set_editor_property("title", k["title"]); p.set_editor_property("biomes", k["biomes"])
    p.set_editor_property("weight", float(k.get("weight", 1.0))); p.set_editor_property("layer", int(k.get("layer", 0)))
    p.set_editor_property("road", bool(k.get("road", False))); p.set_editor_property("roaming", bool(k.get("roaming", False)))
    p.set_editor_property("hunts", bool(k.get("hunts", False)))          # (the list of 2026-11-10: an ambush hunts her)
    p.set_editor_property("props", k.get("props", [])); p.set_editor_property("use", k.get("use", "None"))
    p.set_editor_property("things", k.get("things", [])); p.set_editor_property("text", k.get("text", ""))
    p.set_editor_property("monsters", int(k.get("monsters", 0))); p.set_editor_property("monster_health", float(k.get("monster_health", 1.0)))
    p.set_editor_property("buff_damage", float(k.get("buff_damage", 0))); p.set_editor_property("buff_armour", float(k.get("buff_armour", 0)))
    p.set_editor_property("buff_seconds", float(k.get("buff_seconds", 0))); p.set_editor_property("reusable", bool(k.get("reusable", False)))
    kinds.append(p)
    for pr in k.get("props", []):
        pre = pr.split("|")[0]
        if not any(x.startswith(pre) for x in pieces): report.append(f"{k['name']}: no wild piece '{pre}'")
    for t in k.get("things", []):
        if t.split("|")[0] not in items: report.append(f"{k['name']}: no item '{t.split('|')[0]}'")
    for b in k["biomes"]:
        if biomes and b != "*" and b not in biomes: report.append(f"{k['name']}: no biome '{b}'")
g.set_editor_property("wild_poi_kinds", kinds)
g.set_editor_property("wild_poi_fill", float(D["fill"])); g.set_editor_property("wild_encounter_gap", float(D["gap"]))
g.set_editor_property("wild_engage_m", float(D["engage_m"]) * 100.0)
g.modify()
les.save_current_level()
print("POI", len(kinds), "kinds;", "; ".join(report) if report else "every piece, item and biome found")
del g, kinds
import gc
gc.collect()
