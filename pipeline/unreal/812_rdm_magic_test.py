"""random_dungeonmagic_level, random_dungeonmagic_level2 and random_dungeonmagic_level3 test, run in PIE (813_rdm_magic.ps1 starts PIE, arms this
and waits for "RDMTEST done"); the level is the one PIE plays. Drives the caster's combat component, the keys and the
generator and measures what happens. Plan = comma separated steps:
  setup     the pawn is the level's caster (random_dungeonmagic_level: BP_RDM_CasterCharacter, SK_JRPG_Caster, her one
            weapon the fire spell and nothing in her hands; random_dungeonmagic_level2: BP_RDM2_DarkCasterCharacter,
            SK_JRPG_DarkCaster, the sword in her right hand and the fire spell cast alongside it from her left;
            random_dungeonmagic_level3: BP_RDM3_RogueCharacter, SK_JRPG_Rogue, a dagger in each hand and the crossbow on
            her back, the roll set) in the middle of the start section with 100 hit points
  weapons   (level 3) her hands on the dagger handles and the crossbow's stock (the handle point of each mesh by the hand
            bone, the business end away from it); the crossbow carried on her back while the daggers are drawn, the
            daggers along the outside of her thighs while the crossbow is drawn (measured against her bones); 2 draws the
            crossbow, the mouse wheel and Y switch, 1 draws the daggers; the bolt lies on the crossbow's rail
  keys      the keys, pressed as on the keyboard (through her player controller): W walks her at her walk speed, Left
            Shift + W runs her at her run speed (both measured from her travel), A / S / D move her the way they should;
            the cast keys (level 1: E and the left mouse button; level 2: E and the right mouse button) each cast one
            bolt, and in level 2 the left mouse button swings the sword (no bolt); level 3: the left mouse button stabs
            with the daggers (no bolt) and shoots with the crossbow (a bolt), E and the right mouse do nothing; her character has no handler for the
            other actions the input context puts on those keys
  pad       the magic levels' controls (bCasterControls), pressed through her player controller: a key makes the keyboard
            the device in use and a gamepad button the gamepad (the HUD's controls panel follows it); the left stick held
            forward walks her at her walk speed, LT switches to running (her run speed) and back, R does the same with W
            held; the right stick turns the camera; A jumps; RB attacks with the weapon in her hand (level 1: the spell), LB casts the spell; RT and Y (the
            combat level's buttons) do nothing; X by a closed container opens it; Back opens the big map and closes it.
            Level 3: RB stabs with the daggers, LB and RT do nothing, Y switches to the crossbow (and back), B rolls
  walls     the broken walls (wall_check.py): rays from each broken segment's room on a grid over its face end on the
            wall or, through a hole, on the stone plate behind it (never beyond the wall); she pushes and jumps into
            holes low on the wall and stays out (without the plates the same rays went beyond the wall); every
            prison cell is closed all round (rays from its middle meet bars, a door or a wall), its hay pile blocks; dropped below the floor she is put back where she stood
  hair      (level 2) the Warlock's hair: she stands, runs, stops, jumps and is teleported; the tips swing away from where
            her head carries them (over 5 cm) and settle when she stands (under 4 cm of jitter); the hair bones keep their
            length standing (8 %), running (45 %) and landing (60 %: the solver's joints give for a moment), the back
            strands' tips keep their gaps (within 20 cm), the hair keeps out of the spheres round her head, face and
            chest and above the plane on her back (2 cm at most)
  cast      9 m from a monster she can see: one cast. The charge's particles burn at her casting hand while she winds up;
            the cast clip plays (her hand moves); at the release a bolt leaves her hand, flies at the spell's speed
            (measured between frames), with particles alive around it, and bursts on that monster: it loses the spell's
            damage, particles burn where it burst, the light is out a moment later; the charge, cast and burst sounds
            are played once each
  nothing   no monster within the spell's reach: she does not turn, the bolt flies straight on and bursts on a wall or at
            the end of its reach, nobody is hurt (level 3: the bolt stays stuck in the wall)
  far       a monster 18 m away (beyond the reach; level 3: 30 m, the crossbow reaches 26): not taken as the target
  kill[:N]  N times: from 9 m from the nearest live monster of the start section she casts until it is dead: each bolt
            that bursts on it takes the spell's damage, the kill is counted, the bolts needed match its hit points
  sword[:N] (level 2) N times: beside the nearest live monster of the start section she cuts with the sword until it is
            dead: every blow takes the sword's damage, the kill is counted
  daggers[:N] (level 3) as sword with the daggers
  roll      (level 3) B standing: a backward roll, she keeps facing the way she did and is carried ~ the roll's distance
            back, her middle goes down near the floor and comes up again; with W held: a roll forward the way she
            walks; a second B during a roll does nothing; the gamepad's B rolls too; she can strike right after
  dodge     (level 3) a monster's blow (ApplyDamage, as the monsters call it) in the middle of a roll misses her (counted);
            the same blow after it takes her hit points
  dual      (level 2) a cast while the sword is drawn: the sword stays in her right hand all through it, the charge burns
            at her left hand, the bolt leaves from it; right after, the sword swings
  tier      the section east of the start is generated: its monsters are on a par with her (hit points ~ hers, damage
            ~ her average blow)
  face      (a level with a face: random_dungeonmagic_level5, the Summoner) her face measured where it shows: the level's
            face camera (RDM5_FaceCam, 834) is put in front of her face and captures only her; each expression channel held
            alone (SetManual) must set its morph targets and patches to the channel's numbers and change the picture (her
            idle stopped, the colour as painted: unlit) against her face at rest (how much of the face changed, against two pictures at rest: the noise); each morph target alone
            must change the picture too (a weight says nothing about whether the face moved); then the occasions: hurt (her
            cry: Pain in, then out), a cast (Focus), the start of a fight (a monster after her: Anger, held, gone when it
            leaves her), low hit points (Fear held, gone when they come back), death (Dead: eyes shut), and blinks over
            twelve quiet seconds (the eyes' patch fully on and off again). The pictures go to Saved/FaceTest/<tag>
            (face_<tag>_<channel>.png) for the eye.
Writes SourceArt/random_dungeon_magic[2|3|5]/test_<tag>.json and logs "RDMTEST done | <tag> | ok / FAILED | ...". Args: plan tag"""
import unreal, sys, json, math, os
__keep__ = True
TAG = sys.argv[2] if len(sys.argv) > 2 else "t"
V = unreal.Vector; GS = unreal.GameplayStatics; ML = unreal.MathLibrary
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
assert w is not None, "PIE is not running"
LEVELS = {"random_dungeonmagic_level": {"pawn": "BP_RDM_CasterCharacter_C", "mesh": "SK_JRPG_Caster", "ch": "Caster", "dual": False, "out": "random_dungeon_magic",
                                        "bps": ("/Game/JRPG/Game/BP_JRPGCasterCharacter", "/Game/RandomDungeon/Blueprints/BP_RDM_CasterCharacter"), "cast_keys": ("E", "LeftMouseButton"),
                                        "plan": "setup,keys,pad,walls,cast,nothing,far,kill:3,tier"},
          "random_dungeonmagic_level2": {"pawn": "BP_RDM2_DarkCasterCharacter_C", "mesh": "SK_JRPG_DarkCaster", "ch": "DarkCaster", "dual": True, "out": "random_dungeon_magic2",
                                         "bps": ("/Game/JRPG/Game/BP_JRPGDarkCasterCharacter", "/Game/RandomDungeon/Blueprints/BP_RDM2_DarkCasterCharacter"), "cast_keys": ("E", "RightMouseButton"),
                                         "plan": "setup,keys,pad,hair,walls,cast,dual,nothing,far,kill:2,sword:2,tier"},
          "random_dungeonmagic_level3": {"pawn": "BP_RDM3_RogueCharacter_C", "mesh": "SK_JRPG_Rogue", "ch": "Rogue", "dual": False, "rogue": True, "out": "random_dungeon_magic3",
                                         "bps": ("/Game/JRPG/Game/BP_JRPGRogueCharacter", "/Game/RandomDungeon/Blueprints/BP_RDM3_RogueCharacter"), "cast_keys": ("LeftMouseButton",),
                                         "plan": "setup,weapons,keys,pad,walls,cast,nothing,far,kill:2,daggers:2,roll,dodge,tier"},
          "random_dungeonmagic_level5": {"pawn": "BP_RDM5_SummonerCharacter_C", "mesh": "SK_JRPG_Summoner", "ch": "Summoner", "dual": False, "out": "random_dungeon_magic5",
                                         "bps": ("/Game/JRPG/Game/BP_JRPGSummonerCharacter", "/Game/RandomDungeon/Blueprints/BP_RDM5_SummonerCharacter"), "cast_keys": ("E", "LeftMouseButton"),
                                         "plan": "setup,keys,pad,walls,cast,nothing,far,kill:3,tier,face"}}
LV = LEVELS[w.get_path_name().split(".")[-1].replace("UEDPIE_0_", "")]
PLAN = [s.strip() for s in (sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "all" else LV["plan"]).split(",") if s.strip()]
OUT = "E:\\code\\claude-ue5\\claude_ue5\\SourceArt\\" + LV["out"]
G = {}; R = {"tag": TAG, "plan": PLAN, "level": w.get_path_name().split(".")[-1], "steps": []}
gen = GS.get_all_actors_of_class(w, unreal.RDDungeonGenerator)[0]
pc = GS.get_player_controller(w, 0); pawn = pc.get_controlled_pawn()
G.update({"w": w, "gen": gen, "pc": pc, "pawn": pawn})
def now(): return GS.get_time_seconds(G["w"])
def cb(): return G["gen"].get_player_combat()
def spell_index(): return next(i for i, d in enumerate(G["gen"].get_editor_property("weapons")) if d.spell)
def spell(): return G["gen"].get_editor_property("weapons")[spell_index()]
def cast(c):
    if LV.get("rogue"): c.select_weapon(spell_index()); return c.start_attack()        # (the crossbow: drawn, then shot)
    return c.start_spell() if LV["dual"] else c.start_attack()
