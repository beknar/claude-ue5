"""Graymourne, the fog-bound port (the user's spec of 2026-11-07, docs/graymourne.txt): one of the wilderness's towns on the
brokenspire level, planned as a port (C++: the generator's TownPlan 3 for the town FRDWildWorld places on the northern coast;
RDTownPlan.cpp's bPort, RDPort.cpp's harbour). This script gives the brokenspire level's generator what that plan builds with
and who lives there:
- the harbour's pieces ("Port.*"): the piers' decks (Medieval Docks' gangway planks), their pilings (Sea Side Docks) and
  bollards (Docks' mooring posts), the quay's stone face (Castle Forge's plain wall, as the town wall), the ships moored at
  the piers (Castle Forge's longship) and the boats (Harbour Collection's small boat), the wrecks (its broken ship), the
  drowned dead laid on the quay (Pirates Age's dead pirates), gibbets (Mystic Dungeon's), the fishers' racks (Harbour
  Collection's rack, its fish and its rope: three meshes on one origin), nets, crab cages (Docks), barrels
- the sewer gate in the sluice house's far wall ("Port.SewerArch": the Sewer pack's round iron gate, in rusted iron)
- the effect "SewerDrip" (MERIDIAN's water leak)
- the sewers' level for the town (TownDungeons["Graymourne"]: sewers, 897)
- its people and quests from SourceArt/graymourne/city.json: townsfolk and quests of the town "Graymourne" (those of another
  run of this script replaced; the other towns' kept)
Run after 882 / 886 / 890 (882 rewrites the "Town." pieces, Brokenspire's people and quests, and keeps these), 892 and 894.
Args: none"""
import os, json, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); eal = unreal.EditorAssetLibrary
V = unreal.Vector
MAP = "/Game/RandomDungeon/Maps/brokenspire"
DUNGEON = "/Game/RandomDungeon/Maps/sewers"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\graymourne"
D = json.load(open(os.path.join(SA, "city.json"), encoding="utf-8"))
TOWN = D["town"]
TILE = 300.0
YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
missing = []
P = {}


def load(p):
    m = unreal.load_asset(p)
    if m is None: missing.append(p)
    return m


def corners(b): return [V(x, y, z) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]


