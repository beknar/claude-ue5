"""mistward_castle (the user's of 2026-10-26, docs/improvements.txt): random_dungeonmagic_level5 as it is, with the rules
of that list (864 its themes' pieces, 865 its items, traps, prisoners and switches, 866 the monsters' height, 867 its
test). Five tiers named Mistward Castle: the stone dungeon and crypt (tier 1), the castle keep and its cells (tier 2), the
dwarven deep halls (tier 3), all three mixed (tiers 4 and 5).
First run (the level does not exist yet): opens random_dungeonmagic_level5 and saves it as /Game/RandomDungeon/Maps/
mistward_castle (Save As: a map is never duplicated), then stops: RESTART THE EDITOR and run it again. With the copy there
it opens it and sets what makes it Mistward's own: its name (DungeonTitle), its menu (MenuLevel: mistward_castle_select,
made by 826 with the argument mistward), saves it. Args: none"""
import unreal
eal = unreal.EditorAssetLibrary
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SRC = "/Game/RandomDungeon/Maps/random_dungeonmagic_level5"; MAP = "/Game/RandomDungeon/Maps/mistward_castle"
def done():
    import gc
    for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
    gc.collect()
if not eal.does_asset_exist(MAP):
    if not ues.get_editor_world().get_path_name().startswith(SRC + "."): les.load_level(SRC)
    assert ues.get_editor_world().get_path_name().startswith(SRC + "."), ues.get_editor_world().get_path_name()
    ok = unreal.EditorLoadingAndSavingUtils.save_map(ues.get_editor_world(), MAP)
    print("MISTWARD copied" if ok else "MISTWARD copy FAILED", SRC, "->", MAP, "| restart the editor, then run 863 again")
else:
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(MAP + "."), w.get_path_name()
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    gen.set_editor_property("dungeon_title", "Mistward Castle")
    gen.set_editor_property("menu_level", MAP + "_select")
    gen.set_editor_property("max_tier", 5)
    les.save_current_level()
    print("MISTWARD", MAP, "| title", gen.get_editor_property("dungeon_title"), "| menu", gen.get_editor_property("menu_level"), "| tiers", gen.get_editor_property("max_tier"))
done()
