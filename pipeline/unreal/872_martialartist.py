"""The Martial Artist (ai models/MartialArtist2.glb; the user's of 2026-10-28), a hero of mistward_castle and martial_arts.
Run after blender_numpy/tripo_build.py with martialartist_clips.py into SourceArt/jrpg_martialartist and 600 / 610 / 615 /
620 for MartialArtist (her mesh, her clips, her AnimBP, BP_JRPGMartialArtistCharacter); 819 after this (her walk / run).
- her flinch and death: Animations_Warrior's Get_Hit_1 and Dead_1 retargeted onto her rig (822's source rig)
- her fists ("Fists", weapon type "unarmed": a Dexterity ring adds to it): Tripo's own Box_01 and Front_kick_02 (the
  user's of 2026-10-28), each one attack played whole, its blow where one of her hands or feet moves fastest; 1.6 m reach;
  her damage (the user's of 2026-10-29) close to the Warrior's with an average weapon of the table: the fists' blow that
  damage a second times their average clip, the chi table scaled so the ten do it over their moves (printed: "MA damage") (with "whole" off in martial_arts.json each clip listed is cut into its strikes instead: a peak of at least
  half the clip's fastest, 0.4 s or more from the next)
- her chi attacks (martial_arts.json: the user's table): bolt spells (from her striking hand or foot at the blow of its
  own clip (martialartist_clips.py's `hit`), after the monster she faces, 4 m at most: FRDWeaponDef::BoltRange; the burst
  hurting others within Splash half as much), each with its mana, damage and tier; no tome teaches them (no drop chance).
  Their looks (the user's of 2026-10-29) are on her fists and legs while the move plays (FRDWeaponDef::LimbFx from the
  json's `look`: wind, lightning, fire, smoke, sparks, rings, rods, fireworks, a fireball, chain lightning); the bolt is
  unseen but for the Piercing Palm's rod, and its burst on the monster is the json's `hit`. Two are hers from the start,
  the other eight her hero's LockedWeapons: two more for each tier boss she slays
- her knives: each short blade of the weapons table wielded in both hands with rogue_clips.py's stabs (as the Rogue does;
  855's grip mapping onto a dagger held as 822 holds it, from her own reference pose); +30 % damage (TypeBonus)
- her hero: 140 hit points (the Warrior's), 100 mana and 2 a second (the Mage's), light armour, HP and Dexterity rings
  (the ring adds to her fists and knives, not her chi), the Rogue's controls (B rolls: her own roll clips), a dash (V, the
  right mouse button, RT: her Dash clip) into a strike
- her armour: the seven light sets fitted to her (849 heroes MartialArtist, blender_numpy/summoner3_armour.py --hero
  MartialArtist (the tiefling's at --pct 70, as the Rogue's), 851 MartialArtist <sets>), each item's fit added where the
  Rogue has one (her fits are named by the set's key)
- BP_MA_MartialArtistCharacter (a child of BP_JRPGMartialArtistCharacter, a 36 cm capsule)
Writes her on every map of MAPS that exists (the hero replaced if there, the chi spells and the knives' fits as well) and
saves them. Args: none"""
import json, math, os, unreal
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions; ML = unreal.MathLibrary
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V = unreal.Vector
CH = "MartialArtist"; HERO = "MartialArtist"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
SRC = os.path.join(SA, "jrpg_martialartist")
DATA = json.load(open(os.path.join(SA, "martial_arts", "martial_arts.json"), encoding="utf-8"))
TIMES = json.load(open(os.path.join(SRC, "ma_times.json"))); RTIMES = json.load(open(os.path.join(SRC, "times.json")))
WT = json.load(open(os.path.join(SA, "random_dungeon_magic5", "weapons_table.json"), encoding="utf-8"))
FR = json.load(open(os.path.join(SA, "random_dungeon_magic5", "weapon_frames.json"), encoding="utf-8"))["weapons"]
OUT = "/Game/RandomDungeon/Martial"; ANIMS = OUT + "/Anims"; RIGS = OUT + "/Rigs"
MAPS = ["/Game/RandomDungeon/Maps/mistward_castle", "/Game/RandomDungeon/Maps/martial_arts"]
tgt_mesh = unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{CH}"); tgt_rig = unreal.load_asset(f"/Game/JRPG/Rigs/IK_JRPG_{CH}_Auto")
assert tgt_mesh and tgt_rig, "run 600-620 for MartialArtist first"
DAGGER, DAGGER_Z = "/Game/Medieval_Weapons/Meshes/VOL2/SM_Dagger", 28.5
o_ = unreal.AnimPoseEvaluationOptions()


