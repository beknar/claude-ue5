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
The third list (docs/improvements2.txt, 870; also on random_dungeonmagic_level5 with the ps1's -lv):
  outline  the Rogue's seen trap outlined in red (its plate drawn over, a ring), the red measured in pictures; the Warrior none
  tabs     five tabs, each its own kinds; Q / E, LB / RB and a click change it; E no longer uses; copies of a found weapon
           as worn as each other one line; the anvil says how many are left
  slots    ten quick slots: a number, Y (the D-pad's slot) and the right mouse button put a weapon in one; 1 - 0 and the
           D-pad left / right draw them
  helmet   the worn set's helmet sections found on the mesh; H hides and shows them (pictures measured), the armour tab's line
  block    the right mouse button / LT held: her speed halved, the shield's share + 30 %, five times its wear, no swing; the
           Mage cannot; her shield hand raised
  startgear the Warrior: the Dagger, the worst shield, no armour; hers for good (no wear, kept when she falls)
  pickups  the armories' tables' tier things; F takes one off its table
  rooms    the eight special rooms: shrine, healing / speed / mana fountains, arena, trap gauntlet, vault and key, throne room
  slashes  a boss's slash; on a weapon through the inventory, T takes it off, on the bow; a swing and a shot; all twenty measured
The user's of 2026-10-28 (871; also on level 5):
  tomemana the Mage's pool 100, 200 with the best ring; Null Sanctum's tome makes it 220 and the sanctum is cast, Apocalypse's
           300 and it is cast; the ring off changes nothing; kept through a death, gone at a restart; the Summoner's pool unchanged
The Martial Artist (872, 873; the user's of 2026-10-28):
  martial  in mistward_castle: her numbers, fists, the Dexterity ring on fists and knives (not chi), a knife in both hands
           (+30 %), a chi attack (mana, damage, the blast's half beside, refused out of reach), the dash, the roll, a tier
           boss's two chi attacks, kept through a death, forgotten at a restart
  martialroom  (alone, in martial_arts: -lv martial_arts) the one room, her eleven weapons, the room's monsters coming
           back, each chi attack cast (mana, damage, effect, a picture), the dash
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
DEFAULT = "basics,shields,torch,armour,inventory,heights,tiers,open,layout,traps,teleport,cells,death,outline,tabs,slots,helmet,block,startgear,pickups,rooms,slashes,tomemana,martial"
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
    # (her starting shield: the worst of the table since the third list (2026-10-27); the Heater Shield before)
    ss = str(md(g.get_editor_property("start_shield")).get("Warrior"))
    res = {"start": {"worn": str(c.get_worn_shield()), "in_hand": c.is_shield_in_hand(), "share": round(c.get_shield_share(), 4), "start_shield": ss}}
    res["start"]["want_share"] = SH[ss]["damage"] * 0.04 if ss in SH else None
    heater = SH["Heater Shield"]
    # (a found Heater Shield: her speed with it and without it)
    c.add_item("Heater Shield", 1); c.wear_shield("Heater Shield"); yield from wait(0.2)
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
    ok = (s["worn"] == ss and s["in_hand"] and s["want_share"] is not None and abs(s["share"] - s["want_share"]) < 1e-3
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
    for it in [i for i in g.get_editor_property("items") if i.kind in (unreal.RDItemKind.HEALING, unreal.RDItemKind.FOOD, unreal.RDItemKind.MANA, unreal.RDItemKind.SPEED)] + \
              [i for i in g.get_editor_property("items") if i.kind == unreal.RDItemKind.COMPONENT][:40]:
        c.add_item(str(it.name), 1)
    c.set_health(c.get_max_health() * 0.5)
    c.set_inventory_open(True); yield from rwait(0.2)
    # (with the tabs (the third list) the list is one tab's: the potions and food, the longest)
    if g.get_editor_property("inventory_tabs"): c.set_inventory_tab(2)
    yield from rwait(0.2)
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
        # (shields in its containers' lists (found as loot, not given by the test), by the set's tier; not a vault's chests:
        # they hold the tier above's things, by the third list's rule)
        vaults = {int(str(l).split("|")[2]) for l in g.get_special_room_lines() if str(l).split("|")[3] == "Vault" and int(str(l).split("|")[0]) == sc.x and int(str(l).split("|")[1]) == sc.y}
        for i in range(S.get_num_containers()):
            if S.room_at(S.get_container_location(i)) in vaults: continue
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
        out.append({"s": I2(int(p[0]), int(p[1])), "i": int(p[2]), "name": p[3], "kind": p[4], "at": V(float(p[5]), float(p[6]), float(p[7])), "state": int(p[8]), "seen": int(p[9]),
                    "room": int(p[10]) if len(p) > 10 else -1})
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
        # (what she carries of every item: her gift may be one she has already (an earlier step gave her potions))
        names_ = [str(i.name) for i in g.get_editor_property("items")]
        n0 = {n: c.get_item_count(n) for n in names_}; f0 = g.prisoners_freed
        shot("cell_prisoner_before"); yield from rwait(0.6)
        r["f"] = str(g.interact_nearest(G["pawn"].get_actor_location(), 260.0)); yield from wait(1.0)
        r["freed"] = g.prisoners_freed - f0; r["says"] = str(c.message); r["found"] = str(g.last_found)
        r["carried_more"] = sum(c.get_item_count(n) - n0[n] for n in names_)
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
    # (her starting shield is hers for good (bKeepStartGear): it stays with her; the found Kite Shield worn drops and goes back on)
    ss = str(md(g.get_editor_property("start_shield")).get("Warrior"))
    keep = g.get_editor_property("keep_start_gear")
    c.wear_shield("Kite Shield")
    yield from wait(0.3)
    before = sorted(lines(c)); res = {"gave": give, "lines_before": len(before), "start_shield": ss, "keep_start_gear": keep}
    # (a blow just past her hit points, as a monster's: one of a million also broke her shield, which takes its share first)
    c.apply_damage(c.get_health() / max(1.0 - c.get_shield_share(), 0.1) + 5.0, None); yield from wait(1.5)
    piles = [p for p in g.loot_piles if p]
    res["dead"] = c.is_dead(); res["piles"] = len(piles)
    if piles:
        p = piles[0]
        res["pile"] = {"things": [str(x) for x in p.things], "pictures": p.pictures, "particles": p.get_effect_particles(), "from_her_m": round(dist2(p.get_actor_location(), spot) / 100, 2)}
    def have(n): return c.get_item_count(n) + sum(1 for d in g.get_editor_property("weapons") if str(d.item) == n)
    res["carried_after"] = {n: have(n) for n in give}
    res["start_shield_after"] = have(ss)
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
        res["carried_back"] = {n: have(n) for n in give + [ss]}
        res["shield_worn_again"] = str(c.get_worn_shield())
        res["piles_after"] = len([p for p in g.loot_piles if p])
    quiet(False)
    pl = res.get("pile", {})
    # (all of her found equipment drops (the list's words); the shield she started with drops too unless it is hers for good
    # (bKeepStartGear, the third list); her hero's own weapons are not items)
    want = sorted(give + ([] if keep else [ss]))
    ok = (res["dead"] and res["piles"] == 1 and sorted(pl.get("things", [])) == want and pl.get("pictures", 0) >= len(want) and len(want) > 12
          and pl.get("particles", 0) > 0 and pl.get("from_her_m", 9) < 1.5 and all(v == 0 for v in res["carried_after"].values())
          and res["start_shield_after"] == (1 if keep else 0)
          and 9 in res["marks"] and res["revived"] and res.get("f") == "loot" and all(v == 1 for v in res.get("carried_back", {"x": 0}).values())
          and res.get("shield_worn_again") == "Kite Shield" and res.get("piles_after") == 0)
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

# ================================================================================================ the third list (docs/improvements2.txt)
def png_stat(path, box, fn):
    """the mean of fn(r, g, b) over a part of a PNG (fractions of its width and height), read with zlib as png_luma does"""
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
                i = x * bpp; tot += fn(line[i], line[i + 1], line[i + 2]); n += 1
        prev = line
    return round(tot / max(n, 1), 4)
def red_share(r, g, b): return 1.0 if (r > 110 and g < 0.4 * r and b < 0.4 * r) else 0.0      # (a deep red: torch-lit stone is orange, g 0.5-0.65 of r)
def shot_stat(name, box, fn, res="640x360"):
    """a picture of the game now and fn's mean over a part of it (none: the picture did not come)"""
    p = os.path.join(SHOTS, f"mw_{TAG}_{name}.png")
    if os.path.exists(p): os.remove(p)
    shot(name, res); t0 = time.time()
    while time.time() - t0 < 8:
        yield from rwait(0.3)
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            yield from rwait(0.3)
            try: return png_stat(p, box, fn)
            except Exception: continue
    return None
def face(at_from, at_to, pitch=-12.0):
    yaw = math.degrees(math.atan2(at_to.y - at_from.y, at_to.x - at_from.x))
    G["pawn"].set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), True); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=pitch, yaw=yaw))
    return yaw
def stand_near(S, room, target, lo=250.0, hi=600.0):
    """a free tile of a room lo to hi cm from a point, the nearest to the middle of that span (none: the room's farthest)"""
    tiles = list(S.get_room_free_tiles(room)); best = None
    for t in tiles:
        d = dist2(t, target)
        if lo <= d <= hi and (best is None or abs(d - (lo + hi) / 2) < abs(dist2(best, target) - (lo + hi) / 2)): best = t
    if best is None and tiles: best = min(tiles, key=lambda t: abs(dist2(t, target) - lo))
    return best
def spawn_dummy(at, hmul=30.0):
    """a harmless monster (no damage) with many hit points, standing where it is put"""
    g = G["gen"]; kinds = [str(d.name) for d in g.get_editor_property("monsters")]
    m = g.spawn_monster_named(kinds[0], V(at.x, at.y, at.z), 1, hmul, 0.0, 1.0)
    return m
def md(m):
    """an unreal.Map as a dict with str keys"""
    try: return {str(k): v for k, v in m.items()}
    except Exception: return {}
def cursor_to(c, row):
    """the inventory's cursor walked to a row with S / W as the keyboard sends them (at most 60 presses)"""
    for _ in range(60):
        if row is None or c.get_inventory_cursor() == row: return
        yield from slate_hold("S" if c.get_inventory_cursor() < row else "W", 0.05)
def kill_all_near(at, r):
    for m in G["gen"].get_monsters():
        if alive(m) and dist2(m.get_actor_location(), at) < r: m.apply_damage(1e7, None)
def drop(ms):
    """the trial's monsters killed (destroyed, they stayed in the generator's list a while and a chain or an inferno struck
    their ghosts: the dead are passed by)"""
    for m in ms:
        try:
            if m and unreal.SystemLibrary.is_valid(m) and not m.is_dead(): m.apply_damage(1e7, None)
        except Exception: pass

def screen_box(at, half_w=0.07, half_h=0.09):
    """a box of the picture (fractions) round where a world point is on the screen (none: off the screen)"""
    ok_ = unreal.GameplayStatics.project_world_to_screen(G["pc"], at, False)
    ok, sp = (ok_[0], ok_[1]) if isinstance(ok_, tuple) else (ok_ is not None, ok_)
    if not ok or sp is None: return None
    vs = unreal.WidgetLayoutLibrary.get_viewport_size(G["w"])
    fx, fy = sp.x / max(vs.x, 1.0), sp.y / max(vs.y, 1.0)
    if not (0.05 < fx < 0.95 and 0.05 < fy < 0.95): return None
    return (max(0.0, fx - half_w), max(0.0, fy - half_h), min(1.0, fx + half_w), min(1.0, fy + half_h))

def outline_view(t, stand):
    """her at `stand` facing the trap, the camera down at it, her body hidden for the picture (it stood between them)"""
    put(stand, face(stand, t["at"], -32)); face(stand, t["at"], -32)
    G["pawn"].set_actor_hidden_in_game(True)
    yield from wait(0.8)

def step_outline():
    """the Rogue's traps: a trap she has seen is outlined in red (its plate drawn over, a red ring at its reach); the Warrior
    sees none and none is outlined. Measured on the components and in pictures: the same place and camera for the Warrior
    (no outline) and then the Rogue (the trap seen), her body hidden; the red share round the trap's point on the screen"""
    g = G["gen"]; res = {"trials": []}
    c = yield from restart("Warrior"); quiet(True)
    T = [t for t in trap_lines() if t["state"] == 0 and t["s"].x == 0 and t["s"].y == 0]
    res["traps"] = len(T)
    om = g.get_editor_property("trap_outline_material")
    plate = [t for t in T if t["name"] in ("Pit", "Darts", "Deadfall", "Crusher", "Spring", "Lingering", "Chain")]
    glow = [t for t in T if t["name"] in ("Glyph", "Ward", "Teleport", "Emanation", "Cursed")]
    picks = plate[:1] + glow[:1]
    stands = {}
    # ---- the Warrior: the same view of each, no outline (she sees no trap)
    for t in picks:
        S = g.get_section(t["s"]); room = S.room_at(t["at"])
        st = stand_near(S, room, t["at"], 420.0, 650.0) if room >= 0 else None
        stands[t["i"]] = st or V(t["at"].x - 500, t["at"].y, 0.0)
        yield from outline_view(t, stands[t["i"]])
        box = screen_box(t["at"]); res.setdefault("boxes", []).append([round(v, 3) for v in box] if box else None)
        red0 = (yield from shot_stat(f"outline_warrior_{t['name']}", box, red_share)) if box else None
        G["pawn"].set_actor_hidden_in_game(False)
        res["trials"].append({"trap": t["name"], "i": t["i"], "red_warrior": red0, "m": round(dist2(stands[t["i"]], t["at"]) / 100, 1)})
    res["warrior"] = {"seen": sum(x["seen"] for x in trap_lines()), "rings": len(g.get_section(I2(0, 0)).get_components_by_tag(unreal.StaticMeshComponent, "RDOutline"))}
    # ---- the Rogue (the same traps: the restart's seed is the same): from the same place she sees it (8 m)
    c = yield from restart("Rogue"); quiet(True)
    for tr, t in zip(res["trials"], picks):
        S = g.get_section(t["s"])
        rings0 = len([x for x in S.get_components_by_tag(unreal.StaticMeshComponent, "RDOutline") if dist2(x.get_world_location(), t["at"]) < 50])
        yield from outline_view(t, stands[t["i"]])
        t1 = time.time()
        while time.time() - t1 < 3.0 and not next((x["seen"] for x in trap_lines() if x["s"] == t["s"] and x["i"] == t["i"]), 0): yield
        seen = next((x["seen"] for x in trap_lines() if x["s"] == t["s"] and x["i"] == t["i"]), 0)
        yield from wait(0.4)
        box = screen_box(t["at"])
        red1 = (yield from shot_stat(f"outline_rogue_{t['name']}", box, red_share)) if box else None
        G["pawn"].set_actor_hidden_in_game(False)
        rings = [x for x in S.get_components_by_tag(unreal.StaticMeshComponent, "RDOutline") if dist2(x.get_world_location(), t["at"]) < 50]
        overl = [x for x in S.get_components_by_class(unreal.StaticMeshComponent) if dist2(x.get_world_location(), t["at"]) < 80 and not x.component_has_tag("RDOutline")
                 and x.get_overlay_material() is not None and x.get_overlay_material().get_name() == om.get_name()]
        tr.update({"seen": seen, "rings_before": rings0, "rings": len(rings), "ring_scale": round(rings[0].get_world_scale().x, 2) if rings else None,
                   "plate_outlined": len(overl), "red_rogue": red1})
    quiet(False)
    tr = res["trials"]
    ok = (len(tr) == 2 and all(x.get("seen") == 1 and x.get("rings_before") == 0 and x.get("rings") == 1 and x.get("red_warrior") is not None and x.get("red_rogue") is not None
                               and x["red_rogue"] > x["red_warrior"] + 0.02 for x in tr)
          and tr[0].get("plate_outlined", 0) >= 1 and res["warrior"]["seen"] == 0 and res["warrior"]["rings"] == 0)
    step_result("outline", ok, **res)

def step_tabs():
    """the inventory in five tabs: each tab its own kinds; Q / E and LB / RB (sent as the devices send them) and a click on a tab
    change it; E no longer uses; copies of a found weapon as worn as each other on one line; the anvil says how many are left"""
    c = yield from restart("Warrior"); g = G["gen"]; quiet(True)
    give = {"Dagger": 2, "Arming Sword": 1, "Small Healing Potion": 2, "Iron Ingot": 3, "Kite Shield": 2, "Vault Key": 1, "Ember Slash": 1, "Whetstone": 1}
    ring = next((str(i.name) for i in items_of(unreal.RDItemKind.RING)), None); give[ring] = 1
    arm = next((str(i.name) for i in items_of(unreal.RDItemKind.ARMOUR)), None); give[arm] = 1
    for n, k in give.items(): c.add_item(n, k)
    c.set_health(c.get_max_health() * 0.5)
    c.set_inventory_open(True); yield from rwait(0.4)
    res = {"tabs": {}, "refused": []}
    allk = [str(l).split("|")[0] for l in c.get_all_inventory_lines()]
    want = {0: {"weapon", "carried"}, 1: {"armour", "shield", "torch", "helmet"}, 2: {"item"}, 3: {"component", "repair"}, 4: {"ring", "tome", "teleport", "slash", "key"}}
    for t in range(5):
        c.set_inventory_tab(t); yield from rwait(0.15)
        ks = [str(l).split("|")[0] for l in c.get_inventory_lines()]
        res["tabs"][t] = {"kinds": sorted(set(ks)), "lines": len(ks), "all_its_own": all(k in want[t] for k in ks)}
    res["lines_total"] = len(allk); res["lines_in_tabs"] = sum(v["lines"] for v in res["tabs"].values())
    # (the keys as the devices send them)
    c.set_inventory_tab(0); yield from rwait(0.2); seq = []
    for nm in ("E", "E", "Q", "Gamepad_RightShoulder", "Gamepad_LeftShoulder"):
        why = yield from slate_hold(nm, 0.08)
        if why: res["refused"].append(f"{nm}: {why}")
        seq.append(c.get_inventory_tab())
    res["key_tabs"] = seq
    # (a click on the fourth tab, where the HUD drew it)
    yield from rwait(0.3)
    tb = [tuple(float(v) for v in str(b).split("|")) for b in c.get_tab_boxes()]
    res["tab_boxes"] = len(tb)
    if len(tb) == 5:
        why = yield from slate_click(unreal.Vector2D((tb[3][0] + tb[3][2]) / 2, (tb[3][1] + tb[3][3]) / 2))
        if why: res["refused"].append("click: " + why)
        res["clicked_tab"] = c.get_inventory_tab()
    # (E on the potions' tab: the tab changes, nothing is drunk)
    c.set_inventory_tab(2); yield from rwait(0.2); n0 = c.get_item_count("Small Healing Potion")
    yield from slate_hold("E", 0.08); res["e_on_potions"] = {"tab_after": c.get_inventory_tab(), "drunk": n0 - c.get_item_count("Small Healing Potion")}
    # (stacks: the two found daggers as one line "x 2"; one worn down: two lines)
    c.set_inventory_tab(0); yield from rwait(0.2)
    dl = [str(l) for l in c.get_inventory_lines() if str(l).startswith("weapon|Dagger|")]
    res["daggers_lines"] = dl
    found = [i for i, d in enumerate(g.get_editor_property("weapons")) if str(d.name) == "Dagger" and str(d.item) != "None"]
    if found: c.set_weapon_wear(found[0], 20.0); yield from rwait(0.1)
    res["daggers_after_wear"] = [str(l) for l in c.get_inventory_lines() if str(l).startswith("weapon|Dagger|")]
    shot("tabs_weapons"); yield from rwait(0.5)
    c.set_inventory_tab(4); yield from rwait(0.2); shot("tabs_magic"); yield from rwait(0.5)
    c.set_inventory_open(False); yield from rwait(0.2)
    # (the anvil: how many are left of what is broken down)
    c.set_crafting_open(True); yield from rwait(0.3)
    res["anvil_kite"] = c.break_down_gear("Kite Shield"); res["anvil_says"] = str(c.message)
    wi = next((i for i, d in enumerate(g.get_editor_property("weapons")) if str(d.name) == "Dagger" and str(d.item) != "None"), -1)
    res["anvil_dagger"] = c.break_down_weapon(wi) if wi >= 0 else False; res["anvil_dagger_says"] = str(c.message)
    shot("tabs_anvil"); yield from rwait(0.5)
    c.set_crafting_open(False); quiet(False)
    tbs = res["tabs"]
    ok = (all(v["all_its_own"] for v in tbs.values()) and res["lines_in_tabs"] == res["lines_total"] and all(tbs[t]["lines"] > 0 for t in range(5))
          and res["key_tabs"] == [1, 2, 1, 2, 1] and not res["refused"] and res.get("clicked_tab") == 3
          and res["e_on_potions"]["tab_after"] == 3 and res["e_on_potions"]["drunk"] == 0
          and any(l.split("|")[5] == "2" for l in res["daggers_lines"]) and len(res["daggers_after_wear"]) == len(res["daggers_lines"]) + 1
          and res["anvil_kite"] and "(1 left)" in res["anvil_says"] and res["anvil_dagger"] and "(1 left)" in res["anvil_dagger_says"])
    step_result("tabs", ok, **res)

def step_slots():
    """ten quick slots: filled as weapons come; in the inventory a weapon's number (sent as the keyboard sends it) puts it in that
    slot, the gamepad's Y in the slot the D-pad left / right chose, the right mouse button too; outside, 1 to 0 draw a slot's,
    the D-pad left / right step through the filled ones"""
    c = yield from restart("Warrior"); g = G["gen"]; quiet(True)
    put(g.get_start_room_center(), 0.0); yield from wait(0.3)
    for n in ("Arming Sword", "Longbow", "Viking Sword"): c.add_item(n, 1)
    yield from wait(0.3)
    res = {"slots_filled": [str(s) for s in c.get_quick_slots()], "refused": []}
    def row_of(name):
        L_ = lines(c); return next((i for i, l in enumerate(L_) if l.startswith(f"weapon|{name}|")), None)
    c.set_inventory_open(True); c.set_inventory_tab(0); yield from rwait(0.3)
    # (the Longbow into slot 5 with the key 5)
    r_ = row_of("Longbow")
    yield from cursor_to(c, r_)
    why = yield from slate_hold("Five", 0.08)
    if why: res["refused"].append("5: " + why)
    res["after_5"] = [str(s) for s in c.get_quick_slots()]
    # (the Viking Sword into slot 8: D-pad right three times from slot 5 (the slot chosen follows the last), then Y)
    r_ = row_of("Viking Sword")
    yield from cursor_to(c, r_)
    for _ in range(3): yield from slate_hold("Gamepad_DPad_Right", 0.06)
    res["assign_slot"] = c.get_assign_slot()
    yield from slate_hold("Gamepad_FaceButton_Top", 0.08)
    res["after_y"] = [str(s) for s in c.get_quick_slots()]
    # (the Arming Sword with the right mouse button on its row, into the slot chosen: D-pad left back to slot 7)
    yield from slate_hold("Gamepad_DPad_Left", 0.06)
    yield from rwait(0.3); R_ = rows(c); r_ = row_of("Arming Sword")
    if r_ in R_:
        b = R_[r_]; g.slate_mouse_move(unreal.Vector2D(b[0] + 30, b[1] - 50)); yield from rwait(0.2); g.slate_mouse_move(mid(b)); yield from rwait(0.25)
        why = str(g.slate_mouse_button(mid(b), key("RightMouseButton"), True)); yield from rwait(0.08); g.slate_mouse_button(mid(b), key("RightMouseButton"), False); yield from rwait(0.25)
        if why: res["refused"].append("rmb: " + why)
    res["after_rmb"] = [str(s) for s in c.get_quick_slots()]
    shot("slots_inventory"); yield from rwait(0.5)
    c.set_inventory_open(False); yield from rwait(0.3)
    # (outside: 5 draws the Longbow, 1 the Dagger, the D-pad right the next filled slot, left back)
    seq = []
    for nm in ("Five", "One", "Gamepad_DPad_Right", "Gamepad_DPad_Right", "Gamepad_DPad_Left"):
        why = yield from slate_hold(nm, 0.08); yield from wait(0.25)
        if why: res["refused"].append(f"{nm}: {why}")
        seq.append(str(c.get_weapon_name()))
    res["drawn_seq"] = seq
    shot("slots_bar"); yield from rwait(0.5)
    quiet(False)
    s5, sy, sr = res["after_5"], res["after_y"], res["after_rmb"]
    filled = [s for s in sy if s != "None"]
    ok = (not res["refused"] and res["slots_filled"][0] == "Dagger" and s5[4] == "Longbow" and s5.count("Longbow") == 1 and res["assign_slot"] == 7 and sy[7] == "Viking Sword"
          and sr[6] == "Arming Sword" and seq[0] == "Longbow" and seq[1] == "Dagger" and seq[2] != "Dagger" and seq[4] == seq[2] and len(filled) >= 3)
    step_result("slots", ok, **res)

def step_helmet():
    """the helmet: of each set of armour the sections her head bone moves (the helmet), found on the mesh; H (as the keyboard
    sends it) hides them and shows them again, the armour tab's helmet line too; a picture of her head each way and the
    difference measured in it"""
    c = yield from restart("Warrior"); g = G["gen"]; quiet(True)
    sets = [str(i.name) for i in items_of(unreal.RDItemKind.ARMOUR)]
    res = {"sets": len(sets), "with_helmet": [], "without": []}
    for s in sets:
        c.add_item(s, 1)
        if not c.wear_armour(s): continue
        yield from wait(0.05)
        hl = [str(x) for x in c.get_helmet_lines()]
        (res["with_helmet"] if hl else res["without"]).append(s)
    pick = "Plate Armour" if "Plate Armour" in res["with_helmet"] else (res["with_helmet"][0] if res["with_helmet"] else None)
    res["pick"] = pick
    if pick:
        c.wear_armour(pick); yield from wait(0.3)
        # (her face from the front, close)
        p = G["pawn"]; L = p.get_actor_location(); fw = p.get_actor_forward_vector()
        G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-5, yaw=p.get_actor_rotation().yaw + 180)); yield from wait(0.5)
        # (her head in the picture: the third-person view puts it a little left of the middle, under the upper third; the
        # pixels there compared one by one between the two pictures (a mean brightness hardly moved: dark hair for dark iron))
        box = (0.40, 0.33, 0.50, 0.55)
        PX = []
        l0 = yield from shot_stat("helmet_on", box, lambda r, g_, b: PX.append((r, g_, b)) or 0.0)
        n_on = len(PX)
        why = yield from slate_hold("H", 0.08); yield from wait(0.4)
        res["h_refused"] = why; res["hidden"] = c.is_helmet_hidden(); res["lines_hidden"] = [str(x) for x in c.get_helmet_lines()]
        l1 = yield from shot_stat("helmet_off", box, lambda r, g_, b: PX.append((r, g_, b)) or 0.0)
        A_, B_ = PX[:n_on], PX[n_on:]
        res["pixels"] = [len(A_), len(B_)]
        res["head_diff"] = round(sum(abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2]) for a, b in zip(A_, B_)) / 3.0 / max(1, min(len(A_), len(B_))), 2) if A_ and len(A_) == len(B_) else None
        res["luma_on"] = l0; res["luma_off"] = l1
        # (the armour tab's line shows it again)
        c.set_inventory_open(True); c.set_inventory_tab(1); yield from rwait(0.2)
        hrow = next((i for i, l in enumerate(lines(c)) if l.startswith("helmet|")), None)
        res["helmet_row"] = lines(c)[hrow] if hrow is not None else None
        if hrow is not None:
            yield from cursor_to(c, hrow)
            yield from slate_hold("Enter", 0.08)
        res["shown_by_row"] = not c.is_helmet_hidden()
        c.set_inventory_open(False); yield from wait(0.3)
    quiet(False)
    ok = (pick is not None and not res.get("h_refused") and res.get("hidden") and all(x.endswith("|1") for x in res.get("lines_hidden", [])) and res.get("lines_hidden")
          and (res.get("head_diff") or 0) > 8.0 and res.get("helmet_row") and res.get("shown_by_row"))
    step_result("helmet", ok, **res)

