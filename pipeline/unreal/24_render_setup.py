"""Cameras + level sequences for the final renders, and a Movie Render Queue job per sequence.
Args: out_dir [render]"""
import sys, unreal
OUT = sys.argv[1]; DO_RENDER = "render" in sys.argv
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
eal = unreal.EditorAssetLibrary
at = unreal.AssetToolsHelpers.get_asset_tools()
LEVEL = "/Game/Fig4/Maps/L_Fig4_Studio"

def cine(label, loc, target, focal, fstop, focus=None, aspect=1.5):
    for a in eas.get_all_level_actors():
        if a.get_actor_label() == label: eas.destroy_actor(a)
    c = eas.spawn_actor_from_class(unreal.CineCameraActor, unreal.Vector(*loc))
    c.set_actor_label(label)
    c.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*loc), unreal.Vector(*target)), False)
    cc = c.get_cine_camera_component()
    # sensor aspect matches the render aspect (no letterboxing)
    fb = cc.get_editor_property("filmback"); fb.sensor_width = 36.0; fb.sensor_height = 36.0 / aspect
    cc.set_editor_property("filmback", fb)
    cc.set_editor_property("current_focal_length", focal); cc.set_editor_property("current_aperture", fstop)
    fs = cc.get_editor_property("focus_settings"); fs.focus_method = unreal.CameraFocusMethod.MANUAL
    fs.manual_focus_distance = focus or (unreal.Vector(*loc) - unreal.Vector(*target)).length()
    cc.set_editor_property("focus_settings", fs)
    return c

EYES = (0.0, 0.0, 154.0)
camA = cine("Cam_FullBody", (0, 430, 112), (0, 0, 95), 50.0, 2.8, focus=(unreal.Vector(0, 430, 112) - unreal.Vector(0, 8, 120)).length(), aspect=0.8)
# she faces +Y: her eyes are ~9 cm in front of the head centre
camB = cine("Cam_Portrait", (14, 95, 151), (0, 0, 146), 85.0, 2.0, focus=(unreal.Vector(14, 95, 151) - unreal.Vector(0, 9, 153)).length(), aspect=0.8)
camC = cine("Cam_Wide", (-95, 500, 150), (0, -40, 102), 32.0, 4.0, focus=(unreal.Vector(-95, 500, 150) - unreal.Vector(0, 5, 110)).length(), aspect=16 / 9)

def sequence(name, cams):
    path = f"/Game/Fig4/Cinematics/{name}"
    if eal.does_asset_exist(path): eal.delete_asset(path)
    seq = at.create_asset(name, "/Game/Fig4/Cinematics", unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    seq.set_display_rate(unreal.FrameRate(24, 1))
    seq.set_playback_start(0); seq.set_playback_end(len(cams))
    cut_track = seq.add_track(unreal.MovieSceneCameraCutTrack)
    for i, cam in enumerate(cams):
        b = seq.add_possessable(cam)
        sec = cut_track.add_section()
        sec.set_range(i, i + 1)
        sec.set_camera_binding_id(seq.get_binding_id(b) if hasattr(seq, "get_binding_id") else b.get_binding_id())
    eal.save_loaded_asset(seq)
    return path

seq_portrait = sequence("LS_Fig4_Portraits", [camA, camB])
seq_wide = sequence("LS_Fig4_Wide", [camC])
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print("sequences:", seq_portrait, seq_wide)

mq = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
queue = mq.get_queue(); queue.delete_all_jobs()
def job(seq_path, res, label):
    j = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
    j.job_name = label
    j.sequence = unreal.SoftObjectPath(seq_path); j.map = unreal.SoftObjectPath(LEVEL)
    cfg = j.get_configuration()
    o = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    o.output_resolution = unreal.IntPoint(*res)
    o.output_directory = unreal.DirectoryPath(OUT)
    o.file_name_format = "{sequence_name}_{camera_name}"
    o.override_existing_output = True
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
    cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
    aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
    aa.spatial_sample_count = 1; aa.temporal_sample_count = 32
    aa.override_anti_aliasing = True; aa.anti_aliasing_method = unreal.AntiAliasingMethod.AAM_NONE
    aa.engine_warm_up_count = 48; aa.render_warm_up_count = 48; aa.use_camera_cut_for_warm_up = False
    cv = cfg.find_or_add_setting_by_class(unreal.MoviePipelineConsoleVariableSetting)
    for k, v in {"r.HairStrands.Visibility.MSAA.SamplePerPixel": 8, "r.Lumen.Reflections.HierarchicalScreenTraces": 1,
                 "r.MegaLights.NumSamplesPerPixel": 4, "r.Nanite.MaxPixelsPerEdge": 0.5,
                 "r.Shadow.Virtual.SMRT.RayCountLocal": 16, "r.Shadow.Virtual.SMRT.SamplesPerRayLocal": 8,
                 "r.DepthOfFieldQuality": 4, "r.MotionBlurQuality": 0, "r.ScreenPercentage": 100,
                 "r.Streaming.FullyLoadUsedTextures": 1, "r.SkinCache.Mode": 1}.items():
        try:
            cv.add_or_update_console_variable(k, float(v))
        except Exception as e:
            print("cvar", k, str(e)[:60])
    try:
        go = cfg.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)
        go.cinematic_quality_settings = True; go.texture_streaming = unreal.MoviePipelineTextureStreamingMethod.FULLY_LOAD
    except Exception as e:
        print("game override:", str(e)[:80])
    return j
job(seq_portrait, (1600, 2000), "Fig4_Portraits")
job(seq_wide, (2560, 1440), "Fig4_Wide")
print("queue jobs:", len(queue.get_jobs()))
if DO_RENDER:
    mq.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)
    print("RENDER started ->", OUT)
