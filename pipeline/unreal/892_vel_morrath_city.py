"""Vel Morrath, the holy city (the user's spec of 2026-11-06, docs/vel_morrath.txt): one of the wilderness's towns on the
brokenspire level, planned as a holy city (C++: the generator's TownPlan 1 for the town FRDWildWorld places north-east of
Brokenspire; RDTownPlan.cpp's bHoly, RDHoly.cpp's cathedral). This script gives the brokenspire level's generator what that
plan builds with and who lives there:
- the city's white stone houses ("Holy.*": House Forge's stone set in Castle of Eternal Mist's pale arch stone, their roofs and
  doors their own), the cathedral's pieces ("Cathedral.*": Castle of Eternal Mist's blind arch walls inside, its columned stone
  and arched windows outside, its stone floors and ceilings, Crownfall's spire and entrance window, Gothic Props' chandelier),
  the plaza's statues on their plinths, its fountain, the wayside shrines, the arch of the stair down into the catacombs
- the catacombs' level the cathedral's stair opens (CatacombsLevel: vel_morrath, 891)
- its people and quests from SourceArt/vel_morrath/city.json: townsfolk and quests of the town "Vel Morrath" (those of
  another run of this script replaced; Brokenspire's, 882's, kept)
Run after 882 / 886 / 890 (882 rewrites the "Town." pieces, Brokenspire's people and quests, and keeps these). Args: none"""
import os, json, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); eal = unreal.EditorAssetLibrary
V = unreal.Vector
MAP = "/Game/RandomDungeon/Maps/brokenspire"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\vel_morrath"
D = json.load(open(os.path.join(SA, "city.json"), encoding="utf-8"))
TOWN = D["town"]
MODULE, WALL_H = 300.0, 300.0
H = MODULE / 2
YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
FACE = 25.0
missing = []
P = {}


def load(p):
    m = unreal.load_asset(p)
    if m is None: missing.append(p)
    return m


def corners(b): return [V(x, y, z) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]


