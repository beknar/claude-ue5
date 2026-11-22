"""stories15: the user's list of 2026-11-20 (docs/improvements15.txt, item 25: docs/wilderness_ideas.md's idea 8), its plan's fifteenth
phase: story encounters (C++ RD/RDList15n.cpp). From SourceArt/wilderness/stories15.json: brokenspire's encounter director's story kinds
(roaming points of interest with a Story15, the ones of an earlier run taken out first by name; each person's body and each rival's place
checked against the level), the courier's letters, the pursuers, the cart's tilt and the rival. Run after 912 and 920 (which write the
director's kinds anew). No arguments."""
import os, json, gc, unreal
MAPS = "/Game/RandomDungeon/Maps/"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\wilderness"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
J = json.load(open(os.path.join(SA, "stories15.json"), encoding="utf-8"))


def run():
    les.load_level(MAPS + "brokenspire"); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    defs = {str(d.get_editor_property("name")) for d in g.get_editor_property("townsfolk") if d.get_editor_property("mesh")}
    mine = {k["name"] for k in J["kinds"]}
    kinds = [k for k in g.get_editor_property("wild_poi_kinds") if str(k.get_editor_property("name")) not in mine]
    places = {str(k.get_editor_property("name")) for k in kinds if not k.get_editor_property("roaming")}
    for k in J["kinds"]:
        if k["folk"]: assert k["folk"] in defs, ("no townsfolk body", k["folk"])
        for p in [x for x in k.get("place", "").split(",") if x]: assert p in places, ("no point of interest", p)
        d = unreal.RDWildPoiKind()
        d.set_editor_property("name", k["name"]); d.set_editor_property("title", k["title"]); d.set_editor_property("biomes", ["*"])
        d.set_editor_property("weight", float(k["weight"])); d.set_editor_property("roaming", True)
        d.set_editor_property("folk", k["folk"]); d.set_editor_property("text", k["text"]); d.set_editor_property("gift", k["gift"])
        d.set_editor_property("gift_gold", int(k["gold"])); d.set_editor_property("place", k.get("place", "")); d.set_editor_property("story15", k["story"])
        kinds.append(d)
    g.set_editor_property("wild_poi_kinds", kinds)
    r = J["rival"]
    assert r["def"] in defs, ("no townsfolk body", r["def"])
    for p, v in (("story_letters15", J["letters"]), ("story_default_sender15", J["default_sender"]), ("story_pursuers15", int(J["pursuers"])),
                 ("story_cart_tilt15", float(J["cart_tilt"])), ("story_rival_name15", r["name"]), ("story_rival_def15", r["def"]),
                 ("story_rival_hello15", r["hello"]), ("story_rival_again15", r["again"]), ("story_rival_won15", r["won"]), ("story_rival_lost15", r["lost"]),
                 ("story_rival_lead15", float(r["lead"])), ("story_rival_reach_cm15", float(r["reach_m"]) * 100.0)):
        g.set_editor_property(p, v)
    g.modify(); les.save_current_level()
    print(f"STORIES15 941 brokenspire: {len(J['kinds'])} story kinds ({', '.join(k['story'] for k in J['kinds'])}), {len(J['letters'])} letters, rival {r['name']}")
    g = None


run()
gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