def make(cls, fac, name, folder):
    p = f"{folder}/{name}"
    if eal.does_asset_exist(p): eal.delete_asset(p)
    return at.create_asset(name, folder, cls, fac) or unreal.load_asset(p)


def clip(n):
    p = f"/Game/JRPG/{CH}Anims/AS_{CH}_{n}"; a = unreal.load_asset(p); assert a, p
    a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
    return a


def speeds(anim, bones):
    """per sample: the fastest of the bones (relative to the pelvis), smoothed over 5 samples; the sample's time"""
    L = unreal.AnimationLibrary.get_sequence_length(anim); n = max(30, int(L * 60)); pts = {b: [] for b in bones}
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(anim, L * k / n, o_); q = APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.WORLD).translation
        for b in bones:
            h = APE.get_bone_pose(p, b, unreal.AnimPoseSpaces.WORLD).translation; pts[b].append(V(h.x - q.x, h.y - q.y, h.z - q.z))
    sp = [max((pts[b][k + 1] - pts[b][k]).length() / (L / n) for b in bones) for k in range(n)]
    sm = [sum(sp[max(0, k - 2):k + 3]) / len(sp[max(0, k - 2):k + 3]) for k in range(n)]
    return L, [(L * (k + 0.5) / n, sm[k]) for k in range(n)]


def strikes(anim):
    """the clip's strikes: (start, hit, end) seconds"""
    L, s = speeds(anim, ["hand_l", "hand_r", "foot_l", "foot_r"])
    top = max(v for _, v in s); peaks = []
    for i in range(1, len(s) - 1):
        t, v = s[i]
        if v >= 0.5 * top and v >= s[i - 1][1] and v >= s[i + 1][1]:
            if peaks and t - peaks[-1][0] < 0.4:
                if v > peaks[-1][1]: peaks[-1] = (t, v)
            else: peaks.append((t, v))
    out = []
    for i, (t, v) in enumerate(peaks):
        a = 0.0 if i == 0 else 0.5 * (peaks[i - 1][0] + t)
        b = min(L, t + 0.5) if i == len(peaks) - 1 else 0.5 * (t + peaks[i + 1][0])
        out.append((round(max(0.0, min(a, t - 0.05)), 3), round(t, 3), round(max(b, t + 0.12), 3)))
    return L, out


def fastest(anim, bones, after=0.0):
    L, s = speeds(anim, bones)
    return L, max((x for x in s if x[0] >= after), key=lambda x: x[1])[0]


# ---- flinch and death (822's)
src_mesh = unreal.load_asset("/Game/Animations_Warrior/Mesh/SK_Mannequin"); assert src_mesh
src_rig = unreal.load_asset("/Game/RandomDungeon/Magic3/Rigs/IK_RDM3_Warrior_Source"); assert src_rig, "822 first (its source rig)"
rtg = make(unreal.IKRetargeter, unreal.IKRetargetFactory(), f"RTG_MA_Warrior_To_{CH}", RIGS)
rc = unreal.IKRetargeterController.get_controller(rtg)
rc.add_default_ops()
rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
rc.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, src_mesh); rc.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, tgt_mesh)
rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, src_rig); rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
rm = rc.get_op_controller(rc.get_index_of_op_by_name("Root Motion"))
rm.set_source_root_bone("root"); rm.set_target_root_bone("root"); rm.set_target_pelvis_bone("pelvis")
try: rc.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
except Exception as e: print("MA align", e)
eal.save_loaded_asset(rtg)
ar = unreal.AssetRegistryHelpers.get_asset_registry()
def find(pack, name):
    for a in ar.get_assets_by_path("/Game/" + pack, recursive=True):
        if str(a.asset_name) == name and str(a.asset_class_path.asset_name) == "AnimSequence": return a
    raise RuntimeError(name)
