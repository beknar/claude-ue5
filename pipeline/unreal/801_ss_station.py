"""starship_level (after 800): the space station, the clutter of the 5 km x 5 km x 5 km area and what the arena spawns
in play. Everything is a pack mesh placed by the middle of its bounds (tag ss_clutter, removed and rebuilt each run).
- Station "spindle" in the middle of the area, from Mega_City: two drum modules back to back as the hub, a landing
  deck and a tower cluster above and (upside down) below, six spokes to pylons (Red_Echo) with docking pads, antennas
  and hologram signs; parked ships (Spaceship_Kit's BP_ship_Flying, Mega_City cars), container stacks and a docked
  cargo ship (the Sci-Fi Flying Cargo Ship level blueprint).
- Clutter: big asteroids (too big to destroy) in five belts, a gate course from the start toward the station (six
  Mega_City tunnel rings, each pointing at the next: a bent pipe 59 m in radius to fly through. The pack's tunnel has
  a black disc closing one end, which the city hides its tunnel ends behind: the gates use a copy of the mesh,
  /Game/Starship/Meshes/SM_SS_Gate, in which that disc is invisible and has no collision), a jump gate (Red_Echo
  portal), relay satellites (Red_Echo antennas), a wreck field (Spaceship_Kit hulls, cargo ship modules).
- SS_Arena data: asteroid fields and a container field (destructible targets spawned in play), where nothing may be
  spawned, the drone types and the volumes they patrol.
The fighter (placed by 800) is moved onto the first gate's axis, facing it. Prints what it placed. Args: [seed]"""
import sys, math, random, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
V = unreal.Vector; Rot = unreal.Rotator; L = unreal.load_asset
w = ues.get_editor_world(); assert w.get_path_name().startswith("/Game/Starship/Maps/starship_level."), w.get_path_name()
TAG = "ss_clutter"; HALF = 250000.0
rnd = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 4107)
for a in eas.get_all_level_actors():
    if TAG in [str(t) for t in a.tags]: eas.destroy_actor(a)
arena = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.SSArena))
fighter = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.SSFighter))
START = V(-150000.0, -60000.0, 20000.0)             # (800's: the layout hangs on it; the fighter itself is moved to the gate course below)
MC = "/Game/Mega_City/Meshes/"; RE = "/Game/Red_Echo/Meshes/"; CS = "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/"; SK = "/Game/Spaceship_Kit/Meshes/"
N = {"station": 0, "asteroids": 0, "clutter": 0}
KEEP = []                                           # (centre, radius): nothing destructible is spawned here
def mesh(path):
    m = L(path); assert m, path; return m
def put(path, center, rot=None, scale=1.0, label=None, folder="Starship/Station", kind="station", shadow=True):
    """a static mesh actor whose bounds are centred on `center`"""
    rot = rot or Rot(); sc = scale if isinstance(scale, unreal.Vector) else V(scale, scale, scale)
    m = mesh(path); off = unreal.MathLibrary.transform_location(unreal.Transform(V(0, 0, 0), rot, sc), m.get_bounds().origin)
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, center - off, rot); a.tags = [TAG]
    c = a.static_mesh_component; c.set_static_mesh(m); a.set_actor_scale3d(sc)
    c.set_collision_profile_name("BlockAll"); c.set_cast_shadow(shadow); c.set_mobility(unreal.ComponentMobility.STATIC)
    if label: a.set_actor_label(label)
    a.set_folder_path(folder); N[kind] += 1
    return a
def size(path, scale=1.0):
    e = mesh(path).get_bounds().box_extent; return V(e.x * 2 * scale, e.y * 2 * scale, e.z * 2 * scale)
def ring(n, radius, z=0.0, phase=0.0):
    return [(V(math.cos(phase + 2 * math.pi * k / n) * radius, math.sin(phase + 2 * math.pi * k / n) * radius, z), math.degrees(phase + 2 * math.pi * k / n)) for k in range(n)]
FLIP = Rot(roll=180, pitch=0, yaw=0)

