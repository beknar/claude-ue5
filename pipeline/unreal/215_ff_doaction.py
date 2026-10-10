"""BP_FFCharacter.DoAction body as nested if/else (an elif chain wrote an empty body)."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
bp = unreal.load_asset("/Game/FF/Game/BP_FFCharacter")
g = {x.get_name(): x for x in T.list_graphs(bp)}["DoAction"]
NOW = "(Utilities|Time|GetGameTimeinSeconds)"
GROUNDED = "(< (Math|Vector|VectorLengthSquared (* (Transformation|GetVelocity) (Math|Vector|MakeVector 0.0 0.0 1.0))) 25.0)"
P = lambda c: f'(CallFunction|BeginAction :Len (Animation|PlayAnimMontage :AnimMontage "/Game/FF/Anims/AM_FF_{c}.AM_FF_{c}"))'
MOVES = ["Attack_01", "Attack_02", "Attack_03", "Dash"]
chain = f"(else {P('ChargedAttack')})"                     # elif nests as the last form of the previous branch
for i in range(len(MOVES) - 1, 0, -1):
    chain = f"(elif (< Which {i + 0.5}) {P(MOVES[i])} {chain})"
code = f"""
(fn DoAction (Which)
  (if (and (>= {NOW} (Variables|Default|GetActionLockUntil)) {GROUNDED})
    (if (< Which 0.5) {P(MOVES[0])} {chain})))"""
assert code.count("(") == code.count(")"), (code.count("("), code.count(")"))
r = T.write_graph_dsl(g, code); print("write", r)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
print(T.read_graph_dsl(g))
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp)); unreal.EditorAssetLibrary.save_loaded_asset(bp)
