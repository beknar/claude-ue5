"""Shared by 840 / 841 / 848 (and the face test): a MetaHuman face's data file as the C++ structs. Default
SourceArt/summoner/face_mh.json (the first Summoner's: a MetaHuman face on her anime body); load("summoner2/face_s2.json")
is Summoner2's (a whole MetaHuman: face on its own body). meta_face() an RDMetaFace (the face mesh, its placement on the
body, the bones it follows, the body's material if any, the grooms, the outfits), channels() the expression channels with
their control curves (the old face.json's morphs and painted patches left out). The first Summoner's placement is measured
on the face mesh itself (a component without animation in the editor world: its eye joints' middle), scaled by 'scale'
about it and put at 'eyes_at'; 'placement': 'identity' keeps the face where the build put it on its body."""
import json, os, unreal
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
J = json.load(open(os.path.join(SA, "summoner", "face_mh.json")))


def load(rel):
    return json.load(open(os.path.join(SA, rel)))


def face_eyes(mesh):
    """the face mesh's eye joints' middle in its own space (its rest: a component without animation)"""
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    a = eas.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    try:
        c = a.skeletal_mesh_component; c.set_skeletal_mesh_asset(mesh)
        L = c.get_socket_location("FACIAL_L_Eye"); R = c.get_socket_location("FACIAL_R_Eye")
        return (L + R) * 0.5, (L - R).length()
    finally:
        eas.destroy_actor(a)


def meta_face(j=None):
    j = j or J
    mesh = unreal.load_asset(j["face_mesh"]); assert mesh, j["face_mesh"] + ": build the MetaHuman first (838 / 844)"
    E, apart = face_eyes(mesh)
    if j.get("placement") == "identity":
        t = unreal.Transform(); s = 1.0; info = {"placement": "identity"}
    else:
        s = j["scale"]; at = unreal.Vector(*j["eyes_at"])
        t = unreal.Transform(location=at - E * s, rotation=unreal.Rotator(0, 0, 0), scale=unreal.Vector(s, s, s))
        info = {"scale": s, "eyes_at": j["eyes_at"]}
    mf = unreal.RDMetaFace()
    mf.mesh = mesh; mf.placement = t
    mf.bones = {unreal.Name(k): unreal.Name(v) for k, v in j["bones"].items()}
    if j.get("body_material"): mf.body_material = unreal.load_asset(j["body_material"])
    gs = []
    for g in j["grooms"]:
        x = unreal.RDMetaFaceGroom(); x.groom = unreal.load_asset(g["groom"]); x.binding = unreal.load_asset(g["binding"])
        assert x.groom and x.binding, g["groom"]
        x.scalars = {unreal.Name(k): float(v) for k, v in g.get("scalars", {}).items()}; gs.append(x)
    mf.grooms = gs; mf.forced_lod = 0
    outs = [unreal.load_asset(p) for p in j.get("outfits", [])]
    assert all(outs), j.get("outfits")
    mf.outfits = outs
    info.update({"eyes_rest": [round(E.x, 2), round(E.y, 2), round(E.z, 2)], "eyes_apart_cm": round(apart, 2)})
    return mf, info


def channels(j=None):
    j = j or J
    if "channels_from" in j: j = load(j["channels_from"])
    out = []
    for name, curves in j["channels"].items():
        c = unreal.RDFaceChannel(); c.name = name
        c.curves = {unreal.Name("CTRL_expressions_" + k): float(v) for k, v in curves.items()}
        out.append(c)
    return out
