"""The list of 2026-11-26 (docs/improvements17.txt; the plan docs/improvements17_plan.md), Closed Structures on `brokenspire`:

    949_improvements17.py level   phase 5: the building level `town_building` (an empty map, made once: a closed building's door streams it
                                  in as a level instance, RD/RDBuilding17.cpp lays the building's furnishing in it), and brokenspire's
                                  generator pointed at it (BuildingLevel17), at the windows' view material (948's M_HT24_View: a cube
                                  sampled by the view's way) and at the pane's mesh (the engine's plane)

Run on the editor with any level open (it opens brokenspire at its end and saves it). The map is named to the cook by
pipeline/package_mistward.ps1."""
import sys, gc
import unreal

EAL = unreal.EditorAssetLibrary
LS = unreal.EditorLoadingAndSavingUtils
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MAP = "/Game/RandomDungeon/Maps/brokenspire"
BLD = "/Game/RandomDungeon/Maps/town_building"
VIEW = "/Game/RandomDungeon/HeavenTower/M_HT24_View"
PLANE = "/Engine/BasicShapes/Plane"
REPORT = []


def level():
    if not EAL.does_asset_exist(BLD):
        # (an empty map: nothing of its own, the furnishing is laid in play)
        w = LS.new_blank_map(False)
        ok = LS.save_map(w, BLD)
        REPORT.append(f"level: {BLD} made ({ok})")
    else:
        REPORT.append(f"level: {BLD} there")
    les.load_level(MAP)
    unreal.SystemLibrary.execute_console_command(None, "obj gc")
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    view = unreal.load_asset(VIEW); plane = unreal.load_asset(PLANE)
    assert view and plane, "949: the view material or the plane is missing (948 makes M_HT24_View)"
    g.set_editor_property("building_level17", BLD)
    g.set_editor_property("building_view_material17", view)
    g.set_editor_property("building_pane_mesh17", plane)
    g.modify(); les.save_current_level()
    REPORT.append(f"level: brokenspire's generator -> {BLD}, {view.get_name()}, {plane.get_name()}")
    del g


PARTS = {"level": level}
for t in (sys.argv[1:] or ["level"])[0].split(","): PARTS[t]()
for l in REPORT: print("949", l)
gc.collect()
