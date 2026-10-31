"""random_dungeonmagic_level4 demo reel: the menu's pilot and recorder (the render of random_dungeonmagic_level4_select,
LS_RDM4select_Showcase: 814 with "4select", 816 with "4select"). Arm it right before 816: it waits for the render's world,
then from frame 0 plays four passages of PASSAGE seconds, one for each hero in the reel's order, with the menu's own keys
(ARDHeroSelect.SimulateKey: what A / D and Enter do): in the first the Warrior is shown and she looks through the others
(D, D, A, A) before START; then D to the Mage, START; D to the Warlock, a look at the Rogue (D) and back (A), START; D to
the Rogue, START. START does not leave the menu in the reel (bStayOnConfirm: the queue renders one level; the dungeon is
rendered on its own, a run for each hero, 815 with level 4). The reel's overlay (rdm4_reel_assemble.py) cuts the render
into the four passages and draws the menu over it from this record, which has every frame's hero shown, when she was
shown, when START was pressed, the turntable's turn and the key pressed. Writes SourceArt/random_dungeon_magic4/cine_menu.json
and logs "RDM4MENU saved". Keeps its namespace (tick callback).
Level 5 (random_dungeonmagic_level5_select, LS_RDM5select_Showcase; the Summoner's armour reel): one passage, in which
she looks through the five heroes with D from the Warrior to the Summoner and presses START; the record goes to
SourceArt/random_dungeon_magic5/cine_menu.json. Level 5 with "Warrior" (the weapons and tiers reel): she looks through all
five and round to the Warrior again, START on her (cine_menu_warrior.json). Level 5 with "quartet" (the four heroes'
weapons reel, 815's run5h): level 4's four passages on level 5's menu, START on the Warrior, the Mage, the Warlock and the
Rogue in turn, the Summoner never picked (cine_menu_quartet.json). Level 5 with "caps" (the four heroes' capabilities
reel, 815's run5x; the menu's four heroes since 2026-10-26): level 4's four passages as they are (cine_menu_caps.json).
Level "mw" (mistward_castle_select, LS_RDMmwselect_Showcase; 815's run5m): level 4's four passages as they are; the record
(SourceArt/mistward/cine_menu_mw.json) also has the game's title over the menu (ARDHeroSelect's GameTitle, "Mistward Castle").
Level "mw" with "five" (the castle's five heroes, the Martial Artist the fifth: 815's "mistward3"): a fifth passage, D to
her and START (cine_menu_mw5.json). With "six" (the castle's six heroes, the Summoner the sixth: 815's "mistward4"): a sixth
passage, D to her and START (cine_menu_mw6.json).
Args: [seconds a passage, 7] [level: 4, 5 or mw] [level 5: the hero picked, Summoner or Warrior, or quartet, or caps; mw: five or six]"""
import unreal, sys, json, os
__keep__ = True
PASSAGE = float(sys.argv[1]) if len(sys.argv) > 1 else 7.0
LV = sys.argv[2] if len(sys.argv) > 2 else "4"
OUT = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_magic%s\cine_menu.json" % LV
GS = unreal.GameplayStatics; ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
# (seconds into a passage, key); the passages in the reel's order: Warrior, Mage, Warlock, Rogue
PLAN = [[(1.1, "D"), (2.2, "D"), (3.4, "A"), (4.5, "A"), (5.7, "Enter")],
        [(1.6, "D"), (4.6, "Enter")],
        [(1.4, "D"), (3.0, "D"), (4.0, "A"), (5.5, "Enter")],
        [(1.6, "D"), (4.8, "Enter")]]