def step_block():
    """the Warrior's block: the right mouse button held (as the mouse sends it): blocking, her speed halved, a blow takes the
    shield's share + 30 % less and wears the shield five times as much, no swing while she blocks; LT the same; the Mage cannot
    block; her left hand raised before her chest (the pose), pictures"""
    c = yield from restart("Warrior"); g = G["gen"]; quiet(True)
    put(g.get_start_room_center(), 0.0); yield from wait(0.3)
    c.add_item("Kite Shield", 1); c.wear_shield("Kite Shield"); yield from wait(0.3)
    share = c.get_shield_share(); body = G["pawn"].get_editor_property("mesh")
    def hand(): h = body.get_socket_location("hand_l"); s = G["pawn"].get_actor_location(); f = G["pawn"].get_actor_forward_vector(); d = h - s; return round(d.dot(f), 1), round(d.z, 1)
    res = {"shield": str(c.get_worn_shield()), "share": round(share, 3), "refused": []}
    s0 = walk_speed(); res["hand_rest"] = hand()
    # (a blow without the block)
    c.set_health(c.get_max_health()); w0 = c.get_shield_wear("Kite Shield"); h0 = c.get_health()
    c.apply_damage(40.0, None); yield from wait(0.1)
    res["plain"] = {"lost": round(h0 - c.get_health(), 2), "shield_lost": round(w0 - c.get_shield_wear("Kite Shield"), 2), "share": round(c.last_shield_share, 3)}
    # (the right mouse button held)
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=G["pawn"].get_actor_rotation().yaw + 110)); yield from wait(0.3)
    why = str(g.slate_key(key("RightMouseButton"), True)); yield from rwait(0.5)
    if why: res["refused"].append("rmb: " + why)
    res["blocking"] = c.is_blocking(); s1 = walk_speed(); res["hand_block"] = hand()
    c.set_health(c.get_max_health()); w1 = c.get_shield_wear("Kite Shield"); h1 = c.get_health(); bh = c.blocked_hits
    c.apply_damage(40.0, None); yield from wait(0.1)
    res["blocked"] = {"lost": round(h1 - c.get_health(), 2), "shield_lost": round(w1 - c.get_shield_wear("Kite Shield"), 2), "share": round(c.last_shield_share, 3), "hits": c.blocked_hits - bh}
    res["swing_refused"] = not c.start_attack()
    shot("block_on"); yield from rwait(0.6)
    g.slate_key(key("RightMouseButton"), False); yield from rwait(0.5)
    res["after_release"] = {"blocking": c.is_blocking(), "speed": round(walk_speed(), 1), "hand": hand()}
    shot("block_off"); yield from rwait(0.6)
    # (LT held: the gamepad's)
    why = str(g.slate_key(key("Gamepad_LeftTrigger"), True)); yield from rwait(0.4)
    res["lt_blocking"] = c.is_blocking(); g.slate_key(key("Gamepad_LeftTrigger"), False); yield from rwait(0.3)
    if why: res["refused"].append("lt: " + why)
    res["speed"] = {"normal": round(s0, 1), "blocking": round(s1, 1), "ratio": round(s1 / max(s0, 1), 3)}
    # (blocking when play restarts: the held pose let go (the PR review's find: the flag was cleared, the paused clip stayed))
    c.set_blocking(True); yield from wait(0.5)
    g.restart_play(0); yield from wait(1.2); refresh(); c = cb(); body = G["pawn"].get_editor_property("mesh")
    res["after_restart"] = {"blocking": c.is_blocking(), "hand": hand()}
    # (the Mage: no shield, no block)
    g.switch_hero("Mage"); yield from wait(0.6); refresh(); c = cb()
    g.slate_key(key("RightMouseButton"), True); yield from rwait(0.4); res["mage_blocking"] = c.is_blocking(); g.slate_key(key("RightMouseButton"), False); yield from rwait(0.2)
    g.switch_hero("Warrior"); yield from wait(0.6); refresh(); quiet(False)
    p_, b_ = res["plain"], res["blocked"]
    want_share = min(share + 0.3, 0.95)
    ok = (not res["refused"] and res["blocking"] and abs(res["speed"]["ratio"] - 0.5) < 0.03 and abs(b_["share"] - want_share) < 0.005 and b_["hits"] == 1
          and b_["lost"] < p_["lost"] * 0.8 and p_["shield_lost"] > 0 and abs(b_["shield_lost"] / max(p_["shield_lost"], 1e-3) - 5.0 * (want_share / max(share, 1e-3))) < 1.0
          and res["swing_refused"] and not res["after_release"]["blocking"] and res["after_release"]["speed"] > s1 * 1.8
          and res["hand_block"][1] > res["hand_rest"][1] + 15 and res["after_release"]["hand"][1] < res["hand_block"][1] - 10
          and res["lt_blocking"] and not res["mage_blocking"]
          and not res["after_restart"]["blocking"] and res["after_restart"]["hand"][1] < res["hand_block"][1] - 10)
    step_result("block", ok, **res)

