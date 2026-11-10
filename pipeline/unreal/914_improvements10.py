"""The user's list of 2026-11-10 (docs/improvements10.txt), its first phase's data (the C++ is the rest: RD/RDConsoleCmds.cpp, the quick
bar's items, the anvil's mending and stacks, the quest window, the save drop-down, the horse's blocker, the ambushers). Steps (all
by default, or name some):
  brewers  "only mages and martial artists should be able to make healing potions and mana potions at the anvil": the generator's
           PotionBrewers (Mage, MartialArtist) on every map of the game
  horse    "horse travel should be at least 5x faster than what the player can move": brokenspire's HorseDef.SpeedMul 5.5
  food     "if there is food on a table, the player should be able to put it into the inventory": on the six dungeons of the game
           (the castle and its copies) the prep table is the bare one (890's SM_Kit_PrepTableBare) with the town's food pieces laid
           on it as things to take (bTableFood); the start section built again (its furniture is saved)
  noshield "the warrior should not have a default shield on": every map of the game and martial_arts checked again (899's rule:
           no start shield, no shield mesh on her weapons), a shield found anywhere taken off and said
The second phase (C++ RD/RDSkyFar.cpp):
  sky      "a disc in the sky in the day time, a visible border near the horizon, also at night": brokenspire's FarLandMaterial
           (M_RD_FarLand: the far land's ring lit, its colour the world model's ground by vertex, two-sided) and its clouds'
           SkyCoverRange (0.05 to 0.6: at 0.1 to 1 fair weather drew a grey deck over the whole sky, 884 sky10)
  stairs   "the stairway to get into the guard towers in mistward castle looks like a series of stairs was built up and angled until
           it reached the top" (E:\\temp\\stonestairway.jpg): brokenspire's StairBlockMaterial and StairWallMaterial (Castle of
           Eternal Mist's stair stone for the blocks, its pale brick for the coursed wall under them: RDTownPlan.cpp's CastleStairBuild)
  dungeon  "when the tier boss appears, a teleporter back to the first dungeon room or to brokenspire should spawn there with him"
           (bBossPorts) and "a library's bookshelves should contain either scrolls of that tier or below or crafting components for
           scrolls of that tier or below, could also contain tomes" (bLibraryShelves) on the six dungeons of the game
  crowd    "some of the NPC crowd in the Arena have no heads": each crowd body's head and hair (the NPC Characters pack's _Full_02
           bodies carry them as meshes of their own, Separate/, as 882's townsfolk) as CrowdParts, on every map with a crowd
  see      "if the player walks under a structure that blocks sight of her, make the structure see-through": brokenspire's bSeeThrough
The third phase (C++ RD/RDList10c.cpp):
  forge    "the fighter and only the fighter should be able to craft basic weapons and armor she has already looted at a forge - a
           forge is a new crafting station": bForge (ForgeHeroes Warrior, ForgePieces Forge) and a Station "Forge" recipe for every
           weapon, shield and set of armour of the game's tier 1, its cost what breaking it down gives and half again (rounded up), on
           every map of the game; the dungeons' start sections built again (a forge by the great hall's anvil)
  oven     "everyone should be able to craft food items from food components at an oven": the dungeons' kitchens' bread ovens
           (bDungeonOvens) with brokenspire's oven recipes, and the gardens' ingredients found in their containers (weight 12)
  ankh     the revealing light: SM_RD_Ankh (blender_numpy/ankh.py) imported with a metal of its own, the item "Revealing Ankh" (kind
           Light, the game's tier 2, held as the torch is: each hero's torch grip), its picture (ui_art's "ankh") on every map
  block    "when the warrior does a shield block, she should be in a new animation shield block stance like in this picture":
           AS_Warrior3_BlockLunge (blender_numpy/warrior3_block.py through tripo_build.py) imported, her AnimBP's whole-body blend
           toward it under the upper body's layer (BlockLegsAlpha: while she stands), the layer's clip the same, BlockClip on every map
The fourth phase (C++ RD/RDList10d.cpp):
  lines    "generate at least 30 different things the non-interactive NPCs can say depending on what their job is": brokenspire's
           RoleLines from SourceArt/brokenspire/role_lines_a.json, _b, _c (every town; a line naming the castle or the Mistgate
           Brokenspire's alone) and SourceArt/heaven/role_lines.json (Heaven's alone); the farm families' lines from
           SourceArt/wilderness/farm_lines10.json added to WildFarmLines
  sleep    "if an NPC is supposed to be sleeping at night, have them sleep in their beds with a new animation or clip in blender":
           AS_Town_Sleep (blender_numpy/town_work_clips.py only=Sleep writefbx into SourceArt/brokenspire/work_clips/sleep) imported
           on the NPC pack's skeleton, every townsfolk def with work clips given it as "Sleep"
  people   "there should be more children in town ..." and "the town should be 25% more populated ...": brokenspire's bTownBeds and
           bMorePeople (HomeSecondShare, HomeChildShare)
  sleepsrc the four FBX town_work_clips.py takes (the NPC pack's SKM_Manny, NPC_Character_01's body, MM_Idle, MM_Walk_Fwd) exported to
           SourceArt/brokenspire/work_clips/src (then Blender, then sleep)
C++ first (RD/RDList10b.cpp, RD/RDList10c.cpp, RD/RDList10d.cpp). Args: [brewers] [horse] [food] [noshield] [sky] [stairs] [dungeon] [crowd] [see] [forge] [oven] [ankh] [block] [lines] [sleep] [people] [sleepsrc]"""
import sys, unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary
V = unreal.Vector
MAPS = "/Game/RandomDungeon/Maps/"
GAME_MAPS = ("brokenspire", "mistward_castle", "vel_morrath", "war_engine", "sewers", "kethrys_spire", "heaven_fortress")
DUNGEONS = GAME_MAPS[1:]
STEPS = [a for a in sys.argv[1:] if a in ("brewers", "horse", "food", "noshield", "sky", "stairs", "dungeon", "crowd", "see", "forge", "oven", "ankh", "block", "lines", "sleep", "people", "sleepsrc")] or ["brewers", "horse", "food", "noshield", "sky", "stairs", "dungeon", "crowd", "see", "forge", "oven", "ankh", "block", "lines", "sleep", "people"]
REPORT = []


