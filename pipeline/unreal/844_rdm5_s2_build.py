"""random_dungeonmagic_level5, Summoner2, step 3: MHC_Summoner2 (842, 843) through Epic's cloud service and the build, as 838
does the first Summoner's face, but the whole MetaHuman: face and body. Steps (args, in order; default all):
  textures  the high-resolution face and body textures synthesized for her skin (request_texture_sources)
  rig       the face rig: joints and blend shapes (request_auto_rigging) -- what RigLogic moves when a control curve moves
  build     the assembly (cinematic pipeline) into /Game/JRPG/MetaHuman/Summoner2: SKM_MHC_Summoner2_FaceMesh,
            SKM_MHC_Summoner2_BodyMesh (MetaHuman's body skeleton: the UE5 mannequin's bones and more), the grooms (hair,
            brows, lashes, peach fuzz) bound to the face; common folder /Game/JRPG/MetaHuman/Common (838's)
  postprocess  the face mesh's post-process AnimBP: a copy of Epic's ABP_Face_PostProcess without its body copy
            (ABP_S2_FacePostProcess; the face component's animation moves the face's neck and head with the body's)
  grooms    the built grooms' material slots (MI_Hair, MI_Hair_Cards, MI_Hair_Helmet) given 843's colours: the hair's
            ombre (MI_Summoner2_Hair...), the brows' and the lashes'
  underwear the grey briefs MetaHuman bakes into the body's textures (only the top has a switch) painted out with the skin
            round them (blender_numpy/s2_underwear.py, in Python with numpy / scipy / Pillow: the UE_PY environment variable,
            or the amv-maker venv): the base colour, normal and roughness maps exported to SourceArt/summoner2/body_tex,
            fixed, and imported back over the same textures (their compression, sRGB and virtual texturing kept)
The cloud steps need the editor signed in to an Epic account. Args: [textures] [rig] [build] [postprocess] [grooms] [underwear]"""
import sys, time, unreal
STEPS = sys.argv[1:] or ["textures", "rig", "build", "postprocess", "grooms", "underwear"]
ch = unreal.load_asset("/Game/JRPG/MetaHuman/MHC_Summoner2"); assert ch, "run 842 / 843 first"
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
for a in eas.get_all_level_actors():
    if "PreviewActor" in a.get_actor_label(): eas.destroy_actor(a)
BUILD = "/Game/JRPG/MetaHuman"; NAME = "Summoner2"
if any(s in STEPS for s in ("textures", "rig", "build")):
    if not (mhs.is_object_added_for_editing(ch) or mhs.try_add_object_to_edit(ch)): raise RuntimeError("cannot edit MHC_Summoner2")
    try:
        if "textures" in STEPS:
            t = time.time(); req = unreal.MetaHumanCharacterTextureRequestParams(); req.blocking = True; req.report_progress = False
            mhs.request_texture_sources(ch, req)
            print(f"S2BUILD textures ({time.time() - t:.0f} s): high resolution {ch.has_high_resolution_textures}")
        if "rig" in STEPS:
            t = time.time(); rr = unreal.MetaHumanCharacterAutoRiggingRequestParams(); rr.blocking = True; rr.report_progress = False
            rr.rig_type = unreal.MetaHumanRigType.JOINTS_AND_BLEND_SHAPES
            mhs.request_auto_rigging(ch, rr)
            print(f"S2BUILD rig requested ({time.time() - t:.0f} s)")
        eal.save_loaded_asset(ch, only_if_is_dirty=False)
        if "build" in STEPS:
            print("S2BUILD can build:", mhs.can_build_meta_human(ch))
            bp = unreal.MetaHumanCharacterEditorBuildParameters()
            bp.pipeline_type = unreal.MetaHumanDefaultPipelineType.CINEMATIC
            bp.pipeline_quality = unreal.MetaHumanQualityLevel.CINEMATIC
            bp.absolute_build_path = BUILD; bp.common_folder_path = BUILD + "/Common"; bp.name_override = NAME
            bp.enable_wardrobe_item_validation = False
            t = time.time()
            try: mhs.build_meta_human(character=ch, params=bp)
            except RuntimeError as e: print("S2BUILD build reported (non-fatal):", str(e).splitlines()[0][:160])
            print(f"S2BUILD BUILD done in {time.time() - t:.0f} s")
            eal.save_directory(BUILD + "/" + NAME, only_if_is_dirty=False, recursive=True)
            eal.save_directory(BUILD + "/Common", only_if_is_dirty=False, recursive=True)
    finally:
        if mhs.is_object_added_for_editing(ch): mhs.remove_object_to_edit(ch)