def step_startgear():
    """the Warrior starts with no armour, the worst weapon she can wield (the Dagger) and the worst shield; both are hers for good:
    the shield takes blows without wearing, and when she falls both stay with her (her found things drop)"""
    c = yield from restart("Warrior"); g = G["gen"]; quiet(True)
    put(g.get_start_room_center(), 0.0); yield from wait(0.3)
    W = g.get_editor_property("weapons"); ss = str(md(g.get_editor_property("start_shield")).get("Warrior"))
    shields = sorted(items_of(unreal.RDItemKind.SHIELD), key=lambda i: (i.amount, str(i.name)))
    res = {"weapons": [(str(w.name), str(w.item), w.durability) for w in W], "worn_shield": str(c.get_worn_shield()), "start_shield": ss,
           "worst_shield": str(shields[0].name), "worn_armour": str(c.get_worn_armour())}
    w0 = c.get_shield_wear(ss)
    for _ in range(5): c.set_health(c.get_max_health()); c.apply_damage(30.0, None); yield from wait(0.05)
    res["shield_wear"] = [round(w0, 1), round(c.get_shield_wear(ss), 1)]
    # (she falls with a found sword and shield worn: they drop, hers stay)
    c.add_item("Arming Sword", 1); c.add_item("Kite Shield", 1); c.wear_shield("Kite Shield"); yield from wait(0.2)
    c.apply_damage(c.get_health() * 4.0 + 50.0, None); yield from wait(1.2)
    piles = [p for p in g.loot_piles if p]
    res["pile"] = sorted(str(x) for x in piles[0].things) if piles else None
    res["after_fall"] = {"shield": str(c.get_worn_shield()), "count": c.get_item_count(ss), "weapons": [str(w.name) for w in g.get_editor_property("weapons")]}
    t0 = time.time()
    while c.is_dead() and time.time() - t0 < 20: yield
    yield from wait(0.8)
    if piles:
        put(piles[0].get_actor_location(), 0.0); yield from wait(0.4)
        res["f"] = str(g.interact_nearest(G["pawn"].get_actor_location(), 260.0)); yield from wait(0.3)
        res["back"] = {"shield": str(c.get_worn_shield()), "kite": c.get_item_count("Kite Shield"), "start": c.get_item_count(ss)}
    quiet(False)
    # (a level without the castle's drop on death (level 5): nothing drops, hers stay hers)
    res["drop_on_death"] = g.get_editor_property("drop_on_death")
    fall_ok = ((res["pile"] is not None and ss not in res["pile"] and "Kite Shield" in res["pile"] and "Arming Sword" in res["pile"]
                and res["after_fall"]["shield"] == ss and res["after_fall"]["count"] == 1 and res["after_fall"]["weapons"] == ["Dagger"]
                and res.get("f") == "loot" and res.get("back", {}).get("shield") == "Kite Shield" and res.get("back", {}).get("start") == 1) if res["drop_on_death"] else
               (res["pile"] is None and res["after_fall"]["count"] == 1 and "Dagger" in res["after_fall"]["weapons"]))
    ok = (len(res["weapons"]) == 1 and res["weapons"][0][0] == "Dagger" and res["weapons"][0][1] == "None" and res["weapons"][0][2] == 0
          and res["worn_shield"] == ss == res["worst_shield"] and res["worn_armour"] == "None" and res["shield_wear"][0] == res["shield_wear"][1] and fall_ok)
    step_result("startgear", ok, **res)