def open_map(m):
    path = MAPS + m
    if not ues.get_editor_world().get_path_name().startswith(path + "."):
        les.load_level(path); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    w = ues.get_editor_world(); assert w.get_path_name().startswith(path + "."), w.get_path_name()
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def each(maps, fn, label):
    for m in maps:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"{label}: no map {m}"); continue
        g = open_map(m)
        what = fn(g)
        g.modify(); les.save_current_level()
        unreal.SystemLibrary.execute_console_command(None, "obj gc")
        REPORT.append(f"{label} {m}: {what}")


def piece(mesh):
    """a piece in the dungeon frame, footprint centred, bottom at z 0, no collision (890's piece() for a static mesh)"""
    p = unreal.RDPiece(); p.mesh = mesh
    b = mesh.get_bounding_box()
    p.adjust = unreal.Transform(V(-(b.min.x + b.max.x) / 2, -(b.min.y + b.max.y) / 2, -b.min.z), unreal.Rotator(0, 0, 0), V(1, 1, 1))
    p.size = V(b.max.x - b.min.x, b.max.y - b.min.y, b.max.z - b.min.z)
    p.collision = False
    return p


if "brewers" in STEPS:
    def brewers(g):
        g.set_editor_property("potion_brewers", [unreal.Name("Mage"), unreal.Name("MartialArtist")])
        heroes = [str(h.name) for h in g.get_editor_property("heroes")]
        return f"potion brewers Mage, MartialArtist (heroes here: {', '.join(heroes)})"
    each(GAME_MAPS, brewers, "brewers")

if "horse" in STEPS:
    def horse(g):
        d = g.get_editor_property("horse_def")
        was = d.get_editor_property("speed_mul")
        d.set_editor_property("speed_mul", 5.5); g.set_editor_property("horse_def", d)
        return f"the horse {was} -> 5.5 times her speed"
    each(["brokenspire"], horse, "horse")

if "food" in STEPS:
    bare = unreal.load_asset("/Game/RandomDungeon/Town7/SM_Kit_PrepTableBare")
    K = "/Game/Castle/Furniture/Kit/"
    foods = {}
    for n, m in (("FoodBread", "SM_Kit_BreadLoaf"), ("FoodBreadRound", "SM_Kit_BreadRound"), ("FoodCheese", "SM_Kit_Cheese"), ("FoodApples", "SM_Kit_AppleBasket")):
        a = unreal.load_asset(K + m)
        if a: foods["Town." + n] = piece(a)
        else: REPORT.append("food: MISSING " + m)
    if not bare: REPORT.append("food: no bare prep table (run 890 town first)")

    def food(g):
        P = g.get_editor_property("pieces")
        pk = unreal.Name("PrepTable")
        if pk not in P: return "no PrepTable piece: nothing to lay food on"
        pt = P[pk]; was = pt.mesh.get_name() if pt.mesh else "none"
        if bare: pt.mesh = bare; P[pk] = pt
        for k, v in foods.items(): P[unreal.Name(k)] = v
        g.set_editor_property("pieces", P)
        items = {str(i.get_editor_property("name")) for i in g.get_editor_property("items")}
        missing = [n for n in ("Bread", "Cheese", "Fruit") if n not in items]
        g.set_editor_property("table_food", True)
        g.modify(); g.build_start_section()
        return f"prep table {was} -> {bare.get_name() if bare else was}, {len(foods)} food pieces, table food on" + (f"; MISSING items {missing}" if missing else "")
    if bare: each(DUNGEONS, food, "food")

