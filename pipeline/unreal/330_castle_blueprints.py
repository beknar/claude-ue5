"""Interactive village blueprints + Interact input:
- IA_Interact (F, gamepad face-button-left) in IMC_Default, bConsumeInput off so every interactable hears it.
- BP_Door      : Leaf (hinged mesh, pivot = actor origin) + Prompt text; F toggles, leaf swings to OpenYaw (eased).
- BP_Container : Body + Lid (hinge pivot) + Contents + Prompt; F toggles, lid swings to OpenRoll.
  Both: input enabled at BeginPlay; act only when the player pawn is within NearDist of the Prompt point and facing it.
- BP_Splash    : Crown + Ring, 0.7 s life: crown rises/collapses, ring spreads, both fade ('Opacity'), then destroys itself.
  Strength = actor scale (set by the spawner)."""
import unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem); lib = unreal.SubobjectDataBlueprintFunctionLibrary
D = "/Game/Castle/Interactive"
# ---------- input
IA = "/Game/Input/Actions/IA_Interact"
ia = unreal.load_asset(IA) if eal.does_asset_exist(IA) else at.create_asset("IA_Interact", "/Game/Input/Actions", unreal.InputAction, None)
ia.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN)
try: ia.set_editor_property("consume_input", False)
except Exception as e: print("consume_input", e)
eal.save_loaded_asset(ia, only_if_is_dirty=False)
imc = unreal.load_asset("/Game/Input/IMC_Default")
have = {(m.get_editor_property("action").get_name(), str(m.get_editor_property("key").get_editor_property("key_name")))
        for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings") if m.get_editor_property("action")}
for k in ("F", "Gamepad_FaceButton_Left"):
    if ("IA_Interact", k) not in have:
        key = unreal.Key(); key.set_editor_property("key_name", k); imc.map_key(ia, key)
imc.modify(); eal.save_loaded_asset(imc, only_if_is_dirty=False)
unreal.EditorLoadingAndSavingUtils.reload_packages([unreal.load_package("/Game/Input/IMC_Default")])
imc = unreal.load_asset("/Game/Input/IMC_Default")
print("IA_Interact keys:", [str(m.get_editor_property("key").get_editor_property("key_name")) for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings")
                            if m.get_editor_property("action") and m.get_editor_property("action").get_name() == "IA_Interact"], "consume", ia.get_editor_property("consume_input"))
# ---------- helpers
def new_bp(name, comps, variables):
    path = f"{D}/Blueprints/{name}"
    if eal.does_asset_exist(path): eal.delete_asset(path)
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.Actor)
    bp = at.create_asset(name, f"{D}/Blueprints", unreal.Blueprint, f)
    root = sds.k2_gather_subobject_data_for_blueprint(bp)[0]
    objs = {}
    for nm, cls in comps:
        h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=cls, blueprint_context=bp))
        sds.rename_subobject(h, unreal.Text(nm)); objs[nm] = lib.get_object_for_blueprint(lib.get_data(h), bp)
    for nm, typ, editable in variables:
        T.add_variable(bp, nm, typ)
        if editable: T.set_variable_instance_editable(bp, nm, True)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    return bp, objs
def graphs(bp): return {x.get_name(): x for x in T.list_graphs(bp)}
def fn(bp, name, code, params=(), outs=()):
    assert code.count("(") == code.count(")"), name
    if name not in graphs(bp):
        g = T.add_function_graph(bp, name)
        for p, t in params: T.add_function_param(g, p, t, True)
        for p, t in outs: T.add_function_param(g, p, t, False)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    T.write_graph_dsl(graphs(bp)[name], code); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    body = T.read_graph_dsl(graphs(bp)[name]); assert len(body.strip().splitlines()) > 1, f"{name}: empty body, see LogScript"
def events(bp, code):
    assert code.count("(") == code.count(")")
    g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    T.write_graph_dsl(g, code); unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    return g
def wire_interact(bp):
    g = unreal.BlueprintEditorLibrary.find_event_graph(bp)
    info = lambda n: T.get_node_infos([n])[0]
    pin = lambda i, nm, out: next(p.pin_id for p in (i.output_pins if out else i.input_pins) if str(p.name) == nm)
    ev = T.create_node(g, "Input|EnhancedActionEvents|IA_Interact", unreal.IntPoint(-900, 900))
    call = T.create_node(g, "CallFunction|TryInteract", unreal.IntPoint(-450, 900))
    T.connect_pins(pin(info(ev), "Started", True), pin(info(call), "execute", False))
