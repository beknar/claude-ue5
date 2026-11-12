"""The heroes' animations in one three.js page (the user's of 2026-11-12: "put all of the heroes into the three.js viewer so their
animations can be viewed ... there should be a choice as to which hero to view"). Reads 922_hero_viewer.py's export (each
hero's mesh.glb and her clips, one glTF each, from the game) and writes one page:
  - each hero's clips merged onto her mesh as one GLB (a clip's channels found on the mesh by their bones' names; a channel
    whose values stay the same over the clip folded to one key: most bones' translations and every scale), kept in the page as
    base64 and decoded only when she is chosen;
  - a choice of hero, her clips by kind (locomotion, combat, spells and casts, the rider's, swimming, the rest) with the one
    before and after, whole loops of the chosen clip, pause, speed, a slider that scrubs it, rewind, and a camera to drag; her
    real size (the game's, in metres), the floor and the camera kept with her pelvis.
One file, so it opens from the disk; three.js is loaded from cdn.jsdelivr.net.
Python: hero_viewer.py <922's export dir> <out.html> [--heroes Warrior,Mage,...]"""
import argparse, base64, json, os, re, struct
ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("out")
ap.add_argument("--heroes", default="Warrior,Mage,Warlock,Rogue,MartialArtist,Summoner")
A = ap.parse_args()
TITLES = {"Warrior": "Warrior", "Mage": "Mage", "Warlock": "Warlock", "Rogue": "Rogue", "MartialArtist": "Martial Artist", "Summoner": "Summoner"}
NC = {"SCALAR": 1, "VEC3": 3, "VEC4": 4}


def read_glb(path):
    raw = open(path, "rb").read()
    n = struct.unpack("<I", raw[12:16])[0]; J = json.loads(raw[20:20 + n])
    o = 20 + n; B = b""
    if o + 8 <= len(raw):
        bn = struct.unpack("<I", raw[o:o + 4])[0]; B = raw[o + 8:o + 8 + bn]
    return J, B


def accessor(J, B, i):
    a = J["accessors"][i]; v = J["bufferViews"][a["bufferView"]]
    assert a["componentType"] == 5126, "float accessors only"
    k = NC[a["type"]]; off = v.get("byteOffset", 0) + a.get("byteOffset", 0); stride = v.get("byteStride", 4 * k)
    out = []
    for e in range(a["count"]):
        out.append(struct.unpack_from(f"<{k}f", B, off + e * stride))
    return out


def write_glb(J, B):
    js = json.dumps(J, separators=(",", ":")).encode("utf-8")
    js += b" " * ((4 - len(js) % 4) % 4); B += b"\0" * ((4 - len(B) % 4) % 4)
    J_len, B_len = len(js), len(B)
    return (struct.pack("<III", 0x46546C67, 2, 12 + 8 + J_len + 8 + B_len) + struct.pack("<II", J_len, 0x4E4F534A) + js
            + struct.pack("<II", B_len, 0x004E4942) + B)


def kind(c):
    f, n = c.get("folder", ""), c["name"].lower()
    if "/Swim/" in f: return "Swimming"
    if "/Horse/" in f: return "On horseback"
    if "Locomotion" in f: return "Locomotion"
    if "/Spells11/" in f or "/Magic" in f or "cast" in n or "spell" in n: return "Spells and casts"
    if "Anims" in f or "/Martial/" in f or "/Summoner4/" in f: return "Combat and moves"
    return "Other"


ORDER = ["Locomotion", "Combat and moves", "Spells and casts", "Swimming", "On horseback", "Other"]


def shown(name, rig):
    s = re.sub(r"^(AS|A|Anim|ANIM)_", "", name)
    s = re.sub(rf"(^{rig}_|_{rig}$)", "", s)
    s = re.sub(r"^(JRPG_)", "", s).replace("_", " ").strip()
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    return (s[:1].upper() + s[1:]) or name


