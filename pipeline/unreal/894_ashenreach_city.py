"""Ashenreach, the forge city (the user's spec of 2026-11-07, docs/ashenreach.txt): one of the wilderness's towns on the
brokenspire level, planned as a forge city (C++: the generator's TownPlan 2 for the town FRDWildWorld places in the
continent's middle north of Brokenspire, at the edge of its burned plain; RDTownPlan.cpp's bForge, RDForge.cpp's foundry).
This script gives the brokenspire level's generator what that plan builds with and who lives there:
- the city's houses of soot-dark stone ("Forge.*": House Forge's stone set in a darkened copy of its own stone, made here:
  /Game/RandomDungeon/Materials/Forge/MI_Forge_SootStone; their roofs and doors their own)
- the foundry's pieces ("Foundry.*": Dwarven Citadel's brick walls inside and out, its floor and ceiling tiles, its
  chandeliers; a chimney on each stack; a brick kiln either side of the iron gate; the gate itself, the dungeon's doorway
  larger, as the cathedral's crypt arch)
- the square's things ("Forge.*": the guild's great anvil on a plinth, the open forges (the castle kit's hooded forge) and
  their anvils, the ore carts on wooden rails (Old Mine), the barricade's spiked palisades (War Camp))
- the effects "ChimneySmoke" (MERIDIAN's chimney smoke) and "ForgeSparks" (Dragon Graveyard's sparks)
- The War Engine's level for the town (TownDungeons["Ashenreach"]: war_engine, 895)
- its people and quests from SourceArt/ashenreach/city.json: townsfolk and quests of the town "Ashenreach" (those of another
  run of this script replaced; the other towns' kept)
Run after 882 / 886 / 890 (882 rewrites the "Town." pieces, Brokenspire's people and quests, and keeps these) and 892.
Args: none"""
import os, json, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); eal = unreal.EditorAssetLibrary
V = unreal.Vector
MAP = "/Game/RandomDungeon/Maps/brokenspire"
DUNGEON = "/Game/RandomDungeon/Maps/war_engine"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\ashenreach"
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
    """770's / 864's normalisation (892's): center: XY centred, bottom z 0; floor: top z 0; ceil: flipped, underside z 0;
    wallface: the room face at x = 25, thickness behind; raw: rotation only. fit: (x, y) the footprint to scale it to"""
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


