"""sf-city-level road: a bridge road from the city's south dock platform (deck z 32, open west end at y -58200) straight west
across the void to the Monolith Megastructure, down the low channel in its +Y landscape edge onto the entrance plaza.
- deck: the Monolith pack's SM_bridge_spline (539.5 long, walkable top at the pivot height, 7.6 m between 88 cm railings),
  laid end to end along x = XC heading -Y, each piece pitched to the next sample height. Over the landscape the deck top
  rides 4 cm above the highest terrain under its width; across the void it climbs linearly between the two shores.
- two support pylons (SM_large_module_01) under the void span, city street lamps (SM_street_lamp_02) along the railings
- invisible walls (block Pawn only; visibility / camera ignore) outside both railings over the void span and 20 m beyond:
  the railings are lower than her jump.
Writes SourceArt/sf_city/route.json (road points). Actors tagged 'sfc_road' in the persistent level."""
import json, math, os, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); V = unreal.Vector
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); w = ues.get_editor_world()
assert w.get_path_name().startswith("/Game/SFCityLevel/Maps/sf-city-level."), w.get_path_name()
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_current_level_by_name("sf-city-level")
TAG = unreal.Name("sfc_road"); SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\sf_city"; os.makedirs(SA, exist_ok=True)
for a in eas.get_all_level_actors():
    if TAG in a.tags: eas.destroy_actor(a)
XC, Y0, Y1 = -15000.0, -58100.0, -87600.0                 # centre line x, start (1 m onto the dock: its edge is y -58200), end (on the plaza)
DECK = unreal.load_asset("/Game/Monolith_megastructure/Meshes/Bridge/SM_bridge_spline"); DL = 539.469
LAMP = unreal.load_asset("/Game/Mega_City/Meshes/Street_lights/SM_street_lamp_02")
PYLON = unreal.load_asset("/Game/Monolith_megastructure/Meshes/Modules/SM_large_module_01")
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
def ground(x, y):
    """highest surface under the deck width at (x, y) between z 3000 and -1500 (dock / landscape), else None (void)"""
    zs = []
    for dx in (-400.0, -200.0, 0.0, 200.0, 400.0):
        r = unreal.SystemLibrary.line_trace_single(w, V(x + dx, y, 3000), V(x + dx, y, -1500), unreal.TraceTypeQuery.ECC_VISIBILITY, False, [], unreal.DrawDebugTrace.NONE, True)
        if r: zs.append(r.to_tuple()[4].z)
    return max(zs) if zs else None
n = int(round(abs(Y1 - Y0) / DL)); seg = abs(Y1 - Y0) / n
ys = [Y0 - k * seg for k in range(n + 1)]
g = [ground(XC, y) for y in ys]
top = [None if z is None else z + 4.0 for z in g]
solid = [k for k, z in enumerate(top) if z is not None]
assert solid and solid[0] == 0 and solid[-1] == n, f"road ends must be on solid ground: {top[0]} {top[-1]}"
for k in range(n + 1):                                        # void span: straight line between the shores
    if top[k] is None:
        a = max(i for i in solid if i < k); b = min(i for i in solid if i > k)
        top[k] = top[a] + (top[b] - top[a]) * (k - a) / (b - a)
void = [k for k in range(n + 1) if g[k] is None]
print(f"{n} deck pieces of {seg:.1f} cm | void span pieces {void[0]}..{void[-1]} (y {ys[void[0]]:.0f}..{ys[void[-1]]:.0f}) | top z {top[0]:.0f} -> {top[void[0]]:.0f}..{top[void[-1]]:.0f} -> {top[-1]:.0f}")
def fin(a, label, folder="SFC/Road"):
    a.tags = [TAG]; a.set_actor_label(label); a.set_folder_path(folder); return a
