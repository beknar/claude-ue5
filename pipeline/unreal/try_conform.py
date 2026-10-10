"""Conform a throwaway character with given overrides, spawn it, capture front+side face, delete.
Args: tag overrides out_dir"""
import sys, os, unreal
tag, overrides, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
name = f"MHC_Try_{tag}"
here = os.path.dirname(os.path.abspath(__file__))
sys.argv = ["02_conform.py", "/Game/Fig4/Conform/fig4_body_target_clean/StaticMeshes/fig4_body_target_clean",
            r"E:\code\claude-ue5\claude_ue5\SourceArt\fig4\fig4_portrait.png", "/Game/Fig4/Try", name, overrides]
exec(compile(open(os.path.join(here, "02_conform.py"), encoding="utf-8").read(), "02_conform.py", "exec"), {"__name__": "__main__"})

ch = unreal.load_asset(f"/Game/Fig4/Try/{name}")
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for a in eas.get_all_level_actors():
    if "PreviewActor" in a.get_actor_label():
        a.set_actor_location(unreal.Vector(0, 0, -1000), False, False)
unreal.get_editor_subsystem(unreal.AssetEditorSubsystem).open_editor_for_assets([ch])
mh = mhs.spawn_meta_human_actor(ch)
mh.set_actor_location(unreal.Vector(0, -400, 0), False, False)

def capture(path, loc, yaw):
    cap = eas.spawn_actor_from_class(unreal.SceneCapture2D, loc, unreal.Rotator(pitch=0, yaw=yaw, roll=0))
    comp = cap.capture_component2d
    rt = unreal.RenderingLibrary.create_render_target2d(world, 512, 512, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    comp.texture_target = rt; comp.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    comp.fov_angle = 22; comp.capture_every_frame = False; comp.always_persist_rendering_state = True
    for _ in range(3): comp.capture_scene()
    unreal.RenderingLibrary.export_render_target(world, rt, *os.path.split(path))
    eas.destroy_actor(cap)

capture(os.path.join(out_dir, f"try_{tag}_front.png"), unreal.Vector(0, -320, 146.5), -90)
capture(os.path.join(out_dir, f"try_{tag}_side.png"), unreal.Vector(80, -400, 146.5), 180)
print("TRY DONE", tag)
