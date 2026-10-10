"""Rewrite ABP_Unarmed_FF2.RemapSpeed for the locked stance speeds (walk 102.3 / run 337 cm/s -> 300 / 600 grid)."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
WALK, RUN = 102.3, 337.0
abp = unreal.load_asset("/Game/FF2/Locomotion/Anims/ABP_Unarmed_FF2")
g = {x.get_name(): x for x in T.list_graphs(abp)}["RemapSpeed"]
k1, k2 = 300.0 / WALK, 300.0 / (RUN - WALK)
T.write_graph_dsl(g, f"""
(fn RemapSpeed (S)
  (return (select (< S {WALK}) (* S {k1:.6f}) (Math|Float|Min(Float) 600.0 (+ 300.0 (* (- S {WALK}) {k2:.6f}))))))""")
print(" ".join(T.read_graph_dsl(g).split()))
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(abp)); unreal.EditorAssetLibrary.save_loaded_asset(abp)
