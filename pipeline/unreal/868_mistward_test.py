"""mistward_castle test (play-in-editor; 868_mistward_test.ps1 starts it). The rules of docs/improvements.txt, measured in play.
Steps (plan, comma separated):
  menu     (alone, in mistward_castle_select: the ps1's plan "menu") the pointer shown; clicks on a hero's name, the arrows,
           her name again (starts) and START, sent as the mouse sends them (Slate): START opens mistward_castle as the hero
           chosen, the pointer hidden there
  basics   the level is "Mistward Castle" with five tiers; the frame rate is measured and shown in the upper left corner (where
           the HUD drew it, and a picture); the anvil's lists are alphabetical (recipes, then what she can break down: four
           shields and hers); the Plate Knight's Sword is a tier 2
           find; the tiers' looks: tier 1 the stone dungeon, tier 2 the castle keep, tier 3 the dwarven halls, tiers 4 and 5
           mixed (more than one look among their sets of rooms)
  shields  the Warrior starts with the Heater Shield on her arm with her sword; a blow takes the shield's share (damage x 4 %)
           less, and the shield loses what it took; she moves (10 - speed) x 3 % slower with it than without; two Kite Shields
           carried as two (one spare); put on, taken off; at the anvil a carried one breaks down into the table's materials, the
           one she wears (the last of its kind) is refused; the Mage cannot wear one
  torch    made at the anvil from 2 wood, 2 straw rope and 1 oils (used up); held in the left hand by each of the four heroes:
           the torch on her left hand bone with her hand on its shaft (within 12 cm), its light on at its head, the shield is not in her hand while it burns; put out, the shield
           is back; a picture in a dark place, and its light measured: the picture round her 5 % brighter lit than put out
  armour   two of one armour set are carried as two (one spare, each with its own durability); one breaks down at the anvil
           into the table's materials, the worn one (the last) is refused
  inventory with 40 kinds in her pack, input sent as the devices send it (Slate, the viewport): holding S walks the cursor
           down (more than 8 lines in 1.5 s), W back up, the gamepad's D-pad the same; the pointer shown while it is open: moved
           onto a potion's row it chooses it, a click uses it, the wheel scrolls the list (the cursor stays); hidden when closed
  open     a chest opened with F stays open: F again does not close it, F no longer offers it; its set of rooms built again
           (one generated in play: after "tiers") builds it open
  heights  every monster kind spawned and measured for 6 s as it idles and wanders (16 samples: legs, wings and clips move
           the body): the lowest point of its drawn body comes down to the floor (within 5 cm) and never sinks more than 5
           cm under it (the Insect hovers in its idle)
           (Half Creature 05 among them: it was drawn 6 to 54 cm under the floor)
  tiers    the 50 % rule (75 % until 2026-10-27): tier 1's rooms, monsters and chests counted (the census); the start set's
           rooms explored and chests looted, its monsters killed one at a time: tier 2 stays shut under 50 % and opens at the
           kill that reaches it
           ("TIER 2 IS OPEN"). Then: a boss (the
           tier's strongest kind, about BossHealth x its hit points, bigger) and 3 to 6 tier-2 monsters in an explored room of
           tier 1 that is not hers; a guarded ring (her kind: the Warrior's HP ring 1 or 2) put first in a container of an
           explored room with 4 guards; the minimap and the big map draw both marks. Tier 2's eight sets cleared: tier 3 opens
           with its own boss and ring
  layout   in every generated set of rooms: shaped rooms (their tiles not their whole rectangle; a dome, a pyramid or a tall
           room's ceiling heights vary), many shapes; the themes' meshes (castle pieces in tier 2, dwarven in tier 3, none in
           tier 1); no two pieces of furniture or containers overlap (their meshes' boxes as built; 1.5 cm allowed: the
           generator sets pieces side by side 0.5 cm under their sizes; it was 3 cm and 7 allowed until 2026-10-27); before
           every container a clear way in (95 cm) on its room's floor, and no container between beds; pictures of shaped rooms
           and of tier 1's barracks; rooms of many sizes (small chambers, long galleries, the largest); no hay mound in any
           cell; shields in containers, each of its tier's ranks
  traps    each kind set off on her (she steps on it): the damaging ones take hit points, the snare and the pit hold her;
           the curse weakens, the emanation slows, the ward throws her back, the chain holds her before it strikes (more
           than once), the lingering trap's worst blow comes after its first, the magic ones' effects have live particles;
           the teleport trap carries her into another room and the spring plate (directional) along hers, each into monsters
           or glyphs; the Warrior sees no trap; the Rogue sees one within range (the map marks it) and disarms it with F
           (DisarmChance 1 for the test)
  teleport the great hall's pad and tier 2's first set's pad with its ring; F on tier 2's pad takes the ring; the ring used
           carries her to the great hall's pad; F there carries her to tier 2's pad, F there back; tier 3's ring taken
           from its pad carries her to the great hall's pad, which then offers tier 3
  cells    a prisoner's cell opened with F: the prisoner thanks her, gives her a thing of the tier and walks off, gone after a
           while; a monster's cell: it opens when she comes near and the monster comes out and strikes her
  death    the Warrior with things found (more than twelve kinds) falls: a pile where she fell with all of them and her own
           shield (a picture for each, the Loot Drops effect alive, the map's mark), her pack empty; back on her feet, F at
           the pile gives them back, the shield on her arm again
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
G["probe_cells"] = TAG.startswith("probe")          # (a tag "probe...": the cells step also shoots the monster's cell from in front)
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
    # (where the HUD drew the frame rate in normal play: the upper left corner, over the controls)
    fb = G["pc"].get_hud().get_fps_box(); res["fps_box"] = [round(fb.x), round(fb.y), round(fb.z), round(fb.w)]
    shot("hud_fps")
    # (things to break down, several of them, so that the anvil's second list has an order to keep)
    for n in ("Kite Shield", "Dock Shield", "Beast Shield", "Eastern Shield"): c.add_item(n, 1)
    c.set_crafting_open(True); yield from rwait(0.3)
    cl = [str(x).split("|") for x in c.get_craft_lines()]; c.set_crafting_open(False)
    rec = [x[1] for x in cl if x[0] == "recipe"]; bd = [x[1] for x in cl if x[0] == "breakdown"]
    res["recipes"] = rec; res["recipes_sorted"] = rec == sorted(rec, key=lambda s: s.lower())
    res["breakdowns"] = bd; res["breakdowns_sorted"] = len(bd) >= 4 and bd == sorted(bd, key=lambda s: s.lower())
    pk = [i for i in g.get_editor_property("items") if str(i.name) == "Plate Knight's Sword"]
    res["plate_knight_tiers"] = list(pk[0].tiers) if pk else None
    # (the looks: tier 1 the start (0, 0), tier 2 ring 1, tier 3 ring 2; tiers 4 and 5 every set of their rings)
    res["themes"] = {1: g.get_theme_name(I2(0, 0)), 2: g.get_theme_name(I2(1, 0)), 3: g.get_theme_name(I2(2, 0))}
    for t, r in ((4, 3), (5, 4)):
        res["themes"][t] = sorted({g.get_theme_name(I2(x, y)) for x in range(-r, r + 1) for y in range(-r, r + 1) if max(abs(x), abs(y)) == r})
    quiet(False)
    fbx = res["fps_box"]
    ok = (res["title"] == "Mistward Castle" and res["max_tier"] == 5 and res["show_fps"] and 5 < res["fps"] < 400 and res["recipes_sorted"]
          and res["breakdowns_sorted"] and fbx[2] > fbx[0] + 100 and fbx[0] < 80 and fbx[1] < 80
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
SHOTS = r"E:\code\claude-ue5\claude_ue5\Saved\Screenshots\WindowsEditor"
def png_luma(path, box=(0.3, 0.35, 0.7, 0.95)):
    """the mean brightness (0-255, Rec. 709) of a part of a PNG (fractions of its width and height), read here with zlib: the
    editor's Python has no image library"""
    import zlib, struct
    data = open(path, "rb").read(); pos = 8; w = h = 0; ct = 6; idat = b""
    while pos < len(data):
        ln, typ = struct.unpack(">I4s", data[pos:pos + 8]); body = data[pos + 8:pos + 8 + ln]; pos += 12 + ln
        if typ == b"IHDR": w, h, bd, ct = struct.unpack(">IIBB", body[:10])
        elif typ == b"IDAT": idat += body
    bpp = 4 if ct == 6 else 3; raw = zlib.decompress(idat); stride = w * bpp
    prev = bytearray(stride); x0, y0, x1, y1 = int(box[0] * w), int(box[1] * h), int(box[2] * w), int(box[3] * h)
    tot = 0.0; n = 0
    for y in range(h):
        f = raw[y * (stride + 1)]; line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        if f == 1:
            for i in range(bpp, stride): line[i] = (line[i] + line[i - bpp]) & 255
        elif f == 2:
            for i in range(stride): line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride): line[i] = (line[i] + (((line[i - bpp] if i >= bpp else 0) + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0; b = prev[i]; c_ = prev[i - bpp] if i >= bpp else 0
                p = a + b - c_; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c_)
                line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c_)) & 255
        if y0 <= y < y1:
            for x in range(x0, x1, 2):
                i = x * bpp; tot += 0.2126 * line[i] + 0.7152 * line[i + 1] + 0.0722 * line[i + 2]; n += 1
        prev = line
    return round(tot / max(n, 1), 2)