HEROES = []
for hero in [h for h in A.heroes.split(",") if h]:
    d = os.path.join(A.src, hero)
    meta = json.load(open(os.path.join(d, "clips.json"), encoding="utf-8"))
    J, B = read_glb(os.path.join(d, "mesh.glb"))
    B = bytearray(B)
    names = {nd.get("name"): i for i, nd in enumerate(J["nodes"]) if nd.get("name")}
    J.setdefault("animations", [])
    if not J.get("buffers"): J["buffers"] = [{"byteLength": 0}]
    clips, kept, folded, missing = [], 0, 0, set()
    used = set()
    for c in meta["clips"]:
        p = os.path.join(d, "clips", c.get("file", c["name"]) + ".glb")
        if not os.path.exists(p): continue
        CJ, CB = read_glb(p)
        if not CJ.get("animations"): continue
        an = CJ["animations"][0]
        label = shown(c["name"], meta["rig"])
        if label in used: label = f"{label} ({c.get('folder', '').rsplit('/', 1)[-1]})"
        used.add(label)
        chans, samps = [], []
        for ch in an["channels"]:
            tn = CJ["nodes"][ch["target"]["node"]].get("name")
            if tn not in names: missing.add(tn); continue
            s = an["samplers"][ch["sampler"]]
            t = [v[0] for v in accessor(CJ, CB, s["input"])]; vals = accessor(CJ, CB, s["output"])
            if not t: continue
            # (one key when the value stays the same over the clip: within 1e-5 of the first, every component)
            if all(max(abs(a - b) for a, b in zip(v, vals[0])) < 1e-5 for v in vals): t, vals = [t[0]], [vals[0]]; folded += 1
            else: kept += 1
            k = len(vals[0]); typ = {3: "VEC3", 4: "VEC4"}[k]
            for arr, ty, mn in ((t, "SCALAR", True), (vals, typ, False)):
                flat = arr if ty == "SCALAR" else [x for v in arr for x in v]
                while len(B) % 4: B.append(0)
                off = len(B); B += struct.pack(f"<{len(flat)}f", *flat)
                J["bufferViews"].append({"buffer": 0, "byteOffset": off, "byteLength": 4 * len(flat)})
                acc = {"bufferView": len(J["bufferViews"]) - 1, "componentType": 5126, "count": len(arr), "type": ty}
                if mn: acc["min"] = [min(arr)]; acc["max"] = [max(arr)]
                J["accessors"].append(acc)
            samps.append({"input": len(J["accessors"]) - 2, "output": len(J["accessors"]) - 1, "interpolation": s.get("interpolation", "LINEAR")})
            chans.append({"sampler": len(samps) - 1, "target": {"node": names[tn], "path": ch["target"]["path"]}})
        if not chans: continue
        J["animations"].append({"name": label, "channels": chans, "samplers": samps})
        clips.append({"name": label, "kind": kind(c), "length": c["length"], "asset": c["asset"]})
    J["buffers"][0]["byteLength"] = len(B)
    glb = write_glb(J, bytes(B))
    clips.sort(key=lambda x: (ORDER.index(x["kind"]), x["name"].lower()))
    HEROES.append({"id": hero, "title": TITLES.get(hero, hero), "clips": clips, "b64": base64.b64encode(glb).decode("ascii")})
    print(f"hero {hero}: {len(clips)} clips, {kept} channels kept, {folded} folded to one key, {len(glb) / 1e6:.1f} MB"
          + (f", bones not on the mesh: {sorted(missing)[:6]}" if missing else ""))

