"""mistward_castle test (play-in-editor; 868_mistward_test.ps1 starts it). The rules of docs/improvements.txt, measured in play.
Steps (plan, comma separated):
  basics   the level is "Mistward Castle" with five tiers; the frame rate is measured and shown (a picture of the upper left);
           the anvil's lists are alphabetical (recipes, then what she can break down); the Plate Knight's Sword is a tier 2
           find; the tiers' looks: tier 1 the stone dungeon, tier 2 the castle keep, tier 3 the dwarven halls, tiers 4 and 5
           mixed (more than one look among their sets of rooms)
  shields  the Warrior starts with the Heater Shield on her arm with her sword; a blow takes the shield's share (damage x 4 %)
           less, and the shield loses what it took; she moves (10 - speed) x 3 % slower with it than without; two Kite Shields
           carried as two (one spare); put on, taken off; at the anvil a carried one breaks down into the table's materials, the
           one she wears (the last of its kind) is refused; the Mage cannot wear one
  torch    made at the anvil from 2 wood, 2 straw rope and 1 oils (used up); held in the left hand by each of the four heroes:
           the torch on her left hand bone with her hand on its shaft (within 12 cm), its light on at its head, the shield is not in her hand while it burns; put out, the shield
           is back; a picture in a dark place
  armour   two of one armour set are carried as two (one spare, each with its own durability); one breaks down at the anvil
           into the table's materials, the worn one (the last) is refused
  inventory with 40 kinds in her pack, holding S walks the cursor down (more than 8 lines in 1.5 s), holding W back up
  open     a chest opened with F stays open: F again does not close it, F no longer offers it; its set of rooms built again
           (one generated in play: after "tiers") builds it open
  heights  every monster kind spawned and measured for 6 s as it idles and wanders (16 samples: legs, wings and clips move
           the body): the lowest point of its drawn body comes down to the floor (within 5 cm) and never sinks more than 5
           cm under it (the Insect hovers in its idle)
           (Half Creature 05 among them: it was drawn 6 to 54 cm under the floor)
  tiers    the 75 % rule: tier 1's rooms, monsters and chests counted (the census); the start set's rooms explored and chests
           looted, its monsters killed one at a time: tier 2 stays shut under 75 % and opens at the kill that reaches it
           ("TIER 2 IS OPEN"). Then: a boss (the
           tier's strongest kind, about BossHealth x its hit points, bigger) and 3 to 6 tier-2 monsters in an explored room of
           tier 1 that is not hers; a guarded ring (her kind: the Warrior's HP ring 1 or 2) put first in a container of an
           explored room with 4 guards; the minimap and the big map draw both marks. Tier 2's eight sets cleared: tier 3 opens
           with its own boss and ring
  layout   in every generated set of rooms: shaped rooms (their tiles not their whole rectangle; a dome, a pyramid or a tall
           room's ceiling heights vary), many shapes; the themes' meshes (castle pieces in tier 2, dwarven in tier 3, none in
           tier 1); no two pieces of furniture or containers overlap (their meshes' boxes as built; 7 cm allowed: the generator
           sets pieces side by side 3 cm under their sizes); before
           every container a clear way in (95 cm) on its room's floor, and no container between beds; pictures of shaped rooms
  traps    each kind set off on her (TriggerTrap where it lies): the damaging ones take hit points, the snare and the pit hold
           her, the curse weakens, the teleport trap carries her into another room; the Warrior sees no trap; the Rogue sees
           one within range (the map marks it) and disarms it with F (DisarmChance 1 for the test)
  teleport the great hall's pad and tier 2's first set's pad with its ring; F on tier 2's pad takes the ring; the ring used
           carries her to the great hall's pad; F there carries her to tier 2's pad, F there back
  cells    a prisoner's cell opened with F: the prisoner thanks her, gives her a thing of the tier and walks off, gone after a
           while; a monster's cell: it opens when she comes near and the monster comes for her
  death    the Warrior with things found falls: a pile where she fell with all of them (pictures drawn, the Loot Drops effect
           alive, the map's mark), her pack empty but for her own shield; back on her feet, F at the pile gives them back
Writes SourceArt/mistward/test_<tag>.json and logs "MWTEST done | <tag> | ok / FAILED | ...". Args: plan tag"""
import unreal, sys, json, math, os, time
__keep__ = True
TAG = sys.argv[2] if len(sys.argv) > 2 else "t"
V = unreal.Vector; GS = unreal.GameplayStatics
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
OUT = os.path.join(SA, "mistward")
SH = {s["name"]: s for s in json.load(open(os.path.join(OUT, "shields.json"), encoding="utf-8"))["shields"]}
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
G = {"w": UES.get_game_world()}
assert G["w"] is not None, "PIE is not running"
DEFAULT = "basics,shields,torch,armour,inventory,heights,tiers,open,layout,traps,teleport,cells,death"
PLAN = [s.strip() for s in (sys.argv[1] if len(sys.argv) > 1 else DEFAULT).split(",") if s.strip()]
R = {"tag": TAG, "plan": PLAN, "level": G["w"].get_path_name().split(".")[-1], "steps": []}
I2 = unreal.IntPoint


def refresh():
    w = UES.get_game_world(); G["w"] = w
    if w is None: return False
    gens = GS.get_all_actors_of_class(w, unreal.RDDungeonGenerator); G["gen"] = gens[0] if gens else None
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
def press(name, hold=0.12):
    cb().simulate_key(key(name), True); yield from rwait(hold); cb().simulate_key(key(name), False); yield from rwait(0.1)
def step_result(name, ok, **kw):
    R["steps"].append({"step": name, "ok": bool(ok), **kw})
    unreal.log(f"MWTEST step {name}: {'ok' if ok else 'FAILED'} {json.dumps(kw, ensure_ascii=False, default=str)[:2400]}")
def alive(m):
    try: return m is not None and unreal.SystemLibrary.is_valid(m) and not m.is_dead()
    except Exception: return False
def quiet(on):
    g = G["gen"]
    if on:
        if "aggro" not in G: G["aggro"] = (g.get_editor_property("aggro_distance"), g.get_editor_property("lose_distance"))
        g.set_editor_property("aggro_distance", 0.0); g.set_editor_property("lose_distance", 1.0)
    elif "aggro" in G: a_, l_ = G.pop("aggro"); g.set_editor_property("aggro_distance", a_); g.set_editor_property("lose_distance", l_)
def restart(hero="Warrior"):
    g = G["gen"]
    if str(g.get_editor_property("current_hero")) != hero: g.switch_hero(hero); yield from wait(0.6); refresh()
    G["gen"].restart_play(0); yield from wait(0.8); refresh()
    c = cb(); c.set_scripted_only(False); c.set_inventory_open(False); c.set_crafting_open(False); return c
def shot(name, res="1920x1080"):
    unreal.SystemLibrary.execute_console_command(G["w"], f"HighResShot {res} filename=mw_{TAG}_{name}")
    R.setdefault("shots", []).append(f"mw_{TAG}_{name}.png")
def lines(c): return [str(l) for l in c.get_inventory_lines()]
def put(at, yaw=None, z=None):
    p = G["pawn"]; p.set_actor_location(V(at.x, at.y, (at.z if z is None else z) + 100.0), False, True)
    if yaw is not None:
        p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), True); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=yaw))
def dist2(a, b): return math.hypot(a.x - b.x, a.y - b.y)
def walk_speed(): return G["pawn"].get_editor_property("character_movement").get_editor_property("max_walk_speed")
def items_of(kind): return [i for i in G["gen"].get_editor_property("items") if i.kind == kind]
def section_at(p): return G["gen"].get_section(G["gen"].world_to_section(p))
def tally(t):
    r = G["gen"].get_tier_tally(t)
    if r is None: return None
    if isinstance(r, tuple) and len(r) == 3: ok, d, a = r
    else: d, a = r; ok = True
    return {"ok": bool(ok), "done": [d.x, d.y, d.z], "all": [a.x, a.y, a.z]}