names = ["Anim_Warrior_Get_Hit_1", "Anim_Warrior_Dead_1"]
for n in names:
    if eal.does_asset_exist(f"{ANIMS}/{n}_{CH}"): eal.delete_asset(f"{ANIMS}/{n}_{CH}")
inp = unreal.IKRetargetBatchOperationInputs()
inp.set_editor_property("assets_to_retarget", [find("Animations_Warrior", n) for n in names])
inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", "_" + CH)
inp.set_editor_property("target_path", ANIMS); inp.set_editor_property("include_referenced_assets", False)
inp.set_editor_property("overwrite_existing_files", True)
unreal.IKRetargetBatchOperation.run_batch_retarget(inp)
flinch, death = [unreal.load_asset(f"{ANIMS}/{n}_{CH}") for n in names]
for a in (flinch, death):
    assert a; a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)

# ---- her reference pose: the dagger grips (822's), the frame mapping (855's)
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

# ---- the weapons
def blank(name):
    w = unreal.RDWeaponDef(); w.name = name; w.hand_bone = "hand_r"; w.off_hand_bone = "hand_l"; w.spell_bone = "hand_r"
    w.get_hit = flinch; w.death = death; w.play_rate = 1.0; w.icon = "None"; w.holster_bone = "None"; w.off_hand_holster_bone = "None"
    return w
F = DATA["fists"]
fists = blank("Fists"); fa, fs, fe, fh = [], [], [], []
report = []
for n in F["clips"]:
    a = clip(n); L, ss = strikes(a)
    if F.get("whole"):
        # (the user's of 2026-10-28: each clip one basic attack, played whole; its blow where her hand or foot is fastest)
        L2, hit = fastest(a, ["hand_l", "hand_r", "foot_l", "foot_r"])
        fa.append(a); fs.append(0.0); fe.append(round(L2, 3)); fh.append(round(hit, 3))
        report.append(f"{n} {L:.2f} s whole, the blow at {hit:.2f} (its strikes {[h for _, h, _ in ss]})"); continue
    for (s0, hit, s1) in ss[:F.get("max_per_clip", 3)]:
        fa.append(a); fs.append(s0); fe.append(s1); fh.append(hit)
    report.append(f"{n} {L:.2f} s: " + ", ".join(f"{h:.2f} ({s0:.2f}-{s1:.2f})" for s0, h, s1 in ss))
fists.attacks = fa; fists.attack_starts = fs; fists.attack_ends = fe; fists.hit_times = fh
# ---- her damage (the user's of 2026-10-29: close to what the Warrior does with an average weapon). The Warrior's average
# weapon of the table, each by its rules (8 + 3 x its damage rating, +30 % her melee bonus (heroes.json; none on a bow), one
# blow every 1.6 - (speed - 1) x 1.05 / 9 s): damage a second. Her fists' blow is that times her fists' average clip (each
# played whole: one blow per clip); her chi attacks' table (the user's) times the share that puts the ten's damage over their
# moves' seconds at it too
HJ = {h["name"]: h for h in json.load(open(os.path.join(SA, "random_dungeon_magic4", "heroes.json"), encoding="utf-8"))["heroes"]}
WB = HJ["Warrior"]["melee_bonus"]
_d = [(8 + 3 * w["damage"]) * (1.0 + (0.0 if w["type"] == "ranged" else WB)) for w in WT["weapons"]]
_c = [1.6 - (w["speed"] - 1) * 1.05 / 9.0 for w in WT["weapons"]]
WARRIOR_DPS = sum(d / c for d, c in zip(_d, _c)) / len(_d)
FIST_CYCLE = sum(e - s for s, e in zip(fs, fe)) / len(fe) / float(F["play_rate"])
FIST_DAMAGE = round(WARRIOR_DPS * FIST_CYCLE)
_cl = sum(TIMES[c["clip"]]["length"] for c in DATA["chi"]); _cd = sum(c["damage"] for c in DATA["chi"])
CHI_SCALE = WARRIOR_DPS / (_cd / _cl)
CHI_DAMAGE = {c["name"]: round(c["damage"] * CHI_SCALE) for c in DATA["chi"]}
print(f"MA damage: the Warrior's average weapon {WARRIOR_DPS:.1f} a second; her fists one blow every {FIST_CYCLE:.2f} s: {FIST_DAMAGE} a blow"
      f" (was {F['damage']}); the chi table x {CHI_SCALE:.3f} ({_cd / _cl:.1f} a second before): {CHI_DAMAGE}")
