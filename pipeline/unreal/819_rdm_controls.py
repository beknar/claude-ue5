"""The magic levels' walk / run switch: BP_RDM_CasterCharacter (random_dungeonmagic_level), BP_RDM2_DarkCasterCharacter
(random_dungeonmagic_level2) and BP_RDM3_RogueCharacter (random_dungeonmagic_level3) get a bool RunMode, which URDCombatComponent::SetRunMode sets (R on the keyboard, the left
trigger on the gamepad: generator bCasterControls), and a MoveScale of their own that picks her run speed while RunMode is
on or the run action (Shift, the left stick's click) is held, her walk speed otherwise; a stick pushed part way scales it
down as before (620's MoveScale, with RunMode). Run after 810 / 817 / 822 (their characters), before 811 / 818 / 823. Idempotent.
Args: none"""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary
for CH, PATH in (("Caster", "/Game/RandomDungeon/Blueprints/BP_RDM_CasterCharacter"), ("DarkCaster", "/Game/RandomDungeon/Blueprints/BP_RDM2_DarkCasterCharacter"),
                 ("Rogue", "/Game/RandomDungeon/Blueprints/BP_RDM3_RogueCharacter")):
    bp = unreal.load_asset(PATH); assert bp, PATH + ": run 810 / 817 / 822 first"
    WALK, RUN = [float(v) for v in open(r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_" + CH.lower() + r"\speeds.txt").read().split()]
    cdo = unreal.get_default_object(bp.generated_class())
    try: cdo.get_editor_property("RunMode")
    except Exception: T.add_variable(bp, "RunMode", "bool")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    graphs = lambda: {x.get_name(): x for x in T.list_graphs(bp)}
    if "MoveScale" not in graphs(): T.add_function_graph(bp, "MoveScale"); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    code = f"""
(fn MoveScale (X Y)
  (bind k (/ (select (or (Input|EnhancedActionValues|IA_Sprint) (Variables|Default|GetRunMode)) 1.0 {WALK / RUN:.4f}) (Math|Float|Max(Float) (Math|Float|Sqrt (+ (* X X) (* Y Y))) 1.0)))
  (return (* X k) (* Y k)))"""
    assert code.count("(") == code.count(")")
    T.write_graph_dsl(graphs()["MoveScale"], code)
    ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    back = " ".join(T.read_graph_dsl(graphs()["MoveScale"]).split())
    assert "RunMode" in back and "IA_Sprint" in back, "MoveScale did not take: " + back[:300]
    eal.save_loaded_asset(bp, only_if_is_dirty=False)
    cdo = unreal.get_default_object(bp.generated_class())          # (the one before the compile is a REINST_ copy)
    print(f"RDMCONTROLS {bp.get_name()}: RunMode={cdo.get_editor_property('RunMode')}, compile {ok} | walk {WALK:.1f} / run {RUN:.1f} cm/s | MoveScale: {back[:220]}")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
