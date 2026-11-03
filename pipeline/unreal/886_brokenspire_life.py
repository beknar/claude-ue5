"""Brokenspire after the user's third list (2026-11-02): the town's life, the hour-long day, falls that hurt, the Warrior's
dagger in her palm. Run after 882 (which writes the town's pieces and townsfolk anew) and 885.
- brokenspire: the day lasts an hour (DayLengthSeconds 3600); falls hurt (bFallDamage; mistward_castle too)
- the farm animals (pipeline/blender_numpy/farm_animals.py, SourceArt/brokenspire/farm_animals: SK_Farm_<Animal>.fbx with
  its Idle, Graze and Walk takes, _B / _C other colourings on the same skeleton) imported into /Game/RandomDungeon/Town/Animals
  and written as the generator's TownAnimals (their walk speed and size from farm_animals.json; the pens take them in turn)
- the townsfolk's work clips (pipeline/blender_numpy/town_work_clips.py, SourceArt/brokenspire/work_clips: Stir, Crank, Tend,
  Scatter, SitDrink, SitTalk, CarryWalk, CarryIdle, Talk on the UE5 mannequin of the NPC packs) imported onto the
  NPC_Characters_Pack's skeleton; the other packs' mannequins made compatible with it; every townsperson on that mannequin
  given them (FRDTownsfolkDef::WorkClips); the smith (Dwarf_Pack) his pack's forge clips; the drunk (the UE4 body) the
  Drunk_Man_Animations' chair sit and talk
- what they hold (TownProps: a ladle, a tray, a mug, a bowl, a hammer) and how far from the thing worked they stand
  (TownWorkReach), from work_clips.json; the spits' rod and meat
- the Warrior's Dagger (mistward_castle and brokenspire): its grip moved into the base of her fingers and along its handle
  to the palm's middle (measured on Warrior3's reference pose: the handle lay over the middle of the palm, 6.4 cm from the
  wrist, and its middle 4 cm off the palm's toward the blade; a fist holds a grip at the fingers' base, 9.5 cm out)
- the town's start section built again and the levels saved
Args: [noimport] (the assets are there already)"""
import sys, os, json, unreal
ARGS = globals().get("ARGS", sys.argv[1:])
IMPORT = "noimport" not in ARGS
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); eal = unreal.EditorAssetLibrary
V = unreal.Vector
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\brokenspire"
TOWN = "/Game/RandomDungeon/Maps/brokenspire"; CASTLE = "/Game/RandomDungeon/Maps/mistward_castle"
DA = "/Game/RandomDungeon/Town/Animals"; DW = "/Game/RandomDungeon/Anims/Town/Work"
NPC_SKEL = "/Game/NPC_Characters_Pack/Demoscene_UE5/Mesh/SKM_Manny_Skeleton"
PACKS = ("NPC_Characters_Pack", "NPC_Kids_Pack", "NPC_Beggars_Pack", "NPC_King_And_Queen", "NPC_Old_gangster", "NPC_Sailor_custom", "NPC_Distopia")
DAGGER_SHIFT = V(3.5, -3.0, 0.0)            # (hand_r's frame: +x toward the little finger (the pommel's way), -y toward the fingers)
said = []


def open_map(m):
    if not ues.get_editor_world().get_path_name().startswith(m + "."): les.load_level(m)


def gen():
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def fbx_task(path, dest, skeleton=None, mesh=True, anims=True, materials=True):
    o = unreal.FbxImportUI()
    o.set_editor_property("import_mesh", mesh); o.set_editor_property("import_as_skeletal", True)
    o.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH if mesh else unreal.FBXImportType.FBXIT_ANIMATION)
    if skeleton: o.set_editor_property("skeleton", skeleton)
    o.set_editor_property("import_animations", anims)
    o.set_editor_property("import_materials", materials); o.set_editor_property("import_textures", False)
    t = unreal.AssetImportTask(); t.filename = path; t.destination_path = dest
    t.automated = True; t.replace_existing = True; t.save = True; t.options = o
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    return [unreal.load_asset(p) for p in t.imported_object_paths]


