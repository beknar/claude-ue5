"""random_dungeonmagic_level (and _level2, _level3) demo reel: the Level Sequence the Movie Render Queue renders,
/Game/RandomDungeon/Cinematics/LS_RDM_Showcase (level 2: LS_RDM2_Showcase, level 3: LS_RDM3_Showcase).
It only gives the render its length (45 s at 30 fps) and its one shot: the reel is played live by the pilot script (815)
through the game's own functions, and the picture is the player's view (her third-person camera, turned by the pilot),
so the sequence has no tracks. Rebuilt on every run: an existing one is emptied, not deleted (deleting a loaded sequence
and making it again under its name gives None, and left it deleted for the session). Level 4: LS_RDM4_Showcase (one hero's
run), and "4select": LS_RDM4select_Showcase (the menu, 829); level 5 and "5select" the same for the Summoner's armour
reel. Args: [seconds] [level: 1, 2, 3, 4, 4select, 5 or 5select]"""
import sys, unreal
SEC = float(sys.argv[1]) if len(sys.argv) > 1 else 45.0
LV = sys.argv[2] if len(sys.argv) > 2 else "1"
FPS = 30; PATH = "/Game/RandomDungeon/Cinematics"; NAME = "LS_RDM%s_Showcase" % ("" if LV == "1" else LV)
EAL = unreal.EditorAssetLibrary
if EAL.does_asset_exist(f"{PATH}/{NAME}"):
    seq = unreal.load_asset(f"{PATH}/{NAME}")
    for b in seq.get_bindings(): b.remove()
    for t in seq.get_tracks(): seq.remove_track(t)
else:
    seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, PATH, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
seq.set_display_rate(unreal.FrameRate(FPS, 1))
seq.set_playback_start(0); seq.set_playback_end(int(round(SEC * FPS)))
EAL.save_loaded_asset(seq, False)
print("sequence", seq.get_path_name(), seq.get_playback_start(), seq.get_playback_end(), "frames at", FPS, "fps")