def piece(key, path, front="+y", mode="center", scale=(1, 1, 1), collision=True, fit=None, material=None, shift=(0, 0, 0)):
    """770's / 864's normalisation (center: XY centred, bottom z 0; floor: top z 0; ceil: flipped, underside z 0; wallface: the
    room face at x = 25, thickness behind; raw: rotation only). fit: (x, y) the footprint to scale it to (z by the larger scale)"""
    m = load(path)
    if m is None: return None
    if isinstance(scale, (int, float)): scale = (scale,) * 3
    rot = unreal.Rotator(roll=180.0 if mode == "ceil" else 0.0, pitch=0.0, yaw=YAW[front])
    if fit:
        t1 = unreal.Transform(V(0, 0, 0), rot, V(1, 1, 1))
        pts = [unreal.MathLibrary.transform_location(t1, c) for c in corners(m.get_bounding_box())]
        sx = fit[0] / max(max(p.x for p in pts) - min(p.x for p in pts), 1.0); sy = fit[1] / max(max(p.y for p in pts) - min(p.y for p in pts), 1.0)
        scale = (sx, sy, max(sx, sy)) if mode != "floor" and mode != "ceil" else (sx, sy, 1.0)
    t0 = unreal.Transform(V(0, 0, 0), rot, V(*scale))
    pts = [unreal.MathLibrary.transform_location(t0, c) for c in corners(m.get_bounding_box())]
    mn = V(min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)); mx = V(max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
    tx, ty, tz = -(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z
    if mode == "raw": tx = ty = tz = 0.0
    elif mode == "floor": tz = -mx.z
    elif mode == "wallface": tx = FACE - mx.x
    p = unreal.RDPiece(); p.mesh = m
    p.adjust = unreal.Transform(V(tx + shift[0], ty + shift[1], tz + shift[2]), rot, V(*scale))
    p.size = V(mx.x - mn.x, mx.y - mn.y, mx.z - mn.z); p.collision = collision
    if material is not None: p.material = material
    P[key] = p
    return p


def fixed(key, path, loc=(0, 0, 0), yaw=0.0, scale=(1, 1, 1), size=None, collision=True, material=None):
    """a kit piece with an explicit Adjust: House Forge's, as 882 sets them"""
    m = load(path)
    if m is None: return None
    p = unreal.RDPiece(); p.mesh = m
    p.adjust = unreal.Transform(V(*loc), unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw), V(*scale))
    b = m.get_bounding_box(); p.size = V(*size) if size else V(b.max.x - b.min.x, b.max.y - b.min.y, b.max.z - b.min.z)
    p.collision = collision
    if material is not None: p.material = material
    P[key] = p
    return p


# ---------------------------------------------------------------- the houses: House Forge's stone set in pale arch stone
HF = "/Game/HouseForge_01/Meshes/"
WHITE = load("/Game/CastleofEternalMist/Material/Instances/MI_ArchStone_A")
b = HF + "Stone/SM_Stone_"; wall_z, gable_out = 0.0, 19.0
fl = load(b + "Foundation")
fixed("Holy.Floor", b + "Foundation", loc=(H, H, -fl.get_bounding_box().max.z + 2.0), size=(MODULE, MODULE, 30), material=WHITE)
for k, n in {"Wall": "Wall", "WallWindow": "WallWindow", "WallWindow2": "WallWindow_Arc", "Doorway": "Doorway"}.items():
    fixed(f"Holy.{k}", b + n, loc=(0, -H, wall_z), yaw=180.0, size=(40, MODULE, WALL_H), material=WHITE)
fixed("Holy.Pillar", b + "Pillar_01", loc=(0, 0, wall_z), size=(50, 50, WALL_H), material=WHITE)
fixed("Holy.Roof", b + "Roof", loc=(H, H, wall_z), collision=False, size=(MODULE, MODULE, MODULE))
fixed("Holy.RoofTrim", b + "RoofOverhang", loc=(H, H, wall_z), collision=False)
fixed("Holy.RoofEndL", b + "Roof_End_L", loc=(H, H, wall_z), collision=False)
fixed("Holy.RoofEndR", b + "Roof_End_R", loc=(H, -H, wall_z), collision=False)
fixed("Holy.GableNeg", HF + "Stone/SM_Wall_Tri_L", loc=(gable_out, 0, wall_z), yaw=180.0, collision=False, material=WHITE)
fixed("Holy.GablePos", HF + "Stone/SM_Wall_Tri_R", loc=(gable_out, 0, wall_z), yaw=180.0, collision=False, material=WHITE)
d = fixed("Holy.Door", HF + "Stone/SM_Reinforced_Door", loc=(0, 0, 114.0), yaw=180.0)
if d: d.hinge = V(-13.0, 54.0, 2.0); d.size = V(12, 107, 214)

# ---------------------------------------------------------------- the cathedral (Castle of Eternal Mist's arch walls, 400 x 93 x 601)
BL = "/Game/CastleofEternalMist/Meshes/Arch/Blind/"; WN = "/Game/CastleofEternalMist/Meshes/Arch/Window/"
CW = dict(front="+y", mode="wallface", scale=(0.75, 1, 1))
piece("Cathedral.Wall", BL + "SM_ArchWall_Blind_4x6_A", **CW)
piece("Cathedral.WallOut", BL + "SM_ArchWallStone_Blind_Column_F_4x6_B", **CW)
piece("Cathedral.WindowOut", WN + "SM_ArchWall_Window_Bricks_4x6_A", **CW)
piece("Cathedral.Floor", "/Game/CastleofEternalMist/Meshes/StoneFlooor/SM_StoneFloor_A_StoneFloor_A", front="+x", mode="floor", fit=(300, 300))
piece("Cathedral.Ceil", "/Game/CastleofEternalMist/Meshes/StoneFlooor/SM_StoneFloor_A_StoneFloor_B", front="+x", mode="ceil", fit=(300, 300))
piece("Cathedral.Spire", "/Game/Crownfall/Assets/NaveAssets/SM_S_SpireV1", front="+x", fit=(1150, 1150), collision=False)
# (Crownfall's entrance window stood over the door as a black slab 7 m tall (the first pictures, 2026-11-06): left out; the
# cathedral has no "Cathedral.Rose")
piece("Cathedral.Chandelier", "/Game/Gothic_Props/Assets/Meshes/SM_Prop_Chandelier_A", front="+x", collision=False)
# (the nave's pews: 4.5 m long across the nave, their seats toward the choir (+X); the high altar)
pm = load("/Game/CHURCH/VOL1/Meshes/LP/SM_Pew_01a")
if pm:
    bb = pm.get_bounding_box(); lx, ly = bb.max.x - bb.min.x, bb.max.y - bb.min.y
    piece("Cathedral.Pew", "/Game/CHURCH/VOL1/Meshes/LP/SM_Pew_01a", front="+x" if ly >= lx else "+y", scale=450.0 / max(lx, ly))
piece("Cathedral.Altar", "/Game/Relics/VOL2_ForgottenRelics/Meshes/LP/SM_Altar_01b", front="+x")

# ---------------------------------------------------------------- the plaza: statues on plinths, the fountain, the shrines
piece("Holy.StatuePlinth", "/Game/DarkHalls/StaticMeshes/Props/SM_StatuePlinth", front="+x")
for i, n in enumerate(("SM_Statue_God_Stone1", "SM_Statue_Women_Stone", "SM_Statue_God_Stone2")):
    piece(f"Holy.Statue{i + 1}", "/Game/Statues/Meshes/" + n, front="+x", collision=False)
piece("Holy.Fountain", "/Game/Cemetery_VOL4/Meshes/SM_Fountain_01a", front="+x")
piece("Holy.Shrine", "/Game/Relics/VOL2_ForgottenRelics/Meshes/LP/SM_Altar_01a", front="+x")

w = ues.get_editor_world()
if not w.get_path_name().startswith(MAP + "."): les.load_level(MAP)
g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
pieces = g.get_editor_property("pieces")
for k in [k for k in pieces.keys() if str(k).startswith(("Holy.", "Cathedral."))]: pieces.pop(k)
# (the arch of the stair down: the dungeon's doorway, larger, as the Mistgate's)
dw = pieces.get("Doorway")
if dw:
    a = unreal.RDPiece(); a.mesh = dw.mesh; a.size = dw.size; a.collision = False
    a.adjust = unreal.Transform(dw.adjust.translation, dw.adjust.rotation.rotator(), V(1.0, 1.35, 1.35)); P["Holy.CryptArch"] = a
for k, v in P.items(): pieces[k] = v
g.set_editor_property("pieces", pieces)
g.set_editor_property("catacombs_level", "/Game/RandomDungeon/Maps/vel_morrath")
print("VM pieces:", len(P), "| missing:", missing)

# ---------------------------------------------------------------- its people and quests
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
            # (the forward walk with its root held (882's): the pack's in-place walk moves no foot)
            dst = f"/Game/RandomDungeon/Anims/Town/AS_{pack}_WalkLocked"
            if not eal.does_asset_exist(dst): eal.duplicate_asset(fwd.get_path_name().split(".")[0], dst)
            wl = unreal.load_asset(dst)
            if wl:
                wl.set_editor_property("force_root_lock", True); wl.set_editor_property("enable_root_motion", False)
                # (saved, as 882 saves it: unsaved, a pack only the city uses left its walkers without a walk after a restart)
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
                 ("mesh", mesh), ("idle", idle), ("walk", walk), ("walk_clip_speed", speed), ("walk_speed", 95.0 if t["role"] in ("Pilgrim", "Beggar", "Mourner", "Monk") else 120.0),
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
print("VM", len(defs), "townsfolk of", len(D["townsfolk"]), "|", len(quests), "quests | kept", len(keep_f), "townsfolk and", len(keep_q), "quests of other towns | missing:", missing)
les.save_current_level()
print("VM saved", ues.get_editor_world().get_path_name())
import gc
del g, pieces, defs, quests, keep_f, keep_q
gc.collect()
