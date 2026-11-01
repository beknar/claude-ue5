"""The Summoner (ai models/Summoner4.glb; the user's list of 2026-10-30, docs/improvements3.txt), mistward_castle's sixth hero.
Run after blender_numpy/tripo_build.py with summoner4_clips.py into SourceArt/jrpg_summoner4 and 600 / 610 / 615 / 620 for
Summoner4 (her mesh, her clips, her AnimBP, BP_JRPGSummoner4Character), and after 875; 819 after this (her walk / run),
826 mistward (the menu), 877 (her pictures).
- the list's capabilities: she knows only two spells of the table, Fire Bolt and Dark Fire, with the Mage's damage and
  effects (the Mage's spell weapons, cast with her own CastBolt clip); half the Mage's mana (50, a second back: 1); she
  wields only daggers (the weapons table's short blades, a knife in each hand with rogue_clips' stabs on her rig, as the
  Martial Artist does), which are never enchanted (she is not among the generator's SlashHeroes); she uses the Mage's
  equipment: no armour, Magic rings, the torch, potions; she learns no tome (the list: "can only know 2 spells") and reads
  every scroll (the list's table)
- her summons (spells of kind Summon, numbers 201-205; mana half her pool: ManaShare 0.5): Summon Tier 1 (the Soldier, 2 at
  a time) from the start; Tier 2 (the Gunner, 3), Tier 3 (Orc 05, 4), Tier 4 (Alien Warrior 05, 5), Tier 5 (the Spider, 5)
  her hero's LockedWeapons, one for each tier's boss she slays (UnlockPerBoss 1); each cast with its own clip
  (summoner4_clips.py's Summon1-5, the list: "each tier has different spell casting motions"); the one summoned is as
  strong as a monster of its own tier and stays until it falls
- her flinch: her own Hit_to_body_01; her death: Animations_Warrior's Dead_1 retargeted onto her rig (as 872's)
- BP_SU4_SummonerCharacter (a child of BP_JRPGSummoner4Character, a 30 cm capsule)
- the torch's fit for her hand (865's grip, from her reference pose)
Replaces the hero named Summoner (level 5's Summoner3) on mistward_castle and saves it. Args: none"""
import json, math, os, unreal
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions; ML = unreal.MathLibrary
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V = unreal.Vector
CH = "Summoner4"; HERO = "Summoner"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
SRC = os.path.join(SA, "jrpg_summoner4")
TIMES = json.load(open(os.path.join(SRC, "s4_times.json"))); RTIMES = json.load(open(os.path.join(SRC, "times.json")))
WT = json.load(open(os.path.join(SA, "random_dungeon_magic5", "weapons_table.json"), encoding="utf-8"))
FR = json.load(open(os.path.join(SA, "random_dungeon_magic5", "weapon_frames.json"), encoding="utf-8"))["weapons"]
HV = json.load(open(os.path.join(SA, "mistward", "harvest.json"), encoding="utf-8"))
MAP = "/Game/RandomDungeon/Maps/mistward_castle"
RIGS = "/Game/RandomDungeon/Summoner4/Rigs"; ANIMS = "/Game/RandomDungeon/Summoner4/Anims"
tgt_mesh = unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{CH}"); tgt_rig = unreal.load_asset(f"/Game/JRPG/Rigs/IK_JRPG_{CH}_Auto")
assert tgt_mesh and tgt_rig, "run 600-620 for Summoner4 first"
DAGGER, DAGGER_Z = "/Game/Medieval_Weapons/Meshes/VOL2/SM_Dagger", 28.5
# (her card: SourceArt/mistward/summoner4.json; the list: Tier 1 the Soldier, 2 at a time; 2 the Gunner, 3; 3 Orc 05, 4; 4 Alien
# Warrior 05, 5; 5 the Spider, 5)
CARD = json.load(open(os.path.join(SA, "mistward", "summoner4.json"), encoding="utf-8"))
SUMMONS = [tuple(x) for x in CARD["summons"]]
MANA, MANA_PER_SECOND, HEALTH = float(CARD["mana"]), float(CARD["mana_per_second"]), float(CARD["health"])          # (half the Mage's 100 and 2; her old card's hit points)
SCROLL_TYPES = [unreal.RDSpellType.OFFENSE, unreal.RDSpellType.PROTECTION, unreal.RDSpellType.CURSE, unreal.RDSpellType.SUMMON]


