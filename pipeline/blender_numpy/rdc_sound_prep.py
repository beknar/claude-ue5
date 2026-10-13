"""random_dungeoncombat_level: prepares the game's sounds from the local sound library.

Reads claude_ue5/SourceArt/random_dungeon_combat/sounds.json (which library files are played for which occasion) and
writes each chosen file as 44.1 kHz 16 bit WAV into claude_ue5/SourceArt/random_dungeon_combat/audio:
  * mono (a sound placed in the world has to be mono to be heard from its direction), stereo only for "stereo" sets
  * one-shots: the silence before and after is trimmed, "max_len" cuts a long tail, short fades at both ends
  * "cut": [start, length] takes a part of a long file, "fade": [in, out] seconds
  * levelled: the sounding part of every file of a set gets the set's "level" (RMS, dBFS), with the peak kept under
    -1 dBFS; how loud a set is in the game is then the set's "volume" alone
  * loops ("loop") are left whole, so they still loop
and audio/index.json (the files of each set, with their lengths and sources), which pipeline/unreal/797 reads.
The library and the converted files are licensed sound packs: neither is in the repository.

Usage (a Python with numpy and imageio_ffmpeg):  rdc_sound_prep.py [sounds.json] [out_dir]
"""
import sys, os, re, json, wave, subprocess
import numpy as np, imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", "..", "claude_ue5", "SourceArt", "random_dungeon_combat"))
MANIFEST = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SRC, "sounds.json")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(SRC, "audio")
SR = 44100
FF = imageio_ffmpeg.get_ffmpeg_exe()


def natural(s):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", s)]


def decode(path, channels):
    r = subprocess.run([FF, "-v", "error", "-i", path, "-ac", str(channels), "-ar", str(SR), "-f", "f32le", "-"], capture_output=True)
    if r.returncode != 0: raise RuntimeError("ffmpeg: " + r.stderr.decode(errors="replace")[:200])
    return np.frombuffer(r.stdout, dtype=np.float32).reshape(-1, channels).astype(np.float64)


def envelope(x):
    """peak of each 5 ms window (all channels)"""
    a = np.abs(x).max(axis=1); n = int(SR * 0.005)
    return a[:len(a) // n * n].reshape(-1, n).max(axis=1), n


def trim(x):
    env, n = envelope(x)
    if len(env) == 0 or env.max() <= 0: return x
    on = np.nonzero(env > env.max() * 0.02)[0]
    a = max(0, on[0] * n - int(SR * 0.004)); b = min(len(x), (on[-1] + 1) * n + int(SR * 0.04))
    return x[a:b]


def fade(x, t_in, t_out):
    x = x.copy()
    n = min(int(SR * t_in), len(x) // 2)
    if n > 0: x[:n] *= np.linspace(0.0, 1.0, n)[:, None]
    n = min(int(SR * t_out), len(x) // 2)
    if n > 0: x[-n:] *= (np.cos(np.linspace(0.0, np.pi, n)) * 0.5 + 0.5)[:, None]
    return x


def level(x, target_db):
    env, n = envelope(x)
    if len(env) == 0 or env.max() <= 0: return x, 0.0
    loud = np.repeat(env > env.max() * 0.1, n)
    part = x[:len(loud)][loud]
    rms = np.sqrt((part ** 2).mean()) if len(part) else 1e-9
    gain = 10 ** (target_db / 20.0) / max(rms, 1e-9)
    gain = min(gain, 10 ** (-1.0 / 20.0) / np.abs(x).max())      # the peak stays under -1 dBFS
    return x * gain, 20 * np.log10(gain)


def write(path, x):
    pcm = np.clip(np.round(x * 32767.0), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(x.shape[1]); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


def main():
    man = json.load(open(MANIFEST, encoding="utf-8"))
    root = man["root"]
    os.makedirs(OUT, exist_ok=True)
    for f in os.listdir(OUT):
        if f.endswith(".wav"): os.remove(os.path.join(OUT, f))
    listing = {}
    def files(pack):
        if pack not in listing:
            base = os.path.join(root, man["packs"][pack]); out = []
            for d, _, fs in os.walk(base):
                for f in fs:
                    if f.lower().endswith((".wav", ".ogg", ".flac")): out.append(os.path.relpath(os.path.join(d, f), base).replace("\\", "/"))
            listing[pack] = (base, sorted(out, key=natural))
        return listing[pack]
    index = {}; missing = []
    for key, s in man["sets"].items():
        ch = 2 if s.get("stereo") else 1
        loop = bool(s.get("loop"))
        cand = []
        for pack, rx in s["from"]:
            base, fs = files(pack)
            got = [f for f in fs if re.search(rx, f)]
            if not got: missing.append("%s: nothing in '%s' matches %s" % (key, pack, rx))
            cand += [(pack, f, os.path.join(base, f)) for f in got]
        clips = []
        for pack, rel, path in cand:
            x = decode(path, ch)
            if "cut" in s: x = x[int(SR * s["cut"][0]):int(SR * (s["cut"][0] + s["cut"][1]))]
            if not loop and s.get("trim", True): x = trim(x)
            if "max_len" in s and len(x) > SR * s["max_len"]: x = fade(x[:int(SR * s["max_len"])], 0.0, min(0.12, s["max_len"] * 0.3))
            if len(x) < SR * 0.03: continue
            clips.append((pack, rel, x))
        pick = s.get("pick", "all")
        if pick.startswith(("shortest:", "longest:")):
            k = int(pick.split(":")[1]); clips.sort(key=lambda c: len(c[2]), reverse=pick.startswith("longest"))
            clips = sorted(clips[:k], key=lambda c: natural(c[1]))
        mx = s.get("max", len(clips))
        if len(clips) > mx: clips = [clips[int(round(i * (len(clips) - 1) / float(mx - 1)))] for i in range(mx)] if mx > 1 else clips[:1]
        entry = {"files": [], "seconds": [], "source": [], "gain_db": []}
        for n, (pack, rel, x) in enumerate(clips):
            if not loop:
                fi, fo = s.get("fade", [0.003, 0.02]); x = fade(x, fi, fo)
            x, g = level(x, s.get("level", -20.0))
            name = "%s_%02d.wav" % (key.replace(".", "_"), n + 1)
            write(os.path.join(OUT, name), x)
            entry["files"].append(name); entry["seconds"].append(round(len(x) / SR, 3)); entry["source"].append(pack + ": " + rel); entry["gain_db"].append(round(float(g), 1))
        index[key] = entry
        sec = entry["seconds"]
        print("%-22s %2d files  %5.2f - %5.2f s  gain %+5.1f .. %+5.1f dB%s" % (key, len(sec), min(sec) if sec else 0, max(sec) if sec else 0,
              min(entry["gain_db"]) if sec else 0, max(entry["gain_db"]) if sec else 0, "  LOOP" if loop else ""))
        if not sec: missing.append(key + ": no sound at all")
    json.dump(index, open(os.path.join(OUT, "index.json"), "w", encoding="utf-8"), indent=1)
    total = sum(len(e["files"]) for e in index.values())
    size = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT) if f.endswith(".wav"))
    print("RDCSOUND %d sets, %d files, %.1f MB -> %s" % (len(index), total, size / 1048576.0, OUT))
    for m in missing: print("RDCSOUND MISSING", m)


if __name__ == "__main__":
    main()
