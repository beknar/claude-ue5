"""BP_FF2Character.WaterStep: bigger splashes at speed (0.6 + speed/300, up to 1.7x). Only this function is rewritten."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
bp = unreal.load_asset("/Game/FF2/Game/BP_FF2Character")
g = {x.get_name(): x for x in T.list_graphs(bp)}["WaterStep"]
WATER = '"/Game/Medieval_Fantasy_Village/Blueprint/Water/BP_water.BP_water_C"'
code = f"""
(fn WaterStep (DT)
  (if (not (Variables|Default|GetWaterChecked))
    (Variables|Default|SetWaterChecked true)
    (Variables|Default|SetWaterZ -1000000.0)
    (bind w (Actor|GetActorOfClass :ActorClass {WATER}))
    (bind wz (.z (Transformation|GetActorLocation :self w)))
    (Variables|Default|SetWaterZ (select (< (* wz wz) 0.000001) -1000000.0 wz)))
  (bind base (- (.z (Transformation|GetActorLocation)) 85.2))
  (bind inwater (> (Variables|Default|GetWaterZ) (+ base 3.0)))
  (bind spd (Math|Vector|VectorLengthXY (Transformation|GetVelocity)))
  (bind s (Math|Float|Clamp(Float) :Value (+ 0.6 (/ spd 300.0)) :Min 0.6 :Max 1.7))
  (bind pl (Transformation|GetSocketLocation :self (Variables|Character|GetMesh) :InSocketName "ball_l"))
  (bind pr (Transformation|GetSocketLocation :self (Variables|Character|GetMesh) :InSocketName "ball_r"))
  (bind lz (- (.z pl) base))
  (bind rz (- (.z pr) base))
  (bind falling (Movement|IsFalling :self (Variables|Character|GetCharacterMovement)))
  (if (and inwater (and (> (Variables|Default|GetPrevLZ) 7.0) (<= lz 7.0)))
    (CallFunction|SpawnSplash :X (.x pl) :Y (.y pl) :S s))
  (if (and inwater (and (> (Variables|Default|GetPrevRZ) 7.0) (<= rz 7.0)))
    (CallFunction|SpawnSplash :X (.x pr) :Y (.y pr) :S s))
  (if (and inwater (and (Variables|Default|GetWasFalling) (not falling)))
    (CallFunction|SpawnSplash :X (.x (Transformation|GetActorLocation)) :Y (.y (Transformation|GetActorLocation)) :S 2.1))
  (Variables|Default|SetPrevLZ lz)
  (Variables|Default|SetPrevRZ rz)
  (Variables|Default|SetWasFalling falling))"""
assert code.count("(") == code.count(")")
T.write_graph_dsl(g, code)
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp)); unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
print("ok" if "0.6" in T.read_graph_dsl(g) and "SpawnSplash" in T.read_graph_dsl(g) else "CHECK WaterStep")