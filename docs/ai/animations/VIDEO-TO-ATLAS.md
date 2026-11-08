# Video and animated image sources → Visual Atlas

Keep the existing `smi-visual-pack/1` region/sequence contract as the delivery format. Videos are **inputs to review and extraction**, not new runtime asset types. This importer does not run generative models, infer a skeleton, remove backgrounds, or certify art.

## Linux Mint setup

From a checkout of Superior-MI-Icon-Atlas:

```bash
sudo apt update
sudo apt install -y ffmpeg python3-pil
python3 -m tools.import_animation input.mp4 --out /tmp/sky-review --fps 16 --seconds 3
```

Inputs: GIF, APNG, animated WebP, MP4, WebM, MOV, MKV and M4V. Animated image durations are preserved; video frames are sampled at the requested fixed FPS (1–30), from `--start` seconds for up to 8 seconds. Source files are never modified. Frame-count and pixel bounds are inherited from the existing GIF importer.

The review folder includes `frames-review.png` and `qa-report.json`. Inspect **every frame**, particularly character identity, feet, tail roots, alpha, and last→first loop seam. Audio and variable original timestamps are not carried into the game sprite sequence.

## Package only after visual review

For a transparent sprite animation:

```bash
python3 -m tools.import_animation sky_walk.webm --out /tmp/sky-review \
  --fps 16 --seconds 0.6 --playback loop
# Inspect the entire contact sheet, then explicitly approve:
python3 -m tools.import_animation sky_walk.webm --out /tmp/sky-review \
  --fps 16 --seconds 0.6 --id sky.walk.test --license UNSPECIFIED \
  --pack /tmp/sky-walk.zip --approve-visual
python3 tools/validate_visual_pack.py /tmp/sky-walk.zip
```

Most generative video is **opaque**. For characters, the default alpha gate blocks packaging until the source is properly matted and visually checked. For a *deliberately opaque* scene/background clip only, add `--allow-opaque`. This does not make transparency or copyright clearance appear. Generated model videos may have cuts, framing drift or incorrect limbs; these must be rejected before calling a sequence game-ready.

The resulting ZIP imports through the existing Builder: **Builder / My Bag → Import ZIP**. The web Builder does not currently take raw MP4/WebM directly; use this local preprocessing step rather than a second browser-side decoder.

## Three controlled generative-model tests

1. **Image-to-video motion:** one isolated, high-resolution approved Sky master; fixed right-facing camera; generate 3–5s walk in place. Evaluate identity drift and tail/foot consistency.
2. **Start/end conditioned video:** use two *independently verified* contact poses; request intermediate movement; evaluate the transition and loop seam without assuming the model provides a seamless cycle.
3. **Pose/motion-driven video:** drive Sky from a clean reference gait clip, keeping background/camera fixed. Compare with the original and RIFE-only output at the **same cycle time and viewport size**.

Source video and model settings remain private experimental inputs. Do not publish model output just because it decodes successfully. Treat source rights, fidelity, temporal motion, and exact Builder import as independent QA gates.

Comparison metrics: selected original source frames, unique frame count, clip time, alpha coverage, first/last seam, foot plant and tail counts. Use RIFE only *after* selecting valid source poses. Do not stack optical flow blindly to conceal bad anatomy.

This script is a narrow adapter to `tools/import_gif.py` for contact-sheet QA and deterministic atlas packing. It adds no new Atlas asset kinds or renderer logic.
