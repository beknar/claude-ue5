"""The reel of 2026-11-18 (RD/RDReel15.cpp, record_mistward_autoplay.ps1 -Reel15): its scenes cut out of the Game Bar recording,
joined, scaled to 1080p, with the narration of each scene spoken by Piper (the Rhasspy project's neural text-to-speech, installed
on E: by the user's go-ahead of 2026-11-18: E:/tools/piper/venv, its voices in E:/tools/piper/voices) or a Windows voice, laid over
it, the game's own sound ducked under the voice; written as <name>_Showcase.mp4 and <name>_Showcase_20MB.mp4 (20 MB or less, two
passes).

Usage: reel15_cut.py <gamebar.mp4> <out dir> <name> [--engine piper|sapi] [--model <voice.onnx>] [--scale 1.0] [--voice ...] [--rate 1] [--keep <dir>]
  beside the video: <video>.go.txt (seconds from the video's start to the go) and <video>.timeline.txt (the game's done file:
  "<s from the go>|scene|<name>|<title>|<line>|<narration>", "<s>|end|<name>", "<s>|note|...")
  --engine  piper (the default) or sapi (the Windows voices)
  --piper   the Python with piper-tts (E:/tools/piper/venv/Scripts/python.exe); --model its voice (en_US-ryan-high, from
            huggingface.co/rhasspy/piper-voices by `python -m piper.download_voices`); --scale its length scale (1: the voice's
            own pace; a line too long for its scene is spoken faster, to 0.8 at most)
  --voice   (sapi) an installed System.Speech voice (this machine: Microsoft David Desktop, Microsoft Zira Desktop)
  --rate    the voice's rate (-10 to 10); a line too long for its scene is spoken faster, to 5 at most, then left to run over
            the scene's end into the next by up to a second (said in the printout)
  --novoice no narration: the game's own sound alone (through the same level and limiter)
  --no20mb  the full Showcase only
  --keep    the narration's .wav files and the joined sound are kept there (else a folder beside the output)
  --blur    x:y:w:h of the source picture blurred in place ("none": nothing): a system overlay's strip recorded with the game
            (2026-11-18's take: "FPS | GPU | CPU | LAT" over the top right corner, Game Bar's or the graphics driver's); the
            default is that strip's place on a 2560 x 1440 recording, scaled to the video's size
Nobody here hears the result: the script prints each line's length against its scene, and the mix's levels (volumedetect)
with and without the voice, as the measure of it."""
import sys, os, re, wave, subprocess, json, math, argparse, imageio_ffmpeg

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("out"); ap.add_argument("name")
ap.add_argument("--voice", default="Microsoft David Desktop"); ap.add_argument("--rate", type=int, default=1)
ap.add_argument("--keep", default=""); ap.add_argument("--blur", default="auto")
ap.add_argument("--novoice", action="store_true"); ap.add_argument("--no20mb", action="store_true")
ap.add_argument("--engine", default="piper", choices=["piper", "sapi"])
ap.add_argument("--piper", default=r"E:\tools\piper\venv\Scripts\python.exe")
ap.add_argument("--model", default=r"E:\tools\piper\voices\en_US-ryan-high.onnx"); ap.add_argument("--scale", type=float, default=1.0)
a = ap.parse_args()
ff = imageio_ffmpeg.get_ffmpeg_exe()
os.makedirs(a.out, exist_ok=True)
work = a.keep or os.path.join(a.out, a.name + "_narration")
os.makedirs(work, exist_ok=True)
go = float(open(a.video + ".go.txt", encoding="utf-8").read().strip().replace(",", ""))
lines = [l.rstrip("\n") for l in open(a.video + ".timeline.txt", encoding="utf-8") if l.strip()]

# ---- the scenes: start, end (from the go), caption and narration
scenes, open_ = [], {}
for l in lines:
    p = l.split("|")
    t = float(p[0])
    if p[1] == "scene":
        open_[p[2]] = {"name": p[2], "t0": t, "title": p[3], "line": p[4], "say": p[5] if len(p) > 5 else ""}
    elif p[1] == "end" and p[2] in open_:
        s = open_.pop(p[2]); s["t1"] = t; scenes.append(s)
scenes.sort(key=lambda s: s["t0"])
print(f"{len(scenes)} scenes, the go at {go:.2f} s into the video")

