"""mistward_castle: its items, traps, prisoners and switches (docs/improvements.txt, the user's of 2026-10-26; after 864).
- shields: the 22 fantasy shields of docs/objects.md with the user's table (SourceArt/mistward/shields.json: rank, damage
  reduction, speed, durability). Kind Shield: a blow takes damage x 4 % less, she is (10 - speed) x 3 % slower, the shield
  loses what it takes and breaks at 0 (the user's choice of 2026-10-26). Found in containers by rank (ranks 1-4 tier 5,
  5-8 tier 4, 9-13 tier 3, 14-17 tier 2, 18-22 tier 1). Only the Warrior carries one (her left forearm: a grip for each
  shield from her reference pose, as 862's shield, the shield turned so that its face looks out and its wide end is up,
  measured from the mesh: its thinnest axis, its longest, which end is wider, which side its middle bulges to). She starts
  with the Heater Shield (her level 5 shield) worn; her sword's own shield mesh is taken off the hero.
  The War Tower Shield is a skeletal mesh in its pack: a static copy is made (Geometry Script) in /Game/RandomDungeon/Mistward.
- the torch: an item made at the anvil (2 wood, 2 straw rope, 1 oils), held in the left hand by every hero (a grip for each
  from her reference pose: in her fist along her thumb, its head turned 20 degrees up), the dungeon's torch flame on its
  head and a light
- teleport rings: one for each tier 2-5, found on that tier's teleporter pad; the pad (MysticDungeon's mosaic ring), its
  effect and the teleport's (Medieval Weapons' NS_TeleportRing, Toon Explosions' circle)
- armour: kept set by set (several of one kind), broken down at the anvil by its type (the table's breakdown types)
- the Plate Knight's Sword: tier 2 only (it was tier 1)
- traps (the generator's Traps): pit, darts, deadfall, crusher, snare (mechanical), glyph, ward, emanation, cursed rune stone
  (magical: the spells' own effects), chain and lingering (complex), teleport; the Rogue finds and disarms them
- prisoners: the NPC Prisoners pack's ten (their own idle and walk), what a freed prisoner gives
- her things where she falls: Loot Drops Vol. 2's NS_LootDrop03_lvl5_yellow and a picture of each thing (a material made
  here: M_RD_LootIcon, unlit, see-through, its texture parameter Icon)
- the switches: the frame rate, the inventory walked by a held key, the anvil's alphabetical lists, containers that stay open, tidy furniture, shaped rooms, the
  75 % rule, the boss and the guarded ring at each tier's opening, dropping on death, teleporters
Args: none"""
import unreal, json, math, os
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ML = unreal.MathLibrary; V = unreal.Vector; APE = unreal.AnimPoseExtensions
MAP = "/Game/RandomDungeon/Maps/mistward_castle"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
OUT = SA + r"\mistward"
MW = "/Game/RandomDungeon/Mistward"
os.makedirs(OUT, exist_ok=True)
SH = json.load(open(OUT + r"\shields.json", encoding="utf-8"))
OBJ = {o["name"]: o for o in json.load(open(SA + r"\object_gallery\objects.json", encoding="utf-8"))["objects"]}
if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
items = [i for i in gen.get_editor_property("items") if i.kind not in (unreal.RDItemKind.SHIELD, unreal.RDItemKind.TORCH, unreal.RDItemKind.TELEPORT)]
heroes = list(gen.get_editor_property("heroes"))
KP = unreal.ProceduralMeshLibrary
def verts_of(m):
    vs = []
    for s in range(m.get_num_sections(0)):
        vs += [(v.x, v.y, v.z) for v in KP.get_section_from_static_mesh(m, 0, s)[0]]
    return vs
def hero_mesh(h):
    pawn = unreal.get_default_object(h.pawn_class)
    m = pawn.get_editor_property("mesh")
    return m.get_skeletal_mesh_asset() if hasattr(m, "get_skeletal_mesh_asset") else m.get_editor_property("skeletal_mesh")
def ref_bone(mesh, n):
    ref = APE.get_reference_pose(mesh.skeleton)
    return APE.get_bone_pose(ref, n, unreal.AnimPoseSpaces.WORLD)
