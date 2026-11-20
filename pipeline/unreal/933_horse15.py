"""The user's of 2026-11-18: "there is a new ultimate horse kit downloaded in the fab cache. use those resources to improve the horse
movement and riding mechanics" (the user's choices: the pack's own horse and clips; momentum and gaits, getting on and off, a jump
and a rear, the hooves' sound and dust, swimming; a natural gallop of about 12 m/s). The Ultimate Horse Pack (copied from the Fab
vault cache into Content/UltimateHorsePack, its demo levels left out) on brokenspire's horse (C++ RD/RDHorse15.cpp,
RD/RDHorseAnim.cpp; HorseDef.bPack). Steps (all by default, or name some):
  rider    the pack's rider clips (on its UE5 mannequin) retargeted onto the hero menu's six (hero_rigs.py) into
           /Game/RandomDungeon/Horse/Anims15/<rig>: idle, walk, gallop, up and down on each side, the jump's three, the rear
  measure  each hero's seat (her pelvis in the retargeted mount idle against the pack's rider's) and her feet at the mount's start;
           the horse's clips measured on its skeleton: each gait's ground speed (a planted hoof's speed back along the horse) and
           where each hoof lands; written to SourceArt/brokenspire/horse15.json
  level    brokenspire's HorseDef (the pack's realistic horse in a bay and a grey coat, its medieval saddle, its clips and their
           speeds, the ride's numbers, the rider socket's rest, the dust) and RiderClips by hero (with their offsets), the
           horse's sound sets (Horse.Hoof.Grass / Dirt / Hard, Horse.Neigh, Horse.Snort, Horse.Mount, Horse.Dismount, Horse.Jump,
           Horse.Swim, Horse.Hit: the pack's own cues)
C++ first. Args: [rider] [measure] [level]"""
import os, sys, json, math, unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); eal = unreal.EditorAssetLibrary; AL = unreal.AnimationLibrary
STEPS = [a for a in sys.argv[1:] if a in ("rider", "measure", "level")] or ["rider", "measure", "level"]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hero_rigs, importlib
importlib.reload(hero_rigs)
HERO_RIG = hero_rigs.HERO_RIG
P = "/Game/UltimateHorsePack"; PA = P + "/Animations"
RIGS = "/Game/RandomDungeon/Horse/Rigs15"; ANIMS = "/Game/RandomDungeon/Horse/Anims15"
MAP = "/Game/RandomDungeon/Maps/brokenspire"
SA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "claude_ue5", "SourceArt", "brokenspire"))
JSON = os.path.join(SA, "horse15.json")
# (her clip for each slot of RiderClips: the pack's rider)
RIDER = {"idle": "A_Rider_Mount_Idle", "walk": "A_Rider_Mounted_Walk_Slow", "run": "A_Rider_FastGallop",
         "mount_l": "A_Rider_MountUP_Left", "mount_r": "A_Rider_MountUP_Right", "dismount_l": "A_Rider_Dismount_Left", "dismount_r": "A_Rider_Dismount_Right",
         "jump_start": "A_Rider_Mounted_Jump_Start", "jump_loop": "A_Rider_Muonted_Jump_loop", "jump_land": "A_Rider_Mounted_Jump_End", "rear": "A_Rider_Rearing"}
HORSE_MESH = P + "/Meshes/SK_HorseRealistic"
HOOVES = ["Fingers_L", "Fingers_R", "Toes2_L", "Toes2_R"]          # (front left, front right, hind left, hind right)
# (the walk: the pack's alternate walk, which its own blend space uses: in A_Horse_Walk a planted hoof's speed back along the
# horse swings from -33 to 294 cm/s round its median of 94 (it slides 38 % of the speed whatever the rate: 888 horse15's first
# runs); in the alternate one it holds 145 within 1 %)
HORSE = {"idle": "A_Horse_Idle", "walk": "A_Horse_Walk_Alternate", "run": "A_Horse_Canter", "back": "A_Horse_Walk_Backwards_3", "stop": "A_Horse_SuddenStop2",
         "jump_start": "A_Horse_Jump_Start", "jump_loop": "A_Horse_Jump_Loop", "jump_land": "A_Horse_Jump_End", "rear": "A_Horse_Rearing",
         "swim_idle": "A_Horse_Swim_inPlace", "swim": "A_Horse_Swim"}
