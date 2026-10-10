"""Meshy anims: rename to AS_Meshy_*, root motion flags, blendspace (idle 0 / walk 140 / run 430, no snapping),
AnimBP idle sequence -> Idle_3, foot-IK control rig alpha 0, montages for actions/idle variants/turns."""
import re, math, unreal
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
C = "/Game/Meshy/Character"; A = "/Game/Meshy/Anims"; LA = "/Game/Meshy/Locomotion/Anims"
ROOT_MOTION = {"Idle_Turn_Left", "Idle_Turn_Right", "Step_Step_Turn_Kick", "Leg_Sweep", "walking_2"}
anims = {}
for p in eal.list_assets(C, recursive=False):
    n = p.split(".")[-1]
    if n.startswith("SK_Meshy_BipedArmature_A_"):
        clip = n.replace("SK_Meshy_BipedArmature_A_", "")
        dst = f"{A}/AS_Meshy_{clip}"
        if not eal.does_asset_exist(dst): eal.rename_asset(p.split(".")[0], dst)
for p in eal.list_assets(A, recursive=False):
    n = p.split(".")[-1]
    if n.startswith("AS_Meshy_"): anims[n.replace("AS_Meshy_", "")] = unreal.load_asset(p.split(".")[0])
print("anims", sorted(anims))
for clip, a in anims.items():
    a.set_editor_property("enable_root_motion", clip in ROOT_MOTION)
    if clip in ROOT_MOTION:
        a.set_editor_property("force_root_lock", False)
    eal.save_loaded_asset(a)
# root motion sanity: root yaw / travel over the turn and kick clips
APE = unreal.AnimPoseExtensions
for clip in ("Idle_Turn_Left", "Idle_Turn_Right", "Step_Step_Turn_Kick"):
    a = anims[clip]; L = unreal.AnimationLibrary.get_sequence_length(a)
    p0 = APE.get_bone_pose(APE.get_anim_pose_at_time(a, 0.0, unreal.AnimPoseEvaluationOptions()), "root", unreal.AnimPoseSpaces.WORLD)
    p1 = APE.get_bone_pose(APE.get_anim_pose_at_time(a, L, unreal.AnimPoseEvaluationOptions()), "root", unreal.AnimPoseSpaces.WORLD)
    print(clip, "root start", p0.translation, p0.rotation.rotator(), "end", p1.translation, p1.rotation.rotator())

# ---- blendspace ----
bs = unreal.load_asset(f"{LA}/BS_Idle_Walk_Run_Meshy")
ps = []
for p in bs.get_editor_property("blend_parameters"):
    t = p.export_text().replace("bSnapToGrid=True", "bSnapToGrid=False")
    if "Speed" in t: t = re.sub(r"Max=[0-9.]+", "Max=430.000000", t); t = re.sub(r"GridNum=\d+", "GridNum=43", t)
    q = unreal.BlendParameter(); q.import_text(t); ps.append(q)
bs.set_editor_property("blend_parameters", ps)
walk, run, idle = anims["Walking"], anims["Running"], anims["Idle_3"]   # Walking_Woman is authored ~90 deg off-axis
# deterministic grid: 9 directions x (idle 0, walk 140, run 430); her clips are forward-only, and with
# orient-to-movement the AnimBP clamps Direction to +-45, so every column uses the same clip per speed
template = bs.get_editor_property("sample_data")[0].export_text()
out = []
for x in range(-180, 181, 45):
    for clip, y in ((idle, 0.0), (walk, 140.0), (run, 430.0)):
        t = re.sub(r'Animation="[^"]*"', f'Animation="/Script/Engine.AnimSequence\'{clip.get_path_name()}\'"', template)
        t = re.sub(r"SampleValue=\(X=[-0-9.]+,Y=[-0-9.]+", f"SampleValue=(X={x:.6f},Y={y:.6f}", t)
        n = unreal.BlendSample(); n.import_text(t); out.append(n)
bs.set_editor_property("sample_data", out)
bs.modify()
if hasattr(bs, "post_edit_change"): bs.post_edit_change()          # rebuilds the runtime blend grid
else: print("WARNING: no post_edit_change on BlendSpace")
eal.save_loaded_asset(bs)
print("BS samples", sorted({(s.export_text().split("AS_Meshy_")[1].split(".")[0] if "AS_Meshy_" in s.export_text() else "?", s.export_text().split("Y=")[1][:5]) for s in bs.get_editor_property("sample_data")}))

# ---- AnimBP: idle sequence + disable foot-IK rig ----
abp = unreal.load_asset(f"{LA}/ABP_Unarmed_Meshy1" if eal.does_asset_exist(f"{LA}/ABP_Unarmed_Meshy1") else f"{LA}/ABP_Unarmed_Meshy")
print("configuring", abp.get_path_name())
for g in T.list_graphs(abp):
    for n in T.find_nodes(g, ""):
        c = n.get_class().get_name()
        if c == "AnimGraphNode_SequencePlayer" and g.get_name() == "Idle":
            nd = n.get_editor_property("node"); t = nd.export_text()
            t = re.sub(r"Sequence=\"[^\"]*\"", f"Sequence=\"/Script/Engine.AnimSequence'{idle.get_path_name()}'\"", t)
            nd.import_text(t); n.set_editor_property("node", nd); print("idle state ->", idle.get_name())
        if c == "AnimGraphNode_ControlRig":
            nd = n.get_editor_property("node"); t = re.sub(r"Alpha=[0-9.]+", "Alpha=0.000000", nd.export_text())
            nd.import_text(t); n.set_editor_property("node", nd)
            i = T.get_node_infos([n])[0]
            for p in i.input_pins:
                if str(p.name) == "Alpha": T.set_pin_value(p.pin_id, "0.0")
            print("foot IK alpha 0")
print("compile", unreal.BlueprintEditorLibrary.compile_blueprint(abp)); eal.save_loaded_asset(abp)
for p in eal.list_assets(LA, recursive=False): eal.save_asset(p.split(".")[0], True)

# ---- montages (DefaultSlot) ----
def montage(clip):
    path = f"{A}/AM_Meshy_{clip}"
    if eal.does_asset_exist(path): return unreal.load_asset(path)
    f = unreal.AnimMontageFactory(); f.set_editor_property("source_animation", anims[clip])
    m = at.create_asset(f"AM_Meshy_{clip}", A, unreal.AnimMontage, f)
    m.set_editor_property("blend_in", m.get_editor_property("blend_in"))
    eal.save_loaded_asset(m); return m
for clip in ("Left_Jab_from_Guard", "Left_Short_Hook_from_Guard", "Boxing_Guard_Prep_Straight_Punch", "Leg_Sweep",
             "Step_Step_Turn_Kick", "Idle_Turn_Left", "Idle_Turn_Right", "Idle_4", "Idle_5", "Idle_6", "Idle_7", "walking_2", "Run_02", "RunFast"):
    m = montage(clip); print("montage", m.get_name(), round(m.get_play_length(), 2))