if "noshield" in STEPS:
    def noshield(g):
        ss = dict(g.get_editor_property("start_shield"))
        had = str(ss.pop(unreal.Name("Warrior"), "none"))
        g.set_editor_property("start_shield", ss)
        def strip(ws):
            n = 0; out = []
            for w in ws:
                m = w.get_editor_property("off_hand_mesh")
                if m and "shield" in m.get_name().lower(): w.set_editor_property("off_hand_mesh", None); n += 1
                out.append(w)
            return out, n
        heroes = list(g.get_editor_property("heroes")); hn = 0
        for h in heroes:
            if str(h.name) != "Warrior": continue
            ws, k = strip(list(h.weapons)); h.weapons = ws; hn += k
        g.set_editor_property("heroes", heroes)
        lw, ln = strip(list(g.get_editor_property("weapons"))); g.set_editor_property("weapons", lw)
        return f"start shield {had}; shield meshes taken off {hn} of her weapons and {ln} of the level's"
    each(GAME_MAPS + ("martial_arts",), noshield, "noshield")

if "sky" in STEPS:
    MEL = unreal.MaterialEditingLibrary; path = "/Game/RandomDungeon/Sky/M_RD_FarLand"
    if eal.does_asset_exist(path): eal.delete_asset(path)
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_RD_FarLand", "/Game/RandomDungeon/Sky", unreal.Material, unreal.MaterialFactoryNew())
    vc = MEL.create_material_expression(m, unreal.MaterialExpressionVertexColor, -400, 0)
    rough = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 200); rough.set_editor_property("r", 1.0)
    MEL.connect_material_property(vc, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    m.set_editor_property("two_sided", True)
    MEL.recompile_material(m); eal.save_loaded_asset(m, only_if_is_dirty=False)
    def sky(g):
        g.set_editor_property("far_land_material", m)
        g.set_editor_property("sky_cover_range", unreal.Vector2D(0.05, 0.6))
        return f"far land {m.get_name()}, cover 0.05 to 0.6, clouds traced {g.get_editor_property('sky_cloud_trace_km')} km"
    each(["brokenspire"], sky, "sky")

if "stairs" in STEPS:
    CK = "/Game/Medieval_Castle/CastleKit/Walls_Stone/Materials/"
    # (the wall under the steps in Castle of Eternal Mist's pale brick, the pack's own wall under its stairs (its ExtendDown
    # pieces), as the hall's walls are: Castle Forge's wall stone read dark brown against them (884 k10h's picture))
    # (the blocks in the same pack's stair stone, at its stairs' scale (312 cm a repeat): Castle Forge's stair stone is laid out for
    # its spiral's pieces and drew the blocks' ends near black (884 k10i))
    blk = unreal.load_asset("/Game/CastleofEternalMist/Material/Instances/MI_Stairs"); wal = unreal.load_asset("/Game/CastleofEternalMist/Material/Instances/MI_BrickStoneWall_Disp")
    def stairs(g):
        g.set_editor_property("stair_block_material", blk); g.set_editor_property("stair_wall_material", wal)
        g.set_editor_property("stair_block_uv_cm", 312.0); g.set_editor_property("stair_wall_uv_cm", 400.0)
        return f"blocks {blk.get_name() if blk else 'MISSING'}, wall {wal.get_name() if wal else 'MISSING'}"
    each(["brokenspire"], stairs, "stairs")

if "dungeon" in STEPS:
    def dungeon(g):
        g.set_editor_property("boss_ports", True); g.set_editor_property("library_shelves", True)
        return f"boss teleporters on, library shelves on (shelf chance {g.get_editor_property('shelf_loot_chance')})"
    each(DUNGEONS, dungeon, "dungeon")

if "crowd" in STEPS:
    def crowd(g):
        cm = list(g.get_editor_property("crowd_meshes"))
        if not cm: return "no crowd"
        out = []; heads = 0
        for mesh in cm:
            cp = unreal.RDCrowdParts(); parts = []
            mn = mesh.get_name() if mesh else ""
            # (882's way: the pack's _Full_02 bodies' head, hair, beard and moustache from Separate/)
            if mesh and "NPC_Characters_Pack" in mesh.get_path_name() and "_Full_02" in mn:
                base = mesh.get_path_name().rsplit("/Full/", 1)[0] + "/Separate/" + mn.split("_Full_02")[0]
                for part in ("_Head", "_Hair", "_Beard", "_Mustache"):
                    if eal.does_asset_exist(base + part): parts.append(unreal.load_asset(base + part))
                heads += 1 if any(str(x.get_name()).endswith("_Head") for x in parts) else 0
            cp.set_editor_property("parts", parts); out.append(cp)
        g.set_editor_property("crowd_parts", out)
        return f"{len(cm)} bodies, {sum(len(c.get_editor_property('parts')) for c in out)} parts, {heads} heads given"
    each(GAME_MAPS, crowd, "crowd")

if "see" in STEPS:
    def see(g):
        g.set_editor_property("see_through", True)
        return f"see-through on (hold {g.get_editor_property('see_through_hold')} s)"
    each(["brokenspire"], see, "see")

def kind_of(it): return str(it.kind).split(".")[-1].split(":")[0]
def part(label, kinds, n):
    p = unreal.RDRecipePart(); p.label = label; p.any_of = kinds; p.count = n; return p

if "forge" in STEPS:
    import math
    def forge(g):
        items = list(g.get_editor_property("items")); bds = list(g.get_editor_property("breakdowns"))
        rec = [r for r in g.get_editor_property("recipes") if str(r.station) != "Forge"]
        made = []; nobd = []
        for it in items:
            if kind_of(it) not in ("WEAPON", "ARMOUR", "SHIELD"): continue
            tiers = list(it.get_editor_property("tiers"))
            if not tiers or min(tiers) != 1: continue
            wt = str(it.get_editor_property("weapon_type")).lower()
            bd = next((b for b in bds if wt in [str(x).lower() for x in b.get_editor_property("types")]), None)
            if not bd: nobd.append(str(it.name)); continue
            rc = unreal.RDRecipe(); rc.item = it.name; rc.station = "Forge"; rc.tier = 1
            # (what breaking it down gives at tier 1, and half again, rounded up)
            rc.parts = [part(str(gv).lower(), [gv], int(math.ceil(n * 1.5))) for gv, n in zip(bd.get_editor_property("gives"), bd.get_editor_property("per_tier"))]
            rec.append(rc); made.append(str(it.name))
        g.set_editor_property("recipes", rec)
        g.set_editor_property("forge", True); g.set_editor_property("forge_heroes", [unreal.Name("Warrior")])
        g.set_editor_property("forge_pieces", [unreal.Name("Forge")]); g.set_editor_property("forge_station_piece", unreal.Name("Forge"))
        has_piece = unreal.Name("Forge") in g.get_editor_property("pieces")
        if g.get_editor_property("town") is False and has_piece: g.modify(); g.build_start_section()
        return f"{len(made)} forge recipes, the Forge piece {'there' if has_piece else 'MISSING'}" + (f", no breakdown for {nobd}" if nobd else "")
    each(GAME_MAPS, forge, "forge")

if "oven" in STEPS:
    g0 = open_map("brokenspire")
    OVEN = [r for r in g0.get_editor_property("recipes") if str(r.station) == "Oven"]
    ING = ("Wheat", "Wild Carrot", "Pumpkin", "Sunflower Seeds", "Herbs")
    def oven(g):
        rec = [r for r in g.get_editor_property("recipes") if str(r.station) != "Oven"] + OVEN
        g.set_editor_property("recipes", rec)
        items = list(g.get_editor_property("items")); n = 0
        for it in items:
            if str(it.name) in ING: it.set_editor_property("weight", 12.0); n += 1
        g.set_editor_property("items", items)
        g.set_editor_property("dungeon_ovens", True)
        return f"{len(OVEN)} oven recipes, {n} of {len(ING)} ingredients found in containers"
    each(DUNGEONS, oven, "oven")

if "ankh" in STEPS:
    import os
    SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\list10\ankh"
    D10 = "/Game/RandomDungeon/List10"
    ML = unreal.MathLibrary
    o = unreal.FbxImportUI(); o.set_editor_property("import_mesh", True); o.set_editor_property("import_as_skeletal", False)
    o.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH); o.set_editor_property("import_materials", False); o.set_editor_property("import_textures", False)
    sm = o.get_editor_property("static_mesh_import_data"); sm.set_editor_property("combine_meshes", True); sm.set_editor_property("auto_generate_collision", False)
    t = unreal.AssetImportTask(); t.filename = os.path.join(SA, "SM_RD_Ankh.fbx"); t.destination_path = D10; t.automated = True; t.replace_existing = True; t.save = True; t.options = o
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    am = unreal.load_asset(D10 + "/SM_RD_Ankh"); assert am, "the ankh did not import"
    # (its metal: bronze, a faint pale glow)
    MEL = unreal.MaterialEditingLibrary; mp = D10 + "/M_RD_Ankh"
    if eal.does_asset_exist(mp): eal.delete_asset(mp)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_RD_Ankh", D10, unreal.Material, unreal.MaterialFactoryNew())
    def const3(x, y, c):
        n = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, x, y); n.set_editor_property("constant", unreal.LinearColor(*c, 1)); return n
    def const1(x, y, v):
        n = MEL.create_material_expression(mat, unreal.MaterialExpressionConstant, x, y); n.set_editor_property("r", v); return n
    MEL.connect_material_property(const3(-400, 0, (0.62, 0.44, 0.2)), "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(const1(-400, 150, 1.0), "", unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(const1(-400, 250, 0.32), "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(const3(-400, 350, (0.05, 0.07, 0.11)), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(mat); eal.save_loaded_asset(mat, only_if_is_dirty=False)
    am.set_material(0, mat); eal.save_loaded_asset(am, only_if_is_dirty=False)
    ab = am.get_bounding_box()
    # (the torch's frame (865's): its long axis and its grip a fifth of the way up; the ankh is made in that frame, its grip at its origin)
    TORCH = unreal.load_asset("/Game/Medieval_Castle/CastleKit/Props/Meshes/Props/TorchKit/SM_Torch_01a"); tb = TORCH.get_bounding_box()
    tsz = [tb.max.x - tb.min.x, tb.max.y - tb.min.y, tb.max.z - tb.min.z]; long_ = max(range(3), key=lambda i: tsz[i])
    assert long_ == 2, f"the torch's long axis is not Z ({tsz})"
    v_ = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(TORCH, 0, 0)[0]
    lo, hi = tb.min.z, tb.max.z
    def wz(a, c):
        s_ = [p for p in v_ if a <= p.z <= c]
        return max(max(p.x for p in s_) - min(p.x for p in s_), max(p.y for p in s_) - min(p.y for p in s_)) if s_ else 0.0
    head_up = wz(hi - 0.2 * (hi - lo), hi) >= wz(lo, lo + 0.2 * (hi - lo)); assert head_up, "the torch's head is down"
    grip = V((tb.min.x + tb.max.x) / 2, (tb.min.y + tb.max.y) / 2, lo + (hi - lo) * 0.22)
    ICON = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_magic4\ui_art\ankh.png"
    ti = unreal.AssetImportTask(); ti.set_editor_property("filename", ICON); ti.set_editor_property("destination_path", "/Game/RandomDungeon/UI")
    ti.set_editor_property("destination_name", "T_RDM4_ankh"); ti.set_editor_property("replace_existing", True); ti.set_editor_property("automated", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([ti])
    tex = unreal.load_asset("/Game/RandomDungeon/UI/T_RDM4_ankh"); assert tex, "the ankh's picture did not import"
    tex.set_editor_property("srgb", True); tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_EDITOR_ICON)
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI); tex.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    tex.set_editor_property("never_stream", True); tex.set_editor_property("address_x", unreal.TextureAddress.TA_CLAMP); tex.set_editor_property("address_y", unreal.TextureAddress.TA_CLAMP)
    eal.save_loaded_asset(tex, False)
    def ankh(g):
        items = [i for i in g.get_editor_property("items") if kind_of(i) != "LIGHT"]
        torch = next((i for i in items if kind_of(i) == "TORCH"), None)
        if not torch: return "no torch to take the grips from"
        it = unreal.RDItemDef(); it.name = "Revealing Ankh"; it.kind = unreal.RDItemKind.LIGHT; it.weight = 6.0; it.found_max = 1
        it.tiers = [2]; it.icon = unreal.Name("ankh"); it.looks = "a bronze ankh whose loop glows pale"; it.weapon_type = "light"
        fits = []
        for f in torch.get_editor_property("weapon_fits"):
            w = f.get_editor_property("weapon"); gt = w.get_editor_property("off_hand_grip")
            # (the torch's grip takes its mesh's points to her hand; the ankh's point p is the torch's p + its grip point)
            ga = ML.compose_transforms(unreal.Transform(grip, unreal.Rotator(0, 0, 0), V(1, 1, 1)), gt)
            wd = unreal.RDWeaponDef(); wd.name = "Revealing Ankh"; wd.off_hand_mesh = am; wd.off_hand_bone = w.get_editor_property("off_hand_bone"); wd.off_hand_grip = ga
            nf = unreal.RDWeaponFit(); nf.hero = f.get_editor_property("hero"); nf.weapon = wd; fits.append(nf)
        it.weapon_fits = fits; items.append(it)
        g.set_editor_property("items", items)
        ua = g.get_editor_property("ui_art")
        art = unreal.RDUIArt(); art.set_editor_property("texture", tex); art.set_editor_property("border", unreal.Vector4(0, 0, 0, 0)); art.set_editor_property("inner", unreal.Vector4(0, 0, 1, 1))
        ua[unreal.Name("ankh")] = art; g.set_editor_property("ui_art", ua)
        return f"Revealing Ankh: {len(fits)} heroes' grips, tier 2, its picture"
    each(GAME_MAPS, ankh, "ankh")
    REPORT.append(f"ankh mesh {[round(ab.max.z - ab.min.z, 1)]} cm tall, torch grip at {grip}")

if "block" in STEPS:
    import os
    SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\list10\warrior3_block\SK_JRPG_Warrior3_Clips.fbx"
    AN = "/Game/JRPG/Warrior3Anims"; DST = AN + "/AS_Warrior3_BlockLunge"
    skel = unreal.load_asset("/Game/JRPG/Character/SK_JRPG_Warrior3").get_editor_property("skeleton")
    o = unreal.FbxImportUI(); o.set_editor_property("import_mesh", False); o.set_editor_property("import_as_skeletal", True)
    o.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION); o.set_editor_property("skeleton", skel)
    o.set_editor_property("import_animations", True); o.set_editor_property("import_materials", False); o.set_editor_property("import_textures", False)
    tmp = AN + "/_import_block"
    t = unreal.AssetImportTask(); t.filename = SA; t.destination_path = tmp; t.automated = True; t.replace_existing = True; t.save = True; t.options = o
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    import editor_toolset.toolsets.blueprint as BT
    T = BT.BlueprintTools
    ABP_PATH = "/Game/JRPG/Warrior3Locomotion/ABP_Unarmed_Warrior3"
    def repoint(to):
        """every user of the stance (her AnimBP's evaluators of it, or of nothing; every map's BlockClip) onto this clip, saved"""
        ab = unreal.load_asset(ABP_PATH); gr = {x.get_name(): x for x in T.list_graphs(ab)}["AnimGraph"]
        for n in T.find_nodes(gr, ""):
            if n.get_class().get_name() != "AnimGraphNode_SequenceEvaluator": continue
            nd = n.get_editor_property("node"); sq = nd.get_editor_property("sequence")
            if sq is None or "BlockLunge" in sq.get_name(): nd.set_editor_property("sequence", to); n.set_editor_property("node", nd)
        unreal.BlueprintEditorLibrary.compile_blueprint(ab); eal.save_loaded_asset(ab, only_if_is_dirty=False)
        def one(g):
            bc = g.get_editor_property("block_clip")
            if unreal.Name("Warrior") in bc: bc[unreal.Name("Warrior")] = to; g.set_editor_property("block_clip", bc)
            return "repointed"
        each(GAME_MAPS, one, "block repoint")
    clip = None
    for pth in t.imported_object_paths:
        a = unreal.load_asset(pth)
        if isinstance(a, unreal.AnimSequence) and pth.split(".")[-1].endswith("A_BlockLunge"):
            # (made again: its users moved onto the new import and saved, the old one deleted, the new one renamed to its name and
            # its users moved onto that (consolidate_assets crashed the editor on the second run: an access violation))
            if eal.does_asset_exist(DST): repoint(a); eal.delete_asset(DST)
            eal.rename_asset(pth.split(".")[0], DST); clip = unreal.load_asset(DST)
            clip.set_editor_property("enable_root_motion", False); clip.set_editor_property("force_root_lock", True); eal.save_loaded_asset(clip, False)
            repoint(clip)
    for pth in eal.list_assets(tmp, recursive=True): eal.delete_asset(pth.split(".")[0])
    eal.delete_directory(tmp)
    assert clip, "BlockLunge was not imported"
    # (her AnimBP: a two-way blend toward the stance under 885's upper-body layer, its alpha BlockLegsAlpha; the layer's own clip the stance)
    abp = unreal.load_asset("/Game/JRPG/Warrior3Locomotion/ABP_Unarmed_Warrior3")
    ag = {x.get_name(): x for x in T.list_graphs(abp)}["AnimGraph"]
    nodes = T.find_nodes(ag, "")
    def pin(n, nm, out):
        i = T.get_node_infos([n])[0]
        for p_ in (i.output_pins if out else i.input_pins):
            if str(p_.name) == nm: return p_
        raise KeyError((n.get_name(), nm, [str(p_.name) for p_ in (i.output_pins if out else i.input_pins)]))
    lb = next(n for n in nodes if n.get_class().get_name() == "AnimGraphNode_LayeredBoneBlend")
    if "BlockLegsAlpha" not in [str(v) for v in T.list_variables(abp)]: T.add_variable(abp, "BlockLegsAlpha", "float")
    # (the graph made once: run again, only the clip is new, its users moved onto it above)
    if not any(n.get_class().get_name() == "AnimGraphNode_TwoWayBlend" for n in nodes):
        ev_type = next((x for x in [str(y) for y in T.find_node_types(ag, "BlockLunge")] if "Evaluate" in x), None)
        assert ev_type, "no Evaluate node type for the clip"
        # (the layer's pose: the stance)
        bp0 = pin(lb, "BlendPoses_0", False)
        for q in bp0.get_editor_property("connected_pins"): T.break_pins(bp0.pin_id, q)
        ev1 = T.create_node(ag, ev_type, unreal.IntPoint(-100, 800))
        T.connect_pins(pin(ev1, "Pose", True).pin_id, bp0.pin_id)
        base = pin(lb, "BasePose", False)
        src = list(base.get_editor_property("connected_pins"))
        for q in src: T.break_pins(base.pin_id, q)
        bt = "Animation|Blends|TwoWayBlend"
        tw = T.create_node(ag, bt, unreal.IntPoint(0, 200))
        ev2 = T.create_node(ag, ev_type, unreal.IntPoint(-300, 350))
        gv = next(x for x in [str(y) for y in T.find_node_types(ag, "BlockLegsAlpha")] if "Get" in x)
        va = T.create_node(ag, gv, unreal.IntPoint(-300, 450))
        twi = T.get_node_infos([tw])[0]
        REPORT.append(f"block blend pins {[str(p_.name) for p_ in twi.input_pins]}")
        for q in src: T.connect_pins(q, pin(tw, "A", False).pin_id)
        T.connect_pins(pin(ev2, "Pose", True).pin_id, pin(tw, "B", False).pin_id)
        T.connect_pins(pin(va, "BlockLegsAlpha", True).pin_id, pin(tw, "Alpha", False).pin_id)
        T.connect_pins(pin(tw, "Pose", True).pin_id, base.pin_id)
    # (the blend's A is her locomotion (the slot): a run stopped half way had cut the slot from the layer and left A empty, and
    # out of the block she stood in her reference pose (868 l10p: her resting hand 52 cm over her middle, 8 before))
    nodes = T.find_nodes(ag, "")
    tw_ = next((n for n in nodes if n.get_class().get_name() == "AnimGraphNode_TwoWayBlend"), None)
    if tw_ and len(pin(tw_, "A", False).get_editor_property("connected_pins")) == 0:
        sl_ = next(n for n in nodes if n.get_class().get_name() == "AnimGraphNode_Slot"); so_ = pin(sl_, "Pose", True)
        for q in so_.get_editor_property("connected_pins"): T.break_pins(so_.pin_id, q)
        T.connect_pins(so_.pin_id, pin(tw_, "A", False).pin_id); REPORT.append("block: the slot joined to the blend's A again")
    ok = unreal.BlueprintEditorLibrary.compile_blueprint(abp); eal.save_loaded_asset(abp, only_if_is_dirty=False)
    REPORT.append(f"block AnimBP compiled {ok}: nodes {sorted({n.get_class().get_name() for n in T.find_nodes(ag, '')})}")
    def block(g):
        bc = g.get_editor_property("block_clip")
        if unreal.Name("Warrior") not in bc: return "no Warrior block here"
        bc[unreal.Name("Warrior")] = clip; g.set_editor_property("block_clip", bc)
        bt_ = g.get_editor_property("block_clip_time"); bt_[unreal.Name("Warrior")] = 0.0; g.set_editor_property("block_clip_time", bt_)
        return "the Warrior's block clip BlockLunge"
    each(GAME_MAPS, block, "block")