def built(S, sec=40.0):
    g = G["gen"]; t0 = time.time()
    while time.time() - t0 < sec:
        if g.is_section_generated(S) and g.get_section_progress(S) is not None and not g.get_section(S).is_building(): return True
        yield
    return False

# ------------------------------------------------------------------------------------------------ basics
def step_basics():
    c = yield from restart(); g = G["gen"]; quiet(True)
    yield from wait(1.5)
    res = {"title": str(g.dungeon_title), "max_tier": g.max_tier, "show_fps": g.show_fps, "fps": round(g.get_fps(), 1)}
    shot("hud_fps")
    c.set_crafting_open(True); yield from rwait(0.3)
    cl = [str(x).split("|") for x in c.get_craft_lines()]; c.set_crafting_open(False)
    rec = [x[1] for x in cl if x[0] == "recipe"]
    res["recipes"] = rec; res["recipes_sorted"] = rec == sorted(rec, key=lambda s: s.lower())
    pk = [i for i in g.get_editor_property("items") if str(i.name) == "Plate Knight's Sword"]
    res["plate_knight_tiers"] = list(pk[0].tiers) if pk else None
    # (the looks: tier 1 the start (0, 0), tier 2 ring 1, tier 3 ring 2; tiers 4 and 5 every set of their rings)
    res["themes"] = {1: g.get_theme_name(I2(0, 0)), 2: g.get_theme_name(I2(1, 0)), 3: g.get_theme_name(I2(2, 0))}
    for t, r in ((4, 3), (5, 4)):
        res["themes"][t] = sorted({g.get_theme_name(I2(x, y)) for x in range(-r, r + 1) for y in range(-r, r + 1) if max(abs(x), abs(y)) == r})
    quiet(False)
    ok = (res["title"] == "Mistward Castle" and res["max_tier"] == 5 and res["show_fps"] and 5 < res["fps"] < 400 and res["recipes_sorted"]
          and "Torch" in rec and res["plate_knight_tiers"] == [2] and res["themes"][1] == "None" and res["themes"][2] == "Castle"
          and res["themes"][3] == "Dwarf" and len(res["themes"][4]) >= 2 and len(res["themes"][5]) >= 2)
    step_result("basics", ok, **res)

# ------------------------------------------------------------------------------------------------ shields
def step_shields():
    c = yield from restart("Warrior"); g = G["gen"]; quiet(True)
    put(g.get_start_room_center(), 0.0); yield from wait(0.5)
    res = {"start": {"worn": str(c.get_worn_shield()), "in_hand": c.is_shield_in_hand(), "share": round(c.get_shield_share(), 4)}}
    heater = SH["Heater Shield"]
    res["start"]["want_share"] = heater["damage"] * 0.04
    # (her speed with it and without it)
    with_ = walk_speed(); c.wear_shield("Heater Shield"); yield from wait(0.2); without = walk_speed(); off_hand = c.is_shield_in_hand()
    c.wear_shield("Heater Shield"); yield from wait(0.2)
    res["speed"] = {"with": round(with_, 1), "without": round(without, 1), "taken_off_in_hand": off_hand, "back_on": str(c.get_worn_shield()),
                    "measured_share": round(1 - with_ / max(without, 1), 4), "want_share": (10 - heater["speed"]) * 0.03}
    # (a blow of 40: what reaches her, what the shield takes)
    c.set_health(c.get_max_health()); h0 = c.get_health(); w0 = c.get_shield_wear("Heater Shield")
    c.apply_damage(40.0, None); yield from wait(0.1)
    res["blow"] = {"lost": round(h0 - c.get_health(), 2), "want_lost": round(40.0 * (1 - heater["damage"] * 0.04), 2), "shield_lost": round(w0 - c.get_shield_wear("Heater Shield"), 2)}
    # (several of a kind, put on, broken down)
    c.add_item("Kite Shield", 2); yield from wait(0.1)
    res["kite"] = {"count": c.get_item_count("Kite Shield"), "spares": len(c.get_spares("Kite Shield"))}
    c.wear_shield("Kite Shield"); yield from wait(0.1); res["kite"]["worn"] = str(c.get_worn_shield())
    kite = SH["Kite Shield"]; res["kite"]["share"] = round(c.get_shield_share(), 4); res["kite"]["want_share"] = kite["damage"] * 0.04
    mats0 = {n: c.get_item_count(n) for n in ("Iron Ingot", "Steel Ingot", "Timber")}
    res["kite"]["broke_down"] = c.break_down_gear("Kite Shield"); yield from wait(0.1)
    res["kite"]["count_after"] = c.get_item_count("Kite Shield")
    res["kite"]["materials"] = {n: c.get_item_count(n) - mats0[n] for n in mats0}
    res["kite"]["last_refused"] = not c.break_down_gear("Kite Shield"); res["kite"]["refused_says"] = str(c.message)
    c.set_crafting_open(True); yield from rwait(0.2)
    res["kite"]["anvil_line"] = [str(x) for x in c.get_craft_lines() if str(x).startswith("breakdown|Kite Shield")]
    c.set_crafting_open(False)
    shot("shield_kite")
    yield from rwait(0.6)
    g.switch_hero("Mage"); yield from wait(0.6); refresh(); c = cb()
    c.add_item("Kite Shield", 1); res["mage"] = {"wore": c.wear_shield("Kite Shield"), "says": str(c.message)}
    g.switch_hero("Warrior"); yield from wait(0.6); refresh(); quiet(False)
    s, sp, b, k = res["start"], res["speed"], res["blow"], res["kite"]
    ok = (s["worn"] == "Heater Shield" and s["in_hand"] and abs(s["share"] - s["want_share"]) < 1e-3
          and not sp["taken_off_in_hand"] and sp["back_on"] == "Heater Shield" and abs(sp["measured_share"] - sp["want_share"]) < 0.01
          and abs(b["lost"] - b["want_lost"]) < 0.6 and b["shield_lost"] > 0
          and k["count"] == 2 and k["spares"] == 1 and k["worn"] == "Kite Shield" and abs(k["share"] - k["want_share"]) < 1e-3
          and k["broke_down"] and k["count_after"] == 1 and sum(k["materials"].values()) > 0 and k["last_refused"] and k["anvil_line"]
          and not res["mage"]["wore"])
    step_result("shields", ok, **res)