# ---------------------------------------------------------------- a static copy of a skeletal shield
def static_copy(path, name):
    dst = f"{MW}/{name}"
    if eal.does_asset_exist(dst): return unreal.load_asset(dst)
    sk = unreal.load_asset(path)
    dm = unreal.DynamicMesh()
    o = unreal.GeometryScriptCopyMeshFromAssetOptions()
    lod = unreal.GeometryScriptMeshReadLOD()
    dm, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh(sk, dm, o, lod)
    no = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    no.set_editor_property("enable_nanite", False); no.set_editor_property("enable_collision", False)
    sm, outcome2 = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dm, dst, no)
    # (its materials, slot by slot as the skeletal mesh has them)
    mats = [s.material_interface for s in sk.materials]
    for i, mi in enumerate(mats):
        if i < len(sm.static_materials): sm.set_material(i, mi)
    eal.save_loaded_asset(sm, only_if_is_dirty=False)
    print("STATIC COPY", path, "->", dst, outcome, outcome2)
    return sm
# ---------------------------------------------------------------- a shield's own frame: its face out (+Y), its wide end up (+Z)
AX = {"x": V(1, 0, 0), "y": V(0, 1, 0), "z": V(0, 0, 1)}
def shield_frame(m, flip=False, turn=False):
    """mesh -> the shield's frame (the Heater Shield's, SM_Shield_1's own: its face toward +Y, its top +Z, centred)"""
    b = m.get_bounding_box(); vs = verts_of(m)
    mn = [b.min.x, b.min.y, b.min.z]; mx = [b.max.x, b.max.y, b.max.z]; size = [mx[i] - mn[i] for i in range(3)]
    thin = min(range(3), key=lambda i: size[i]); others = [i for i in range(3) if i != thin]
    up = max(others, key=lambda i: size[i]); side = [i for i in others if i != up][0]
    if turn: up, side = side, up
    lo, hi = mn[up], mx[up]
    def width(a, c): s = [v[side] for v in vs if a <= v[up] <= c]; return (max(s) - min(s)) if s else 0.0
    up_sign = 1.0 if width(hi - 0.2 * (hi - lo), hi) >= width(lo, lo + 0.2 * (hi - lo)) - 1.0 else -1.0
    cs, cu = (mn[side] + mx[side]) / 2, (lo + hi) / 2
    rad = lambda v: max(abs(v[side] - cs) / (size[side] / 2 + 1e-3), abs(v[up] - cu) / (size[up] / 2 + 1e-3))
    rim = [v[thin] for v in vs if rad(v) > 0.85]; mid = [v[thin] for v in vs if rad(v) < 0.3]
    # (its face bulges out: the middle stands in front of the rim)
    f_sign = 1.0 if (sum(mid) / max(len(mid), 1)) >= (sum(rim) / max(len(rim), 1)) else -1.0
    if flip: f_sign = -f_sign
    u = AX["xyz"[up]] * up_sign; f = AX["xyz"[thin]] * f_sign; s = f.cross(u)
    c2m = unreal.Transform(V(0, 0, 0), ML.make_rotation_from_axes(s, f, u), V(1, 1, 1))
    center = V((mn[0] + mx[0]) / 2, (mn[1] + mx[1]) / 2, (mn[2] + mx[2]) / 2)
    return ML.compose_transforms(unreal.Transform(center * -1.0, unreal.Rotator(0, 0, 0), V(1, 1, 1)), c2m.inverse()), size[thin]
# ---------------------------------------------------------------- the Warrior's forearm (862's shield grip, her reference pose)
WARRIOR = next(h for h in heroes if str(h.name) == "Warrior")
WMESH = hero_mesh(WARRIOR)
SHIELD_SCALE = 0.8
def arm_frame(depth):
    elbow = ref_bone(WMESH, "lowerarm_l"); hand = ref_bone(WMESH, "hand_l").translation
    fore = (hand - elbow.translation).normal(); back = V(0, 0, 1); back = (back - fore * back.dot(fore)).normal()
    # (the shield's middle out from the forearm by half its depth: a deep one does not sink into her arm)
    out = max(6.0, depth * SHIELD_SCALE * 0.5 + 2.0)
    w = unreal.Transform(elbow.translation + (hand - elbow.translation) * 0.55 + back * out, ML.make_rot_from_zy(fore * -1.0, back), V(SHIELD_SCALE, SHIELD_SCALE, SHIELD_SCALE))
    return w, elbow