def make(cls, fac, name, folder):
    p = f"{folder}/{name}"
    if eal.does_asset_exist(p): eal.delete_asset(p)
    return at.create_asset(name, folder, cls, fac) or unreal.load_asset(p)


def clip(n):
    p = f"/Game/JRPG/{CH}Anims/AS_{CH}_{n}"; a = unreal.load_asset(p); assert a, p
    a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
    return a


# ---- her death (822's source rig, as 872's)
src_mesh = unreal.load_asset("/Game/Animations_Warrior/Mesh/SK_Mannequin"); assert src_mesh
src_rig = unreal.load_asset("/Game/RandomDungeon/Magic3/Rigs/IK_RDM3_Warrior_Source"); assert src_rig, "822 first (its source rig)"
rtg = make(unreal.IKRetargeter, unreal.IKRetargetFactory(), f"RTG_SU4_Warrior_To_{CH}", RIGS)
rc = unreal.IKRetargeterController.get_controller(rtg)
rc.add_default_ops()
rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
rc.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, src_mesh); rc.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, tgt_mesh)
rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
rm = rc.get_op_controller(rc.get_index_of_op_by_name("Root Motion"))
rm.set_source_root_bone("root"); rm.set_target_root_bone("root"); rm.set_target_pelvis_bone("pelvis")
try: rc.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
except Exception as e: print("SU4 align", e)
eal.save_loaded_asset(rtg)
ar = unreal.AssetRegistryHelpers.get_asset_registry()
dead = next(a for a in ar.get_assets_by_path("/Game/Animations_Warrior", recursive=True) if str(a.asset_name) == "Anim_Warrior_Dead_1" and str(a.asset_class_path.asset_name) == "AnimSequence")
if eal.does_asset_exist(f"{ANIMS}/Anim_Warrior_Dead_1_{CH}"): eal.delete_asset(f"{ANIMS}/Anim_Warrior_Dead_1_{CH}")
inp = unreal.IKRetargetBatchOperationInputs()
inp.set_editor_property("assets_to_retarget", [dead]); inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", "_" + CH); inp.set_editor_property("target_path", ANIMS)
inp.set_editor_property("include_referenced_assets", False); inp.set_editor_property("overwrite_existing_files", True)
unreal.IKRetargetBatchOperation.run_batch_retarget(inp)
death = unreal.load_asset(f"{ANIMS}/Anim_Warrior_Dead_1_{CH}"); assert death
death.set_editor_property("enable_root_motion", False); death.set_editor_property("force_root_lock", True); eal.save_loaded_asset(death, False)
flinch = clip("Hit_to_body_01")

# ---- her reference pose: the dagger grips (822's), the frame mapping (855's), the torch (865's)
ref = APE.get_reference_pose(tgt_mesh.skeleton)
bone = lambda n: APE.get_bone_pose(ref, n, unreal.AnimPoseSpaces.WORLD)
def hand_bits(s):
    hand = bone(f"hand_{s}"); h = hand.translation
    fore = (h - bone(f"lowerarm_{s}").translation).normal()
    th = bone(f"thumb_01_{s}").translation - h; along = (bone(f"middle_01_{s}").translation - h).normal()
    th = th - along * th.dot(along); th = (th - fore * th.dot(fore)).normal()
    return hand, h + fore * 6.5 + V(0, 0, -2.5), fore, th, along
def slant(th, fore, deg):
    g = math.radians(deg); return (th * math.cos(g) + fore * math.sin(g)).normal()
dm = unreal.load_asset(DAGGER); bb = dm.get_bounding_box(); DEND = 1.0 if bb.max.z - DAGGER_Z >= DAGGER_Z - bb.min.z else -1.0
def dagger_grip(s):
    hand, palm, fore, th, along = hand_bits(s)
    rot = ML.make_rot_from_zx(slant(th, fore, RTIMES["grip_tilt"]["dagger"]) * DEND, fore)
    return ML.make_relative_transform(unreal.Transform(palm - ML.get_up_vector(rot) * DAGGER_Z, rot, V(1, 1, 1)), hand)