META = [{"id": h["id"], "title": h["title"], "clips": h["clips"]} for h in HEROES]
PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hero animations</title>
<style>
  html, body { margin: 0; height: 100%; background: #14171c; color: #e8e6e1; font: 14px/1.4 system-ui, "Segoe UI", sans-serif; overflow: hidden; }
  canvas { display: block; }
  #top { position: fixed; left: 16px; top: 14px; right: 16px; display: flex; gap: 14px; align-items: center; flex-wrap: wrap; }
  #top label { color: #a7adb8; }
  #cap { position: fixed; left: 16px; top: 64px; }
  #cap b { display: block; font-size: 22px; font-weight: 600; }
  #cap span { color: #a7adb8; }
  #bar { position: fixed; left: 0; right: 0; bottom: 0; padding: 18px 12px 10px; background: linear-gradient(transparent, rgba(10, 12, 15, .9) 45%); }
  #scrub { display: flex; gap: 12px; align-items: center; max-width: 860px; margin: 0 auto 10px; }
  #seek { flex: 1; min-width: 0; height: 22px; accent-color: #c8553d; cursor: pointer; }
  #time { color: #a7adb8; font-variant-numeric: tabular-nums; white-space: nowrap; min-width: 9.5em; text-align: right; }
  #keys { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: center; }
  button, select { font: inherit; color: #e8e6e1; background: #262b33; border: 1px solid #3a414c; border-radius: 6px; padding: 7px 12px; cursor: pointer; }
  button:hover { background: #30363f; }
  button.on { background: #c8553d; border-color: #c8553d; color: #fff; }
  button:focus-visible, select:focus-visible, #seek:focus-visible { outline: 2px solid #f0b35a; outline-offset: 2px; }
  #clip { max-width: min(60vw, 420px); }
  #msg { position: fixed; inset: 0; display: flex; align-items: center; justify-content: center; color: #a7adb8; pointer-events: none; }
  .sep { width: 1px; height: 22px; background: #3a414c; }
</style></head><body>
<div id="top">
  <label>Hero <select id="hero"></select></label>
  <label>Animation <select id="clip"></select></label>
  <button id="prev" title="The animation before">&larr;</button><button id="next" title="The animation after">&rarr;</button>
</div>
<div id="cap"><b id="name">&nbsp;</b><span id="info"></span></div>
<div id="msg">Loading ...</div>
<div id="bar">
  <div id="scrub"><input id="seek" type="range" min="0" max="1000" step="1" value="0" aria-label="Place in the animation"><span id="time">0.00 / 0.00 s</span></div>
  <div id="keys">
    <button id="rewind" title="Back to the start">Rewind</button><button id="pause">Pause</button>
    <label>Speed <select id="speed"><option value="0.25">0.25x</option><option value="0.5">0.5x</option><option value="1" selected>1x</option><option value="2">2x</option></select></label>
    <span class="sep"></span>
    <button id="all" title="Each animation in turn">Play all</button>
  </div>
</div>
__DATA__
<script type="importmap">{ "imports": { "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js", "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/" } }</script>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const HEROES = __META__;
const $ = id => document.getElementById(id);
const state = { ready: false, hero: null, clip: null, error: null, frames: 0, clips: 0, height: 0 };
window.__heroview = state;
for (const h of HEROES) { const o = document.createElement('option'); o.value = h.id; o.textContent = h.title; $('hero').append(o); }

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.1;
document.body.prepend(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x14171c); scene.fog = new THREE.Fog(0x14171c, 9, 24);
const camera = new THREE.PerspectiveCamera(35, innerWidth / innerHeight, 0.05, 100);
const controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = true; controls.minDistance = 1.2; controls.maxDistance = 12;
controls.maxPolarAngle = Math.PI * 0.495;
scene.add(new THREE.HemisphereLight(0xdfe6f2, 0x30343c, 1.5));
const sun = new THREE.DirectionalLight(0xfff1dc, 2.6); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -3, right: 3, top: 3, bottom: -3, near: 0.5, far: 20 }); sun.shadow.bias = -0.0005;
scene.add(sun, sun.target);
const rim = new THREE.DirectionalLight(0x8fb4ff, 1.2); scene.add(rim, rim.target);
const tile = document.createElement('canvas'); tile.width = tile.height = 256;
{ const g = tile.getContext('2d'); g.fillStyle = '#2a2f37'; g.fillRect(0, 0, 256, 256); g.strokeStyle = '#48505c'; g.lineWidth = 4; g.strokeRect(0, 0, 256, 256);
  g.strokeStyle = '#343a44'; g.lineWidth = 2; g.beginPath(); g.moveTo(128, 0); g.lineTo(128, 256); g.moveTo(0, 128); g.lineTo(256, 128); g.stroke(); }
const tex = new THREE.CanvasTexture(tile); tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.repeat.set(60, 60); tex.colorSpace = THREE.SRGBColorSpace;
const floor = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.95 }));
floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);

