"""sfc_monolith (copy made by 700): remove what the persistent sf-city-level provides - sun, sky light, atmosphere, height
fog, sky blueprint, unbound post-process, showcase camera + sequence. Keeps the landscape, the megastructure, its rect
lights, cloud FX and the packed ground-detail actors. Saves the sub-level map."""
import unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MAP = "/Game/SFCityLevel/Maps/sfc_monolith"
if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
assert ues.get_editor_world().get_path_name().startswith(MAP + ".")
DROP = (unreal.DirectionalLight, unreal.SkyLight, unreal.SkyAtmosphere, unreal.ExponentialHeightFog, unreal.PostProcessVolume,
        unreal.CineCameraActor, unreal.LevelSequenceActor, unreal.VolumetricCloud)
gone = []
for a in eas.get_all_level_actors():
    if isinstance(a, DROP) or a.get_class().get_name() in ("BP_sky_C",):
        gone.append(a.get_class().get_name()); eas.destroy_actor(a)
les.save_current_level()
print("removed", len(gone), sorted(set(gone)))
del gone
import gc; gc.collect()
