"""The list of 2026-11-11 (docs/improvements11.txt), its fifth phase: the wilderness and Graymourne, on brokenspire. Steps (name them,
comma-separated):
  heads    "some NPCs in graymourne do not have heads": every townsfolk def whose body ends at its neck (the mesh's top within 12 cm
           over its own neck bone, measured on a mesh actor) and that has no parts gets its pack's separate head and hair (the
           folder beside the body's Full/: Separate/<base>_Head*, _Hair*), following the body; run it after the cities' stages
           (892, 894, 896, 906, 908 write their people anew)
  meadows  the meadows' trees in clusters, strips and clearings (Grove), and their debris (SourceArt/wilderness/meadows11.json);
           after 887 data
  leaves   the leaves blown round her in the biomes meadows11.json names
  events   the director's new roaming kinds (SourceArt/wilderness/events11.json); after 912
  port     Graymourne's harbour open to the sea, its ramps, the water's splash and rings (SourceArt/graymourne/port11.json);
           after 896
Args: steps   e.g.  ue_exec.py 920_wild11.py heads,meadows,leaves,events,port"""
import unreal, sys
STEPS = [s for a in sys.argv[1:] for s in a.split(",") if s]
MAP = "/Game/RandomDungeon/Maps/brokenspire"; SCRATCH = "/Game/RandomDungeon/Maps/rl_scratch"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ar = unreal.AssetRegistryHelpers.get_asset_registry()
REPORT = []


def generator():
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def neck_top(m):
    """a body's top and its neck bone's height, on a mesh actor in the open level (its own reference pose)"""
    a = eas.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 100000))
    try:
        c = a.skeletal_mesh_component
        if hasattr(c, "set_skinned_asset_and_update"): c.set_skinned_asset_and_update(m)
        else: c.set_editor_property("skeletal_mesh", m)
        neck = c.get_socket_location("neck_01").z - 100000 if c.does_socket_exist("neck_01") else None
    finally:
        a.destroy_actor()
    b = m.get_bounds()
    return b.origin.z + b.box_extent.z, neck


def separate_parts(m):
    """the pack's separate head and hair for a body (Separate/ beside its Full/ folder): the first of each"""
    folder = m.get_path_name().split(".")[0].rsplit("/", 1)[0]
    sep = (folder.rsplit("/", 1)[0] if folder.endswith("/Full") else folder) + "/Separate"
    names = sorted(str(x.package_name) for x in ar.get_assets_by_path(sep, recursive=True) if x.asset_class_path.asset_name == "SkeletalMesh")
    head = next((n for n in names if n.rsplit("/", 1)[-1].split("_Head")[0] != n.rsplit("/", 1)[-1] and "_Head" in n), None)
    hair = next((n for n in names if "_Hair" in n), None)
    return [unreal.load_asset(n) for n in (head, hair) if n]


if "heads" in STEPS:
    g = generator()
    defs = list(g.get_editor_property("townsfolk"))
    measured, fixed, missing = {}, [], []
    for i, d in enumerate(defs):
        m = d.get_editor_property("mesh")
        if not m or list(d.get_editor_property("parts") or []): continue
        k = m.get_path_name()
        if k not in measured: measured[k] = neck_top(m)
        top, neck = measured[k]
        if neck is None or top >= neck + 12.0: continue
        parts = separate_parts(m)
        if not any("_Head" in p.get_name() for p in parts): missing.append((str(d.name), m.get_name())); continue
        d.set_editor_property("parts", parts); defs[i] = d
        fixed.append((str(d.name), m.get_name(), [p.get_name() for p in parts]))
    g.set_editor_property("townsfolk", defs); g.modify(); les.save_current_level()
    REPORT.append(f"heads: {len(fixed)} of {len(defs)} defs given a head {fixed} | no head part found {missing}")
    del g, defs

import json, os
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"

if "meadows" in STEPS or "leaves" in STEPS:
    MJ = json.load(open(os.path.join(SA, "wilderness", "meadows11.json"), encoding="utf-8"))