for k in range(n):                                            # deck pieces: mesh +X along -Y, mesh y [-840, 0] -> world x [XC-420, XC+420]
    p0, p1 = V(XC, ys[k], top[k]), V(XC, ys[k + 1], top[k + 1])
    pitch = math.degrees(math.atan2(top[k + 1] - top[k], seg))
    rot = unreal.Rotator(roll=0, pitch=pitch, yaw=-90.0)
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, p0 + V(420, 0, 0), rot)
    a.static_mesh_component.set_static_mesh(DECK); a.set_actor_scale3d(V(math.hypot(seg, top[k + 1] - top[k]) / DL * 1.004, 1, 1))
    fin(a, f"RoadDeck_{k:02d}")
kv0, kv1 = void[0] - 1, void[-1] + 1                          # last solid piece before / first after the void
for f in (1 / 3, 2 / 3):                                      # pylons under the void span, tops just under the deck slab (-212)
    k = int(round(kv0 + (kv1 - kv0) * f)); zt = top[k] - 215.0
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, V(XC, ys[k], zt - 11771.0 * 0.9), unreal.Rotator())
    a.static_mesh_component.set_static_mesh(PYLON); a.set_actor_scale3d(V(0.55, 0.5, 0.9)); fin(a, f"RoadPylon_{k}")
for k in range(2, n - 1, 5):                                  # lamps every ~27 m, alternating sides, just inside the railings
    side = 1 if (k // 5) % 2 == 0 else -1
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, V(XC + side * 330, ys[k], top[k]), unreal.Rotator(roll=0, pitch=0, yaw=90 if side > 0 else -90))
    a.static_mesh_component.set_static_mesh(LAMP); fin(a, f"RoadLamp_{k}")
    l = eas.spawn_actor_from_class(unreal.PointLight, V(XC + side * 250, ys[k], top[k] + 560), unreal.Rotator())
    lc = l.get_component_by_class(unreal.PointLightComponent); lc.set_editor_property("intensity", 2500.0); lc.set_editor_property("attenuation_radius", 1400.0)
    lc.set_editor_property("light_color", unreal.Color(r=255, g=214, b=170, a=255)); lc.set_editor_property("cast_shadows", False); fin(l, f"RoadLampLight_{k}")
# invisible walls outside the railings: void span plus 20 m (~4 pieces) on the landscape side, 1 piece onto the dock side
def wall(p0, p1, z0, z1, label, th=20.0):
    d = p1 - p0; L = math.hypot(d.x, d.y); yaw = math.degrees(math.atan2(d.y, d.x))
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, V((p0.x + p1.x) / 2, (p0.y + p1.y) / 2, (z0 + z1) / 2), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    a.static_mesh_component.set_static_mesh(CUBE); a.set_actor_scale3d(V(L / 100.0, th / 100.0, (z1 - z0) / 100.0))
    c = a.static_mesh_component; c.set_collision_profile_name("InvisibleWall")
    for ch in (unreal.CollisionChannel.ECC_VISIBILITY, unreal.CollisionChannel.ECC_CAMERA): c.set_collision_response_to_channel(ch, unreal.CollisionResponseType.ECR_IGNORE)
    c.set_editor_property("hidden_in_game", True); c.set_editor_property("cast_shadow", False); a.set_actor_hidden_in_game(True)
    return fin(a, label, "SFC/Safety")
ka, kb = max(0, kv0 - 1), min(n, kv1 + 4)
for side in (-1, 1):
    x = XC + side * 432.0
    for k in range(ka, kb):                                   # one wall per deck piece (follows the slope), 10 cm overlap
        wall(V(x, ys[k] + 5, 0), V(x, ys[k + 1] - 5, 0), min(top[k], top[k + 1]) - 150.0, max(top[k], top[k + 1]) + 450.0, f"RoadWall_{'L' if side < 0 else 'R'}{k:02d}")
json.dump({"centre_x": XC, "points": [[XC, y, z] for y, z in zip(ys, top)], "void": [ys[void[0]], ys[void[-1]]],
           "walls": [ys[ka], ys[kb]]}, open(SA + r"\route.json", "w"), indent=1)
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True); print("saved")
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
