"""The user's list of 2026-11-07 (docs/improvements8.txt, "new improvements from the graymourne build"; C++ RD/RDTown8.cpp,
RD/RDWild8.cpp and the rest named there). Run with play stopped. Parts (argv[1], default all but town, in this order):
  crops   the corn and potato plants made in Blender (blender_numpy/wild_crops.py -> SourceArt/wilderness/crops) imported to
          /Game/RandomDungeon/Wild/Crops, their stalk and leaf materials (instances of 887's bark and leaf masters: run 887
          trees first). The farms' rows (biomes.json's crops, read by 887 data) name them
  fauna   on brokenspire: the wild animals' hit points, body (the middle's height, its reach for blows and bolts), what each
          gives when killed (Coarse Hide, Light Leather, the wolf's Hound Fang) and its cries; a killed kind comes back after
          WildAnimalRespawnSeconds, its body goes after WildCorpseSeconds
  block   the Warrior's block walks only ahead or back, slowly (BlockMoveSpeed 90 cm/s, back at 0.8 of it; the stick's side
          turns her at 120 degrees a second) on every map of the packaged game: brokenspire, mistward_castle, vel_morrath,
          war_engine, sewers (level 5 keeps the third list's block)
  sky     the height fog's cutoff past every cloud (FogSkyCutoff 1000 km: at 6 km an edge ran round the zenith)
  town    brokenspire's town built again (build_start_section: the boarded windows' planks' colliders; the barracks' dummies
          are play's own now, so the saved build loses its static ones) and the level saved
Run after it on brokenspire: 887 materials,data,level (the farms' crops and the ground's rows; level builds the town again and
saves it), 890 sky (the rain's streaks), then 898 town (or 887 level last): the saved town must be built again, or it keeps the
barracks' static dummies under play's own and no colliders on the boarded windows' planks (PR #27's review).
Args: [parts]   e.g.  ue_exec.py 898_improvements8.py crops,fauna,block,town"""
import unreal, os, sys, json, gc

PARTS = (sys.argv[1] if len(sys.argv) > 1 else "crops,fauna,block,sky").split(",")
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SA = os.path.join(REPO, "claude_ue5", "SourceArt")
MAPS = "/Game/RandomDungeon/Maps/"
MAP = MAPS + "brokenspire"
MEL = unreal.MaterialEditingLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
WILD = "/Game/RandomDungeon/Wild"; CROPS = WILD + "/Crops"
REPORT = []


def open_map(m):
    if not ues.get_editor_world().get_path_name().startswith(m + "."): les.load_level(m)
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