ROGUE = LV.get("rogue", False)
def key(n): k = unreal.Key(); k.set_editor_property("key_name", n); return k
def mesh_point(comp, x, y, z): return ML.transform_location(comp.get_world_transform(), V(x, y, z))
def in_actor(v): return ML.inverse_transform_location(G["pawn"].get_actor_transform(), v)
def wait(sec):
    t0 = now()
    while now() - t0 < sec: yield
def step_result(name, ok, **kw):
    R["steps"].append({"step": name, "ok": bool(ok), **kw})
    unreal.log(f"RDMTEST step {name}: {'ok' if ok else 'FAILED'} {json.dumps(kw)[:1800]}")
def alive(m):
    try: return m is not None and unreal.SystemLibrary.is_valid(m) and not m.is_dead()
    except Exception: return False
def start_monsters(): return [m for m in G["gen"].get_monsters() if alive(m) and m.get_editor_property("section").get_editor_property("coord") == unreal.IntPoint(0, 0)]
def v3(v): return [round(v.x), round(v.y), round(v.z)]
def clear(a, b, ignore):
    """no wall between two points (monsters and she do not count)"""
    h = unreal.SystemLibrary.line_trace_single(G["w"], a, b, unreal.TraceTypeQuery.ECC_VISIBILITY, False, ignore, unreal.DrawDebugTrace.NONE, True)
    return h is None or not h.to_tuple()[0]
def stand_off(m, gap):
    """puts her `gap` cm from the monster in its room, where she can see it and the camera has room behind her"""
    p = G["pawn"]; sec = m.get_editor_property("section"); ml = m.get_actor_location(); room = sec.room_at(ml)
    ign = [p] + list(G["gen"].get_monsters()); best = None
    for k in range(32):
        a = k * math.pi / 16; q = V(ml.x + math.cos(a) * gap, ml.y + math.sin(a) * gap, ml.z)
        if room >= 0 and sec.room_at(q) != room: continue
        path = sec.find_path_world(q, ml)
        if not len(path) or math.hypot(path[0].x - q.x, path[0].y - q.y) > 135.0: continue
        if not clear(V(q.x, q.y, 150), V(ml.x, ml.y, ml.z + 20), ign): continue
        # (and at the height a crossbow's bolt leaves: a bolt shot over a table burst on it 2.5 m out, the view above it clear)
        if not clear(V(q.x, q.y, 128), V(ml.x, ml.y, ml.z + 20), ign): continue
        best = q; break
    if best is None: return False
    p.set_actor_location(V(best.x, best.y, 100.0), False, True)
    yaw = math.degrees(math.atan2(ml.y - best.y, ml.x - best.x)); p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw), True)
    G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=yaw))
    return True

def step_setup():
    yield from wait(1.0)
    c = cb(); p = G["pawn"]; s = G["gen"].get_start_room_center(); l = p.get_actor_location()
    wd = list(G["gen"].get_editor_property("weapons")); wm = c.get_weapon_mesh() if c else None
    sk = p.mesh.get_skeletal_mesh_asset() if hasattr(p.mesh, "get_skeletal_mesh_asset") else p.mesh.skeletal_mesh
    if LV["dual"]:
        held = wm is not None and wm.static_mesh is not None and wm.is_visible() and str(wm.get_attach_socket_name()) == "hand_r"
        arms = len(wd) == 2 and not wd[0].spell and wd[1].spell and wd[1].alongside and str(wd[1].spell_bone) == "hand_l" and c.get_weapon_index() == 0 and c.get_alongside_spell() == 1 and held
    elif ROGUE:
        om = c.get_off_hand_mesh(); hx = c.get_holster_mesh(1, False)
        arms = (len(wd) == 2 and not wd[0].spell and wd[0].off_hand_mesh is not None and wd[1].spell and wd[1].bolt_mesh is not None and c.get_weapon_index() == 0
                and wm is not None and wm.is_visible() and str(wm.get_attach_socket_name()) == "hand_r" and om is not None and om.is_visible() and str(om.get_attach_socket_name()) == "hand_l"
                and hx is not None and hx.is_visible() and str(hx.get_attach_socket_name()) == "spine_03" and not c.get_holster_mesh(0, False).is_visible()
                and G["gen"].get_editor_property("rogue_controls") and G["gen"].get_editor_property("roll_clip") is not None)
    else: arms = len(wd) == 1 and wd[0].spell and c.is_spell() and (wm is None or wm.static_mesh is None or not wm.is_visible())
    ok = (c is not None and p.get_class().get_name() == LV["pawn"] and sk.get_name() == LV["mesh"] and abs(c.get_health() - 100.0) < 0.5 and math.hypot(l.x - s.x, l.y - s.y) < 300 and arms
          and G["gen"].get_editor_property("caster_controls") and len(G["gen"].get_editor_property("controls_pad")) > 0)
    step_result("setup", ok, pawn=p.get_class().get_name(), mesh=sk.get_name(), in_her_right_hand=wm.static_mesh.get_name() if wm is not None and wm.static_mesh is not None and wm.is_visible() else None, hit_points=c.get_health() if c else None, weapons=[str(d.name) for d in wd], spell=bool(c.is_spell()) if c else None,
                from_start_room_cm=round(math.hypot(l.x - s.x, l.y - s.y)), title=G["gen"].get_editor_property("player_title"), caster_controls=G["gen"].get_editor_property("caster_controls"),
                keys=list(G["gen"].get_editor_property("controls_keys")), pad=list(G["gen"].get_editor_property("controls_pad")))

