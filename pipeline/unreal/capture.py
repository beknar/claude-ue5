"""Render the editor world from a given camera into a PNG with a SceneCapture2D.
Args: out_png x y z pitch yaw fov width height [ortho_width]"""
import sys, os, unreal

out = sys.argv[1]
x, y, z, pitch, yaw, fov = map(float, sys.argv[2:8])
w, h = int(sys.argv[8]), int(sys.argv[9])
ortho = float(sys.argv[10]) if len(sys.argv) > 10 else 0.0

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
cap = eas.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(x, y, z), unreal.Rotator(pitch=pitch, yaw=yaw, roll=0))
try:
    comp = cap.capture_component2d
    rt = unreal.RenderingLibrary.create_render_target2d(world, w, h, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    comp.texture_target = rt
    comp.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    comp.fov_angle = fov
    if ortho > 0:
        comp.projection_type = unreal.CameraProjectionMode.ORTHOGRAPHIC
        comp.ortho_width = ortho
    comp.capture_every_frame = False
    comp.capture_on_movement = False
    comp.always_persist_rendering_state = True
    for _ in range(3):           # warm up temporal effects / streaming
        comp.capture_scene()
    d, f = os.path.split(out)
    unreal.RenderingLibrary.export_render_target(world, rt, d, f)
    print("CAPTURED", out)
finally:
    eas.destroy_actor(cap)