def shot_luma(name):
    """a small picture of the game now, and its brightness round her (none: the picture did not come)"""
    p = os.path.join(SHOTS, f"mw_{TAG}_{name}.png")
    if os.path.exists(p): os.remove(p)
    shot(name, "640x360"); t0 = time.time()
    while time.time() - t0 < 8:
        yield from rwait(0.3)
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            yield from rwait(0.3)
            try: return png_luma(p)
            except Exception: continue
    return None
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
            # (its light measured in the picture: the same view with the torch lit and put out, the brightness round her)
            r["luma_lit"] = yield from shot_luma("torch_lit")
            c.hold_torch(False); yield from wait(0.3)
            r["luma_out"] = yield from shot_luma("torch_out")
            c.hold_torch(True); yield from wait(0.3)
        c.hold_torch(False); yield from wait(0.2)
        r["after_out"] = {"is_held": c.is_torch_held(), "shield_in_hand": c.is_shield_in_hand(), "light_visible": bool(L and L.is_visible())}
        res["heroes"][hero] = r
    g.switch_hero("Warrior"); yield from wait(0.6); refresh(); quiet(False)
    hs = res["heroes"]
    ok = (res["can"] and res["made"] and res["torches"] == 1 and all(v == 0 for v in res["left"].values())
          and all(h["held"] and h["is_held"] and h["light"] > 0 and h["light_visible"] and h["torch_bone"] == "hand_l" and h["hand_to_shaft_cm"] is not None and h["hand_to_shaft_cm"] < 12
                  and h["light_to_hand_cm"] < (h["torch_length_cm"] or 0) + 20
                  and not h["shield_in_hand"] and not h["after_out"]["is_held"] and not h["after_out"]["light_visible"] for h in hs.values())
          and hs["Warrior"]["after_out"]["shield_in_hand"]
          and hs["Warrior"].get("luma_lit") is not None and hs["Warrior"].get("luma_out") is not None and hs["Warrior"]["luma_lit"] > hs["Warrior"]["luma_out"] * 1.05)
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
def rows(c):
    """the inventory's rows as the HUD drew them: index -> (x0, y0, x1, y1)"""
    out = {}
    for l in c.get_list_rows():
        p = str(l).split("|"); out[int(p[0])] = tuple(float(v) for v in p[1:5])
    return out
