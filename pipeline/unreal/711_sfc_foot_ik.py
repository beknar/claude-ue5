"""Foot IK for the sf-city-level character (her clips plant the feet on a flat floor; on rubble, stones and steps a planted foot
sank into the ground - up to 25 cm at the Monolith gate). ABP_SFC_Fem5 = copy of ABP_Unarmed_Fem5 (the meadow keeps the
original) with:
- EventGraph: UpdateFootIK (after SetDirection, every update): visibility traces under each foot and ball bone (from 75 cm
  above to 60 cm below the mesh root plane); foot offset = highest ground under the foot - root plane (clamped -45..60),
  smoothed; pelvis offset = min(0, both feet); effectors = (0, 0, foot offset - pelvis offset) in each foot bone's space;
  IKAlpha eases to 0 while falling.
- AnimGraph: ... ControlRig -> LocalToComponent -> Transform(Modify)Bone pelvis (+PelvisVec, world space, additive) ->
  TwoBoneIK foot_l -> TwoBoneIK foot_r (effector in the foot's bone space, the current knee as pole) -> ComponentToLocal -> Output
BP_SFC_Fem5Character's mesh uses ABP_SFC_Fem5."""
import re, unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary
P = "/Game/SFCityLevel/Anim/ABP_SFC_Fem5"
if not eal.does_asset_exist(P): eal.duplicate_asset("/Game/JRPG/Fem5Locomotion/ABP_Unarmed_Fem5", P)
abp = unreal.load_asset(P)
gs = lambda: {g.get_name(): g for g in T.list_graphs(abp)}
info = lambda n: T.get_node_infos([n])[0]
def pin(n, name, out):
    i = info(n)
    for p in (i.output_pins if out else i.input_pins):
        if str(p.name) == name: return p
    raise KeyError(f"{n.get_name()}.{name} (have {[str(p.name) for p in (i.output_pins if out else i.input_pins)]})")
cdo = unreal.get_default_object(abp.generated_class())
for nm, typ in (("FootOffL", "float"), ("FootOffR", "float"), ("PelvisOff", "float"), ("IKAlpha", "float"), ("EffL", "vector"), ("EffR", "vector"), ("PelvisVec", "vector")):
    try: cdo.get_editor_property(nm)
    except Exception: T.add_variable(abp, nm, typ)
unreal.BlueprintEditorLibrary.compile_blueprint(abp)
# ---------- EventGraph: UpdateFootIK
def trace_off(bone, k):
    return f"""
  (bind s{k} (Transformation|GetSocketLocation :self mesh :InSocketName "{bone}"))
  (bind (h{k} ok{k}) (Collision|LineTraceByChannel :Start (Math|Vector|MakeVector (.x s{k}) (.y s{k}) (+ base 75.0)) :End (Math|Vector|MakeVector (.x s{k}) (.y s{k}) (- base 60.0)) :TraceChannel "TraceTypeQuery1" :bTraceComplex true :bIgnoreSelf true))
  (bind (b{k} o{k} t{k}) (Collision|BreakHitResult h{k}))
  (bind off{k} (select ok{k} (- 75.0 (* t{k} 135.0)) -60.0))"""
EFF = lambda side: f"""
  (Variables|Default|SetEff{side} (Math|Transform|InverseTransformDirection :T (Transformation|GetSocketTransform :self mesh :InSocketName "foot_{side.lower()}" :TransformSpace "RTS_World") :Direction (Math|Vector|MakeVector 0.0 0.0 (- (Variables|Default|GetFootOff{side}) (Variables|Default|GetPelvisOff)))))"""