def step_keys():
    import editor_toolset.toolsets.blueprint as BT
    sub = [s for s in unreal.ObjectIterator(unreal.EnhancedInputLocalPlayerSubsystem) if "LocalPlayer" in s.get_path_name()][0]
    move = unreal.load_asset("/Game/Input/Actions/IA_Move"); sprint = unreal.load_asset("/Game/Input/Actions/IA_Sprint")
    # (the keys are measured below by pressing them; has_mapping_context of the editor's local player says False in
    # PIE although its mappings are what moves her, so it is only reported)
    imc0 = unreal.load_asset("/Game/Input/IMC_Default"); active = bool(sub.has_mapping_context(imc0))
    maps0 = imc0.get_editor_property("default_key_mappings").get_editor_property("mappings")
    keys = lambda a: sorted(str(m.key.get_editor_property("key_name")) for m in maps0 if m.action == a)
    mk, sk = keys(move), keys(sprint)
    # what her character reacts to (her Blueprint and its parents): no other action may take E or the left mouse button
    handled = set()
    for bp_path in ("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter",) + LV["bps"]:
        bp = unreal.load_asset(bp_path)
        for g in BT.BlueprintTools.list_graphs(bp):
            for n in BT.BlueprintTools.find_nodes(g, ""):
                tid = str(BT.BlueprintTools.get_node_infos([n])[0].type_id)
                if "IA_" in tid: handled.add(tid.split("IA_")[-1])
    imc = unreal.load_asset("/Game/Input/IMC_Default")
    on_spell_keys = sorted({str(m.action.get_name()) for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings") if str(m.key.get_editor_property("key_name")) in ("E", "LeftMouseButton", "RightMouseButton")})
    clash = [a for a in on_spell_keys if a.replace("IA_", "") in handled]
    # the keys pressed as on the keyboard (through her player controller): W walks her, Left Shift + W runs her, each of
    # A / S / D moves her the way it should (camera to the east: A north, S west, D south), E and the left mouse cast
    p = G["pawn"]; c = cb(); c.revive(True); c.set_scripted_only(False); yield from wait(0.5)
    s = G["gen"].get_start_room_center(); key = lambda n: (lambda k: (k.set_editor_property("key_name", n), k)[1])(unreal.Key())
    G["pc"].set_ignore_look_input(True); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=0))
    speeds = {}; heading = {}
    for name, held in (("walk", ["W"]), ("run", ["LeftShift", "W"]), ("A", ["A"]), ("S", ["S"]), ("D", ["D"])):
        p.set_actor_location(V(s.x, s.y, 100.0), False, True); yield from wait(0.6)
        for k in held: c.simulate_key(key(k), True)
        yield from wait(0.8)
        a = p.get_actor_location(); t0 = now(); yield from wait(1.0); b = p.get_actor_location(); t1 = now()
        for k in reversed(held): c.simulate_key(key(k), False)
        speeds[name] = round(math.hypot(b.x - a.x, b.y - a.y) / max(t1 - t0, 1e-3), 1); heading[name] = round(math.degrees(math.atan2(b.y - a.y, b.x - a.x)))
        yield from wait(0.8)
    casts = {}
    seq = [(k, k) for k in LV["cast_keys"] + (("LeftMouseButton",) if LV["dual"] else ())]
    if ROGUE: seq = [("LeftMouseButton daggers", "LeftMouseButton"), ("RightMouseButton", "RightMouseButton"), ("E", "E"), ("Two", None), ("LeftMouseButton crossbow", "LeftMouseButton"), ("One", None)]
    for label, k in seq:
        if k is None:                      # (a key that draws a weapon)
            c.simulate_key(key(label), True); yield from wait(0.2); c.simulate_key(key(label), False); yield from wait(0.4); continue
        yield from wait(1.2); n0 = c.attacks_made; b0 = c.bolts_cast
        c.simulate_key(key(k), True); yield from wait(0.2); c.simulate_key(key(k), False)
        t0 = now()
        while c.is_attacking() and now() - t0 < 3.0: yield
        casts[label] = {"attacks": c.attacks_made - n0, "bolts": c.bolts_cast - b0}
    G["pc"].set_ignore_look_input(False)
    walk, runs = [float(x) for x in open(r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_" + LV["ch"].lower() + r"\speeds.txt").read().split()]
    want = {"walk": 0, "run": 0, "A": -90, "S": 180, "D": 90}
    dirs_ok = all(abs((heading[n] - want[n] + 180) % 360 - 180) < 15 for n in want)
    ok = (all(k in mk for k in ("W", "A", "S", "D")) and "LeftShift" in sk and not clash and abs(speeds["walk"] - walk) < 0.15 * walk and abs(speeds["run"] - runs) < 0.15 * runs and dirs_ok
          and (all(v["attacks"] == 1 and v["bolts"] == (0 if (LV["dual"] and k == "LeftMouseButton") else 1) for k, v in casts.items()) if not ROGUE else
               casts["LeftMouseButton daggers"] == {"attacks": 1, "bolts": 0} and casts["RightMouseButton"]["attacks"] == 0 and casts["E"]["attacks"] == 0
               and casts["LeftMouseButton crossbow"] == {"attacks": 1, "bolts": 1} and c.get_weapon_index() == 0))
    step_result("keys", ok, context_active=active, move_keys=mk, run_keys=sk, actions_on_E_and_left_mouse=on_spell_keys, her_handlers=sorted(handled), clash=clash,
                walk_cm_s=speeds["walk"], her_walk=walk, run_cm_s=speeds["run"], her_run=runs, speeds=speeds, headings_deg=heading, wanted_headings=want, attacks_by_key=casts)

def step_pad():
    """the magic levels' controls (generator bCasterControls), pressed through her player controller as on the gamepad"""
    p = G["pawn"]; c = cb(); gen = G["gen"]; c.revive(True); c.set_scripted_only(False); c.set_run_mode(False); yield from wait(0.5)
    s = gen.get_start_room_center(); key = lambda n: (lambda k: (k.set_editor_property("key_name", n), k)[1])(unreal.Key())
    G["pc"].set_ignore_look_input(True); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=0))
    walk, runs = [float(x) for x in open(r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_" + LV["ch"].lower() + r"\speeds.txt").read().split()]
    out = {}
    def tap(k, hold=0.15):
        c.simulate_key(key(k), True); yield from wait(hold); c.simulate_key(key(k), False); yield from wait(0.1)
    def travel(label, axis=None, keys=()):
        """her speed (cm/s) and heading over a second: the left stick held forward (axis) or keys held"""
        p.set_actor_location(V(s.x, s.y, 100.0), False, True); yield from wait(0.6)
        for k in keys: c.simulate_key(key(k), True)
        t0 = now(); a = None
        while now() - t0 < 1.8:
            if axis: c.simulate_axis(key(axis), 1.0)
            if a is None and now() - t0 >= 0.8: a = p.get_actor_location(); ta = now()
            yield
        b = p.get_actor_location(); tb = now()
        if axis: c.simulate_axis(key(axis), 0.0)
        for k in reversed(keys): c.simulate_key(key(k), False)
        out[label] = {"cm_s": round(math.hypot(b.x - a.x, b.y - a.y) / max(tb - ta, 1e-3), 1), "heading_deg": round(math.degrees(math.atan2(b.y - a.y, b.x - a.x))), "running": bool(c.is_run_mode())}
        yield from wait(0.6)
    # the device in use: a key makes it the keyboard, a gamepad button the gamepad
    yield from tap("W"); kb = not c.is_using_gamepad()
    yield from tap("Gamepad_DPad_Down"); pad = c.is_using_gamepad()
    yield from tap("W"); kb2 = not c.is_using_gamepad()
    out["device"] = {"after_W": "keyboard" if kb else "gamepad", "after_pad_button": "gamepad" if pad else "keyboard", "after_W_again": "keyboard" if kb2 else "gamepad"}
    # walking and running: the left stick forward walks her; LT switches to running and back; R does the same on the keyboard
    yield from travel("stick_walk", axis="Gamepad_LeftY")
    yield from tap("Gamepad_LeftTrigger"); lt_on = c.is_run_mode()
    yield from travel("stick_run", axis="Gamepad_LeftY")
    yield from tap("Gamepad_LeftTrigger"); lt_off = not c.is_run_mode()
    yield from tap("R"); r_on = c.is_run_mode()
    yield from travel("W_run", keys=("W",))
    yield from tap("R"); r_off = not c.is_run_mode()
    yield from travel("W_walk", keys=("W",))
    out["switch"] = {"LT_runs": lt_on, "LT_again_walks": lt_off, "R_runs": r_on, "R_again_walks": r_off}
    # A jumps
    p.set_actor_location(V(s.x, s.y, 100.0), False, True); yield from wait(0.8)
    z0 = p.get_actor_location().z; top = z0; c.simulate_key(key("Gamepad_FaceButton_Bottom"), True); t0 = now()
    while now() - t0 < 0.9: top = max(top, p.get_actor_location().z); yield
    c.simulate_key(key("Gamepad_FaceButton_Bottom"), False); out["A_jump_cm"] = round(top - z0); yield from wait(0.8)
    # the right stick turns the camera
    G["pc"].set_ignore_look_input(False); yaw0 = G["pc"].get_control_rotation().yaw; t0 = now()
    while now() - t0 < 0.5: c.simulate_axis(key("Gamepad_RightX"), 1.0); yield
    c.simulate_axis(key("Gamepad_RightX"), 0.0); yield from wait(0.2)
    out["right_stick_turned_deg"] = round((G["pc"].get_control_rotation().yaw - yaw0 + 180) % 360 - 180, 1)
    # RB: the weapon in her hand; LB: the spell (cast alongside, or the drawn one); RT and Y (the combat level's) do nothing here
    def press(label, k, axis=False):
        yield from wait(1.0); n0 = (c.attacks_made, c.bolts_cast); idx = set()
        if axis: c.simulate_axis(key(k), 1.0)
        else: c.simulate_key(key(k), True)
        t0 = now()
        while now() - t0 < 0.2:
            if c.is_attacking(): idx.add(c.get_attack_index())
            yield
        if axis: c.simulate_axis(key(k), 0.0)
        else: c.simulate_key(key(k), False)
        while c.is_attacking() and now() - t0 < 3.0: idx.add(c.get_attack_index()); yield
        yield from wait(0.3)
        out[label] = {"attacks": c.attacks_made - n0[0], "bolts": c.bolts_cast - n0[1], "weapons": sorted(idx)}
    c.select_weapon(0)
    yield from press("RB", "Gamepad_RightShoulder"); yield from press("LB", "Gamepad_LeftShoulder")
    yield from press("RT", "Gamepad_RightTriggerAxis", axis=True); yield from press("Y", "Gamepad_FaceButton_Top")
    if ROGUE:
        # (Y switched to the crossbow: RB shoots it; Y again back to the daggers; B rolls)
        out["Y"]["drawn_after"] = c.get_weapon_index(); yield from press("RB crossbow", "Gamepad_RightShoulder")
        yield from tap("Gamepad_FaceButton_Top"); out["Y"]["drawn_after_again"] = c.get_weapon_index()
        p.set_actor_location(V(s.x, s.y, 100.0), False, True); yield from wait(0.8); r0 = c.rolls
        yield from tap("Gamepad_FaceButton_Right"); yield from wait(1.2); out["B"] = {"rolls": c.rolls - r0}
    # X opens the container she stands by (the generator's InteractNearest, as F)
    sec = gen.get_section(unreal.IntPoint(0, 0)); found = None
    for k in range(sec.get_num_containers()):
        q = sec.get_container_location(k)
        if sec.get_container_open_alpha(k) > 0.01 or sec.get_container_kind(k).endswith("_r"): continue
        for r in (120.0, 150.0, 180.0):
            for j in range(16):
                a = j * math.pi / 8; st = V(q.x + math.cos(a) * r, q.y + math.sin(a) * r, 100.0)
                if sec.room_at(st) < 0 or not gen.describe_nearest(st, 260.0).startswith("open ") or "door" in gen.describe_nearest(st, 260.0): continue
                pth = sec.find_path_world(st, q)
                if len(pth) and math.hypot(pth[0].x - st.x, pth[0].y - st.y) < 135: found = (k, st); break
            if found: break
        if found: break
    if found:
        k, st = found; p.set_actor_location(st, False, True); yield from wait(0.6)
        what = gen.describe_nearest(p.get_actor_location(), 260.0); n0 = c.attacks_made
        yield from tap("Gamepad_FaceButton_Left"); yield from wait(1.4)
        out["X"] = {"prompt": what, "container": sec.get_container_kind(k), "open_alpha": round(sec.get_container_open_alpha(k), 2), "attacks": c.attacks_made - n0, "device": "gamepad" if c.is_using_gamepad() else "keyboard"}
    else: out["X"] = {"why": "no closed container with a place to stand"}
    # Back (View) opens the big map and closes it again (the generator, as M)
    gen.set_map_open(False); yield from tap("Gamepad_Special_Left"); yield from wait(0.3); back_open = bool(gen.get_editor_property("map_open"))
    yield from tap("Gamepad_Special_Left"); yield from wait(0.3); back_shut = not gen.get_editor_property("map_open")
    out["Back"] = {"opens_map": back_open, "closes_it": back_shut}
    G["pc"].set_ignore_look_input(False)
    spell_w = spell_index()
    drawn = 0
    rb_ok = out["RB"]["attacks"] == 1 and out["RB"]["weapons"] == [drawn if (LV["dual"] or ROGUE) else spell_w] and out["RB"]["bolts"] == (0 if (LV["dual"] or ROGUE) else 1)
    lb_ok = out["LB"]["attacks"] == 1 and out["LB"]["weapons"] == [spell_w] and out["LB"]["bolts"] == 1
    if ROGUE:
        lb_ok = (out["LB"]["attacks"] == 0 and out["Y"].get("drawn_after") == 1 and out["Y"].get("drawn_after_again") == 0 and out["RB crossbow"]["bolts"] == 1
                 and out["RB crossbow"]["weapons"] == [1] and out["B"]["rolls"] == 1)
    near = lambda v, want: abs(v - want) < 0.15 * want
    ok = (kb and pad and kb2 and all(out["switch"].values()) and near(out["stick_walk"]["cm_s"], walk) and near(out["stick_run"]["cm_s"], runs)
          and near(out["W_run"]["cm_s"], runs) and near(out["W_walk"]["cm_s"], walk) and abs(out["stick_walk"]["heading_deg"]) < 15 and out["A_jump_cm"] > 20 and abs(out["right_stick_turned_deg"]) > 10
          and rb_ok and lb_ok and out["RT"]["attacks"] == 0 and out["Y"]["attacks"] == 0 and found is not None and out["X"]["open_alpha"] > 0.5 and out["X"]["attacks"] == 0 and back_open and back_shut)
    step_result("pad", ok, her_walk=walk, her_run=runs, **out)
    c.set_run_mode(False); c.revive(True)

def step_hair():
    """(level 2) the Warlock's hair (820: AnimDynamics on six chains): she stands, runs, stops, jumps, is teleported (the jitter: the last 0.5 s of standing, after 0.8 s of settling, 1.2 s after a landing); per
    frame the hair tips' offset from where her head carries them (it swings, and settles when she stands), each hair
    bone's length (no stretching), the gap between neighbouring back strands' tips (they do not tear apart), how far
    each hair body keeps out of the spheres round her head, upper back, face and chest"""
    p = G["pawn"]; c = cb(); gen = G["gen"]; m = p.mesh; c.revive(True); c.set_scripted_only(False); c.set_run_mode(False)
    D = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_darkcaster\hair_dynamics.json"))
    # (the rest places are the mesh's, written by 820: the skeleton keeps an older reference pose for bones it already had)
    REF = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\jrpg_darkcaster\hair_ref.json"))
    bones = [b for b in REF if b.startswith("hair_")]
    if not bones: step_result("hair", False, why="no hair bones (run tripo_build with hair.json, then 820)"); return
    RW = lambda b: unreal.Transform(V(*REF[b]["t"]), unreal.Quat(*REF[b]["q"]).rotator(), V(1, 1, 1))
    chains = {ch: sorted([b for b in bones if b.startswith(ch + "_") and b[len(ch) + 1:].isdigit()], key=lambda b: int(b.split("_")[-1])) + [ch + "_end"] for ch in D["chains"]}
    rest_len = {(a, b): (RW(b).translation - RW(a).translation).length() for ch, bs in chains.items() for a, b in zip(bs[1:-1], bs[2:])}
    # (the limits 820 set up, in their bones' spaces: spheres the hair is kept out of, planes it is kept above)
    spheres = [(s["bone"], V(*s["local"]), s["radius"], s.get("chains")) for s in REF["_spheres"]]
    planes = [(q["bone"], V(*q["local_point"]), V(*q["local_normal"]), q.get("chains")) for q in REF["_planes"]]
    key = lambda n: (lambda k: (k.set_editor_property("key_name", n), k)[1])(unreal.Key())
    head = lambda: m.get_socket_transform("head", unreal.RelativeTransformSpace.RTS_WORLD)
    tips = [bs[-1] for bs in chains.values()]
    def rel(b): return ML.inverse_transform_location(head(), m.get_socket_location(b))
    s = gen.get_start_room_center(); p.set_actor_location(V(s.x - 600, s.y, 100), False, True); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-10, yaw=0))
    yield from wait(1.5)
    rest = {b: rel(b) for b in tips}; back = [chains[ch][-1] for ch in D["chains"] if ch.startswith("hair_b")]
    gap0 = [(m.get_socket_location(a) - m.get_socket_location(b)).length() for a, b in zip(back, back[1:])]
    R_ = {"dev": {}, "stretch": 1.0, "stretch_at": None, "stretch_by": {}, "spread_cm": 0.0, "clear_cm": 99.0, "clear_at": None}
    def sample(phase):
        d = max((rel(b) - rest[b]).length() for b in tips); R_["dev"].setdefault(phase, []).append(d)
        for (a, b), L in rest_len.items():
            r_ = (m.get_socket_location(b) - m.get_socket_location(a)).length() / max(L, 0.1)
            if r_ > R_["stretch"]: R_["stretch"] = r_; R_["stretch_at"] = [a, b, phase]
            R_["stretch_by"][phase] = max(R_["stretch_by"].get(phase, 1.0), r_)
        g = [(m.get_socket_location(a) - m.get_socket_location(b)).length() for a, b in zip(back, back[1:])]
        R_["spread_cm"] = max(R_["spread_cm"], max(abs(x - y) for x, y in zip(g, gap0)))
        for bone, off, rad, only in spheres:
            cen = ML.transform_location(m.get_socket_transform(bone, unreal.RelativeTransformSpace.RTS_WORLD), off)
            for ch, bs in chains.items():
                if only and not any(ch.startswith(q) for q in only): continue
                for a, b in zip(bs[1:-1], bs[2:]):
                    mid = (m.get_socket_location(a) + m.get_socket_location(b)) * 0.5; cl = (mid - cen).length() - rad
                    if cl < R_["clear_cm"]: R_["clear_cm"] = cl; R_["clear_at"] = [ch, bone + " sphere", phase]
        for bone, lp, ln, only in planes:
            btf = m.get_socket_transform(bone, unreal.RelativeTransformSpace.RTS_WORLD); P_ = ML.transform_location(btf, lp); N_ = ML.transform_direction(btf, ln).normal()
            for ch, bs in chains.items():
                if only and not any(ch.startswith(q) for q in only): continue
                for a, b in zip(bs[1:-1], bs[2:]):
                    cl = ((m.get_socket_location(a) + m.get_socket_location(b)) * 0.5 - P_).dot(N_)
                    if cl < R_["clear_cm"]: R_["clear_cm"] = cl; R_["clear_at"] = [ch, bone + " plane", phase]
    def during(sec, phase):
        t0 = now()
        while now() - t0 < sec: sample(phase); yield
    c.set_run_mode(True); c.simulate_key(key("W"), True); yield from during(1.6, "run")
    c.simulate_key(key("W"), False); yield from during(1.0, "stop"); yield from during(0.8, "settling after the stop"); yield from during(0.5, "standing after the stop")
    c.simulate_key(key("SpaceBar"), True); yield from during(0.2, "jump"); c.simulate_key(key("SpaceBar"), False); yield from during(1.2, "jump")
    yield from during(1.2, "settling after the jump"); yield from during(0.5, "standing after the jump")      # (a landing swings the hair longer than a stop)
    p.set_actor_location(V(s.x, s.y, 100), False, True); yield from during(0.8, "after a teleport"); yield from during(0.5, "standing after the teleport")
    c.set_run_mode(False)
    peak = {k: round(max(v), 1) for k, v in R_["dev"].items()}
    jitter = {k: round(max(v) - min(v), 1) for k, v in R_["dev"].items() if k.startswith("standing")}
    ok = (peak["run"] > 5.0 and peak["stop"] > 5.0 and peak["jump"] > 5.0 and all(j < 4.0 for j in jitter.values())
          # (AnimDynamics' joints give under fast motion: about a third of a 6 to 7 cm bone at the moment she lands, none when she stands)
          and all(v < 1.08 for k, v in R_["stretch_by"].items() if k.startswith("standing")) and R_["stretch_by"]["run"] < 1.45 and R_["stretch"] < 1.6
          and R_["spread_cm"] < 20.0 and R_["clear_cm"] > -2.0 and peak["standing after the teleport"] < 15.0)
    step_result("hair", ok, chains={k: len(v) - 2 for k, v in chains.items()}, peak_tip_offset_cm=peak, standing_jitter_cm=jitter, worst_bone_stretch=round(R_["stretch"], 3), worst_stretch_where=R_["stretch_at"], stretch_by_phase={k: round(v, 3) for k, v in R_["stretch_by"].items()},
                back_tips_spread_change_cm=round(R_["spread_cm"], 1), closest_to_a_limit_cm=round(R_["clear_cm"], 1), closest_where=R_["clear_at"])

