"""The Martial Artist's parts that follow her rig, shared by 872 (her whole hero) and 917 (her rig changed: MartialArtist3,
2026-11-10): her clips measured (each blow where a hand or foot is fastest), her flinch and death retargeted from
Animations_Warrior (822's source rig), her knife grips from her reference pose (822's dagger grip, 855's frame mapping), and
her dungeon character (BP_MA_MartialArtistCharacter, a child of 620's BP_JRPGMartialArtistCharacter, a 36 cm capsule).
Imported by the stages (pipeline/unreal on sys.path), not run."""
import math, unreal
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions; ML = unreal.MathLibrary
V = unreal.Vector
CH = "MartialArtist"
ANIMS = "/Game/RandomDungeon/Martial/Anims"; RIGS = "/Game/RandomDungeon/Martial/Rigs"
DAGGER, DAGGER_Z = "/Game/Medieval_Weapons/Meshes/VOL2/SM_Dagger", 28.5
FLINCH_DEATH = ["Anim_Warrior_Get_Hit_1", "Anim_Warrior_Dead_1"]
_o = unreal.AnimPoseEvaluationOptions()


def make(cls, fac, name, folder):
    p = f"{folder}/{name}"
    if eal.does_asset_exist(p): eal.delete_asset(p)
    return at.create_asset(name, folder, cls, fac) or unreal.load_asset(p)


def clip(n):
    """her clip of that name, its root locked"""
    p = f"/Game/JRPG/{CH}Anims/AS_{CH}_{n}"; a = unreal.load_asset(p); assert a, p
    a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
    return a


def speeds(anim, bones):
    """per sample: the fastest of the bones (relative to the pelvis), smoothed over 5 samples; the sample's time"""
    L = unreal.AnimationLibrary.get_sequence_length(anim); n = max(30, int(L * 60)); pts = {b: [] for b in bones}
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(anim, L * k / n, _o); q = APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.WORLD).translation
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


def flinch_death(tgt_mesh, tgt_rig):
    """Animations_Warrior's Get_Hit_1 and Dead_1 retargeted onto her rig (822's source rig): (flinch, death)"""
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
    for n in FLINCH_DEATH:
        if eal.does_asset_exist(f"{ANIMS}/{n}_{CH}"): eal.delete_asset(f"{ANIMS}/{n}_{CH}")
    inp = unreal.IKRetargetBatchOperationInputs()
    inp.set_editor_property("assets_to_retarget", [find("Animations_Warrior", n) for n in FLINCH_DEATH])
    inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
    inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", "_" + CH)
    inp.set_editor_property("target_path", ANIMS); inp.set_editor_property("include_referenced_assets", False)
    inp.set_editor_property("overwrite_existing_files", True)
    unreal.IKRetargetBatchOperation.run_batch_retarget(inp)
    out = [unreal.load_asset(f"{ANIMS}/{n}_{CH}") for n in FLINCH_DEATH]
    for a in out:
        assert a; a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
    return out[0], out[1]


