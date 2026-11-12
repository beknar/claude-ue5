"""The farmsteads' designs (the user's list of 2026-11-11, docs/improvements11.txt, its fourth phase: "all the farms use the exact
same design. have at least 50 different designs for farms, and they should all have interiors. they should have these types of
buildings: the farmhouse, the barn, gardens, animals in pens with different configurations for pens and the kinds of animals in
them"), written to SourceArt/wilderness/farm_designs.json for 919 farms (the generator's FarmDesigns and FarmLoot).

Each design is a farm's parts in its frame (metres: U along the farm's way, V across it; the farmstead's yard is the 34 m round
FarmsteadsIn keeps level and dry): a farmhouse and a barn of the town's kit always (Nx tiles of 3 m deep along the door's way,
Ny wide), and by the design sheds, coops, granaries, gardens (crops Town.Crop1..6), pens (one, two side by side, round) with the
town's farm animals, a barn's stalls, and yard things (well, cart, woodpile, hay, trough, scarecrow). Laid out by one of six plans
(row, courtyard, L, scattered, compact, long), each from a seeded stream, and kept only if every footprint stands clear of the
others by 2 m, inside 31 m of the middle, and every door has 4 m clear before it; designs that repeat another's buildings, pens and
plan are drawn again. Run: python farm_designs.py [count] [seed]  (60, 1111)"""
import json, math, os, random, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "claude_ue5", "SourceArt", "wilderness", "farm_designs.json")
TILE = 3.0
RADIUS = 31.0
BIG = ["Cow", "Goat", "Pig"]
SMALL = ["Chicken", "Rabbit"]
PEN = {"Chicken": (5, 8), "Rabbit": (4, 6), "Goat": (3, 4), "Pig": (2, 3), "Cow": (2, 3)}
PLANS = ["row", "courtyard", "ell", "scattered", "compact", "long"]
LOOT = {
    "chest": "Bread|1|2|0.7;Cheese|1|1|0.4;Jerky|1|2|0.4;Sweet Roll|1|1|0.25;Small Healing Potion|1|1|0.15",
    "barrel": "Fruit|1|3|0.7;Fish|1|2|0.4;Wheat|1|3|0.4",
    "crate": "Bread|1|2|0.5;Nuts and Seeds|1|2|0.5;Hardtack|1|2|0.4;Wild Carrot|1|3|0.4;Pumpkin|1|1|0.3",
    "wardrobe": "Travel Cake|1|1|0.35;Bread|1|1|0.35;Hardtack|1|1|0.3",
    "barn": "Wheat|2|4|0.8;Nuts and Seeds|1|2|0.4;Pumpkin|1|2|0.4;Fruit|1|2|0.3",
    "granary": "Wheat|2|5|0.9;Bread|1|2|0.4;Nuts and Seeds|1|3|0.5",
    "coop": "Nuts and Seeds|1|2|0.6;Bread|1|1|0.3",
    "shed": "Jerky|1|2|0.4;Hardtack|1|2|0.4;Wild Carrot|1|2|0.4;Fruit|1|2|0.3",
}


def foot(p):
    """a part's footprint: its middle, half sizes along U and V (metres, the farm's frame), a margin round it"""
    k = p["kind"]
    if k in ("house", "barn", "shed", "coop", "granary"):
        hx, hy = p["nx"] * TILE / 2, p["ny"] * TILE / 2
        if round(p["yaw"]) % 180 == 90: hx, hy = hy, hx
        return p["u"], p["v"], hx, hy
    if k == "pen" and p["shape"] == 2: return p["u"], p["v"], p["hu"], p["hu"]
    if k in ("pen", "garden"): return p["u"], p["v"], p["hu"], p["hv"]
    return p["u"], p["v"], 1.0, 1.0


def door_front(p):
    """the 4 m before a building's door (a rectangle like a footprint), or None"""
    if p["kind"] not in ("house", "barn", "shed", "coop", "granary"): return None
    a = math.radians(p["yaw"]); fx, fy = math.cos(a), math.sin(a)
    hx = p["nx"] * TILE / 2
    cx, cy = p["u"] + fx * (hx + 2.2), p["v"] + fy * (hx + 2.2)
    return cx, cy, (2.0 if abs(fx) > 0.5 else 1.0), (1.0 if abs(fx) > 0.5 else 2.0)


def overlaps(a, b, gap):
    return abs(a[0] - b[0]) < a[2] + b[2] + gap and abs(a[1] - b[1]) < a[3] + b[3] + gap