def step_pickups():
    """the armories' tables: weapons and shields of the set's tier lie on them (meshes drawn); F (as the keyboard sends it) takes
    the nearest: it is in her pack and gone from the table"""
    c = yield from restart("Warrior"); g = G["gen"]; quiet(True)
    P = [str(l).split("|") for l in g.get_pickup_lines()]
    tiers = {str(i.name): list(i.tiers) for i in g.get_editor_property("items")}
    res = {"pickups": len(P), "items": sorted({p[3] for p in P}), "drawn": sum(int(p[8]) for p in P), "tier_ok": all(not tiers.get(p[3]) or 1 in tiers[p[3]] for p in P if p[0] == "0" and p[1] == "0")}
    if P:
        p = P[0]; at = V(float(p[4]), float(p[5]), 0.0); S = g.get_section(I2(int(p[0]), int(p[1]))); room = S.room_at(at)
        # (beside its table, in its room: the room's free tiles are 3 m apart, too far for F's 2 m)
        st = None
        for r_ in (120.0, 150.0, 175.0):
            for k in range(16):
                q = V(at.x + math.cos(k * math.pi / 8) * r_, at.y + math.sin(k * math.pi / 8) * r_, 0.0)
                if S.room_at(q) != room: continue
                put(q, face(q, at, -30)); yield from wait(0.15)
                hl = G["pawn"].get_actor_location()
                if dist2(hl, at) < 190.0 and str(g.describe_nearest(hl, 260.0)).startswith("take the"): st = q; break
            if st: break
        st = st or V(at.x - 150, at.y, 0)
        put(st, face(st, at, -30)); face(st, at, -30); yield from wait(0.5)
        hl = G["pawn"].get_actor_location()
        res["stand"] = {"room": room, "at": [round(at.x), round(at.y)], "st": [round(st.x), round(st.y)], "her": [round(hl.x), round(hl.y), round(hl.z)], "her_d": round(dist2(hl, at))}
        res["describe"] = str(g.describe_nearest(hl, 260.0))
        shot("pickup_before"); yield from rwait(0.6)
        n0 = c.get_item_count(p[3]) + sum(1 for d in g.get_editor_property("weapons") if str(d.item) == p[3])
        why = yield from slate_hold("F", 0.08); yield from wait(0.3)
        res["f_refused"] = why
        n1 = c.get_item_count(p[3]) + sum(1 for d in g.get_editor_property("weapons") if str(d.item) == p[3])
        after = [str(l).split("|") for l in g.get_pickup_lines()]
        mine = next((a for a in after if a[0] == p[0] and a[1] == p[1] and a[2] == p[2]), None)
        res["took"] = {"item": p[3], "gained": n1 - n0, "taken_flag": mine[7] if mine else None, "drawn": mine[8] if mine else None, "taken_total": g.pickups_taken}
        shot("pickup_after"); yield from rwait(0.6)
    quiet(False)
    t = res.get("took", {})
    ok = (res["pickups"] >= 4 and res["drawn"] == res["pickups"] and res["tier_ok"] and res.get("describe", "").startswith("take the") and not res.get("f_refused")
          and t.get("gained") == 1 and t.get("taken_flag") == "1" and t.get("drawn") == "0" and t.get("taken_total") == 1)
    step_result("pickups", ok, **res)

def special_rooms():
    out = []
    for l in G["gen"].get_special_room_lines():
        p = str(l).split("|"); out.append({"s": I2(int(p[0]), int(p[1])), "room": int(p[2]), "kind": p[3], "at": V(float(p[4]), float(p[5]), float(p[6])), "done": int(p[7])})
    return out
