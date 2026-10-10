"""BP_Wardrobe: Body + DoorL/DoorR (pivots on the outer edges, swing out toward +Y) + Prompt. F toggles when the player is
near and facing it (same rules as BP_Door/BP_Container); AutoOpenAt (-1 = off) opens it on the sequence clock."""
import json, unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
D = "/Game/Castle/Interactive/Blueprints"; K = "/Game/Castle/Furniture/Kit"
HG = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\castle_furniture\kit.json"))["_hinges"]
path = f"{D}/BP_Wardrobe"
if eal.does_asset_exist(path): eal.delete_asset(path)
f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.Actor)
bp = at.create_asset("BP_Wardrobe", D, unreal.Blueprint, f)
root = sds.k2_gather_subobject_data_for_blueprint(bp)[0]; c = {}
for nm, cls in (("Body", unreal.StaticMeshComponent), ("DoorL", unreal.StaticMeshComponent), ("DoorR", unreal.StaticMeshComponent), ("Prompt", unreal.TextRenderComponent)):
    h, _ = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=cls, blueprint_context=bp))
    sds.rename_subobject(h, unreal.Text(nm)); c[nm] = lib.get_object_for_blueprint(lib.get_data(h), bp)
c["Body"].set_static_mesh(unreal.load_asset(f"{K}/SM_Kit_WardrobeBody"))
for nm, key in (("DoorL", "WardrobeL"), ("DoorR", "WardrobeR")):
    c[nm].set_static_mesh(unreal.load_asset(f"{K}/SM_Kit_Wardrobe{nm[-1] == 'L' and 'DoorL' or 'DoorR'}"))
    h = HG[key]; c[nm].set_editor_property("relative_location", unreal.Vector(h[0], -h[1], h[2]))
p = c["Prompt"]; p.set_editor_property("text", unreal.Text("F - Open / Close")); p.set_editor_property("world_size", 12.0)
p.set_editor_property("horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER); p.set_editor_property("vertical_alignment", unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
p.set_editor_property("text_render_color", unreal.Color(r=255, g=236, b=200, a=255)); p.set_editor_property("relative_location", unreal.Vector(0, 45, 150)); p.set_visibility(False)
for nm, typ, ed in (("Open", "bool", True), ("Angle", "float", False), ("OpenYaw", "float", True), ("NearDist", "float", True), ("AutoOpenAt", "float", True)):
    T.add_variable(bp, nm, typ)
    if ed: T.set_variable_instance_editable(bp, nm, True)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
graphs = lambda: {x.get_name(): x for x in T.list_graphs(bp)}
def fn(name, code, outs=()):
    assert code.count("(") == code.count(")"), name
    if name not in graphs():
        g = T.add_function_graph(bp, name)
        for o, ty in outs: T.add_function_param(g, o, ty, False)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    T.write_graph_dsl(graphs()[name], code); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    assert len(T.read_graph_dsl(graphs()[name]).strip().splitlines()) > 1, name + " empty"
PAWN = "(Game|GetPlayerPawn :PlayerIndex 0)"; PR = "(Variables|Default|GetPrompt)"; NOW = "(Utilities|Time|GetGameTimeinSeconds)"
fn("Targeted", f"""
(fn Targeted ()
  (bind p (Transformation|GetActorLocation :self {PAWN}))
  (bind d (- (Transformation|GetWorldLocation :self {PR}) p))
  (bind flat (Math|Vector|MakeVector (.x d) (.y d) 0.0))
  (bind facing (Math|Vector|DotProduct (Math|Vector|Normalize flat) (Transformation|GetActorForwardVector :self {PAWN})))
  (return (and (< (Math|Vector|VectorLength flat) (Variables|Default|GetNearDist)) (> facing 0.35))))""", outs=(("Out", "bool"),))
fn("TryInteract", """
(fn TryInteract ()
  (if (CallFunction|Targeted)
    (Variables|Default|SetOpen (not (Variables|Default|GetOpen)))))""")
fn("SeqTime", f"""
(fn SeqTime ()
  (bind lsa (Utilities|Casting|CastToLevelSequenceActor :Object (Actor|GetActorOfClass :ActorClass "/Script/LevelSequence.LevelSequenceActor"))
    (:then
      (return (Utilities|TimeManagement|QualifiedFrameTimeToSeconds (Sequencer|Player|GetCurrentTime :self (Class|LevelSequenceActor|GetSequencePlayer :self lsa)))))
    (:CastFailed
      (return {NOW}))))""", outs=(("Out", "float"),))
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
code = f"""
(event EventBeginPlay ()
  (Input|EnableInput :PlayerController (Game|GetPlayerController :PlayerIndex 0)))
(event EventTick (DeltaSeconds)
  (if (>= (Variables|Default|GetAutoOpenAt) 0.0)
    (if (>= (CallFunction|SeqTime) (Variables|Default|GetAutoOpenAt))
      (Variables|Default|SetOpen true)))
  (Variables|Default|SetAngle (Math|Interpolation|FInterpTo :Current (Variables|Default|GetAngle) :Target (select (Variables|Default|GetOpen) (Variables|Default|GetOpenYaw) 0.0) :DeltaTime DeltaSeconds :InterpSpeed 3.5))
  (Transformation|SetRelativeRotation :self (Variables|Default|GetDoorL) :NewRotation (Math|Rotator|MakeRotator :Roll 0.0 :Pitch 0.0 :Yaw (Variables|Default|GetAngle)))
  (Transformation|SetRelativeRotation :self (Variables|Default|GetDoorR) :NewRotation (Math|Rotator|MakeRotator :Roll 0.0 :Pitch 0.0 :Yaw (* -1.0 (Variables|Default|GetAngle))))
  (bind show (CallFunction|Targeted))
  (Rendering|SetVisibility :self {PR} :bNewVisibility show)
  (if show
    (Transformation|SetWorldRotation :self {PR} :NewRotation (Math|Rotator|FindLookatRotation :Start (Transformation|GetWorldLocation :self {PR}) :Target (Camera|GetCameraLocation :self (Game|GetPlayerCameraManager :PlayerIndex 0))))))
"""
assert code.count("(") == code.count(")")
T.write_graph_dsl(g, code); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
info = lambda n: T.get_node_infos([n])[0]
pin = lambda i, nm, out: next(q.pin_id for q in (i.output_pins if out else i.input_pins) if str(q.name) == nm)
ev = T.create_node(g, "Input|EnhancedActionEvents|IA_Interact", unreal.IntPoint(-900, 900)); call = T.create_node(g, "CallFunction|TryInteract", unreal.IntPoint(-450, 900))
T.connect_pins(pin(info(ev), "Started", True), pin(info(call), "execute", False))
ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
cdo = unreal.get_default_object(bp.generated_class())
for k, v in (("OpenYaw", 100.0), ("NearDist", 170.0), ("AutoOpenAt", -1.0)): cdo.set_editor_property(k, v)
eal.save_loaded_asset(bp, only_if_is_dirty=False)
d = " ".join(T.read_graph_dsl(g).split())
print("BP_Wardrobe compile", ok, "| tick:", "SetAngle" in d, "| doors:", "GetDoorL" in d and "GetDoorR" in d, "| input:", "EnhancedInputAction" in d)
