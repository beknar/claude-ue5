"""The user's list of 2026-11-08b (docs/improvements9.txt), its first phase: the quick fixes. Run with play stopped. Parts
(argv[1], default all, in this order):
  noshield the Warrior starts with no shield (StartShield emptied) on every map of the packaged game: brokenspire,
           mistward_castle, vel_morrath, war_engine, sewers (level 5 keeps its own)
  pad      every hero's gamepad list on those maps: Start opens the inventory, held half a second the Escape menu
  crops    the crop plants made in Blender (blender_numpy/wild_crops.py -> SourceArt/wilderness/crops: corn, potatoes and
           since this list oats, rye, peas, beans, flax, hemp) imported to /Game/RandomDungeon/Wild/Crops, each kind's stalk
           and leaf materials (instances of 887's bark and leaf masters: run 887 trees first). The farms' thirteen crops
           (biomes.json's crops and foliage, read by 887 data) name them
Run after it on brokenspire: 887 materials,data,level (the ground's rows read the crop / 16; the crops' table and weights;
level builds the town again and saves it).
The C++ of the list (storage stacks and holds, the gamepad's Escape menu, Backspace held, rd.TimeSpeed / rd.GameSpeed, the
crops' weights and the crop under the minimap) needs build_cpp.ps1 first.
Args: [parts]   e.g.  ue_exec.py 899_improvements9.py noshield,pad"""
import unreal, os, sys, json, gc

PARTS = (sys.argv[1] if len(sys.argv) > 1 else "noshield,pad,crops").split(",")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SA = os.path.join(REPO, "claude_ue5", "SourceArt")
MAPS = "/Game/RandomDungeon/Maps/"
MAP = MAPS + "brokenspire"
GAME_MAPS = ("brokenspire", "mistward_castle", "vel_morrath", "war_engine", "sewers")
MEL = unreal.MaterialEditingLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
WILD = "/Game/RandomDungeon/Wild"; CROPS = WILD + "/Crops"
REPORT = []


def open_map(m):
    if not ues.get_editor_world().get_path_name().startswith(m + "."): les.load_level(m)
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def each_game_map(fn, label):
    for m in GAME_MAPS:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"{label}: no map {m}"); continue
        g = open_map(MAPS + m)
        what = fn(g)
        les.save_current_level()
        unreal.SystemLibrary.execute_console_command(None, "obj gc")
        REPORT.append(f"{label} {m}: {what}")
    open_map(MAP)


# ================================================================================================ no starting shield
def noshield():
    """the list: "the warrior should have no default shield". Her block needs a shield in her hand: she blocks once she has
    found one (an armory's table, a chest, a shop)"""
    def fn(g):
        ss = dict(g.get_editor_property("start_shield"))
        had = str(ss.get(unreal.Name("Warrior"), "none"))
        ss.pop(unreal.Name("Warrior"), None)
        g.set_editor_property("start_shield", ss)
        # (her weapons also carried a shield of their own on her left forearm (OffHandMesh, Medieval Weapons' SM_Shield_1 since
        # the combat level), drawn whether she wore one or not: measured in play, she still showed a shield. Taken off her
        # weapons and the level's own list; a shield she finds is drawn as it was)
        def strip(ws):
            n = 0; out = []
            for w in ws:
                m = w.get_editor_property("off_hand_mesh")
                if m and "shield" in m.get_name().lower(): w.set_editor_property("off_hand_mesh", None); n += 1
                out.append(w)
            return out, n
        heroes = list(g.get_editor_property("heroes")); hn = 0
        for h in heroes:
            if str(h.name) != "Warrior": continue
            ws, k = strip(list(h.weapons)); h.weapons = ws; hn += k
            sw = str(h.get_editor_property("starts_with"))
            if "shield" in sw.lower(): h.set_editor_property("starts_with", "Dagger: hers for good (it never breaks, never drops); no shield until she finds one")
        g.set_editor_property("heroes", heroes)
        lw, ln = strip(list(g.get_editor_property("weapons"))); g.set_editor_property("weapons", lw)
        return f"the Warrior's start shield {had} taken away ({len(ss)} left), shield meshes off {hn} of her weapons and {ln} of the level's"
    each_game_map(fn, "noshield")