def mid(b): return unreal.Vector2D((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)
def slate_hold(name, sec):
    """a key held as the device sends it (Slate, the viewport, the player controller), then let go; "" or why it was refused"""
    g = G["gen"]; why = str(g.slate_key(key(name), True))
    if why: return why
    yield from rwait(sec); why = str(g.slate_key(key(name), False)); yield from rwait(0.2)
    return why
def slate_click(p):
    g = G["gen"]; why = str(g.slate_mouse_button(p, key("LeftMouseButton"), True)); yield from rwait(0.08)
    why = why or str(g.slate_mouse_button(p, key("LeftMouseButton"), False)); yield from rwait(0.25)
    return why
def step_inventory():
    # (the keys, the gamepad's D-pad and the mouse sent into Slate as the devices send them: through the game's viewport, as in
    # normal play (the user's of 2026-10-27: held keys did not walk the list for them; the mouse could not point or scroll))
    c = yield from restart("Warrior"); g = G["gen"]
    for it in [i for i in g.get_editor_property("items") if i.kind in (unreal.RDItemKind.COMPONENT, unreal.RDItemKind.HEALING, unreal.RDItemKind.FOOD)][:40]:
        c.add_item(str(it.name), 1)
    c.set_health(c.get_max_health() * 0.5)
    c.set_inventory_open(True); yield from rwait(0.4)
    n = len(lines(c)); res = {"lines": n, "pointer_shown": c.is_pointer_shown(), "cursor_shown": G["pc"].show_mouse_cursor, "refused": []}
    # ---- held keys: the keyboard's S and W, the gamepad's D-pad down and up
    for nm, sec, k in (("S", 1.5, "hold_s"), ("W", 1.0, "hold_w"), ("Gamepad_DPad_Down", 1.5, "hold_dpad_down"), ("Gamepad_DPad_Up", 1.0, "hold_dpad_up")):
        a = c.get_inventory_cursor(); why = yield from slate_hold(nm, sec)
        if why: res["refused"].append(f"{nm}: {why}")
        res[k] = c.get_inventory_cursor() - a
    a = c.get_inventory_cursor(); why = yield from slate_hold("S", 0.1); res["one_press"] = c.get_inventory_cursor() - a
    # ---- the mouse: onto a potion's row (it is chosen), a click on it (it is used), the wheel (the list scrolls, the cursor stays)
    yield from rwait(0.2); R_ = rows(c); L_ = lines(c)
    pot = next((i for i in sorted(R_) if L_[i].startswith("item|") and i != c.get_inventory_cursor()), None)
    res["rows_drawn"] = len(R_); m = {}
    if pot is not None:
        nm = L_[pot].split("|")[1]; b = R_[pot]
        # (a row is chosen when the pointer moves onto it: first somewhere else, a few frames, then onto it)
        why = str(g.slate_mouse_move(unreal.Vector2D(b[0] + 30, b[1] - 60))); yield from rwait(0.25)
        why = why or str(g.slate_mouse_move(mid(b)))
        if why: res["refused"].append("move: " + why)
        yield from rwait(0.3)
        m["row"] = pot; m["item"] = nm; m["chosen_by_pointer"] = c.get_inventory_cursor() == pot
        n0 = c.get_item_count(nm); u0 = c.mouse_uses
        why = yield from slate_click(mid(b))
        if why: res["refused"].append("click: " + why)
        m["used"] = n0 - c.get_item_count(nm); m["mouse_uses"] = c.mouse_uses - u0; m["says"] = str(c.message)
        f0 = c.get_list_first(); k0 = c.get_inventory_cursor()
        for _ in range(2):
            why = str(g.slate_wheel(mid(b), -1.0)); yield from rwait(0.15)
            if why: res["refused"].append("wheel: " + why)
        m["first_before"] = f0; m["first_after_wheel_down"] = c.get_list_first(); m["cursor_kept"] = c.get_inventory_cursor() == k0
        why = str(g.slate_wheel(mid(b), 1.0)); yield from rwait(0.15)
        m["first_after_wheel_up"] = c.get_list_first()
        # (a double click on a row of three small potions: one drunk, not two (the second press of a double click is a press too))
        c.add_item("Small Healing Potion", 3); c.set_health(c.get_max_health() * 0.3); yield from rwait(0.3)
        # (the keys walk the cursor to its row, which brings the wheel-scrolled list back to the cursor)
        want_ = next((i for i, l_ in enumerate(lines(c)) if l_.startswith("item|Small Healing Potion|")), None)
        for _ in range(60):
            if want_ is None or c.get_inventory_cursor() == want_: break
            yield from slate_hold("S" if c.get_inventory_cursor() < want_ else "W", 0.05)
        R2 = rows(c); L2 = lines(c); sp_ = next((i for i in sorted(R2) if L2[i].startswith("item|Small Healing Potion|")), None)
        if sp_ is not None:
            b2 = R2[sp_]; g.slate_mouse_move(unreal.Vector2D(b2[0] + 30, b2[1] - 60)); yield from rwait(0.25)
            g.slate_mouse_move(mid(b2)); yield from rwait(0.3)
            n2 = c.get_item_count("Small Healing Potion"); u2 = c.mouse_uses
            for _ in range(2):
                g.slate_mouse_button(mid(b2), key("LeftMouseButton"), True); yield from rwait(0.05)
                g.slate_mouse_button(mid(b2), key("LeftMouseButton"), False); yield from rwait(0.08)
            yield from rwait(0.3)
            m["double_click_drank"] = n2 - c.get_item_count("Small Healing Potion"); m["double_click_uses"] = c.mouse_uses - u2
    res["mouse"] = m
    shot("inventory_mouse"); yield from rwait(0.6)
    c.set_inventory_open(False); yield from rwait(0.2)
    res["pointer_after_close"] = c.is_pointer_shown(); res["cursor_after_close"] = G["pc"].show_mouse_cursor
    ok = (n > 20 and not res["refused"] and res["pointer_shown"] and res["cursor_shown"] and res["hold_s"] > 8 and res["hold_w"] < -4
          and res["hold_dpad_down"] > 8 and res["hold_dpad_up"] < -4 and res["one_press"] == 1
          and m.get("chosen_by_pointer") and m.get("used") == 1 and m.get("mouse_uses") == 1
          and m.get("first_after_wheel_down", 0) >= m.get("first_before", 0) + 3 and m.get("cursor_kept")
          and m.get("first_after_wheel_up", 99) < m.get("first_after_wheel_down", 0) and m.get("double_click_drank") == 1
          and not res["pointer_after_close"] and not res["cursor_after_close"])
    step_result("inventory", ok, **res)

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

# ------------------------------------------------------------------------------------------------ the tiers: 50 %, the boss, the guarded ring
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
        # (the Magic Potency Ring, as the list names it, whoever she is (until 2026-10-27 her kind: the Warrior's HP ring))
        r["ring_kind_ok"] = rg["name"].startswith("Magic Potency Ring") and rg["name"].endswith((f" {2 * t - 3}", f" {2 * t - 2}"))
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
    # (every planned monster of the start set up and alive first: RestartPlay puts them back over several frames, and the debug
    # clear counts as killed every one not standing (at 1 s only 3 of 14 stood: the first clear made it 11 killed))
    def standing(): return [m for m in g.get_monsters() if alive(m) and m.spawn_index >= 0 and g.world_to_section(m.get_actor_location()) == S0]
    t0 = time.time()
    while len(standing()) < n_mon and time.time() - t0 < 15: yield from wait(0.3)
    res["standing_before"] = len(standing())
    # (the rooms explored and the chests looted, then the monsters killed one at a time (the debug clear leaving fewer
    # each time): tier 2 opens at the first kill that brings the share to the rule's 50 % or more, not before)
    steps_ = []
    for leave in range(n_mon, -1, -1):
        g.debug_clear_section(S0, leave, g.get_start_room_center()); yield from wait(0.3)
        ta = tally(1); op = g.is_tier_open(2)
        steps_.append({"killed": ta["done"][1], "of": ta["all"][1], "share": round(ta["done"][1] / max(ta["all"][1], 1), 3), "open": op})
        if op: break
    res["kills"] = steps_
    shut = [s_ for s_ in steps_ if not s_["open"]]; opened = [s_ for s_ in steps_ if s_["open"]]
    SHARE = res["share"]          # (the level's rule: 0.5 since 2026-10-27, 0.75 before)
    res["open_short"] = any(s_["open"] and s_["share"] < SHARE for s_ in steps_)
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
    ok = (abs(SHARE - 0.5) < 1e-6 and res["tally1_start"] and not res["open_short"] and res["open_enough"] and res["opened_at_share"] is not None
          and res["opened_at_share"] >= SHARE and res["last_shut_share"] is not None and res["last_shut_share"] < SHARE and "TIER 2" in res["notice"] and ok2
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
    shapes = {}; shaped_ok = []; theme_meshes = {}; overlaps = []; blocked = []; between_beds = []; n_furn = 0; n_cont = 0; sizes = []
    # (the cells' hay: the mound read as a big rock in every cell (the user's of 2026-10-27): none in the castle)
    pcs_ = g.get_editor_property("pieces")
    hay_paths = {p.mesh.get_path_name() for p in [pcs_.get(unreal.Name(k)) for k in ("HayPile", "Castle.HayPile", "Dwarf.HayPile")] if p and p.mesh}
    hay_path = next(iter(hay_paths), None); n_hay = 0; shields_found = {}; n_floor = 0; n_no_floor = 0; no_floor = []
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
        # (the rooms' sizes in tiles, junctions left out: small chambers, long galleries, the block's largest)
        for i in range(S.get_num_rooms()):
            kd = str(S.get_room_kind(i))
            if "unction" in kd: continue
            bmin, bmax = S.get_room_bounds(i)
            w_, h_ = round((bmax.x - bmin.x) / 300.0), round((bmax.y - bmin.y) / 300.0)
            sizes.append((min(w_, h_), max(w_, h_), kd, t))
        # (the looks: which packs its walls come from)
        packs = set()
        for comp in S.get_components_by_class(unreal.InstancedStaticMeshComponent):
            if comp.static_mesh: packs.add(comp.static_mesh.get_path_name().split("/")[2])
            if comp.static_mesh and comp.static_mesh.get_path_name() in hay_paths: n_hay += comp.get_instance_count()
        theme_meshes[f"{sc.x},{sc.y}"] = {"tier": t, "theme": g.get_theme_name(sc), "castle": "CastleofEternalMist" in packs or "Medieval_Castle" in packs, "dwarf": "DwarvenCitadel" in packs}
        # (a floor under every room tile, by a trace down at its middle: one of the Dwarven floors was drawn with no collision,
        # and she fell through whole rooms of tier 3)
        for i in range(S.get_num_rooms()):
            r_ = S.get_room_tiles(i); tl_ = r_[0] if isinstance(r_, tuple) else r_
            for p_ in tl_:
                n_floor += 1
                h_ = unreal.SystemLibrary.line_trace_single(G["w"], V(p_.x + 37, p_.y + 23, 250), V(p_.x + 37, p_.y + 23, -400), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [G["pawn"]], unreal.DrawDebugTrace.NONE, True)
                tt_ = h_.to_tuple() if h_ else None
                if not tt_ or tt_[4].z < -60:
                    if len(no_floor) < 30: no_floor.append({"section": [sc.x, sc.y], "room": i, "kind": str(S.get_room_kind(i)), "at": [round(p_.x), round(p_.y)]})
                    n_no_floor += 1
        # (shields in its containers' lists (found as loot, not given by the test), by the set's tier)
        for i in range(S.get_num_containers()):
            for x in g.loot_list_of(sc, i):
                if str(x) in SH: shields_found.setdefault(t, set()).add(str(x))
        # (furniture as built)
        F = furniture(S, g)
        n_furn += len(F); n_cont += sum(1 for f in F if f[0].startswith("container:"))
        for a in range(len(F)):
            for b in range(a + 1, len(F)):
                d = sat(F[a][1], F[b][1])
                if d > 1.5: overlaps.append({"section": [sc.x, sc.y], "a": F[a][0], "b": F[b][0], "cm": round(d, 1), "at": [round(F[a][1][0]), round(F[a][1][1])]})
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
    # (tier 1's barracks, where the beds and their chests stand (the user saw them in each other on level 5): a picture of each
    # of the first two, from inside, looking along the room)
    S0 = g.get_section(I2(0, 0)); nb = 0
    for i in range(S0.get_num_rooms() if S0 else 0):
        if str(S0.get_room_kind(i)) != "Barracks" or nb >= 2: continue
        bmin, bmax = S0.get_room_bounds(i); ctr = S0.get_room_center(i)
        along = 0.0 if (bmax.x - bmin.x) >= (bmax.y - bmin.y) else 90.0
        put(V(ctr.x - math.cos(math.radians(along)) * ((bmax.x - bmin.x) * 0.35), ctr.y - math.sin(math.radians(along)) * ((bmax.y - bmin.y) * 0.35), ctr.z), along)
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-22, yaw=along)); yield from wait(0.8)
        shot(f"tier1_barracks_{nb}"); pics.append(f"tier1_barracks_{nb}"); nb += 1; yield from rwait(1.0)
    th_ok = all((v["castle"] if v["theme"] == "Castle" else True) and (v["dwarf"] if v["theme"] == "Dwarf" else True)
                and (not v["castle"] and not v["dwarf"] if v["theme"] == "None" else True) for v in theme_meshes.values())
    quiet(False)
    small = sum(1 for s in sizes if s[1] <= 4); long_ = sum(1 for s in sizes if s[1] >= 9 and s[0] <= 4); big = sum(1 for s in sizes if s[0] >= 10)
    hist = {}
    for s in sizes: hist[f"{s[0]}x{s[1]}"] = hist.get(f"{s[0]}x{s[1]}", 0) + 1
    ok = (len(shapes) >= 6 and all(s["ok"] for s in shaped_ok) and th_ok and not overlaps and not blocked and not between_beds and n_cont > 0
          and small >= 3 and long_ >= 3 and big >= 3 and n_hay == 0 and hay_path is not None
          and all(SH[n]["rank"] >= {1: 18, 2: 14, 3: 9, 4: 5, 5: 1}[t_] and SH[n]["rank"] <= {1: 22, 2: 17, 3: 13, 4: 8, 5: 4}[t_] for t_, ns in shields_found.items() for n in ns)
          and sum(len(v) for v in shields_found.values()) >= 2 and n_floor > 1000 and n_no_floor == 0)
    step_result("layout", ok, sections=len(secs), shapes=shapes, shaped_bad=[s for s in shaped_ok if not s["ok"]][:20], themes=theme_meshes,
                furniture=n_furn, containers=n_cont, overlaps=overlaps[:30], n_overlaps=len(overlaps), blocked=blocked[:30], n_blocked=len(blocked),
                between_beds=between_beds[:10], pictures=pics, rooms=len(sizes), small_rooms=small, long_galleries=long_, largest_rooms=big,
                sizes=dict(sorted(hist.items(), key=lambda kv: -kv[1])), hay_piles=n_hay, shields_in_containers={k: sorted(v) for k, v in shields_found.items()},
                floor_tiles=n_floor, tiles_without_floor=n_no_floor, without_floor=no_floor)

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
        falls = []
        for t in cand[:2]:
            r_ = yield from trap_trial(name, t, c)
            # (the fall guard moved her (she was below the floor at the trap's spot): said in the record, tried once more on
            # another of its kind. Seen once, on a lingering trap in a built set whose floor traces found no hole)
            if name not in ("Teleport",) and r_["farthest_m"] > 30: falls.append({"at": [round(t["at"].x), round(t["at"].y)], "section": [t["s"].x, t["s"].y], "moved_m": r_["moved_m"]}); continue
            break
        r_["fell_through"] = falls
        res["by_kind"][name] = r_
    # (who sees them: the Warrior none; the Rogue within range, and she disarms one)
    T = trap_lines(); fresh = [t for t in T if t["state"] == 0]
    res["warrior_seen"] = sum(t["seen"] for t in T)
    yield from traps_rogue(res, T, fresh)

