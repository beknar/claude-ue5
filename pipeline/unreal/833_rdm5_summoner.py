"""random_dungeonmagic_level5: the Summoner (ai models/Summoner.glb, character Summoner of 600-620) with the Mage's abilities,
and her face. Run after:
  832 (the Mage's flinch and death exported for the clip maker)
  blender_numpy/summoner_rig.py "ai models/Summoner.glb" SourceArt/summoner/Summoner_rig.glb SourceArt/summoner/face.json
  blender_numpy/tripo_build.py SourceArt/summoner/Summoner_rig.glb SourceArt/jrpg_summoner SK_JRPG_Summoner Summoner 170 summoner_clips.py
  blender_numpy/summoner_face.py "ai models/Summoner.glb" SourceArt/summoner/face.json SourceArt/summoner/face
  600 / 610 / 615 / 620 for Summoner (620 ... 85 keepmeadow)
What it does:
- her flinch and death: the Mage's (832 exported them; summoner_clips.py transferred them with her other clips, as
  AS_Summoner_Flinch / AS_Summoner_Death; root locked here). Unreal's IK retargeter, from the pack's mannequin onto her
  rig with its extra bones, had folded her up on the floor in the death clip.
- her casts (the Mage's three, retargeted by summoner_clips.py): the bolt leaves where her right hand moves fastest (as 810
  measures the Mage's); a cast is cut a little after it
- the spell: the Mage's fire, as 810 wrote it to SourceArt/random_dungeon_magic/spell.json (damage, reach, the bolt, the
  effects), with her own casts -> SourceArt/random_dungeon_magic5/spell.json for 834
- her face material M_JRPG_Summoner_Face: M_JRPG_Summoner's (base colour, metal-rough, normal) with the painted patches
  (SourceArt/summoner/face/T_Summoner_Face_<Patch>.png, imported to /Game/JRPG/Textures/Face) laid over the base colour in
  face.json's patch_order, each by a scalar parameter of its name (0: not there, 1: painted on): the face component sets
  them. Given to SK_JRPG_Summoner's slot.
- BP_RDM5_SummonerCharacter (child of BP_JRPGSummonerCharacter, a 36 cm capsule as the Mage's) and BP_RDM5_GameMode
  (BP_RD_GameMode with her as the pawn). Prints the morph targets the mesh has and the material's parameters. Args: none"""
import json, os, sys, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, mat_lib as L
importlib.reload(L)
at = unreal.AssetToolsHelpers.get_asset_tools(); eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions; mel = L.mel
V = unreal.Vector
CH = "Summoner"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
JSON = SA + r"\random_dungeon_magic5\spell.json"
FACE = json.load(open(SA + r"\summoner\face.json"))
tgt_mesh = unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{CH}"); tgt_rig = unreal.load_asset(f"/Game/JRPG/Rigs/IK_JRPG_{CH}_Auto")
assert tgt_mesh and tgt_rig, "run 600-620 for Summoner first"
CASTS = ["Cast1", "Cast2", "Cast3"]
AFTER = 0.42
MAGE = json.load(open(SA + r"\random_dungeon_magic\spell.json"))
SPELL = {k: v for k, v in MAGE.items() if k not in ("casts", "flinch", "death")}
o = unreal.AnimPoseEvaluationOptions()
def release(anim):
    L_ = unreal.AnimationLibrary.get_sequence_length(anim); n = max(30, int(L_ * 60)); pts = []
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(anim, L_ * k / n, o)
        h = APE.get_bone_pose(p, "hand_r", unreal.AnimPoseSpaces.WORLD).translation; q = APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.WORLD).translation
        pts.append(V(h.x - q.x, h.y - q.y, h.z - q.z))
    sp = [(pts[k + 1] - pts[k]).length() / (L_ / n) for k in range(n)]
    sm = [sum(sp[max(0, k - 2):k + 3]) / len(sp[max(0, k - 2):k + 3]) for k in range(n)]
    k = max(range(n), key=lambda i: sm[i])
    return L_, L_ * (k + 0.5) / n, sm[k]
# ---- flinch and death: the Mage's, transferred onto her by summoner_clips.py with her other clips (832 exported them)
FL, DE = f"/Game/JRPG/{CH}Anims/AS_{CH}_Flinch", f"/Game/JRPG/{CH}Anims/AS_{CH}_Death"
for p_ in (FL, DE):
    a = unreal.load_asset(p_); assert a, p_ + ": run 832 before the build (summoner_clips.py takes the Mage's flinch and death from it)"
    a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
# ---- her casts
casts = []
for n in CASTS:
    p = f"/Game/JRPG/{CH}Anims/AS_{CH}_{n}"; a = unreal.load_asset(p); assert a, p
    a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
    L_, hit, speed = release(a)
    casts.append({"clip": p, "length": round(L_, 3), "hit": round(hit, 3), "end": round(min(L_, hit + AFTER), 3), "hand_speed": round(speed)})
mage_hits = [c["hit"] for c in MAGE["casts"]]
res = dict(SPELL, casts=casts, flinch=FL, death=DE)
os.makedirs(os.path.dirname(JSON), exist_ok=True); json.dump(res, open(JSON, "w"), indent=1)
print("RDM5SUMMONER casts: " + ", ".join(f"{n} bolt at {x['hit']:.2f} s (the Mage's {m:.2f}; hand {x['hand_speed']} cm/s)" for n, x, m in zip(CASTS, casts, mage_hits)))
# ---- her face material: the base material with the painted patches over the base colour
FD = SA + r"\summoner\face"
T = {}
for role, kind in (("Color", "color"), ("Normal", "normal"), ("MetalRough", "linear")):
    T[role] = unreal.load_asset(f"/Game/JRPG/Textures/T_{CH}_{role}")
