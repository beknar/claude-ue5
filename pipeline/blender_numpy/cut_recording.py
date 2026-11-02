"""A recording (Game Bar's or ffmpeg's .mp4 of the packaged game) -> a reel's two files: <name>_Showcase.mp4 (1080p, CRF 16,
AAC 192 kbps) and <name>_Showcase_20MB.mp4 (a two-pass encode sized to 18.5 MB with a 128 kbps track), cut from <start> for
<seconds>, the sound raised by one gain for the whole cut so that its peak is at -1.5 dBFS (at most +14 dB; measured with
ffmpeg's volumedetect over the cut), as encode_video.py does for a rendered reel's track. Game Bar's variable frame rate is kept
(its first pass warns of non-monotonic timestamps to the null muxer: harmless).
Usage: cut_recording.py <recording.mp4> <out_dir> <name> [start_s 0] [seconds 60]
Needs imageio-ffmpeg (CLAUDE.md: the amv-maker venv)."""
import sys, os, re, subprocess, imageio_ffmpeg
src, out_dir, name = sys.argv[1], sys.argv[2], sys.argv[3]
start = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
secs = float(sys.argv[5]) if len(sys.argv) > 5 else 60.0
ff = imageio_ffmpeg.get_ffmpeg_exe()
cut = ["-ss", f"{start:g}", "-t", f"{secs:g}", "-i", src]
r = subprocess.run([ff] + cut + ["-vn", "-af", "volumedetect", "-f", "null", "NUL" if os.name == "nt" else "/dev/null"], capture_output=True, text=True).stderr
mx = re.search(r"max_volume: (-?[\d.]+) dB", r); mean = re.search(r"mean_volume: (-?[\d.]+) dB", r)
af = []
if mx:
    gain = min(-1.5 - float(mx.group(1)), 14.0)
    af = ["-af", f"volume={gain:.2f}dB"]
    print(f"sound: mean {mean.group(1) if mean else '?'} dB, peak {mx.group(1)} dB, gain {gain:+.1f} dB")
else:
    print("sound: none")
vf = ["-vf", "scale=1920:1080:flags=lanczos", "-pix_fmt", "yuv420p"]
full = os.path.join(out_dir, f"{name}_Showcase.mp4"); small = os.path.join(out_dir, f"{name}_Showcase_20MB.mp4")
aud = lambda k: (af + ["-c:a", "aac", "-b:a", k]) if mx else ["-an"]
subprocess.run([ff, "-y", "-loglevel", "error"] + cut + vf + ["-c:v", "libx264", "-preset", "slow", "-crf", "16"] + aud("192k") + ["-movflags", "+faststart", full], check=True)
kbps = int(18.5 * 8 * 1024 * 1024 / secs / 1000) - (128 if mx else 0)          # (two-pass lands within a few % of it; 20 MB the limit)
log = os.path.join(os.path.dirname(os.path.abspath(small)), "ff2pass")
v = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{kbps}k", "-passlogfile", log]
subprocess.run([ff, "-y", "-loglevel", "error"] + cut + vf + v + ["-pass", "1", "-an", "-f", "null", "NUL" if os.name == "nt" else "/dev/null"], check=True)
subprocess.run([ff, "-y", "-loglevel", "error"] + cut + vf + v + ["-pass", "2"] + aud("128k") + ["-movflags", "+faststart", small], check=True)
for f in os.listdir(os.path.dirname(log)):
    if f.startswith("ff2pass"): os.remove(os.path.join(os.path.dirname(log), f))
for f in (full, small):
    r = subprocess.run([ff, "-i", f], capture_output=True, text=True).stderr
    d = re.search(r"Duration: ([\d:.]+)", r); vv = re.search(r"Video: .*?(\d{3,5}x\d{3,5})", r)
    print(os.path.basename(f), d.group(1) if d else "?", vv.group(1) if vv else "?", f"{os.path.getsize(f) / 1048576:.1f} MB", "audio" if "Audio:" in r else "no audio")
