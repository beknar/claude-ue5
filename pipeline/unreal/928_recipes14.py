"""The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), its sixth phase (item 4): "recipes
can be found to make more advanced food, more advanced potions, more advanced scrolls".

Parts (args):
  items         SourceArt/balance/recipes14.json's advanced things written on every map of the game (its "maps"): each item copied
                from its "like" with its numbers, buff, picture and game tiers (its tier, +5, ... to 30, as 910 bands the
                consumables); its recipe (the oven's for food, the alchemist's or librarian's tables' by kind); and its recipe item
                ("<item> Recipe", ERDItemKind::Recipe, Teaches the item, the same tiers, a weight in the containers' draws); then
                bRecipes14 (an advanced recipe refused until its recipe is read: RD/RDList14e.cpp). Idempotent: its own items,
                recipe items and recipes taken out first, by name.
  wild          brokenspire: the wilds' ruins' and structures' chests given "@recipe" (its "wild_loot"): a recipe of the land's tier
                where the chest stands (WildRuinKinds' and WildSiteKinds' Loot, any earlier "@recipe" line taken out first).
  icons <dir>   the pictures painted for them (rdm4_ui_gen.py / rdm4_ui_cut.py --export <dir>) imported and given to every map's
                UIArt under their names.
Run after 910, 905, 911, 918, 925, 926 and 927 tables (910 bands the consumables' tiers and remakes its own copies; 927 tables
switches the alchemist's and librarian's tables on); run again after any of them.
"""
import json, os, sys, gc
import unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ui_tex import ui_texture

SA = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "SourceArt")
J = json.load(open(os.path.join(SA, "balance", "recipes14.json"), encoding="utf-8"))
eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MAPS = "/Game/RandomDungeon/Maps/"
REPORT = []
KINDS = {"HEALING": unreal.RDItemKind.HEALING, "MANA": unreal.RDItemKind.MANA, "SPEED": unreal.RDItemKind.SPEED, "FOOD": unreal.RDItemKind.FOOD,
         "SCROLL": unreal.RDItemKind.SCROLL}


def each(maps, fn, label):
    for m in maps:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"{label}: no map {m}"); continue
        les.load_level(MAPS + m); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
        what = fn(g)
        g.modify(); les.save_current_level()
        # (the generator let go before the next map loads (PR #78's review))
        g = None; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        REPORT.append(f"928 {label} {m}: {what}")


def band(t): return list(range(int(t), 31, 5))


def items_fn(g):
    RI = J["recipe_item"]
    mine = {x["name"] for x in J["items"]} | {x["name"] + RI["suffix"] for x in J["items"]}
    items = [i for i in g.get_editor_property("items") if str(i.name) not in mine]
    recs = [r for r in g.get_editor_property("recipes") if str(r.item) not in mine]
    spells = {str(s.name) for s in g.get_editor_property("spells")}
    have = {str(i.name) for i in items}
    made, missing = [], []
    for X in J["items"]:
        like = next((i for i in items if str(i.name) == X["like"]), None)
        assert like, f"928 items: no {X['like']} on this map to copy"
        if X.get("spell") and X["spell"] not in spells: missing.append(f"spell {X['spell']}"); continue
        for pt in X["parts"]:
            if not any(n in have for n in pt[1]): missing.append(f"{X['name']}: no {pt[1]}")
        it = unreal.RDItemDef()
        for k in ("kind", "amount", "seconds", "weight", "icon", "looks", "tiers", "found_max", "spell"): it.set_editor_property(k, like.get_editor_property(k))
        it.set_editor_property("name", X["name"]); it.set_editor_property("kind", KINDS[X["kind"]])
        for k in ("amount", "seconds"):
            if k in X: it.set_editor_property(k, float(X[k]))
        if X.get("spell"): it.set_editor_property("spell", unreal.Name(X["spell"]))
        it.set_editor_property("icon", unreal.Name(X["icon"])); it.set_editor_property("tiers", band(X["tier"]))
        # (never found made: only its recipe makes it (PR #83's review); the containers' and shelves' draws pass it by)
        it.set_editor_property("weight", 0.0)
        if X.get("buff"):
            it.set_editor_property("buff_kind", unreal.Name(X["buff"][0])); it.set_editor_property("buff_amount", float(X["buff"][1])); it.set_editor_property("buff_seconds", float(X["buff"][2]))
        items.append(it)
        st = X.get("station", "")
        rc = unreal.RDRecipe(); rc.item = X["name"]; rc.tier = int(X["tier"]); rc.station = st
        ps = []
        for lb, any_of, n in X["parts"]:
            p = unreal.RDRecipePart(); p.label = lb; p.any_of = [unreal.Name(a) for a in any_of if a in have]; p.count = int(n); ps.append(p)
        rc.parts = ps
        recs.append(rc)
        # (its recipe: kept, read once; its picture by where the thing is made)
        r = unreal.RDItemDef()
        for k in ("found_max",): r.set_editor_property(k, like.get_editor_property(k))
        r.set_editor_property("name", X["name"] + RI["suffix"]); r.set_editor_property("kind", unreal.RDItemKind.RECIPE)
        # (its weight among the recipes when one is drawn: the containers draw recipes apart, on a stream of their own)
        r.set_editor_property("amount", 0.0); r.set_editor_property("seconds", 0.0); r.set_editor_property("weight", float(RI["weight"]))
        where = st if st else ("Librarian" if X["kind"] == "SCROLL" else "Alchemist")
        r.set_editor_property("icon", unreal.Name(RI["icons"][where])); r.set_editor_property("tiers", band(X["tier"]))
        r.set_editor_property("teaches", unreal.Name(X["name"]))
        r.set_editor_property("looks", f"a recipe for the {X['name'].lower()}")
        items.append(r)
        made.append(X["name"])
    g.set_editor_property("items", items); g.set_editor_property("recipes", recs)
    g.set_editor_property("recipes14", True)
    assert not missing, f"928 items: {missing}"
    return f"{len(made)} advanced things, their recipes and recipe items"


def wild_fn(g):
    tok = J["wild_loot"]; n = 0
    for prop in ("wild_ruin_kinds", "wild_site_kinds"):
        ks = list(g.get_editor_property(prop))
        for k in ks:
            lines = [l for l in str(k.get_editor_property("loot")).split(";") if l and not l.startswith("@recipe")]
            k.set_editor_property("loot", ";".join(lines + [tok])); n += 1
        # (a struct read out of a list is a copy: the list is written back (the rules' 920 lesson))
        g.set_editor_property(prop, ks)
    return f"{n} kinds' chests hold a recipe ({tok})"


def icons(src):
    src = os.path.abspath(src)
    names = sorted({x["icon"] for x in J["items"]} | set(J["recipe_item"]["icons"].values()))
    names = [n for n in names if os.path.exists(os.path.join(src, f"{n}.png"))]
    assert names, f"928 icons: no picture in {src} (rdm4_ui_cut.py --export)"
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
if args and args[0] == "wild": each(["brokenspire"], wild_fn, "wild")
if args and args[0] == "icons": icons(args[1])
for line in REPORT: print(line)
gc.collect()