def step_rooms():
    """the special rooms: shrines (a blessing), healing / speed / mana fountains (once each), an arena (its doors shut, three
    waves, won: its doors open, a prize), a trap gauntlet (its traps, a chest), a vault (locked; its key in another room's
    chest; opened, its chests hold the tier beyond's things), a throne room (its usurper slain: a slash for the Warrior)"""
    c = yield from restart("Warrior"); g = G["gen"]; quiet(True)
    res = {"kinds": {}, "refused": []}
    # (more sets of rooms: tier 2 opened (the start set cleared), its four nearest sets generated)
    g.debug_clear_section(I2(0, 0), 0, V(0, 0, 0)); yield from wait(0.5)
    for s_ in (I2(1, 0), I2(-1, 0), I2(0, 1), I2(0, -1), I2(1, 1)):
        if g.is_tier_open(2) and not g.is_section_generated(s_): g.generate_section_now(s_); yield from built(s_)
    # (the rarer kinds (a throne room) may be in none of those: the rest of tier 2's sets until all eight are there)
    for s_ in (I2(-1, 1), I2(-1, -1), I2(1, -1)):
        if len({r["kind"] for r in special_rooms()}) >= 8: break
        if not g.is_section_generated(s_): g.generate_section_now(s_); yield from built(s_)
    SR = special_rooms()
    for r in SR: res["kinds"].setdefault(r["kind"], 0); res["kinds"][r["kind"]] += 1
    def first(kind): return next((r for r in special_rooms() if r["kind"] == kind and r["done"] == 0), None)
    def go(r, lo=120, hi=230):
        S = g.get_section(r["s"]); st = stand_near(S, r["room"], r["at"], lo, hi) or V(r["at"].x - 180, r["at"].y, 0)
        put(st, face(st, r["at"], -15)); face(st, r["at"], -15); return S
    def go_use(r):
        """beside a fixture, within F's reach (2.8 m): points round it in its room, the first from which F names it"""
        S = g.get_section(r["s"])
        for r_ in (150.0, 190.0, 230.0, 120.0):
            for k in range(16):
                q = V(r["at"].x + math.cos(k * math.pi / 8) * r_, r["at"].y + math.sin(k * math.pi / 8) * r_, 0.0)
                if S.room_at(q) != r["room"]: continue
                put(q, face(q, r["at"], -15)); yield from wait(0.12)
                hl = G["pawn"].get_actor_location()
                dn = str(g.describe_nearest(hl, 280.0))
                if dist2(hl, r["at"]) < 260.0 and any(w_ in dn for w_ in ("shrine", "fountain")): return S
        return go(r)
    # ---- the shrine
    r = first("Shrine")
    if r:
        yield from go_use(r); yield from wait(0.5)
        d0 = c.get_damage_of(0); a0 = c.get_bless_armour(); sp0 = c.get_speed_bonus()
        res["shrine"] = {"describe": str(g.describe_nearest(G["pawn"].get_actor_location(), 280.0)), "f": str(g.interact_nearest(G["pawn"].get_actor_location(), 280.0))}
        yield from wait(0.3)
        res["shrine"].update({"blessing": str(c.get_blessing()), "damage_x": round(c.get_damage_of(0) / max(d0, 1e-3), 3), "armour": round(c.get_bless_armour() - a0, 3),
                              "speed": round(c.get_speed_bonus() - sp0, 3), "again": str(g.interact_nearest(G["pawn"].get_actor_location(), 280.0))})
        shot("room_shrine"); yield from rwait(0.6)
    # ---- the fountains (the mana one as the Mage)
    for kind, key_ in (("Healing fountain", "heal"), ("Fountain of speed", "speed")):
        r = first(kind)
        if not r: continue
        yield from go_use(r); yield from wait(0.4)
        c.set_health(c.get_max_health() * 0.3); h0 = c.get_health(); s0 = walk_speed()
        f = str(g.interact_nearest(G["pawn"].get_actor_location(), 280.0)); yield from wait(0.3)
        res[key_] = {"f": f, "hp_gain": round((c.get_health() - h0) / c.get_max_health(), 3), "speed_x": round(walk_speed() / max(s0, 1), 3), "speed_bonus": round(c.get_speed_bonus(), 3),
                     "again": str(g.interact_nearest(G["pawn"].get_actor_location(), 280.0)), "particles": g.get_particles_near(r["at"], 400)}
        shot(f"room_{key_}"); yield from rwait(0.6)
    r = first("Fountain of mana")
    if r:
        g.switch_hero("Mage"); yield from wait(0.6); refresh(); c = cb(); quiet(True)
        yield from go_use(r); yield from wait(0.4); c.set_mana(0.0); m0 = c.get_mana()
        f = str(g.interact_nearest(G["pawn"].get_actor_location(), 280.0)); yield from wait(0.3)
        res["mana"] = {"f": f, "mana": [round(m0, 1), round(c.get_mana(), 1), round(c.get_max_mana(), 1)], "again": str(g.interact_nearest(G["pawn"].get_actor_location(), 280.0))}
        shot("room_mana"); yield from rwait(0.6)
        g.switch_hero("Warrior"); yield from wait(0.6); refresh(); c = cb(); quiet(True)
    # ---- the arena
    r = first("Arena")
    if r:
        S = g.get_section(r["s"]); doors = list(S.get_room_doors(r["room"]))
        for d in doors:
            if not S.is_target_open(True, d): S.push_door(d, S.get_door_location(d))
        yield from wait(0.5)
        res["arena"] = {"doors": len(doors), "open_before": sum(1 for d in doors if S.is_target_open(True, d)), "began": g.start_arena(r["s"], r["room"])}
        yield from wait(1.5)
        res["arena"]["doors_open_after_begin"] = sum(1 for d in doors if S.is_target_open(True, d))
        # (a door pushed while it is fought: stays shut)
        if doors: S.push_door(doors[0], S.get_door_location(doors[0]))
        yield from wait(0.2); res["arena"]["pushed_open"] = S.is_target_open(True, doors[0]) if doors else None
        res["arena"]["waves"] = []
        for _ in range(4):
            res["arena"]["waves"].append({"wave": g.get_arena_wave(), "left": g.get_arena_left()})
            if g.get_arena_wave() < 0: break
            kill_all_near(r["at"], 2500); yield from wait(1.0)
        res["arena"]["won"] = md(g.room_uses).get("arena_won", 0)
        res["arena"]["prize"] = [sorted(str(x) for x in p.things) for p in g.loot_piles if p and not p.hers and dist2(p.get_actor_location(), S.get_room_center(r["room"])) < 400]
        if doors: S.push_door(doors[0], S.get_door_location(doors[0]))
        yield from wait(0.3); res["arena"]["opens_after"] = S.is_target_open(True, doors[0]) if doors else None
    # ---- the trap gauntlet
    r = first("Trap gauntlet")
    if r:
        T = [t for t in trap_lines() if t["s"] == r["s"] and t["room"] == r["room"]]
        S = g.get_section(r["s"])
        chest = [i for i in range(S.get_num_containers()) if S.room_at(S.get_container_location(i)) == r["room"]]
        res["gauntlet"] = {"traps": len(T), "kinds": sorted({t["name"] for t in T}), "chests": len(chest),
                           "chest_loot": [str(x) for x in g.loot_list_of(r["s"], chest[0])] if chest else None}
        go(r, 300, 700); yield from wait(0.5); shot("room_gauntlet"); yield from rwait(0.6)
    # ---- the vault: one whose key's chest is still shut (the debug clear that opened tier 2 opened every container of the start set)
    def key_chest(rr):
        S_ = g.get_section(rr["s"])
        k_ = [i for i in range(S_.get_num_containers()) if "Vault Key" in [str(x) for x in g.loot_list_of(rr["s"], i)]]
        return k_[0] if k_ and not S_.is_container_looted(k_[0]) else None
    def vault_ready(): return next((rr for rr in special_rooms() if rr["kind"] == "Vault" and rr["done"] == 0 and key_chest(rr) is not None), None)
    r = vault_ready()
    for s_ in (I2(-1, -1), I2(1, -1), I2(-1, 1), I2(1, 0), I2(-1, 0), I2(0, 1), I2(0, -1), I2(1, 1)):
        # (which sets are built depends on where she has been: more of tier 2's until one holds such a vault)
        if r is not None: break
        if not g.is_section_generated(s_): g.generate_section_now(s_); yield from built(s_)
        r = vault_ready()
    r = r or first("Vault")
    if r:
        S = g.get_section(r["s"]); doors = list(S.get_room_doors(r["room"]))
        v = {"doors": len(doors)}
        if doors:
            dl = S.get_door_location(doors[0]); room_c = S.get_room_center(r["room"])
            out = V(dl.x + (dl.x - room_c.x) / max(dist2(dl, room_c), 1) * 150, dl.y + (dl.y - room_c.y) / max(dist2(dl, room_c), 1) * 150, 0)
            put(out, face(out, dl)); yield from wait(0.4)
            v["locked_f"] = str(g.interact_nearest(G["pawn"].get_actor_location(), 260.0)); yield from wait(0.3)
            v["open_without_key"] = S.is_target_open(True, doors[0])
            # (its key: in a chest of another room of the set)
            kc = [i for i in range(S.get_num_containers()) if "Vault Key" in [str(x) for x in g.loot_list_of(r["s"], i)]]
            v["key_chests"] = len(kc)
            if kc:
                cl = S.get_container_location(kc[0]); v["key_room"] = S.room_at(cl)
                # (F at its chest: points round it, the first from which F names a container)
                # (nearest first: F opens the nearest container, which beside a shelf of chests may be another one)
                v["key_chest_f"] = None; v["other_opened"] = 0
                for r_ in (95.0, 120.0, 150.0, 180.0):
                    for k in range(16):
                        q = V(cl.x + math.cos(k * math.pi / 8) * r_, cl.y + math.sin(k * math.pi / 8) * r_, 0.0)
                        if S.room_at(q) != v["key_room"]: continue
                        put(q, face(q, cl, -25)); yield from wait(0.12)
                        if not str(g.describe_nearest(G["pawn"].get_actor_location(), 260.0)).startswith("open"): continue
                        v["key_chest_f"] = str(g.interact_nearest(G["pawn"].get_actor_location(), 260.0)); yield from wait(0.6)
                        if S.is_container_looted(kc[0]): break
                        v["other_opened"] += 1
                    if S.is_container_looted(kc[0]): break
                v["has_key"] = c.get_item_count("Vault Key")
                if v["has_key"] == 0:
                    c.add_item("Vault Key", 1); v["key_given_by_test"] = True
                put(out, face(out, dl)); yield from wait(0.4)
                v["f"] = str(g.interact_nearest(G["pawn"].get_actor_location(), 260.0)); yield from wait(0.8)
                v["open_with_key"] = S.is_target_open(True, doors[0]); v["key_after"] = c.get_item_count("Vault Key")
                vc = [i for i in range(S.get_num_containers()) if S.room_at(S.get_container_location(i)) == r["room"]]
                v["vault_chests"] = len(vc); v["vault_loot"] = [str(x) for x in g.loot_list_of(r["s"], vc[0])] if vc else None
                tier = g.tier_of(r["s"]); tiers = {str(i.name): list(i.tiers) for i in g.get_editor_property("items")}
                v["tier_beyond"] = [tiers.get(x, []) for x in (v["vault_loot"] or [])][:2]
                go(r, 200, 500); yield from wait(0.4); shot("room_vault"); yield from rwait(0.6)
        res["vault"] = v
    # ---- the throne room
    r = first("Throne room")
    if r:
        E_ = [str(l).split("|") for l in g.get_encounter_lines()]
        us = [e for e in E_ if "USURPER" in e[7]]
        t = {"encounters": len(us), "label": us[0][7] if us else None}
        go(r, 300, 700); yield from wait(0.6); shot("room_throne"); yield from rwait(0.6)
        given0 = len(g.slashes_given)
        # (a usurper standing now: one whose set of rooms was dropped (far from her) has no monster until it is built again)
        pick_ = None
        for u_ in us:
            at = V(float(u_[1]), float(u_[2]), float(u_[3]))
            ms = [m for m in g.get_monsters() if alive(m) and m.boss and dist2(m.get_actor_location(), at) < 800]
            if ms: pick_ = (u_, at, ms); break
        if pick_:
            u_, at, ms = pick_
            t["alive"] = len(ms)
            for m in ms: m.apply_damage(1e7, None)
            yield from wait(0.8)
            t["slain_notice"] = str(g.tier_notice); t["usurper_uses"] = md(g.room_uses).get("usurper", 0)
            t["slashes_given"] = [str(x) for x in g.slashes_given][given0:]
            t["slash_in_pack"] = [str(x) for x in c.get_all_inventory_lines() if str(x).startswith("slash|")]
        res["throne"] = t
    quiet(False)
    k = res["kinds"]; sh, he, spd, mn, ar, ga, va, th = (res.get(x, {}) for x in ("shrine", "heal", "speed", "mana", "arena", "gauntlet", "vault", "throne"))
    bless_ok = sh.get("f") == "shrine" and sh.get("again") == "shrine used" and (abs(sh.get("damage_x", 0) - 1.25) < 0.01 or abs(sh.get("armour", 0) - 0.25) < 0.01 or abs(sh.get("speed", 0) - 0.2) < 0.01)
    ok = (len(k) == 8 and bless_ok
          and he.get("f") == "fountain" and abs(he.get("hp_gain", 0) - 0.6) < 0.02 and he.get("again") == "fountain dry"
          and spd.get("f") == "fountain" and abs(spd.get("speed_bonus", 0) - 0.3) < 0.005 and spd.get("again") == "fountain dry"
          and mn.get("f") == "fountain" and mn.get("mana", [0, 0, 1])[1] == mn.get("mana", [0, 0, 1])[2] and mn.get("again") == "fountain dry"
          and ar.get("began") and ar.get("doors_open_after_begin") == 0 and ar.get("pushed_open") is False and ar.get("won") == 1 and ar.get("prize") and ar.get("opens_after")
          and [w["left"] > 0 for w in ar.get("waves", [])][:3] == [True, True, True]
          and ga.get("traps", 0) >= 3 and ga.get("chests", 0) >= 1 and len(ga.get("chest_loot") or []) >= 3
          and va.get("locked_f") == "vault locked" and va.get("open_without_key") is False and va.get("key_chests") == 1 and va.get("key_room") != None and va.get("has_key") == 1 and not va.get("key_given_by_test")
          and va.get("f") == "vault" and va.get("open_with_key") and va.get("key_after") == 0 and va.get("vault_chests", 0) >= 1 and va.get("vault_loot")
          and th.get("encounters", 0) >= 1 and th.get("alive") == 1 and th.get("usurper_uses") == 1 and len(th.get("slashes_given", [])) == 1)
    step_result("rooms", ok, **res)

