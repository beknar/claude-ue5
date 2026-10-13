"""PNG sequence -> H.264 MP4 (imageio-ffmpeg's bundled ffmpeg), optionally with a sound track.
Usage: encode_video.py frames_dir out.mp4 [start_frame] [fps] [track.wav] [video_kbps]
  track.wav    (16 bit) is added as AAC, raised by one gain for the whole of it so that its peak is at -1.5 dBFS
               (the Movie Render Queue's .wav of a game's own mix is as quiet or loud as the game)
  video_kbps   two-pass encode at that video bitrate instead of CRF 16 (a file of a wanted size: 45 s at 3300 kbps
               with a 128 kbps track is about 18.5 MB)"""
import sys, os, re, array, math, wave, subprocess, imageio_ffmpeg
src, out = sys.argv[1], sys.argv[2]
start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
fps = int(sys.argv[4]) if len(sys.argv) > 4 else 30
track = sys.argv[5] if len(sys.argv) > 5 and sys.argv[5] not in ("", "-") else None
kbps = int(sys.argv[6]) if len(sys.argv) > 6 else 0
frames = sorted(f for f in os.listdir(src) if f.endswith(".png"))
m = re.match(r"(.*?)(\d+)\.png$", frames[0]); prefix, digits = m.group(1), len(m.group(2))
ff = imageio_ffmpeg.get_ffmpeg_exe()
vin = ["-framerate", str(fps), "-start_number", str(start), "-i", os.path.join(src, f"{prefix}%0{digits}d.png")]
ain, aout = [], ["-an"]
if track:
    w = wave.open(track, "rb"); assert w.getsampwidth() == 2, "a 16 bit .wav is expected"
    s = array.array("h", w.readframes(w.getnframes())); peak = max(max(s), -min(s), 1) / 32768.0
    gain = min(-1.5 - 20 * math.log10(peak), 14.0)
    print(f"track: {w.getnframes() / w.getframerate():.2f} s, peak {20 * math.log10(peak):.1f} dBFS, gain {gain:+.1f} dB")
    ain = ["-i", track]; aout = ["-af", f"volume={gain:.2f}dB", "-c:a", "aac", "-b:a", "128k" if kbps else "192k", "-shortest"]
if kbps:
    log = os.path.join(os.path.dirname(os.path.abspath(out)), "ff2pass")
    video = ["-c:v", "libx264", "-preset", "slow", "-b:v", f"{kbps}k", "-pix_fmt", "yuv420p", "-passlogfile", log]
    subprocess.run([ff, "-y"] + vin + video + ["-pass", "1", "-an", "-f", "null", "NUL" if os.name == "nt" else "/dev/null"], check=True, capture_output=True)
    subprocess.run([ff, "-y"] + vin + ain + video + ["-pass", "2"] + aout + ["-movflags", "+faststart", out], check=True, capture_output=True)
    for f in os.listdir(os.path.dirname(log)):
        if f.startswith("ff2pass"): os.remove(os.path.join(os.path.dirname(log), f))
else:
    cmd = [ff, "-y"] + vin + ain + ["-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p"] + aout + ["-movflags", "+faststart", out]
    print(" ".join(cmd)); subprocess.run(cmd, check=True, capture_output=bool(track))
n = len(frames) - start
print(f"wrote {out}: {n} frames, {n / fps:.1f} s, {os.path.getsize(out) / 1048576:.1f} MB" + (", with sound" if track else ""))
