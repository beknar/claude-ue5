"""The list of 2026-11-12's seventh phase (docs/improvements12.txt): the Rogue's sixteen arts, from SourceArt/balance/rogue12.json,
onto every map of the game she plays (mistward_castle, brokenspire and the five dungeons after it).
Steps (name them; all three by default):
  caltrop    the caltrop (blender_numpy/caltrop.py's FBX: blender -b -P pipeline/blender_numpy/caltrop.py -- claude_ue5/SourceArt/rogue12)
             imported as /Game/RandomDungeon/Rogue12/SM_RD_Caltrop in a pack's iron
  materials  the arts' materials of their own (her double's smoke, the lotus's silver afterimages, the red crosshair, the acid's pool,
             the rope, the vanishing act's shimmer) under /Game/RandomDungeon/Rogue12
  arts       on every map: the sixteen arts as secondary abilities of hers (FRDSecondaryDef with a Slot, its numbers, cost, cooldown
             and looks), their manuals (items of kind Tome, "Manual of <title>", Weight 0: only their place's tome draw gives one, to
             her), the props' shared meshes (a disc, a plane, a cylinder) and the rope's material; the old arts and manuals taken out
             first
C++ first (RD/RDRogue12.cpp). Run after 911 (it writes the whole list of secondary abilities anew: the Rogue's arts would go). Args: steps"""
import os, sys, json, unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary
SA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "claude_ue5", "SourceArt"))
RJ = json.load(open(os.path.join(SA, "balance", "rogue12.json"), encoding="utf-8"))
STEPS = [s for a in sys.argv[1:] for s in a.split(",") if s] or ["caltrop", "materials", "arts"]
DEST = "/Game/RandomDungeon/Rogue12"
MAPS = ("mistward_castle", "brokenspire", "vel_morrath", "war_engine", "sewers", "kethrys_spire", "heaven_fortress")
REPORT = []


def generator():
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def open_map(m):
    path = "/Game/RandomDungeon/Maps/" + m
    if not ues.get_editor_world().get_path_name().startswith(path + "."):
        les.load_level(path); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    assert ues.get_editor_world().get_path_name().startswith(path + "."), ues.get_editor_world().get_path_name()