# ---------------------------------------------------------------- the station
DRUM = MC + "City_buildings/SM_large_building_module_01"; DECK = MC + "Landing_pad/SM_landing_pad"; TOWERS = MC + "City_buildings/SM_main_building"
dz = size(DRUM).z; kz = size(DECK).z; TS = 0.7; tz = size(TOWERS, TS).z
put(DRUM, V(0, 0, dz / 2), label="Station_Hub_Upper"); put(DRUM, V(0, 0, -dz / 2), FLIP, label="Station_Hub_Lower")
put(DECK, V(0, 0, dz + kz / 2), label="Station_Deck_Upper"); put(DECK, V(0, 0, -dz - kz / 2), FLIP, label="Station_Deck_Lower")
put(TOWERS, V(0, 0, dz + kz + tz / 2), scale=TS, label="Station_Towers_Upper"); put(TOWERS, V(0, 0, -dz - kz - tz / 2), FLIP, TS, "Station_Towers_Lower")
TOP = dz + kz + tz
put(MC + "Antennas/SM_antenna_03", V(2000, 1500, TOP + 9000), scale=6.0, label="Station_Mast_Upper")
put(MC + "Antennas/SM_antenna_03", V(-2000, 1500, -TOP - 9000), FLIP, 6.0, "Station_Mast_Lower")
SPOKE = MC + "City_details/SM_pipe_big"; PYLON = RE + "Ciruclar_module/SM_circular_module_large"; PAD = RE + "Landing_pad/SM_landing_pad"
hub_r = size(DRUM).x / 2
PADS = []
for k, (p, yaw) in enumerate(ring(6, 1.0, 0.0, math.radians(15))):
    d = V(p.x, p.y, 0)
    put(SPOKE, d * (hub_r - 500 + 13500), Rot(roll=0, pitch=0, yaw=yaw), V(6.0, 8.0, 8.0), f"Station_Spoke_{k}")
    put(PYLON, d * (hub_r + 29000), scale=3.0, label=f"Station_Pylon_{k}")
    pz = 9000.0 if k % 2 == 0 else -9000.0
    pad = d * (hub_r + 29000 + 11500) + V(0, 0, pz)
    put(PAD, pad, Rot(roll=0 if pz > 0 else 180, pitch=0, yaw=yaw), 4.0, f"Station_Pad_{k}")
    PADS.append((pad, yaw, 1.0 if pz > 0 else -1.0))
for k, (p, yaw) in enumerate(ring(3, hub_r + 9000, 0.0, math.radians(75))):
    put(MC + "SM_big_hologram", p + V(0, 0, 26000 if k % 2 == 0 else -24000), Rot(roll=0, pitch=0, yaw=yaw + 90), 2.2, f"Station_Hologram_{k}", shadow=False)
# work lights: the station is lit from close by on every side (no shadows)
def lamp(p, candelas, radius, color, label):
    a = eas.spawn_actor_from_class(unreal.PointLight, p, Rot()); a.tags = [TAG]; a.set_actor_label(label); a.set_folder_path("Starship/Station/Lights")
    c = a.point_light_component; c.set_mobility(unreal.ComponentMobility.STATIC if False else unreal.ComponentMobility.MOVABLE)
    c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS); c.set_editor_property("intensity", candelas); c.set_editor_property("attenuation_radius", radius)
    c.set_editor_property("light_color", color); c.set_editor_property("cast_shadows", False); c.set_editor_property("use_inverse_squared_falloff", True)
    return a
for k, (p, yaw) in enumerate(ring(6, hub_r + 16000, 0.0, math.radians(45))):
    lamp(p + V(0, 0, 14000 if k % 2 else -14000), 500000.0, 70000.0, unreal.Color(r=255, g=214, b=170, a=255), f"Station_Lamp_{k}")
for k, z in enumerate((dz + kz + 9000, -dz - kz - 9000)):
    for j, (p, yaw) in enumerate(ring(3, hub_r + 22000, z, math.radians(20 + 60 * k))):
        lamp(p, 700000.0, 90000.0, unreal.Color(r=190, g=215, b=255, a=255), f"Station_Tower_Lamp_{k}_{j}")
