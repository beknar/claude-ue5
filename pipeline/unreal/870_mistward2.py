"""mistward_castle and random_dungeonmagic_level5: the user's third list (docs/improvements2.txt, 2026-10-27; the user chose both
levels). Writes into each level's generator (the C++ is RD/RDMistward2.cpp, every rule a switch of its own):
- bTrapOutline: a trap the Rogue has seen is outlined in red: its plate tinted red (an overlay material), a red disc at its
  reach with a wide pulsing rim (/Engine/BasicShapes/Plane and a material made here, every run), a red light over it
- bInventoryTabs, bQuickSlots, bHelmetToggle: the inventory in tabs (stacks, the anvil's counts), ten quick slots, the helmet;
  bMouseUI (the inventory's pointer, Mistward's since the second list) on level 5 too: a click on a tab, a right click into a slot
- bShieldBlock: the Warrior blocks with her shield (RMB / LT held; her run switch on the gamepad moves to the left stick
  pressed); the pose held: AS_Warrior3_Box_03 at 1.6 s (measured: her left hand 24 cm before her chest, 14 cm over it)
- bKeepStartGear: the Warrior starts with no armour, the worst weapon she can wield (the weapons table's lowest damage
  rating of tier 1: the Dagger) and the worst shield (the shield table's lowest share, then by name: the Painted Viking
  Shield); both never
  break and never drop
- bWeaponPickups: the armories' tables hold weapons and shields of the tier, taken up with F
- bSpecialRooms: shrines (Crownfall's praying statue), healing / speed / mana fountains (Castle Collection's fountain),
  arenas, trap gauntlets, vaults (a key item in another room's chest), throne rooms (Castle Collection's throne, a usurper)
- bBossSlashes: the 20 slashes of the list (the Stylized Slashes V2 pack, copied into Content/StylizedSlashesV2), an item each;
  a boss gives the Warrior one of its tier
Level 5 gets Mistward's shields (its Warrior's worst shield) and their breakdowns at the anvil, and its traps (in trap gauntlets only: the room and hallway shares
0) and the Rogue's trap finding. Each level's start section is built again (its furniture is saved with the map).
Run on any level (it opens both, mistward_castle first, and ends on mistward_castle). Before packaging run 869 again: the
special rooms' pieces (the fountain, the statue, the throne) are drawn through the sections' instanced meshes and need its
usage flags. Args: none"""
import unreal, math
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools()
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MEL = unreal.MaterialEditingLibrary
V = unreal.Vector; L = unreal.load_asset
MW = "/Game/RandomDungeon/Mistward"
MAPS = ["/Game/RandomDungeon/Maps/mistward_castle", "/Game/RandomDungeon/Maps/random_dungeonmagic_level5"]
SL = "/Game/StylizedSlashesV2/Particles/NiagaraSystems/"
LD = "/Game/LootDropsV2/Particles/NiagaraSystems/LootDrop02/"
# ---------------------------------------------------------------- the slashes (docs/improvements2.txt, as the user wrote them)
E = unreal.RDSlashEffect
SLASHES = [  # name, tier, pack name, bonus, type, effect, amount, seconds, radius, count, text, colour
    ("Ember Slash", 1, "Fire", 6, "Fire", E.BURN, 0.5, 3, 0, 0, "burns: 50 % more over 3 s", (1, .35, .08)),
    ("Frost Slash", 1, "Ice", 5, "Frost", E.SLOW, 0.25, 2, 0, 0, "slows the monster 25 % for 2 s", (.45, .8, 1)),
    ("Venom Slash", 1, "Poison", 4, "Poison", E.POISON, 12, 4, 0, 0, "poison: 12 over 4 s", (.4, 1, .25)),
    ("Gale Slash", 1, "Wind", 5, "Physical", E.SWIFT, 0.10, 4, 0, 0, "her speed +10 % for 4 s after a hit", (.8, 1, .9)),
    ("Blood Slash", 2, "Blood", 9, "Blood", E.DRAIN, 0.30, 0, 0, 0, "drain: 30 % of the damage back to her as hit points", (.8, .05, .08)),
    ("Wave Slash", 2, "Water", 9, "Water", E.KNOCKBACK, 300, 0, 0, 0, "knockback: pushes the monster 3 m", (.2, .55, 1)),
    ("Verdant Slash", 2, "Nature", 8, "Nature", E.REGEN, 1.5, 5, 0, 0, "regeneration: 1.5 hit points a second for 5 s", (.35, .9, .3)),
    ("Petal Slash", 2, "Sakura", 8, "Physical", E.EVADE, 0.15, 3, 0, 0, "evasion: 15 % of blows on her miss for 3 s", (1, .6, .8)),
    ("Crystal Slash", 3, "Crystal", 14, "Crystal", E.SHIELD, 0, 6, 0, 0, "damage shield: absorbs her next blow taken (once every 6 s)", (.6, .9, 1)),
    ("Storm Slash", 3, "Lightning", 15, "Lightning", E.CHAIN, 0.5, 0, 500, 2, "chains to 2 more monsters within 5 m at half damage", (.6, .7, 1)),
    ("Ink Slash", 3, "Ink", 13, "Dark", E.BLIND, 0.4, 3, 0, 0, "blind: the monster's blows miss 40 % of the time for 3 s", (.15, .1, .2)),
    ("Tide Slash", 3, "Water2", 14, "Water", E.TIDE, 0.2, 2, 400, 0, "sweeps an arc: slows 20 % and pushes 4 m", (.15, .45, .9)),
    ("Inferno Slash", 4, "Fire2", 24, "Fire", E.INFERNO, 0.4, 4, 250, 0, "explodes within 2.5 m, burns 40 % more over 4 s", (1, .45, .05)),
    ("Shadow Slash", 4, "Shadow", 22, "Shadow", E.CURSE, 0.25, 5, 0, 0, "ignores armour; curse: the monster takes 25 % more damage for 5 s", (.45, .2, .7)),
    ("Neon Slash", 4, "Neon", 20, "Arcane", E.HASTE, 0.2, 5, 0, 0, "haste: her attack speed +20 % for 5 s", (1, .2, 1)),
    ("Pulse Slash", 4, "Cyber", 20, "Energy", E.DEFLECT, 0.25, 4, 0, 0, "deflection: 25 % of blows on her are turned back on the attacker for 4 s", (.2, 1, 1)),
    ("Magma Slash", 5, "Lava", 36, "Fire", E.MAGMA, 10, 4, 300, 0, "burning ground, 3 m around, 10 a second for 4 s", (1, .25, .02)),
    ("Void Slash", 5, "Cosmic", 34, "Void", E.VOID, 0.25, 0, 500, 0, "pulls monsters within 5 m to the target and slows them 25 %", (.35, .15, .9)),
    ("Overload Slash", 5, "Cyber2", 38, "Energy", E.STUN, 0, 1, 8, 0, "stun: the monster is held for 1 s (once every 8 s per monster)", (.3, .9, 1)),
    ("Prismatic Slash", 5, "Rainbow", 32, "All", E.PRISMATIC, 0, 0, 0, 0, "each hit adds a random effect: burn, slow, poison or drain", (1, 1, 1)),
]
def slash_defs():
    out = []
    for nm, tier, pack, bonus, typ, eff, amt, secs, rad, cnt, text, col in SLASHES:
        d = unreal.RDSlashDef()
        d.name = nm; d.tier = tier; d.bonus = float(bonus); d.type = typ; d.effect = eff
        d.amount = float(amt); d.seconds = float(secs); d.radius = float(rad); d.count = cnt; d.text = text
        d.color = unreal.LinearColor(*col, 1.0)
        d.fx = L(SL + "NS_Slash_" + pack); d.impact_fx = L(SL + "NS_SlashImpact_" + pack)
        assert d.fx and d.impact_fx, pack
        d.fx_scale = 1.0; d.impact_fx_scale = 1.0
        out.append(d)
    return out
