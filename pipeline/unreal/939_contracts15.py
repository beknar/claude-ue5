"""contracts15: the user's list of 2026-11-20 (docs/improvements15.txt, item 25: docs/wilderness_ideas.md's idea 5), its plan's
thirteenth phase: monster contracts on the wild towns' boards (C++ RD/RDList15l.cpp). From SourceArt/wilderness/contracts15.json:
brokenspire's beasts (each kind checked against the level's monsters, three signs each), how many a board posts, the weakness's share and
the bounty's gold. Needs `938 data` (the glow's mesh and material the signs take). No arguments."""
import os, json, gc, unreal
MAPS = "/Game/RandomDungeon/Maps/"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\wilderness"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
J = json.load(open(os.path.join(SA, "contracts15.json"), encoding="utf-8"))


def run():
    les.load_level(MAPS + "brokenspire"); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    kinds = {str(m.get_editor_property("name")) for m in g.get_editor_property("monsters")}
    lines = []
    for b in J["beasts"]:
        assert b["kind"] in kinds, ("no monster", b["kind"])
        assert len(b["signs"]) == 3, (b["name"], "three signs")
        for f in (b["name"], b["weakness"], b["offer"]) + tuple(b["signs"]):
            assert "|" not in f and "~" not in f, f
        lines.append("|".join([b["name"], b["kind"], f"{b['hp']:g}", str(int(b["tier_up"])), b["weakness"], b["offer"], "~".join(b["signs"])]))
    assert g.get_editor_property("reward_glow_mesh15"), "run 938 data first (the glow)"
    assert int(J["per_board"]) <= len(lines), ("a board would post one beast twice", J["per_board"], len(lines))
    g.set_editor_property("contracts15", lines)
    g.set_editor_property("contracts_per_board15", int(J["per_board"]))
    g.set_editor_property("contract_weak_share15", float(J["weak_share"]))
    g.set_editor_property("contract_gold15", float(J["gold"]))
    g.modify(); les.save_current_level()
    print(f"CONTRACTS15 939 brokenspire: {len(lines)} beasts, {J['per_board']} a board, weakness +{J['weak_share']:g}, {J['gold']} g at tier 1")
    g = None


run()
gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
