"""mistward_castle (docs/improvements5.txt): the arena audience's sounds, made from the local sound library.

The library has crowd murmurs (the ambience pack's Ambience_Crowd_*_Loop: steady, a 2-5 dB range, no cheering) and one
person clapping (Extra_Claps.wav), but no cheering crowd and no applause. So:
  Arena_Crowd.wav      the murmur as they appear: Ambience_Crowd_03_Loop (the widest range of the seven), 7 s, faded
  Arena_Cheer_<k>.wav  a cheer: battle cries of NV adult voices of the human vocal packs (never the Kids folders), each
                       voice once, started 0-0.4 s apart at -6..0 dB, over the murmur raised 6 dB; three takes
  Arena_Clap_<k>.wav   applause: the single claps cut from Extra_Claps.wav (onsets 12 dB over the floor, 110 ms each),
                       NC clappers each at 3.5-5.5 claps a second with a little jitter, rising in 0.15 s, dying away over
                       the last 0.8 s; three takes
All mono 44.1 kHz 16 bit (placed in the world), levelled to an RMS of -16 dBFS with the peak under -1 dBFS, and an
index.json (files, lengths, sources) for pipeline/unreal/879. The draws come from a fixed seed: a run makes the same files.
The library and these files are licensed: neither is in the repository (*.wav is ignored).

Usage (a Python with numpy and imageio_ffmpeg):  crowd_sounds.py [library_root] [out_dir]
"""
import sys, os, json, wave, subprocess
import numpy as np, imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = sys.argv[1] if len(sys.argv) > 1 else r"I:\game assets"
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.normpath(os.path.join(HERE, "..", "..", "claude_ue5", "SourceArt", "mistward", "audio5"))
AMB = os.path.join(ROOT, "complete rpg creator bundle", "ambience sounds pack", "The_Sound_Guild_Ambience_Sounds", "WAV - 44100 Hz - 16 Bit")
VOX = [os.path.join(ROOT, "complete rpg creator bundle", v) for v in ("human vocals vol 1", "human vocals vol 2")]
SR = 44100
FF = imageio_ffmpeg.get_ffmpeg_exe()
NV, NC, TAKES = 9, 14, 3
rng = np.random.default_rng(20261101)


