"""fantasy_castle_level: Lake Village interiors. The village houses are hollow (two-sided modular walls) but empty and shut by
static door meshes. For each house (one per door from 420's village_rooms.json):
  - room: flood fill on a 25 cm grid in the door frame (cells with ground ~ at the door's floor, a roof overhead, and no wall between
    neighbours at 1.0 / 1.9 m), largest inscribed rectangle -> room box
  - the static door is hidden (no collision) and replaced by a BP_Door with the re-pivoted leaf (414), swinging inward (F)
  - plank floor, capped-exposure post-process volume, lamps, and furniture by purpose:
      tavern (largest room), fisherman's house, farmhouse, weaver's cottage, smithy, barn (double-door buildings), storehouse
Actors spawn in the persistent level tagged 'fcl_int_village'; nothing in fcl_lake_village is deleted (doors are only hidden).
Frame: origin = door centre at floor level, +Y into the house, +X along the door wall (interior_lib.door_frame)."""
import json, math, random, sys, unreal
sys.path.insert(0, r"E:\code\claude-ue5\pipeline\unreal")
import importlib, interior_lib as IL; importlib.reload(IL)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); V = unreal.Vector
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
assert "fantasy_castle_level." in w.get_path_name(), w.get_path_name()
assert unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).set_current_level_by_name("fantasy_castle_level")
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\fantasy_castle"; TAG = "fcl_int_village"
ROOMS = json.load(open(SA + r"\village_rooms.json"))
MAT = lambda n: f"/Game/FantasyCastleLevel/Materials/{n}"; LEAF = lambda m: f"/Game/FantasyCastleLevel/Meshes/{m}_Leaf"
LAKE = IL.LAKE; PACK = IL.PACK
print("cleared", IL.clear(TAG))
ACT = {a.get_actor_label(): a for a in eas.get_all_level_actors() if "fcl_lake_village" in a.get_level().get_path_name()}
def hide(a, on=True):                                    # reversible: hidden in game + editor, no collision (saved component settings)
    a.set_actor_hidden_in_game(on); a.set_is_temporarily_hidden_in_editor(on); a.set_actor_enable_collision(not on)
    a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION if on else unreal.CollisionEnabled.QUERY_AND_PHYSICS)
for a in ACT.values():                                   # un-hide what a previous run hid (doors + doorway blocker planes; rebuilt below)
    if isinstance(a, unreal.StaticMeshActor) and unreal.Name("fcl_hidden") in a.tags: hide(a, False); a.tags = [t for t in a.tags if str(t) != "fcl_hidden"]
def tr(a, b, ignore):
    r = unreal.SystemLibrary.line_trace_single(w, a, b, unreal.TraceTypeQuery.ECC_VISIBILITY, True, ignore, unreal.DrawDebugTrace.NONE, True)
    t = r.to_tuple() if r else None
    return (t[4], t[9]) if t and (t[0] or t[1]) else (None, None)
