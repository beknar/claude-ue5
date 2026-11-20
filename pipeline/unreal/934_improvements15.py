"""The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), in phases.

Parts (args):
  allies          the second phase (items 2, 3, 9, 30; C++ RD/RDList15.cpp): on every map the Summoner plays (the castle, the
                  dungeons copied from it and brokenspire), her allies solid to her and stepping aside (bAllySolid15,
                  bAllyYield15), the arena gathering them (bArenaAllies15, the maps with arenas), her summons answering in the wilds
                  (bWildSummons15, brokenspire). Off everywhere else (level 5's raised dead, the older levels: PR #94's review).
  summons         the third phase (item 18): each summoning's kinds (FRDSpellDef::SummonKinds) on every map she plays: its own kind
                  first, then four more of the same dungeon's table (the castle's, The War Engine's, the sewers', the tower's,
                  the fortress's: SourceArt/<dungeon>/monsters.json) nearest its tier (its own tier first; stronger first; never the
                  final boss), each one this map has with its mesh. Writes what it chose to SourceArt/balance/summons15.json.
  hands           the third phase (item 13): the Summoner's bare hands ("Bare Hands", bUnarmed15: no mesh, its attack refused) at
                  the end of her weapons on every map she plays.
  quick           the third phase (item 14): a scroll her hero can read goes on the quick bar (bQuickScrolls15) on every map of the
                  game and martial_arts.
  shelves <dir>   the fourth phase (item 7): the Gothic bookshelf (SM_Prop_Cabinet_D) exported to <dir>, its back panel cut into two
                  door leaves by blender_numpy/shelf_doors15.py, imported to /Game/RandomDungeon/List15 (the cabinet's material);
                  on every map of the game the Bookshelf, Bookshelf2 and Pew pieces turned round as 770 writes them now (their
                  Adjust had put the cabinet's back panel and the pew's backrest to the front) and the leaves, their hinges and
                  bShelfDoors15 set.
  dungeon         the fourth phase (items 5, 6, 8, 11): the great hall's oven (bStartOven15), the stations' marks (bStationMarks15),
                  the big map's zoom (bMapZoom15) on every map of the game (the pews by 770's Pew and the shelves part); each
                  dungeon map's start section built again (its oven and its shelves saved).
"""
import gc, json, os, sys
import unreal

eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
REPORT = []
MAPS = "/Game/RandomDungeon/Maps/"
# (the maps of the game the Summoner plays: martial_arts is the Martial Artist's alone)
GAME_MAPS = ("brokenspire", "mistward_castle", "vel_morrath", "war_engine", "sewers", "kethrys_spire", "heaven_fortress")
PARTS = ("allies", "summons", "hands", "quick", "shelves", "dungeon")
args = [a for a in sys.argv[1:] if a in PARTS] or [p for p in PARTS if p != "shelves"]          # (shelves needs its folder: named only)
SA = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "SourceArt")
DUNGEONS = ("war_engine", "sewers", "kethrys_spire", "heaven_fortress")
FAMILY = {}
for d in DUNGEONS:
    for m in json.load(open(os.path.join(SA, d, "monsters.json"), encoding="utf-8"))["monsters"]: FAMILY[m["name"]] = d
CHOSEN = {}


def open_map(m):
    path = MAPS + m
    if not ues.get_editor_world().get_path_name().startswith(path + "."):
        les.load_level(path); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    w = ues.get_editor_world(); assert w.get_path_name().startswith(path + "."), w.get_path_name()
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def each(maps, fn, label):
    for m in maps:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"{label}: no map {m}"); continue
        g = open_map(m)
        what = fn(g, m)
        g.modify(); les.save_current_level()
        # (the generator let go before the next map loads: one left in a variable made a load fatal (PR #78's review))
        g = None; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        REPORT.append(f"934 {label} {m}: {what}")


def allies(g, m):
    sets = {"ally_solid15": True, "ally_yield15": True, "arena_allies15": True, "wild_summons15": m == "brokenspire"}
    for k, v in sets.items(): g.set_editor_property(k, v)
    return {k: g.get_editor_property(k) for k in sets}


