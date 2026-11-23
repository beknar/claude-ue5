"""Write the packaged game's measured frame rates into docs/performance.md (the list of 2026-11-22).

Usage: python perf_doc.py <docs/performance.md> "<heading>" <perf file> [<perf file> ...]

Each perf file is RD/RDList16.cpp's -RDPerf output, one leg after another (the wilds', the castle's, a dungeon's): each leg's
"perf|info|<WxH>|<GPU>|<when>|<overall quality>|<screen %>|<map>|<quality groups>", its "place|..." lines (where each place stood, for
the later runs' replay), a line a place "perf|<kind>|<name>|<hour>|<fps>|<p95 ms>|<p99 ms>|<game ms>|<draw ms>|<rhi ms>|<gpu ms>|
<frames>|<x m>|<y m>|<biome there>|<metres run>" (or "perf|<kind>|<name>|<hour>|skipped|<why>"), then "perf|done". The section under <heading> is written anew (one table per resolution); the
rest of the page is kept. Under an AFTER heading, each row also gives the change against the BEFORE section's row of the same place
and resolution, when the page has one.
"""
import os
import re
import sys
from datetime import datetime


def read(path):
    info, rows = {}, []
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            p = line.rstrip("\n").split("|")
            if len(p) < 2 or p[0] != "perf":
                continue
            if p[1] == "info":
                # (one info line a leg: the first one's resolution, GPU, time and quality are the run's)
                if not info:
                    info = {"res": p[2], "gpu": p[3] if len(p) > 3 else "", "when": p[4] if len(p) > 4 else "",
                            "quality": p[5] if len(p) > 5 else "?", "sp": p[6] if len(p) > 6 else "?", "groups": p[8] if len(p) > 8 else ""}
                info["legs"] = info.get("legs", 0) + 1
            elif p[1] == "done":
                info["done"] = info.get("done", 0) + 1
            elif len(p) >= 6 and p[4] == "skipped":
                rows.append({"kind": p[1], "name": p[2], "hour": float(p[3]), "skipped": p[5]})
            elif len(p) >= 16:
                rows.append({"kind": p[1], "name": p[2], "hour": float(p[3]), "fps": float(p[4]), "p95": float(p[5]), "p99": float(p[6]),
                             "game": float(p[7]), "draw": float(p[8]), "rhi": float(p[9]), "gpu": float(p[10]), "frames": int(p[11]),
                             "x": float(p[12]), "y": float(p[13]), "biome": p[14], "run": float(p[15])})
    return info, rows


def place(r):
    h = "noon" if r["hour"] == 12 else "midnight" if r["hour"] == 0 else f"{r['hour']:.0f}:00"
    k = r["kind"]
    if k in ("square", "street"):
        return f"{r['name']}: {k}, {h}"
    if k == "run":
        return f"{r['name']}: running"
    if k == "hall":
        return f"{r['name']}: first hall"
    return r["name"]


def before_rows(text):
    """the BEFORE section's fps per (resolution, place), from its tables"""
    out = {}
    m = re.search(r"^## BEFORE[^\n]*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        return out
    res = None
    for line in m.group(1).splitlines():
        h = re.match(r"^### (\d+x\d+)", line)
        if h:
            res = h.group(1)
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if res and len(c) >= 3 and re.match(r"^[\d.]+$", c[1]):
            out[(res, c[0])] = float(c[1])
    return out


def section(heading, files, before):
    lines = [f"## {heading}", ""]
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines += [f"Written {stamp} from the Shipping package's `-RDPerf` run (`pipeline/perf_mistward.ps1`, `RD/RDList16.cpp`), the editor closed, full screen: each city's square and a street about 100 m off it at noon and at midnight; each biome at its nearest site to Brokenspire at noon, standing, then running 30 s from there; the castle's and Heaven's fortress's first hall. Each standing place settled 20 s after the world round her was built, then measured until 15 s and 300 frames had passed (at most 45 s), clear weather, her HUD hidden, facing the longest clear line from her eyes. FPS is the mean over the frames; p95 and p99 are the 95th and 99th percentile frame times in ms; the thread times are the engine's own (stat unit's game, draw, RHI and GPU) averaged over the frames (0 where the build does not keep them). A biome whose name differs from the one under her feet was measured where the put-down found ground.", ""]
    for path in files:
        info, rows = read(path)
        res = info.get("res", "?")
        unfinished = "" if info.get("done", 0) >= info.get("legs", 1) else " (a leg did not finish: the places after its last row were not measured)"
        grp = f" (by group: {info['groups']})" if info.get("groups") else ""
        lines += [f"### {res}", "", f"Measured {info.get('when', '?')} on {info.get('gpu', '?')}, overall quality level {info.get('quality', '?')} (0 low to 3 epic){grp}, screen percentage {info.get('sp', '?')}, vertical sync off and no frame cap{unfinished}.", ""]
        after = bool(before)
        head = "| Place | FPS | p95 ms | p99 ms | Game ms | Draw ms | RHI ms | GPU ms | Frames | Where (km) | Biome there |" + (" Change |" if after else "")
        lines += [head, "|" + "---|" * (head.count("|") - 1)]
        for r in rows:
            if "skipped" in r:
                lines.append(f"| {place(r)} | skipped: {r['skipped']} |" + " |" * (10 if after else 9))
                continue
            ch = ""
            if after:
                b = before.get((res, place(r)))
                ch = f" {100.0 * (r['fps'] - b) / b:+.0f} % |" if b else " - |"
            where = f"{r['x'] / 1000:.1f}, {r['y'] / 1000:.1f}" + (f" ({r['run']:.0f} m run)" if r["kind"] == "run" else "")
            lines.append(f"| {place(r)} | {r['fps']:.1f} | {r['p95']:.1f} | {r['p99']:.1f} | {r['game']:.1f} | {r['draw']:.1f} | {r['rhi']:.1f} | {r['gpu']:.1f} | {r['frames']} | {where} | {r['biome']} |{ch}")
        lines.append("")
    return "\n".join(lines)


def main():
    doc, heading, files = sys.argv[1], sys.argv[2], sys.argv[3:]
    text = open(doc, encoding="utf-8").read() if os.path.exists(doc) else "# Performance\n\nThe packaged game's frame rate in every city and every biome, measured before and after the list of 2026-11-22 ([improvements16.txt](improvements16.txt)).\n\n"
    before = before_rows(text) if heading.upper().startswith("AFTER") else {}
    new = section(heading, files, before)
    # (the section of exactly this heading (not one that only starts with it); the new text put in as it is, not as a pattern)
    pat = re.compile(r"^## " + re.escape(heading) + r"[ \t]*\n.*?(?=^## |\Z)", re.S | re.M)
    text = pat.sub(lambda m: new + "\n", text) if pat.search(text) else text.rstrip("\n") + "\n\n" + new + "\n"
    with open(doc, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("perf_doc: wrote", heading, "into", doc)


if __name__ == "__main__":
    main()
