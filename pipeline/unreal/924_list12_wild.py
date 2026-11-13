"""The list of 2026-11-12 (docs/improvements12.txt) in the wilderness, on brokenspire (the user's choices: memory improvements12-plan).
Steps (name them; several in one run):
  ruins    its third phase, the twenty kinds of ruins: SourceArt/wilderness/ruins12.json's pieces into the generator's WildPieces
           (r12_<name>#<n>, the old r12_ entries taken out first) and its kinds into WildRuinKinds (RD/RDWildRuin12.cpp lays them:
           a wild place of kind "ruins" is one of them, chosen from its id among the kinds of its biome)
C++ first (RD/RDWildRuin12.cpp). Args: steps"""
import os, sys, json, unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
STEPS = [s for a in sys.argv[1:] for s in a.split(",") if s]
SA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "claude_ue5", "SourceArt", "wilderness"))
MAP = "/Game/RandomDungeon/Maps/brokenspire"
REPORT = []


def generator():
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."):
        les.load_level(MAP); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def step_ruins():
    J = json.load(open(os.path.join(SA, "ruins12.json"), encoding="utf-8"))
    g = generator()
    wp = g.get_editor_property("wild_pieces")
    for k in [k for k in wp.keys() if str(k).startswith("r12_")]: wp.pop(k)
    missing, n = [], 0
    for name, paths in J["pieces"].items():
        for i, p in enumerate(paths):
            m = unreal.load_asset(p)
            if not isinstance(m, unreal.StaticMesh): missing.append(p); continue
            wp[unreal.Name(f"r12_{name}#{i + 1}")] = m; n += 1
    assert not missing, f"924 ruins: meshes not found: {missing}"
    g.set_editor_property("wild_pieces", wp)
    # (every part's piece must be in the table, a places' piece or a container: a prefix nothing matches lays nothing, silently)
    table = {str(k) for k in wp.keys()}
    kinds = []
    for K in J["kinds"]:
        for line in K["parts"]:
            kv = dict(x.split("=", 1) for x in line.split(";") if "=" in x)
            if "p" in kv: assert any(t.startswith(kv["p"]) for t in table), f"924 ruins: {K['name']}'s piece {kv['p']} is in no table"
        k = unreal.RDWildRuinKind()
        k.set_editor_property("name", K["name"]); k.set_editor_property("title", K["title"]); k.set_editor_property("text", K["text"])
        k.set_editor_property("biomes", K["biomes"]); k.set_editor_property("weight", float(K.get("weight", 1.0)))
        k.set_editor_property("water", bool(K.get("water", False))); k.set_editor_property("parts", K["parts"])
        k.set_editor_property("loot", K.get("loot", "")); k.set_editor_property("guards", int(K.get("guards", 0)))
        kinds.append(k)
    g.set_editor_property("wild_ruin_kinds", kinds)
    g.modify(); les.save_current_level()
    REPORT.append(f"ruins: {len(kinds)} kinds, {n} meshes in {len(J['pieces'])} pieces")


for s in STEPS:
    {"ruins": step_ruins}[s]()
print("924 " + " | ".join(REPORT))
import gc
gc.collect()