def vec(a): return V(*a)
def mesh_frame(k, flip=False):
    f = FR[k]; y = vec(f["y"]) * (-1.0 if flip else 1.0)
    return unreal.Transform(vec(f["origin"]), ML.make_rot_from_xy(vec(f["x"]), y), V(1, 1, 1))
def grip_from(frame_in_hand, k, flip=False): return ML.compose_transforms(ML.invert_transform(mesh_frame(k, flip)), frame_in_hand)
def angle_between(q1, q2):
    d = abs(q1.x * q2.x + q1.y * q2.y + q1.z * q2.z + q1.w * q2.w); return math.degrees(2.0 * math.acos(min(1.0, d)))
def mapped(tmpl_grip, k, s):
    hand, palm, fore, th, along = hand_bits(s); kn = ML.inverse_transform_direction(hand, along)
    tf = ML.compose_transforms(mesh_frame("template_dagger"), tmpl_grip)
    if tf.rotation.rotate_vector(V(0, 1, 0)).dot(kn) < 0: tf = ML.compose_transforms(mesh_frame("template_dagger", True), tmpl_grip)
    if FR[k]["single_edged"]: return grip_from(tf, k)
    a, b = grip_from(tf, k), grip_from(tf, k, True)
    return a if angle_between(a.rotation, tmpl_grip.rotation) <= angle_between(b.rotation, tmpl_grip.rotation) else b
TORCH = "/Game/Medieval_Castle/CastleKit/Props/Meshes/Props/TorchKit/SM_Torch_01a"; TORCH_TILT = 20.0
KP = unreal.ProceduralMeshLibrary
tm = unreal.load_asset(TORCH); tb = tm.get_bounding_box()
tv = [(v.x, v.y, v.z) for s in range(tm.get_num_sections(0)) for v in KP.get_section_from_static_mesh(tm, 0, s)[0]]
tsz = [tb.max.x - tb.min.x, tb.max.y - tb.min.y, tb.max.z - tb.min.z]
long_ = max(range(3), key=lambda i: tsz[i]); tmn = [tb.min.x, tb.min.y, tb.min.z][long_]; tmx = [tb.max.x, tb.max.y, tb.max.z][long_]
def twidth(a, c):
    o_ = [i for i in range(3) if i != long_]; s_ = [v for v in tv if a <= v[long_] <= c]
    return max((max(v[k] for v in s_) - min(v[k] for v in s_)) for k in o_) if s_ else 0.0
head_up = twidth(tmx - 0.2 * (tmx - tmn), tmx) >= twidth(tmn, tmn + 0.2 * (tmx - tmn))
head = tmx if head_up else tmn; foot = tmn if head_up else tmx
AX = {"x": V(1, 0, 0), "y": V(0, 1, 0), "z": V(0, 0, 1)}
TORCH_FRAME_AX = AX["xyz"[long_]] * (1.0 if head_up else -1.0)
mid_other = [((tb.min.x + tb.max.x) / 2, (tb.min.y + tb.max.y) / 2, (tb.min.z + tb.max.z) / 2)[i] for i in range(3)]
grip_pt = list(mid_other); grip_pt[long_] = foot + (head - foot) * 0.22; grip_pt = V(*grip_pt)
def torch_grip():
    """865's: her left fist round the torch's handle a fifth of the way up, the torch along her thumb turned 20 degrees toward her elbow"""
    hand = bone("hand_l"); fore = (hand.translation - bone("lowerarm_l").translation).normal()
    thumb = V(0, 1, 0); thumb = (thumb - fore * thumb.dot(fore)).normal()
    palm = hand.translation + fore * 6.5 + V(0, 0, -2.5)
    hd = (thumb * math.cos(math.radians(TORCH_TILT)) - fore * math.sin(math.radians(TORCH_TILT))).normal()
    rot = ML.make_rot_from_zx(hd, fore)
    other = [k for k in "xyz" if k != "xyz"[long_]][0]
    t2 = unreal.Transform(V(0, 0, 0), ML.make_rot_from_zx(TORCH_FRAME_AX, AX[other]), V(1, 1, 1)).inverse()
    frame = ML.compose_transforms(unreal.Transform(grip_pt * -1.0, unreal.Rotator(0, 0, 0), V(1, 1, 1)), t2)
    return ML.make_relative_transform(ML.compose_transforms(frame, unreal.Transform(palm, rot, V(1, 1, 1))), hand)


