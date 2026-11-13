"""The ridden horse's gaits into its def, shared by 913 (the Blender horse) and 915 (the Tripo horse) so both say the same (PR #55's
review): each clip's sole speed and the speeds the game changes gait at, all from the clips' record (farm_animals.py /
tripo_animals.py: walk_speed_cm_s, canter_speed_cm_s, run_speed_cm_s, canter_from_cm_s, gallop_from_cm_s; the list of
2026-11-12's gaits). A record without a canter keeps the old switch: the gallop from 250 cm/s."""
import unreal


def gaits_into_def(d, J, seqs):
    """d an unreal.RDHorseDef, J the horse's record, seqs its clips by name ("Walk", "Canter", "Run", ...)"""
    for k in ("Idle", "Walk", "Run", "Canter"): d.set_editor_property(k.lower(), seqs.get(k))
    d.set_editor_property("walk_clip_speed", float(J["walk_speed_cm_s"]))
    d.set_editor_property("run_clip_speed", float(J.get("run_speed_cm_s", 260.0)))
    canter = seqs.get("Canter") is not None and "canter_speed_cm_s" in J
    d.set_editor_property("canter_clip_speed", float(J.get("canter_speed_cm_s", 650.0)))
    d.set_editor_property("canter_from", float(J.get("canter_from_cm_s", 400.0)))
    d.set_editor_property("gallop_from", float(J.get("gallop_from_cm_s", 1300.0)) if canter else 250.0)
    if not canter: d.set_editor_property("canter", None)
    return {"walk": J["walk_speed_cm_s"], "canter": J.get("canter_speed_cm_s") if canter else None, "run": J.get("run_speed_cm_s"),
            "canter_from": d.get_editor_property("canter_from"), "gallop_from": d.get_editor_property("gallop_from")}