# ---- the narration, a .wav a scene (Piper, or System.Speech through PowerShell), each fitted to its scene
PIPER = r"""
import sys, json, wave
from piper import PiperVoice, SynthesisConfig
v = PiperVoice.load(sys.argv[1])
for text, scale, path in json.load(open(sys.argv[2], encoding="utf-8")):
    with wave.open(path, "wb") as w: v.synthesize_wav(text, w, syn_config=SynthesisConfig(length_scale=scale))
"""
def speak(jobs):
    """jobs: [(text, rate or length scale, path)]: one process for all"""
    if a.engine == "piper":
        jf = os.path.join(work, "piper_jobs.json"); json.dump(jobs, open(jf, "w", encoding="utf-8"))
        sf = os.path.join(work, "piper_say.py"); open(sf, "w", encoding="utf-8").write(PIPER)
        subprocess.run([a.piper, sf, a.model, jf], check=True); return
    ps = ["Add-Type -AssemblyName System.Speech", "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer", f"$s.SelectVoice('{a.voice}')"]
    for text, rate, path in jobs:
        ps += [f"$s.Rate = {rate}", f"$s.SetOutputToWaveFile('{path}')", "$s.Speak('" + text.replace("'", "''") + "')", "$s.SetOutputToNull()"]
    ps.append("$s.Dispose()")
    subprocess.run(["powershell", "-NoProfile", "-Command", "; ".join(ps)], check=True)
def secs(path):
    w = wave.open(path, "rb"); return w.getnframes() / w.getframerate()
LEAD = 0.6          # (the voice begins this long into its scene)
for i, s in enumerate(scenes):
    s["wav"] = os.path.join(work, f"say_{i:02d}.wav"); s["rate"] = a.scale if a.engine == "piper" else a.rate
if a.novoice:
    for s in scenes: s["say"] = ""
speak([(s["say"], s["rate"], s["wav"]) for s in scenes if s["say"]]) if any(s["say"] for s in scenes) else None
for _ in range(6):
    redo = []
    for s in scenes:
        if not s["say"]: continue
        room = (s["t1"] - s["t0"]) - LEAD - 0.4
        if secs(s["wav"]) <= room: continue
        if a.engine == "piper" and s["rate"] > 0.81: s["rate"] = round(s["rate"] - 0.05, 2); redo.append((s["say"], s["rate"], s["wav"]))
        elif a.engine == "sapi" and s["rate"] < 5: s["rate"] += 1; redo.append((s["say"], s["rate"], s["wav"]))
    if not redo: break
    speak(redo)

# ---- the cut: each scene's stretch of the video (0.15 s in from each end), a short fade in and out, joined; the narration laid at
# each scene's start in the joined time
T = 0.0
vf, af, inputs = [], [], ["-i", a.video]
r_ = subprocess.run([ff, "-hide_banner", "-i", a.video], capture_output=True, text=True).stderr
m_ = re.search(r"Video: .*?(\d{3,5})x(\d{3,5})", r_); SW, SH = (int(m_.group(1)), int(m_.group(2))) if m_ else (2560, 1440)
blur = None
if a.blur == "auto": blur = (round(2110 * SW / 2560), 0, round(450 * SW / 2560), round(44 * SH / 1440))
elif a.blur != "none": blur = tuple(int(x) for x in a.blur.split(":"))
n = len(scenes)
pre = []
if blur:
    bx, by, bw, bh = blur; bw = min(bw, SW - bx)
    pre.append(f"[0:v]split=2[base][cut];[cut]crop={bw}:{bh}:{bx}:{by},boxblur=10:3:5:3[bl];[base][bl]overlay={bx}:{by},split={n}" + "".join(f"[s{i}]" for i in range(n)))
else:
    pre.append("[0:v]split=" + str(n) + "".join(f"[s{i}]" for i in range(n)))
for i, s in enumerate(scenes):
    v0, v1 = go + s["t0"] + 0.15, go + s["t1"] - 0.15
    d = v1 - v0; s["out0"] = T; s["dur"] = d
    vf.append(f"[s{i}]trim=start={v0:.3f}:end={v1:.3f},setpts=PTS-STARTPTS,fps=30,scale=1920:1080:flags=lanczos,"
              f"fade=t=in:st=0:d=0.25,fade=t=out:st={max(d - 0.25, 0):.3f}:d=0.25[v{i}]")
    af.append(f"[0:a]atrim=start={v0:.3f}:end={v1:.3f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.25,afade=t=out:st={max(d - 0.25, 0):.3f}:d=0.25[a{i}]")
    T += d
