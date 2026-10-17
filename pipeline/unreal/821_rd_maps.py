"""The dungeon levels' maps as tactical maps (the generator's bTacticalMaps, ARDHUD): the minimap is dark monochrome
terrain with a feathered rim and no frame, under bright markers (monsters red dots, the strongest of their tier orange
triangles, unopened chests and trunks gold stars, hallway exits into sections not yet generated cyan diamonds); the big map
(M, Back) is a see-through wireframe of the walls, doorways and passage borders over the game, centred on her and north
up, with the same markers, while the game goes on under it (she moves and fights). Sets it on every dungeon level and
saves each: random_dungeon_level, its Cine copy, random_dungeoncombat_level and the three magic levels. Args: [off]"""
import sys, unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ON = "off" not in sys.argv
LEVELS = ["random_dungeon_level", "random_dungeon_level_Cine", "random_dungeoncombat_level", "random_dungeonmagic_level", "random_dungeonmagic_level2", "random_dungeonmagic_level3"]
start = ues.get_editor_world().get_path_name()
order = sorted(LEVELS, key=lambda n: start.endswith("/" + n + "." + n))          # (the open level last: it is never reloaded)
for n in order:
    path = f"/Game/RandomDungeon/Maps/{n}"
    if not ues.get_editor_world().get_path_name().startswith(path + "."): les.load_level(path)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(path + "."), w.get_path_name()
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    g.set_editor_property("tactical_maps", ON); les.save_current_level()
    print(f"RDMAPS {n}: tactical maps {g.get_editor_property('tactical_maps')}")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
