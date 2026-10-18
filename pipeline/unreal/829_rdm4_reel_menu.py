"""random_dungeonmagic_level4 demo reel: the menu's pilot and recorder (the render of random_dungeonmagic_level4_select,
LS_RDM4select_Showcase: 814 with "4select", 816 with "4select"). Arm it right before 816: it waits for the render's world,
then from frame 0 plays four passages of PASSAGE seconds, one for each hero in the reel's order, with the menu's own keys
(ARDHeroSelect.SimulateKey: what A / D and Enter do): in the first the Warrior is shown and she looks through the others
(D, D, A, A) before START; then D to the Mage, START; D to the Warlock, a look at the Rogue (D) and back (A), START; D to
the Rogue, START. START does not leave the menu in the reel (bStayOnConfirm: the queue renders one level; the dungeon is
rendered on its own, a run for each hero, 815 with level 4). The reel's overlay (rdm4_reel_assemble.py) cuts the render
into the four passages and draws the menu over it from this record, which has every frame's hero shown, when she was
shown, when START was pressed, the turntable's turn and the key pressed. Writes SourceArt/random_dungeon_magic4/cine_menu.json
and logs "RDM4MENU saved". Keeps its namespace (tick callback). Args: [seconds a passage, 7]"""
import unreal, sys, json, os
__keep__ = True
PASSAGE = float(sys.argv[1]) if len(sys.argv) > 1 else 7.0
FPS = 30; DUR = PASSAGE * 4
OUT = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_magic4\cine_menu.json"
GS = unreal.GameplayStatics; ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
# (seconds into a passage, key); the passages in the reel's order: Warrior, Mage, Warlock, Rogue
PLAN = [[(1.1, "D"), (2.2, "D"), (3.4, "A"), (4.5, "A"), (5.7, "Enter")],
        [(1.6, "D"), (4.6, "Enter")],
        [(1.4, "D"), (3.0, "D"), (4.0, "A"), (5.5, "Enter")],
        [(1.6, "D"), (4.8, "Enter")]]
WANT = ["Warrior", "Mage", "Warlock", "Rogue"]
G = {}; S = {"rows": {}, "events": [], "saved": False}
if getattr(unreal, "_rdm4_menu", None) is not None:
    try: unreal.unregister_slate_post_tick_callback(unreal._rdm4_menu)
    except Exception: pass
def key(n): k = unreal.Key(); k.set_editor_property("key_name", n); return k
def save(why=None):
    if S["saved"]: return
    S["saved"] = True
    s = G.get("sel")
    heroes = []
    if s is not None:
        for h in s.heroes:
            heroes.append({"name": str(h.name), "title": h.title, "hp": h.max_health, "mana": h.max_mana, "abilities": list(h.abilities), "armour": h.armour,
                           "starts_with": h.starts_with, "accent": [h.accent.r, h.accent.g, h.accent.b]})
    rows = [S["rows"][k] for k in sorted(S["rows"])]
    picked = [e["hero"] for e in S["events"] if e["kind"] == "start"]
    out = {"fps": FPS, "passage": PASSAGE, "rows": rows, "events": S["events"], "heroes": heroes, "picked": picked, "want": WANT, "error": why}
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
        sels[0].set_editor_property("stay_on_confirm", True)
        unreal.log("RDM4MENU armed, %d passages of %.1f s" % (len(PLAN), PASSAGE))
    if w is None: stop(None if G.get("t", 0.0) >= DUR - 0.05 else "the world ended"); return
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