# ---- the weapons
def blank(name):
    w = unreal.RDWeaponDef(); w.name = name; w.hand_bone = "hand_r"; w.off_hand_bone = "hand_l"; w.spell_bone = "hand_r"
    w.get_hit = flinch; w.death = death; w.play_rate = 1.0; w.icon = "None"; w.holster_bone = "None"; w.off_hand_holster_bone = "None"
    return w
def copy(x, cls):
    n = cls(); n.import_text(x.export_text()); return n
knife = blank("Knife"); knife.mesh = dm; knife.off_hand_mesh = dm; knife.grip = dagger_grip("r"); knife.off_hand_grip = dagger_grip("l")
ka, kh, ke = [], [], []
o_ = unreal.AnimPoseEvaluationOptions()
def fastest(anim, bones, after=0.0):
    """872's: the time a hand moves fastest (relative to the pelvis, smoothed over 5 samples) after `after`"""
    L = unreal.AnimationLibrary.get_sequence_length(anim); n = max(30, int(L * 60)); pts = {b: [] for b in bones}
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(anim, L * k / n, o_); q = APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.WORLD).translation
        for b in bones:
            h = APE.get_bone_pose(p, b, unreal.AnimPoseSpaces.WORLD).translation; pts[b].append(V(h.x - q.x, h.y - q.y, h.z - q.z))
    sp = [max((pts[b][k + 1] - pts[b][k]).length() / (L / n) for b in bones) for k in range(n)]
    sm = [sum(sp[max(0, k - 2):k + 3]) / len(sp[max(0, k - 2):k + 3]) for k in range(n)]
    return L, max(((L * (k + 0.5) / n, sm[k]) for k in range(n) if L * (k + 0.5) / n >= after), key=lambda x: x[1])[0]
for n, hands in (("Stab1", ["hand_r"]), ("Stab2", ["hand_l"]), ("Stab3", ["hand_r", "hand_l"])):
    a = clip(n); L, hit = fastest(a, hands, RTIMES["Stabs"][n]["wind"])
    ka.append(a); kh.append(round(hit, 3)); ke.append(round(min(L, hit + 0.24), 3))
knife.attacks = ka; knife.attack_starts = [0.0] * 3; knife.attack_ends = ke; knife.hit_times = kh
knife.weapon_type = "short blades"; knife.sound_key = "Daggers"; knife.reach = 150.0; knife.arc = 110.0
cast = clip("CastBolt"); ct = TIMES["CastBolt"]

if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
allh = list(gen.get_editor_property("heroes"))
mage = next(h for h in allh if str(h.name) == "Mage")
# (Fire Bolt and Dark Fire: the Mage's weapons (her damage, mana, effects, sounds, pictures), cast with the Summoner's clip)
spells_w = []
for mw in mage.weapons:
    w = copy(mw, unreal.RDWeaponDef)
    w.attacks = [cast]; w.attack_starts = [0.0]; w.attack_ends = [float(ct["length"])]; w.hit_times = [float(ct["hit"])]; w.play_rate = 1.0
    w.spell_bone = ct["bone"]; w.get_hit = flinch; w.death = death
    spells_w.append(w)