def cast_at(m, gap=900.0, label="cast"):
    """one cast at m from `gap` cm; measures the charge, the flight, the burst"""
    c = cb(); p = G["pawn"]; gen = G["gen"]; c.set_scripted_only(True); c.revive(False)
    if not stand_off(m, gap): return {"ok": False, "why": "no place to stand"}
    yield from wait(0.4)
    d = spell(); hb = str(d.spell_bone)
    # (monsters open and close doors as they wander: by now a door may have shut between them; the bolt flies from her hand)
    ml = m.get_actor_location(); frm = p.mesh.get_socket_location(hb)
    if ROGUE:                                           # (the bolt leaves from the crossbow's front: 83 cm ahead of her, 61 cm up)
        pl = p.get_actor_location(); dv = V(ml.x - pl.x, ml.y - pl.y, 0).normal(); frm = V(pl.x + dv.x * 83, pl.y + dv.y * 83, pl.z + 61)
    if not clear(frm, V(ml.x, ml.y, ml.z + 20), [p] + list(gen.get_monsters())): return {"ok": False, "why": "no place to stand"}
    wn = str(d.name); snd = [f"Player.{k}.{wn}" for k in ("Charge", "Cast", "Hit")]
    hp0 = m.get_health(); n0 = (c.bolts_cast, c.bolts_on_monsters, c.bolts_elsewhere); snd0 = {k: gen.get_sound_count(k) for k in snd}
    bolt_mesh = d.bolt_mesh; flying = 0; loaded_before = None; loaded_gone = None; muzzle_gap = None
    rel = lambda: ML.inverse_transform_location(p.get_actor_transform(), p.mesh.get_socket_location(hb))
    if ROGUE: c.select_weapon(spell_index()); yield from wait(0.5); loaded_before = bool(c.get_loaded_bolt_mesh().is_visible())
    a0 = rel(); started = cast(c); target = c.get_last_target(); t0 = now()
    charge = 0; moved = 0.0; mont = False; track = []; near_bolt = 0; launched_at = None
    while now() - t0 < 4.0:
        hand = p.mesh.get_socket_location(hb); moved = max(moved, (rel() - a0).length()); mont = mont or p.mesh.get_anim_instance().is_any_montage_playing()
        if c.is_charging(): charge = max(charge, c.get_spell_particles(hand, 120.0)[0])
        bs = c.get_bolts()
        if bs and bolt_mesh is not None:
            fl = [q for q in p.get_components_by_class(unreal.StaticMeshComponent) if q.static_mesh == bolt_mesh and q.is_visible() and q.get_attach_parent() is None]
            flying = max(flying, len(fl))
            if loaded_gone is None: loaded_gone = not c.get_loaded_bolt_mesh().is_visible()
            if muzzle_gap is None: muzzle_gap = round((c.last_bolt_from - mesh_point(c.get_weapon_mesh(), *list(d.bolt_muzzle.to_tuple()))).length(), 1)
        if bs:
            if launched_at is None: launched_at = now() - t0
            track.append((now(), bs[0])); near_bolt = max(near_bolt, c.get_spell_particles(bs[0], 150.0)[0])
        if c.bolts_on_monsters + c.bolts_elsewhere > n0[1] + n0[2]: break
        yield
    burst_at = c.last_burst_at; yield from wait(0.15)
    burst_particles = c.get_spell_particles(burst_at, 300.0)[0]
    sp = [(track[k + 1][1] - track[k][1]).length() / max(track[k + 1][0] - track[k][0], 1e-4) for k in range(len(track) - 1)]
    speed = sorted(sp)[len(sp) // 2] if sp else 0.0
    yield from wait(0.6)
    e = {"monster": str(m.monster_name), "gap_cm": round(gap), "hand": hb, "started": bool(started), "target_is_it": target == m, "montage": bool(mont), "hand_moved_cm": round(moved),
         "charge_particles": charge, "bolt_left_at_s": round(launched_at, 2) if launched_at is not None else None, "bolt_speed_cm_s": round(speed), "spell_speed": d.bolt_speed,
         "particles_round_the_bolt": near_bolt, "on_monster": c.bolts_on_monsters - n0[1], "elsewhere": c.bolts_elsewhere - n0[2], "flown_cm": round(c.last_bolt_flown),
         "it_lost": round(hp0 - m.get_health(), 1) if alive(m) else round(hp0, 1), "damage": d.damage, "burst_particles": burst_particles, "burst_at": v3(burst_at),
         "sounds": {k: gen.get_sound_count(k) - snd0[k] for k in snd0}}
    if ROGUE:
        e.update({"bolt_meshes_flying": flying, "loaded_bolt_before": loaded_before, "loaded_bolt_gone_at_the_shot": loaded_gone, "bolt_left_from_the_muzzle_cm": muzzle_gap,
                  "loaded_bolt_back_after": bool(c.get_loaded_bolt_mesh().is_visible()), "bolt_left_from_hand_cm": round((c.last_bolt_from - p.mesh.get_socket_location("hand_r")).length())})
    rogue_ok = not ROGUE or (flying == 1 and loaded_before and loaded_gone and muzzle_gap is not None and muzzle_gap < 3.0 and e["loaded_bolt_back_after"] and e["bolt_left_from_hand_cm"] > 30)
    e["ok"] = bool(started and target == m and mont and moved > 25 and (charge > 0 or d.charge_effect is None) and launched_at is not None and abs(speed - d.bolt_speed) < 0.1 * d.bolt_speed and near_bolt > 0 and rogue_ok
                   and e["on_monster"] == 1 and abs(min(hp0, d.damage) - (hp0 - (m.get_health() if alive(m) else 0.0))) < 0.6 and burst_particles > 0 and all(v == 1 for v in e["sounds"].values()))
    c.set_scripted_only(False)
    return e

def step_cast():
    ms = start_monsters(); p = G["pawn"]; l = p.get_actor_location(); e = None
    for m in sorted(ms, key=lambda q: (q.get_actor_location() - l).length())[:6]:
        g = cast_at(m)
        try:
            while True: next(g); yield
        except StopIteration as s: e = s.value
        if e.get("why") != "no place to stand": break
    e = e or {"ok": False, "why": "no monster"}
    step_result("cast", e.pop("ok"), **e)

def step_nothing():
    c = cb(); p = G["pawn"]; gen = G["gen"]; c.set_scripted_only(True); c.revive(False)
    sec = gen.get_section(unreal.IntPoint(0, 0)); d = spell(); spot = None
    for i in range(sec.get_num_rooms()):
        q = sec.get_room_center(i)
        if all((m.get_actor_location() - q).length() > d.reach + 400 for m in gen.get_monsters() if alive(m)): spot = q; break
    if spot is None: step_result("nothing", False, why="no room without a monster within reach"); return
    p.set_actor_location(V(spot.x, spot.y, 100.0), False, True); p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=37.0), True); yield from wait(0.5)
    if ROGUE: c.select_weapon(spell_index()); yield from wait(0.5)
    yaw0 = p.get_actor_rotation().yaw; n0 = (c.bolts_on_monsters, c.bolts_elsewhere, c.hits_landed); dmg0 = c.damage_dealt; st0 = c.get_stuck_bolts()
    cast(c); target = c.get_last_target(); t0 = now(); f = p.get_actor_forward_vector(); first = None
    while now() - t0 < 4.0 and c.bolts_elsewhere == n0[1] and c.bolts_on_monsters == n0[0]:
        bs = c.get_bolts()
        if bs and first is None: first = bs[0]
        yield
    burst = c.last_burst_at; frm = c.last_bolt_from; yield from wait(0.2); stuck = c.get_stuck_bolts() - st0
    dev = 0.0
    if first is not None:
        dv = V(burst.x - frm.x, burst.y - frm.y, 0).normal(); dev = math.degrees(math.acos(max(-1.0, min(1.0, dv.x * f.x + dv.y * f.y))))
    ok = target is None and abs(p.get_actor_rotation().yaw - yaw0) < 1.0 and c.bolts_elsewhere == n0[1] + 1 and c.damage_dealt == dmg0 and dev < 5.0 and c.last_bolt_flown <= d.reach + 160
    if ROGUE: ok = ok and stuck == 1
    step_result("nothing", ok, stuck_in_the_wall=stuck if ROGUE else None, target=None if target is None else target.get_name(), turned_deg=round(p.get_actor_rotation().yaw - yaw0, 1), off_her_heading_deg=round(dev, 1), flown_cm=round(c.last_bolt_flown), reach=d.reach,
                damage_dealt=round(c.damage_dealt - dmg0, 1))
    c.set_scripted_only(False); yield from wait(1.0)