NOW = "(Utilities|Time|GetGameTimeinSeconds)"
PAWN = "(Game|GetPlayerPawn :PlayerIndex 0)"
TARGETED = f"""
(fn Targeted ()
  (bind p (Transformation|GetActorLocation :self {PAWN}))
  (bind d (- (Transformation|GetWorldLocation :self (Variables|Default|GetPrompt)) p))
  (bind flat (Math|Vector|MakeVector (.x d) (.y d) 0.0))
  (bind facing (Math|Vector|DotProduct (Math|Vector|Normalize flat) (Transformation|GetActorForwardVector :self {PAWN})))
  (return (and (< (Math|Vector|VectorLength flat) (Variables|Default|GetNearDist)) (> facing 0.35))))"""
def interact_common(bp):
    fn(bp, "Targeted", TARGETED, outs=(("Out", "bool"),))
    fn(bp, "TryInteract", """
(fn TryInteract ()
  (if (CallFunction|Targeted)
    (Variables|Default|SetOpen (not (Variables|Default|GetOpen)))))""")
def prompt_tick(open_txt, close_txt):
    return f"""
  (bind show (CallFunction|Targeted))
  (Rendering|SetVisibility :self (Variables|Default|GetPrompt) :bNewVisibility show)
  (if show
    (Transformation|SetWorldRotation :self (Variables|Default|GetPrompt) :NewRotation (Math|Rotator|FindLookatRotation :Start (Transformation|GetWorldLocation :self (Variables|Default|GetPrompt)) :Target (Camera|GetCameraLocation :self (Game|GetPlayerCameraManager :PlayerIndex 0)))))"""   # text pins take no literals: static prompt text
