"""A three.js page that shows the frigates (frigate_build.py's frigate-test, frigate4b_build.py's frigate-4b): buttons to
switch between them, a camera to drag round the one shown (mouse or touch; the wheel zooms), a slow turntable to switch on
and off, views from her picture's angle, the side, the stern, the bow, above and below, and her lights glowing (bloom, which
can be switched off) against a field of stars. ?ship=<name> and ?view=<view> open on one.
One file: the GLBs are inside it (base64), so it opens from the disk; three.js is loaded from cdn.jsdelivr.net.
Python: frigate_viewer.py <out.html> <name>=<ship.glb>[@x,y,z,k] ...   (x,y,z,k: her picture's view, a direction from her
middle in three.js's axes (her bow +Z) and a distance in her lengths)"""
import base64, json, os, sys

out = sys.argv[1]
SHIPS = []
for arg in sys.argv[2:]:
    name, rest = arg.split("=", 1)
    glb, _, pv = rest.partition("@")
    SHIPS.append({"name": name, "glb": base64.b64encode(open(glb, "rb").read()).decode("ascii"),
                  "picture": [float(v) for v in pv.split(",")] if pv else [-0.75, 0.42, -0.5, 1.35]})
assert SHIPS, "no ship given"
PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Frigate Viewer</title>
<style>
  html, body { margin: 0; height: 100%; background: #07090d; color: #e6e9ee; font: 14px/1.4 system-ui, "Segoe UI", sans-serif; overflow: hidden; }
  canvas { display: block; }
  #cap { position: fixed; left: 16px; top: 14px; pointer-events: none; }
  #cap b { display: block; font-size: 22px; font-weight: 600; }
  #cap span { color: #9aa3b2; }
  #ships { position: fixed; right: 16px; top: 14px; display: flex; gap: 8px; }
  #bar { position: fixed; left: 0; right: 0; bottom: 0; padding: 18px 16px 12px; background: linear-gradient(transparent, rgba(5, 7, 10, .9) 45%);
         display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: center; }
  button { font: inherit; color: #e6e9ee; background: #1c222b; border: 1px solid #343d4a; border-radius: 6px; padding: 7px 14px; cursor: pointer; }
  button:hover { background: #252c37; }
  button.on { background: #a8262e; border-color: #a8262e; color: #fff; }
  button:focus-visible { outline: 2px solid #6cb8ff; outline-offset: 2px; }
  .sep { width: 1px; height: 22px; background: #343d4a; }
  #msg { position: fixed; inset: 0; display: flex; align-items: center; justify-content: center; color: #9aa3b2; pointer-events: none; }
</style></head><body>
<div id="cap"><b id="title">Frigate</b><span id="info">&nbsp;</span></div>
<div id="ships"></div>
<div id="msg">Loading the model ...</div>
<div id="bar">
  <button data-view="picture" class="on">Picture angle</button><button data-view="side">Side</button><button data-view="stern">Stern</button>
  <button data-view="bow">Bow</button><button data-view="top">Above</button><button data-view="below">Below</button>
  <span class="sep"></span>
  <button id="spin">Turntable</button><button id="glow" class="on">Glow</button>
</div>
<script type="application/json" id="ships-data">__SHIPS__</script>
<script type="importmap">{ "imports": { "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js", "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/" } }</script>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
const $ = id => document.getElementById(id);
const SHIPS = JSON.parse($('ships-data').textContent);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.setSize(innerWidth, innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 0.85;
document.body.prepend(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x07090d);
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;   // (reflections on the metal)
scene.environmentIntensity = 0.3;
const camera = new THREE.PerspectiveCamera(35, innerWidth / innerHeight, 1, 5000);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.minDistance = 25; controls.maxDistance = 900; controls.autoRotateSpeed = 0.8;
scene.add(new THREE.HemisphereLight(0xdfe7f5, 0x1a1f28, 0.55));
const sun = new THREE.DirectionalLight(0xfff4e6, 1.7); sun.position.set(-120, 160, 90); scene.add(sun);
const sun2 = new THREE.DirectionalLight(0xfff4e6, 1.0); sun2.position.set(140, 120, 60); scene.add(sun2);   // (the other side lit too)
const rim = new THREE.DirectionalLight(0x8fb6ff, 0.6); rim.position.set(140, 40, -160); scene.add(rim);

// stars on a far sphere
{ const n = 3000, p = new Float32Array(n * 3), v = new THREE.Vector3();
  for (let i = 0; i < n; i++) { v.randomDirection().multiplyScalar(1800 + Math.random() * 1200); v.toArray(p, i * 3); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(p, 3));
  scene.add(new THREE.Points(g, new THREE.PointsMaterial({ color: 0xbfd0ff, size: 2.2, sizeAttenuation: false }))); }

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(innerWidth, innerHeight), 0.7, 0.35, 1.6);   // (only what glows well past white: her lights)
composer.addPass(bloom); composer.addPass(new OutputPass());
let glow = true;

// the views: where the camera stands, as a direction from her middle and a distance in her lengths (her bow is +Z); the
// picture's angle is each ship's own
const VIEWS = { side: [-1, 0.04, 0, 1.5], stern: [-0.3, 0.15, -1, 1.3], bow: [-0.55, 0.25, 1, 1.2], top: [-0.05, 1, 0.02, 1.4],
                below: [-0.6, -0.7, 0.35, 1.25] };
let current = null, centre = new THREE.Vector3(), size = 110;
const loaded = {};
function view(name) {
  const [x, y, z, k] = name === 'picture' ? current.picture : VIEWS[name];
  camera.position.copy(centre).add(new THREE.Vector3(x, y, z).normalize().multiplyScalar(size * k));
  controls.target.copy(centre); controls.update();
  document.querySelectorAll('[data-view]').forEach(b => b.classList.toggle('on', b.dataset.view === name));
}
function bytes(b64) {
  const s = atob(b64), a = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) a[i] = s.charCodeAt(i);
  return a.buffer;
}
const state = { ready: false, error: null, ship: null, triangles: 0, frames: 0 };
window.__frigate = state;
let wanted = null;
function show(ship, viewName) {
  const done = gltf => {
    if (current && loaded[current.name]) scene.remove(loaded[current.name].scene);
    current = ship; const root = gltf.scene; scene.add(root);
    let tris = 0;
    root.traverse(o => { if (o.isMesh) { tris += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3;
      for (const m of [].concat(o.material)) {
        if (m.map) m.map.anisotropy = renderer.capabilities.getMaxAnisotropy();
        if (m.emissive && m.emissive.getHex() === 0) { m.metalness = Math.min(m.metalness, 0.2); m.roughness = Math.max(m.roughness, 0.55); }   // (no sun glare blooming)
      } } });
    const box = new THREE.Box3().setFromObject(root), dim = box.getSize(new THREE.Vector3());
    box.getCenter(centre); size = Math.max(dim.x, dim.y, dim.z);
    $('title').textContent = ship.name;
    $('info').textContent = dim.z.toFixed(0) + ' m long, ' + dim.x.toFixed(0) + ' m across, ' + Math.round(tris).toLocaleString() + ' triangles';
    const msg = $('msg'); if (msg) msg.remove();
    Object.assign(state, { ready: true, ship: ship.name, triangles: Math.round(tris), length: dim.z });
    document.querySelectorAll('[data-ship]').forEach(b => b.classList.toggle('on', b.dataset.ship === ship.name));
    view(viewName || 'picture');
  };
  // (the ship asked for last is the one shown: a slow parse that ends after another ship was picked is kept, not shown (PR #52's review))
  wanted = ship.name;
  if (loaded[ship.name]) return done(loaded[ship.name]);
  new GLTFLoader().parse(bytes(ship.glb), '', gltf => { loaded[ship.name] = gltf; if (wanted === ship.name) done(gltf); },
                         e => { state.error = String(e); $('info').textContent = 'The model did not load: ' + e; });
}
for (const s of SHIPS) {
  const b = document.createElement('button'); b.textContent = s.name; b.dataset.ship = s.name;
  b.onclick = () => show(s); $('ships').appendChild(b);
}
const q = new URLSearchParams(location.search);
const first = SHIPS.find(s => s.name === q.get('ship')) || SHIPS[0];
show(first, VIEWS[q.get('view')] || q.get('view') === 'picture' ? q.get('view') : 'picture');

document.querySelectorAll('[data-view]').forEach(b => b.onclick = () => { if (state.ready) view(b.dataset.view); });
$('spin').onclick = () => { controls.autoRotate = !controls.autoRotate; $('spin').classList.toggle('on', controls.autoRotate); };
$('glow').onclick = () => { glow = !glow; $('glow').classList.toggle('on', glow); };
addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight); composer.setSize(innerWidth, innerHeight); });
renderer.setAnimationLoop(() => {
  controls.update();
  if (glow) composer.render(); else renderer.render(scene, camera);
  state.frames++;
});
</script></body></html>
"""
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
page = PAGE.replace("__SHIPS__", json.dumps(SHIPS))
open(out, "w", encoding="utf-8", newline="\n").write(page)
print("FRIGATE viewer", out, len(page), [s["name"] for s in SHIPS])