fists.damage = float(FIST_DAMAGE); fists.reach = float(F["reach"]); fists.arc = float(F["arc"]); fists.play_rate = float(F["play_rate"])
fists.weapon_type = "unarmed"; fists.sound_key = F["sound"]; fists.icon = F.get("icon", "None")          # (874's picture)
print("MA fists:", " | ".join(report))
# her knife (both hands): rogue_clips' stabs on her rig
knife = blank("Knife"); knife.mesh = dm; knife.off_hand_mesh = dm
knife.grip = dagger_grip("r"); knife.off_hand_grip = dagger_grip("l")
ka, kh, ke = [], [], []
for n, hands in (("Stab1", ["hand_r"]), ("Stab2", ["hand_l"]), ("Stab3", ["hand_r", "hand_l"])):
    a = clip(n); L, hit = fastest(a, hands, RTIMES["Stabs"][n]["wind"]); ka.append(a); kh.append(round(hit, 3)); ke.append(round(min(L, hit + 0.24), 3))
knife.attacks = ka; knife.attack_starts = [0.0] * 3; knife.attack_ends = ke; knife.hit_times = kh
knife.weapon_type = "short blades"; knife.sound_key = "Daggers"; knife.reach = 150.0; knife.arc = 110.0
print("MA knife stabs at", kh)
# the chi attacks (the clips of moves no longer in the table deleted: the first table's Cannon Punch, Roundhouse Fist,
# Slashing Palm and Uppercut Punch were made kicks the same day)
keep = {c["clip"] for c in DATA["chi"]}
for p in eal.list_assets(f"/Game/JRPG/{CH}Anims", recursive=False):
    nm = p.split(".")[-1]
    if nm.startswith(f"AS_{CH}_Chi_") and nm[len(f"AS_{CH}_"):] not in keep: print("MA deleted the old", nm, eal.delete_asset(p.split(".")[0]))
spells_new, chi_w = [], []
PACKS = {"MP4": "/Game/MagicProjectilesVol4", "MP5": "/Game/MagicProjectilesVol5", "SL": "/Game/StylizedSlashesV2", "SH": "/Game/StylizedShieldsVol1",
         "TE1": "/Game/ToonExplosionVol1", "LD": "/Game/LootDropsV2"}
def fx_of(p):
    """an effect by its short path (martial_arts.json's note: MP5/Hits/NS_Hit_Orb01 ...); None for none"""
    if not p: return None
    k, rest = p.split("/", 1); path = f"{PACKS[k]}/Particles/NiagaraSystems/{rest}"
    a = unreal.load_asset(path); assert a, path
    return a
def limb_fx(c, t):
    """the chi's look (FRDLimbFx, one per bone listed; `at`: one-shots), within its clip (t: its length)"""
    out = []
    for e in c.get("look", []):
        fx = fx_of(e["fx"])
        for b in e["bones"]:
            for (s0, s1) in ([(a, a) for a in e["at"]] if "at" in e else [(e["from"], e["to"])]):
                assert 0.0 <= s0 <= t["length"] and s1 <= t["length"], f"{c['name']}: {e['fx']} at {s0}-{s1} outside the clip"
                L = unreal.RDLimbFx(); L.fx = fx; L.bone = b; L.scale = float(e["scale"]); L.start_at = float(s0); L.stop_at = float(s1)
                L.life = float(e.get("life", 0.4)); L.user_scale = bool(e.get("user_scale", True))
                if "offset" in e: L.offset = V(*e["offset"])
                if "turn" in e: L.turn = unreal.Rotator(pitch=e["turn"][0], yaw=e["turn"][1], roll=e["turn"][2])
                out.append(L)
    return out