CODE = f"""
(fn UpdateFootIK ()
  (bind mesh (Animation|GetOwningComponent))
  (bind base (.z (Transformation|GetWorldLocation :self mesh)))
  (bind dt (Utilities|Time|GetWorldDeltaSeconds)){trace_off("foot_l", 1)}{trace_off("ball_l", 2)}{trace_off("foot_r", 3)}{trace_off("ball_r", 4)}
  (bind tl (Math|Float|Clamp(Float) (Math|Float|Max(Float) off1 off2) -45.0 60.0))
  (bind tr (Math|Float|Clamp(Float) (Math|Float|Max(Float) off3 off4) -45.0 60.0))
  (Variables|Default|SetFootOffL (Math|Interpolation|FInterpTo :Current (Variables|Default|GetFootOffL) :Target tl :DeltaTime dt :InterpSpeed 18.0))
  (Variables|Default|SetFootOffR (Math|Interpolation|FInterpTo :Current (Variables|Default|GetFootOffR) :Target tr :DeltaTime dt :InterpSpeed 18.0))
  (Variables|Default|SetPelvisOff (Math|Interpolation|FInterpTo :Current (Variables|Default|GetPelvisOff) :Target (Math|Float|Min(Float) 0.0 (Math|Float|Min(Float) (Variables|Default|GetFootOffL) (Variables|Default|GetFootOffR))) :DeltaTime dt :InterpSpeed 12.0))
  (Variables|Default|SetPelvisVec (Math|Vector|MakeVector 0.0 0.0 (Variables|Default|GetPelvisOff)))
  (Variables|Default|SetIKAlpha (Math|Interpolation|FInterpTo :Current (Variables|Default|GetIKAlpha) :Target (select (Variables|Default|GetIsFalling) 0.0 1.0) :DeltaTime dt :InterpSpeed 10.0)){EFF("L")}{EFF("R")})"""
assert CODE.count("(") == CODE.count(")")
if "UpdateFootIK" not in gs():
    T.add_function_graph(abp, "UpdateFootIK"); unreal.BlueprintEditorLibrary.compile_blueprint(abp)
T.write_graph_dsl(gs()["UpdateFootIK"], CODE); unreal.BlueprintEditorLibrary.compile_blueprint(abp)
body = T.read_graph_dsl(gs()["UpdateFootIK"]); assert "SetEffR" in body and "LineTraceByChannel" in body, "UpdateFootIK incomplete - see LogScript"
eg = gs()["EventGraph"]
nodes = T.find_nodes(eg, "")
calls = [n for n in nodes if "UpdateFootIK" in str(info(n).type_id)]
if not calls:
    sd = next(n for n in nodes if str(info(n).type_id).endswith("|SetDirection"))
    ids = [str(x) for x in T.find_node_types(eg, "UpdateFootIK")]
    call = T.create_node(eg, "CallFunction|UpdateFootIK" if "CallFunction|UpdateFootIK" in ids else ids[0], unreal.IntPoint(1800, 900))
    T.connect_pins(pin(sd, "then", True).pin_id, pin(call, "execute", False).pin_id)
# ---------- AnimGraph chain
ag = gs()["AnimGraph"]
KINDS = ("AnimGraphNode_TwoBoneIK", "AnimGraphNode_ModifyBone", "AnimGraphNode_LocalToComponentSpace", "AnimGraphNode_ComponentToLocalSpace")
for n in T.find_nodes(ag, ""):
    if n.get_class().get_name() in KINDS or (n.get_class().get_name() == "K2Node_VariableGet" and any(v in str(info(n).type_id) for v in ("EffL", "EffR", "PelvisVec", "IKAlpha"))):
        T.delete_node(n)
root = next(n for n in T.find_nodes(ag, "") if n.get_class().get_name() == "AnimGraphNode_Root")
cr = next(n for n in T.find_nodes(ag, "") if n.get_class().get_name() == "AnimGraphNode_ControlRig")
res = pin(root, "Result", False); crp = pin(cr, "Pose", True)
for c in res.get_editor_property("connected_pins"): T.break_pins(c, res.pin_id)
def mk(tid, x, y): return T.create_node(ag, tid, unreal.IntPoint(x, y))
def setnode(n, **kv):
    nd = n.get_editor_property("node"); t = nd.export_text()
    for k, v in kv.items():
        t, cnt = re.subn(rf"(?<=[(,]){k}=(\([^()]*(\([^()]*(\([^()]*\))*[^()]*\))*[^()]*\)|[^,()]*)", f"{k}={v}", t, count=1)
        assert cnt == 1, k
    nd.import_text(t); n.set_editor_property("node", nd)