# ---------------------------------------------------------------- the trap outline's materials
def outline_materials():
    """the seen trap's look, made again every run (the test measures it in pictures: the first version, a fresnel edge on the
    plate and a thin rim, read as a faint arc from 6 m in a torch-lit room)"""
    om, rm = f"{MW}/M_RD_TrapOutline", f"{MW}/M_RD_TrapRing"
    for p_ in (om, rm):
        if eal.does_asset_exist(p_): eal.delete_asset(p_)
    # (an overlay: the whole plate or rune tinted red, brightest at its edges)
    m = at.create_asset("M_RD_TrapOutline", MW, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    fr = MEL.create_material_expression(m, unreal.MaterialExpressionFresnel, -500, 0)
    fr.set_editor_property("exponent", 2.0); fr.set_editor_property("base_reflect_fraction", 0.35)
    col = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -500, -200); col.set_editor_property("constant", unreal.LinearColor(14.0, 0.35, 0.2, 1))
    MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    # opacity = 0.4 + 0.5 x fresnel
    op = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, 100); op.set_editor_property("const_b", 0.5)
    MEL.connect_material_expressions(fr, "", op, "A")
    ad = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -120, 100); ad.set_editor_property("const_b", 0.4)
    MEL.connect_material_expressions(op, "", ad, "A")
    MEL.connect_material_property(ad, "", unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m); eal.save_loaded_asset(m, only_if_is_dirty=False)
    # (a disc on the floor at the trap's reach: a wide pulsing rim (0.36-0.5 of its half width) over a red fill)
    m = at.create_asset("M_RD_TrapRing", MW, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    uv = MEL.create_material_expression(m, unreal.MaterialExpressionTextureCoordinate, -900, 0)
    c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant2Vector, -900, 120); c.set_editor_property("r", 0.5); c.set_editor_property("g", 0.5)
    dist = MEL.create_material_expression(m, unreal.MaterialExpressionDistance, -700, 40)
    MEL.connect_material_expressions(uv, "", dist, "A"); MEL.connect_material_expressions(c, "", dist, "B")
    # rim = saturate(1 - abs(d - 0.43) / 0.07)
    sub = MEL.create_material_expression(m, unreal.MaterialExpressionSubtract, -550, 40); sub.set_editor_property("const_b", 0.43)
    MEL.connect_material_expressions(dist, "", sub, "A")
    ab = MEL.create_material_expression(m, unreal.MaterialExpressionAbs, -420, 40); MEL.connect_material_expressions(sub, "", ab, "")
    dv = MEL.create_material_expression(m, unreal.MaterialExpressionDivide, -300, 40); dv.set_editor_property("const_b", 0.07)
    MEL.connect_material_expressions(ab, "", dv, "A")
    om1 = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -180, 40); MEL.connect_material_expressions(dv, "", om1, "")
    sat = MEL.create_material_expression(m, unreal.MaterialExpressionSaturate, -60, 40); MEL.connect_material_expressions(om1, "", sat, "")
    # fill = 0.3 x saturate((0.40 - d) / 0.02)
    fs = MEL.create_material_expression(m, unreal.MaterialExpressionSubtract, -550, -120); fs.set_editor_property("const_a", 0.40)
    MEL.connect_material_expressions(dist, "", fs, "B")
    fd = MEL.create_material_expression(m, unreal.MaterialExpressionDivide, -420, -120); fd.set_editor_property("const_b", 0.02)
    MEL.connect_material_expressions(fs, "", fd, "A")
    fsat = MEL.create_material_expression(m, unreal.MaterialExpressionSaturate, -300, -120); MEL.connect_material_expressions(fd, "", fsat, "")
    fm = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -180, -120); fm.set_editor_property("const_b", 0.3)
    MEL.connect_material_expressions(fsat, "", fm, "A")
    both = MEL.create_material_expression(m, unreal.MaterialExpressionMax, 0, -40)
    MEL.connect_material_expressions(sat, "", both, "A"); MEL.connect_material_expressions(fm, "", both, "B")
    # pulse 0.7 .. 1.0
    tm = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -600, 260)
    sn = MEL.create_material_expression(m, unreal.MaterialExpressionSine, -450, 260); sn.set_editor_property("period", 1.2); MEL.connect_material_expressions(tm, "", sn, "")
    pm = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -320, 260); pm.set_editor_property("const_b", 0.15); MEL.connect_material_expressions(sn, "", pm, "A")
    pa = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -200, 260); pa.set_editor_property("const_b", 0.85); MEL.connect_material_expressions(pm, "", pa, "A")
    op = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, 120, 120); MEL.connect_material_expressions(both, "", op, "A"); MEL.connect_material_expressions(pa, "", op, "B")
    MEL.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
    col = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, 80, -200); col.set_editor_property("constant", unreal.LinearColor(30.0, 0.6, 0.3, 1))
    MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); eal.save_loaded_asset(m, only_if_is_dirty=False)
    return L(om), L(rm)