WANT = ["Warrior", "Mage", "Warlock", "Rogue"]
PICK = sys.argv[3] if len(sys.argv) > 3 else "Summoner"
if LV == "mw":
    OUT = r"E:\code\claude-ue5\claude_ue5\SourceArt\mistward\cine_menu_mw.json"
    if PICK in ("five", "six"):
        # (the castle's five heroes (the user's of 2026-10-29: the Martial Artist the fifth): a fifth passage, D from the Rogue to
        # her, START; six (the user's of 2026-10-30: the Summoner the sixth): a sixth, D from the Martial Artist to her)
        PLAN = PLAN + [[(1.6, "D"), (4.8, "Enter")]]; WANT = WANT + ["MartialArtist"]
        if PICK == "six": PLAN = PLAN + [[(1.6, "D"), (4.8, "Enter")]]; WANT = WANT + ["Summoner"]
        OUT = OUT.replace("cine_menu_mw.json", "cine_menu_mw6.json" if PICK == "six" else "cine_menu_mw5.json")
elif LV == "5" and PICK == "caps":
    # (the four heroes' capabilities reel, 815's run5x: the menu has four heroes since 2026-10-26 (the Summoner left off,
    # the Warrior Warrior3): level 4's four passages as they are)
    OUT = OUT.replace("cine_menu.json", "cine_menu_caps.json")
elif LV == "5" and PICK == "quartet":
    # (the four heroes' weapons reel: level 4's passages; in the last the Summoner is looked at (D) and left (A))
    PLAN = PLAN[:3] + [[(1.2, "D"), (2.6, "D"), (3.9, "A"), (5.3, "Enter")]]
    OUT = OUT.replace("cine_menu.json", "cine_menu_quartet.json")
elif LV == "5" and PICK == "Warrior":
    # (the weapons and tiers reel: all five looked at, round to the Warrior again (the list wraps), START on her)
    PLAN = [[(1.0, "D"), (1.9, "D"), (2.8, "D"), (3.7, "D"), (4.6, "D"), (5.9, "Enter")]]; WANT = ["Warrior"]
    OUT = OUT.replace("cine_menu.json", "cine_menu_warrior.json")
elif LV == "5":
    PLAN = [[(1.2, "D"), (2.2, "D"), (3.2, "D"), (4.2, "D"), (5.7, "Enter")]]; WANT = ["Summoner"]
FPS = 30; DUR = PASSAGE * len(PLAN)
G = {}; S = {"rows": {}, "events": [], "saved": False}
if getattr(unreal, "_rdm4_menu", None) is not None:
    try: unreal.unregister_slate_post_tick_callback(unreal._rdm4_menu)
    except Exception: pass
def key(n): k = unreal.Key(); k.set_editor_property("key_name", n); return k
def card_data(s):
    heroes = []
    if s is not None:
        for h in s.heroes:
            # (what the card shows: the bars, the line of her other numbers, the abilities, each weapon and spell with its picture)
            heroes.append({"name": str(h.name), "title": h.title, "hp": h.max_health, "mana": h.max_mana, "abilities": list(h.abilities), "armour": h.armour,
                           "starts_with": h.starts_with, "accent": [h.accent.r, h.accent.g, h.accent.b], "mana_per_second": h.mana_per_second,
                           "melee_bonus": h.melee_bonus, "ranged_bonus": h.ranged_bonus, "roll": h.roll_clip is not None,
                           "weapons": [{"name": str(w.name), "icon": str(w.icon), "damage": w.damage, "reach": w.reach, "spell": bool(w.spell),
                                        "bolt": w.bolt_mesh is not None, "mana": w.mana_cost} for w in h.weapons]})
    return heroes
def save(why=None):
    if S["saved"]: return
    S["saved"] = True
    heroes = G.get("heroes", [])          # (read when it was armed: at the render's end the menu's actor may be gone)
    rows = [S["rows"][k] for k in sorted(S["rows"])]
    picked = [e["hero"] for e in S["events"] if e["kind"] == "start"]
    out = {"fps": FPS, "passage": PASSAGE, "rows": rows, "events": S["events"], "heroes": heroes, "picked": picked, "want": WANT, "error": why, "game_title": G.get("title", "")}
    os.makedirs(os.path.dirname(OUT), exist_ok=True); json.dump(out, open(OUT, "w"), indent=0)
    ok = picked == WANT and not why
    (unreal.log if ok else unreal.log_error)("RDM4MENU %s | %d frames | picked %s | %s" % ("saved" if ok else "failed", len(rows), picked, why or ""))
