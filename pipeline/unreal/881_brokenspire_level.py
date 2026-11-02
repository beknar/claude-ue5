"""Brokenspire (docs/brokenspire.txt, the user's of 2026-11-02): the starting town, a hub for Mistward Castle.
First run (the level does not exist yet): opens mistward_castle and saves it as /Game/RandomDungeon/Maps/brokenspire (Save
As: a map is never duplicated), then stops: RESTART THE EDITOR and run it again.
With the copy there:
- brokenspire: its generator's town switches (bTown: the start section is the town, ARDSection::PlanTown; bTownLink: gold,
  her things and the purse kept between the levels), one 504 m section (SectionTiles 168), its name, where the Mistgate
  leads (CastleLevel), the village's ground material, no start-room items; outdoor light (a low sun, a sky light and the
  atmosphere, the castle's haze thinned into a mist), a ground to the horizon (the village's far ground); its start section
  is built by 882 (the town's pieces and people first)
- mistward_castle: bTownLink and the way back (TownLevel)
- mistward_castle_select (the hero menu): it opens Brokenspire now (a new game)
Args: none"""
import unreal
eal = unreal.EditorAssetLibrary
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SRC = "/Game/RandomDungeon/Maps/mistward_castle"; MAP = "/Game/RandomDungeon/Maps/brokenspire"; MENU = SRC + "_select"
TAG = unreal.Name("bs_level")
V = unreal.Vector


def done():
    import gc
    for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
    gc.collect()


def open_map(p):
    if not ues.get_editor_world().get_path_name().startswith(p + "."): les.load_level(p)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(p + "."), w.get_path_name()
    return w


def gen_of():
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


if not eal.does_asset_exist(MAP):
    open_map(SRC)
    ok = unreal.EditorLoadingAndSavingUtils.save_map(ues.get_editor_world(), MAP)
    print("BROKENSPIRE copied" if ok else "BROKENSPIRE copy FAILED", SRC, "->", MAP, "| restart the editor, then run 881 again")
else:
    # ---- the town
    w = open_map(MAP)
    g = gen_of()
    for k, v in (("town", True), ("town_link", True), ("section_tiles", 168), ("dungeon_title", "Brokenspire"), ("town_name", "Brokenspire"),
                 ("castle_level", SRC), ("town_level", MAP), ("menu_level", MENU), ("town_new_seed", True), ("start_seed", 20261102),
                 ("town_ground_material", unreal.load_asset("/Game/RandomIsoVillage/Materials/M_IV_Ground")), ("start_room_items", []),
                 ("reveal_effect", False)):
        g.set_editor_property(k, v)
    # (what stood in the castle's saved start set goes with it: 882 builds the town)
    for a in eas.get_all_level_actors():
        if a.tags and TAG in a.tags: eas.destroy_actor(a)
    # outdoor light: a low evening sun through the mist, the sky's light, the atmosphere
    sun = eas.spawn_actor_from_class(unreal.DirectionalLight, V(0, 0, 3000), unreal.Rotator(roll=0.0, pitch=-24.0, yaw=128.0))
    sun.set_actor_label("BS_Sun"); sun.tags = [TAG]
    lc = sun.light_component
    lc.set_editor_property("intensity", 7.5); lc.set_editor_property("light_color", unreal.Color(255, 214, 170, 255))
    lc.set_editor_property("atmosphere_sun_light", True); lc.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    sky = eas.spawn_actor_from_class(unreal.SkyAtmosphere, V(0, 0, 0)); sky.set_actor_label("BS_Sky"); sky.tags = [TAG]
    sl = eas.spawn_actor_from_class(unreal.SkyLight, V(0, 0, 500)); sl.set_actor_label("BS_SkyLight"); sl.tags = [TAG]
    slc = sl.light_component
    slc.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE); slc.set_editor_property("real_time_capture", True); slc.set_editor_property("intensity", 1.6)
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.ExponentialHeightFog):
            fc = a.component
            fc.set_editor_property("fog_density", 0.012); fc.set_editor_property("fog_height_falloff", 0.06)
            fc.set_editor_property("fog_inscattering_luminance", unreal.LinearColor(0.42, 0.45, 0.5, 1.0))
            fc.set_editor_property("enable_volumetric_fog", True)
    # the ground beyond the town to the horizon (4 km, a little under the town's own)
    far = eas.spawn_actor_from_class(unreal.StaticMeshActor, V(0, 0, -6))
    far.set_actor_label("BS_FarGround"); far.tags = [TAG]
    smc = far.static_mesh_component
    smc.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Plane")); smc.set_material(0, unreal.load_asset("/Game/RandomIsoVillage/Materials/MI_IV_FarGround"))
    far.set_actor_scale3d(V(4000, 4000, 1)); smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    les.save_current_level()
    print("BROKENSPIRE", MAP, "| town", g.get_editor_property("town"), "| tiles", g.get_editor_property("section_tiles"), "| castle", g.get_editor_property("castle_level"))
    # ---- the castle: the way back, gold and her things kept
    open_map(SRC)
    g = gen_of()
    g.set_editor_property("town_link", True); g.set_editor_property("town_level", MAP); g.set_editor_property("town_name", "Brokenspire")
    les.save_current_level()
    print("MISTWARD town link", g.get_editor_property("town_link"), g.get_editor_property("town_level"))
    # ---- the hero menu opens the town
    open_map(MENU)
    sel = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDHeroSelect))
    sel.set_editor_property("target_level", MAP)
    les.save_current_level()
    print("MENU opens", sel.get_editor_property("target_level"))
    open_map(MAP)
done()
