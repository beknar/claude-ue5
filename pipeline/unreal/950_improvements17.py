"""The list of 2026-11-26 (docs/improvements17.txt; the plan docs/improvements17_plan.md), the markets on `brokenspire`:

    950_improvements17.py stalls   phase 3, the squares' twelve stands: Heaven's own stands, three modern kiosks made from boxes in
                                   Heaven's materials (heaven_kit.py) under the medieval stalls' names for Heaven's theme
                                   (Heaven.Town.Stall1 a newsstand, Heaven.Town.Stall2 a food cart, Heaven.Town.Stall3 a coffee kiosk),
                                   their counter's front +X as the town's stalls' (the buyer stands before it, the keeper behind)

Run on the editor with any level open (it opens brokenspire and saves it). The stands themselves, their trades and keepers are the C++'s
(RD/RDList17b.cpp); a medieval town's stalls are the town's own Town.Stall1-3."""
import os, sys, importlib
import unreal
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heaven_kit as hk; importlib.reload(hk)

V = unreal.Vector
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MAP = "/Game/RandomDungeon/Maps/brokenspire"
REPORT = []


def gen():
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def raw(mesh, collision=True):
    p = unreal.RDPiece(); p.mesh = mesh; p.adjust = unreal.Transform()
    b = mesh.get_bounding_box()
    p.size = V(b.max.x - b.min.x, b.max.y - b.min.y, b.max.z - b.min.z)
    p.collision = collision
    return p


def kiosks():
    """three stands about 2.4 m square (the town's stalls' footprint, 260 cm blocked), their counter on the +X face"""
    # (x0, x1, y0, y1, z0, z1, material)
    news = [(-110, 100, -115, 115, 0, 95, "dark"), (-112, 102, -117, 117, 95, 99, "steel"),            # (the counter)
            (100, 104, -110, 110, 20, 90, "signblue"),                                                   # (its front panel)
            (-110, -100, -115, 115, 99, 250, "white"),                                                   # (the back wall)
            (-110, 100, -115, -105, 99, 250, "white"), (-110, 100, 105, 115, 99, 250, "white"),           # (the side walls)
            (-125, 125, -130, 130, 250, 262, "signblue"), (110, 126, -130, 130, 225, 250, "cyan")]       # (the roof, its lit band)
    for k in range(5):          # (magazines on the counter and racks on the back wall)
        news.append((60, 95, -95 + k * 40, -65 + k * 40, 99, 101, ("prod_red", "prod_yellow", "prod_blue", "prod_green", "prod_orange")[k]))
        news.append((-100, -96, -95 + k * 40, -65 + k * 40, 140, 190, ("prod_yellow", "prod_blue", "prod_red", "prod_orange", "prod_green")[k]))
    cart = [(-70, 70, -120, 120, 40, 135, "white"), (70, 72, -118, 118, 90, 110, "prod_red"),            # (the body, a red stripe)
            (-72, 72, -122, 122, 135, 139, "steel"),                                                     # (its top)
            (-20, 20, -90, -50, 0, 40, "tyre"), (-20, 20, 50, 90, 0, 40, "tyre"),                         # (wheels)
            (-5, 5, -5, 5, 139, 230, "steel"), (-115, 115, -140, 140, 230, 238, "prod_yellow"),          # (the parasol)
            (20, 60, -80, -20, 139, 160, "steel"), (20, 60, 20, 80, 139, 150, "dark")]                    # (a griddle, a box)
    coffee = [(-110, 100, -110, 110, 0, 100, "steel"), (-112, 104, -112, 112, 100, 104, "dark"),
              (-110, -100, -110, 110, 104, 240, "steel"), (-110, 100, -110, -100, 104, 240, "steel"), (-110, 100, 100, 110, 104, 240, "steel"),
              (-120, 110, -120, 120, 240, 255, "prod_green"), (96, 104, -100, 100, 200, 240, "prod_green"),
              (98, 102, -60, 60, 210, 230, "panel"),                                                      # (its lit menu board)
              (-90, -60, -60, -20, 104, 160, "dark"), (-90, -60, 20, 60, 104, 140, "steel")]              # (the machine, a grinder)
    mats = hk.materials()
    out = {}
    for name, parts in (("Heaven.Town.Stall1", news), ("Heaven.Town.Stall2", cart), ("Heaven.Town.Stall3", coffee)):
        m = hk.boxes("SM_HV_" + name.split(".")[-1] + "17", parts, mats)
        if m is None: raise RuntimeError(f"950: the merge made nothing for {name}")
        out[name] = raw(m)
        b = m.get_bounding_box()
        REPORT.append(f"stalls: {name} {b.max.x - b.min.x:.0f} x {b.max.y - b.min.y:.0f} x {b.max.z - b.min.z:.0f} cm")
    return out


def stalls(g):
    pcs = g.get_editor_property("pieces")
    for k, p in kiosks().items(): pcs[unreal.Name(k)] = p
    g.set_editor_property("pieces", pcs)


PARTS = {"stalls": stalls}
todo = (sys.argv[1:] or ["stalls"])[0].split(",")
g = gen()
for t in todo: PARTS[t](g)
g.modify(); les.save_current_level()
for l in REPORT: print("950", l)
del g
import gc; gc.collect()