class Grips:
    """her knife grips from her reference pose: dagger_grip(side) the template dagger (822's), mapped(template grip, the table
    weapon's key, side) another short blade by 855's frame mapping (fr: weapon_frames.json's weapons; tilt: the grip's slant)"""
    def __init__(self, tgt_mesh, fr, tilt):
        self.ref = APE.get_reference_pose(tgt_mesh.skeleton); self.fr = fr; self.tilt = tilt
        self.dm = unreal.load_asset(DAGGER); bb = self.dm.get_bounding_box()
        self.dend = 1.0 if bb.max.z - DAGGER_Z >= DAGGER_Z - bb.min.z else -1.0

    def bone(self, n): return APE.get_bone_pose(self.ref, n, unreal.AnimPoseSpaces.WORLD)

    def hand_bits(self, s):
        hand = self.bone(f"hand_{s}"); h = hand.translation
        fore = (h - self.bone(f"lowerarm_{s}").translation).normal()
        th = self.bone(f"thumb_01_{s}").translation - h; along = (self.bone(f"middle_01_{s}").translation - h).normal()
        th = th - along * th.dot(along); th = (th - fore * th.dot(fore)).normal()
        return hand, h + fore * 6.5 + V(0, 0, -2.5), fore, th, along

    @staticmethod
    def slant(th, fore, deg):
        g = math.radians(deg); return (th * math.cos(g) + fore * math.sin(g)).normal()

    def dagger_grip(self, s):
        hand, palm, fore, th, along = self.hand_bits(s)
        rot = ML.make_rot_from_zx(self.slant(th, fore, self.tilt) * self.dend, fore)
        return ML.make_relative_transform(unreal.Transform(palm - ML.get_up_vector(rot) * DAGGER_Z, rot, V(1, 1, 1)), hand)

    def mesh_frame(self, k, flip=False):
        f = self.fr[k]; y = V(*f["y"]) * (-1.0 if flip else 1.0)
        return unreal.Transform(V(*f["origin"]), ML.make_rot_from_xy(V(*f["x"]), y), V(1, 1, 1))

    def grip_from(self, frame_in_hand, k, flip=False): return ML.compose_transforms(ML.invert_transform(self.mesh_frame(k, flip)), frame_in_hand)

    @staticmethod
    def angle_between(q1, q2):
        d = abs(q1.x * q2.x + q1.y * q2.y + q1.z * q2.z + q1.w * q2.w); return math.degrees(2.0 * math.acos(min(1.0, d)))

    def mapped(self, tmpl_grip, k, s):
        hand, palm, fore, th, along = self.hand_bits(s); kn = ML.inverse_transform_direction(hand, along)
        tf = ML.compose_transforms(self.mesh_frame("template_dagger"), tmpl_grip)
        if tf.rotation.rotate_vector(V(0, 1, 0)).dot(kn) < 0: tf = ML.compose_transforms(self.mesh_frame("template_dagger", True), tmpl_grip)
        if self.fr[k]["single_edged"]: return self.grip_from(tf, k)
        a, b = self.grip_from(tf, k), self.grip_from(tf, k, True)
        return a if self.angle_between(a.rotation, tmpl_grip.rotation) <= self.angle_between(b.rotation, tmpl_grip.rotation) else b


def character_bp():
    """BP_MA_MartialArtistCharacter: a child of 620's BP_JRPGMartialArtistCharacter (put back on it: 620 makes its parent anew),
    a 36 cm capsule"""
    G = "/Game/RandomDungeon/Blueprints"; CHP = f"{G}/BP_MA_MartialArtistCharacter"
    PARENT = unreal.load_asset(f"/Game/JRPG/Game/BP_JRPG{CH}Character").generated_class()
    if not eal.does_asset_exist(CHP):
        f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", PARENT); at.create_asset(CHP.split("/")[-1], G, unreal.Blueprint, f)
    chbp = unreal.load_asset(CHP)
    if unreal.BlueprintEditorLibrary.get_blueprint_parent_class(chbp) != PARENT: unreal.BlueprintEditorLibrary.reparent_blueprint(chbp, PARENT)
    unreal.BlueprintEditorLibrary.compile_blueprint(chbp)
    cdo = unreal.get_default_object(chbp.generated_class())
    cdo.get_component_by_class(unreal.CapsuleComponent).set_editor_property("capsule_radius", 36.0)
    # (her mesh and AnimBP from her parent's: a child keeps what its inherited mesh component held when her mesh was deleted
    # (917 clean) as overrides of its own, none and none, and she had no body to play anything on (868 martial, 2026-11-10))
    pm = unreal.get_default_object(PARENT).get_component_by_class(unreal.SkeletalMeshComponent)
    cm = cdo.get_component_by_class(unreal.SkeletalMeshComponent)
    cm.set_editor_property("skeletal_mesh_asset", pm.get_skeletal_mesh_asset())
    cm.set_editor_property("anim_class", pm.get_editor_property("anim_class"))
    unreal.BlueprintEditorLibrary.compile_blueprint(chbp); eal.save_loaded_asset(chbp, only_if_is_dirty=False)
    cm = unreal.get_default_object(chbp.generated_class()).get_component_by_class(unreal.SkeletalMeshComponent)
    m, a = cm.get_skeletal_mesh_asset(), cm.get_editor_property("anim_class")
    assert m and a, "her character's mesh or AnimBP did not take"
    print("MA character", chbp.get_name(), "| mesh", m.get_name(), "| anim", a.get_name())
    return chbp