# ---------------------------------------------------------------- the soot-dark stone: a copy of House Forge's own, darkened
MD = "/Game/RandomDungeon/Materials/Forge"; SOOT_P = MD + "/MI_Forge_SootStone"
if not eal.does_asset_exist(SOOT_P):
    unreal.AssetToolsHelpers.get_asset_tools().create_asset("MI_Forge_SootStone", MD, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
SOOT = unreal.load_asset(SOOT_P)
MEL = unreal.MaterialEditingLibrary
MEL.set_material_instance_parent(SOOT, unreal.load_asset("/Game/HouseForge_01/Materials/Stone/MI_Rocks"))
# (0.34 read nearly black against the morning sky (884 ar1's picture of the square): 0.5)
MEL.set_material_instance_vector_parameter_value(SOOT, "Base Color -Tint", unreal.LinearColor(0.5, 0.46, 0.43, 1.0))
MEL.set_material_instance_scalar_parameter_value(SOOT, "Desaturation", 0.35)
MEL.set_material_instance_scalar_parameter_value(SOOT, "Dirt - Amount", 1.0)
MEL.update_material_instance(SOOT)
eal.save_loaded_asset(SOOT, False)

# ---------------------------------------------------------------- the houses: House Forge's stone set in the soot-dark stone
HF = "/Game/HouseForge_01/Meshes/"
b = HF + "Stone/SM_Stone_"; wall_z, gable_out = 0.0, 19.0
fl = load(b + "Foundation")
fixed("Forge.Floor", b + "Foundation", loc=(H, H, -fl.get_bounding_box().max.z + 2.0), size=(MODULE, MODULE, 30), material=SOOT)
for k, n in {"Wall": "Wall", "WallWindow": "WallWindow", "WallWindow2": "WallWindow_Arc", "Doorway": "Doorway"}.items():
    fixed(f"Forge.{k}", b + n, loc=(0, -H, wall_z), yaw=180.0, size=(40, MODULE, WALL_H), material=SOOT)
fixed("Forge.Pillar", b + "Pillar_01", loc=(0, 0, wall_z), size=(50, 50, WALL_H), material=SOOT)
fixed("Forge.Roof", b + "Roof", loc=(H, H, wall_z), collision=False, size=(MODULE, MODULE, MODULE))
fixed("Forge.RoofTrim", b + "RoofOverhang", loc=(H, H, wall_z), collision=False)
fixed("Forge.RoofEndL", b + "Roof_End_L", loc=(H, H, wall_z), collision=False)
fixed("Forge.RoofEndR", b + "Roof_End_R", loc=(H, -H, wall_z), collision=False)
fixed("Forge.GableNeg", HF + "Stone/SM_Wall_Tri_L", loc=(gable_out, 0, wall_z), yaw=180.0, collision=False, material=SOOT)
fixed("Forge.GablePos", HF + "Stone/SM_Wall_Tri_R", loc=(gable_out, 0, wall_z), yaw=180.0, collision=False, material=SOOT)
d = fixed("Forge.Door", HF + "Stone/SM_Reinforced_Door", loc=(0, 0, 114.0), yaw=180.0)
if d: d.hinge = V(-13.0, 54.0, 2.0); d.size = V(12, 107, 214)

# ---------------------------------------------------------------- the foundry (Dwarven Citadel's brick, 400 x 23 x 401 a wall)
DW = "/Game/DwarvenCitadel/Meshes/"
BW = dict(front="+y", mode="wallface", scale=(0.75, 1, 0.75))
piece("Foundry.Wall", DW + "SM_ST_BrickWall_05", **BW)
piece("Foundry.WallOut", DW + "SM_ST_MainHall_BrickWall_06", **BW)
piece("Foundry.Floor", DW + "SM_ST_FloorTile_04", front="+x", mode="floor", fit=(300, 300))
piece("Foundry.Ceil", DW + "SM_ST_FloorTile_01", front="+x", mode="ceil", fit=(300, 300))
piece("Foundry.Lamp", DW + "SM_PR_Chandelier_A", front="+x", scale=0.45, collision=False)
# (a chimney on each stack: Riverside's chimney top, 4.2 m, made 10 m)
piece("Foundry.Chimney", "/Game/BefourStudios/RiversideEuropeanVillage/Meshes/HouseKit/Deco/SM_ChimneyTop", front="+x", scale=2.4, collision=False)
# (the furnaces either side of the gate: House Forge's brick kiln, 1.4 x 1.4 x 2.0 m, made half again as big)
piece("Foundry.Furnace", HF + "Misc/SM_Forge", front="+x", scale=1.5)

# ---------------------------------------------------------------- the square: the great anvil, the open forges, carts, barricade
AN = "/Game/HouseForge_01/Viking_Village_Props/Meshes/Props/BlackSmith/Anvil/sm_Anvil_01a"
piece("Forge.Anvil", AN, front="+x")
piece("Forge.GreatAnvil", AN, front="+x", scale=3.2)
piece("Forge.Plinth", "/Game/DarkHalls/StaticMeshes/Props/SM_StatuePlinth", front="+x")
piece("Forge.OpenForge", "/Game/Castle/Furniture/Kit/SM_Kit_Forge", front="+x")
OM = "/Game/Scene_OldMine/Assets/Megascans/3D_Assets/"
piece("Forge.Cart", OM + "Ind_Min_Cart_Metal_Old_02/SM_Ind_Min_Cart_Metal_Old_02", front="+x")
piece("Forge.Rail", OM + "Ind_Min_Rail_Tracks_Wood_Modular_01/SM_Ind_Min_Rail_Tracks_Wood_Modular_01_A", front="+x", collision=False)
piece("Forge.Barricade", "/Game/WarCamp_Collection/Props/SM_Camp_Barricade/Meshes/FBX/SM_Camp_Barricade_Var3_SM_Barricade_Var3", front="+x")

FX = {"ChimneySmoke": "/Game/MERIDIAN/VOL31_14WidowSt/VFX/NS_Smoke_Chimney_01a", "ForgeSparks": "/Game/Dragon_graveyard/Fx/Sparks/NS_sparks"}

w = ues.get_editor_world()
if not w.get_path_name().startswith(MAP + "."): les.load_level(MAP)
g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
pieces = g.get_editor_property("pieces")
for k in [k for k in pieces.keys() if str(k).startswith(("Forge.", "Foundry."))]: pieces.pop(k)
# (the iron gate down into The War Engine: the dungeon's doorway, larger, as the cathedral's crypt arch)
dw = pieces.get("Doorway")
if dw:
    a = unreal.RDPiece(); a.mesh = dw.mesh; a.size = dw.size; a.collision = False
    a.adjust = unreal.Transform(dw.adjust.translation, dw.adjust.rotation.rotator(), V(1.0, 1.5, 1.5)); P["Foundry.Gate"] = a
for k, v in P.items(): pieces[k] = v
g.set_editor_property("pieces", pieces)
effects = g.get_editor_property("effects")
for k, path in FX.items():
    s = load(path)
    if s: effects[k] = s
g.set_editor_property("effects", effects)
td = g.get_editor_property("town_dungeons"); td[TOWN] = DUNGEON; g.set_editor_property("town_dungeons", td)
print("AR pieces:", len(P), "| effects:", [k for k in FX if k in effects], "| missing:", missing)

# ---------------------------------------------------------------- its people and quests (892's way)
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
print("AR", len(defs), "townsfolk of", len(D["townsfolk"]), "|", len(quests), "quests | kept", len(keep_f), "townsfolk and", len(keep_q), "quests of other towns | missing:", missing)
les.save_current_level()
print("AR saved", ues.get_editor_world().get_path_name())
import gc
del g, pieces, defs, quests, keep_f, keep_q, effects, td
gc.collect()
