"""starship_level demo reel: the Movie Render Queue job for LS_SS_Showcase on the playable level itself (no Cine copy:
the game runs as in play, under SSGameMode, and the pilot script flies it). Arm 805 first.
  preview  640 x 360        final  1920 x 1080
Both use 8 temporal samples a frame and no other anti-aliasing: the game is stepped at 240 Hz either way, so the pilot
flies the same flight in the preview and in the final render. Args: out_dir preview|final [file_prefix]"""
import sys, unreal
OUT = sys.argv[1]; MODE = sys.argv[2] if len(sys.argv) > 2 else "preview"; PREFIX = sys.argv[3] if len(sys.argv) > 3 else "ss"
mq = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
queue = mq.get_queue(); queue.delete_all_jobs()
j = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
j.job_name = "Starship_" + MODE
j.sequence = unreal.SoftObjectPath("/Game/Starship/Cinematics/LS_SS_Showcase"); j.map = unreal.SoftObjectPath("/Game/Starship/Maps/starship_level")
cfg = j.get_configuration()
o = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
o.output_resolution = unreal.IntPoint(*((640, 360) if MODE == "preview" else (1920, 1080)))
o.output_directory = unreal.DirectoryPath(OUT); o.file_name_format = PREFIX + ".{frame_number}"; o.override_existing_output = True
cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
aa.override_anti_aliasing = True; aa.spatial_sample_count = 1; aa.temporal_sample_count = 8; aa.anti_aliasing_method = unreal.AntiAliasingMethod.AAM_NONE
aa.engine_warm_up_count = 32; aa.render_warm_up_count = 32; aa.use_camera_cut_for_warm_up = False
cv = cfg.find_or_add_setting_by_class(unreal.MoviePipelineConsoleVariableSetting)
for k, v in {"r.Streaming.FullyLoadUsedTextures": 1, "r.ScreenPercentage": 100, "r.Nanite.MaxPixelsPerEdge": 0.5 if MODE != "preview" else 1.0}.items():
    try: cv.add_or_update_console_variable(k, float(v))
    except Exception as e: print("cvar", k, str(e)[:60])
go = cfg.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)
go.cinematic_quality_settings = True; go.texture_streaming = unreal.MoviePipelineTextureStreamingMethod.FULLY_LOAD
go.set_editor_property("soft_game_mode_override", unreal.SSGameMode)
print("game mode:", go.get_editor_property("soft_game_mode_override"))
mq.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)
print("RENDER", MODE, "->", OUT)