if "meadows" in STEPS:
    # (the meadows' trees in clusters and strips with clearings between (their Grove share of the world's grove pattern), the
    # bushes partly so, and the debris: stumps, logs, branches, leaf piles; edited in place: 887 data would make the table again
    # without the later stages' changes (890's swaying grass): run this after 887 data)
    g = generator()
    biomes = list(g.get_editor_property("wild_biomes"))
    debris_paths = {d[0] for d in MJ["debris"]}
    made = []
    for i, b in enumerate(biomes):
        if str(b.name) not in MJ["biomes"]: continue
        # (the debris a run before made, whatever its file said then: a meadow has no logs or litter of its own)
        fol = [f for f in b.foliage if f.kind not in ("log", "litter") and (not f.mesh or f.mesh.get_path_name().split(".")[0] not in debris_paths)]
        for f in fol:
            if f.kind == "tree": f.set_editor_property("density", float(MJ["trees"]["density"])); f.set_editor_property("grove", float(MJ["trees"]["grove"]))
            elif f.kind == "bush": f.set_editor_property("grove", float(MJ["bushes"]["grove"]))
        for path, kind, dens, lo, hi, flags, grove, sink in MJ["debris"]:
            m = unreal.load_asset(path)
            if not m or not isinstance(m, unreal.StaticMesh): made.append(f"MISSING {path}"); continue
            F = unreal.RDWildFoliage()
            F.set_editor_property("mesh", m); F.set_editor_property("kind", kind); F.set_editor_property("density", float(dens))
            F.set_editor_property("scale_min", float(lo)); F.set_editor_property("scale_max", float(hi))
            F.set_editor_property("slope_max", 25.0 if kind == "log" else 32.0); F.set_editor_property("sink", float(sink))
            F.set_editor_property("cull_distance", 20000.0 if kind == "log" else 7000.0)
            F.set_editor_property("collision", "c" in flags); F.set_editor_property("align", "a" in flags); F.set_editor_property("near_only", "n" in flags)
            F.set_editor_property("grove", float(grove))
            fol.append(F)
            e = m.get_bounding_box().max - m.get_bounding_box().min
            made.append(f"{m.get_name()} {round(e.x)}x{round(e.y)}x{round(e.z)} cm")
        b.set_editor_property("foliage", fol); biomes[i] = b
        grass_sway = [(f.mesh.get_name(), len(f.materials)) for f in fol if f.kind == "grass"]
        REPORT.append(f"meadows {b.name}: {len(fol)} kinds; grass sway materials {grass_sway}")
    g.set_editor_property("wild_biomes", biomes); g.modify(); les.save_current_level()
    REPORT.append("debris " + "; ".join(made))
    del g, biomes

if "leaves" in STEPS:
    # (the leaves blown round her: the system chosen by 888 leaves11's screening, in the biomes named)
    g = generator()
    L = MJ["leaves"]
    fx = unreal.load_asset(L["fx"])
    g.set_editor_property("wild_leaves_fx", fx); g.set_editor_property("wild_leaves_biomes", L["biomes"])
    g.set_editor_property("wild_leaves_ahead", float(L["ahead"])); g.set_editor_property("wild_leaves_scale", float(L["scale"]))
    g.modify(); les.save_current_level()
    REPORT.append(f"leaves: {fx.get_name() if fx else 'MISSING ' + L['fx']} in {L['biomes']}")
    del g

if "events" in STEPS:
    # (the director's new roaming kinds, added to 912's (run this after 912, which makes WildPoiKinds again))
    EJ = json.load(open(os.path.join(SA, "wilderness", "events11.json"), encoding="utf-8"))
    g = generator()
    names = {k["name"] for k in EJ["kinds"]}
    kinds = [k for k in g.get_editor_property("wild_poi_kinds") if str(k.name) not in names]
    statics = {str(k.name) for k in kinds if not k.roaming}
    items = {str(i.name) for i in g.get_editor_property("items")}
    folk = {str(d.name) for d in g.get_editor_property("townsfolk") if d.get_editor_property("mesh")}
    fauna = {str(a.name) for a in g.get_editor_property("wild_fauna")}
    bad = []
    for e in EJ["kinds"]:
        K = unreal.RDWildPoiKind()
        for f, v in (("name", unreal.Name(e["name"])), ("title", e["title"]), ("biomes", e["biomes"]), ("weight", float(e["weight"])), ("roaming", True),
                     ("text", e.get("text", "")), ("place", e.get("place", "")), ("animals", e.get("animals", "")), ("folk", e.get("folk", "")),
                     ("gift", e.get("gift", "")), ("gift_gold", int(e.get("gold", 0)))):
            K.set_editor_property(f, v)
        kinds.append(K)
        bad += [f"{e['name']}: place {p}" for p in e.get("place", "").split(",") if p and p not in statics]
        bad += [f"{e['name']}: item {x.split('|')[0]}" for x in e.get("gift", "").split(";") if x and x.split("|")[0] not in items]
        bad += [f"{e['name']}: folk {e['folk']}" for _ in [0] if e.get("folk") and e["folk"] not in folk]
        bad += [f"{e['name']}: animal {a.split(':')[0]}" for a in e.get("animals", "").split(",") if a and a.split(":")[0] not in fauna]
    g.set_editor_property("wild_poi_kinds", kinds); g.modify(); les.save_current_level()
    REPORT.append(f"events: {len(EJ['kinds'])} roaming kinds added ({sum(1 for k in kinds if k.roaming)} roaming of {len(kinds)}) | missing {bad}")
    del g, kinds