# ------------------------------------------------------------------------------------------------ the caltrop
if "caltrop" in STEPS:
    fbx = os.path.join(SA, RJ["caltrop_fbx"])
    assert os.path.exists(fbx), f"925 caltrop: make it first (blender_numpy/caltrop.py): {fbx}"
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", fbx); t.set_editor_property("destination_path", DEST); t.set_editor_property("destination_name", "SM_RD_Caltrop")
    t.set_editor_property("replace_existing", True); t.set_editor_property("automated", True); t.set_editor_property("save", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    m = unreal.load_asset(f"{DEST}/SM_RD_Caltrop")
    assert isinstance(m, unreal.StaticMesh), "925 caltrop: not imported"
    iron = unreal.load_asset(RJ["caltrop_material"]); assert iron, RJ["caltrop_material"]
    m.set_material(0, iron)
    b = m.get_bounding_box()
    eal.save_loaded_asset(m, False)
    REPORT.append(f"caltrop: {round(b.max.z - b.min.z, 1)} cm tall, {round(b.max.x - b.min.x, 1)} cm across")


# ------------------------------------------------------------------------------------------------ the materials
def material(name, M):
    path = f"{DEST}/M_RD_Art_{name}"
    if eal.does_asset_exist(path): m = unreal.load_asset(path); MEL.delete_all_material_expressions(m)
    else: m = unreal.AssetToolsHelpers.get_asset_tools().create_asset(f"M_RD_Art_{name}", DEST, unreal.Material, unreal.MaterialFactoryNew())
    y = [0]
    def n(cls, **props):
        y[0] += 110; e = MEL.create_material_expression(m, cls, -700, y[0])
        for k, v in props.items(): e.set_editor_property(k, v)
        return e
    def c(a, ap, b, bp):
        r = MEL.connect_material_expressions(a, ap, b, bp)
        assert r is not False, f"{name}: pin {bp}"
    def prop(e, p):
        assert MEL.connect_material_property(e, "", p) is not False, f"{name}: {p}"
    def custom(code, ins, out=unreal.CustomMaterialOutputType.CMOT_FLOAT1):
        e = n(unreal.MaterialExpressionCustom); e.set_editor_property("code", code); e.set_editor_property("output_type", out)
        cis = []
        for nm in ins:
            ci = unreal.CustomInput(); ci.set_editor_property("input_name", nm); cis.append(ci)
        e.set_editor_property("inputs", cis)
        return e
    k = M["kind"]
    col = n(unreal.MaterialExpressionVectorParameter, parameter_name="Color", default_value=unreal.LinearColor(*(M.get("color", [1, 1, 1]) + [1])))
    if k == "translucent":
        # (her body in smoke or silver: see-through, more solid at its rim (a fresnel), a little glow)
        fr = n(unreal.MaterialExpressionFresnel, exponent=float(M.get("fresnel", 2.0)))
        op = custom("return saturate(O * (0.35 + 0.65 * F));", ["O", "F"])
        c(n(unreal.MaterialExpressionScalarParameter, parameter_name="Opacity", default_value=float(M["opacity"])), "", op, "O"); c(fr, "", op, "F")
        em = custom("return C * (0.4 + E + F);", ["C", "E", "F"], unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        c(col, "", em, "C"); c(n(unreal.MaterialExpressionScalarParameter, parameter_name="Glow", default_value=float(M.get("emissive", 0.0))), "", em, "E"); c(fr, "", em, "F")
        prop(em, unreal.MaterialProperty.MP_EMISSIVE_COLOR); prop(op, unreal.MaterialProperty.MP_OPACITY)
        m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT); m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    elif k == "crosshair":
        tex = unreal.load_asset(M["texture"]); assert tex, M["texture"]
        ts = n(unreal.MaterialExpressionTextureSample, texture=tex)
        em = custom("return C * E;", ["C", "E"], unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        c(col, "", em, "C"); c(n(unreal.MaterialExpressionScalarParameter, parameter_name="Glow", default_value=float(M["emissive"])), "", em, "E")
        op = custom("return saturate(max(T.a * dot(T.rgb, float3(0.33, 0.33, 0.33)), 0.0) * 1.4);", ["T"])
        c(ts, "RGBA", op, "T")
        prop(em, unreal.MaterialProperty.MP_EMISSIVE_COLOR); prop(op, unreal.MaterialProperty.MP_OPACITY)
        m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT); m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        m.set_editor_property("two_sided", True)
    elif k == "acid":
        # (an amber pool, bubbling: bright and darker patches drifting over it, its rim soft)
        wp = n(unreal.MaterialExpressionWorldPosition); tm = n(unreal.MaterialExpressionTime); uv = n(unreal.MaterialExpressionTextureCoordinate, coordinate_index=0)
        b_ = custom("float a = sin(P.x * 0.045 + T * 2.1) * sin(P.y * 0.051 - T * 1.7);\nfloat b = sin((P.x + P.y) * 0.083 + T * 3.3);\nreturn 0.7 + 0.22 * a + 0.12 * b;", ["P", "T"])
        c(wp, "", b_, "P"); c(tm, "", b_, "T")
        em = custom("return C * E * B;", ["C", "E", "B"], unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        c(col, "", em, "C"); c(n(unreal.MaterialExpressionScalarParameter, parameter_name="Glow", default_value=float(M["emissive"])), "", em, "E"); c(b_, "", em, "B")
        op = custom("float r = length(U - 0.5) * 2.0; return 0.85 * saturate((1.0 - r) * 6.0);", ["U"])
        c(uv, "", op, "U")
        prop(em, unreal.MaterialProperty.MP_EMISSIVE_COLOR); prop(op, unreal.MaterialProperty.MP_OPACITY)
        m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT); m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    elif k == "puff":
        # (a soft round puff of smoke, its edge broken by drifting noise: the smoke bomb's cloud)
        uv = n(unreal.MaterialExpressionTextureCoordinate, coordinate_index=0); wp = n(unreal.MaterialExpressionWorldPosition); tm = n(unreal.MaterialExpressionTime)
        sh = custom("float2 d = U - 0.5; float r = length(d) * 2.0;\nfloat n = sin(P.x * 0.013 + T * 0.6 + d.x * 5.0) * sin(P.y * 0.017 - T * 0.5 + d.y * 6.0) * 0.5 + 0.5;\n"
                    "float m = sin((d.x * 7.0 + d.y * 5.0) + T * 0.9 + P.z * 0.01) * 0.5 + 0.5;\nfloat a = saturate(1.0 - r * (0.85 + 0.3 * n)); a = a * a * (3.0 - 2.0 * a);\nreturn a * (0.6 + 0.25 * n + 0.15 * m);", ["U", "P", "T"])
        c(uv, "", sh, "U"); c(wp, "", sh, "P"); c(tm, "", sh, "T")
        op = custom("return S * O;", ["S", "O"]); c(sh, "", op, "S"); c(n(unreal.MaterialExpressionScalarParameter, parameter_name="Opacity", default_value=float(M["opacity"])), "", op, "O")
        em = custom("return C * (0.75 + 0.35 * S);", ["C", "S"], unreal.CustomMaterialOutputType.CMOT_FLOAT3); c(col, "", em, "C"); c(sh, "", em, "S")
        prop(em, unreal.MaterialProperty.MP_EMISSIVE_COLOR); prop(op, unreal.MaterialProperty.MP_OPACITY)
        m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT); m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        m.set_editor_property("two_sided", True)
    elif k == "ring":
        # (a bright band near a plane's rim, soft inside it: the flashbang's ring spreading out (its plane scaled in play))
        uv = n(unreal.MaterialExpressionTextureCoordinate, coordinate_index=0)
        sh = custom("float r = length(U - 0.5) * 2.0;\nfloat a = saturate(1.0 - abs(r - 0.86) / Th);\nreturn a * a * saturate((1.0 - r) * 12.0);", ["U", "Th"])
        c(uv, "", sh, "U"); c(n(unreal.MaterialExpressionScalarParameter, parameter_name="Thickness", default_value=float(M["thickness"])), "", sh, "Th")
        em = custom("return C * E * S;", ["C", "E", "S"], unreal.CustomMaterialOutputType.CMOT_FLOAT3)
        c(col, "", em, "C"); c(n(unreal.MaterialExpressionScalarParameter, parameter_name="Glow", default_value=float(M["emissive"])), "", em, "E"); c(sh, "", em, "S")
        prop(em, unreal.MaterialProperty.MP_EMISSIVE_COLOR); prop(sh, unreal.MaterialProperty.MP_OPACITY)
        m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT); m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        m.set_editor_property("two_sided", True)
    elif k == "haze":
        # (a shimmer over her: faint bands of light drifting up through her body)
        wp = n(unreal.MaterialExpressionWorldPosition); tm = n(unreal.MaterialExpressionTime)
        sh = custom("float s = sin(P.z * 0.21 - T * 7.0 + sin(P.x * 0.11 + T * 3.0) * 2.0) * 0.5 + 0.5;\nreturn s * s;", ["P", "T"])
        c(wp, "", sh, "P"); c(tm, "", sh, "T")
        op = custom("return O * (0.35 + S);", ["O", "S"]); c(n(unreal.MaterialExpressionScalarParameter, parameter_name="Opacity", default_value=float(M["opacity"])), "", op, "O"); c(sh, "", op, "S")
        em = custom("return float3(0.8, 0.85, 0.9) * (0.3 + S);", ["S"], unreal.CustomMaterialOutputType.CMOT_FLOAT3); c(sh, "", em, "S")
        prop(em, unreal.MaterialProperty.MP_EMISSIVE_COLOR); prop(op, unreal.MaterialProperty.MP_OPACITY)
        m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT); m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    else:
        prop(col, unreal.MaterialProperty.MP_BASE_COLOR)
        prop(n(unreal.MaterialExpressionConstant, r=float(M.get("roughness", 0.8))), unreal.MaterialProperty.MP_ROUGHNESS)
    # (a packaged game draws a mesh only in a material with its usage: her body and her copies are skinned)
    m.set_editor_property("used_with_skeletal_mesh", True); m.set_editor_property("used_with_static_lighting", False)
    print(f"925 MATERIAL-FINAL {name}")
    MEL.recompile_material(m); eal.save_loaded_asset(m, only_if_is_dirty=False)
    ins = MEL.get_statistics(m).num_pixel_shader_instructions
    assert ins > 0, f"925: M_RD_Art_{name} did not compile"
    return f"{name} {ins}"