def getter(var, x, y):
    ids = [str(i) for i in T.find_node_types(ag, "Get" + var)]
    tid = next(i for i in ids if i.endswith("|Get" + var))
    return T.create_node(ag, tid, unreal.IntPoint(x, y))
ltc = mk("Animation|ConvertSpaces|LocalToComponent", 300, 0)
mb = mk("Animation|SkeletalControls|Transform(Modify)Bone", 600, 0)
setnode(mb, BoneToModify='(BoneName="pelvis")', TranslationMode="BMM_Additive", TranslationSpace="BCS_WorldSpace")
iks = []
for k, side in enumerate(("l", "r")):
    n = mk("Animation|SkeletalControls|TwoBoneIK", 900 + 300 * k, 0)
    setnode(n, IKBone=f'(BoneName="foot_{side}")', EffectorLocationSpace="BCS_BoneSpace",
            EffectorTarget=f'(bUseSocket=False,BoneReference=(BoneName="foot_{side}"),SocketReference=(SocketName=""))',
            JointTargetLocationSpace="BCS_BoneSpace", JointTarget=f'(bUseSocket=False,BoneReference=(BoneName="calf_{side}"),SocketReference=(SocketName=""))')
    iks.append(n)
ctl = mk("Animation|ConvertSpaces|ComponentToLocal", 1600, 0)
T.connect_pins(crp.pin_id, pin(ltc, "LocalPose", False).pin_id)
T.connect_pins(pin(ltc, "ComponentPose", True).pin_id, pin(mb, "ComponentPose", False).pin_id)
T.connect_pins(pin(mb, "Pose", True).pin_id, pin(iks[0], "ComponentPose", False).pin_id)
T.connect_pins(pin(iks[0], "Pose", True).pin_id, pin(iks[1], "ComponentPose", False).pin_id)
T.connect_pins(pin(iks[1], "Pose", True).pin_id, pin(ctl, "ComponentPose", False).pin_id)
T.connect_pins(pin(ctl, "Pose", True).pin_id, res.pin_id)
T.connect_pins(pin(getter("PelvisVec", 450, 250), "PelvisVec", True).pin_id, pin(mb, "Translation", False).pin_id)
for n, x in ((mb, 450), (iks[0], 750), (iks[1], 1050)):
    T.connect_pins(pin(getter("IKAlpha", x, 350), "IKAlpha", True).pin_id, pin(n, "Alpha", False).pin_id)
for n, var, x in ((iks[0], "EffL", 750), (iks[1], "EffR", 1050)):
    T.connect_pins(pin(getter(var, x, 250), var, True).pin_id, pin(n, "EffectorLocation", False).pin_id)
ok = unreal.BlueprintEditorLibrary.compile_blueprint(abp); eal.save_loaded_asset(abp, only_if_is_dirty=False)
print("ABP compile", ok, "| chain:", " -> ".join(n.get_class().get_name().replace("AnimGraphNode_", "") for n in (cr, ltc, mb, iks[0], iks[1], ctl, root)))
for n in iks + [mb]: print("  ", n.get_editor_property("node").export_text()[:260])
# ---------- character uses it
ch = unreal.load_asset("/Game/SFCityLevel/Blueprints/BP_SFC_Fem5Character")
m = unreal.get_default_object(ch.generated_class()).get_component_by_class(unreal.SkeletalMeshComponent)
m.set_editor_property("anim_class", abp.generated_class()); unreal.BlueprintEditorLibrary.compile_blueprint(ch); eal.save_loaded_asset(ch, only_if_is_dirty=False)
print("BP_SFC_Fem5Character anim class:", unreal.get_default_object(ch.generated_class()).get_component_by_class(unreal.SkeletalMeshComponent).get_editor_property("anim_class").get_name())
