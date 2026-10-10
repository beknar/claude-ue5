"""Sprint (hold Left Ctrl / right trigger) on RunFast without touching the blendspace grid:
the never-used +-180 direction slots of the run row play RunFast, and above run speed the AnimBP steers
Direction 135 -> 180 (Running -> RunFast blend) while GroundSpeed stays on the run row.
Speeds: walk 140, run 430, sprint 580 (CMC max)."""
import re, unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
LA = "/Game/Meshy/Locomotion/Anims"
# ---- input ----
p = "/Game/Input/Actions/IA_SprintFast"
ia = unreal.load_asset(p) if eal.does_asset_exist(p) else at.create_asset("IA_SprintFast", "/Game/Input/Actions", unreal.InputAction, None)
ia.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN); eal.save_loaded_asset(ia)
imc = unreal.load_asset("/Game/Input/IMC_Default")
have = {(m.get_editor_property("action").get_name(), str(m.get_editor_property("key").get_editor_property("key_name")))
        for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings")}
for k in ("LeftControl", "Gamepad_RightTrigger"):
    if ("IA_SprintFast", k) not in have:
        key = unreal.Key(); key.set_editor_property("key_name", k); imc.map_key(ia, key)
eal.save_loaded_asset(imc)
# ---- blendspace: run-row +-180 slots -> RunFast (in place, grid untouched) ----
bs = unreal.load_asset(f"{LA}/BS_Idle_Walk_Run_MeshyLoco")
runfast = unreal.load_asset("/Game/Meshy/Anims/AS_Meshy_RunFast")
samples = bs.get_editor_property("sample_data")
for i in range(len(samples)):
    t = samples[i].export_text()
    x = float(t.split("X=")[1].split(",")[0]); y = float(t.split("Y=")[1].split(",")[0])
    if y > 450 and abs(abs(x) - 180) < 1:
        s = samples[i]; s.set_editor_property("animation", runfast); samples[i] = s; print("sample", i, "->", "RunFast", x, y)
bs.set_editor_property("sample_data", samples); eal.save_loaded_asset(bs)
# ---- AnimBP: speed cap on the run row + direction steering for sprint ----
abp = unreal.load_asset(f"{LA}/ABP_Unarmed_Meshy1")
gs = {x.get_name(): x for x in T.list_graphs(abp)}
T.write_graph_dsl(gs["RemapSpeed"], """
(fn RemapSpeed (S)
  (return (select (< S 140.0) (* S 2.142857) (Math|Float|Min(Float) 600.0 (+ 300.0 (* (- S 140.0) 1.034483))))))""")
if "RemapDir" not in gs:
    fg = T.add_function_graph(abp, "RemapDir")
    T.add_function_param(fg, "D", "float", True); T.add_function_param(fg, "Out", "float", False)
    unreal.BlueprintEditorLibrary.compile_blueprint(abp)
    gs = {x.get_name(): x for x in T.list_graphs(abp)}
T.write_graph_dsl(gs["RemapDir"], """
(fn RemapDir (D)
  (bind v (Math|Vector|VectorLengthXY (Variables|Default|GetVelocity)))
  (return (select (> v 435.0) (+ 135.0 (* 45.0 (Math|Float|Min(Float) 1.0 (/ (- v 430.0) 150.0)))) D)))""")
unreal.BlueprintEditorLibrary.compile_blueprint(abp)
print(T.read_graph_dsl(gs["RemapDir"]))
eg = gs["EventGraph"]
def info(n): return T.get_node_infos([n])[0]
def pin(i, name, out):
    for p in (i.output_pins if out else i.input_pins):
        if str(p.name) == name: return p
    raise KeyError(f"{name} in {[str(p.name) for p in (i.output_pins if out else i.input_pins)]}")
nodes = T.find_nodes(eg, "")
if not any("RemapDir" in str(info(n).type_id) for n in nodes):
    sd = [n for n in nodes if "SetDirection" in str(info(n).type_id)][0]; si = info(sd)
    ex, vi = pin(si, "execute", False), pin(si, "Direction", False)
    pe, pv = ex.get_editor_property("connected_pins")[0], vi.get_editor_property("connected_pins")[0]
    call = T.create_node(eg, [str(x) for x in T.find_node_types(eg, "RemapDir")][0], unreal.IntPoint(600, 500)); ci = info(call)
    T.break_pins(pe, ex.pin_id); T.break_pins(pv, vi.pin_id)
    T.connect_pins(pe, pin(ci, "execute", False).pin_id); T.connect_pins(pin(ci, "then", True).pin_id, ex.pin_id)
    T.connect_pins(pv, pin(ci, "D", False).pin_id); T.connect_pins(pin(ci, "Out", True).pin_id, vi.pin_id)
    print("RemapDir spliced")
print("ABP compile", unreal.BlueprintEditorLibrary.compile_blueprint(abp)); eal.save_loaded_asset(abp)
# ---- character: max speed 580, input scaling ----
bp = unreal.load_asset("/Game/Meshy/Game/BP_MeshyCharacter")
cdo = unreal.get_default_object(bp.generated_class())
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
for h in sds.k2_gather_subobject_data_for_blueprint(bp):
    o = lib.get_associated_object(lib.get_data(h)) if hasattr(lib, "get_associated_object") else lib.get_object(lib.get_data(h))
    if isinstance(o, unreal.CharacterMovementComponent): o.set_editor_property("max_walk_speed", 580.0)
cdo.character_movement.set_editor_property("max_walk_speed", 580.0)
mg = {x.get_name(): x for x in T.list_graphs(bp)}["MoveScale"]
T.write_graph_dsl(mg, """
(fn MoveScale (X Y)
  (bind s (select (Input|EnhancedActionValues|IA_SprintFast) 1.0 (select (Input|EnhancedActionValues|IA_Sprint) 0.741 0.241)))
  (bind k (select (< (Utilities|Time|GetGameTimeinSeconds) (Variables|Default|GetActionLockUntil)) 0.0 (/ s (Math|Float|Max(Float) (Math|Float|Sqrt (+ (* X X) (* Y Y))) 1.0))))
  (return (* X k) (* Y k)))""")
print(T.read_graph_dsl(mg)[:300])
print("BP compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp)); eal.save_loaded_asset(bp)
print("max walk", unreal.get_default_object(bp.generated_class()).character_movement.max_walk_speed)
