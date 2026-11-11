"""A three.js page that plays every clip of an animated GLB, with martialartist3_viewer.py's controls (the user's of
2026-11-11: "put the Summoner5.glb into her own three.js viewer with all of her animations with the same controls as the
martial artist"). One shot a clip, named from it ("walk.001" -> Walk), whole loops of it (about 7 s), and All (each shot
in turn). How each clip moves her is measured in the page when the model loads: a clip that moves her itself (its pelvis
more than 20 cm on over the clip: Summoner5's walk and run) is carried on by that way at each loop's end, so she goes on
instead of going back to its start; one that walks in place is carried at the speed of her planted foot (the clip sampled
60 times, the lower ball's way between samples, the median, turned round). The camera, floor and lights follow her
pelvis. A shot is a function
of its time alone, so the slider under it scrubs it back and forth as well as showing where it is; with rewind (the shot
from its start), stop (held at its start), pause, speed, a camera to drag and a button that records the shot as a WebM.
Her size: the model's height (its mesh at rest) scaled to --height metres.
One file: the GLB is inside it (base64), so it opens from the disk; three.js itself is loaded from cdn.jsdelivr.net.
Python: clip_viewer.py <model.glb> <out.html> [--title T] [--height M] [--shot-seconds S] [--first idle,walk,run]"""
import argparse, base64, json, re, struct
ap = argparse.ArgumentParser()
ap.add_argument("glb"); ap.add_argument("out")
ap.add_argument("--title", default=None); ap.add_argument("--height", type=float, default=1.65)
ap.add_argument("--shot-seconds", type=float, default=7.0)
ap.add_argument("--first", default="", help="clip names (their start, any case) to put first, in this order: idle,walk,run")
A = ap.parse_args()
raw = open(A.glb, "rb").read()
n = struct.unpack("<I", raw[12:16])[0]; J = json.loads(raw[20:20 + n])
CLIPS = [a.get("name") or f"clip {i}" for i, a in enumerate(J.get("animations", []))]
assert CLIPS, "the GLB has no animations"
FIRST = [f.strip().lower() for f in A.first.split(",") if f.strip()]
rank = lambda c: next((i for i, f in enumerate(FIRST) if c.lower().startswith(f)), len(FIRST))
CLIPS = sorted(CLIPS, key=lambda c: (rank(c), CLIPS.index(c)))
title = A.title or re.sub(r"\.glb$", "", A.glb.replace("\\", "/").split("/")[-1], flags=re.I)


def shown(name):
    s = re.sub(r"\.\d+$", "", name).replace("_", " ").strip()
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)
    return s[:1].upper() + s[1:]


SHOTS = [{"clip": c, "name": shown(c), "id": f"s{i}"} for i, c in enumerate(CLIPS)]
PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__ clips</title>
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
<div id="cap"><b id="shot">&nbsp;</b><span id="move">__TITLE__</span></div>
<div id="msg">Loading the model ...</div>
<div id="bar">
  <div id="scrub"><input id="seek" type="range" min="0" max="1000" step="1" value="0" aria-label="Place in the shot"><span id="time">0.00 / 0.00 s</span></div>
  <div id="keys">
    <span id="shots"></span><button data-shot="all">All</button>
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

const SHOTS = __SHOTS__, TITLE = __TITLE_JS__, HEIGHT_M = __HEIGHT__, SHOT_S = __SHOT_S__;
const $ = id => document.getElementById(id);
for (const s of SHOTS) { const b = document.createElement('button'); b.dataset.shot = s.id; b.textContent = s.name; $('shots').append(b, ' '); }

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
let hero, model, mixer, acts = {}, shot = null, T = 0, lap = 0, length = 1, paused = false, playAll = false, onShotEnd = null, scrubbing = false;
const vel = {};                                                                    // (per clip: the floor speed she is carried at, m/s)
const state = { ready: false, error: null, shot: null, move: null, x: 0, z: 0, t: 0, length: 0, lap: 0, paused: false, frames: 0, speeds: {} };
window.__clipview = state;
const byId = Object.fromEntries(SHOTS.map(s => [s.id, s]));
const dur = c => acts[c].getClip().duration;
const loops = c => Math.max(1, Math.round(SHOT_S / dur(c)));