# ---------------------------------------------------------------- pieces (864's normalisation: footprint centred, bottom at z 0, +X the front)
YAW = {"+x": 0.0, "-x": 180.0, "+y": -90.0, "-y": 90.0}
def piece(path, front="+x", scale=1.0, collision=True):
    m = L(path); assert m, path
    rot = unreal.Rotator(roll=0.0, pitch=0.0, yaw=YAW[front]); sc = V(scale, scale, scale)
    t0 = unreal.Transform(V(0, 0, 0), rot, sc)
    b = m.get_bounding_box()
    pts = [unreal.MathLibrary.transform_location(t0, V(x, y, z)) for x in (b.min.x, b.max.x) for y in (b.min.y, b.max.y) for z in (b.min.z, b.max.z)]
    mn = V(min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)); mx = V(max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))
    p = unreal.RDPiece(); p.mesh = m; p.adjust = unreal.Transform(V(-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z), rot, sc)
    p.size = V(mx.x - mn.x, mx.y - mn.y, mx.z - mn.z); p.collision = collision
    return p
PIECES = {"Fountain": ("/Game/Castle_Collection/Props/SM_Fountain/Meshes/FBX/SM_Fountain", "+x", 0.85),
          "ShrineStatue": ("/Game/Crownfall/Assets/PrayingWomanStatue/SM_S_FirekeeperPrayingStatue", "-y", 0.9),
          "ThroneRoyal": ("/Game/Castle_Collection/Props/SM_Castle_Throne/Meshes/FBX/SM_Castle_Throne_SM_Castle_Throne", "-y", 1.0)}