def piece(key, path, front="+x", mode="center", scale=(1, 1, 1), collision=True, shift=(0, 0, 0), like=None, material=None):
    """the dungeon frame (the mesh's `front` to +X): center: XY centred, bottom z 0; front0: the front face at x 0, the
    rest behind it (-X), centred across, bottom z 0; back: the back at x 0, the rest in front. like: another piece's Adjust
    (meshes that share one origin, as the fish rack's three)"""
    m = load(path)
    if m is None: return None
    if isinstance(scale, (int, float)): scale = (scale,) * 3
    rot = unreal.Rotator(roll=0.0, pitch=0.0, yaw=YAW[front])
    t0 = unreal.Transform(V(0, 0, 0), rot, V(*scale))
    pts = [unreal.MathLibrary.transform_location(t0, c) for c in corners(m.get_bounding_box())]
    mn = V(min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)); mx = V(max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
    tx, ty, tz = -(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z
    if mode == "front0": tx = -mx.x
    elif mode == "back": tx = -mn.x
    p = unreal.RDPiece(); p.mesh = m
    p.adjust = like.adjust if like is not None else unreal.Transform(V(tx + shift[0], ty + shift[1], tz + shift[2]), rot, V(*scale))
    p.size = V(mx.x - mn.x, mx.y - mn.y, mx.z - mn.z); p.collision = collision
    if material:
        mt = load(material)
        if mt: p.material = mt
    P[key] = p
    return p


# ---------------------------------------------------------------- the piers: a deck a tile long and the pier's 2 tiles wide
GW = load("/Game/Hivemind/Medieval_Docks/Static_Meshes/Gangways/SM_Gangway_01")
if GW:
    b = GW.get_bounding_box()
    piece("Port.Deck", GW.get_path_name().split(".")[0], scale=(TILE / (b.max.x - b.min.x) * 1.02, 2 * TILE / (b.max.y - b.min.y) * 1.02, 1.0))
# (the pilings from the harbour's bed (2.6 m down) to just over the deck; the bollards at a pier's end)
piece("Port.Piling", "/Game/SeaSideDocks/VOL1_Docks/Meshes/LP/SM_Pier_Pilings_01a", collision=False)
piece("Port.Bollard", "/Game/Docks/VOL2_Powell/Meshes/SM_Mooring_post_NN_01h", scale=2.5)
# (the quay's face: Castle Forge's plain wall (316 x 114 x 311) with its face toward the water at the edge, the stone behind
# under the quay, from the bed (2.6 m down) to 2 cm under the quay)
piece("Port.Quay", "/Game/Medieval_Castle/CastleKit/Walls_Stone/SM_Castle_Stone_Wall_01a_NN", front="+y", mode="front0", scale=(1.0, 1.0, 258.0 / 311.0), collision=False)

# ---------------------------------------------------------------- the ships, boats and wrecks (their length along +X)
piece("Port.Ship", "/Game/Medieval_Castle/CastleKit/Props/Meshes/Props/VikingBoat/SM_VikingBoat_01a", scale=1.5, collision=False)
piece("Port.Boat", "/Game/Harbour_Collection/Props/SM_SmallBoat/Meshes/FBX/SM_SmallBoat", collision=False)
piece("Port.Wreck", "/Game/Harbour_Collection/Props/SM_BrokenShip/Meshes/FBX/SM_BrokenShip", scale=0.45, collision=False)

# ---------------------------------------------------------------- the quay's dead, gibbets, the fishers' things
piece("Port.Body", "/Game/PiratesAge/VOL5_Prisioners/Meshes/LP/SM_Dead_Pirate_01c", collision=False)
piece("Port.Body2", "/Game/PiratesAge/VOL5_Prisioners/Meshes/LP/SM_Dead_Pirate_01d", collision=False)
piece("Port.Gibbet", "/Game/MysticDungeon/Meshes/Cage/SM_Gibbet_A")
FR = "/Game/Harbour_Collection/Props/SM_FishRack/Meshes/FBX/SM_FishRack_SM_FishRack_"
rack = piece("Port.FishRack", FR + "Wood", front="+y")
if rack:
    piece("Port.FishRack2", FR + "Fish", front="+y", collision=False, like=rack)
    piece("Port.FishRack3", FR + "Rope", front="+y", collision=False, like=rack)
piece("Port.Net", "/Game/Harbour_Collection/Props/SM_BigFishNet/Meshes/FBX/SM_BigFishNet", collision=False)
piece("Port.Cages", "/Game/Docks/VOL5_Laguna/Meshes/SM_Crab_Cages_01a", scale=1.4)
piece("Port.Barrel", "/Game/Castle/Interactive/Meshes/SM_barrel_01_body")

# ---------------------------------------------------------------- the sewer gate in the sluice house's far wall
# (the Sewer pack's round iron sewer gate (189 x 12 x 188) made 1.4 times, standing 45 cm out of the far wall into the room:
# RDPort.cpp's SewerGateBuild. Its gateway frame (SM_Gateway_01) is a plain metal door frame; its
# barred outfall (SM_Sewer_Bars_01a) is pale concrete that read as a glowing white ring in the sluice house (884 gm1, gm2);
# the gate's own metal read nearly as pale in the fog (gm4): it is in Junkyard's rusted iron, as The War Engine's golems)
piece("Port.SewerArch", "/Game/Sewer/Meshes/Concrete_Tube/SM_Sewer_Tube_Gate_01a", front="+y", mode="back", scale=1.4, collision=False,
      material="/Game/Scene_Junkyard/Assets/MS/3D/Ind_Jun_Gear_Metal_Rusty_02/MI_Ind_Jun_Gear_Metal_Rusty_02")

FX = {"SewerDrip": "/Game/MERIDIAN/VOL31_14WidowSt/VFX/NS_Water_Leakage_03a"}

w = ues.get_editor_world()
if not w.get_path_name().startswith(MAP + "."): les.load_level(MAP)
g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
pieces = g.get_editor_property("pieces")
for k in [k for k in pieces.keys() if str(k).startswith("Port.")]: pieces.pop(k)
for k, v in P.items(): pieces[k] = v
g.set_editor_property("pieces", pieces)
effects = g.get_editor_property("effects")
for k, path in FX.items():
    s = load(path)
    if s: effects[k] = s
g.set_editor_property("effects", effects)
td = g.get_editor_property("town_dungeons"); td[TOWN] = DUNGEON; g.set_editor_property("town_dungeons", td)
print("GM pieces:", len(P), "| effects:", [k for k in FX if k in effects], "| missing:", missing)

# ---------------------------------------------------------------- its people and quests (892's / 894's way)
clips = {}
def pack_clips(pack):
    if pack not in clips:
        a = f"/Game/{pack}/Demoscene_UE5/Animations/"
        idle = unreal.load_asset(a + "MM_Idle"); walk = unreal.load_asset(a + "MM_Walk_InPlace"); speed = 150.0
        fwd = unreal.load_asset(a + "MM_Walk_Fwd")
        if fwd:
            n = unreal.AnimationLibrary.get_num_frames(fwd)
            dd = unreal.AnimationLibrary.get_bone_pose_for_frame(fwd, "root", n - 1, False).translation - unreal.AnimationLibrary.get_bone_pose_for_frame(fwd, "root", 0, False).translation
            if dd.length() > 50: speed = dd.length() / fwd.get_play_length()
            dst = f"/Game/RandomDungeon/Anims/Town/AS_{pack}_WalkLocked"
            if not eal.does_asset_exist(dst): eal.duplicate_asset(fwd.get_path_name().split(".")[0], dst)
            wl = unreal.load_asset(dst)
            if wl:
                wl.set_editor_property("force_root_lock", True); wl.set_editor_property("enable_root_motion", False)
                eal.save_loaded_asset(wl, False)
                walk = wl
        clips[pack] = (idle, walk, speed)
    return clips[pack]
defs = []
for t in D["townsfolk"]:
    mesh = unreal.load_asset(f"/Game/{t['pack']}/{t['mesh']}")
    idle, walk, speed = pack_clips(t["pack"])
    if not (mesh and idle):
        print("  MISSING townsperson", t["name"], t["mesh"], "mesh" if not mesh else "idle"); missing.append(t["name"]); continue
    parts = []
    mn = mesh.get_name()
    if "NPC_Characters_Pack" in mesh.get_path_name() and "_Full_02" in mn:
        base = mesh.get_path_name().rsplit("/Full/", 1)[0] + "/Separate/" + mn.split("_Full_02")[0]
        for part in ("_Head", "_Hair", "_Beard", "_Mustache"):
            if eal.does_asset_exist(base + part): parts.append(unreal.load_asset(base + part))
    x = unreal.RDTownsfolkDef()
    x.set_editor_property("parts", parts)
    for k, v in (("name", t["name"]), ("role", getattr(unreal.RDTownRole, t["role"].upper())), ("town", TOWN), ("title", t["title"]), ("calling", t.get("calling", "")),
                 ("mesh", mesh), ("idle", idle), ("walk", walk), ("walk_clip_speed", speed), ("walk_speed", 95.0 if t["role"] in ("Refugee", "Mourner") else 120.0),
                 ("scale", float(t.get("scale", 1.0))), ("mesh_yaw", -90.0), ("mesh_z", 0.0), ("count", int(t.get("count", 1))), ("lines", t.get("lines", [])), ("topics", t.get("topics", []))):
        x.set_editor_property(k, v)
    defs.append(x)
quests = []
for q in D["quests"]:
    x = unreal.RDQuestDef()
    for k, v in (("id", q["id"]), ("giver", q["giver"]), ("town", TOWN), ("title", q["title"]), ("offer", q["offer"]), ("done", q.get("done", "")), ("goal", q["goal"]),
                 ("count", int(q.get("count", 1))), ("gold", int(q.get("gold", 0))), ("reward_item", q.get("reward", "None")), ("after", q.get("after", "None")), ("hint", q.get("hint", ""))):
        x.set_editor_property(k, v)
    quests.append(x)
keep_f = [d_ for d_ in g.get_editor_property("townsfolk") if str(d_.get_editor_property("town")) != TOWN]
keep_q = [q_ for q_ in g.get_editor_property("quests") if str(q_.get_editor_property("town")) != TOWN]
g.set_editor_property("townsfolk", keep_f + defs); g.set_editor_property("quests", keep_q + quests)
print("GM", len(defs), "townsfolk of", len(D["townsfolk"]), "|", len(quests), "quests | kept", len(keep_f), "townsfolk and", len(keep_q), "quests of other towns | missing:", missing)
les.save_current_level()
print("GM saved", ues.get_editor_world().get_path_name())
import gc
del g, pieces, defs, quests, keep_f, keep_q, effects, td
gc.collect()