def take_name(a):
    """an imported take's name: the FBX's "Armature|Idle" comes out as ..._Idle"""
    return a.get_name().split("_")[-1]


# ---------------------------------------------------------------- the farm animals
FJ = json.load(open(os.path.join(SA, "farm_animals", "farm_animals.json"), encoding="utf-8"))
PEN = {"Chicken": (5, 8), "Rabbit": (4, 6), "Goat": (3, 4), "Pig": (2, 3), "Cow": (2, 3)}
animals = []
for name in ("Chicken", "Pig", "Goat", "Cow", "Rabbit"):
    d = f"{DA}/{name}"
    fbx = os.path.join(SA, "farm_animals", f"SK_Farm_{name}.fbx")
    # (imported when its folder has no mesh yet, or with "reanimals": its clips deleted before its meshes and skeleton (deleted
    # the other way round in a session that had them loaded, the clips lost their skeleton and the import failed))
    have = eal.does_directory_exist(d) and any(isinstance(unreal.load_asset(p.split(".")[0]), unreal.SkeletalMesh) for p in eal.list_assets(d, recursive=True))
    if IMPORT and os.path.exists(fbx) and (not have or "reanimals" in ARGS):
        if eal.does_directory_exist(d):
            ps = [p.split(".")[0] for p in eal.list_assets(d, recursive=True)]
            order = lambda p: 0 if isinstance(unreal.load_asset(p), unreal.AnimSequence) else 1 if isinstance(unreal.load_asset(p), unreal.SkeletalMesh) else 2
            for p in sorted(ps, key=order): eal.delete_asset(p)
        got = fbx_task(fbx, d)
        sk = next((a for a in got if isinstance(a, unreal.SkeletalMesh)), None)
        # (the other colourings: meshes on the same skeleton)
        for var in ("B", "C"):
            f2 = os.path.join(SA, "farm_animals", f"SK_Farm_{name}_{var}.fbx")
            if sk and os.path.exists(f2): fbx_task(f2, d, skeleton=sk.get_editor_property("skeleton"), anims=False)
    assets = [unreal.load_asset(p.split(".")[0]) for p in eal.list_assets(d, recursive=True)] if eal.does_directory_exist(d) else []
    meshes = sorted([a for a in assets if isinstance(a, unreal.SkeletalMesh)], key=lambda a: a.get_name())
    seqs = {take_name(a): a for a in assets if isinstance(a, unreal.AnimSequence)}
    if not meshes or "Idle" not in seqs:
        said.append(f"{name}: not imported ({[a.get_name() for a in assets]})"); continue
    # (Interchange takes Blender's 30 fps FBX at its own rate: each clip plays at the length Blender built it to)
    J = FJ[name]
    for k, a in seqs.items():
        L = float(J["clips"].get(k, {}).get("length_s", a.get_play_length()))
        if L > 0 and abs(a.get_play_length() - L) > 0.02:
            a.set_editor_property("rate_scale", a.get_play_length() / L); eal.save_loaded_asset(a, only_if_is_dirty=False)
    sz = J["size_cm"]
    for m in meshes:
        ad = unreal.RDTownAnimalDef()
        ad.set_editor_property("name", f"{name}{'' if m == meshes[0] else '_' + m.get_name().split('_')[-1]}")
        ad.set_editor_property("mesh", m); ad.set_editor_property("idle", seqs.get("Idle")); ad.set_editor_property("graze", seqs.get("Graze", seqs.get("Idle")))
        ad.set_editor_property("walk", seqs.get("Walk", seqs.get("Idle")))
        ad.set_editor_property("walk_speed", float(J.get("walk_speed_cm_s", 40.0))); ad.set_editor_property("scale", 1.0); ad.set_editor_property("mesh_yaw", 0.0)
        ad.set_editor_property("half_size", unreal.Vector2D(sz["length_x"] * 0.5, sz["width_y"] * 0.5))
        ad.set_editor_property("pen_min", PEN[name][0]); ad.set_editor_property("pen_max", PEN[name][1])
        animals.append(ad)
    said.append(f"{name}: {len(meshes)} colourings, clips {sorted(seqs)}, {J.get('walk_speed_cm_s')} cm/s")
