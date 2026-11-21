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
  items           the fifth phase (items 10, 12, 15, 16, 17, 19; SourceArt/list15/items15.json): each scroll's picture its spell's;
                  the blessed rune stone (the cursed one's look and label, weight 0) and bBlessedStones15; Player.Loot.Gear (convert
                  first: rdc_sound_prep.py SourceArt/list15/items15.json SourceArt/list15/audio_items) and bGearThud15; the ankh's
                  chests only; the torch's and the ankh's burn time and bLightBurn15; the teleporters' R3 (bPadTripButton15). Run after
                  910, 918 and 928, which write the items and spells anew.
  town            the sixth phase (items 1, 20, 21, 22) on brokenspire: a pen's animals kept apart (bPenApart15), a quest's "boss" goal
                  the castle's tiers whose boss she has slain (bBossGoalCastle15) and "The First Warden" offered from the start (its
                  after taken off, as town.json now has it), the town maps' symbols and key (bTownSymbols15), the wilds' hearths heard
                  (bWildHearthSound15).
  hearth          the sixth phase's item 22 on every map of the game: the kit fireplace's flat flame cards (slot 4) hidden in a copy
                  (SM_Kit_Fireplace15, M_RD15_Hidden in the slot) that the "Fireplace" piece points at, and Hearthvale's
                  NS_Fireplace_Low at every hearth (bHearth15, HearthFx15; screened by 884 hearthfx15: P_TorchFire drew nothing there).
  terrace         the seventh phase (items 26, 29) on brokenspire: the villages' houses and square on level pads cut into the slope,
                  their retaining walls and buttresses, 8 to 15 houses (bVillageTerraces15; the world's version 6).
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
PARTS = ("allies", "summons", "hands", "quick", "shelves", "dungeon", "items", "town", "hearth", "terrace")
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


I15 = None


def items_sounds():
    """Player.Loot.Gear's files (rdc_sound_prep.py's conversion of SourceArt/list15/items15.json) imported once"""
    aud = os.path.join(SA, "list15", "audio_items"); idx = os.path.join(aud, "index.json")
    assert os.path.exists(idx), "run rdc_sound_prep.py SourceArt/list15/items15.json SourceArt/list15/audio_items first"
    I = json.load(open(idx, encoding="utf-8")); dest = "/Game/RandomDungeon/Audio/List15"
    if not eal.does_directory_exist(dest): eal.make_directory(dest)
    at = unreal.AssetToolsHelpers.get_asset_tools(); made = {}
    for key, spec in I15["sets"].items():
        waves = []
        for f in I.get(key, {}).get("files", []):
            t = unreal.AssetImportTask(); t.set_editor_property("filename", os.path.join(aud, f)); t.set_editor_property("destination_path", dest)
            t.set_editor_property("destination_name", "SW_" + f[:-4]); t.set_editor_property("replace_existing", True); t.set_editor_property("automated", True)
            at.import_asset_tasks([t])
            w = unreal.load_asset(f"{dest}/SW_{f[:-4]}")
            if w: w.set_editor_property("looping", False); eal.save_loaded_asset(w, False); waves.append(w)
        assert waves, f"934 items: no files for {key}"
        made[key] = (waves, spec)
    return made


def items(g, m, made):
    out = {}
    # (item 15: the gear's thud)
    snd = g.get_editor_property("sounds")
    for key, (waves, spec) in made.items():
        s = unreal.RDSoundSet(); s.set_editor_property("sounds", waves)
        s.set_editor_property("volume", float(spec.get("volume", 1.0))); s.set_editor_property("pitch_variation", float(spec.get("pitch_var", 0.05)))
        s.set_editor_property("b2d", bool(spec.get("flat", False)))
        snd[unreal.Name(key)] = s
    g.set_editor_property("sounds", snd)
    # (item 10: each scroll's picture its spell's)
    sp = {str(s.name): str(s.icon) for s in g.get_editor_property("spells")}
    its = list(g.get_editor_property("items")); n_icon = 0; no_icon = []
    for i, it in enumerate(its):
        if it.kind == unreal.RDItemKind.SCROLL:
            ic = sp.get(str(it.spell), "None")
            if ic and ic != "None": it.set_editor_property("icon", unreal.Name(ic)); its[i] = it; n_icon += 1
            else: no_icon.append(str(it.name))
        # (item 17: the torch's and the ankh's burn time)
        k = str(it.kind).split(".")[-1].split(":")[0].strip("<> ").title()
        if k in ("Torch", "Light") and k in I15["light"]: it.set_editor_property("durability", float(I15["light"][k])); its[i] = it
    g.set_editor_property("items", its)
    out["scroll_icons"] = n_icon; out["scrolls_without_a_spell_icon"] = no_icon
    # (item 12: the blessed stone, the cursed one's look and label, weight 0 (never drawn with the others))
    tr = list(g.get_editor_property("traps"))
    cur = next((t for t in tr if t.kind == unreal.RDTrapKind.CURSED), None)
    tr = [t for t in tr if t.kind != unreal.RDTrapKind.BLESSED]
    if cur:
        b = unreal.RDTrapDef(); b.import_text(cur.export_text()); b.set_editor_property("kind", unreal.RDTrapKind.BLESSED); b.set_editor_property("weight", 0.0)
        tr.append(b)
    g.set_editor_property("traps", tr)
    sets = {"blessed_stones15": bool(cur), "gear_thud15": True, "ankh_chests_only15": True, "light_burn15": True, "pad_trip_button15": True}
    for k_, v_ in sets.items(): g.set_editor_property(k_, v_)
    g.set_editor_property("blessed_share15", float(I15["blessed"]["share"])); g.set_editor_property("blessed_seconds15", float(I15["blessed"]["seconds"]))
    out["blessed_def"] = bool(cur); out["gear_set"] = unreal.Name("Player.Loot.Gear") in g.get_editor_property("sounds")
    return out


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
if "items" in args:
    I15 = json.load(open(os.path.join(SA, "list15", "items15.json"), encoding="utf-8"))
    made = items_sounds()
    each(tuple(I15["maps"]), lambda g, m: items(g, m, made), "items")
def town(g, m):
    # (brokenspire alone: the castle's and the dungeons' maps hold no quests, their trackers none to draw (PR #98's review asked))
    for k_ in ("pen_apart15", "boss_goal_castle15", "town_symbols15", "wild_hearth_sound15"): g.set_editor_property(k_, True)
    qs = list(g.get_editor_property("quests")); n = 0
    for i, q in enumerate(qs):
        if str(q.get_editor_property("id")) == "captain_warden":
            # (its kills before it was taken count: the user's choice for this quest, not every boss goal (PR #98's review))
            q.set_editor_property("after", unreal.Name("None")); q.set_editor_property("goal_whole15", True); qs[i] = q; n += 1
    g.set_editor_property("quests", qs)
    w = next((q for q in g.get_editor_property("quests") if str(q.get_editor_property("id")) == "captain_warden"), None)
    whole = [str(q.get_editor_property("id")) for q in g.get_editor_property("quests") if q.get_editor_property("goal_whole15")]
    return {"warden_after": str(w.get_editor_property("after")) if w else "no quest", "changed": n, "whole": whole, "hearth_set": unreal.Name("Env.Hearth") in g.get_editor_property("sounds")}


if "town" in args: each(("brokenspire",), town, "town")


L15 = "/Game/RandomDungeon/List15"
HEARTH = {}


def hearth_assets():
    MEL = unreal.MaterialEditingLibrary
    hid = unreal.load_asset(f"{L15}/M_RD15_Hidden")
    if not hid:
        hid = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_RD15_Hidden", L15, unreal.Material, unreal.MaterialFactoryNew())
        hid.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED); hid.set_editor_property("two_sided", True)
        c = MEL.create_material_expression(hid, unreal.MaterialExpressionConstant, -300, 0); c.set_editor_property("r", 0.0)
        MEL.connect_material_property(c, "", unreal.MaterialProperty.MP_OPACITY_MASK)
        for u in ("used_with_instanced_static_meshes", "used_with_nanite"): hid.set_editor_property(u, True)
        MEL.recompile_material(hid); eal.save_loaded_asset(hid, False)
    src = unreal.load_asset("/Game/Castle/Furniture/Kit/SM_Kit_Fireplace")
    names = [str(s.material_slot_name) for s in src.static_materials]
    assert names[4] == "Flame", names          # (the kit's flame cards)
    dst = f"{L15}/SM_Kit_Fireplace15"
    m = unreal.load_asset(dst) or eal.duplicate_asset(src.get_path_name(), dst)
    mats = list(m.static_materials); s = mats[4]; s.material_interface = hid; mats[4] = s
    m.modify(); m.set_editor_property("static_materials", mats); eal.save_loaded_asset(m, False)
    m = unreal.load_asset(dst); assert m.static_materials[4].material_interface == hid, "the flame slot kept its material"
    fx = unreal.load_asset("/Game/Hearthvale/VFX/NS_Fireplace_Low"); assert fx, "no NS_Fireplace_Low"
    HEARTH.update(mesh=m, hid=hid, fx=fx)


def hearth(g, m):
    pcs = g.get_editor_property("pieces"); p = pcs.get(unreal.Name("Fireplace"))
    if p:
        p.set_editor_property("mesh", HEARTH["mesh"]); pcs[unreal.Name("Fireplace")] = p; g.set_editor_property("pieces", pcs)
    g.set_editor_property("hearth_fx15", HEARTH["fx"]); g.set_editor_property("hearth_hide_mat15", HEARTH["hid"]); g.set_editor_property("hearth15", True)
    back = g.get_editor_property("pieces").get(unreal.Name("Fireplace"))
    return {"fireplace": back.get_editor_property("mesh").get_name() if back else None, "fx": g.get_editor_property("hearth_fx15").get_name()}


def terrace(g, m):
    g.set_editor_property("village_terraces15", True)
    return {"village_terraces15": g.get_editor_property("village_terraces15")}


if "terrace" in args: each(("brokenspire",), terrace, "terrace")


if "hearth" in args:
    hearth_assets(); each(GAME_MAPS, hearth, "hearth")
# (after shelves: the start sections built again with the turned shelves and their doors)
if "dungeon" in args: each(GAME_MAPS, dungeon, "dungeon")
print("\n".join(REPORT))
del eal, eas, les, ues
gc.collect()
