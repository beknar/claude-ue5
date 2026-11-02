"""The user's list of 2026-11-02 (after Brokenspire's reel): "run is no longer mapped to the gamepad. make LB the block button
for the warrior and make LT to activate run. the castle's outer walls look strange being covered with arches ... create a day
night cycle where a full day can elapse within a half hour. the overhead village map should look more like [ai models/fairhill
village.jpg]".
- the Warrior's gamepad list on mistward_castle, brokenspire and random_dungeonmagic_level5 (the maps 870 wrote it on):
  "LT|switch walk / run" and "LB (hold)|block with the shield" (the C++: URDCombatComponent::TickBlocking holds the right
  mouse button or LB; LT switches every hero's run). A rerun of 870's filter had dropped her run line altogether.
- brokenspire: its day and night (bDayNight, DayLengthSeconds 1800: a day in half an hour of play; the morning's 8 o'clock
  for a new game; RD/RDTownDay.cpp)
Then run 882 (the castle's and the town wall's new pieces, the town built again) and 883 with the colour map's pictures.
Args: none"""
import unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MAPS = ["/Game/RandomDungeon/Maps/mistward_castle", "/Game/RandomDungeon/Maps/brokenspire", "/Game/RandomDungeon/Maps/random_dungeonmagic_level5"]


def warrior_pad(pad):
    """her list: no block on LT, no run on L3; LT runs (fourth), LB held blocks (after it)"""
    pad = [k for k in pad if not k.startswith(("LT (hold)|", "L3|", "LT|", "LB (hold)|"))]
    pad.insert(min(len(pad), 3), "LT|switch walk / run")
    pad.insert(min(len(pad), 4), "LB (hold)|block with the shield")
    return pad


for MAP in MAPS:
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    heroes = list(g.get_editor_property("heroes"))
    for h in heroes:
        if str(h.name) == "Warrior": h.controls_pad = warrior_pad(list(h.controls_pad))
    g.set_editor_property("heroes", heroes)
    w = next(h for h in g.get_editor_property("heroes") if str(h.name) == "Warrior")
    print("885", MAP.split("/")[-1], "Warrior pad:", list(w.controls_pad))
    if MAP.endswith("brokenspire"):
        for k, v in (("day_night", True), ("day_length_seconds", 1800.0), ("town_start_hour", 8.0), ("day_max_sun_elevation", 62.0),
                     # (the moon at 0.5 lux left the wall walk, which has no lamps, nearly black: 1.0)
                     ("moon_lux", 1.0)):
            g.set_editor_property(k, v)
        print("885 brokenspire day and night:", g.get_editor_property("day_night"), g.get_editor_property("day_length_seconds"), "s a day")
    les.save_current_level()
les.load_level(MAPS[1])
import gc
del g, heroes, w
gc.collect()
