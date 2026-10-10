"""Reimport darker rock/dirt albedo; grass: no distance-field lighting (removes blocky DF shadows)."""
import os, sys, importlib, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mat_lib as L
importlib.reload(L)
SRC = r"E:\code\claude-ue5\claude_ue5\SourceArt\terrain"
for n in ("T_Rock_BC", "T_Dirt_BC"):
    L.import_texture(os.path.join(SRC, n + ".png"), "/Game/Fig4/World/Textures", "color")
g = unreal.load_asset("/Game/Fig4/World/Meshes/SM_GrassClump/StaticMeshes/SM_GrassClump")
try:
    bs = g.get_source_model(0).build_settings
    bs.set_editor_property("generate_mesh_distance_field", False)
    sm0 = g.get_source_model(0); sm0.build_settings = bs
    g.set_editor_property("source_models", [sm0])
except Exception as e:
    print("df build setting:", e)
L.eal.save_loaded_asset(g)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Grass":
        for c in a.get_components_by_class(unreal.HierarchicalInstancedStaticMeshComponent):
            c.set_editor_property("affect_distance_field_lighting", False)
            c.set_editor_property("affect_dynamic_indirect_lighting", False)
            print("grass DF off", c.get_name())
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