SA_ROOT = r"E:\code\claude-ue5\claude_ue5\SourceArt"
if "lines" in STEPS:
    import os, json, re
    entries = []
    for f in ("brokenspire/role_lines_a.json", "brokenspire/role_lines_b.json", "brokenspire/role_lines_c.json", "heaven/role_lines.json"):
        for e in json.load(open(os.path.join(SA_ROOT, f), encoding="utf-8"))["lines"]:
            town = e.get("town", "")
            if town:
                entries.append((e["role"], town, True, e["lines"])); continue
            # (a line naming the castle or the Mistgate stands only in Brokenspire, by Mistward Castle)
            local = [l for l in e["lines"] if re.search(r"\b(castle|mistgate|mistward)\b", l, re.I)]
            entries.append((e["role"], "", False, [l for l in e["lines"] if l not in local]))
            if local: entries.append((e["role"], "Brokenspire", False, local))
    farm = json.load(open(os.path.join(SA_ROOT, "wilderness", "farm_lines10.json"), encoding="utf-8"))["lines"]
    def lines(g):
        rl = []
        for role, town, only, ls in entries:
            r = unreal.RDRoleLines(); r.set_editor_property("role", unreal.Name(role)); r.set_editor_property("town", town)
            r.set_editor_property("only", only); r.set_editor_property("lines", ls); rl.append(r)
        g.set_editor_property("role_lines", rl)
        wl = [l for l in g.get_editor_property("wild_farm_lines")]
        have = set(str(l) for l in wl)
        n = 0
        for who, ls in farm.items():
            for l in ls:
                k = f"{who}|{l}"
                if k not in have: wl.append(k); n += 1
        g.set_editor_property("wild_farm_lines", wl)
        return f"{len(rl)} role sets ({sum(len(e[3]) for e in entries)} lines), {n} farm lines added ({len(wl)} in all)"
    each(["brokenspire"], lines, "lines")