// how a clip moves her, measured: its pelvis's way over the clip (root motion: Summoner5's walk takes her 1.35 m a loop
// with her feet planted) and, for a clip that walks in place, her planted foot's speed: the clip sampled, the lower ball
// each time, its way between samples, the median of those turned round. A clip that moves her itself is carried only by
// a loop's way at each loop's end (else she would go back to its start); one in place by the foot's speed
const PELVIS = ['pelvis', 'hips', 'Hips', 'mixamorig:Hips'];
let pelvis = null;
function measure(clip) {
  const a = acts[clip], ball = ['ball_l', 'ball_r'].map(n => model.getObjectByName(n)).filter(Boolean);
  for (const n in acts) acts[n].setEffectiveWeight(0);
  a.setEffectiveWeight(1); const N = 60, d = dur(clip), steps = [], p0 = [new THREE.Vector3(), new THREE.Vector3()], p1 = [new THREE.Vector3(), new THREE.Vector3()];
  const at = (t, out) => { a.time = t; mixer.update(0); model.updateMatrixWorld(true); ball.forEach((b, i) => b.getWorldPosition(out[i])); };
  const hip = t => { a.time = t; mixer.update(0); model.updateMatrixWorld(true); return pelvis.getWorldPosition(new THREE.Vector3()); };
  const way = hip(Math.max(0, d - 1e-4)).sub(hip(0)); way.y = 0;
  let foot = new THREE.Vector3();
  if (ball.length === 2) {
    at(0, p0);
    for (let i = 1; i <= N; i++) {
      at(d * i / N, p1); const k = p0[0].y + p1[0].y < p0[1].y + p1[1].y ? 0 : 1;     // (the foot lower over the step)
      steps.push(p1[k].clone().sub(p0[k]).multiplyScalar(N / d)); p0.forEach((v, j) => v.copy(p1[j]));
    }
    const med = ax => { const v = steps.map(s => s[ax]).sort((x, y) => x - y); return v[v.length >> 1]; };
    foot = new THREE.Vector3(-med('x'), 0, -med('z'));
  }
  a.setEffectiveWeight(0);
  // (moves her itself: more than 20 cm a loop and 0.4 m/s; a hit reaction that knocks her back 20 cm in a second is no
  // walk, and carried on it would take her further back at each repeat. In place, a foot faster than 0.3 m/s: an idle's
  // shuffling feet are not a walk either)
  const own = way.length() > 0.2 && way.length() / d > 0.4;
  if (!own && foot.length() < 0.3) foot.set(0, 0, 0);
  return { way: own ? way : new THREE.Vector3(), speed: own ? new THREE.Vector3() : foot, own };
}

// the whole of her at the shot's time T: its clip at T within its loop, the loops before it carried on by the clip's own
// way and an in-place clip by its speed (the shot's laps before too); the camera, floor and lights follow her pelvis
const follow = new THREE.Vector3();
function pose() {
  for (const n in acts) acts[n].setEffectiveWeight(0);
  const c = byId[shot].clip, a = acts[c], m = vel[c], k = Math.floor(T / dur(c));
  a.time = Math.min(T - k * dur(c), dur(c) - 1e-4); a.setEffectiveWeight(1); mixer.update(0);
  const p = m.way.clone().multiplyScalar(lap * loops(c) + k).addScaledVector(m.speed, lap * length + T);
  hero.position.copy(p); model.updateMatrixWorld(true);
  const f = pelvis.getWorldPosition(new THREE.Vector3()); f.y = 0;
  const d = f.clone().sub(follow); follow.copy(f); camera.position.add(d); controls.target.add(d);
  floor.position.set(Math.round(f.x), 0, Math.round(f.z));
  sun.target.position.copy(f); sun.position.copy(f).add(new THREE.Vector3(3, 6, 4));
  rim.target.position.copy(f); rim.position.copy(f).add(new THREE.Vector3(-4, 3, -5));
  if (!scrubbing) $('seek').value = Math.round(1000 * T / length);
  $('time').textContent = T.toFixed(2) + ' / ' + length.toFixed(2) + ' s';
  Object.assign(state, { x: f.x, z: f.z, t: T, lap, move: c });
}
function setPaused(p) { paused = p; state.paused = p; $('pause').textContent = p ? 'Play' : 'Pause'; $('pause').classList.toggle('on', p); }
function endShot() {
  if (onShotEnd) { const f = onShotEnd; onShotEnd = null; f(); }
  if (playAll) start(SHOTS[(SHOTS.findIndex(s => s.id === shot) + 1) % SHOTS.length].id, true);
  else { T = 0; lap++; }                                                          // (a shot alone goes round; a walk goes on from where she is)
}
function start(which, keepAll) {
  playAll = !!keepAll; shot = which; T = 0; lap = 0;
  const c = byId[which].clip; length = loops(c) * dur(c);
  Object.assign(state, { shot: which, length });
  document.querySelectorAll('[data-shot]').forEach(b => b.classList.toggle('on', b.dataset.shot === (playAll ? 'all' : which)));
  $('shot').textContent = byId[which].name;
  hero.position.set(0, 0, 0); T = 0; pose();
  // (the camera from her front right, turned to the way she goes when she goes anywhere, kept with her pelvis)
  const m = vel[c], v = m.way.clone().add(m.speed), ahead = v.length() > 0.05 ? v.normalize() : new THREE.Vector3(0, 0, 1), side = new THREE.Vector3(ahead.z, 0, -ahead.x);
  controls.target.set(follow.x, 0.9, follow.z); camera.position.copy(controls.target).addScaledVector(ahead, 2.6).addScaledVector(side, -3.4).add(new THREE.Vector3(0, 0.4, 0));
  controls.update();
}
function restart(hold) {
  if (!state.ready) return;
  if (onShotEnd) { const f = onShotEnd; onShotEnd = null; f(); }                  // (a recording under way ends here)
  T = 0; lap = 0; if (hold) setPaused(true); pose();
}