# (the pens take the kinds in turn: the first colouring of each first, then the others)
animals.sort(key=lambda a: ("_" in str(a.get_editor_property("name")), ["Chicken", "Pig", "Goat", "Cow", "Rabbit"].index(str(a.get_editor_property("name")).split("_")[0])))

# ---------------------------------------------------------------- the work clips
WJ_PATH = os.path.join(SA, "work_clips", "work_clips.json")
WJ = json.load(open(WJ_PATH, encoding="utf-8")) if os.path.exists(WJ_PATH) else None
work = {}
npc_skel = unreal.load_asset(NPC_SKEL)
if WJ and npc_skel:
    if IMPORT:
        fbx = os.path.join(SA, "work_clips", WJ.get("fbx", "SK_Town_Work_Clips.fbx"))
        if eal.does_directory_exist(DW):
            for p in eal.list_assets(DW, recursive=True): eal.delete_asset(p.split(".")[0])
        got = fbx_task(fbx, DW + "/_Import", skeleton=npc_skel, mesh=False, anims=True, materials=False)
        for a in got:
            if isinstance(a, unreal.AnimSequence):
                dst = f"{DW}/AS_Town_{take_name(a)}"
                if eal.does_asset_exist(dst): eal.delete_asset(dst)
                eal.rename_asset(a.get_path_name().split(".")[0], dst)
        for p in eal.list_assets(DW + "/_Import", recursive=True): eal.delete_asset(p.split(".")[0])
        if eal.does_directory_exist(DW + "/_Import"): eal.delete_directory(DW + "/_Import")
    for k in WJ["clips"]:
        a = unreal.load_asset(f"{DW}/AS_Town_{k}")
        if not a: continue
        L = float(WJ["clips"][k].get("length_s", a.get_play_length()))
        if L > 0 and abs(a.get_play_length() - L) > 0.02:
            a.set_editor_property("rate_scale", a.get_play_length() / L)
        # (the carry walk plays as the walk does: its root held)
        if k == "CarryWalk": a.set_editor_property("force_root_lock", True); a.set_editor_property("enable_root_motion", False)
        eal.save_loaded_asset(a, only_if_is_dirty=False)
        work[k] = a
    # (every NPC pack's mannequin takes the clips: the same bones)
    for pk in PACKS:
        s = unreal.load_asset(f"/Game/{pk}/Demoscene_UE5/Mesh/SKM_Manny_Skeleton")
        if not s or s == npc_skel: continue
        have = [str(x.get_path_name()) for x in s.get_editor_property("compatible_skeletons")]
        if npc_skel.get_path_name() not in have:
            s.add_compatible_skeleton(npc_skel); eal.save_loaded_asset(s, only_if_is_dirty=False)
        have2 = [str(x.get_path_name()) for x in npc_skel.get_editor_property("compatible_skeletons")]
        if s.get_path_name() not in have2:
            npc_skel.add_compatible_skeleton(s); eal.save_loaded_asset(npc_skel, only_if_is_dirty=False)
    said.append(f"work clips: {sorted(work)}")
else:
    said.append("work clips: none yet (work_clips.json missing)")
SMITH = {"Hammer": "/Game/Dwarf_Pack/Animations/5Forge/Anim_Forge_A_Sword_Hit", "Forge": "/Game/Dwarf_Pack/Animations/5Forge/Anim_Forge_A_Sword_Idle",
         "Talk": "/Game/Dwarf_Pack/Animations/2Without_Weapon/Anim_Idle_Without_Weapon"}
DRUNK = {"SitDrink": "/Game/Drunk_Man_Animations/Animations/Anim_Drunk_Chair_Sit_Idle", "SitTalk": "/Game/Drunk_Man_Animations/Animations/Anim_Drunk_Chair_Sit_Idle_02",
         "Talk": "/Game/Drunk_Man_Animations/Animations/Anim_Drunk_Man_Talk"}

