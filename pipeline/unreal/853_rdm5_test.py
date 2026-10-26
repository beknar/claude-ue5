"""random_dungeonmagic_level5 test: the Summoner, the armour she finds and wears, up to six items a container
(play-in-editor; 828 with -lv 5 starts it). Steps (plan, comma separated):
  select   (the menu level random_dungeonmagic_level5_select) four heroes, Warrior, Mage, Warlock, Rogue (the Summoner off
           the menu since 2026-10-26), the Warrior's figure Warrior3's mesh; Left from the first shows the Rogue and only
           her figure; Enter opens random_dungeonmagic_level5?Hero=Rogue, where her pawn is BP_RDM3_RogueCharacter with
           her hit points and mana
  loot     (the dungeon) the great hall's containers hold the tier-1 sets of loot_table.json's start_room_armour
           between them; any other armour in the start section (tier 1) or in a generated tier-2 section is of that
           tier; every container of the start section holds 1 to 6 items, and over 6000 more containers each count from
           1 to 6 comes about a sixth of the time; F by a great hall container opens it and gives everything on its list
           (the FOUND list too), the others opened give theirs, she carries exactly what they held (a material 1 to 3 at
           a time, a set of armour once), opened again they give nothing
  wear     (the dungeon) with the keys (I, S / W to the set, Enter) each set goes on: one set's meshes on her at a
           time, following her body (leader pose), her armour the set's share; Enter again takes it off; the
           Mage given a set cannot wear it (she wears no armour)
  heroarmour (the dungeon) each of the four heroes given all five sets: the weights her card allows go on (856: the
           Warrior light, medium and heavy, the Warlock light and medium, the Rogue light, the Mage none), with the fit
           made for her (SK_<her mesh>_<set>) on her body as leader; the others are refused and the message says why (the
           weight, or that she wears no armour); in her heaviest set she runs and the armour stays on her bones (as follow);
           a picture of each in it, from in front
  follow   (the dungeon) in plate armour she runs and casts: skinned on the CPU as drawn, the armour's vertices
           keep their distance to her body's nearest vertices (median, 95th percentile against the same armour
           left in its reference pose on her, which falls behind her limbs)
  damage   (the dungeon) a monster's blows on her without armour and in a light, a medium and the heaviest set:
           what reached her is the blow less the set's share, her hit points fell by that, and the set's durability by
           1 a blow
  ui       (the dungeon) a great hall container's FOUND plaque with its first item's picture; the inventory with
           every item scrolls: at the top the armour's pictures are not drawn; walked down to the end every armour set,
           material and repair item has its own picture drawn; HighResShots of the top and the bottom
  armourtable (the dungeon) the 27 sets as the game has them against armour.json (the user's table): the share of a
           blow (damage rating x 5 %), the speed lost ((10 - speed rating) x 3 %), durability, tiers, rarity 20, the
           weight by type; on the Summoner her top speed and her measured running speed without armour, in a set that
           does not slow her and in the heaviest; blows that reach her take 1 each off the worn set, at 0 it takes off
           half its share (and the next blow shows it)
  repair   (the dungeon) the Warrior with a worn set and a found weapon worn down, two patch kits and leather strips:
           with the keys (I, to the patch kit, Enter) the repair list shows both; Enter on each gives back 75 % of its
           full durability (up to full) and uses a kit; leather strips on a whole set are refused and kept; Backspace
           goes back to the inventory; a worn-out set takes off half its share, mended its whole share
  craft    (the dungeon) an anvil in the great hall and in every generated set of rooms (and in each forge); F by the
           hall's anvil ("use the anvil") opens the crafting panel and pauses the game; without materials nothing can
           be made and Enter says what is missing; given what leather strips take (the wood from three kinds) Enter
           makes one and uses exactly that up; F shuts it; a picture of the panel
  maps     (the dungeon) the minimap and the big map write each room's tier (1 in the start section, 2 in a tier-2
           section she walks into) and draw the anvils she has seen; the big map's key names the anvil; pictures
  fire     (the dungeon) the audio device's output recorded 2.5 m from a torch (music off, monsters quiet) with the
           fires' volumes as they are and as they were (sounds.json's before the change), and far from every fire: the
           fire's own level (the recording less the floor) fell by about 8 dB
  tiers    (the dungeon) the five tiers (855: MaxTier 5): a section's tier is its ring plus one (8, 16, 24, 32 sections
           round the start); at the start only tier 1 is open (2026-10-24): the start section's hallways are barred and
           nothing is generated as she walks to its border; the start section cleared, "TIER 2 IS OPEN" and its gratings
           go. One set of tier 2 cleared as she would clear it: walked
           into room by room (explored only once she is in each), every chest and trunk opened, every monster killed: it
           counts as cleared ("SET CLEARED"). Tier 3 is not generated past it; its hallways into tier 3 are sealed: a
           capsule is stopped at the grating and she, walking at it for 2.5 s, stays on her side of the border; the seal
           says what opens it. The set dropped and generated again has no monsters (her kills stay killed) and is still
           cleared. The other seven sets cleared (the debug clear): "TIER 3 IS OPEN", the gratings go, walking on she gets
           tier 3 generated. Tiers 3 and 4 cleared: tier 5 opens; a tier 5 section's hallways out of the dungeon are
           walled (they lead to tier 6, which is never allowed)
  tierloot the containers of each tier (2500 each, any section of it): a weapon, an armour set, a potion or a food only
           in its tiers (the tables'), every weapon and every set of a tier found, the materials and repair items in
           every tier; the weapons' and the armour's share of what is found as their weights say (within 4.5 sd)
  weapons  each hero given all 29 weapons: the ones her card allows join her weapons (Warrior, Warlock: all; Rogue: short
           blades and ranged), the others stay in her pack as weapons she cannot wield (the Mage and the Summoner: all,
           and using one says she cannot); each one drawn: its mesh in her hand with its handle's grip point within 7 cm
           of her palm, its damage (8 + 3 x rating, her bonus), its attack's length (the table's speed: 1.6 - (speed - 1)
           x 1.05 / 9 s); a two-handed sword: the Warrior (Warrior3) swings it with her own slash, its grip point where her left
           palm comes along the hilt (her right palm within 7 cm of its place below it); the Warlock as her one-handed sword
           (her sword's clips); nothing in the other hand at the blow; a blow that lands
           takes 1 off its durability, and at 0 it breaks: gone from her weapons, her first one drawn, "broke"; pictures
           from in front of her (the face camera, her alone) at the blow
  warrior3 (2026-10-26) as the Warrior, Warrior3: her pawn and mesh; F at a great hall container; the anvil: crafting
           and a two-handed sword broken down; plate armour on her own fit; her sword and shield kill a monster; her
           slash lands; a blow taken plays her flinch; M opens the big map
  (the user's list of 2026-10-24)
  chance   one container in three holds anything (6000 drawn, within 4.5 sd), then 1 to 6 items a sixth each; the great
           hall's armour is in its containers whatever the draw; a container of the start section that holds nothing,
           opened, says "Empty: nothing inside", gives nothing and is counted (ContainersEmpty)
  corpses  three monsters of a tier-2 set killed: after the corpse time and more they lie where they fell, frozen (no
           ticking); the set dropped and generated again lays each where it lay, dead, the kills still counted
  monsters each tier's section (1 to 5) spawns only the gallery monsters of that tier (monster_tiers.json): their hit points
           about the tier's average (rising tier by tier), their walking speed and their blows' pace the tier's multiple of
           their kind's; abilities only from tier 3
  abilities a tier 3+ monster of each ability (poison, weaken, slow) strikes her: she is poisoned (and loses hit points
           to it), weakened, slowed; on the Mage Dispel Hex ends them all, and none takes hold right after
  spells   the Warrior learns no spell (her tome is carried), the Warlock only offense and curses, the Mage all 30 (28 new:
           her fire bolt and dark fire are the table's); each released at a monster of a tier-3 set (or by her) does
           what its line says, measured: the monsters' hit points (and slow, curse, burn), her own (a ward's blocks, Iron
           Skin's and the rune's share, the mirror turning a blow back, the sanctum, the pact, the veil's misses, a drain
           giving back), allies raised and summoned, corpses burst; its effects' particles near it; a picture each; a
           cooldown refuses the next cast, a spell dearer than her mana is refused and says so
  rings    the Mage's magic potency rings add their share to her mana (one of a kind: the next replaces it; off, back), an
           hp ring refused; the Warrior's hp ring adds to her hit points and what she has; the Rogue's dexterity ring to
           her crossbow's damage
  breakdown at the anvil the Warrior's found two-handed sword is listed and breaks down (cursor, Enter) into the table's
           materials x its tier and is gone; the one in her hands is refused; the Mage's carried bow breaks down too
  menu     Escape opens the menu and pauses; the environment volume set to half with the keys (saved in the user
           settings); the fire at 2.5 m recorded at 1 and at 0.5 (about -6 dB); the buttons say what they would do (a dry
           run); Resume and Escape go back
Writes SourceArt/random_dungeon_magic5/test_<tag>.json and logs "RDM5TEST done | <tag> | ok / FAILED | ...". Args: plan tag"""
import unreal, sys, json, math, os, time
__keep__ = True
TAG = sys.argv[2] if len(sys.argv) > 2 else "t"
V = unreal.Vector; GS = unreal.GameplayStatics
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
OUT = os.path.join(SA, "random_dungeon_magic5")
HJ = json.load(open(os.path.join(OUT, "summoner_hero.json"), encoding="utf-8"))
AJ = json.load(open(os.path.join(SA, "summoner3", "armour.json"), encoding="utf-8"))
LT = json.load(open(os.path.join(SA, "random_dungeon_magic5", "loot_table.json"), encoding="utf-8"))
START_ARMOUR = list(LT["start_room_armour"]["items"])
SET_TIERS = {s["title"]: set(s["tiers"]) for s in AJ["sets"]}
SETS = [s["title"] for s in AJ["sets"]]
LEVEL = "random_dungeonmagic_level5"
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
G = {"w": UES.get_game_world()}
assert G["w"] is not None, "PIE is not running"
PLAN = [s.strip() for s in (sys.argv[1] if len(sys.argv) > 1 else "loot,wear,follow,damage,ui").split(",") if s.strip()]
R = {"tag": TAG, "plan": PLAN, "level": G["w"].get_path_name().split(".")[-1], "steps": []}
def refresh():
    w = UES.get_game_world(); G["w"] = w
    if w is None: return False
    gens = GS.get_all_actors_of_class(w, unreal.RDDungeonGenerator); G["gen"] = gens[0] if gens else None
    sels = GS.get_all_actors_of_class(w, unreal.RDHeroSelect); G["sel"] = sels[0] if sels else None
    G["pc"] = GS.get_player_controller(w, 0); G["pawn"] = G["pc"].get_controlled_pawn() if G["pc"] else None
    return True
refresh()
def now(): return GS.get_time_seconds(G["w"])
def cb(): return G["gen"].get_player_combat()
def key(n): k = unreal.Key(); k.set_editor_property("key_name", n); return k
def wait(sec):
    t0 = now()
    while now() - t0 < sec: yield
def rwait(sec):
    t0 = time.time()
    while time.time() - t0 < sec: yield
def press(name, hold=0.12, sim=None):
    sim = sim or (lambda k, d: cb().simulate_key(k, d))
    sim(key(name), True); yield from rwait(hold); sim(key(name), False); yield from rwait(0.1)
def step_result(name, ok, **kw):
    R["steps"].append({"step": name, "ok": bool(ok), **kw})
    unreal.log(f"RDM5TEST step {name}: {'ok' if ok else 'FAILED'} {json.dumps(kw, ensure_ascii=False)[:1800]}")
def alive(m):
    try: return m is not None and unreal.SystemLibrary.is_valid(m) and not m.is_dead()
    except Exception: return False
def start_monsters(): return [m for m in G["gen"].get_monsters() if alive(m) and m.get_editor_property("section").get_editor_property("coord") == unreal.IntPoint(0, 0)]
def clear(a, b, ignore):
    h = unreal.SystemLibrary.line_trace_single(G["w"], a, b, unreal.TraceTypeQuery.ECC_VISIBILITY, False, ignore, unreal.DrawDebugTrace.NONE, True)
    return h is None or not h.to_tuple()[0]
def stand_off(m, gap):
    p = G["pawn"]; sec = m.get_editor_property("section"); ml = m.get_actor_location(); room = sec.room_at(ml)
    ign = [p] + list(G["gen"].get_monsters())
    for k in range(32):
        a = k * math.pi / 16; q = V(ml.x + math.cos(a) * gap, ml.y + math.sin(a) * gap, ml.z)
        if room >= 0 and sec.room_at(q) != room: continue
        path = sec.find_path_world(q, ml)
        if not len(path) or math.hypot(path[0].x - q.x, path[0].y - q.y) > 135.0: continue
        if not clear(V(q.x, q.y, 150), V(ml.x, ml.y, ml.z + 20), ign): continue
        p.set_actor_location(V(q.x, q.y, 100.0), False, True)
        yaw = math.degrees(math.atan2(ml.y - q.y, ml.x - q.x)); p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), True)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=yaw))
        return True
    return False
def quiet(on):
    g = G["gen"]
    if on:
        if "aggro" not in G: G["aggro"] = (g.get_editor_property("aggro_distance"), g.get_editor_property("lose_distance"))
        g.set_editor_property("aggro_distance", 0.0); g.set_editor_property("lose_distance", 1.0)
    elif "aggro" in G: a_, l_ = G.pop("aggro"); g.set_editor_property("aggro_distance", a_); g.set_editor_property("lose_distance", l_)
def restart():
    """the dungeon back to its start (fixed seed), her as the Summoner with nothing found"""
    G["gen"].restart_play(0); yield from wait(0.8); refresh()
    c = cb(); c.set_scripted_only(False); return c
def hud_art():
    h = G["pc"].get_hud() if G.get("pc") else None
    return sorted(str(n) for n in h.get_art_drawn()) if h else []
def shot(name):
    unreal.SystemLibrary.execute_console_command(G["w"], f"HighResShot 1920x1080 filename=rdm5_{TAG}_{name}")
    R.setdefault("shots", []).append(f"rdm5_{TAG}_{name}.png")
def lines(c): return [str(l) for l in c.get_inventory_lines()]
def cursor_to(c, i):
    while c.get_inventory_cursor() < i: yield from press("S")
    while c.get_inventory_cursor() > i: yield from press("W")

# ------------------------------------------------------------------------------------------------ the menu
def step_select():
    s = G["sel"]; assert s, "open random_dungeonmagic_level5_select for the select step"
    sim = lambda k, d: G["sel"].simulate_key(k, d)
    yield from wait(0.6)
    names = [str(h.name) for h in s.heroes]
    first = str(s.get_hero_name())
    # (the Warrior's figure is Warrior3 (862): her mesh on the turntable)
    def fig_mesh(i):
        try:
            sk_ = s.figures[i].get_component_by_class(unreal.SkeletalMeshComponent); return sk_.get_skinned_asset().get_name()
        except Exception: return None
    warrior_mesh = fig_mesh(0)
    shot("menu_warrior"); yield from rwait(1.5)
    # (Left from the first wraps round to the last: the Rogue, since the Summoner is off the menu)
    yield from press("Left", sim=sim); yield from wait(0.2)
    shown = [s.is_figure_shown(i) for i in range(len(names))]
    pick = str(s.get_hero_name()); target = str(s.target_level)
    shot("menu_rogue"); yield from rwait(1.5)
    sim(key("Enter"), True)
    opened = ""; G["traveling"] = True; t0 = time.time(); arrived = False
    while time.time() - t0 < 60:
        yield
        try:
            if unreal.SystemLibrary.is_valid(s) and s.opened: opened = s.opened
        except Exception: pass
        w = UES.get_game_world()
        if w is not None and w.get_path_name().endswith(LEVEL) and refresh() and G["gen"] is not None and G["pawn"] is not None and G["gen"].get_player_combat():
            arrived = True; break
    G["traveling"] = False
    if arrived: yield from wait(0.5)
    c = cb() if arrived else None
    hero = str(G["gen"].current_hero) if arrived else None
    pawn = G["pawn"].get_class().get_name() if arrived else None
    RJ = next(h for h in json.load(open(os.path.join(SA, "random_dungeon_magic4", "heroes.json"), encoding="utf-8"))["heroes"] if h["name"] == "Rogue")
    want_pawn = os.path.basename(RJ["pawn"]) + "_C"
    stats = [c.get_max_health(), c.get_max_mana()] if c else None
    ok = (names == ["Warrior", "Mage", "Warlock", "Rogue"] and warrior_mesh == "SK_JRPG_Warrior3" and first == "Warrior" and pick == "Rogue" and shown == [False] * 3 + [True]
          and target.endswith(LEVEL) and opened.endswith(LEVEL + "?Hero=Rogue") and arrived and hero == "Rogue" and pawn == want_pawn
          and stats == [float(RJ["health"]), float(RJ["mana"])])
    step_result("select", ok, heroes=names, warrior_mesh=warrior_mesh, first=first, picked=pick, seen=shown, target=target, opened=opened, dungeon_hero=hero, pawn=pawn,
                want_pawn=want_pawn, health_mana=stats)

