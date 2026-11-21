"""landmarks15: the user's list of 2026-11-20 (docs/improvements15.txt, item 25: docs/wilderness_ideas.md's ideas), its plan's tenth phase:
the regions' landmarks and lookouts, on brokenspire (C++ RD/RDList15i.cpp). From SourceArt/wilderness/landmarks15.json:
- the regions' landmark kinds (RegionLandmarkLines15: a great tree, a smoking crater, a beacon stone with its beam by night, a
  lighthouse with its lamp by night; the open lands keep their broken towers), their meshes (RegionLandmarkMeshes15) and the
  materials of their extras (RegionLandmarkMats15: the smoke, the beam, the lamp, made here: /Game/RandomDungeon/Wild15/Materials)
- the travellers' camps' smoke by night (CampSmokeMesh15, CampSmokeMat15, CampSmokeSize15)
- the villages' houses lit by night (bHouseLights15, HouseLightCandelas15)
The lookouts need no data (the Old Watchtower's pieces, 882's); their map symbol is wild_symbols.py's wmap_lookout through `887 symbols`.
Args: none"""
import os, json, gc, unreal
WILD = "/Game/RandomDungeon/Maps/brokenspire"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\wilderness"
MATS = "/Game/RandomDungeon/Wild15/Materials"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
J = json.load(open(os.path.join(SA, "landmarks15.json"), encoding="utf-8"))


def material(name, spec):
    """an unlit material of ours, made again in place on every run: translucent (a colour at an opacity, its edges softened by the
    view's angle) or additive (a glowing colour)"""
    path = MATS + "/M_RD_" + name.capitalize() + "15"
    m = unreal.load_asset(path) if eal.does_asset_exist(path) else unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_RD_" + name.capitalize() + "15", MATS, unreal.Material, unreal.MaterialFactoryNew())
    MEL.delete_all_material_expressions(m)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    col = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -600, 0)
    c = spec["color"]
    if spec["blend"] == "additive":
        m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
        mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -300, 0)
        col.set_editor_property("constant", unreal.LinearColor(c[0], c[1], c[2], 1.0))
        mul.set_editor_property("const_b", float(spec["emissive"]))
        assert MEL.connect_material_expressions(col, "", mul, "A")
        assert MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    else:
        m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        col.set_editor_property("constant", unreal.LinearColor(c[0], c[1], c[2], 1.0))
        assert MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        # (the column's opacity falls toward its sides as seen (a fresnel's complement): a soft plume, not a solid pipe)
        fr = MEL.create_material_expression(m, unreal.MaterialExpressionFresnel, -600, 250)
        one = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -400, 250)
        mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -200, 250)
        mul.set_editor_property("const_b", float(spec["opacity"]))
        assert MEL.connect_material_expressions(fr, "", one, "")
        assert MEL.connect_material_expressions(one, "", mul, "A")
        assert MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m); eal.save_loaded_asset(m, False)
    return m


def go():
    les.load_level(WILD)
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    mats = {k: material(k, v) for k, v in J["materials"].items()}
    mat_names = list(mats.keys())
    meshes = []; lines = []
    def mesh_index(path):
        m = unreal.load_asset(path); assert m, path
        if m not in meshes: meshes.append(m)
        return meshes.index(m)
    for k in J["kinds"]:
        mi = mesh_index(k["main"])
        xi = mesh_index(k["extra"]) if k.get("extra") else -1
        ma = mat_names.index(k["material"]) if k.get("material") else -1
        lines.append("|".join([k["kind"], ";".join(k["biomes"]), str(mi), f'{k["height"]:g}', str(xi), f'{k.get("extra_height", 0):g}', f'{k.get("extra_width", 0):g}',
                               "1" if k.get("night") else "0", str(ma), f'{k.get("sink", 2.0):g}']))
    # (every biome named must be one of the world's)
    known = {str(b.get_editor_property("name")) for b in g.get_editor_property("wild_biomes")}
    for k in J["kinds"]:
        for b in k["biomes"]: assert b in known, (k["kind"], b, sorted(known))
    g.set_editor_property("region_landmark_lines15", lines)
    g.set_editor_property("region_landmark_meshes15", meshes)
    g.set_editor_property("region_landmark_mats15", [mats[n] for n in mat_names])
    g.set_editor_property("region_landmark_km15", float(J["km"]))
    cs = J["camp_smoke"]
    g.set_editor_property("camp_smoke_mesh15", unreal.load_asset(cs["mesh"]))
    g.set_editor_property("camp_smoke_mat15", mats[cs["material"]])
    g.set_editor_property("camp_smoke_size15", unreal.Vector(cs["width"], cs["width"], cs["height"]))
    g.set_editor_property("house_lights15", bool(J["house_lights"]["on"]))
    g.set_editor_property("house_light_candelas15", float(J["house_lights"]["candelas"]))
    g.modify(); les.save_current_level()
    print("LANDMARKS15", len(lines), "kinds |", [l.split("|")[0] for l in lines], "| meshes", [m.get_name() for m in meshes], "| materials", mat_names)
    del g, meshes, mats


go()
gc.collect()
