"""random_dungeoncombat_level demo reel: the Level Sequence the Movie Render Queue renders, /Game/RandomDungeon/Cinematics/LS_RDC_Showcase.
It only gives the render its length (45 s at 30 fps) and its one shot: the reel is played live by the pilot script (795)
through the game's own functions, and the picture is the player's view (her third-person camera, turned by the pilot),
so the sequence has no tracks. Rebuilt on every run. Args: [seconds]"""
import sys, unreal
SEC = float(sys.argv[1]) if len(sys.argv) > 1 else 45.0
FPS = 30; PATH = "/Game/RandomDungeon/Cinematics"; NAME = "LS_RDC_Showcase"
EAL = unreal.EditorAssetLibrary
if EAL.does_asset_exist(f"{PATH}/{NAME}"): EAL.delete_asset(f"{PATH}/{NAME}")
seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, PATH, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
seq.set_display_rate(unreal.FrameRate(FPS, 1))
seq.set_playback_start(0); seq.set_playback_end(int(round(SEC * FPS)))
EAL.save_loaded_asset(seq, False)
print("sequence", seq.get_path_name(), seq.get_playback_start(), seq.get_playback_end(), "frames at", FPS, "fps")