# ------------------------------------------------------------------------------------------------ the loot
def step_loot():
    g = G["gen"]; c = yield from restart()
    S0 = unreal.IntPoint(0, 0)
    s0 = g.get_section(S0); n = s0.get_num_containers(); hall = list(g.get_start_room_containers())
    lists = {i: [str(x) for x in g.loot_list_of(S0, i)] for i in range(n)}
    in_hall = [x for i in hall for x in lists[i] if x in SETS]
    # (armour anywhere else in the start section: tier-1 sets only)
    elsewhere = [(i, x) for i in range(n) if i not in hall for x in lists[i] if x in SETS and 1 not in SET_TIERS[x]]
    lens_start = sorted({len(v) for v in lists.values()})
    # many more containers: the counts 1..6 about a sixth each, never armour
    N = 6000; cnt = {}; arm_more = 0
    for i in range(N):
        l_ = [str(x) for x in g.loot_list_of(S0, 100000 + i)]
        cnt[len(l_)] = cnt.get(len(l_), 0) + 1; arm_more += sum(1 for x in l_ if x in SETS and 1 not in SET_TIERS[x])
    # (2026-10-24: a container holds anything one time in three: the counts 1..6 are a sixth each of those that do)
    held = sum(v for k, v in cnt.items() if k > 0)
    p6 = 1.0 / 6.0; sd = math.sqrt(p6 * (1 - p6) / max(held, 1))
    worst = max(abs(cnt.get(k, 0) / max(held, 1) - p6) / sd for k in range(1, 7))
    # F by a great hall container
    p = G["pawn"]; fpress = None
    for i in hall:
        cl = s0.get_container_location(i)
        for k in range(16):
            a = k * math.pi / 8; q = V(cl.x + math.cos(a) * 130, cl.y + math.sin(a) * 130, 100)
            if s0.room_at(q) < 0: continue
            d = g.describe_nearest(q, 260.0) or ""
            if not d.startswith("open") or "door" in d: continue
            p.set_actor_location(q, False, True); yield from wait(0.3)
            if s0.get_container_open_alpha(i) > 0.0: break
            f0 = g.items_found; yield from press("F"); yield from wait(0.5)
            # (F opens the one it names: which one it was is the one now open)
            opened = [j for j in hall if s0.get_container_open_alpha(j) > 0.0]
            if opened:
                j = opened[0]
                fpress = {"container": j, "found": g.items_found - f0, "list": lists[j], "found_list": [str(x) for x in g.last_found_list],
                          "counts": [g.loot_count_of(S0, j, k) for k in range(len(lists[j]))]}
            break
        if fpress: break
    # the rest of the hall, and every other container of the start section
    # (a wardrobe's two doors are one container, the lower index's: opening one opens both, and the other is skipped)
    bad = []; opened_lists = [list(zip(fpress["list"], fpress["counts"]))] if fpress else []
    for i in range(n):
        if s0.is_target_open(False, i): continue
        f0 = g.items_found; s0.toggle_container(i)
        if i in hall or i % 10 == 0: yield
        got = g.items_found - f0; fl = [str(x) for x in g.last_found_list]
        opened_lists.append(list(zip(fl, [g.loot_count_of(S0, i, k) for k in range(len(fl))])) if got else [])
        # (an empty one finds nothing: the found list is the last container's still)
        if got != len(lists[i]) or (got and fl != lists[i]): bad.append({"container": i, "found": got, "found_list": fl if got else [], "list": lists[i]})
    want = {}
    for v in opened_lists:
        for x, k in v: want[x] = want.get(x, 0) + k
    for x in want:
        if x in SETS: want[x] = 1                     # (a set found again mends hers: it is carried once)
    # (a tome teaches her its spell when she finds it: it is not carried)
    for x in [x for x in want if x.startswith("Tome of ") and c.knows_spell(x[8:])]: del want[x]
    ls = lines(c)
    have = {l.split("|")[1]: int(l.split("|")[2]) for l in ls if l.split("|")[0] in ("item", "repair", "component", "tome")}
    have.update({l.split("|")[1]: 1 for l in ls if l.startswith("armour|")})
    have.update({l.split("|")[1]: int(l.split("|")[3]) for l in ls if l.startswith("ring|")})
    # (855's weapons: the Summoner cannot wield them, so she carries them as items: "carried|<name>|<count>")
    have.update({l.split("|")[1]: int(l.split("|")[2]) for l in ls if l.startswith("carried|")})
    # opened again: nothing more
    yield from wait(1.0); i0 = hall[0]; f0 = g.items_found
    s0.toggle_container(i0); yield from wait(1.0); s0.toggle_container(i0); yield from wait(0.5)
    again = g.items_found - f0
    # a section generated in play: no armour
    g.generate_section_now(unreal.IntPoint(1, 0)); t0 = time.time()
    while time.time() - t0 < 30:
        s1 = g.get_section(unreal.IntPoint(1, 0))
        if s1 and not s1.is_building(): break
        yield
    s1 = g.get_section(unreal.IntPoint(1, 0)); n1 = s1.get_num_containers() if s1 else 0
    gen_armour = sum(1 for i in range(n1) for x in g.loot_list_of(unreal.IntPoint(1, 0), i) if str(x) in SETS and 2 not in SET_TIERS[str(x)])
    counts_ok = fpress is not None and all(1 <= k <= 3 for k in fpress["counts"])
    ok = (len(hall) > 0 and set(START_ARMOUR) <= set(in_hall) and not elsewhere and counts_ok and lens_start[-1] <= 6
          and min(cnt) >= 0 and max(cnt) <= 6 and len([k for k in cnt if k > 0]) == 6 and worst < 4.5 and arm_more == 0
          and fpress is not None and fpress["found"] == len(fpress["list"]) and fpress["found_list"] == fpress["list"]
          and not bad and have == want and again == 0 and n1 > 0 and gen_armour == 0)
    step_result("loot", ok, containers=n, great_hall=hall, hall_lists={str(i): lists[i] for i in hall}, armour_elsewhere=elsewhere,
                start_counts=lens_start, more=N, counts={str(k): cnt[k] for k in sorted(cnt)}, worst_sd=round(worst, 2), armour_in_more=arm_more,
                by_f=fpress, wrong=bad[:5], wrong_count=len(bad), items_kinds=len(want), carried_matches=have == want, opened_again_gave=again,
                generated_containers=n1, generated_armour=gen_armour)

# ------------------------------------------------------------------------------------------------ wearing
def step_wear():
    g = G["gen"]; c = yield from restart(); quiet(True)
    for t in SETS: c.add_item(t, 1)
    body = G["pawn"].get_component_by_class(unreal.SkeletalMeshComponent)
    amount = {str(it.name): it.amount for it in g.get_editor_property("items") if it.kind == unreal.RDItemKind.ARMOUR}
    want_mesh = {s["title"]: "SK_S3_" + s["key"] for s in AJ["sets"]}
    out = []
    yield from press("I")
    for t in SETS:
        ls = lines(c); i = next(k for k, l in enumerate(ls) if l.startswith("armour|" + t + "|"))
        yield from cursor_to(c, i); ch0 = c.armour_changes
        yield from press("Enter")
        ms = list(c.get_armour_meshes())
        e = {"set": t, "cursor": c.get_inventory_cursor(), "worn": str(c.get_worn_armour()), "armour": round(c.get_armour(), 3), "want": amount.get(t),
             "meshes": [m.skeletal_mesh_asset.get_name() if m.skeletal_mesh_asset else None for m in ms],
             "follows_her": all(m.leader_pose_component == body and m.get_attach_parent() == body for m in ms), "message": str(c.message),
             "line": next(l for l in lines(c) if l.startswith("armour|" + t + "|"))}
        e["ok"] = (e["cursor"] == i and e["worn"] == t and abs(e["armour"] - (amount.get(t) or -1)) < 1e-4 and e["meshes"] == [want_mesh[t]]
                   and e["follows_her"] and e["line"].split("|")[2] == "1" and c.armour_changes == ch0 + 1)
        out.append(e)
    # Enter again on the worn set: off
    t = SETS[-1]; yield from press("Enter")
    off = {"worn": str(c.get_worn_armour()), "armour": c.get_armour(), "meshes": len(c.get_armour_meshes()), "message": str(c.message)}
    yield from press("I")
    # the Mage cannot wear it
    ok_sw = g.switch_hero("Mage"); yield from wait(0.6); refresh(); m = cb(); m.add_item(SETS[0], 1)
    mage = {"switched": ok_sw, "wore": m.wear_armour(SETS[0]), "worn": str(m.get_worn_armour()), "meshes": len(m.get_armour_meshes()), "message": str(m.message)}
    g.switch_hero("Summoner"); yield from wait(0.6); refresh(); quiet(False)
    ok = (all(e["ok"] for e in out) and off["worn"] == "None" and off["armour"] == 0.0 and off["meshes"] == 0 and "take off" in off["message"]
          and mage["switched"] and not mage["wore"] and mage["worn"] == "None" and mage["meshes"] == 0 and "wears no armour" in mage["message"])
    step_result("wear", ok, sets=out, taken_off=off, mage=mage)

HERO_MESH = {"Warrior": "Warrior3", "Mage": "Caster", "Warlock": "DarkCaster", "Rogue": "Rogue"}
def step_heroarmour():
    """each hero tries on all five sets: the weights she wears go on with her own fit, the others are refused with why;
    her heaviest set stays on her bones as she runs"""
    g = G["gen"]; HJ4 = {h["name"]: h for h in json.load(open(os.path.join(SA, "random_dungeon_magic4", "heroes.json"), encoding="utf-8"))["heroes"]}
    weight = {s["title"]: s["weight"] for s in AJ["sets"]}; skey = {s["title"]: s["key"] for s in AJ["sets"]}
    order = {"light": 0, "medium": 1, "heavy": 2}; res = {}
    for h in ("Warrior", "Mage", "Warlock", "Rogue"):
        c = yield from restart(); quiet(True)
        ok_sw = g.switch_hero(h); yield from wait(0.6); refresh(); c = cb(); quiet(True)
        body = G["pawn"].get_component_by_class(unreal.SkeletalMeshComponent)
        for t in SETS: c.add_item(t, 1)
        wears = HJ4[h]["wears"]; tries = []
        for t in SETS:
            if str(c.get_worn_armour()) != "None": c.wear_armour(str(c.get_worn_armour()))      # (off first: a wrong one must not stay on)
            wore = bool(c.wear_armour(t)); ms = list(c.get_armour_meshes())
            e = {"set": t, "weight": weight[t], "wore": wore, "worn": str(c.get_worn_armour()), "message": str(c.message),
                 "meshes": [m.skeletal_mesh_asset.get_name() if m.skeletal_mesh_asset else None for m in ms],
                 "follows_her": all(m.leader_pose_component == body and m.get_attach_parent() == body for m in ms)}
            allowed = weight[t] in wears
            e["ok"] = (wore and e["worn"] == t and e["meshes"] == ["SK_%s_%s" % (HERO_MESH[h], skey[t])] and e["follows_her"]) if allowed else \
                      (not wore and e["worn"] == "None" and not e["meshes"]
                       and (("wears no armour" in e["message"]) if not wears else ("wears only" in e["message"] and weight[t] in e["message"])))
            tries.append(e)
        # her heaviest set, running: on her bones within a centimetre
        heavy = max((t for t in SETS if weight[t] in wears), key=lambda t: order[weight[t]], default=None)
        follow = None
        if heavy:
            if str(c.get_worn_armour()) != heavy: c.wear_armour(heavy)
            yield from wait(0.3)
            sim = lambda k, d: c.simulate_key(k, d); sim(key("LeftShift"), True); sim(key("W"), True)
            rs = []
            for k in range(4):
                yield from wait(0.25); r = list(c.measure_armour_follow(600)); rs.append(r)
            sim(key("W"), False); sim(key("LeftShift"), False); yield from wait(0.4)
            follow = {"set": heavy, "bone_max": round(max(r[5] for r in rs), 3) if all(rs) else None, "skin_median": round(max(r[1] for r in rs), 2) if all(rs) else None,
                      "bone_n": min(int(r[3]) for r in rs) if all(rs) else 0}
            # a picture of her in it, from in front
            p = G["pawn"]; l = p.get_actor_location(); yaw = p.get_actor_rotation().yaw
            G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=yaw + 180.0)); yield from wait(0.5)
            shot("armour_" + h); yield from rwait(1.5)
        res[h] = {"switched": bool(ok_sw), "wears": wears, "tries": tries, "follow": follow,
                  "ok": bool(ok_sw) and all(e["ok"] for e in tries) and (follow is None or (follow["bone_n"] > 50 and follow["bone_max"] < 1.0 and follow["skin_median"] < 0.5))
                        and (heavy is not None) == bool(wears)}
    g.switch_hero("Summoner"); yield from wait(0.6); refresh(); quiet(False)
    step_result("heroarmour", all(v["ok"] for v in res.values()), heroes=res)

def step_follow():
    g = G["gen"]; c = yield from restart(); quiet(True)
    c.add_item(SETS[0], 1); c.wear_armour(SETS[0])
    samples = []
    def measure(what):
        r = list(c.measure_armour_follow(600))
        samples.append({"when": what, "n": int(r[0]) if r else 0, "skin_median": round(r[1], 2) if r else None, "skin_p95": round(r[2], 2) if r else None,
                        "bone_n": int(r[3]) if r else 0, "bone_p95": round(r[4], 3) if r else None, "bone_max": round(r[5], 3) if r else None,
                        "bone_p95_left_in_rest_pose": round(r[6], 2) if r else None})
    yield from wait(0.3); measure("standing")
    sim = lambda k, d: c.simulate_key(k, d)
    sim(key("LeftShift"), True); sim(key("W"), True)
    for k in range(6):
        yield from wait(0.25); measure(f"running {k}")
    sim(key("W"), False); sim(key("LeftShift"), False)
    yield from wait(0.3)
    sim(key("LeftMouseButton"), True); yield from wait(0.15); sim(key("LeftMouseButton"), False)
    for k in range(4):
        yield from wait(0.15); measure(f"casting {k}")
    shot("follow"); yield from rwait(1.5)
    quiet(False)
    # (on her bones within a centimetre, everywhere: a broken bone map or a mesh left in its pose shows by metres; measured
    # 0.09 cm standing and up to 0.48 cm running at 3.4 m/s, growing with her speed; her skin's median within half a
    # centimetre: the armour stays on her)
    moving = [s for s in samples if s["when"] != "standing" and s["n"]]
    ok = (len(moving) == 10 and all(s["bone_n"] > 50 and s["bone_max"] < 1.0 and s["skin_median"] < 0.5 for s in samples)
          and max(s["bone_p95_left_in_rest_pose"] for s in moving) > 10.0)
    step_result("follow", ok, samples=samples)