for i, c in enumerate(DATA["chi"]):
    # (the user's of 2026-10-29: each chi's look on her fists or legs (wind, lightning, fire, smoke, sparks, rings, rods,
    # fireworks, a fireball, chain lightning); the blow itself an unseen bolt, 4 m at most, with its burst on the monster;
    # only the Piercing Palm's rods fly)
    t = TIMES[c["clip"]]; a = clip(c["clip"])
    look = limb_fx(c, t); bolt = fx_of(c.get("bolt")); hit = fx_of(c.get("hit"))
    bsc = float(c.get("bolt_scale", 1.0)); hsc = float(c.get("hit_scale", 1.0)); spl = float(DATA["splash"][str(c["tier"])])
    s = unreal.RDSpellDef(); s.name = c["name"]; s.number = 100 + i + 1; s.type = unreal.RDSpellType.OFFENSE; s.kind = unreal.RDSpellKind.BOLT
    s.effect = c["effect"]; s.mana = float(c["mana"]); s.damage = float(CHI_DAMAGE[c["name"]]); s.tier = int(c["tier"]); s.reach = float(DATA["chi_reach"])
    s.splash = spl; s.drop_chance = 0.0; s.cooldown = 0.0; s.bolt_speed = float(DATA["chi_bolt_speed"])
    s.cast_fx = None; s.bolt_fx = bolt; s.impact_fx = hit; s.bolt_fx_scale = bsc; s.impact_fx_scale = hsc
    s.sound_key = "Fire"; s.icon = c["icon"]
    spells_new.append(s)
    w = blank(c["name"]); w.spell = True; w.attacks = [a]; w.attack_starts = [0.0]; w.attack_ends = [float(t["length"])]; w.hit_times = [float(t["hit"])]
    w.damage = float(CHI_DAMAGE[c["name"]]); w.mana_cost = float(c["mana"]); w.reach = float(DATA["chi_reach"]); w.spell_bone = t["bone"] if t["bone"] != "pelvis" else "hand_r"
    w.sound_key = "Fire"; w.icon = c["icon"]
    w.charge_effect = None; w.bolt_effect = bolt; w.bolt_effect_scale = bsc; w.burst_effect = hit; w.burst_effect_scale = hsc; w.limb_fx = look
    w.burst_life = float(c.get("hit_life", 0.0))
    w.bolt_speed = float(DATA["chi_bolt_speed"]); w.bolt_turn_rate = 260.0; w.bolt_splash = spl; w.bolt_range = float(DATA["chi_range"])
    chi_w.append(w)
    print(f"MA chi {c['name']}: {w.damage:.0f} damage ({c['damage']} in the table), icon {c['icon']}, look {[(L.fx.get_name(), str(L.bone), round(L.start_at, 2), round(L.stop_at, 2)) for L in look]} | bolt {bolt.get_name() if bolt else None}"
          f" | hit {hit.get_name() if hit else None} | from {w.spell_bone}, {w.bolt_range:.0f} cm at most")

# ---- her dungeon character
G = "/Game/RandomDungeon/Blueprints"; CHP = f"{G}/BP_MA_MartialArtistCharacter"
PARENT = unreal.load_asset(f"/Game/JRPG/Game/BP_JRPG{CH}Character").generated_class()
if not eal.does_asset_exist(CHP):
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", PARENT); at.create_asset(CHP.split("/")[-1], G, unreal.Blueprint, f)
chbp = unreal.load_asset(CHP)
if unreal.BlueprintEditorLibrary.get_blueprint_parent_class(chbp) != PARENT: unreal.BlueprintEditorLibrary.reparent_blueprint(chbp, PARENT)
unreal.BlueprintEditorLibrary.compile_blueprint(chbp)
unreal.get_default_object(chbp.generated_class()).get_component_by_class(unreal.CapsuleComponent).set_editor_property("capsule_radius", 36.0)
unreal.BlueprintEditorLibrary.compile_blueprint(chbp); eal.save_loaded_asset(chbp, only_if_is_dirty=False)