# ---------------------------------------------------------------- one level
CARRY = {}          # (Mistward's shields and traps, as text, for level 5)
def open_map(m):
    if not ues.get_editor_world().get_path_name().startswith(m + "."): les.load_level(m)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(m + "."), w.get_path_name()
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
for MAP in MAPS:
    gen = open_map(MAP)
    level = MAP.rsplit("/", 1)[1]
    items = list(gen.get_editor_property("items"))
    K = unreal.RDItemKind
    if level == "mistward_castle":
        CARRY["shields"] = [i.export_text() for i in items if i.kind == K.SHIELD]
        CARRY["traps"] = [t.export_text() for t in gen.get_editor_property("traps")]
        CARRY["trap_finders"] = [str(n) for n in gen.get_editor_property("trap_finders")]
        # (the shields' breakdowns at the anvil (865's "shield metal" / "shield wood"): level 5's anvil had none for them)
        CARRY["breakdowns"] = [b.export_text() for b in gen.get_editor_property("breakdowns") if any(str(x).startswith("shield") for x in b.types)]
    else:
        # (level 5: Mistward's shields and traps, copied as text: a struct of another level's actor hung the editor once)
        items = [i for i in items if i.kind != K.SHIELD]
        for t in CARRY.get("shields", []):
            d = unreal.RDItemDef(); d.import_text(t); items.append(d)
        traps = []
        for t in CARRY.get("traps", []):
            d = unreal.RDTrapDef(); d.import_text(t); traps.append(d)
        gen.set_editor_property("traps", traps)
        gen.set_editor_property("trap_finders", CARRY.get("trap_finders", ["Rogue"]))
        gen.set_editor_property("trap_room_share", 0.0); gen.set_editor_property("trap_hall_share", 0.0)
        bds = [b for b in gen.get_editor_property("breakdowns") if not any(str(x).startswith("shield") for x in b.types)]
        for t_ in CARRY.get("breakdowns", []):
            d = unreal.RDBreakdown(); d.import_text(t_); bds.append(d)
        gen.set_editor_property("breakdowns", bds)
    # (the slashes' items and the vault's key: found only where the rules put them)
    items = [i for i in items if i.kind not in (K.SLASH, K.KEY)]
    for nm, tier, *_ in SLASHES:
        d = unreal.RDItemDef(); d.name = nm; d.kind = K.SLASH; d.weight = 0.0; d.amount = 0.0; d.tiers = [tier]; items.append(d)
    key = unreal.RDItemDef(); key.name = "Vault Key"; key.kind = K.KEY; key.weight = 0.0; key.amount = 0.0
    items.append(key)
    gen.set_editor_property("items", items)
    # (the Warrior: the worst weapon she can wield of tier 1, the worst shield; no armour)
    shields = sorted([i for i in items if i.kind == K.SHIELD and any(str(f.hero) == "Warrior" for f in i.weapon_fits)], key=lambda i: (i.amount, str(i.name)))
    wcands = []
    for i in items:
        if i.kind != K.WEAPON or (len(i.tiers) and 1 not in list(i.tiers)): continue
        for f in i.weapon_fits:
            if str(f.hero) == "Warrior": wcands.append((f.weapon.damage_rating, f.weapon.damage, str(i.name), f.weapon))
    wcands.sort(key=lambda c: (c[0], c[1], c[2]))
    heroes = list(gen.get_editor_property("heroes"))
    worst_w = wcands[0]; worst_s = shields[0]
    for h in heroes:
        keys = [k for k in h.controls_keys if not k.startswith(("1 - 0|", "H|", "RMB (hold)|", "Q / E|"))]
        pad = [k for k in h.controls_pad if not k.startswith(("D-pad left / right|", "LT (hold)|", "L3|"))]
        keys.insert(min(len(keys), 4), "1 - 0|quick slots")
        pad.insert(min(len(pad), 4), "D-pad left / right|quick slots")
        if str(h.name) == "Warrior":
            w = worst_w[3]
            w.item = "None"; w.durability = 0.0; w.slash = "None"
            h.weapons = [w]
            h.starts_with = f"{worst_w[2]} and the {str(worst_s.name).lower()}: hers for good (they never break, never drop)"
            keys.insert(min(len(keys), 4), "RMB (hold)|block with the shield")
            pad = [("L3|switch walk / run" if k.startswith("LT|") else k) for k in pad]
            pad.insert(min(len(pad), 4), "LT (hold)|block with the shield")
        h.controls_keys = keys; h.controls_pad = pad
    gen.set_editor_property("heroes", heroes)
    ss = dict(gen.get_editor_property("start_shield")); ss[unreal.Name("Warrior")] = worst_s.name
    gen.set_editor_property("start_shield", ss)
    # (her shields' 869 usage and the slashes' and the rooms' effects; the spells' effects for the rooms' glows)
    spells = {}
    for s in gen.get_editor_property("spells"): spells.setdefault(s.kind.name.lower(), s)
    def sfx(kind, field):
        s = spells.get(kind); return s.get_editor_property(field) if s else None
    om, rm = outline_materials()
    pieces = dict(gen.get_editor_property("pieces"))
    for k in ("Fountain", "ShrineStatue", "ShrinePlinth", "ThroneRoyal"):
        if unreal.Name(k) in pieces: del pieces[unreal.Name(k)]
    for k, (p, front, sc) in PIECES.items(): pieces[unreal.Name(k)] = piece(p, front, sc)
    gen.set_editor_property("pieces", pieces)
    for k, v in (("trap_outline", True), ("trap_outline_material", om), ("trap_ring_mesh", L("/Engine/BasicShapes/Plane")), ("trap_ring_material", rm),
                 ("inventory_tabs", True), ("quick_slots", True), ("helmet_toggle", True),
                 # (the inventory's pointer: a click on a tab, a right click into a quick slot; on level 5 too (the user's "or the mouse"))
                 ("mouse_ui", True),
                 ("shield_block", True), ("block_heroes", ["Warrior"]), ("block_share", 0.3), ("block_slow", 0.5), ("block_wear", 5.0),
                 ("block_clip", {unreal.Name("Warrior"): L("/Game/JRPG/Warrior3Anims/AS_Warrior3_Box_03")}), ("block_clip_time", {unreal.Name("Warrior"): 1.6}),
                 ("keep_start_gear", True), ("weapon_pickups", True),
                 ("special_rooms", True), ("special_room_share", 0.2), ("shrine_fx", sfx("rune", "area_fx")), ("heal_fountain_fx", L(LD + "NS_LootDrop02_lvl6_red")), ("speed_fountain_fx", L(LD + "NS_LootDrop02_lvl2_green")), ("mana_fountain_fx", L(LD + "NS_LootDrop02_lvl3_blue")),
                 ("bless_fx", sfx("nova", "impact_fx") or sfx("ward", "cast_fx")), ("bless_seconds", 90.0), ("fountain_speed", 0.3), ("fountain_speed_seconds", 45.0),
                 ("fountain_heal", 0.6), ("arena_waves", 3), ("vault_key_item", "Vault Key"),
                 ("boss_slashes", True), ("slash_heroes", ["Warrior"])):
        gen.set_editor_property(k, v)
    gen.set_editor_property("slashes", slash_defs())
    gen.modify(); gen.build_start_section()
    les.save_current_level()
    print(f"MISTWARD2 {level}: items {len(items)} (shields {sum(1 for i in items if i.kind == K.SHIELD)}, slashes {sum(1 for i in items if i.kind == K.SLASH)}) | traps {len(gen.get_editor_property('traps'))}"
          f" | Warrior: {worst_w[2]} (rating {worst_w[0]}, {worst_w[1]:.0f} damage), {worst_s.name} ({worst_s.amount:.2f}) | slashes {len(gen.get_editor_property('slashes'))}"
          f" | pieces {[k for k in PIECES]} | fx {[x.get_name() if x else None for x in (gen.get_editor_property('shrine_fx'), gen.get_editor_property('heal_fountain_fx'), gen.get_editor_property('speed_fountain_fx'), gen.get_editor_property('mana_fountain_fx'), gen.get_editor_property('bless_fx'))]}")
open_map(MAPS[0])
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