def step_damage():
    g = G["gen"]; res = []
    for t in [None, "Orc Warrior\u2019s Armour", "Demonic Armour", "Epic Plate (Female)"]:
        c = yield from restart()
        if t: c.add_item(t, 1); c.wear_armour(t)
        ms = start_monsters(); p = G["pawn"]
        ms.sort(key=lambda m: (m.get_actor_location() - p.get_actor_location()).length())
        for m in ms:
            if stand_off(m, 150): break
        else:
            res.append({"set": t, "error": "no place by a monster"}); continue
        c.set_health(c.get_max_health()); h0, n0 = c.get_health(), c.hits_taken; t0 = now(); w0 = c.get_armour_wear(t) if t else 0.0
        while now() - t0 < 10.0 and c.hits_taken == n0: yield
        yield from wait(0.05)
        e = {"set": t, "armour": round(c.get_armour(), 3), "hits": c.hits_taken - n0, "blow": round(c.last_blow_before, 3), "reached_her": round(c.last_blow_taken, 3),
             "hp_fell": round(h0 - c.get_health(), 3), "monster": m.get_name(), "wear_fell": (w0 - c.get_armour_wear(t)) if t else 0.0}
        # (a second blow may land before the reading: her hit points then fell by two of them)
        e["ok"] = (e["hits"] in (1, 2) and e["blow"] > 0 and abs(e["reached_her"] - e["blow"] * (1 - e["armour"])) < 0.01 and abs(e["hp_fell"] - e["reached_her"] * e["hits"]) < 0.01
                   and (t is None) == (e["armour"] == 0.0) and (t is None or abs(e["wear_fell"] - e["hits"]) < 1e-3))
        res.append(e)
    ok = len(res) == 4 and all(e.get("ok") for e in res)
    step_result("damage", ok, blows=res)

def step_ui():
    g = G["gen"]; c = yield from restart(); quiet(True)
    S0 = unreal.IntPoint(0, 0); s0 = g.get_section(S0); hall = list(g.get_start_room_containers())
    icons = {str(i.name): str(i.icon) for i in g.get_editor_property("items")}
    ua = [str(k) for k in g.get_editor_property("ui_art").keys()]
    arm_icons = [icons.get(t) for t in SETS]
    # FOUND: the hall's longest list
    i = max(hall, key=lambda j: len(g.loot_list_of(S0, j)))
    first = str(g.loot_list_of(S0, i)[0]); n_in = len(g.loot_list_of(S0, i))
    s0.toggle_container(i); yield from wait(0.6)
    fd = hud_art(); shot("found"); yield from rwait(1.5)
    found_ok = "banner" in fd and icons.get(first) in fd
    # the inventory with everything: it scrolls (once the FOUND plaque is gone: its picture would count)
    t0 = now()
    while now() - t0 < 12.0 and "banner" in hud_art(): yield
    gone = "banner" not in hud_art()
    for it in g.get_editor_property("items"): c.add_item(it.name, 1)
    yield from press("I"); yield from rwait(0.4)
    top = hud_art(); shot("inventory_top"); yield from rwait(1.5)
    # (walked down the whole list: each row's picture is drawn while it is in view)
    ls = lines(c); seen = set(top)
    for k in range(len(ls)):
        c.move_inventory_cursor(1) if k else None; yield; yield
        seen |= set(hud_art())
    bottom = hud_art(); shot("inventory_bottom"); yield from rwait(1.5)
    yield from press("I"); quiet(False)
    kinds = {str(it.name): it.kind for it in g.get_editor_property("items")}
    new_icons = sorted({icons[n_] for n_, k_ in kinds.items() if k_ in (unreal.RDItemKind.COMPONENT, unreal.RDItemKind.REPAIR)})
    want_seen = set(arm_icons) | set(new_icons)
    ok = (all(a in ua for a in arm_icons + new_icons) and found_ok and gone and not (set(arm_icons) & set(top)) and want_seen <= seen
          and "panel_wide" in bottom and len(set(arm_icons)) == len(SETS) and len(new_icons) == 20)
    step_result("ui", ok, armour_icons=arm_icons, new_icons=new_icons, not_imported=[a for a in arm_icons + new_icons if a not in ua], found_container=i,
                found_items=n_in, found_first=first, found_drawn=fd, plaque_gone=gone, lines=len(ls), top_drawn=top, not_seen=sorted(want_seen - seen))

# ------------------------------------------------------------------------------------------------ the weapons table, the tiers
W5 = json.load(open(os.path.join(OUT, "weapons_table.json"), encoding="utf-8"))
W5F = json.load(open(os.path.join(OUT, "weapon_frames.json"), encoding="utf-8"))["weapons"]
wkey = lambda name: "".join(ch for ch in name.title() if ch.isalnum())
def cycle(speed): return 1.6 - (speed - 1) * 1.05 / 9.0
I2 = unreal.IntPoint
def out_tuple(r):
    """(a UFUNCTION's return value, its out parameter) as Python gives them: a bool function that returns false gives None"""
    if r is None: return (False, None)
    return r if isinstance(r, tuple) else (True, r)
def progress(S):
    ok, p = out_tuple(G["gen"].get_section_progress(S))
    if not ok: return None
    return {"tier": p.tier, "rooms": p.rooms, "explored": p.rooms_explored, "chests": len(p.chests), "looted": p.chests_looted, "monsters": p.monsters,
            "killed": len(p.killed), "cleared": p.cleared}
def built(S, sec=40.0):
    t0 = time.time()
    while time.time() - t0 < sec:
        s = G["gen"].get_section(S)
        if s and not s.is_building(): return s
        yield
    return None
def make_and_clear(S):
    """a section generated now and cleared at once (the debug clear: its rooms explored, its chests looted, its monsters gone)"""
    g = G["gen"]
    if not g.is_section_generated(S): g.generate_section_now(S)
    yield from built(S)                     # (one generated as she walked by may still be being built)
    ok = g.debug_clear_section(S); yield
    return ok
def seals(s):
    pts, kinds = s.get_seal_points()          # (the points returned, the kinds as the out parameter)
    return list(zip(list(pts), list(kinds)))
def seal_out(s, b):
    """the way out of section s through the border point b (the axis it is on)"""
    mn = s.get_section_min(); size = G["gen"].tile_size * G["gen"].section_tiles
    cx, cy = mn.x + size / 2, mn.y + size / 2; dx, dy = b.x - cx, b.y - cy
    return V(1 if dx > 0 else -1, 0, 0) if abs(dx) > abs(dy) else V(0, 1 if dy > 0 else -1, 0)

def step_tiers():
    g = G["gen"]; c = yield from restart(); quiet(True); p = G["pawn"]
    res = {"max_tier": g.max_tier, "open_at_start": g.get_open_tiers(),
           "tiers_of": [g.tier_of(I2(*xy)) for xy in ((0, 0), (1, 0), (-1, 1), (2, -1), (3, 3), (4, 0), (5, 0))],
           "sizes": [g.tier_size(t) for t in range(1, 6)],
           "allowed_at_start": [g.is_section_allowed(I2(*xy)) for xy in ((1, 0), (1, 1), (2, 0), (4, 0), (5, 0))]}
    # (2026-10-24: tier 2 waits for the start section, as the tiers after it wait for theirs: its hallways barred, nothing
    # generated as she walks to its border; the start section cleared, tier 2 opens and its gratings go)
    s0 = g.get_section(I2(0, 0))
    res["start_seals"] = {"grating": sum(1 for _, k in seals(s0) if k == 1), "wall": sum(1 for _, k in seals(s0) if k == 2)}
    mn = s0.get_section_min(); size = g.tile_size * g.section_tiles
    p.set_actor_location(V(mn.x + size - 900, mn.y + size * 0.5 + 150, 100.0), False, True); yield from wait(3.0)
    res["tier2_generated_while_shut"] = any(g.is_section_generated(I2(*xy)) for xy in ((1, 0), (1, 1), (1, -1)))
    p.set_actor_location(V(0, 0, 100.0), False, True); yield from wait(0.3)
    g.debug_clear_section(I2(0, 0)); yield from wait(0.3)
    res["start_cleared"] = {"notice": str(g.tier_notice), "open": g.get_open_tiers(), "tier2_allowed": g.is_section_allowed(I2(1, 0)),
                            "gratings_left": sum(1 for _, k in seals(g.get_section(I2(0, 0))) if k == 1)}
    # one set of tier 2 cleared as she would: every room walked into, every chest and trunk opened, every monster killed
    S = I2(1, 0); g.generate_section_now(S); s = yield from built(S)
    before = progress(S)
    rooms = [i for i in range(s.get_num_rooms()) if s.get_room_kind(i) != "Hallway junction"]
    c.set_health(c.get_max_health())
    for i in rooms:
        rc = s.get_room_center(i); p.set_actor_location(V(rc.x, rc.y, 100.0), False, True); yield from wait(0.06)
    after_rooms = progress(S)
    for i in range(s.get_num_containers()):
        if s.get_container_kind(i) in ("chest", "trunk") and not s.is_container_looted(i): s.toggle_container(i)
    yield from wait(0.1); after_chests = progress(S)
    kills0 = g.monsters_killed
    for m in list(s.spawned_monsters):
        if alive(m): m.apply_damage(1.0e6, p)
    yield from wait(0.3); after = progress(S)
    res.update({"set_before": before, "after_rooms": after_rooms, "after_chests": after_chests, "after_kills": after, "monsters_killed": g.monsters_killed - kills0,
                "notice": str(g.tier_notice), "tier2_cleared": g.get_tier_cleared(2)})
    # tier 3 stays shut: nothing generated past her set, its hallways sealed; the seal stops a body and stops her walking
    near = [(b, k) for b, k in seals(s)]
    res["seals_of_set"] = {"grating": sum(1 for _, k in near if k == 1), "wall": sum(1 for _, k in near if k == 2),
                           "into": sorted({str(g.tier_of(g.world_to_section(b + seal_out(s, b) * 200.0))) for b, _ in near})}
    res["tier3_generated"] = g.is_section_generated(I2(2, 0))
    blocked = walked_out = None
    if near:
        b, _ = next(((b, k) for b, k in near if seal_out(s, b).x > 0), near[0]); out = seal_out(s, b)
        a0 = V(b.x - out.x * 150, b.y - out.y * 150, 110.0); a1 = V(b.x + out.x * 150, b.y + out.y * 150, 110.0)
        h = unreal.SystemLibrary.capsule_trace_single(G["w"], a0, a1, 34.0, 80.0, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [p], unreal.DrawDebugTrace.NONE, True)
        hit = h.to_tuple() if h else None
        blocked = {"hit": bool(hit and hit[0]), "at_cm_from_border": round((hit[4].x - b.x) * out.x + (hit[4].y - b.y) * out.y, 1) if hit and hit[0] else None}
        p.set_actor_location(V(b.x - out.x * 260, b.y - out.y * 260, 100.0), False, True)
        yaw = math.degrees(math.atan2(out.y, out.x)); p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), True); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=yaw))
        yield from wait(0.2)
        sim = lambda k, d: c.simulate_key(k, d)
        sim(key("W"), True); yield from wait(2.5); sim(key("W"), False)
        q = p.get_actor_location(); walked_out = round((q.x - b.x) * out.x + (q.y - b.y) * out.y, 1)
        shot("tier_seal"); yield from rwait(1.5)
        res["seal_prompt"] = str(g.describe_seal_near(q, 450.0))
    res.update({"seal_blocks_a_body": blocked, "walked_past_the_border_cm": walked_out})
    # the set generated again (dropped and made anew): her kills stay killed, it stays cleared
    p.set_actor_location(V(0, 0, 100.0), False, True); yield from wait(0.3)
    g.reload_section(S); s = yield from built(S)
    # (her kills lie there as corpses: none of them alive)
    res["regenerated"] = {"monsters": len([m for m in s.spawned_monsters if alive(m)]) if s else None, "corpses": len([m for m in s.spawned_monsters if unreal.SystemLibrary.is_valid(m) and m.is_corpse()]) if s else None,
                          "progress": progress(S)}
    # the other seven sets of tier 2: tier 3 opens, the seals toward it go; walking on, tier 3 is generated
    for xy in ((1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)):
        yield from make_and_clear(I2(*xy))
    res["after_tier2"] = {"cleared": g.get_tier_cleared(2), "open": g.get_open_tiers(), "notice": str(g.tier_notice), "tier3_allowed": g.is_section_allowed(I2(2, 0))}
    p.set_actor_location(V(s.get_section_min().x + 12000, s.get_section_min().y + 12600, 100.0), False, True); yield from wait(0.5)
    s = G["gen"].get_section(S) or (yield from built(S))
    res["seals_of_set_after"] = sum(1 for _, k in seals(s) if k == 1) if s else None
    t0 = time.time(); p.set_actor_location(V(s.get_section_min().x + 24500, s.get_section_min().y + 12600, 100.0), False, True)
    while time.time() - t0 < 40 and not g.is_section_generated(I2(2, 0)): yield
    res["tier3_generated_when_near"] = g.is_section_generated(I2(2, 0))
    # tiers 3 and 4 cleared (the debug clear): tier 5 opens, and nothing past it is ever made
    for t in (3, 4):
        r = t - 1; failed = []
        for x in range(-r, r + 1):
            for y in range(-r, r + 1):
                if max(abs(x), abs(y)) != r: continue
                ok_ = yield from make_and_clear(I2(x, y))
                if not ok_: failed.append({"set": [x, y], "generated": g.is_section_generated(I2(x, y)), "progress": progress(I2(x, y))})
        res[f"after_tier{t}"] = {"cleared": g.get_tier_cleared(t), "open": g.get_open_tiers(), "notice": str(g.tier_notice), "not_cleared": failed}
    g.generate_section_now(I2(4, 0)); s4 = yield from built(I2(4, 0))
    sl = seals(s4) if s4 else []
    res["tier5_section"] = {"walls": sum(1 for _, k in sl if k == 2), "gratings": sum(1 for _, k in sl if k == 1),
                            "walls_lead_to_tier": sorted({g.tier_of(g.world_to_section(b + seal_out(s4, b) * 200.0)) for b, k in sl if k == 2}),
                            "tier6_allowed": g.is_section_allowed(I2(5, 0)), "seal_kind_east": g.get_seal_kind(I2(4, 0), I2(5, 0))}
    p.set_actor_location(V(0, 0, 100.0), False, True); quiet(False)
    a = res["after_kills"]; ar = res["after_rooms"]
    sc = res["start_cleared"]
    ok = (res["max_tier"] == 5 and res["open_at_start"] == 1 and res["tiers_of"] == [1, 2, 2, 3, 4, 5, 6] and res["sizes"] == [1, 8, 16, 24, 32]
          and res["allowed_at_start"] == [False, False, False, False, False] and res["start_seals"]["grating"] > 0 and not res["tier2_generated_while_shut"]
          and sc["notice"] == "TIER 2 IS OPEN" and sc["open"] == 2 and sc["tier2_allowed"] and sc["gratings_left"] == 0
          and res["set_before"] and not res["set_before"]["cleared"] and ar["explored"] == ar["rooms"] and not ar["cleared"]
          and a["cleared"] and a["looted"] == a["chests"] and a["killed"] == a["monsters"] and res["monsters_killed"] == a["monsters"] and "SET CLEARED" in res["notice"]
          and res["seals_of_set"]["grating"] > 0 and res["seals_of_set"]["into"] == ["3"] and not res["tier3_generated"]
          and blocked and blocked["hit"] and walked_out is not None and walked_out < 0 and "Sealed" in res.get("seal_prompt", "")
          and res["regenerated"]["monsters"] == 0 and res["regenerated"]["progress"]["cleared"]
          and res["after_tier2"]["cleared"] == 8 and res["after_tier2"]["open"] == 3 and res["after_tier2"]["notice"] == "TIER 3 IS OPEN" and res["after_tier2"]["tier3_allowed"]
          and res["seals_of_set_after"] == 0 and res["tier3_generated_when_near"]
          and res["after_tier3"]["cleared"] == 16 and res["after_tier3"]["open"] == 4 and res["after_tier4"]["cleared"] == 24 and res["after_tier4"]["open"] == 5
          and res["tier5_section"]["walls"] > 0 and res["tier5_section"]["walls_lead_to_tier"] == [6] and not res["tier5_section"]["tier6_allowed"]
          and res["tier5_section"]["seal_kind_east"] == 2)
    step_result("tiers", ok, **res)