RANK_TIER = lambda r: [5] if r <= 4 else [4] if r <= 8 else [3] if r <= 13 else [2] if r <= 17 else [1]
grips = {}
for s in SH["shields"]:
    o = OBJ[s["name"]]
    path = o["meshes"][0].split(".")[0]
    m = unreal.load_asset(path)
    if isinstance(m, unreal.SkeletalMesh): m = static_copy(path, "SM_" + s["name"].replace(" ", "").replace("'", "").replace("(", "").replace(")", "").replace("-", ""))
    frame, depth = shield_frame(m, s.get("flip", False), s.get("turn", False))
    w, elbow = arm_frame(depth)
    grip = ML.make_relative_transform(ML.compose_transforms(frame, w), elbow)
    it = unreal.RDItemDef()
    it.name = s["name"]; it.kind = unreal.RDItemKind.SHIELD
    # (the user's rules: 4 % of a blow per damage point, 3 % slower per speed point under 10; the item carries both)
    it.amount = s["damage"] * 0.04; it.slower = (10 - s["speed"]) * 0.03; it.durability = float(s["durability"])
    it.damage_rating = s["damage"]; it.speed_rating = s["speed"]
    it.tiers = RANK_TIER(s["rank"]); it.weight = float(SH["rarity"]); it.found_max = 1
    it.looks = o.get("looks", ""); it.icon = unreal.Name("mw_" + o["id"]); it.weapon_type = "shield " + s["material"]
    wd = unreal.RDWeaponDef(); wd.name = s["name"]; wd.off_hand_mesh = m; wd.off_hand_bone = "lowerarm_l"; wd.off_hand_grip = grip
    fit = unreal.RDWeaponFit(); fit.hero = "Warrior"; fit.weapon = wd
    it.weapon_fits = [fit]
    items.append(it)
    grips[s["name"]] = {"mesh": m.get_path_name(), "depth": round(depth, 1), "tiers": list(it.tiers)}
    print(f"SHIELD {s['rank']:2d} {s['name']:32s} {it.amount * 100:4.0f}% less  {it.slower * 100:4.0f}% slower  {it.durability:5.0f}  tier {list(it.tiers)}  {m.get_name()}")
# ---------------------------------------------------------------- the torch (held upright in her left fist, as a sword is in her right)
# (the pack's bare torch: SM_TorchHolded_01a is one in its wall bracket, whose plate stood out of her fist)
TORCH = "/Game/Medieval_Castle/CastleKit/Props/Meshes/Props/TorchKit/SM_Torch_01a"
TORCH_TILT = 20.0
tm = unreal.load_asset(TORCH); tb = tm.get_bounding_box(); tv = verts_of(tm)
tsz = [tb.max.x - tb.min.x, tb.max.y - tb.min.y, tb.max.z - tb.min.z]
long_ = max(range(3), key=lambda i: tsz[i]); tmn = [tb.min.x, tb.min.y, tb.min.z][long_]; tmx = [tb.max.x, tb.max.y, tb.max.z][long_]
def twidth(a, c):
    o_ = [i for i in range(3) if i != long_]; s_ = [v for v in tv if a <= v[long_] <= c]
    return max((max(v[k] for v in s_) - min(v[k] for v in s_)) for k in o_) if s_ else 0.0
head_up = twidth(tmx - 0.2 * (tmx - tmn), tmx) >= twidth(tmn, tmn + 0.2 * (tmx - tmn))
head = tmx if head_up else tmn; foot = tmn if head_up else tmx
TORCH_FRAME_AX = AX["xyz"[long_]] * (1.0 if head_up else -1.0)
mid_other = [((tb.min.x + tb.max.x) / 2, (tb.min.y + tb.max.y) / 2, (tb.min.z + tb.max.z) / 2)[i] for i in range(3)]
head_pt = list(mid_other); head_pt[long_] = head; head_pt = V(*head_pt)
grip_pt = list(mid_other); grip_pt[long_] = foot + (head - foot) * 0.22; grip_pt = V(*grip_pt)
def torch_grip(mesh):
    """her left hand's fist round the torch's handle a fifth of the way up, the torch along her thumb turned TORCH_TILT degrees
    toward her elbow (862's weapon_grip, left): with her arm hanging its head is up and forward, not straight ahead at her hip"""
    hand = ref_bone(mesh, "hand_l"); fore = (hand.translation - ref_bone(mesh, "lowerarm_l").translation).normal()
    thumb = V(0, 1, 0); thumb = (thumb - fore * thumb.dot(fore)).normal()
    palm = hand.translation + fore * 6.5 + V(0, 0, -2.5)
    head = (thumb * math.cos(math.radians(TORCH_TILT)) - fore * math.sin(math.radians(TORCH_TILT))).normal()
    rot = ML.make_rot_from_zx(head, fore)
    # (the torch's frame: its long axis +Z, its handle point at the origin)
    other = [k for k in "xyz" if k != "xyz"[long_]][0]
    t2 = unreal.Transform(V(0, 0, 0), ML.make_rot_from_zx(TORCH_FRAME_AX, AX[other]), V(1, 1, 1)).inverse()
    frame = ML.compose_transforms(unreal.Transform(grip_pt * -1.0, unreal.Rotator(0, 0, 0), V(1, 1, 1)), t2)
    w = unreal.Transform(palm, rot, V(1, 1, 1))
    return ML.make_relative_transform(ML.compose_transforms(frame, w), hand)
