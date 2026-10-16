"""random_dungeon_level (/Game/RandomDungeon/Maps/random_dungeon_level): procedural dungeon (C++ ARDDungeonGenerator,
Source/claude_ue5/RD). Packs: Dungeon Builder top-down kit (MysticDungeon: walls, doorways, floors, columns, torches,
gratings, gibbets, cages, chains, chandeliers), Modular Dungeon kits (HallowedDepths: crypt double doors, cell doors,
tombs, candles, debris; DarkHalls: brazier, pillars, plinths, bone piles), Gothic Props (pews, tables, chairs, bookshelves,
candle stands, banners, paintings, carpet), Medieval Weapons, the castle furniture kit (beds, tables, hearth, forge,
chests / trunks / wardrobes) and castle_level's openable barrels and crates; monsters from Creatures_Pack (own skeletons
and idle / walk clips).
- pieces: every mesh normalised to the dungeon frame (front +X, footprint centred, floor at z 0; see FRDPiece)
- level: no sky (lit only by its torches, braziers, candles, chandeliers), dark height fog, exposure range for torchlight
- generator at the origin + the 252 m start section built with a fixed seed (saved); PlayerStart in the great hall
- BP_RD_GameMode: BP_SFC_Fem5Character (jrpg-fem5-tripo) + RDHUD (minimap, M map, F prompt)
- reveal materials: random_level's M_RT_RevealPP / M_RT_RevealCurtain (753)
Args: [no_build] | pieces   (pieces: only rewrites the piece table in the generator of the open level, one of
      random_dungeon_level, its Cine copy, random_dungeoncombat_level or the two magic levels, builds its start section
      again and saves it)"""
import sys, json, math, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eal = unreal.EditorAssetLibrary; V = unreal.Vector
MAP = "/Game/RandomDungeon/Maps/random_dungeon_level"
TAG = unreal.Name("rd_level")
ar = unreal.AssetRegistryHelpers.get_asset_registry()
NAMES = {}
for root in ("/Game/MysticDungeon/Meshes", "/Game/HallowedDepths/Meshes", "/Game/DarkHalls/StaticMeshes", "/Game/Gothic_Props/Assets", "/Game/Castle/Furniture/Kit",
             "/Game/Castle/Interactive/Meshes", "/Game/Medieval_Weapons"):
    for ad in ar.get_assets_by_path(root, recursive=True):
        if str(ad.asset_class_path.asset_name) == "StaticMesh": NAMES.setdefault(str(ad.asset_name), str(ad.package_name))
def mesh(n):
    p = NAMES.get(n) or NAMES.get("SM_" + n)
    if not p: print("  MISSING mesh", n); return None
    return unreal.load_asset(p)
YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
def corners(b):
    return [V(x, y, z) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]
