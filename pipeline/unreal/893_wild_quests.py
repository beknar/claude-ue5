"""Brokenspire's captain's two quests in the wilderness (2026-11-07): "Wolves on the Mill Road" (wild:wolves) and "The Lost
Patrol" (wild:patrol), offered as "later" until the wilderness opened the gate. Their places, monsters and counting are C++
(FRDWildWorld::MakeQuestPlaces, RDWildPlaces.cpp, RDWildQuest.cpp); this writes their words (offer, done, hint) and numbers
from SourceArt/brokenspire/town.json into the brokenspire level's quests, the other quests left as they are (882 writes the
same entries from the same file when it runs). Args: none"""
import os, json, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
MAP = "/Game/RandomDungeon/Maps/brokenspire"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\brokenspire"
D = json.load(open(os.path.join(SA, "town.json"), encoding="utf-8"))
WILD = {q["id"]: q for q in D["quests"] if str(q["goal"]).startswith("wild:")}
w = ues.get_editor_world()
if not w.get_path_name().startswith(MAP + "."): les.load_level(MAP)
g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
quests = list(g.get_editor_property("quests"))
done = []
for x in quests:
    q = WILD.get(str(x.get_editor_property("id")))
    if not q or str(x.get_editor_property("town")): continue
    for k, v in (("title", q["title"]), ("offer", q["offer"]), ("done", q.get("done", "")), ("goal", q["goal"]), ("count", int(q.get("count", 1))),
                 ("gold", int(q.get("gold", 0))), ("reward_item", q.get("reward", "None")), ("hint", q.get("hint", ""))):
        x.set_editor_property(k, v)
    done.append(q["id"])
assert sorted(done) == sorted(WILD), f"the level lacks {sorted(set(WILD) - set(done))}: run 882 first"
g.set_editor_property("quests", quests)
les.save_current_level()
print("WILDQUESTS", done, "written; saved", ues.get_editor_world().get_path_name())
import gc
del g, quests, x
gc.collect()