HITS = ["A_Horse_HitReact_Front2", "A_Horse_HitReact_back", "A_Horse_HitReact_Left", "A_Horse_HitReact_right"]
IDLES = ["A_horse_Idle_3", "A_horse_Idle_4", "A_horse_Idle_5"]
REPORT = []


# ---------------------------------------------------------------- a clip's bones in its mesh's component space
def uq(q): return (q.w, q.x, q.y, q.z)
def uv(v): return (v.x, v.y, v.z)
def qmul(a, b):
    aw, ax, ay, az = a; bw, bx, by, bz = b
    return (aw*bw-ax*bx-ay*by-az*bz, aw*bx+ax*bw+ay*bz-az*by, aw*by-ax*bz+ay*bw+az*bx, aw*bz+ax*by-ay*bx+az*bw)
def qrot(q, v):
    w, x, y, z = q; r = qmul(qmul(q, (0.0,) + tuple(v)), (w, -x, -y, -z)); return r[1:]
def vadd(a, b): return tuple(x + y for x, y in zip(a, b))


def rig_of(mesh):
    a = eas.spawn_actor_from_object(mesh, unreal.Vector(0, 0, -50000))
    c = a.get_editor_property("skeletal_mesh_component")
    names = [str(c.get_bone_name(i)) for i in range(c.get_num_bones())]
    out = (names, {n: str(c.get_parent_bone(n)) for n in names}, {n: c.get_ref_pose_transform(i) for i, n in enumerate(names)})
    eas.destroy_actor(a)
    return out


def bones_at(clip, rg, bones, frames=None):
    """[(frame, {bone: (x, y, z)})] in the mesh's component space; a locked root stays at its rest (as the game plays it)"""
    names, parent, ref = rg
    canon = {x.lower(): x for x in names}
    tracks = [str(x) for x in AL.get_animation_track_names(clip)]
    n = AL.get_num_frames(clip)
    lock = clip.get_editor_property("force_root_lock")
    out = []
    for f in (frames if frames is not None else range(n + 1)):
        f = max(0, min(n, f))
        loc = dict(ref)
        for b, tr in zip(tracks, AL.get_bone_poses_for_frame(clip, tracks, f, False)): loc[canon.get(b.lower(), b)] = tr
        if lock and names[0] in ref: loc[names[0]] = ref[names[0]]
        cs = {}
        def g(b):
            if b in cs: return cs[b]
            tr = loc[b]; r, p = uq(tr.rotation), uv(tr.translation)
            pb = parent.get(b, "None")
            if pb in ("None", "") or pb not in loc: cs[b] = (r, p)
            else:
                pr, pp = g(pb); cs[b] = (qmul(pr, r), vadd(pp, qrot(pr, p)))
            return cs[b]
        out.append((f, {b: g(b)[1] for b in bones if b in loc}))
    return out


def clip(name):
    c = unreal.load_asset(f"{PA}/{name}"); assert c, name
    return c


# ---------------------------------------------------------------- rider
if "rider" in STEPS:
    src = unreal.load_asset(P + "/Demo/Mannequins_UE5/Meshes/SK_Manny"); assert src, "the pack's mannequin"
    paths = [f"{PA}/{n}" for n in RIDER.values()]
    for hero, (ch, made, why) in hero_rigs.retarget_onto_heroes(src, paths, RIGS, ANIMS, "Rider15", "RIDER15").items():
        # (the getting down is the getting up played backwards (rate scale -1 on the pack's): kept so on hers)
        for a in made:
            base = a.get_name()[: -len(ch) - 1]
            want = clip(base).get_editor_property("rate_scale")
            if abs(a.get_editor_property("rate_scale") - want) > 1e-3: a.set_editor_property("rate_scale", want); eal.save_loaded_asset(a, False)
        REPORT.append(f"rider {hero}: {why}" if why else f"rider {hero} ({ch}): {len(made)} of {len(RIDER)}")