fc = pre + vf + af + ["".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vcat][game]"]
vo = []
for i, s in enumerate(scenes):
    if not s["say"]: continue
    inputs += ["-i", s["wav"]]; k = len(inputs) // 2 - 1
    ms = int((s["out0"] + LEAD) * 1000)
    fc.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[n{i}]")
    vo.append(f"[n{i}]")
    s["say_s"] = round(secs(s["wav"]), 2)
if vo:
    fc.append("".join(vo) + f"amix=inputs={len(vo)}:normalize=0:duration=longest,apad,atrim=end={T:.3f},volume=2.2[vo]")
    fc.append("[vo]asplit=2[vo1][vo2]")
    fc.append("[game]aresample=48000,volume=1.6[g]")
    fc.append("[g][vo1]sidechaincompress=threshold=0.015:ratio=9:attack=20:release=450[duck]")
    fc.append("[duck][vo2]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[mix]")
else:
    fc.append("[game]aresample=48000,volume=1.6,alimiter=limit=0.95[mix]")
for s in scenes:
    room = s["dur"] - LEAD
    print(f"  {s['name']:<16} {s['dur']:5.1f} s  voice {s.get('say_s', 0):4.1f} s at {'length scale' if a.engine == 'piper' else 'rate'} {s['rate']}{'  RUNS OVER' if s.get('say_s', 0) > room else ''}")
graph = os.path.join(work, "graph.txt"); open(graph, "w", encoding="utf-8").write(";\n".join(fc))
full = os.path.join(a.out, f"{a.name}_Showcase.mp4")
small = os.path.join(a.out, f"{a.name}_Showcase_20MB.mp4")
mixwav = os.path.join(work, "mix.wav")
# (the joined picture and sound once, as an intermediate of high quality; the two deliveries from it)
inter = os.path.join(work, "joined.mkv")
subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error"] + inputs + ["-filter_complex_script", graph, "-map", "[vcat]", "-map", "[mix]",
                "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", inter], check=True)
subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-i", inter, "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", full], check=True)
if a.no20mb: small = None
kb = int((19.3 * 8 * 1024 * 1024 / 1000) / T - 96)          # (19.3 MB over its length, the sound's 96 kb/s taken off)
log = os.path.join(work, "ff2pass")
if small:
  v2 = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{kb}k", "-pix_fmt", "yuv420p", "-passlogfile", log]
  subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-i", inter] + v2 + ["-pass", "1", "-an", "-f", "null", "NUL"], check=True)
  subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-i", inter] + v2 + ["-pass", "2", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", small], check=True)
for f in os.listdir(work):
    if f.startswith("ff2pass"): os.remove(os.path.join(work, f))
# ---- the measure: the mix's level where the voice speaks and where it does not, and the files
def level(path, ss, t):
    r = subprocess.run([ff, "-hide_banner", "-ss", f"{ss:.2f}", "-t", f"{t:.2f}", "-i", path, "-vn", "-af", "volumedetect", "-f", "null", "NUL"], capture_output=True, text=True).stderr
    m = re.search(r"mean_volume: ([-\d.]+) dB", r); x = re.search(r"max_volume: ([-\d.]+) dB", r)
    return (float(m.group(1)) if m else None, float(x.group(1)) if x else None)
spoke = [level(full, s["out0"] + LEAD + 0.3, max(s.get("say_s", 0) - 0.6, 0.5)) for s in scenes if s.get("say_s")]
quiet = [level(full, s["out0"] + LEAD + s["say_s"] + 0.4, 1.0) for s in scenes if s.get("say_s") and s["dur"] - LEAD - s["say_s"] > 1.6]
print(f"mix: mean {sum(x[0] for x in spoke) / len(spoke):.1f} dB while the voice speaks (peak {max(x[1] for x in spoke):.1f}),"
      f" {sum(x[0] for x in quiet) / max(len(quiet), 1):.1f} dB in the gaps ({len(quiet)} gaps)" if spoke else "no narration")
if not spoke: print("game sound: mean %.1f dB, peak %.1f dB" % level(full, 0, T))
for f in (full, small) if small else (full,):
    r = subprocess.run([ff, "-hide_banner", "-i", f], capture_output=True, text=True).stderr
    d = re.search(r"Duration: ([\d:.]+)", r); v = re.search(r"Video: .*?(\d{3,5})x(\d{3,5})", r)
    print(f"wrote {f}: {os.path.getsize(f) / 1048576:.1f} MB, {d.group(1) if d else '?'}, {v.group(1) + 'x' + v.group(2) if v else '?'}")
json.dump([{k: v for k, v in s.items() if k != "wav"} for s in scenes], open(os.path.join(work, "scenes.json"), "w", encoding="utf-8"), indent=1)
