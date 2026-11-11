"""Import an animated Tripo character built by blender_numpy/tripo_build.py (generalised 240_ff2_import.py):
skeletal mesh -> /Game/JRPG/Character/SK_JRPG_<CH>, its own clips (separate FBX, imported onto that skeleton) ->
/Game/JRPG/<CH>Anims/AS_<CH>_<Clip>, material M_JRPG_<CH> (base colour; normal / metal-rough if the GLB had them; two-sided).
The mesh's shape keys come in as morph targets (printed: "morph targets").
glb [roll,pitch,yaw]: the mesh and the clips straight from the source GLB (build.json's "source") through Interchange's glTF
importer, not tripo_build's FBX pair; scaled to build.json's height and turned by the given turn (a pipeline asset of the
character's own, /Game/JRPG/Pipelines/PL_<CH>_Glb), then given the usual names (2026-11-10, MartialArtist3: Unreal read her FBX's
thighs turned 18 to 123 degrees about their own length from what the file and Blender hold, with either FBX importer, and her
stockings were wrung in every clip or torn at rest; the GLB is what the three.js viewer plays, and its import holds every bone
where the GLB's clips put it). tripo_build writes <name>.glb of its own scene (standing, her height, in metres), which this takes when it is there: no turn or scale is applied at import (applied there, the turn left the clips' root unturned and the scale doubled her size).
Args: CH (e.g. Fem5) [glb [roll,pitch,yaw]]."""
import os, sys, json, importlib, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mat_lib as L
importlib.reload(L)
mel = L.mel; eal = L.eal
CH = sys.argv[1] if len(sys.argv) > 1 else "Fem5"
SRC = r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_" + CH.lower(); NAME = "SK_JRPG_" + CH
D = "/Game/JRPG"; A = f"{D}/{CH}Anims"
info = json.load(open(os.path.join(SRC, "build.json")))
GLB = "glb" in sys.argv[2:]
TURN = [float(v) for v in next((x for x in sys.argv[2:] if x.count(",") == 2), "0,0,0").split(",")]
if GLB:
    # (tripo_build's own GLB when it wrote one: standing, her height, in metres, no turn or scale left to apply (an import's turn
    # left the clips' root unturned, its scale went into the root and the mesh both: she came out twice her size); else the
    # source GLB, scaled and turned here)
    if info.get("glb") and os.path.exists(info["glb"]): src = info["glb"]; scale = 1.0
    else: src = info["source"]; scale = float(info["height_cm"]) / (float(info["source_height_m"]) * 100.0)
    stem = os.path.splitext(os.path.basename(src))[0]
    tmp = D + "/_GlbImport"; PD = D + "/Pipelines"; PIPE = f"{PD}/PL_{CH}_Glb"
    if eal.does_directory_exist(tmp): eal.delete_directory(tmp)
    if eal.does_asset_exist(PIPE): eal.delete_asset(PIPE)
    pipe = L.at.duplicate_asset(f"PL_{CH}_Glb", PD, unreal.load_asset("/Interchange/Pipelines/DefaultAssetsPipeline"))
    pipe.set_editor_property("import_offset_rotation", unreal.Rotator(roll=TURN[0], pitch=TURN[1], yaw=TURN[2]))
    pipe.set_editor_property("import_offset_uniform_scale", scale); eal.save_loaded_asset(pipe, only_if_is_dirty=False)
    params = unreal.ImportAssetParameters(); params.is_automated = True; params.override_pipelines = [unreal.SoftObjectPath(pipe.get_path_name())]
    mgr = unreal.InterchangeManager.get_interchange_manager_scripted()
    mgr.import_asset(tmp, unreal.InterchangeManager.create_source_data(src), params)
    got = {}
    for q in eal.list_assets(tmp, recursive=True):
        x = unreal.load_asset(q.split(".")[0]); got.setdefault(x.get_class().get_name(), []).append(q.split(".")[0])
    print("glb imported from", src, "| scale", round(scale, 4), "turn", TURN, "|", {k: len(v) for k, v in got.items()})
    assert len(got.get("SkeletalMesh", [])) == 1 and len(got.get("Skeleton", [])) == 1, got
    # (the usual names: what was there is deleted first (917 clean deletes it with the maps closed))
    moves = [(got["SkeletalMesh"][0], f"{D}/Character/{NAME}"), (got["Skeleton"][0], f"{D}/Character/{NAME}_Skeleton")]
    moves += [(q, f"{D}/Character/{NAME}_PhysicsAsset") for q in got.get("PhysicsAsset", [])[:1]]
    for q in got.get("AnimSequence", []):
        clip = q.split("/")[-1]; clip = clip[len(stem):] if clip.startswith(stem) else clip
        clip = clip.lstrip("_"); clip = clip[2:] if clip.startswith("A_") else clip          # (tripo_build's actions are A_<clip>)
        moves.append((q, f"{A}/AS_{CH}_{clip}"))
    for s_, d_ in moves:
        if eal.does_asset_exist(d_): eal.delete_asset(d_)
        assert eal.rename_asset(s_, d_), (s_, d_)
    for q in eal.list_assets(tmp, recursive=True): eal.delete_asset(q.split(".")[0])
    eal.delete_directory(tmp)
    sk = unreal.load_asset(f"{D}/Character/{NAME}"); skel = sk.get_editor_property("skeleton")
    # (an import turn stands the mesh and the skeleton's rest up, not the clips' root track, which keeps the GLB's unturned
    # root: every clip laid her on her side, her pelvis 86 cm out along Y (2026-11-10). Only then is each clip's root track set
    # to her rest's root, the turn included, which holds for a rig whose root never moves; with no turn (tripo_build's own GLB)
    # the clips keep their own root, and how far it strays from the rest's is printed (PR #45's review: a character whose
    # clips move the root would have lost it))
    APE_ = unreal.AnimPoseExtensions
    rt = APE_.get_bone_pose(APE_.get_reference_pose(skel), "root", unreal.AnimPoseSpaces.LOCAL)
    turned = any(abs(float(v)) > 1e-3 for v in TURN)
    nroot, stray = 0, 0.0
    for s_, d_ in moves:
        if not d_.startswith(A): continue
        clip_ = unreal.load_asset(d_)
        if not turned:
            for t_ in (0.0, clip_.get_play_length() * 0.5, clip_.get_play_length()):
                p_ = APE_.get_bone_pose(APE_.get_anim_pose_at_time(clip_, t_, unreal.AnimPoseEvaluationOptions()), "root", unreal.AnimPoseSpaces.LOCAL)
                stray = max(stray, (p_.translation - rt.translation).length())
            continue
        ctrl = clip_.controller
        n = unreal.AnimationLibrary.get_num_frames(clip_) + 1
        ctrl.open_bracket(unreal.Text("root track"), True)
        ctrl.set_bone_track_keys("root", [rt.translation] * n, [rt.rotation] * n, [rt.scale3d] * n, True)
        ctrl.close_bracket(True); nroot += 1
    print("root tracks set to her rest's root:", nroot, "" if turned else f"(no turn: kept; the farthest from the rest's {stray:.2f} cm)")
    for x in [skel, sk.get_editor_property("physics_asset"), sk] + [unreal.load_asset(d_) for s_, d_ in moves if d_.startswith(A)]:
        if x: eal.save_loaded_asset(x, only_if_is_dirty=False)
    kinds = {"SkeletalMesh": [sk.get_path_name()]}