STATION_R = hub_r + 29000 + 11500 + 9000
KEEP.append((V(0, 0, 0), TOP + 14000))
print(f"station: hub radius {hub_r / 100:.0f} m, top at {TOP / 100:.0f} m, pads out to {STATION_R / 100:.0f} m")
# ---- on the pads: parked ships and container stacks
SHIP_BP = unreal.EditorAssetLibrary.load_blueprint_class("/Game/Spaceship_Kit/Blueprint/BP_ship_Flying")
CONT = [CS + f"Container/SM_container_{c}" for c in ("blue", "orange", "red", "white")]
CARS = [MC + f"Cars/SM_car_0{i}" for i in (1, 2, 3, 4)]
for k, (pad, yaw, up) in enumerate(PADS):
    top = pad + V(0, 0, up * 3400)
    if k in (0, 3):
        a = eas.spawn_actor_from_class(SHIP_BP, top + V(0, 0, up * 1200), Rot(roll=0 if up > 0 else 180, pitch=0, yaw=yaw + 90)); a.tags = [TAG]
        a.set_actor_label(f"Station_Parked_Ship_{k}"); a.set_folder_path("Starship/Station"); N["clutter"] += 1
    elif k in (1, 4):
        for i in range(10):
            col, row, lay = i % 3, (i // 3) % 2, i // 6
            put(CONT[rnd.randrange(4)], top + V((col - 1) * 520, (row - 0.5) * 1900, up * (230 + lay * 440)), Rot(roll=0, pitch=0, yaw=0), 1.0, f"Station_Container_{k}_{i}", kind="clutter")
    else:
        for i in range(3):
            put(CARS[rnd.randrange(4)], top + V((i - 1) * 2200, rnd.uniform(-900, 900), up * 320), Rot(roll=0 if up > 0 else 180, pitch=0, yaw=yaw + rnd.choice((0, 180))), 1.0, f"Station_Car_{k}_{i}", kind="clutter")
# ---- the cargo ship standing off the station
CARGO_AT = V(STATION_R + 26000, -52000, 6000)
cargo = eas.spawn_actor_from_class(unreal.EditorAssetLibrary.load_blueprint_class("/Game/Sci-Fi_Flying_Cargo_Ship/Blueprint/BPP_L_cargo_02"), CARGO_AT, Rot(roll=0, pitch=0, yaw=35))
cargo.tags = [TAG]; cargo.set_actor_label("Cargo_Ship"); cargo.set_folder_path("Starship/Clutter"); N["clutter"] += 1
co = CARGO_AT                                      # (a level blueprint's bounds are not reliable right after it is spawned)
KEEP.append((co, 16000))

# ---------------------------------------------------------------- clutter
def inside(p, pad): return max(abs(p.x), abs(p.y), abs(p.z)) < HALF - pad
def clear(p, r): return all((p - c).length() > r + kr for c, kr in KEEP)
# ring gates: a course from the start toward the station
EAL = unreal.EditorAssetLibrary; MEL = unreal.MaterialEditingLibrary
def clear_material():
    """a material that draws nothing (masked, mask 0)"""
    path = "/Game/Starship/Materials/M_SS_Clear"
    if EAL.does_asset_exist(path): return L(path)
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_SS_Clear", "/Game/Starship/Materials", unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -300, 0); c.set_editor_property("r", 0.0)
    MEL.connect_material_property(c, "", unreal.MaterialProperty.MP_OPACITY_MASK)
    MEL.recompile_material(m); EAL.save_loaded_asset(m, False)
    return m
def gate_mesh():
    """the pack's tunnel without the black disc that closes one of its ends"""
    path = "/Game/Starship/Meshes/SM_SS_Gate"
    if not EAL.does_asset_exist(path): assert EAL.duplicate_asset(MC + "SM_tunnel", path), path
    m = L(path); sms = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    k = next(i for i, s in enumerate(m.static_materials) if str(s.material_slot_name) == "Black")
    m.modify(); m.set_material(k, clear_material())
    for lod in range(m.get_num_lods()):
        if k < m.get_num_sections(lod) and sms.is_section_collision_enabled(m, lod, k): sms.enable_section_collision(m, False, lod, k)
    EAL.save_loaded_asset(m, False)
    return path
GATE = gate_mesh()
to = (V(0, 0, 0) - START).normal(); side = to.cross(V(0, 0, 1)).normal(); up = side.cross(to).normal()
GATES = []
for i in range(6):
    t = 22000.0 + i * 13000.0
    p = START + to * t + side * (math.sin(i * 1.3) * 7000.0) + up * (math.cos(i * 0.9) * 5000.0 + 2000.0)
    nxt = START + to * (t + 13000.0) + side * (math.sin((i + 1) * 1.3) * 7000.0) + up * (math.cos((i + 1) * 0.9) * 5000.0 + 2000.0)
    GATES.append((p, (nxt - p).normal()))
GATE_S = 5.0
for i, (p, d) in enumerate(GATES):
    # (the tunnel is a ring around its Y axis: its opening faces along Y)
    put(GATE, p, unreal.MathLibrary.make_rot_from_y(d), GATE_S, f"Gate_{i}", "Starship/Clutter", "clutter")
# the fighter starts on the first gate's axis, 228 m before its middle and facing it (800 puts it at START, from where
# flying straight on meets the first gate's rim)
LAUNCH = GATES[0][0] - GATES[0][1] * 22800.0
fighter.set_actor_location_and_rotation(LAUNCH, unreal.MathLibrary.make_rot_from_x(GATES[0][1]), False, False)
# jump gate and relay satellites
JUMP = V(165000, 150000, 60000)
put(RE + "Portal/SM_vertical_portal", JUMP, Rot(roll=0, pitch=0, yaw=225), 14.0, "Jump_Gate", "Starship/Clutter", "clutter"); KEEP.append((JUMP, 22000))
for i in range(7):
    while True:
        p = V(rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1)) * (HALF - 30000)
        if clear(p, 6000) and (p - START).length() > 30000: break
    r = Rot(roll=rnd.uniform(-180, 180), pitch=rnd.uniform(-60, 60), yaw=rnd.uniform(-180, 180))
    put(RE + "Antenna/SM_big_antenna", p, r, 4.0, f"Relay_{i}", "Starship/Clutter", "clutter"); KEEP.append((p, 6000))
