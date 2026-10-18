"""Tripo trio / quartet showcase: the fire and the bolts, spawned while the Movie Render Queue renders LS_Tripo_Trio_Showcase or
LS_Tripo_Quartet_Showcase (arm it right before 662).
The casts' times are 660's (SourceArt/tripo_trio/plan.json), on the sequence's clock: from a cast's start to its release
the charge (Starter Content P_Sparks) burns on the casting hand; at the release the bolt (the warm copy of DarkHalls
NS_FirePool) leaves that hand and flies straight at the monster's chest at the spell's speed; where it arrives the burst
(P_Explosion and the warm NS_FireWings for a moment) goes off, and the stage's spell light flashes there; while the bolt
flies the light goes with it. Positions are read from the characters and monsters in the render's world, so the bolt
leaves the hand where the hand is. The quartet's crossbow bolts (663's "bolt" events): at the release the bolt actor
placed by 663 is put on the crossbow's muzzle (where the weapon actor is now) with the arrow trail on it, flies straight
at the monster's chest at the crossbow's speed (the mesh along its flight, placed as RDCombat places it) and stops 40 cm
short of the chest, where the pack's impact goes off and the bolt is put away. Logs every effect ("TRIO fx") and "TRIO
pilot done" at the end.
  render (default) | rehearse (a PIE session of the showcase level that plays the sequence);  trio (default) | quartet
Keeps its namespace (tick callback). Args: [render|rehearse] [trio|quartet]"""
import unreal, sys, json, math
__keep__ = True
MODE = sys.argv[1] if len(sys.argv) > 1 else "render"
WHICH = sys.argv[2] if len(sys.argv) > 2 else "trio"
LIGHT = 0.35          # (the stage's exposure is higher than the dungeon's: the spell light at the game's strength washes the fire out)
PLAN = json.load(open(r"E:\code\claude-ue5\claude_ue5\SourceArt\tripo_%s\plan.json" % WHICH))
SPELL = PLAN["spell"]; FPS = PLAN["fps"]; DUR = PLAN["seconds"]
V = unreal.Vector; GS = unreal.GameplayStatics
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
A = {k: unreal.load_asset(SPELL[k]) for k in ("charge", "bolt", "burst", "burst_flame")}
XB = PLAN.get("crossbow")
if XB:
    A["trail"] = unreal.load_asset(XB["trail"]); A["impact"] = unreal.load_asset(XB["hit_fx"]); bx = XB["bolt_xf"]
    XB["xf"] = unreal.Transform(V(*bx["loc"]), unreal.Rotator(roll=bx["rot"][0], pitch=bx["rot"][1], yaw=bx["rot"][2]), V(*bx["scale"]))
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
        t0 = unreal.TimeManagementLibrary.conv_qualified_frame_time_to_seconds(G["player"].get_current_time())
        for e in G["ev"]:                      # (a render of a part of the sequence: what was before it is not played)
            if e["release"] < t0 - 0.5: e["state"] = 3
        unreal.log("TRIO pilot armed (%s) | %d casts" % (MODE, len(G["ev"])))
    if w is None: stop(); return
    t = unreal.TimeManagementLibrary.conv_qualified_frame_time_to_seconds(G["player"].get_current_time()); G["t"] = t
    for e in G["ev"]:
        if e["kind"] == "bolt": crossbow_bolt(e, t); continue
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
def put_bolt(b, at, d):
    """the bolt mesh at a point of its flight, as RDCombat places it: the mesh's transform in a frame whose X is the flight"""
    frame = unreal.Transform(at, unreal.MathLibrary.make_rot_from_x(d), V(1, 1, 1))
    b.set_actor_transform(unreal.MathLibrary.compose_transforms(XB["xf"], frame), False, True)
def crossbow_bolt(e, t):
    if e["state"] == 0 and t >= e["release"]:
        xb = actor(e["weapon"]); b = actor(e["bolt"])
        frm = xb.get_actor_transform().transform_location(V(*XB["muzzle"])); c = chest(e["target"]); d = (c - frm).normal()
        to = c - d * 40.0
        e.update({"from": frm, "to": to, "dir": d, "dist": (to - frm).length(), "b": b}); put_bolt(b, frm, d)
        s = XB["trail_scale"]
        e["trail"] = GS.spawn_emitter_attached(A["trail"], b.static_mesh_component, unreal.Name("None"), V(0, 0, 0), unreal.Rotator(), V(s, s, s), unreal.AttachLocation.KEEP_RELATIVE_OFFSET, True)
        e["state"] = 2; log("crossbow bolt from (%.0f %.0f %.0f), %.0f cm to %s (%.0f %.0f %.0f)" % (frm.x, frm.y, frm.z, e["dist"], e["target"], to.x, to.y, to.z))
    if e["state"] == 2:
        u = min(1.0, (t - e["release"]) * XB["speed"] / max(e["dist"], 1.0)); at = e["from"] + (e["to"] - e["from"]) * u
        put_bolt(e["b"], at, e["dir"])
        if u >= 1.0:
            if e["trail"] is not None: e["trail"].deactivate()
            s = XB["hit_scale"]
            GS.spawn_emitter_at_location(G["w"], A["impact"], at, unreal.MathLibrary.make_rot_from_x(e["dir"] * -1.0), V(s, s, s), True)
            e["b"].set_actor_location(V(0, 4000, 0), False, True)
            e["state"] = 3; log("bolt hits %s after %.2f s" % (e["target"], t - e["release"]))
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