def trap_trial(name, t, c):
    """one trap set off on her: what it did, measured every frame"""
    g = G["gen"]
    if True:
        # (its set of rooms built through first: one generated again a moment before had no floor yet, she fell through it and
        # the fall guard put her back 459 m away, the crusher untested)
        yield from built(t["s"])
        # (a step off it first, on the floor of its own room or hallway, then onto it: it goes off as she steps on, from her hit
        # points as they were)
        S_ = g.get_section(t["s"]); off = None
        for k_ in range(16):
            a_ = k_ * math.pi / 8; q_ = V(t["at"].x + math.cos(a_) * 350, t["at"].y + math.sin(a_) * 350, t["at"].z)
            pth = list(S_.find_path_world(q_, t["at"])) if S_ else []
            if pth and dist2(pth[0], q_) < 120: off = q_; break
        for _try in range(3):
            put(off or V(t["at"].x + 400, t["at"].y, t["at"].z), 0.0); yield from wait(0.4)
            if dist2(G["pawn"].get_actor_location(), off or V(t["at"].x + 400, t["at"].y, t["at"].z)) < 150: break      # (she stands there)
            yield from wait(0.6)
        mx = c.get_max_health(); c.set_health(mx); h0 = c.get_health()
        hits0 = g.trap_hits; trig0 = g.traps_triggered
        g.set_editor_property("log_traps", True)
        amb0 = {(s_.x, s_.y): str(g.get_section(s_).last_ambush) for s_ in g.get_section_coords() if g.is_section_generated(s_) and g.get_section(s_)}
        # (onto it facing the way she came from the step off it: a ward throws her back that way, along open floor (faced a
        # fixed way, "back" was often a wall a metre behind her))
        face = math.degrees(math.atan2(t["at"].y - off.y, t["at"].x - off.x)) if off else 0.0
        put(t["at"], face); p0 = G["pawn"].get_actor_location(); held = False; low = h0
        # (what it does to her, sampled every frame: hit points (each drop and when), held, weakened, slowed, how far from where
        # she stood on it, the live particles of the effects round the trap and round her)
        t0 = now(); last = h0; drops = []; t_held = None; weak = 0.0; slow = 0.0; far = 0.0; parts = 0; peak = 0.0
        while now() - t0 < (7.0 if name == "Lingering" else 4.0):
            hp = c.get_health()
            if hp < last - 0.5: drops.append([round(now() - t0, 2), round(last - hp, 1)])
            last = hp; low = min(low, hp)
            if c.is_held() and t_held is None: t_held = round(now() - t0, 2)
            held = held or c.is_held(); weak = max(weak, c.get_weakness()); slow = max(slow, c.get_slowness())
            pl = G["pawn"].get_actor_location(); far = max(far, dist2(pl, p0))
            vv = G["pawn"].get_velocity(); peak = max(peak, math.hypot(vv.x, vv.y))
            parts = max(parts, g.get_particles_near(t["at"], 600.0), g.get_particles_near(pl, 600.0))
            yield
        p1 = G["pawn"].get_actor_location(); st = [x for x in trap_lines() if x["s"] == t["s"] and x["i"] == t["i"]]
        amb = {f"{k[0]},{k[1]}": str(g.get_section(I2(*k)).last_ambush) for k in [(s_.x, s_.y) for s_ in g.get_section_coords() if g.is_section_generated(s_) and g.get_section(s_)]
               if str(g.get_section(I2(*k)).last_ambush) != amb0.get(k, "")}
        r_ = {"present": True, "kind": t["kind"], "hp_lost": round(h0 - low, 1), "held": held, "moved_m": round(dist2(p0, p1) / 100, 1),
                                "farthest_m": round(far / 100, 1), "peak_speed": round(peak), "drops": drops[:12], "held_at": t_held, "weakness": round(weak, 2), "slowness": round(slow, 2),
                                "particles": parts, "ambush": amb, "hits": g.trap_hits - hits0, "triggered": g.traps_triggered - trig0,
                                "state": st[0]["state"] if st else None, "says": str(c.message)}
        # (monsters an ambush brought: away again, they would fight her through the next kinds)
        if amb:
            for m_ in g.get_monsters():
                try:
                    if alive(m_) and not m_.caged and dist2(m_.get_actor_location(), G["pawn"].get_actor_location()) < 2500:
                        m_.set_actor_location(V(0, 0, -50000), False, True); m_.set_actor_tick_enabled(False)
                except Exception: pass
        c.set_health(mx); g.set_editor_property("log_traps", False); yield from wait(0.3)
        return r_