def step_tierloot():
    """what each tier's containers hold: a weapon only in the tiers of its rooms; potions and food everywhere; the
    weapons' share as their weights say"""
    g = G["gen"]; c = yield from restart()
    wt = {w["name"]: set(w["tiers"]) for w in W5["weapons"]}
    items = [it for it in g.get_editor_property("items") if it.weight > 0]
    tiered = {str(it.name): set(it.tiers) for it in items if len(it.tiers)}
    # (a Spell Tome is found as the tome of a spell of the room's tier: those are checked by their own tiers)
    tiered.update({str(it.name): set(it.tiers) for it in g.get_editor_property("items") if it.kind == unreal.RDItemKind.TOME and len(it.tiers)})
    anywhere = {str(it.name) for it in items if not len(it.tiers) and it.kind != unreal.RDItemKind.TOME}
    res = {}; ok = True; N = 2500
    for t in range(1, 6):
        S = I2(t - 1, 0); cnt = {}; wrong = set(); n = 0; nw = 0; na = 0; arm = set(); seen_all = set()
        for i in range(N):
            for x in g.loot_list_of(S, 300000 + i):
                x = str(x); n += 1; seen_all.add(x)
                if x in tiered and t not in tiered[x]: wrong.add(x)
                if x in SETS: na += 1; arm.add(x)
                if x in wt:
                    nw += 1; cnt[x] = cnt.get(x, 0) + 1
            if i % 250 == 0: yield
        inw = sum(it.weight for it in items if (not it.tiers or t in list(it.tiers)) and str(it.name) in wt)
        alls = sum(it.weight for it in items if not it.tiers or t in list(it.tiers))
        share, want = nw / max(n, 1), inw / alls
        sd = math.sqrt(want * (1 - want) / max(n, 1))
        ina = sum(it.weight for it in items if (not it.tiers or t in list(it.tiers)) and str(it.name) in SETS)
        sa, wa = na / max(n, 1), ina / alls; sda = math.sqrt(max(wa * (1 - wa), 1e-9) / max(n, 1))
        e = {"items": n, "weapons": sorted(cnt), "want": sorted(k for k, v in wt.items() if t in v), "wrong_tier": sorted(wrong),
             "weapon_share": round(share, 4), "expected": round(want, 4), "sd_off": round(abs(share - want) / sd, 2),
             "armour": sorted(arm), "armour_want": sorted(k for k, v in SET_TIERS.items() if t in v), "armour_share": round(sa, 4), "armour_expected": round(wa, 4),
             "armour_sd_off": round(abs(sa - wa) / sda, 2), "everywhere_missing": sorted(anywhere - seen_all)}
        e["ok"] = (e["weapons"] == e["want"] and not wrong and e["sd_off"] < 4.5 and e["armour"] == e["armour_want"] and e["armour_sd_off"] < 4.5
                   and not e["everywhere_missing"])
        ok = ok and e["ok"]; res[f"tier{t}"] = e
    step_result("tierloot", ok, **res)

W3SLASH = json.load(open(os.path.join(SA, "random_dungeon_magic5", "w5_clips", "Warrior3", "slash.json")))
HILT_SPACING = {}
for _h, _ch in (("Warrior", "Warrior3"), ("Warlock", "DarkCaster")):
    try: HILT_SPACING[_h] = float(json.load(open(os.path.join(SA, "random_dungeon_magic5", "w5_clips", _ch, "w5_times.json")))["left_on_hilt"])
    except Exception: pass


def step_weapons():
    g = G["gen"]; c = yield from restart(); quiet(True)
    rules = W5["rules"]["who"]; out = {}; shots_ = []
    cams = [a for a in GS.get_all_actors_of_class(G["w"], unreal.SceneCapture2D) if a.actor_has_tag("RDM5_WeaponCam")]
    cam = cams[0] if cams else None
    shot_dir = os.path.join(unreal.Paths.project_saved_dir(), "W5Test", TAG)
    def front_shot(name, dist=300.0, height=30.0):
        """her alone, unlit (the colour as painted: the great hall is lit by torches), from her front-right and her right side"""
        if not cam: return
        p = G["pawn"]; l = p.get_actor_location(); f = p.get_actor_forward_vector(); r = p.get_actor_right_vector()
        cc = cam.capture_component2d
        cc.set_editor_property("primitive_render_mode", unreal.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST)
        cc.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_BASE_COLOR)
        for view, way in (("front", f * 0.85 + r * 0.5), ("side", r)):
            at_ = l + way.normal() * dist + V(0, 0, height)
            cam.set_actor_location(at_, False, True)
            d = l + V(0, 0, 20) - at_; cam.set_actor_rotation(unreal.Rotator(roll=0, pitch=math.degrees(math.atan2(d.z, math.hypot(d.x, d.y))), yaw=math.degrees(math.atan2(d.y, d.x))), True)
            cc.clear_show_only_components(); cc.show_only_actor_components(p, True); cc.capture_scene()
            unreal.RenderingLibrary.export_render_target(G["w"], cc.texture_target, shot_dir, f"{name}_{view}.png"); shots_.append(f"{name}_{view}.png")
    def palm_local(body, bone):
        """her palm point on the hand bone (the grips' place: 6.5 cm along the forearm, 2.5 below, in her reference pose)"""
        ref = unreal.AnimPoseExtensions.get_reference_pose(body.skeletal_mesh_asset.skeleton)
        bp = lambda n: unreal.AnimPoseExtensions.get_bone_pose(ref, n, unreal.AnimPoseSpaces.WORLD)
        h = bp(bone); s_ = bone[-1]; fore = (h.translation - bp(f"lowerarm_{s_}").translation).normal()
        return unreal.MathLibrary.inverse_transform_location(h, h.translation + fore * 6.5 + V(0, 0, -2.5))
    for hero in ("Warrior", "Warlock", "Rogue", "Mage", "Summoner"):
        if str(g.current_hero) != hero: g.switch_hero(hero); yield from wait(0.6); refresh()
        c = cb(); quiet(True); body = G["pawn"].mesh
        n0 = len(g.weapons)
        for w in W5["weapons"]: c.add_item(w["name"], 1)
        took = [str(x.name) for x in g.weapons][n0:]
        carried = sorted(l.split("|")[1] for l in lines(c) if l.startswith("carried|"))
        allowed = rules[hero]
        want = [w["name"] for w in W5["weapons"] if allowed == "all" or w["type"] in allowed]
        e = {"took": len(took), "carried": len(carried), "took_right": took == want, "carried_right": carried == sorted(w["name"] for w in W5["weapons"] if w["name"] not in want)}
        if not took:
            msg_ok = not c.use_item(W5["weapons"][0]["name"]) and "cannot wield" in str(c.message)
            e["refused"] = msg_ok; out[hero] = e; continue
        pr = palm_local(body, "hand_r"); pl = palm_local(body, "hand_l")
        hands, nums = [], []
        for wi, name in enumerate(took):
            i = n0 + wi; wd = g.weapons[i]; fr = W5F[wkey(name)]; w = next(x for x in W5["weapons"] if x["name"] == name)
            c.select_weapon(i); yield
            comp = c.get_weapon_mesh(); bone = str(wd.hand_bone)
            xf = comp.get_world_transform(); grip = xf.transform_location(V(*fr["origin"]))
            # (Warrior3's slash: the grip point lies where the clip's left palm comes along the hilt, the right palm
            # slash.json's left_on below it)
            slash = w["type"] == "two handed sword" and hero == "Warrior"
            if slash: grip = grip - xf.transform_direction(V(*fr["x"])).normal() * W3SLASH["left_on"]
            palm = body.get_socket_transform(bone, unreal.RelativeTransformSpace.RTS_WORLD).transform_location(pl if bone == "hand_l" else pr)
            bonus = (g.melee_bonus if not wd.get_editor_property("spell") else g.ranged_bonus)
            h = {"weapon": name, "mesh_ok": comp.static_mesh == wd.mesh, "bone": bone, "grip_to_palm_cm": round((grip - palm).length(), 1),
                 "damage": round(c.get_damage_of(i), 2), "want_damage": round((8 + 3 * w["damage"]) * (1 + bonus), 2), "durability": c.get_weapon_durability(i), "wear": c.get_weapon_wear(i)}
            # the attacks' length (each of her clips at the weapon's rate: their mean is the table's speed) and, for two
            # hands, the left palm on the hilt at each blow
            lens = []; offs = []; alongs = []
            for k in range(len(wd.attacks)):
                if not c.start_attack(): break
                lens.append(c.get_attack_length())
                hit_at = (wd.hit_times[k] - (wd.attack_starts[k] if len(wd.attack_starts) > k else 0.0)) / wd.play_rate
                yield from wait(hit_at)
                if w["type"] == "two handed sword":
                    # (wielded as her one-handed sword: her sword's clips, nothing in her other hand at the blow)
                    oh = c.get_off_hand_mesh()
                    offs.append(bool(oh is not None and oh.static_mesh is not None and oh.is_visible()))
                if k == 0 and (wi == 0 or name in ("Katana", "Plate Knight's Sword", "Ursag's Horn Blade", "Kukri", "Longbow", "Viking Bow", "Crossbow", "Dwarf Crossbow")):
                    front_shot(f"{hero}_{wkey(name)}")
                t0 = now()
                while c.is_attacking() and now() - t0 < 3.0: yield
                yield from wait(0.12)
            if lens: h["attack_s"] = round(sum(lens) / len(lens), 3); h["attacks"] = len(lens); h["want_s"] = round(cycle(w["speed"]), 3)
            if w["type"] == "two handed sword":
                h["off_hand_shown"] = any(offs)
                if slash: h["slash_clips"] = [a.get_name() for a in wd.attacks] == ["AS_Warrior3_Slash"]
                else: h["sword_clips"] = [a.get_name() for a in wd.attacks] == [a.get_name() for a in g.weapons[0].attacks]
            hands.append(h)
        # a blow that lands takes 1 off; at 0 it breaks and she draws her first weapon
        i = n0; name = took[0]; c.select_weapon(i); yield
        ms = start_monsters(); ms.sort(key=lambda m: (m.get_actor_location() - G["pawn"].get_actor_location()).length())
        brk = {"weapon": name}
        gap = 110 if not g.weapons[i].get_editor_property("spell") else 600
        def by_a_monster():
            """next to the nearest monster of the start section, facing it (a quiet monster wanders off between blows)"""
            ms_ = start_monsters(); ms_.sort(key=lambda m: (m.get_actor_location() - G["pawn"].get_actor_location()).length())
            return any(stand_off(m, gap) for m in ms_)
        by_a_monster()
        c.set_weapon_wear(i, 2.0); h0 = c.hits_landed; b0 = c.weapons_broken
        t0 = now()
        while now() - t0 < 6.0 and c.hits_landed == h0:
            if not c.is_attacking(): c.start_attack()
            yield
        yield from wait(0.3); brk["wear_after_one"] = c.get_weapon_wear(i) if str(g.weapons[i].name) == name else None
        t0 = now(); h1 = c.hits_landed
        while now() - t0 < 10.0 and c.weapons_broken == b0:
            if str(c.get_weapon_name()) == name and not c.is_attacking():
                if c.hits_landed == h1 and now() - t0 > 1.5: by_a_monster(); t0b = now()
                c.start_attack()
            yield
        yield from wait(0.2)
        brk.update({"broke": c.weapons_broken - b0, "last_broken": str(c.last_broken), "still_carried": name in [str(x.name) for x in g.weapons], "now_in_hand": str(c.get_weapon_name()),
                    "message": str(c.message)})
        e.update({"hands": hands, "break": brk})
        out[hero] = e
    quiet(False)
    def hero_ok(hero, e):
        if not e["took_right"] or not e["carried_right"]: return False
        if not e.get("hands"): return e.get("refused", False)
        for h in e["hands"]:
            if not (h["mesh_ok"] and h["grip_to_palm_cm"] < 7.0 and abs(h["damage"] - h["want_damage"]) < 0.01 and abs(h.get("attack_s", -9) - h.get("want_s", 9)) < 0.03): return False
            # (a two-handed sword wielded as her one-handed sword: her sword's clips, nothing in her other hand)
            if "sword_clips" in h and not (h["sword_clips"] and not h["off_hand_shown"]): return False
            # (the Warrior, Warrior3: her own slash, nothing in her other hand)
            if "slash_clips" in h and not (h["slash_clips"] and not h["off_hand_shown"]): return False
        b = e["break"]
        return b.get("wear_after_one") == 1.0 and b["broke"] == 1 and b["last_broken"] == b["weapon"] and not b["still_carried"] and b["now_in_hand"] != b["weapon"] and "broke" in b["message"]
    ok = all(hero_ok(h, e) for h, e in out.items()) and len(out) == 5
    R.setdefault("shots", []).extend(shots_)
    step_result("weapons", ok, heroes=out, front_shots=shots_)

# ------------------------------------------------------------------------------------------------ the armour table, repairs, crafting
WT = {"full plate": "heavy", "heavy": "heavy", "medium": "medium", "partial": "medium", "light": "light"}
def clear_run(p, length=1100.0):
    """a direction from where she stands with a body-wide sweep clear for `length`"""
    l = p.get_actor_location(); best = None
    for k in range(24):
        a = k * math.pi / 12; d = V(math.cos(a), math.sin(a), 0.0)
        h = unreal.SystemLibrary.sphere_trace_single(G["w"], V(l.x, l.y, l.z), V(l.x + d.x * length, l.y + d.y * length, l.z), 45.0,
                                                     unreal.TraceTypeQuery.ECC_VISIBILITY, False, [p], unreal.DrawDebugTrace.NONE, True)
        if h is None or not h.to_tuple()[0]: best = a; break
    return best
def run_speed(c, p, yaw):
    """her running speed (cm/s) along yaw: run 1.6 s, measured over the last 0.8 s"""
    p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=math.degrees(yaw)), True)
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=math.degrees(yaw)))
    sim = lambda k_, d_: c.simulate_key(k_, d_)
    sim(key("LeftShift"), True); sim(key("W"), True)
    yield from wait(0.8); a = p.get_actor_location(); t0 = now()
    yield from wait(0.8); b = p.get_actor_location(); t1 = now()
    sim(key("W"), False); sim(key("LeftShift"), False); yield from wait(0.5)
    return math.hypot(b.x - a.x, b.y - a.y) / max(t1 - t0, 1e-3)