# ---------------------------------------------------------------- what they hold, how far they stand
BASIC = "/Engine/BasicShapes/Cylinder"
WOOD = unreal.load_asset("/Game/HouseForge_01/Materials/Wood/MI_Wood_Burnt")
def prop(mesh, bone, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
    p = unreal.RDTownProp(); p.set_editor_property("mesh", unreal.load_asset(mesh)); p.set_editor_property("bone", bone)
    p.set_editor_property("grip", unreal.Transform(V(*loc), unreal.Rotator(roll=rot[0], pitch=rot[1], yaw=rot[2]), V(*scale)))
    return p
ML = unreal.MathLibrary
def socket_prop(mesh, clip, key, along=0.0, scale=(1, 1, 1)):
    """a prop on the clip's socket (work_clips.json: its bone, its origin and X and Z axes in that bone's frame, Z the prop's
    axis), its own origin `along` cm along that axis from the socket's"""
    s = ((WJ or {}).get("clips", {}).get(clip, {}) or {}).get(key)
    if not s: return None
    x = V(*s["x_axis_ue"]); z = V(*s["z_axis_ue"])
    p = unreal.RDTownProp(); p.set_editor_property("mesh", unreal.load_asset(mesh)); p.set_editor_property("bone", s["bone"])
    p.set_editor_property("grip", unreal.Transform(V(*s["location_ue"]) + z * along, ML.make_rot_from_zx(z, x), V(*scale)))
    return p
props = {}
if WJ:
    st = WJ["clips"]["Stir"]
    # (the ladle: the engine's cylinder (100 cm along its Z round its middle) 84 cm long, from 15 cm above the right fist to its
    # tip 68.8 cm down the shaft, 3.4 cm thick)
    props["Ladle"] = socket_prop(BASIC, "Stir", "socket_ladle_hand_r", (float(st["ladle_tip_from_grip_cm"]) - 15.0) * 0.5, (0.034, 0.034, (float(st["ladle_tip_from_grip_cm"]) + 15.0) / 100.0))
    # (the tray: Medieval Docks' plate (28 cm, its origin its bottom's middle) made 45 cm; the mug the furniture kit's tankard
    # (13 cm tall, origin at its bottom) its middle on the socket; the bowl the kit's (18 cm) made 23)
    props["Tray"] = socket_prop("/Game/Hivemind/Medieval_Docks/Static_Meshes/Props/SM_Plate_01", "CarryIdle", "socket_tray_hand_r", 0.0, (1.6, 1.6, 1.6))
    props["Mug"] = socket_prop("/Game/Castle/Furniture/Kit/SM_Kit_Tankard", "SitDrink", "socket_mug_hand_r", -6.5)
    props["Bowl"] = socket_prop("/Game/Castle/Furniture/Kit/SM_Kit_Bowl", "Scatter", "socket_bowl_hand_l", -2.0, (1.3, 1.3, 1.3))
props = {k: v for k, v in props.items() if v}
props["Hammer"] = prop("/Game/HouseForge_01/Viking_Village_Props/Meshes/Props/ToolKit/SM_ToolHammer_01a", "hand_r", (0, 0, 0), (0, 0, 90))
# (how far her feet stand from the thing worked, from the clips: the pot's middle 66.9 cm before her; the crank's circle 40 cm
# before her (and 17 to her right: the plan's); the soil her fingers touch 33.7 cm before her; the stool's middle 2.7 cm
# before her root (negative: toward the stool from the table's side); the tray 35 cm before her (85 from the table's middle))
reach = {"Stir": 70.0, "Crank": 40.0, "Tend": 45.0, "Scatter": 70.0, "SitDrink": 0.0, "CarryIdle": 85.0, "Hammer": 85.0}
if WJ:
    c_ = WJ["clips"]
    reach["Stir"] = float(c_["Stir"]["pot_middle_root"]["her"][1])
    reach["Crank"] = float(c_["Crank"]["crank_circle_root"]["centre_her"][1])
    reach["Tend"] = float(c_["Tend"]["hand_touch_root"]["her"][1])
    reach["SitDrink"] = -float(c_["SitDrink"]["seat_point_root"]["her"][1])

# ---------------------------------------------------------------- the town
open_map(TOWN)
g = gen()
g.set_editor_property("day_length_seconds", 3600.0)
g.set_editor_property("fall_damage", True)
if animals: g.set_editor_property("town_animals", animals)
g.set_editor_property("town_props", props)
g.set_editor_property("town_work_reach", reach)
g.set_editor_property("town_spit_rod", unreal.load_asset(BASIC)); g.set_editor_property("town_spit_rod_material", WOOD)
g.set_editor_property("town_spit_meat", unreal.load_asset("/Game/HouseForge_01/Viking_Village_Props/Meshes/Props/FishnMeat/SM_Meat_01b"))
g.set_editor_property("town_spit_height", float(WJ["clips"]["Crank"]["crank_circle_root"]["centre_her"][2]) if WJ else 75.0); g.set_editor_property("town_pot_height", 12.0)
defs = list(g.get_editor_property("townsfolk")); given = []
for d in defs:
    m = d.get_editor_property("mesh"); mp = m.get_path_name() if m else ""
    clips = {}
    if "/Demoscene_UE5/" in (m.get_editor_property("skeleton").get_path_name() if m else ""):
        clips = {k: v for k, v in work.items()}
    elif d.get_editor_property("role") == unreal.RDTownRole.SMITH:
        clips = {k: unreal.load_asset(v) for k, v in SMITH.items()}
    elif d.get_editor_property("role") == unreal.RDTownRole.DRUNK:
        clips = {k: unreal.load_asset(v) for k, v in DRUNK.items()}
    clips = {unreal.Name(k): v for k, v in clips.items() if v}
    d.set_editor_property("work_clips", clips)
    if clips: given.append(f"{d.get_editor_property('name')}:{len(clips)}")
g.set_editor_property("townsfolk", defs)
said.append(f"townsfolk with work clips: {len(given)} of {len(defs)} ({', '.join(given)})")


def fix_dagger(g_):
    """the Warrior's Dagger: its grip moved by DAGGER_SHIFT in her hand's frame (the item's and her hero's start weapon), once:
    the shift is recorded in the weapon's name of record (`grip_note`) so a second run does not move it twice"""
    n = 0
    items = list(g_.get_editor_property("items"))
    for it in items:
        if str(it.get_editor_property("name")) != "Dagger": continue
        fits = list(it.get_editor_property("weapon_fits"))
        for fi in fits:
            if str(fi.hero) != "Warrior": continue
            w = fi.weapon; gr = w.grip
            if abs(gr.translation.x - (-29.578)) > 0.05: continue           # (moved already, or not the grip measured)
            w.grip = unreal.Transform(gr.translation + DAGGER_SHIFT, gr.rotation.rotator(), gr.scale3d); fi.weapon = w; n += 1
        it.set_editor_property("weapon_fits", fits)
    g_.set_editor_property("items", items)
    heroes = list(g_.get_editor_property("heroes"))
    for h in heroes:
        if str(h.name) != "Warrior": continue
        ws = list(h.weapons)
        for w in ws:
            if str(w.name) == "Dagger" and abs(w.grip.translation.x - (-29.578)) < 0.05:
                w.grip = unreal.Transform(w.grip.translation + DAGGER_SHIFT, w.grip.rotation.rotator(), w.grip.scale3d); n += 1
        h.weapons = ws
    g_.set_editor_property("heroes", heroes)
    return n
said.append(f"brokenspire: the Warrior's dagger grips moved: {fix_dagger(g)}")
g.build_start_section()
s = unreal.GameplayStatics.get_all_actors_of_class(ues.get_editor_world(), unreal.RDSection)
said.append(f"brokenspire built: {[(x.get_editor_property('num_instances'), x.get_editor_property('num_lights')) for x in s]}")
les.save_current_level()
del g, defs, s

# ---------------------------------------------------------------- the castle
open_map(CASTLE)
g = gen()
g.set_editor_property("fall_damage", True)
said.append(f"mistward_castle: falls hurt; the Warrior's dagger grips moved: {fix_dagger(g)}")
les.save_current_level()
del g
open_map(TOWN)
for l in said: print("886", l)
import gc
gc.collect()