def traps_rogue(res, T, fresh):
    """(the traps step's end) the Rogue sees a trap and disarms it; then every kind's result judged"""
    g = G["gen"]
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
    DAMAGING = ("Pit", "Darts", "Deadfall", "Crusher", "Glyph", "Ward", "Emanation", "Cursed", "Chain", "Lingering", "Spring")
    MAGIC = ("Glyph", "Ward", "Emanation", "Cursed", "Teleport")
    def k_ok(n, v):
        if not v.get("present"): return False
        dr = v.get("drops", [])
        return (((v["hp_lost"] > 0) if n in DAMAGING else True) and (v["held"] if n in ("Snare", "Pit", "Chain") else True)
        # (each kind's own effect, measured)
        and (v["particles"] > 0 if n in MAGIC else True)                                   # (the packs' effects are there)
        and (v["weakness"] > 0 if n == "Cursed" else True) and (v["slowness"] > 0 if n == "Emanation" else True)
        # (thrown back: her speed, which the throw gives her (she stood still on it; she walks at 350 at most); how far depends
        # on what stands behind her: 1.2 to 1.6 m measured)
        and (v["peak_speed"] > 500 if n == "Ward" else True)
        and ((v["held_at"] is not None and dr and v["held_at"] <= dr[0][0] and len(dr) >= 2) if n == "Chain" else True)   # (held first, then struck, more than once)
        and ((len(dr) >= 3 and max(d[1] for d in dr[1:]) > dr[0][1]) if n == "Lingering" else True)                     # (worse the longer she stays)
        and ((v["moved_m"] > 4 and len(v["ambush"]) == 1) if n == "Teleport" else True)    # (carried off, into monsters or glyphs)
        and ((v["farthest_m"] > 2 and len(v["ambush"]) == 1) if n == "Spring" else True))  # (thrown along the room, into monsters or glyphs)
    kind_ok = {n: bool(k_ok(n, v)) for n, v in bk.items()}
    res["kind_ok"] = kind_ok
    ok = (all(kind_ok.values()) and len(kind_ok) == 13 and res["warrior_seen"] == 0 and r.get("seen_from_5m") == 1 and 11 in r.get("marks", [])
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
    # (tier 3's pad and ring as well (the tiers step opened it): its ring taken there carries her back to the first tier's pad,
    # which then offers tier 3)
    r3 = {}
    if g.is_tier_open(3):
        t0 = time.time(); pads = {int(k): v for k, v in g.pads.items()}
        while 3 not in pads and time.time() - t0 < 20:
            yield from wait(0.3); pads = {int(k): v for k, v in g.pads.items()}
        if 3 in pads:
            ring3 = next((str(i.name) for i in items_of(unreal.RDItemKind.TELEPORT) if i.teleport_tier == 3), None)
            put(pads[3], 0.0); yield from wait(0.5)
            t0 = time.time(); acts = {a.tier: a for a in GS.get_all_actors_of_class(G["w"], unreal.RDTeleporter)}
            while 3 not in acts and time.time() - t0 < 20:
                yield from wait(0.3); acts = {a.tier: a for a in GS.get_all_actors_of_class(G["w"], unreal.RDTeleporter)}
            put(pads[3], 0.0); yield from wait(0.6)
            r3["ring_on_3"] = acts[3].has_ring() if 3 in acts else None
            r3["f_3"] = str(g.interact_nearest(G["pawn"].get_actor_location(), 260.0)); yield from wait(0.5)
            r3["ring"] = ring3; r3["ring_count"] = c.get_item_count(ring3) if ring3 else 0
            r3["used"] = c.use_item(ring3) if ring3 else False; yield from wait(1.0)
            r3["after_ring_to_pad1_m"] = round(dist2(G["pawn"].get_actor_location(), pads[1]) / 100, 2)
            r3["destinations"] = list(g.get_pad_destinations())
    res["tier3"] = r3
    quiet(False)
    ok = (res["ring_on_2"] and res["ring_count"] == 1 and not res["ring_on_2_after"] and res["used"] and res["after_ring_to_pad1_m"] < 3
          and 2 in res["destinations"] and res["after_pad1_to_pad2_m"] < 3 and res["back_to_pad1_m"] < 3
          and r3.get("ring_on_3") and r3.get("ring_count") == 1 and r3.get("used") and r3.get("after_ring_to_pad1_m", 99) < 3 and 3 in r3.get("destinations", []))
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
                        "who": int(p[7]), "who_at": V(float(p[8]), float(p[9]), float(p[10])), "yaw": float(p[11])})
    return out
