"""random_dungeonmagic_level5's weapons table (SourceArt/random_dungeon_magic5/weapons_table.json) and its five tiers of
rooms, on the level. Run after 854 (the meshes and their frames: weapon_frames.json) and after the clips were built by
blender_numpy/tripo_build.py with weapon5_clips.py as its clip maker into SourceArt/random_dungeon_magic5/w5_clips/<CH>
(Fem5 and DarkCaster: W5_TwoHand1-3, W5_Bow, W5_Shoot; Rogue: W5_Bow).
- the clips imported onto each hero's skeleton: /Game/RandomDungeon/Magic5/Anims/<CH>/AS_<CH>_W5_<clip>; a cut's blow
  lands where her right hand moves fastest after the wind-up (as 822 measures), the arrow and the bolt leave at the
  release weapon5_clips.py wrote (w5_times.json)
- each weapon, for each hero whose card lets her wield it (the table's rules: the Warrior and the Warlock all, the Rogue
  short blades and ranged weapons, the Mage and the Summoner none), an FRDWeaponDef (the item's WeaponFits):
    one-handed blades (short sword, one handed sword, curved and eastern sword, short blades): her own melee weapon's
      clips, flinch and death (the Warrior: her sword and shield; the Warlock: her sword; the Rogue: her daggers, the found
      blade in both hands), the new blade held where hers is: the grip maps the weapon's frame (854: where the hand
      closes, the blade's way, its edge) onto her weapon's frame in her hand. A one-edged blade's edge is turned the
      way her knuckles lead (her middle finger's way in her reference pose)
    two handed sword: the W5_TwoHand cuts; the grip from her hand as weapon5_clips.py holds it (the blade her thumb's way
      leaning 25 degrees toward her fingers, the edge her fingers' way, at her palm); no shield
    bows: the W5_Bow shot, in her left hand (the limbs her thumb's way leaning 15 degrees, the arrow's way her forearm's);
      an arrow (the crossbow's bolt mesh, 0.75 long) shot from the bow's grip straight at the monster she faces
    crossbows: the crossbow shot (the Rogue's own; the others W5_Shoot), held as 822 holds the Rogue's (the front her
      thumb's way leaning 45 degrees, the rail away from her fingers); its muzzle and the bolt lying ready from 854
  its numbers from the table: damage 8 + 3 x the damage rating; an attack every 1.6 - (speed - 1) x 1.05 / 9 s (her
  clip played at its length / that); reach and arc by type; durability; the sounds of the weapon it is like
- an item per weapon (kind Weapon): its durability as Amount, its rarity as Weight (as level 4's item table), the tiers
  its rooms are in, a line of what it is
- the generator: MaxTier 5, the containers of every section hold items (bLootAllSections)
Prints each weapon's numbers per hero and saves the level. Args: none"""
import json, math, os, unreal
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_magic5"
T = json.load(open(os.path.join(SA, "weapons_table.json"), encoding="utf-8"))
FR = json.load(open(os.path.join(SA, "weapon_frames.json"), encoding="utf-8"))["weapons"]
MAP = "/Game/RandomDungeon/Maps/random_dungeonmagic_level5"
ANIMS = "/Game/RandomDungeon/Magic5/Anims"
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); APE = unreal.AnimPoseExtensions; ML = unreal.MathLibrary
V = unreal.Vector
CH = {"Warrior": "Fem5", "Warlock": "DarkCaster", "Rogue": "Rogue"}
WHO = T["rules"]["who"]
ONE_HAND = ("short sword", "one handed sword", "curved and eastern sword", "short blades")
REACH = {"short blades": (150.0, 110.0), "short sword": (165.0, 120.0), "one handed sword": (175.0, 130.0), "curved and eastern sword": (180.0, 135.0),
         "two handed sword": (210.0, 160.0)}
BOW = {"reach": 3000.0, "speed": 5000.0, "len_scale": 0.75, "thick": 0.8}
SOUND = {"short blades": "Daggers", "two handed sword": "Axe"}            # (the rest: the hero's own melee weapon's; ranged: Crossbow)
key = lambda name: "".join(c for c in name.title() if c.isalnum())


