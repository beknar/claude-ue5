"""The user's list of 2026-11-08b (docs/improvements9.txt), its third phase: the dungeons' keys in order. On every map of the
packaged game (brokenspire, mistward_castle, vel_morrath, war_engine, sewers) the generator's DungeonChain (from
SourceArt/dungeons/chain.json: "<dungeon key>|<level>|<town>|<title>|<key item>|<map item>") and each dungeon's key and map as
items of kind Key (weight 0: never in a container; the vault key's picture if it has one, none yet for a map). C++ (RD/RDKeys.cpp): the way
into a town's dungeon refused without its key, the dungeon's boss dropping the next key and map, the map revealing the road, the
keys kept at a death; the wilderness's tiers along the chain of towns (FRDWildWorld::TierAt). Run with play stopped, C++ first.
Args: none   e.g.  ue_exec.py 905_dungeon_keys.py"""
import unreal, os, json, gc

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHAIN = os.path.join(REPO, "claude_ue5", "SourceArt", "dungeons", "chain.json")
MAPS = "/Game/RandomDungeon/Maps/"
GAME_MAPS = ("brokenspire", "mistward_castle", "vel_morrath", "war_engine", "sewers")
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
REPORT = []


def open_map(m):
    if not ues.get_editor_world().get_path_name().startswith(m + "."): les.load_level(m)
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def main():
    J = json.load(open(CHAIN, encoding="utf-8"))
    lines = [f'{c["key"]}|{c["level"]}|{c["town"]}|{c["title"]}|{c["key_item"]}|{c["map_item"]}' for c in J["chain"]]
    for m in GAME_MAPS:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"no map {m}"); continue
        g = open_map(MAPS + m)
        g.set_editor_property("dungeon_chain", lines)
        items = list(g.get_editor_property("items"))
        # (the vault key's picture, if it has one: not one of the chain's own items (a run before gave them pictures))
        ours = {c[k] for c in J["chain"] for k in ("key_item", "map_item") if c[k]}
        key_icon = next((i.get_editor_property("icon") for i in items if i.get_editor_property("kind") == unreal.RDItemKind.KEY and str(i.get_editor_property("name")) not in ours
                         and str(i.get_editor_property("icon")) != "None"), unreal.Name("None"))
        # (no picture of a map yet: a scroll's would read as a spell scroll; the inventory shows the name)
        map_icon = unreal.Name("None")
        names = set()
        for c in J["chain"]:
            for nm, looks, icon in ((c["key_item"], c.get("key_looks", ""), key_icon), (c["map_item"], c.get("map_looks", ""), map_icon)):
                if not nm: continue
                names.add(nm)
                it = unreal.RDItemDef()
                it.set_editor_property("name", unreal.Name(nm)); it.set_editor_property("kind", unreal.RDItemKind.KEY)
                it.set_editor_property("amount", 0.0); it.set_editor_property("weight", 0.0)
                it.set_editor_property("icon", icon); it.set_editor_property("looks", looks)
                k = next((i for i, x in enumerate(items) if str(x.get_editor_property("name")) == nm), -1)
                if k >= 0: items[k] = it
                else: items.append(it)
        g.set_editor_property("items", items)
        les.save_current_level()
        unreal.SystemLibrary.execute_console_command(None, "obj gc")
        REPORT.append(f"{m}: {len(lines)} links, {len(names)} key and map items (icons {key_icon}, {map_icon})")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        REPORT.append(f"FAILED {e!r}"); traceback.print_exc()
    print("905 " + " | ".join(REPORT))
    del les, ues, eas, eal
    gc.collect()
