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


def clip(n, ch=None):
    """her clip of that name, its root locked"""
    ch = ch or CH
    p = f"/Game/JRPG/{ch}Anims/AS_{ch}_{n}"; a = unreal.load_asset(p); assert a, p
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


def flinch_death(tgt_mesh, tgt_rig, ch=None, anims=None, rigs=None, clips=None, tag="MA"):
    """Animations_Warrior's Get_Hit_1 and Dead_1 retargeted onto her rig (822's source rig): (flinch, death). Another hero's
    (the list of 2026-11-11: the Rogue on Rogue2, the Summoner on Summoner5): her tag, folders and the clips wanted (each
    returned in that order)"""
    ch = ch or CH; anims = anims or ANIMS; rigs = rigs or RIGS; clips = clips or FLINCH_DEATH
    src_mesh = unreal.load_asset("/Game/Animations_Warrior/Mesh/SK_Mannequin"); assert src_mesh
    src_rig = unreal.load_asset("/Game/RandomDungeon/Magic3/Rigs/IK_RDM3_Warrior_Source"); assert src_rig, "822 first (its source rig)"
    rtg = make(unreal.IKRetargeter, unreal.IKRetargetFactory(), f"RTG_{tag}_Warrior_To_{ch}", rigs)
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
    for n in clips:
        if eal.does_asset_exist(f"{anims}/{n}_{ch}"): eal.delete_asset(f"{anims}/{n}_{ch}")
    inp = unreal.IKRetargetBatchOperationInputs()
    inp.set_editor_property("assets_to_retarget", [find("Animations_Warrior", n) for n in clips])
    inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
    inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", "_" + ch)
    inp.set_editor_property("target_path", anims); inp.set_editor_property("include_referenced_assets", False)
    inp.set_editor_property("overwrite_existing_files", True)
    unreal.IKRetargetBatchOperation.run_batch_retarget(inp)
    out = [unreal.load_asset(f"{anims}/{n}_{ch}") for n in clips]
    for a in out:
        assert a; a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
    return tuple(out)


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

    # ---- the Rogue's (822's) and the found bows' and crossbows' (855's) and the torch's (865's / 876's), from her own reference
    # pose (the list of 2026-11-11: the Rogue on Rogue2, the Summoner on Summoner5; never copied from the old body's)
    def crossbow_grip(self, tilt=45.0, grip=(31.0, 0.0, 0.5)):
        """822's: the template crossbow (SM_Crossbow, its front -X, the rail +Z) in her right hand, the stock along the thumb"""
        hand, palm, fore, th, along = self.hand_bits("r"); g = math.radians(tilt)
        rot = ML.make_rot_from_xz(self.slant(th, fore, tilt) * -1.0, th * math.sin(g) - fore * math.cos(g))
        X, Z = ML.get_forward_vector(rot), ML.get_up_vector(rot)
        return ML.make_relative_transform(unreal.Transform(palm - X * grip[0] - Z * grip[2], rot, V(1, 1, 1)), hand)

    def holster_thigh(self, s):
        """822's: a dagger along the outside of a thigh, blade down, the guard by the top of the thigh"""
        th = self.bone(f"thigh_{s}"); down = (self.bone(f"calf_{s}").translation - th.translation).normal()
        out = V(-1, 0, 0) if s == "r" else V(1, 0, 0); out = (out - down * out.dot(down)).normal()
        rot = ML.make_rot_from_zy(down * -1.0, out)
        at_ = th.translation + down * 16.0 + out * 8.5 + V(0, 2.0, 0)
        return ML.make_relative_transform(unreal.Transform(at_ - ML.get_up_vector(rot) * 20.0, rot, V(1, 1, 1)), th)

    def holster_back(self, bone_name):
        """822's: the crossbow across her back, its front down toward her left hip; on the bone given (the old rig's
        spine_03 was the top of three; on a rig of five the same place is spine_05's)"""
        sp = self.bone(bone_name); back = V(0, -1, 0)
        front = (V(0, 0, -1) * 0.82 + V(1, 0, 0) * 0.57).normal()
        rot = ML.make_rot_from_xz(front * -1.0, back * -1.0)
        at_ = sp.translation + back * 25.0 + V(0, 0, -6.0)
        return ML.make_relative_transform(unreal.Transform(at_ - ML.get_forward_vector(rot) * 4.0, rot, V(1, 1, 1)), sp)

    def hand_frame(self, s, kind):
        """855's: where a found weapon's frame goes in her hand (hand-bone space): 'bow' in the left, 'crossbow' in the right"""
        hand, palm, fore, th, along = self.hand_bits(s)
        if kind == "bow":
            x = self.slant(th, fore, 15.0); y = fore - x * fore.dot(x)
        else:
            g = math.radians(45.0); x = self.slant(th, fore, 45.0); z = th * math.sin(g) - fore * math.cos(g); y = z.cross(x)
        return ML.make_relative_transform(unreal.Transform(palm, ML.make_rot_from_xy(x.normal(), y.normal()), V(1, 1, 1)), hand)

    def found(self, kind, k):
        """a found bow's or crossbow's grip (its weapon_frames.json key k), 855's"""
        return self.grip_from(self.hand_frame("l" if kind == "bow" else "r", kind), k)

    def torch_grip(self, torch_mesh, tilt=20.0):
        """865's / 876's: her left fist round the torch's handle a fifth of the way up, the torch along her thumb turned
        `tilt` toward her elbow"""
        KP = unreal.ProceduralMeshLibrary; tb = torch_mesh.get_bounding_box()
        tv = [(v.x, v.y, v.z) for sec in range(torch_mesh.get_num_sections(0)) for v in KP.get_section_from_static_mesh(torch_mesh, 0, sec)[0]]
        tsz = [tb.max.x - tb.min.x, tb.max.y - tb.min.y, tb.max.z - tb.min.z]
        long_ = max(range(3), key=lambda i: tsz[i]); tmn = [tb.min.x, tb.min.y, tb.min.z][long_]; tmx = [tb.max.x, tb.max.y, tb.max.z][long_]
        def width(a, c):
            o_ = [i for i in range(3) if i != long_]; s_ = [v for v in tv if a <= v[long_] <= c]
            return max((max(v[k] for v in s_) - min(v[k] for v in s_)) for k in o_) if s_ else 0.0
        head_up = width(tmx - 0.2 * (tmx - tmn), tmx) >= width(tmn, tmn + 0.2 * (tmx - tmn))
        head = tmx if head_up else tmn; foot = tmn if head_up else tmx
        AX = {"x": V(1, 0, 0), "y": V(0, 1, 0), "z": V(0, 0, 1)}
        frame_ax = AX["xyz"[long_]] * (1.0 if head_up else -1.0)
        mid = [((tb.min.x + tb.max.x) / 2, (tb.min.y + tb.max.y) / 2, (tb.min.z + tb.max.z) / 2)[i] for i in range(3)]
        gp = list(mid); gp[long_] = foot + (head - foot) * 0.22; gp = V(*gp)
        hand = self.bone("hand_l"); fore = (hand.translation - self.bone("lowerarm_l").translation).normal()
        thumb = V(0, 1, 0); thumb = (thumb - fore * thumb.dot(fore)).normal()
        palm = hand.translation + fore * 6.5 + V(0, 0, -2.5)
        hd = (thumb * math.cos(math.radians(tilt)) - fore * math.sin(math.radians(tilt))).normal()
        rot = ML.make_rot_from_zx(hd, fore)
        other = [k for k in "xyz" if k != "xyz"[long_]][0]
        t2 = unreal.Transform(V(0, 0, 0), ML.make_rot_from_zx(frame_ax, AX[other]), V(1, 1, 1)).inverse()
        frame = ML.compose_transforms(unreal.Transform(gp * -1.0, unreal.Rotator(0, 0, 0), V(1, 1, 1)), t2)
        return ML.make_relative_transform(ML.compose_transforms(frame, unreal.Transform(palm, rot, V(1, 1, 1))), hand)


