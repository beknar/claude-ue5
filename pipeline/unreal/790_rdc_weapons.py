"""random_dungeoncombat_level: jrpg-fem5-tripo's three melee weapons, how she holds them and the clips she wields them
with. Meshes from the Medieval_Weapons pack; each weapon takes its clips from a Fab animation pack made for it (all on
the packs' own UE4-style mannequin):
  Sword (+ shield)   Weapon_Shield_Animations      one-handed cuts
  Spear (+ shield)   Spear_And_Shield_Animations   thrusts
  Axe                Animations_Warrior            heavy swings
For each pack: an IK rig for its mannequin (auto-generated), a retargeter onto her rig (IK_JRPG_Fem5_Auto, from 610), and
the weapon's attack, flinch and death clips retargeted to /Game/RandomDungeon/Combat/Anims (root locked: she attacks
on the spot). Every attack clip is then measured on her skeleton: the blow lands where her weapon hand moves fastest.
Grips: her skeleton has no fingers, so they are computed from her reference pose, in which her arms are out to the
sides with the palms down: a handle lies across the palm, at right angles to the forearm, its business end pointing
the way the thumb does (forward), a blade's edge leading away along the forearm; a shield lies along the left forearm,
its top toward the elbow (upright when her arm hangs), its face turned the way the back of the hand faces.
Where the hand closes (`hand_z`) is data, and it is checked against the mesh: there the weapon must be a handle, round
and thin, and the business end is the longer part from there. The meshes' origins are not where one would think: the
sword's is the tip of its blade (the hilt is at z 65 to 87), and a grip written for "blade +Z from the origin" had
her holding the blade a hand from its tip.
Writes SourceArt/random_dungeon_combat/weapons.json (meshes, grips, damage / reach / arc / play rate, clips with their
lengths and hit times) for the level script, 791. Idempotent (rigs, retargeters and clips are made again).
Args: [grips]   (grips: only the grips are computed again and written into the existing weapons.json; run 791 after)"""
import json, os, sys, unreal
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions; ML = unreal.MathLibrary
V = unreal.Vector
OUT = "/Game/RandomDungeon/Combat"; ANIMS = OUT + "/Anims"; RIGS = OUT + "/Rigs"
JSON = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_combat\weapons.json"
tgt_mesh = unreal.load_asset("/Game/JRPG/Character/SK_JRPG_Fem5"); tgt_rig = unreal.load_asset("/Game/JRPG/Rigs/IK_JRPG_Fem5_Auto")
assert tgt_mesh and tgt_rig
MW = "/Game/Medieval_Weapons/Meshes/VOL2/"
# weapon: mesh (long axis Z), where along it the hand closes (cm from the mesh origin, on the handle: see handle_end), shield; what it does: damage a
# blow, reach (cm from her to the monster's capsule), arc in front of her (degrees), play rate of its clips, how long
# after the blow a clip is cut (s: the recovery back to idle is blended out, so the next blow can follow);
# pack, clip prefix, attacks, flinch, death
SETS = [
    {"name": "Sword", "mesh": MW + "SM_Sword_1", "hand_z": 69.0, "shield": MW + "SM_Shield_1", "damage": 22.0, "reach": 170.0, "arc": 130.0, "rate": 1.25, "after": 0.55,
     "pack": "Weapon_Shield_Animations", "prefix": "Anim_Weapon_Shield_", "attacks": ["Attack_01", "Attack_03", "Attack_08"], "flinch": "Get_Hit", "death": "Dead_01"},
    {"name": "Spear", "mesh": MW + "SM_Spear", "hand_z": 95.0, "shield": MW + "SM_Shield_1", "damage": 17.0, "reach": 260.0, "arc": 70.0, "rate": 1.3, "after": 0.55,
     "pack": "Spear_And_Shield_Animations", "prefix": "Anim_Spear_Shield_", "attacks": ["Attack_01", "Attack_02", "Attack_04"], "flinch": "Get_Hit_01", "death": "Dead_01"},
    {"name": "Axe", "mesh": MW + "SM_Axe", "hand_z": 7.0, "shield": None, "damage": 36.0, "reach": 190.0, "arc": 150.0, "rate": 1.2, "after": 0.7,
     "pack": "Animations_Warrior", "prefix": "Anim_Warrior_", "attacks": ["Attack_1", "Attack_2", "Attack_4"], "flinch": "Get_Hit_1", "death": "Dead_1"},
]
SHIELD_SCALE = 0.8
ar = unreal.AssetRegistryHelpers.get_asset_registry()
def make(cls, fac, name, folder):
    p = f"{folder}/{name}"
    if eal.does_asset_exist(p): eal.delete_asset(p)
    return at.create_asset(name, folder, cls, fac) or unreal.load_asset(p)
