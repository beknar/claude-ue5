"""The heroes' secondary abilities (the user's list of 2026-11-08b, docs/improvements9.txt, its sixth phase: "earned in the
wilderness by gathering materials and making Angel Tokens"), from SourceArt/balance/secondary.json, onto every map of the game
(brokenspire and the six dungeons):
- the generator's Secondaries (each ability: its hero, title, kind, numbers by rank, cooldowns, reach)
- the Angel Token (an item of kind Token: used, it raises an ability a rank) and the wilderness's two materials it is made from
  (Seraph Feather: the wilds' monsters drop it; Hallowed Stone: one at each ruin, ritual site and cave), none of them found in
  containers (weight 0)
- the token's recipe at the anvil (3 feathers and a stone)
- the generator's AngelTokenItem, SeraphFeatherItem / Chance, HallowedStoneItem / Kinds
C++ first (RD/RDSecondary.cpp). Rerun after anything that writes the levels' items or recipes anew (857, 875, 910).
Args: [map ...] (default: all seven)"""
import os, sys, json, unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "claude_ue5", "SourceArt"))
D = json.load(open(os.path.join(SA, "balance", "secondary.json"), encoding="utf-8"))
ALL = ["brokenspire", "mistward_castle", "vel_morrath", "war_engine", "sewers", "kethrys_spire", "heaven_fortress"]
MAPS = [a for a in sys.argv[1:] if a in ALL] or ALL
KIND = {"active": unreal.RDSecondaryKind.ACTIVE, "toggle": unreal.RDSecondaryKind.TOGGLE, "passive": unreal.RDSecondaryKind.PASSIVE}
TOKEN = D["token"]; MATS = D["materials"]
OURS = {TOKEN["item"]} | {m["item"] for m in MATS}


def open_map(m):
    path = "/Game/RandomDungeon/Maps/" + m
    if not ues.get_editor_world().get_path_name().startswith(path + "."):
        les.load_level(path); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    w = ues.get_editor_world(); assert w.get_path_name().startswith(path + "."), w.get_path_name()
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def item(name, kind, icon, looks):
    it = unreal.RDItemDef()
    it.set_editor_property("name", name); it.set_editor_property("kind", kind); it.set_editor_property("icon", icon)
    it.set_editor_property("looks", looks); it.set_editor_property("weight", 0.0); it.set_editor_property("amount", 0.0)
    it.set_editor_property("found_max", 99)
    return it


for m in MAPS:
    g = open_map(m)
    # ---- the abilities
    defs = []
    for a in D["abilities"]:
        s = unreal.RDSecondaryDef()
        s.set_editor_property("name", a["id"]); s.set_editor_property("hero", a["hero"]); s.set_editor_property("title", a["title"])
        s.set_editor_property("text", a["text"]); s.set_editor_property("kind", KIND[a["kind"]])
        for k, p in (("values", "values"), ("values2", "values2"), ("seconds", "seconds"), ("cooldowns", "cooldowns")):
            s.set_editor_property(p, [float(x) for x in a.get(k, [])])
        s.set_editor_property("reach", float(a.get("reach", 0)))
        s.set_editor_property("share", float(a.get("missile_share", a.get("back_share", a.get("stagger", 0.0)))))
        s.set_editor_property("look_spell", a.get("look_spell", "None"))
        s.set_editor_property("chooses_spell", bool(a.get("boost", False)))
        defs.append(s)
    g.set_editor_property("secondaries", defs)
    # ---- the items: the token and its materials (made again: ours taken out first)
    items = [i for i in g.get_editor_property("items") if str(i.get_editor_property("name")) not in OURS]
    items.append(item(TOKEN["item"], unreal.RDItemKind.TOKEN, TOKEN["icon"], TOKEN["looks"]))
    for mt in MATS: items.append(item(mt["item"], unreal.RDItemKind.COMPONENT, mt["icon"], mt["looks"]))
    g.set_editor_property("items", items)
    # ---- the token's recipe at the anvil
    rec = [r for r in g.get_editor_property("recipes") if str(r.get_editor_property("item")) != TOKEN["item"]]
    r = unreal.RDRecipe(); r.set_editor_property("item", TOKEN["item"]); r.set_editor_property("tier", 0)
    parts = []
    for nm, n in TOKEN["recipe"]:
        p = unreal.RDRecipePart(); p.set_editor_property("label", nm.lower()); p.set_editor_property("any_of", [nm]); p.set_editor_property("count", int(n))
        parts.append(p)
    r.set_editor_property("parts", parts)
    rec.append(r)
    g.set_editor_property("recipes", rec)
    # ---- the generator's own
    g.set_editor_property("angel_token_item", TOKEN["item"])
    feather = next(x for x in MATS if x["from"] == "wild monsters"); stone = next(x for x in MATS if x["from"] == "wild places")
    g.set_editor_property("seraph_feather_item", feather["item"]); g.set_editor_property("seraph_feather_chance", float(feather["chance"]))
    g.set_editor_property("hallowed_stone_item", stone["item"]); g.set_editor_property("hallowed_kinds", stone["kinds"])
    g.modify()
    les.save_current_level()
    print("SEC", m, len(defs), "abilities,", len(items), "items,", len(rec), "recipes")
    del g, items, rec, defs
import gc
gc.collect()
