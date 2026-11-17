"""The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), its seventh phase's second part
(item 12): "in the wilderness, enable the ability to kill farm animals and loot them - crafting items, food, can be found".

Parts (args):
  items         SourceArt/wilderness/farm_animals14.json's things (Raw Meat, Feathers, Eggs) on every map of the game (its "maps"),
                each copied from its "like", found only from the animals (no weight, no tiers); the oven's recipe for meat (raw meat
                roasted into the Well Done Steak); raw meat among the meats of the recipes whose part is "meat" (928's stew and pie).
                Idempotent: its own items and recipes taken out first. Run after 928 (whose items it adds to).
  animals       brokenspire: the farm animals' hit points and things (TownAnimals' Health and Drops: RD/RDList14g.cpp).
  icons <dir>   their pictures (rdm4_ui_gen.py / rdm4_ui_cut.py --export <dir>) on every map's UIArt.
"""
import json, os, sys, gc
import unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui_tex import ui_texture

SA = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "SourceArt")
J = json.load(open(os.path.join(SA, "wilderness", "farm_animals14.json"), encoding="utf-8"))
eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MAPS = "/Game/RandomDungeon/Maps/"
REPORT = []
KINDS = {"COMPONENT": unreal.RDItemKind.COMPONENT, "FOOD": unreal.RDItemKind.FOOD}


def each(maps, fn, label):
    for m in maps:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"{label}: no map {m}"); continue
        les.load_level(MAPS + m); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
        what = fn(g)
        g.modify(); les.save_current_level()
        g = None; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        REPORT.append(f"929 {label} {m}: {what}")


def items_fn(g):
    mine = {x["name"] for x in J["items"]}
    items = [i for i in g.get_editor_property("items") if str(i.name) not in mine]
    for X in J["items"]:
        like = next((i for i in items if str(i.name) == X["like"]), None)
        assert like, f"929 items: no {X['like']} on this map to copy"
        it = unreal.RDItemDef()
        for k in ("kind", "amount", "seconds", "icon", "looks", "found_max"): it.set_editor_property(k, like.get_editor_property(k))
        it.set_editor_property("name", X["name"]); it.set_editor_property("kind", KINDS[X["kind"]])
        for k in ("amount", "seconds"):
            if k in X: it.set_editor_property(k, float(X[k]))
        it.set_editor_property("icon", unreal.Name(X["icon"])); it.set_editor_property("looks", X["looks"])
        # (found only from the animals: no container's draw takes it)
        it.set_editor_property("weight", 0.0); it.set_editor_property("tiers", [])
        items.append(it)
    g.set_editor_property("items", items)
    have = {str(i.name) for i in items}
    # (the oven's recipes for meat (its own, by item, taken out first); raw meat among the meats of the "meat" parts)
    ov = {o["item"] for o in J["oven"]}
    recs = [r for r in g.get_editor_property("recipes") if not (str(r.item) in ov and str(r.station) == "Oven")]
    n_meat = 0
    for r in recs:
        ps = list(r.get_editor_property("parts")); changed = False
        for p in ps:
            if str(p.get_editor_property("label")) == J["meat_label"] and "Raw Meat" not in [str(a) for a in p.get_editor_property("any_of")]:
                p.set_editor_property("any_of", [unreal.Name("Raw Meat")] + list(p.get_editor_property("any_of"))); changed = True
        if changed: r.set_editor_property("parts", ps); n_meat += 1
    for o in J["oven"]:
        if o["item"] not in have: continue
        rc = unreal.RDRecipe(); rc.item = o["item"]; rc.station = "Oven"; rc.tier = 0
        pl = []
        for lb, any_of, n in o["parts"]:
            p = unreal.RDRecipePart(); p.label = lb; p.any_of = [unreal.Name(a) for a in any_of]; p.count = int(n); pl.append(p)
        rc.parts = pl; recs.append(rc)
    g.set_editor_property("recipes", recs)
    return f"{len(J['items'])} things, {len(J['oven'])} oven recipe(s), raw meat in {n_meat} recipes' meats"


def animals_fn(g):
    defs = list(g.get_editor_property("town_animals")); n = 0
    for d in defs:
        A = J["animals"].get(str(d.get_editor_property("name")))
        if not A: continue
        d.set_editor_property("health", float(A["health"])); d.set_editor_property("drops", A["drops"]); n += 1
    # (a struct read out of a list is a copy: the list written back)
    g.set_editor_property("town_animals", defs)
    return f"{n} of {len(defs)} kinds can be killed"


def icons(src):
    src = os.path.abspath(src)
    names = [x["icon"] for x in J["items"] if os.path.exists(os.path.join(src, f"{x['icon']}.png"))]
    assert names, f"929 icons: no picture in {src}"
    tex = {n: ui_texture(os.path.join(src, f"{n}.png"), "/Game/RandomDungeon/UI", f"T_RDM4_{n}") for n in names}
    def fn(g):
        ua = g.get_editor_property("ui_art")
        for n, t in tex.items():
            art = unreal.RDUIArt(); art.set_editor_property("texture", t)
            art.set_editor_property("border", unreal.Vector4(0, 0, 0, 0)); art.set_editor_property("inner", unreal.Vector4(0, 0, 1, 1))
            ua[unreal.Name(n)] = art
        g.set_editor_property("ui_art", ua)
        return ", ".join(tex)
    each(J["maps"], fn, "icons")


args = sys.argv[1:]
if args and args[0] == "items": each(J["maps"], items_fn, "items")
if args and args[0] == "animals": each(["brokenspire"], animals_fn, "animals")
if args and args[0] == "icons": icons(args[1])
for line in REPORT: print(line)
gc.collect()
