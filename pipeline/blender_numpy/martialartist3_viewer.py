"""A three.js page that plays MartialArtist3's clips (martialartist3_retarget.py's MartialArtist3_Animated.glb and
ma3_clips.json): four shots, Idle (her 9 s idle twice round, closer; the page opens on it), Walk, Run (she moves at the
speed measured from her planted foot, the camera with her) and Combat (her idle's calm first 1.1 s, the three boxing
clips, the two front kicks, the dash and the ten chi attacks, each faded into the next, its name shown). A shot is a function of its time alone (the clip and its place in it, the fade from the clip
before, how far she has come), so the slider under it scrubs it back and forth as well as showing where it is; with
rewind (the shot from its start), stop (held at its start), pause, speed, a camera to drag and a button that records
the shot as a WebM file.
One file: the GLB is inside it (base64), so it opens from the disk; three.js itself is loaded from cdn.jsdelivr.net.
Python: martialartist3_viewer.py <MartialArtist3_Animated.glb> <ma3_clips.json> <out.html>"""
import base64, json, sys
glb, meta, out = sys.argv[1:4]
META = json.load(open(meta))
COMBAT = ["Idle", "Box_01", "Box_02", "Box_03", "Front_kick_01", "Front_kick_02", "Dash", "Chi_StraightPunch", "Chi_SideKick", "Chi_SmashingStrike",
          "Chi_RoundhouseKick", "Chi_ChainPunch", "Chi_RearKick", "Chi_PiercingPalm", "Chi_AxeKick", "Chi_MeteorFist", "Chi_SpinningKick", "Idle"]
missing = [c for c in COMBAT + ["Walk", "Run"] if c not in META["clips"]]
assert not missing, missing
HEIGHT_M = 1.65
PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>MartialArtist3 clips</title>
<style>
  html, body { margin: 0; height: 100%; background: #14171c; color: #e8e6e1; font: 14px/1.4 system-ui, "Segoe UI", sans-serif; overflow: hidden; }
  canvas { display: block; }
  #bar { position: fixed; left: 0; right: 0; bottom: 0; padding: 18px 12px 10px; background: linear-gradient(transparent, rgba(10, 12, 15, .9) 45%); }
  #scrub { display: flex; gap: 12px; align-items: center; max-width: 860px; margin: 0 auto 10px; }
  #seek { flex: 1; min-width: 0; height: 22px; accent-color: #c8553d; cursor: pointer; }
  #time { color: #a7adb8; font-variant-numeric: tabular-nums; white-space: nowrap; min-width: 9.5em; text-align: right; }
  #keys { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; justify-content: center; }
  button, select { font: inherit; color: #e8e6e1; background: #262b33; border: 1px solid #3a414c; border-radius: 6px; padding: 7px 14px; cursor: pointer; }
  button:hover { background: #30363f; }
  button.on { background: #c8553d; border-color: #c8553d; color: #fff; }
  button:focus-visible, select:focus-visible, #seek:focus-visible { outline: 2px solid #f0b35a; outline-offset: 2px; }
  #cap { position: fixed; left: 16px; top: 14px; }
  #cap b { display: block; font-size: 22px; font-weight: 600; letter-spacing: .01em; }
  #cap span { color: #a7adb8; }
  #msg { position: fixed; inset: 0; display: flex; align-items: center; justify-content: center; color: #a7adb8; pointer-events: none; }
  .sep { width: 1px; height: 22px; background: #3a414c; }
</style></head><body>
<div id="cap"><b id="shot">&nbsp;</b><span id="move"></span></div>
<div id="msg">Loading the model ...</div>
<div id="bar">
  <div id="scrub"><input id="seek" type="range" min="0" max="1000" step="1" value="0" aria-label="Place in the shot"><span id="time">0.00 / 0.00 s</span></div>
  <div id="keys">
    <button data-shot="idle">Idle</button><button data-shot="walk">Walk</button><button data-shot="run">Run</button><button data-shot="combat">Combat</button><button data-shot="all">All four</button>
    <span class="sep"></span>
    <button id="rewind" title="Back to the start of the shot">Rewind</button><button id="stop" title="Stop at the start of the shot">Stop</button><button id="pause">Pause</button>
    <label>Speed <select id="speed"><option value="0.25">0.25x</option><option value="0.5">0.5x</option><option value="1" selected>1x</option></select></label>
    <span class="sep"></span>
    <button id="rec">Record this shot (WebM)</button>
  </div>
</div>
<script type="application/octet-stream" id="glb">__GLB__</script>
<script type="importmap">{ "imports": { "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js", "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/" } }</script>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const META = __META__, COMBAT = __COMBAT__, HEIGHT_M = __HEIGHT__;
const SCALE = HEIGHT_M / META.height, FADE = 0.15, LOOPS = { idle: 2, walk: 3, run: 6 };   // (an idle, walk or run shot: whole loops of its clip)
// (in the combat shot the idle plays only its calm first 1.1 s, before her hands go to her hips: it is 9 s long)
const COMBAT_IDLE = 1.1, span = n => n === 'Idle' ? Math.min(COMBAT_IDLE, dur(n)) : dur(n);
const CLIP = { idle: 'Idle', walk: 'Walk', run: 'Run' }, NEXT = { idle: 'walk', walk: 'run', run: 'combat', combat: 'idle' };
const $ = id => document.getElementById(id);

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.setSize(innerWidth, innerHeight);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.1;
document.body.prepend(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0x14171c); scene.fog = new THREE.Fog(0x14171c, 9, 24);
const camera = new THREE.PerspectiveCamera(35, innerWidth / innerHeight, 0.05, 100);
const controls = new OrbitControls(camera, renderer.domElement); controls.enableDamping = true; controls.minDistance = 1.5; controls.maxDistance = 12;
controls.maxPolarAngle = Math.PI * 0.495;
scene.add(new THREE.HemisphereLight(0xdfe6f2, 0x30343c, 1.5));
const sun = new THREE.DirectionalLight(0xfff1dc, 2.6); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -3, right: 3, top: 3, bottom: -3, near: 0.5, far: 20 }); sun.shadow.bias = -0.0005;
scene.add(sun, sun.target);
const rim = new THREE.DirectionalLight(0x8fb4ff, 1.2); scene.add(rim, rim.target);

// the floor: one-metre tiles, kept under her (it steps a whole tile at a time, so the lines stay where they are)
const tile = document.createElement('canvas'); tile.width = tile.height = 256;
{ const g = tile.getContext('2d'); g.fillStyle = '#2a2f37'; g.fillRect(0, 0, 256, 256); g.strokeStyle = '#48505c'; g.lineWidth = 4; g.strokeRect(0, 0, 256, 256);
  g.strokeStyle = '#343a44'; g.lineWidth = 2; g.beginPath(); g.moveTo(128, 0); g.lineTo(128, 256); g.moveTo(0, 128); g.lineTo(256, 128); g.stroke(); }
const tex = new THREE.CanvasTexture(tile); tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.repeat.set(60, 60); tex.colorSpace = THREE.SRGBColorSpace;
tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
const floor = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.95 }));
floor.rotation.x = -Math.PI / 2; floor.receiveShadow = true; scene.add(floor);

