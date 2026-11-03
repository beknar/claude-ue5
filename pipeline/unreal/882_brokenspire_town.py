"""Brokenspire (docs/brokenspire.txt): the town's pieces, its people and its quests, then its start section built.
- pieces "Town.*" in the generator's Pieces (the dungeon frame: front +X, footprint centred, floor z 0; the house kit's in
  the village's own frame, which RDTownPlan.cpp builds with: walls centred on their segment with the outside +X, roofs
  cell-centred with the eave +X, floors tile-centred): House Forge's timber, stone and thatch houses (780's STYLES), the
  same timber in House Forge's burnt wood for the burned houses; Castle Forge's walls, parapets, gate and tower roofs for
  the town wall and the castle's top; the square's well, quest board, market stalls, fire baskets; the circle's standing
  stones; the graveyard's stones and fence; the barracks' dummies; carts, hay, sacks, logs; trees, bushes and grass; the
  trades' signs; the castle's Mistgate arch and the storehouse's chest (the dungeon's, without a lid that opens)
- the townsfolk (FRDTownsfolkDef) and the quests (FRDQuestDef) from SourceArt/brokenspire/town.json: each model's idle and
  in-place walk clips from its pack (the walk's ground speed measured on the pack's MM_Walk_Fwd root, as 786); the drunk's
  clips are another pack's (Drunk_Man_Animations): its skeleton is made compatible with the NPC pack's
- the start section built with the generator's StartSeed (BuildStartSection) and the level saved
Run after 881. Args: [nobuild]"""
import sys, os, json, unreal
ARGS = globals().get("ARGS", sys.argv[1:])
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); eal = unreal.EditorAssetLibrary
ar = unreal.AssetRegistryHelpers.get_asset_registry()
V = unreal.Vector
MAP = "/Game/RandomDungeon/Maps/brokenspire"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\brokenspire"
MODULE, WALL_H = 300.0, 300.0
HF = "/Game/HouseForge_01/Meshes/"; VK = "/Game/HouseForge_01/Viking_Village_Props/Meshes/"; DK = "/Game/Hivemind/Medieval_Docks/Static_Meshes/"
FOL = "/Game/Hivemind/Medieval_Docks/Scanned_Foliage/Foliage/"; SH = "/Game/Hive_Sherwood/Meshes/"; VC = "/Game/Village_Collection/Props/"
CC = "/Game/Castle_Collection/Props/"; WC = "/Game/WarCamp_Collection/Props/"; CK = "/Game/Medieval_Castle/CastleKit/"
missing = []


def load(p):
    m = unreal.load_asset(p)
    if m is None: missing.append(p)
    return m


def find(folder, *words):
    """the first static mesh under folder whose name has all the words (lower case), or None"""
    for a in sorted(ar.get_assets_by_path(folder, recursive=True), key=lambda a: str(a.asset_name)):
        if str(a.asset_class_path.asset_name) != "StaticMesh": continue
        n = str(a.asset_name).lower()
        if all(w in n for w in words): return str(a.package_name)
    missing.append(f"{folder} {words}")
    return None


YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
def corners(b): return [V(x, y, z) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]
P = {}