torch = unreal.RDItemDef(); torch.name = "Torch"; torch.kind = unreal.RDItemKind.TORCH; torch.weight = 0.0; torch.found_max = 1
torch.icon = unreal.Name("mw_torch"); torch.looks = "a pitch torch for the left hand"; torch.weapon_type = "torch"
fits = []
for h in heroes:
    try: mesh = hero_mesh(h)
    except Exception: continue
    if mesh is None or mesh.skeleton is None: continue
    wd = unreal.RDWeaponDef(); wd.name = "Torch"; wd.off_hand_mesh = tm; wd.off_hand_bone = "hand_l"; wd.off_hand_grip = torch_grip(mesh)
    f = unreal.RDWeaponFit(); f.hero = h.name; f.weapon = wd; fits.append(f)
torch.weapon_fits = fits
items.append(torch)
gen.set_editor_property("torch_flame", head_pt)
effects = gen.get_editor_property("effects")
gen.set_editor_property("torch_fx", effects.get(unreal.Name("TorchFire")))
gen.set_editor_property("torch_fx_scale", 0.45); gen.set_editor_property("torch_light", 80.0)
recipes = [r for r in gen.get_editor_property("recipes") if str(r.item) != "Torch"]
def part(label, kinds, n):
    p = unreal.RDRecipePart(); p.label = label; p.any_of = kinds; p.count = n; return p
rc = unreal.RDRecipe(); rc.item = "Torch"
rc.parts = [part("wood (any)", ["Hardwood", "Timber", "Wood Log"], 2), part("straw rope", ["Straw Rope"], 2), part("oils", ["Oils"], 1)]
recipes.append(rc)
gen.set_editor_property("recipes", recipes)
print("TORCH", tm.get_name(), "long axis", "xyz"[long_], "head", "up" if head_up else "down", "fits", [str(f.hero) for f in fits], "flame at", head_pt)
# ---------------------------------------------------------------- teleport rings (one a tier, on its pad)
ROMAN = {2: "II", 3: "III", 4: "IV", 5: "V"}
ring_icon = next((i.icon for i in items if i.kind == unreal.RDItemKind.RING), unreal.Name("None"))
for t in (2, 3, 4, 5):
    r = unreal.RDItemDef(); r.name = f"Teleport Ring {ROMAN[t]}"; r.kind = unreal.RDItemKind.TELEPORT; r.teleport_tier = t
    r.weight = 0.0; r.icon = ring_icon; r.looks = f"the ring of tier {t}'s teleporter"; items.append(r)
gen.set_editor_property("teleporters", True)
gen.set_editor_property("pad_mesh", unreal.load_asset("/Game/MysticDungeon/Meshes/Floor/SM_floor_Ring_Mosaic_A"))
pb = unreal.load_asset("/Game/MysticDungeon/Meshes/Floor/SM_floor_Ring_Mosaic_A").get_bounding_box()
pk = 240.0 / max(pb.max.x - pb.min.x, pb.max.y - pb.min.y)
gen.set_editor_property("pad_transform", unreal.Transform(V(-(pb.min.x + pb.max.x) / 2 * pk, -(pb.min.y + pb.max.y) / 2 * pk, -pb.min.z * pk + 1.0), unreal.Rotator(0, 0, 0), V(pk, pk, pk)))
gen.set_editor_property("pad_fx", unreal.load_asset("/Game/Medieval_Weapons/VFX/NS_TeleportRing")); gen.set_editor_property("pad_fx_scale", 1.6)
gen.set_editor_property("teleport_fx", unreal.load_asset("/Game/ToonExplosionVol1/Particles/NiagaraSystems/NS_ExplosionsCircle_03"))
gen.set_editor_property("teleport_ring_mesh", unreal.load_asset("/Game/StylizedShieldsVol1/Models/SM_Ring_01"))
# ---------------------------------------------------------------- armour: several of a kind, broken down by type; the shields' and the torch's materials
for i in items:
    if i.kind == unreal.RDItemKind.ARMOUR: i.weapon_type = str(i.armour_type).lower()
    # (the Plate Knight's Sword: tier 2, the user's)
    if i.kind == unreal.RDItemKind.WEAPON and str(i.name) == "Plate Knight's Sword": i.tiers = [2]
