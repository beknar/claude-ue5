"""random_dungeonmagic_level5 (the Summoner), first step: the Mage's clips that exist only in Unreal, exported for the
Summoner's clip maker. Her flinch and death (810 retargeted them onto the Mage from Animations_Warrior) are written as FBX
(with the Mage's skeleton) to SourceArt/summoner/mage_clips/Flinch.fbx and Death.fbx (ignored by git, as every FBX);
blender_numpy/summoner_clips.py transfers them onto the Summoner with her other clips, bone by bone as the Mage's bones
point. (Unreal's IK retargeter, given the pack's mannequin and the Summoner's rig with its extra bones, folded her up on
the floor in the death clip: the transfer that made her other clips does it the same way for these.) Args: none"""
import os, unreal
OUT = r"E:\code\claude-ue5\claude_ue5\SourceArt\summoner\mage_clips"
os.makedirs(OUT, exist_ok=True)
CLIPS = {"Flinch": "/Game/RandomDungeon/Magic/Anims/Anim_Warrior_Get_Hit_1_Caster", "Death": "/Game/RandomDungeon/Magic/Anims/Anim_Warrior_Dead_1_Caster"}
for name, path in CLIPS.items():
    a = unreal.load_asset(path); assert a, path + ": run 810 first"
    t = unreal.AssetExportTask()
    t.set_editor_property("object", a); t.set_editor_property("filename", os.path.join(OUT, name + ".fbx"))
    t.set_editor_property("automated", True); t.set_editor_property("prompt", False); t.set_editor_property("replace_identical", True)
    t.set_editor_property("exporter", unreal.AnimSequenceExporterFBX())
    ok = unreal.Exporter.run_asset_export_task(t)
    f = os.path.join(OUT, name + ".fbx")
    print("RDM5MAGECLIP", name, path.split("/")[-1], "->", f, "ok" if ok and os.path.exists(f) else "FAILED", os.path.getsize(f) if os.path.exists(f) else 0, "bytes",
          round(unreal.AnimationLibrary.get_sequence_length(a), 2), "s")
