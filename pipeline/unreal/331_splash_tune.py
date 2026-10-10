"""BP_Splash: lighter, more transparent crown/ring (only the tick graph is rewritten; BP_Door/BP_Container untouched)."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
bp = unreal.load_asset("/Game/Castle/Interactive/Blueprints/BP_Splash")
g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
for n in T.find_nodes(g, ""):
    if any(str(p.name) == "DeltaSeconds" for p in T.get_node_infos([n])[0].output_pins): T.delete_node(n)
T.write_graph_dsl(g, """
(event EventTick (DeltaSeconds)
  (Variables|Default|SetAge (+ (Variables|Default|GetAge) DeltaSeconds))
  (bind t (Math|Float|Min(Float) 1.0 (/ (Variables|Default|GetAge) 0.75)))
  (bind rise (Math|Float|Max(Float) 0.04 (* 4.4 (* t (- 1.0 t)))))
  (Transformation|SetRelativeScale3D :self (Variables|Default|GetCrown) :NewScale3D (Math|Vector|MakeVector (+ 0.45 (* 0.8 t)) (+ 0.45 (* 0.8 t)) rise))
  (Transformation|SetRelativeScale3D :self (Variables|Default|GetRing) :NewScale3D (Math|Vector|MakeVector (+ 0.35 (* 2.6 t)) (+ 0.35 (* 2.6 t)) 1.0))
  (Rendering|Material|SetScalarParameterValueonMaterials :self (Variables|Default|GetCrown) :ParameterName "Opacity" :ParameterValue (* 0.72 (- 1.0 (* t t))))
  (Rendering|Material|SetScalarParameterValueonMaterials :self (Variables|Default|GetRing) :ParameterName "Opacity" :ParameterValue (* 0.5 (- 1.0 t)))
  (if (>= t 1.0)
    (Actor|DestroyActor)))
""")
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp)); unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
print(" ".join(T.read_graph_dsl(g).split())[:160])