def decode(path):
    r = subprocess.run([FF, "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True)
    if r.returncode != 0: raise RuntimeError("ffmpeg: " + r.stderr.decode(errors="replace")[:200])
    return np.frombuffer(r.stdout, dtype=np.float32).astype(np.float64)


def fade(x, a, b):
    x = x.copy(); na, nb = int(a * SR), int(b * SR)
    if na: x[:na] *= np.linspace(0, 1, na)
    if nb: x[-nb:] *= np.linspace(1, 0, nb)
    return x


def trim(x, floor_db=-45.0):
    e = np.abs(x); th = 10 ** (floor_db / 20) * max(e.max(), 1e-9)
    idx = np.nonzero(e > th)[0]
    return x[idx[0]:idx[-1] + 1] if len(idx) else x


def level(x, rms_db=-16.0):
    act = x[np.abs(x) > 0.02 * np.abs(x).max()] if np.abs(x).max() > 0 else x
    rms = np.sqrt((act ** 2).mean() + 1e-12)
    y = x * (10 ** (rms_db / 20) / rms)
    pk = np.abs(y).max()
    if pk > 10 ** (-1 / 20): y *= 10 ** (-1 / 20) / pk
    return y


def write(name, x):
    p = os.path.join(OUT, name)
    with wave.open(p, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    return {"file": name, "length": round(len(x) / SR, 3), "rms_db": round(20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-12), 1), "peak_db": round(20 * np.log10(np.abs(x).max() + 1e-12), 1)}


os.makedirs(OUT, exist_ok=True)
index = {"Env.Arena.Crowd": {"files": [], "sources": []}, "Env.Arena.Cheer": {"files": [], "sources": []}, "Env.Arena.Clap": {"files": [], "sources": []}}
# ---- the murmur
mur_src = os.path.join(AMB, "Ambience_Crowd_03_Loop.wav")
mur = decode(mur_src)
crowd = fade(mur[int(2.0 * SR):int(9.0 * SR)], 1.0, 2.0)
index["Env.Arena.Crowd"]["files"].append(write("Arena_Crowd.wav", level(crowd, -20.0))); index["Env.Arena.Crowd"]["sources"].append(mur_src)
# ---- the cheers: one battle cry from each of NV adult voices
cries = {}
for v in VOX:
    for dp, _, fs in os.walk(v):
        if os.sep + "Kids" + os.sep in dp + os.sep: continue
        for f in fs:
            if f.lower().endswith(".wav") and "_Battle_Cry" in f:
                who = f.split("_Battle_Cry")[0]
                cries.setdefault(who, []).append(os.path.join(dp, f))
voices = sorted(cries)
print("adult voices with battle cries:", len(voices), voices)
assert len(voices) >= NV, voices
for k in range(TAKES):
    pick = rng.choice(len(voices), NV, replace=False)
    parts, srcs = [], []
    for i in pick:
        f = sorted(cries[voices[i]])[int(rng.integers(len(cries[voices[i]])))]
        x = trim(decode(f)); x = x / max(np.abs(x).max(), 1e-9)
        parts.append((float(rng.uniform(0.0, 0.4)), x * 10 ** (rng.uniform(-6, 0) / 20))); srcs.append(f)
    n = int((max(o + len(x) / SR for o, x in parts) + 0.6) * SR)
    mix = np.zeros(n)
    for o, x in parts: s = int(o * SR); mix[s:s + len(x)] += x
    bed = mur[int((3 + 5 * k) * SR):int((3 + 5 * k) * SR) + n]
    bed = fade(bed / max(np.abs(bed).max(), 1e-9) * 0.35, 0.15, 0.6)
    mix = fade(mix + bed, 0.01, 0.5)
    index["Env.Arena.Cheer"]["files"].append(write(f"Arena_Cheer_{k + 1}.wav", level(mix))); index["Env.Arena.Cheer"]["sources"].append(srcs + [mur_src])
# ---- the applause: single claps cut from one person's clapping
clap_src = os.path.join(AMB, "Extra_Claps.wav")
cx = decode(clap_src)
env = np.convolve(np.abs(cx), np.ones(64) / 64, mode="same")
floor = np.percentile(env, 20) + 1e-9
on = np.nonzero((env[1:] > floor * 4) & (env[:-1] <= floor * 4))[0]
claps, last = [], -SR
for o in on:
    if o - last < int(0.15 * SR): continue
    last = o; s = max(o - int(0.005 * SR), 0)
    c = cx[s:s + int(0.11 * SR)]
    if len(c) == int(0.11 * SR): claps.append(fade(c / max(np.abs(c).max(), 1e-9), 0.002, 0.04))
print("single claps cut:", len(claps))
assert len(claps) >= 6, len(claps)
for k in range(TAKES):
    L = 2.4; n = int(L * SR); mix = np.zeros(n + SR)
    for _ in range(NC):
        rate = rng.uniform(3.5, 5.5); t = rng.uniform(0.0, 0.15); g = 10 ** (rng.uniform(-8, 0) / 20)
        while t < L:
            c = claps[int(rng.integers(len(claps)))]
            s = int(t * SR); mix[s:s + len(c)] += c * g * rng.uniform(0.7, 1.0)
            t += 1.0 / rate + rng.normal(0, 0.015)
    mix = mix[:n]
    envl = np.ones(n); envl[:int(0.15 * SR)] = np.linspace(0, 1, int(0.15 * SR)); envl[-int(0.8 * SR):] = np.linspace(1, 0, int(0.8 * SR)) ** 1.5
    index["Env.Arena.Clap"]["files"].append(write(f"Arena_Clap_{k + 1}.wav", level(mix * envl))); index["Env.Arena.Clap"]["sources"].append([clap_src])
json.dump(index, open(os.path.join(OUT, "index.json"), "w", encoding="utf-8"), indent=1)
for key, e in index.items(): print(key, [(f["file"], f["length"], f["rms_db"], f["peak_db"]) for f in e["files"]])