# wreck field: hulls and cargo modules adrift
WRECK = V(-120000, 150000, -70000)
for i, (path, s) in enumerate(((SK + "Ship_parts/SM_space_ship_body", 2.4), (CS + "Cargo_modules/SM_cargo_body_01", 1.0), (CS + "Cargo_modules/SM_top_cargo", 1.6), (CS + "Hangar/SM_hangar", 1.2),
                              (SK + "Ship_parts/SM_space_ship_body", 1.6), (CS + "Cargo/SM_cargo_02", 1.0), (SK + "Ship_parts/SM_reactor_left", 3.0), (CS + "Reactor/SM_reactor", 1.0), (MC + "Ship/SM_ship", 2.0))):
    p = WRECK + V(rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.6, 0.6)) * 32000.0
    put(path, p, Rot(roll=rnd.uniform(-180, 180), pitch=rnd.uniform(-80, 80), yaw=rnd.uniform(-180, 180)), s, f"Wreck_{i}", "Starship/Clutter", "clutter")
    e = size(path, s); KEEP.append((p, max(e.x, e.y, e.z) * 0.6))
# big asteroids (too big to destroy): three belts of rocks from the packs, 35 m to 300 m across
ROCKS = [SK + "Rock/SM_rock_01", "/Game/SciFi_Cliff/Meshes/Rocks/SM_rock_01", "/Game/SciFi_Cliff/Meshes/Rocks/SM_rock_02", RE + "Rock/SM_rock_01"]
BELTS = [(V(20000, 165000, 20000), 75000, 30), (V(140000, -130000, -60000), 65000, 26), (V(-170000, 40000, -110000), 60000, 22), (V(50000, 30000, 185000), 55000, 16), (V(-60000, -170000, 120000), 55000, 16)]
BIG = []
for bi, (c, rad, n) in enumerate(BELTS):
    made = tries = 0
    while made < n and tries < n * 30:
        tries += 1
        d = V(rnd.gauss(0, 1), rnd.gauss(0, 1), rnd.gauss(0, 0.55)); p = c + d * (rad * 0.5)
        want = rnd.choice((1800, 2500, 3500, 5000, 7000, 10000, 15000)) * rnd.uniform(0.8, 1.2)            # radius, cm
        if not inside(p, want + 2000) or not clear(p, want) or any((p - q).length() < want + qr + 1500 for q, qr in BIG) or (p - START).length() < want + 25000: continue
        if any(((p - g) - d2 * (p - g).dot(d2)).length() < want + 9000 and abs((p - g).dot(d2)) < 20000 for g, d2 in GATES): continue          # (keep the gate course open)
        path = rnd.choice(ROCKS); m = mesh(path); s = want / m.get_bounds().sphere_radius
        put(path, p, Rot(roll=rnd.uniform(-180, 180), pitch=rnd.uniform(-90, 90), yaw=rnd.uniform(-180, 180)), V(s * rnd.uniform(0.8, 1.2), s * rnd.uniform(0.8, 1.2), s * rnd.uniform(0.8, 1.2)),
            f"Asteroid_{bi}_{made}", "Starship/Asteroids", "asteroids")
        BIG.append((p, want)); made += 1
