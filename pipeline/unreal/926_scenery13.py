"""The list of 2026-11-14 (docs/improvements13.txt): the biomes' scenery, on brokenspire (the user's choices: memory improvements13-plan).
Steps (name them; several in one run, in this order):
  kit <dir>  the scenery's own pieces made in Blender (blender_numpy/scenery13_kit.py -> SourceArt/wilderness/scenery13) imported
             into /Game/RandomDungeon/Wild13/Kit, each material slot an instance of the wilds' bark (opaque) or leaves (masked,
             both faces) master with its own picture
  items      the scenery's new things (scenery13.json's items: honey, wild fruit, eggs, mushrooms) on every map of the game, each a
             copy of the item it is "like" with its own numbers (a thing carried from the wilds must exist where she takes it)
  icons <dir>  the new things' pictures (ui_art.json's honey, eggs, mushrooms ...: painted by rdm4_ui_gen.py --only <names>, exported by
             rdm4_ui_cut.py --export <dir>) as /Game/RandomDungeon/UI/T_RDM4_<name>, named in every game map's UIArt
  fauna      the farm animals a scenery's herd may be (scenery13.json's fauna: goats in a shepherd's fold) as wild animals of no
             biome: they come only with their scenery, never on their own
  scenery    scenery13.json's pieces into WildPieces (n13_<name>#<n>) and its kinds into WildSceneryKinds (through wild_tables.py,
             as 924's), its effects into WildSceneryFx (f13_<name>), its channels into WildChannelRules, the far storms, and the
             biomes' swales from biomes.json
C++ first (RD/RDWildScenery13.cpp, RD/RDWildRuin12.cpp's layouts, RDWildWorld.cpp's SceneryIn and channels). Args: steps"""
import os, sys, json, unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib, wild_tables
importlib.reload(wild_tables)          # (ue_exec keeps a module imported between runs: its REPORT and any change to it)
from wild_tables import les, eal, SA, REPORT, generator, lay_table
importlib.reload(importlib.import_module("ui_tex"))
from ui_tex import ui_texture
at = unreal.AssetToolsHelpers.get_asset_tools(); MEL = unreal.MaterialEditingLibrary
ARGS = sys.argv[1:]
J = json.load(open(os.path.join(SA, "scenery13.json"), encoding="utf-8"))
KIT = "/Game/RandomDungeon/Wild13/Kit"
MAPS = "/Game/RandomDungeon/Maps/"
GAME_MAPS = ("brokenspire", "mistward_castle", "vel_morrath", "war_engine", "sewers", "kethrys_spire", "heaven_fortress")


