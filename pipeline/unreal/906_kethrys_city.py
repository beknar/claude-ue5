"""Kethrys Spire, the mage city (the user's list of 2026-11-08b, docs/improvements9.txt, its fourth phase: "a mage-city
clustered around a black tower that hasn't opened its gates in a century. there are magical effects, laboratories, libraries,
stone houses. this city is not poor"): one of the wilderness's towns on the brokenspire level, planned as a mage city (C++: the
generator's TownPlan 4 for the town FRDWildWorld places north-west of Graymourne; RDTownPlan.cpp's bMage, RDMage.cpp's black
tower). This script gives the brokenspire level's generator what that plan builds with and who lives there:
- the city's houses of well-kept grey-blue stone ("Mage.*": House Forge's stone set in a cooled copy of its own stone, made
  here: /Game/RandomDungeon/Materials/Mage/MI_Mage_Stone; their roofs and doors their own)
- the black tower's pieces ("Spire.*": the town castle's wall, floor and ceiling in a black copy of the same stone
  (MI_Spire_Black); Castle of Eternal Mist's round tower with windows, its crown and its cap, made 2.2 times as big; the
  sealed gate, the dungeon's doorway larger)
- the mage city's things ("Mage.*": a rune stone (Relics), a plinth (Dark Halls) with an ice crystal on it (Alien Planet),
  a cauldron (CauldronFX), a laboratory's table (the castle kit's), potions (Crownfall))
- the effects "MageWard" (Mystic Dungeon's passage), "MageRune" (Particle Rings' first), "MageCrystal" (Character Body FX's
  light orbs), "MageMist" (Frozen Norse's mist), "MageBeam" (Mystic Dungeon's light ray), "CauldronFx" (Liquid Surface's
  magic potion)
- the tower's dungeon's level for the town (TownDungeons["Kethrys Spire"]: kethrys_spire, 907)
- its people and quests from SourceArt/kethrys/city.json: townsfolk and quests of the town "Kethrys Spire" (those of another
  run of this script replaced; the other towns' kept)
Run after 882 / 886 / 890 / 892 / 894 / 896 (882 rewrites the "Town." pieces and keeps these). C++ first (build_cpp.ps1).
Args: none"""
import os, json, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); eal = unreal.EditorAssetLibrary
V = unreal.Vector
MAP = "/Game/RandomDungeon/Maps/brokenspire"
DUNGEON = "/Game/RandomDungeon/Maps/kethrys_spire"
SA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "claude_ue5", "SourceArt", "kethrys"))
D = json.load(open(os.path.join(SA, "city.json"), encoding="utf-8"))
TOWN = D["town"]
MODULE, WALL_H = 300.0, 300.0
H = MODULE / 2
YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
missing = []
P = {}


def load(p):
    m = unreal.load_asset(p)
    if m is None: missing.append(p)
    return m


def corners(b): return [V(x, y, z) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]