function bytes() {
  const s = atob($('glb').textContent.trim()), a = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) a[i] = s.charCodeAt(i);
  return a.buffer;
}
let hero, mixer, acts = {}, shot = null, T = 0, lap = 0, length = 1, starts = [], paused = false, playAll = false, onShotEnd = null, scrubbing = false;
const state = { ready: false, error: null, shot: null, move: null, z: 0, t: 0, length: 0, lap: 0, paused: false, frames: 0 };
window.__ma3 = state;
const dur = n => acts[n].getClip().duration;
const shown = n => n.replace(/^Chi_/, 'Chi: ').replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2');

// the whole of her at the shot's time T: every clip off but the one that plays there (and, in its first FADE seconds,
// the end of the one before it); a walk or run carries her forward by her speed (the laps before this one too)
function pose() {
  for (const n in acts) acts[n].setEffectiveWeight(0);
  let name, z = 0;
  if (shot === 'combat') {
    let i = starts.length - 1; while (i > 0 && T < starts[i]) i--;
    name = COMBAT[i]; const local = T - starts[i], a = acts[name], w = i > 0 ? Math.min(1, local / FADE) : 1;
    a.time = Math.min(local, span(name) - 1e-4); a.setEffectiveWeight(w);
    if (w < 1) { const p = acts[COMBAT[i - 1]]; p.time = span(COMBAT[i - 1]) - 1e-4; p.setEffectiveWeight(1 - w); }
  } else {
    name = CLIP[shot]; const a = acts[name];
    a.time = T % dur(name); a.setEffectiveWeight(1);
    if (shot !== 'idle') z = META.clips[name].speed * SCALE * (lap * length + T);  // (she faces +Z; the idle stays put)
  }
  mixer.update(0);
  const dz = z - hero.position.z; hero.position.z = z; camera.position.z += dz; controls.target.z += dz;
  floor.position.z = Math.round(z);
  sun.target.position.copy(hero.position); sun.position.copy(hero.position).add(new THREE.Vector3(3, 6, 4));
  rim.target.position.copy(hero.position); rim.position.copy(hero.position).add(new THREE.Vector3(-4, 3, -5));
  if (state.move !== name) { state.move = name; $('move').textContent = shown(name); }
  if (!scrubbing) $('seek').value = Math.round(1000 * T / length);
  $('time').textContent = T.toFixed(2) + ' / ' + length.toFixed(2) + ' s';
  Object.assign(state, { z, t: T, lap });
}
function setPaused(p) { paused = p; state.paused = p; $('pause').textContent = p ? 'Play' : 'Pause'; $('pause').classList.toggle('on', p); }
function endShot() {
  if (onShotEnd) { const f = onShotEnd; onShotEnd = null; f(); }
  if (playAll) start(NEXT[shot], true);
  else { T = 0; if (shot === 'walk' || shot === 'run') lap++; }                     // (a shot alone goes round; a walk goes on from where she is)
}
function start(which, keepAll) {
  playAll = !!keepAll; shot = which; T = 0; lap = 0;
  if (which === 'combat') { starts = []; let t = 0; for (const n of COMBAT) { starts.push(t); t += span(n); } length = t; }
  else length = LOOPS[which] * dur(CLIP[which]);
  Object.assign(state, { shot: which, length });
  document.querySelectorAll('[data-shot]').forEach(b => b.classList.toggle('on', b.dataset.shot === (playAll ? 'all' : which)));
  $('shot').textContent = { idle: 'Idle', walk: 'Walking', run: 'Running', combat: 'Combat' }[which];
  pose();
  const view = { idle: [1.5, 1.2, 2.6], combat: [2.6, 1.35, 3.6] }[which] || [3.4, 1.3, 2.6];
  controls.target.set(0, 0.9, 0); camera.position.copy(controls.target).add(new THREE.Vector3(...view));
  controls.update();
}
// the shot from its start again (the camera stays as it was turned); held there when stopped
function restart(hold) {
  if (!state.ready) return;
  if (onShotEnd) { const f = onShotEnd; onShotEnd = null; f(); }                  // (a recording under way ends here)
  T = 0; lap = 0; if (hold) setPaused(true); pose();
}