def setup_prompt(o, txt):
    o.set_editor_property("text", unreal.Text(txt)); o.set_editor_property("world_size", 12.0)
    o.set_editor_property("horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER)
    o.set_editor_property("vertical_alignment", unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    o.set_editor_property("text_render_color", unreal.Color(r=255, g=236, b=200, a=255))
    o.set_editor_property("hidden_in_game", False); o.set_visibility(False)
    o.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION) if hasattr(o, "set_collision_enabled") else None
# ---------- BP_Door
bp, c = new_bp("BP_Door", [("Leaf", unreal.StaticMeshComponent), ("Prompt", unreal.TextRenderComponent)],
               [("Open", "bool", True), ("Angle", "float", False), ("OpenYaw", "float", True), ("NearDist", "float", True)])
c["Leaf"].set_static_mesh(unreal.load_asset(f"{D}/Meshes/SM_house_02_door0"))
c["Prompt"].set_editor_property("relative_location", unreal.Vector(80, -74, 140)); setup_prompt(c["Prompt"], "F - Open / Close")
cdo = unreal.get_default_object(bp.generated_class())
interact_common(bp)
events(bp, f"""
(event EventBeginPlay ()
  (Input|EnableInput :PlayerController (Game|GetPlayerController :PlayerIndex 0)))
(event EventTick (DeltaSeconds)
  (Variables|Default|SetAngle (Math|Interpolation|FInterpTo :Current (Variables|Default|GetAngle) :Target (select (Variables|Default|GetOpen) (Variables|Default|GetOpenYaw) 0.0) :DeltaTime DeltaSeconds :InterpSpeed 3.2))
  (Transformation|SetRelativeRotation :self (Variables|Default|GetLeaf) :NewRotation (Math|Rotator|MakeRotator :Roll 0.0 :Pitch 0.0 :Yaw (Variables|Default|GetAngle)))
{prompt_tick("F - Open door", "F - Close door")})
""")
wire_interact(bp)
print("BP_Door compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp))
cdo = unreal.get_default_object(bp.generated_class()); cdo.set_editor_property("OpenYaw", 100.0); cdo.set_editor_property("NearDist", 230.0)
eal.save_loaded_asset(bp, only_if_is_dirty=False)
print(" tick:", " ".join(T.read_graph_dsl(unreal.BlueprintEditorLibrary.find_event_graph(bp)).split())[:300])
# ---------- BP_Container
bp, c = new_bp("BP_Container", [("Body", unreal.StaticMeshComponent), ("Lid", unreal.StaticMeshComponent), ("Contents", unreal.StaticMeshComponent),
                                ("Prompt", unreal.TextRenderComponent)],
               [("Open", "bool", True), ("Angle", "float", False), ("OpenRoll", "float", True), ("NearDist", "float", True)])
c["Body"].set_static_mesh(unreal.load_asset(f"{D}/Meshes/SM_crate_01_body")); c["Lid"].set_static_mesh(unreal.load_asset(f"{D}/Meshes/SM_crate_01_lid"))
c["Lid"].set_editor_property("relative_location", unreal.Vector(0, -29.7, 35.8))
c["Contents"].set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
c["Prompt"].set_editor_property("relative_location", unreal.Vector(0, 0, 75)); setup_prompt(c["Prompt"], "F - Open / Close")
interact_common(bp)
events(bp, f"""
(event EventBeginPlay ()
  (Input|EnableInput :PlayerController (Game|GetPlayerController :PlayerIndex 0)))
(event EventTick (DeltaSeconds)
  (Variables|Default|SetAngle (Math|Interpolation|FInterpTo :Current (Variables|Default|GetAngle) :Target (select (Variables|Default|GetOpen) (Variables|Default|GetOpenRoll) 0.0) :DeltaTime DeltaSeconds :InterpSpeed 4.0))
  (Transformation|SetRelativeRotation :self (Variables|Default|GetLid) :NewRotation (Math|Rotator|MakeRotator :Roll (Variables|Default|GetAngle) :Pitch 0.0 :Yaw 0.0))
{prompt_tick("F - Open", "F - Close")})
""")
wire_interact(bp)
print("BP_Container compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp))
cdo = unreal.get_default_object(bp.generated_class()); cdo.set_editor_property("OpenRoll", 105.0); cdo.set_editor_property("NearDist", 170.0)
eal.save_loaded_asset(bp, only_if_is_dirty=False)
# ---------- BP_Splash
bp, c = new_bp("BP_Splash", [("Crown", unreal.StaticMeshComponent), ("Ring", unreal.StaticMeshComponent)], [("Age", "float", False)])
for nm in ("Crown", "Ring"):
    c[nm].set_static_mesh(unreal.load_asset(f"{D}/Meshes/SM_splash_{nm.lower()}")); c[nm].set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    c[nm].set_editor_property("cast_shadow", False)
LIFE = 0.7
events(bp, f"""
(event EventTick (DeltaSeconds)
  (Variables|Default|SetAge (+ (Variables|Default|GetAge) DeltaSeconds))
  (bind t (Math|Float|Min(Float) 1.0 (/ (Variables|Default|GetAge) {LIFE})))
  (bind rise (Math|Float|Max(Float) 0.04 (* 4.4 (* t (- 1.0 t)))))
  (Transformation|SetRelativeScale3D :self (Variables|Default|GetCrown) :NewScale3D (Math|Vector|MakeVector (+ 0.45 (* 0.8 t)) (+ 0.45 (* 0.8 t)) rise))
  (Transformation|SetRelativeScale3D :self (Variables|Default|GetRing) :NewScale3D (Math|Vector|MakeVector (+ 0.35 (* 2.4 t)) (+ 0.35 (* 2.4 t)) 1.0))
  (Rendering|Material|SetScalarParameterValueonMaterials :self (Variables|Default|GetCrown) :ParameterName "Opacity" :ParameterValue (* 0.9 (- 1.0 (* t t))))
  (Rendering|Material|SetScalarParameterValueonMaterials :self (Variables|Default|GetRing) :ParameterName "Opacity" :ParameterValue (* 0.7 (- 1.0 t)))
  (if (>= t 1.0)
    (Actor|DestroyActor)))
""")
print("BP_Splash compile", unreal.BlueprintEditorLibrary.compile_blueprint(bp)); eal.save_loaded_asset(bp, only_if_is_dirty=False)
print(" splash tick:", " ".join(T.read_graph_dsl(unreal.BlueprintEditorLibrary.find_event_graph(bp)).split())[:200])
for p in eal.list_assets(f"{D}/_Probe", recursive=True): eal.delete_asset(p.split(".")[0])
eal.delete_directory(f"{D}/_Probe")