if "materials" in STEPS:
    REPORT.append("materials: " + ", ".join(material(k, v) for k, v in RJ["materials"].items()))


# ------------------------------------------------------------------------------------------------ the arts on every map
def load(p, what):
    if not p: return None
    a = unreal.load_asset(p); assert a, f"925 {what}: {p} not found"; return a


def text_of(A):
    """its text with its numbers (an art has one rank: no placeholders left for the game)"""
    def num(v, pct):
        v = v * 100.0 if pct and v <= 1.0 else v
        return f"{v:.0f}" if abs(v - round(v)) < 1e-6 else f"{v:.1f}"
    t = A["text"]
    for key, arr in (("{v2}", A.get("values2")), ("{v}", A.get("values")), ("{s}", A.get("seconds"))):
        if key in t and arr: t = t.replace(key + "%", num(arr[0], True) + "%").replace(key, num(arr[0], False))
    return t.replace("{share}", num(A.get("share", 0), False))


if "arts" in STEPS:
    mats = {k: unreal.load_asset(f"{DEST}/M_RD_Art_{k}") for k in RJ["materials"]}
    assert all(mats.values()), f"925 arts: run materials first ({[k for k, v in mats.items() if not v]})"
    caltrop = unreal.load_asset(f"{DEST}/SM_RD_Caltrop"); assert caltrop, "925 arts: run caltrop first"
    shared = {k: load(v, k) for k, v in RJ["shared"].items() if k != "rope_material"}
    defs = []
    for A in RJ["arts"]:
        d = unreal.RDSecondaryDef()
        for f, v in (("name", A["name"]), ("hero", RJ["hero"]), ("title", A["title"]), ("text", text_of(A)), ("kind", unreal.RDSecondaryKind.ACTIVE),
                     ("values", [float(x) for x in A.get("values", [])]), ("values2", [float(x) for x in A.get("values2", [])]), ("seconds", [float(x) for x in A.get("seconds", [])]),
                     ("cooldowns", [float(A["cooldown"])]), ("reach", float(A.get("reach", 0))), ("share", float(A.get("share", 0))), ("slot", int(A["place"])),
                     ("dex", float(A["dex"])), ("mesh_scale", float(A.get("mesh_scale", 1.0))), ("fx_scale", float(A.get("fx_scale", 1.0))), ("clip", A.get("clip") or "None")):
            d.set_editor_property(f, v)
        mp = A.get("mesh")
        d.set_editor_property("mesh", caltrop if mp == "caltrop" else load(mp, A["name"]))
        d.set_editor_property("fx", load(A.get("fx"), A["name"])); d.set_editor_property("fx2", load(A.get("fx2"), A["name"]))
        d.set_editor_property("material", mats.get(A.get("material")) if A.get("material") else None)
        if A.get("tint"): d.set_editor_property("tint", unreal.LinearColor(*(A["tint"] + [1])))
        defs.append(d)
    for mp in MAPS:
        open_map(mp)
        g = generator()
        sec = [s for s in g.get_editor_property("secondaries") if not (str(s.hero) == RJ["hero"] and int(s.slot) > 0)]
        g.set_editor_property("secondaries", sec + defs)
        items = [it for it in g.get_editor_property("items") if not str(it.name).startswith("Manual of ")]
        src = next((it for it in items if str(it.name) == RJ["manual_icon_from"]), None)
        assert src, f"925 arts: {RJ['manual_icon_from']} not on {mp}"
        for A in RJ["arts"]:
            it = unreal.RDItemDef(); it.import_text(src.export_text())
            for f, v in (("name", "Manual of " + A["title"]), ("kind", unreal.RDItemKind.TOME), ("spell", A["name"]), ("tiers", [int(A["place"])]), ("weight", 0.0),
                         ("looks", f"A rogue's manual: {A['title'].lower()}. {text_of(A)}")):
                it.set_editor_property(f, v)
            items.append(it)
        g.set_editor_property("items", items)
        g.set_editor_property("art_disc", shared["disc"]); g.set_editor_property("art_plane", shared["plane"]); g.set_editor_property("art_cylinder", shared["cylinder"])
        g.set_editor_property("art_rope_material", mats[RJ["shared"]["rope_material"]])
        g.modify(); les.save_current_level()
        REPORT.append(f"{mp}: {len(defs)} arts, {len(RJ['arts'])} manuals, {sum(1 for s in sec if str(s.hero) != RJ['hero'])} other abilities kept")
        del g, sec, items, src
        import gc; gc.collect()

print("925 " + " | ".join(REPORT))
import gc; gc.collect()