# (her summons: spells of the generator's table past the 30 (201-205), effects as the Abyssal Knight's call)
spells = [s for s in gen.get_editor_property("spells") if not 201 <= s.number <= 205]
knight = next(s for s in spells if s.kind == unreal.RDSpellKind.KNIGHT)
mons = {str(m.name): m for m in gen.get_editor_property("monsters")}
base = len(spells); summons = []
for k, (kind, count) in enumerate(SUMMONS):
    assert kind in mons, f"876: no monster {kind}"
    s = copy(knight, unreal.RDSpellDef)
    s.name = f"Summon Tier {k + 1}"; s.number = 201 + k; s.type = unreal.RDSpellType.SUMMON; s.kind = unreal.RDSpellKind.SUMMON
    title = mons[kind].title or kind
    s.effect = f"calls {title} (a tier {mons[kind].tier} monster) to fight at her side until it falls; {count} at most"
    s.summon_kind = kind; s.count = count; s.mana = MANA * 0.5; s.cooldown = 0.0; s.duration = 0.0; s.tier = k + 1; s.drop_chance = 0.0
    s.damage = 0.0; s.reach = 1400.0; s.icon = f"summon_{k + 1}"
    spells.append(s)
    t = TIMES[f"Summon{k + 1}"]
    w = blank(s.name); w.spell = True; w.attacks = [clip(f"Summon{k + 1}")]; w.attack_starts = [0.0]; w.attack_ends = [float(t["length"])]; w.hit_times = [float(t["hit"])]
    w.spell_index = base + k; w.damage = 0.0; w.mana_cost = MANA * 0.5; w.mana_share = 0.5; w.reach = 1400.0; w.spell_bone = t["bone"]
    w.charge_effect = knight.cast_fx; w.charge_effect_scale = 0.6; w.sound_key = knight.sound_key; w.icon = s.icon
    summons.append(w)
    print(f"SU4 {s.name}: {kind} (tier {mons[kind].tier}, {mons[kind].sound_set}), {count} at most, clip Summon{k + 1} {t['length']} s (hit {t['hit']})")
gen.set_editor_property("spells", spells)

# ---- her dungeon character
G = "/Game/RandomDungeon/Blueprints"; CHP = f"{G}/BP_SU4_SummonerCharacter"
PARENT = unreal.load_asset(f"/Game/JRPG/Game/BP_JRPG{CH}Character").generated_class()
if not eal.does_asset_exist(CHP):
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", PARENT); at.create_asset(CHP.split("/")[-1], G, unreal.Blueprint, f)
chbp = unreal.load_asset(CHP)
if unreal.BlueprintEditorLibrary.get_blueprint_parent_class(chbp) != PARENT: unreal.BlueprintEditorLibrary.reparent_blueprint(chbp, PARENT)
unreal.BlueprintEditorLibrary.compile_blueprint(chbp)
unreal.get_default_object(chbp.generated_class()).get_component_by_class(unreal.CapsuleComponent).set_editor_property("capsule_radius", 30.0)
unreal.BlueprintEditorLibrary.compile_blueprint(chbp); eal.save_loaded_asset(chbp, only_if_is_dirty=False)

# ---- her hero, in the place of level 5's Summoner
h = copy(mage, unreal.RDHeroDef)
h.name = HERO; h.title = CARD["title"]; h.pawn_class = chbp.generated_class()
h.max_health = HEALTH; h.max_mana = MANA; h.mana_per_second = MANA_PER_SECOND; h.melee_bonus = 0.0; h.ranged_bonus = 0.0; h.rogue_controls = False
h.roll_clip = None; h.roll_back_clip = None; h.dash_clip = None
h.controls_keys = [c.replace("1 / 2, wheel|fire / dark fire", "1 - 3, wheel|fire / dark fire / summon") for c in mage.controls_keys]
h.controls_pad = list(mage.controls_pad)
# (one line each: six two-line abilities ran the Martial Artist's card under the hero tabs)
h.abilities = CARD["abilities"]
h.armour = CARD["armour"]; h.starts_with = CARD["starts_with"]; h.accent = unreal.LinearColor(*CARD["accent"], 1.0)
h.wears = []; h.ring_kinds = [unreal.RDRingKind.MAGIC]; h.learns = []; h.scroll_types = SCROLL_TYPES
h.set_editor_property("tome_mana", {}); h.set_editor_property("type_bonus", {}); h.dexterity_types = []
h.weapons = spells_w + summons[:1]; h.locked_weapons = summons[1:]; h.unlock_per_boss = 1
si = next((k for k, x in enumerate(allh) if str(x.name) == HERO), len(allh))
heroes = [x for x in allh if str(x.name) != HERO]; heroes.insert(min(si, len(heroes)), h)
gen.set_editor_property("heroes", heroes)