def step_far():
    c = cb(); p = G["pawn"]; gen = G["gen"]; c.set_scripted_only(True); d = spell(); done = None; far = max(1800.0, d.reach + 400.0)     # (beyond the reach: the crossbow's is 26 m)
    for m in start_monsters():
        sec = m.get_editor_property("section"); ml = m.get_actor_location()
        for k in range(16):
            a = k * math.pi / 8; q = V(ml.x + math.cos(a) * far, ml.y + math.sin(a) * far, ml.z)
            pth = sec.find_path_world(q, ml)
            if len(pth) and math.hypot(pth[0].x - q.x, pth[0].y - q.y) < 135 and all((o.get_actor_location() - q).length() > d.reach + 300 for o in gen.get_monsters() if alive(o) and o != m):
                done = (m, q); break
        if done: break
    if not done: step_result("far", False, why=f"no place {far / 100:.0f} m from a monster with none nearer"); c.set_scripted_only(False); return
    m, q = done; p.set_actor_location(V(q.x, q.y, 100.0), False, True)
    p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=math.degrees(math.atan2(m.get_actor_location().y - q.y, m.get_actor_location().x - q.x))), True); yield from wait(0.4)
    dist = (m.get_actor_location() - p.get_actor_location()).length(); cast(c); target = c.get_last_target()
    while c.is_attacking(): yield
    step_result("far", target is None and dist > d.reach + 200, monster=str(m.monster_name), distance_cm=round(dist), reach=d.reach, target=None if target is None else target.get_name())
    c.set_scripted_only(False); yield from wait(1.5)

