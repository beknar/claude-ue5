"""The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), its eighth phase (items 9 and
11): the wilds' people struck, killed and looted ("if a random monster encounter comes across a wandering NPC before it reaches
the player, it should attack the NPC instead, damaging and killing it"; "kill NPCs and loot them"). C++: RD/RDList14h.cpp.

Parts (args):
  clips   the Dwarf pack's unarmed death, flinch and run (SourceArt/wilderness/folk14.json's "clips") retargeted onto the NPC pack's
          Manny through 918's retargeter (RTG_Guard_Dwarf_To_NPCManny; run 918 guards first), as every townsfolk def's WorkClips
          Die, Hit and Run on brokenspire (the defs whose mesh is on that skeleton, the packs' own copies of it made compatible as
          914 sleep's).
  data    brokenspire: bWildFolkHurt14 on, the people's hit points, gold and things (WildFolkLoot14), how near a person a monster
          takes it for its foe (WildFolkPreyCm14) and how fast it runs (WildFolkRunSpeed14).
Idempotent: the clips made again in their folder, the defs' three clips and the data set anew.
"""
import json, os, sys, gc
import unreal

SA = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "SourceArt")
J = json.load(open(os.path.join(SA, "wilderness", "folk14.json"), encoding="utf-8"))
eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MAPS = "/Game/RandomDungeon/Maps/"
TD = "/Game/RandomDungeon/Anims/Town/Hurt"
RTG = "/Game/RandomDungeon/Anims/Town/Rigs/RTG_Guard_Dwarf_To_NPCManny"
SRC = "/Game/Dwarf_Pack/Animations/2Without_Weapon/"
SKEL = "/Game/NPC_Characters_Pack/Demoscene_UE5/Mesh/SKM_Manny_Skeleton"
REPORT = []


def each(maps, fn, label):
    for m in maps:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"{label}: no map {m}"); continue
        les.load_level(MAPS + m); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
        what = fn(g)
        g.modify(); les.save_current_level()
        g = None; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        REPORT.append(f"930 {label} {m}: {what}")


def make_clips():
    rtg = unreal.load_asset(RTG)
    assert rtg, "no " + RTG + ": run 918 guards first"
    src_mesh = unreal.load_asset("/Game/Dwarf_Pack/Mesh/SK_Mannequin"); assert src_mesh
    # (the target mesh as 918 found it: the NPC pack's Manny)
    tgt_mesh = unreal.load_asset("/Game/NPC_Characters_Pack/Demoscene_UE5/Mesh/SKM_Manny")
    if not tgt_mesh:
        for p in eal.list_assets("/Game/NPC_Characters_Pack/Demoscene_UE5/Mesh", recursive=True):
            a = unreal.load_asset(p.split(".")[0])
            if isinstance(a, unreal.SkeletalMesh) and a.skeleton.get_path_name().startswith(SKEL): tgt_mesh = a; break
    assert tgt_mesh, "no mesh on the NPC pack's Manny skeleton"
    if eal.does_directory_exist(TD):
        for p in eal.list_assets(TD, recursive=False): eal.delete_asset(p.split(".")[0])
    names = list(J["clips"].values())
    for n in names: assert eal.does_asset_exist(SRC + n), "no " + SRC + n
    inp = unreal.IKRetargetBatchOperationInputs()
    inp.set_editor_property("assets_to_retarget", [eal.find_asset_data(SRC + n) for n in names])
    inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
    inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", "_Folk")
    inp.set_editor_property("target_path", TD); inp.set_editor_property("include_referenced_assets", False)
    inp.set_editor_property("overwrite_existing_files", True)
    unreal.IKRetargetBatchOperation.run_batch_retarget(inp)
    out = {}
    for kind, n in J["clips"].items():
        a = unreal.load_asset(f"{TD}/{n}_Folk"); assert a, n
        # (played in place: the person's actor carries it (its flight), the death lies where it fell)
        a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True)
        eal.save_loaded_asset(a, False)
        out[kind] = a
    REPORT.append("930 clips: " + ", ".join(f"{k} {v.get_name()} ({v.get_play_length():.2f} s)" for k, v in out.items()))
    return out


def defs_fn(clips):
    skel = unreal.load_asset(SKEL); assert skel
    def fn(g):
        tf = list(g.get_editor_property("townsfolk")); n = 0
        for d in tf:
            m = d.get_editor_property("mesh")
            ms = m.get_editor_property("skeleton") if m else None
            on = ms is not None and ms.get_name() == skel.get_name()
            if on and ms != skel and not any(x == skel for x in ms.get_editor_property("compatible_skeletons")):
                ms.add_compatible_skeleton(skel); eal.save_loaded_asset(ms, only_if_is_dirty=False)
            wc = d.get_editor_property("work_clips")
            for k in clips:
                if on: wc[unreal.Name(k)] = clips[k]
                elif unreal.Name(k) in wc: wc.pop(unreal.Name(k))
            d.set_editor_property("work_clips", wc)
            n += 1 if on else 0
        # (a struct read out of a list is a copy: the list written back)
        g.set_editor_property("townsfolk", tf)
        return f"Die, Hit, Run for {n} of {len(tf)} defs"
    return fn


def data_fn(g):
    g.set_editor_property("wild_folk_hurt14", True)
    g.set_editor_property("wild_folk_loot14", ["|".join(str(x) for x in row) for row in J["folk"]])
    g.set_editor_property("wild_folk_prey_cm14", float(J["prey_m"]) * 100.0)
    g.set_editor_property("wild_folk_run_speed14", float(J["run_speed"]))
    return f"{len(J['folk'])} kinds of people, prey within {J['prey_m']} m"


args = sys.argv[1:]
if "clips" in args:
    C = make_clips()
    each(J["maps"], defs_fn(C), "clips")
    C = None
if "data" in args: each(J["maps"], data_fn, "data")
for line in REPORT: print(line)
gc.collect()
