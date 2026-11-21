# 3D model generation with ComfyUI (image to 3D)

What was set up, run and learned on the LAN's ComfyUI server between 2026-11-19 and 2026-11-20. The goal was generating textured 3D models from single images (a test chest, then two frigates from concept art) and reading what each model does well and badly. This is a record, not a tutorial: numbers are measured unless marked otherwise.

## Contents

- [The host](#the-host)
- [Installing the 3D stack](#installing-the-3d-stack)
- [The models compared](#the-models-compared)
- [Matching a photo's look: Pixal3D and projection](#matching-a-photos-look-pixal3d-and-projection)
- [Running jobs](#running-jobs)
- [Operational lessons](#operational-lessons)
- [What was delivered](#what-was-delivered)
- [Open items](#open-items)

## The host

### Hardware and system

- **Host:** `192.168.1.35`, the same machine as InvokeAI (`:9090`).
- **GPU:** RTX 4090 with 24 GB. ComfyUI reports "Total VRAM 24209 MB".
- **Memory:** 32 GB of RAM and 27 GB of swap.
- **System:** Ubuntu 24.04, dual-booting Windows with the GRUB menu hidden.
- **Disks:**
  - `/` is 837 G, with 108 G free.
  - `/apps` is 98 G, with **9.7 G free**: the 3D models fill it.
  - `/genai` is 1.5 T, 97 % used.

### NVIDIA driver

The driver is **595.99.02 open** (`nvidia-driver-595-open`) on kernel 6.8.0-149, reporting CUDA 13.2. It was 535.309.01 (CUDA 12.2) until 2026-11-19, when it was upgraded with the user's go-ahead.

- **Why it had to change:**
  - unattended-upgrades had installed kernel 149 without an NVIDIA module, so the next reboot would have come up with no GPU;
  - Ollama needs driver 550 or newer, and on the old driver it ran on Vulkan.
- **How it was upgraded:**
  1. Record the state.
  2. Boot 149 once with `grub-reboot`.
  3. Stop every GPU user (both containers and Ollama).
  4. Install the driver.
  5. Check each kernel with `modinfo -k <kernel> nvidia`.
  6. Reboot. The machine was back in 114 s and the GPU services were down about 6 minutes.
  7. Verify, then put GRUB back as it was.
- **Rollback:** `/root/driver-upgrade-2026-11-19/` holds the notes, the original grub file, `ROLLBACK.txt` and 16 of the 535 debs. The rollback is partial: the 535 module for kernel 149 is not among the debs.
- **Kernels 134 and 136 have no NVIDIA module now.** The archive's 595 builds for them are older than 595.99.02 and cannot be installed beside it.
- **Lesson: check before every reboot.** unattended-upgrades installs kernels without keeping the NVIDIA module meta-package in step. Run `modinfo -k <newest kernel> nvidia` first.
- **Checked after the change:** the test jobs gave the same results (the chest at 381,636 faces, TRELLIS in 64 s), InvokeAI made a FLUX image in 78 s, and Ollama moved to CUDA (33 layers, about 200 tok/s).

### The container

- **Container:** `comfyui-cu124`, image `yanwk/comfyui-boot:cu124-slim`. The image is openSUSE Tumbleweed with glibc 2.42 and Python 3.12.
- **Compose file:** `/genai/comfyui/docker-compose.yml`. A backup is `docker-compose.yml.bak-2026-11-19`, and a copy is `setup/docker-compose.yml.current`.
- **Restart policy:** `no`, as for InvokeAI. Start both by hand after a reboot with `docker compose up -d` in `/genai/comfyui` and `/genai/InvokeAI/docker`. wan2gp is `unless-stopped`.
- **`/root` is an anonymous volume** (`d87c5ed8…`). It holds:
  - the ComfyUI checkout and about 230 GB of earlier models;
  - the user-site packages in `/root/.local` (11 GB);
  - the CUDA build toolkit in `/root/cuda126`.

  It survives `docker compose up -d` recreating the container. The container has no `find`. Its files can be edited from the host under `/var/lib/docker/volumes/d87c5ed8…/_data/`.
- **Mounts added:**
  - `/apps/comfyui-3d` → `/root/ComfyUI/models/3d`.
- **Environment added in compose:**
  - `HF_HOME=/root/ComfyUI/models/3d/hf`, so the Hugging Face cache lands on `/apps`, not `/`.
  - `LD_LIBRARY_PATH=` (empty), because the image's value points at its own torch 2.6 libraries.
  - `ATTN_BACKEND=xformers` and `SPARSE_ATTN_BACKEND=xformers` (see [TRELLIS](#trellis-image-large-microsoft-smthemexs-pack)).
- **Model paths:** `extra_model_paths.yaml` adds a block `comfyui_3d` with base `/root/ComfyUI/models/3d` and these folders: checkpoints, diffusers, diffusion_models, vae, dinov2, upscale_models, clip_vision, background_removal, geometry_estimation.
  - The canonical copy is `/apps/comfyui-3d/setup/extra_model_paths.yaml`. It is copied into the container by `fixyaml.sh`.
  - Never keep the working copy in the host's `/tmp`: the 2026-11-19 reboot wiped it. A script then wrote an empty file over the config, and ComfyUI crashed at start.

### Versions

The versions as of 2026-11-20:

| Component | Version |
|---|---|
| ComfyUI | 0.46.0 (`v0.46.0-11-g199442068`). The pre-update commit `ba6080bba` (0.5.1) is saved in `setup/comfyui-commit-before-update.txt` |
| Frontend | 1.59.6 |
| Workflow templates | 0.11.112 |
| comfy-kitchen | 0.2.41 |
| torch, torchvision, torchaudio | 2.8.0+cu126, 0.23.0, 2.8.0. Installed in the user site; they shadow the image's torch 2.6 |
| xformers | 0.0.32.post2 |
| numpy | 1.26.4 |
| diffusers, transformers, accelerate, huggingface-hub | 0.36.0, 4.57.0, 1.10.1, 0.35.3 |
| kaolin, spconv-cu124, warp-lang | 0.18.0, 2.3.8, 1.9.1 |
| nvdiffrast, custom_rasterizer, diso | 0.4.0, 0.1.0+torch280.cuda126, 0.1.4 |
| pymeshlab, open3d, trimesh, xatlas | 2025.7.post1, 0.20.0, 4.8.3, 0.0.11 |
| rembg, onnxruntime-gpu | 2.0.67, 1.23.0 |
| OpenCV | `opencv-contrib-python-headless` 4.11.0.86, in the user site |

- **Custom node packs:**
  - `ComfyUI-Hunyuan3DWrapper` (kijai), commit `2609efa`;
  - `ComfyUI-Hunyuan3d-2-1` (visualbruno), commit `a0b26fb`;
  - `ComfyUI_TRELLIS` (smthemex), commit `a257bb6`.
  - TRELLIS.2 and Pixal3D are native in ComfyUI 0.46 and need no pack.
- **Two warnings remain in the log:**
  - "PYTORCH CUDA VERSION BELOW 13.0 … performance will be terrible";
  - comfy_kitchen's cuda and triton backends are disabled, leaving only eager.

  Both want cu130 builds of torch, which driver 595 now allows. That move hasn't been made: it means rebuilding every compiled 3D extension.

## Installing the 3D stack

The scripts are in `/apps/comfyui-3d/setup/` on the host. In order:

1. **`mount.sh`:** adds the bind mount and recreates the container. The volumes are kept.
2. **`download.sh`:** downloads 39 GB in about 8 minutes. It also left a 9.3 GB Hugging Face chunk cache in `/root/.cache/huggingface` on `/`, which was deleted; the scripts now clear `$M/hf/xet` themselves.
3. **`paths.sh`:** sets `HF_HOME` on `/apps`, writes the model-paths file, and links the kijai wrapper's `models/diffusers/hunyuan3d-{paint,delight}-v2-0` into `/apps`. It also puts the Hunyuan 2.1 dit and vae into `diffusion_models/` and `vae/`. Without that, the 2.1 pack downloads them into the cache on `/`.
4. **`cuda2.sh`, the toolkit:** the image has no `nvcc`. A CUDA toolkit was assembled in the volume from NVIDIA's redistributable archives (nvcc, cudart, cccl, nvtx, profiler_api, all sha256-checked) plus pip's nvidia packages for the math headers and libraries. This first one was 12.4; it was later replaced by 12.6 in `/root/cuda126`.
5. **`fixmath.py`:** CUDA 12.x's `crt/math_functions.h` clashes with glibc 2.41 and newer, which declare `sinpi`, `cospi`, `rsqrt` and their `f` versions `noexcept`. The script patches the six declarations to `noexcept (true)` and asserts each match. It is needed for every CUDA 12 toolkit on this image.
6. **`hy_deps.sh`, constraints and requirements:** writes `/root/pip-3d-constraints.txt` from the current pins, then installs both Hunyuan packs' requirements with `pip install --user -c /root/pip-3d-constraints.txt`.
   - **The constraints file is the rule for every install.** It keeps torch, numpy, xformers and diffusers where they are; an unpinned install upgrades them under the other packs.
   - The two Hunyuan packs ship different `custom_rasterizer` sources; the wrapper's was built.
7. **`hy_build.sh`, the Hunyuan extensions:** builds `custom_rasterizer` and the mesh processors with `TORCH_CUDA_ARCH_LIST=8.9` and `MAX_JOBS=8`. The image's pybind11 pointed at a missing include folder, so a full pybind11 went into the user site with `CPLUS_INCLUDE_PATH` set.
8. **`trellis_build.sh`, the TRELLIS extensions:** builds nvdiffrast, diffoctreerast (cloned recursively), diff-gaussian-rasterization (the mip-splatting fork) and vox2seq from git. kaolin comes from NVIDIA's wheel index, and the DINOv2 weights from Meta.
9. **`spconv.sh`:** `spconv-cu124==2.3.8` (there is no cu120 build for Python 3.12) and `warp-lang==1.9.1` (newer warp wanted a newer driver than 535 at the time).
10. **`cvfix.sh`:** the image's system `cv2` loads the system Qt, so importing `cv2` and then `pymeshlab` failed and the wrapper didn't load. The fix was `opencv-contrib-python-headless` in the user site.
11. **`update.sh`, the ComfyUI update:**
    - The Manager said 26 commits behind; it was actually 1,974.
    - The update crashed at start on torch 2.6, because comfy_kitchen registers an op annotated `list[int]` ("infer_schema … unsupported type"). Parking comfy_kitchen broke the import instead ("cannot import name 'ck'").
    - It was rolled back to `ba6080bba` within minutes, then redone on torch 2.8.
12. **`torch28.sh`, the move to torch 2.8:**
    1. Tested first in a throwaway `--target` folder: matmul, SDPA and the `list[int]` custom op.
    2. Installed torch 2.8.0/cu126 and xformers 0.0.32.post2 in the user site.
    3. Built the CUDA 12.6 toolkit, with `fixmath.py` applied.
    4. Installed kaolin 0.18 for torch 2.8.0/cu126.
    5. Rebuilt every compiled extension (custom_rasterizer, nvdiffrast, diffoctreerast, diff-gaussian, vox2seq, and diso with `--no-binary`), and smoke-tested each on the GPU.
    6. Saved the old pins and the freezes: `pip-3d-constraints-torch26.txt` and `pip-*freeze-before-3d.txt`.

    **Any torch change means rebuilding all of these extensions.**
13. **`switch.sh`:** sets `LD_LIBRARY_PATH=` in compose, checks out master, puts comfy_kitchen back and recreates the container. The old toolkit and 4.4 GB of pip cache were then removed.
14. **`dl2.sh`:** downloads the wrapper's 2.0 dit and vae (its loader lists only `diffusion_models`) and RealESRGAN x4, which the 2.1 texture node asks for.
15. **`diffusers.sh`:** diffusers 0.35.1 with transformers 4.57 fails in the wrapper's delight loader (`CLIPTextModel.__init__() got an unexpected keyword argument 'offload_state_dict'`). The fix is diffusers 0.36.0.
16. **`attnenv.sh`, TRELLIS's attention:** TRELLIS chooses its attention backend when it is imported and defaults to flash-attn, which isn't installed. The failure doesn't say so: it shows up as `RepositoryNotFoundError 401 … huggingface.co/ckpts/slat_dec_gs…`. The fix is the `ATTN_BACKEND` and `SPARSE_ATTN_BACKEND` variables in compose.
17. **`dl_trellis2.sh`:** downloads the TRELLIS.2 and Pixal3D files from Comfy-Org (TRELLIS.2, BiRefNet), about 14 GB together with `dl_pixal3d`.

### Local patches to ComfyUI_TRELLIS

The originals are kept beside them as `*.orig`. **Updating the pack undoes both.**

- **`TRELLIS_node.py`:** `texture_size` maximum raised from 2048 to 4096.
- **`trellis/utils/postprocessing_utils.py`:** when the bake mode is `opt` and the texture is over 2048, the 100 views stay in RAM as uint8 and are rasterised one per step. Without this, a 4096 texture needed about 20 GB of GPU memory for the views and about 40 GB more for their UV maps.

### Models on `/apps/comfyui-3d`

| Folder | Files and sizes |
|---|---|
| `checkpoints/` | `hunyuan_3d_v2.1` 7.37 G; `hunyuan3d-dit-v2_fp16`, `-v2-mv_fp16`, `-v2-mv-turbo_fp16` 4.93 G each |
| `diffusion_models/` | `hunyuan3d-dit-v2-0-fp16` 4.93; `hunyuan3D-dit-v2-1-fp16` 7.37; `trellis_2_bf16` 10.34; `pixal3d_bf16` 11.0 |
| `vae/` | `hunyuan3d-vae-v2-0-fp16` 0.43; `Hunyuan3D-vae-v2-1-fp16` 0.66; `trellis_2_shape_vae_bf16` 1.10; `trellis_2_texture_vae_bf16` 0.95 |
| `clip_vision/` | `dino_v3_vit_l` 1.21 (TRELLIS.2); `dino_v3_L_naf_fp32` 1.22 (Pixal3D) |
| `background_removal/`, `geometry_estimation/`, `dinov2/` | `birefnet` 0.44; `moge_2_vitl_normal_fp16` 0.66; `dinov2_vitl14_reg4_pretrain.pth` 1.22 |
| `rembg/`, `upscale_models/` | isnet-general-use 0.18, birefnet-general 0.97; `RealESRGAN_x4plus` 0.07 (sha256 checked) |
| `diffusers/` (12 G) | tencent/Hunyuan3D-2 paint and delight; microsoft/TRELLIS-image-large 3.1 G |
| `hf/` (11 G) | the Hunyuan3D-2.1 paint-PBR model, facebook/dinov2-giant |

## The models compared

**The test chest:** an SDXL picture of an antique wooden chest on white, 1024². It was made with `perfectionRealisticILXL_50`, seed 4242, 28 steps, cfg 5, euler_a, in 60 s.

**The frigates:** two pieces of concept art: `greys-boarding-frigate.jpg` and `greys-ecm-frigate.jpg`.

### Cutting the background out

**Every image needs its background cut out first.**
- On the raw chest photo, Hunyuan 2.1 modelled the tabletop and the backdrop as part of the chest.
- `rembg` with `isnet-general-use` worked.
- `birefnet-general` through onnx failed: onnxruntime's CUDA provider couldn't load `libcublasLt.so.12`, then reported "cannot parse data from external tensors".

**Beams of light have to be removed by hand.** The frigate's thruster beams would otherwise have become solid cones. They were taken out in two passes: a blue-glow mask, keeping the largest component, then filling holes.

**Keep the largest component.** On the ECM frigate this dropped a second ship in the background.

### Hunyuan3D 2.1, ComfyUI's built-in nodes (shape only)

- **Graph:** `ImageOnlyCheckpointLoader` → `CLIPVisionEncode` (center) → `Hunyuan3Dv2Conditioning` → `ModelSamplingAuraFlow` (shift 1) → `EmptyLatentHunyuan3Dv2` (res 4096) → `KSampler` (30 steps, cfg 5, euler/normal) → `VAEDecodeHunyuan3D` (8000 chunks, octree 256) → `VoxelToMesh` → `SaveGLB`.
- **The `VoxelToMesh` threshold decides the result.** A "part" below is a connected piece of the mesh.

  | Threshold | Result |
  |---|---|
  | 0.6 (the template's), surface net | 631,458 faces in 124,772 parts; the largest part only 58 % (a floor of debris) |
  | 0.6, basic | 503,648 faces |
  | **0.8** | **381,636 faces; the largest part 94.7 %. Chosen** |
  | 0.95 | the largest part 92.9 % |
  | 0.0 | hung, and `/interrupt` didn't stop it; the container had to be restarted |

- **Time:** 24 s with the image cut out; 75 s on the first run, including the model's load.
- **Remeshing:** `RemeshMesh` (sdf, qef, res 512, drop_small 0.01) plus `DecimateMesh` to 200k: 45 s, 197,075 faces, still 625 parts.
- **Verdict:** a good shape. The lid, keys, padlock and handles were all modelled. It has no texture.

### Hunyuan3D 2.0, kijai's wrapper (textured)

- **Graph:**
  - Generation: `Hy3DModelLoader` (dit-v2-0-fp16, SDPA) → `Hy3DGenerateMesh` (guidance 5.5, 30 steps) → `Hy3DVAEDecode` (octree 384, 8000 chunks, marching cubes) → `PostprocessMesh` (max 50k).
  - Texturing: Delight (50 steps, 512) → Paint v2-0 → `UVWrap` → camera config (6 views: azimuths 0/90/180/270/0/180, elevations 0/0/0/0/90/-90) → `RenderMultiView` (1024, texture 1024) → `SampleMultiView` (view 512, 30 steps) → Bake → vertex inpaint → cv2 inpaint (ns, r3) → Apply → Export.
- **Chest:** 81 s, 50,000 faces, a 1024² texture. A few rough patches on the keys.

### Hunyuan3D 2.1, visualbruno's pack (PBR)

- **Graph:** wired as its Full_Workflow example. `Hy3D21MeshGenerator` (25 steps, guidance 7.5) → `VAEDecode` (octree 256, 64000 chunks, flash_vdm) → Postprocess (max 200k) → `UVWrap` → camera config (weights 1/.5/1/.5/1/1, ortho 1.1) → `MultiViewsGenerator` (view 768, 10 steps, guidance 3, texture 1024) → `BakeMultiViews` → InPaint.
- **Chest:** 204 s on the first run, including loading the paint model and dinov2-giant. 200,000 faces, 1024² PBR with metallic and roughness.
- **Frigate:**
  - The first run ran out of GPU memory after 341 s, because InvokeAI held 12.8 GB (see [Operational lessons](#operational-lessons)).
  - After freeing it: 180 s, 200,000 faces.
  - It came out flat dark navy, the panel detail lost.
- **Quirks:**
  - it ignores the filename's folder prefix and writes `output/<name>.glb`;
  - it leaves `temp.glb` and `mr_combined.png` in `/root` on every run.

### TRELLIS image-large (microsoft), smthemex's pack

- **Loader:** `Trellis_LoadModel` with the repo pointed at the local folder `/root/ComfyUI/models/3d/diffusers/microsoft/TRELLIS-image-large` (its default downloads again), DINOv2 `dinov2_vitl14_reg4_pretrain.pth`, and xformers attention.
- **Sampler:** `Trellis_Sampler` with seed 7, cfg 7.5, 12 steps, slat cfg 3, slat steps 12, mode `opt`, texture 1024, `mesh_simplify` 0.95.
  - **The sampler is not an output node.** The graph needs a `Preview3D` after it, or nothing runs.
  - It writes a randomly named GLB in `output/`.
- **`mesh_simplify` is the share of faces *removed***, from 0 to 0.98:
  - 0.95 gives about 12.5k faces;
  - 0.5 gives about 155k.
- **Chest:** 66 s, 29,154 faces, 1024² texture. It left out the keys inside the lock.
- **Frigate at 0.95 and 1024:**
  - 160 s, 12,566 faces, 1.5 MB.
  - A gunmetal hull with panel lines and blue lights, but it invented rear legs.
  - The best result before TRELLIS.2.
- **Frigate "detailed 4K"** (`mesh_simplify` 0.5, texture 4096, which needs both local patches):
  - 188 s, 155,158 faces, 17.6 MB.
  - **The 4K texture held no more detail than 1K** in close-ups from the same camera. TRELLIS's colour comes from its fixed-resolution Gaussian appearance, so the texture size can't add detail. Only the mesh's extra detail was a gain.

### TRELLIS.2 (native in ComfyUI 0.46)

- **Template:** `3d_pixal3d_trellis2_image_to_model.json`, the only TRELLIS template. A `PrimitiveBoolean` switches between its two paths:
  - False (the default) is Pixal3D;
  - True is `Trellis2Conditioning`.
- **Weights:** the template's `UNETLoader` defaults to `pixal3d_int8_convrot`; the bf16 files were used instead. That int8 won't run here was inferred from comfy_kitchen's disabled backends, **not tested**.
- **The graph** (`tT2_frigate.py`):
  - **Input:** `LoadImage` → BiRefNet `RemoveBackground` → `ImageCropToMask` (1024, pad 1.1, black) → `CLIPVisionLoader` `dino_v3_vit_l` → `Trellis2Conditioning` → `UNETLoader` `trellis_2_bf16`.
  - **Structure:** `CFGOverride` (1.0, from 0.667 to 1) → `RescaleCFG` 0.7 → `ModelSamplingSD3` shift 5 → `EmptyTrellis2LatentStructure` → `KSampler` (seed 56, 12 steps, cfg 7.5, euler/normal) → `VaeDecodeStructureTrellis2` (res 32).
  - **Shape:** `CFGOverride` (0.769) → `RescaleCFG` 0.5 → `Trellis2ShapeStage` → `KSampler` (seed 42, 20 steps, cfg 7.5) → `Trellis2UpsampleStage` (to 1536) → `KSampler` (12 steps, simple) → `VaeDecodeShapeTrellis`.
  - **Texture:** `Trellis2TextureStage` → `KSampler` (seed 43, 12 steps, cfg 1) → `VaeDecodeTextureTrellis`.
  - **Mesh:**
    1. `RemeshMesh` (res 768, solid, fill 20, smooth 20, drop_small 0.01);
    2. `DecimateMesh` (midpoint), then `MeshSmoothNormals` (180);
    3. `UnwrapMesh` (pec);
    4. `BakeTextureFromVoxel`;
    5. `BakeNormalMapFromMesh` (2048, cage 0.05);
    6. `BakeAmbientOcclusion` (1024, 64 samples, distance 0.71);
    7. `ApplyTextureToMesh`, then `SaveGLB`.
- **Frigate:**
  - 151 s. The raw shape was 19.6 million faces (a 351 MB GLB), decimated to 699,868 faces.
  - Maps: colour and metal-rough at 4096, normal at 2048, AO at 1024. The GLB is 54 MB.
  - **Far sharper than TRELLIS:** crisp ring steps, panel seams, a ribbed dome, segmented legs.
  - But it lost the blue lights, made the hull lighter than the art, added faint noise, and is far too heavy for a game.
- **ECM frigate** (the user's spec: TRELLIS.2, 2048 maps, about 12 to 15k faces; decimated to 13,500):
  - 205 s. The raw shape was 42 million faces (745 MB); the result 13,480 faces, 12.8 MB.
  - The holographic dishes came out solid teal, a fin came out as two blades, and domes were added for symmetry.
- **TRELLIS.2 bakes de-lit albedo**, measured against the source art in Blender renders (lit, unlit at 1×, 2× and 4×, and with a headlight):

  | | Brightness | Saturation | Fine detail |
  |---|---|---|---|
  | Source art | 0.289 | 0.38 | 0.033 |
  | Baked colour map | 0.086 | 0.87 | 0.011 |
  | Baked normal map | | | 0.042 |

  So:
  - the art's grey, its panel highlights and its glow are lighting, which TRELLIS.2 removes;
  - the panels TRELLIS.2 draws are in its normal map, and are its own invention, not the art's.
- **Fixing the colour map alone wasn't enough.** Correcting it to the art's luminance (0.289) and saturation (0.55), plus a cavity layer from the normal map, still left TRELLIS.2's panels, not the art's.

### Rigging, animation and export

- **Nothing local is installed for rigging or animation.**
  - The Meshy and Tripo nodes in ComfyUI are paid cloud services.
  - `BuildPoseFile` only works on its own body model.
  - Candidates named but not installed: Mesh2Motion, SkinTokens / UniRig, Make-It-Animatable, HY-Motion, Kimodo.
- **Export formats:**
  - The Hunyuan packs write GLB, OBJ, PLY, STL, 3MF and DAE.
  - TRELLIS writes GLB, OBJ and a splat PLY. Its FBX option needs Blender inside the container, which isn't installed.
  - ComfyUI 0.46's `SaveGLB` also takes glTF, FBX, OBJ, STL, USDZ and PLY.

## Matching a photo's look: Pixal3D and projection

The user asked for the ECM frigate to carry the concept art's colours and panel details, which no model did. Projecting the art onto the model does.

1. **Generate with Pixal3D** (`tP_ecm.py`). It is camera-aligned: the shape is generated in the photo's own camera frame.
   - Weights: `pixal3d_bf16` (11 GB) and `dino_v3_L_naf_fp32`.
   - MoGe `moge_2_vitl_normal_fp16` estimates the field of view: `MoGeInference` (level 9, force projection, apply mask, refine 3) → `MoGeGeometryToFOV` (horizontal) → `Pixal3DConditioning(camera_angle_x)`.
   - Then the same TRELLIS.2 stages, at 13,500 faces and 2048 maps. The graph also saves the exact 1024 crop and its mask.
   - Result: 105 s, a horizontal FOV of 55.75°, a raw shape of 17 million faces.
2. **Fit the camera and project the art** (`setup/project_photo.py`):
   - **The camera fit:** nvdiffrast soft coverage fitted with Adam, in 300 iterations at 128 px, 300 at 256 and 200 at 512. It starts from 24 axis-aligned views times 3 tilts. The best start reached IoU 0.828 and fitted to **0.9948**; the other starts stopped at 0.84 to 0.88.
   - **The bake:** each texel the photo sees takes its colour, depth-tested and weighted by how squarely it faces the camera, feathered with a Gaussian of 1.5.
   - **The rest of the texture:** texels the photo can't see keep the model's own colour, matched in mean and spread to the projected colours, and the texture is grown into the UV gutters.
   - **The glow:** emissive is taken from the bright blue-white glow (3.8 % of texels).
   - **Coverage:** about 32 % of the surface comes from the photo.
   - **Measured:** the error against the art from its own viewpoint fell from **33.6/255 to 10.4/255**.
   - **A bug caught before the run:** the fill's statistics first mixed texture-space and render-space pixel orders.
3. **Level the model** (`setup/level_mesh.py`). Pixal3D's model sits in the photo's camera frame, here tilted 23.8°.
   - The script takes the thinnest PCA axis as up, and a skew sign to choose which side is the top.
   - On the ECM frigate that guess picked the lower pod as the top, so the `flip` argument was needed.
   - **Always look at front, side, back and underside renders before delivering.**
4. **Result:** `ecm_frigate_pixal3d_photo_13k_2k.glb`: 13,500 faces; colour, emissive, metal-rough, normal and AO at 2048; 12.5 MB. The back and underside are Pixal3D's guess, and the dishes are still solid.

### Validating a GLB

The Khronos validator wasn't installed, so the project's own `validate_glb.py` checked `ecm_frigate_trellis2_13k_2k.glb`. It is valid:
- 11,667 vertices, 13,480 triangles, tangents present;
- three PNG maps at 2048, with AO packed into metal-rough;
- opaque and double-sided;
- a closed surface, with 1 duplicate triangle and 21 non-manifold edges of 20,199.

## Running jobs

**Jobs are posted to ComfyUI's API in API format** with `cq.py`:
- `/upload/image` sends the input;
- `/prompt` queues the graph;
- `/history` is polled for the result;
- `/view` fetches the files.

**The workflow scripts** (`tA_*`, `tB_wrapper`, `tC_21`, `tD_trellis`, `tF_*`, `tT2_*`, `tP_ecm`) and the renders are in the session's scratch folder, `comfy3d\`, which is not durable. `tP_ecm.py` and the projection scripts are also in `setup/` on the host.

**Free the GPU before a heavy job.** InvokeAI keeps about 12.8 GB of FLUX cached after its last job, and the Hunyuan 2.1 texturing then runs out of memory. Send both:
- `POST http://192.168.1.35:9090/api/v2/models/empty_model_cache` to InvokeAI;
- `POST /free` with `{"unload_models": true, "free_memory": true}` to ComfyUI.

The GPU dropped to about 1.1 GB used. The `tT2_*` and `tP_*` scripts do this first.

**Expect large leftovers.** Each TRELLIS.2 run saves its raw shape as a big GLB (351 MB and 745 MB so far) in `output/` on `/`, which now holds 1.3 GB.

## Operational lessons

- **Never split a generated mesh on the host.** trimesh `split()` on a 200k-face mesh grew to 20 GB and stalled the server for about 10 minutes, until the process was killed. Count parts from the face adjacency instead: `trimesh.graph.connected_components(face_adjacency)`.
- **A stuck `VoxelToMesh` can't be interrupted.** Neither `/interrupt` nor clearing the queue stops it: restart the container.
- **Commands go over ssh as script files, not inline.** PowerShell mangles inline commands: an inner `"…|…"` was split into separate commands. What works:
  1. Write a `.sh` file locally, with LF line endings and UTF-8 without a BOM.
  2. `scp` it to `/tmp/c3d_x.sh` on the host.
  3. Run it with `ssh … "bash /tmp/c3d_x.sh"`.
  4. For Python inside the container: `docker cp` the file in, then `docker exec … python3`.
- **The Manager's "commits behind" is stale.** It showed 26 against 1,974 actual.
- **Look before trusting a number.** Two examples:
  - the 4K TRELLIS texture measured "bigger" and held no more detail;
  - TRELLIS.2's panel detail was in the normal map, not the colour.

  Compare same-camera close-ups, and measure brightness, saturation and detail against the source.
- **On Windows,** the Python with the needed libraries is the amv-maker venv. The system Python 3.12 failed SSL verification against GitHub.

## What was delivered

**In `I:\game assets\3d unity samples\test`** (written there at the user's request; the library is otherwise read only):

| Model | Files |
|---|---|
| Chest | `chest_A_hunyuan21_builtin_shape.glb`; `chest_B_hunyuan20_wrapper_{shape,textured}.glb`; `chest_C_hunyuan21_{shape,pbr_textured}.glb`; `chest_D_trellis_textured.glb`; the input image and its cut-out |
| Frigate | `frigate_hunyuan21_{shape,pbr_textured}.glb`; `frigate_trellis_textured.glb`; `frigate_trellis_detailed_4k.glb`; `frigate_trellis2_textured_4k.glb`; its 4K base colour; the cut-out |
| ECM frigate | `ecm_frigate_trellis2_13k_2k.glb`; the TRELLIS.2 and Pixal3D base colours; the Pixal3D emissive; the cut-out; `ecm_frigate_pixal3d_photo_13k_2k.zip`, with a folder of that name holding the projected model |

**A three.js viewer** of all of them, as a private artifact:
- links straight to each model;
- lighting modes Headlight, Studio and Unlit, with a brightness slider;
- a Download button that saves a model as a zip. The button wasn't tested by the agent; the zip in the folder suggests it worked.

**On the server:**
- the test outputs in `output/test3d/`, `output/frigate/` and `output/ecm/`;
- the scripts in `/apps/comfyui-3d/setup/`.

## Open items

- **No rigging or animation** installed.
- **The cu130 torch move** isn't done, and the log still warns about it. It means rebuilding every 3D extension for CUDA 13.
- **The int8 TRELLIS.2 and Pixal3D weights, and Pixal3D's multi-view variant,** were not tried.
- **Not run:** Hunyuan3D's multi-view checkpoints were downloaded but never used, and TripoSG and other models were not tried.
- **Lost on a pack update:** the TRELLIS patches.
- **Space on `/apps`:** 9.7 GB left. Cleanup to do:
  - the raw TRELLIS.2 shapes in `output/` on `/`;
  - the 2.1 pack's `temp.glb` and `mr_combined.png` in `/root`;
  - ten apt autoremove packages.
- **The driver's loose ends:** kernels 134 and 136 have no NVIDIA module, and the offline 535 rollback is partial.
- **A failing import:** `comfyui-ltxvideo-registry-mattabyte` still fails to import. Whether to disable it is the user's call.
- **A lighter TRELLIS.2 frigate** (about 100k faces) was offered and not made.