new GLTFLoader().parse(bytes(), '', gltf => {
  hero = new THREE.Group(); hero.add(gltf.scene); gltf.scene.scale.setScalar(SCALE); scene.add(hero);
  gltf.scene.traverse(o => { if (o.isMesh) { o.castShadow = true; o.frustumCulled = false; if (o.material) { o.material.metalness = 0; o.material.roughness = 0.85; } } });
  mixer = new THREE.AnimationMixer(gltf.scene);
  const have = Object.fromEntries(gltf.animations.map(c => [c.name, c]));
  const lacking = COMBAT.concat(['Walk', 'Run']).filter(n => !have[n]);       // (Idle is COMBAT's first)
  if (lacking.length) { state.error = 'clips missing: ' + lacking.join(', '); $('msg').textContent = state.error; return; }
  for (const n of new Set(COMBAT.concat(['Walk', 'Run']))) { const a = mixer.clipAction(have[n]); a.play(); a.setEffectiveWeight(0); acts[n] = a; }
  $('msg').remove(); state.ready = true; state.clips = gltf.animations.length;
  const asked = new URLSearchParams(location.search).get('shot');           // (?shot=idle | walk | run | combat opens on that shot)
  if (['idle', 'walk', 'run', 'combat'].includes(asked)) start(asked); else start('idle', true);
}, e => { state.error = String(e); $('msg').textContent = 'The model did not load: ' + e; });

document.querySelectorAll('[data-shot]').forEach(b => b.onclick = () => { if (!state.ready) return; setPaused(false); b.dataset.shot === 'all' ? start('idle', true) : start(b.dataset.shot); });
$('pause').onclick = () => setPaused(!paused);
$('rewind').onclick = () => restart(false);
$('stop').onclick = () => restart(true);
// the slider: the shot stands still under the hand and follows it; let go, it plays on from there (or stays, if paused)
const seek = $('seek');
seek.addEventListener('pointerdown', () => { scrubbing = true; });
addEventListener('pointerup', () => { scrubbing = false; });
seek.addEventListener('input', () => { if (!state.ready) return; T = Math.min(length - 1e-3, length * seek.value / 1000); pose(); });
seek.addEventListener('keydown', () => { scrubbing = true; }); seek.addEventListener('keyup', () => { scrubbing = false; });
seek.addEventListener('blur', () => { scrubbing = false; });

// a recording of the shot from its start to its end, saved as a file
$('rec').onclick = () => {
  if (!state.ready || !window.MediaRecorder) return;
  const which = shot, type = ['video/webm;codecs=vp9', 'video/webm'].find(t => MediaRecorder.isTypeSupported(t));
  const rec = new MediaRecorder(renderer.domElement.captureStream(60), { mimeType: type, videoBitsPerSecond: 12e6 }), parts = [];
  rec.ondataavailable = e => parts.push(e.data);
  rec.onstop = () => {
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(parts, { type: 'video/webm' })); a.download = 'MartialArtist3_' + which + '.webm'; a.click();
    $('rec').textContent = 'Record this shot (WebM)'; $('rec').classList.remove('on');
  };
  setPaused(false); start(which); onShotEnd = () => rec.stop(); rec.start();
  $('rec').textContent = 'Recording ...'; $('rec').classList.add('on');
};

addEventListener('resize', () => { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); });
const clock = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 0.1);
  if (state.ready && !paused && !scrubbing) {
    T += dt * +$('speed').value;
    if (T >= length) endShot();
    pose();
  }
  controls.update(); renderer.render(scene, camera); state.frames++;
});
</script></body></html>
"""
page = (PAGE.replace("__GLB__", base64.b64encode(open(glb, "rb").read()).decode("ascii")).replace("__META__", json.dumps(META))
        .replace("__COMBAT__", json.dumps(COMBAT)).replace("__HEIGHT__", str(HEIGHT_M)))
open(out, "w", encoding="utf-8", newline="\n").write(page)
print("MA3 viewer", out, len(page))
