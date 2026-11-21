"""roamers15: the user's list of 2026-11-20 (docs/improvements15.txt, item 25: docs/wilderness_ideas.md's idea 3), its plan's eleventh
phase: the named roaming monsters (C++ RD/RDList15j.cpp). From SourceArt/wilderness/roamers15.json:
- `items`: the roamers' unique named rings on every map of the game (its "maps"): each a copy of the strongest ring of its kind on that
  map, its amount times the ring's "times", weight 0 (never found anywhere else: a roamer drops it once), the ones of an earlier run taken
  out first (by name)
- `data`: brokenspire's roamers: the names, epithets, rings, the share of the regions' cells with one, the tiers over the region's, the hit
  points' factor, the round's time and the reach
Run after 910, 911, 918, 928 and 929 (which write the maps' items anew). Args: [items,data]   (no argument: both)"""
import sys, os, json, gc, unreal
MAPS = "/Game/RandomDungeon/Maps/"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\wilderness"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
eal = unreal.EditorAssetLibrary
J = json.load(open(os.path.join(SA, "roamers15.json"), encoding="utf-8"))
PARTS = (sys.argv[1] if len(sys.argv) > 1 else "items,data").split(",")
REPORT = []
KIND = {"Health": unreal.RDRingKind.HEALTH, "Magic": unreal.RDRingKind.MAGIC, "Dexterity": unreal.RDRingKind.DEXTERITY}


def each(fn, label, maps):
    for m in maps:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"{label}: no map {m}"); continue
        les.load_level(MAPS + m); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
        what = fn(g)
        g.modify(); les.save_current_level()
        g = None; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        REPORT.append(f"937 {label} {m}: {what}")


def items(g):
    names = {r["name"] for r in J["rings"]}
    its = [i for i in g.get_editor_property("items") if str(i.get_editor_property("name")) not in names]
    rings = [i for i in its if i.get_editor_property("kind") == unreal.RDItemKind.RING]
    added = []
    for r in J["rings"]:
        same = [i for i in rings if i.get_editor_property("ring_kind") == KIND[r["kind"]]]
        assert same, (r["kind"], "no ring of that kind on the map")
        best = max(same, key=lambda i: i.get_editor_property("amount"))
        d = unreal.RDItemDef(); d.import_text(best.export_text())
        d.set_editor_property("name", r["name"])
        d.set_editor_property("amount", round(float(best.get_editor_property("amount")) * float(r["times"]), 2))
        d.set_editor_property("weight", 0.0)
        d.set_editor_property("tiers", [])
        d.set_editor_property("found_max", 1)
        added.append(d)
    g.set_editor_property("items", its + added)
    return f"{len(added)} rings ({', '.join(f'{str(d.name)} {d.amount:g}' for d in added[:3])} ...)"


def data(g):
    g.set_editor_property("roamer_names15", J["names"])
    g.set_editor_property("roamer_epithets15", J["epithets"])
    g.set_editor_property("roamer_rings15", [unreal.Name(r["name"]) for r in J["rings"]])
    for k, p in (("chance", "roamer_chance15"), ("hp", "roamer_hp15"), ("round_seconds", "roamer_round_seconds15"), ("reach_m", "roamer_reach_m15")):
        g.set_editor_property(p, float(J[k]))
    g.set_editor_property("roamer_tier_up15", int(J["tier_up"]))
    have = {str(i.get_editor_property("name")) for i in g.get_editor_property("items")}
    missing = [r["name"] for r in J["rings"] if r["name"] not in have]
    assert not missing, ("run 937 items first", missing)
    return f"{len(J['names'])} names, {len(J['epithets'])} epithets, {len(J['rings'])} rings, chance {J['chance']}, tier +{J['tier_up']}"


if "items" in PARTS: each(items, "items", J["maps"])
if "data" in PARTS: each(data, "data", ["brokenspire"])
for l in REPORT: print("ROAMERS15", l)
gc.collect()