# ------------------------------------------------------------------------------------------------ the torch
def step_torch():
    c = yield from restart("Warrior"); g = G["gen"]; quiet(True)
    put(g.get_start_room_center(), 0.0); yield from wait(0.4)
    give = {"Hardwood": 1, "Timber": 1, "Straw Rope": 2, "Oils": 1}
    for n, k in give.items(): c.add_item(n, k)
    c.set_crafting_open(True); yield from rwait(0.2)
    res = {"can": c.can_craft("Torch"), "made": c.craft("Torch"), "torches": c.get_item_count("Torch"),
           "left": {n: c.get_item_count(n) for n in give}}
    c.set_crafting_open(False); yield from rwait(0.2)
    res["heroes"] = {}
    for hero in ("Warrior", "Mage", "Warlock", "Rogue"):
        if str(g.get_editor_property("current_hero")) != hero: g.switch_hero(hero); yield from wait(0.6); refresh()
        c = cb()
        if c.get_item_count("Torch") < 1: c.add_item("Torch", 1)
        held = c.hold_torch(True); yield from wait(0.4)
        L = c.get_torch_light(); body = G["pawn"].get_editor_property("mesh")
        hand = body.get_socket_location("hand_l")
        # (the torch in her hand: its mesh on her left hand bone, her hand on its shaft (the line along its length), the
        # light at its head)
        tc = next((x for x in G["pawn"].get_components_by_class(unreal.StaticMeshComponent) if x.static_mesh and "Torch" in x.static_mesh.get_name() and x.is_visible()), None)
        shaft = None; length = None
        if tc:
            bb = tc.static_mesh.get_bounding_box(); wt = tc.get_world_transform()
            a_ = wt.transform_location(V((bb.min.x + bb.max.x) / 2, (bb.min.y + bb.max.y) / 2, bb.min.z)); b_ = wt.transform_location(V((bb.min.x + bb.max.x) / 2, (bb.min.y + bb.max.y) / 2, bb.max.z))
            ab = b_ - a_; u = max(0.0, min(1.0, (hand - a_).dot(ab) / max(ab.dot(ab), 1e-6))); shaft = round((a_ + ab * u - hand).length(), 1); length = round(ab.length(), 1)
        r = {"held": held, "is_held": c.is_torch_held(), "shield_in_hand": c.is_shield_in_hand(),
             "light": round(L.intensity, 1) if L else 0.0, "light_visible": bool(L and L.is_visible()),
             "torch_bone": str(tc.get_attach_socket_name()) if tc else None, "hand_to_shaft_cm": shaft, "torch_length_cm": length,
             "light_to_hand_cm": round((L.get_world_location() - hand).length(), 1) if L else None}
        if hero == "Warrior":
            # (in the dark: the unlit side of the great hall, the torch the light)
            shot("torch_warrior")
            yield from rwait(0.6)
        c.hold_torch(False); yield from wait(0.2)
        r["after_out"] = {"is_held": c.is_torch_held(), "shield_in_hand": c.is_shield_in_hand(), "light_visible": bool(L and L.is_visible())}
        res["heroes"][hero] = r
    g.switch_hero("Warrior"); yield from wait(0.6); refresh(); quiet(False)
    hs = res["heroes"]
    ok = (res["can"] and res["made"] and res["torches"] == 1 and all(v == 0 for v in res["left"].values())
          and all(h["held"] and h["is_held"] and h["light"] > 0 and h["light_visible"] and h["torch_bone"] == "hand_l" and h["hand_to_shaft_cm"] is not None and h["hand_to_shaft_cm"] < 12
                  and h["light_to_hand_cm"] < (h["torch_length_cm"] or 0) + 20
                  and not h["shield_in_hand"] and not h["after_out"]["is_held"] and not h["after_out"]["light_visible"] for h in hs.values())
          and hs["Warrior"]["after_out"]["shield_in_hand"])
    step_result("torch", ok, **res)

# ------------------------------------------------------------------------------------------------ armour by the set
def step_armour():
    c = yield from restart("Warrior"); g = G["gen"]
    sets = [i for i in items_of(unreal.RDItemKind.ARMOUR) if any(str(f.hero) == "Warrior" for f in i.armour_fits)] if hasattr(unreal.RDItemDef, "armour_fits") else items_of(unreal.RDItemKind.ARMOUR)
    a = str(sets[0].name)
    c.add_item(a, 2); yield from wait(0.1)
    res = {"set": a, "count": c.get_item_count(a), "spares": [round(x, 1) for x in c.get_spares(a)], "durability": round(c.get_armour_wear(a), 1)}
    res["worn"] = c.wear_armour(a); yield from wait(0.2)
    before = {str(n.name): c.get_item_count(str(n.name)) for n in items_of(unreal.RDItemKind.COMPONENT)}
    res["broke_down"] = c.break_down_gear(a); yield from wait(0.1)
    res["count_after"] = c.get_item_count(a)
    res["materials"] = {k: c.get_item_count(k) - v for k, v in before.items() if c.get_item_count(k) != v}
    res["last_refused"] = not c.break_down_gear(a); res["says"] = str(c.message)
    ok = res["count"] == 2 and len(res["spares"]) == 1 and res["broke_down"] and res["count_after"] == 1 and res["materials"] and res["last_refused"]
    step_result("armour", ok, **res)

# ------------------------------------------------------------------------------------------------ the inventory scrolls while a key is held
def step_inventory():
    c = yield from restart("Warrior"); g = G["gen"]
    for it in [i for i in g.get_editor_property("items") if i.kind in (unreal.RDItemKind.COMPONENT, unreal.RDItemKind.HEALING, unreal.RDItemKind.FOOD)][:40]:
        c.add_item(str(it.name), 1)
    c.set_inventory_open(True); yield from rwait(0.3)
    n = len(lines(c)); c0 = c.get_inventory_cursor()
    c.simulate_key(key("S"), True); yield from rwait(1.5); c.simulate_key(key("S"), False); yield from rwait(0.2)
    c1 = c.get_inventory_cursor()
    c.simulate_key(key("W"), True); yield from rwait(1.0); c.simulate_key(key("W"), False); yield from rwait(0.2)
    c2 = c.get_inventory_cursor()
    # (one press is one line)
    yield from press("S"); c3 = c.get_inventory_cursor()
    c.set_inventory_open(False)
    res = {"lines": n, "start": c0, "after_hold_down_1_5s": c1, "after_hold_up_1s": c2, "one_press": c3 - c2}
    step_result("inventory", n > 20 and c1 - c0 > 8 and c2 < c1 - 4 and res["one_press"] == 1, **res)

# ------------------------------------------------------------------------------------------------ opened containers stay open
def step_open():
    # (in a set of rooms generated in play when there is one (after "tiers"): the start set is saved and never built again)
    g = G["gen"]
    def unlooted(s):
        S_ = g.get_section(s)
        return S_ is not None and any(S_.get_container_kind(i) in ("chest", "trunk") and not S_.is_container_looted(i) for i in range(S_.get_num_containers()))
    if g.is_tier_open(3) and not g.is_section_generated(I2(2, 0)): g.generate_section_now(I2(2, 0)); yield from built(I2(2, 0))
    gen_ = [s for s in g.get_section_coords() if g.is_section_generated(s) and not (s.x == 0 and s.y == 0) and unlooted(s)]
    if gen_: c = cb(); sc = gen_[0]
    else: c = yield from restart("Warrior"); sc = I2(0, 0)
    quiet(True)
    S = g.get_section(sc)
    cand = list(g.get_start_room_containers()) if sc.x == 0 and sc.y == 0 else list(range(S.get_num_containers()))
    best = None
    for i in cand:
        k = S.get_container_kind(i)
        if k in ("chest", "trunk") and not S.is_container_looted(i) and S.get_container_open_alpha(i) < 0.05: best = i; break
    p = S.get_container_location(best)
    # (a stand point from which F names that container)
    stand = None
    for k in range(16):
        a = k * math.pi / 8; q = V(p.x + math.cos(a) * 140, p.y + math.sin(a) * 140, p.z)
        put(q, math.degrees(math.atan2(p.y - q.y, p.x - q.x))); yield
        d = str(g.describe_nearest(G["pawn"].get_actor_location(), 260.0))
        if d and S.get_container_open_alpha(best) < 0.05 and g.describe_nearest(G["pawn"].get_actor_location(), 260.0):
            stand = q; break
    res = {"section": [sc.x, sc.y], "container": best, "kind": S.get_container_kind(best), "describe_before": d}
    r1 = str(g.interact_nearest(G["pawn"].get_actor_location(), 260.0)); yield from wait(1.5)
    res["first_f"] = r1; res["alpha_open"] = round(S.get_container_open_alpha(best), 3)
    res["describe_after"] = str(g.describe_nearest(G["pawn"].get_actor_location(), 260.0))
    r2 = str(g.interact_nearest(G["pawn"].get_actor_location(), 260.0)); yield from wait(1.5)
    res["second_f"] = r2; res["alpha_after_second_f"] = round(S.get_container_open_alpha(best), 3)
    S.toggle_container(best); yield from wait(1.2); res["alpha_after_toggle"] = round(S.get_container_open_alpha(best), 3)
    # (the set of rooms built again)
    old = S.get_name()
    res["reloaded"] = g.reload_section(sc); yield from wait(1.0)
    ok_ = yield from built(sc); S2 = g.get_section(sc); yield from wait(0.5)
    res["rebuilt_new_actor"] = bool(S2) and S2.get_name() != old
    res["alpha_rebuilt"] = round(S2.get_container_open_alpha(best), 3) if S2 else None
    res["looted_rebuilt"] = S2.is_container_looted(best) if S2 else None
    quiet(False)
    ok = (stand is not None and res["alpha_open"] > 0.95 and res["alpha_after_second_f"] > 0.95 and res["alpha_after_toggle"] > 0.95
          and res["alpha_rebuilt"] is not None and res["alpha_rebuilt"] > 0.95 and res["looted_rebuilt"] and (res["reloaded"] or sc.x == 0 and sc.y == 0))
    step_result("open", ok, **res)