else:
    t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, NAME + ".fbx"); t.destination_path = D + "/Character"
    t.automated = True; t.replace_existing = True; t.save = True
    o = unreal.FbxImportUI(); o.import_mesh = True; o.import_as_skeletal = True; o.import_animations = False; o.import_materials = False; o.import_textures = False
    o.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH; t.options = o
    # (the shape keys a build carries become morph targets: the Summoner's face, summoner_face.py)
    o.skeletal_mesh_import_data.set_editor_property("import_morph_targets", True)
    L.at.import_asset_tasks([t])
    kinds = {}
    for p in t.imported_object_paths:
        a = unreal.load_asset(p)
        if a: kinds.setdefault(a.get_class().get_name(), []).append(p)
    print({k: len(v) for k, v in kinds.items()})
    sk = unreal.load_asset(kinds["SkeletalMesh"][0]); skel = sk.get_editor_property("skeleton")
    # (saved here: an automated task can save the mesh but not the skeleton and physics asset it makes, and an editor that went
    # down later took the skeleton with it (2026-11-10: her mesh then had none, her clips no skeleton))
    for a in (skel, sk.get_editor_property("physics_asset")):
        if a: print("saved", a.get_name(), eal.save_loaded_asset(a, only_if_is_dirty=False))
    o = unreal.FbxImportUI()
    o.set_editor_property("import_mesh", False); o.set_editor_property("import_as_skeletal", True)
    o.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    o.set_editor_property("skeleton", skel); o.set_editor_property("import_animations", True)
    o.set_editor_property("import_materials", False); o.set_editor_property("import_textures", False)
    ta = unreal.AssetImportTask(); ta.filename = os.path.join(SRC, NAME + "_Clips.fbx"); ta.destination_path = D + "/_ClipImport"
    ta.automated = True; ta.replace_existing = True; ta.save = True; ta.options = o
    L.at.import_asset_tasks([ta])
    for p in ta.imported_object_paths:
        a = unreal.load_asset(p)
        if isinstance(a, unreal.AnimSequence):
            clip = p.split(".")[-1].split("Armature_A_")[-1]; dst = f"{A}/AS_{CH}_{clip}"
            if eal.does_asset_exist(dst): eal.delete_asset(dst)
            eal.rename_asset(p.split(".")[0], dst)
    for p in eal.list_assets(D + "/_ClipImport", recursive=True): eal.delete_asset(p.split(".")[0])
    eal.delete_directory(D + "/_ClipImport")