def find(pack, name):
    for a in ar.get_assets_by_path("/Game/" + pack, recursive=True):
        if str(a.asset_name) == name and str(a.asset_class_path.asset_name) == "AnimSequence": return a
    raise RuntimeError(f"{pack}: no clip {name}")
o = unreal.AnimPoseEvaluationOptions()
def measure(anim):
    """length and the time her weapon hand moves fastest (component space, the pelvis's own travel taken out)"""
    L = unreal.AnimationLibrary.get_sequence_length(anim); n = max(30, int(L * 60)); pts = []
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(anim, L * k / n, o)
        h = APE.get_bone_pose(p, "hand_r", unreal.AnimPoseSpaces.WORLD).translation; q = APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.WORLD).translation
        pts.append(V(h.x - q.x, h.y - q.y, h.z - q.z))
    sp = [(pts[k + 1] - pts[k]).length() / (L / n) for k in range(n)]
    sm = [sum(sp[max(0, k - 2):k + 3]) / len(sp[max(0, k - 2):k + 3]) for k in range(n)]           # (smoothed over 5 samples)
    k = max(range(n), key=lambda i: sm[i])
    return L, L * (k + 0.5) / n, sm[k]
# ---- grips, from her reference pose (component space: she faces +Y, her right arm points along -X)
ref = APE.get_reference_pose(tgt_mesh.skeleton)
bone = lambda n: APE.get_bone_pose(ref, n, unreal.AnimPoseSpaces.WORLD)
def xf(t): r = t.rotation.rotator(); return {"loc": [t.translation.x, t.translation.y, t.translation.z], "rot": [r.roll, r.pitch, r.yaw], "scale": [t.scale3d.x, t.scale3d.y, t.scale3d.z]}
def handle_end(path, hand_z):
    """+1 / -1: which way along the mesh's Z the business end lies from the hand (the longer part). Fails unless the
    mesh is a handle where the hand closes: round (as wide as it is deep) and thin."""
    m = unreal.load_asset(path); vs = []
    for sec in range(m.get_num_sections(0)): vs += list(unreal.ProceduralMeshLibrary.get_section_from_static_mesh(m, 0, sec)[0])
    s = [v for v in vs if abs(v.z - hand_z) <= 3.0]
    assert s, f"{path}: nothing of the mesh at z {hand_z}"
    ex = max(v.x for v in s) - min(v.x for v in s); ey = max(v.y for v in s) - min(v.y for v in s)
    assert max(ex, ey) < 7.5 and max(ex, ey) < 1.8 * max(min(ex, ey), 0.1), f"{path}: no handle at z {hand_z} (the mesh is {ex:.1f} x {ey:.1f} cm there)"
    b = m.get_bounding_box()
    print(f"  {os.path.basename(path)}: handle {ex:.1f} x {ey:.1f} cm at z {hand_z:.0f}, mesh z {b.min.z:.0f}..{b.max.z:.0f}, business end toward {'+Z' if b.max.z - hand_z >= hand_z - b.min.z else '-Z'}")
    return 1.0 if b.max.z - hand_z >= hand_z - b.min.z else -1.0
def weapon_grip(path, hand_z):
    """the weapon mesh (edge along X, long axis Z) relative to hand_r"""
    hand = bone("hand_r"); fore = (hand.translation - bone("lowerarm_r").translation).normal()
    thumb = V(0, 1, 0); thumb = (thumb - fore * thumb.dot(fore)).normal()
    palm = hand.translation + fore * 6.5 + V(0, 0, -2.5)        # in the closed hand: past the wrist, a little under the bones
    rot = ML.make_rot_from_xz(fore, thumb * handle_end(path, hand_z))
    return ML.make_relative_transform(unreal.Transform(palm - ML.get_up_vector(rot) * hand_z, rot, V(1, 1, 1)), hand)
def shield_grip(path):
    """the shield mesh (face +Y, tall along Z: its flat top at +Z, its point at -Z) relative to lowerarm_l"""
    elbow = bone("lowerarm_l"); hand = bone("hand_l").translation
    fore = (hand - elbow.translation).normal(); back = V(0, 0, 1); back = (back - fore * back.dot(fore)).normal()
    w = unreal.Transform(elbow.translation + (hand - elbow.translation) * 0.55 + back * 6.0, ML.make_rot_from_zy(fore * -1.0, back), V(SHIELD_SCALE, SHIELD_SCALE, SHIELD_SCALE))
    b = unreal.load_asset(path).get_bounds().origin
    w = unreal.Transform(ML.transform_location(w, V(-b.x, -b.y, -b.z)), w.rotation.rotator(), w.scale3d)
    return ML.make_relative_transform(w, elbow)
