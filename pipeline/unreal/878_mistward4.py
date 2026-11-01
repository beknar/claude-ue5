"""mistward_castle: the user's list of 2026-10-31, its switches (RD/RDMistward4.cpp, RDHUD.cpp, RDHeroSelect.cpp; the Martial
Artist's arm is in her clips, blender_numpy/martialartist_clips.py). On the castle's generator ("Mistward4"):
- bOptionsMenu   the Escape menu in two pages: Resume, Options, Choose another hero, Quit; Options: the four volumes, the
                 controls hint on / off, a resolution (the common ones no larger than the screen), a display mode, Apply, Back
- bAllySpacing   her allies keep apart (a summon called to a spot nobody stands on; they step away from each other)
- bSummonPanel   the HUD lists her summoned allies: how many of how many she may lead, each one's hit points
- bAllyMarkers   her allies marked on the minimap and the big map
On its menu's ARDHeroSelect (mistward_castle_select): bQuitButton (QUIT GAME in the upper right; Escape twice quits).
random_dungeonmagic_level5 keeps its menu and HUD as they were. Saves both maps; ends on mistward_castle. Args: none"""
import unreal
MAP = "/Game/RandomDungeon/Maps/mistward_castle"; SEL = MAP + "_select"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def open_map(m):
    if not ues.get_editor_world().get_path_name().startswith(m + "."): les.load_level(m)


open_map(SEL)
sel = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDHeroSelect))
sel.set_editor_property("quit_button", True); sel.modify(); les.save_current_level()
said = f"878 {SEL.split('/')[-1]}: quit button {sel.get_editor_property('quit_button')}"
del sel
open_map(MAP)
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
for p in ("options_menu", "ally_spacing", "summon_panel", "ally_markers"): gen.set_editor_property(p, True)
gen.modify(); les.save_current_level()
print(said)
print("878 mistward_castle: " + " | ".join(f"{p} {gen.get_editor_property(p)}" for p in ("options_menu", "ally_spacing", "summon_panel", "ally_markers", "escape_menu")))
import gc
del gen
gc.collect()