new GLTFLoader().parse(bytes(), '', gltf => {
  model = gltf.scene; hero = new THREE.Group(); hero.add(model); scene.add(hero);
  // (her bones placed before she is measured, and her skinned vertices measured one by one: a skinned mesh's box read
  // before its bones' matrices were set came out a fraction of her and drew her ten times too big)
  model.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(model, true), h = box.max.y - box.min.y, k = HEIGHT_M / h;
  model.scale.setScalar(k); model.position.y = -box.min.y * k;
  model.traverse(o => { if (o.isMesh) { o.castShadow = true; o.frustumCulled = false; if (o.material) { o.material.metalness = 0; o.material.roughness = 0.85; } } });
  mixer = new THREE.AnimationMixer(model);
  for (const c of gltf.animations) { const a = mixer.clipAction(c); a.play(); a.setEffectiveWeight(0); acts[c.name] = a; }
  const lacking = SHOTS.filter(s => !acts[s.clip]).map(s => s.clip);
  if (lacking.length) { state.error = 'clips missing: ' + lacking.join(', '); $('msg').textContent = state.error; return; }
  pelvis = PELVIS.map(n => model.getObjectByName(n)).find(Boolean) || model;
  for (const s of SHOTS) {
    const m = vel[s.clip] = measure(s.clip);
    state.speeds[s.name] = { own: m.own, way_m: +m.way.length().toFixed(3), speed: +(m.way.length() / dur(s.clip) + m.speed.length()).toFixed(3) };
  }
  $('msg').remove(); state.ready = true; state.clips = gltf.animations.length; state.height = +(h * k).toFixed(3);
  const asked = new URLSearchParams(location.search).get('shot');           // (?shot=<clip's name, any case> opens on that shot)
  const pick = SHOTS.find(s => asked && s.name.toLowerCase() === asked.toLowerCase());
  if (pick) start(pick.id); else start(SHOTS[0].id, true);
}, e => { state.error = String(e); $('msg').textContent = 'The model did not load: ' + e; });

document.querySelectorAll('[data-shot]').forEach(b => b.onclick = () => { if (!state.ready) return; setPaused(false); b.dataset.shot === 'all' ? start(SHOTS[0].id, true) : start(b.dataset.shot); });
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
    const a = document.createElement('a'); a.href = URL.createObjectURL(new Blob(parts, { type: 'video/webm' })); a.download = TITLE + '_' + byId[which].name + '.webm'; a.click();
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
page = (PAGE.replace("__GLB__", base64.b64encode(raw).decode("ascii")).replace("__SHOTS__", json.dumps(SHOTS))
        .replace("__TITLE_JS__", json.dumps(title)).replace("__TITLE__", title).replace("__HEIGHT__", str(A.height))
        .replace("__SHOT_S__", str(A.shot_seconds)))
open(A.out, "w", encoding="utf-8", newline="\n").write(page)
print("clip viewer", A.out, len(page), "shots", [s["name"] for s in SHOTS])