def character_bp(ch=None, child="BP_MA_MartialArtistCharacter", radius=36.0):
    """BP_MA_MartialArtistCharacter: a child of 620's BP_JRPGMartialArtistCharacter (put back on it: 620 makes its parent anew),
    a 36 cm capsule; another hero's dungeon character the same way (BP_RDM3_RogueCharacter 36, BP_SU4_SummonerCharacter 30)"""
    ch = ch or CH
    G = "/Game/RandomDungeon/Blueprints"; CHP = f"{G}/{child}"
    PARENT = unreal.load_asset(f"/Game/JRPG/Game/BP_JRPG{ch}Character").generated_class()
    if not eal.does_asset_exist(CHP):
        f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", PARENT); at.create_asset(CHP.split("/")[-1], G, unreal.Blueprint, f)
    chbp = unreal.load_asset(CHP)
    if unreal.BlueprintEditorLibrary.get_blueprint_parent_class(chbp) != PARENT: unreal.BlueprintEditorLibrary.reparent_blueprint(chbp, PARENT)
    unreal.BlueprintEditorLibrary.compile_blueprint(chbp)
    cdo = unreal.get_default_object(chbp.generated_class())
    cdo.get_component_by_class(unreal.CapsuleComponent).set_editor_property("capsule_radius", radius)
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
    print("character", chbp.get_name(), "| mesh", m.get_name(), "| anim", a.get_name())
    return chbp