def piece(name, m, front="+y", mode="center", scale=(1, 1, 1), collision=True, size=None, actor=None, material=None, shift=(0, 0, 0)):
    """mesh frame -> the dungeon frame: the mesh's `front` side to +X; center (footprint centred, bottom z 0), raw (rotation
    only), back (back at x 0)"""
    if isinstance(m, str): m = load(m)
    if m is None: return None
    if isinstance(scale, (int, float)): scale = (scale,) * 3
    rot = unreal.Rotator(roll=0.0, pitch=0.0, yaw=YAW[front]); t0 = unreal.Transform(V(0, 0, 0), rot, V(*scale))
    pts = [unreal.MathLibrary.transform_location(t0, c) for c in corners(m.get_bounding_box())]
    mn = V(min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)); mx = V(max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
    tx, ty, tz = -(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z
    if mode == "raw": tx = ty = tz = 0.0
    elif mode == "back": tx = -mn.x
    p = unreal.RDPiece()
    if actor is not None: p.actor_class = actor
    else: p.mesh = m
    p.adjust = unreal.Transform(V(tx + shift[0], ty + shift[1], tz + shift[2]), rot, V(*scale))
    p.size = V(*size) if size else V(mx.x - mn.x, mx.y - mn.y, mx.z - mn.z)
    p.collision = collision
    if material is not None: p.material = material
    P["Town." + name] = p
    return p


def fixed(name, path, loc=(0, 0, 0), yaw=0.0, scale=(1, 1, 1), size=None, collision=True, material=None):
    """a kit piece with an explicit Adjust (location after rotation): the house kit's, as 780 sets them"""
    m = load(path)
    if m is None: return None
    p = unreal.RDPiece(); p.mesh = m
    p.adjust = unreal.Transform(V(*loc), unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw), V(*scale))
    b = m.get_bounding_box(); p.size = V(*size) if size else V(b.max.x - b.min.x, b.max.y - b.min.y, b.max.z - b.min.z)
    p.collision = collision
    if material is not None: p.material = material
    P["Town." + name] = p
    return p


# ---------------------------------------------------------------- the houses: House Forge's three styles (780's), and burnt
H = MODULE / 2
BURNT = load("/Game/HouseForge_01/Materials/Wood/MI_Wood_Burnt")
STYLES = {  # style: (folder, prefix, wall names, door mesh, door bottom below its pivot, hinge, wall z, gable offset out, material)
    "Timber": ("Wood/", "SM_Wood_", {"Wall": "Wall", "WallWindow": "WallWindow", "WallWindow2": "WallWindowLarge", "Doorway": "Doorway"}, "Wood/SM_Wood_Door", 114.0, (-9.8, 53.3, 2.3), 0.0, 19.0, None),
    "Stone": ("Stone/", "SM_Stone_", {"Wall": "Wall", "WallWindow": "WallWindow", "WallWindow2": "WallWindow_Arc", "Doorway": "Doorway"}, "Stone/SM_Reinforced_Door", 114.0, (-13.0, 54.0, 2.0), 0.0, 19.0, None),
    "Thatch": ("Primitive/", "SM_Primitive_", {"Wall": "Wall_V2", "WallWindow": "WallWindow", "WallWindow2": "WallWindow_V2", "Doorway": "Doorway"}, "Primitive/SM_Primitive_Door", 147.0, (-2.6, 58.1, -28.5), -13.0, 40.0, None),
    "Burnt": ("Wood/", "SM_Wood_", {"Wall": "Wall", "WallWindow": "WallWindow", "WallWindow2": "WallWindowLarge", "Doorway": "Doorway"}, "Wood/SM_Wood_Door", 114.0, (-9.8, 53.3, 2.3), 0.0, 19.0, BURNT),
}
for style, (folder, pre, walls, door, door_drop, hinge, wall_z, gable_out, mat) in STYLES.items():
    b = HF + folder + pre
    fl = load((HF + "Wood/SM_Wood_" if style in ("Thatch", "Burnt") else b) + "Foundation")
    fixed(f"{style}_Floor", fl.get_path_name().split(".")[0], loc=(H, H, -fl.get_bounding_box().max.z + 2.0), size=(MODULE, MODULE, 30), material=mat)
    for k, n in walls.items(): fixed(f"{style}_{k}", b + n, loc=(0, -H, wall_z), yaw=180.0, size=(40, MODULE, WALL_H), material=mat)
    fixed(f"{style}_Pillar", b + "Pillar_01", loc=(0, 0, wall_z), size=(50, 50, WALL_H), material=mat)
    fixed(f"{style}_Roof", b + "Roof", loc=(H, H, wall_z), collision=False, size=(MODULE, MODULE, MODULE), material=mat)
    fixed(f"{style}_RoofTrim", b + "RoofOverhang", loc=(H, H, wall_z), collision=False, material=mat)
    endl, endr = ("RoofEnd_L", "RoofEnd_R") if style != "Stone" else ("Roof_End_L", "Roof_End_R")
    fixed(f"{style}_RoofEndL", b + endl, loc=(H, H, wall_z), collision=False, material=mat)
    fixed(f"{style}_RoofEndR", b + endr, loc=(H, -H, wall_z), collision=False, material=mat)
    tri = b if style != "Stone" else HF + "Stone/SM_"
    fixed(f"{style}_GableNeg", tri + "Wall_Tri_L", loc=(gable_out, 0, wall_z), yaw=180.0, collision=False, material=mat)
    fixed(f"{style}_GablePos", tri + "Wall_Tri_R", loc=(gable_out, 0, wall_z), yaw=180.0, collision=False, material=mat)
    d = fixed(f"{style}_Door", HF + door, loc=(0, 0, door_drop), yaw=180.0, scale=(-1, 1, 1) if style == "Thatch" else (1, 1, 1), material=mat)
    if d: d.hinge = V(*hinge); d.size = V(12, 107, 214)
# ---------------------------------------------------------------- the town wall, its gate and towers; the castle's top
# (Castle Forge's walls: 01a is plain stone; 02a, used here until 2026-11-02, has an arched doorway through it, and the town
# wall was a row of arches; 02h has an arrow slit, 02f / 02g small windows, 02d a tall one)
WS = CK + "Walls_Stone/"
piece("CityWall", WS + "SM_Castle_Stone_Wall_01a_NN", front="+y")
piece("CityWallSlit", WS + "SM_Castle_Stone_Wall_02h_NN", front="+y")
piece("CityWallWin", WS + "SM_Castle_Stone_Wall_02f_NN", front="+y")
# (the watchtowers' door from the town (2026-11-02): 02a's arched doorway, 112 cm wide and 240 high in its middle; drawn without
# its own collision, which closes the doorway's foot: RDTownPlan.cpp puts boxes beside and over the opening)
piece("CityWallDoor", WS + "SM_Castle_Stone_Wall_02a_NN", front="+y", collision=False)
piece("Parapet", WS + "SM_Castle_Stone_Parapet_01a_NN", front="+y", collision=False)
# the castle's outside (RDTownPlan.cpp's CastleOuterFace / CastleTowersBuild; the user's of 2026-11-02: medieval walls with
# windows, arrow slits, towers and a way up to the battlements instead of the dungeon's blind arches)
for n, m in (("CWall", "01a"), ("CWallSlit", "02h"), ("CWallWin1", "02f"), ("CWallWin2", "02g"), ("CWallWinL", "02d")):
    piece(n, WS + f"SM_Castle_Stone_Wall_{m}_NN", front="+y")
# (the round tower's quarters: their origin is the tower's middle, the quarter between +X and +Y (raw: no centring); a slit,
# a small window, a window, a doorway, plain stone)
for c in "abcde":
    piece("TowerRing" + c.upper(), WS + f"SM_Castle_Tower_Wall_02{c}_NN", front="+x", mode="raw", collision=False)
piece("TowerCone", WS + "SM_Tower_Roof_02a_NN", front="+x", mode="raw", collision=False)
# (a quarter turn of a spiral stair round its post, 100 cm up, climbing clockwise from its yaw; walked on: complex collision)
piece("Spiral", WS + "SM_Stone_Stairs_01a_NN", front="+x", mode="raw")
# (the towers' collision: hidden boxes, the pack's quarters close the foot of their doorways)
col = piece("Collider", "/Engine/BasicShapes/Cube", front="+x")
if col: col.hidden = True
piece("Gate", CK + "Wood_Structures/SM_Main_Gate_03a_NN", front="+y", collision=False)
piece("GateLeaves", CK + "Wood_Structures/SM_Gate_Door_01c_NN", front="+y", collision=False)
piece("GateBar", CK + "Wood_Structures/SM_Gate_Door_01e_NN", front="+y", collision=False, mode="raw")
piece("TowerRoof", CK + "Walls_Stone/SM_Tower_Roof_01d_NN", front="+x", scale=2.4, collision=False)
# (the castle's roof is its wall walk since 2026-11-02: walked on)
piece("CastleRoof", CK + "Walls_Stone/SM_Stone_Floor_01a_NN", front="+x", scale=0.9)
# ---------------------------------------------------------------- the square, the circle, the graveyard, the yards
piece("Well", VC + "SM_OldWell/Meshes/FBX/SM_OldWell_SM_OldWell_Stone", front="+x", mode="raw", size=(180, 180, 280))
piece("WellTop", VC + "SM_OldWell/Meshes/FBX/SM_OldWell_SM_OldWell_Wood", front="+x", mode="raw", collision=False)
# (SM_WantedBoard is the board's plank face, not papers: the pack's board has none. Turned +y with the frame's own Adjust its
# planks and the frame's slats interleaved; as it was, -y and raw, the board looks whole)
piece("Board", VC + "SM_WantedBoard/Meshes/FBX/SM_WantedBoard_Wood", front="-y")
piece("BoardNotes", VC + "SM_WantedBoard/Meshes/FBX/SM_WantedBoard", front="-y", mode="raw", collision=False)
# (the board's papers themselves: that "notes" mesh is the board's plank face, with nothing on it. A bounty notice, drawn by
# blender_numpy/bs_notice.py and imported by 883 (T_BS_mapc_notice), on a plane stood up facing +X, 32 x 42 cm, in a
# two-sided material made here; RDTownPlan.cpp pins a notice for each bounty)
NT = unreal.load_asset("/Game/RandomDungeon/UI/Brokenspire/T_BS_mapc_notice")
if NT:
    MP = "/Game/RandomDungeon/Materials/M_BS_Notice"
    mat_n = unreal.load_asset(MP)
    if not mat_n:
        mat_n = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_BS_Notice", "/Game/RandomDungeon/Materials", unreal.Material, unreal.MaterialFactoryNew())
        MEL = unreal.MaterialEditingLibrary
        ts = MEL.create_material_expression(mat_n, unreal.MaterialExpressionTextureSample, -400, 0); ts.texture = NT
        MEL.connect_material_property(ts, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
        rc = MEL.create_material_expression(mat_n, unreal.MaterialExpressionConstant, -400, 250); rc.r = 0.85
        MEL.connect_material_property(rc, "", unreal.MaterialProperty.MP_ROUGHNESS)
        mat_n.set_editor_property("two_sided", True); mat_n.set_editor_property("used_with_instanced_static_meshes", True)
        MEL.recompile_material(mat_n); eal.save_loaded_asset(mat_n, False)
    pl = load("/Engine/BasicShapes/Plane")
    if pl:
        p = unreal.RDPiece(); p.mesh = pl; p.collision = False; p.material = mat_n
        # (the plane lies in XY facing +Z: pitched -90 it faces +X, its X the notice's height)
        p.adjust = unreal.Transform(V(0, 0, 0), unreal.Rotator(roll=0.0, pitch=-90.0, yaw=0.0), V(0.42, 0.32, 1.0)); p.size = V(1, 32, 42)
        P["Town.Notice"] = p
else: print("  TOWN no notice texture yet (bs_notice.py, then 883, then 882 again)")
for i in (1, 2, 3):
    piece(f"Stall{i}", DK + "Props/Market/SM_Market_Stand_01", front="-y", mode="raw", actor=eal.load_blueprint_class(f"/Game/Hivemind/Medieval_Docks/Blueprints/BP_MarketStand_0{i}"))
piece("Lamp", WC + "SM_FireBasket/Meshes/FBX/SM_FireBasket", front="+x")
piece("CircleStone", CK + "Walls_Stone/SM_Castle_Stone_Pillar_01a_NN", front="+x", scale=(1.3, 1.3, 1.25))
piece("CircleFloor", CK + "Walls_Stone/SM_Stone_Floor_02a_NN", front="+x", scale=(3.6, 3.6, 1.0), collision=False)
for i, g in enumerate(("01a", "01b", "01c", "01d", "02a", "02b", "02c", "02d")):
    piece(f"Grave{i + 1}", f"/Game/CHURCH/VOL2_Graveyard/Meshes/LP/SM_GraveStones_{g}", front="+y")
piece("Fence", "/Game/FantasyCemetery/Assets/SM_FenceA", front="+y")
piece("FenceGate", "/Game/FantasyCemetery/Assets/SM_GateA", front="+y", collision=False)
dead = find("/Game/Hive_Sherwood", "dead") or find("/Game/Hivemind/Medieval_Docks/Scanned_Foliage", "beech", "l_02")
if dead: piece("DeadTree", dead, front="+x", mode="raw", collision=False)
piece("Dummy", WC + "SM_Garrison_Dummy/Meshes/FBX/SM_Garrison_Dummy", front="+y")
piece("Target", WC + "SM_Garrison_Target/Meshes/FBX/SM_Garrison_Target", front="+y")
piece("Cart", VC + "SM_WoodenCart/Meshes/FBX/SM_WoodenCart", front="+y")
piece("Cart2", VC + "SM_WoodWagons_Var/Meshes/FBX/SM_WoodWagons_Var1", front="+x")
piece("Hay", VC + "SM_HaySquare/Meshes/FBX/SM_HaySquare_SM_HaySquare", front="+x")
piece("Sacks", DK + "Props/SM_Sack_01", front="+x")
piece("Logs", VK + "Props/WoodLogs/sm_WoodLog_01d", front="+y")
piece("StillPot", DK + "Props/SM_Cauldron", front="+x", scale=1.6)
piece("Keg", DK + "Props/SM_Large_Keg", front="+x")
tent = find("/Game/Hive_Sherwood/Meshes", "tent")
if tent: piece("Tent", tent, front="+x")
fire = find(CC, "firepit") or find(WC, "firebasket")
if fire: piece("Firepit", fire, front="+x", collision=False)
mill = eal.load_blueprint_class("/Game/Old_Windmill/Blueprint/BP_windmill")
if mill: piece("Mill", "/Game/Old_Windmill/Meshes/Millstone/SM_millstone_bottom", front="+x", mode="raw", actor=mill, size=(900, 900, 1600))
B_ = FOL + "EuropeanBeech/Meshes/SM_EuropeanBeech_"
for n, m in (("Tree1", B_ + "L_01"), ("Tree2", B_ + "M_01"), ("Tree3", FOL + "SilverFir/Meshes/SM_SilverFir_M_01")):
    piece(n, m, front="+x", mode="raw")
piece("Bush", SH + "SM_Bush_02", front="+x", mode="raw", scale=1.6, collision=False)
piece("Grass", SH + "SM_Grass_2", front="+x", mode="raw", scale=0.8, collision=False)
piece("Sign", DK + "Props/SM_TavernSign_01", front="+x", mode="raw", collision=False)
piece("Planks", SH + "SM_Wooden_Planks_B", front="+x", scale=0.6, collision=False)
beam = find("/Game/CastleofEternalMist/Meshes", "beam", "dmg")
if beam: piece("CharredBeam", beam, front="+x", collision=False, material=BURNT)
# ---------------------------------------------------------------- the castle's Mistgate arch, the storehouse's chest
w = ues.get_editor_world()
if not w.get_path_name().startswith(MAP + "."): les.load_level(MAP)
g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
pieces = g.get_editor_property("pieces")
for k in [k for k in pieces.keys() if str(k).startswith("Town.")]: pieces.pop(k)
dw = pieces.get("Doorway")
if dw:
    a = unreal.RDPiece(); a.mesh = dw.mesh; a.size = dw.size; a.collision = False
    a.adjust = unreal.Transform(dw.adjust.translation, dw.adjust.rotation.rotator(), V(1.0, 1.35, 1.35)); P["Town.MistArch"] = a
ch = pieces.get("Chest")
if ch:
    a = unreal.RDPiece(); a.mesh = ch.mesh; a.adjust = ch.adjust; a.size = ch.size; a.collision = True; P["Town.StashChest"] = a
for k, v in P.items(): pieces[k] = v
g.set_editor_property("pieces", pieces)
print("TOWN pieces:", len(P), "| missing:", missing)

# ---------------------------------------------------------------- the townsfolk and the quests
D = json.load(open(os.path.join(SA, "town.json"), encoding="utf-8"))
clips = {}
def pack_clips(pack, ue4):
    key = (pack, ue4)
    if key not in clips:
        a = f"/Game/{pack}/Demoscene_{'UE4' if ue4 else 'UE5'}/Animations/"
        idle = unreal.load_asset(a + ("ThirdPersonIdle" if ue4 else "MM_Idle")); walk = unreal.load_asset(a + ("ThirdPersonWalk" if ue4 else "MM_Walk_InPlace"))
        fwd = None if ue4 else unreal.load_asset(a + "MM_Walk_Fwd")
        speed = 150.0
        if fwd:
            n = unreal.AnimationLibrary.get_num_frames(fwd)
            d = unreal.AnimationLibrary.get_bone_pose_for_frame(fwd, "root", n - 1, False).translation - unreal.AnimationLibrary.get_bone_pose_for_frame(fwd, "root", 0, False).translation
            if d.length() > 50: speed = d.length() / fwd.get_play_length()
            # (the walk: the pack's forward walk with its root held in place, so its feet step back under her as she moves; the
            # pack's MM_Walk_InPlace moves no foot forward or back at all (measured: 0.0 cm, 9 cm up): the townsfolk marched on
            # the spot while they slid (the user's of 2026-11-02: "the children NPCs' legs do not move when they walk"))
            dst = f"/Game/RandomDungeon/Anims/Town/AS_{pack}_WalkLocked"
            if not eal.does_asset_exist(dst): eal.duplicate_asset(fwd.get_path_name().split(".")[0], dst)
            wl = unreal.load_asset(dst)
            if wl:
                wl.set_editor_property("force_root_lock", True); wl.set_editor_property("enable_root_motion", False)
                eal.save_loaded_asset(wl, False); walk = wl
        clips[key] = (idle, walk, speed)
    return clips[key]
# (the drunk's clips are on Drunk_Man_Animations' mannequin: the NPC pack's UE4 skeleton takes them as compatible)
npc4 = unreal.load_asset("/Game/NPC_Characters_Pack/Demoscene_UE4/Mesh/UE4_Mannequin_Skeleton")
drunk = unreal.load_asset("/Game/Drunk_Man_Animations/Mesh/SK_Mannequin_Skeleton")
if npc4 and drunk:
    have = [str(s) for s in npc4.get_editor_property("compatible_skeletons")]
    if not any("Drunk_Man_Animations" in h for h in have):
        npc4.add_compatible_skeleton(drunk); eal.save_loaded_asset(npc4, only_if_is_dirty=False)
        print("TOWN the NPC pack's UE4 skeleton takes the drunk's clips (compatible skeleton)")
roles = {r: getattr(unreal.RDTownRole, r.upper()) for r in ("Elder", "Scholar", "Captain", "Smith", "Trader", "Healer", "Priest", "Keeper", "Innkeeper", "Drunk", "Witch",
                                                           "Child", "Refugee", "Idiot", "Preacher", "Mourner", "Guard", "Militia", "Soldier", "Townsfolk")}
defs = []
for t in D["townsfolk"]:
    mesh = unreal.load_asset(f"/Game/{t['pack']}/{t['mesh']}")
    ue4 = "/Mesh_UE4/" in t["mesh"]
    idle, walk, speed = pack_clips(t["pack"], ue4)
    if t.get("idle"): idle = unreal.load_asset(t["idle"])
    if t.get("walk"): walk = unreal.load_asset(t["walk"])
    if not (mesh and idle):
        print("  MISSING townsperson", t["name"], t["mesh"], "mesh" if not mesh else "idle"); continue
    # (the NPC pack's _Full_02 bodies come without a head (the user's of 2026-11-02: Simple Tam, the innkeeper, the priest and
    # the drunk had none): its Separate folder's head, hair, beard and moustache go on as parts, following the body)
    parts = []
    mn = mesh.get_name()
    if "NPC_Characters_Pack" in mesh.get_path_name() and "_Full_02" in mn:
        base = mesh.get_path_name().rsplit("/Full/", 1)[0] + "/Separate/" + mn.split("_Full_02")[0]
        for part in ("_Head", "_Hair", "_Beard", "_Mustache"):
            if eal.does_asset_exist(base + part): parts.append(unreal.load_asset(base + part))
        print("  TOWN parts for", t["name"], mn, [p.get_name() for p in parts])
    d = unreal.RDTownsfolkDef()
    d.set_editor_property("parts", parts)
    for k, v in (("name", t["name"]), ("role", roles[t["role"]]), ("title", t["title"]), ("calling", t.get("calling", "")), ("mesh", mesh), ("idle", idle), ("walk", walk),
                 ("walk_clip_speed", speed if not t.get("walk") else 120.0), ("walk_speed", 95.0 if t["role"] in ("Drunk", "Refugee", "Mourner") else 120.0),
                 ("scale", float(t.get("scale", 1.0))), ("mesh_yaw", -90.0), ("mesh_z", 0.0), ("count", int(t.get("count", 1))), ("lines", t.get("lines", [])), ("topics", t.get("topics", []))):
        d.set_editor_property(k, v)
    defs.append(d)
quests = []
for q in D["quests"]:
    x = unreal.RDQuestDef()
    for k, v in (("id", q["id"]), ("giver", q["giver"]), ("title", q["title"]), ("offer", q["offer"]), ("done", q.get("done", "")), ("goal", q["goal"]), ("count", int(q.get("count", 1))),
                 ("gold", int(q.get("gold", 0))), ("reward_item", q.get("reward", "None")), ("after", q.get("after", "None")), ("hint", q.get("hint", ""))):
        x.set_editor_property(k, v)
    quests.append(x)
g.set_editor_property("townsfolk", defs); g.set_editor_property("quests", quests)
print("TOWN", len(defs), "townsfolk of", len(D["townsfolk"]), "|", len(quests), "quests")
if "nobuild" not in ARGS:
    g.build_start_section()
    s = unreal.GameplayStatics.get_all_actors_of_class(ues.get_editor_world(), unreal.RDSection)
    print("TOWN built:", len(s), "section(s)", [(x.get_editor_property("num_instances"), x.get_editor_property("num_lights"), round(x.get_editor_property("generate_ms"))) for x in s])
les.save_current_level()
print("saved", ues.get_editor_world().get_path_name())
import gc
del g, pieces, defs, quests
gc.collect()