def slash_trial(c, name, idx):
    """one slash on her drawn weapon (Index), struck at a harmless monster before her (as a blow that lands, ApplySlashHitNow);
    its effect measured on the monster, on others round it, or on her"""
    g = G["gen"]; p = G["pawn"]; L = p.get_actor_location(); f = p.get_actor_forward_vector(); r_ = p.get_actor_right_vector()
    sd = next(s for s in g.get_editor_property("slashes") if str(s.name) == name)
    eff = sd.effect.name.lower()
    if c.get_item_count(name) < 1: c.add_item(name, 1)
    applied = c.apply_slash(name, idx)
    at0 = V(L.x + f.x * 150, L.y + f.y * 150, L.z - 90)
    main = spawn_dummy(at0); others = []
    if eff in ("chain", "inferno", "void", "tide"):
        # (two within reach of it, one well beyond)
        # (two within its reach (2.3 m before it and 2.3 m beside it), one well beyond (11 m))
        for off, side in ((230, 0.0), (0, 2.3), (1100, 0.0)):
            q = V(at0.x + f.x * off + r_.x * side * 100, at0.y + f.y * off + r_.y * side * 100, at0.z); others.append(spawn_dummy(q))
    yield from wait(0.4)
    hp = lambda m: m.get_health() if alive(m) else None
    pos = lambda m: m.get_actor_location() if alive(m) else None
    h0 = hp(main); o_h0 = [hp(m) for m in others]; o_p0 = [pos(m) for m in others]; m_p0 = pos(main)
    c.set_health(c.get_max_health() * 0.5); her0 = c.get_health()
    procs0 = md(c.slash_procs); bonus0 = c.slash_bonus_dealt
    ok_hit = c.apply_slash_hit_now(idx, main)
    fx_now = c.get_slash_fx_alive(); yield from rwait(0.15); fx_soon = c.get_slash_fx_alive()
    r = {"applied": applied, "effect": eff, "hit": ok_hit, "bonus": round(c.slash_bonus_dealt - bonus0, 2), "want_bonus": sd.bonus, "fx": max(fx_now, fx_soon)}
    r["procs"] = {k: v - procs0.get(k, 0) for k, v in md(c.slash_procs).items() if v != procs0.get(k, 0)}
    yield from wait(0.25)
    h1 = hp(main)
    if eff == "burn" or eff == "poison" or eff == "magma":
        r["burning"] = main.is_burning() if alive(main) else None
        yield from wait(max(sd.seconds, 1.0) + 0.6); r["dot"] = round((h1 or 0) - (hp(main) or 0), 2)
        r["want_dot"] = round((c.get_damage_of(idx) + sd.bonus) * sd.amount if eff == "burn" else sd.amount if eff == "poison" else sd.amount * sd.seconds * 0.9, 1)
        r["ok"] = r["dot"] > r["want_dot"] * 0.6
    elif eff == "slow": r["slow"] = round(main.get_slow_share(), 3); r["ok"] = abs(r["slow"] - sd.amount) < 0.01
    elif eff == "swift": r["speed_bonus"] = round(c.get_speed_bonus(), 3); r["ok"] = abs(r["speed_bonus"] - sd.amount) < 0.01
    elif eff == "drain": r["healed"] = round(c.get_health() - her0, 2); r["want"] = round((c.get_damage_of(idx) + sd.bonus) * sd.amount, 2); r["ok"] = abs(r["healed"] - r["want"]) < 1.0
    elif eff == "knockback":
        yield from wait(1.2); r["moved_cm"] = round(dist2(pos(main), m_p0)) if alive(main) else None; r["want_cm"] = sd.amount
        r["ok"] = sd.amount * 0.6 < (r["moved_cm"] or 0) < sd.amount * 1.6
    elif eff == "regen":
        # (two more hits: renewed, not added up (the PR review's find: each hit added another 1.5 HP/s))
        c.apply_slash_hit_now(idx, main); c.apply_slash_hit_now(idx, main)
        r["regen"] = round(c.get_regen_per_second(), 3); r["ok"] = abs(r["regen"] - sd.amount) < 0.05
    elif eff == "evade": r["evade"] = round(c.get_slash_evade(), 3); r["ok"] = abs(r["evade"] - sd.amount) < 0.01
    elif eff == "shield":
        # (her hit points can rise meanwhile: the regeneration slash's trial may still be healing her; the shield's own count says it)
        # (the petal slash's evasion from the trial before may still be on: it dodged the test's blow before the shield took it)
        t_ = time.time()
        while c.get_slash_evade() > 0 and time.time() - t_ < 5.0: yield
        r["up"] = c.has_slash_shield(); hb = c.get_health(); st0 = md(c.slash_procs).get("shield_took", 0); c.apply_damage(20.0, None); yield from wait(0.1)
        r["absorbed"] = md(c.slash_procs).get("shield_took", 0) - st0 == 1 and c.get_health() >= hb - 0.01; r["down_after"] = not c.has_slash_shield(); r["ok"] = r["up"] and r["absorbed"] and r["down_after"]
    elif eff == "chain":
        r["spawned"] = [bool(m) for m in others]
        r["others_lost"] = [round((a or 0) - (hp(m) or 0), 1) for a, m in zip(o_h0, others)]; r["ok"] = all(r["spawned"]) and r["others_lost"][0] > 0 and r["others_lost"][1] > 0 and r["others_lost"][2] == 0
    elif eff == "blind": r["blind"] = round(main.get_blind_share(), 3); r["ok"] = abs(r["blind"] - sd.amount) < 0.01
    elif eff == "tide":
        yield from wait(0.6); r["slow"] = round(main.get_slow_share(), 3); r["moved_cm"] = round(dist2(pos(main), m_p0)) if alive(main) else None
        r["ok"] = abs(r["slow"] - sd.amount) < 0.01 and (r["moved_cm"] or 0) > 120
    elif eff == "inferno":
        r["near_lost"] = round((o_h0[0] or 0) - (hp(others[0]) or 0), 1); r["near_burning"] = others[0].is_burning() if alive(others[0]) else None
        r["far_lost"] = round((o_h0[2] or 0) - (hp(others[2]) or 0), 1); r["ok"] = r["near_lost"] > 0 and r["near_burning"] and r["far_lost"] == 0
    elif eff == "curse": r["curse"] = round(main.get_curse_share(), 3); r["ok"] = abs(r["curse"] - sd.amount) < 0.01
    elif eff == "haste":
        r["haste"] = round(c.get_haste(), 3)
        c.start_attack(); yield from wait(0.05); r["swing_s"] = round(c.get_attack_length(), 3); yield from wait(1.5)
        r["ok"] = abs(r["haste"] - sd.amount) < 0.01
    elif eff == "deflect": r["deflect"] = round(c.get_slash_deflect(), 3); r["ok"] = abs(r["deflect"] - sd.amount) < 0.01
    elif eff == "void":
        yield from wait(1.0)
        r["closer_cm"] = [round(dist2(a, m_p0) - dist2(pos(m), m_p0)) if (a and alive(m)) else None for a, m in zip(o_p0, others)]; r["slow"] = round(others[0].get_slow_share(), 3) if alive(others[0]) else None
        r["ok"] = (r["closer_cm"][0] or 0) > 60 and (r["closer_cm"][2] or 0) < 30 and abs((r["slow"] or 0) - sd.amount) < 0.01
    elif eff == "stun":
        r["stunned"] = main.is_stunned(); c.apply_slash_hit_now(idx, main); r["second_waits"] = md(c.slash_procs).get("stun_wait", 0) > procs0.get("stun_wait", 0)
        r["ok"] = r["stunned"] and r["second_waits"]
    elif eff == "prismatic":
        r["ok"] = r["procs"].get("prismatic", 0) == 1 and any(k in r["procs"] for k in ("burn", "slow", "poison", "drain"))
    # (the bonus on the monster struck; a chain or an inferno deal more to the others round it, counted too)
    r["ok"] = bool(r.get("ok")) and applied and ok_hit and (abs(r["bonus"] - sd.bonus) < 0.6 or (eff in ("chain", "inferno") and r["bonus"] >= sd.bonus - 0.6)) and r["fx"] > 0
    drop([main] + others); c.remove_slash(idx)
    return r

def step_slashes():
    """the slashes: a boss slain gives the Warrior one of its tier; through the inventory (keys as the keyboard sends them) it goes
    on a weapon, T takes it off, it goes on another (the bow); a real swing with it (its effect seen, its bonus dealt); then each of
    the twenty measured on a monster (or on her): burn, slow, poison, speed, drain, knockback, regeneration, evasion, the crystal
    shield, the chain, blindness, the tide, the inferno, the curse, haste, deflection, magma, the void, the stun, the prism"""
    c = yield from restart("Warrior"); g = G["gen"]; quiet(True)
    ctr = g.get_start_room_center(); put(V(ctr.x + 300, ctr.y + 300, ctr.z), 0.0); yield from wait(0.5)
    res = {"refused": []}
    # (a boss: Mistward's at tier 2's opening (the start set cleared); level 5 has none: a throne room's usurper (the rooms step))
    given0 = len(g.slashes_given)
    if g.get_editor_property("boss_encounters"):
        g.debug_clear_section(I2(0, 0), 0, V(0, 0, 0)); yield from wait(1.5)
        E_ = [str(l).split("|") for l in g.get_encounter_lines()]; boss = [e for e in E_ if e[0] == "boss" and "USURPER" not in e[7]]
        if boss:
            at = V(float(boss[0][1]), float(boss[0][2]), float(boss[0][3]))
            for m in g.get_monsters():
                if alive(m) and dist2(m.get_actor_location(), at) < 600: m.apply_damage(1e7, None)
            yield from wait(0.8)
    res["boss_gave"] = [str(x) for x in g.slashes_given][given0:]
    tiers = {str(s.name): s.tier for s in g.get_editor_property("slashes")}
    res["boss_slash_tier"] = [tiers.get(x) for x in res["boss_gave"]]
    # (through the inventory: the magic tab, its row, Enter, Enter on the Dagger)
    for n in ("Ember Slash", "Longbow"): c.add_item(n, 1)
    c.set_inventory_open(True); yield from rwait(0.3)
    for nm in ("E", "E", "E", "E"): yield from slate_hold(nm, 0.06)
    res["tab"] = c.get_inventory_tab()
    srow = next((i for i, l in enumerate(lines(c)) if l == "slash|Ember Slash|1"), None)
    yield from cursor_to(c, srow)
    yield from slate_hold("Enter", 0.08); res["picking"] = c.is_picking_slash(); res["pick_lines"] = [str(x) for x in c.get_slash_lines()]
    shot("slash_pick"); yield from rwait(0.5)
    yield from slate_hold("Enter", 0.08)
    W = g.get_editor_property("weapons"); res["on_dagger"] = str(W[0].slash)
    # (T on the Dagger's row: off again; then onto the Longbow)
    c.set_inventory_tab(0); yield from rwait(0.2)
    yield from cursor_to(c, 0)
    yield from slate_hold("T", 0.08); res["off_dagger"] = str(g.get_editor_property("weapons")[0].slash); res["back_in_pack"] = c.get_item_count("Ember Slash")
    bi = next(i for i, w in enumerate(g.get_editor_property("weapons")) if str(w.name) == "Longbow")
    res["on_bow"] = c.apply_slash("Ember Slash", bi); res["bow_slash"] = str(g.get_editor_property("weapons")[bi].slash)
    c.set_inventory_open(False); yield from rwait(0.3)
    # (a real swing with the Ember Slash on the Dagger, at a monster before her: its effect alive, its bonus dealt; a picture at the hit)
    c.remove_slash(bi); c.apply_slash("Ember Slash", 0); c.select_weapon(0); yield from wait(0.3)
    p = G["pawn"]; L = p.get_actor_location(); f = p.get_actor_forward_vector()
    m = spawn_dummy(V(L.x + f.x * 130, L.y + f.y * 130, L.z - 90)); yield from wait(0.4)
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=p.get_actor_rotation().yaw + 40))
    b0 = c.slash_bonus_dealt; h0 = m.get_health() if alive(m) else None
    res["swing"] = {"started": c.start_attack()}
    t0 = time.time(); fx_max = 0; shot_done = False
    while time.time() - t0 < 1.6:
        yield
        fx_max = max(fx_max, c.get_slash_fx_alive())
        if not shot_done and c.get_slash_fx_alive() > 0: shot("slash_swing"); shot_done = True
    res["swing"].update({"fx_max": fx_max, "bonus": round(c.slash_bonus_dealt - b0, 2), "monster_lost": round((h0 or 0) - (m.get_health() if alive(m) else 0), 1), "pictured": shot_done})
    drop([m]); c.remove_slash(0)
    # (the ranged one: the Ember Slash on the Longbow, a shot at a monster)
    c.apply_slash("Ember Slash", bi); c.select_weapon(bi); yield from wait(0.4)
    m = spawn_dummy(V(L.x + f.x * 600, L.y + f.y * 600, L.z - 90)); yield from wait(0.4)
    b0 = c.slash_bonus_dealt; c.start_attack(); yield from wait(2.0)
    res["shot"] = {"bonus": round(c.slash_bonus_dealt - b0, 2), "procs": md(c.slash_procs).get("burn", 0)}
    drop([m]); c.remove_slash(bi); c.select_weapon(0); yield from wait(0.3)
    # (each of the twenty on the Dagger; the monsters near her cleared first: a chain or a void reaches whoever is near)
    kill_all_near(G["pawn"].get_actor_location(), 2500); yield from wait(0.5)
    res["each"] = {}
    for sd in g.get_editor_property("slashes"):
        try: res["each"][str(sd.name)] = yield from slash_trial(c, str(sd.name), 0)
        except Exception as e: res["each"][str(sd.name)] = {"ok": False, "error": str(e)}
        yield from wait(0.3)
    quiet(False)
    ev = res["each"]; sw = res["swing"]
    ok = ((not g.get_editor_property("boss_encounters") or (len(res["boss_gave"]) == 1 and res["boss_slash_tier"] == [2]))
          and res["tab"] == 4 and res["picking"] and res["on_dagger"] == "Ember Slash" and res["off_dagger"] == "None" and res["back_in_pack"] == 1
          and res["on_bow"] and res["bow_slash"] == "Ember Slash" and sw["started"] and sw["fx_max"] > 0 and abs(sw["bonus"] - 6.0) < 0.6 and sw["monster_lost"] > 6
          and res["shot"]["bonus"] > 0 and len(ev) == 20 and all(v.get("ok") for v in ev.values()))
    step_result("slashes", ok, **res)