bds = [b for b in gen.get_editor_property("breakdowns") if not any(str(t).startswith(("shield", "armour:")) or str(t) in SH["armour_breakdown"] for t in b.types)]
for types, gives in [([k], v) for k, v in SH["armour_breakdown"].items() if not k.startswith("_")] + [(["shield metal"], SH["shield_breakdown"]["metal"]), (["shield wood"], SH["shield_breakdown"]["wood"])]:
    b = unreal.RDBreakdown(); b.types = types; b.gives = list(gives.keys()); b.per_tier = list(gives.values()); bds.append(b)
gen.set_editor_property("breakdowns", bds)
gen.set_editor_property("armour_stacks", True)
gen.set_editor_property("items", items)
# ---------------------------------------------------------------- the Warrior: her shield is an item now (worn when play begins)
hs = []
for h in heroes:
    h2 = unreal.RDHeroDef(); h2.import_text(h.export_text())
    if str(h2.name) == "Warrior":
        ws = []
        for wd in h2.weapons:
            if str(wd.name) == "Sword": wd.off_hand_mesh = None
            ws.append(wd)
        h2.weapons = ws
    hs.append(h2)
gen.set_editor_property("heroes", hs)
gen.set_editor_property("start_shield", {unreal.Name("Warrior"): unreal.Name(SH["start_shield"])})
# ---------------------------------------------------------------- traps (their effects: the spells' own and the packs')
spells = {}
for s in gen.get_editor_property("spells"): spells.setdefault(s.kind.name.lower(), s)
def sfx(kind, field):
    s = spells.get(kind)
    return s.get_editor_property(field) if s else None
L = unreal.load_asset
PLATE = L("/Game/MysticDungeon/Meshes/Floor/SM_Floor_Stone_Square_Tiles_A")
pbx = PLATE.get_bounding_box(); pks = 110.0 / max(pbx.max.x - pbx.min.x, 1)
PLATE_XF = unreal.Transform(V(-(pbx.min.x + pbx.max.x) / 2 * pks, -(pbx.min.y + pbx.max.y) / 2 * pks, -pbx.max.z * 0.3 + 1.5), unreal.Rotator(0, 0, 0), V(pks, pks, 0.3))
ARROW = L("/Game/Medieval_Weapons/Meshes/VOL2/Ranged/SM_ProjectileArrowMesh")
ROCK = L("/Game/Medieval_Castle/CastleKit/Props/Meshes/Rocks/SM_RockStoneWall_01a")
BLOCK = L("/Game/Medieval_Castle/CastleKit/Walls_Stone/SM_Castle_Stone_Pillar_01a_NN")
RUNE = L("/Game/Relics/VOL2_ForgottenRelics/Meshes/LP/SM_Rune_01a")
CHAIN = L("/Game/MysticDungeon/Meshes/Chain/SM_Chain_Line_c") or None
DUST = L("/Game/ToonExplosionVol1/Particles/NiagaraSystems/NS_ExplosionsCircle_01")
def td(name, kind, label, magic, dmg, radius, secs, tier, w, mesh=None, mxf=None, missile=None, misxf=None, idle=None, trig=None, hit=None, isc=1.0, tsc=1.0, hsc=1.0, color=(1, .4, .1)):
    d = unreal.RDTrapDef()
    d.name = name; d.kind = kind; d.label = label; d.magic = magic; d.damage = dmg; d.radius = radius; d.seconds = secs; d.min_tier = tier; d.weight = w
    if mesh: d.mesh = mesh; d.mesh_transform = mxf or unreal.Transform()
    if missile: d.missile = missile; d.missile_transform = misxf or unreal.Transform()
    d.idle_fx = idle; d.trigger_fx = trig; d.hit_fx = hit; d.idle_fx_scale = isc; d.trigger_fx_scale = tsc; d.hit_fx_scale = hsc
    d.color = unreal.LinearColor(*color, 1.0)
    return d