MAXR = 1400.0                                             # a village room is at most ~14 m across
def find_room(fr, floor_hint, ignore):
    """free rectangle in front of the door, measured wall to wall with horizontal rays at 40 cm (below the window sills) and 1.5 m.
    Every ray must hit a wall within MAXR (else: not enclosed -> None); the ground must stay near the door's floor."""
    W = lambda x, y, z: fr.transform_location(V(x, y, z))
    def dist(x, y, dx, dy):
        best = MAXR
        for z in (40, 150):
            h, _ = tr(W(x, y, z), W(x + dx * MAXR, y + dy * MAXR, z), ignore)
            best = min(best, (fr.inverse_transform_location(h) - V(x, y, z)).length() if h is not None else MAXR)
        return best
    g, _ = tr(W(0, 90, 160), W(0, 90, -120), ignore)
    assert g is not None and -60 < fr.inverse_transform_location(g).z < 90, "no floor just inside"
    D = min(dist(x, 30, 0, 1) for x in (-40, 0, 40)) + 30
    if D >= MAXR - 1 or D < 220: return None
    left = right = MAXR
    for y in [60 + k * 50 for k in range(int((D - 100) // 50) + 1)]:
        left = min(left, dist(0, y, 1, 0)); right = min(right, dist(0, y, -1, 0))
    if left >= MAXR - 1 or right >= MAXR - 1: return None
    x0, x1, y0, y1 = -right + 15, left - 15, 15.0, D - 15
    for x in (x0 + 30, (x0 + x1) / 2, x1 - 30):                         # the floor must be continuous across the room
        for y in (y0 + 30, (y0 + y1) / 2, y1 - 30):
            h, _ = tr(W(x, y, 160), W(x, y, -150), ignore)
            if h is None or not (-60 < fr.inverse_transform_location(h).z < 90): return None
            c, _ = tr(W(x, y, 2500), W(x, y, 100), ignore)                 # roofed: from above, something covers the room
            if c is None or fr.inverse_transform_location(c).z < 180: return None
    return (x0, x1, y0, y1, 0)
rng = random.Random(11)
found = []
for rm in ROOMS:
    d = ACT.get(rm["door"])
    if d is None: continue
    best = None                                       # 420's inward guess can point at a porch: try both sides, keep the enclosed room
    for sgn in (1, -1):
        inward = (rm["inward"][0] * sgn, rm["inward"][1] * sgn)
        fr_ = IL.door_frame(unreal.Transform(), (d.get_actor_location().x, d.get_actor_location().y), rm["floor"], inward)
        try: b_ = find_room(fr_, rm["floor"], [d])
        except AssertionError: b_ = None
        if b_ and (best is None or (b_[1] - b_[0]) * (b_[3] - b_[2]) > (best[1][1] - best[1][0]) * (best[1][3] - best[1][2])): best = (fr_, b_, inward)
    if not best: print(rm["door"], "skip: no enclosed room on either side"); continue
    fr, box, inw = best; rm = dict(rm, inward=list(inw))
    x0, x1, y0, y1, n = box; area = (x1 - x0) * (y1 - y0) / 1e4
    print(f"{rm['door']} {rm['door_mesh']} room x[{x0:.0f},{x1:.0f}] y[{y0:.0f},{y1:.0f}] {area:.1f} m2 (cells {n})")
    if area >= 9.0 and (x1 - x0) >= 260 and (y1 - y0) >= 260: found.append((area, rm, d, fr, (x0, x1, y0, y1)))
# purposes: double-door buildings -> barn / storehouse, the largest house -> tavern, the rest by size
found.sort(key=lambda f: -f[0])
uniq = []                                            # two doors of one building -> one room
for f in found:
    x0, x1, y0, y1 = f[4]; c = f[3].transform_location(V((x0 + x1) / 2, (y0 + y1) / 2, 0))
    if all((c - u[0]).length() > 300 for u in uniq): uniq.append((c, f))
found = [u[1] for u in uniq]
houses = [f for f in found if f[1]["door_mesh"] != "SM_M_Door02"]; barns = [f for f in found if f[1]["door_mesh"] == "SM_M_Door02"]
plan = []
for k, f in enumerate(houses[:4]): plan.append((["fisher", "farmhouse", "smithy", "weaver"][k], f))
for k, f in enumerate(barns[:1]): plan.append((["tavern"][k], f))     # (the small shed SM_M_Door02_014 has a rising rock-slab floor: left shut)     # the big double-door hall (four doors) is the village inn
def door_swap(r, d, rm, x0, x1):
    """hide the static door; BP_Door with the matching leaf at the static door's hinge, swinging into the room"""
    sm = d.static_mesh_component.static_mesh; b = sm.get_bounding_box()
    dtr = d.get_actor_transform(); hinge_w = dtr.transform_location(V(b.min.x, (b.min.y + b.max.y) / 2, b.min.z))
    far_w = dtr.transform_location(V(b.max.x, (b.min.y + b.max.y) / 2, b.min.z))
    h_l = r.tr.inverse_transform_location(hinge_w); f_l = r.tr.inverse_transform_location(far_w)
    xh = min(h_l.x, f_l.x); width = abs(f_l.x - h_l.x)                 # leaf along +X in the frame from the left end
    hide(d); d.tags = list(d.tags) + [unreal.Name("fcl_hidden")]
    # the pack backs its (fake) doors with flat blocker planes (SM_M_Wall10 / Cube / Plane): hide any in the doorway
    xm = (h_l.x + f_l.x) / 2
    for lab, a in list(ACT.items()):
        if a is d or not isinstance(a, unreal.StaticMeshActor) or not a.static_mesh_component.static_mesh: continue
        if a.static_mesh_component.static_mesh.get_name() not in ("SM_M_Wall10", "Cube", "Plane", "SM_FarmHouseWall01"): continue
        hit = r.tr.inverse_transform_location(a.get_actor_bounds(False)[0]); e = a.get_actor_bounds(False)[1]
        if abs(hit.x - xm) < width / 2 + 100 and -80 < hit.y < 150 and hit.z < 300:
            o, ex = a.get_actor_bounds(False)
            box_ok = all(abs(r.tr.inverse_transform_location(o + V(sx * ex.x, sy * ex.y, 0)).y) < 260 for sx in (-1, 1) for sy in (-1, 1))   # (axis-aligned bounds of rotated planes are fat)
            if box_ok: print("  removed doorway blocker", lab); ACT.pop(lab); eas.destroy_actor(a)   # black fake-interior boxes; the sub-level is regenerated by 400/401
    return r.door(LEAF(sm.get_name()), xh, (h_l.y + f_l.y) / 2, h_l.z, width=width, height=(b.max.z - b.min.z), label="Door_" + d.get_actor_label())
for purpose, (area, rm, d, fr, (x0, x1, y0, y1)) in plan:
    r = IL.Room(fr, 0.0, TAG, f"FCL/Interiors/Village_{purpose}")
    W, Dp = x1 - x0, y1 - y0; cx = (x0 + x1) / 2
    door_swap(r, d, rm, x0, x1)
    # floor: planks a little above the highest ground in the room
    hz = max((tr(fr.transform_location(V(x, y, 150)), fr.transform_location(V(x, y, -100)), [d])[0] or fr.transform_location(V(0, 0, 0))).z
             for x in (x0 + 20, cx, x1 - 20) for y in (y0 + 20, (y0 + y1) / 2, y1 - 20))
    top = fr.inverse_transform_location(V(0, 0, hz)).z + 3
    r.z = top
    r.box(cx, (y0 + y1) / 2, top - 30, W + 24, Dp + 24, 30, label="Floor", mat=MAT("MI_FCL_WoodFloor"))
    # threshold steps when the outside ground is well below the new floor (double-door halls sit on a plinth)
    xm = r.tr.inverse_transform_location(d.get_actor_location()).x
    go = tr(fr.transform_location(V(xm, -90, 200)), fr.transform_location(V(xm, -90, -200)), [d])[0]
    if go is not None:
        drop = top - fr.inverse_transform_location(go).z
        n = int(math.ceil(drop / 22.0)) if drop > 25 else 0
        for k in range(n):                                                   # outward from the door line, each 22 cm lower
            h = top - (k + 1) * drop / (n + 1)
            r.box(xm, -18 - k * 30, h - 40, 300, 30, 40, label="Step", mat=MAT("MI_FCL_WoodFloor"))
        if n: print(f"  {n} threshold steps ({drop:.0f} cm)")
    H = min(320.0, rm["ceiling"] - rm["floor"] - 20)
    r.exposure(x0, x1, y0, y1, -30, H + 60)
    r.light(cx, (y0 + y1) / 2, top + min(H - 40, 240), 55.0, radius=850.0, label="HouseLamp")
    far = y1 - 45; left, right = x1 - 45, x0 + 45                         # +X is the left side looking in
    if purpose == "tavern":
        r.put("S:BarCounter", left - 30, y0 + Dp * 0.55, top, yaw=-90, label="Bar")
        r.put("S:KegStand", left - 25, y1 - 70, top, yaw=-90, label="Kegs")
        for k in range(2): r.put(PACK("Small_props/SM_barrel_0" + str(1 + k)), left - 40, y0 + 70 + k * 80, top, label="AleBarrel")
        r.hearth(right, y0 + Dp * 0.6, "+x", cauldron=True)
        for k, (tx, ty) in enumerate(((cx, y0 + Dp * 0.35), (cx - W * 0.15, y0 + Dp * 0.75))):
            if ty < y1 - 140: r.dining(tx, ty, 0, kind="small" if W < 600 else "long", seats="bench" if k == 0 else "chairs")
        r.put("Chandelier", cx, (y0 + y1) / 2, top + H - 140, label="Chandelier", coll=False)
        r.light(cx, y0 + Dp * 0.75, top + H - 120, 60.0, radius=800.0, label="TavernLamp")
    elif purpose in ("fisher", "fisher2"):
        r.bed("BedSingle", left - 100, far - 120 if Dp > 400 else (y0 + y1) / 2, -90 + 180)
        r.hearth(cx, far + 5, "-y", cauldron=True)
        r.put(LAKE("SM_RodHolder"), right + 20, y0 + 120, top, yaw=90, label="RodHolder")
        r.put(LAKE("SM_Rod"), right + 25, y0 + 220, top, yaw=90, label="FishingRod")
        for k in range(2): r.put(LAKE("SM_WoodenBucket0" + str(1 + k)), right + 40, y0 + 300 + k * 60, top, label="FishBucket")
        r.put(LAKE("SM_WoodenBarrel01"), right + 45, far - 40, top, label="SaltBarrel")
        r.dining(cx - 40, y0 + Dp * 0.45, 0, kind="small", seats="bench")
        r.put("Chest", left - 45, y0 + 80, top, yaw=-90, label="FisherChest")
    elif purpose == "farmhouse":
        for k in range(2 if W > 450 else 1):
            r.bed("BedDouble" if k == 0 else "BedSingleGreen", left - 110 - k * 170, far - 110, 180)
        r.hearth(right, y0 + Dp * 0.45, "+x", cauldron=True)
        r.dining(cx, y0 + Dp * 0.35, 0, kind="small", seats="chairs")
        r.put("Wardrobe", left - 40, y0 + 90, top, yaw=-90, label="Wardrobe")
        r.put("ShelfRack", right + 20, far - 30, top, yaw=0 + 180, label="Shelf")
        r.put(LAKE("SM_FlowerPot01"), cx, y0 + Dp * 0.35, top + 76, coll=False, label="Pot")
    elif purpose == "smithy":
        r.put("Forge", cx, far - 30, top, yaw=180, label="Forge")
        r.fire_light(cx, far - 120, top + 110)
        r.put("Anvil", cx, far - 170, top, yaw=90, label="Anvil")
        r.put("QuenchTub", cx + 110, far - 160, top, label="QuenchTub")
        r.put("ToolBoard", left - 6, y0 + Dp * 0.5, top + 110, yaw=-90, label="ToolBoard")
        r.put(LAKE("SM_WoodenBox01"), right + 40, y0 + 80, top, label="IronStock")
        r.put("Chest", right + 45, y0 + 180, top, yaw=90, label="SmithChest")
    elif purpose == "weaver":
        r.put(LAKE("SM_Cloth01"), cx, far - 40, top, yaw=0, label="ClothRack", coll=False)
        r.put(LAKE("SM_Cloth02"), left - 50, y0 + Dp * 0.5, top, yaw=90, label="Cloth", coll=False)
        r.put("TableLong" if W > 500 else "TableSmall", cx, y0 + Dp * 0.45, top, yaw=0, label="CuttingTable")
        r.put(LAKE("SM_Chair"), cx, y0 + Dp * 0.45 - 70, top, label="Chair")
        r.put("S:Trunk", right + 50, y0 + 90, top, yaw=90, label="ClothTrunk")
        r.put("BedSingle", right + 110, far - 110, top, yaw=180, label="Bed")
        r.put("Candles", cx, y0 + Dp * 0.45, top + 76, coll=False, label="Candles")
    elif purpose == "barn":
        for k in range(min(3, int(Dp // 260))): r.put("StallPartition", left - 110, y0 + 180 + k * 260, top, yaw=90, label="Stall")
        r.put("Trough", left - 60, y0 + 120, top, yaw=90, label="Trough")
        r.put("HayPile", right + 120, far - 120, top, label="Hay"); r.put("HayBale", right + 70, y0 + 120, top, label="HayBale")
        r.put("Cart", cx, (y0 + y1) / 2, top, yaw=0, label="Cart")
        for k, t in enumerate(("Pitchfork", "Rake", "Shovel")): r.put(t, right + 15, y0 + 250 + k * 40, top, yaw=90, label="Tool", coll=False)
    elif purpose == "storehouse":
        for k in range(int(W // 160)):
            r.put("ShelfRack", x0 + 90 + k * 160, far - 20, top, yaw=180, label="Rack")
        r.storage(cx, y0 + Dp * 0.68, rng, n=7, spread=min(W * 0.6, Dp * 0.45))      # back half: the doorway stays clear
        r.put("ShelfRack", right + 20, (y0 + y1) / 2, top, yaw=90, label="Rack")
    print(f"furnished {purpose}: {rm['door']} {W:.0f} x {Dp:.0f} cm, floor top {top:.0f}, {r.n} actors")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True); print("saved")
json.dump([{"purpose": p, "door": f[1]["door"], "frame": [f[3].translation.x, f[3].translation.y, f[3].translation.z, f[3].rotation.rotator().yaw], "box": list(f[4])} for p, f in plan],
          open(SA + r"\village_interiors.json", "w"), indent=1)
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