def piece(m, front="+y", mode="center", back=30.0, scale=(1, 1, 1), collision=True, hinge=None, moving=None, moving2=None, hinge2=None,
          size=None, shift=(0, 0, 0), actor=None, flip=False, pitch=0.0):
    """mesh frame -> dungeon frame. modes: center (XY centred, bottom z 0), floor (top z 0), ceil (flipped, underside z 0),
    wall (back at x = back, Y centred, bottom z 0), wallc (same, z centred), walltop (same, top z 0), raw (rotation only)"""
    if isinstance(m, str): m = unreal.load_asset(m) if m.startswith("/") else mesh(m)
    if m is None and actor is None: return None
    sc = V(*scale)
    rot = unreal.Rotator(roll=180.0 if (mode == "ceil" or flip) else 0.0, pitch=pitch, yaw=YAW[front])
    t0 = unreal.Transform(V(0, 0, 0), rot, sc)
    b = m.get_bounding_box()
    pts = [unreal.MathLibrary.transform_location(t0, c) for c in corners(b)]
    mn = V(min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)); mx = V(max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
    tx, ty = -(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2
    tz = -mn.z
    if mode == "floor": tz = -mx.z
    elif mode == "ceil": tz = -mn.z
    elif mode in ("wall", "wallc", "walltop"):
        tx = back - mn.x
        if mode == "wallc": tz = -(mn.z + mx.z) / 2
        if mode == "walltop": tz = -mx.z
    elif mode == "raw": tx = ty = tz = 0.0
    t = unreal.Transform(V(tx + shift[0], ty + shift[1], tz + shift[2]), rot, sc)
    p = unreal.RDPiece()
    p.mesh = m if actor is None else None
    if actor is not None: p.actor_class = actor
    p.adjust = t
    p.size = V(*size) if size else V(mx.x - mn.x, mx.y - mn.y, mx.z - mn.z)
    p.collision = collision
    if hinge is not None: p.hinge = unreal.MathLibrary.transform_location(t, V(*hinge))
    if hinge2 is not None: p.hinge2 = unreal.MathLibrary.transform_location(t, V(*hinge2))
    if moving is not None: p.moving = mesh(moving) if isinstance(moving, str) else moving
    if moving2 is not None: p.moving2 = mesh(moving2) if isinstance(moving2, str) else moving2
    return p
P = {}
def add(name, *a, **k):
    p = piece(*a, **k)
    if p is not None: P[name] = p
# ---------------------------------------------------------------- shell
add("Floor_Stone", "SM_Floor_Stone_Square_Tiles_A", mode="floor"); add("Floor_Stone_Alt", "SM_Floor_Stone_Square_Tiles_A_Extude", mode="floor")      # (the _DMG tiles have holes)
add("Floor_Wood", "SM_Floor_Wood_Cobble_A", mode="floor")
add("Floor_Tiles", "SM_floor_tiles_A", mode="floor"); add("Floor_Tiles_Alt", "SM_Floor_Tiles_B", mode="floor")
add("Floor_Brick", "SM_FloorRandomBrick_A", mode="floor"); add("Floor_Brick_Alt", "SM_FloorRandomBrick_C", mode="floor")
add("Floor_Brick2", "SM_Floor_Stone_Square_Tiles_B", mode="floor")
add("Floor_Random", "SM_Floor_Random_Tiles_B", mode="floor"); add("Floor_Random_Alt", "SM_FloorRandomBrick_A", mode="floor")
add("Floor_Corr", "SM_FloorRandomBrick_C", mode="floor"); add("Floor_Corr_Alt", "SM_FloorRandomBrick_A", mode="floor")
add("Ceil_Room", "SM_Floor_Stone_Square_Tiles_B", mode="ceil"); add("Ceil_Corr", "SM_FloorRandomBrick_A", mode="ceil")
add("Wall_Stone", "SM_Wall_A", front="+y"); add("Wall_Block", "SM_wall_LargeBlock_B_300", front="+y"); add("Wall_Rough", "SM_Wall_A_DMG_D", front="+y")
add("Wall_Corr", "SM_wall_LargeBlock_A", front="+y")
# Broken walls come in variants: a section gives each wall segment one of "Wall_Rough", "Wall_Rough_2", ... and never
# the one beside or under it (one broken mesh along a whole room showed the same break every 3 m). A variant is set
# so that its mesh origin (the wall's own line) lies where the first one's does: the breaks stick out of the bounding
# boxes by different amounts, and centring each on its box would leave gaps at the joints.
def wall_variant(name, m, base):
    b0 = mesh(base).get_bounding_box(); b = mesh(m).get_bounding_box()
    sh = ((b.min.y + b.max.y) / 2 - (b0.min.y + b0.max.y) / 2, (b0.min.x + b0.max.x) / 2 - (b.min.x + b.max.x) / 2, b.min.z - b0.min.z)    # (front +y: piece x = mesh y, piece y = -mesh x)
    p = piece(m, front="+y", shift=sh)
    if p is not None: p.size = P[name.rsplit("_", 1)[0]].size; P[name] = p
for i, m in enumerate(("SM_Wall_A_DMG_A", "SM_Wall_A_DMG_B", "SM_Wall_A_DMG_C", "SM_Wall_A")): wall_variant(f"Wall_Rough_{i + 2}", m, "SM_Wall_A_DMG_D")
# The broken walls have holes right through them: she saw the void behind them and the backs of the rooms beyond, and
# could climb into the bigger holes and fall out of the dungeon. Each broken segment gets (RDSection's Stack):
# - Wall_Rough_Back: a stone plate (SM_Wall_A thinned to 8 cm) from 15.5 to 23.5 cm behind the wall line: seen through a
#   hole it is the back of a cavity. The walls are centred on the tile edge (the broken ones +-33 cm, their breaks to
#   -45 cm); behind them is an empty tile, or at a section's border the next section's wall on the same line, of which
#   the thinnest (Wall_Stone) reaches 25 cm back: the plate stays inside it and is never seen from there.
# - Wall_Rough_Seal: an invisible box from 33 cm behind the line to 30 cm in front of it (the wall's face is at 33), the
#   whole segment's width and height: she cannot step or jump into a hole.
add("Wall_Rough_Back", "SM_Wall_A", front="+y", scale=(1.03, 0.16, 1.03), shift=(-19.5, 0, 0))
cb = piece("/Engine/BasicShapes/Cube", front="+x", scale=(0.63, 3.14, 3.11), shift=(-1.5, 0, 0))
if cb: cb.hidden = True; P["Wall_Rough_Seal"] = cb
add("Doorway", "SM_Wall_Entrance_A", front="+y")
add("CornerColumn", "SM_StoneCorner_SmallColumn_A")
# double crypt doors (2 x 70 cm): the leaf spans +Y from its hinge; Hinge = (inset, half opening)
dl = piece("SM_Door_Crypt_leftdoor", front="-x", mode="raw", scale=(1, 0.92, 1.0))
if dl:
    # leaf mesh: hinge at y 0, leaf toward -Y, thickness x 0..10 -> yaw 180: leaf toward +Y, thickness -10..0 -> shift +5
    dl.adjust = unreal.Transform(V(5, 0, 0), unreal.Rotator(roll=0, pitch=0, yaw=180), V(1, 0.92, 1.0)); dl.size = V(10, 70, 208); dl.hinge = V(0, 70, 0)
    P["DoorLeaf"] = dl
cd = piece("SM_Wall_Cell_Chamber_Door_Var_01", front="+y", mode="raw", scale=(0.926, 1, 1))
if cd:
    cd.adjust = unreal.Transform(V(3.5, 0, 0), unreal.Rotator(roll=0, pitch=0, yaw=-90), V(0.926, 1, 1)); cd.size = V(17, 150, 304)
    P["CellDoor"] = cd
# cell bars: their simple collision is a flat slab reaching into the room, so the bars get none and invisible
# boxes block instead (CellBlock: the whole front, CellBlockHalf: the barred half next to a cell door)
add("CellFrame", "SM_Grating_Base_A_Half", front="+y", scale=(0.943, 1, 1), shift=(0, -75, 0), collision=False)     # covers [-150, 0]; the door the other half
add("Grating", "SM_Grating_a", front="+y", collision=False)
for n, w_, sh in (("CellBlock", 3.0, 0), ("CellBlockHalf", 1.5, -75)):
    cb = piece("/Engine/BasicShapes/Cube", front="+x", scale=(0.12, w_, 3.1), shift=(0, sh, 0))
    if cb: cb.hidden = True; P[n] = cb
# ---------------------------------------------------------------- lights and effects
TORCH_SC = 1.3
add("Torch", "SM_Torch_A", front="+y", mode="wallc", back=30.0, scale=(TORCH_SC,) * 3, collision=False, hinge=(2 / TORCH_SC, 26 / TORCH_SC, 56 / TORCH_SC - 0))
add("Candles", "SM_Candle_low_001", collision=False)
add("Chandelier", "SM_Chandelier_A", collision=False)
add("Brazier", "SM_Brazier_02", scale=(1.35, 1.35, 1.35))
add("Crystal", "SM_CrystalLight_A", collision=False)
cs_bp = eal.load_blueprint_class("/Game/Gothic_Props/Assets/Blueprints/BP_Prop_CandleStand_B_Lit1")
add("CandleStand", "SM_Prop_CandleStand_B", actor=cs_bp)
# ---------------------------------------------------------------- furniture
for n, m, kw in (("Bed", "SM_Kit_BedSingle", {}), ("Stool", "SM_Kit_Stool", {}), ("TableLong", "SM_Kit_TableLong", {}), ("TableSmall", "SM_Kit_TableSmall", {}),
                 ("PrepTable", "SM_Kit_PrepTable", {}), ("ToolBoard", "SM_Kit_ToolBoard", {}), ("ShelfRack", "SM_Kit_ShelfRack", {}), ("Anvil", "SM_Kit_Anvil", {}),
                 ("Fireplace", "SM_Kit_Fireplace", {}), ("BreadOven", "SM_Kit_BreadOven", {}), ("Tripod", "SM_Kit_Tripod", {}), ("Cauldron", "SM_Kit_Cauldron", {"collision": False}),
                 ("Bench", "SM_Kit_Bench", {}), ("PotRack", "SM_Kit_PotRack", {"collision": False}), ("Forge", "SM_Kit_Forge", {}), ("QuenchTub", "SM_Kit_QuenchTub", {}),
                 ("Firewood", "SM_Kit_Firewood", {}), ("HayPile", "SM_Kit_HayPile", {})):      # (the prison cells' mound: it blocks; its mesh collides as its triangles)
    add(n, m, front="+y", **kw)
add("Pew", "SM_Prop_Bench_A", front="-y"); add("Altar", "SM_Prop_Table_A", front="-y"); add("Desk", "SM_Prop_Table_A", front="-y")
add("Chair", "SM_Prop_Chair_A", front="-y"); add("Throne", "SM_Prop_Chair_A", front="-y", scale=(1.25, 1.25, 1.25))
add("Painting", "SM_Prop_Frame_B", front="-y", mode="wallc", back=22.0, collision=False)
add("Banner", "SM_Prop_Flag_B_Torn", front="+x", mode="walltop", back=22.0, collision=False)
add("Carpet", "SM_Carpet_A", front="+x", collision=False); add("CarpetLong", "SM_Carpet_A", front="+y", collision=False)
add("Books", "SM_Prop_Bookset_A", collision=False)
bs_c = eal.load_blueprint_class("/Game/Gothic_Props/Assets/Blueprints/BP_Prop_Bookshelf_C"); bs_d = eal.load_blueprint_class("/Game/Gothic_Props/Assets/Blueprints/BP_Prop_Bookshelf_D")
add("Bookshelf", "SM_Prop_Cabinet_D", front="-y", actor=bs_c); add("Bookshelf2", "SM_Prop_Cabinet_D", front="-y", actor=bs_d)
add("Column", "SM_PillarStem_01"); add("Dais", "SM_StatuePlinth_02"); add("Pedestal", "SM_Plinth_01")
add("Gibbet", "SM_Gibbet_A"); add("CageLarge", "SM_LargeCage_A"); add("CageHanging", "SM_HangingCage_A", collision=False)
add("Chain", "SM_Chain_Line_c", collision=False); add("Shackles", "SM_RingWall_A", front="+y", mode="wallc", back=22.0, collision=False)
for i in range(1, 5): add(f"Tomb{i}", f"SM_Tomb_Crypt_Damage_Var_0{i}")
add("BonePile", "SM_Chapel_BonesAndSkillPile_Var1_SM_Chapel_BonesAndSkillPile_Var1", collision=False)
add("BonePile2", "SM_Chapel_BonesAndSkillPile_Var3_SM_Chapel_BonesAndSkillPile_Var3", collision=False)
add("Bones", "SM_Chapel_BonesAndSkillPile_Var2_SM_Chapel_BonesAndSkillPile_Var2", collision=False)
add("Debris", "SM_Debris_01", collision=False)
add("Sword", "SM_Sword_1", front="-y", mode="wall", back=24.0, collision=False); add("Spear", "SM_Spear", front="-y", mode="wall", back=24.0, collision=False)
add("Axe", "SM_Axe", front="-y", mode="wall", back=24.0, collision=False); add("Shield", "SM_Shield_1", front="-y", mode="wallc", back=24.0, collision=False)
for n, m in (("SwordFlat", "SM_Sword_1"), ("AxeFlat", "SM_Axe"), ("SpearFlat", "SM_Spear")): add(n, m, front="-y", pitch=90.0, collision=False)      # lying on a table
# ---------------------------------------------------------------- containers (all open with F)
# A moving part's mesh has its origin at its hinge, so the hinge below is where that origin goes on the body (body mesh
# frame, UE axes). Both data files are written by Blender scripts and hold Blender's y: UE's is the negative.
KH = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\castle_furniture\kit.json"))["_hinges"]
ueh = lambda h: (h[0], -h[1], h[2])
add("Chest", "SM_Kit_ChestBody", front="+y", moving="SM_Kit_ChestLid", hinge=ueh(KH["Chest"]))
add("Trunk", "SM_Kit_TrunkBody", front="+y", moving="SM_Kit_TrunkLid", hinge=ueh(KH["Trunk"]))
add("Wardrobe", "SM_Kit_WardrobeBody", front="+y", moving="SM_Kit_WardrobeDoorL", hinge=ueh(KH["WardrobeL"]),
    moving2="SM_Kit_WardrobeDoorR", hinge2=ueh(KH["WardrobeR"]))
CJ = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\castle_interactive\interactive.json"))["containers"]
for n, src in (("Barrel", "SM_barrel_01"), ("Barrel2", "SM_barrel_02"), ("Crate", "SM_crate_01"), ("Crate2", "SM_crate_02")):
    h = ueh(CJ[src]["hinge"])                                          # the hinge is at the back: the front is the other side
    front = ("-y" if h[1] > 0 else "+y") if abs(h[1]) >= abs(h[0]) else ("-x" if h[0] > 0 else "+x")
    add(n, f"{src}_body", front=front, moving=f"{src}_lid", hinge=h)
if "pieces" in sys.argv:
    # Only the piece table, in the generator of the level that is open, and its start section built again from it (same
    # seed: the same rooms and furniture). The Save As copies (the Cine copy, the combat level) carry a table and a start
    # section of their own, and their generators have settings this script knows nothing of: it must not rebuild them.
    w = ues.get_editor_world(); assert w.get_path_name().startswith("/Game/RandomDungeon/Maps/"), w.get_path_name()
    g = [a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator)][0]
    g.modify(); g.set_editor_property("pieces", P); g.build_start_section()
    sec = g.get_section(unreal.IntPoint(0, 0))
    print("pieces set in", w.get_path_name(), "|", len(P), "pieces | start section:", sec.get_num_rooms(), "rooms,", sec.get_editor_property("num_instances"), "instances, reachable rooms",
          sec.count_reachable_rooms(), "| walls", {str(k): v for k, v in sec.get_wall_piece_counts().items()}, "repeats", sec.get_wall_repeats(),
          "| broken segments backed and sealed", len(sec.get_backed_wall_segments()[0]))
    les.save_current_level()
    import gc
    for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
    gc.collect()
    raise SystemExit
print("pieces:", len(P), sorted(P))
# ---------------------------------------------------------------- effects
FX = {"TorchFire": "/Game/MysticDungeon/VFX/P_TorchFire", "CandleFire": "/Game/MysticDungeon/VFX/NS_Candle_Fire_A",
      "BrazierFire": "/Game/MysticDungeon/VFX/P_TorchFire", "HearthFire": "/Game/MysticDungeon/VFX/P_TorchFire"}      # (NS_FireFX_01 is a bonfire metres across: it engulfed the hallways)
effects = {k: unreal.load_asset(v) for k, v in FX.items()}
# ---------------------------------------------------------------- monsters (Creatures_Pack: own skeleton + idle / walk)
def clip_speed(anim):
    """ground speed of the walk clip: horizontal speed of the lowest foot while it is planted (in-place clips)"""
    try:
        opts = unreal.AnimPoseEvaluationOptions()
        L = anim.get_play_length() if hasattr(anim, "get_play_length") else anim.get_editor_property("sequence_length")
        p0 = unreal.AnimPoseExtensions.get_anim_pose_at_time(anim, 0.0, opts)
        feet = [b for b in unreal.AnimPoseExtensions.get_bone_names(p0) if "foot" in str(b).lower() or "toe" in str(b).lower()]
        if not feet: return None
        n = 60; speeds = []
        for f in feet:
            pts = []
            for i in range(n + 1):
                pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(anim, L * i / n, opts)
                tr = unreal.AnimPoseExtensions.get_bone_pose(pose, f, unreal.AnimPoseSpaces.WORLD)
                pts.append(tr.translation)
            zmin = min(p.z for p in pts)
            for i in range(n):
                if pts[i].z < zmin + 4 and pts[i + 1].z < zmin + 4:
                    speeds.append(math.hypot(pts[i + 1].x - pts[i].x, pts[i + 1].y - pts[i].y) / (L / n))
        speeds = sorted(s for s in speeds if s > 5)
        return speeds[len(speeds) // 2] if speeds else None
    except Exception as e:
        print("   clip speed failed:", e); return None
MON = []
for name, weight in (("Troll", 1.0), ("Daemon", 1.0), ("Horned", 0.8), ("Ripper_dog", 1.0), ("Spider", 0.7), ("Mutant", 0.8)):
    sk = unreal.load_asset(f"/Game/Creatures_Pack/Mesh/SK_{name}")
    anims = {}
    for ad in ar.get_assets_by_path("/Game/Creatures_Pack", recursive=True):
        if str(ad.asset_class_path.asset_name) != "AnimSequence": continue
        an = str(ad.asset_name)
        if an == f"Anim_{name}_Idle": anims["idle"] = str(ad.package_name)
        if an == f"Anim_{name}_Walk": anims["walk"] = str(ad.package_name)
    if not sk or "idle" not in anims or "walk" not in anims: print("  skip monster", name, anims); continue
    idle, walk = unreal.load_asset(anims["idle"]), unreal.load_asset(anims["walk"])
    b = sk.get_bounds(); ext = b.box_extent; org = b.origin
    zmin = org.z - ext.z
    hh = max(40.0, ext.z); rad = min(60.0, max(28.0, min(ext.x, ext.y) * 0.8))
    spd = clip_speed(walk) or 150.0
    d = unreal.RDMonsterDef(); d.name = name; d.mesh = sk; d.idle = idle; d.walk = walk
    d.walk_clip_speed = spd; d.walk_speed = max(90.0, min(220.0, spd)); d.capsule_radius = rad; d.capsule_half_height = hh
    d.mesh_z = -hh - zmin; d.mesh_yaw = -90.0; d.scale = 1.0; d.weight = weight
    MON.append(d)
    print(f"  monster {name}: height {ext.z * 2:.0f} capsule r{rad:.0f} hh{hh:.0f} walk clip {spd:.0f} cm/s -> {d.walk_speed:.0f}")
# ---------------------------------------------------------------- game mode (fem5 + dungeon HUD)
G = "/Game/RandomDungeon/Blueprints"; GM = f"{G}/BP_RD_GameMode"
if not eal.does_asset_exist(GM): eal.duplicate_asset("/Game/RandomLevel/Blueprints/BP_RL_GameMode", GM)
gm = unreal.load_asset(GM); cdo = unreal.get_default_object(gm.generated_class())
cdo.set_editor_property("default_pawn_class", unreal.load_asset("/Game/SFCityLevel/Blueprints/BP_SFC_Fem5Character").generated_class())
cdo.set_editor_property("hud_class", unreal.RDHUD)
unreal.BlueprintEditorLibrary.compile_blueprint(gm); eal.save_loaded_asset(gm, only_if_is_dirty=False)
# ---------------------------------------------------------------- level
if eal.does_asset_exist(MAP):
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
else:
    les.new_level(MAP)
w = ues.get_editor_world(); assert w.get_path_name().startswith(MAP + "."), w.get_path_name()
for a in eas.get_all_level_actors():
    if isinstance(a, unreal.WorldSettings) or a.get_class().get_name() == "Brush": continue
    eas.destroy_actor(a)
def spawn(cls, loc, rot=None, label=None, folder="RandomDungeon/Environment"):
    a = eas.spawn_actor_from_class(cls, loc, rot or unreal.Rotator()); a.tags = [TAG]
    if label: a.set_actor_label(label)
    a.set_folder_path(folder); return a
ppv = spawn(unreal.PostProcessVolume, V(0, 0, 0), label="PostProcess"); ppv.set_editor_property("unbound", True)
s = ppv.settings
s.override_auto_exposure_method = True; s.auto_exposure_method = unreal.AutoExposureMethod.AEM_HISTOGRAM
s.override_auto_exposure_min_brightness = True; s.auto_exposure_min_brightness = 0.5
s.override_auto_exposure_max_brightness = True; s.auto_exposure_max_brightness = 4.0
s.override_auto_exposure_bias = True; s.auto_exposure_bias = 0.6
s.override_auto_exposure_speed_up = True; s.auto_exposure_speed_up = 2.0
s.override_auto_exposure_speed_down = True; s.auto_exposure_speed_down = 1.5
s.override_bloom_intensity = True; s.bloom_intensity = 0.8
s.override_vignette_intensity = True; s.vignette_intensity = 0.45
s.override_dynamic_global_illumination_method = True; s.dynamic_global_illumination_method = unreal.DynamicGlobalIlluminationMethod.LUMEN
s.override_reflection_method = True; s.reflection_method = unreal.ReflectionMethod.LUMEN
try:
    s.override_b_mega_lights = True; s.mega_lights = True
except Exception as e: print("  (no MegaLights override:", e, ")")
ppv.set_editor_property("settings", s)
fog = spawn(unreal.ExponentialHeightFog, V(0, 0, 0), label="DungeonHaze")
fc = fog.component; fc.set_editor_property("fog_density", 0.02); fc.set_editor_property("fog_height_falloff", 0.002)
fc.set_editor_property("fog_inscattering_luminance", unreal.LinearColor(0.004, 0.0035, 0.003, 1)); fc.set_editor_property("enable_volumetric_fog", True)
fc.set_editor_property("volumetric_fog_scattering_distribution", 0.4); fc.set_editor_property("volumetric_fog_extinction_scale", 0.6)
gen = spawn(unreal.RDDungeonGenerator, V(0, 0, 0), label="RD_DungeonGenerator", folder="RandomDungeon")
gen.set_editor_property("pieces", P)
gen.set_editor_property("effects", effects)
gen.set_editor_property("monsters", MON)
gen.set_editor_property("reveal_post_material", unreal.load_asset("/Game/RandomLevel/Materials/M_RT_RevealPP"))
gen.set_editor_property("reveal_curtain_material", unreal.load_asset("/Game/RandomLevel/Materials/M_RT_RevealCurtain"))
gen.set_editor_property("reveal_duration", 7.0)
ws = w.get_world_settings(); ws.set_editor_property("default_game_mode", gm.generated_class()); ws.set_editor_property("kill_z", -3000.0)
if "no_build" not in sys.argv:
    gen.build_start_section()
    sec = gen.get_section(unreal.IntPoint(0, 0))
    print("start section:", sec.get_num_rooms(), "rooms,", sec.get_num_doors(), "door leaves,", sec.get_num_containers(), "container parts,",
          sec.get_editor_property("num_instances"), "instances,", sec.get_editor_property("num_lights"), "lights,", round(sec.get_editor_property("generate_ms")), "ms,",
          "reachable rooms", sec.count_reachable_rooms())
    kinds = {}
    for i in range(sec.get_num_rooms()): kinds[sec.get_room_kind(i)] = kinds.get(sec.get_room_kind(i), 0) + 1
    print("rooms by kind:", kinds)
c = gen.get_start_room_center()
ps = spawn(unreal.PlayerStart, V(c.x, c.y, 100), unreal.Rotator(roll=0, pitch=0, yaw=0), "RD_PlayerStart")
print("player start", round(c.x), round(c.y))
les.save_current_level()
print("saved", MAP)
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