# ================================================================================================ the pad's list
def pad():
    """Start's line in every hero's gamepad list: held half a second it opens the Escape menu (the list: "the esc menu is
    inaccessible from the gamepad")"""
    def fn(g):
        heroes = list(g.get_editor_property("heroes")); n = 0
        for h in heroes:
            p = [str(k) for k in h.controls_pad]
            q = []
            for k in p:
                if k.startswith("Start|") and "held" not in k: k = k + " (held: the menu)"; n += 1
                q.append(k)
            if not any(k.startswith("Start|") for k in q): q.append("Start (held)|the menu"); n += 1
            h.controls_pad = q
        g.set_editor_property("heroes", heroes)
        return f"{n} lines in {len(heroes)} heroes"
    each_game_map(fn, "pad")


# ================================================================================================ the crops
def crops():
    src = os.path.join(SA, "wilderness", "crops")
    rec_p = os.path.join(src, "wild_crops.json")
    if not os.path.isfile(rec_p): REPORT.append(f"crops: no {rec_p} (run blender_numpy/wild_crops.py)"); return
    rec = json.load(open(rec_p, encoding="utf-8"))
    if not eal.does_directory_exist(CROPS): eal.make_directory(CROPS)
    tasks = []
    for f in sorted(os.listdir(src)):
        if not (f.endswith(".png") or f.endswith(".fbx")): continue
        tk = unreal.AssetImportTask(); tk.set_editor_property("filename", os.path.join(src, f)); tk.set_editor_property("destination_path", CROPS)
        tk.set_editor_property("replace_existing", True); tk.set_editor_property("automated", True); tk.set_editor_property("save", True)
        if f.endswith(".fbx"):
            o = unreal.FbxImportUI(); o.import_mesh = True; o.import_materials = False; o.import_textures = False; o.import_as_skeletal = False
            # (no collision: she walks through a field, as through the grass)
            o.static_mesh_import_data.combine_meshes = True; o.static_mesh_import_data.auto_generate_collision = False; o.static_mesh_import_data.generate_lightmap_u_vs = False
            tk.set_editor_property("options", o)
        tasks.append(tk)
    at.import_asset_tasks(tasks)
    bark, leaves = unreal.load_asset(f"{WILD}/M_RD_WildBark"), unreal.load_asset(f"{WILD}/M_RD_WildLeaves")
    if not bark or not leaves: REPORT.append("crops: no M_RD_WildBark / M_RD_WildLeaves (run 887 trees)"); return
    # (each kind's two textures, as wild_crops.py names them: tex_bark / tex_leaves in its record, else the old names)
    kinds = sorted({m.split("_")[2] for m in rec.get("meshes", {})})
    tex_of = rec.get("kind_textures", {})
    old = {"Corn": ("CornStalk", "CornLeaves"), "Potato": ("PotatoStem", "PotatoLeaves")}
    n = 0
    for kind in kinds:
        tb, tl = tex_of.get(kind, old.get(kind, (f"{kind}Stem", f"{kind}Leaves")))
        mis = []
        for part, parent, tex in (("Bark", bark, tb), ("Leaves", leaves, tl)):
            nm = f"MI_RD_Wild{kind}{part}"; pth = f"{CROPS}/{nm}"
            if not eal.does_asset_exist(pth): at.create_asset(nm, CROPS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
            mi = unreal.load_asset(pth); MEL.set_material_instance_parent(mi, parent)
            tx = unreal.load_asset(f"{CROPS}/{tex if tex.startswith('T_') else 'T_Wild_' + tex}")
            if tx: MEL.set_material_instance_texture_parameter_value(mi, "Tex", tx)
            else: REPORT.append(f"crops: no texture {tex} for {kind}")
            eal.save_loaded_asset(mi, only_if_is_dirty=False); mis.append(mi)
        for mesh in sorted(m for m in rec.get("meshes", {}) if m.split("_")[2] == kind):
            m = unreal.load_asset(f"{CROPS}/{mesh}")
            if not m: REPORT.append(f"crops: {mesh} not imported"); continue
            sm = list(m.get_editor_property("static_materials"))
            for i, s in enumerate(sm):
                s.set_editor_property("material_interface", mis[1] if "Leaves" in str(s.get_editor_property("material_slot_name")) else mis[0]); sm[i] = s
            m.set_editor_property("static_materials", sm)
            try: unreal.EditorStaticMeshLibrary.remove_collisions(m)
            except Exception: pass
            eal.save_loaded_asset(m, only_if_is_dirty=False); n += 1
    REPORT.append(f"crops: {n} meshes of {len(kinds)} kinds ({', '.join(kinds)}) imported with their materials")


for part in PARTS:
    part = part.strip()
    if not part: continue
    try:
        {"noshield": noshield, "pad": pad, "crops": crops}[part]()
    except Exception as e:
        import traceback
        REPORT.append(f"{part}: FAILED {e!r}"); traceback.print_exc()
print("899 " + " | ".join(REPORT))
gc.collect()
