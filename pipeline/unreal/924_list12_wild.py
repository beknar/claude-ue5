"""The list of 2026-11-12 (docs/improvements12.txt) in the wilderness, on brokenspire (the user's choices: memory improvements12-plan).
Steps (name them; several in one run):
  ruins    its third phase, the twenty kinds of ruins: SourceArt/wilderness/ruins12.json's pieces into the generator's WildPieces
           (r12_<name>#<n>, the old r12_ entries taken out first) and its kinds into WildRuinKinds (RD/RDWildRuin12.cpp lays them:
           a wild place of kind "ruins" is one of them, chosen from its id among the kinds of its biome); a solid piece's mesh
           with no simple collision is given its own shape as its collision (saved: the packs' meshes)
  lairs    its fourth phase, the lairs hidden behind something: SourceArt/wilderness/lairs12.json's pieces (l12_<name>#<n>) and
           its covers into WildLairCovers (RD/RDWildLair12.cpp: a lair's cover, laid by the ruins' layout language, its monsters
           inside it); after ruins (its covers use the ruins' walls, rubble, cliffs and cave)
  sites    its fifth phase, the structures of the wilds: SourceArt/wilderness/sites12.json's pieces (s12_<name>#<n>) and its 34
           kinds into WildSiteKinds (FRDWildSiteKind: the world places them (SitesIn), RD/RDWildSite12.cpp lays them with their
           chests, guards, prisoners and traps), the living beast's creature; after ruins and lairs (it lays their pieces too)
  quests   its 25 quests into WildQuests (RD/RDWildQuest12.cpp runs them); after sites (their things are its pieces)
C++ first (RD/RDWildRuin12.cpp, RD/RDWildLair12.cpp, RD/RDWildSite12.cpp, RD/RDWildQuest12.cpp). Args: steps"""
import os, sys, json, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, wild_tables
importlib.reload(wild_tables)          # (ue_exec keeps a module imported between runs: its REPORT and any change to it)
from wild_tables import les, eal, SA, REPORT, generator, lay_table          # (shared with 926: wild_tables.py)
STEPS = [s for a in sys.argv[1:] for s in a.split(",") if s]


def step_ruins():
    lay_table("ruins12.json", "r12_", "wild_ruin_kinds", "kinds")


def step_sites():
    def more(k, K):
        k.set_editor_property("need_water", K.get("need_water", ""))
        k.set_editor_property("prisoners", int(K.get("prisoners", 0))); k.set_editor_property("traps", int(K.get("traps", 0)))
        k.set_editor_property("quests", [unreal.Name(x) for x in K.get("quests", [])])
    J, g = lay_table("sites12.json", "s12_", "wild_site_kinds", "kinds", unreal.RDWildSiteKind, more)
    # (every quest a structure names must be in quests12.json)
    Q = {x["name"] for x in json.load(open(os.path.join(SA, "quests12.json"), encoding="utf-8"))["quests"]}
    missing = sorted({x for K in J["kinds"] for x in K.get("quests", []) if x not in Q})
    assert not missing, f"924 sites: quests in no table: {missing}"
    B = J.get("beast", {})
    if B:
        m = unreal.load_asset(B["mesh"]); a = unreal.load_asset(B["walk"])
        assert m and a, f"924 sites: the beast's mesh or walk is missing ({B})"
        g.set_editor_property("wild_beast_mesh", m); g.set_editor_property("wild_beast_walk", a)
        g.set_editor_property("wild_beast_scale", float(B.get("scale", 2.6))); g.set_editor_property("wild_beast_speed", float(B.get("speed", 110.0)))
        g.set_editor_property("wild_beast_radius", float(B.get("radius", 45.0)))
        bd = unreal.load_asset(B["build"]) if B.get("build") else None
        assert bd or not B.get("build"), f"924 sites: the beast's build is missing ({B['build']})"
        g.set_editor_property("wild_beast_build", bd)
        g.modify(); les.save_current_level()
    REPORT.append(f"sites: {len(J['kinds'])} kinds, the beast {'set' if B else 'none'}")


def step_quests():
    J = json.load(open(os.path.join(SA, "quests12.json"), encoding="utf-8"))
    g = generator()
    table = {str(k) for k in g.get_editor_property("wild_pieces").keys()}
    out = []
    for Q in J["quests"]:
        for line in Q["stages"]:
            kv = dict(x.split("=", 1) for x in line.split(";") if "=" in x)
            if kv.get("thing"): assert any(t.startswith(kv["thing"]) for t in table), f"924 quests: {Q['name']}'s thing {kv['thing']} is in no table"
        q = unreal.RDWildQuestDef()
        q.set_editor_property("name", Q["name"]); q.set_editor_property("title", Q["title"])
        q.set_editor_property("giver", Q.get("giver", "")); q.set_editor_property("giver_title", Q.get("giver_title", ""))
        q.set_editor_property("offer", Q.get("offer", "")); q.set_editor_property("stages", Q["stages"])
        q.set_editor_property("gold", int(Q.get("gold", 0))); q.set_editor_property("things", Q.get("things", ""))
        out.append(q)
    g.set_editor_property("wild_quests", out)
    g.modify(); les.save_current_level()
    REPORT.append(f"quests: {len(out)}")


def step_lairs():
    lay_table("lairs12.json", "l12_", "wild_lair_covers", "covers")


for s in STEPS:
    {"ruins": step_ruins, "lairs": step_lairs, "sites": step_sites, "quests": step_quests}[s]()
print("924 " + " | ".join(REPORT))
import gc
gc.collect()