def step_tomemana():
    """the user's of 2026-10-28 (871): the Mage's pool is 100, 200 with the best Magic Potency Ring; Null Sanctum's tome found
    makes it 220 (the message says so, her mana goes up by what the pool did) and the sanctum is cast (220 taken); the ring
    off, it stays 220; Apocalypse's makes it 300 and it is cast (300 taken); she falls and is back: both spells and the 300
    are still hers; a restart forgets them (100); the Summoner (no TomeMana) learns the sanctum with her pool unchanged"""
    c = yield from restart("Mage"); g = G["gen"]; quiet(True)
    put(g.get_start_room_center(), 0.0); yield from wait(0.3)
    K = unreal.RDItemKind
    tome = {str(i.spell): str(i.name) for i in items_of(K.TOME)}
    ring = max((i for i in items_of(K.RING) if i.ring_kind == unreal.RDRingKind.MAGIC), key=lambda i: i.amount)
    def widx(sp): return next((k for k, d in enumerate(g.get_editor_property("weapons")) if str(d.name) == sp), -1)
    res = {"tomes": {s: tome.get(s) for s in ("Null Sanctum", "Apocalypse")}, "ring": str(ring.name), "tome_mana": c.get_tome_mana()}
    res["base"] = round(c.get_max_mana(), 1)
    c.add_item(str(ring.name), 1); c.wear_ring(str(ring.name)); yield from wait(0.2)
    res["ringed"] = round(c.get_max_mana(), 1)
    def learn_and_cast(sp):
        c.set_mana(c.get_max_mana()); m0 = c.get_mana(); p0 = c.get_max_mana()
        c.add_item(tome[sp], 1); yield from wait(0.2)
        r = {"knows": c.knows_spell(sp), "pool": round(c.get_max_mana(), 1), "pool_before": round(p0, 1), "mana_gain": round(c.get_mana() - m0, 1),
             "message": str(c.message), "tome_mana": c.get_tome_mana()}
        i = widx(sp); r["index"] = i
        c.set_mana(c.get_max_mana()); m1 = c.get_mana()
        r["cast"] = bool(c.start_attack_with(i)) if i >= 0 else False
        r["mana_taken"] = round(m1 - c.get_mana(), 1)
        yield from wait(3.5)
        return r
    res["sanctum"] = yield from learn_and_cast("Null Sanctum")
    c.wear_ring(str(ring.name)); yield from wait(0.2)              # (worn: taken off)
    res["ring_off"] = round(c.get_max_mana(), 1)
    res["apocalypse"] = yield from learn_and_cast("Apocalypse")
    # (she falls and is back: the spells learned stay, and the pool with them)
    c.apply_damage(c.get_health() + 50.0, None); yield from wait(1.0)
    res["dead"] = c.is_dead()
    t0 = time.time()
    while c.is_dead() and time.time() - t0 < 20: yield
    yield from wait(1.0)
    res["after_death"] = {"revived": not c.is_dead(), "knows": [c.knows_spell("Null Sanctum"), c.knows_spell("Apocalypse")], "pool": round(c.get_max_mana(), 1)}
    g.restart_play(0); yield from wait(1.0); refresh(); c = cb()
    res["after_restart"] = {"knows": [c.knows_spell("Null Sanctum"), c.knows_spell("Apocalypse")], "pool": round(c.get_max_mana(), 1)}
    # (the Summoner learns every type but has no TomeMana: her pool stays)
    if any(str(h.name) == "Summoner" for h in g.get_editor_property("heroes")):
        g.switch_hero("Summoner"); yield from wait(0.6); refresh(); c = cb()
        p0 = c.get_max_mana(); c.add_item(tome["Null Sanctum"], 1); yield from wait(0.2)
        res["summoner"] = {"knows": c.knows_spell("Null Sanctum"), "pool_before": round(p0, 1), "pool": round(c.get_max_mana(), 1)}
        g.restart_play(0); yield from wait(0.8); refresh()
        g.switch_hero("Warrior"); yield from wait(0.6); refresh()
    else: g.switch_hero("Warrior"); yield from wait(0.6); refresh()
    quiet(False)
    s_, a_, d_ = res["sanctum"], res["apocalypse"], res["after_death"]
    ok = (res["base"] == 100 and res["ringed"] == 200 and res["tome_mana"] == 0
          and s_["knows"] and s_["pool"] == 220 and abs(s_["mana_gain"] - 20) < 0.6 and "grows to 220" in s_["message"] and s_["cast"] and abs(s_["mana_taken"] - 220) < 0.6
          and res["ring_off"] == 220
          and a_["knows"] and a_["pool"] == 300 and abs(a_["mana_gain"] - 80) < 0.6 and "grows to 300" in a_["message"] and a_["cast"] and abs(a_["mana_taken"] - 300) < 0.6
          and res["dead"] and d_["revived"] and all(d_["knows"]) and d_["pool"] == 300
          and not any(res["after_restart"]["knows"]) and res["after_restart"]["pool"] == 100
          and (("summoner" not in res) or (res["summoner"]["knows"] and res["summoner"]["pool"] == res["summoner"]["pool_before"])))
    step_result("tomemana", ok, **res)

def ahead(cm, side=0.0):
    """a floor point cm in front of her (side cm to her right)"""
    p = G["pawn"]; L = p.get_actor_location(); f = p.get_actor_forward_vector(); r = p.get_actor_right_vector()
    return V(L.x + f.x * cm + r.x * side, L.y + f.y * cm + r.y * side, L.z - 90)

def hp(m): return m.get_health() if alive(m) else 0.0

def chi_trial(c, i, dist=260.0, splash_at=None, picture=None):
    """one chi attack (weapon i) at a dummy dist cm ahead: the mana it took, what the dummy lost, the effect's particles near
    it; with splash_at a second dummy that far beside the first (it takes half)"""
    g = G["gen"]; c.select_weapon(i); yield from wait(0.3)
    m = spawn_dummy(ahead(dist)); m2 = spawn_dummy(ahead(dist, splash_at)) if splash_at else None
    yield from wait(0.4)
    c.set_mana(c.get_max_mana()); m0 = c.get_mana(); h0 = hp(m); h2 = hp(m2) if m2 else 0.0
    W = g.get_editor_property("weapons")[i]; nm = str(W.name); r0 = md(c.spells_released).get(nm, 0)
    b0 = c.bolts_cast; started = c.start_attack_with(i); taken = round(m0 - c.get_mana(), 1)
    t0 = time.time(); fx = 0; pic = False; at = m.get_actor_location(); t_fx = None; seq = 0
    while time.time() - t0 < float(W.attack_ends[0]) + 0.8:
        yield
        n = c.get_spell_particles(at, 400.0); n = n[0] if isinstance(n, tuple) else n; fx = max(fx, n)
        # (the picture when the blow has landed: taken as the bolt left her hand, its long frame made a bolt miss (a chi bolt
        # flies; a Rend's blow did not))
        if picture and not pic and h0 - hp(m) > 0: shot(picture); pic = True; t_fx = time.time()
        # (a tag "probe...": the blast also pictured 0.2, 0.4 and 0.7 s after it began)
        if TAG.startswith("probe") and t_fx and seq < 3 and time.time() - t_fx >= (0.2, 0.4, 0.7)[seq]: seq += 1; shot(f"{picture}_{seq}")
    r = {"name": nm, "started": started, "mana": taken, "lost": round(h0 - hp(m), 1), "fx": fx, "released": md(c.spells_released).get(nm, 0) - r0, "bolts": c.bolts_cast - b0,
         "damage_of": round(c.get_damage_of(i), 1), "pictured": pic}
    if m2: r["splash_lost"] = round(h2 - hp(m2), 1)
    drop([m] + ([m2] if m2 else [])); yield from wait(0.3)
    return r

