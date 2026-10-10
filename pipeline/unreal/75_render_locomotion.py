"""MRQ job for a showcase sequence. Args: out_dir preview|final [level] [sequence] [file_prefix]"""
import sys, unreal
OUT = sys.argv[1]; MODE = sys.argv[2] if len(sys.argv) > 2 else "preview"
LEVEL = sys.argv[3] if len(sys.argv) > 3 else "/Game/Fig4/Maps/L_Fig4_Meadow_Cine"
SEQ = sys.argv[4] if len(sys.argv) > 4 else "/Game/Fig4/Cinematics/LS_Fig4_Locomotion"
mq = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
queue = mq.get_queue(); queue.delete_all_jobs()
j = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
j.job_name = "Fig4_Locomotion_" + MODE
j.sequence = unreal.SoftObjectPath(SEQ); j.map = unreal.SoftObjectPath(LEVEL)
cfg = j.get_configuration()
o = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
o.output_resolution = unreal.IntPoint(*((960, 540) if MODE == "preview" else (1920, 1080)))
o.output_directory = unreal.DirectoryPath(OUT)
o.file_name_format = (sys.argv[5] if len(sys.argv) > 5 else "fig4_loco") + ".{frame_number}"
o.override_existing_output = True
cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
png = cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
aa.override_anti_aliasing = True
if MODE == "preview":
    aa.spatial_sample_count = 1; aa.temporal_sample_count = 1; aa.anti_aliasing_method = unreal.AntiAliasingMethod.AAM_TEMPORAL_AA
else:
    aa.spatial_sample_count = 1; aa.temporal_sample_count = 8; aa.anti_aliasing_method = unreal.AntiAliasingMethod.AAM_NONE
aa.engine_warm_up_count = 32; aa.render_warm_up_count = 32; aa.use_camera_cut_for_warm_up = False
cv = cfg.find_or_add_setting_by_class(unreal.MoviePipelineConsoleVariableSetting)
cvars = {"r.Streaming.FullyLoadUsedTextures": 1, "r.SkinCache.Mode": 1, "r.ScreenPercentage": 100}
if MODE != "preview":
    cvars.update({"r.HairStrands.Visibility.MSAA.SamplePerPixel": 8, "r.Lumen.Reflections.HierarchicalScreenTraces": 1,
                  "r.Nanite.MaxPixelsPerEdge": 0.5, "r.DepthOfFieldQuality": 4,
                  "r.Shadow.Virtual.SMRT.RayCountDirectional": 16, "r.Shadow.Virtual.SMRT.SamplesPerRayDirectional": 8})
for k, v in cvars.items():
    try: cv.add_or_update_console_variable(k, float(v))
    except Exception as e: print("cvar", k, str(e)[:60])
go = cfg.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)
go.cinematic_quality_settings = True; go.texture_streaming = unreal.MoviePipelineTextureStreamingMethod.FULLY_LOAD
print("game mode override:", go.get_editor_property("game_mode_override"))
mq.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)
print("RENDER", MODE, "->", OUT)
