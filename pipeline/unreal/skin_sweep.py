"""Commit a few skin tone U/V values to MHC_Fig4 and capture the preview actor's face for each.
Args: out_dir 'u,v;u,v;...'"""
import sys, os, unreal
out_dir, combos = sys.argv[1], [tuple(map(float, c.split(","))) for c in sys.argv[2].split(";")]
ch = unreal.load_asset("/Game/Fig4/MetaHuman/MHC_Fig4_Final")
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def capture(path):
    cap = eas.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0, 80, 146.5), unreal.Rotator(pitch=0, yaw=-90, roll=0))
    comp = cap.capture_component2d
    rt = unreal.RenderingLibrary.create_render_target2d(world, 384, 384, unreal.TextureRenderTargetFormat.RTF_RGBA8_SRGB)
    comp.texture_target = rt; comp.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    comp.fov_angle = 22; comp.capture_every_frame = False; comp.always_persist_rendering_state = True
    for _ in range(3): comp.capture_scene()
    unreal.RenderingLibrary.export_render_target(world, rt, *os.path.split(path))
    eas.destroy_actor(cap)

for u, v in combos:
    ss = ch.skin_settings; sk = ss.skin; sk.u, sk.v = u, v; ss.skin = sk
    mhs.commit_skin_settings(ch, ss)
    capture(os.path.join(out_dir, f"skin_{u:.2f}_{v:.2f}.png"))
    print("captured", u, v)