K = unreal.RDTrapKind
traps = [
    td("Pit", K.PIT, "pit trap", False, 0.14, 80, 1.6, 1, 1.0, PLATE, PLATE_XF, hit=DUST, tsc=0.6, hsc=0.6),
    td("Darts", K.MISSILES, "dart trap", False, 0.15, 90, 0, 1, 1.0, PLATE, PLATE_XF, ARROW, unreal.Transform(V(0, 0, 0), unreal.Rotator(0, 0, 0), V(1.2, 1.2, 1.2))),
    td("Deadfall", K.DEADFALL, "deadfall", False, 0.2, 85, 0, 1, 1.0, PLATE, PLATE_XF, ROCK, unreal.Transform(V(0, 0, 0), unreal.Rotator(0, 0, 0), V(0.28, 0.28, 0.28)), hit=DUST, hsc=0.5),
    td("Crusher", K.CRUSHER, "crusher", False, 0.3, 110, 0, 2, 0.8, PLATE, PLATE_XF, BLOCK, unreal.Transform(V(0, 0, 0), unreal.Rotator(0, 0, 0), V(2.4, 2.4, 0.45)), hit=DUST, hsc=0.8),
    td("Snare", K.SNARE, "snare", False, 0.05, 75, 2.5, 1, 1.0, CHAIN, unreal.Transform(V(0, 0, 3), unreal.Rotator(roll=0, pitch=90, yaw=0), V(0.6, 0.6, 0.6)) if CHAIN else None),
    td("Glyph", K.GLYPH, "glyph of fire", True, 0.22, 90, 0, 1, 1.0, idle=sfx("rune", "area_fx"), trig=None, hit=sfx("nova", "impact_fx") or sfx("bolt", "impact_fx"), isc=0.6, hsc=1.0, color=(1, .35, .1)),
    td("Ward", K.WARD, "warding barrier", True, 0.12, 100, 0, 2, 0.7, idle=sfx("ward", "shield_fx"), hit=sfx("bolt", "impact_fx"), isc=1.2, hsc=0.7, color=(.4, .6, 1)),
    td("Emanation", K.EMANATION, "poison emanation", True, 0.5, 100, 6.0, 2, 0.8, hit=sfx("cloud", "area_fx"), hsc=1.0, color=(.4, 1, .3)),
    td("Cursed", K.CURSED, "cursed rune stone", True, 0.06, 90, 0, 1, 0.7, RUNE, unreal.Transform(V(0, 0, 0), unreal.Rotator(0, 0, 0), V(1, 1, 1)), hit=sfx("curse", "impact_fx") or sfx("curse", "area_fx"), hsc=1.0, color=(.6, .2, 1)),
    td("Chain", K.CHAIN, "chain of traps", False, 0.2, 90, 0, 3, 0.6, PLATE, PLATE_XF, ROCK, unreal.Transform(V(0, 0, 0), unreal.Rotator(0, 0, 0), V(0.25, 0.25, 0.25)), hit=sfx("nova", "impact_fx") or DUST),
    td("Lingering", K.LINGERING, "lingering trap", True, 0.18, 110, 0, 3, 0.6, PLATE, PLATE_XF, ARROW, unreal.Transform(V(0, 0, 0), unreal.Rotator(0, 0, 0), V(1.2, 1.2, 1.2)), hit=sfx("pillar", "impact_fx") or sfx("bolt", "impact_fx")),
    td("Teleport", K.TELEPORT, "teleport trap", True, 0.0, 85, 0, 2, 0.6, idle=sfx("rift", "area_fx"), trig=L("/Game/Medieval_Weapons/VFX/NS_TeleportRing"), isc=0.5, tsc=1.4, color=(.5, .3, 1)),
]
gen.set_editor_property("traps", traps)
gen.set_editor_property("trap_finders", ["Rogue"])
gen.set_editor_property("trap_room_share", 0.3); gen.set_editor_property("trap_hall_share", 0.12)
print("TRAPS", [(str(t.name), t.mesh.get_name() if t.mesh else None, t.idle_fx.get_name() if t.idle_fx else None, t.hit_fx.get_name() if t.hit_fx else None) for t in traps])
# ---------------------------------------------------------------- prisoners (the NPC Prisoners pack: its UE4 mannequin meshes, its own idle and walk)
PR = "/Game/Prisoners/Mesh/Mesh_UE4/Full/"
IDLE = L("/Game/Prisoners/Demoscene_UE4/Animations/ThirdPersonIdle") or None
WALK = L("/Game/Prisoners/Demoscene_UE4/Animations/ThirdPersonWalk") or None
if IDLE is None or WALK is None:
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    for ad in ar.get_assets_by_path("/Game/Prisoners", recursive=True):
        if str(ad.asset_name) == "ThirdPersonIdle": IDLE = L(str(ad.package_name))
        if str(ad.asset_name) == "ThirdPersonWalk": WALK = L(str(ad.package_name))
