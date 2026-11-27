"""The list of 2026-11-26 (docs/improvements17.txt; the plan docs/improvements17_plan.md), Closed Structures on `brokenspire`:

    949_improvements17.py level   phase 5: the building level `town_building` (an empty map, made once: a closed building's door streams it
                                  in as a level instance, RD/RDBuilding17.cpp lays the building's furnishing in it), and brokenspire's
                                  generator pointed at it (BuildingLevel17), at the windows' view material (948's M_HT24_View: a cube
                                  sampled by the view's way) and at the pane's mesh (the engine's plane)

    949_improvements17.py rooms   phase 7: the rooms' pictures (SourceArt/list17/rooms/<key>.png, taken by 884 rooms17 from inside the
                                  game's own furnished rooms) imported as textures, the pane material M_B17_Pane (unlit: the picture dim
                                  by day, glowing by the instance's custom value 0 / 1 at night) and an instance a picture, and
                                  brokenspire's generator's RoomPanes17 keyed by the pictures' names

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


ROOMS = r"E:\code\claude-ue5\claude_ue5\SourceArt\list17\rooms"
RDIR = "/Game/RandomDungeon/List17/Rooms"
PANE = "/Game/RandomDungeon/List17/M_B17_Pane"
MEL = unreal.MaterialEditingLibrary


def pane_material():
    if EAL.does_asset_exist(PANE): return unreal.load_asset(PANE)          # (made once: a stage never deletes what the level uses)
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_B17_Pane", PANE.rsplit("/", 1)[0], unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("used_with_instanced_static_meshes", True)
    tx = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -700, 0)
    tx.set_editor_property("parameter_name", "Room")
    tc = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -950, 0)
    MEL.connect_material_expressions(tc, "", tx, "UVs")
    pc = MEL.create_material_expression(m, unreal.MaterialExpressionPerInstanceCustomData, -700, 300)
    pc.set_editor_property("data_index", 0)
    day = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, 420); day.set_editor_property("parameter_name", "Day"); day.set_editor_property("default_value", 0.45)
    night = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, 520); night.set_editor_property("parameter_name", "Night"); night.set_editor_property("default_value", 3.0)
    lp = MEL.create_material_expression(m, unreal.MaterialExpressionLinearInterpolate, -450, 380)
    MEL.connect_material_expressions(day, "", lp, "A"); MEL.connect_material_expressions(night, "", lp, "B"); MEL.connect_material_expressions(pc, "", lp, "Alpha")
    mu = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, 100)
    MEL.connect_material_expressions(tx, "RGB", mu, "A"); MEL.connect_material_expressions(lp, "", mu, "B")
    MEL.connect_material_property(mu, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); EAL.save_loaded_asset(m, False)
    st = MEL.get_statistics(m)
    REPORT.append(f"rooms: {PANE} made ({st.num_pixel_shader_instructions} pixel instructions)")
    return m


def rooms():
    import os
    pngs = sorted(f for f in os.listdir(ROOMS) if f.lower().endswith(".png"))
    assert pngs, "949 rooms: no pictures (884 rooms17 takes them)"
    tasks = []
    for f in pngs:
        t = unreal.AssetImportTask(); t.filename = os.path.join(ROOMS, f); t.destination_path = RDIR
        t.destination_name = "T_B17_" + f[:-4]; t.replace_existing = True; t.automated = True; t.save = True
        tasks.append(t)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    base = pane_material()
    mp = {}
    for f in pngs:
        key = f[:-4]
        tx = unreal.load_asset(f"{RDIR}/T_B17_{key}")
        assert tx, f"949 rooms: {key} not imported"
        tx.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD); EAL.save_loaded_asset(tx, False)
        ip = f"{RDIR}/MI_B17_{key}"
        mi = unreal.load_asset(ip) if EAL.does_asset_exist(ip) else unreal.AssetToolsHelpers.get_asset_tools().create_asset(f"MI_B17_{key}", RDIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        MEL.set_material_instance_parent(mi, base)
        MEL.set_material_instance_texture_parameter_value(mi, "Room", tx)
        EAL.save_loaded_asset(mi, False)
        got = MEL.get_material_instance_texture_parameter_value(mi, "Room")
        assert got and got.get_name() == tx.get_name(), f"949 rooms: {key}'s picture not taken"
        mp[key] = mi
    les.load_level(MAP)
    unreal.SystemLibrary.execute_console_command(None, "obj gc")
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    g.set_editor_property("room_panes17", {unreal.Name(k): v for k, v in mp.items()})
    g.modify(); les.save_current_level()
    REPORT.append(f"rooms: {len(mp)} pictures on brokenspire's generator: {', '.join(sorted(mp))}")
    del g


PARTS = {"level": level, "rooms": rooms}
for t in (sys.argv[1:] or ["level"])[0].split(","): PARTS[t]()
for l in REPORT: print("949", l)
gc.collect()
