"""The wilds' map inside its scroll (the list of 2026-11-12: "the wilderness map is a square with a scroll overlay on it, with the
square showing in the gaps of the irregular scroll edges. map square should not show up outside of the scroll overlay"),
measured in two pictures of the same screen with the map moved far between them (888 list12's l12_map_cut and l12_map_cut2):
the pixels where the scroll's edge picture is neither its parchment nor its open middle (past the torn outline, in the worn
holes, between the threads) show only the backdrop and must not change; the map's own pixels must.

    python l12_scroll_check.py <picture 1> <picture 2> <mapc_scroll_edge.png> <888's test json> [frame name]

The edge's place on the screen comes from the map's frame in the test's record (its sheet, A and B) and ARDHUD::DrawWildMap's
insets (11.5 % and 5.4 % of the edge's picture). Needs numpy and Pillow (CLAUDE.md: the amv-maker venv)."""
import sys, json
from collections import deque
import numpy as np
from PIL import Image
P1, P2, EDGE, REC = sys.argv[1:5]
NAME = sys.argv[5] if len(sys.argv) > 5 else "l12_map_cut"
SIDE, TOPB = 0.115, 0.054                       # (RDWildHUD.cpp's insets: change both together)
f = json.load(open(REC, encoding="utf-8"))["frames"][NAME]
(ax, ay), (bx, by) = f["a"], f["b"]
pic_w = (bx - ax) / (1.0 - 2.0 * SIDE); pic_h = (by - ay) / (1.0 - 2.0 * TOPB)
ix, iy = ax - SIDE * pic_w, ay - TOPB * pic_h
e = Image.open(EDGE)
N = e.size[0]
ea = np.asarray(e)[..., 3].astype(np.float32) / 255.0
mid = np.zeros((N, N), bool); q = deque([(N // 2, N // 2)]); mid[N // 2, N // 2] = True
while q:
    y0, x0 = q.popleft()
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        y1, x1 = y0 + dy, x0 + dx
        if 0 <= y1 < N and 0 <= x1 < N and not mid[y1, x1] and ea[y1, x1] < 0.9: mid[y1, x1] = True; q.append((y1, x1))
a1 = np.asarray(Image.open(P1).convert("RGB")).astype(np.float32); a2 = np.asarray(Image.open(P2).convert("RGB")).astype(np.float32)
H, W = a1.shape[:2]
diff = np.abs(a1 - a2).mean(axis=2)
gap, inside = [], []
for sy in range(int(max(0, iy)), int(min(H, iy + pic_h))):
    v = int((sy - iy) / pic_h * N)
    if not 0 <= v < N: continue
    for sx in range(int(max(0, ix)), int(min(W, ix + pic_w))):
        u = int((sx - ix) / pic_w * N)
        if not 0 <= u < N: continue
        if ea[v, u] < 0.05 and not mid[v, u]: gap.append(diff[sy, sx])         # (fully clear of the edge, outside its middle)
        elif mid[v, u] and ax + 4 <= sx <= bx - 4 and ay + 4 <= sy <= by - 4: inside.append(diff[sy, sx])
gap, inside = np.array(gap), np.array(inside)
print(json.dumps({"gap_pixels": int(gap.size), "gap_changed_mean": round(float(gap.mean()), 2) if gap.size else None,
                  "gap_changed_over_12": round(float((gap > 12).mean()), 4) if gap.size else None,
                  "map_pixels": int(inside.size), "map_changed_mean": round(float(inside.mean()), 2) if inside.size else None}))
