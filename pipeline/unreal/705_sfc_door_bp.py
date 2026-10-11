"""BP_SciFiDoor (/Game/SFCityLevel/Blueprints): automatic sci-fi blast door for the sf-city-level structures.
Actor origin = doorway bottom centre, X along the wall, Y through it.
- Leaf    : Red_Echo SM_door scaled to the opening (visual only, no collision); rises by Lift into the wall above the doorway
- Blocker : hidden box exactly filling the opening (blocks Pawn / camera), moves with the leaf - the mesh's own complex
            collision has holes
- opens while the player pawn is within NearDist (and roughly level with the door), or once the level-sequence clock passes
  AutoOpenAt (cinematics; -1 = off); closes when she has left. Alpha eases 0..1.
Instance-editable: Width, Height, Lift, NearDist, AutoOpenAt (the construction-time size is applied by the spawner)."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
D = "/Game/SFCityLevel/Blueprints"; PATH = f"{D}/BP_SciFiDoor"
if eal.does_asset_exist(PATH): eal.delete_asset(PATH)
f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.Actor)
bp = at.create_asset("BP_SciFiDoor", D, unreal.Blueprint, f)
root = sds.k2_gather_subobject_data_for_blueprint(bp)[0]
c = {}
for nm, cls in (("Leaf", unreal.StaticMeshComponent), ("Blocker", unreal.StaticMeshComponent)):
    h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=cls, blueprint_context=bp))
    sds.rename_subobject(h, unreal.Text(nm)); c[nm] = lib.get_object_for_blueprint(lib.get_data(h), bp)
for nm, typ, ed in (("Open", "bool", False), ("Alpha", "float", False), ("Lift", "float", True), ("NearDist", "float", True), ("AutoOpenAt", "float", True)):
    T.add_variable(bp, nm, typ)
    if ed: T.set_variable_instance_editable(bp, nm, True)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
W, H = 200.0, 250.0
leaf = c["Leaf"]; leaf.set_static_mesh(unreal.load_asset("/Game/Red_Echo/Meshes/Blocking/SM_door"))
leaf.set_editor_property("relative_scale3d", unreal.Vector(W / 274.0, 1.1, H / 321.0)); leaf.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
blk = c["Blocker"]; blk.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube"))
blk.set_editor_property("relative_location", unreal.Vector(0, 0, H / 2)); blk.set_editor_property("relative_scale3d", unreal.Vector(W / 100.0, 0.16, H / 100.0))
blk.set_editor_property("hidden_in_game", True); blk.set_visibility(False); blk.set_editor_property("cast_shadow", False)
blk.set_collision_profile_name("BlockAll")
graphs = lambda: {x.get_name(): x for x in T.list_graphs(bp)}
NOW = "(Utilities|Time|GetGameTimeinSeconds)"
SEQ = f"""
(fn SeqTime ()
  (bind lsa (Utilities|Casting|CastToLevelSequenceActor :Object (Actor|GetActorOfClass :ActorClass "/Script/LevelSequence.LevelSequenceActor"))
    (:then
      (return (Utilities|TimeManagement|QualifiedFrameTimeToSeconds (Sequencer|Player|GetCurrentTime :self (Class|LevelSequenceActor|GetSequencePlayer :self lsa)))))
    (:CastFailed
      (return {NOW}))))"""
PAWN = "(Game|GetPlayerPawn :PlayerIndex 0)"
NEAR = f"""
(fn Near ()
  (bind d (- (Transformation|GetActorLocation :self {PAWN}) (Transformation|GetActorLocation)))
  (return (and (< (Math|Vector|VectorLength (Math|Vector|MakeVector (.x d) (.y d) 0.0)) (Variables|Default|GetNearDist)) (< (* (.z d) (.z d)) 67600.0))))"""
for name, code, outs in (("SeqTime", SEQ, (("Out", "float"),)), ("Near", NEAR, (("Out", "bool"),))):
    assert code.count("(") == code.count(")"), name
    g = T.add_function_graph(bp, name)
    for p, t in outs: T.add_function_param(g, p, t, False)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    T.write_graph_dsl(graphs()[name], code); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert len(T.read_graph_dsl(graphs()[name]).strip().splitlines()) > 1, name + ": empty body, see LogScript"
TICK = """
(event EventTick (DeltaSeconds)
  (Variables|Default|SetOpen (or (CallFunction|Near) (and (>= (Variables|Default|GetAutoOpenAt) 0.0) (>= (CallFunction|SeqTime) (Variables|Default|GetAutoOpenAt)))))
  (Variables|Default|SetAlpha (Math|Interpolation|FInterpTo :Current (Variables|Default|GetAlpha) :Target (select (Variables|Default|GetOpen) 1.0 0.0) :DeltaTime DeltaSeconds :InterpSpeed 5.0))
  (Transformation|SetRelativeLocation :self (Variables|Default|GetLeaf) :NewLocation (Math|Vector|MakeVector 0.0 0.0 (* (Variables|Default|GetAlpha) (Variables|Default|GetLift))))
  (Transformation|SetRelativeLocation :self (Variables|Default|GetBlocker) :NewLocation (Math|Vector|MakeVector 0.0 0.0 (+ 125.0 (* (Variables|Default|GetAlpha) (Variables|Default|GetLift))))))
"""
assert TICK.count("(") == TICK.count(")")
g = unreal.BlueprintEditorLibrary.find_event_graph(bp); T.write_graph_dsl(g, TICK)
ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
cdo = unreal.get_default_object(bp.generated_class())
for k, v in (("Lift", 262.0), ("NearDist", 300.0), ("AutoOpenAt", -1.0)): cdo.set_editor_property(k, v)
eal.save_loaded_asset(bp, only_if_is_dirty=False)
d = " ".join(T.read_graph_dsl(g).split()); print("compile", ok, "| tick:", d[d.find("EventTick"):][:260])
