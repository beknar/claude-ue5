"""random_dungeonmagic_level5, Summoner2, step 7: she is the level's hero. On the level's generator:
- her spell: the Mage's fire as the Summoner had it (834), with her own clips (846's spell_s2.json: the casts retargeted
  onto her MetaHuman body, each bolt released where her right hand moves fastest; her flinch and death);
- her face: FaceMeta from SourceArt/summoner2/face_s2.json (rdm5_mh_face.py): the built face mesh on her body, its neck and
  head bones following her body's, the hair, brows, lashes and peach fuzz (844's colours), the bikini following her body
  (845); FaceChannels the MetaHuman control curves of the sixteen FACS expressions (face_mh.json's), FaceCues the
  occasions of face.json (Hurt -> Pain, Cast -> Focus, Loot -> Joy; Fight -> Anger, LowHealth -> Fear, Death -> Dead held);
- the level's game mode BP_RDM5S2_GameMode (847: her as the pawn).
834 and 840 run again put the first Summoner back. Run after 842-847 and 819. Args: none"""
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
S = json.load(open(os.path.join(SA, "random_dungeon_magic5", "spell_s2.json")))
d = gen.get_editor_property("weapons")[0]
d.set_editor_property("attacks", [unreal.load_asset(c["clip"]) for c in S["casts"]])
d.set_editor_property("attack_starts", [0.0 for c in S["casts"]]); d.set_editor_property("attack_ends", [float(c["end"]) for c in S["casts"]])
d.set_editor_property("hit_times", [float(c["hit"]) for c in S["casts"]])
d.set_editor_property("get_hit", unreal.load_asset(S["flinch"])); d.set_editor_property("death", unreal.load_asset(S["death"]))
assert all(d.attacks) and d.get_hit and d.death
gen.set_editor_property("weapons", [d])
J = MF.load(os.path.join("summoner2", "face_s2.json"))
mf, info = MF.meta_face(J)
F = json.load(open(os.path.join(SA, "summoner", "face.json")))
cues = {}
for occ, c in F["cues"].items():
    q = unreal.RDFaceCue()
    q.set_editor_property("weight", float(c["weight"])); q.set_editor_property("fade_in", float(c["in"]))
    q.set_editor_property("hold", float(c["hold"])); q.set_editor_property("fade_out", float(c["out"]))
    q.set_editor_property("channel", c["channel"]); cues[occ] = q
chans = MF.channels(J); names = {str(c.name) for c in chans}
missing = [str(q.channel) for q in cues.values() if str(q.channel) not in names]
assert not missing, "cues without a channel: " + ", ".join(missing)
gen.set_editor_property("face_channels", chans); gen.set_editor_property("face_cues", cues); gen.set_editor_property("face_meta", mf)
ws = w.get_world_settings()
ws.set_editor_property("default_game_mode", unreal.load_asset("/Game/RandomDungeon/Blueprints/BP_RDM5S2_GameMode").generated_class())
les.save_current_level()
back = gen.get_editor_property("weapons")[0]
print("S2LEVEL", MAP, "| casts", [a.get_name() for a in back.attacks], "bolts at", [round(h, 2) for h in back.hit_times],
      "| flinch", back.get_hit.get_name(), "death", back.death.get_name(), "| face", mf.mesh.get_name(), info,
      "| grooms", [g.groom.get_name() for g in mf.grooms], "| outfits", [o.get_name() for o in mf.outfits],
      "| channels", len(chans), "| game mode", ws.get_editor_property("default_game_mode").get_name())
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
