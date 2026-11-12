"""A three.js page that plays the summoner witch's two clips (witch_build.py's SummonerWitch.glb and witch_clips.json):
Walk and Run, each a few whole loops in which she moves forward at the speed measured from her planted foot, the
camera going with her. Play / Pause, a slider that scrubs through the shot (the shot is a function of its time alone, so
dragging it shows every moment of her movement, forward and back) and a speed of 0.25x, 0.5x or 1x.
One file: the GLB is inside it (base64), so it opens from the disk; three.js is loaded from cdn.jsdelivr.net.
Python: witch_viewer.py <SummonerWitch.glb> <witch_clips.json> <out.html>"""
import base64, json, sys

glb, meta, out = sys.argv[1:4]
META = json.load(open(meta))
missing = [c for c in ("Walk", "Run") if c not in META["clips"]]
assert not missing, missing
PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Summoner Witch</title>
<style>
  html, body { margin: 0; height: 100%; background: #16141c; color: #ece8e1; font: 14px/1.4 system-ui, "Segoe UI", sans-serif; overflow: hidden; }
  canvas { display: block; }
  #bar { position: fixed; left: 0; right: 0; bottom: 0; padding: 18px 16px 12px; background: linear-gradient(transparent, rgba(12, 10, 16, .92) 45%); }
  #scrub { display: flex; gap: 12px; align-items: center; max-width: 860px; margin: 0 auto 10px; }
  #seek { flex: 1; min-width: 0; height: 22px; accent-color: #e9a43a; cursor: pointer; }
  #time { color: #b0aab8; font-variant-numeric: tabular-nums; white-space: nowrap; min-width: 8.5em; text-align: right; }
  #keys { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: center; }
  button, select { font: inherit; color: #ece8e1; background: #28232f; border: 1px solid #3f3848; border-radius: 6px; padding: 7px 14px; cursor: pointer; }
  button:hover { background: #332c3b; }
  button.on { background: #9b2a24; border-color: #9b2a24; color: #fff; }
  button:focus-visible, select:focus-visible, #seek:focus-visible { outline: 2px solid #e9a43a; outline-offset: 2px; }
  #cap { position: fixed; left: 16px; top: 14px; }
  #cap b { display: block; font-size: 22px; font-weight: 600; }
  #cap span { color: #b0aab8; }
  #msg { position: fixed; inset: 0; display: flex; align-items: center; justify-content: center; color: #b0aab8; pointer-events: none; }
  .sep { width: 1px; height: 22px; background: #3f3848; }
</style></head><body>
<div id="cap"><b id="shot">&nbsp;</b><span id="move"></span></div>
<div id="msg">Loading the model ...</div>
<div id="bar">
  <div id="scrub"><input id="seek" type="range" min="0" max="1000" step="1" value="0" aria-label="Place in her movement"><span id="time">0.00 / 0.00 s</span></div>
  <div id="keys">
    <button data-shot="walk">Walk</button><button data-shot="run">Run</button>
    <span class="sep"></span>
    <button id="play">Pause</button>
    <label>Speed <select id="speed"><option value="0.25">0.25x</option><option value="0.5">0.5x</option><option value="1" selected>1x</option></select></label>
  </div>
</div>
<script type="application/octet-stream" id="glb">__GLB__</script>
<script type="importmap">{ "imports": { "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js", "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/" } }</script>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const META = __META__, LOOPS = { walk: 4, run: 6 }, CLIP = { walk: 'Walk', run: 'Run' };
const $ = id => document.getElementById(id);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
document.body.prepend(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x16141c); scene.fog = new THREE.Fog(0x16141c, 9, 24);
const camera = new THREE.PerspectiveCamera(35, innerWidth / innerHeight, 0.05, 100);
const controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = true; controls.minDistance = 1.2; controls.maxDistance = 12;
controls.maxPolarAngle = Math.PI * 0.495;
scene.add(new THREE.HemisphereLight(0xe8e4f2, 0x2c2834, 1.6));
const sun = new THREE.DirectionalLight(0xfff0dc, 2.4); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -3, right: 3, top: 3, bottom: -3, near: 0.5, far: 20 }); sun.shadow.bias = -0.0005;
scene.add(sun, sun.target);
const rim = new THREE.DirectionalLight(0xb9a6ff, 1.0); scene.add(rim, rim.target);

// the floor: one-metre tiles, kept under her (it steps a whole tile at a time, so the lines stay where they are)
const tile = document.createElement('canvas'); tile.width = tile.height = 256;
{ const g = tile.getContext('2d'); g.fillStyle = '#2b2733'; g.fillRect(0, 0, 256, 256); g.strokeStyle = '#4a4356'; g.lineWidth = 4; g.strokeRect(0, 0, 256, 256);
  g.strokeStyle = '#353040'; g.lineWidth = 2; g.beginPath(); g.moveTo(128, 0); g.lineTo(128, 256); g.moveTo(0, 128); g.lineTo(256, 128); g.stroke(); }
const tex = new THREE.CanvasTexture(tile); tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.repeat.set(60, 60); tex.colorSpace = THREE.SRGBColorSpace;
tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
const floor = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.95 }));
floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);

