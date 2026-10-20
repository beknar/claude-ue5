"""The Summoner's face: the shapes that move it (way 4 of docs/emotional-content.md) and the painted patches that change
what is painted on it (way 6). Her eyes and mouth are painted on the texture; each eye is a small mesh piece set into the
face, the face's skin is one piece and the bangs over it are pieces of their own.

Shapes (add_shapes, called by summoner_rig.py): face.json's pushes, a move at full weight falling off smoothly to 0 at its
radius (measured in the front view), on the face's skin and eye pieces only (found by welding the mesh's seams and taking
the pieces under the nose and under the eyes): Smile (mouth corners up and out, the cheeks and the lower lids up), Frown,
BrowsDown, BrowsUp, Squint, JawOpen. The hair over them does not move.

Patches (main): her face rendered from the front (orthographic, unlit, face.json's render), each expression painted over
it with numpy (soft-edged ellipses and strokes: the eyes covered with skin and drawn shut, happy, screwed up in pain or
narrowed in anger; the brows angry or sad; the mouth open), then baked back into her texture through that front
projection (Cycles, emission), on the face's pieces only and only where they face the front (the back of her head is
on the same projection). Each patch is written as a full-size RGBA texture: its colour where it was painted, its alpha
how much (0 elsewhere), for the material to blend in by a parameter of its own (833).

    blender -b -P summoner_face.py -- <Summoner_rig.glb or Summoner.glb> face.json <out_dir>   (patches + a preview sheet)
Writes <out_dir>/T_Summoner_Face_<Patch>.png, front.png (the render), paint_<Patch>.png (the painted front views) and
prints each patch's painted pixels in the texture ("SUMMONER patch")."""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree


# ---------------------------------------------------------------- the face's pieces
def face_pieces(mesh, F):
    """vertex indices of the face's skin and eye pieces (the seams welded; the pieces a ray from the front meets at the
    nose and at each eye)"""
    bm = bmesh.new(); bm.from_mesh(mesh.data); bm.transform(mesh.matrix_world)
    orig = [v.index for v in bm.verts]
    # (weld a copy: keep the map from the welded vertices back to the mesh's)
    pos = {}
    key = lambda co: (round(co.x, 5), round(co.y, 5), round(co.z, 5))
    for v in bm.verts: pos.setdefault(key(v.co), []).append(v.index)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
    comp = [-1] * len(bm.verts); n = 0
    for v in bm.verts:
        if comp[v.index] >= 0: continue
        st = [v]; comp[v.index] = n
        while st:
            a = st.pop()
            for e in a.link_edges:
                b = e.other_vert(a)
                if comp[b.index] < 0: comp[b.index] = n; st.append(b)
        n += 1
    tree = BVHTree.FromBMesh(bm); L = F["landmarks"]; want = set()
    for k in ("nose", "eye_l", "eye_r"):
        x, z = L[k]; hit = tree.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)))
        assert hit[0] is not None, k
        want.add(comp[bm.faces[hit[2]].verts[0].index])
    # (and every small piece wholly in front of the eyes and the mouth: the lashes are pieces of their own; left out, the
    # old upper lashes stayed over the closed eyes. The bangs reach above it.)
    box = {}
    for v in bm.verts:
        c = comp[v.index]; ok = abs(v.co.x) < 0.095 and 1.43 < v.co.z < 1.57 and v.co.y < -0.08      # (the lashes reach x 0.084, the brows' pieces z 1.563; the bangs 1.66)
        box[c] = box.get(c, True) and ok
    want |= {c for c, ok in box.items() if ok}
    keep = set()
    for v in bm.verts:
        if comp[v.index] in want:
            for i in pos.get(key(v.co), []): keep.add(i)
    bm.free()
    return keep, len(want)


