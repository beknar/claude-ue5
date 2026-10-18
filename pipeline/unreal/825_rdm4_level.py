"""random_dungeonmagic_level4: random_dungeonmagic_level3 with four heroes to choose from (the menu level, 826), mana,
potions and food in the start section's containers, and an inventory. Run 824 and 819 first.
First run (the level does not exist yet): opens random_dungeonmagic_level3 and saves it as
/Game/RandomDungeon/Maps/random_dungeonmagic_level4 (Save As), then stops: RESTART THE EDITOR and run it again. With the
copy there, it reads each hero's weapons from the level they come from (the generators of random_dungeoncombat_level,
random_dungeonmagic_level, _level2 and _level3: the weapons as those levels have them, clips, grips, effects and all),
opens the copy and sets it up from SourceArt/random_dungeon_magic4/heroes.json and items.json:
- the generator's Heroes: the Warrior (sword and shield, 140 hit points, +30 % melee damage), the Mage (fire and dark
  fire, the dark fire being her cast clips with the Warlock's fire; 70 hit points, 100 mana), the Warlock (the sword in
  her right hand and fire from her left, 100 hit points, 60 mana), the Rogue (daggers and crossbow, 100 hit points, +30 %
  ranged damage, the roll as her uncanny dodge); a cast takes mana (ManaCost); DefaultHero: the one played when the level
  is opened without the menu
- Items (the user's table: rarity = the weight of the pick), bStartLoot: each container of the start section holds one
- RegenPerSecond 0: hit points come back only from potions and food; mana comes back slowly (each hero's ManaPerSecond)
- MonsterReferenceHealth / Blow: the monsters do not follow the hero's hit points and blows
- the sounds of the dark fire (the fire's) and of the inventory (Player.Loot / Drink / Eat / Inventory / NoMana: 827's
  sound sets, when they are there)
- the game mode BP_RDM4_GameMode (824: the hero of ?Hero= gets her pawn)
Args: none"""
import json, unreal
eal = unreal.EditorAssetLibrary
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
M = "/Game/RandomDungeon/Maps/"
SRC = M + "random_dungeonmagic_level3"; MAP = M + "random_dungeonmagic_level4"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_magic4"
V = unreal.Vector
def done():
    import gc
    for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
    gc.collect()
def open_map(path):
    if not ues.get_editor_world().get_path_name().startswith(path + "."): les.load_level(path)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(path + "."), w.get_path_name()
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
if not eal.does_asset_exist(MAP):
    open_map(SRC)
    ok = unreal.EditorLoadingAndSavingUtils.save_map(ues.get_editor_world(), MAP)
    print("RDM4 copied" if ok else "RDM4 copy FAILED", SRC, "->", MAP, "| restart the editor, then run 825 again")