FACE = f"{BUILD}/{NAME}/Face/SKM_MHC_{NAME}_FaceMesh"
if "postprocess" in STEPS:
    import editor_toolset.toolsets.blueprint as BT
    T = BT.BlueprintTools
    SRC, DST = BUILD + "/Common/Face/ABP_Face_PostProcess", f"{BUILD}/{NAME}/Face/ABP_S2_FacePostProcess"
    if eal.does_asset_exist(DST): eal.delete_asset(DST)
    abp = eal.duplicate_asset(SRC, DST); assert abp, DST
    g = [x for x in T.list_graphs(abp) if x.get_name() == "AnimGraph"][0]
    nodes = {str(i.node).split(".")[-1].rstrip("'"): (n, i) for n, i in zip(T.find_nodes(g, ""), T.get_node_infos(T.find_nodes(g, "")))}
    def node(prefix):
        hits = [v for k, v in nodes.items() if k.startswith(prefix)]
        assert len(hits) == 1, (prefix, list(nodes))
        return hits[0]
    inp, inp_i = node("AnimGraphNode_LinkedInputPose"); cache, cache_i = node("AnimGraphNode_SaveCachedPose_0")
    assert "InputPose" in str(cache_i.type_id), cache_i.type_id
    for pre in ("AnimGraphNode_CopyPoseFromMesh", "AnimGraphNode_LayeredBoneBlend"):
        n, _ = node(pre); T.delete_node(n)
    T.connect_pins(inp_i.output_pins[0].pin_id, cache_i.input_pins[0].pin_id)
    T.compile_blueprint(abp); eal.save_loaded_asset(abp, only_if_is_dirty=False)
    fm = unreal.load_asset(FACE); assert fm, FACE
    fm.set_editor_property("post_process_anim_blueprint", unreal.load_asset(DST).generated_class())
    eal.save_loaded_asset(fm, only_if_is_dirty=False)
    print("S2BUILD post-process", DST, "on", fm.get_name())
if "grooms" in STEPS:
    MD = f"{BUILD}/{NAME}/Materials"
    for a in eal.list_assets(f"{BUILD}/{NAME}/Grooms", recursive=False):
        g = unreal.load_asset(a.split(".")[0])
        if not isinstance(g, unreal.GroomAsset): continue
        kind = next((k for k in ("Hair", "Eyebrows", "Eyelashes") if g.get_name().startswith(k)), None)
        if not kind: continue
        mine = {"Hair": "MI_Summoner2_Hair", "Eyebrows": "MI_Summoner2_Brows", "Eyelashes": "MI_Summoner2_Lashes"}[kind]
        ms = list(g.get_editor_property("hair_groups_materials")); out = []
        for m in ms:
            slot = str(m.get_editor_property("slot_name")); suffix = "_Cards" if slot.endswith("_Cards") else ("_Helmet" if slot.endswith("_Helmet") else "")
            mi = unreal.load_asset(f"{MD}/{mine}{suffix}"); assert mi, f"{MD}/{mine}{suffix}: run 843"
            m.set_editor_property("material", mi); out.append(m)
        g.set_editor_property("hair_groups_materials", out); g.modify(); eal.save_loaded_asset(g, only_if_is_dirty=False)
        back = [m.get_editor_property("material").get_name() for m in unreal.load_asset(a.split(".")[0]).get_editor_property("hair_groups_materials")]
        print("S2BUILD groom", g.get_name(), back)
if "underwear" in STEPS:
    import os, subprocess
    TD = r"E:\code\claude-ue5\claude_ue5\SourceArt\summoner2\body_tex"; os.makedirs(TD, exist_ok=True)
    TEX = {"body_bc": f"{BUILD}/{NAME}/Body/Baked/T_Body_BC_VT", "body_n": f"{BUILD}/{NAME}/Body/Baked/T_Body_N_VT", "body_srmf": f"{BUILD}/{NAME}/Body/Baked/T_Body_SRMF_VT"}
    keep = {}
    for k, p in TEX.items():
        t = unreal.load_asset(p); assert t, p
        keep[k] = {n: t.get_editor_property(n) for n in ("srgb", "compression_settings", "virtual_texture_streaming", "lod_group")}
        task = unreal.AssetExportTask(); task.object = t; task.filename = os.path.join(TD, k + ".png"); task.automated = True; task.prompt = False; task.replace_identical = True
        assert unreal.Exporter.run_asset_export_task(task), p
    py = os.environ.get("UE_PY") or r"C:\Users\kestanol\Documents\code\amv-maker\venv\Scripts\python.exe"
    r = subprocess.run([py, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "blender_numpy", "s2_underwear.py"), TD], capture_output=True, text=True)
    print(r.stdout.strip()); assert r.returncode == 0, r.stderr[-800:]
    for k, p in TEX.items():
        task = unreal.AssetImportTask(); task.filename = os.path.join(TD, k + "_fixed.png"); task.destination_path = p.rsplit("/", 1)[0]
        task.destination_name = p.rsplit("/", 1)[1]; task.replace_existing = True; task.automated = True; task.save = False
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        t = unreal.load_asset(p)
        for n, v in keep[k].items(): t.set_editor_property(n, v)
        eal.save_loaded_asset(t, only_if_is_dirty=False)
        print("S2BUILD underwear painted out:", p, keep[k]["compression_settings"], "VT", keep[k]["virtual_texture_streaming"])
for a in unreal.AssetRegistryHelpers.get_asset_registry().get_assets_by_path(f"{BUILD}/{NAME}", recursive=True):
    cls = str(a.asset_class_path.asset_name)
    if cls in ("SkeletalMesh", "Blueprint", "GroomAsset", "GroomBindingAsset"):
        o = a.get_asset(); extra = ""
        if isinstance(o, unreal.SkeletalMesh):
            extra = f"| morphs {len(o.get_all_morph_target_names())} | skeleton {o.get_editor_property('skeleton').get_path_name()} | post {o.get_editor_property('post_process_anim_blueprint')}"
        print("S2BUILD built", cls, a.package_name, extra)
