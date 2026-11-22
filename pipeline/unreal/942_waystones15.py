"""waystones15: the user's list of 2026-11-20 (docs/improvements15.txt, item 25: docs/wilderness_ideas.md's idea 9 in part), its plan's
sixteenth phase: getting about (C++ RD/RDList15o.cpp, RD/RDList14k.cpp). From SourceArt/wilderness/waystones15.json: brokenspire's
switches for the waystones and the crossroads posts and the stone's height; checks the places' table's "stone" piece and the map's
wmap_waystone symbol (run blender_numpy/wild_symbols.py SourceArt/wilderness/symbols and `887 symbols` first). No arguments."""
import os, json, gc, unreal
MAPS = "/Game/RandomDungeon/Maps/"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\wilderness"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
J = json.load(open(os.path.join(SA, "waystones15.json"), encoding="utf-8"))


def run():
    les.load_level(MAPS + "brokenspire"); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    pieces = {str(k) for k in g.get_editor_property("wild_pieces").keys()}
    assert any(n.startswith("stone") for n in pieces), "no stone piece in the places' table: no waystone would be laid"
    art = {str(k) for k in g.get_editor_property("ui_art").keys()}
    assert "wmap_waystone" in art, "no wmap_waystone in the UIArt: run wild_symbols.py and 887 symbols first"
    g.set_editor_property("waystones15", bool(J["waystones"]))
    g.set_editor_property("cross_posts15", bool(J["crossroads_posts"]))
    g.set_editor_property("waystone_height15", float(J["height_m"]))
    g.modify(); les.save_current_level()
    print(f"WAYSTONES15 942 brokenspire: waystones {J['waystones']} ({J['height_m']} m), crossroads posts {J['crossroads_posts']}")
    g = None


run()
gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