order = FACE["patch_order"]
P = {}
for nm in order:
    t = L.import_texture(os.path.join(FD, f"T_Summoner_Face_{nm}.png"), "/Game/JRPG/Textures/Face", "color")
    t.set_editor_property("srgb", True); t.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
    eal.save_loaded_asset(t); P[nm] = t
path = f"/Game/JRPG/Materials/M_JRPG_{CH}_Face"
m = L.new_material(path)
if mel.get_num_material_expressions(m) if hasattr(mel, "get_num_material_expressions") else False: mel.delete_all_material_expressions(m)
mel.delete_all_material_expressions(m)
m.set_editor_property("use_material_attributes", True); m.set_editor_property("two_sided", True)
S = unreal.MaterialSamplerType
mma = L.expr(m, unreal.MaterialExpressionMakeMaterialAttributes, 200, 0)
col = L.tex_sample(m, T["Color"], -1400, -300); col_out = "RGB"
for i, nm in enumerate(order):
    ps = L.tex_sample(m, P[nm], -1400, 200 + i * 260)
    prm = L.scalar(m, nm, 0.0, -1100, 300 + i * 260)
    a = L.mul(m, ps, prm, -900, 260 + i * 260, a_out="A")
    sat = L.expr(m, unreal.MaterialExpressionSaturate, -760, 260 + i * 260); L.link(a, "", sat, "")
    lp = L.expr(m, unreal.MaterialExpressionLinearInterpolate, -600, -300 + i * 60)
    L.link(col, col_out, lp, "A"); L.link(ps, "RGB", lp, "B"); L.link(sat, "", lp, "Alpha")
    col, col_out = lp, ""
tint = L.vector(m, "AlbedoTint", (1.0, 1.0, 1.0), -300, -500)
alb = L.expr(m, unreal.MaterialExpressionMultiply, -100, -350); L.link(col, col_out, alb, "A"); L.link(tint, "", alb, "B"); L.link(alb, "", mma, "BaseColor")
if T["MetalRough"]:
    mr = L.tex_sample(m, T["MetalRough"], -400, 0, sampler=S.SAMPLERTYPE_MASKS); L.link(mr, "B", mma, "Metallic"); L.link(mr, "G", mma, "Roughness")
if T["Normal"]:
    nmx = L.tex_sample(m, T["Normal"], -400, 300, sampler=S.SAMPLERTYPE_NORMAL); L.link(nmx, "RGB", mma, "Normal")
L.link(L.scalar(m, "Specular", 0.4, -100, 250), "", mma, "Specular")
mel.connect_material_property(mma, "", unreal.MaterialProperty.MP_MATERIAL_ATTRIBUTES)
try: m.set_editor_property("used_with_skeletal_mesh", True); m.set_editor_property("used_with_morph_targets", True)
except Exception as e: print("usage flags", e)
unreal.log("RDM5SUMMONER compiling the face material (the 'Failed to compile' lines above this one are its half-built states)")
L.finish(m)
tgt_mesh.set_editor_property("materials", [unreal.SkeletalMaterial(material_interface=m, material_slot_name=str(s.get_editor_property("material_slot_name"))) for s in tgt_mesh.get_editor_property("materials")])
tgt_mesh.modify(); eal.save_loaded_asset(tgt_mesh, only_if_is_dirty=False)
pn = [str(x) for x in mel.get_scalar_parameter_names(m)] if hasattr(mel, "get_scalar_parameter_names") else []
stats = mel.get_statistics(m)
print("RDM5SUMMONER face material", path, "| parameters", pn, "| pixel instructions", stats.num_pixel_shader_instructions)
print("RDM5SUMMONER morph targets", list(tgt_mesh.get_all_morph_target_names()))
# ---- her dungeon character and game mode
G = "/Game/RandomDungeon/Blueprints"; CHP = f"{G}/BP_RDM5_SummonerCharacter"; GM = f"{G}/BP_RDM5_GameMode"
if not eal.does_asset_exist(CHP):
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.load_asset(f"/Game/JRPG/Game/BP_JRPG{CH}Character").generated_class())
    at.create_asset("BP_RDM5_SummonerCharacter", G, unreal.Blueprint, f)
chbp = unreal.load_asset(CHP); unreal.BlueprintEditorLibrary.compile_blueprint(chbp)
unreal.get_default_object(chbp.generated_class()).get_component_by_class(unreal.CapsuleComponent).set_editor_property("capsule_radius", 36.0)
unreal.BlueprintEditorLibrary.compile_blueprint(chbp); eal.save_loaded_asset(chbp, only_if_is_dirty=False)
if eal.does_asset_exist(GM): eal.delete_asset(GM)
gm = eal.duplicate_asset(f"{G}/BP_RD_GameMode", GM); cdo = unreal.get_default_object(gm.generated_class())
cdo.set_editor_property("default_pawn_class", chbp.generated_class())
unreal.BlueprintEditorLibrary.compile_blueprint(gm); eal.save_loaded_asset(gm, only_if_is_dirty=False)
cdo = unreal.get_default_object(unreal.load_asset(GM).generated_class())
print("RDM5SUMMONER", GM, "-> pawn", cdo.get_editor_property("default_pawn_class").get_name(), "hud", cdo.get_editor_property("hud_class").get_name(), "| saved", JSON)
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