def step_armourtable():
    g = G["gen"]; c = yield from restart(); quiet(True)
    items = {str(i.name): i for i in g.get_editor_property("items") if i.kind == unreal.RDItemKind.ARMOUR}
    rows = []
    for s_ in AJ["sets"]:
        it = items.get(s_["title"])
        ww = WT.get(s_["type"]) or ("light" if s_["speed_rating"] >= 7 else "medium" if s_["speed_rating"] >= 4 else "heavy")
        e = {"set": s_["title"], "type": s_["type"], "dr": s_["damage_rating"], "sp": s_["speed_rating"]}
        if it is None: e["ok"] = False; rows.append(e); continue
        e.update({"share": round(it.amount, 4), "slower": round(it.slower, 4), "durability": it.durability, "tiers": list(it.tiers), "weight": str(it.armour_weight.name).lower(),
                  "rarity": it.weight, "ratings": [it.damage_rating, it.speed_rating], "type_in_game": str(it.armour_type)})
        e["ok"] = (abs(it.amount - 0.05 * s_["damage_rating"]) < 1e-4 and abs(it.slower - 0.03 * (10 - s_["speed_rating"])) < 1e-4 and it.durability == s_["durability"]
                   and list(it.tiers) == s_["tiers"] and e["weight"] == ww and it.weight == 20.0 and e["ratings"] == [s_["damage_rating"], s_["speed_rating"]]
                   and e["type_in_game"] == s_["type"])
        rows.append(e)
    # her speed: none, a set that does not slow her (speed 10), the heaviest (speed 1)
    p = G["pawn"]; start = p.get_actor_location(); cm = p.get_component_by_class(unreal.CharacterMovementComponent)
    yaw = clear_run(p); speeds = {}
    for t in (None, "Orc Warrior\u2019s Armour", "Epic Plate (Female)"):
        if t: c.add_item(t, 1); c.wear_armour(t) if str(c.get_worn_armour()) != t else None
        else: c.take_off_armour()
        p.set_actor_location(start, False, True); yield from wait(0.4)
        top = cm.get_editor_property("max_walk_speed"); slow = c.get_armour_slow()
        v = (yield from run_speed(c, p, yaw)) if yaw is not None else 0.0
        speeds[t or "none"] = {"top": round(top, 1), "slow": round(slow, 3), "ran": round(v, 1)}
    s0_, s1_, s2_ = speeds["none"], speeds["Orc Warrior\u2019s Armour"], speeds["Epic Plate (Female)"]
    speed_ok = (yaw is not None and abs(s1_["top"] - s0_["top"]) < 0.5 and abs(s2_["top"] / s0_["top"] - 0.73) < 0.005
                and abs(s1_["ran"] / max(s0_["ran"], 1) - 1.0) < 0.05 and abs(s2_["ran"] / max(s0_["ran"], 1) - 0.73) < 0.05)
    # durability: three blows that reach her take 3 off; at 0 half its share
    t = "Epic Plate (Female)"; full = c.get_armour_durability(t); c.set_health(c.get_max_health())
    w0 = c.get_armour_wear(t)
    for _ in range(3): c.apply_damage(10.0, None); yield from wait(0.25)
    w3 = c.get_armour_wear(t); share_full = c.get_armour()
    c.set_armour_wear(t, 1.0); c.set_health(c.get_max_health()); c.apply_damage(10.0, None); yield from wait(0.2)
    took_last = c.last_blow_taken; at0 = {"wear": c.get_armour_wear(t), "share": round(c.get_armour(), 4), "message": str(c.message)}
    c.apply_damage(10.0, None); yield from wait(0.2)
    took_worn = c.last_blow_taken; line = next(l for l in lines(c) if l.startswith("armour|" + t + "|"))
    dur = {"full": full, "before": w0, "after_3": w3, "share_full": round(share_full, 4), "blow_at_1_left": round(took_last, 3), "at_0": at0,
           "blow_worn_out": round(took_worn, 3), "line": line}
    dur_ok = (full == 600 and w0 == 600 and w3 == 597 and abs(share_full - 0.5) < 1e-4 and abs(took_last - 5.0) < 0.01 and at0["wear"] == 0
              and abs(at0["share"] - 0.25) < 1e-4 and "worn out" in at0["message"] and abs(took_worn - 7.5) < 0.01 and line.endswith("|0|600"))
    c.take_off_armour(); quiet(False)
    ok = all(r["ok"] for r in rows) and len(rows) == 27 and speed_ok and dur_ok
    step_result("armourtable", ok, sets=rows, speed=speeds, speed_ok=speed_ok, durability=dur, durability_ok=dur_ok)

def step_repair():
    g = G["gen"]; c = yield from restart(); quiet(True)
    ok_sw = g.switch_hero("Warrior"); yield from wait(0.6); refresh(); c = cb(); c.set_scripted_only(False)
    t = "Templar\u2019s Armour"; c.add_item(t, 1); c.wear_armour(t); c.set_armour_wear(t, 0.0)
    worn_share = c.get_armour()
    wpn = "Viking Shortsword"; c.add_item(wpn, 1)
    wl_ = list(g.get_editor_property("weapons")); wi = next(i for i in range(len(wl_)) if str(wl_[i].name) == wpn); wfull = c.get_weapon_durability(wi); c.set_weapon_wear(wi, 10.0)
    c.add_item("Patch Kit", 2); c.add_item("Leather Strips", 1)
    yield from press("I"); ls = lines(c)
    yield from cursor_to(c, next(i for i, l in enumerate(ls) if l.startswith("repair|Patch Kit|")))
    yield from press("Enter")
    picking = c.is_picking_repair(); rl = [str(x) for x in c.get_repair_lines()]
    shot("repair_list"); yield from rwait(1.5)
    def rcursor(i):
        while c.get_repair_cursor() < i: yield from press("S")
        while c.get_repair_cursor() > i: yield from press("W")
    ai = next(i for i, l in enumerate(rl) if l.startswith("armour|" + t + "|")); yield from rcursor(ai); yield from press("Enter")
    arm = {"wear": c.get_armour_wear(t), "share": round(c.get_armour(), 4), "kits": c.get_item_count("Patch Kit"), "message": str(c.message)}
    rl2 = [str(x) for x in c.get_repair_lines()]; still = c.is_picking_repair()
    wl = next(i for i, l in enumerate(rl2) if l.startswith("weapon|%d|" % wi)); yield from rcursor(wl); yield from press("Enter")
    wp = {"wear": c.get_weapon_wear(wi), "full": wfull, "kits": c.get_item_count("Patch Kit"), "picking_after_last_kit": c.is_picking_repair(), "message": str(c.message)}
    # leather strips on the whole (mended) weapon: refused, kept
    ls = lines(c); yield from cursor_to(c, next(i for i, l in enumerate(ls) if l.startswith("repair|Leather Strips|")))
    c.set_weapon_wear(wi, wfull); c.set_armour_wear(t, c.get_armour_durability(t))
    yield from press("Enter"); rl3 = [str(x) for x in c.get_repair_lines()]
    yield from rcursor(0); yield from press("Enter")
    whole = {"strips": c.get_item_count("Leather Strips"), "message": str(c.message)}
    yield from press("BackSpace"); back = {"picking": c.is_picking_repair(), "inventory_open": c.is_inventory_open()}
    yield from press("I"); g.switch_hero("Summoner"); yield from wait(0.6); refresh(); quiet(False)
    want_arm = min(210.0, 0.0 + 210 * 0.75)
    ok = (ok_sw and picking and abs(worn_share - 0.1) < 1e-4 and len(rl) == 2 and abs(arm["wear"] - want_arm) < 1e-3 and abs(arm["share"] - 0.2) < 1e-4 and arm["kits"] == 1 and still
          and abs(wp["wear"] - min(wfull, 10 + wfull * 0.75)) < 1e-3 and wp["kits"] == 0 and not wp["picking_after_last_kit"]
          and whole["strips"] == 1 and "whole already" in whole["message"] and not back["picking"] and back["inventory_open"])
    step_result("repair", ok, switched=ok_sw, worn_out_share=round(worn_share, 4), lines=rl, armour=arm, armour_want=want_arm, weapon=wp, whole=whole, back=back)

def step_craft():
    g = G["gen"]; c = yield from restart(); quiet(True); p = G["pawn"]
    s0 = g.get_section(I2(0, 0)); hall_room = s0.room_at(g.get_start_room_center())
    anv0 = [a for a in s0.get_anvil_points()]; in_hall = [a for a in anv0 if s0.room_at(a) == hall_room]
    gen_ = {}
    for S in (I2(1, 0), I2(0, 1), I2(-1, 0), I2(0, -1)):
        if not g.get_section(S): g.generate_section_now(S)
        s = yield from built(S)
        forges = [i for i in range(s.get_num_rooms()) if s.get_room_kind(i) == "Forge"]
        forge_ok = all(any(s.room_at(a) == i for a in s.get_anvil_points()) for i in forges)
        gen_["%d,%d" % (S.x, S.y)] = {"anvils": len(s.get_anvil_points()), "forges": len(forges), "forges_have_one": forge_ok, "added_in_room": s.anvil_room}
    # by the hall's anvil
    a = in_hall[0] if in_hall else None; opened = {}
    if a:
        for k in range(16):
            ang = k * math.pi / 8; q = V(a.x + math.cos(ang) * 150, a.y + math.sin(ang) * 150, 100)
            if s0.room_at(q) != hall_room: continue
            p.set_actor_location(q, False, True); yield from wait(0.3)
            if g.describe_nearest(p.get_actor_location(), 260.0) == "use the anvil": break
        yaw = math.degrees(math.atan2(a.y - q.y, a.x - q.x)); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-15, yaw=yaw))
        said = g.describe_nearest(p.get_actor_location(), 260.0)
        yield from press("F"); yield from rwait(0.3)
        cl = [str(x) for x in c.get_craft_lines()]
        opened = {"prompt": said, "open": c.is_crafting_open(), "paused": GS.is_game_paused(G["w"]), "lines": cl}
        # nothing to make it with
        yield from rwait(0.2); yield from press("Enter")
        refused = {"made": c.items_crafted, "message": str(c.message), "can": [l.split("|")[2] for l in cl]}
        # what leather strips take, the wood from three kinds
        give = {"Straw Rope": 5, "Glue": 5, "Cured Leather Strip": 5, "Hardwood": 2, "Timber": 2, "Wood Log": 3}
        for n_, k_ in give.items(): c.add_item(n_, k_)
        cl2 = [str(x) for x in c.get_craft_lines()]
        shot("crafting"); yield from rwait(1.5)
        yield from press("Enter")
        left = {n_: c.get_item_count(n_) for n_ in give}; made = {"strips": c.get_item_count("Leather Strips"), "crafted": c.items_crafted, "message": str(c.message)}
        yield from press("F"); yield from rwait(0.3)
        closed = {"open": c.is_crafting_open(), "paused": GS.is_game_paused(G["w"])}
    quiet(False)
    wood_left = left.get("Hardwood", 9) + left.get("Timber", 9) + left.get("Wood Log", 9) if a else None
    ok = (len(in_hall) >= 1 and all(v["anvils"] >= 1 and v["forges_have_one"] for v in gen_.values()) and opened.get("prompt") == "use the anvil" and opened.get("open")
          and opened.get("paused") and len(opened.get("lines", [])) == 5 and refused["made"] == 0 and "need" in refused["message"] and set(refused["can"]) == {"0"}
          and cl2[0].split("|")[2] == "1" and made["strips"] == 1 and made["crafted"] == 1 and left["Straw Rope"] == 0 and left["Glue"] == 0
          and left["Cured Leather Strip"] == 0 and wood_left == 2 and not closed["open"] and not closed["paused"])
    step_result("craft", ok, start_anvils=len(anv0), in_great_hall=len(in_hall), generated=gen_, opened=opened, refused=refused if a else None,
                lines_given=cl2 if a else None, made=made if a else None, left=left if a else None, closed=closed if a else None)

def step_maps():
    g = G["gen"]; c = yield from restart(); quiet(True); p = G["pawn"]; hud = G["pc"].get_hud()
    s0 = g.get_section(I2(0, 0)); hall_room = s0.room_at(g.get_start_room_center())
    hall_anvil = next((a for a in s0.get_anvil_points() if s0.room_at(a) == hall_room), None)
    yield from wait(0.5)
    mini = {"tiers": sorted(set(str(x) for x in hud.get_mini_tier_labels())), "anvils": [[round(v.x), round(v.y)] for v in hud.get_anvils_drawn()]}
    shot("minimap_t1"); yield from rwait(1.5)
    yield from press("M"); yield from rwait(0.5)
    big = {"tiers": sorted(set(str(x) for x in hud.get_map_tier_labels())), "anvils": [[round(v.x), round(v.y)] for v in hud.get_anvils_drawn()]}
    shot("bigmap_t1"); yield from rwait(1.5); yield from press("M")
    # into a tier-2 set of rooms
    S = I2(1, 0)
    if not g.get_section(S): g.generate_section_now(S)
    s = yield from built(S)
    rooms = [i for i in range(s.get_num_rooms()) if s.get_room_kind(i) != "Hallway junction"]
    rc = s.get_room_center(rooms[0]); p.set_actor_location(V(rc.x, rc.y, 100), False, True); yield from wait(1.0)
    mini2 = sorted(set(str(x) for x in hud.get_mini_tier_labels()))
    yield from press("M"); yield from rwait(0.5)
    big2 = sorted(set(str(x) for x in hud.get_map_tier_labels())); anv2 = [[round(v.x), round(v.y)] for v in hud.get_anvils_drawn()]
    shot("bigmap_t2"); yield from rwait(1.5); yield from press("M"); quiet(False)
    ha = [round(hall_anvil.x), round(hall_anvil.y)] if hall_anvil else None
    t_of = lambda labels: sorted({l.split("|")[1] for l in labels})
    ok = (ha is not None and mini["tiers"] and t_of(mini["tiers"]) == ["1"] and ha in mini["anvils"] and big["tiers"] and t_of(big["tiers"]) == ["1"]
          and ha in big["anvils"] and "2" in t_of(mini2) and "2" in t_of(big2))
    step_result("maps", ok, hall_anvil=ha, minimap_t1=mini, bigmap_t1=big, minimap_t2=mini2, bigmap_t2=big2, bigmap_t2_anvils=anv2)

def rms_of(path):
    """the root mean square of a 16-bit wav (both channels)"""
    import wave, array
    w = wave.open(path, "rb"); n = w.getnframes(); data = array.array("h", w.readframes(n)); w.close()
    if not len(data): return 0.0
    return math.sqrt(sum(float(x) * x for x in data) / len(data)) / 32768.0
def step_fire():
    g = G["gen"]; mv0 = g.get_editor_property("music_volume"); g.set_editor_property("music_volume", 0.0)
    try:
        res = yield from fire_measure(g)
    finally:
        g.set_editor_property("music_volume", mv0); quiet(False)
        lms = unreal.find_object(None, "/Script/UnrealEd.Default__LevelEditorMiscSettings")
        if "bg_audio" in G: lms.set_editor_property("bAllowBackgroundAudio", G.pop("bg_audio"))
    ok = (res.get("spot") is not None and res.get("far") is not None and res.get("fire_db_change") is not None and -10.0 < res["fire_db_change"] < -6.0
          and res["rms_before"] > res["rms_now"] > res["rms_floor"] and all(abs(v_ - w_) < 1e-3 for v_, w_ in zip(res["volumes_now"].values(), (0.22, 0.26, 0.34))))
    step_result("fire", ok, **res)
