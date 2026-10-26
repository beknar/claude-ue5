"""The magic levels' walk / run switch: BP_RDM_CasterCharacter (random_dungeonmagic_level), BP_RDM2_DarkCasterCharacter
(random_dungeonmagic_level2), BP_RDM3_RogueCharacter (random_dungeonmagic_level3), BP_RDM4_WarriorCharacter (the
Warrior of random_dungeonmagic_level4), BP_RDM5_SummonerCharacter, BP_RDM5_Summoner2Character, BP_RDM5_Summoner3Character and BP_RDM5_Warrior3Character (random_dungeonmagic_level5) get a bool RunMode, which URDCombatComponent::SetRunMode sets (R on the keyboard, the left
trigger on the gamepad: generator bCasterControls), and a MoveScale of their own that picks her run speed while RunMode is
on or the run action (Shift, the left stick's click) is held, her walk speed otherwise; a stick pushed part way scales it
down as before (620's MoveScale, with RunMode). Run after 810 / 817 / 822 / 824 / 832 / 847 / 852 / 862 (their characters), before 811 / 818 / 823 / 825 / 833. Idempotent.
Args: none"""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary
for CH, PATH in (("Caster", "/Game/RandomDungeon/Blueprints/BP_RDM_CasterCharacter"), ("DarkCaster", "/Game/RandomDungeon/Blueprints/BP_RDM2_DarkCasterCharacter"),
                 ("Rogue", "/Game/RandomDungeon/Blueprints/BP_RDM3_RogueCharacter"), ("Fem5", "/Game/RandomDungeon/Blueprints/BP_RDM4_WarriorCharacter"),
                 ("Summoner", "/Game/RandomDungeon/Blueprints/BP_RDM5_SummonerCharacter"), ("summoner2", "/Game/RandomDungeon/Blueprints/BP_RDM5_Summoner2Character"),
                 ("Summoner3", "/Game/RandomDungeon/Blueprints/BP_RDM5_Summoner3Character"), ("Warrior3", "/Game/RandomDungeon/Blueprints/BP_RDM5_Warrior3Character")):
    bp = unreal.load_asset(PATH)
    if not bp and CH in ("summoner2", "Summoner3", "Warrior3"): print(f"RDMCONTROLS (no {CH} yet: 847 / 852 / 862 make her)"); continue
    assert bp, PATH + ": run 810 / 817 / 822 / 824 / 832 first"
    SP = r"E:\code\claude-ue5\claude_ue5\SourceArt" + ("\\summoner2" if CH == "summoner2" else "\\jrpg_" + CH.lower()) + r"\speeds.txt"
    WALK, RUN = [float(v) for v in open(SP).read().split()]
    cdo = unreal.get_default_object(bp.generated_class())
    try: cdo.get_editor_property("RunMode")
    except Exception: T.add_variable(bp, "RunMode", "bool")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    graphs = lambda: {x.get_name(): x for x in T.list_graphs(bp)}
    BEL = unreal.BlueprintEditorLibrary
    # (the parent that has a MoveScale: her own character's, or further up for the Warrior, whose dungeon character is a
    # child of the city level's)
    def has_move_scale(cls):
        while cls is not None:
            pb = unreal.load_asset(cls.get_path_name().rsplit(".", 1)[0])
            if not isinstance(pb, unreal.Blueprint): return False
            if "MoveScale" in [g.get_name() for g in T.list_graphs(pb)]: return True
            cls = BEL.get_blueprint_parent_class(pb)
        return False
    if has_move_scale(BEL.get_blueprint_parent_class(bp)):
        # an override of her own character's (620's) MoveScale: a function of the same name made while the parent had none
        # (620 had deleted it: the editor gave the child to the class above) does not compile once the parent has it again
        if "MoveScale" in graphs(): BEL.remove_function_graph(bp, "MoveScale")
        BEL.add_function_override(bp, "MoveScale"); BEL.compile_blueprint(bp)
    elif "MoveScale" not in graphs(): T.add_function_graph(bp, "MoveScale"); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    code = f"""
(fn MoveScale (X Y)
  (bind k (/ (select (or (Input|EnhancedActionValues|IA_Sprint) (Variables|Default|GetRunMode)) 1.0 {WALK / RUN:.4f}) (Math|Float|Max(Float) (Math|Float|Sqrt (+ (* X X) (* Y Y))) 1.0)))
  (return (* X k) (* Y k)))"""
    assert code.count("(") == code.count(")")
    for attempt in range(2):
        # (the first write into an override made in place of such a function did not take: the second, after a compile, did)
        T.write_graph_dsl(graphs()["MoveScale"], code)
        ok = unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        back = " ".join(T.read_graph_dsl(graphs()["MoveScale"]).split())
        if "RunMode" in back: break
    assert "RunMode" in back and "IA_Sprint" in back, "MoveScale did not take: " + back[:300]
    eal.save_loaded_asset(bp, only_if_is_dirty=False)
    cdo = unreal.get_default_object(bp.generated_class())          # (the one before the compile is a REINST_ copy)
    print(f"RDMCONTROLS {bp.get_name()}: RunMode={cdo.get_editor_property('RunMode')}, compile {ok} | walk {WALK:.1f} / run {RUN:.1f} cm/s | MoveScale: {back[:220]}")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