def step_kill(n=3):
    c = cb(); p = G["pawn"]; out = []; d = spell()
    for k in range(n):
        ms = start_monsters()
        if not ms: out.append({"ok": False, "why": "no live monster"}); break
        l = p.get_actor_location(); placed = None
        for m in sorted(ms, key=lambda q: (q.get_actor_location() - l).length())[:8]:
            c.revive(False)
            if stand_off(m, 900.0): placed = m; break
        if placed is None: out.append({"ok": False, "why": "no place to stand"}); break
        m = placed; c.set_scripted_only(True); yield from wait(0.3)
        name = str(m.monster_name); hp0 = m.get_max_health(); k0 = c.kills; casts = 0; direct = 0; each_ok = True; t0 = now(); hurt0 = c.damage_taken
        while alive(m) and now() - t0 < 40.0:
            if not c.is_attacking():
                h = m.get_health(); n0 = c.bolts_on_monsters; tg = None
                if cast(c):
                    casts += 1; tg = c.get_last_target()
                    while c.is_attacking() or len(c.get_bolts()) > 0: yield
                    if c.bolts_on_monsters > n0 and tg == m:
                        direct += 1
                        lost = h - (m.get_health() if alive(m) else 0.0)
                        if abs(lost - min(h, d.damage)) > 0.6 and abs(lost - min(h, d.damage * 1.5)) > 0.6: each_ok = False     # (a splash from a burst on its neighbour may add half)
            if c.is_dead(): c.revive(False)
            yield
        dead = not alive(m)
        e = {"monster": name, "hit_points": hp0, "casts": casts, "bolts_on_it": direct, "bolts_needed": math.ceil(hp0 / d.damage), "killed": dead, "kills_counted": c.kills - k0, "each_bolt_took_the_damage": each_ok,
             "she_lost": round(c.damage_taken - hurt0), "seconds": round(now() - t0, 1)}
        e["ok"] = bool(dead and c.kills - k0 >= 1 and each_ok and direct <= math.ceil(hp0 / d.damage))        # (a burst may kill a neighbour too)
        out.append(e); c.set_scripted_only(False); yield from wait(0.6)
    c.revive(True)
    step_result("kill", len(out) == n and all(e["ok"] for e in out), fights=out, monsters_killed=G["gen"].get_editor_property("monsters_killed"))

def step_sword(n=2):
    """the sword: beside the monster, cut until it is down"""
    c = cb(); p = G["pawn"]; out = []; c.set_scripted_only(True); d = G["gen"].get_editor_property("weapons")[0]; c.select_weapon(0)
    for k in range(n):
        ms = start_monsters()
        if not ms: out.append({"ok": False, "why": "no live monster"}); break
        l = p.get_actor_location(); placed = None
        for m in sorted(ms, key=lambda q: (q.get_actor_location() - l).length())[:8]:
            c.revive(False)
            if stand_off(m, m.capsule_component.get_scaled_capsule_radius() + 110.0): placed = m; break
        if placed is None: out.append({"ok": False, "why": "no place to stand"}); break
        m = placed; yield from wait(0.3)
        name = str(m.monster_name); hp0 = m.get_max_health(); k0 = c.kills; blows = 0; each = True; t0 = now(); b0 = c.bolts_cast
        while alive(m) and now() - t0 < 40.0:
            h = m.get_health(); n0 = c.hits_landed
            if c.start_attack():
                while c.is_attacking(): yield
                if c.hits_landed > n0:
                    blows += 1
                    if alive(m) and abs((h - m.get_health()) - d.damage) > 0.6: each = False
                else: stand_off(m, m.capsule_component.get_scaled_capsule_radius() + 110.0)
            if c.is_dead(): c.revive(False)
            yield
        dead = not alive(m)
        e = {"monster": name, "hit_points": hp0, "weapon": str(d.name), "damage": d.damage, "blows": blows, "blows_needed": math.ceil(hp0 / d.damage), "killed": dead, "kills_counted": c.kills - k0,
             "each_blow_took_the_damage": each, "bolts_cast": c.bolts_cast - b0, "seconds": round(now() - t0, 1)}
        e["ok"] = bool(dead and c.kills - k0 >= 1 and each and blows <= math.ceil(hp0 / d.damage) and c.bolts_cast == b0)
        out.append(e); yield from wait(0.6)
    c.revive(True); c.set_scripted_only(False)
    step_result("daggers" if ROGUE else "sword", len(out) == n and all(e["ok"] for e in out), fights=out)

def step_dual():
    """a cast with the sword drawn: the sword stays in her right hand, the fire comes from the left; then a cut"""
    c = cb(); p = G["pawn"]; c.set_scripted_only(True); c.revive(True); yield from wait(0.6)
    wm = c.get_weapon_mesh(); n0 = (c.attacks_made, c.bolts_cast); d = spell(); held = True; charge_l = 0; charge_r = 0; idx = []
    ok_cast = c.start_spell(); t0 = now()
    while now() - t0 < 2.0:
        held = held and wm.is_visible() and wm.static_mesh is not None and str(wm.get_attach_socket_name()) == "hand_r" and (wm.get_world_location() - p.mesh.get_socket_location("hand_r")).length() < 130.0
        if c.is_charging():
            charge_l = max(charge_l, c.get_spell_particles(p.mesh.get_socket_location("hand_l"), 90.0)[0]); charge_r = max(charge_r, c.get_spell_particles(p.mesh.get_socket_location("hand_r"), 40.0)[0])
        if c.is_attacking(): idx.append(c.get_attack_index())
        if not c.is_attacking() and c.bolts_cast > n0[1]: break
        yield
    frm = c.last_bolt_from; dl = (frm - p.mesh.get_socket_location("hand_l")).length()
    yield from wait(0.3)
    ok_cut = c.start_attack(); cut_idx = c.get_attack_index(); b1 = c.bolts_cast
    while c.is_attacking(): yield
    ok = (ok_cast and held and charge_l > 0 and set(idx) == {spell_index()} and c.bolts_cast >= n0[1] + 1 and ok_cut and cut_idx == 0 and c.bolts_cast == b1 and c.get_weapon_index() == 0)
    step_result("dual", ok, cast_started=bool(ok_cast), sword_held_all_through=held, charge_particles_left_hand=charge_l, attack_weapon_while_casting=sorted(set(idx)),
                bolt_from_left_hand_cm=round(dl), cut_started=bool(ok_cut), cut_weapon=cut_idx, bolts_by_the_cut=c.bolts_cast - b1)
    c.set_scripted_only(False)

def step_weapons():
    """(level 3) where her weapons are: in her hands, on her body, switched by the keys"""
    c = cb(); p = G["pawn"]; gen = G["gen"]; c.revive(True); c.set_scripted_only(False); yield from wait(0.5)
    wd = list(gen.get_editor_property("weapons")); out = {}
    def tap(k): c.simulate_key(key(k), True); yield from wait(0.15); c.simulate_key(key(k), False); yield from wait(0.5)
    yield from tap("One")
    mb = lambda b: p.mesh.get_socket_location(b)
    def centre(comp): return unreal.SystemLibrary.get_component_bounds(comp)[0]
    # the daggers: each handle (28.5 cm up the mesh) by its hand, the point away from it
    for side, comp in (("r", c.get_weapon_mesh()), ("l", c.get_off_hand_mesh())):
        h = mb(f"hand_{side}"); handle = mesh_point(comp, 0, 0, 28.5); tip = mesh_point(comp, 0, 0, 0)
        out[f"dagger_{side}"] = {"visible": bool(comp.is_visible()), "bone": str(comp.get_attach_socket_name()), "handle_from_hand_cm": round((handle - h).length(), 1), "point_from_hand_cm": round((tip - h).length(), 1)}
    # the crossbow on her back: behind spine_03, between her hips and her head
    hx = c.get_holster_mesh(1, False); cx = in_actor(centre(hx)); sp = in_actor(mb("spine_03"))
    out["crossbow_on_back"] = {"visible": bool(hx.is_visible()), "behind_spine_cm": round(sp.x - cx.x, 1), "height_over_pelvis_cm": round(cx.z - in_actor(mb("pelvis")).z, 1)}
    # 2: the crossbow drawn, its stock in her right hand, the daggers on her thighs, the bolt on the rail
    yield from tap("Two"); out["drawn_after_2"] = c.get_weapon_index()
    wm = c.get_weapon_mesh(); grip = mesh_point(wm, 31.0, 0.0, 0.5); front = mesh_point(wm, -40.0, 0.0, 0.0)
    out["crossbow"] = {"mesh": wm.static_mesh.get_name(), "bone": str(wm.get_attach_socket_name()), "stock_from_hand_cm": round((grip - mb("hand_r")).length(), 1),
                       "front_from_hand_cm": round((front - mb("hand_r")).length(), 1), "off_hand_shown": bool(c.get_off_hand_mesh().is_visible()), "back_holster_shown": bool(hx.is_visible())}
    for side in ("r", "l"):
        comp = c.get_holster_mesh(0, side == "l"); th = mb(f"thigh_{side}"); ca = mb(f"calf_{side}"); q = centre(comp)
        axis = (ca - th).normal(); t = max(0.0, min((q - th).dot(axis), (ca - th).length())); near = th + axis * t
        lateral = in_actor(q).y - in_actor(near).y
        out[f"dagger_on_thigh_{side}"] = {"visible": bool(comp.is_visible()), "from_thigh_bone_cm": round((q - near).length(), 1), "down_the_thigh_cm": round(t, 1),
                                          "outward_cm": round(lateral if side == "r" else -lateral, 1)}
    lb = c.get_loaded_bolt_mesh()
    out["loaded_bolt"] = {"visible": bool(lb.is_visible()), "from_rail_front_cm": round((centre(lb) - mesh_point(wm, -12.0, 0.0, 5.6)).length(), 1)}
    # the wheel and Y switch, 1 draws the daggers again
    c.simulate_key(key("MouseScrollDown"), True); yield; c.simulate_key(key("MouseScrollDown"), False); yield from wait(0.4); out["after_wheel"] = c.get_weapon_index()
    yield from tap("Gamepad_FaceButton_Top"); out["after_Y"] = c.get_weapon_index()
    yield from tap("One"); out["after_1"] = c.get_weapon_index()
    dg = [out["dagger_r"], out["dagger_l"]]; th = [out["dagger_on_thigh_r"], out["dagger_on_thigh_l"]]
    ok = (all(d_["visible"] and d_["handle_from_hand_cm"] < 10.0 and d_["point_from_hand_cm"] > 22.0 for d_ in dg) and out["dagger_r"]["bone"] == "hand_r" and out["dagger_l"]["bone"] == "hand_l"
          and out["crossbow_on_back"]["visible"] and 12.0 < out["crossbow_on_back"]["behind_spine_cm"] < 40.0 and 0.0 < out["crossbow_on_back"]["height_over_pelvis_cm"] < 60.0
          and out["drawn_after_2"] == 1 and out["crossbow"]["mesh"] == "SM_Crossbow" and out["crossbow"]["stock_from_hand_cm"] < 10.0 and out["crossbow"]["front_from_hand_cm"] > 50.0
          and not out["crossbow"]["off_hand_shown"] and not out["crossbow"]["back_holster_shown"]
          and all(t_["visible"] and 4.0 < t_["from_thigh_bone_cm"] < 16.0 and t_["outward_cm"] > 3.0 and t_["down_the_thigh_cm"] < 30.0 for t_ in th)
          and out["loaded_bolt"]["visible"] and out["loaded_bolt"]["from_rail_front_cm"] < 25.0 and out["after_wheel"] == 0 and out["after_Y"] == 1 and out["after_1"] == 0)
    step_result("weapons", ok, **out)