KEEP += [(p, r * 1.05) for p, r in BIG] + [(START, 26000), (LAUNCH, 20000)]
# (nothing adrift inside the gate course: its tunnels, the joints between them and the ways in and out)
for i, (p, d) in enumerate(GATES):
    KEEP += [(p + d * s, 7800) for s in (-6000.0, 0.0, 6000.0)]
    if i + 1 < len(GATES): KEEP.append(((p + GATES[i + 1][0]) * 0.5, 7200))
KEEP += [(GATES[0][0] - GATES[0][1] * 13000.0, 6500), (GATES[-1][0] + GATES[-1][1] * 13000.0, 6500)]

# ---------------------------------------------------------------- what the arena spawns in play
def sphere(c, r):
    s = unreal.SSSphere(); s.set_editor_property("center", c); s.set_editor_property("radius", float(r)); return s
def field(c, r, n, lo, hi, kind=unreal.SSTargetKind.ASTEROID):
    f = unreal.SSField()
    for k, v in (("center", c), ("radius", float(r)), ("count", n), ("min_size", float(lo)), ("max_size", float(hi)), ("kind", kind)): f.set_editor_property(k, v)
    return f
FIELDS = [field(START + to * 52000 + side * 24000, 22000, 60, 250, 1400)]                       # something to shoot at right away
FIELDS += [field(c, rad * 1.05, n * 4, 250, 2200) for c, rad, n in BELTS]
FIELDS.append(field(V(0, -150000, -150000), 55000, 70, 250, 2000))
FIELDS.append(field(co + V(0, -19000, 9000), 13000, 36, 700, 950, unreal.SSTargetKind.CONTAINER))  # cargo adrift by the cargo ship
def drone(name, path, rot, scale, health, speed, points, trail):
    d = unreal.SSDroneDef()
    for k, v in (("name", name), ("mesh", mesh(path)), ("mesh_rotation", rot), ("scale", scale), ("health", health), ("speed", speed), ("points", points), ("trail_offset", trail)): d.set_editor_property(k, v)
    return d
DRONES = [drone("Raider", MC + "Ship/SM_ship", Rot(roll=0, pitch=0, yaw=-90), 0.9, 90.0, 11000.0, 150, V(-1000, 0, 0)),
          drone("Dart", MC + "Cars/SM_car_04", Rot(roll=0, pitch=0, yaw=0), 0.8, 60.0, 14500.0, 100, V(-700, 0, 0)),
          drone("Hauler", MC + "Cars/SM_car_02", Rot(roll=0, pitch=0, yaw=0), 1.2, 150.0, 7500.0, 80, V(-800, 0, 0))]
PATROLS = [sphere(V(0, 0, 0), 150000), sphere(V(0, 0, 0), 190000), sphere(START + to * 70000, 45000), sphere(BELTS[0][0], 90000), sphere(BELTS[1][0], 80000), sphere(co, 60000)]
for k, v in (("asteroid_meshes", [mesh(p) for p in ROCKS]), ("container_meshes", [mesh(p) for p in CONT]), ("fields", FIELDS), ("keep_out", [sphere(c, r) for c, r in KEEP]),
             ("drone_types", DRONES), ("patrols", PATROLS), ("drone_count", 14), ("drone_respawn_delay", 10.0)):
    arena.set_editor_property(k, v)
print(f"placed: {N['station']} station pieces, {N['asteroids']} big asteroids, {N['clutter']} clutter actors | arena: {len(FIELDS)} fields ({sum(f.count for f in FIELDS)} targets wanted), "
      f"{len(KEEP)} keep-out spheres, {len(DRONES)} drone types x {arena.get_editor_property('drone_count')}, {len(PATROLS)} patrol volumes")
les.save_current_level()
print("saved")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