def cell_gap(x, d):
    # (a point d cm out from the cell's door gap, on the line through it; the gap is the door's half of the front, 73 cm to the
    # cell's right of the front's middle: the door's hinge is at the cell's corner, and a line from the cell's middle through
    # the hinge left the room at a row's end (she was put in the void))
    a = math.radians(x["yaw"]); fw = (math.cos(a), math.sin(a)); rt = (-math.sin(a), math.cos(a))
    k = G["gen"].tile_size * 0.5 + d
    return V(x["at"].x + fw[0] * k + rt[0] * 73.0, x["at"].y + fw[1] * k + rt[1] * 73.0, x["at"].z)
def stand_by_cell(x, ds, others):
    # (the first of the distances that is on the floor (she is still there after a moment) and in no other cell)
    for d in ds:
        p = cell_gap(x, d)
        if any(dist2(p, y["at"]) < 170 for y in others): continue
        put(p, x["yaw"] + 180); yield from wait(0.4)
        q = G["pawn"].get_actor_location()
        if dist2(q, p) < 60 and abs(q.z - (p.z + 90)) < 60: return d
    return None
def step_cells():
    g = G["gen"]; c = cb()
    C = cells(); res = {"cells": len(C), "prisoners": sum(1 for x in C if x["occ"] == 1), "monsters": sum(1 for x in C if x["occ"] == 2), "empty": sum(1 for x in C if x["occ"] == 0)}
    # (a prisoner with no caged monster within 6.5 m: one would break out as she frees the prisoner)
    caged = [x for x in C if x["occ"] == 2 and not x["opened"]]
    pr = next((x for x in C if x["occ"] == 1 and not x["opened"] and all(dist2(x["at"], y["at"]) >= 650 for y in caged)),
              next((x for x in C if x["occ"] == 1 and not x["opened"]), None))
    if pr:
        quiet(True)
        S = g.get_section(pr["s"])
        put(cell_gap(pr, 90), pr["yaw"] + 180); yield from wait(0.5)
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
    # (a monster's cell with no other caged monster within 9 m: standing by one cell must not let out its neighbours too)
    C = cells()          # (again: what the prisoner's part let out)
    mons = [x for x in C if x["occ"] == 2 and not x["opened"]]
    mo = next((x for x in mons if all(dist2(x["at"], y["at"]) >= 900 for y in mons if y is not x)), mons[0] if mons else None)
    if mo:
        others = [y for y in C if y is not mo]
        mon = sorted([m for m in g.get_monsters() if alive(m) and m.caged and dist2(m.get_actor_location(), mo["who_at"]) < 60], key=lambda m: dist2(m.get_actor_location(), mo["who_at"]))
        r = {"caged_before": bool(mon), "lonely": all(dist2(mo["at"], y["at"]) >= 900 for y in mons if y is not mo)}
        b0 = g.cell_breakouts
        # (first out of its reach, 5.2 m from the cell's middle: 4 to 4.6 m out from the gap, where there is floor)
        r["far_d"] = yield from stand_by_cell(mo, (460, 430, 400), others)
        r["opened_far"] = g.cell_breakouts - b0
        # (then nearer: 2.5 m out from the gap, about 4 m from the cell's middle)
        r["near_d"] = yield from stand_by_cell(mo, (250, 220, 190), others)
        c.set_health(c.get_max_health()); h0 = c.get_health(); d0 = dist2(mon[0].get_actor_location(), G["pawn"].get_actor_location()) if mon else None
        # (where it goes, in the cell's axes: forward out of the cell, right toward the door's half of the front)
        ya = math.radians(mo["yaw"]); r["track"] = []
        def local(p): dx, dy = p.x - mo["at"].x, p.y - mo["at"].y; return [round(dx * math.cos(ya) + dy * math.sin(ya)), round(-dx * math.sin(ya) + dy * math.cos(ya))]
        for _k in range(10):
            yield from wait(0.5)
            if mon and alive(mon[0]): r["track"].append(local(mon[0].get_actor_location()))
        r["her"] = local(G["pawn"].get_actor_location())
        r["door_alpha"] = round(g.get_section(mo["s"]).get_door_open_alpha(mo["door"]), 2)
        r["breakouts"] = g.cell_breakouts - b0; r["caged_after"] = bool(mon) and mon[0].caged
        r["came_m"] = round((d0 - dist2(mon[0].get_actor_location(), G["pawn"].get_actor_location())) / 100, 1) if mon and alive(mon[0]) else None
        r["hp_lost"] = round(h0 - c.get_health(), 1)
        # (out of its cell: past the front, 1.5 m from the cell's middle; a monster stuck at its bars once struck her through them)
        r["out_of_cell_m"] = round(dist2(mon[0].get_actor_location(), mo["at"]) / 100, 2) if mon and alive(mon[0]) else None
        shot("cell_monster"); yield from rwait(0.6)
        if G.get("probe_cells"):
            # (what stands in the door's gap: a capsule swept from inside the cell out through it)
            def at_local(f, s_, z):
                return V(mo["at"].x + f * math.cos(ya) - s_ * math.sin(ya), mo["at"].y + f * math.sin(ya) + s_ * math.cos(ya), mo["at"].z + z)
            ign = [G["pawn"]] + [m for m in mon]
            for lat in (40, 73, 100):
                hit = unreal.SystemLibrary.capsule_trace_single(G["w"], at_local(108, lat, 95), at_local(300, lat, 95), 38.0, 80.0, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, ign, unreal.DrawDebugTrace.NONE, True)
                if hit:
                    # (BreakHitResult's order: blocking, initial overlap, time, distance, location, impact point, normal, impact
                    # normal, material, actor, component, ...)
                    t = hit.to_tuple(); comp = t[10]
                    r["gap_%d" % lat] = {"x": local(t[4])[0], "initial": bool(t[1]), "actor": str(t[9].get_name()) if t[9] else None,
                                         "comp": str(comp.get_name()) if comp else None,
                                         "mesh": str(comp.get_editor_property("static_mesh").get_name()) if comp and isinstance(comp, unreal.StaticMeshComponent) and comp.get_editor_property("static_mesh") else None}
                else: r["gap_%d" % lat] = None
            # (what overlaps a 30 cm capsule along the way out through the gap)
            ov = {}
            for f in (60, 90, 120, 150, 180):
                comps = unreal.SystemLibrary.capsule_overlap_components(G["w"], at_local(f, 73, 95), 30.0, 80.0, [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1, unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2], None, ign)
                if isinstance(comps, tuple): comps = comps[-1]
                names = []
                for cp in (comps or []):
                    nm = cp.get_name()
                    if isinstance(cp, unreal.StaticMeshComponent) and cp.get_editor_property("static_mesh"): nm += ":" + cp.get_editor_property("static_mesh").get_name()
                    if isinstance(cp, unreal.InstancedStaticMeshComponent):
                        try:
                            for ii in list(cp.get_instances_overlapping_sphere(at_local(f, 73, 95), 30.0, True))[:2]:
                                tr = cp.get_instance_transform(ii, True)
                                if isinstance(tr, tuple): tr = tr[-1]
                                lp = local(tr.translation); sc_ = tr.scale3d
                                nm += " @(%d,%d) yaw %.0f scale (%.2f,%.2f,%.2f)" % (lp[0], lp[1], tr.rotation.rotator().yaw - mo["yaw"], sc_.x, sc_.y, sc_.z)
                        except Exception as e_: nm += " (" + str(e_)[:80] + ")"
                    names.append(nm)
                ov[str(f)] = names
            r["overlaps_73"] = ov
            # (a look at the cell from in front, with the monsters quiet)
            quiet(True); yield from stand_by_cell(mo, (330, 300, 270), others); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-25, yaw=mo["yaw"] + 180))
            yield from wait(0.5); shot("cell_monster_front"); yield from rwait(0.6); quiet(False)
        for m in mon:
            try: m.set_actor_location(V(0, 0, -50000), False, True)
            except Exception: pass
        c.set_health(c.get_max_health())
        res["monster"] = r
    p_, m_ = res.get("prisoner", {}), res.get("monster", {})
    ok = (bool(pr) and bool(mo) and p_.get("freed") == 1 and p_.get("carried_more", 0) >= 1 and "thanks" in p_.get("says", "") and p_.get("gone")
          and m_.get("caged_before") and m_.get("opened_far") == 0 and m_.get("breakouts") == 1 and not m_.get("caged_after")
          and m_.get("near_d") is not None and (m_.get("out_of_cell_m") or 0) > 1.6 and (m_.get("hp_lost") or 0) > 0)       # (out, and it struck her)
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
    # (more kinds than one ring of twelve pictures holds: every one is shown)
    give += [str(i.name) for i in items_of(unreal.RDItemKind.COMPONENT)[:11] if str(i.name) not in give]
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
        res["carried_back"] = {n: have(n) for n in give + ["Heater Shield"]}
        res["shield_worn_again"] = str(c.get_worn_shield())
        res["piles_after"] = len([p for p in g.loot_piles if p])
    quiet(False)
    pl = res.get("pile", {})
    # (all of her equipment drops (the list's words): the shield she started with too; her hero's own weapons are not items)
    want = sorted(give + ["Heater Shield"])
    ok = (res["dead"] and res["piles"] == 1 and sorted(pl.get("things", [])) == want and pl.get("pictures", 0) >= len(want) and len(want) > 12
          and pl.get("particles", 0) > 0 and pl.get("from_her_m", 9) < 1.5 and all(v == 0 for v in res["carried_after"].values())
          and 9 in res["marks"] and res["revived"] and res.get("f") == "loot" and all(v == 1 for v in res.get("carried_back", {"x": 0}).values())
          and res.get("shield_worn_again") == "Heater Shield" and res.get("piles_after") == 0)
    step_result("death", ok, **res)

