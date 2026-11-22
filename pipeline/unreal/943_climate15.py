"""climate15: the user's list of 2026-11-20 (docs/improvements15.txt, item 25: docs/wilderness_ideas.md's idea 7), its plan's
seventeenth phase: preparing for regions (C++ RD/RDList15p.cpp). From SourceArt/wilderness/climate15.json:
- `items`: on every map of the game (its "maps"): the regions' herbs and the meals cooked from them (copies of their "like", weight 0:
  never found in a chest; the meals' buffs "warm" and "cool"), and the meals' recipes at the oven, the ones of an earlier run taken out
  first (by name); a map without a "like" takes the first map's
- `data`: brokenspire's: the armour sets' warmth and coolness (each set checked against its items), the hot regions and hours, the
  regions' herbs (each region checked against its biomes)
Run `items` after 928 and 929 (which write the maps' items anew). Args: [items,data]   (no argument: both)"""
import sys, os, json, gc, unreal
MAPS = "/Game/RandomDungeon/Maps/"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\wilderness"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
eal = unreal.EditorAssetLibrary
J = json.load(open(os.path.join(SA, "climate15.json"), encoding="utf-8"))
PARTS = (sys.argv[1] if len(sys.argv) > 1 else "items,data").split(",")
REPORT = []
TEMPLATE = {}


def each(fn, label, maps):
    for m in maps:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"{label}: no map {m}"); continue
        les.load_level(MAPS + m); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
        what = fn(g)
        g.modify(); les.save_current_level()
        g = None; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        REPORT.append(f"943 {label} {m}: {what}")


def items(g):
    mine = {x["name"] for x in J["items"]}
    its = [i for i in g.get_editor_property("items") if str(i.get_editor_property("name")) not in mine]
    names = {str(i.get_editor_property("name")) for i in its}
    for i in its:
        n = str(i.get_editor_property("name"))
        if n in {x["like"] for x in J["items"]}: TEMPLATE.setdefault(n, i.export_text())
    added = []
    for X in J["items"]:
        assert X["like"] in TEMPLATE, ("no item like", X["like"], "on this map or the ones before it")
        d = unreal.RDItemDef(); d.import_text(TEMPLATE[X["like"]])
        d.set_editor_property("name", X["name"]); d.set_editor_property("weight", 0.0); d.set_editor_property("tiers", []); d.set_editor_property("found_max", 1)
        if "amount" in X: d.set_editor_property("amount", float(X["amount"]))
        if "seconds" in X: d.set_editor_property("seconds", float(X["seconds"]))
        if X.get("buff"):
            d.set_editor_property("buff_kind", unreal.Name(X["buff"][0])); d.set_editor_property("buff_amount", float(X["buff"][1])); d.set_editor_property("buff_seconds", float(X["buff"][2]))
        added.append(d)
    g.set_editor_property("items", its + added)
    names |= mine
    # (the meals' recipes at the oven: a part's items those the map has)
    recs = [r for r in g.get_editor_property("recipes") if str(r.get_editor_property("item")) not in mine]
    made = 0; skipped = []
    for X in J["items"]:
        if not X.get("parts"): continue
        r = unreal.RDRecipe(); r.set_editor_property("item", unreal.Name(X["name"])); r.set_editor_property("station", unreal.Name("Oven")); r.set_editor_property("tier", 0)
        ps = []; missing = []
        for lab, anyof, n in X["parts"]:
            have = [a for a in anyof if a in names]
            if not have: missing.append(lab); continue
            p = unreal.RDRecipePart(); p.set_editor_property("label", lab); p.set_editor_property("any_of", [unreal.Name(a) for a in have]); p.set_editor_property("count", int(n))
            ps.append(p)
        # (a map with none of a part's items (the castle has no garden berries) has no such recipe: its meal is still carried there)
        if missing: skipped.append(f"{X['name']} (no {', '.join(missing)})"); continue
        r.set_editor_property("parts", ps); recs.append(r); made += 1
    g.set_editor_property("recipes", recs)
    return f"{len(added)} items, {made} recipes" + (f", left off: {'; '.join(skipped)}" if skipped else "")


def data(g):
    have = {str(i.get_editor_property("name")) for i in g.get_editor_property("items")}
    for x in J["items"]: assert x["name"] in have, ("run 943 items first", x["name"])
    for s, w, c in J["gear"]: assert s in have, ("no armour set", s)
    known = {str(b.get_editor_property("name")) for b in g.get_editor_property("wild_biomes")}
    for b in J["heat"]["biomes"]: assert b in known, ("no biome", b)
    for h in J["herbs"]:
        for b in h["biomes"]: assert b in known, (h["item"], b)
    g.set_editor_property("climate_gear15", [f"{s}|{w:g}|{c:g}" for s, w, c in J["gear"]])
    g.set_editor_property("wild_heat_biomes15", J["heat"]["biomes"])
    g.set_editor_property("heat_from15", float(J["heat"]["from"])); g.set_editor_property("heat_to15", float(J["heat"]["to"]))
    g.set_editor_property("heat_seconds15", float(J["heat"]["seconds"]))
    g.set_editor_property("climate_herbs15", [f"{h['item']}|{';'.join(h['biomes'])}" for h in J["herbs"]])
    return f"{len(J['gear'])} sets, {len(J['heat']['biomes'])} hot regions {J['heat']['from']}-{J['heat']['to']} h, {len(J['herbs'])} herbs"


if "items" in PARTS: each(items, "items", J["maps"])
if "data" in PARTS: each(data, "data", ["brokenspire"])
for l in REPORT: print("CLIMATE15", l)
gc.collect()