def inside(f):
    """every corner within the yard's radius"""
    return all(math.hypot(f[0] + sx * f[2], f[1] + sy * f[3]) <= RADIUS for sx in (-1, 1) for sy in (-1, 1))


def valid(parts):
    fs = [foot(p) for p in parts]
    for i, f in enumerate(fs):
        if not inside(f): return False
        for j in range(i):
            if overlaps(f, fs[j], 2.0 if parts[i]["kind"] not in ("well", "cart", "woodpile", "hay", "trough") else 0.8): return False
    for i, p in enumerate(parts):
        d = door_front(p)
        if d is None: continue
        if not inside(d): return False
        for j, f in enumerate(fs):
            if j != i and overlaps(d, f, 0.3): return False
    return True


def face_middle(u, v):
    """a building's yaw that turns its door toward the yard's middle, by quarter turns"""
    a = math.degrees(math.atan2(-v, -u))
    return float((round(a / 90.0) * 90) % 360)


def building(r, kind, u, v, yaw=None):
    if kind == "house": nx, ny, st = r.choice([3, 3, 4]), r.choice([3, 4, 4, 5]), r.choice([0, 0, 1, 2])
    elif kind == "barn": nx, ny, st = r.choice([3, 4, 4, 5]), r.choice([4, 5, 6]), r.choice([0, 2, 0])
    elif kind == "granary": nx, ny, st = 2, r.choice([3, 3, 4]), 1
    elif kind == "coop": nx, ny, st = 2, 2, r.choice([0, 2])
    else: nx, ny, st = 2, r.choice([2, 3]), r.choice([0, 2])
    p = {"kind": kind, "u": u, "v": v, "yaw": face_middle(u, v) if yaw is None else yaw, "nx": nx, "ny": ny, "hu": 0, "hv": 0, "style": st, "shape": 0, "animals": "", "variant": ""}
    if kind == "barn" and r.random() < 0.55:
        k = r.choice(BIG); p["animals"] = f"{k}:{r.randint(2, 3)}"
    if kind == "coop" and r.random() < 0.7: p["animals"] = f"Chicken:{r.randint(3, 5)}"
    return p


def herd(r, kind):
    lo, hi = PEN[kind]
    return f"{kind}:{r.randint(lo, hi)}"


def pen(r, u, v, big=True):
    shape = r.choice([0, 0, 1, 2]) if big else r.choice([0, 2])
    if shape == 2:
        rr = r.uniform(4.0, 6.5) if big else r.uniform(2.6, 3.8)
        kinds = [r.choice(BIG if big else SMALL)]
        return {"kind": "pen", "u": u, "v": v, "yaw": 0, "nx": 0, "ny": 0, "hu": round(rr, 1), "hv": round(rr, 1), "style": 0, "shape": 2, "animals": ",".join(herd(r, k) for k in kinds), "variant": ""}
    hu = r.uniform(5.0, 8.0) if big else r.uniform(2.5, 3.8)
    hv = r.uniform(3.5, 6.0) if big else r.uniform(2.2, 3.2)
    if shape == 1:
        a, b = r.sample(BIG + SMALL, 2) if r.random() < 0.4 else r.sample(BIG, 2)
        return {"kind": "pen", "u": u, "v": v, "yaw": 0, "nx": 0, "ny": 0, "hu": round(max(hu, 6.0), 1), "hv": round(hv, 1), "style": 0, "shape": 1, "animals": f"{herd(r, a)},{herd(r, b)}", "variant": ""}
    return {"kind": "pen", "u": u, "v": v, "yaw": 0, "nx": 0, "ny": 0, "hu": round(hu, 1), "hv": round(hv, 1), "style": 0, "shape": 0, "animals": herd(r, r.choice(BIG if big else SMALL)), "variant": ""}


def garden(r, u, v):
    crops = "".join(sorted(r.sample("123456", r.randint(1, 3))))
    return {"kind": "garden", "u": u, "v": v, "yaw": 0, "nx": 0, "ny": 0, "hu": round(r.uniform(2.2, 4.0), 1), "hv": round(r.uniform(1.6, 3.0), 1), "style": 0, "shape": 0, "animals": "", "variant": crops}


def thing(kind, u, v, yaw=0.0):
    return {"kind": kind, "u": u, "v": v, "yaw": yaw, "nx": 0, "ny": 0, "hu": 0, "hv": 0, "style": 0, "shape": 0, "animals": "", "variant": ""}


