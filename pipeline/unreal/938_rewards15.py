"""rewards15: the user's list of 2026-11-20 (docs/improvements15.txt, item 25: docs/wilderness_ideas.md's idea 4), its plan's twelfth
phase: rewards that last (C++ RD/RDList15k.cpp). From SourceArt/wilderness/rewards15.json:
- `items`: on every map of the game (its "maps"): the collectibles (copies of a crafting material with its picture, weight 0: never found
  in a chest) and the structures' named rings (copies of the strongest ring of their kind times their "times", weight 0), the ones of an
  earlier run taken out first (by name); a map with no item of a kind takes the first map's
- `data`: brokenspire's: the collectibles' kinds and glow, their share of the cells, the temple's trade, the ruins' treasure maps, the
  buried chest's things, gold and mesh (the dungeon's chest), the glow's mesh and material (made here), the structures' named items
Run after 910, 911, 918, 928, 929 and 937 (which write the maps' items anew). Args: [items,data]   (no argument: both)"""
import sys, os, json, gc, unreal
MAPS = "/Game/RandomDungeon/Maps/"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\wilderness"
MATS = "/Game/RandomDungeon/Wild15/Materials"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
eal = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary
J = json.load(open(os.path.join(SA, "rewards15.json"), encoding="utf-8"))
PARTS = (sys.argv[1] if len(sys.argv) > 1 else "items,data").split(",")
REPORT = []
KIND = {"Health": unreal.RDRingKind.HEALTH, "Magic": unreal.RDRingKind.MAGIC, "Dexterity": unreal.RDRingKind.DEXTERITY}
TEMPLATE = {}


def each(fn, label, maps):
    for m in maps:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"{label}: no map {m}"); continue
        les.load_level(MAPS + m); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
        what = fn(g)
        g.modify(); les.save_current_level()
        g = None; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        REPORT.append(f"938 {label} {m}: {what}")


def copy_of(text, name, **props):
    d = unreal.RDItemDef(); d.import_text(text); d.set_editor_property("name", name)
    for k, v in props.items(): d.set_editor_property(k, v)
    return d


def items(g):
    mine = {c["name"] for c in J["collectibles"]} | {p[1] for p in J["place_items"]}
    its = [i for i in g.get_editor_property("items") if str(i.get_editor_property("name")) not in mine]
    comp = [i for i in its if i.get_editor_property("kind") == unreal.RDItemKind.COMPONENT and str(i.get_editor_property("icon")) not in ("", "None")]
    if comp: TEMPLATE.setdefault("collectible", comp[0].export_text())
    assert "collectible" in TEMPLATE, "no crafting material on this map or the ones before it"
    added = []
    for c in J["collectibles"]:
        added.append(copy_of(TEMPLATE["collectible"], c["name"], weight=0.0, tiers=[], found_max=1))
    rings = [i for i in its if i.get_editor_property("kind") == unreal.RDItemKind.RING]
    for kind, name, rk, times in [(p[0], p[1], p[2], p[3]) for p in J["place_items"]]:
        same = [i for i in rings if i.get_editor_property("ring_kind") == KIND[rk] and i.get_editor_property("weight") > 0]
        if same:
            best = max(same, key=lambda i: i.get_editor_property("amount"))
            TEMPLATE.setdefault("ring:" + rk, best.export_text())
        assert ("ring:" + rk) in TEMPLATE, (rk, "no ring of that kind")
        d = copy_of(TEMPLATE["ring:" + rk], name, weight=0.0, tiers=[], found_max=1)
        d.set_editor_property("amount", round(float(d.get_editor_property("amount")) * float(times), 2))
        added.append(d)
    g.set_editor_property("items", its + added)
    return f"{len(J['collectibles'])} collectibles, {len(J['place_items'])} named rings"


def glow_material():
    path = MATS + "/M_RD_Glow15"
    m = unreal.load_asset(path) if eal.does_asset_exist(path) else unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_RD_Glow15", MATS, unreal.Material, unreal.MaterialFactoryNew())
    MEL.delete_all_material_expressions(m)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    v = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -600, 0)
    v.set_editor_property("parameter_name", "Color"); v.set_editor_property("default_value", unreal.LinearColor(1.0, 0.8, 0.4, 1.0))
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, 0)
    mul.set_editor_property("const_b", 6.0)
    assert MEL.connect_material_expressions(v, "", mul, "A")
    assert MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); eal.save_loaded_asset(m, False)
    return m


def data(g):
    have = {str(i.get_editor_property("name")) for i in g.get_editor_property("items")}
    missing = [c["name"] for c in J["collectibles"] if c["name"] not in have] + [p[1] for p in J["place_items"] if p[1] not in have]
    assert not missing, ("run 938 items first", missing[:5])
    known = {str(b.get_editor_property("name")) for b in g.get_editor_property("wild_biomes")}
    for c in J["collectibles"]:
        for b in c["biomes"]: assert b in known, (c["name"], b)
    sites = {str(k.get_editor_property("name")) for k in g.get_editor_property("wild_site_kinds")}
    for p in J["place_items"]: assert p[0] in sites, ("no structure kind", p[0])
    g.set_editor_property("collectible_kinds15", ["|".join([c["name"], ";".join(c["biomes"]), ",".join(f"{x:g}" for x in c["color"])]) for c in J["collectibles"]])
    g.set_editor_property("collectible_chance15", float(J["collectible_chance"]))
    g.set_editor_property("collectible_trade_n15", int(J["trade_n"]))
    t = J["treasure"]
    g.set_editor_property("treasure_map_chance15", float(t["map_chance"]))
    g.set_editor_property("treasure_chest_items15", int(t["items"]))
    g.set_editor_property("treasure_chest_gold15", float(t["gold"]))
    chest = g.get_editor_property("pieces").get(unreal.Name("Chest"))
    assert chest and chest.mesh, "no Chest piece"
    g.set_editor_property("treasure_chest_mesh15", chest.mesh)
    g.set_editor_property("reward_glow_mesh15", unreal.load_asset("/Engine/BasicShapes/Sphere"))
    g.set_editor_property("reward_glow_mat15", glow_material())
    g.set_editor_property("place_items15", [f"{p[0]}|{p[1]}" for p in J["place_items"]])
    return f"{len(J['collectibles'])} collectible kinds, chance {J['collectible_chance']}, trade {J['trade_n']}, maps {t['map_chance']}, chest {chest.mesh.get_name()}, {len(J['place_items'])} place items"


if "items" in PARTS: each(items, "items", J["maps"])
if "data" in PARTS: each(data, "data", ["brokenspire"])
for l in REPORT: print("REWARDS15", l)
gc.collect()
