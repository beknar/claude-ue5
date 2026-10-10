"""Spawn the MetaHuman preview actor at the origin and the scan 70 cm to her right (−X), for
side-by-side review captures."""
import unreal
ch = unreal.load_asset("/Game/Fig4/MetaHuman/MHC_Fig4_Final")
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if a.get_actor_label().startswith(("REVIEW_", "MetaHuman")) or "MHC_Fig4" in a.get_actor_label():
        eas.destroy_actor(a)
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([ch])
mh = mhs.spawn_meta_human_actor(ch)
print("MH actor", mh.get_actor_label(), mh.get_actor_location())
scan = eas.spawn_actor_from_object(unreal.load_asset("/Game/Fig4/Scan/fig4_scan_full/StaticMeshes/fig4_scan_full"),
                                   unreal.Vector(-70, 0, 0))
scan.set_actor_label("REVIEW_Scan")
for c in mh.get_components_by_class(unreal.SkeletalMeshComponent):
    print(" comp", c.get_name(), c.skeletal_mesh_asset.get_name() if c.skeletal_mesh_asset else None, c.bounds.origin, c.bounds.box_extent)