def step_martial():
    """the Martial Artist (872) in mistward_castle: 140 hit points, 100 mana; her fists (14 a blow, landing on a monster before
    her), the Dexterity ring adding to them and to her knives but not to her chi; a knife found: in both hands, +30 % (and the
    ring); a chi attack: its mana taken, its damage on the monster she faces within 4.2 m, the blast's half on one beside it,
    nothing on one out of reach; the dash: at the monster ahead, stopping short of it, and the strike after; the roll; a tier's
    boss slain teaches her the next two chi attacks (and two more asked for), kept through a death; a restart forgets them.
    A chi with no monster within its reach is refused and costs no mana"""
    c = yield from restart("MartialArtist"); g = G["gen"]; quiet(True)
    ctr = g.get_start_room_center(); put(V(ctr.x + 300, ctr.y + 300, ctr.z), 0.0); yield from wait(0.5)
    kill_all_near(G["pawn"].get_actor_location(), 1500); yield from wait(0.5)
    W = lambda: [str(w.name) for w in g.get_editor_property("weapons")]
    res = {"hero": str(g.get_editor_property("current_hero")), "hp": c.get_max_health(), "mana": c.get_max_mana(), "weapons": W(),
           "pawn": G["pawn"].get_class().get_name()}
    # (her fists: a strike at a dummy before her)
    c.select_weapon(0); yield from wait(0.3)
    m = spawn_dummy(ahead(120)); yield from wait(0.4); h0 = hp(m)
    res["fists"] = {"damage_of": round(c.get_damage_of(0), 1), "bonus": round(c.get_bonus_of(0), 3), "started": c.start_attack()}
    yield from wait(1.6); res["fists"]["lost"] = round(h0 - hp(m), 1); res["fists"]["hits"] = c.hits_landed; drop([m])
    # (the Dexterity ring: her fists and knives, not her chi)
    ring = max((i for i in items_of(unreal.RDItemKind.RING) if i.ring_kind == unreal.RDRingKind.DEXTERITY), key=lambda i: i.amount)
    c.add_item(str(ring.name), 1); res["ring_worn"] = c.wear_ring(str(ring.name)); yield from wait(0.2)
    res["ring"] = {"amount": ring.amount, "fists": round(c.get_damage_of(0), 1), "chi": round(c.get_damage_of(1), 1)}
    c.add_item("Dagger", 1); yield from wait(0.3)
    ki = next((k for k, w in enumerate(g.get_editor_property("weapons")) if str(w.name) == "Dagger"), -1)
    if ki >= 0:
        kw = g.get_editor_property("weapons")[ki]
        res["knife"] = {"index": ki, "damage": kw.damage, "damage_of": round(c.get_damage_of(ki), 1), "bonus": round(c.get_bonus_of(ki), 3),
                        "both_hands": bool(kw.mesh) and bool(kw.off_hand_mesh), "type": str(kw.weapon_type)}
        c.select_weapon(ki); yield from wait(0.3)
        m = spawn_dummy(ahead(120)); yield from wait(0.4); h0 = hp(m); c.start_attack(); yield from wait(1.0)
        res["knife"]["lost"] = round(h0 - hp(m), 1); drop([m]); shot("ma_knife")
    c.wear_ring(str(ring.name)); yield from wait(0.2)
    res["ring_off"] = {"fists": round(c.get_damage_of(0), 1), "knife": round(c.get_damage_of(ki), 1) if ki >= 0 else None}
    # (a chi attack: Straight Punch at 2.6 m, a second dummy 1 m beside; then one out of reach at 6 m)
    res["chi"] = yield from chi_trial(c, 1, 260.0, 100.0, "ma_chi_straight")
    res["chi_far"] = yield from chi_trial(c, 1, 600.0)
    # (the dash: at a dummy 6 m ahead, with her fists)
    c.select_weapon(0); yield from wait(0.3)
    m = spawn_dummy(ahead(600)); yield from wait(0.5); h0 = hp(m)
    d0 = dist2(G["pawn"].get_actor_location(), m.get_actor_location()); a0 = c.attacks_made
    res["dash"] = {"started": c.start_dash(), "before_m": round(d0 / 100, 2)}
    yield from wait(0.25); shot("ma_dash"); yield from wait(1.6)
    res["dash"].update({"after_m": round(dist2(G["pawn"].get_actor_location(), m.get_actor_location()) / 100, 2), "length": round(c.last_dash_length, 1),
                        "at_it": c.last_dash_target == m if c.last_dash_target else False, "attacked": c.attacks_made - a0, "lost": round(h0 - hp(m), 1), "dashes": c.dashes})
    drop([m])
    r0 = c.rolls; c.start_roll(V(0, 0, 0)); yield from wait(1.0); res["rolls"] = c.rolls - r0
    # (her armour: a light set worn (her own fit), a medium one refused; a picture of her in it)
    A = items_of(unreal.RDItemKind.ARMOUR)
    li = next(str(i.name) for i in A if i.armour_weight == unreal.RDArmourWeight.LIGHT); me = next(str(i.name) for i in A if i.armour_weight == unreal.RDArmourWeight.MEDIUM)
    for n in (li, me): c.add_item(n, 1)
    c.wear_armour(me); yield from wait(0.2); res["medium_worn"] = str(c.get_worn_armour())
    c.wear_armour(li); yield from wait(0.4); res["light_worn"] = str(c.get_worn_armour()); res["armour_share"] = round(c.get_armour(), 3)
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-8, yaw=G["pawn"].get_actor_rotation().yaw + 160)); yield from wait(0.5); shot("ma_armour")
    yield from rwait(0.6)
    # (a tier's boss slain: the next two; then two more asked for)
    n0 = len(W())
    if g.get_editor_property("boss_encounters"):
        g.debug_clear_section(I2(0, 0), 0, V(0, 0, 0)); yield from wait(1.5)
        E_ = [str(l).split("|") for l in g.get_encounter_lines()]; boss = [e for e in E_ if e[0] == "boss" and "USURPER" not in e[7]]
        if boss:
            at = V(float(boss[0][1]), float(boss[0][2]), float(boss[0][3]))
            for mo in g.get_monsters():
                if alive(mo) and mo.boss and dist2(mo.get_actor_location(), at) < 600: mo.apply_damage(1e7, None)
            yield from wait(0.8)
    res["boss"] = {"weapons": W()[n0:], "unlocked": g.weapons_unlocked}
    res["asked"] = g.unlock_hero_weapons(2); res["after_ask"] = W()[n0:]
    # (kept through a death)
    c.apply_damage(c.get_health() + 500.0, None); yield from wait(1.0)
    t0 = time.time()
    while c.is_dead() and time.time() - t0 < 20: yield
    yield from wait(1.0)
    res["after_death"] = W()
    g.restart_play(0); yield from wait(1.0); refresh(); c = cb()
    res["after_restart"] = W()
    g.switch_hero("Warrior"); yield from wait(0.6); refresh(); quiet(False)
    f_, ch, dsh = res["fists"], res["chi"], res["dash"]
    chi4 = ["Smashing Strike", "Roundhouse Kick", "Chain Punch", "Rear Kick"]
    ok = (res["hero"] == "MartialArtist" and res["hp"] == 140 and res["mana"] == 100 and res["weapons"] == ["Fists", "Straight Punch", "Side Kick"]
          and f_["damage_of"] == 14 and f_["lost"] >= 14 and abs(res["ring"]["fists"] - 14 * (1 + ring.amount)) < 0.2 and abs(res["ring"]["chi"] - 22) < 0.2
          and res.get("knife", {}).get("both_hands") and abs(res["knife"]["bonus"] - (0.3 + ring.amount)) < 0.01 and res["knife"]["lost"] > 0
          and abs(res["ring_off"]["knife"] - 11 * 1.3) < 0.2 and res["ring_off"]["fists"] == 14
          and ch["started"] and ch["mana"] == 7 and abs(ch["lost"] - 22) < 0.6 and ch["fx"] > 0 and abs(ch.get("splash_lost", 0) - 11) < 0.6
          and res["chi_far"]["lost"] == 0 and not res["chi_far"]["started"] and res["chi_far"]["mana"] == 0 and dsh["started"] and dsh["at_it"] and dsh["after_m"] < dsh["before_m"] - 2.5 and dsh["attacked"] >= 1 and dsh["lost"] > 0
          and res["rolls"] == 1 and res["light_worn"] == li and res["medium_worn"] == "None" and res["armour_share"] > 0)
    if g.get_editor_property("boss_encounters"):
        ok = ok and res["boss"]["weapons"] == chi4[:2] and res["after_ask"][-2:] == chi4[2:] and all(n in res["after_death"] for n in chi4)
    else:
        ok = ok and res["after_ask"] == chi4[:2] and all(n in res["after_death"] for n in chi4[:2])
    ok = ok and res["after_restart"] == ["Fists", "Straight Punch", "Side Kick"]
    step_result("martial", ok, **res)

def step_martialroom():
    """martial_arts (873): one room (its tiles, no section beyond), the Martial Artist alone with her fists and all ten chi
    attacks; three monsters in the room and one more after one falls; each chi attack cast on a monster within 4.2 m: its
    mana, its damage, its effect's particles, a picture at its blast; the dash"""
    c = yield from restart("MartialArtist"); g = G["gen"]
    S = g.get_section(I2(0, 0)); room = S.room_at(g.get_start_room_center())
    th = S.get_room_tiles(room); tiles = th[0] if isinstance(th, tuple) else th
    res = {"title": str(g.dungeon_title), "heroes": [str(h.name) for h in g.get_editor_property("heroes")], "rooms": S.get_num_rooms() if hasattr(S, "get_num_rooms") else None,
           "room_tiles": len(tiles), "beyond": [g.is_section_generated(I2(dx, dy)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))],
           "weapons": [str(w.name) for w in g.get_editor_property("weapons")]}
    t0 = time.time()
    while time.time() - t0 < 12 and len([m for m in g.get_monsters() if alive(m)]) < 3: yield
    res["monsters"] = len([m for m in g.get_monsters() if alive(m)]); s0 = g.one_room_spawned
    one = next((m for m in g.get_monsters() if alive(m)), None)
    if one: one.apply_damage(1e7, None)
    t0 = time.time()
    while time.time() - t0 < 10 and g.one_room_spawned == s0: yield
    res["respawned"] = g.one_room_spawned - s0
    quiet(True); kill_all_near(G["pawn"].get_actor_location(), 5000); yield from wait(0.5)
    g.set_editor_property("one_room_monsters", 0)          # (none come while the attacks are tried)
    put(g.get_start_room_center(), 0.0); yield from wait(0.5); shot("ma_room")
    res["chi"] = []
    for i, w in enumerate(g.get_editor_property("weapons")):
        if not w.spell: continue
        nm = str(w.name).replace(" ", "")
        res["chi"].append((yield from chi_trial(c, i, 260.0, None, "ma_" + nm)))
        put(g.get_start_room_center(), 0.0); yield from wait(0.3)
    # (with no monster at all: the chi goes off in front of her (bChiWithoutTarget), and her mana stays full (bInfiniteMana))
    kill_all_near(G["pawn"].get_actor_location(), 5000); yield from wait(0.5)
    ci = next(i for i, w in enumerate(g.get_editor_property("weapons")) if w.spell)
    c.select_weapon(ci); yield from wait(0.3); r0 = md(c.spells_released).get(str(g.get_editor_property("weapons")[ci].name), 0); m0 = c.get_mana()
    fa = ahead(250); fa = V(fa.x, fa.y, fa.z + 110); her = G["pawn"].get_actor_location(); bc0 = c.bolts_cast; st = c.start_attack_with(ci); fxn = 0; far = 0.0; seen = 0
    for _ in range(120):
        yield
        n = c.get_spell_particles(fa, 300.0); n = n[0] if isinstance(n, tuple) else n; fxn = max(fxn, n)
        for b in c.get_bolts(): far = max(far, dist2(b, her)); seen += 1
    res["free"] = {"started": st, "released": c.bolts_cast - bc0, "fx": fxn,
                   "mana_full": c.get_mana() == c.get_max_mana() and m0 == c.get_max_mana(), "bolt_farthest_m": round(far / 100, 2), "bolt_frames": seen}
    # (no bolt stays: each chi fired at nothing, and 2.5 s after its bolt burst none of her spell effects has a particle left
    # (the user's of 2026-10-28: "some of the bolts stick around, suspended in the air"))
    res["linger"] = {}
    if g.get_editor_property("chi_without_target"):
        for i, w in enumerate(g.get_editor_property("weapons")):
            if not w.spell: continue
            put(g.get_start_room_center(), 0.0); c.select_weapon(i); yield from wait(0.3)
            c.start_attack_with(i); t0 = time.time()
            while time.time() - t0 < float(w.attack_ends[0]) + 0.3: yield
            while c.get_bolts() and time.time() - t0 < 5.0: yield
            yield from wait(2.5)
            n = c.get_spell_particles(G["pawn"].get_actor_location(), 0.0); res["linger"][str(w.name)] = n[0] if isinstance(n, tuple) else n
    c.select_weapon(0); m = spawn_dummy(ahead(650)); yield from wait(0.5); d0 = dist2(G["pawn"].get_actor_location(), m.get_actor_location())
    res["dash"] = {"started": c.start_dash()}; yield from wait(1.6)
    res["dash"]["closed_m"] = round((d0 - dist2(G["pawn"].get_actor_location(), m.get_actor_location())) / 100, 2); drop([m])
    g.set_editor_property("one_room_monsters", 3); quiet(False)
    want = {c_["name"]: c_ for c_ in json.load(open(os.path.join(SA, "martial_arts", "martial_arts.json"), encoding="utf-8"))["chi"]}
    inf = g.get_editor_property("infinite_mana")
    good = [x for x in res["chi"] if x["started"] and x["bolts"] == 1 and want.get(x["name"]) and x["mana"] == (0 if inf else want[x["name"]]["mana"]) and abs(x["lost"] - want[x["name"]]["damage"]) < 0.6 and x["fx"] > 0]
    res["chi_ok"] = [x["name"] for x in good]
    # (with no monster the bolt flies to the end of its range: 4 m from her hand (it leaves 0.3 to 0.6 m out from her), no further)
    fr = res["free"]; free_ok = (fr["started"] and fr["released"] == 1 and fr["fx"] > 0 and 3.5 <= fr["bolt_farthest_m"] <= 4.8) if g.get_editor_property("chi_without_target") else not fr["started"]
    ok = (res["heroes"] == ["MartialArtist"] and res["room_tiles"] == 100 and not any(res["beyond"]) and len(res["weapons"]) == 11
          and res["monsters"] >= 3 and res["respawned"] >= 1 and len(good) == 10 and res["dash"]["started"] and res["dash"]["closed_m"] > 2.5
          and free_ok and (fr["mana_full"] or not inf) and all(v == 0 for v in res["linger"].values()))
    step_result("martialroom", ok, **res)

STEPS = {"menu": step_menu, "basics": step_basics, "shields": step_shields, "torch": step_torch, "armour": step_armour, "inventory": step_inventory, "open": step_open,
         "heights": step_heights, "tiers": step_tiers, "layout": step_layout, "traps": step_traps, "teleport": step_teleport, "cells": step_cells,
         "death": step_death, "outline": step_outline, "tabs": step_tabs, "slots": step_slots, "helmet": step_helmet, "block": step_block,
         "startgear": step_startgear, "pickups": step_pickups, "rooms": step_rooms, "slashes": step_slashes, "tomemana": step_tomemana,
         "martial": step_martial, "martialroom": step_martialroom}
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
