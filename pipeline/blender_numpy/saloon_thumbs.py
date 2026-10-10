"""Thumbnail every Megascans FBX of the Saloon_Interior pack (albedo-textured, 3/4 view) + size (cm) -> PNGs + JSON.
Blender: -b -P saloon_thumbs.py -- pack_fbx_root out_dir"""
import bpy, sys, os, json, math, glob
from mathutils import Vector
argv = sys.argv[sys.argv.index("--") + 1:]
root, out = argv[0], argv[1]; os.makedirs(out, exist_ok=True)
info = {}
for fbx in sorted(glob.glob(os.path.join(root, "**", "*.fbx"), recursive=True)):
    aid = os.path.splitext(os.path.basename(fbx))[0]; folder = os.path.dirname(fbx)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    try: bpy.ops.import_scene.fbx(filepath=fbx)
    except Exception as e: print("fail", aid, e); continue
    obs = [o for o in sc.objects if o.type == 'MESH']
    if not obs: continue
    pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    size_cm = [round((hi[k] - lo[k]) * 100, 1) for k in range(3)]
    tex = sorted(glob.glob(os.path.join(folder, "*.jpg")) + glob.glob(os.path.join(os.path.dirname(folder), aid + "*.jpg")))
    alb = next((t for t in tex if any(k in t.lower() for k in ("albedo", "basecolor", "base_color", "diffuse"))), tex[0] if tex else None)
    mat = bpy.data.materials.new("m"); mat.use_nodes = True
    if alb:
        n = mat.node_tree.nodes.new("ShaderNodeTexImage"); n.image = bpy.data.images.load(alb)
        mat.node_tree.links.new(n.outputs[0], mat.node_tree.nodes["Principled BSDF"].inputs[0])
    for o in obs:
        o.data.materials.clear(); o.data.materials.append(mat)
    c = (lo + hi) / 2; r = max((hi - lo).length, 0.05)
    cam = bpy.data.objects.new("c", bpy.data.cameras.new("c")); sc.collection.objects.link(cam); sc.camera = cam
    cam.location = c + Vector((r * 1.1, -r * 1.3, r * 0.8)); cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sun = bpy.data.objects.new("s", bpy.data.lights.new("s", 'SUN')); sun.data.energy = 3.0; sun.rotation_euler = (0.8, 0.2, 0.6); sc.collection.objects.link(sun)
    sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.35, 0.35, 0.38)
    sc.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
    sc.render.resolution_x = sc.render.resolution_y = 240; sc.render.filepath = os.path.join(out, aid + ".png")
    bpy.ops.render.render(write_still=True)
    info[aid] = {"size_cm": size_cm, "fbx": fbx, "textures": [os.path.basename(t) for t in tex][:8], "tris": sum(len(o.data.polygons) for o in obs)}
    print("thumb", aid, size_cm)
json.dump(info, open(os.path.join(out, "saloon_info.json"), "w"), indent=1)
