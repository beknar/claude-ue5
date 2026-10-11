"""sf-city-level player setup:
- PlayerStart on the dock boulevard between the Port Authority / Hab Apartment and the Noodle Bar, facing the road head (-Y)
- World Kill Z -25000 (far below every walkable surface, so the fall guard always acts first)
- BP_SFC_Fem5Character (child of BP_JRPGFem5Character, capsule radius 36) + BP_SFC_GameMode as the level's game mode
- BP_SFC_FallGuard (safety net behind the 708 barrier walls): remembers the player's last grounded location and, if she
  ever drops below FloorZ, teleports her back there (counts Catches, prints a message). Also unsticks her: airborne but
  motionless for 0.75 s (wedged between a steep surface - a parked car's hood - and a barrier wall) -> back to the last safe spot
  (counts Unsticks). Placed once, tag 'sfc_start'.
Args: [floor_z]  (default -2500: the lowest walkable surface is the Monolith landscape, about -330)"""
import sys, unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
FLOORZ = float(sys.argv[1]) if len(sys.argv) > 1 else -2500.0
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert w.get_path_name().startswith("/Game/SFCityLevel/Maps/sf-city-level."), w.get_path_name()
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_current_level_by_name("sf-city-level")
TAG = unreal.Name("sfc_start")
for a in eas.get_all_level_actors():
    if TAG in a.tags or isinstance(a, unreal.PlayerStart): eas.destroy_actor(a)
START = unreal.Vector(-15000, -46500, 32 + 95)
ps = eas.spawn_actor_from_class(unreal.PlayerStart, START, unreal.Rotator(roll=0, pitch=0, yaw=-90)); ps.tags = [TAG]; ps.set_actor_label("SFC_PlayerStart"); ps.set_folder_path("SFC")
ws = w.get_world_settings(); ws.set_editor_property("kill_z", -25000.0)
# ---- level character: child of BP_JRPGFem5Character with a 36 cm capsule. Her clips swing hands / feet up to 34 cm to the
# side of the capsule axis (run arms 32, land arms 34, idle feet 31): with the stock 28 cm they brushed into walls and counters.
G = "/Game/SFCityLevel/Blueprints"; CH = f"{G}/BP_SFC_Fem5Character"; GM = f"{G}/BP_SFC_GameMode"
if not eal.does_asset_exist(CH):
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.load_asset("/Game/JRPG/Game/BP_JRPGFem5Character").generated_class())
    at.create_asset("BP_SFC_Fem5Character", G, unreal.Blueprint, f)
chbp = unreal.load_asset(CH); unreal.BlueprintEditorLibrary.compile_blueprint(chbp)
cap = unreal.get_default_object(chbp.generated_class()).get_component_by_class(unreal.CapsuleComponent)
cap.set_editor_property("capsule_radius", 36.0); eal.save_loaded_asset(chbp, only_if_is_dirty=False)
if not eal.does_asset_exist(GM): eal.duplicate_asset("/Game/JRPG/Game/BP_JRPGFem5GameMode", GM)
gm = unreal.load_asset(GM); unreal.get_default_object(gm.generated_class()).set_editor_property("default_pawn_class", chbp.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(gm); eal.save_loaded_asset(gm, only_if_is_dirty=False)
ws.set_editor_property("default_game_mode", gm.generated_class())
print("game mode", gm.get_name(), "-> pawn", chbp.get_name(), "capsule r", unreal.get_default_object(chbp.generated_class()).get_component_by_class(unreal.CapsuleComponent).get_editor_property("capsule_radius"))
# ---- fall guard blueprint
PATH = "/Game/SFCityLevel/Blueprints/BP_SFC_FallGuard"
if not eal.does_asset_exist(PATH):
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.Actor)
    bp = at.create_asset("BP_SFC_FallGuard", "/Game/SFCityLevel/Blueprints", unreal.Blueprint, f)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
bp = unreal.load_asset(PATH)
cdo0 = unreal.get_default_object(bp.generated_class())
for nm, typ in (("FloorZ", "float"), ("Safe", "vector"), ("Catches", "int"), ("StuckT", "float"), ("Unsticks", "int")):
    try: cdo0.get_editor_property(nm)
    except Exception: T.add_variable(bp, nm, typ); T.set_variable_instance_editable(bp, nm, True)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
CM = "(Class|Character|GetCharacterMovement :self ch)"
TICK = f"""
(event EventTick (DeltaSeconds)
  (bind ch (Utilities|Casting|CastToCharacter :Object (Game|GetPlayerPawn :PlayerIndex 0))
    (:then
      (bind loc (Transformation|GetActorLocation :self ch))
      (if (< (.z loc) (Variables|Default|GetFloorZ))
        (Transformation|SetActorLocation :self ch :NewLocation (Math|Vector|MakeVector (.x (Variables|Default|GetSafe)) (.y (Variables|Default|GetSafe)) (+ (.z (Variables|Default|GetSafe)) 30.0)) :bTeleport true)
        (Components|Movement|StopMovementImmediately :self {CM})
        (Variables|Default|SetCatches (+ (Variables|Default|GetCatches) 1))
        (Development|PrintString :InString "SFC fall guard: caught a fall, returned to the last safe spot")
        (else
          (if (Movement|IsMovingonGround :self {CM})
            (Variables|Default|SetSafe loc)
            (Variables|Default|SetStuckT 0.0)
            (else
              (if (< (Math|Vector|VectorLength (Transformation|GetVelocity :self ch)) 5.0)
                (Variables|Default|SetStuckT (+ (Variables|Default|GetStuckT) DeltaSeconds))
                (if (> (Variables|Default|GetStuckT) 0.75)
                  (Transformation|SetActorLocation :self ch :NewLocation (Math|Vector|MakeVector (.x (Variables|Default|GetSafe)) (.y (Variables|Default|GetSafe)) (+ (.z (Variables|Default|GetSafe)) 30.0)) :bTeleport true)
                  (Components|Movement|StopMovementImmediately :self {CM})
                  (Variables|Default|SetStuckT 0.0)
                  (Variables|Default|SetUnsticks (+ (Variables|Default|GetUnsticks) 1)))
                (else
                  (Variables|Default|SetStuckT 0.0))))))))))
"""
assert TICK.count("(") == TICK.count(")")
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
for n in T.find_nodes(g, ""):
    if any(str(p.name) == "DeltaSeconds" for p in T.get_node_infos([n])[0].output_pins): T.delete_node(n)
T.write_graph_dsl(g, TICK)
ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp); eal.save_loaded_asset(bp, only_if_is_dirty=False)
d = " ".join(T.read_graph_dsl(g).split()); assert "SetSafe" in d and "SetActorLocation" in d, "fall guard graph empty: see LogScript"
fg = eas.spawn_actor_from_class(bp.generated_class(), START + unreal.Vector(0, 0, 300), unreal.Rotator()); fg.tags = [TAG]; fg.set_actor_label("SFC_FallGuard"); fg.set_folder_path("SFC")
fg.set_editor_property("FloorZ", FLOORZ); fg.set_editor_property("Safe", START)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
print("compile", ok, "| PlayerStart", START, "| KillZ", ws.get_editor_property("kill_z"), "| guard FloorZ", FLOORZ)