# ---- her daggers (each short blade of the table, in both hands) and the torch in her hand
items = list(gen.get_editor_property("items")); nfit = 0
key = lambda name: "".join(c for c in name.title() if c.isalnum())
def finish(wd, w):
    seg = [wd.attack_ends[i] - wd.attack_starts[i] for i in range(len(wd.attacks))]
    cyc = 1.6 - (w["speed"] - 1) * 1.05 / 9.0
    wd.name = w["name"]; wd.item = w["name"]; wd.damage = 8.0 + 3.0 * w["damage"]
    wd.play_rate = max(0.35, min(2.6, (sum(seg) / len(seg)) / cyc))
    wd.durability = float(w["durability"]); wd.speed_rating = w["speed"]; wd.damage_rating = w["damage"]; wd.weapon_type = w["type"]
    wd.sound_key = "Daggers"; wd.mana_cost = 0.0; wd.alongside = False; wd.icon = "None"; wd.holster_bone = "None"; wd.off_hand_holster_bone = "None"
    return wd
for it in items:
    if it.kind == unreal.RDItemKind.WEAPON:
        w = next((x for x in WT["weapons"] if x["name"] == str(it.name)), None)
        fits = [f for f in it.weapon_fits if str(f.hero) != HERO]
        if w and w["type"] == "short blades":
            k = key(w["name"]); wd = copy(knife, unreal.RDWeaponDef); wd.mesh = unreal.load_asset(FR[k]["mesh"]); wd.off_hand_mesh = wd.mesh
            wd.grip = mapped(knife.grip, k, "r"); wd.off_hand_grip = mapped(knife.off_hand_grip, k, "l")
            finish(wd, w); f = unreal.RDWeaponFit(); f.hero = HERO; f.weapon = wd; fits.append(f); nfit += 1
        it.weapon_fits = fits
    elif it.kind == unreal.RDItemKind.TORCH:
        fits = [f for f in it.weapon_fits if str(f.hero) != HERO]
        wd = unreal.RDWeaponDef(); wd.name = "Torch"; wd.off_hand_mesh = tm; wd.off_hand_bone = "hand_l"; wd.off_hand_grip = torch_grip()
        f = unreal.RDWeaponFit(); f.hero = HERO; f.weapon = wd; fits.append(f); it.weapon_fits = fits
    elif it.kind == unreal.RDItemKind.ARMOUR:
        it.fits = [f for f in it.fits if str(f.hero) != HERO]          # (no armour for her: the Mage's equipment)
gen.set_editor_property("items", items)
assert HERO not in [str(x) for x in gen.get_editor_property("slash_heroes")], "876: her daggers are never enchanted"
# (every spell weapon named as a spell of the table pointed at its place again: this stage and 872 each take their spells
# out and add them at the table's end, and a weapon points at its spell by its place; 872's chi attacks after her
# summons moved down when the summons went)
_by = {str(s.name): i for i, s in enumerate(gen.get_editor_property("spells"))}; _moved = [0]
def _fix(ws):
    out = []
    for w in ws:
        i = _by.get(str(w.name))
        if w.spell and i is not None and w.spell_index != i: w.spell_index = i; _moved[0] += 1
        out.append(w)
    return out
_hs = list(gen.get_editor_property("heroes"))
for _h in _hs: _h.weapons = _fix(_h.weapons); _h.locked_weapons = _fix(_h.locked_weapons)
gen.set_editor_property("heroes", _hs); gen.set_editor_property("weapons", _fix(gen.get_editor_property("weapons")))
print(f"SU4 spell weapons pointed again at their spells by name: {_moved[0]}")
gen.modify(); les.save_current_level()
back = next(x for x in gen.get_editor_property("heroes") if str(x.name) == HERO)
print(f"SU4 mistward_castle: hero {back.title} ({back.pawn_class.get_name()}) hp {back.max_health} mana {back.max_mana} ({back.mana_per_second}/s) | weapons {[str(w.name) for w in back.weapons]} "
      f"(mana {[w.mana_cost for w in back.weapons]}) | locked {[str(w.name) for w in back.locked_weapons]} | dagger fits {nfit} | heroes {[str(x.name) for x in gen.get_editor_property('heroes')]} "
      f"| knife stabs at {kh} | spells {len(gen.get_editor_property('spells'))}")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
