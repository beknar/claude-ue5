"""Tripo trio showcase: the fire, spawned while the Movie Render Queue renders LS_Tripo_Trio_Showcase (arm it right before 662).
The casts' times are 660's (SourceArt/tripo_trio/plan.json), on the sequence's clock: from a cast's start to its release
the charge (Starter Content P_Sparks) burns on the casting hand; at the release the bolt (the warm copy of DarkHalls
NS_FirePool) leaves that hand and flies straight at the monster's chest at the spell's speed; where it arrives the burst
(P_Explosion and the warm NS_FireWings for a moment) goes off, and the stage's spell light flashes there; while the bolt
flies the light goes with it. Positions are read from the characters and monsters in the render's world, so the bolt
leaves the hand where the hand is. Logs every effect ("TRIO fx") and "TRIO pilot done" at the end.
  render (default) | rehearse (a PIE session of L_Tripo_Trio_Showcase that plays the sequence)
Keeps its namespace (tick callback). Args: [render|rehearse]"""
import unreal, sys, json, math
__keep__ = True
MODE = sys.argv[1] if len(sys.argv) > 1 else "render"
LIGHT = 0.35          # (the stage's exposure is higher than the dungeon's: the spell light at the game's strength washes the fire out)
PLAN = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\tripo_trio\plan.json"))
SPELL = PLAN["spell"]; FPS = PLAN["fps"]; DUR = PLAN["seconds"]
V = unreal.Vector; GS = unreal.GameplayStatics
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
A = {k: unreal.load_asset(SPELL[k]) for k in ("charge", "bolt", "burst", "burst_flame")}
G = {"ev": [dict(e, state=0) for e in PLAN["events"]], "timed": [], "flash": None}
if getattr(unreal, "_trio_pilot", None) is not None:
    try: unreal.unregister_slate_post_tick_callback(unreal._trio_pilot)
    except Exception: pass
def log(s): unreal.log("TRIO fx %6.2f s  %s" % (G.get("t", -1.0), s))
def actor(tag):
    a = GS.get_all_actors_with_tag(G["w"], unreal.Name(tag)); return a[0] if a else None
def mesh(tag): return actor(tag).skeletal_mesh_component
def chest(tag):
    """its chest: the actor stands on the floor, the chest about 55% of its height up (the mesh's bounds, scaled)"""
    a = actor(tag); m = a.skeletal_mesh_component; sk = m.get_skeletal_mesh_asset() if hasattr(m, "get_skeletal_mesh_asset") else m.skeletal_mesh
    b = sk.get_bounds(); l = a.get_actor_location(); return V(l.x, l.y, l.z + b.box_extent.z * 2.0 * 0.55 * a.get_actor_scale3d().z)
def light(at, cd):
    l = G["light"]
    if l is None: return
    l.set_actor_location(at, False, True); l.point_light_component.set_intensity(cd)
def body():
    w = ues.get_game_world()
    if "w" not in G:
        if w is None: return
        lsa = GS.get_all_actors_of_class(w, unreal.LevelSequenceActor)
        if not lsa or lsa[0].get_editor_property("sequence_player") is None: return
        G.update({"w": w, "player": lsa[0].get_editor_property("sequence_player")}); G["light"] = actor("trio_spell_light")
        if MODE == "rehearse": G["player"].play()
        unreal.log("TRIO pilot armed (%s) | %d casts" % (MODE, len(G["ev"])))
    if w is None: stop(); return
    t = unreal.TimeManagementLibrary.conv_qualified_frame_time_to_seconds(G["player"].get_current_time()); G["t"] = t
    for e in G["ev"]:
        if e["state"] == 0 and t >= e["charge"] and t < e["release"]:
            m = mesh(e["who"])
            e["charge_fx"] = GS.spawn_emitter_attached(A["charge"], m, unreal.Name(e["hand"]), V(0, 0, 0), unreal.Rotator(), V(SPELL["charge_scale"], SPELL["charge_scale"], SPELL["charge_scale"]),
                                                       unreal.AttachLocation.SNAP_TO_TARGET, True)
            e["state"] = 1; log("charge %s %s" % (e["who"], e["hand"]))
        if e["state"] in (0, 1) and t >= e["release"]:
            if e.get("charge_fx") is not None: e["charge_fx"].deactivate()
            frm = mesh(e["who"]).get_socket_location(unreal.Name(e["hand"])); to = chest(e["target"])
            e["from"], e["to"] = frm, to; e["dist"] = (to - frm).length()
            e["bolt"] = unreal.NiagaraFunctionLibrary.spawn_system_at_location(G["w"], A["bolt"], frm, unreal.Rotator(), V(SPELL["bolt_scale"], SPELL["bolt_scale"], SPELL["bolt_scale"]), True, True)
            e["state"] = 2; log("bolt from %s (%.0f %.0f %.0f), %.0f cm to %s (%.0f %.0f %.0f)" % (e["who"], frm.x, frm.y, frm.z, e["dist"], e["target"], to.x, to.y, to.z))
        if e["state"] == 2:
            u = min(1.0, (t - e["release"]) * SPELL["bolt_speed"] / max(e["dist"], 1.0))
            at = e["from"] + (e["to"] - e["from"]) * u
            if e["bolt"] is not None: e["bolt"].set_world_location(at, False, True)
            light(at, SPELL["light_cd"] * LIGHT)
            if u >= 1.0:
                if e["bolt"] is not None: e["bolt"].deactivate()
                GS.spawn_emitter_at_location(G["w"], A["burst"], at, unreal.Rotator(), V(SPELL["burst_scale"], SPELL["burst_scale"], SPELL["burst_scale"]), True)
                fl = unreal.NiagaraFunctionLibrary.spawn_system_at_location(G["w"], A["burst_flame"], at, unreal.Rotator(), V(SPELL["burst_flame_scale"], SPELL["burst_flame_scale"], SPELL["burst_flame_scale"]), True, True)
                G["timed"].append((t + SPELL["burst_flame_seconds"], fl)); G["flash"] = (t, at)
                e["state"] = 3; log("burst on %s after %.2f s" % (e["target"], t - e["release"]))
    for item in list(G["timed"]):
        if t >= item[0]:
            try: item[1].deactivate()
            except Exception: pass
            G["timed"].remove(item)
    if G["flash"] is not None and not any(e["state"] == 2 for e in G["ev"]):
        age = t - G["flash"][0]; k = max(0.0, 1.0 - age / 0.45)
        light(G["flash"][1], SPELL["light_cd"] * LIGHT * 3.0 * k * k)
        if k <= 0.0: G["flash"] = None; light(V(0, 0, -500), 0.0)
    if t >= DUR - 0.05 and not G.get("done"):
        G["done"] = True; unreal.log("TRIO pilot done | %s" % " ".join("%s:%d" % (e["who"][5:], e["state"]) for e in G["ev"]))
def stop():
    unreal.unregister_slate_post_tick_callback(unreal._trio_pilot); unreal._trio_pilot = None
    if not G.get("done"): unreal.log("TRIO pilot ended at %.2f s" % G.get("t", -1.0))
    G.clear()
def tick(dt):
    try: body()
    except Exception as e:
        import traceback
        unreal.log_error("TRIO pilot error: " + str(e) + traceback.format_exc()); stop()
unreal._trio_pilot = unreal.register_slate_post_tick_callback(tick)
print("trio pilot armed:", MODE)
