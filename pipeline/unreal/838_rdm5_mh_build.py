"""random_dungeonmagic_level5, the Summoner's MetaHuman face, step 2: MHC_Summoner (837) through Epic's cloud service and
the build. Steps (args, in order; default all):
  textures  the high-resolution face textures synthesized for her skin (request_texture_sources)
  rig       the face rig: joints and blend shapes (request_auto_rigging) -- what RigLogic moves when a control curve moves
  build     the assembly (cinematic pipeline) into /Game/JRPG/MetaHuman/Summoner, with a common folder of its own
            (/Game/JRPG/MetaHuman/Common, so fig4's /Game/MetaHumans/Common is left as it is)
  postprocess  the face mesh's post-process AnimBP: a copy of Epic's ABP_Face_PostProcess without its first two nodes.
            Epic's copies the body's bones by name from the mesh the face is attached to (a MetaHuman body: same bones,
            same axes) before RigLogic; attached to her, it copied her spine, neck and head (other axes) and folded the
            face's neck down to her waist. The copy (ABP_RDM5_FacePostProcess) takes the pose its own animation gives
            (URDMetaFaceAnimInstance: the neck and head following hers) straight into the cached pose RigLogic works on.
The cloud steps need the editor signed in to an Epic account (the first fig4 run did it through 04b's progress window).
Prints the face mesh, its morph targets and its post-process AnimBP (RigLogic). Args: [textures] [rig] [build] [postprocess]"""
import sys, time, unreal
STEPS = sys.argv[1:] or ["textures", "rig", "build", "postprocess"]
ch = unreal.load_asset("/Game/JRPG/MetaHuman/MHC_Summoner"); assert ch, "run 837 first"
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    if "PreviewActor" in a.get_actor_label(): eas.destroy_actor(a)
if not (mhs.is_object_added_for_editing(ch) or mhs.try_add_object_to_edit(ch)): raise RuntimeError("cannot edit MHC_Summoner")
BUILD = "/Game/JRPG/MetaHuman"
try:
    if "textures" in STEPS:
        t = time.time(); req = unreal.MetaHumanCharacterTextureRequestParams(); req.blocking = True; req.report_progress = False
        mhs.request_texture_sources(ch, req)
        print(f"RDM5MH textures ({time.time() - t:.0f} s): high resolution {ch.has_high_resolution_textures}")
    if "rig" in STEPS:
        t = time.time(); rr = unreal.MetaHumanCharacterAutoRiggingRequestParams(); rr.blocking = True; rr.report_progress = False
        rr.rig_type = unreal.MetaHumanRigType.JOINTS_AND_BLEND_SHAPES
        mhs.request_auto_rigging(ch, rr)
        print(f"RDM5MH rig requested ({time.time() - t:.0f} s)")
    unreal.EditorAssetLibrary.save_loaded_asset(ch, only_if_is_dirty=False)
    if "build" in STEPS:
        print("RDM5MH can build:", mhs.can_build_meta_human(ch))
        bp = unreal.MetaHumanCharacterEditorBuildParameters()
        bp.pipeline_type = unreal.MetaHumanDefaultPipelineType.CINEMATIC
        bp.pipeline_quality = unreal.MetaHumanQualityLevel.CINEMATIC
        bp.absolute_build_path = BUILD; bp.common_folder_path = BUILD + "/Common"; bp.name_override = "Summoner"
        bp.enable_wardrobe_item_validation = False
        t = time.time()
        try:
            mhs.build_meta_human(character=ch, params=bp)
        except RuntimeError as e:
            print("RDM5MH build reported (non-fatal):", str(e).splitlines()[0][:160])   # (Control Rig "Cannot break link" warnings come back as errors; the build completes: fig4's 06)
        print(f"RDM5MH BUILD done in {time.time() - t:.0f} s")
        unreal.EditorAssetLibrary.save_directory(BUILD + "/Summoner", only_if_is_dirty=False, recursive=True)
        unreal.EditorAssetLibrary.save_directory(BUILD + "/Common", only_if_is_dirty=False, recursive=True)
finally:
    if mhs.is_object_added_for_editing(ch): mhs.remove_object_to_edit(ch)
if "postprocess" in STEPS:
    import editor_toolset.toolsets.blueprint as BT
    T = BT.BlueprintTools; eal = unreal.EditorAssetLibrary
    SRC, DST = BUILD + "/Common/Face/ABP_Face_PostProcess", BUILD + "/Summoner/Face/ABP_RDM5_FacePostProcess"
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
    T.compile_blueprint(abp)
    eal.save_loaded_asset(abp, only_if_is_dirty=False)
    left = [str(i.type_id) for i in T.get_node_infos(T.find_nodes(g, ""))]
    assert not any("CopyPoseFromMesh" in t or "Layeredblend" in t for t in left), left
    fm = unreal.load_asset(BUILD + "/Summoner/Face/SKM_MHC_Summoner_FaceMesh")
    fm.set_editor_property("post_process_anim_blueprint", unreal.load_asset(DST).generated_class())
    eal.save_loaded_asset(fm, only_if_is_dirty=False)
    print("RDM5MH post-process", DST, "| nodes", len(left), "| on the face mesh:", fm.get_editor_property("post_process_anim_blueprint").get_name())
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for a in ar.get_assets_by_path(BUILD + "/Summoner", recursive=True):
    if str(a.asset_class_path.asset_name) in ("SkeletalMesh", "Blueprint"):
        o = a.get_asset(); print("RDM5MH built", a.asset_class_path.asset_name, a.package_name)
        if isinstance(o, unreal.SkeletalMesh) and "Face" in str(a.package_name):
            print("   morph targets", len(o.get_all_morph_target_names()), "| post process", o.get_editor_property("post_process_anim_blueprint"))
