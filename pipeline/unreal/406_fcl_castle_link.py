"""The castle's east terrace (SM_Platform, z 7649) has no walkable way to the island bridge: the pack's own east stair ends in a
ditch at the outer wall (SM_WallUvd), and the bridge deck (SM_BridgeUvd, ~6200 at the castle end of its south-east branch) runs
outside that wall. Build a stone link along y = 118450: a short ramp over the terrace parapet (7811), a level slab across the
ditch and over the wall top (~7700), then the pack's long stair (SM_Stairslong, scaled) down onto the bridge deck, with two
columns under the flying stair. Actors tagged 'fcl_link'."""
import math, unreal
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert "fantasy_castle_level." in w.get_path_name(), w.get_path_name()
# spawn into the persistent level, never into the streamed village (fcl_lake_village is rebuilt from the pack)
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_current_level_by_name("fantasy_castle_level")
TAG = unreal.Name("fcl_link"); Y = 118450.0; W = 600.0
for a in eas.get_all_level_actors():
    if TAG in a.tags: eas.destroy_actor(a)
F = "/Game/FantasyCastle/Mesh/"
def spawn(mesh, loc, rot, scale, label):
    a = eas.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
    a.static_mesh_component.set_static_mesh(unreal.load_asset(F + mesh)); a.set_actor_scale3d(scale)
    a.set_actor_label(label); a.tags = [TAG]; a.set_folder_path("FCL/CastleLink"); return a
def ztop(a, x, y):
    r = a.static_mesh_component.line_trace_component(V(x, y, 20000), V(x, y, 0), True, False, False)
    return r[0].z if r else None
SLAB = unreal.load_asset(F + "SM_FloorType1"); sb = SLAB.get_bounding_box()      # 2660 x 3051 x 48, top at +36
def slab(x0, z0, x1, z1, label):
    L = math.hypot(x1 - x0, z1 - z0); pitch = math.degrees(math.atan2(z1 - z0, x1 - x0))
    a = spawn("SM_FloorType1", V((x0 + x1) / 2, Y, 0), unreal.Rotator(roll=0, pitch=pitch, yaw=0), V(L / (sb.max.x - sb.min.x), W / (sb.max.y - sb.min.y), 1.0), label)
    zt = ztop(a, (x0 + x1) / 2, Y); a.set_actor_location(V((x0 + x1) / 2, Y, (z0 + z1) / 2 - (zt - a.get_actor_location().z)), False, True)
    return a
TOP = 7840.0
slab(6150, 7652, 6560, TOP, "FCL_Link_Ramp")
slab(6540, TOP, 8380, TOP, "FCL_Link_Slab")
# the long stair: 2400 run x 600 wide x 1511 rise in the mesh; fit it from the slab end (8380, TOP) down to the deck (10650, deck z)
deck_h = unreal.SystemLibrary.line_trace_single(w, V(10750, Y, 20000), V(10750, Y, 0), unreal.TraceTypeQuery.ECC_VISIBILITY, True, [], unreal.DrawDebugTrace.NONE, True).to_tuple()[4].z
x0, x1 = 8380.0, 10650.0
st = spawn("SM_Stairslong", V((x0 + x1) / 2, Y, (TOP + deck_h) / 2), unreal.Rotator(roll=0, pitch=0, yaw=0), V((x1 - x0) / 2400.0, 1.0, (TOP - deck_h) / 1511.0), "FCL_Link_Stair")
za, zb = ztop(st, x0 + 60, Y), ztop(st, x1 - 60, Y)
if za is not None and zb is not None and za < zb:                           # mesh rises toward +X: turn it round
    st.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=180), False); za, zb = ztop(st, x0 + 60, Y), ztop(st, x1 - 60, Y)
st.set_actor_location(st.get_actor_location() + V(0, 0, TOP - za), False, True)
za, zb = ztop(st, x0 + 60, Y), ztop(st, x1 - 60, Y)
for k, xc in enumerate((9000.0, 9900.0)):                                     # columns from the lake to the stair's underside
    zs = ztop(st, xc, Y)
    if zs is None: continue
    h = (zs - 300) - 3390
    spawn("SM_Collum", V(xc, Y, 3390 + h / 2), unreal.Rotator(roll=0, pitch=0, yaw=0), V(1.6, 1.6, h / 796.0), f"FCL_Link_Column{k}")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print(f"link: ramp 7652->{TOP:.0f}, slab {TOP:.0f} over the wall, stair top {za:.0f} -> bottom {zb:.0f} (deck {deck_h:.0f})")