def add_shapes(mesh, F):
    keep, pieces = face_pieces(mesh, F)
    mw = mesh.matrix_world; inv = mw.inverted().to_3x3()
    if not mesh.data.shape_keys: mesh.shape_key_add(name="Basis", from_mix=False)
    report = {}
    for name, pushes in F["shapes"].items():
        old = mesh.data.shape_keys.key_blocks.get(name)
        if old: mesh.shape_key_remove(old)
        sk = mesh.shape_key_add(name=name, from_mix=False)
        moved = 0; most = 0.0
        for i in keep:
            p = mw @ mesh.data.vertices[i].co
            if p.y > -0.09: continue                         # (the front of the face only)
            d = Vector((0.0, 0.0, 0.0))
            for ps in pushes:
                for side in ((1, -1) if ps.get("mirror") else (1,)):
                    cx, cz = ps["center"][0] * side, ps["center"][1]
                    if "below" in ps and p.z > ps["below"]: continue
                    r = math.hypot(p.x - cx, p.z - cz) / ps["radius"]
                    if r >= 1.0: continue
                    w = (1.0 - r * r) ** 2
                    d += Vector((ps["move"][0] * side, ps["move"][1], ps["move"][2])) * w
            if d.length > 0.0:
                sk.data[i].co = mesh.data.vertices[i].co + inv @ d; moved += 1; most = max(most, d.length)
        report[name] = {"vertices": moved, "most_mm": round(most * 1000, 2)}
    report["_face_vertices"] = len(keep); report["_pieces"] = pieces
    return report


# ---------------------------------------------------------------- painting (numpy, in the front render's pixels)
class Canvas:
    def __init__(self, h, w):
        self.h, self.w = h, w
        yy, xx = np.mgrid[0:h, 0:w]; self.x = xx + 0.5; self.y = yy + 0.5
        self.rgb = np.zeros((h, w, 3), np.float32); self.a = np.zeros((h, w), np.float32)
    def put(self, cov, col):
        """paint colour col (one colour, or one per pixel) with coverage cov (0..1) over what is painted already ("over",
        the colour kept straight: blending into the empty canvas's black had ringed every patch with a dark line)"""
        cov = np.clip(cov, 0, 1); c = np.asarray(col, np.float32)
        if c.ndim == 1: c = c[None, None, :]
        na = self.a + cov * (1 - self.a)
        w_new = (cov / np.maximum(na, 1e-6))[..., None]
        self.rgb = self.rgb * (1 - w_new) + c * w_new; self.a = na
    def ellipse_cov(self, cx, cy, rx, ry, feather=3.0):
        d = np.sqrt(((self.x - cx) / rx) ** 2 + ((self.y - cy) / ry) ** 2)
        return np.clip((1.0 - d) * min(rx, ry) / feather + 0.5, 0, 1)
    def ellipse(self, cx, cy, rx, ry, col, feather=3.0):
        self.put(self.ellipse_cov(cx, cy, rx, ry, feather), col)
    def stroke(self, pts, width, col, feather=1.5, taper=True):
        """a polyline, its width tapering to the ends when taper"""
        best = np.full((self.h, self.w), 1e9, np.float32); wid = np.zeros_like(best)
        n = len(pts) - 1
        for i in range(n):
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            vx, vy = x1 - x0, y1 - y0; L2 = max(vx * vx + vy * vy, 1e-6)
            t = np.clip(((self.x - x0) * vx + (self.y - y0) * vy) / L2, 0, 1)
            dx = self.x - (x0 + t * vx); dy = self.y - (y0 + t * vy); d = np.sqrt(dx * dx + dy * dy)
            u = (i + t) / n
            ww = width * (np.sin(np.pi * np.clip(u, 0, 1)) ** 0.5 * 0.85 + 0.15) if taper else np.full_like(d, width)
            m = d < best; best = np.where(m, d, best); wid = np.where(m, ww, wid)
        cov = np.clip((wid / 2.0 - best) / feather + 0.5, 0, 1)
        self.put(cov, col)


def blur(a, r):
    """a box blur of radius r three times (about a Gaussian), along both axes"""
    for _ in range(3):
        for ax in (0, 1):
            c = np.cumsum(np.pad(a, [(r + 1, r) if i == ax else (0, 0) for i in range(a.ndim)], mode="edge"), axis=ax)
            a = (np.take(c, range(2 * r + 1, c.shape[ax]), axis=ax) - np.take(c, range(0, c.shape[ax] - 2 * r - 1), axis=ax)) / (2 * r + 1)
    return a


def skin_fill(front, hole, r=22):
    """the colour the skin would have under hole (a 0..1 mask): the skin round it (the hair, the eyes and the dark lines left
    out) blurred into it, weighted by how much skin each blurred pixel took"""
    R, G, B = front[..., 0], front[..., 1], front[..., 2]
    ok = ((R - B) < 0.30) & (R > 0.70) & ((R + G + B) / 3 > 0.62) & (hole < 0.02)
    w = ok.astype(np.float32)
    num = np.dstack([blur(front[..., k] * w, r) for k in range(3)]); den = blur(w, r)[..., None]
    for _ in range(3):              # (widen it where the hole is larger than the blur reaches)
        far = den[..., 0] < 1e-3
        if not far.any(): break
        r = int(r * 1.8); num = np.where(far[..., None], np.dstack([blur(front[..., k] * w, r) for k in range(3)]), num); den = np.where(far[..., None], blur(w, r)[..., None], den)
    return num / np.maximum(den, 1e-4)