# ---------------------------------------------------------------- measure
if "measure" in STEPS:
    J = {"heroes": {}, "horse": {}}
    # (the pack's rider seated: its mount idle's pelvis; and its feet at the mount's start)
    manny = rig_of(unreal.load_asset(P + "/Demo/Mannequins_UE5/Meshes/SK_Manny"))
    seat_m = bones_at(clip(RIDER["idle"]), manny, ["pelvis"], [0])[0][1]["pelvis"]
    J["pack_seat_pelvis"] = [round(x, 2) for x in seat_m]
    FEET = ("foot_l", "foot_r", "ball_l", "ball_r")
    for hero, ch in HERO_RIG.items():
        mesh = unreal.load_asset(f"/Game/JRPG/Character/SK_JRPG_{ch}")
        if not mesh: REPORT.append(f"measure {hero}: no mesh"); continue
        rg = rig_of(mesh)
        names, parent, ref = rg
        idle = unreal.load_asset(f"{ANIMS}/{ch}/{RIDER['idle']}_{ch}")
        if not idle: REPORT.append(f"measure {hero}: no retargeted idle"); continue
        hp = bones_at(idle, rg, ["pelvis"], [0])[0][1]["pelvis"]
        # (her feet's rest height: the lowest of them in her reference pose, standing on the ground)
        rest = bones_at(idle, (names, parent, ref), [], [0])          # (only to keep the helper's shape)
        refcs = {}
        def gref(b):
            if b in refcs: return refcs[b]
            tr = ref[b]; r, p = uq(tr.rotation), uv(tr.translation); pb = parent.get(b, "None")
            if pb in ("None", "") or pb not in ref: refcs[b] = (r, p)
            else:
                pr, pp = gref(pb); refcs[b] = (qmul(pr, r), vadd(pp, qrot(pr, p)))
            return refcs[b]
        ankle = min(gref(b)[1][2] for b in FEET if b in ref)
        lows = []
        for k in ("mount_l", "mount_r"):
            c = unreal.load_asset(f"{ANIMS}/{ch}/{RIDER[k]}_{ch}")
            if c: lows.append(min(p[2] for p in bones_at(c, rg, list(FEET), [0])[0][1].values()))
        J["heroes"][hero] = {"rig": ch, "seat_pelvis": [round(x, 2) for x in hp], "foot_rest_z": round(ankle, 2),
                             "mount_foot0_z": [round(x, 2) for x in lows]}
    # (the horse: each gait's ground speed and the hooves' landings)
    H = rig_of(unreal.load_asset(HORSE_MESH))
    for k in ("walk", "run", "back", "swim"):
        c = clip(HORSE[k]); L = c.get_play_length(); rs = c.get_editor_property("rate_scale")
        fr = bones_at(c, H, HOOVES); n = len(fr) - 1; dt = L / max(n, 1)
        sp, lands = [], []
        for h in HOOVES:
            zs = [f[1][h][2] for f in fr]; ys = [f[1][h][1] for f in fr]; zmin = min(zs)
            st = [i for i in range(n + 1) if zs[i] < zmin + 2.0]
            sp += [-(ys[i + 1] - ys[i]) / dt for i in range(n) if i in st and (i + 1) in st]
            first = [i for i in st if (i - 1) % (n + 1) not in st]
            lands.append(round(first[0] / n, 3) if first else 0.0)
        sp.sort()
        med = sp[len(sp) // 2] if sp else 0.0
        J["horse"][k] = {"clip": HORSE[k], "length": round(L, 3), "rate_scale": round(rs, 3), "planted_cm_s_clip": round(med, 1),
                         "ground_cm_s": round(abs(med * rs), 1), "lands": lands}
    # (an idle that walks its root about would carry the horse off its place: only those that keep it)
    keep = []
    for n_ in IDLES:
        c = clip(n_); fr = bones_at(c, H, [H[0][0], "Root_M"], list(range(0, AL.get_num_frames(c) + 1, 4)))
        r0 = fr[0][1]["Root_M"]; drift = max(math.dist(f[1]["Root_M"][:2], r0[:2]) for f in fr)
        J["horse"].setdefault("idles", {})[n_] = round(drift, 1)
        if drift < 6.0: keep.append(n_)
    J["horse"]["idles_kept"] = keep
    # (the rider socket at rest, in the horse's component space)
    a = eas.spawn_actor_from_object(unreal.load_asset(HORSE_MESH), unreal.Vector(0, 0, -50000))
    t = a.get_editor_property("skeletal_mesh_component").get_socket_transform("RiderSocket", unreal.RelativeTransformSpace.RTS_COMPONENT)
    q = t.rotation
    J["rider_socket"] = {"loc": [round(t.translation.x, 3), round(t.translation.y, 3), round(t.translation.z, 3)], "quat": [q.x, q.y, q.z, q.w]}
    eas.destroy_actor(a)
    os.makedirs(SA, exist_ok=True)
    json.dump(J, open(JSON, "w", encoding="utf-8"), indent=1)
    REPORT.append("measure: " + ", ".join(f"{k} {v['ground_cm_s']} cm/s lands {v['lands']}" for k, v in J["horse"].items() if isinstance(v, dict) and "ground_cm_s" in v)
                  + f"; idles kept {keep}; seats " + ", ".join(f"{h} {v['seat_pelvis']}" for h, v in J["heroes"].items()))

# ---------------------------------------------------------------- level
if "level" in STEPS:
    J = json.load(open(JSON, encoding="utf-8"))
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."):
        les.load_level(MAP); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    d = g.get_editor_property("horse_def")
    hm = unreal.load_asset(HORSE_MESH)
    sets = {"mesh": hm, "mesh_b": hm, "saddle_mesh": unreal.load_asset(P + "/Meshes/SK_MedievalSaddle"), "mesh_yaw": -90.0,
            "coat_slot": 2, "hair_slot": 0,
            "coat_a": unreal.load_asset(P + "/Materials/MI_Horse_Brown02_Realistic"), "coat_b": unreal.load_asset(P + "/Materials/MI_Horse_Grey01_Realistic"),
            "hair_a": unreal.load_asset(P + "/Materials/Hair/MI_HorseHair_brown04"), "hair_b": unreal.load_asset(P + "/Materials/Hair/MI_HorseHair_White"),
            "idle": clip(HORSE["idle"]), "walk": clip(HORSE["walk"]), "run": clip(HORSE["run"]), "canter": None, "back": clip(HORSE["back"]),
            "stop": clip(HORSE["stop"]), "jump_start": clip(HORSE["jump_start"]), "jump_loop": clip(HORSE["jump_loop"]), "jump_land": clip(HORSE["jump_land"]),
            "rear": clip(HORSE["rear"]), "swim_idle": clip(HORSE["swim_idle"]), "swim": clip(HORSE["swim"]),
            "hits": [clip(n) for n in HITS], "idles": [clip(n) for n in J["horse"]["idles_kept"]],
            "walk_clip_speed": J["horse"]["walk"]["ground_cm_s"], "run_clip_speed": J["horse"]["run"]["ground_cm_s"],
            "back_clip_speed": J["horse"]["back"]["ground_cm_s"], "swim_clip_speed": 300.0,
            "walk_falls": J["horse"]["walk"]["lands"], "run_falls": J["horse"]["run"]["lands"], "hoof_bones": HOOVES,
            # (PR #93's review: the backing clip's own landings, measured above, for its hooves' sounds and dust)
            "back_falls": J["horse"]["back"]["lands"],
            # (the user's choice: a natural gallop of about 12 m/s (the clip's own pace 1.7 times); a brisk walk 1.2 times its)
            "top_walk": round(J["horse"]["walk"]["ground_cm_s"] * 1.2), "top_run": 1200.0, "top_back": 140.0, "top_swim": 300.0,
            "accel": 320.0, "decel": 500.0, "hard_stop": 1100.0, "turn_slow": 150.0, "turn_fast": 65.0, "gallop_edge": 360.0, "jump_z": 450.0,
            "rider_socket": "RiderSocket", "rider_frame_up": 20.0, "seat_pelvis": unreal.Vector(*J["pack_seat_pelvis"]),
            "swim_depth": 110.0, "swim_lift": 25.0,
            "dust_step": unreal.load_asset(P + "/VFX/NiagaraSystems/FXS_HorseFootstep_Dirt"), "dust_gallop": unreal.load_asset(P + "/VFX/NiagaraSystems/FXS_HorseCanterFootstep_Dirt"),
            "dust_stop": unreal.load_asset(P + "/VFX/NiagaraSystems/FXS_HorseDecelerate_Dirt"), "dust_scale": 1.0,
            "model_reins": True, "pack": True, "speed_mul": 1.0, "seat_ahead": 0.0, "seat_up": 0.0, "rider_lift": 0.0}
    for k, v in sets.items(): d.set_editor_property(k, v)
    rs = J["rider_socket"]
    d.set_editor_property("rider_socket_ref", unreal.Transform(unreal.Vector(*rs["loc"]), unreal.Quat(*rs["quat"]).rotator(), unreal.Vector(1, 1, 1)))
    g.set_editor_property("horse_def", d)
    # (each hero's clips and her offsets: her pelvis brought to the pack's rider's seat; at the mount's start her lowest foot on the
    # ground, which lies RiderFrameUp under the rider's frame. Her mesh's turn in her pawn: the pack's is -90 (its +Y her front))
    pawn_rot = {}
    for hd in g.get_editor_property("heroes"):
        cls = hd.get_editor_property("pawn_class")
        try: pawn_rot[str(hd.get_editor_property("name"))] = unreal.get_default_object(cls).get_editor_property("mesh").get_editor_property("relative_rotation").yaw if cls else -90.0
        except Exception: pawn_rot[str(hd.get_editor_property("name"))] = -90.0
    rc_map = {}
    seat_m = J["pack_seat_pelvis"]
    for hero, ch in HERO_RIG.items():
        r = unreal.RDRiderClips()
        for k, n in RIDER.items():
            a = unreal.load_asset(f"{ANIMS}/{ch}/{n}_{ch}")
            r.set_editor_property(k.replace("_l", "_l").replace("_r", "_r"), a)
        hj = J["heroes"].get(hero)
        if hj:
            # (the pack's seat in her mesh's axes: her mesh turned (yaw - (-90)) from the pack's rider's)
            yaw = math.radians(-(pawn_rot.get(hero, -90.0) + 90.0))
            mx, my, mz = seat_m
            mx, my = mx * math.cos(yaw) - my * math.sin(yaw), mx * math.sin(yaw) + my * math.cos(yaw)
            hx, hy, hz = hj["seat_pelvis"]
            seat = (mx - hx, my - hy, mz - hz)
            lows = hj["mount_foot0_z"] or [0.0]
            gz = -20.0 + hj["foot_rest_z"] - sum(lows) / len(lows)
            r.set_editor_property("seat_offset", unreal.Vector(*seat))
            r.set_editor_property("ground_offset", unreal.Vector(seat[0], seat[1], gz))
            REPORT.append(f"level {hero}: mesh yaw {pawn_rot.get(hero)}, seat offset ({seat[0]:.1f}, {seat[1]:.1f}, {seat[2]:.1f}), ground z {gz:.1f}")
        rc_map[hero] = r
    g.set_editor_property("rider_clips", rc_map)
    # (the horse's sounds: the pack's cues (each its own random pick of its files), heard through the game's own attenuation)
    S = g.get_editor_property("sounds")
    def sset(cues, vol, inner=200.0, fall=2500.0, pv=0.06):
        s = unreal.RDSoundSet()
        s.set_editor_property("sounds", [unreal.load_asset(f"{P}/SFX/{c}") for c in cues])
        s.set_editor_property("volume", vol); s.set_editor_property("pitch_variation", pv)
        s.set_editor_property("inner_radius", inner); s.set_editor_property("falloff_distance", fall)
        assert all(s.get_editor_property("sounds")), cues
        return s
    for k, v in {"Horse.Hoof.Grass": sset(["Cue_HorseFootstep_Grass"], 0.55), "Horse.Hoof.Dirt": sset(["Cue_HorseFootstep_Dirt"], 0.6),
                 "Horse.Hoof.Hard": sset(["Cue_HorseFootstep_Concrete"], 0.6), "Horse.Neigh": sset(["Cue_Horse_Neigh"], 0.8, 400.0, 4000.0),
                 "Horse.Snort": sset(["Cue_Horse_Grunt"], 0.6), "Horse.Mount": sset(["Cue_MountUP"], 0.7), "Horse.Dismount": sset(["Cue_Rider_Dismount"], 0.7),
                 "Horse.Jump": sset(["Cue_jump"], 0.7), "Horse.Swim": sset(["Cue_Swim"], 0.6), "Horse.Hit": sset(["Cue_Hit_React"], 0.7)}.items():
        S[k] = v
    g.set_editor_property("sounds", S)
    g.modify(); les.save_current_level()
    back = g.get_editor_property("horse_def")
    REPORT.append(f"level: pack {back.pack}, walk {back.walk_clip_speed} / run {back.run_clip_speed} cm/s, tops {back.top_walk} / {back.top_run}, "
                  f"falls {list(back.walk_falls)} / {list(back.run_falls)}, idles {len(back.idles)}, sounds {sorted(k for k in g.get_editor_property('sounds') if str(k).startswith('Horse.'))}")
    del g
print("HORSE15 " + " | ".join(REPORT))
import gc
gc.collect()
