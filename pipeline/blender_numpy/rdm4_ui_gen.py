"""Generate random_dungeonmagic_level4's interface art on an InvokeAI server (a batch on its queue).

    python rdm4_ui_gen.py <ui_art.json> <out_dir> [--only a,b] [--model NAME] [--seeds N] [--tag T]

Reads the elements of ui_art.json (prompt + its kind's style + the common style + backdrop, the element's
own backdrop if it has one; size), queues `seeds` pictures of each
with FLUX (InvokeAI's own flux_model_loader -> flux_text_encoder -> flux_denoise -> flux_vae_decode graph),
waits for them and downloads them to <out_dir>/raw/<element>_<tag>_<seed>.png, with a line per picture in
<out_dir>/raw/manifest.json (element, model, seed, InvokeAI image name, seconds). A picture already
downloaded is not asked for again. The pictures also land on the server's board named in ui_art.json.
Seeds come from the element's name, so a run makes the same pictures again. No dependencies beyond
the standard library.
"""
import json, os, sys, time, zlib, urllib.request, urllib.parse

args = sys.argv[1:]
def opt(name, default=None):
    if name in args:
        i = args.index(name); v = args[i + 1]; del args[i:i + 2]; return v
    return default
ONLY = opt("--only"); MODEL = opt("--model"); SEEDS = opt("--seeds"); TAG = opt("--tag")
DATA, OUT = args[0], args[1]
D = json.load(open(DATA, encoding="utf-8"))
INV = D["invoke"]; HOST = INV["host"].rstrip("/")
MODEL = MODEL or INV["model"]
SEEDS = int(SEEDS or INV["seeds"])
TAG = TAG or "".join(c for c in MODEL.lower() if c.isalnum())[:12]
RAW = os.path.join(OUT, "raw"); os.makedirs(RAW, exist_ok=True)


def call(path, body=None, method=None):
    req = urllib.request.Request(HOST + path, method=method or ("POST" if body is not None else "GET"))
    data = None
    if body is not None:
        data = json.dumps(body).encode(); req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data, timeout=120) as r:
        raw = r.read()
    return json.loads(raw) if raw[:1] in (b"{", b"[") else raw


def model_ref(model_type, name):
    for m in call("/api/v2/models/?model_type=" + model_type)["models"]:
        if m["name"] == name:
            return {k: m[k] for k in ("key", "hash", "name", "base", "type")}
    raise SystemExit(f"no {model_type} model named {name!r} on {HOST}")


def board_id(name):
    for b in call("/api/v1/boards/?all=true"):
        if b["board_name"] == name:
            return b["board_id"]
    return call("/api/v1/boards/?board_name=" + urllib.parse.quote(name), method="POST")["board_id"]


LOADER = {"id": "loader", "type": "flux_model_loader", "is_intermediate": True, "use_cache": True,
          "model": model_ref("main", MODEL), "t5_encoder_model": model_ref("t5_encoder", INV["t5_encoder"]),
          "clip_embed_model": model_ref("clip_embed", INV["clip_embed"]), "vae_model": model_ref("vae", INV["vae"])}
BOARD = board_id(INV["board"])
EDGES = [(("loader", "transformer"), ("denoise", "transformer")), (("loader", "clip"), ("pos", "clip")),
         (("loader", "t5_encoder"), ("pos", "t5_encoder")), (("loader", "max_seq_len"), ("pos", "t5_max_seq_len")),
         (("pos", "conditioning"), ("denoise", "positive_text_conditioning")),
         (("denoise", "latents"), ("out", "latents")), (("loader", "vae"), ("out", "vae"))]


def graph(prompt, w, h):
    return {"id": "rdm4_ui", "nodes": {
        "loader": LOADER,
        "pos": {"id": "pos", "type": "flux_text_encoder", "is_intermediate": True, "use_cache": True, "prompt": prompt},
        "denoise": {"id": "denoise", "type": "flux_denoise", "is_intermediate": True, "use_cache": True,
                    "denoising_start": 0.0, "denoising_end": 1.0, "add_noise": True, "cfg_scale": 1.0,
                    "cfg_scale_start_step": 0, "cfg_scale_end_step": -1, "width": w, "height": h,
                    "num_steps": INV["steps"], "guidance": INV["guidance"], "seed": 0},
        "out": {"id": "out", "type": "flux_vae_decode", "is_intermediate": False, "use_cache": False,
                "board": {"board_id": BOARD}}},
        "edges": [{"source": {"node_id": a, "field": b}, "destination": {"node_id": c, "field": d}} for (a, b), (c, d) in EDGES]}


def full_prompt(e):
    return f"{e['prompt']}, {D['styles'][e['kind']]}, {D['style']}, {e.get('backdrop', D['backdrop'])}"


MAN = os.path.join(RAW, "manifest.json")
manifest = json.load(open(MAN)) if os.path.exists(MAN) else []
have = {(m["element"], m["tag"], m["seed"]) for m in manifest}
els = [e for e in D["elements"] if not ONLY or e["name"] in ONLY.split(",")]
pending = {}                                     # item_id -> (element, seed)
for e in els:
    seeds = [(zlib.crc32(e["name"].encode()) + k * 7919) % 2 ** 31 for k in range(SEEDS)]
    seeds = [s for s in seeds if (e["name"], TAG, s) not in have]
    if not seeds:
        continue
    w, h = e["size"]
    r = call("/api/v1/queue/default/enqueue_batch", {"prepend": False, "batch": {
        "graph": graph(full_prompt(e), w, h), "runs": 1, "origin": "claude-ue5", "destination": "rdm4_ui",
        "data": [[{"node_path": "denoise", "field_name": "seed", "items": seeds}]]}})
    for iid in r["item_ids"]:
        pending[iid] = e["name"]
    print("queued", e["name"], len(r["item_ids"]), flush=True)

t0 = time.time()
while pending:
    time.sleep(4)
    for iid in list(pending):
        it = call(f"/api/v1/queue/default/i/{iid}")
        st = it["status"]
        if st in ("pending", "in_progress"):
            continue
        name = pending.pop(iid)
        seed = next(f["value"] for f in it["field_values"] if f["field_name"] == "seed")
        if st != "completed":
            print("FAILED", name, seed, st, it.get("error_type"), it.get("error_message"), flush=True)
            continue
        img = next(v["image"]["image_name"] for v in it["session"]["results"].values() if "image" in v)
        path = os.path.join(RAW, f"{name}_{TAG}_{seed}.png")
        open(path, "wb").write(call(f"/api/v1/images/i/{img}/full"))
        secs = round(time.mktime(time.strptime(it["completed_at"][:19], "%Y-%m-%d %H:%M:%S")) -
                     time.mktime(time.strptime(it["started_at"][:19], "%Y-%m-%d %H:%M:%S")))
        manifest.append({"element": name, "tag": TAG, "model": MODEL, "seed": seed, "image": img, "seconds": secs,
                         "file": os.path.basename(path)})
        json.dump(manifest, open(MAN, "w"), indent=1)
        print(f"done {name} seed {seed} {secs}s ({len(pending)} left, {time.time() - t0:.0f}s)", flush=True)
print("all done")