const loaded = {};                                                       // (each hero parsed once, when first chosen)
let H = null, model = null, mixer = null, acts = {}, list = [], idx = 0, T = 0, paused = false, playAll = false, scrubbing = false, pelvis = null;
function bytes(id) {
  const s = atob($('glb-' + id).textContent.trim()), a = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) a[i] = s.charCodeAt(i);
  return a.buffer;
}
function fillClips() {
  const sel = $('clip'); sel.innerHTML = '';
  let group = null, k = '';
  list.forEach((c, i) => {
    if (c.kind !== k) { group = document.createElement('optgroup'); group.label = c.kind; sel.append(group); k = c.kind; }
    const o = document.createElement('option'); o.value = i; o.textContent = c.name; group.append(o);
  });
}
function pickHero(id) {
  const meta = HEROES.find(h => h.id === id); if (!meta) return;
  state.ready = false; $('msg').textContent = 'Loading the ' + meta.title + ' ...'; $('msg').style.display = 'flex';
  const show = gltf => {
    if (H) scene.remove(H.root);
    H = gltf; model = gltf.model; mixer = gltf.mixer; acts = gltf.acts; pelvis = gltf.pelvis;
    scene.add(H.root); list = meta.clips.filter(c => acts[c.name]); fillClips();
    $('msg').style.display = 'none'; Object.assign(state, { ready: true, hero: id, clips: list.length, height: gltf.height });
    // (?clip=<part of an animation's name> opens on it, the first time; else her idle)
    const ask = (new URLSearchParams(location.search).get('clip') || '').toLowerCase();
    let want = ask && !state.asked ? list.findIndex(c => c.name.toLowerCase().includes(ask)) : -1; state.asked = true;
    if (want < 0) want = list.findIndex(c => /^idle$/i.test(c.name));
    play(want >= 0 ? want : 0);
    // (the camera from her front right, at her size)
    controls.target.set(0, gltf.height * 0.55, 0); camera.position.set(gltf.height * 1.5, gltf.height * 0.85, gltf.height * 2.3); controls.update();
  };
  if (loaded[id]) return show(loaded[id]);
  setTimeout(() => new GLTFLoader().parse(bytes(id), '', gltf => {
    const root = new THREE.Group(), m = gltf.scene; root.add(m);
    m.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(m, true);
    m.position.y = -box.min.y;                                           // (her feet on the floor, her own size)
    m.traverse(o => { if (o.isMesh) { o.castShadow = true; o.frustumCulled = false; if (o.material) { o.material.metalness = 0; o.material.roughness = Math.max(o.material.roughness, 0.6); } } });
    const mx = new THREE.AnimationMixer(m), a = {};
    for (const c of gltf.animations) { const x = mx.clipAction(c); x.play(); x.setEffectiveWeight(0); a[c.name] = x; }
    const pel = m.getObjectByName('pelvis') || m;
    // (her bones and their lowest at rest: each clip is set down so its lowest bone is where hers is at rest (a rider's clip
    // carries its mount's seat: the camel rider's pelvis is 2 m over its root, and she hung in the air over the floor))
    // (her body's bones: the root stays on the floor while a rider's clip lifts the rest, and the IK targets are no part of her)
    const bones = []; m.traverse(o => { if (o.isBone && !/^(root|ik_)/i.test(o.name)) bones.push(o); });
    const lowest = () => { m.updateMatrixWorld(true); let y = Infinity; const v = new THREE.Vector3(); for (const b of bones) { b.getWorldPosition(v); y = Math.min(y, v.y); } return y; };
    loaded[id] = { root, model: m, mixer: mx, acts: a, pelvis: pel, height: +(box.max.y - box.min.y).toFixed(3), bones, lowest, rest: lowest(), baseY: m.position.y, ground: {} };
    show(loaded[id]);
  }, e => { state.error = String(e); $('msg').textContent = 'The model did not load: ' + e; }), 30);
}
const dur = () => acts[list[idx].name].getClip().duration;
let loopsDone = 0;
function play(i) {
  idx = (i + list.length) % list.length; T = 0; loopsDone = 0;
  for (const n in acts) acts[n].setEffectiveWeight(0);
  const c = list[idx]; $('clip').value = String(idx); $('name').textContent = c.name;
  // (set down: the clip's lowest bone over 12 moments against her rest's, once a clip)
  if (H.ground[c.name] === undefined) {
    const a = acts[c.name], d = a.getClip().duration; let low = Infinity;
    model.position.y = H.baseY; a.setEffectiveWeight(1);
    for (let k = 0; k < 12; k++) { a.time = d * k / 12; mixer.update(0); low = Math.min(low, H.lowest()); }
    a.setEffectiveWeight(0); H.ground[c.name] = H.rest - low;
  }
  model.position.y = H.baseY + H.ground[c.name];
  $('info').textContent = c.kind + ' · ' + dur().toFixed(2) + ' s · ' + c.asset.split('/').pop();
  state.clip = c.name; pose();
}
const follow = new THREE.Vector3();
function pose() {
  if (!list.length) return;
  for (const n in acts) acts[n].setEffectiveWeight(0);
  const a = acts[list[idx].name]; a.time = Math.min(T, dur() - 1e-4); a.setEffectiveWeight(1); mixer.update(0);
  model.updateMatrixWorld(true);
  const f = pelvis.getWorldPosition(new THREE.Vector3()); f.y = 0;
  const d = f.clone().sub(follow); follow.copy(f); camera.position.add(d); controls.target.add(d);
  floor.position.set(Math.round(f.x), 0, Math.round(f.z));
  sun.target.position.copy(f); sun.position.copy(f).add(new THREE.Vector3(3, 6, 4));
  rim.target.position.copy(f); rim.position.copy(f).add(new THREE.Vector3(-4, 3, -5));
  if (!scrubbing) $('seek').value = Math.round(1000 * T / dur());
  $('time').textContent = T.toFixed(2) + ' / ' + dur().toFixed(2) + ' s';
}
function setPaused(p) { paused = p; $('pause').textContent = p ? 'Play' : 'Pause'; $('pause').classList.toggle('on', p); }
$('hero').onchange = () => pickHero($('hero').value);
$('clip').onchange = () => { playAll = false; $('all').classList.remove('on'); play(+$('clip').value); };
$('prev').onclick = () => { if (state.ready) play(idx - 1); };
$('next').onclick = () => { if (state.ready) play(idx + 1); };
$('pause').onclick = () => setPaused(!paused);
$('rewind').onclick = () => { T = 0; pose(); };
$('all').onclick = () => { playAll = !playAll; $('all').classList.toggle('on', playAll); if (playAll) { setPaused(false); play(0); } };
const seek = $('seek');
seek.addEventListener('pointerdown', () => { scrubbing = true; }); addEventListener('pointerup', () => { scrubbing = false; });
seek.addEventListener('input', () => { if (!state.ready) return; T = Math.min(dur() - 1e-3, dur() * seek.value / 1000); pose(); });
addEventListener('keydown', e => { if (e.target.tagName === 'SELECT') return; if (e.key === 'ArrowRight') $('next').click(); if (e.key === 'ArrowLeft') $('prev').click(); if (e.key === ' ') { e.preventDefault(); setPaused(!paused); } });
addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });
const clock = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 0.1);
  if (state.ready && !paused && !scrubbing && list.length) {
    T += dt * +$('speed').value;
    // (each animation loops; Play all goes on to the next after two loops, or one of a long one)
    if (T >= dur()) { T -= dur(); loopsDone++; if (playAll && loopsDone >= (dur() > 2.5 ? 1 : 2)) play(idx + 1); }
    pose();
  }
  controls.update(); renderer.render(scene, camera); state.frames++;
});
const asked = new URLSearchParams(location.search).get('hero');
const first = HEROES.find(h => asked && h.id.toLowerCase() === asked.toLowerCase()) || HEROES[0];
$('hero').value = first.id; pickHero(first.id);
</script></body></html>
"""
data = "\n".join(f'<script type="application/octet-stream" id="glb-{h["id"]}">{h["b64"]}</script>' for h in HEROES)
page = PAGE.replace("__META__", json.dumps(META)).replace("__DATA__", data)
open(A.out, "w", encoding="utf-8", newline="\n").write(page)
print("hero viewer", A.out, f"{len(page) / 1e6:.1f} MB", {h["id"]: len(h["clips"]) for h in HEROES})