# ------------------------------------------------------------------------------------------------ monsters stand on the floor
def step_heights():
    c = yield from restart("Warrior"); g = G["gen"]; quiet(True)
    kinds = [str(m.name) for m in g.get_editor_property("monsters")]
    ctr = g.get_start_room_center(); out = {}; errs = []
    for b in range(0, len(kinds), 8):
        made = []
        for j, k in enumerate(kinds[b:b + 8]):
            m = g.spawn_monster_named(k, V(ctr.x - 900 + (j % 4) * 450, ctr.y - 400 + (j // 4) * 800, ctr.z), 1, 1, 1, 1)
            if m: made.append((k, m))
            else: errs.append(k)
        yield from wait(1.2)
        samples = {k: [] for k, _ in made}
        for _ in range(16):
            for k, m in made:
                try: samples[k].append(m.get_drawn_bottom(0.01, True))
                except Exception as e: errs.append(f"{k}: {e}")
            yield from wait(0.4)
        for k, v in samples.items():
            if v: out[k] = [round(min(v), 1), round(sorted(v)[len(v) // 2], 1), round(max(v), 1)]
        for k, m in made:
            try: m.set_actor_hidden_in_game(True); m.set_actor_location(V(0, 0, -50000), False, True); m.set_actor_tick_enabled(False)
            except Exception: pass
        yield
    bad = {k: v for k, v in out.items() if not -5.0 <= v[0] <= 5.0}
    quiet(False)
    step_result("heights", not bad and not errs and len(out) == len(kinds), kinds=len(kinds), measured=len(out), off=bad, errors=errs,
                half_creature_05=out.get("Half_Creature_05"), all=out)

# ------------------------------------------------------------------------------------------------ the tiers: 75 %, the boss, the guarded ring
def enc():
    out = []
    for l in G["gen"].get_encounter_lines():
        p = str(l).split("|")
        out.append({"kind": p[0], "at": [float(p[1]), float(p[2]), float(p[3])], "name": p[4], **({"alive": int(p[5]), "tier": int(p[6]), "label": p[7], "max_health": float(p[8])} if p[0] != "ring" else {"key": int(p[5]), "tier": int(p[6]), "section": [int(p[7]), int(p[8])]})})
    return out
def map_marks(big):
    hud = G["pc"].get_hud()
    if big: yield from press("M"); yield from rwait(0.5)
    else: yield from rwait(0.3)
    ks = sorted({int(v.z) for v in hud.get_marks_drawn()})
    if big: shot(f"map_tier{len(G['gen'].tiers_opened) + 1}"); yield from rwait(1.0); yield from press("M")
    return ks
def check_opening(t, res):
    g = G["gen"]; e = [x for x in enc() if (x.get("tier") == t)]
    boss = [x for x in e if x["kind"] == "boss"]; band = [x for x in e if x["kind"] == "band"]; guards = [x for x in e if x["kind"] == "guard"]
    ring = [x for x in e if x["kind"] == "ring"]
    her = G["pawn"].get_actor_location(); hs = section_at(her); her_room = hs.room_at(her) if hs else -2
    r = {"boss": boss, "band": len(band), "guards": len(guards), "ring": ring}
    if boss:
        b = boss[0]; bp = V(*b["at"]); S = section_at(bp)
        r["boss_tier_of_room"] = g.tier_of(g.world_to_section(bp)); r["boss_room_is_hers"] = (S == hs and S.room_at(bp) == her_room)
        ms = [m for m in g.get_monsters() if alive(m) and m.boss and m.get_max_health() == b["max_health"]]
        if ms:
            # (bigger by its capsule and mesh, not the actor's scale: against a plain one of its kind)
            plain = g.spawn_monster_named(b["name"], V(bp.x, bp.y, -40000), t, 1, 1, 1)
            r["boss_scale"] = round(ms[0].capsule_component.get_scaled_capsule_half_height() / max(plain.capsule_component.get_scaled_capsule_half_height(), 1.0), 2) if plain else None
            r["boss_mesh_scale"] = round(ms[0].mesh.get_editor_property("relative_scale3d").z / max(plain.mesh.get_editor_property("relative_scale3d").z, 1e-3), 2) if plain else None
            if plain: plain.set_actor_hidden_in_game(True); plain.set_actor_tick_enabled(False)
        else: r["boss_scale"] = None
        # (the tier's kinds' plain hit points: a band member of the same tier)
        r["band_health"] = sorted({x["max_health"] for x in band})
    if ring:
        rg = ring[0]; S = g.get_section(I2(*rg["section"]))
        if rg["key"] >= 0: r["ring_first_in_container"] = [str(x) for x in g.loot_list_of(I2(*rg["section"]), rg["key"])][:1]
        else:
            # (every container of the room already opened (the debug clear opens them all): the ring lies on the floor, a pile)
            r["ring_first_in_container"] = [rg["name"]] if any(pl and not pl.hers and rg["name"] in [str(x) for x in pl.things] for pl in g.loot_piles) else []
            r["ring_in_pile"] = True
        r["ring_kind_ok"] = rg["name"].startswith("HP Potency Ring") and rg["name"].endswith((f" {2 * t - 3}", f" {2 * t - 2}"))
    res[f"tier{t}"] = r
    return (len(boss) == 1 and 3 <= len(band) <= 6 and r.get("boss_tier_of_room") == t - 1 and not r.get("boss_room_is_hers")
            and r.get("boss_scale") and r["boss_scale"] > 1.2 and band and boss[0]["max_health"] > 2.0 * max(r["band_health"])
            and len(guards) == G["gen"].guard_count and ring and r.get("ring_kind_ok") and r["ring_first_in_container"] == [ring[0]["name"]])
def step_tiers():
    c = yield from restart("Warrior"); g = G["gen"]; quiet(True)
    res = {"share": g.tier_open_share}
    yield from wait(1.0)
    res["tally1_start"] = tally(1)
    S0 = I2(0, 0); n_mon = res["tally1_start"]["all"][1] if res["tally1_start"] else 0
    # (the rooms explored and the chests looted, then the monsters killed one at a time (the debug clear leaving fewer
    # each time): tier 2 opens at the first kill that brings the share to 75 % or more, not before)
    steps_ = []
    for leave in range(n_mon, -1, -1):
        g.debug_clear_section(S0, leave, g.get_start_room_center()); yield from wait(0.3)
        ta = tally(1); op = g.is_tier_open(2)
        steps_.append({"killed": ta["done"][1], "of": ta["all"][1], "share": round(ta["done"][1] / max(ta["all"][1], 1), 3), "open": op})
        if op: break
    res["kills"] = steps_
    shut = [s_ for s_ in steps_ if not s_["open"]]; opened = [s_ for s_ in steps_ if s_["open"]]
    res["open_short"] = any(s_["open"] and s_["share"] < 0.75 for s_ in steps_)
    res["opened_at_share"] = opened[0]["share"] if opened else None
    res["last_shut_share"] = shut[-1]["share"] if shut else None
    res["tally1_enough"] = tally(1); res["open_enough"] = g.is_tier_open(2); res["notice"] = str(g.tier_notice)
    yield from wait(0.5)
    ok2 = check_opening(2, res)
    res["marks_minimap"] = yield from map_marks(False)
    res["marks_map"] = yield from map_marks(True)
    # (tier 2's eight sets cleared: tier 3)
    t0 = time.time()
    notices = []
    for S in [s for s in [I2(x, y) for x in range(-1, 2) for y in range(-1, 2)] if not (s.x == 0 and s.y == 0)]:
        g.generate_section_now(S); yield from built(S)
        g.debug_clear_section(S, 0, g.get_start_room_center()); yield from wait(0.2)
        n_ = str(g.tier_notice)
        if not notices or notices[-1] != n_: notices.append(n_)
    res["notices_tier2"] = notices
    yield from wait(1.0)
    res["tally2"] = tally(2); res["open3"] = g.is_tier_open(3); res["notice3"] = str(g.tier_notice); res["tiers_opened"] = list(g.tiers_opened)
    ok3 = check_opening(3, res)
    res["seconds"] = round(time.time() - t0, 1)
    quiet(False)
    ok = (res["tally1_start"] and not res["open_short"] and res["open_enough"] and res["opened_at_share"] is not None and res["opened_at_share"] >= 0.75
          and (res["last_shut_share"] is None or res["last_shut_share"] < 0.75) and "TIER 2" in res["notice"] and ok2
          and 7 in res["marks_map"] and 8 in res["marks_map"] and res["open3"] and ok3 and any(n_.startswith("TIER 3 IS OPEN") for n_ in res["notices_tier2"]))
    step_result("tiers", ok, ok_tier2=ok2, ok_tier3=ok3, **res)

# ------------------------------------------------------------------------------------------------ the rooms: shapes, themes, furniture
def obb_of(c, t):
    """a mesh's box as built: 2D centre, half sizes, yaw (deg), from the mesh's bounds and the world transform"""
    b = c.static_mesh.get_bounding_box()
    lc = V((b.min.x + b.max.x) / 2, (b.min.y + b.max.y) / 2, (b.min.z + b.max.z) / 2)
    s = t.scale3d; wc = t.transform_location(lc)
    return (wc.x, wc.y, abs((b.max.x - b.min.x) / 2 * s.x), abs((b.max.y - b.min.y) / 2 * s.y), t.rotation.rotator().yaw, wc.z - abs((b.max.z - b.min.z) / 2 * s.z))
def sat(a, b):
    """how far two boxes overlap (the least push that parts them; <= 0: apart)"""
    def axes(o): r = math.radians(o[4]); return [(math.cos(r), math.sin(r)), (-math.sin(r), math.cos(r))]
    def proj(o, ax):
        r = math.radians(o[4]); ux, uy = math.cos(r), math.sin(r); vx, vy = -uy, ux
        c = o[0] * ax[0] + o[1] * ax[1]; e = abs(o[2] * (ux * ax[0] + uy * ax[1])) + abs(o[3] * (vx * ax[0] + vy * ax[1]))
        return c - e, c + e
    best = 1e9
    for ax in axes(a) + axes(b):
        a0, a1 = proj(a, ax); b0, b1 = proj(b, ax); best = min(best, min(a1, b1) - max(a0, b0))
    return best
def furniture(S, g):
    """the furniture and containers of a set of rooms as built: (name, box)"""
    pieces = g.get_editor_property("pieces")
    names = S.get_footprints()[2] if isinstance(S.get_footprints(), tuple) else []
    fp = S.get_footprints(); names = [str(n) for n in fp[2]] if isinstance(fp, tuple) and len(fp) == 3 else []
    meshes = {}
    for n in set(x for x in names if not x.startswith("access:")):
        for key_ in [n] + [f"{t}.{n}" for t in ("Castle", "Dwarf")]:
            p = pieces.get(unreal.Name(key_))
            # (the cells' invisible blockers stand inside their bars, one against the next: not furniture)
            if p and p.mesh and not p.hidden: meshes[p.mesh.get_path_name()] = n
    out = []
    for comp in S.get_components_by_class(unreal.InstancedStaticMeshComponent):
        m = comp.static_mesh
        if not m or m.get_path_name() not in meshes or str(comp.get_collision_profile_name()) == "NoCollision": continue
        for i in range(comp.get_instance_count()):
            t = comp.get_instance_transform(i, True)
            if isinstance(t, tuple): t = t[-1]
            o = obb_of(comp, t)
            if o[5] < 40: out.append((meshes[m.get_path_name()], o))
    # (containers: the body on each container's pivot (the pivot stands where the section says the container is; its lid or
    # doors hang from pivots of their own under it, and doors have pivots too))
    inter = list(S.get_components_by_tag(unreal.StaticMeshComponent, "RDInteractive"))
    for i in range(S.get_num_containers()):
        at = S.get_container_location(i)
        body = None
        for comp in inter:
            par = comp.get_attach_parent()
            if par is None: continue
            pl = par.get_world_location()
            if abs(pl.x - at.x) < 3 and abs(pl.y - at.y) < 3 and par.get_attach_parent() == S.root_component: body = (comp, par); break
        if body is None: continue
        o = obb_of(body[0], body[0].get_world_transform())
        # (a wardrobe's two doors are two containers of one piece: its body once)
        if any(x[0].startswith("container:") and abs(x[1][0] - o[0]) < 5 and abs(x[1][1] - o[1]) < 5 for x in out): continue
        if o[5] < 40: out.append((f"container:{S.get_container_kind(i)}:{i}", o, body[1].get_world_rotation().yaw))
    return out
def step_layout():
    g = G["gen"]; quiet(True)
    secs = [s for s in g.get_section_coords() if g.is_section_generated(s)]
    shapes = {}; shaped_ok = []; theme_meshes = {}; overlaps = []; blocked = []; between_beds = []; n_furn = 0; n_cont = 0
    for sc in secs:
        S = g.get_section(sc); t = g.tier_of(sc)
        for i in range(S.get_num_rooms()):
            sh = str(S.get_room_shape(i))
            if not sh or sh == "rect": continue
            r = S.get_room_tiles(i); tiles, heights = (r[0], r[1]) if isinstance(r, tuple) else (r, [])
            bmin, bmax = S.get_room_bounds(i)
            rect = max(1, round((bmax.x - bmin.x) / 300.0) * round((bmax.y - bmin.y) / 300.0))
            hv = (max(heights) - min(heights)) if heights else 0
            shapes[sh] = shapes.get(sh, 0) + 1
            want_h = sh in ("dome", "pyramid", "step pyramid", "steps")
            shaped_ok.append({"section": [sc.x, sc.y], "room": i, "shape": sh, "tiles": len(tiles), "rect": rect, "height_range": round(hv),
                              "ok": (len(tiles) < rect or sh in ("tall", "dome", "pyramid", "step pyramid")) and (hv > 50 if want_h else True)})
        # (the looks: which packs its walls come from)
        packs = set()
        for comp in S.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if comp.static_mesh: packs.add(comp.static_mesh.get_path_name().split("/")[2])
        theme_meshes[f"{sc.x},{sc.y}"] = {"tier": t, "theme": g.get_theme_name(sc), "castle": "CastleofEternalMist" in packs or "Medieval_Castle" in packs, "dwarf": "DwarvenCitadel" in packs}
        # (furniture as built)
        F = furniture(S, g)
        n_furn += len(F); n_cont += sum(1 for f in F if f[0].startswith("container:"))
        for a in range(len(F)):
            for b in range(a + 1, len(F)):
                d = sat(F[a][1], F[b][1])
                if d > 7.0: overlaps.append({"section": [sc.x, sc.y], "a": F[a][0], "b": F[b][0], "cm": round(d, 1), "at": [round(F[a][1][0]), round(F[a][1][1])]})
        beds = [f for f in F if "bed" in f[0].lower()]
        for f in F:
            if not f[0].startswith("container:"): continue
            o, yaw = f[1], f[2]
            fx, fy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
            # (the way in: 95 cm before its front; its front is the piece's +X)
            # (the box's own axes against the container's: turned a quarter, its Y half is the depth to its front)
            dd = abs(((o[4] - yaw + 90) % 180) - 90)
            depth, half_w = (o[3], o[2]) if dd > 45 else (o[2], o[3])
            way = (o[0] + fx * (depth + 50), o[1] + fy * (depth + 50), 47.0, max(half_w, 45.0), yaw, 0)
            hit = [x[0] for x in F if x is not f and sat(way, x[1]) > 5.0]
            room = S.room_at(V(o[0], o[1], 50)); wroom = S.room_at(V(way[0], way[1], 50))
            if hit or wroom != room:
                # (what the generator recorded near it: its footprints, to set against the meshes as built)
                fp_ = S.get_footprints(); near_ = []
                if isinstance(fp_, tuple) and len(fp_) == 3:
                    for c_, hy_, n_ in zip(*fp_):
                        if math.hypot(c_.x - o[0], c_.y - o[1]) < 400: near_.append([str(n_), round(c_.x), round(c_.y), round(hy_.x), round(hy_.y), round(hy_.z)])
                blocked.append({"section": [sc.x, sc.y], "container": f[0], "blocked_by": hit, "room": room, "way_room": wroom, "box": [round(v) for v in o], "yaw": round(yaw),
                                "way": [round(v) for v in way[:5]], "hits": [[x[0]] + [round(v) for v in x[1][:5]] for x in F if x is not f and sat(way, x[1]) > 5.0], "footprints": near_})
            nb = [bd for bd in beds if math.hypot(bd[1][0] - o[0], bd[1][1] - o[1]) < max(bd[1][2], bd[1][3]) + max(o[2], o[3]) + 30]
            if len(nb) >= 2:
                xs = sorted([nb[0][1], nb[1][1]], key=lambda q: q[0])
                between_beds.append({"section": [sc.x, sc.y], "container": f[0], "beds": len(nb)})
    # (pictures of shaped rooms: the first of a few shapes, from inside)
    pics = []
    for want in ("circle", "dome", "triangle", "L", "U", "octagon", "step pyramid"):
        x = next((s for s in shaped_ok if s["shape"] == want), None)
        if not x: continue
        S = g.get_section(I2(*x["section"])); ctr = S.get_room_center(x["room"])
        put(ctr, 45.0); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=8, yaw=45)); yield from wait(0.8)
        shot("room_" + want.replace(" ", "_")); pics.append(want); yield from rwait(1.0)
    th_ok = all((v["castle"] if v["theme"] == "Castle" else True) and (v["dwarf"] if v["theme"] == "Dwarf" else True)
                and (not v["castle"] and not v["dwarf"] if v["theme"] == "None" else True) for v in theme_meshes.values())
    quiet(False)
    ok = (len(shapes) >= 6 and all(s["ok"] for s in shaped_ok) and th_ok and not overlaps and not blocked and not between_beds and n_cont > 0)
    step_result("layout", ok, sections=len(secs), shapes=shapes, shaped_bad=[s for s in shaped_ok if not s["ok"]][:20], themes=theme_meshes,
                furniture=n_furn, containers=n_cont, overlaps=overlaps[:30], n_overlaps=len(overlaps), blocked=blocked[:30], n_blocked=len(blocked),
                between_beds=between_beds[:10], pictures=pics)

# ------------------------------------------------------------------------------------------------ traps
def trap_lines():
    out = []
    for l in G["gen"].get_trap_lines():
        p = str(l).split("|")
        out.append({"s": I2(int(p[0]), int(p[1])), "i": int(p[2]), "name": p[3], "kind": p[4], "at": V(float(p[5]), float(p[6]), float(p[7])), "state": int(p[8]), "seen": int(p[9])})
    return out
def step_traps():
    g = G["gen"]; c = cb(); quiet(True)
    if str(g.get_editor_property("current_hero")) != "Warrior": g.switch_hero("Warrior"); yield from wait(0.6); refresh(); c = cb()
    # (tier 3's traps (the chain and the lingering trap are tier 3's): sets of it generated until every kind is there)
    want = {str(d.name) for d in g.get_editor_property("traps")}
    for sc_ in [I2(2, 0), I2(2, 1), I2(2, -1), I2(-2, 0), I2(0, 2)]:
        if want <= {t["name"] for t in trap_lines()} or not g.is_tier_open(3): break
        if not g.is_section_generated(sc_): g.generate_section_now(sc_); yield from built(sc_)
    T = trap_lines(); kinds = sorted({t["name"] for t in T})
    res = {"traps": len(T), "kinds_present": kinds, "by_kind": {}}
    for name in [str(d.name) for d in g.get_editor_property("traps")]:
        cand = [t for t in trap_lines() if t["name"] == name and t["state"] == 0]
        if not cand and g.is_tier_open(3):
            # (its set may have been dropped as she went: tier 3's sets generated again)
            for sc_ in [I2(2, 0), I2(2, 1), I2(2, -1), I2(-2, 0), I2(0, 2)]:
                if not g.is_section_generated(sc_): g.generate_section_now(sc_); yield from built(sc_)
                cand = [t for t in trap_lines() if t["name"] == name and t["state"] == 0]
                if cand: break
        if not cand: res["by_kind"][name] = {"present": False}; continue
        t = cand[0]
        # (a step off it first, on the floor of its own room or hallway, then onto it: it goes off as she steps on, from her hit
        # points as they were)
        S_ = g.get_section(t["s"]); off = None
        for k_ in range(16):
            a_ = k_ * math.pi / 8; q_ = V(t["at"].x + math.cos(a_) * 350, t["at"].y + math.sin(a_) * 350, t["at"].z)
            pth = list(S_.find_path_world(q_, t["at"])) if S_ else []
            if pth and dist2(pth[0], q_) < 120: off = q_; break
        put(off or V(t["at"].x + 400, t["at"].y, t["at"].z), 0.0); yield from wait(0.3)
        mx = c.get_max_health(); c.set_health(mx); h0 = c.get_health()
        hits0 = g.trap_hits; trig0 = g.traps_triggered
        g.set_editor_property("log_traps", True)
        put(t["at"], 0.0); p0 = G["pawn"].get_actor_location(); held = False; low = h0
        t0 = now()
        while now() - t0 < 4.0:
            held = held or c.is_held(); low = min(low, c.get_health()); yield
        p1 = G["pawn"].get_actor_location(); st = [x for x in trap_lines() if x["s"] == t["s"] and x["i"] == t["i"]]
        res["by_kind"][name] = {"present": True, "kind": t["kind"], "hp_lost": round(h0 - low, 1), "held": held, "moved_m": round(dist2(p0, p1) / 100, 1),
                                "hits": g.trap_hits - hits0, "triggered": g.traps_triggered - trig0, "state": st[0]["state"] if st else None, "says": str(c.message)}
        c.set_health(mx); g.set_editor_property("log_traps", False); yield from wait(0.3)
    # (who sees them: the Warrior none; the Rogue within range, and she disarms one)
    T = trap_lines(); fresh = [t for t in T if t["state"] == 0]
    res["warrior_seen"] = sum(t["seen"] for t in T)
    g.switch_hero("Rogue"); yield from wait(0.6); refresh(); c = cb(); g.set_editor_property("disarm_chance", 1.0)
    t = fresh[0] if fresh else None; r = {}
    if t:
        S = g.get_section(t["s"]); q = None
        for k in range(16):
            a = k * math.pi / 8; cand = V(t["at"].x + math.cos(a) * 500, t["at"].y + math.sin(a) * 500, t["at"].z)
            if S.room_at(cand) >= 0 or S.room_at(t["at"]) < 0: q = cand; break
        put(q or V(t["at"].x + 500, t["at"].y, t["at"].z), None); yield from wait(1.0)
        r["seen_from_5m"] = [x for x in trap_lines() if x["s"] == t["s"] and x["i"] == t["i"]][0]["seen"]
        r["marks"] = yield from map_marks(False)
        a = math.atan2(q.y - t["at"].y, q.x - t["at"].x) if q else 0.0
        put(V(t["at"].x + math.cos(a) * 150, t["at"].y + math.sin(a) * 150, t["at"].z), math.degrees(a) + 180); yield from wait(0.3)
        r["describe"] = str(g.describe_nearest(G["pawn"].get_actor_location(), 260.0))
        r["f"] = str(g.interact_nearest(G["pawn"].get_actor_location(), 260.0)); yield from wait(0.3)
        r["progress"] = round(g.get_disarm_progress(), 2)
        yield from wait(g.disarm_seconds + 0.8)
        r["state_after"] = [x for x in trap_lines() if x["s"] == t["s"] and x["i"] == t["i"]][0]["state"]; r["disarmed"] = g.traps_disarmed; r["says"] = str(c.message)
        shot("trap_rogue")
        yield from rwait(0.8)
    res["rogue"] = r
    g.set_editor_property("disarm_chance", 0.85)
    g.switch_hero("Warrior"); yield from wait(0.6); refresh(); quiet(False)
    bk = res["by_kind"]
    DAMAGING = ("Pit", "Darts", "Deadfall", "Crusher", "Glyph", "Ward", "Emanation", "Cursed", "Chain", "Lingering")
    kind_ok = {n: (v.get("present") and ((v["hp_lost"] > 0) if n in DAMAGING else True) and (v["held"] if n in ("Snare", "Pit", "Chain") else True)
                   and (v["moved_m"] > 4 if n == "Teleport" else True)) for n, v in bk.items()}
    res["kind_ok"] = kind_ok
    ok = (all(kind_ok.values()) and len(kind_ok) == 12 and res["warrior_seen"] == 0 and r.get("seen_from_5m") == 1 and 11 in r.get("marks", [])
          and r.get("f") and r.get("progress", 0) > 0 and r.get("state_after") == 3)
    step_result("traps", ok, **res)

# ------------------------------------------------------------------------------------------------ teleporters
def step_teleport():
    g = G["gen"]; c = cb(); quiet(True)
    pads = {int(k): v for k, v in g.pads.items()}
    acts = {a.tier: a for a in GS.get_all_actors_of_class(G["w"], unreal.RDTeleporter)}
    res = {"pads": sorted(pads), "pad_actors": sorted(acts), "ring_on_2": acts[2].has_ring() if 2 in acts else None}
    if 2 not in pads or 1 not in pads:
        step_result("teleport", False, **res); quiet(False); return
    ring = next((str(i.name) for i in items_of(unreal.RDItemKind.TELEPORT) if i.teleport_tier == 2), None)
    put(pads[2], 0.0); yield from wait(0.5)
    # (its set of rooms may have been dropped: generated again as she comes, its pad with it)
    t0 = time.time()
    while 2 not in acts and time.time() - t0 < 20:
        yield from wait(0.3); acts = {a.tier: a for a in GS.get_all_actors_of_class(G["w"], unreal.RDTeleporter)}
    res["ring_on_2"] = acts[2].has_ring() if 2 in acts else None
    put(pads[2], 0.0); yield from wait(0.6)          # (again, on the pad of the set as built now)
    res["describe_2"] = str(g.describe_nearest(G["pawn"].get_actor_location(), 260.0))
    res["f_2"] = str(g.interact_nearest(G["pawn"].get_actor_location(), 260.0)); yield from wait(0.5)
    res["ring"] = ring; res["ring_count"] = c.get_item_count(ring); res["ring_on_2_after"] = acts[2].has_ring()
    shot("pad_tier2")
    yield from rwait(0.6)
    res["used"] = c.use_item(ring); yield from wait(1.0)
    res["after_ring_to_pad1_m"] = round(dist2(G["pawn"].get_actor_location(), pads[1]) / 100, 2)
    res["destinations"] = list(g.get_pad_destinations())
    res["f_1"] = str(g.interact_nearest(G["pawn"].get_actor_location(), 260.0)); yield from wait(1.0)
    res["after_pad1_to_pad2_m"] = round(dist2(G["pawn"].get_actor_location(), pads[2]) / 100, 2)
    res["f_2b"] = str(g.interact_nearest(G["pawn"].get_actor_location(), 260.0)); yield from wait(1.0)
    res["back_to_pad1_m"] = round(dist2(G["pawn"].get_actor_location(), pads[1]) / 100, 2)
    res["teleports"] = g.teleports
    quiet(False)
    ok = (res["ring_on_2"] and res["ring_count"] == 1 and not res["ring_on_2_after"] and res["used"] and res["after_ring_to_pad1_m"] < 3
          and 2 in res["destinations"] and res["after_pad1_to_pad2_m"] < 3 and res["back_to_pad1_m"] < 3)
    step_result("teleport", ok, **res)

# ------------------------------------------------------------------------------------------------ prison cells
def cells():
    out = []
    g = G["gen"]
    for sc in g.get_section_coords():
        if not g.is_section_generated(sc): continue
        S = g.get_section(sc)
        for l in S.get_cell_lines():
            p = str(l).split("|")
            out.append({"s": sc, "cell": int(p[0]), "door": int(p[1]), "occ": int(p[2]), "opened": int(p[3]), "at": V(float(p[4]), float(p[5]), float(p[6])),
                        "who": int(p[7]), "who_at": V(float(p[8]), float(p[9]), float(p[10]))})
    return out
def step_cells():
    g = G["gen"]; c = cb()
    C = cells(); res = {"cells": len(C), "prisoners": sum(1 for x in C if x["occ"] == 1), "monsters": sum(1 for x in C if x["occ"] == 2), "empty": sum(1 for x in C if x["occ"] == 0)}
    pr = next((x for x in C if x["occ"] == 1 and not x["opened"]), None)
    if pr:
        quiet(True)
        S = g.get_section(pr["s"]); door = S.get_door_location(pr["door"])
        a = math.atan2(door.y - pr["at"].y, door.x - pr["at"].x)
        put(V(door.x + math.cos(a) * 90, door.y + math.sin(a) * 90, door.z), math.degrees(a) + 180); yield from wait(0.5)
        r = {"describe": str(g.describe_nearest(G["pawn"].get_actor_location(), 260.0))}
        n0 = len(lines(c)); f0 = g.prisoners_freed
        shot("cell_prisoner_before"); yield from rwait(0.6)
        r["f"] = str(g.interact_nearest(G["pawn"].get_actor_location(), 260.0)); yield from wait(1.0)
        r["freed"] = g.prisoners_freed - f0; r["says"] = str(c.message); r["found"] = str(g.last_found)
        r["carried_more"] = len(lines(c)) - n0
        yield from wait(2.5); shot("cell_prisoner_out"); yield from rwait(0.6)
        yield from wait(9.0)
        after = [x for x in cells() if x["s"] == pr["s"] and x["cell"] == pr["cell"]][0]
        r["gone"] = after["who"] == 0; r["door_open"] = S.get_door_open_alpha(pr["door"]) > 0.5
        res["prisoner"] = r; quiet(False)
    mo = next((x for x in C if x["occ"] == 2 and not x["opened"]), None)
    if mo:
        a0 = g.get_editor_property("aggro_distance")
        S = g.get_section(mo["s"]); door = S.get_door_location(mo["door"])
        a = math.atan2(door.y - mo["at"].y, door.x - mo["at"].x)
        mon = sorted([m for m in g.get_monsters() if alive(m) and m.caged and dist2(m.get_actor_location(), mo["who_at"]) < 60], key=lambda m: dist2(m.get_actor_location(), mo["who_at"]))
        r = {"caged_before": bool(mon)}
        b0 = g.cell_breakouts
        put(V(door.x + math.cos(a) * 600, door.y + math.sin(a) * 600, door.z), math.degrees(a) + 180); yield from wait(0.5)
        r["opened_far"] = g.cell_breakouts - b0
        # (then nearer: 2.5 m from the door, about 4 m from the cell's middle)
        put(V(door.x + math.cos(a) * 250, door.y + math.sin(a) * 250, door.z), math.degrees(a) + 180)
        c.set_health(c.get_max_health()); h0 = c.get_health(); d0 = dist2(mon[0].get_actor_location(), G["pawn"].get_actor_location()) if mon else None
        yield from wait(5.0)
        r["breakouts"] = g.cell_breakouts - b0; r["caged_after"] = bool(mon) and mon[0].caged
        r["came_m"] = round((d0 - dist2(mon[0].get_actor_location(), G["pawn"].get_actor_location())) / 100, 1) if mon and alive(mon[0]) else None
        r["hp_lost"] = round(h0 - c.get_health(), 1)
        shot("cell_monster"); yield from rwait(0.6)
        for m in mon:
            try: m.set_actor_location(V(0, 0, -50000), False, True)
            except Exception: pass
        c.set_health(c.get_max_health())
        res["monster"] = r
    p_, m_ = res.get("prisoner", {}), res.get("monster", {})
    ok = (bool(pr) and bool(mo) and p_.get("freed") == 1 and p_.get("carried_more", 0) >= 1 and "thanks" in p_.get("says", "") and p_.get("gone")
          and m_.get("caged_before") and m_.get("opened_far") == 0 and m_.get("breakouts") == 1 and not m_.get("caged_after") and ((m_.get("came_m") or 0) > 0.5 or m_.get("hp_lost", 0) > 0))
    step_result("cells", ok, **res)

# ------------------------------------------------------------------------------------------------ her things where she falls
def step_death():
    c = yield from restart("Warrior"); g = G["gen"]; quiet(True)
    ctr = g.get_start_room_center(); spot = V(ctr.x + 600, ctr.y + 300, ctr.z)
    put(spot, 0.0); yield from wait(0.5)
    give = ["Kite Shield", "Small Healing Potion", "Iron Ingot"]
    arm = str(items_of(unreal.RDItemKind.ARMOUR)[0].name); give.append(arm)
    wpn = next((str(i.name) for i in items_of(unreal.RDItemKind.WEAPON) if any(str(f.hero) == "Warrior" for f in i.weapon_fits)), None)
    if wpn: give.append(wpn)
    for n in give: c.add_item(n, 1)
    yield from wait(0.3)
    before = sorted(lines(c)); res = {"gave": give, "lines_before": len(before)}
    # (a blow just past her hit points, as a monster's: one of a million also broke her shield, which takes its share first)
    c.apply_damage(c.get_health() / max(1.0 - c.get_shield_share(), 0.1) + 5.0, None); yield from wait(1.5)
    piles = [p for p in g.loot_piles if p]
    res["dead"] = c.is_dead(); res["piles"] = len(piles)
    if piles:
        p = piles[0]
        res["pile"] = {"things": [str(x) for x in p.things], "pictures": p.pictures, "particles": p.get_effect_particles(), "from_her_m": round(dist2(p.get_actor_location(), spot) / 100, 2)}
    def have(n): return c.get_item_count(n) + sum(1 for d in g.get_editor_property("weapons") if str(d.item) == n)
    res["carried_after"] = {n: have(n) for n in give + ["Heater Shield"]}
    res["marks"] = yield from map_marks(False)
    shot("death_pile")
    yield from rwait(0.8)
    t0 = time.time()
    while c.is_dead() and time.time() - t0 < 20: yield
    yield from wait(1.0)
    res["revived"] = not c.is_dead(); res["where_after_m"] = round(dist2(G["pawn"].get_actor_location(), spot) / 100, 1)
    if piles:
        put(piles[0].get_actor_location(), 0.0); yield from wait(0.4)
        res["describe"] = str(g.describe_nearest(G["pawn"].get_actor_location(), 260.0))
        res["f"] = str(g.interact_nearest(G["pawn"].get_actor_location(), 260.0)); yield from wait(0.4)
        res["carried_back"] = {n: have(n) for n in give}
        res["piles_after"] = len([p for p in g.loot_piles if p])
    quiet(False)
    pl = res.get("pile", {})
    ok = (res["dead"] and res["piles"] == 1 and sorted(pl.get("things", [])) == sorted(give) and pl.get("pictures", 0) >= len(give) and pl.get("particles", 0) > 0
          and pl.get("from_her_m", 9) < 1.5 and all(res["carried_after"][n] == 0 for n in give) and res["carried_after"]["Heater Shield"] == 1
          and 9 in res["marks"] and res["revived"] and res.get("f") == "loot" and all(v == 1 for v in res.get("carried_back", {"x": 0}).values())
          and res.get("piles_after") == 0)
    step_result("death", ok, **res)

STEPS = {"basics": step_basics, "shields": step_shields, "torch": step_torch, "armour": step_armour, "inventory": step_inventory, "open": step_open,
         "heights": step_heights, "tiers": step_tiers, "layout": step_layout, "traps": step_traps, "teleport": step_teleport, "cells": step_cells,
         "death": step_death}
def run():
    for s in PLAN:
        try:
            yield from STEPS[s]()
        except Exception as e:
            import traceback
            step_result(s, False, error=str(e), trace=traceback.format_exc()[-1500:])
            try: quiet(False)
            except Exception: pass
        yield from rwait(0.3)
def finish(err=None):
    unreal.unregister_slate_post_tick_callback(G["h"])
    R["error"] = err
    try:
        c = cb() if G.get("gen") else None
        if c: c.set_scripted_only(False); c.set_inventory_open(False); c.set_crafting_open(False)
        if G.get("gen"): quiet(False)
    except Exception as e: R["error"] = (err or "") + " / " + str(e)
    os.makedirs(OUT, exist_ok=True); json.dump(R, open(os.path.join(OUT, f"test_{TAG}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    ok = not R.get("error") and len(R["steps"]) == len(PLAN) and all(s["ok"] for s in R["steps"])
    unreal.log(f"MWTEST done | {TAG} | {'ok' if ok else 'FAILED'} | " + " | ".join(f"{s['step']} {'ok' if s['ok'] else 'FAILED'}" for s in R["steps"]) + f" | {R.get('error') or ''}")
    G.clear()
def tick(dt):
    try:
        if UES.get_game_world() is None: finish("PIE ended"); return
        next(G["gen_"])
    except StopIteration: finish()
    except Exception as e:
        import traceback
        unreal.log_error("MWTEST error: " + str(e) + traceback.format_exc()); finish(str(e))
G["gen_"] = run()
G["h"] = unreal.register_slate_post_tick_callback(tick)
print("mistward test armed:", PLAN, TAG)