def fire_measure(g):
    """(the fire step) the recordings and their levels"""
    c = yield from restart(); quiet(True); p = G["pawn"]
    unreal.RDDungeonGenerator.set_unfocused_volume(1.0)
    # (the editor sets the volume to 0 while it is not in front, unless its Allow Background Audio is on: on for the step)
    lms = unreal.find_object(None, "/Script/UnrealEd.Default__LevelEditorMiscSettings"); G["bg_audio"] = lms.get_editor_property("bAllowBackgroundAudio")
    lms.set_editor_property("bAllowBackgroundAudio", True)
    s0 = g.get_section(I2(0, 0)); fires = [(s0.get_fire_point(i), s0.get_fire_kind(i)) for i in range(s0.get_num_fire_points())]
    torches = [f for f, k in fires if k == 0]
    # a place 2.5 m in front of a torch, in its room, with no other fire within 9 m
    spot = None
    for f in torches:
        if any((o - f).length() > 1.0 and (o - f).length() < 900.0 for o, _ in fires): continue
        for k in range(16):
            a = k * math.pi / 8; q = V(f.x + math.cos(a) * 250, f.y + math.sin(a) * 250, 100)
            if s0.room_at(q) >= 0: spot = (q, f); break
        if spot: break
    # (somewhere out of that torch's earshot, to stop its voice: every room has fires of its own, so the floor is measured
    # at the spot with the fires' volume at 0)
    far = None
    if spot:
        for r_ in range(s0.get_num_rooms()):
            q = s0.get_room_center(r_); q = V(q.x, q.y, 100)
            if s0.get_room_kind(r_) != "Hallway junction" and (q - spot[1]).length() > 2200: far = q; break
    out = os.path.join(unreal.Paths.project_saved_dir(), "RDM5Fire", TAG); os.makedirs(out, exist_ok=True)
    def record(name, at, sec=4.0):
        p.set_actor_location(far, False, True); yield from wait(0.8)        # (away from every fire: its voice stops)
        p.set_actor_location(at, False, True); yield from wait(1.6)                                   # (back: it starts with the set's volume)
        g.start_recording_output(sec + 1.0)
        yield from rwait(sec)
        g.stop_recording_output(out, name)
        yield from rwait(0.5)
        return rms_of(os.path.join(out, name + ".wav"))
    def set_vol(scale):
        snd = g.get_editor_property("sounds")
        for k_, v_ in VOLS.items():
            # (one loop file per set for the step: a voice picks one of a set's files at random, and two files' own
            # loudness differs by more than the change measured)
            st = snd[k_]; st.volume = v_ * scale; st.sounds = list(st.sounds)[:1]; snd[k_] = st
        G["fire_scale"] = scale
        g.set_editor_property("sounds", snd)
    VOLS = {k_: g.get_editor_property("sounds")[k_].volume for k_ in ("Env.Torch", "Env.Brazier", "Env.Hearth")}
    res = {"volumes_now": {k_: round(v_, 3) for k_, v_ in VOLS.items()}, "spot": [round(spot[0].x), round(spot[0].y)] if spot else None, "far": [round(far.x), round(far.y)] if far else None}
    if spot and far:
        set_vol(0.0); floor = yield from record("floor", spot[0]); set_vol(1.0)
        new = yield from record("fire_now", spot[0])
        set_vol(1.0 / 0.4); old = yield from record("fire_before", spot[0]); set_vol(1.0)
        fire_new = math.sqrt(max(new * new - floor * floor, 0.0)); fire_old = math.sqrt(max(old * old - floor * floor, 0.0))
        db = 20 * math.log10(fire_new / fire_old) if fire_new > 0 and fire_old > 0 else None
        res.update({"rms_floor": round(floor, 6), "rms_now": round(new, 6), "rms_before": round(old, 6), "fire_db_change": round(db, 2) if db is not None else None,
                    "fire_over_floor_db_now": round(20 * math.log10(max(new, 1e-9) / max(floor, 1e-9)), 2), "wavs": out})
    return res

# ------------------------------------------------------------------------------------------------ 2026-10-24: the user's second list
SPJ = json.load(open(os.path.join(OUT, "spells.json"), encoding="utf-8"))
MTJ = json.load(open(os.path.join(OUT, "monster_tiers.json"), encoding="utf-8"))

def step_chance():
    """a container holds anything one time in three; then 1 to 6 items as before; the great hall's armour whatever"""
    g = G["gen"]; c = yield from restart(); S = I2(0, 0)
    N = 6000; held = 0; cnt = {}; mism = 0
    for i in range(N):
        idx = 200000 + i; n = len(g.loot_list_of(S, idx))
        if n: held += 1; cnt[n] = cnt.get(n, 0) + 1
        if bool(g.container_holds_loot(S, idx)) != (n > 0): mism += 1
        if i % 500 == 0: yield
    want = float(LT["container_chance"]["chance"]); share = held / N; sd = math.sqrt(want * (1 - want) / N)
    p6 = 1.0 / 6.0; sd6 = math.sqrt(p6 * (1 - p6) / max(held, 1))
    worst = max(abs(cnt.get(k, 0) / max(held, 1) - p6) / sd6 for k in range(1, 7))
    hall = list(g.get_start_room_containers())
    hall_items = {str(x) for i in hall for x in g.loot_list_of(S, i)}
    # (one of the start section's containers that holds nothing, opened: it says so, and nothing is found)
    s0 = g.get_section(S); empty = {}
    ei = next((i for i in range(s0.get_num_containers()) if i not in hall and not s0.is_target_open(False, i) and not len(g.loot_list_of(S, i))), None)
    if ei is not None:
        f0 = g.items_found; e0 = g.containers_empty; s0.toggle_container(ei); yield from wait(0.3)
        empty = {"container": ei, "kind": str(s0.get_container_kind(ei)), "message": str(c.message), "found": g.items_found - f0, "counted": g.containers_empty - e0}
    ok_empty = bool(empty) and empty["message"] == "Empty: nothing inside" and empty["found"] == 0 and empty["counted"] == 1
    ok = abs(share - want) / sd < 4.5 and sorted(cnt) == [1, 2, 3, 4, 5, 6] and worst < 4.5 and mism == 0 and set(START_ARMOUR) <= hall_items and ok_empty
    step_result("chance", ok, containers=N, holding=held, share=round(share, 4), wanted=want, sd_off=round(abs(share - want) / sd, 2),
                counts={str(k): cnt[k] for k in sorted(cnt)}, counts_worst_sd=round(worst, 2), draw_mismatch=mism, hall=hall, hall_armour=sorted(hall_items & set(SETS)), empty_opened=empty)

def step_corpses():
    """the dead stay where they fell (no sinking, no vanishing), frozen; the set generated again lays them where they lay"""
    g = G["gen"]; c = yield from restart(); quiet(True); p = G["pawn"]
    S = I2(1, 0); g.generate_section_now(S); s = yield from built(S)
    ms = [m for m in s.spawned_monsters if alive(m)][:3]
    for m in ms: m.apply_damage(1.0e6, p)
    before = [(m.get_actor_location(), m.spawn_index, str(m.monster_name)) for m in ms]
    yield from wait(g.corpse_seconds + 5.0)
    stay = [bool(unreal.SystemLibrary.is_valid(m) and m.is_corpse() and (m.get_actor_location() - b).length() < 5.0) for m, (b, _, _) in zip(ms, before)]
    frozen = [bool(unreal.SystemLibrary.is_valid(m) and not m.is_actor_tick_enabled()) for m in ms]
    pr = progress(S)
    # (dropped and generated again: its corpses lie where they fell, dead; the rest alive as before)
    p.set_actor_location(V(0, 0, 100.0), False, True); yield from wait(0.3)
    g.reload_section(S); yield from wait(0.2)
    if not g.is_section_generated(S): g.generate_section_now(S)
    s = yield from built(S)
    laid = {m.spawn_index: m for m in s.spawned_monsters if unreal.SystemLibrary.is_valid(m) and m.is_corpse()} if s else {}
    again = [bool(i in laid and (laid[i].get_actor_location() - b).length() < 30.0 and str(laid[i].monster_name) == n) for b, i, n in before]
    pr2 = progress(S); quiet(False)
    ok = len(ms) >= 2 and all(stay) and all(frozen) and all(again) and pr2["killed"] == pr["killed"] >= len(ms)
    step_result("corpses", ok, killed=len(ms), stayed_put_after_s=round(g.corpse_seconds + 5.0, 1), stayed=stay, frozen=frozen, laid_again_in_place=again,
                killed_counted=[pr["killed"], pr2["killed"]])

def step_monsters():
    """each tier's sections spawn the gallery monsters of that tier, in their own colours (no tint), their hit points,
    damage, speed and blows' pace by the tier"""
    g = G["gen"]; c = yield from restart(); quiet(True)
    defs = {str(d.name): d for d in g.get_editor_property("monsters")}
    res = {}; ok = True; avg = []
    for t in range(1, 6):
        S = I2(t - 1, 0)
        if t > 1: g.generate_section_now(S)
        s = yield from built(S)
        ms = [m for m in s.spawned_monsters if alive(m)] if s else []
        kinds = sorted({str(m.monster_name) for m in ms})
        wrong = sorted({k for k in kinds if defs[k].tier != t})
        hp = [m.get_max_health() for m in ms]; dmg = [m.get_damage() for m in ms]
        # (her kind's walking speed times the tier's; a blow's pace the tier's)
        spd = [round(m.get_walk_speed() / max(defs[str(m.monster_name)].walk_speed, 1.0), 3) for m in ms]
        gap = [round(m.get_attack_interval() / max(defs[str(m.monster_name)].attack_interval, 0.01), 3) for m in ms]
        abil = sorted({str(m.ability.name) for m in ms})
        want_spd = MTJ["tiers"]["speed"][t - 1]; want_gap = MTJ["tiers"]["attack_interval"][t - 1]
        e = {"monsters": len(ms), "kinds": kinds, "wrong_tier": wrong, "mean_hp": round(sum(hp) / max(len(hp), 1), 1), "tier_hp": round(g.get_monster_health(S), 1),
             "mean_damage": round(sum(dmg) / max(len(dmg), 1), 1), "tier_damage": round(g.get_monster_damage(S), 1),
             "speed_x": sorted(set(spd)), "want_speed_x": want_spd, "blow_gap_x": sorted(set(gap)), "want_gap_x": want_gap, "abilities": abil}
        e["ok"] = (len(ms) > 0 and not wrong and all(abs(x - want_spd) < 0.01 for x in spd) and all(abs(x - want_gap) < 0.01 for x in gap)
                   and abs(e["mean_hp"] - e["tier_hp"]) < 0.35 * e["tier_hp"] and (t >= 3 or abil == ["NONE"]))
        ok = ok and e["ok"]; res[f"tier{t}"] = e; avg.append(e["mean_hp"])
        if t <= 2: shot(f"monsters_tier{t}")
    ok = ok and all(avg[i] < avg[i + 1] for i in range(4))
    quiet(False)
    step_result("monsters", ok, **res)

def step_abilities():
    """a tier 3+ monster's blow carries its ability: poison eats her hit points, weakening takes off her blows, slowing her
    speed; Dispel Hex ends them all and none takes hold while it lasts"""
    g = G["gen"]; c = yield from restart(); p = G["pawn"]
    for xy in ((2, 0), (3, 0), (-2, 0), (0, 2), (-3, 0)): g.generate_section_now(I2(*xy))
    for xy in ((2, 0), (3, 0), (-2, 0), (0, 2), (-3, 0)): yield from built(I2(*xy))
    by = {}
    for xy in ((2, 0), (3, 0), (-2, 0), (0, 2), (-3, 0)):
        for m in g.get_section(I2(*xy)).spawned_monsters:
            if alive(m) and str(m.ability.name) != "NONE": by.setdefault(str(m.ability.name), m)
    res = {"found": sorted(by)}
    hp0 = c.get_max_health()
    for ab, m in by.items():
        c.clear_afflictions(); c.set_health(c.get_max_health())
        if not stand_near(m, (150.0, 200.0, 260.0, 330.0)): res[ab] = "no place by it"; continue
        h0 = m.hits_landed; t0 = time.time()
        while m.hits_landed == h0 and time.time() - t0 < 12: yield
        quiet(True)                     # (no more blows: what follows is the ability's alone)
        e = {"monster": str(m.title), "tier": m.tier, "power": round(m.ability_power, 2), "hits": m.hits_landed - h0,
             "poisoned": c.is_poisoned(), "weakness": round(c.get_weakness(), 3), "slowness": round(c.get_slowness(), 3), "buffs": [str(x) for x in c.get_buff_lines()]}
        if ab == "POISON":
            hp_a = c.get_health(); yield from wait(1.5); e["poison_took"] = round(hp_a - c.get_health(), 1)
        res[ab] = e
        quiet(False)
    # (Dispel Hex ends them; then none takes hold while it lasts)
    c.apply_monster_ability(unreal.RDMonsterAbility.POISON, 1.4, 20.0); c.apply_monster_ability(unreal.RDMonsterAbility.SLOW, 1.4, 20.0); c.apply_monster_ability(unreal.RDMonsterAbility.WEAKEN, 1.4, 20.0)
    before = [c.is_poisoned(), c.get_slowness() > 0, c.get_weakness() > 0]
    g.switch_hero("Mage"); yield from wait(0.5); refresh(); c = cb(); c.add_item("Tome of Dispel Hex")
    wi = next(i for i, l in enumerate(lines(c)) if l.startswith("weapon|Dispel Hex"))
    c.apply_monster_ability(unreal.RDMonsterAbility.POISON, 1.4, 20.0); c.apply_monster_ability(unreal.RDMonsterAbility.SLOW, 1.4, 20.0)
    on = [c.is_poisoned(), c.get_slowness() > 0]
    c.cast_spell_now(wi, None)
    after = [c.is_poisoned(), c.get_slowness() > 0, c.get_weakness() > 0]
    c.apply_monster_ability(unreal.RDMonsterAbility.POISON, 1.4, 20.0); immune = not c.is_poisoned()
    res.update({"set_by_hand": before, "on_the_mage": on, "after_dispel": after, "immune_after": immune})
    g.switch_hero(g.get_editor_property("default_hero")); yield from wait(0.5); refresh()
    ok = (set(res["found"]) == {"POISON", "WEAKEN", "SLOW"} and isinstance(res.get("POISON"), dict) and res["POISON"]["poisoned"] and res["POISON"].get("poison_took", 0) > 0
          and isinstance(res.get("WEAKEN"), dict) and res["WEAKEN"]["weakness"] > 0 and isinstance(res.get("SLOW"), dict) and res["SLOW"]["slowness"] > 0
          and all(before) and all(on) and not any(after) and immune)
    step_result("abilities", ok, **res)

def stand_near(m, gaps):
    """stand_off at the first of these distances where there is a place"""
    for gp in gaps:
        if stand_off(m, gp): return True
    return False

def fresh_monster(g, exclude):
    for xy in ((2, 0), (-2, 0), (0, 2), (0, -2), (2, 2), (-2, -2), (3, 0), (-3, 0)):
        s = g.get_section(I2(*xy))
        if not s: continue
        for m in s.spawned_monsters:
            if alive(m) and not m.is_ally() and m not in exclude: return m
    return None

