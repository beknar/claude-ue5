import sys, unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
ALPHA = float(sys.argv[1]) if len(sys.argv) > 1 else -1
abp = unreal.load_asset("/Game/Fig4/Locomotion/Anims/ABP_Unarmed_Fig4")
g = [x for x in T.list_graphs(abp) if x.get_name() == "AnimGraph"][0]
for n in T.find_nodes(g, ""):
    c = n.get_class().get_name()
    i = T.get_node_infos([n])[0]
    if c in ("AnimGraphNode_ControlRig", "K2Node_CallFunction", "K2Node_VariableGet"):
        print(c, i.type_id, "in:", [(str(p.name), len(p.get_editor_property("connected_pins"))) for p in i.input_pins][:12],
              "out:", [(str(p.name), len(p.get_editor_property("connected_pins"))) for p in i.output_pins][:6])
    if c == "AnimGraphNode_ControlRig" and ALPHA >= 0:
        nd = n.get_editor_property("node"); t = nd.export_text()
        import re
        t = re.sub(r"Alpha=[0-9.]+", f"Alpha={ALPHA:.6f}", t)
        nd.import_text(t); n.set_editor_property("node", nd)
        print("alpha now", n.get_editor_property("node").export_text().split("Alpha=")[1][:10])
        for p in i.input_pins:
            if str(p.name) == "Alpha" and p.get_editor_property("connected_pins"):
                print("Alpha pin is driven:", p.get_editor_property("connected_pins"))
            if str(p.name) == "Alpha":
                try: T.set_pin_value(p.pin_id, f"{ALPHA}"); print("alpha pin set")
                except Exception as e: print("pin set", str(e)[:80])
if ALPHA >= 0:
    print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(abp)); unreal.EditorAssetLibrary.save_loaded_asset(abp)