print("clips:", sorted((a.split(".")[-1], round(unreal.load_asset(a.split(".")[0]).get_play_length(), 2)) for a in eal.list_assets(A, recursive=False)))
T = {}
for role, kind in (("Color", "color"), ("Normal", "normal"), ("MetalRough", "linear")):
    f = os.path.join(SRC, f"T_{CH}_{role}.png")
    if os.path.exists(f):
        T[role] = L.import_texture(f, D + "/Textures", kind)
        if kind == "normal": T[role].set_editor_property("flip_green_channel", True); eal.save_loaded_asset(T[role])
path = f"{D}/Materials/M_JRPG_{CH}"
if eal.does_asset_exist(path): m = unreal.load_asset(path); mel.delete_all_material_expressions(m)
else: m = L.new_material(path)
m.set_editor_property("use_material_attributes", True); m.set_editor_property("two_sided", True)
S = unreal.MaterialSamplerType
mma = L.expr(m, unreal.MaterialExpressionMakeMaterialAttributes, -200, 0)
bc = L.tex_sample(m, T["Color"], -900, -300)
tint = L.vector(m, "AlbedoTint", (1.0, 1.0, 1.0), -900, -500)
alb = L.expr(m, unreal.MaterialExpressionMultiply, -600, -350); L.link(bc, "RGB", alb, "A"); L.link(tint, "", alb, "B"); L.link(alb, "", mma, "BaseColor")
if "MetalRough" in T:
    mr = L.tex_sample(m, T["MetalRough"], -900, 0, sampler=S.SAMPLERTYPE_MASKS); L.link(mr, "B", mma, "Metallic"); L.link(mr, "G", mma, "Roughness")
else:
    L.link(L.scalar(m, "Roughness", 0.6, -450, 50), "", mma, "Roughness")
if "Normal" in T:
    nm = L.tex_sample(m, T["Normal"], -900, 300, sampler=S.SAMPLERTYPE_NORMAL); L.link(nm, "RGB", mma, "Normal")
L.link(L.scalar(m, "Specular", 0.4, -450, 250), "", mma, "Specular")
mel.connect_material_property(mma, "", unreal.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
try: m.set_editor_property("used_with_skeletal_mesh", True)
except Exception: pass
L.finish(m)
sk.set_editor_property("materials", [unreal.SkeletalMaterial(material_interface=m, material_slot_name=str(s.get_editor_property("material_slot_name"))) for s in sk.get_editor_property("materials")])
sk.modify(); eal.save_loaded_asset(sk, only_if_is_dirty=False)
for p in eal.list_assets(D + "/Character", recursive=False):
    if "tripo_" in p.lower() and eal.does_asset_exist(p.split(".")[0]): print("delete placeholder", p.split("/")[-1], eal.delete_asset(p.split(".")[0]))
sk = unreal.load_asset(kinds["SkeletalMesh"][0])
print("slots", [(str(s.material_slot_name), s.material_interface.get_name() if s.material_interface else None) for s in sk.get_editor_property("materials")])
b = sk.get_bounds(); print("bounds", b.origin, b.box_extent)
print("morph targets", list(sk.get_all_morph_target_names()))
ref = unreal.AnimPoseExtensions.get_reference_pose(skel)
for bn in ("root", "pelvis", "head", "foot_l", "ball_l"):
    tr = unreal.AnimPoseExtensions.get_bone_pose(ref, bn, unreal.AnimPoseSpaces.WORLD); print(bn, [round(v, 1) for v in (tr.translation.x, tr.translation.y, tr.translation.z)])
