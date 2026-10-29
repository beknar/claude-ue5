"""martial_arts (the user's of 2026-10-28): a basic one-room dungeon level with the Martial Artist alone, every one of her
abilities on, to try her form and function. A Save As copy of mistward_castle (after 872, which put her there) with:
- the generator's bOneRoom: the start section plans its great hall alone (OneRoomTiles 10 a side: 30 m), with no doors, no
  hallways and no other section; three monsters of tier 1 stand in it, one more 4 s after one falls (TickOneRoom)
- bUnlockAll: all ten of her chi attacks are hers from the start
- bInfiniteMana: no mana is ever taken; bChiWithoutTarget: a chi attack with no monster in range goes off all the same,
  its bolt flying straight ahead to the end of its 4 m (the user's of 2026-10-28, to try the moves on their own)
- her alone among the heroes (DefaultHero), no menu (MenuLevel empty), one tier, none of the castle's traps, special
  rooms, ring guards, teleporters or prisoners
Run as `873 saveas` (it saves the copy and quits the editor: a copied map is opened only after a restart), then, the
editor started again, `873` (it sets the copy up, builds its start section and saves it). Args: [saveas]"""
import sys, unreal
SRC, DST = "/Game/RandomDungeon/Maps/mistward_castle", "/Game/RandomDungeon/Maps/martial_arts"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
HERO = "MartialArtist"
if len(sys.argv) > 1 and sys.argv[1] == "saveas":
    assert not eal.does_asset_exist(DST), "martial_arts exists: set it up with 873 (no argument)"
    if not ues.get_editor_world().get_path_name().startswith(SRC + "."): les.load_level(SRC)
    ok = unreal.EditorLoadingAndSavingUtils.save_map(ues.get_editor_world(), DST)
    print("MARTIAL saved as", DST, ok, "| quitting: start the editor again and run 873")
    unreal.SystemLibrary.quit_editor()
else:
    if not ues.get_editor_world().get_path_name().startswith(DST + "."): les.load_level(DST)
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    heroes = [h for h in gen.get_editor_property("heroes") if str(h.name) == HERO]; assert heroes, "872 first: no Martial Artist on mistward_castle"
    gen.set_editor_property("heroes", heroes)
    for k, v in (("default_hero", HERO), ("menu_level", ""), ("dungeon_title", "Martial Arts"), ("max_tier", 1),
                 ("one_room", True), ("one_room_tiles", 10), ("one_room_monsters", 3), ("one_room_respawn", 4.0), ("unlock_all", True),
                 ("infinite_mana", True), ("chi_without_target", True),
                 ("special_rooms", False), ("ring_guards", False), ("teleporters", False), ("trap_room_share", 0.0), ("trap_hall_share", 0.0),
                 ("boss_slashes", False), ("weapon_pickups", False)):
        try: gen.set_editor_property(k, v)
        except Exception as e: print("MARTIAL (no", k, ")", e)
    gen.set_editor_property("prisoner_defs", [])
    gen.modify(); gen.build_start_section()
    les.save_current_level()
    s = gen.get_section(unreal.IntPoint(0, 0)) if hasattr(gen, "get_section") else None
    print("MARTIAL", DST, "| heroes", [str(h.name) for h in gen.get_editor_property("heroes")], "| one room", gen.get_editor_property("one_room"),
          gen.get_editor_property("one_room_tiles"), "| unlock all", gen.get_editor_property("unlock_all"), "| title", gen.get_editor_property("dungeon_title"))
import gc
gc.collect()