# ---- the maps
H = DATA["hero"]
key = lambda name: "".join(c for c in name.title() if c.isalnum())
def finish(wd, w):
    """855's: the table's numbers on her knife"""
    seg = [wd.attack_ends[i] - wd.attack_starts[i] for i in range(len(wd.attacks))]
    cyc = 1.6 - (w["speed"] - 1) * 1.05 / 9.0
    wd.name = w["name"]; wd.item = w["name"]; wd.damage = 8.0 + 3.0 * w["damage"]
    wd.play_rate = max(0.35, min(2.6, (sum(seg) / len(seg)) / cyc))
    wd.durability = float(w["durability"]); wd.speed_rating = w["speed"]; wd.damage_rating = w["damage"]; wd.weapon_type = w["type"]
    wd.sound_key = "Daggers"; wd.mana_cost = 0.0; wd.alongside = False; wd.icon = "None"; wd.holster_bone = "None"; wd.off_hand_holster_bone = "None"
    return wd
def copy(x, cls):
    n = cls(); n.import_text(x.export_text()); return n
def repoint_spell_weapons(gen):
    """every spell weapon named as a spell of the table (on every hero, locked or not, and among the generator's weapons)
    pointed at that spell's place again: this stage and 876 each take their spells out and add them at the table's end,
    and a weapon points at its spell by its place (FRDWeaponDef::SpellIndex). The table's own spells (the Mage's "Fire"
    for Fire Bolt) are named otherwise and stay where they were: they are never moved. How many were moved."""
    by = {str(s.name): i for i, s in enumerate(gen.get_editor_property("spells"))}; n = [0]
    def fix(ws):
        out = []
        for w in ws:
            i = by.get(str(w.name))
            if w.spell and i is not None and w.spell_index != i: w.spell_index = i; n[0] += 1
            out.append(w)
        return out
    hs = list(gen.get_editor_property("heroes"))
    for h_ in hs: h_.weapons = fix(h_.weapons); h_.locked_weapons = fix(h_.locked_weapons)
    gen.set_editor_property("heroes", hs); gen.set_editor_property("weapons", fix(gen.get_editor_property("weapons")))
    return n[0]