def step_spells():
    """the 30 spells of the table: the Mage learns them from tomes (key and message), the Warlock only offense and curses,
    the Warrior none; each released by its weapon at a monster of a tier-3 set (or round her) does what its line says,
    measured on the monsters and on her; its effects are there (particles near it); a picture of each; a cooldown and a
    want of mana refuse a cast"""
    g = G["gen"]; c = yield from restart(); quiet(True); p = G["pawn"]
    for xy in ((2, 0), (-2, 0), (0, 2), (0, -2), (2, 2), (-2, -2), (3, 0), (-3, 0)): g.generate_section_now(I2(*xy))
    for xy in ((2, 0), (-2, 0), (0, 2), (0, -2), (2, 2), (-2, -2), (3, 0), (-3, 0)): yield from built(I2(*xy))
    res = {}
    # who learns what
    learn = {}
    for hero, tomes in (("Warrior", ["Tome of Fireball"]), ("Warlock", ["Tome of Frost Shard", "Tome of Ash Ward", "Tome of Curse of Frailty", "Tome of Fire Bolt", "Tome of Raise Dead"])):
        g.switch_hero(hero); yield from wait(0.5); refresh(); c = cb()
        for t in tomes: c.add_item(t)
        learn[hero] = {"weapons": [l.split("|")[1] for l in lines(c) if l.startswith("weapon|")], "tomes_carried": [l.split("|")[1] for l in lines(c) if l.startswith("tome|")]}
    g.switch_hero("Mage"); yield from wait(0.5); refresh(); c = cb(); p = G["pawn"]
    for s in SPJ["spells"]: c.add_item("Tome of " + s["name"])
    weaps = [l.split("|")[1] for l in lines(c) if l.startswith("weapon|")]
    learn["Mage"] = {"weapons": len(weaps), "learned": c.spells_learned, "message": str(c.message)}
    res["learn"] = learn
    # each spell released
    sp_out = {}; used = []
    name_of_w = {"Fire Bolt": "Fire"}
    for s in SPJ["spells"]:
        nm = s["name"]; wname = name_of_w.get(nm, nm)
        wi = next((i for i, w in enumerate(weaps) if w == wname), -1)
        e = {"weapon": wi}
        if wi < 0: sp_out[nm] = e; continue
        c.clear_afflictions(); c.set_health(c.get_max_health()); c.set_mana(c.get_max_mana())
        kind = s["kind"]
        close = kind in ("Lash", "Ward", "Skin", "Mirror", "Rune", "Sanctum", "Pact", "Veil", "Nova", "Raise", "Knight", "Dispel")
        # (a monster with room beside it: the next one when there is none (one in a corner left Ash Ward untried))
        m = None; tried = 0
        for _ in range(4):
            q = fresh_monster(g, used)
            if q is None: break
            tried += 1
            if stand_near(q, (160.0, 220.0, 280.0, 340.0) if close else (520.0, 440.0, 600.0, 360.0)): m = q; break
            used.append(q)
        if m is None:
            e["no_monster" if tried == 0 else "no_place"] = True; e["monsters_tried"] = tried; sp_out[nm] = e; continue
        yield from wait(0.2)
        near = [x for x in g.get_monsters() if alive(x) and (x.get_actor_location() - p.get_actor_location()).length() < 1500]
        if kind == "Drain": c.set_health(c.get_max_health() * 0.5)         # (hurt: the drain has something to give back)
        hp0 = {x.get_name(): x.get_health() for x in near}; her0 = c.get_health()
        # (what needs a corpse: monsters near her killed first; the one she faces too, for Raise Dead)
        if kind in ("Raise", "Corpse"):
            victims = [x for x in near if x != m and (x.get_actor_location() - p.get_actor_location()).length() < 1000][:2]
            if kind == "Raise" or not victims: victims.append(m)
            for x in victims: x.apply_damage(1.0e6, p)
            yield from wait(1.2)
            e["corpses_near"] = len(g.get_corpses_near(p.get_actor_location(), 1400.0))
        rel0 = {str(k_): v_ for k_, v_ in dict(c.get_editor_property("spells_released")).items()}
        corpse_at = [x.get_actor_location() for x in g.get_corpses_near(p.get_actor_location(), 1400.0)] if kind == "Corpse" else []
        c.cast_spell_now(wi, m if alive(m) else None)
        yield from wait(0.25)
        if corpse_at:
            # (the bursts are where the corpses lay: their particles there, now and a moment later)
            best = 0
            for _ in range(3):
                for q in corpse_at: best = max(best, c.get_spell_particles(q, 450.0)[0])
                yield from wait(0.3)
            e["particles_at_corpses"] = best
        # (what holds a while: looked at now, before it wears off)
        if kind == "Curse": e["cursed"] = sum(1 for x in near if unreal.SystemLibrary.is_valid(x) and x.get_curse_share() > 0)
        n_, sys_ = c.get_spell_particles(m.get_actor_location() if unreal.SystemLibrary.is_valid(m) else p.get_actor_location(), 900.0)
        n2, sys2 = c.get_spell_particles(p.get_actor_location(), 600.0)
        e["particles"] = max(n_, n2, e.get("particles_at_corpses", 0)); e["systems"] = max(sys_, sys2)
        shot("spell_" + "".join(ch if ch.isalnum() else "_" for ch in nm.lower()))
        # what it did
        if kind == "Ward":
            hits0 = c.ward_blocks; h0 = c.get_health()
            for _ in range(int(s.get("count", 0)) or 1): c.apply_damage(15.0, m)
            if s.get("amount"): c.apply_damage(c.get_max_health() * 0.3, m)
            e.update({"blocked": c.ward_blocks - hits0, "health_lost": round(h0 - c.get_health(), 1)})
            e["ok"] = e["blocked"] >= (int(s.get("count", 0)) or 1) and e["health_lost"] < 1.0
        elif kind == "Skin":
            c.apply_damage(40.0, m); e["blow_taken"] = round(c.last_blow_taken, 1); e["ok"] = abs(e["blow_taken"] - 40.0 * (1 - s["amount"])) < 0.5
        elif kind == "Dispel":
            e["ok"] = not c.is_poisoned()
        elif kind == "Mirror":
            mh = m.get_health(); h0 = c.get_health(); c.apply_damage(30.0, m)
            e.update({"monster_lost": round(mh - m.get_health(), 1), "she_lost": round(h0 - c.get_health(), 1), "reflected": c.reflected}); e["ok"] = e["monster_lost"] >= 29.0 and e["she_lost"] < 1.0
        elif kind == "Rune":
            c.apply_damage(40.0, m); e["blow"] = round(c.last_blow_before, 1); e["ok"] = abs(e["blow"] - 40.0 * (1 - s["amount"])) < 0.5
        elif kind == "Sanctum":
            h0 = c.get_health(); c.apply_damage(40.0, m); e["she_lost"] = round(h0 - c.get_health(), 1); e["ok"] = e["she_lost"] < 0.5
        elif kind == "Pact":
            c.set_health(5.0); c.apply_damage(100.0, m); e.update({"alive": not c.is_dead(), "health": round(c.get_health(), 1), "saves": c.pact_saves})
            e["ok"] = e["alive"] and abs(e["health"] - c.get_max_health() * s["amount"]) < 1.0
        elif kind == "Veil":
            ev0 = c.evaded
            for _ in range(40): c.apply_damage(5.0, m)
            e["evaded_of_40"] = c.evaded - ev0; e["veiled"] = c.is_veiled(); e["ok"] = e["veiled"] and 20 <= e["evaded_of_40"] <= 38
        elif kind == "Knight":
            yield from wait(1.0)
            al = g.get_allies(); e.update({"allies": len(al), "champion": [str(a.title) for a in al if a.is_champion()]}); e["ok"] = len(e["champion"]) == 1
        elif kind == "Raise":
            yield from wait(1.5)
            al = [a for a in g.get_allies() if not a.is_champion()]; e.update({"raised": len(al), "alive": all(alive(a) for a in al)}); e["ok"] = len(al) >= 1
            if al:
                # (her camera passes her allies, and one it is in is hidden: an ally behind her filled the reel's view)
                a = al[0]; cm = G["pc"].player_camera_manager; a0 = a.get_actor_location()
                cam_ignored = a.capsule_component.get_collision_response_to_channel(unreal.CollisionChannel.ECC_CAMERA) == unreal.CollisionResponseType.ECR_IGNORE
                a.set_actor_location(cm.get_camera_location(), False, True); yield from wait(0.2)
                hid_at_cam = bool(a.get_editor_property("hidden"))
                a.set_actor_location(a0, False, True); yield from wait(0.2)
                e.update({"camera_ignores_ally": cam_ignored, "hidden_at_camera": hid_at_cam, "shown_away": not a.get_editor_property("hidden")})
                e["ok"] = e["ok"] and cam_ignored and hid_at_cam and e["shown_away"]
        else:
            # (offense, curses: the monsters near her hurt; what lasts: over its duration; a slow looked at as it holds)
            if s.get("slow"):
                yield from wait(0.5); e["slowed"] = sum(1 for x in near if unreal.SystemLibrary.is_valid(x) and x.get_slow_share() > 0)
            yield from wait(max(float(s.get("duration", 0)), 0.8) + (2.8 if kind == "Meteors" else 0.6))
            hurt = {k_: round(v_ - (x.get_health() if unreal.SystemLibrary.is_valid(x) else 0.0), 1) for x in near for k_, v_ in hp0.items() if k_ == x.get_name()}
            e["hurt"] = sum(1 for v_ in hurt.values() if v_ > 0.5); e["damage_dealt"] = round(sum(v_ for v_ in hurt.values() if v_ > 0.5), 1)
            if kind == "Nova": e["her_price"] = round(her0 - c.get_health(), 1)
            if kind == "Drain": e["she_gained"] = round(c.get_health() - her0, 1)
            if kind == "Corpse": e["corpses_left"] = len(g.get_corpses_near(p.get_actor_location(), 1400.0))
            e["ok"] = (e["hurt"] >= 1 if kind not in ("Curse", "Corpse") else e.get("cursed", 0) >= 1 if kind == "Curse" else e["corpses_left"] < e.get("corpses_near", 0))
            if kind == "Bolt":
                # (where the bolt ended, against the monster aimed at: a miss says where it went)
                ba = c.last_burst_at; e.update({"monster": str(m.title) if unreal.SystemLibrary.is_valid(m) else "?", "flown_m": round(c.last_bolt_flown / 100.0, 1),
                                                "burst_from_monster_m": round((ba - m.get_actor_location()).length() / 100.0, 1) if unreal.SystemLibrary.is_valid(m) else None})
            if kind == "Bolt" and s.get("count"): e["ok"] = e["ok"] and e["hurt"] >= min(2, len(near))
            if kind == "Nova": e["ok"] = e["ok"] and e["her_price"] > 0
        rel = {str(k_): v_ for k_, v_ in dict(c.get_editor_property("spells_released")).items()}; e["released"] = rel.get(nm, 0) - rel0.get(nm, 0)
        if s.get("slow"): e["ok"] = e.get("ok") and e.get("slowed", 0) >= 1
        e["ok"] = bool(e.get("ok")) and e["particles"] > 0
        sp_out[nm] = e; used.append(m)
        yield from rwait(0.6)
    res["spells"] = sp_out
    # a cooldown refuses the next cast; a spell costing more than her mana is refused and says so
    wi = weaps.index("Ash Ward"); c.set_mana(c.get_max_mana())
    a1 = c.start_attack_with(wi); yield from wait(2.0); a2 = c.start_attack_with(wi)
    res["cooldown"] = {"first": a1, "second": a2, "left": round(c.get_cooldown_left(wi), 1), "refusals": c.cooldown_refusals}
    wi = weaps.index("Apocalypse"); r0 = c.casts_refused; yield from wait(1.0); a3 = c.start_attack_with(wi)
    res["too_dear"] = {"cast": a3, "refused": c.casts_refused - r0, "message": str(c.message)}
    g.switch_hero(g.get_editor_property("default_hero")); yield from wait(0.5); refresh(); quiet(False)
    lw = learn["Warlock"]
    ok = (learn["Warrior"]["weapons"] == ["Sword"] and learn["Warrior"]["tomes_carried"] == ["Tome of Fireball"]
          and "Frost Shard" in lw["weapons"] and "Curse of Frailty" in lw["weapons"] and "Ash Ward" not in lw["weapons"] and "Raise Dead" not in lw["weapons"]
          and sorted(lw["tomes_carried"]) == ["Tome of Ash Ward", "Tome of Raise Dead"] and learn["Mage"]["learned"] == 28 and learn["Mage"]["weapons"] == 30
          and all(v.get("ok") for v in sp_out.values()) and a1 and not a2 and res["cooldown"]["refusals"] >= 1 and not a3 and res["too_dear"]["refused"] == 1
          and "more than you have" in res["too_dear"]["message"])
    step_result("spells", ok, failed=sorted(k for k, v in sp_out.items() if not v.get("ok")), **res)

def step_rings():
    """rings: a magic ring adds its share to her mana (spellcasters), an hp ring to her hit points (Warrior, Warlock), a
    dexterity ring to her ranged damage (Rogue); one of a kind at a time (another replaces it); the others refused"""
    g = G["gen"]; c = yield from restart(); res = {}
    g.switch_hero("Mage"); yield from wait(0.5); refresh(); c = cb()
    m0 = c.get_max_mana()
    for r in ("Magic Potency Ring 5", "Magic Potency Ring 9", "HP Potency Ring 3"): c.add_item(r)
    w5 = c.wear_ring("Magic Potency Ring 5"); m5 = c.get_max_mana(); w9 = c.wear_ring("Magic Potency Ring 9"); m9 = c.get_max_mana()
    worn = str(c.get_worn_ring(unreal.RDRingKind.MAGIC)); hp_r = c.wear_ring("HP Potency Ring 3"); msg = str(c.message)
    off = c.wear_ring("Magic Potency Ring 9"); m_off = c.get_max_mana()
    res["Mage"] = {"mana": [m0, m5, m9, m_off], "worn_after_9": worn, "hp_ring_refused": not hp_r, "message": msg, "lines": [l for l in lines(c) if l.startswith("ring|")]}
    g.switch_hero("Warrior"); yield from wait(0.5); refresh(); c = cb()
    h0 = c.get_max_health(); hp_now = c.get_health(); c.add_item("HP Potency Ring 4"); c.wear_ring("HP Potency Ring 4")
    res["Warrior"] = {"health": [h0, c.get_max_health()], "health_now": [hp_now, c.get_health()]}
    g.switch_hero("Rogue"); yield from wait(0.5); refresh(); c = cb()
    xi = next(i for i, l in enumerate(lines(c)) if l.startswith("weapon|Crossbow")); d0 = c.get_damage_of(xi)
    c.add_item("Dexterity Ring 10"); c.wear_ring("Dexterity Ring 10"); d1 = c.get_damage_of(xi)
    res["Rogue"] = {"crossbow": [round(d0, 2), round(d1, 2)]}
    g.switch_hero(g.get_editor_property("default_hero")); yield from wait(0.5); refresh()
    M = res["Mage"]["mana"]; W = res["Warrior"]
    ok = (abs(M[1] - M[0] * 1.5) < 0.5 and abs(M[2] - M[0] * 1.9) < 0.5 and abs(M[3] - M[0]) < 0.5 and res["Mage"]["worn_after_9"] == "Magic Potency Ring 9"
          and res["Mage"]["hp_ring_refused"] and abs(W["health"][1] - W["health"][0] * 1.4) < 0.5 and abs((W["health_now"][1] - W["health_now"][0]) - W["health"][0] * 0.4) < 0.5
          and abs(res["Rogue"]["crossbow"][1] / res["Rogue"]["crossbow"][0] - (1.3 + 1.0) / 1.3) < 0.01)
    step_result("rings", ok, **res)

def step_breakdown():
    """at an anvil the weapons she found break down into materials by type and tier (loot_table.json's breakdown); the one
    in her hands is refused; one she carries but cannot wield breaks down too"""
    g = G["gen"]; c = yield from restart(); res = {}
    BD = {tuple(b["types"]): b["gives"] for b in LT["breakdown"]["types"]}
    wt = {w["name"]: w for w in W5["weapons"]}
    def gives(name):
        w = wt[name]; t = w["type"] if w["type"] != "ranged" else ("crossbow" if "crossbow" in name.lower() else "bow")
        g_ = next(v for k, v in BD.items() if t in k); tier = min(w["tiers"])
        return {k: v * tier for k, v in g_.items()}
    g.switch_hero("Warrior"); yield from wait(0.5); refresh(); c = cb()
    blade = next(w["name"] for w in W5["weapons"] if w["type"] == "two handed sword")
    c.add_item(blade); c.set_crafting_open(True); yield from rwait(0.3)
    cl = [str(l) for l in c.get_craft_lines()]; bl = [l for l in cl if l.startswith("breakdown|")]
    have0 = {k: c.get_item_count(k) for k in gives(blade)}
    # (the cursor to its line, Enter)
    li = next(i for i, l in enumerate(cl) if l.startswith("breakdown|" + blade + "|"))
    while c.get_craft_cursor() != li: yield from press("S")
    yield from press("Enter")
    got = {k: c.get_item_count(k) - have0[k] for k in have0}
    still = any(l.startswith("weapon|" + blade) for l in lines(c))
    c.set_crafting_open(False); yield from rwait(0.3)
    # (the one in her hands: refused)
    c.add_item(blade); wi = next(i for i, l in enumerate(lines(c)) if l.startswith("weapon|" + blade)); c.select_weapon(wi)
    drawn = c.break_down_weapon(wi); drawn_msg = str(c.message)
    res["Warrior"] = {"breakdown_lines": bl, "gave": got, "wanted": gives(blade), "weapon_still_there": still, "drawn_refused": not drawn, "message": drawn_msg}
    g.switch_hero("Mage"); yield from wait(0.5); refresh(); c = cb()
    bow = next(w["name"] for w in W5["weapons"] if w["type"] == "ranged")
    c.add_item(bow); h0 = {k: c.get_item_count(k) for k in gives(bow)}
    ok_i = c.break_down_item(bow); got_b = {k: c.get_item_count(k) - h0[k] for k in h0}
    res["Mage"] = {"carried": bow, "broke": ok_i, "gave": got_b, "wanted": gives(bow), "left": c.get_item_count(bow)}
    g.switch_hero(g.get_editor_property("default_hero")); yield from wait(0.5); refresh()
    ok = (len(bl) == 1 and res["Warrior"]["gave"] == res["Warrior"]["wanted"] and not still and res["Warrior"]["drawn_refused"]
          and ok_i and res["Mage"]["gave"] == res["Mage"]["wanted"] and res["Mage"]["left"] == 0)
    step_result("breakdown", ok, **res)