defs = []
for sex, word in (("Man", "man"), ("Wom", "woman")):
    for i in range(1, 6):
        m = L(f"{PR}{'Man' if sex == 'Man' else 'Woman'}/SK_UE4_Prisoners_{sex}_0{i}_Full_01")
        if not m: continue
        d = unreal.RDPrisonerDef(); d.name = f"Prisoner_{sex}_{i}"; d.mesh = m; d.idle = IDLE; d.walk = WALK; d.thanks = IDLE
        d.mesh_z = 0.0; d.mesh_yaw = -90.0; d.walk_speed = 140.0; d.walk_clip_speed = 150.0; d.title = f"prisoner"
        defs.append(d)
gen.set_editor_property("prisoner_defs", defs)
REW = [str(i.name) for i in items if i.kind in (unreal.RDItemKind.HEALING, unreal.RDItemKind.MANA, unreal.RDItemKind.FOOD, unreal.RDItemKind.REPAIR, unreal.RDItemKind.SPEED)]
gen.set_editor_property("prisoner_rewards", REW)
gen.set_editor_property("cell_occupied", 0.6); gen.set_editor_property("cell_monster_share", 0.35)
print("PRISONERS", len(defs), "idle", IDLE.get_name() if IDLE else None, "walk", WALK.get_name() if WALK else None, "| rewards", len(REW))
# ---------------------------------------------------------------- her things where she falls: the effect, the pictures' material
gen.set_editor_property("loot_pile_fx", L("/Game/LootDropsV2/Particles/NiagaraSystems/LootDrop03/NS_LootDrop03_lvl5_yellow"))
gen.set_editor_property("loot_pile_fx_scale", 1.0)
MAT = f"{MW}/M_RD_LootIcon"
if not eal.does_asset_exist(MAT):
    mat = at.create_asset("M_RD_LootIcon", MW, unreal.Material, unreal.MaterialFactoryNew())
    MEL = unreal.MaterialEditingLibrary
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)
    tex = MEL.create_material_expression(mat, unreal.MaterialExpressionTextureSampleParameter2D, -400, 0)
    tex.set_editor_property("parameter_name", "Icon")
    tex.set_editor_property("texture", L("/Engine/EngineResources/WhiteSquareTexture"))
    MEL.connect_material_property(tex, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(tex, "A", unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(mat); eal.save_loaded_asset(mat, only_if_is_dirty=False)
gen.set_editor_property("icon_material", L(MAT))
# ---------------------------------------------------------------- the switches
for k, v in (("show_fps", True), ("alphabetical_crafting", True), ("key_repeat", True), ("containers_stay_open", True), ("tidy_furniture", True), ("shaped_rooms", True),
             ("shaped_room_share", 0.6), ("tier_open_share", 0.75), ("drop_on_death", True), ("ring_guards", True), ("guard_count", 4),
             ("boss_encounters", True), ("boss_minions", unreal.IntPoint(3, 6)), ("boss_health", 3.0), ("boss_damage", 1.6), ("boss_scale", 1.35)):
    gen.set_editor_property(k, v)
# (the start section again, under the castle's own rules (tidy furniture, its cells): its furniture is saved with the map, and
# the copy of level 5 had it as level 5 built it)
gen.modify(); gen.build_start_section()
les.save_current_level()
json.dump(grips, open(OUT + r"\shield_grips.json", "w"), indent=1)
print("MISTWARD items", len(items), "| shields", sum(1 for i in items if i.kind == unreal.RDItemKind.SHIELD), "| breakdowns", len(bds), "| recipes", [str(r.item) for r in recipes])
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