if "grips" in sys.argv:
    res = json.load(open(JSON))
    for s in SETS:
        e = res["weapons"][s["name"]]
        e["grip"] = xf(weapon_grip(s["mesh"], s["hand_z"])); e["shield_grip"] = xf(shield_grip(s["shield"])) if s["shield"] else None
    json.dump(res, open(JSON, "w"), indent=1); print("grips saved", JSON)
    import gc
    for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
    gc.collect()
    raise SystemExit
res = {"order": [s["name"] for s in SETS], "weapons": {}}
for s in SETS:
    weapon, pack, prefix = s["name"], s["pack"], s["prefix"]
    assert unreal.load_asset(s["mesh"]), s["mesh"]
    src_mesh = unreal.load_asset(f"/Game/{pack}/Mesh/SK_Mannequin"); assert src_mesh, pack
    rig = make(unreal.IKRigDefinition, unreal.IKRigDefinitionFactory(), f"IK_RDC_{weapon}_Source", RIGS)
    c = unreal.IKRigController.get_controller(rig); c.set_skeletal_mesh(src_mesh)
    ok = c.apply_auto_generated_retarget_definition()
    try: c.apply_auto_fbik()
    except Exception: pass
    eal.save_loaded_asset(rig)
    rtg = make(unreal.IKRetargeter, unreal.IKRetargetFactory(), f"RTG_RDC_{weapon}_To_Fem5", RIGS)
    rc = unreal.IKRetargeterController.get_controller(rtg)
    rc.add_default_ops()
    rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, rig); rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
    rc.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, src_mesh); rc.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, tgt_mesh)
    rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, rig); rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
    rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
    rm = rc.get_op_controller(rc.get_index_of_op_by_name("Root Motion"))       # (add_default_ops leaves it without bones)
    rm.set_source_root_bone("root"); rm.set_target_root_bone("root"); rm.set_target_pelvis_bone("pelvis")
    try: rc.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
    except Exception as e: print("  align", e)
    eal.save_loaded_asset(rtg)
    names = [prefix + n for n in s["attacks"] + [s["flinch"], s["death"]]]
    for n in names:                                # (a clean slate: the batch does not replace what an editor session still holds)
        if eal.does_asset_exist(f"{ANIMS}/{n}_Fem5"): eal.delete_asset(f"{ANIMS}/{n}_Fem5")
    inp = unreal.IKRetargetBatchOperationInputs()
    inp.set_editor_property("assets_to_retarget", [find(pack, n) for n in names])
    inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
    inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", "_Fem5")
    inp.set_editor_property("target_path", ANIMS); inp.set_editor_property("include_referenced_assets", False)
    inp.set_editor_property("overwrite_existing_files", True)
    out = [str(r.package_name) for r in unreal.IKRetargetBatchOperation.run_batch_retarget(inp)]
    for n in names:
        p = f"{ANIMS}/{n}_Fem5"; a = unreal.load_asset(p); assert a, p
        a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True)
        eal.save_loaded_asset(a, False)
    e = {k: s[k] for k in ("mesh", "shield", "damage", "reach", "arc", "rate", "pack")}
    e.update({"grip": xf(weapon_grip(s["mesh"], s["hand_z"])), "hand_bone": "hand_r", "shield_bone": "lowerarm_l", "shield_grip": xf(shield_grip(s["shield"])) if s["shield"] else None,
              "flinch": f"{ANIMS}/{prefix}{s['flinch']}_Fem5", "death": f"{ANIMS}/{prefix}{s['death']}_Fem5", "attacks": []})
    for n in s["attacks"]:
        p = f"{ANIMS}/{prefix}{n}_Fem5"; L, hit, speed = measure(unreal.load_asset(p))
        e["attacks"].append({"clip": p, "length": round(L, 3), "hit": round(hit, 3), "end": round(min(L, hit + s["after"]), 3), "hand_speed": round(speed)})
    res["weapons"][weapon] = e
    secs = [x["end"] / s["rate"] for x in e["attacks"]]
    print(f"{weapon}: {len(out)} clips retargeted from {pack} (rig ok={ok}) | " + ", ".join(f"{os.path.basename(x['clip'])} hit {x['hit']:.2f} s, cut at {x['end']:.2f} of {x['length']:.2f} s" for x in e["attacks"])
          + f" | {s['damage']:.0f} damage a blow, a blow every {sum(secs) / len(secs):.2f} s, reach {s['reach']:.0f} cm, arc {s['arc']:.0f}")
os.makedirs(os.path.dirname(JSON), exist_ok=True); json.dump(res, open(JSON, "w"), indent=1)
print("saved", JSON)
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
