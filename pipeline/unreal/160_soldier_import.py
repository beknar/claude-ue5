"""Import Dystopia_Soldier_02 (mesh + skeleton + 39 clips), its Unity PBR textures, and build three materials
(Unity standard metallic workflow: Metallic.R = metal, Metallic.A = smoothness; OpenGL normals -> flip green)."""
import os, sys, importlib, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mat_lib as L
importlib.reload(L)
mel = L.mel; eal = L.eal
SRC = r"E:\code\claude-ue5\claude_ue5\SourceArt\dystopia_soldier02"
TEX = r"E:\code\claude-ue5\claude_ue5\SourceArt\dystopia_soldier02_src\Textures"
D = "/Game/Soldier"
t = unreal.AssetImportTask(); t.filename = os.path.join(SRC, "SK_Dystopia_Soldier_02.fbx"); t.destination_path = D + "/Character"
t.automated = True; t.replace_existing = True; t.save = True
L.at.import_asset_tasks([t])
kinds = {}
for p in t.imported_object_paths:
    a = unreal.load_asset(p); kinds.setdefault(a.get_class().get_name(), []).append(p)
for k, v in kinds.items(): print(k, len(v))
# move/rename clips -> /Game/Soldier/Anims/AS_Soldier_<clip>
for p in kinds.get("AnimSequence", []):
    n = p.split(".")[-1]; clip = n.split("A_", 1)[1] if "A_" in n else n
    eal.rename_asset(p.split(".")[0], f"{D}/Anims/AS_Soldier_{clip}")
print("clips:", sorted(a.split(".")[-1] for a in eal.list_assets(D + "/Anims", recursive=False)))
# textures
def tex(rel, kind):
    p = os.path.join(TEX, rel); tx = L.import_texture(p, D + "/Textures", kind)
    if kind == "normal": tx.set_editor_property("flip_green_channel", True); eal.save_loaded_asset(tx)
    return tx
sets = {"Body": ("Body/Dystopia_Soldier_02_Body", False), "Details": ("Details/Dystopia_Soldier_02_Details", True), "FireGun": ("Weapons/FireGun", False)}
mats = {}
for name, (base, emissive) in sets.items():
    T = {"bc": tex(base + "_Albedo.tga", "color"), "n": tex(base + "_Normals.tga", "normal"),
         "mg": tex(base + "_Metallic.tga", "linear"), "ao": tex(base + "_Ao.tga", "linear")}
    if emissive: T["em"] = tex(base + "_Emissive.tga", "color")
    path = f"{D}/Materials/M_Soldier_{name}"
    if eal.does_asset_exist(path):
        m = unreal.load_asset(path); mel.delete_all_material_expressions(m)
    else:
        m = L.new_material(path)
    m.set_editor_property("use_material_attributes", True)
    S = unreal.MaterialSamplerType
    bc = L.tex_sample(m, T["bc"], -900, -300)
    mg = L.tex_sample(m, T["mg"], -900, 0, sampler=S.SAMPLERTYPE_MASKS)
    nm = L.tex_sample(m, T["n"], -900, 300, sampler=S.SAMPLERTYPE_NORMAL)
    ao = L.tex_sample(m, T["ao"], -900, 600, sampler=S.SAMPLERTYPE_MASKS)
    rough = L.expr(m, unreal.MaterialExpressionOneMinus, -600, 50); L.link(mg, "A", rough, "")
    rs = L.expr(m, unreal.MaterialExpressionMultiply, -450, 50); L.link(rough, "", rs, "A"); L.link(L.scalar(m, "RoughnessScale", 1.0, -600, 150), "", rs, "B")
    mma = L.expr(m, unreal.MaterialExpressionMakeMaterialAttributes, -200, 0)
    L.link(bc, "RGB", mma, "BaseColor"); L.link(mg, "R", mma, "Metallic"); L.link(rs, "", mma, "Roughness")
    L.link(nm, "RGB", mma, "Normal"); L.link(ao, "R", mma, "AmbientOcclusion")
    L.link(L.expr(m, unreal.MaterialExpressionConstant, -450, 250, r=0.5), "", mma, "Specular")
    if "em" in T:
        em = L.tex_sample(m, T["em"], -900, 900)
        es = L.expr(m, unreal.MaterialExpressionMultiply, -450, 900); L.link(em, "RGB", es, "A"); L.link(L.scalar(m, "EmissiveBoost", 4.0, -600, 1000), "", es, "B")
        L.link(es, "", mma, "EmissiveColor")
    mel.connect_material_property(mma, "", unreal.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
    for flag in ("used_with_skeletal_mesh", "used_with_nanite"):
        try: m.set_editor_property(flag, True)
        except Exception: pass
    L.finish(m); mats[name] = m
sk = unreal.load_asset(kinds["SkeletalMesh"][0])
slots = sk.get_editor_property("materials")
for i in range(len(slots)):
    sn = str(slots[i].get_editor_property("material_slot_name"))
    key = "FireGun" if "FireGun" in sn else ("Body" if "Body" in sn else "Details")
    slots[i].set_editor_property("material_interface", mats[key]); print("slot", sn, "->", key)
sk.set_editor_property("materials", slots)
ns = sk.get_editor_property("nanite_settings"); ns.set_editor_property("enabled", True); sk.set_editor_property("nanite_settings", ns)
eal.save_loaded_asset(sk)
b = sk.get_bounds(); print("bounds", b.origin, b.box_extent)
ref = unreal.AnimPoseExtensions.get_reference_pose(sk.get_editor_property("skeleton"))
for bn in ("root", "pelvis", "head", "foot_l", "ball_l"):
    tr = unreal.AnimPoseExtensions.get_bone_pose(ref, bn, unreal.AnimPoseSpaces.WORLD); print(bn, tr.translation, tr.scale3d if bn == "root" else "")
