"""random_dungeonmagic_level4: the menu first. Sets the generator's MenuLevel to the menu level
(random_dungeonmagic_level4_select, 826): the dungeon played without ?Hero= (Play in the editor) opens the menu,
which opens the dungeon again with ?Hero=<her name>. The console variable rd.HeroMenu 0 skips it (828 sets it for
the scripted tests, 815 for the reel's renders, and both set it back to 1). Saves the level and reads it back.
No arguments."""
import unreal

LEVEL = "/Game/RandomDungeon/Maps/random_dungeonmagic_level4"
SELECT = "/Game/RandomDungeon/Maps/random_dungeonmagic_level4_select"
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
if w is None or w.get_name() != "random_dungeonmagic_level4":
    unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
gens = [a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator)]
if not gens:
    raise SystemExit("831: no RDDungeonGenerator in random_dungeonmagic_level4")
gens[0].set_editor_property("menu_level", SELECT)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("831 menu level:", gens[0].get_editor_property("menu_level"), "| heroes", len(gens[0].get_editor_property("heroes")),
      "| default", gens[0].get_editor_property("default_hero"))
del gens, w