def arc(p0, pm, p1, n=24):
    """a quadratic curve from p0 through near pm to p1"""
    out = []
    for i in range(n + 1):
        t = i / n; a = (1 - t) ** 2; b = 2 * (1 - t) * t; c = t * t
        cx = 2 * pm[0] - 0.5 * (p0[0] + p1[0]); cy = 2 * pm[1] - 0.5 * (p0[1] + p1[1])
        out.append((a * p0[0] + b * cx + c * p1[0], a * p0[1] + b * cy + c * p1[1]))
    return out


def paint(name, F, front):
    """the patch called name painted on a canvas the size of the front render (front: its RGB, 0..1)"""
    R = F["render"]; S = R["pixels"] / R["size_m"]; c0x, c0z = R["center"]
    px = lambda x, z: ((x - c0x) * S + R["pixels"] / 2, (c0z - z) * S + R["pixels"] / 2)
    L = F["landmarks"]; ehw, ehh = L["eye_half"][0] * S, L["eye_half"][1] * S
    H, W = front.shape[:2]; cv = Canvas(H, W)
    lash = (0.20, 0.11, 0.09); brow = (0.62, 0.45, 0.30)
    # what gets covered (both eyes, or the top of both, or both brows), and the skin to cover it with
    holes = np.zeros((H, W), np.float32)
    for ek, bk in (("eye_r", "brow_r"), ("eye_l", "brow_l")):
        ex, ey = px(*L[ek]); bx, by = px(*L[bk])
        if name.startswith("Eyes"): holes = np.maximum(holes, cv.ellipse_cov(ex, ey - 4, ehw * 1.10, ehh * 1.30, 10.0))
        if name in ("EyesAngry", "BrowsSad"): holes = np.maximum(holes, cv.ellipse_cov(bx, by, 0.022 * S, 0.0075 * S, 8.0))
    skin = skin_fill(front, holes) if holes.any() else None
    for side, ek, bk in (("r", "eye_r", "brow_r"), ("l", "eye_l", "brow_l")):
        ex, ey = px(*L[ek]); out = -1 if side == "r" else 1       # (image x of her outer corner: her right is the image's left)
        o_x = ex + out * ehw * 1.0; i_x = ex - out * ehw * 0.95
        cover = lambda: cv.put(cv.ellipse_cov(ex, ey - 4, ehw * 1.10, ehh * 1.30, 10.0), skin)      # (taller: the old lashes' ends reach above the eye at its outer corner)
        if name == "EyesClosed":
            cover(); cv.stroke(arc((o_x, ey + 6), (ex, ey + ehh * 0.62), (i_x, ey + 12)), 22, lash)
            cv.stroke([(o_x, ey + 6), (o_x + out * 26, ey - 8)], 10, lash)
        elif name == "EyesHappy":
            cover(); cv.stroke(arc((o_x, ey + ehh * 0.55), (ex, ey - ehh * 0.45), (i_x, ey + ehh * 0.6)), 22, lash)
        elif name == "EyesPain":
            cover()
            tip = (i_x + out * ehw * 0.25, ey + 4)
            cv.stroke([(o_x, ey - ehh * 0.75), tip], 19, lash, taper=False); cv.stroke([tip, (o_x, ey + ehh * 0.8)], 19, lash, taper=False)
        elif name == "EyesAngry":
            # the upper lid comes down from the inside, slanting: the top of the eye covered with skin above it
            p_in = (i_x, ey - ehh * 0.05); p_out = (o_x, ey - ehh * 0.62)
            nx, ny = (p_out[1] - p_in[1]), -(p_out[0] - p_in[0])
            above = ((cv.x - p_in[0]) * nx + (cv.y - p_in[1]) * ny) * np.sign(ny if ny else 1.0)
            inside = np.sqrt(((cv.x - ex) / (ehw * 1.15)) ** 2 + ((cv.y - ey) / (ehh * 1.35)) ** 2) < 1.0
            cov = np.clip(-above / (6.0 * math.hypot(nx, ny)) + 0.5, 0, 1) * inside
            cv.put(cov, skin)
            cv.stroke([p_out, ((p_in[0] + p_out[0]) / 2, (p_in[1] + p_out[1]) / 2 + 3), p_in], 21, lash, taper=False)
            # the brows angled down to the middle
            bx, by = px(*L[bk])
            cv.put(cv.ellipse_cov(bx, by, 0.022 * S, 0.0075 * S, 8.0), skin)
            cv.stroke([(bx + out * 0.020 * S, by - 0.004 * S), (bx - out * 0.017 * S, by + 0.006 * S)], 13, brow)
        elif name == "BrowsSad":
            bx, by = px(*L[bk])
            cv.put(cv.ellipse_cov(bx, by, 0.022 * S, 0.0075 * S, 8.0), skin)
            cv.stroke(arc((bx + out * 0.020 * S, by + 0.004 * S), (bx, by - 0.001 * S), (bx - out * 0.017 * S, by - 0.006 * S)), 12, brow)
    if name == "MouthOpen":
        mx, my = px(*L["mouth"]); cl, cr = px(*L["mouth_corner_l"]), px(*L["mouth_corner_r"]); half = (cl[0] - cr[0]) / 2
        cv.ellipse(mx, my + 0.0055 * S, half * 0.95, 0.0068 * S, (0.36, 0.10, 0.12), feather=2.5)
        cv.ellipse(mx, my + 0.0098 * S, half * 0.55, 0.0030 * S, (0.86, 0.45, 0.47), feather=3.0)
        cv.ellipse(mx, my + 0.0005 * S, half * 0.62, 0.0011 * S, (0.98, 0.97, 0.95), feather=1.5)
        cv.stroke(arc((cr[0], cr[1] + 2), (mx, my + 0.0128 * S), (cl[0], cl[1] + 2)), 6, (0.55, 0.25, 0.25))
        cv.stroke(arc((cr[0], cr[1] + 2), (mx, my - 0.0012 * S), (cl[0], cl[1] + 2)), 5, (0.55, 0.25, 0.25))
    return cv


