"""Decode a saved MCP capture result (JSON with base64 image data) into an image file.
Usage: decode_capture.py (in.txt | latest) out.png [max_px] [crop x0 y0 x1 y1 (fractions)]"""
import sys, json, base64, re, io, glob, os
src, out = sys.argv[1], sys.argv[2]
if src == "latest":
    files = glob.glob(os.path.expanduser(r"~\.claude\projects\E--code-claude-ue5\*\tool-results\mcp-unreal-mcp-call_tool-*.txt"))
    src = max(files, key=os.path.getmtime)
mx = int(sys.argv[3]) if len(sys.argv) > 3 else 1600
txt = open(src, encoding="utf-8").read()
m = re.search(r'"data"\s*:\s*"([A-Za-z0-9+/=]+)"', txt)
raw = base64.b64decode(m.group(1))
from PIL import Image
im = Image.open(io.BytesIO(raw))
print("full size", im.size)
if len(sys.argv) > 7:
    x0, y0, x1, y1 = map(float, sys.argv[4:8]); W, H = im.size
    im = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
im.thumbnail((mx, mx)); im.save(out); print("saved", out, im.size)
