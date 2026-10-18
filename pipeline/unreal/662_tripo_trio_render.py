"""Tripo trio / quartet showcase: the Movie Render Queue job for LS_Tripo_Trio_Showcase in L_Tripo_Trio_Showcase, or
LS_Tripo_Quartet_Showcase in L_Tripo_Quartet_Showcase (arm 661 first, with the same trio|quartet: it puts the fire and the
bolts in while the queue renders). The queue's own game mode (no pawn, no HUD).
  preview  640 x 360        final  1920 x 1080
8 temporal samples a frame, no other anti-aliasing; warm-up only before frame 0 (not at the camera cuts: the pilot's
fire runs on the sequence's clock). first-last: only those frames (a check of one part). Args: out_dir preview|final [file_prefix] [trio|quartet] [first-last]"""
import sys, unreal
OUT = sys.argv[1]; MODE = sys.argv[2] if len(sys.argv) > 2 else "preview"; PREFIX = sys.argv[3] if len(sys.argv) > 3 else "trio"
NAME = {"trio": "Trio", "quartet": "Quartet"}[sys.argv[4] if len(sys.argv) > 4 else "trio"]
mq = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
queue = mq.get_queue(); queue.delete_all_jobs()
j = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
j.job_name = f"Tripo{NAME}_" + MODE
j.sequence = unreal.SoftObjectPath(f"/Game/JRPG/Cinematics/LS_Tripo_{NAME}_Showcase"); j.map = unreal.SoftObjectPath(f"/Game/JRPG/Maps/L_Tripo_{NAME}_Showcase")
cfg = j.get_configuration()
o = cfg.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
o.output_resolution = unreal.IntPoint(*((640, 360) if MODE == "preview" else (1920, 1080)))
if len(sys.argv) > 5:
    a_, b_ = (int(x) for x in sys.argv[5].split("-"))
    o.use_custom_playback_range = True; o.custom_start_frame = a_; o.custom_end_frame = b_
o.output_directory = unreal.DirectoryPath(OUT); o.file_name_format = PREFIX + ".{frame_number}"; o.override_existing_output = True
cfg.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
cfg.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
aa = cfg.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
aa.override_anti_aliasing = True; aa.spatial_sample_count = 1; aa.temporal_sample_count = 8; aa.anti_aliasing_method = unreal.AntiAliasingMethod.AAM_NONE
aa.engine_warm_up_count = 32; aa.render_warm_up_count = 32; aa.use_camera_cut_for_warm_up = False
cv = cfg.find_or_add_setting_by_class(unreal.MoviePipelineConsoleVariableSetting)
for k, v in {"r.Streaming.FullyLoadUsedTextures": 1, "r.ScreenPercentage": 100}.items():
    try: cv.add_or_update_console_variable(k, float(v))
    except Exception as e: print("cvar", k, str(e)[:60])
go = cfg.find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)
go.cinematic_quality_settings = True; go.texture_streaming = unreal.MoviePipelineTextureStreamingMethod.FULLY_LOAD
mq.render_queue_with_executor(unreal.MoviePipelinePIEExecutor)
print("RENDER", MODE, "->", OUT)