def jitter(r, x, s=1.5): return round(x + r.uniform(-s, s), 1)


def layout(r, plan):
    """one design's parts by its plan: the house and barn first, then the rest placed round them"""
    P = []
    if plan == "row":
        P += [building(r, "house", jitter(r, -11), jitter(r, -2), 90.0), building(r, "barn", jitter(r, 9), jitter(r, -3), 90.0)]
    elif plan == "courtyard":
        P += [building(r, "house", jitter(r, -14), 0.0), building(r, "barn", jitter(r, 14), 0.0)]
    elif plan == "ell":
        P += [building(r, "house", jitter(r, -12), jitter(r, -10), 0.0), building(r, "barn", jitter(r, 8), jitter(r, -14), 90.0)]
    elif plan == "scattered":
        a = r.uniform(0, 2 * math.pi)
        P += [building(r, "house", round(14 * math.cos(a), 1), round(14 * math.sin(a), 1)), building(r, "barn", round(16 * math.cos(a + 2.4), 1), round(16 * math.sin(a + 2.4), 1))]
    elif plan == "compact":
        P += [building(r, "house", jitter(r, -6), jitter(r, -10, 1.0), 90.0), building(r, "barn", jitter(r, 10), jitter(r, -9, 1.0), 90.0)]
    else:   # long: the house and barn along V, facing +U
        P += [building(r, "house", jitter(r, -12), jitter(r, -12), 0.0), building(r, "barn", jitter(r, -12), jitter(r, 10), 0.0)]
    # (the rest, each tried at places round the yard until it fits)
    extra = ["pen_big", "garden"]
    extra += r.sample(["pen_small", "pen_big2", "garden2", "shed", "coop", "granary"], r.randint(1, 3))
    extra += r.sample(["well", "cart", "woodpile", "hay", "trough", "scarecrow"], r.randint(2, 4))
    for e in extra:
        for _ in range(60):
            a = r.uniform(0, 2 * math.pi); d = r.uniform(6, 25)
            u, v = round(d * math.cos(a), 1), round(d * math.sin(a), 1)
            if e in ("pen_big", "pen_big2"): q = pen(r, u, v, True)
            elif e == "pen_small": q = pen(r, u, v, False)
            elif e in ("garden", "garden2"): q = garden(r, u, v)
            elif e in ("shed", "coop", "granary"): q = building(r, e, u, v)
            else: q = thing(e, u, v, round(r.uniform(0, 360)) if e != "trough" else 0.0)
            if valid(P + [q]): P.append(q); break
        else:
            if e in ("pen_big", "garden"): return None          # (every design has a pen and a garden)
    return P if valid(P) else None


def signature(plan, P):
    return (plan,) + tuple(sorted((p["kind"], p["nx"], p["ny"], p["shape"], p["animals"].split(":")[0], p["variant"][:1]) for p in P if p["kind"] in ("house", "barn", "shed", "coop", "granary", "pen", "garden")))


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1111
    r = random.Random(seed)
    designs, seen, tries = [], set(), 0
    while len(designs) < count and tries < 20000:
        tries += 1
        plan = PLANS[len(designs) % len(PLANS)]
        P = layout(r, plan)
        if not P: continue
        s = signature(plan, P)
        if s in seen: continue
        seen.add(s)
        designs.append({"name": f"{plan}-{len(designs) + 1:02d}", "parts": P})
    assert len(designs) == count, f"only {len(designs)} designs in {tries} tries"
    # (what they hold, for the record)
    kinds = {}
    for d in designs:
        for p in d["parts"]: kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
    shapes = {s: sum(1 for d in designs for p in d["parts"] if p["kind"] == "pen" and p["shape"] == s) for s in (0, 1, 2)}
    animals = sorted({a.split(":")[0] for d in designs for p in d["parts"] for a in p["animals"].split(",") if a})
    doc = {"_doc": __doc__.split("\n\n")[0].replace("\n", " "), "count": count, "seed": seed, "parts": kinds, "pen_shapes": shapes, "animals": animals,
           "loot": LOOT, "designs": designs}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f: json.dump(doc, f, indent=1)
    print(f"FARMDESIGNS {count} designs in {tries} tries -> {os.path.abspath(OUT)}; parts {kinds}; pen shapes {shapes}; animals {animals}")


if __name__ == "__main__":
    main()