else:
    H = json.load(open(SA + r"\heroes.json")); I = json.load(open(SA + r"\items.json"))
    # ---- the weapons as their own levels have them (as text: nothing of a level is kept once another is opened)
    need = {}
    for h in H["heroes"]:
        for wp in h["weapons"]:
            need.setdefault(wp["level"], set()).add(wp["from"])
            if "like" in wp: need.setdefault(wp["like"][0], set()).add(wp["like"][1])
    TEXT = {}; ROLL = {}
    for lv, names in need.items():
        g = open_map(M + lv)
        have = {str(d.name): d for d in g.get_editor_property("weapons")}
        for n in names:
            assert n in have, f"{lv} has no weapon {n}: {list(have)}"
            TEXT[(lv, n)] = have[n].export_text()
        if lv == "random_dungeonmagic_level3":
            ROLL = {"f": g.get_editor_property("roll_clip").get_path_name(), "b": g.get_editor_property("roll_back_clip").get_path_name(),
                    "dist": g.get_editor_property("roll_distance"), "cool": g.get_editor_property("roll_cooldown"), "dodge": g.get_editor_property("roll_dodge")}
        del g, have
    def weapon(lv, n):
        d = unreal.RDWeaponDef(); d.import_text(TEXT[(lv, n)]); return d
    gen = open_map(MAP); w = ues.get_editor_world()
    heroes = []
    for h in H["heroes"]:
        hd = unreal.RDHeroDef()
        hd.set_editor_property("name", h["name"]); hd.set_editor_property("title", h["title"])
        pawn = unreal.load_asset(h["pawn"]); assert pawn, h["pawn"] + ": run 824 / 810 / 817 / 822"
        hd.set_editor_property("pawn_class", pawn.generated_class())
        ws = []
        for wp in h["weapons"]:
            d = weapon(wp["level"], wp["from"])
            if "like" in wp:
                # (her own clips and hand, the other spell's look, flight and damage)
                o = weapon(*wp["like"])
                for k in ("charge_effect", "charge_effect_scale", "bolt_effect", "bolt_effect_scale", "bolt_core_effect", "bolt_core_effect_scale", "burst_effect",
                          "burst_effect_scale", "burst_flame_effect", "burst_flame_effect_scale", "burst_flame_seconds", "spell_light_color", "spell_light_intensity",
                          "damage", "bolt_speed", "bolt_turn_rate", "bolt_splash", "reach"):
                    d.set_editor_property(k, o.get_editor_property(k))
            d.set_editor_property("name", wp["name"]); d.set_editor_property("mana_cost", float(wp["mana"]))
            if "damage" in wp: d.set_editor_property("damage", float(wp["damage"]))
            ws.append(d)
        hd.set_editor_property("weapons", ws)
        for k, j in (("max_health", "health"), ("max_mana", "mana"), ("mana_per_second", "mana_per_second"), ("melee_bonus", "melee_bonus"), ("ranged_bonus", "ranged_bonus")):
            hd.set_editor_property(k, float(h[j]))
        hd.set_editor_property("rogue_controls", bool(h.get("rogue", False)))
        if h.get("rogue"):
            hd.set_editor_property("roll_clip", unreal.load_asset(ROLL["f"])); hd.set_editor_property("roll_back_clip", unreal.load_asset(ROLL["b"]))
        hd.set_editor_property("controls_keys", h["keys"]); hd.set_editor_property("controls_pad", h["pad"])
        hd.set_editor_property("abilities", h["abilities"]); hd.set_editor_property("armour", h["armour"]); hd.set_editor_property("starts_with", h["starts_with"])
        hd.set_editor_property("accent", unreal.LinearColor(*h["accent"], 1.0))
        heroes.append(hd)
    gen.set_editor_property("heroes", heroes)
    gen.set_editor_property("default_hero", H["default"])
    gen.set_editor_property("roll_distance", float(ROLL["dist"])); gen.set_editor_property("roll_cooldown", float(ROLL["cool"])); gen.set_editor_property("roll_dodge", ROLL["dodge"])
    KIND = {"healing": unreal.RDItemKind.HEALING, "mana": unreal.RDItemKind.MANA, "speed": unreal.RDItemKind.SPEED, "food": unreal.RDItemKind.FOOD}
    items = []
    for it in I["items"]:
        d = unreal.RDItemDef()
        d.set_editor_property("name", it["name"]); d.set_editor_property("kind", KIND[it["kind"]])
        d.set_editor_property("amount", float(it["amount"])); d.set_editor_property("seconds", float(it["seconds"])); d.set_editor_property("weight", float(it["rarity"]))
        items.append(d)
    gen.set_editor_property("items", items); gen.set_editor_property("start_loot", True)
    gen.set_editor_property("regen_per_second", 0.0)
    gen.set_editor_property("monster_reference_health", float(H["monster_reference"]["health"]))
    gen.set_editor_property("monster_reference_blow", float(H["monster_reference"]["blow"]))
    gen.set_editor_property("caster_controls", True); gen.set_editor_property("controls_hint", "")
    # sounds: the dark fire sounds as the fire does; the inventory's own (827) where they are
    snd = gen.get_editor_property("sounds"); added = []
    for occ in ("Charge", "Cast", "Hit"):
        src = unreal.Name(f"Player.{occ}.Fire")
        if src in snd: snd[unreal.Name(f"Player.{occ}.Dark Fire")] = snd[src]; added.append(f"Player.{occ}.Dark Fire")
    gen.set_editor_property("sounds", snd)
    # (the saved level shows the default hero: the same fields play sets from the chosen one)
    gen.apply_hero(H["default"])
    ws_ = w.get_world_settings(); ws_.set_editor_property("default_game_mode", unreal.load_asset("/Game/RandomDungeon/Blueprints/BP_RDM4_GameMode").generated_class())
    c = gen.get_start_room_center()
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.PlayerStart): a.set_actor_location(V(c.x, c.y, 100.0), False, False); a.set_actor_label("RDM4_PlayerStart")
    s0, s1 = unreal.IntPoint(0, 0), unreal.IntPoint(1, 0)
    back = gen.get_editor_property("heroes")
    print("RDM4 heroes: " + " | ".join(f"{h.name}: {h.pawn_class.get_name()}, {h.max_health:.0f} hp, {h.max_mana:.0f} mana +{h.mana_per_second}/s, melee +{h.melee_bonus * 100:.0f}%, ranged +{h.ranged_bonus * 100:.0f}%, "
                                     + ", ".join(f"{d.name} ({d.damage:.0f} dmg, {d.mana_cost:.0f} mana, spell={d.spell}, alongside={d.alongside}, {len(d.attacks)} clips)" for d in h.weapons)
                                     + (f", roll {h.roll_clip.get_name()}" if h.roll_clip else "") for h in back))
    print(f"RDM4 items {len(gen.get_editor_property('items'))}, start loot {gen.start_loot}, regen {gen.regen_per_second}, default {gen.default_hero}, sounds added {added},"
          f" monsters: start {gen.get_monster_health(s0):.0f} hp / {gen.get_monster_damage(s0):.1f} dmg, generated {gen.get_monster_health(s1):.0f} hp / {gen.get_monster_damage(s1):.1f} dmg,"
          f" game mode {ws_.get_editor_property('default_game_mode').get_name()}, tactical maps {gen.tactical_maps}")
    les.save_current_level(); print("saved", MAP)
done()
