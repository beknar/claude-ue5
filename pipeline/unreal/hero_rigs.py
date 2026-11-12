"""The hero menu's six and their rigs, and a pack's clips retargeted onto each, shared by 913 (the rider's clips), 921 (the swim
clips) and 922 (the viewer's export) (PR #53's review: the map was copied in all three and the retarget in two).
Every map's hero keeps her asset names (917 / 918): a new body for a hero changes nothing here."""
import unreal

eal = unreal.EditorAssetLibrary
HERO_RIG = {"Warrior": "Warrior3", "Mage": "Caster", "Warlock": "DarkCaster", "Rogue": "Rogue", "MartialArtist": "MartialArtist", "Summoner": "Summoner4"}


def make(cls, fac, name, folder):
    """the asset of that name, set up again by the caller (an IK rig's mesh and chains, a retargeter's ops cleared); made when
    there is none. (Deleted and made again it failed once the retargeters pointing at the rig had been loaded: delete_asset
    said yes, the package stayed, and create_asset refused the name ("already exists"))"""
    p = f"{folder}/{name}"
    a = unreal.load_asset(p) if eal.does_asset_exist(p) else None
    if isinstance(a, cls): return a
    if a is not None: eal.delete_asset(p)
    return unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, cls, fac)


def retarget_onto_heroes(src_mesh, clip_paths, rigs, anims, tag, log="RETARGET"):
    """the clips (asset paths) on src_mesh's skeleton retargeted onto every hero's rig: an IK rig on the source mesh
    (IK_<tag>_Source), a retargeter per hero onto IK_JRPG_<rig>_Auto (RTG_<tag>_To_<rig>), the clips into <anims>/<rig> as
    <clip>_<rig> with their root locked. -> {hero: (rig, [the clips made], None or why none were)}"""
    rig = make(unreal.IKRigDefinition, unreal.IKRigDefinitionFactory(), f"IK_{tag}_Source", rigs)
    c = unreal.IKRigController.get_controller(rig); c.set_skeletal_mesh(src_mesh); c.apply_auto_generated_retarget_definition()
    try: c.apply_auto_fbik()
    except Exception: pass
    eal.save_loaded_asset(rig)
    names = [p.rsplit("/", 1)[-1] for p in clip_paths]
    out_by_hero = {}
    for hero, ch in HERO_RIG.items():
        tgt_mesh = unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{ch}"); tgt_rig = unreal.load_asset(f"/Game/JRPG/Rigs/IK_JRPG_{ch}_Auto")
        if not tgt_mesh or not tgt_rig: out_by_hero[hero] = (ch, [], f"no mesh or rig for {ch}"); continue
        rtg = make(unreal.IKRetargeter, unreal.IKRetargetFactory(), f"RTG_{tag}_To_{ch}", rigs)
        rc = unreal.IKRetargeterController.get_controller(rtg)
        rc.remove_all_ops(); rc.add_default_ops()          # (a retargeter kept from the last run: its ops made again, not doubled)
        rc.set_ik_rig(unreal.RetargetSourceOrTarget.SOURCE, rig); rc.set_ik_rig(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
        rc.set_preview_mesh(unreal.RetargetSourceOrTarget.SOURCE, src_mesh); rc.set_preview_mesh(unreal.RetargetSourceOrTarget.TARGET, tgt_mesh)
        rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.SOURCE, rig); rc.assign_ik_rig_to_all_ops(unreal.RetargetSourceOrTarget.TARGET, tgt_rig)
        rc.auto_map_chains(unreal.AutoMapChainType.FUZZY, True)
        rm = rc.get_op_controller(rc.get_index_of_op_by_name("Root Motion"))          # (add_default_ops leaves it without bones)
        rm.set_source_root_bone("root"); rm.set_target_root_bone("root"); rm.set_target_pelvis_bone("pelvis")
        try: rc.auto_align_all_bones(unreal.RetargetSourceOrTarget.TARGET)
        except Exception as e: print(log, "align", e)
        eal.save_loaded_asset(rtg)
        out = f"{anims}/{ch}"
        for n in names:
            if eal.does_asset_exist(f"{out}/{n}_{ch}"): eal.delete_asset(f"{out}/{n}_{ch}")
        inp = unreal.IKRetargetBatchOperationInputs()
        # (the batch takes the registry's records of them, not the loaded clips)
        inp.set_editor_property("assets_to_retarget", [eal.find_asset_data(p) for p in clip_paths]); inp.set_editor_property("source_mesh", src_mesh); inp.set_editor_property("target_mesh", tgt_mesh)
        inp.set_editor_property("ik_retarget_asset", rtg); inp.set_editor_property("suffix", "_" + ch); inp.set_editor_property("target_path", out)
        inp.set_editor_property("include_referenced_assets", False); inp.set_editor_property("overwrite_existing_files", True)
        unreal.IKRetargetBatchOperation.run_batch_retarget(inp)
        made = []
        for n in names:
            a = unreal.load_asset(f"{out}/{n}_{ch}")
            if not a: continue
            a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True)
            hang_cloak(a, tgt_mesh.get_editor_property("skeleton"), log)
            eal.save_loaded_asset(a, False)
            made.append(a)
        out_by_hero[hero] = (ch, made, None)
    return out_by_hero