def key_of(w): return key(w["name"])


# ---- the clips
def import_clips(ch):
    d = os.path.join(SA, "w5_clips", ch); f = os.path.join(d, f"SK_JRPG_{ch}_Clips.fbx")
    times = json.load(open(os.path.join(d, "w5_times.json")))
    skel = unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{ch}").get_editor_property("skeleton")
    o = unreal.FbxImportUI()
    o.set_editor_property("import_mesh", False); o.set_editor_property("import_as_skeletal", True)
    o.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    o.set_editor_property("skeleton", skel); o.set_editor_property("import_animations", True)
    o.set_editor_property("import_materials", False); o.set_editor_property("import_textures", False)
    tmp = f"{ANIMS}/_import_{ch}"
    t = unreal.AssetImportTask(); t.filename = f; t.destination_path = tmp; t.automated = True; t.replace_existing = True; t.save = True; t.options = o
    at.import_asset_tasks([t])
    got = {}
    for p in t.imported_object_paths:
        a = unreal.load_asset(p)
        if isinstance(a, unreal.AnimSequence):
            clip = p.split(".")[-1].split("Armature_A_")[-1]
            if not clip.startswith("W5_"): continue
            dst = f"{ANIMS}/{ch}/AS_{ch}_{clip}"
            if eal.does_asset_exist(dst): eal.delete_asset(dst)
            eal.rename_asset(p.split(".")[0], dst); a = unreal.load_asset(dst)
            a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
            got[clip] = a
    for p in eal.list_assets(tmp, recursive=True): eal.delete_asset(p.split(".")[0])
    eal.delete_directory(tmp)
    return got, times


o_ = unreal.AnimPoseEvaluationOptions()
def fastest(anim, bone, after):
    """length, and when the hand moves fastest (relative to the pelvis) after the wind-up: where the blow lands (822's)"""
    L = unreal.AnimationLibrary.get_sequence_length(anim); n = max(30, int(L * 60)); pts = []
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(anim, L * k / n, o_)
        h = APE.get_bone_pose(p, bone, unreal.AnimPoseSpaces.WORLD).translation; q = APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.WORLD).translation
        pts.append(V(h.x - q.x, h.y - q.y, h.z - q.z))
    sp = [(pts[k + 1] - pts[k]).length() / (L / n) for k in range(n)]
    sm = [sum(sp[max(0, k - 2):k + 3]) / len(sp[max(0, k - 2):k + 3]) for k in range(n)]
    k = max((i for i in range(n) if L * (i + 0.5) / n >= after), key=lambda i: sm[i])
    return L, L * (k + 0.5) / n


# ---- frames and grips
def vec(a): return V(*a)
def frame_xf(origin, x, y):
    """a frame (its X and Y ways, at origin) as a transform from the frame to the space they are in"""
    return unreal.Transform(origin, ML.make_rot_from_xy(x, y), V(1, 1, 1))
def mesh_frame(k, flip=False):
    f = FR[k]; y = vec(f["y"]) * (-1.0 if flip else 1.0)
    return frame_xf(vec(f["origin"]), vec(f["x"]), y)
def grip_from(frame_in_hand, k, flip=False):
    """the weapon's mesh relative to the hand bone, its frame put on frame_in_hand (the frame's transform in hand space)"""
    return ML.compose_transforms(ML.invert_transform(mesh_frame(k, flip)), frame_in_hand)