if "sleepsrc" in STEPS:
    import os
    OUT = os.path.join(SA_ROOT, "brokenspire", "work_clips", "src"); os.makedirs(OUT, exist_ok=True)
    for path, fn in (("/Game/NPC_Characters_Pack/Demoscene_UE5/Mesh/SKM_Manny", "SKM_Manny.fbx"),
                     ("/Game/NPC_Characters_Pack/Mesh/NPC_Character_01/Mesh_UE5/Full/SKM_NPC_Character_01_Full_01", "Body_Character01.fbx"),
                     ("/Game/NPC_Characters_Pack/Demoscene_UE5/Animations/MM_Idle", "MM_Idle.fbx"),
                     ("/Game/NPC_Characters_Pack/Demoscene_UE5/Animations/MM_Walk_Fwd", "MM_Walk_Fwd.fbx")):
        t = unreal.AssetExportTask(); t.object = unreal.load_asset(path); t.filename = os.path.join(OUT, fn); t.automated = True; t.prompt = False; t.replace_identical = True
        o = unreal.FbxExportOption(); o.set_editor_property("collision", False); t.options = o
        REPORT.append(f"sleepsrc {fn}: {unreal.Exporter.run_asset_export_task(t)}")

if "sleep" in STEPS:
    import os, json
    FBX = os.path.join(SA_ROOT, "brokenspire", "work_clips", "sleep", "SK_Manny_Town_Work_Clips.fbx")
    js = json.load(open(os.path.join(SA_ROOT, "brokenspire", "work_clips", "sleep", "town_work_clips.json"), encoding="utf-8"))
    DW = "/Game/RandomDungeon/Anims/Town/Work"; DST = DW + "/AS_Town_Sleep"
    skel = unreal.load_asset("/Game/NPC_Characters_Pack/Demoscene_UE5/Mesh/SKM_Manny_Skeleton")
    o = unreal.FbxImportUI(); o.set_editor_property("import_mesh", False); o.set_editor_property("import_as_skeletal", True)
    o.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION); o.set_editor_property("skeleton", skel)
    o.set_editor_property("import_animations", True); o.set_editor_property("import_materials", False); o.set_editor_property("import_textures", False)
    tmp = DW + "/_import_sleep"
    t = unreal.AssetImportTask(); t.filename = FBX; t.destination_path = tmp; t.automated = True; t.replace_existing = True; t.save = True; t.options = o
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    new = next((pth for pth in t.imported_object_paths if isinstance(unreal.load_asset(pth), unreal.AnimSequence)), None)
    assert new, "the Sleep clip was not imported"
    def defs_with(g, clip):
        """every townsfolk def whose mesh is on the clip's skeleton (the NPC pack's) given the clip as Sleep, the cities' own too (they
        have no work clips); one on another skeleton (the drunk's, the Dwarf smith's) has none"""
        # (each NPC pack has its own copy of the Manny skeleton (the kids', the knights', the beggars'...): the clip's is made
        # compatible with each, saved, as 907 does for its casters)
        tf = list(g.get_editor_property("townsfolk")); n = 0
        for d in tf:
            m = d.get_editor_property("mesh")
            ms = m.get_editor_property("skeleton") if m else None
            on = ms is not None and ms.get_name() == skel.get_name()
            if on and ms != skel and not any(x == skel for x in ms.get_editor_property("compatible_skeletons")):
                ms.add_compatible_skeleton(skel); eal.save_loaded_asset(ms, only_if_is_dirty=False)
            wc = d.get_editor_property("work_clips")
            if on: wc[unreal.Name("Sleep")] = clip; n += 1
            elif unreal.Name("Sleep") in wc: wc.pop(unreal.Name("Sleep"))
            d.set_editor_property("work_clips", wc)
        g.set_editor_property("townsfolk", tf)
        return n
    # (made again: its users onto the new import, the old one deleted, the new renamed, its users onto that (914 block's way))
    na = unreal.load_asset(new)
    if eal.does_asset_exist(DST): each(["brokenspire"], lambda g: f"{defs_with(g, na)} defs moved onto the new import", "sleep repoint"); eal.delete_asset(DST)
    eal.rename_asset(new.split(".")[0], DST); clip = unreal.load_asset(DST)
    L = float(js["clips"]["Sleep"].get("length_s", clip.get_play_length()))
    if L > 0 and abs(clip.get_play_length() - L) > 0.02: clip.set_editor_property("rate_scale", clip.get_play_length() / L)
    clip.set_editor_property("enable_root_motion", False); clip.set_editor_property("force_root_lock", True); eal.save_loaded_asset(clip, False)
    for pth in eal.list_assets(tmp, recursive=True):
        if eal.does_asset_exist(pth.split(".")[0]): eal.delete_asset(pth.split(".")[0])
    eal.delete_directory(tmp)
    each(["brokenspire"], lambda g: f"Sleep ({clip.get_play_length():.2f} s) for {defs_with(g, clip)} defs", "sleep")

if "people" in STEPS:
    def people(g):
        g.set_editor_property("town_beds", True); g.set_editor_property("more_people", True)
        # (measured (884 people10): a child in 45 % of the homes and a second grown-up in 20 % made 36 % and 31 % more people)
        g.set_editor_property("home_second_share", 0.2); g.set_editor_property("home_child_share", 0.33)
        return f"beds on, households: a second grown-up {g.get_editor_property('home_second_share')}, a child {g.get_editor_property('home_child_share')}"
    each(["brokenspire"], people, "people")

open_map("mistward_castle")
print("LIST10 " + " | ".join(REPORT))
import gc
gc.collect()
