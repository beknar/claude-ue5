"""PNG sequence -> H.264 MP4 (imageio-ffmpeg's bundled ffmpeg).
Usage: encode_video.py frames_dir out.mp4 [start_frame] [fps]"""
import sys, os, re, subprocess, imageio_ffmpeg
src, out = sys.argv[1], sys.argv[2]
start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
fps = int(sys.argv[4]) if len(sys.argv) > 4 else 30
frames = sorted(f for f in os.listdir(src) if f.endswith(".png"))
m = re.match(r"(.*?)(\d+)\.png$", frames[0]); prefix, digits = m.group(1), len(m.group(2))
cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-framerate", str(fps), "-start_number", str(start),
       "-i", os.path.join(src, f"{prefix}%0{digits}d.png"),
       "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
print(" ".join(cmd)); subprocess.run(cmd, check=True)
n = len(frames) - start
print(f"wrote {out}: {n} frames, {n / fps:.1f} s")