def ring_material(R):
    """the rings on the water (a plane's UVs): a soft bright band near the rim and a fainter one inside it, see-through, unlit;
    Fade (set in play, 0 to 1) and Opacity scale it"""
    MEL = unreal.MaterialEditingLibrary; eal = unreal.EditorAssetLibrary
    path = "/Game/RandomDungeon/Wild11/M_RD_WaterRing"
    if eal.does_asset_exist(path): m = unreal.load_asset(path); MEL.delete_all_material_expressions(m)
    else: m = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_RD_WaterRing", "/Game/RandomDungeon/Wild11", unreal.Material, unreal.MaterialFactoryNew())
    y = [0]
    def n(cls, **props):
        y[0] += 110; e = MEL.create_material_expression(m, cls, -600, y[0])
        for k, v in props.items(): e.set_editor_property(k, v)
        return e
    def c(a, ap, b, bp):
        r = MEL.connect_material_expressions(a, ap, b, bp)
        assert r is not False, f"pin {bp}"
    sh = n(unreal.MaterialExpressionCustom)
    sh.set_editor_property("code", "float r = length(U - 0.5) * 2.0;\nfloat a = saturate(1.0 - abs(r - 0.86) / Th);\nfloat b = saturate(1.0 - abs(r - 0.62) / (Th * 0.7)) * 0.45;\n"
                                   "return (a * a + b * b) * saturate((1.0 - r) * 12.0);")
    sh.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT1)
    ins = []
    for nm in ("U", "Th"):
        ci = unreal.CustomInput(); ci.set_editor_property("input_name", nm); ins.append(ci)
    sh.set_editor_property("inputs", ins)
    c(n(unreal.MaterialExpressionTextureCoordinate, coordinate_index=0), "", sh, "U")
    c(n(unreal.MaterialExpressionScalarParameter, parameter_name="Thickness", default_value=float(R["thickness"])), "", sh, "Th")
    col = n(unreal.MaterialExpressionVectorParameter, parameter_name="Color", default_value=unreal.LinearColor(*R["color"]))
    fade = n(unreal.MaterialExpressionScalarParameter, parameter_name="Fade", default_value=1.0)
    opq = n(unreal.MaterialExpressionScalarParameter, parameter_name="Opacity", default_value=float(R["opacity"]))
    m1 = n(unreal.MaterialExpressionMultiply); c(sh, "", m1, "A"); c(fade, "", m1, "B")
    m2 = n(unreal.MaterialExpressionMultiply); c(m1, "", m2, "A"); c(opq, "", m2, "B")
    MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(m2, "", unreal.MaterialProperty.MP_OPACITY)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    print("920 MATERIAL-FINAL M_RD_WaterRing")
    MEL.recompile_material(m); eal.save_loaded_asset(m, only_if_is_dirty=False)
    REPORT.append(f"ring material: {MEL.get_statistics(m).num_pixel_shader_instructions} instructions")
    return m


if "port" in STEPS:
    # (Graymourne's harbour open to the sea (bPortWaterOpen: the world's sea lifted to its water round the port, no blockers or
    # town wall along it), the stone ramps up out of it ("Port.Ramp": a box in the quay's stone), the water's splash and rings;
    # run it after 896, which takes every "Port." piece out and writes its own)
    PJ = json.load(open(os.path.join(SA, "graymourne", "port11.json"), encoding="utf-8"))
    g = generator()
    cube = unreal.load_asset(PJ["ramp"]["mesh"]); wall = unreal.load_asset(PJ["ramp"]["material_from"])
    p = unreal.RDPiece(); p.mesh = cube
    b = cube.get_bounding_box()
    p.adjust = unreal.Transform(unreal.Vector(0, 0, -b.min.z), unreal.Rotator(0, 0, 0), unreal.Vector(1, 1, 1))
    p.size = b.max - b.min; p.collision = True
    if wall: p.material = wall.get_material(0)
    pieces = g.get_editor_property("pieces"); pieces["Port.Ramp"] = p; g.set_editor_property("pieces", pieces)
    sp = unreal.load_asset(PJ["splash"]["fx"]); rg = unreal.load_asset(PJ["ring"]["fx"])
    rm = ring_material(PJ["ring"])
    for f, v in (("port_water_open", bool(PJ["open"])), ("water_splash_fx", sp), ("water_ring_fx", rg), ("water_splash_scale", float(PJ["splash"]["scale"])),
                 ("water_ring_scale", float(PJ["ring"]["scale"])), ("water_fx_life", float(PJ["life"])),
                 ("water_ring_material", rm), ("water_ring_mesh", unreal.load_asset("/Engine/BasicShapes/Plane")),
                 ("water_ring_radius", unreal.Vector2D(*PJ["ring"]["radius"])), ("water_ring_life", float(PJ["ring"]["life"]))):
        g.set_editor_property(f, v)
    g.modify(); les.save_current_level()
    REPORT.append(f"port: open {PJ['open']}, ramp {p.size} in {p.material.get_name() if p.material else None}, splash {sp.get_name() if sp else 'MISSING'}, ring {rg.get_name() if rg else 'MISSING'}")
    del g, pieces, p, cube, wall, sp, rg

print("920 " + " | ".join(REPORT))
import gc; gc.collect()