def summons(g, m):
    """each summoning's five kinds on this map (see the docstring)"""
    fb = str(g.get_editor_property("final_boss_kind"))
    mons = [d for d in g.get_editor_property("monsters") if d.get_editor_property("mesh")]
    tier = {str(d.name): d.tier for d in mons}
    sp = list(g.get_editor_property("spells")); out = {}
    # (a kind is offered by one summoning only: every summoning's own kind is taken first, then each one's four as they are chosen
    # (PR #95's review: Summon Tier 6 and 7, both of The War Engine's tier 3, offered the same five))
    used = {str(s.summon_kind) for s in sp if s.kind == unreal.RDSpellKind.SUMMON}
    for i, s in enumerate(sp):
        if s.kind != unreal.RDSpellKind.SUMMON: continue
        k0 = str(s.summon_kind)
        if k0 not in tier: out[str(s.name)] = f"no {k0} here"; continue
        fam = FAMILY.get(k0, "castle"); t0 = tier[k0]
        cand = [d for d in mons if FAMILY.get(str(d.name), "castle") == fam and str(d.name) != fb and str(d.name) not in used]
        cand.sort(key=lambda d: (abs(d.tier - t0), -d.get_editor_property("health_factor"), str(d.name)))
        kinds = [k0] + [str(d.name) for d in cand[:4]]
        used.update(kinds)
        s.set_editor_property("summon_kinds", [unreal.Name(k) for k in kinds]); sp[i] = s
        out[str(s.name)] = kinds
    g.set_editor_property("spells", sp)
    # (read back from the level: a struct out of a list is a copy)
    back = {str(s.name): [str(k) for k in s.get_editor_property("summon_kinds")] for s in g.get_editor_property("spells") if s.kind == unreal.RDSpellKind.SUMMON}
    assert all(back.get(k) == v for k, v in out.items() if isinstance(v, list)), "summon kinds not written"
    CHOSEN[m] = out
    return {k: (len(v) if isinstance(v, list) else v) for k, v in out.items()}


def hands(g, m):
    """her bare hands at the end of the Summoner's weapons (once)"""
    hs = list(g.get_editor_property("heroes"))
    i = next((k for k, h in enumerate(hs) if str(h.name) == "Summoner"), None)
    if i is None: return "no Summoner"
    h = hs[i]; ws = list(h.get_editor_property("weapons"))
    if not any(w.get_editor_property("unarmed15") for w in ws):
        w = unreal.RDWeaponDef(); w.set_editor_property("name", "Bare Hands"); w.set_editor_property("unarmed15", True)
        ws.append(w); h.set_editor_property("weapons", ws); hs[i] = h; g.set_editor_property("heroes", hs)
    h2 = next(h for h in g.get_editor_property("heroes") if str(h.name) == "Summoner")
    return [str(w.name) for w in h2.get_editor_property("weapons")]


def quick(g, m):
    g.set_editor_property("quick_scrolls15", True)
    return g.get_editor_property("quick_scrolls15")


L15 = "/Game/RandomDungeon/List15"
CAB = "/Game/Gothic_Props/Assets/Meshes/SM_Prop_Cabinet_D"
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
SHELF = {}