def step_menu():
    """Escape opens the menu and pauses the game; W / S choose, A / D set a volume (saved in the user settings); a volume
    measured on what she hears (a fire at 2.5 m recorded with the environment volume at 1 and at 0.5: about -6 dB);
    the buttons (a dry run: they say what they would do): Choose another hero, Quit; Resume and Escape go back"""
    g = G["gen"]; c = yield from restart(); res = {}
    g.set_editor_property("menu_dry_run", True)
    for k in range(4): g.set_user_volume(k, 1.0)
    yield from press("Escape"); yield from rwait(0.3)
    res["open"] = g.is_menu_open(); res["paused"] = GS.is_game_paused(G["w"]); res["lines"] = [str(l) for l in g.get_menu_lines()]
    shot("menu"); yield from rwait(1.5)
    # (to Environment sounds, ten steps down)
    while g.get_menu_cursor() != 2: yield from press("S")
    for _ in range(10): yield from press("A", 0.06)
    res["environment"] = round(g.get_user_volume(2), 3)
    ini = os.path.join(unreal.Paths.project_saved_dir(), "Config", "WindowsEditor", "GameUserSettings.ini")
    res["saved"] = "Environment=0.5" in (open(ini, encoding="utf-8", errors="ignore").read() if os.path.exists(ini) else "")
    for want, idx in (("hero", 5), ("quit", 6)):
        while g.get_menu_cursor() != idx: yield from press("S")
        g.set_editor_property("last_menu_action", ""); yield from press("Enter"); res[want] = str(g.last_menu_action)
    while g.get_menu_cursor() != 4: yield from press("W")
    yield from press("Enter"); yield from rwait(0.3)
    res["resumed"] = not g.is_menu_open() and not GS.is_game_paused(G["w"])
    yield from press("Escape"); yield from rwait(0.2); o2 = g.is_menu_open(); yield from press("Escape"); yield from rwait(0.2)
    res["escape_toggles"] = o2 and not g.is_menu_open()
    # (what she hears: the fire step's recording at the environment volume 1 and 0.5)
    mv0 = g.get_editor_property("music_volume"); g.set_editor_property("music_volume", 0.0)
    try:
        g.set_user_volume(2, 1.0); r1 = yield from fire_measure(g)
        g.set_user_volume(2, 0.5); r2 = yield from fire_measure(g)
    finally:
        g.set_editor_property("music_volume", mv0); quiet(False); g.set_user_volume(2, 1.0)
        lms = unreal.find_object(None, "/Script/UnrealEd.Default__LevelEditorMiscSettings")
        if "bg_audio" in G: lms.set_editor_property("bAllowBackgroundAudio", G.pop("bg_audio"))
    def own(r): return math.sqrt(max(r["rms_now"] ** 2 - r["rms_floor"] ** 2, 0.0)) if r.get("rms_now") else 0.0
    db = 20 * math.log10(own(r2) / own(r1)) if own(r1) > 0 and own(r2) > 0 else None
    res["fire_at_half_db"] = round(db, 2) if db is not None else None
    g.set_editor_property("menu_dry_run", False)
    ok = (res["open"] and res["paused"] and len(res["lines"]) == 7 and res["environment"] == 0.5 and res["saved"] and res["hero"] == "hero" and res["quit"] == "quit"
          and res["resumed"] and res["escape_toggles"] and db is not None and -8.0 < db < -4.0)
    step_result("menu", ok, **res)

def step_warrior3():
    """(2026-10-26) the Warrior is Warrior3 (862): as her, everything the Warrior does. Her pawn and mesh, her hit points;
    F at a great hall container: what she found is its loot list (weapons she wields join her weapons); F at the hall's
    anvil opens the crafting panel and leather strips are made; a two-handed sword broken down there; plate armour on
    (her own fit, SK_Warrior3_<set>); her sword and shield kill a monster of the start section; a two-handed sword's
    blow (her slash) lands; a monster's blow plays her flinch; M opens the big map"""
    g = G["gen"]; c = yield from restart(); quiet(True); res = {}
    ok_sw = g.switch_hero("Warrior"); yield from wait(0.8); refresh(); c = cb(); c.set_scripted_only(False); p = G["pawn"]
    mesh = p.mesh.get_skinned_asset().get_name()
    res["who"] = {"switched": bool(ok_sw), "pawn": p.get_class().get_name(), "mesh": mesh, "health": c.get_max_health(), "weapons": [str(w.name) for w in g.weapons]}
    S0 = I2(0, 0); s0 = g.get_section(S0); hall = list(g.get_start_room_containers()); hall_room = s0.room_at(g.get_start_room_center())
    # (a container by F)
    fpress = None
    for i in hall:
        cl = s0.get_container_location(i); lst = [str(x) for x in g.loot_list_of(S0, i)]
        if not lst or s0.get_container_open_alpha(i) > 0.0: continue
        for k in range(16):
            a = k * math.pi / 8; q = V(cl.x + math.cos(a) * 130, cl.y + math.sin(a) * 130, 100)
            if s0.room_at(q) < 0: continue
            d = g.describe_nearest(q, 260.0) or ""
            if not d.startswith("open") or "door" in d: continue
            p.set_actor_location(q, False, True); yield from wait(0.3)
            n_w = len(g.weapons); f0 = g.items_found; yield from press("F"); yield from wait(0.6)
            opened = [j for j in hall if s0.get_container_open_alpha(j) > 0.0]
            if opened:
                j = opened[0]; lj = [str(x) for x in g.loot_list_of(S0, j)]
                fpress = {"container": j, "found": g.items_found - f0, "list": lj, "found_list": [str(x) for x in g.last_found_list], "weapons_joined": len(g.weapons) - n_w,
                          "weapons_in_list": sum(1 for x in lj if x in {w_["name"] for w_ in W5["weapons"]})}
            break
        if fpress: break
    res["container"] = fpress
    # (the anvil: crafting)
    a = next((x for x in s0.get_anvil_points() if s0.room_at(x) == hall_room), None); craft = {}
    if a is not None:
        for k in range(16):
            ang = k * math.pi / 8; q = V(a.x + math.cos(ang) * 150, a.y + math.sin(ang) * 150, 100)
            if s0.room_at(q) != hall_room: continue
            p.set_actor_location(q, False, True); yield from wait(0.3)
            if g.describe_nearest(p.get_actor_location(), 260.0) == "use the anvil": break
        give = {"Straw Rope": 5, "Glue": 5, "Cured Leather Strip": 5, "Hardwood": 2, "Timber": 2, "Wood Log": 3}
        for n_, k_ in give.items(): c.add_item(n_, k_)
        s_before = c.get_item_count("Leather Strips")
        yield from press("F"); yield from rwait(0.3)
        craft["open"] = c.is_crafting_open(); cl_ = [str(x) for x in c.get_craft_lines()]
        li = next((i for i, l in enumerate(cl_) if "Leather Strips" in l), 0)
        while c.get_craft_cursor() != li: yield from press("S")
        yield from press("Enter"); craft["strips_made"] = c.get_item_count("Leather Strips") - s_before; craft["message"] = str(c.message)
        # (and a two-handed sword broken down there)
        blade = next(w_["name"] for w_ in W5["weapons"] if w_["type"] == "two handed sword"); c.add_item(blade)
        cl_ = [str(x) for x in c.get_craft_lines()]; li = next((i for i, l in enumerate(cl_) if l.startswith("breakdown|" + blade + "|")), None)
        if li is not None:
            while c.get_craft_cursor() != li: yield from press("S")
            yield from press("Enter")
        craft["broke_down"] = li is not None and not any(l.startswith("weapon|" + blade) for l in lines(c)); craft["breakdown_message"] = str(c.message)
        yield from press("F"); yield from rwait(0.3); craft["closed"] = not c.is_crafting_open()
    res["craft"] = craft
    # (plate armour, her own fit)
    heavy = [s_["title"] for s_ in AJ["sets"] if s_["weight"] == "heavy"]; pl = "Plate Armour" if "Plate Armour" in heavy else heavy[0]
    c.add_item(pl, 1); worn = c.wear_armour(pl); yield from wait(0.3); ms_ = list(c.get_armour_meshes())
    res["armour"] = {"set": pl, "worn": bool(worn) and str(c.get_worn_armour()) == pl, "meshes": [m.skeletal_mesh_asset.get_name() if m.skeletal_mesh_asset else None for m in ms_],
                     "follows_her": all(m.leader_pose_component == p.mesh and m.get_attach_parent() == p.mesh for m in ms_)}
    shot("warrior3_armour"); yield from rwait(1.0)
    c.wear_armour(pl)            # (worn again: off)
    # (her sword and shield kill a monster)
    sw = next(i for i, w_ in enumerate(g.weapons) if str(w_.name) == "Sword"); c.select_weapon(sw); yield
    ms = start_monsters(); ms.sort(key=lambda m: (m.get_actor_location() - p.get_actor_location()).length())
    target = None
    for m in ms:
        if stand_off(m, 110): target = m; break
    h0 = c.hits_landed; t0 = now(); kills0 = g.get_editor_property("monsters_killed") if hasattr(g, "monsters_killed") else None
    while target is not None and alive(target) and now() - t0 < 25.0:
        if not c.is_attacking():
            if (target.get_actor_location() - p.get_actor_location()).length() > 200: stand_off(target, 110)
            c.start_attack()
        yield
    res["sword"] = {"hits": c.hits_landed - h0, "killed": target is not None and not alive(target), "attacks": [x.get_name() for x in g.weapons[sw].attacks]}
    shot("warrior3_sword"); yield from rwait(1.0)
    # (a two-handed sword: her slash lands)
    c.add_item(blade); bi = next(i for i, w_ in enumerate(g.weapons) if str(w_.name) == blade); c.select_weapon(bi); yield
    ms = start_monsters(); ms.sort(key=lambda m: (m.get_actor_location() - p.get_actor_location()).length())
    for m in ms:
        if stand_off(m, 120): break
    h0 = c.hits_landed; t0 = now(); shot_done = False
    while c.hits_landed == h0 and now() - t0 < 12.0:
        if not c.is_attacking(): c.start_attack()
        if not shot_done and c.is_attacking() and now() - t0 > 0.6: shot("warrior3_slash"); shot_done = True
        yield
    res["slash"] = {"hits": c.hits_landed - h0, "attacks": [x.get_name() for x in g.weapons[bi].attacks]}
    # (a blow taken: her flinch)
    quiet(False); taken0 = c.hits_taken; t0 = now(); flinch = None; ai = p.mesh.get_anim_instance()
    while now() - t0 < 20.0:
        if c.hits_taken > taken0:
            yield; mt = ai.get_current_active_montage() if ai else None
            flinch = mt is not None; break
        yield
    quiet(True)
    res["flinch"] = {"blows_taken": c.hits_taken - taken0, "montage_after_blow": flinch, "get_hit": g.weapons[sw].get_hit.get_name() if g.weapons[sw].get_hit else None}
    # (the big map)
    hud = G["pc"].get_hud(); yield from press("M"); yield from rwait(0.4)
    res["map"] = {"tiers": sorted(set(str(x) for x in hud.get_map_tier_labels()))}; shot("warrior3_map"); yield from rwait(1.0); yield from press("M")
    g.switch_hero(g.get_editor_property("default_hero")); yield from wait(0.5); refresh(); quiet(False)
    fp = res["container"]; cr = res["craft"]; am = res["armour"]
    ok = (res["who"]["switched"] and res["who"]["pawn"] == "BP_RDM5_Warrior3Character_C" and mesh == "SK_JRPG_Warrior3" and res["who"]["health"] == 140.0
          and fp is not None and fp["found"] == len(fp["list"]) and fp["found_list"] == fp["list"] and fp["weapons_joined"] == fp["weapons_in_list"]
          and cr.get("open") and cr.get("strips_made") == 1 and cr.get("broke_down") and cr.get("closed")
          and am["worn"] and am["meshes"] and all(str(m_).startswith("SK_Warrior3_") for m_ in am["meshes"]) and am["follows_her"]
          and res["sword"]["killed"] and res["sword"]["hits"] >= 1 and all(x.endswith("_Warrior3") for x in res["sword"]["attacks"])
          and res["slash"]["hits"] >= 1 and res["slash"]["attacks"] == ["AS_Warrior3_Slash"]
          and res["flinch"]["blows_taken"] >= 1 and res["flinch"]["montage_after_blow"] and res["map"]["tiers"])
    step_result("warrior3", ok, **res)

STEPS = {"warrior3": step_warrior3, "select": step_select, "loot": step_loot, "wear": step_wear, "heroarmour": step_heroarmour, "follow": step_follow, "damage": step_damage, "ui": step_ui,
         "tiers": step_tiers, "tierloot": step_tierloot, "weapons": step_weapons, "armourtable": step_armourtable, "repair": step_repair, "craft": step_craft,
         "maps": step_maps, "fire": step_fire, "chance": step_chance, "corpses": step_corpses, "monsters": step_monsters, "abilities": step_abilities,
         "spells": step_spells, "rings": step_rings, "breakdown": step_breakdown, "menu": step_menu}
def run():
    for s in PLAN:
        yield from STEPS[s]()
        yield from rwait(0.3)
def finish(err=None):
    unreal.unregister_slate_post_tick_callback(G["h"])
    R["error"] = err
    try:
        c = cb() if G.get("gen") else None
        if c: c.set_scripted_only(False); c.set_inventory_open(False)
        if G.get("gen"): quiet(False)
    except Exception as e: R["error"] = (err or "") + " / " + str(e)
    os.makedirs(OUT, exist_ok=True); json.dump(R, open(os.path.join(OUT, f"test_{TAG}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    ok = not R.get("error") and len(R["steps"]) == len(PLAN) and all(s["ok"] for s in R["steps"])
    unreal.log(f"RDM5TEST done | {TAG} | {'ok' if ok else 'FAILED'} | " + " | ".join(f"{s['step']} {'ok' if s['ok'] else 'FAILED'}" for s in R["steps"]) + f" | {R.get('error') or ''}")
    G.clear()
def tick(dt):
    try:
        if UES.get_game_world() is None and not G.get("traveling"): finish("PIE ended"); return
        next(G["gen_"])
    except StopIteration: finish()
    except Exception as e:
        import traceback
        unreal.log_error("RDM5TEST error: " + str(e) + traceback.format_exc()); finish(str(e))
G["gen_"] = run()
G["h"] = unreal.register_slate_post_tick_callback(tick)
print("rdm5 test armed:", PLAN, TAG)