def piece(key, path, front="+x", mode="center", scale=(1, 1, 1), collision=True, material=None):
    """894's normalisation: center: XY centred, bottom z 0; raw: rotation only"""
    m = load(path)
    if m is None: return None
    if isinstance(scale, (int, float)): scale = (scale,) * 3
    rot = unreal.Rotator(roll=0.0, pitch=0.0, yaw=YAW[front])
    t0 = unreal.Transform(V(0, 0, 0), rot, V(*scale))
    pts = [unreal.MathLibrary.transform_location(t0, c) for c in corners(m.get_bounding_box())]
    mn = V(min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)); mx = V(max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
    tx, ty, tz = -(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z
    if mode == "raw": tx = ty = tz = 0.0
    p = unreal.RDPiece(); p.mesh = m
    p.adjust = unreal.Transform(V(tx, ty, tz), rot, V(*scale))
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


def tint(name, rgb, desat, dirt):
    """a copy of House Forge's stone (MI_Rocks' child) tinted, as 894's soot stone"""
    MD = "/Game/RandomDungeon/Materials/Mage"; path = MD + "/" + name
    if not eal.does_asset_exist(path):
        unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MD, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi = unreal.load_asset(path); MEL = unreal.MaterialEditingLibrary
    MEL.set_material_instance_parent(mi, unreal.load_asset("/Game/HouseForge_01/Materials/Stone/MI_Rocks"))
    MEL.set_material_instance_vector_parameter_value(mi, "Base Color -Tint", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    MEL.set_material_instance_scalar_parameter_value(mi, "Desaturation", desat)
    MEL.set_material_instance_scalar_parameter_value(mi, "Dirt - Amount", dirt)
    MEL.update_material_instance(mi); eal.save_loaded_asset(mi, False)
    return mi


STONE = tint("MI_Mage_Stone", (0.86, 0.9, 1.0), 0.25, 0.15)          # (well kept: little dirt, a cool grey-blue)
BLACK = tint("MI_Spire_Black", (0.13, 0.12, 0.17), 0.6, 0.6)        # (the black tower)

# ---------------------------------------------------------------- the houses: House Forge's stone set in the cool stone
HF = "/Game/HouseForge_01/Meshes/"
b = HF + "Stone/SM_Stone_"; wall_z, gable_out = 0.0, 19.0
fl = load(b + "Foundation")
fixed("Mage.Floor", b + "Foundation", loc=(H, H, -fl.get_bounding_box().max.z + 2.0), size=(MODULE, MODULE, 30), material=STONE)
for k, n in {"Wall": "Wall", "WallWindow": "WallWindow", "WallWindow2": "WallWindow_Arc", "Doorway": "Doorway"}.items():
    fixed(f"Mage.{k}", b + n, loc=(0, -H, wall_z), yaw=180.0, size=(40, MODULE, WALL_H), material=STONE)
fixed("Mage.Pillar", b + "Pillar_01", loc=(0, 0, wall_z), size=(50, 50, WALL_H), material=STONE)
fixed("Mage.Roof", b + "Roof", loc=(H, H, wall_z), collision=False, size=(MODULE, MODULE, MODULE))
fixed("Mage.RoofTrim", b + "RoofOverhang", loc=(H, H, wall_z), collision=False)
fixed("Mage.RoofEndL", b + "Roof_End_L", loc=(H, H, wall_z), collision=False)
fixed("Mage.RoofEndR", b + "Roof_End_R", loc=(H, -H, wall_z), collision=False)
fixed("Mage.GableNeg", HF + "Stone/SM_Wall_Tri_L", loc=(gable_out, 0, wall_z), yaw=180.0, collision=False, material=STONE)
fixed("Mage.GablePos", HF + "Stone/SM_Wall_Tri_R", loc=(gable_out, 0, wall_z), yaw=180.0, collision=False, material=STONE)
d = fixed("Mage.Door", HF + "Stone/SM_Reinforced_Door", loc=(0, 0, 114.0), yaw=180.0)
if d: d.hinge = V(-13.0, 54.0, 2.0); d.size = V(12, 107, 214)

# ---------------------------------------------------------------- the black tower
TW = "/Game/CastleofEternalMist/Meshes/Tower/"
piece("Spire.Ring", TW + "SM_TowerRound_Window_8m_A", scale=2.2, material=BLACK)
piece("Spire.RingTop", TW + "SM_TowerRound_Border_Top_A", scale=2.2, collision=False, material=BLACK)
piece("Spire.Cap", TW + "SM_TowerRound_Cap_4m_A", scale=2.2, collision=False, material=BLACK)

# ---------------------------------------------------------------- the mage city's things
piece("Mage.RuneStone", "/Game/Relics/VOL2_ForgottenRelics/Meshes/LP/SM_Rune_01a")
piece("Mage.Plinth", "/Game/DarkHalls/StaticMeshes/Props/SM_StatuePlinth", scale=0.5)
piece("Mage.Crystal", "/Game/AlienPlanet/Meshes/Foliage/SM_IceCrystal01", scale=1.6, collision=False)
piece("Mage.Cauldron", "/Game/CauldronFX_VDB/Meshes/SM_Cauldron")
piece("Mage.LabTable", "/Game/Castle/Furniture/Kit/SM_Kit_PrepTable", front="+y")
piece("Mage.Potion", "/Game/Crownfall/Assets/SmallAssets/SM_S_Potion", collision=False)

FX = {"MageWard": "/Game/MysticDungeon/VFX/NS_PassageFX_01", "MageRune": "/Game/ParticleRings/FX/NS_ParticleRing_01",
      "MageCrystal": "/Game/CharacterBodyFX/FX/LightOrbs/NS_LightOrbs", "MageMist": "/Game/FrozenNorseEnvironment/Particles/NS_Mist01",
      "MageBeam": "/Game/MysticDungeon/VFX/NS_LightRayFX_01", "CauldronFx": "/Game/LiquidSurfaceFX/FX/NS_MagicPotion"}

w = ues.get_editor_world()
if not w.get_path_name().startswith(MAP + "."): les.load_level(MAP)
g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
pieces = g.get_editor_property("pieces")
for k in [k for k in pieces.keys() if str(k).startswith(("Mage.", "Spire."))]: pieces.pop(k)
# (the tower's hall: the town castle's own wall, floor and ceiling (its Castle theme's) in the black stone; the gate the
# dungeon's doorway larger, as the foundry's)
for src, dst in (("Castle.Wall_Block", "Spire.Wall"), ("Castle.Wall_Block", "Spire.WallOut"), ("Castle.Floor_Stone", "Spire.Floor"), ("Castle.Ceil_Room", "Spire.Ceil")):
    s = pieces.get(unreal.Name(src))
    if not s: missing.append(src); continue
    a = unreal.RDPiece(); a.mesh = s.mesh; a.adjust = s.adjust; a.size = s.size; a.collision = s.collision; a.material = BLACK
    P[dst] = a
dw = pieces.get(unreal.Name("Doorway"))
if dw:
    a = unreal.RDPiece(); a.mesh = dw.mesh; a.size = dw.size; a.collision = False; a.material = BLACK
    a.adjust = unreal.Transform(dw.adjust.translation, dw.adjust.rotation.rotator(), V(1.0, 1.5, 1.5)); P["Spire.Gate"] = a
for k, v in P.items(): pieces[k] = v
g.set_editor_property("pieces", pieces)
effects = g.get_editor_property("effects")
for k, path in FX.items():
    s = load(path)
    if s: effects[k] = s
g.set_editor_property("effects", effects)
td = g.get_editor_property("town_dungeons"); td[TOWN] = DUNGEON; g.set_editor_property("town_dungeons", td)
print("KS pieces:", len(P), "| effects:", [k for k in FX if k in effects], "| missing:", missing)

# ---------------------------------------------------------------- its people and quests (894's way)
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
                 ("mesh", mesh), ("idle", idle), ("walk", walk), ("walk_clip_speed", speed), ("walk_speed", 120.0),
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
print("KS", len(defs), "townsfolk of", len(D["townsfolk"]), "|", len(quests), "quests | kept", len(keep_f), "townsfolk and", len(keep_q), "quests of other towns | missing:", missing)
les.save_current_level()
print("KS saved", ues.get_editor_world().get_path_name())
import gc
del g, pieces, defs, quests, keep_f, keep_q, effects, td
gc.collect()
