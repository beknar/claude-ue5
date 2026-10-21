"""random_dungeonmagic_level5, Summoner2, step 4: her bikini (the GLB's, summoner2_prep.py's s2_bikini.glb) on her MetaHuman
body. Two steps (arg):
  export  (after 844) SourceArt/summoner2/s2_body.fbx: the built body (SKM_MHC_Summoner2_BodyMesh in its bind pose,
          MetaHuman's A-pose) with its skeleton and skin weights, and s2_face.fbx (the face mesh: the neck above the collar). (The posed DNA's body mesh cannot be read back from here:
          get_mesh_for_body_conforming_from_dna gives INVALID_INPUT_DATA for it; the Blender step goes through her own skin.)
          Then: blender -b -P blender_numpy/summoner2_outfit.py -- claude_ue5/SourceArt/summoner2
  import  (after the Blender step) s2_bikini_skinned.fbx onto the body's skeleton (/Game/JRPG/MetaHuman/Summoner2/Outfit/
          s2_bikini_skinned, named after the file), its material M_S2_Bikini from her GLB's textures (base colour, normal, metal-rough: tex/*.png,
          written by the Blender step), two-sided (the chains' thin links). The face component makes it follow the body
          (FRDMetaFace.Outfits: leader pose).
Args: export | import"""
import sys, os, unreal
STEP = sys.argv[1]
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\summoner2"
D = "/Game/JRPG/MetaHuman/Summoner2"
eal = unreal.EditorAssetLibrary
BODY = f"{D}/Body/SKM_MHC_Summoner2_BodyMesh"
if STEP == "export":
    body = unreal.load_asset(BODY); assert body, BODY + ": run 844"
    t = unreal.AssetExportTask(); t.object = body; t.filename = SA + r"\s2_body.fbx"
    t.automated = True; t.replace_identical = True; t.prompt = False
    o = unreal.FbxExportOption(); o.level_of_detail = False; o.collision = False; o.export_morph_targets = False; o.vertex_color = False; o.ascii = False
    t.options = o
    print("S2OUTFIT body fbx", unreal.Exporter.run_asset_export_task(t), os.path.getsize(t.filename))
    # the face mesh too (it carries the neck above the body's collar: the halter straps go round it)
    t2 = unreal.AssetExportTask(); t2.object = unreal.load_asset(f"{D}/Face/SKM_MHC_Summoner2_FaceMesh"); t2.filename = SA + r"\s2_face.fbx"
    t2.automated = True; t2.replace_identical = True; t2.prompt = False; t2.options = o
    print("S2OUTFIT face fbx", unreal.Exporter.run_asset_export_task(t2), os.path.getsize(t2.filename))
elif STEP == "import":
    import importlib; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import mat_lib as L; importlib.reload(L); mel = L.mel
    skel = unreal.load_asset(BODY).get_editor_property("skeleton")
    def setp(obj, name, val):
        try: obj.set_editor_property(name, val)
        except Exception as e: print("  (skip)", name, str(e)[:80])
    pipe = unreal.InterchangeGenericAssetsPipeline()
    setp(pipe.common_skeletal_meshes_and_animations_properties, "skeleton", skel)
    mp = pipe.mesh_pipeline
    setp(mp, "import_skeletal_meshes", True); setp(mp, "import_static_meshes", False); setp(mp, "create_physics_asset", False)
    setp(pipe.animation_pipeline, "import_animations", False); setp(pipe.material_pipeline, "import_materials", False)
    setp(pipe.common_meshes_properties, "force_all_mesh_as_type", unreal.InterchangeForceMeshType.IFMT_SKELETAL_MESH)
    src = unreal.InterchangeManager.create_source_data(SA + r"\s2_bikini_skinned.fbx")
    prm = unreal.ImportAssetParameters(); prm.is_automated = True; prm.replace_existing = True
    prm.override_pipelines.append(unreal.SoftObjectPath(pipe.get_path_name()))
    try: unreal.InterchangeManager.get_interchange_manager_scripted().import_asset(D + "/Outfit", src, prm)
    except RuntimeError as e: print("S2OUTFIT import (non-fatal):", str(e)[:160])
    meshes = [a for a in eal.list_assets(D + "/Outfit", recursive=False) if isinstance(unreal.load_asset(a.split(".")[0]), unreal.SkeletalMesh)]
    print("S2OUTFIT imported", meshes)
    sk = unreal.load_asset(meshes[0].split(".")[0])
    # the material: her GLB's textures
    T = {}
    for role, kind in (("Color", "color"), ("Normal", "normal"), ("MetalRough", "linear")):
        f = SA + rf"\tex\T_S2_{role}.png"
        if os.path.exists(f): T[role] = L.import_texture(f, D + "/Outfit/Textures", kind)
    m = L.new_material(D + "/Outfit/M_S2_Bikini"); mel.delete_all_material_expressions(m)
    m.set_editor_property("two_sided", True)
    S = unreal.MaterialSamplerType
    col = L.tex_sample(m, T["Color"], -600, -200)
    mel.connect_material_property(col, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    if "MetalRough" in T:
        mr = L.tex_sample(m, T["MetalRough"], -600, 100, sampler=S.SAMPLERTYPE_MASKS)
        mel.connect_material_property(mr, "B", unreal.MaterialProperty.MP_METALLIC); mel.connect_material_property(mr, "G", unreal.MaterialProperty.MP_ROUGHNESS)
    if "Normal" in T:
        nm = L.tex_sample(m, T["Normal"], -600, 400, sampler=S.SAMPLERTYPE_NORMAL); mel.connect_material_property(nm, "RGB", unreal.MaterialProperty.MP_NORMAL)
    try: m.set_editor_property("used_with_skeletal_mesh", True)
    except Exception as e: print("usage", e)
    L.finish(m)
    sk.set_editor_property("materials", [unreal.SkeletalMaterial(material_interface=m, material_slot_name=str(s.get_editor_property("material_slot_name"))) for s in sk.get_editor_property("materials")])
    sk.modify(); eal.save_loaded_asset(sk, only_if_is_dirty=False)
    print("S2OUTFIT", sk.get_path_name(), "| skeleton", sk.get_editor_property("skeleton").get_name(), "| material", m.get_name(),
          "| pixel instructions", mel.get_statistics(m).num_pixel_shader_instructions)