for MAP in MAPS:
    if not eal.does_asset_exist(MAP): print("MA (no", MAP, "yet)"); continue
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    names_ = {c["name"] for c in DATA["chi"]}
    # (every chi spell this made before, by its number (101 to 199), and any of the table's names: renamed ones went too;
    # the Summoner's summons (876, 201 on) stay: "101 on" took them, and her summons started, took mana and called nobody)
    spells = [s for s in gen.get_editor_property("spells") if str(s.name) not in names_ and not 101 <= s.number <= 199]
    base = len(spells); spells += [copy(s, unreal.RDSpellDef) for s in spells_new]
    gen.set_editor_property("spells", spells)
    ws = [copy(w, unreal.RDWeaponDef) for w in chi_w]
    for k, w in enumerate(ws): w.spell_index = base + k
    fw = copy(fists, unreal.RDWeaponDef)
    allh = list(gen.get_editor_property("heroes"))
    heroes = [h for h in allh if str(h.name) != HERO]
    # (her def built on the Rogue's (the controls' layout), or on her own where the Rogue is not (martial_arts))
    tmpl = next((h for h in allh if str(h.name) == "Rogue"), None) or next((h for h in allh if str(h.name) == HERO), None)
    h = copy(tmpl, unreal.RDHeroDef) if tmpl else unreal.RDHeroDef()
    h.name = HERO; h.title = H["title"]; h.pawn_class = chbp.generated_class()
    h.max_health = float(H["health"]); h.max_mana = float(H["mana"]); h.mana_per_second = float(H["mana_per_second"])
    h.melee_bonus = 0.0; h.ranged_bonus = 0.0; h.rogue_controls = True
    h.roll_clip = clip("RollF"); h.roll_back_clip = clip("RollB"); h.dash_clip = clip("Dash")
    h.controls_keys = H["controls_keys"]; h.controls_pad = H["controls_pad"]; h.abilities = H["abilities"]
    h.armour = H["armour"]; h.starts_with = H["starts_with"]; h.accent = unreal.LinearColor(*H["accent"], 1.0)
    h.wears = [unreal.RDArmourWeight.LIGHT]; h.ring_kinds = [unreal.RDRingKind.HEALTH, unreal.RDRingKind.DEXTERITY]; h.learns = []
    h.set_editor_property("tome_mana", {})
    h.set_editor_property("type_bonus", {k: float(v) for k, v in H["type_bonus"].items()}); h.dexterity_types = H["dexterity_types"]
    h.weapons = [fw] + ws[:DATA["start_chi"]]; h.locked_weapons = ws[DATA["start_chi"]:]; h.unlock_per_boss = DATA["per_boss"]
    # (the fifth hero (the user's of 2026-10-29): before the Summoner, who is off the castle's menu)
    si = next((k for k, x in enumerate(heroes) if str(x.name) == "Summoner"), len(heroes))
    heroes.insert(si, h)
    gen.set_editor_property("heroes", heroes)
    # (her knives: each short blade of the table, in both hands)
    items = list(gen.get_editor_property("items")); nfit = 0; narm = 0
    # (her armour: the light sets fitted to her (849 heroes MartialArtist, summoner3_armour.py --hero MartialArtist, 851
    # MartialArtist): an item's set found by the Rogue's fit of it, whose meshes are named by the set's key)
    for it in items:
        if it.kind != unreal.RDItemKind.ARMOUR: continue
        fits = [f for f in it.fits if str(f.hero) != HERO]
        rogue = next((f for f in fits if str(f.hero) == "Rogue"), None)
        if rogue and len(rogue.meshes):
            ms = [unreal.load_asset(f"/Game/JRPG/HeroArmour/{CH}/SK_{CH}_" + m.get_name().split("SK_Rogue_")[-1]) for m in rogue.meshes if m]
            if ms and all(ms):
                f = unreal.RDArmourFit(); f.hero = HERO; f.meshes = ms; fits.append(f); narm += 1
        it.fits = fits
    for it in items:
        if it.kind != unreal.RDItemKind.WEAPON: continue
        w = next((x for x in WT["weapons"] if x["name"] == str(it.name)), None)
        fits = [f for f in it.weapon_fits if str(f.hero) != HERO]
        if w and w["type"] in DATA["knife_types"]:
            k = key(w["name"]); wd = copy(knife, unreal.RDWeaponDef); wd.mesh = unreal.load_asset(FR[k]["mesh"]); wd.off_hand_mesh = wd.mesh
            wd.grip = mapped(knife.grip, k, "r"); wd.off_hand_grip = mapped(knife.off_hand_grip, k, "l")
            finish(wd, w); f = unreal.RDWeaponFit(); f.hero = HERO; f.weapon = wd; fits.append(f); nfit += 1
        it.weapon_fits = fits
    gen.set_editor_property("items", items)
    moved = repoint_spell_weapons(gen)
    gen.modify(); les.save_current_level()
    back = next(x for x in gen.get_editor_property("heroes") if str(x.name) == HERO)
    print(f"MA {MAP.rsplit('/', 1)[1]}: spell weapons pointed again at their spells by name: {moved}")
    print(f"MA {MAP.rsplit('/', 1)[1]}: hero {back.title} ({back.pawn_class.get_name()}) | weapons {[str(w.name) for w in back.weapons]} | locked {[str(w.name) for w in back.locked_weapons]}"
          f" | spells {len(gen.get_editor_property('spells'))} (chi from {base}) | knife fits {nfit} | armour fits {narm} | heroes {[str(x.name) for x in gen.get_editor_property('heroes')]}")
if eal.does_asset_exist(MAPS[0]) and not ues.get_editor_world().get_path_name().startswith(MAPS[0] + "."): les.load_level(MAPS[0])
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