def stop(why=None):
    unreal.unregister_slate_post_tick_callback(unreal._rdm4_menu); unreal._rdm4_menu = None
    try: save(why)
    finally: G.clear()
def body():
    w = ues.get_game_world()
    if "sel" not in G:
        if w is None: return
        sels = GS.get_all_actors_of_class(w, unreal.RDHeroSelect); lsa = GS.get_all_actors_of_class(w, unreal.LevelSequenceActor)
        if not sels or not lsa or lsa[0].get_editor_property("sequence_player") is None: return
        G.update({"w": w, "sel": sels[0], "player": lsa[0].get_editor_property("sequence_player"), "going": False, "down": [], "done": set()})
        sels[0].set_editor_property("stay_on_confirm", True); G["heroes"] = card_data(sels[0]); G["title"] = str(sels[0].get_editor_property("game_title"))
        unreal.log("RDM4MENU armed, %d passages of %.1f s" % (len(PLAN), PASSAGE))
    if w is None or not unreal.SystemLibrary.is_valid(G["sel"]): stop(None if G.get("t", 0.0) >= DUR - 0.05 else "the world ended"); return
    if S["saved"]: return
    s = G["sel"]; wt = GS.get_time_seconds(G["w"])
    sec = unreal.TimeManagementLibrary.conv_qualified_frame_time_to_seconds(G["player"].get_current_time())
    if not G["going"]:
        if sec <= 1e-4: G["w0"] = wt; return
        G["going"] = True; G["w0"] = wt; s.show(0); S["events"].append({"t": 0.0, "kind": "begin"})
    t = wt - G["w0"]; G["t"] = t; frame = int(sec * FPS + 1e-3)
    # keys let go a tenth of a second after they went down
    for k, tu in list(G["down"]):
        if t >= tu: s.simulate_key(key(k), False); G["down"].remove((k, tu))
    p = min(int(t // PASSAGE), len(PLAN) - 1); tp = t - p * PASSAGE; pressed = ""
    for i, (at, k) in enumerate(PLAN[p]):
        if (p, i) in G["done"] or tp < at: continue
        G["done"].add((p, i)); s.simulate_key(key(k), True); G["down"].append((k, t + 0.1)); pressed = k
        S["events"].append({"t": round(t, 3), "frame": frame, "kind": "key", "key": k, "passage": p})
        G["key"] = (k, t)
    # (START: the menu says what it opened)
    if s.confirm_time > G.get("confirm", -50.0):
        G["confirm"] = s.confirm_time; S["events"].append({"t": round(t, 3), "frame": frame, "kind": "start", "hero": str(s.get_hero_name()), "opened": s.opened, "passage": p})
        unreal.log("RDM4MENU %.2f s START %s" % (t, s.opened))
    # (when the hero shown changed: the HUD fades her card in)
    if s.get_index() != G.get("shown_i"): G["shown_i"] = s.get_index(); G["shown_t"] = wt
    if frame >= 0 and frame not in S["rows"]:
        f = s.figures[s.get_index()]
        k = G.get("key")
        S["rows"][frame] = {"frame": frame, "t": round(t, 4), "hero": s.get_index(), "shown_ago": round(wt - G["shown_t"], 3), "start_ago": round(wt - s.confirm_time, 3),
                            "turned": round(s.get_turned(), 2), "yaw": round(f.get_actor_rotation().yaw, 2), "key": k[0] if k and t - k[1] < 0.45 else ""}
    if t >= DUR + 0.4: save()
def tick(dt):
    try: body()
    except Exception as e:
        import traceback
        unreal.log_error("RDM4MENU error: " + str(e) + traceback.format_exc()); stop(str(e))
unreal._rdm4_menu = unreal.register_slate_post_tick_callback(tick)
print("menu pilot armed:", PASSAGE)