def translucent_master():
    """M_N13_Translucent: a soft see-through master (the storm's rain; mist, steam and spray after it): its picture's colour times Tint
    as its colour (unlit: it is seen from afar and in front of the sky), its alpha times Opacity as its opacity, both faces; made once"""
    path = f"{KIT}/M_N13_Translucent"
    if eal.does_asset_exist(path): return unreal.load_asset(path)
    m = at.create_asset("M_N13_Translucent", KIT, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    m.set_editor_property("used_with_static_lighting", False)
    for u in ("used_with_instanced_static_meshes", "used_with_nanite"):
        try: m.set_editor_property(u, True)
        except Exception: pass
    tx = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -700, 0)
    tx.set_editor_property("parameter_name", "Tex")
    tx.set_editor_property("texture", unreal.load_asset(f"{KIT}/T_N13_StormRain"))
    tint = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -700, -250)
    tint.set_editor_property("parameter_name", "Tint"); tint.set_editor_property("default_value", unreal.LinearColor(0.35, 0.37, 0.40, 1.0))
    op = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, 250)
    op.set_editor_property("parameter_name", "Opacity"); op.set_editor_property("default_value", 0.55)
    mc = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -350, -150)
    ma = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -350, 150)
    assert MEL.connect_material_expressions(tx, "RGB", mc, "A") and MEL.connect_material_expressions(tint, "", mc, "B")
    assert MEL.connect_material_expressions(tx, "A", ma, "A") and MEL.connect_material_expressions(op, "", ma, "B")
    assert MEL.connect_material_property(mc, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    assert MEL.connect_material_property(ma, "", unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m); eal.save_loaded_asset(m, only_if_is_dirty=False)
    return m


def step_kit(src):
    src = os.path.abspath(src)
    rec = json.load(open(os.path.join(src, "scenery13_kit.json"), encoding="utf-8"))
    tasks = []
    for f in sorted(os.listdir(src)):
        if f.endswith(".png"):
            tk = unreal.AssetImportTask(); tk.filename = os.path.join(src, f); tk.destination_path = KIT
            tk.replace_existing = True; tk.automated = True; tk.save = True; tasks.append(tk)
    for name in rec:
        o = unreal.FbxImportUI(); o.import_mesh = True; o.import_materials = False; o.import_textures = False; o.import_as_skeletal = False
        o.static_mesh_import_data.combine_meshes = True; o.static_mesh_import_data.auto_generate_collision = True; o.static_mesh_import_data.generate_lightmap_u_vs = False
        tk = unreal.AssetImportTask(); tk.filename = rec[name]["fbx"]; tk.destination_path = KIT
        tk.replace_existing = True; tk.automated = True; tk.save = True; tk.options = o; tasks.append(tk)
    at.import_asset_tasks(tasks)
    bark, leaves = unreal.load_asset("/Game/RandomDungeon/Wild/M_RD_WildBark"), unreal.load_asset("/Game/RandomDungeon/Wild/M_RD_WildLeaves")
    assert bark and leaves, "926 kit: the wilds' masters are missing (887 trees)"
    clear = translucent_master()
    n = 0
    for name, R in rec.items():
        m = unreal.load_asset(f"{KIT}/{name}")
        assert m, f"926 kit: {name} was not imported"
        mats = list(m.get_editor_property("static_materials"))
        for i, sm in enumerate(mats):
            slot = str(sm.get_editor_property("material_slot_name"))
            mi_name = f"MI_N13_{slot}"; pth = f"{KIT}/{mi_name}"
            if not eal.does_asset_exist(pth): at.create_asset(mi_name, KIT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
            mi = unreal.load_asset(pth)
            MEL.set_material_instance_parent(mi, clear if slot in R.get("translucent", []) else leaves if slot in R.get("masked", []) else bark)
            tx = unreal.load_asset(f"{KIT}/T_N13_{slot}")
            assert tx, f"926 kit: no picture T_N13_{slot}"
            MEL.set_material_instance_texture_parameter_value(mi, "Tex", tx)
            eal.save_loaded_asset(mi, only_if_is_dirty=False)
            m.set_material(i, mi); n += 1
        eal.save_loaded_asset(m, only_if_is_dirty=False)
    REPORT.append(f"kit: {len(rec)} pieces, {n} slots")


def each(maps, fn, label):
    for mp in maps:
        if not eal.does_asset_exist(MAPS + mp): REPORT.append(f"{label}: no map {mp}"); continue
        les.load_level(MAPS + mp); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        g = next(a for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
        what = fn(g)
        g.modify(); les.save_current_level()
        del g
        import gc; gc.collect()
        REPORT.append(f"{label} {mp}: {what}")


def step_items():
    def fn(g):
        items = list(g.get_editor_property("items"))
        names = {x["name"] for x in J["items"]}
        items = [i for i in items if str(i.name) not in names]
        made = []
        for X in J["items"]:
            like = next((i for i in items if str(i.name) == X["like"]), None)
            assert like, f"926 items: no {X['like']} on this map to copy"
            it = unreal.RDItemDef()
            for k in ("kind", "amount", "seconds", "weight", "icon", "looks", "tiers", "found_max"): it.set_editor_property(k, like.get_editor_property(k))
            # (a number not given is the copied item's: a component (the third phase's resin, as Glue) has no food's)
            it.set_editor_property("name", X["name"])
            for k in ("amount", "seconds", "weight"):
                if k in X: it.set_editor_property(k, float(X[k]))
            it.set_editor_property("icon", unreal.Name(X["icon"])); it.set_editor_property("looks", X["looks"])
            # (found only at their scenery: no tier puts them in a container)
            it.set_editor_property("tiers", [])
            items.append(it); made.append(X["name"])
        g.set_editor_property("items", items)
        return ", ".join(made)
    each(GAME_MAPS, fn, "items")


def step_icons(src):
    src = os.path.abspath(src)
    # (the pictures painted for these things (in <dir>); an item may take a picture the maps have already: fruit, a pumpkin)
    names = sorted(n for n in {x["icon"] for x in J["items"]} if os.path.exists(os.path.join(src, f"{n}.png")))
    assert names, f"926 icons: no item's picture in {src} (rdm4_ui_cut.py --export)"
    tex = {n: ui_texture(os.path.join(src, f"{n}.png"), "/Game/RandomDungeon/UI", f"T_RDM4_{n}") for n in names}
    def fn(g):
        ua = g.get_editor_property("ui_art")
        for n, t in tex.items():
            art = unreal.RDUIArt(); art.set_editor_property("texture", t)
            art.set_editor_property("border", unreal.Vector4(0, 0, 0, 0)); art.set_editor_property("inner", unreal.Vector4(0, 0, 1, 1))
            ua[unreal.Name(n)] = art
        g.set_editor_property("ui_art", ua)
        return ", ".join(tex)
    each(GAME_MAPS, fn, "icons")


def step_fauna():
    g = generator()
    fa = [f for f in g.get_editor_property("wild_fauna") if str(f.name) not in J["fauna"]]
    town = {str(t.name): t for t in g.get_editor_property("town_animals")}
    for name in J["fauna"]:
        if name == "Horse":
            # (phase 2: the steppe's horse herds ("nomad yurt camps with horse herds"): the ridable horse's body and gaits (913, 915),
            # its mesh facing +X at scale 1 as ARDHorse lays it; the walk and the gallop at the speeds its clips were made for)
            h = g.get_editor_property("horse_def"); assert h.mesh and h.walk and h.run, "926 fauna: no horse (913, 915)"
            # (it runs off at its canter, played at the speed the canter was made for)
            run, run_cs = (h.canter, h.canter_clip_speed) if h.canter else (h.run, h.run_clip_speed)
            F = unreal.RDWildFauna(); F.name = name; F.mesh = h.mesh; F.idle = h.idle; F.eat = h.idle; F.walk = h.walk; F.run = run
            F.scale = 1.0; F.mesh_yaw = 0.0; F.walk_speed = h.walk_clip_speed; F.walk_clip_speed = h.walk_clip_speed
            F.run_speed = run_cs; F.run_clip_speed = run_cs; F.flee_min, F.flee_max = 120.0, 250.0
            F.biomes = []; F.per_km2 = 0.0; F.half_length = 110.0
            fa.append(F); continue
        t = town.get(name)
        assert t, f"926 fauna: no town animal {name}"
        F = unreal.RDWildFauna(); F.name = name; F.mesh = t.mesh; F.idle = t.idle; F.eat = t.graze; F.walk = t.walk; F.run = t.walk
        F.scale = t.scale; F.mesh_yaw = t.mesh_yaw; F.walk_speed = max(t.walk_speed, 30.0); F.walk_clip_speed = max(t.walk_speed, 30.0) / max(t.scale, 0.1)
        F.run_speed = max(t.walk_speed, 30.0) * 3.0; F.run_clip_speed = F.walk_clip_speed; F.flee_min, F.flee_max = 80.0, 160.0
        F.biomes = []; F.per_km2 = 0.0; F.half_length = 60.0
        fa.append(F)
    g.set_editor_property("wild_fauna", fa)
    g.modify(); les.save_current_level()
    REPORT.append(f"fauna: {', '.join(J['fauna'])} as herd-only wild animals ({len(fa)} kinds)")


def step_scenery():
    def more(k, K):
        k.set_editor_property("need_water", K.get("need_water", ""))
        k.set_editor_property("place", K.get("place", "")); k.set_editor_property("uses", K.get("uses", []))
        k.set_editor_property("hazards", K.get("hazards", [])); k.set_editor_property("herd", K.get("herd", ""))
        k.set_editor_property("ambush_r", float(K.get("ambush_r", 0)))
        k.set_editor_property("folk", K.get("folk", []))
    _, g = lay_table("scenery13.json", "n13_", "wild_scenery_kinds", "kinds", unreal.RDWildSceneryKind, more)
    # (every herd's beast must be a wild animal of the level, every use's things items of it)
    fauna = {str(f.name) for f in g.get_editor_property("wild_fauna")}
    items = {str(i.name) for i in g.get_editor_property("items")}
    for K in J["kinds"]:
        if K.get("herd"): assert K["herd"].split(";")[0].split(":")[0] in fauna, f"926 scenery: {K['name']}'s herd is no wild animal (926 fauna first)"
        for u in K.get("uses", []):
            kv = dict(x.split("=", 1) for x in u.split(";") if "=" in x)
            for t in [t for t in kv.get("things", "").split(",") if t]:
                assert t.split("|")[0] in items, f"926 scenery: {K['name']}'s thing {t.split('|')[0]} is no item (926 items first)"
    fx = {}
    for name, path in J["fx"].items():
        s = unreal.load_asset(path); assert s, f"926 scenery: no effect {path}"
        fx[unreal.Name("f13_" + name)] = s
    g.set_editor_property("wild_scenery_fx", fx)
    g.set_editor_property("wild_channel_rules", J["channels"])
    # (the far sights: storm cells, a grass fire's smoke)
    fs = []
    for F in J["farsights"]:
        sm = unreal.load_asset(F["mesh"]); assert sm, f"926 scenery: no far sight mesh {F['mesh']} (926 kit first)"
        f = unreal.RDWildFarSight(); f.name = F["name"]; f.biomes = F["biomes"]; f.mesh = sm; f.chance = float(F["chance"])
        f.km = unreal.Vector2D(float(F["km"][0]), float(F["km"][1])); f.drift = float(F.get("drift", 9.0)); f.seconds = float(F.get("secs", 360))
        fs.append(f)
    g.set_editor_property("wild_far_sights", fs)
    # (the materials a part may lay its pieces in)
    mats = {}
    for name, path in J.get("mats", {}).items():
        m = unreal.load_asset(path); assert m, f"926 scenery: no material {path}"
        mats[unreal.Name("m13_" + name)] = m
    g.set_editor_property("wild_scenery_mats", mats)
    # (the third phase: where the needles muffle her steps, and how far the monsters notice her there)
    g.set_editor_property("wild_quiet_biomes", J.get("quiet_biomes", []))
    g.set_editor_property("wild_quiet_notice", float(J.get("quiet_notice", 1.0)))
    # (the fifth phase: where the air is thin, and her slow there)
    g.set_editor_property("wild_thin_air_biomes", J.get("thin_air_biomes", []))
    g.set_editor_property("wild_thin_air_slow", float(J.get("thin_air_slow", 0.0)))
    # (the eighth phase: the auroras' regions and their curtain)
    au = J.get("aurora", {})
    g.set_editor_property("wild_aurora_biomes", au.get("biomes", []))
    g.set_editor_property("wild_aurora_mesh", unreal.load_asset(au["mesh"]) if au.get("mesh") else None)
    assert not au.get("mesh") or g.get_editor_property("wild_aurora_mesh"), "926 scenery: no aurora mesh " + au.get("mesh", "")
    # (every kind's people must be townsfolk of the level)
    defs = [str(t.name) for t in g.get_editor_property("townsfolk")]
    for K in J["kinds"]:
        for f in K.get("folk", []):
            assert any(d.startswith(f.split("|")[0]) for d in defs), f"926 scenery: {K['name']}'s folk {f.split('|')[0]} is no townsfolk"
    # (the swales from biomes.json, the biome table's own source (887 data writes them too))
    B = {b["name"]: b for b in json.load(open(os.path.join(SA, "biomes.json"), encoding="utf-8"))["biomes"]}
    bios = list(g.get_editor_property("wild_biomes")); sw = []
    for i, b in enumerate(bios):
        v = float(B.get(str(b.name), {}).get("swale", 0.0))
        if abs(b.get_editor_property("swale") - v) > 1e-4: b.set_editor_property("swale", v); bios[i] = b
        if v > 0: sw.append(f"{b.name} {v} m")
    g.set_editor_property("wild_biomes", bios)
    g.modify(); les.save_current_level()
    REPORT.append(f"scenery: {len(J['kinds'])} kinds, {len(fx)} effects, {len(J['channels'])} channel rules, {len(fs)} far sights, {len(mats)} materials, swales {', '.join(sw)}")


i = 0
while i < len(ARGS):
    for s in ARGS[i].split(","):
        if not s: continue
        if s == "kit": i += 1; step_kit(ARGS[i])
        elif s == "icons": i += 1; step_icons(ARGS[i])
        else: {"items": step_items, "fauna": step_fauna, "scenery": step_scenery}[s]()
    i += 1
print("926 " + " | ".join(REPORT))
import gc
gc.collect()