function bytes() {
  const s = atob($('glb').textContent.trim()), a = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) a[i] = s.charCodeAt(i);
  return a.buffer;
}
let hero, mixer, acts = {}, shot = 'walk', T = 0, lap = 0, length = 1, paused = false, scrubbing = false;
const state = { ready: false, error: null, shot: null, t: 0, z: 0, length: 0, paused: false, frames: 0 };
window.__witch = state;
const dur = n => acts[n].getClip().duration;

// the whole of her at the shot's time T: its clip at T within its loop, and as far forward as her speed takes her
function pose() {
  const name = CLIP[shot];
  for (const n in acts) acts[n].setEffectiveWeight(n === name ? 1 : 0);
  acts[name].time = T % dur(name);
  mixer.update(0);
  const z = META.clips[name].speed * (lap * length + T);                          // (she faces +Z)
  const dz = z - hero.position.z; hero.position.z = z; camera.position.z += dz; controls.target.z += dz;
  floor.position.z = Math.round(z);
  sun.target.position.copy(hero.position); sun.position.copy(hero.position).add(new THREE.Vector3(3, 6, 4));
  rim.target.position.copy(hero.position); rim.position.copy(hero.position).add(new THREE.Vector3(-4, 3, -5));
  if (!scrubbing) $('seek').value = Math.round(1000 * T / length);
  $('time').textContent = T.toFixed(2) + ' / ' + length.toFixed(2) + ' s';
  Object.assign(state, { t: T, z });
}
function setPaused(p) { paused = p; state.paused = p; $('play').textContent = p ? 'Play' : 'Pause'; $('play').classList.toggle('on', p); }
function start(which) {
  shot = which; T = 0; lap = 0; length = LOOPS[which] * dur(CLIP[which]);
  Object.assign(state, { shot: which, length });
  document.querySelectorAll('[data-shot]').forEach(b => b.classList.toggle('on', b.dataset.shot === which));
  $('shot').textContent = which === 'walk' ? 'Walking' : 'Running';
  $('move').textContent = (META.clips[CLIP[which]].speed).toFixed(2) + ' m/s, a ' + dur(CLIP[which]).toFixed(2) + ' s cycle';
  pose();
  controls.target.set(0, 0.95, hero.position.z); camera.position.set(3.2, 1.45, hero.position.z + 2.6);
  controls.update();
}

new GLTFLoader().parse(bytes(), '', gltf => {
  hero = new THREE.Group(); hero.add(gltf.scene); scene.add(hero);
  gltf.scene.traverse(o => { if (o.isMesh) { o.castShadow = true; o.frustumCulled = false; if (o.material) { o.material.metalness = 0; o.material.roughness = Math.max(0.6, o.material.roughness); } } });
  mixer = new THREE.AnimationMixer(gltf.scene);
  const have = Object.fromEntries(gltf.animations.map(c => [c.name, c]));
  const lacking = ['Walk', 'Run'].filter(n => !have[n]);
  if (lacking.length) { state.error = 'clips missing: ' + lacking.join(', '); $('msg').textContent = state.error; return; }
  for (const n of ['Walk', 'Run']) { const a = mixer.clipAction(have[n]); a.play(); a.setEffectiveWeight(0); acts[n] = a; }
  $('msg').remove(); state.ready = true; state.clips = gltf.animations.length;
  const asked = new URLSearchParams(location.search).get('shot');
  start(asked === 'run' ? 'run' : 'walk');
}, e => { state.error = String(e); $('msg').textContent = 'The model did not load: ' + e; });

document.querySelectorAll('[data-shot]').forEach(b => b.onclick = () => { if (state.ready) start(b.dataset.shot); });
$('play').onclick = () => setPaused(!paused);
// the slider: she stands still under the hand and follows it; let go, she plays on from there (or stays, if paused)
const seek = $('seek');
seek.addEventListener('pointerdown', () => { scrubbing = true; });
addEventListener('pointerup', () => { scrubbing = false; });
seek.addEventListener('input', () => { if (!state.ready) return; T = Math.min(length - 1e-3, length * seek.value / 1000); pose(); });
seek.addEventListener('keydown', () => { scrubbing = true; }); seek.addEventListener('keyup', () => { scrubbing = false; });
seek.addEventListener('blur', () => { scrubbing = false; });
addEventListener('keydown', e => { if (e.code === 'Space' && e.target === document.body) { e.preventDefault(); setPaused(!paused); } });

addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });
const clock = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 0.1);
  if (state.ready && !paused && !scrubbing) {
    T += dt * +$('speed').value;
    if (T >= length) { T -= length; lap++; }                                       // (round again, on from where she is)
    pose();
  }
  controls.update(); renderer.render(scene, camera); state.frames++;
});
</script></body></html>
"""
page = PAGE.replace("__GLB__", base64.b64encode(open(glb, "rb").read()).decode("ascii")).replace("__META__", json.dumps(META))
open(out, "w", encoding="utf-8", newline="\n").write(page)
print("WITCH viewer", out, len(page))
