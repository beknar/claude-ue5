"""Pose fig4 (body anim single node), attach the fitted outfit (same pose), fix the bulb emissive."""
import unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
mel = unreal.MaterialEditingLibrary
pose = unreal.load_asset("/Game/Fig4/Anim/fig4_pose")
fig = next(a for a in eas.get_all_level_actors() if a.get_actor_label() == "Fig4")

def play_pose(c):
    try: c.set_update_animation_in_editor(True)
    except Exception as e: print("update-in-editor:", str(e)[:80])
    c.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    try:
        c.set_editor_property("animation_data", unreal.SingleAnimationPlayData(anim_to_play=pose, saved_looping=False,
                              saved_playing=False, saved_position=0.0, saved_play_rate=1.0))
    except Exception as e: print("anim data:", str(e)[:80])
    c.set_animation(pose)
    c.set_position(0.0, False)

body = next(c for c in fig.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == "Body")
play_pose(body)
fig = next(a for a in eas.get_all_level_actors() if a.get_actor_label() == "Fig4")   # construction script may rebuild
body = next(c for c in fig.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == "Body")
print("body anim mode", body.get_animation_mode())

for a in eas.get_all_level_actors():
    if a.get_actor_label() == "Fig4_Outfit":
        eas.destroy_actor(a)
oa = eas.spawn_actor_from_class(unreal.SkeletalMeshActor, fig.get_actor_location(), fig.get_actor_rotation())
oa.set_actor_label("Fig4_Outfit")
oc = oa.skeletal_mesh_component
oc.set_skeletal_mesh_asset(unreal.load_asset("/Game/Fig4/Outfit/fig4_outfit_skinned"))
play_pose(oc)
oc.set_editor_property("cast_shadow", True)
oa.attach_to_component(body, "", unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.SNAP_TO_TARGET,
                       unreal.AttachmentRule.KEEP_WORLD, False)

# bulb material: emissive into the unlit BSDF (pin is "EmissiveColor")
bm = unreal.load_asset("/Game/Fig4/Studio/Materials/M_Bulb")
mel.delete_all_material_expressions(bm)
col = mel.create_material_expression(bm, unreal.MaterialExpressionConstant3Vector, -400, 0)
col.set_editor_property("constant", unreal.LinearColor(40.0, 18.0, 5.0, 1))
unlit = mel.create_material_expression(bm, unreal.MaterialExpressionSubstrateUnlitBSDF, -150, 0)
print("bulb link", mel.connect_material_expressions(col, "", unlit, "EmissiveColor"))
mel.connect_material_property(unlit, "", unreal.MaterialProperty.MP_FRONT_MATERIAL)
mel.recompile_material(bm); unreal.EditorAssetLibrary.save_loaded_asset(bm)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("posed + outfit attached")
