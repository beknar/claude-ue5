"""BP_Door tick: the swinging/open leaf must not trap the player (doors swing outward over the raised interior floors),
so the leaf ignores Pawn while Angle is off zero and blocks again only when fully closed. Rewrites only the tick graph
(placed BP_Door instances keep working)."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
bp = unreal.load_asset("/Game/Castle/Interactive/Blueprints/BP_Door")
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
for n in T.find_nodes(g, ""):
    if any(str(p.name) == "DeltaSeconds" for p in T.get_node_infos([n])[0].output_pins): T.delete_node(n)
LEAF = "(Variables|Default|GetLeaf)"; PROMPT = "(Variables|Default|GetPrompt)"
code = f"""
(event EventTick (DeltaSeconds)
  (Variables|Default|SetAngle (Math|Interpolation|FInterpTo :Current (Variables|Default|GetAngle) :Target (select (Variables|Default|GetOpen) (Variables|Default|GetOpenYaw) 0.0) :DeltaTime DeltaSeconds :InterpSpeed 3.2))
  (Transformation|SetRelativeRotation :self {LEAF} :NewRotation (Math|Rotator|MakeRotator :Roll 0.0 :Pitch 0.0 :Yaw (Variables|Default|GetAngle)))
  (if (or (Variables|Default|GetOpen) (> (* (Variables|Default|GetAngle) (Variables|Default|GetAngle)) 4.0))
    (Collision|SetCollisionResponsetoChannel :self {LEAF} :Channel "ECC_Pawn" :NewResponse "ECR_Ignore")
    (else
      (Collision|SetCollisionResponsetoChannel :self {LEAF} :Channel "ECC_Pawn" :NewResponse "ECR_Block")))
  (bind show (CallFunction|Targeted))
  (Rendering|SetVisibility :self {PROMPT} :bNewVisibility show)
  (if show
    (Transformation|SetWorldRotation :self {PROMPT} :NewRotation (Math|Rotator|FindLookatRotation :Start (Transformation|GetWorldLocation :self {PROMPT}) :Target (Camera|GetCameraLocation :self (Game|GetPlayerCameraManager :PlayerIndex 0))))))
"""
assert code.count("(") == code.count(")")
T.write_graph_dsl(g, code)
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp)); unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
d = " ".join(T.read_graph_dsl(g).split()); i = d.find("EventTick"); print(d[i:i + 420])