PATCHES = ["EyesClosed", "EyesHappy", "EyesPain", "EyesAngry", "BrowsSad", "MouthOpen"]


# ---------------------------------------------------------------- main: render, paint, bake back
if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:]
    SRC, FJ, OUT = argv[0], argv[1], argv[2]
    F = json.load(open(FJ)); os.makedirs(OUT, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=SRC)
    sc = bpy.context.scene
    mesh = next(o for o in sc.objects if o.type == 'MESH' and o.vertex_groups)
    for o in [o for o in sc.objects if o.type == 'MESH' and o is not mesh]: bpy.data.objects.remove(o, do_unlink=True)
    mat = mesh.data.materials[0]; nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'); outn = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    base_node = bsdf.inputs["Base Color"].links[0].from_node
    while base_node.type != 'TEX_IMAGE': base_node = base_node.inputs[0].links[0].from_node
    base_img = base_node.image; TW, TH = base_img.size
    R = F["render"]; NPX = R["pixels"]
    # (1) the front render, unlit
    em = nt.nodes.new("ShaderNodeEmission"); nt.links.new(base_node.outputs[0], em.inputs[0]); keep_link = outn.inputs[0].links[0].from_socket
    nt.links.new(em.outputs[0], outn.inputs[0])
    sc.render.engine = 'BLENDER_EEVEE'; sc.view_settings.view_transform = 'Standard'
    sc.render.resolution_x = sc.render.resolution_y = NPX
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
    cam = bpy.data.cameras.new("c"); cam.type = 'ORTHO'; cam.ortho_scale = R["size_m"]; co = bpy.data.objects.new("c", cam); sc.collection.objects.link(co); sc.camera = co
    co.location = Vector((R["center"][0], -1.0, R["center"][1])); co.rotation_euler = (math.pi / 2, 0, 0)
    sc.render.filepath = os.path.join(OUT, "front.png"); bpy.ops.render.render(write_still=True)
    fimg = bpy.data.images.load(os.path.join(OUT, "front.png"))
    front = np.array(fimg.pixels[:], np.float32).reshape(NPX, NPX, 4)[::-1, :, :3]          # (rows from the top)
    # (2) the projection: a UV map from the front (as the render frames it), and which corners belong to the face's front
    keep, _ = face_pieces(mesh, F)
    me = mesh.data; mw = mesh.matrix_world
    proj = me.uv_layers.new(name="FrontProj")
    mask = me.attributes.new("FaceFront", 'FLOAT', 'CORNER')
    S_ = 1.0 / R["size_m"]
    for poly in me.polygons:
        n = (mw.to_3x3() @ poly.normal).normalized()
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index; p = mw @ me.vertices[vi].co
            proj.data[li].uv = ((p.x - R["center"][0]) * S_ + 0.5, (p.z - R["center"][1]) * S_ + 0.5)
            mask.data[li].value = 1.0 if (vi in keep and n.y < 0.05 and p.y < -0.09) else 0.0      # (the eye sockets' steep rims too: left out, they kept the old eyeliner as a ring)
    # (3) for each patch: paint, then bake its colour and its coverage into the texture's UVs
    nt.links.new(keep_link, outn.inputs[0])
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 24; sc.cycles.device = 'CPU'       # (enough samples a texel for the strokes' edges)
    sc.render.bake.margin = 6; sc.render.bake.use_clear = True
    for n_ in [n for n in nt.nodes if n.type in ('EMISSION',)]: nt.nodes.remove(n_)
    uvm = nt.nodes.new("ShaderNodeUVMap"); uvm.uv_map = "FrontProj"
    paint_img_node = nt.nodes.new("ShaderNodeTexImage"); paint_img_node.extension = 'CLIP'
    nt.links.new(uvm.outputs[0], paint_img_node.inputs[0])
    attr = nt.nodes.new("ShaderNodeAttribute"); attr.attribute_name = "FaceFront"; attr.attribute_type = 'GEOMETRY'
    em = nt.nodes.new("ShaderNodeEmission")
    target = nt.nodes.new("ShaderNodeTexImage")
    nt.links.new(em.outputs[0], outn.inputs[0])
    base_uv = me.uv_layers[0].name
    me.uv_layers.active = me.uv_layers[base_uv]
    mixm = nt.nodes.new("ShaderNodeMath"); mixm.operation = 'MULTIPLY'
    sheet = []
    for name in PATCHES:
        cv = paint(name, F, front)
        # the painted front view, for the eye
        prev = front * (1 - cv.a[..., None]) + cv.rgb * cv.a[..., None]
        for kind, arr in (("color", np.dstack([cv.rgb, np.ones_like(cv.a)])), ("alpha", np.dstack([cv.a, cv.a, cv.a, np.ones_like(cv.a)])), ("prev", np.dstack([prev, np.ones_like(cv.a)]))):
            im = bpy.data.images.new(f"{name}_{kind}", NPX, NPX, alpha=True, float_buffer=False)
            im.pixels[:] = arr[::-1].astype(np.float32).ravel()
            if kind == "prev": im.filepath_raw = os.path.join(OUT, f"paint_{name}.png"); im.file_format = 'PNG'; im.save(); sheet.append(im)
            elif kind == "color": col_img = im
            else: a_img = im
        res = {}
        for kind, img in (("color", col_img), ("alpha", a_img)):
            paint_img_node.image = img
            for l in list(em.inputs[0].links): nt.links.remove(l)
            if kind == "color":
                nt.links.new(paint_img_node.outputs[0], em.inputs[0])
            else:
                for l in list(mixm.inputs[0].links) + list(mixm.inputs[1].links): nt.links.remove(l)
                nt.links.new(paint_img_node.outputs[0], mixm.inputs[0]); nt.links.new(attr.outputs["Fac"], mixm.inputs[1]); nt.links.new(mixm.outputs[0], em.inputs[0])
            bimg = bpy.data.images.new(f"bake_{name}_{kind}", TW, TH, alpha=False, float_buffer=False)
            bimg.colorspace_settings.name = 'Non-Color' if kind == "alpha" else 'sRGB'
            target.image = bimg
            for nd in nt.nodes: nd.select = False
            target.select = True; nt.nodes.active = target
            for o in sc.objects: o.select_set(False)
            bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
            bpy.ops.object.bake(type='EMIT')
            res[kind] = np.array(bimg.pixels[:], np.float32).reshape(TH, TW, 4)
        rgba = np.dstack([res["color"][..., :3], res["alpha"][..., 0]])
        out = bpy.data.images.new(f"T_Summoner_Face_{name}", TW, TH, alpha=True, float_buffer=False)
        out.pixels[:] = rgba.ravel(); out.filepath_raw = os.path.join(OUT, f"T_Summoner_Face_{name}.png"); out.file_format = 'PNG'; out.save()
        print("SUMMONER patch", name, "painted pixels in the texture", int((rgba[..., 3] > 0.05).sum()), "| on the front view", int((cv.a > 0.05).sum()))
    print("SUMMONER patches done", OUT)
