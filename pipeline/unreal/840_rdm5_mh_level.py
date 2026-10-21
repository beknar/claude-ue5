"""random_dungeonmagic_level5, the Summoner's MetaHuman face, step 3: on the level. The generator's FaceMeta (the face mesh,
its place on her, the bones it follows, her cut-away body material, the brows and lashes: rdm5_mh_face.py from
SourceArt/summoner/face_mh.json) and FaceChannels (each expression as MetaHuman control curves); FaceCues stay the
occasions of face.json (Hurt -> Pain, Cast -> Focus, Loot -> Joy; Fight -> Anger, LowHealth -> Fear, Death -> Dead held).
In play the generator gives her pawn a URDFaceComponent with them; the component makes the face mesh on her. Her own face
(the shapes and patches of 833/834) is cut away under it: 834 run again puts that face back.
Run after 837-839 with the level open (it opens it). Args: none"""
import os, sys, json, importlib, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rdm5_mh_face as MF
importlib.reload(MF)
MAP = "/Game/RandomDungeon/Maps/random_dungeonmagic_level5"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not ues.get_editor_world().get_path_name().startswith(MAP + "."): unreal.EditorLoadingAndSavingUtils.load_map(MAP)
w = ues.get_editor_world(); assert w.get_path_name().startswith(MAP + "."), w.get_path_name()
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
mf, info = MF.meta_face()
F = json.load(open(os.path.join(SA, "summoner", "face.json")))
cues = {}
for occ, c in F["cues"].items():
    q = unreal.RDFaceCue()
    q.set_editor_property("weight", float(c["weight"])); q.set_editor_property("fade_in", float(c["in"]))
    q.set_editor_property("hold", float(c["hold"])); q.set_editor_property("fade_out", float(c["out"]))
    q.set_editor_property("channel", c["channel"]); cues[occ] = q
chans = MF.channels()
names = {str(c.name) for c in chans}
missing = [str(q.channel) for q in cues.values() if str(q.channel) not in names]
assert not missing, "cues without a channel: " + ", ".join(missing)
gen.set_editor_property("face_channels", chans); gen.set_editor_property("face_cues", cues); gen.set_editor_property("face_meta", mf)
les.save_current_level()
print("RDM5MH level", MAP, "| face", mf.mesh.get_name(), info, "| channels", sorted(names), "| cues", {k: str(v.channel) for k, v in cues.items()},
      "| grooms", [g.groom.get_name() for g in mf.grooms], "| body material", mf.body_material.get_name())
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