# ---------------------------------------------------------------- her cloak in a clip retargeted here
# (the Rogue's and the Summoner's cloak have chains of their own (summoner5_cloak.py: cloak_<chain>_<bone> under spine_05);
# the retarget leaves them at rest under her upper back, and lying flat to swim she carried her cloak up out of the water like
# a sail (884 swim12's picture, 2026-11-12). As martialartist3_retarget.py's hang() does for the clips carried in Blender: the
# cloak as her upper back carries it, turned back toward hanging by one turn for the whole cloak (the one that takes her upper
# back's "down" to the component's), a share of it down each chain, so the sheet stays whole)
CLOAK_SHARE = (0.0, 0.35, 0.6, 0.8)
APE = unreal.AnimPoseExtensions
_W = unreal.AnimPoseSpaces.WORLD; _L = unreal.AnimPoseSpaces.LOCAL


def _q(u): return (u.x, u.y, u.z, u.w)
def _mul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by, aw * by - ax * bz + ay * bw + az * bx, aw * bz + ax * by - ay * bx + az * bw, aw * bw - ax * bx - ay * by - az * bz)
def _inv(a): return (-a[0], -a[1], -a[2], a[3])
def _rot(q, v):
    x, y, z, w = _mul(_mul(q, (v[0], v[1], v[2], 0.0)), _inv(q)); return (x, y, z)
def _axis_angle(ax, ang):
    import math
    n = math.sqrt(sum(c * c for c in ax)) or 1.0; s = math.sin(ang / 2.0)
    return (ax[0] / n * s, ax[1] / n * s, ax[2] / n * s, math.cos(ang / 2.0))
def _cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def _dot(a, b): return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def hang_cloak(seq, skeleton, log="CLOAK"):
    """the cloak's bone tracks in seq written anew as above; nothing on a skeleton without cloak bones. -> bones written"""
    import math, re
    ref = APE.get_reference_pose(skeleton)
    names = [str(n) for n in APE.get_bone_names(ref)]
    chains = {}
    for n in names:
        m = re.fullmatch(r"cloak_(\d+)_(\d+)", n)
        if m: chains.setdefault(int(m.group(1)), []).append((int(m.group(2)), n))
    if not chains or "spine_05" not in names: return 0
    for c in chains: chains[c].sort()
    ref_cs = {n: _q(APE.get_bone_pose(ref, n, _W).rotation) for c in chains.values() for k, n in c}
    ref_loc = {n: APE.get_bone_pose(ref, n, _L) for c in chains.values() for k, n in c}
    sp_ref = _q(APE.get_bone_pose(ref, "spine_05", _W).rotation)
    down = (0.0, 0.0, -1.0)
    nf = unreal.AnimationLibrary.get_num_frames(seq); L = seq.get_play_length()
    opts = unreal.AnimPoseEvaluationOptions()
    keys = {n: [] for n in ref_loc}
    for f in range(nf + 1):
        pose = APE.get_anim_pose_at_time(seq, min(L, f * L / max(1, nf)), opts)
        sp = _q(APE.get_bone_pose(pose, "spine_05", _W).rotation)
        Qs = _mul(sp, _inv(sp_ref))
        carried = _rot(Qs, down); ang = math.acos(max(-1.0, min(1.0, _dot(carried, down))))
        ax = _cross(carried, down)
        if math.sqrt(_dot(ax, ax)) < 0.2 * math.sin(max(ang, 1e-3)) or ang > math.radians(150):
            ax = _rot(Qs, (1.0, 0.0, 0.0)); d_ = _dot(ax, down); ax = (ax[0] - down[0] * d_, ax[1] - down[1] * d_, ax[2] - down[2] * d_)
            if _dot(_cross(carried, down), ax) < 0: ax = (-ax[0], -ax[1], -ax[2])
        for c, bones in chains.items():
            parent = sp
            for k, n in bones:
                share = CLOAK_SHARE[min(k, len(CLOAK_SHARE) - 1)]
                want = _mul(_mul(_axis_angle(ax, ang * share), Qs), ref_cs[n]) if ang > 1e-4 else _mul(Qs, ref_cs[n])
                keys[n].append(_mul(_inv(parent), want)); parent = want
    ctrl = seq.get_editor_property("controller")
    ctrl.open_bracket("the cloak hung", False)
    bad = []
    for n, rots in keys.items():
        t = ref_loc[n]
        ok = ctrl.set_bone_track_keys(n, [t.translation] * len(rots), [unreal.Quat(*r) for r in rots], [t.scale3d] * len(rots), False)
        if not ok: bad.append(n)
    ctrl.close_bracket(False)
    if bad: print(log, "cloak tracks not written on", seq.get_name(), bad[:4])
    return len(keys) - len(bad)