def shelves_make(work):
    """the cabinet out, the two leaves made by Blender for the Bookshelf piece's Adjust as turned (read from the castle's table:
    PR #96's review, it was written into the script), in again (their size measured against the script's)"""
    import subprocess
    os.makedirs(work, exist_ok=True)
    t = unreal.AssetExportTask(); t.object = unreal.load_asset(CAB); t.filename = os.path.join(work, "cabinet_d.fbx")
    t.automated = True; t.replace_identical = True; t.prompt = False; t.exporter = unreal.StaticMeshExporterFBX()
    assert unreal.Exporter.run_asset_export_task(t), "the cabinet's export failed"
    out = os.path.join(work, "doors")
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "blender_numpy", "shelf_doors15.py")
    g = open_map("mistward_castle"); a = g.get_editor_property("pieces")[unreal.Name("Bookshelf")].get_editor_property("adjust")
    ax, ay = (a.translation.x, a.translation.y) if a.rotation.z < -0.5 else (-a.translation.x, -a.translation.y)
    g = None; gc.collect()
    r = subprocess.run([BLENDER, "-b", "-P", script, "--", t.filename, out, f"{ax:.4f}", f"{ay:.4f}"], capture_output=True, text=True, timeout=600)
    assert "SHELF15 done" in r.stdout, r.stdout[-2000:] + r.stderr[-2000:]
    rec = json.load(open(os.path.join(out, "shelf_doors15.json"), encoding="utf-8"))
    tasks = []
    for side in ("L", "R"):
        o = unreal.FbxImportUI(); o.import_mesh = True; o.import_materials = False; o.import_textures = False; o.import_as_skeletal = False
        o.static_mesh_import_data.combine_meshes = True; o.static_mesh_import_data.auto_generate_collision = False
        tk = unreal.AssetImportTask(); tk.filename = os.path.join(out, f"SM_RD_ShelfDoor{side}15.fbx"); tk.destination_path = L15
        tk.replace_existing = True; tk.automated = True; tk.save = True; tk.options = o; tasks.append(tk)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    mat = unreal.load_asset(CAB).get_material(0)
    for side in ("L", "R"):
        m = unreal.load_asset(f"{L15}/SM_RD_ShelfDoor{side}15"); assert m, f"no leaf {side}"
        m.set_material(0, mat); unreal.EditorAssetLibrary.save_loaded_asset(m, False)
        b = m.get_bounding_box(); want = rec[side]["box"]
        got = [[round(b.min.x, 1), round(b.min.y, 1), round(b.min.z, 1)], [round(b.max.x, 1), round(b.max.y, 1), round(b.max.z, 1)]]
        assert all(abs(got[i][k] - want[i][k]) < 1.0 for i in range(2) for k in range(3)), f"leaf {side} came in as {got}, made as {want}"
        SHELF[side] = m
    SHELF["hinge"] = unreal.Vector2D(rec["L"]["hinge"][0], abs(rec["L"]["hinge"][1]))
    REPORT.append(f"934 shelves: leaves {rec['L']['box']} / {rec['R']['box']}, hinge {rec['L']['hinge']}")


def shelves(g, m):
    pcs = g.get_editor_property("pieces"); turned = []
    # (the saved maps' pieces as 770 writes them now (front "+y": PR #96's review fixed them at their source): the old "-y" Adjust's
    # +90 sent the cabinet's open front and the pew's seat to -X; turned once, by half a turn)
    for n in ("Bookshelf", "Bookshelf2", "Pew"):
        p = pcs.get(unreal.Name(n))
        if not p: continue
        a = p.get_editor_property("adjust")
        if a.rotation.z > 0.5:
            a.rotation = unreal.Quat(0.0, 0.0, -0.70710678, 0.70710678)
            a.translation = unreal.Vector(-a.translation.x, -a.translation.y, a.translation.z)
            p.set_editor_property("adjust", a); pcs[unreal.Name(n)] = p; turned.append(n)
    g.set_editor_property("pieces", pcs)
    g.set_editor_property("shelf_door_l15", SHELF["L"]); g.set_editor_property("shelf_door_r15", SHELF["R"])
    g.set_editor_property("shelf_door_hinge15", SHELF["hinge"]); g.set_editor_property("shelf_doors15", True)
    back = g.get_editor_property("pieces").get(unreal.Name("Bookshelf"))
    return {"turned": turned, "adjust": str(back.get_editor_property("adjust").rotation) if back else None}


def dungeon(g, m):
    for k in ("start_oven15", "station_marks15", "map_zoom15"): g.set_editor_property(k, True)
    has_oven = g.get_editor_property("pieces").get(unreal.Name("BreadOven")) is not None
    town = bool(g.get_editor_property("town"))
    if not town: g.modify(); g.build_start_section()
    return {"oven_piece": has_oven, "dungeon_ovens": g.get_editor_property("dungeon_ovens"), "start_built": not town}


if "allies" in args: each(GAME_MAPS, allies, "allies")
if "summons" in args:
    each(GAME_MAPS, summons, "summons")
    json.dump(CHOSEN, open(os.path.join(SA, "balance", "summons15.json"), "w", encoding="utf-8"), indent=1)
if "hands" in args: each(GAME_MAPS, hands, "hands")
if "quick" in args: each(GAME_MAPS + ("martial_arts",), quick, "quick")
if "shelves" in args:
    work = next((a for a in sys.argv[1:] if os.path.isabs(a)), None)
    assert work, "934 shelves <work dir>: an absolute folder for the cabinet's export and the leaves"
    shelves_make(work)
    each(GAME_MAPS, shelves, "shelves")
# (after shelves: the start sections built again with the turned shelves and their doors)
if "dungeon" in args: each(GAME_MAPS, dungeon, "dungeon")
print("\n".join(REPORT))
del eal, eas, les, ues
gc.collect()