# ================================================================================================ the crops
def crops():
    src = os.path.join(SA, "wilderness", "crops")
    if not os.path.isdir(src): REPORT.append(f"crops: none in {src} (run blender_numpy/wild_crops.py)"); return
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
    n = 0
    for kind, stalk_t in (("Corn", "CornStalk"), ("Potato", "PotatoStem")):
        mis = []
        for part, parent, tex in (("Bark", bark, stalk_t), ("Leaves", leaves, f"{kind}Leaves")):
            nm = f"MI_RD_Wild{kind}{part}"; pth = f"{CROPS}/{nm}"
            if not eal.does_asset_exist(pth): at.create_asset(nm, CROPS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
            mi = unreal.load_asset(pth); MEL.set_material_instance_parent(mi, parent)
            tx = unreal.load_asset(f"{CROPS}/T_Wild_{tex}")
            if tx: MEL.set_material_instance_texture_parameter_value(mi, "Tex", tx)
            else: REPORT.append(f"crops: no T_Wild_{tex}")
            eal.save_loaded_asset(mi, only_if_is_dirty=False); mis.append(mi)
        for v in ("A", "B"):
            m = unreal.load_asset(f"{CROPS}/SM_Wild_{kind}_{v}")
            if not m: REPORT.append(f"crops: SM_Wild_{kind}_{v} not imported"); continue
            sm = list(m.get_editor_property("static_materials"))
            for i, s in enumerate(sm):
                s.set_editor_property("material_interface", mis[1] if "Leaves" in str(s.get_editor_property("material_slot_name")) else mis[0]); sm[i] = s
            m.set_editor_property("static_materials", sm)
            # (no collision at all on a crop: a field is walked through)
            try: unreal.EditorStaticMeshLibrary.remove_collisions(m)
            except Exception: pass
            eal.save_loaded_asset(m, only_if_is_dirty=False); n += 1
    REPORT.append(f"crops: {n} meshes imported with their materials")


# ================================================================================================ the animals
FAUNA = {
    # name: hit points, body's middle (cm over its feet), reach (cm), drops (each kind's first always: a kill gives something), hurt, death
    "Deer": (40.0, 100.0, 55.0, ["Coarse Hide|1|2|1.0", "Light Leather|1|1|0.6"], "", ""),
    "Wolf": (55.0, 55.0, 45.0, ["Coarse Hide|1|2|1.0", "Hound Fang|1|1|0.6"], "Monster.Dog.Hurt", "Monster.Dog.Death"),
    "Squirrel": (6.0, 12.0, 18.0, ["Light Leather|1|1|1.0"], "", ""),
    "Hare": (10.0, 18.0, 22.0, ["Light Leather|1|1|1.0", "Coarse Hide|1|1|0.3"], "", ""),
}


def fauna():
    g = open_map(MAP)
    items = {str(i.name) for i in g.get_editor_property("items")}
    sounds = {str(k) for k in g.get_editor_property("sounds").keys()}
    out = []
    for F in g.get_editor_property("wild_fauna"):
        nm = str(F.name)
        if nm in FAUNA:
            hp, bz, br, drops, hurt, death = FAUNA[nm]
            ok = [d for d in drops if d.split("|")[0] in items]
            for d in drops:
                if d not in ok: REPORT.append(f"fauna {nm}: no item {d.split('|')[0]} on the level")
            F.set_editor_property("health", hp); F.set_editor_property("body_z", bz); F.set_editor_property("body_radius", br)
            F.set_editor_property("drops", ok)
            F.set_editor_property("hurt_sound", unreal.Name(hurt if hurt in sounds else "None"))
            F.set_editor_property("death_sound", unreal.Name(death if death in sounds else "None"))
            REPORT.append(f"fauna {nm}: {hp:.0f} hp, gives {', '.join(ok) or 'nothing'}")
        out.append(F)
    g.set_editor_property("wild_fauna", out)
    g.set_editor_property("wild_animal_respawn_seconds", 120.0); g.set_editor_property("wild_corpse_seconds", 90.0)
    les.save_current_level()


# ================================================================================================ the block
def block():
    for m in ("brokenspire", "mistward_castle", "vel_morrath", "war_engine", "sewers"):
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"block: no map {m}"); continue
        g = open_map(MAPS + m)
        g.set_editor_property("block_move_speed", 90.0); g.set_editor_property("block_back_share", 0.8); g.set_editor_property("block_turn_rate", 120.0)
        les.save_current_level()
        unreal.SystemLibrary.execute_console_command(None, "obj gc")
        REPORT.append(f"block: {m}")
    open_map(MAP)


# ================================================================================================ the sky
def sky():
    """the height fog's cutoff past every cloud (1000 km): at 6 km the clouds overhead were fogged and those lower in the sky
    were not, an edge round the zenith (888 sky8)"""
    g = open_map(MAP)
    g.set_editor_property("fog_sky_cutoff", 1.0e8)
    les.save_current_level()
    REPORT.append("sky: the fog's cutoff 1000 km")


# ================================================================================================ the town
def town():
    g = open_map(MAP)
    g.build_start_section()
    les.save_current_level()
    REPORT.append("Brokenspire built again, level saved")


for part in PARTS:
    part = part.strip()
    if not part: continue
    try:
        {"crops": crops, "fauna": fauna, "block": block, "sky": sky, "town": town}[part]()
    except Exception as e:
        import traceback
        REPORT.append(f"{part}: FAILED {e!r}"); traceback.print_exc()
print("898 " + " | ".join(REPORT))
gc.collect()