def hand_bits(ch, s):
    """the reference pose: the hand bone's transform, the palm point, the forearm's way, the thumb's way (822's), the fingers' way"""
    ref = APE.get_reference_pose(unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{ch}").get_editor_property("skeleton"))
    bone = lambda n: APE.get_bone_pose(ref, n, unreal.AnimPoseSpaces.WORLD)
    hand = bone(f"hand_{s}"); h = hand.translation
    fore = (h - bone(f"lowerarm_{s}").translation).normal()
    th = bone(f"thumb_01_{s}").translation - h; along = (bone(f"middle_01_{s}").translation - h).normal()
    th = th - along * th.dot(along); th = (th - fore * th.dot(fore)).normal()
    return hand, h + fore * 6.5 + V(0, 0, -2.5), fore, th, along
def slant(th, fore, deg):
    g = math.radians(deg); return (th * math.cos(g) + fore * math.sin(g)).normal()
def hand_frame(ch, s, kind):
    """where a weapon's frame goes in her hand (hand-bone space), as weapon5_clips.py / 822 hold it"""
    hand, palm, fore, th, along = hand_bits(ch, s)
    if kind == "twohand":
        x = slant(th, fore, 25.0); y = along - x * along.dot(x)
    elif kind == "bow":
        x = slant(th, fore, 15.0); y = fore - x * fore.dot(x)
    else:                                  # crossbow: the front its x, the rail its z (up), so y = z cross x
        g = math.radians(45.0); x = slant(th, fore, 45.0); z = th * math.sin(g) - fore * math.cos(g); y = z.cross(x)
    comp = frame_xf(palm, x.normal(), y.normal())
    return ML.make_relative_transform(comp, hand)
def knuckles(ch, s):
    hand, palm, fore, th, along = hand_bits(ch, s)
    return ML.inverse_transform_direction(hand, along)
def angle_between(q1, q2):
    d = abs(q1.x * q2.x + q1.y * q2.y + q1.z * q2.z + q1.w * q2.w)
    return math.degrees(2.0 * math.acos(min(1.0, d)))
def mapped(tmpl_key, tmpl_grip, k, ch, s):
    """a one-handed blade put where the template is in her hand: its frame on the template's (the template's edge turned
    to her knuckles, so a one-edged blade's edge leads); a two-edged blade turned the way that keeps it nearest the template"""
    tf = ML.compose_transforms(mesh_frame(tmpl_key), tmpl_grip)                 # (the template's frame in hand space)
    if tf.rotation.rotate_vector(V(0, 1, 0)).dot(knuckles(ch, s)) < 0:
        tf = ML.compose_transforms(mesh_frame(tmpl_key, True), tmpl_grip)
    if FR[k]["single_edged"]: return grip_from(tf, k)
    a, b = grip_from(tf, k), grip_from(tf, k, True)
    return a if angle_between(a.rotation, tmpl_grip.rotation) <= angle_between(b.rotation, tmpl_grip.rotation) else b


def copy_def(wd):
    n = unreal.RDWeaponDef(); n.import_text(wd.export_text()); return n


def cycle(speed): return 1.6 - (speed - 1) * 1.05 / 9.0


def finish(wd, w, sound):
    """the table's numbers on a hero's weapon"""
    starts = list(wd.attack_starts) or [0.0] * len(wd.attacks); ends = list(wd.attack_ends)
    seg = [(ends[i] if i < len(ends) and ends[i] > 0 else unreal.AnimationLibrary.get_sequence_length(wd.attacks[i])) - (starts[i] if i < len(starts) else 0.0)
           for i in range(len(wd.attacks))]
    wd.name = w["name"]; wd.item = w["name"]
    wd.damage = 8.0 + 3.0 * w["damage"]
    wd.play_rate = max(0.35, min(2.6, (sum(seg) / len(seg)) / cycle(w["speed"])))
    wd.durability = float(w["durability"]); wd.speed_rating = w["speed"]; wd.damage_rating = w["damage"]; wd.weapon_type = w["type"]
    wd.sound_key = sound; wd.mana_cost = 0.0; wd.alongside = False; wd.icon = "None"
    wd.holster_bone = "None"; wd.off_hand_holster_bone = "None"
    return wd


# ---- the level
if not unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world().get_path_name().startswith(MAP + "."):
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
gen = next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
heroes = {str(h.name): h for h in gen.get_editor_property("heroes")}
clips, times = {}, {}
for hero, ch in CH.items():
    clips[hero], times[hero] = import_clips(ch)
    print("W5LEVEL clips", hero, sorted(clips[hero]))
tmpl = {"Warrior": heroes["Warrior"].weapons[0], "Warlock": heroes["Warlock"].weapons[0], "Rogue": heroes["Rogue"].weapons[0], "RogueXbow": heroes["Rogue"].weapons[1]}
twohand = {}
for hero in ("Warrior", "Warlock"):
    tw = times[hero]["TwoHand"]; at_ = []
    for name in ("W5_TwoHand1", "W5_TwoHand2", "W5_TwoHand3"):
        a = clips[hero][name]; L, hit = fastest(a, "hand_r", tw[name]["wind"])
        at_.append((a, hit, min(L, hit + 0.45)))
    twohand[hero] = at_
    print("W5LEVEL", hero, "two-handed cuts land at", [round(x[1], 2) for x in at_], "of", [round(unreal.AnimationLibrary.get_sequence_length(x[0]), 2) for x in at_])
bow_bolt = ML.compose_transforms(unreal.Transform(V(0, 0, 0), ML.make_rot_from_zx(V(1, 0, 0), V(0, 0, -1)), V(BOW["thick"], BOW["thick"], BOW["len_scale"])),
                                 unreal.Transform(V(-48.28 * BOW["len_scale"], 0, 0), unreal.Rotator(0, 0, 0), V(1, 1, 1)))
items = [it for it in gen.get_editor_property("items") if it.kind != unreal.RDItemKind.WEAPON]
report = []
for w in T["weapons"]:
    k = key_of(w); typ = w["type"]; fr = FR[k]; mesh = unreal.load_asset(fr["mesh"]); assert mesh, fr["mesh"]
    fits = []
    for hero in ("Warrior", "Warlock", "Rogue"):
        allowed = WHO[hero]
        if allowed != "all" and typ not in allowed: continue
        ch = CH[hero]
        if typ in ONE_HAND:
            if hero == "Rogue":
                wd = copy_def(tmpl["Rogue"]); wd.mesh = mesh; wd.off_hand_mesh = mesh
                wd.grip = mapped("template_dagger", tmpl["Rogue"].grip, k, ch, "r"); wd.off_hand_grip = mapped("template_dagger", tmpl["Rogue"].off_hand_grip, k, ch, "l")
                sound = "Daggers"
            else:
                wd = copy_def(tmpl[hero]); wd.mesh = mesh
                wd.grip = mapped("template_sword", tmpl[hero].grip, k, ch, "r")
                sound = SOUND.get(typ, "Sword")
            wd.reach, wd.arc = REACH[typ]
        elif typ == "two handed sword":
            wd = copy_def(tmpl[hero]); wd.mesh = mesh; wd.off_hand_mesh = None
            wd.grip = grip_from(hand_frame(ch, "r", "twohand"), k)
            wd.attacks = [x[0] for x in twohand[hero]]; wd.attack_starts = [0.0] * 3; wd.attack_ends = [x[2] for x in twohand[hero]]; wd.hit_times = [x[1] for x in twohand[hero]]
            wd.reach, wd.arc = REACH[typ]; sound = SOUND[typ]
        elif fr["kind"] == "bow":
            wd = copy_def(tmpl["RogueXbow"]); wd.mesh = mesh; wd.hand_bone = "hand_l"; wd.off_hand_mesh = None
            wd.grip = grip_from(hand_frame(ch, "l", "bow"), k)
            a = clips[hero]["W5_Bow"]; tb = times[hero]["Bow"]
            wd.attacks = [a]; wd.attack_starts = [0.0]; wd.attack_ends = [min(unreal.AnimationLibrary.get_sequence_length(a), tb["length"] - 0.2)]; wd.hit_times = [tb["release"]]
            o3 = vec(fr["origin"]) + vec(fr["y"]) * 3.0
            wd.bolt_muzzle = o3; wd.bolt_mesh_transform = bow_bolt; wd.show_loaded_bolt = False
            wd.reach = BOW["reach"]; wd.bolt_speed = BOW["speed"]; sound = "Crossbow"
            if hero != "Rogue": wd.get_hit, wd.death = tmpl[hero].get_hit, tmpl[hero].death
        else:   # crossbow
            wd = copy_def(tmpl["RogueXbow"]); wd.mesh = mesh
            wd.grip = grip_from(hand_frame(ch, "r", "crossbow"), k)
            if hero != "Rogue":
                a = clips[hero]["W5_Shoot"]; ts = times[hero]["Shoot"]
                wd.attacks = [a]; wd.attack_starts = [0.0]; wd.attack_ends = [min(unreal.AnimationLibrary.get_sequence_length(a), ts["length"])]; wd.hit_times = [ts["release"]]
                wd.get_hit, wd.death = tmpl[hero].get_hit, tmpl[hero].death
            wd.bolt_muzzle = vec(fr["muzzle"])
            front = vec(fr["x"])
            wd.loaded_bolt_transform = ML.compose_transforms(tmpl["RogueXbow"].bolt_mesh_transform, unreal.Transform(vec(fr["loaded_tip"]), ML.make_rot_from_x(front), V(1, 1, 1)))
            wd.reach = 2600.0 if k == "Crossbow" else 2800.0; sound = "Crossbow"
        finish(wd, w, sound)
        f = unreal.RDWeaponFit(); f.hero = hero; f.weapon = wd; fits.append(f)
        report.append(f"W5LEVEL {w['name']:22s} {hero:8s} {typ:25s} damage {wd.damage:4.0f}  rate {wd.play_rate:4.2f} (an attack every {cycle(w['speed']):.2f} s)  reach {wd.reach:5.0f}  durability {wd.durability:3.0f}  sound {sound}")
    it = unreal.RDItemDef(); it.name = w["name"]; it.kind = unreal.RDItemKind.WEAPON; it.amount = float(w["durability"]); it.weight = float(w["rarity"])
    it.tiers = list(w["tiers"]); it.looks = f"{typ}  ·  speed {w['speed']} / 10  ·  damage {w['damage']} / 10"; it.weapon_fits = fits
    items.append(it)
gen.set_editor_property("items", items)
gen.set_editor_property("max_tier", 5)
gen.set_editor_property("loot_all_sections", True)
# the test's camera for pictures of her holding the weapons (a test cannot spawn into a play world: placed here, found by
# its tag RDM5_WeaponCam; 834's face camera went with the old level)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
RT = "/Game/RandomDungeon/Magic5/RT_RDM5_Weapons"
rt = unreal.load_asset(RT) or at.create_asset("RT_RDM5_Weapons", "/Game/RandomDungeon/Magic5", unreal.TextureRenderTarget2D, unreal.TextureRenderTargetFactoryNew())
rt.set_editor_property("size_x", 960); rt.set_editor_property("size_y", 720)
rt.set_editor_property("render_target_format", unreal.TextureRenderTargetFormat.RTF_RGBA8)
rt.set_editor_property("clear_color", unreal.LinearColor(0, 0, 0, 1)); eal.save_loaded_asset(rt, only_if_is_dirty=False)
for a in eas.get_all_level_actors():
    if a.actor_has_tag("RDM5_WeaponCam"): eas.destroy_actor(a)
cam = eas.spawn_actor_from_class(unreal.SceneCapture2D, V(0, 0, -6000))
cam.tags = ["RDM5_WeaponCam"]; cam.set_actor_label("RDM5_WeaponCam")
cc = cam.capture_component2d
cc.set_editor_property("texture_target", rt); cc.set_editor_property("capture_every_frame", False); cc.set_editor_property("capture_on_movement", False)
cc.set_editor_property("fov_angle", 50.0); cc.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
for line in report: print(line)
back = gen.get_editor_property("items")
print("W5LEVEL", MAP, "| items", len(back), "of which weapons", sum(1 for i in back if i.kind == unreal.RDItemKind.WEAPON),
      "| fits", sum(len(i.weapon_fits) for i in back), "| max tier", gen.get_editor_property("max_tier"), "| loot in every section", gen.get_editor_property("loot_all_sections"))
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