def step_roll():
    """(level 3) the roll: B standing (backward), B walking (forward), B twice, the gamepad's B; what moves her and her body"""
    c = cb(); p = G["pawn"]; gen = G["gen"]; c.revive(True); c.set_scripted_only(False); c.set_run_mode(False); yield from wait(0.5)
    s = gen.get_start_room_center(); dist = gen.get_editor_property("roll_distance"); out = {}
    G["pc"].set_ignore_look_input(True); G["pc"].set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=0))
    def roll(label, held=(), press="B", twice=False):
        p.set_actor_location(V(s.x, s.y, 100.0), False, True); p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=0), True); yield from wait(0.8)
        for k in held: c.simulate_key(key(k), True)
        if held: yield from wait(0.7)
        a = p.get_actor_location(); yaw0 = p.get_actor_rotation().yaw; r0 = c.rolls; stand = p.mesh.get_socket_location("pelvis").z - a.z; low = stand; back = False
        c.simulate_key(key(press), True); yield from wait(0.1); c.simulate_key(key(press), False)
        t0 = now(); seen_roll = False
        while now() - t0 < 1.3:
            if c.is_rolling(): seen_roll = True; back = back or c.is_rolling_back(); low = min(low, p.mesh.get_socket_location("pelvis").z - p.get_actor_location().z)
            if twice and 0.2 < now() - t0 < 0.3: c.simulate_key(key(press), True)
            if twice and now() - t0 >= 0.3: c.simulate_key(key(press), False)
            yield
        for k in held: c.simulate_key(key(k), False)
        b = p.get_actor_location(); d_ = V(b.x - a.x, b.y - a.y, 0)
        out[label] = {"rolls": c.rolls - r0, "back": back, "moved_x_cm": round(d_.x), "moved_y_cm": round(d_.y), "turned_deg": round((p.get_actor_rotation().yaw - yaw0 + 180) % 360 - 180, 1),
                      "middle_lowest_cm": round(low - stand), "upright_after": not c.is_rolling()}
        yield from wait(0.4)
    yield from roll("standing")
    yield from roll("walking", held=("W",))
    yield from roll("twice", twice=True)
    yield from roll("pad", press="Gamepad_FaceButton_Right")
    yield from wait(0.5); n0 = c.attacks_made; ok_attack = c.start_attack()
    while c.is_attacking(): yield
    out["strike_after"] = bool(ok_attack and c.attacks_made == n0 + 1)
    G["pc"].set_ignore_look_input(False)
    st, wk = out["standing"], out["walking"]
    # (standing she rolls back: the start of the walk is in the 0.7 s before the press, so the walk roll is measured from there)
    ok = (st["rolls"] == 1 and st["back"] and -1.25 * dist < st["moved_x_cm"] < -0.7 * dist and abs(st["moved_y_cm"]) < 60 and abs(st["turned_deg"]) < 3 and st["middle_lowest_cm"] < -35
          and wk["rolls"] == 1 and not wk["back"] and 0.7 * dist < wk["moved_x_cm"] < 1.5 * dist and abs(wk["moved_y_cm"]) < 60 and wk["middle_lowest_cm"] < -35
          and out["twice"]["rolls"] == 1 and out["pad"]["rolls"] == 1 and all(v["upright_after"] for k, v in out.items() if isinstance(v, dict)) and out["strike_after"])
    step_result("roll", ok, roll_distance=dist, **out)

def step_dodge():
    """(level 3) a blow in the middle of a roll misses her; after it, it lands"""
    c = cb(); p = G["pawn"]; gen = G["gen"]; c.revive(True); c.set_scripted_only(True); yield from wait(1.2)
    m = next(iter(start_monsters()), None); h0 = c.get_health(); d0 = c.dodged_hits
    c.start_roll(V(1, 0, 0)); yield from wait(0.3)
    mid = c.is_dodging(); c.apply_damage(10.0, m); h1 = c.get_health(); d1 = c.dodged_hits
    while c.is_rolling(): yield
    yield from wait(0.5); dodging_after = c.is_dodging(); c.apply_damage(10.0, m); h2 = c.get_health()
    ok = mid and h1 == h0 and d1 == d0 + 1 and not dodging_after and abs((h1 - h2) - 10.0) < 0.01
    step_result("dodge", ok, dodging_mid_roll=bool(mid), hit_points_before=h0, after_the_blow_mid_roll=h1, dodged=d1 - d0, after_the_blow_after_it=h2)
    c.revive(True); c.set_scripted_only(False)

def step_tier():
    gen = G["gen"]; c = cb(); s = unreal.IntPoint(1, 0)
    made = gen.generate_section_now(s); yield from wait(0.5)
    ms = [m for m in gen.get_monsters() if alive(m) and m.get_editor_property("section").get_editor_property("coord") == s]
    hp = sum(m.get_max_health() for m in ms) / max(len(ms), 1); dmg = sum(m.get_damage() for m in ms) / max(len(ms), 1); avg = gen.get_average_weapon_damage()
    ok = len(ms) >= 5 and 0.75 <= hp / c.get_max_health() <= 1.25 and 0.75 <= dmg / avg <= 1.25
    step_result("tier", ok, section=[1, 0], monsters=len(ms), average_hit_points=round(hp, 1), hers=c.get_max_health(), average_damage=round(dmg, 1), spell_damage=round(avg, 1))

def step_walls():
    """the broken walls (wall_check.py): what is seen of every broken segment of the start section from its room (the wall,
    or the backing through a hole: never beyond the wall), she cannot get into a hole by pushing or jumping, and dropped
    below the floor she is put back where she stood"""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import wall_check as WC; import importlib; importlib.reload(WC)       # (the editor keeps modules: an edited one must be reloaded)
    c = cb(); p = G["pawn"]; gen = G["gen"]; c.revive(True); c.set_scripted_only(True); yield from wait(0.5)
    secs = [gen.get_section(unreal.IntPoint(0, 0))]; ign = [p] + list(gen.get_monsters())
    r0 = WC.rays(G["w"], secs, ign, without_backing=True); r0.pop("spots")          # (what was seen before: the holes go right through)
    r = WC.rays(G["w"], secs, ign); ce = WC.cells(G["w"], secs, ign)
    wi = yield from WC.walk_in(G["w"], p, r.pop("spots"), wait, now)
    c.revive(True); fl = yield from WC.fall(gen, p, wait)
    ok = r["segments"] > 0 and r0["leak"] > 0 and r["hole"] > 0 and r["leak"] == 0 and wi["ok"] and fl["ok"] and ce["ok"]
    step_result("walls", ok, **r, without_backing={k: r0[k] for k in ("segments", "rays", "face", "hole", "leak")}, walk_in=wi, fall=fl, cells=ce)
    c.revive(True); c.set_scripted_only(False)