# ------------------------------------------------------------------------------------------------ the hero menu with the mouse
def step_menu():
    """(play in mistward_castle_select: 868_mistward_test.ps1 menu <tag>) the pointer shown and free; a click on a hero's name
    shows her, the arrows step, her name clicked again starts; START clicked opens mistward_castle as the hero shown, where
    the pointer is hidden again"""
    w = G["w"]; s = (GS.get_all_actors_of_class(w, unreal.RDHeroSelect) or [None])[0]
    assert s, "open mistward_castle_select for the menu step"
    s.set_editor_property("stay_on_confirm", True); yield from rwait(1.0)
    def buttons(): return {str(l).split("|")[0]: tuple(float(v) for v in str(l).split("|")[1:5]) for l in s.get_buttons()}
    def click(name):
        b = buttons().get(name)
        if not b: return f"no button {name}"
        why = str(s.slate_mouse_move(unreal.Vector2D(b[0] - 40, b[1] - 40))); yield from rwait(0.15)
        why = why or str(s.slate_mouse_move(mid(b))); yield from rwait(0.15)
        why = why or str(s.slate_mouse_button(mid(b), key("LeftMouseButton"), True)); yield from rwait(0.1)
        why = why or str(s.slate_mouse_button(mid(b), key("LeftMouseButton"), False)); yield from rwait(0.4)
        return why
    res = {"mouse_ui": s.mouse_ui, "cursor_shown": G["pc"].show_mouse_cursor, "buttons": sorted(buttons()), "refused": []}
    seq = []
    for nm in ("Hero_2", "Next", "Prev", "Hero_0"):
        why = yield from click(nm)
        if why: res["refused"].append(f"{nm}: {why}")
        seq.append([nm, s.get_index(), str(s.get_hero_name()), s.is_figure_shown(s.get_index())])
    res["clicks"] = seq; res["opened_before"] = str(s.opened)
    why = yield from click("Hero_0")          # (her name again: start as her)
    if why: res["refused"].append("again: " + why)
    res["opened_by_name_again"] = str(s.opened)
    shot("menu_mouse"); yield from rwait(0.8)
    # (START for real: the dungeon opens as the hero shown (the Rogue, chosen with the pointer))
    why = yield from click("Hero_3")
    if why: res["refused"].append("rogue: " + why)
    s.set_editor_property("stay_on_confirm", False)
    b = buttons().get("Start"); res["start_button"] = bool(b)
    if b:
        s.slate_mouse_move(mid(b)); yield from rwait(0.15)
        G["travel_until"] = time.time() + 30
        s.slate_mouse_button(mid(b), key("LeftMouseButton"), True)
        t0 = time.time()
        while time.time() - t0 < 30:
            yield from rwait(0.5)
            gw = UES.get_game_world()
            if gw and gw.get_name().endswith("mistward_castle") and refresh() and G.get("gen") and G.get("pawn"): break
        yield from rwait(2.0); refresh()
        g = G.get("gen")
        if g: g.slate_mouse_button(unreal.Vector2D(200, 200), key("LeftMouseButton"), False)       # (the button let go)
        res["world_after"] = G["w"].get_name() if G.get("w") else None
        res["hero_after"] = str(g.get_editor_property("current_hero")) if g else None
        res["cursor_after"] = G["pc"].show_mouse_cursor if G.get("pc") else None
    G.pop("travel_until", None)
    ok = (res["mouse_ui"] and res["cursor_shown"] and not res["refused"] and [x[1] for x in seq] == [2, 3, 2, 0] and all(x[3] for x in seq)
          and res["opened_before"] == "" and res["opened_by_name_again"].endswith("mistward_castle?Hero=Warrior")
          and (res.get("world_after") or "").endswith("mistward_castle") and res.get("hero_after") == "Rogue" and res.get("cursor_after") is False)
    step_result("menu", ok, **res)