def step_face():
    """her face, measured in pictures of it: each channel and each morph target alone changes it; the occasions show theirs"""
    gen = G["gen"]; p = G["pawn"]; c = cb()
    f = p.get_component_by_class(unreal.RDFaceComponent)
    cams = [a for a in GS.get_all_actors_of_class(G["w"], unreal.SceneCapture2D) if a.actor_has_tag("RDM5_FaceCam")]
    assert f is not None and cams, "no face component on her or no RDM5_FaceCam in the level"
    cam = cams[0]; cc = cam.capture_component2d; rt = cc.texture_target
    cc.set_editor_property("primitive_render_mode", unreal.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST)
    cc.show_only_actor_components(p, True)
    aggro = (gen.get_editor_property("aggro_distance"), gen.get_editor_property("lose_distance"))
    gen.set_editor_property("aggro_distance", 0.0); gen.set_editor_property("lose_distance", 1.0)
    s0 = gen.get_start_room_center(); p.set_actor_location(V(s0.x, s0.y, 100), False, True); p.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=0), True)
    f.set_editor_property("blink", False); f.clear_manual()
    # (still pictures: her idle stopped and the colour as painted, unlit: the idle and the torches' flicker changed two
    # pictures of her at rest by 3 %, as much as some expressions)
    p.mesh.set_editor_property("global_anim_rate_scale", 0.0)
    cc.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_BASE_COLOR)
    yield from wait(1.2)
    outdir = os.path.join(unreal.Paths.project_saved_dir(), "FaceTest", TAG); os.makedirs(outdir, exist_ok=True)      # (test pictures: not in SourceArt)
    def shoot(name=None):
        h = p.mesh.get_socket_location("head"); fw = p.get_actor_forward_vector()
        at = V(h.x + fw.x * 9, h.y + fw.y * 9, h.z + 6)                     # (the face: in front of the head bone, a little up)
        loc = V(at.x + fw.x * 62, at.y + fw.y * 62, at.z + 2)
        cam.set_actor_location(loc, False, True); cam.set_actor_rotation(ML.find_look_at_rotation(loc, at), True)
        cc.capture_scene()
        px = unreal.RenderingLibrary.read_render_target(G["w"], rt)
        if name: unreal.RenderingLibrary.export_render_target(G["w"], rt, outdir, f"face_{TAG}_{name}")
        return [(q.r, q.g, q.b) for q in px]
    def changed(a, b, thr=18):
        n = sum(1 for x, y in zip(a, b) if abs(x[0] - y[0]) + abs(x[1] - y[1]) + abs(x[2] - y[2]) > thr)
        return n / max(len(a), 1)
    def settle(sec=0.25):
        yield from wait(sec)
    rest = shoot("rest"); yield from settle(0.2); rest2 = shoot()
    noise = changed(rest, rest2)
    lit = sum(1 for q in rest if q[0] + q[1] + q[2] > 60) / len(rest)
    chans = {str(x.name): x for x in gen.get_editor_property("face_channels")}
    out = {}; bad = []
    for name, ch in chans.items():
        f.set_manual(name, 1.0); yield from settle()
        img = shoot(name)
        morphs = {str(k): round(f.get_morph_weight(k), 3) for k in ch.morphs.keys()}; params = {str(k): round(f.get_param_value(k), 3) for k in ch.params.keys()}
        want_m = {str(k): min(1.0, v) for k, v in ch.morphs.items()}; want_p = {str(k): min(1.0, v) for k, v in ch.params.items()}
        ok_n = all(abs(morphs[k] - want_m[k]) < 0.02 for k in morphs) and all(abs(params[k] - want_p[k]) < 0.02 for k in params)
        frac = changed(rest, img)
        out[name] = {"face_changed": round(frac, 4), "morphs": morphs, "params": params, "numbers_ok": ok_n}
        if not ok_n or frac < max(0.01, noise * 4): bad.append(name)
        f.set_manual(name, 0.0); yield from settle()
    # each morph target alone (a channel of its own, for the test)
    morph_names = sorted({str(k) for x in chans.values() for k in x.morphs.keys()})
    keep = list(f.get_editor_property("channels")); alone = {}
    for m in morph_names:
        t = unreal.RDFaceChannel(); t.set_editor_property("name", "Test_" + m); t.set_editor_property("morphs", {m: 1.0})
        f.set_editor_property("channels", keep + [t]); f.set_manual("Test_" + m, 1.0); yield from settle()
        img = shoot("morph_" + m); frac = changed(rest, img, 10)
        alone[m] = {"weight": round(f.get_morph_weight(m), 3), "face_changed": round(frac, 4)}
        if frac < max(0.002, noise * 2): bad.append("morph " + m)
        f.set_manual("Test_" + m, 0.0); yield from settle()
    f.set_editor_property("channels", keep); yield from settle()
    p.mesh.set_editor_property("global_anim_rate_scale", 1.0)
    # the occasions
    occ = {}
    def peak(chname, sec):
        best = 0.0; t0 = now()
        while now() - t0 < sec:
            best = max(best, f.get_channel_weight(chname)); yield
        occ.setdefault("_peaks", {})[chname] = round(best, 3)
    c.apply_damage(4.0, None); yield from peak("Pain", 0.5); hurt_peak = occ["_peaks"]["Pain"]; yield from wait(1.2); hurt_after = f.get_channel_weight("Pain")
    occ["hurt"] = {"peak": hurt_peak, "after_1.7s": round(hurt_after, 3)}
    c.set_health(c.get_max_health()); yield from wait(0.3)
    c.start_attack(); yield from peak("Focus", 0.7); occ["cast"] = {"peak": occ["_peaks"]["Focus"]}
    yield from wait(1.2)
    c.set_health(c.get_max_health() * 0.2); yield from wait(1.6); low = f.get_channel_weight("Fear")
    c.set_health(c.get_max_health()); yield from wait(1.8); low_after = f.get_channel_weight("Fear")
    occ["low_health"] = {"held": round(low, 3), "after_recovery": round(low_after, 3)}
    # a fight: a monster of the start section after her, near her
    gen.set_editor_property("aggro_distance", aggro[0]); gen.set_editor_property("lose_distance", aggro[1])
    ms = start_monsters(); fight = {"monster": None}
    if ms and stand_off(ms[0], 700.0):
        t0 = now()
        while now() - t0 < 4.0 and not ms[0].is_aggro(): yield
        yield from wait(1.0); fight = {"monster": str(ms[0].monster_name), "aggro": bool(ms[0].is_aggro()), "anger": round(f.get_channel_weight("Anger"), 3)}
        gen.set_editor_property("aggro_distance", 0.0); gen.set_editor_property("lose_distance", 1.0)
        p.set_actor_location(V(s0.x, s0.y, 100), False, True); yield from wait(2.5)
        fight["anger_after_it_left"] = round(f.get_channel_weight("Anger"), 3); fight["its_aggro_after"] = bool(ms[0].is_aggro())
    else: gen.set_editor_property("aggro_distance", 0.0); gen.set_editor_property("lose_distance", 1.0)
    occ["fight"] = fight
    c.set_health(c.get_max_health()); yield from wait(0.5)
    c.apply_damage(1000.0, None); yield from wait(0.8)
    occ["death"] = {"dead": round(f.get_channel_weight("Dead"), 3), "eyes_shut": round(f.get_param_value("EyesClosed"), 3)}
    c.revive(True); yield from wait(1.5); occ["after_revive_dead"] = round(f.get_channel_weight("Dead"), 3)
    # blinks over quiet seconds
    p.set_actor_location(V(s0.x, s0.y, 100), False, True)
    f.set_editor_property("blink", True); b0 = f.get_blinks(); top = 0.0; low_ = 1.0; t0 = now()
    while now() - t0 < 12.0:
        v = f.get_param_value("EyesClosed"); top = max(top, v); low_ = min(low_, v); yield
    occ["blinks"] = {"in_12s": f.get_blinks() - b0, "eyes_shut_most": round(top, 3), "least": round(low_, 3)}
    counts = {str(k): v for k, v in f.get_cue_counts().items()}
    gen.set_editor_property("aggro_distance", aggro[0]); gen.set_editor_property("lose_distance", aggro[1])
    cam.set_actor_location(V(0, 0, -5000), False, True)
    ok_occ = (hurt_peak > 0.8 and hurt_after < 0.05 and occ["cast"]["peak"] > 0.8 and low > 0.6 and low_after < 0.05 and fight.get("anger", 0) > 0.5
              and fight.get("anger_after_it_left", 1) < 0.1 and occ["death"]["dead"] > 0.9 and occ["death"]["eyes_shut"] > 0.9 and occ["after_revive_dead"] < 0.05
              and occ["blinks"]["in_12s"] >= 2 and occ["blinks"]["eyes_shut_most"] > 0.9 and occ["blinks"]["least"] < 0.05)
    ok = not bad and ok_occ and lit > 0.05 and len(chans) >= 8
    step_result("face", ok, channels=out, morphs_alone=alone, occasions=occ, cue_counts=counts, rest_noise=round(noise, 4), face_lit_share=round(lit, 3), failed=bad, pictures=outdir)

STEPS = {"setup": step_setup, "keys": step_keys, "pad": step_pad, "hair": step_hair, "walls": step_walls, "cast": step_cast, "nothing": step_nothing, "far": step_far, "kill": step_kill, "tier": step_tier, "sword": step_sword, "dual": step_dual,
         "daggers": step_sword, "weapons": step_weapons, "roll": step_roll, "dodge": step_dodge, "face": step_face}
def run():
    for s in PLAN:
        name, _, arg = s.partition(":")
        yield from (STEPS[name](int(arg)) if arg else STEPS[name]())
        yield from wait(0.3)
def finish(err=None):
    unreal.unregister_slate_post_tick_callback(G["h"])
    R["error"] = err
    try:
        c = cb(); R.update({"rolls": c.rolls, "dodged": c.dodged_hits, "kills": c.kills, "casts": c.attacks_made, "bolts": c.bolts_cast, "bolts_on_monsters": c.bolts_on_monsters, "bolts_elsewhere": c.bolts_elsewhere, "deaths": c.deaths,
                            "damage_dealt": c.damage_dealt, "damage_taken": c.damage_taken})
        c.set_scripted_only(False)
    except Exception as e: R["error"] = (err or "") + " / " + str(e)
    os.makedirs(OUT, exist_ok=True); json.dump(R, open(os.path.join(OUT, f"test_{TAG}.json"), "w"), indent=1)
    ok = not R.get("error") and len(R["steps"]) == len(PLAN) and all(s["ok"] for s in R["steps"])
    unreal.log(f"RDMTEST done | {TAG} | {'ok' if ok else 'FAILED'} | " + " | ".join(f"{s['step']} {'ok' if s['ok'] else 'FAILED'}" for s in R["steps"]) + f" | {R.get('error') or ''}")
    G.clear()
def tick(dt):
    try:
        if unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is None: finish("PIE ended"); return
        next(G["gen_"])
    except StopIteration: finish()
    except Exception as e:
        import traceback
        unreal.log_error("RDMTEST error: " + str(e) + traceback.format_exc()); finish(str(e))
G["gen_"] = run()
G["h"] = unreal.register_slate_post_tick_callback(tick)
print("magic test armed:", PLAN, TAG)