STEPS = {"menu": step_menu, "basics": step_basics, "shields": step_shields, "torch": step_torch, "armour": step_armour, "inventory": step_inventory, "open": step_open,
         "heights": step_heights, "tiers": step_tiers, "layout": step_layout, "traps": step_traps, "teleport": step_teleport, "cells": step_cells,
         "death": step_death}
def view_owner():
    """what clears the game's view of the editor's other windows: the generator, or the menu's turntable"""
    if G.get("gen"): return G["gen"]
    return (GS.get_all_actors_of_class(G["w"], unreal.RDHeroSelect) or [None])[0] if G.get("w") else None
def run():
    # (the editor's windows over the game's view (a floating Message Log covered it) hidden while input is sent to it; shown
    # again at the end)
    o = view_owner(); R["windows_hidden"] = str(o.slate_clear_view()) if o else None
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
        o = view_owner(); R["windows_shown_again"] = o.slate_restore_view() if o else None
    except Exception as e: R["error"] = (err or "") + " / " + str(e)
    os.makedirs(OUT, exist_ok=True); json.dump(R, open(os.path.join(OUT, f"test_{TAG}.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    ok = not R.get("error") and len(R["steps"]) == len(PLAN) and all(s["ok"] for s in R["steps"])
    unreal.log(f"MWTEST done | {TAG} | {'ok' if ok else 'FAILED'} | " + " | ".join(f"{s['step']} {'ok' if s['ok'] else 'FAILED'}" for s in R["steps"]) + f" | {R.get('error') or ''}")
    G.clear()
def tick(dt):
    try:
        if UES.get_game_world() is None:
            if G.get("travel_until", 0) > time.time(): return          # (the menu opening the dungeon: a moment with no world)
            finish("PIE ended"); return
        next(G["gen_"])
    except StopIteration: finish()
    except Exception as e:
        import traceback
        unreal.log_error("MWTEST error: " + str(e) + traceback.format_exc()); finish(str(e))
G["gen_"] = run()
G["h"] = unreal.register_slate_post_tick_callback(tick)
print("mistward test armed:", PLAN, TAG)
